"""v38 frozen-protocol pilot; private cloud CPU only."""
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='2'
import csv,gzip,hashlib,io,json,math,signal,statistics,time,urllib.request,sys
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
import sklearn,threadpoolctl
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor,ExtraTreesRegressor
NAMES=['mean','delayed_persistence','seasonal_144','ridge_1','ridge_100','hist_boost','extra_trees']
LAGS=[2,3,6,12,18,36,72,144,288,1008]
URL='https://raw.githubusercontent.com/LuisM78/Appliances-energy-prediction-data/e3e4c27a4ae2b41b21f84b4c9ac2d822d3d0ace1/energydata_complete.csv'
CSV_HASH='2820bf712ad0275cb18b85a05250926100d8e65ebb9f4d2d016ca91ea152a25d'
OUT=Path('/kaggle/working/appliances_v38')
def save(name,obj):
 text=json.dumps(obj,allow_nan=False,separators=(',',':')).encode()
 if name.endswith('.gz'):text=gzip.compress(text,mtime=0)
 (OUT/name).write_bytes(text)
 return hashlib.sha256(text).hexdigest()
def ranks(v):return [sum(x<z for x in v)+(sum(x==z for x in v)+1)/2 for z in v]
def rho(a,b):
 a=ranks(a);b=ranks(b);ma=statistics.mean(a);mb=statistics.mean(b)
 den=math.sqrt(sum((x-ma)**2 for x in a)*sum((x-mb)**2 for x in b))
 return sum((x-ma)*(y-mb) for x,y in zip(a,b))/den if den else None
