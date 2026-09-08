"""Independent orchestration of the frozen v28 protocol; cloud CPU only.
Does not import original pilot, partitions, choices, or scores.
"""
import io,csv,json,gzip,hashlib,urllib.request,zipfile,statistics,time,math,platform
import sklearn,threadpoolctl
from datetime import date
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
NAMES=['mean','ridge_calendar','ridge_trend','ridge_trend_100','hist_boost','extra_trees']
def sha(b):return hashlib.sha256(b).hexdigest()
def rank(v):
 order=sorted(range(len(v)),key=lambda i:v[i]);r=[0.]*len(v);start=0
 while start<len(v):
  end=start+1
  while end<len(v) and v[order[end]]==v[order[start]]:end+=1
  for i in order[start:end]:r[i]=(start+1+end)/2
  start=end
 return r
def correlation(a,b):
 x,y=np.asarray(rank(a)),np.asarray(rank(b));x=x-x.mean();y=y-y.mean()
 den=np.linalg.norm(x)*np.linalg.norm(y)
 return None if den==0 else float(np.dot(x,y)/den)
def run():
 start=time.monotonic()
 versions={"python":platform.python_version(),"numpy":np.__version__,"sklearn":sklearn.__version__,"threadpoolctl":threadpoolctl.__version__}
 assert versions=={"python":"3.12.13","numpy":"2.0.2","sklearn":"1.6.1","threadpoolctl":"3.6.0"},versions
 url='https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip'
 with urllib.request.urlopen(url,timeout=45) as r:b=r.read(1048577)
 assert len(b)<=1048576 and sha(b)=='b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401'
 raw=zipfile.ZipFile(io.BytesIO(b)).read('day.csv');assert sha(raw)=='a6bcf826782d3c0fbfdcbeead17cd0884185a0dafe8ff10cd48a874ee7ba18be'
 rows=list(csv.DictReader(io.StringIO(raw.decode())));ds=[date.fromisoformat(r['dteday']) for r in rows]
 assert len(rows)==731 and all((d-ds[0]).days==i for i,d in enumerate(ds))
 y=np.array([math.log1p(int(r['cnt'])) for r in rows]);calendar=np.array([[float(d.weekday()==w) for w in range(7)]+[float(d.month==m) for m in range(1,13)] for d in ds]);t=np.arange(731,dtype=float)
 trees=np.array([[d.weekday(),d.month,i] for i,d in enumerate(ds)])
 fits=0;plans=[];final=[]
 def train(name,ix):
  nonlocal fits
  fits+=1
  if name=='mean':return float(np.mean(y[ix]))
  if name.startswith('ridge'):
   c=float(np.mean(t[ix]));s=float(np.std(t[ix])) or 1.;x=calendar if name=='ridge_calendar' else np.column_stack((calendar,(t-c)/s));m=Ridge(alpha=100 if name.endswith('100') else 10,solver='svd');m.fit(x[ix],y[ix]);return m,x
  x=trees
  if name=='hist_boost':m=HistGradientBoostingRegressor(max_iter=300,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=5,l2_regularization=1,early_stopping=False,categorical_features=None,random_state=101)
  else:m=ExtraTreesRegressor(n_estimators=300,min_samples_leaf=3,n_jobs=2,random_state=101)
  m.fit(x[ix],y[ix]);return m,x
 def predict(name,m,ix):return np.full(len(ix),m) if name=='mean' else np.maximum(0,m[0].predict(m[1][ix]))
 with threadpool_limits(limits=2):
  for k in range(5):
   training=list(range(120*k,120*k+100));v={'random':sorted(sorted(training,key=lambda i:sha(('capital-v28:'+ds[i].isoformat()).encode()))[:20]),'time':training[-20:]};loss={}
   for strategy,hold in v.items():
    fitting=[i for i in training if i not in set(hold)]
    loss[strategy]=[float(np.mean((y[hold]-predict(n,train(n,fitting),hold))**2)) for n in NAMES]
   plans.append({'block':k,'validation':loss,'choices':{s:NAMES[int(np.argmin(v))] for s,v in loss.items()},'variance':float(np.var(y[training]))});final.append({n:train(n,training) for n in NAMES})
  Path('independent_lock.json').write_text(json.dumps(plans));assert fits==90
  reports=[]
  for p,bank in zip(plans,final):
   ix=list(range(p['block']*120+100,p['block']*120+120));ls=[float(np.mean((y[ix]-predict(n,bank[n],ix))**2)) for n in NAMES];c={s:correlation(v,ls) for s,v in p['validation'].items()};a,b=[NAMES.index(p['choices'][s]) for s in ['random','time']]
   reports.append(dict(p,future_mse=dict(zip(NAMES,ls)),rho=c,D=None if None in c.values() else c['time']-c['random'],E=(ls[a]-ls[b])/p['variance']))
 values=[p['D'] for p in reports]
 out={'status':'independent_reproduction_complete','reports':reports,'fits':fits,'versions':versions,'seconds':time.monotonic()-start,'screen_pass':None not in values and sum(v>0 for v in values)>=4 and statistics.median(values)>=.20,'source_sha256':sha(Path(__file__).read_bytes())}
 Path('independent_results.json.gz').write_bytes(gzip.compress(json.dumps(out,allow_nan=False).encode(),mtime=0));print(json.dumps({k:v for k,v in out.items() if k!='reports'}))
if __name__=='__main__':run()
