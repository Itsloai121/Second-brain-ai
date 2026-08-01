from .calculations import available,average_daily_demand,days_of_cover,reorder_point,eoq

def build_recommendation(item:dict)->dict|None:
    demand=average_daily_demand(item['history'][-28:]); net=available(item['on_hand'],item['allocated'])+item['in_transit']
    rop=reorder_point(item['history'][-56:],item['lead_days'],lead_std_days=item.get('lead_std',0))
    position=net
    if position<=rop:
        annual=demand*365; qty=max(item['moq'],eoq(annual,125,item['unit_cost']))
        return {'sku':item['sku'],'type':'reorder','priority':'critical' if days_of_cover(net,demand)<item['lead_days'] else 'high','quantity':qty,'rationale':{'inventory_position':position,'reorder_point':rop,'avg_daily_demand':round(demand,2),'days_of_cover':days_of_cover(net,demand),'lead_days':item['lead_days']}}
    if item['lead_days']>item.get('quoted_lead_days',item['lead_days'])*1.15:
        return {'sku':item['sku'],'type':'supplier_follow_up','priority':'medium','quantity':None,'rationale':{'actual_lead_days':item['lead_days'],'quoted_lead_days':item['quoted_lead_days']}}
    return None
