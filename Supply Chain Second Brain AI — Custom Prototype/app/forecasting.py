from .calculations import average_daily_demand

def forecast_daily(history:list[dict],horizon:int=30)->dict:
    if not history:return {'daily':[],'total':0,'method':'no-history','confidence':'low'}
    vals=[float(x['units']) for x in history]
    recent=vals[-28:] or vals
    base=average_daily_demand(recent)
    older=average_daily_demand(vals[-56:-28]) if len(vals)>=56 else base
    trend=max(-.25,min(.25,(base-older)/max(older,1)))
    weekday={i:[] for i in range(7)}
    for x in history[-84:]: weekday[x['date'].weekday()].append(float(x['units']))
    factors={k:(average_daily_demand(v)/base if v and base else 1) for k,v in weekday.items()}
    last=history[-1]['date']; daily=[]
    from datetime import timedelta
    for h in range(1,horizon+1):
        day=last+timedelta(days=h); y=max(0,base*(1+trend*h/28)*factors.get(day.weekday(),1))
        daily.append({'date':day.isoformat(),'units':round(y)})
    return {'daily':daily,'total':sum(x['units'] for x in daily),'method':'28-day trend + weekday seasonality','confidence':'medium' if len(vals)>=56 else 'low'}