def main():
 OUT.mkdir(exist_ok=False);signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.alarm(300)
 t0=time.monotonic();summary={'status':'started','fits':0,'cash':0,'reports':[]}
 try:
  versions={'python':sys.version.split()[0],'numpy':np.__version__,'sklearn':sklearn.__version__,'threadpoolctl':threadpoolctl.__version__}
  assert versions=={'python':'3.12.13','numpy':'2.0.2','sklearn':'1.6.1','threadpoolctl':'3.6.0'},versions
  summary['versions']=versions;summary['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
  with urllib.request.urlopen(URL,timeout=45) as response:raw=response.read(16*1024*1024+1)
  assert len(raw)<=16*1024*1024 and hashlib.sha256(raw).hexdigest()==CSV_HASH
  (OUT/'source.csv').write_bytes(raw);rows=list(csv.DictReader(io.StringIO(raw.decode())))
  times=[datetime.strptime(r['date'],'%Y-%m-%d %H:%M:%S') for r in rows];y=np.array([float(r['Appliances']) for r in rows])
  assert len(rows)==19735 and np.isfinite(y).all() and all((b-a).total_seconds()==600 for a,b in zip(times,times[1:]))
  def features(idx):return y[np.array(idx)[:,None]-np.array(LAGS)[None,:]]
  # Deterministic ordinal check: no fit and no loss inspection.
  assert [1010-l for l in LAGS]==[1008,1007,1004,998,992,974,938,866,722,2]
  origin=datetime(2016,1,19);plans=[]
  for e in range(5):
   start=origin+timedelta(days=21*e);cut=start+timedelta(days=14);end=start+timedelta(days=21)
   pool=[i for i,t in enumerate(times) if start<=t<cut][:-1]
   future=[i for i,t in enumerate(times) if cut<=t<end]
   val=pool[-288:];fit=pool[:-289]
   order=sorted(pool,key=lambda i:hashlib.sha256(f'appliances-v38:{i}'.encode()).digest())
   splits={'forward':{'fit':fit,'val':val},'random':{'fit':sorted(order[289:]),'val':sorted(order[:288])}}
   assert len(pool)==2015 and len(future)==1008 and max(pool)==min(future)-2 and min(pool)>=max(LAGS)
   for s,d in splits.items():
    assert len(d['fit'])==1726 and len(d['val'])==288 and not set(d['fit'])&set(d['val'])
    validation=set(d['val']);d['lag_overlap_entries']=sum(i-l in validation for i in d['fit'] for l in LAGS)
   assert max(fit)==min(val)-2 and splits['forward']['lag_overlap_entries']==0
   plans.append({'episode':e,'pool':pool,'future':future,'splits':splits})
  summary['coverage_sha256']=save('coverage.json',plans)
  stored=[];locks=[]
  with threadpoolctl.threadpool_limits(limits=2):
   for plan in plans:
    e=plan['episode'];pool=plan['pool'];future=plan['future'];v=float(np.var(y[pool]));assert v>0
    def predict_set(fit,targets):
     models={'mean':None,'ridge_1':make_pipeline(StandardScaler(),Ridge(alpha=1)),'ridge_100':make_pipeline(StandardScaler(),Ridge(alpha=100)),
      'hist_boost':HistGradientBoostingRegressor(max_iter=200,max_leaf_nodes=15,learning_rate=.05,l2_regularization=1,early_stopping=False,random_state=3800+e),
      'extra_trees':ExtraTreesRegressor(n_estimators=200,min_samples_leaf=5,max_features=1.0,n_jobs=2,random_state=3800+e)}
     result={k:{} for k in targets};avg=float(y[fit].mean())
     for name,model in models.items():
      if model is not None:model.fit(features(fit),y[fit])
      summary['fits']+=1
      for key,idx in targets.items():result[key][name]=([avg]*len(idx) if model is None else model.predict(features(idx)).tolist())
     for key,idx in targets.items():
      result[key]['delayed_persistence']=y[np.array(idx)-2].tolist();result[key]['seasonal_144']=y[np.array(idx)-144].tolist()
     return result
    rec={'episode':e,'variance':v,'validation':{},'retained':{},'choices':{}}
    for s,d in plan['splits'].items():
     pred=predict_set(d['fit'],{'validation':d['val'],'future':future})
     loss={n:float(np.mean((np.array(pred['validation'][n])-y[d['val']])**2)) for n in NAMES}
     rec['validation'][s]={'target':y[d['val']].tolist(),'predictions':pred['validation'],'mse':loss}
     rec['retained'][s]=pred['future'];rec['choices'][s]=min(NAMES,key=lambda n:loss[n])
    locks.append({'episode':e,'choices':rec['choices']})
    save('choice_lock.json',locks) # Before deployment loss, persistent training-only decision.
    rec['common']=predict_set(pool,{'future':future})['future'];rec['future_target']=y[future].tolist();stored.append(rec)
  # All choices locked before any deployment losses are computed.
  summary['raw_sha256']=save('predictions.json.gz',stored)
  for rec in stored:
   target=np.array(rec['future_target']);future_mse={n:float(np.mean((np.array(rec['common'][n])-target)**2)) for n in NAMES}
   correlations={s:rho([rec['validation'][s]['mse'][n] for n in NAMES],[future_mse[n] for n in NAMES]) for s in ['random','forward']}
   assert all(x is not None for x in correlations.values()),'undefined ranking'
   choices=rec['choices'];retained={s:float(np.mean((np.array(rec['retained'][s][choices[s]])-target)**2)) for s in choices}
   summary['reports'].append({'episode':rec['episode'],'variance':rec['variance'],'choices':choices,'validation_mse':{s:rec['validation'][s]['mse'] for s in choices},'future_mse':future_mse,'rho':correlations,'D':correlations['forward']-correlations['random'],'E':(future_mse[choices['random']]-future_mse[choices['forward']])/rec['variance'],'retained_selected_mse':retained,'regret':{s:future_mse[choices[s]]-min(future_mse.values()) for s in choices},'optimism_gap':{s:future_mse[choices[s]]-rec['validation'][s]['mse'][choices[s]] for s in choices}})
  # Separate standard-library arithmetic from reloaded saved predictions.
  loaded=json.loads(gzip.decompress((OUT/'predictions.json.gz').read_bytes()));checked=0
  for rec,report in zip(loaded,summary['reports']):
   for s in ['random','forward']:
    for n in NAMES:
     err=statistics.mean((p-t)**2 for p,t in zip(rec['validation'][s]['predictions'][n],rec['validation'][s]['target']))
     assert math.isclose(err,report['validation_mse'][s][n],rel_tol=1e-10,abs_tol=1e-8);checked+=1
   for n in NAMES:
    err=statistics.mean((p-t)**2 for p,t in zip(rec['common'][n],rec['future_target']))
    assert math.isclose(err,report['future_mse'][n],rel_tol=1e-10,abs_tol=1e-8);checked+=1
  assert checked==105 and summary['fits']==75
  summary['saved_prediction_mse_checks']=checked
  ds=[r['D'] for r in summary['reports']];summary['screen_pass']=sum(d>0 for d in ds)>=4 and statistics.median(ds)>=.20
  summary['status']='complete';summary['scientific_validity_pass']=False
 except Exception as e:summary.update(status='failed',error_type=type(e).__name__,error=str(e))
 finally:
  summary['seconds']=time.monotonic()-t0;save('summary.json',summary);print(json.dumps(summary,allow_nan=False));signal.alarm(0)
if __name__=='__main__':main()
