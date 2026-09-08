"""v36 bounded multi-window ranking adaptation; cloud CPU only."""
import csv,gzip,hashlib,io,json,math,statistics,subprocess,sys,time,urllib.request
from pathlib import Path
IDS=['mean','persistence','ridge_1','ridge_100','hist_boost','extra_trees']
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,x):Path(n).write_bytes(gzip.compress(json.dumps(x,allow_nan=False).encode(),mtime=0))
def rho(a,b):
 def ranks(v):return [1+sum(w<x for w in v)+(sum(w==x for w in v)-1)/2 for x in v]
 x,y=ranks(a),ranks(b)
 return None if len(set(x))==1 or len(set(y))==1 else statistics.correlation(x,y)
def run():
 import numpy as np,sklearn,platform,threadpoolctl
 from sklearn.pipeline import make_pipeline
 from sklearn.preprocessing import StandardScaler
 from sklearn.linear_model import Ridge
 from sklearn.ensemble import HistGradientBoostingRegressor,ExtraTreesRegressor
 state={'status':'failed','fits':0,'cash':0,'source_sha256':sha(Path(__file__).read_bytes())};start=time.monotonic()
 try:
  assert [platform.python_version(),np.__version__,sklearn.__version__,threadpoolctl.__version__]==['3.12.13','2.0.2','1.6.1','3.6.0']
  url='https://raw.githubusercontent.com/vcerqueira/model_selection_forecasting/f7059325eaf6d9e20d04d5e9c02472ecd82f46d4/assets/datasets.rdata'
  with urllib.request.urlopen(url,timeout=40) as r:b=r.read(1048577)
  assert sha(b)=='76b10e5b7f60e0d2b314ddd6d8cc9e1cc943cc0146eadd155f7819af7170e4ea';Path('datasets.rdata').write_bytes(b)
  chosen=sorted(range(1,175),key=lambda i:sha(f'v36:{i}'.encode()))[:5];assert chosen==[109,95,21,59,117]
  code='load("datasets.rdata");for(i in c(109,95,21,59,117))write.table(data.frame(id=i,t=seq_along(ts_list[[i]]),y=as.numeric(ts_list[[i]])),file=paste0("series_",i,".csv"),sep=",",row.names=FALSE)'
  subprocess.run(['Rscript','--vanilla','-e',code],check=True,timeout=40,capture_output=True)
  series=[]
  for i in chosen:
   raw=list(csv.DictReader(Path(f'series_{i}.csv').open()));values=np.array([float(r['y']) for r in raw]);assert np.isfinite(values).all()
   x=np.array([values[t-8:t][::-1] for t in range(8,len(values))]);y=values[8:];n=int(.7*len(y));v=float(np.var(y[:n]));assert n>=100 and len(y)-n>=40 and v>0
   ordered=list(range(n));random=sorted(ordered,key=lambda t:sha(f'v36:{i}:{t}'.encode()));plans={}
   for s,order in [('time',ordered),('random',random)]:
    blocks=[order[j*n//5:(j+1)*n//5] for j in range(5)];plans[s]=[(sum(blocks[:j],[]),blocks[j]) for j in range(1,5)]
    assert all(len(a)>=20 and len(b)>=20 for a,b in plans[s])
   series.append((i,x,y,n,v,plans))
  save('coverage.json.gz',[{'id':i,'train':n,'future':len(y)-n,'variance':v} for i,x,y,n,v,p in series])
  arrays=[];locks=[];banks=[]
  def fit(name,x,y,ix):
   if name=='persistence':return None
   state['fits']+=1;save('progress.json.gz',state)
   if name=='mean':return float(np.mean(y[ix]))
   if name.startswith('ridge'):m=make_pipeline(StandardScaler(),Ridge(alpha=100 if name.endswith('100') else 1,solver='svd'))
   elif name=='hist_boost':m=HistGradientBoostingRegressor(max_iter=300,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=5,l2_regularization=1,early_stopping=False,categorical_features=None,random_state=101)
   else:m=ExtraTreesRegressor(n_estimators=300,min_samples_leaf=3,n_jobs=2,random_state=101)
   return m.fit(x[ix],y[ix])
  def predict(name,m,x,ix):return x[ix,0] if name=='persistence' else np.full(len(ix),m) if name=='mean' else m.predict(x[ix])
  with threadpoolctl.threadpool_limits(limits=2):
   for i,x,y,n,v,plans in series:
    losses={}
    for s,folds in plans.items():
     total={name:0. for name in IDS};count=0
     for j,(tr,va) in enumerate(folds):
      pred={name:predict(name,fit(name,x,y,tr),x,va).tolist() for name in IDS}
      for name in IDS:total[name]+=float(np.sum((y[va]-pred[name])**2))
      count+=len(va);arrays.append({'id':i,'strategy':s,'fold':j,'train':tr,'validation':va,'y':y[va].tolist(),'predictions':pred})
     losses[s]={k:value/count for k,value in total.items()}
    locks.append({'id':i,'variance':v,'validation':losses,'choices':{s:min(IDS,key=ls.__getitem__) for s,ls in losses.items()}})
    banks.append({name:fit(name,x,y,list(range(n))) for name in IDS})
   assert state['fits']==225;save('selection_lock.json.gz',locks);save('validation.json.gz',arrays)
   reports=[];outer=[]
   for (i,x,y,n,v,p),bank,lock in zip(series,banks,locks):
    ix=list(range(n,len(y)));pred={name:predict(name,bank[name],x,ix).tolist() for name in IDS};ls={name:float(np.mean((y[ix]-pred[name])**2)) for name in IDS};corr={s:rho([lock['validation'][s][name] for name in IDS],[ls[name] for name in IDS]) for s in p}
    D=None if None in corr.values() else corr['time']-corr['random'];E=(ls[lock['choices']['random']]-ls[lock['choices']['time']])/v
    reports.append(dict(lock,future_mse=ls,rho=corr,D=D,E=E));outer.append({'id':i,'y':y[ix].tolist(),'predictions':pred})
   save('reports.json.gz',reports);save('outer.json.gz',outer);ds=[r['D'] for r in reports];state.update(status='pilot_complete_not_family_validity',D=ds,E=[r['E'] for r in reports],screen_pass=None not in ds and sum(d>0 for d in ds)>=4 and statistics.median(ds)>=.20)
 except Exception as e:state.update(error_type=type(e).__name__,error=str(e)[:300])
 state['seconds']=time.monotonic()-start;save('summary.json.gz',state);print(json.dumps(state))
if __name__=='__main__':
 if '--child' in sys.argv:run()
 else:
  try:subprocess.run([sys.executable,__file__,'--child'],timeout=540,check=True)
  except Exception as e:save('summary.json.gz',{'status':'failed','error_type':type(e).__name__,'cash':0,'source_sha256':sha(Path(__file__).read_bytes())})
