from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from .db import open_pool,close_pool
from . import repository as repo
from .forecasting import forecast_daily
from .recommendations import build_recommendation
from .calculations import average_daily_demand,available,days_of_cover
from .llm import answer

@asynccontextmanager
async def lifespan(app):
    open_pool();yield;close_pool()
app=FastAPI(title='Navohaus Supply Chain Second Brain',version='0.3.0',lifespan=lifespan)
class ChatIn(BaseModel): question:str=Field(min_length=2,max_length=1500);user_id:str='demo-user';conversation_id:str|None=None
class ActionIn(BaseModel): payload:dict;user_id:str='demo-user'
class EmployeeReportIn(BaseModel): message:str=Field(min_length=5,max_length=2000);user_id:str='demo-user'
def operational():
    out=[]
    for row in repo.dashboard_rows():
        hist=repo.history(row['id'])
        item={**row,'history':[x['units'] for x in hist],'lead_days':row['actual_lead_days'],'quoted_lead_days':row['quoted_lead_days']}
        rec=build_recommendation(item)
        demand=average_daily_demand(item['history'][-28:])
        available_units=available(row['on_hand'],row['allocated'])
        net=available_units+row['in_transit']
        forecast_30=forecast_daily(hist,30)
        out.append({
            'sku':row['sku'],'name':row['name'],'on_hand':row['on_hand'],
            'available':available_units,'allocated':row['allocated'],'in_transit':row['in_transit'],
            'days_of_cover':days_of_cover(net,demand),'avg_daily_demand':demand,
            'actual_lead_days':row['actual_lead_days'],'quoted_lead_days':row['quoted_lead_days'],
            'lead_days':row['actual_lead_days'],'supplier_code':row['supplier_code'],
            'supplier_name':row['supplier_name'],'unit_cost':float(row['unit_cost']),
            'forecast_30_units':forecast_30['total'],'recommendation':rec,'product_id':str(row['id'])
        })
    return out
@app.get('/')
def home():return FileResponse('web/index.html')
@app.get('/api/dashboard')
def dashboard():
    items=operational();return {'kpis':{'skus':len(items),'critical':sum(1 for x in items if x['recommendation'] and x['recommendation']['priority']=='critical'),'units_on_hand':sum(x['on_hand'] for x in items),'units_in_transit':sum(x['in_transit'] for x in items)},'items':items}
@app.post('/api/forecast/{sku}')
def forecast(sku:str,horizon:int=30):
    row=next((x for x in repo.dashboard_rows() if x['sku']==sku),None)
    if not row:raise HTTPException(404,'SKU not found')
    return {'sku':sku,**forecast_daily(repo.history(row['id']),min(max(horizon,1),180))}
@app.post('/api/recommendations/run')
def run_recommendations():
    saved=[]
    for x in operational():
        if x['recommendation']:saved.append({'id':repo.save_recommendation(x['product_id'],x['recommendation']),**x['recommendation']})
    return {'created':len(saved),'recommendations':saved}
@app.post('/api/chat')
async def chat(body:ChatIn):
    cid=body.conversation_id or repo.create_conversation(body.user_id); context=repo.retrieve(body.question); ops=operational(); response=await answer(body.question,context,ops)
    repo.remember(cid,body.user_id,'exchange',{'question':body.question,'answer':response,'sources':[x['title'] for x in context]})
    return {'conversation_id':cid,'answer':response,'sources':[{'title':x['title'],'source':x['source']} for x in context]}
@app.post('/api/actions/purchase-order/draft')
def po_draft(body:ActionIn):return repo.draft_action('purchase_order',body.payload,body.user_id)
@app.post('/api/actions/expedite/draft')
def expedite_draft(body:ActionIn):return repo.draft_action('supplier_expedite',body.payload,body.user_id)
@app.get('/api/monitoring')
def monitoring():return {'service':'healthy','guardrail':'human approval required','metrics':['forecast_wape','stockout_rate','supplier_otd','recommendation_acceptance','action_override_rate']}
@app.get('/api/system-check')
def system_check():return repo.system_checks()
@app.post('/api/employee-reports')
def employee_report(body:EmployeeReportIn):
    result=repo.draft_action('employee_report',{'message':body.message,'category':'project_improvement'},body.user_id)
    return {**result,'message':'Report saved for review'}
