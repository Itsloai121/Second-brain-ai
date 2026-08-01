from collections import defaultdict
from datetime import datetime, timezone
from psycopg.types.json import Jsonb
from .db import db

def dashboard_rows():
    with db() as c:
        c.execute("""SELECT p.id,p.sku,p.name,i.on_hand,i.allocated,i.in_transit,COALESCE(sm.actual_lead_days,35) AS actual_lead_days,COALESCE(sm.quoted_lead_days,35) AS quoted_lead_days,s.moq,p.unit_cost,s.code AS supplier_code,s.name AS supplier_name FROM products p JOIN inventory i ON i.product_id=p.id JOIN suppliers s ON s.id=p.supplier_id LEFT JOIN LATERAL (SELECT * FROM supplier_metrics x WHERE x.supplier_id=s.id ORDER BY measured_on DESC LIMIT 1) sm ON true WHERE p.active""")
        rows=c.fetchall(); cols=[x.name for x in c.description]
        return [dict(zip(cols,r)) for r in rows]
def history(product_id,days=120):
    with db() as c:
        c.execute('SELECT sales_date,SUM(units) FROM sales_daily WHERE product_id=%s AND sales_date>=current_date-%s GROUP BY sales_date ORDER BY sales_date',(product_id,days))
        return [{'date':r[0],'units':r[1]} for r in c.fetchall()]
def retrieve(query,limit=4):
    with db() as c:
        c.execute("SELECT title,body,source,ts_rank(search_vector,websearch_to_tsquery('english',%s)) score FROM knowledge_docs WHERE search_vector @@ websearch_to_tsquery('english',%s) ORDER BY score DESC LIMIT %s",(query,query,limit))
        return [{'title':r[0],'body':r[1],'source':r[2],'score':float(r[3])} for r in c.fetchall()]
def create_conversation(user_id):
    with db() as c:c.execute('INSERT INTO conversations(user_id) VALUES(%s) RETURNING id',(user_id,));return str(c.fetchone()[0])
def remember(conversation_id,user_id,kind,content):
    with db() as c:c.execute('INSERT INTO memories(conversation_id,user_id,kind,content) VALUES(%s,%s,%s,%s)',(conversation_id,user_id,kind,Jsonb(content)))
def save_recommendation(product_id,r):
    with db() as c:c.execute('INSERT INTO recommendations(product_id,type,priority,rationale,recommended_quantity) VALUES(%s,%s,%s,%s,%s) RETURNING id',(product_id,r['type'],r['priority'],Jsonb(r['rationale']),r['quantity']));return str(c.fetchone()[0])
def draft_action(action_type,payload,user_id):
    with db() as c:c.execute('INSERT INTO action_drafts(action_type,payload,created_by) VALUES(%s,%s,%s) RETURNING id,status',(action_type,Jsonb(payload),user_id));r=c.fetchone();return {'id':str(r[0]),'status':r[1]}

def system_checks():
    checks=[]
    def add(name,status,detail): checks.append({'name':name,'status':status,'detail':detail})
    try:
        with db() as c:
            c.execute('SELECT 1');c.fetchone();add('Database connection','pass','PostgreSQL responded successfully')
            c.execute('SELECT COUNT(*) FROM products WHERE active');products=c.fetchone()[0]
            add('Active products','pass' if products else 'fail',f'{products} active products loaded')
            c.execute('SELECT COUNT(*) FROM suppliers WHERE active');suppliers=c.fetchone()[0]
            add('Active suppliers','pass' if suppliers else 'fail',f'{suppliers} active suppliers loaded')
            c.execute('SELECT COUNT(*) FROM inventory WHERE on_hand < 0 OR allocated < 0 OR in_transit < 0');negative=c.fetchone()[0]
            add('Inventory values','pass' if negative == 0 else 'fail','No negative inventory values' if negative == 0 else f'{negative} invalid inventory rows')
            c.execute('SELECT COUNT(*) FROM products WHERE active AND supplier_id IS NULL');missing=c.fetchone()[0]
            add('Supplier assignments','pass' if missing == 0 else 'warning','All products have suppliers' if missing == 0 else f'{missing} products missing suppliers')
            c.execute('SELECT MAX(sales_date),COUNT(*) FROM sales_daily');latest,sales_rows=c.fetchone()
            if latest is None:add('Sales history','fail','No sales history loaded')
            else:
                age=(datetime.now(timezone.utc).date()-latest).days
                add('Sales history','pass' if age <= 2 else 'warning',f'{sales_rows} rows; latest date {latest.isoformat()}')
            c.execute('SELECT COUNT(*) FROM knowledge_docs');docs=c.fetchone()[0]
            add('Knowledge layer','pass' if docs else 'warning',f'{docs} knowledge documents indexed')
    except Exception as exc:
        add('Database connection','fail',f'{type(exc).__name__}: {exc}')
    overall='error' if any(x['status']=='fail' for x in checks) else ('warning' if any(x['status']=='warning' for x in checks) else 'healthy')
    return {'status':overall,'checked_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'summary':{'passed':sum(x['status']=='pass' for x in checks),'warnings':sum(x['status']=='warning' for x in checks),'failed':sum(x['status']=='fail' for x in checks)}}
