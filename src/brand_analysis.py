"""Fixed-sample exploratory panel backtest; see docs/BRAND_PROTOCOL.md."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/processed'
MAPPING={'比亚迪':('byd','BYD','比亚迪'),'特斯拉中国':('tesla','Tesla China','特斯拉'),'小米汽车':('xiaomi','Xiaomi','小米汽车'),'理想汽车':('li','Li Auto','理想'),'蔚来汽车':('nio','NIO','蔚来'),'零跑汽车':('leapmotor','Leapmotor','零跑')}
def prepare():
 s=pd.read_csv(OUT/'manufacturer_wholesale_monthly.csv',parse_dates=['month'])
 a=pd.read_csv(OUT/'attention_monthly_long.csv',parse_dates=['available_month'])
 rows=[]
 for manufacturer,(bid,name,kw) in MAPPING.items():
  d=s[s.manufacturer.eq(manufacturer)].copy().sort_values('month')
  q=a[a.keyword.eq(kw)][['available_month','attention']].rename(columns={'available_month':'month'})
  d=d.merge(q,on='month',validate='one_to_one');d['brand_id']=bid;d['brand']=name;d['keyword']=kw
  if len(d)!=20 or not (d.nev_wholesale_units.gt(0)&d.attention.gt(0)).all():raise ValueError(f'Incomplete candidate: {name}')
  rows.append(d)
 p=pd.concat(rows).sort_values(['brand_id','month'])
 p['sales_growth']=p.groupby('brand_id').nev_wholesale_units.transform(lambda x:np.log(x).diff()*100)
 p['search_growth']=p.groupby('brand_id').attention.transform(lambda x:np.log(x).diff()*100)
 for k in ['sales','search']:p[k+'_relative']=p[k+'_growth']-p.groupby('month')[k+'_growth'].transform('mean')
 for lag in [1,2]:
  for k in ['sales','search']:p[f'{k}_lag{lag}']=p.groupby('brand_id')[k+'_relative'].shift(lag)
 return p

def backtest(p,lag=1,dates=None):
 d=p.dropna(subset=['sales_relative',f'sales_lag{lag}',f'search_lag{lag}']).copy()
 months=sorted(d.month.unique());dates=months[10:] if dates is None else dates
 out=[]
 for date in dates:
  date=pd.Timestamp(date);cutoff=date-pd.DateOffset(months=lag-1)
  train=d[d.month.lt(cutoff)];test=d[d.month.eq(date)]
  assert train.month.max()<date
  y=train.sales_relative.to_numpy()
  pred={'Relative zero':np.zeros(len(test)),'Repeat relative change':test[f'sales_lag{lag}'].to_numpy(),'Historical brand mean':test.brand_id.map(train.groupby('brand_id').sales_relative.mean()).to_numpy()}
  for name,cols in [('History only',[f'sales_lag{lag}']),('History + search',[f'sales_lag{lag}',f'search_lag{lag}'])]:
   x=train[cols].to_numpy();mu=x.mean(0);sd=x.std(0);sd[sd==0]=1
   coef=np.linalg.lstsq(np.column_stack([np.ones(len(x)),(x-mu)/sd]),y,rcond=None)[0]
   pred[name]=np.column_stack([np.ones(len(test)),(test[cols].to_numpy()-mu)/sd])@coef
  for name,values in pred.items():
   for (_,r),v in zip(test.iterrows(),values):out.append(dict(month=date,brand_id=r.brand_id,brand=r.brand,model=name,actual=r.sales_relative,predicted=v,train_end=train.month.max(),feature_month=date-pd.DateOffset(months=lag),n_train=len(train)))
 return pd.DataFrame(out)
def metrics(r,by=['model']):
 rows=[]
 for key,g in r.groupby(by):
  key=(key,) if not isinstance(key,tuple) else key
  e=g.predicted-g.actual;call=g.predicted.abs()>1e-12
  rows.append(dict(zip(by,key),n=len(g),mae=float(e.abs().mean()),rmse=float(np.sqrt((e**2).mean())),direction_accuracy=float((np.sign(g.predicted[call])==np.sign(g.actual[call])).mean()) if call.any() else None,call_coverage=float(call.mean())))
 return pd.DataFrame(rows)
def main():
 p=prepare();r=backtest(p);m=metrics(r);b=metrics(r,['brand_id','model']);delay=backtest(p,2,sorted(r.month.unique()))
 h=m.set_index('model').loc['History only','mae'];s=m.set_index('model').loc['History + search','mae'];wide=b.pivot(index='brand_id',columns='model',values='mae');wins=int((wide['History + search']<wide['History only']).sum());gain=float(1-s/h)
 summary=dict(sample_brands=6,test_months=int(r.month.nunique()),test_observations=int(len(r)/5),start=str(r.month.min().date()),end=str(r.month.max().date()),relative_mae_gain=gain,brands_improved=wins,passes_gate=bool(gain>=.05 and wins>=4),unit='log percentage points',scope='NEV wholesale; exports included',exploratory=True)
 for name,df in [('brand_panel_final',p),('brand_predictions_final',r),('brand_metrics_final',m),('brand_metrics_by_brand',b),('brand_predictions_delayed',delay),('brand_metrics_delayed',metrics(delay))]:df.to_csv(OUT/(name+'.csv'),index=False)
 (OUT/'brand_summary_final.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary));print(m.to_string(index=False))
if __name__=='__main__':main()
