from math import sqrt

def available(on_hand:int, allocated:int)->int: return max(0,on_hand-allocated)
def average_daily_demand(units:list[int])->float: return sum(units)/len(units) if units else 0.0
def demand_std(units:list[int])->float:
    if len(units)<2:return 0.0
    avg=average_daily_demand(units); return sqrt(sum((x-avg)**2 for x in units)/(len(units)-1))
def safety_stock(units:list[int],lead_days:float,service_z:float=1.65,lead_std_days:float=0)->int:
    avg=average_daily_demand(units); sigma=demand_std(units)
    return round(service_z*sqrt(max(0,lead_days*sigma*sigma + avg*avg*lead_std_days*lead_std_days)))
def reorder_point(units:list[int],lead_days:float,service_z:float=1.65,lead_std_days:float=0)->int:
    return round(average_daily_demand(units)*lead_days)+safety_stock(units,lead_days,service_z,lead_std_days)
def eoq(annual_demand:float,order_cost:float,unit_cost:float,holding_rate:float=.25)->int:
    annual_demand=float(annual_demand); order_cost=float(order_cost)
    unit_cost=float(unit_cost); holding_rate=float(holding_rate)
    if annual_demand<=0 or unit_cost<=0 or holding_rate<=0:return 0
    return round(sqrt(2*annual_demand*order_cost/(unit_cost*holding_rate)))
def days_of_cover(net_inventory:int,avg_daily:float)->float:
    return round(net_inventory/avg_daily,1) if avg_daily>0 else 999.0
