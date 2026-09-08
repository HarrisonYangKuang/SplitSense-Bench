"""v28 frozen-ranking pilot; private cloud only."""
import csv,gzip,hashlib,io,json,math,os,statistics,time,urllib.request,zipfile
from datetime import date
from pathlib import Path
IDS=('mean','ridge_calendar','ridge_trend','ridge_trend_100','hist_boost','extra_trees')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,obj):
    b=json.dumps(obj,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
    Path(name+'.tmp').write_bytes(gzip.compress(b,mtime=0));os.replace(name+'.tmp',name)
    return sha(b)
def mse(y,p):return statistics.mean((a-b)**2 for a,b in zip(y,p))
def rho(a,b):
    def ranks(v):return [1+sum(w<x for w in v)+(sum(w==x for w in v)-1)/2 for x in v]
    u,v=ranks(a),ranks(b)
    if len(set(u))==1 or len(set(v))==1:return None
    return statistics.correlation(u,v)
def estimator(n):
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import HistGradientBoostingRegressor,ExtraTreesRegressor
    if n=='mean':return DummyRegressor()
    if n.startswith('ridge'):return Ridge(alpha=100. if n.endswith('100') else 10.,solver='svd')
    if n=='hist_boost':return HistGradientBoostingRegressor(max_iter=300,learning_rate=.05,max_leaf_nodes=15,min_samples_leaf=5,l2_regularization=1.,early_stopping=False,categorical_features=None,random_state=101)
    return ExtraTreesRegressor(n_estimators=300,min_samples_leaf=3,n_jobs=2,random_state=101)
def run():
    import numpy as np,sklearn,threadpoolctl,platform
    start=time.monotonic();state={'status':'failed','fits':0,'cash':0,'source_sha256':sha(Path(__file__).read_bytes())};records=[]
    try:
        versions=[platform.python_version(),np.__version__,sklearn.__version__,threadpoolctl.__version__]
        assert versions==['3.12.13','2.0.2','1.6.1','3.6.0']
        state['versions']=versions
        save('parameters.json.gz',{n:estimator(n).get_params() for n in IDS})
        with urllib.request.urlopen('https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip',timeout=40) as f:b=f.read(1048577)
        assert len(b)<=1048576 and sha(b)=='b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401'
        Path('source.zip').write_bytes(b)
        with zipfile.ZipFile(io.BytesIO(b)) as z:raw=z.read('day.csv')
        assert sha(raw)=='a6bcf826782d3c0fbfdcbeead17cd0884185a0dafe8ff10cd48a874ee7ba18be'
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));assert len(rows)==731
        days=[date.fromisoformat(r['dteday']) for r in rows]
        plans=[];banks=[];arrays=[]
        def labels(ix):return [math.log1p(int(rows[i]['cnt'])) for i in ix]
        def transform(n,ix,center,scale):
            if n in ('hist_boost','extra_trees'):return [[days[i].weekday(),days[i].month,(days[i]-days[0]).days] for i in ix]
            out=[]
            for i in ix:
                d=days[i];v=[float(j==d.weekday()) for j in range(7)]+[float(j==d.month) for j in range(1,13)]
                if n.startswith('ridge_trend'):v.append(((d-days[0]).days-center)/scale)
                out.append(v)
            return out
        def fit(n,ix,block,phase):
            state.update(block=block,phase=phase,model=n);save('progress.json.gz',state)
            t=[(days[i]-days[0]).days for i in ix];center=statistics.mean(t);scale=statistics.pstdev(t) or 1.
            model=estimator(n);model.fit(transform(n,ix,center,scale),labels(ix))
            records.append({'block':block,'phase':phase,'model':n,'indices':ix});state['fits']=len(records);save('fits.json.gz',records)
            return model,center,scale
        def predict(n,model,ix):
            m,c,s=model;p=np.maximum(0.,m.predict(transform(n,ix,c,s)))
            assert np.isfinite(p).all();return p.tolist()
        with threadpoolctl.threadpool_limits(limits=2):
            for block in range(5):
                train=list(range(block*120,block*120+100));random=sorted(train,key=lambda i:sha(('capital-v28:'+str(days[i])).encode()))[:20]
                val={'random':sorted(random),'time':train[-20:]};plan={'block':block,'validation':{},'choices':{},'variance':statistics.pvariance(labels(train)),'train':train}
                assert plan['variance']>0
                for strategy,vi in val.items():
                    fi=[i for i in train if i not in vi];pred={}
                    for n in IDS:pred[n]=predict(n,fit(n,fi,block,strategy),vi)
                    losses={n:mse(labels(vi),pred[n]) for n in IDS};plan['validation'][strategy]=losses;plan['choices'][strategy]=min(IDS,key=losses.__getitem__)
                    arrays.append({'block':block,'phase':strategy,'indices':vi,'y':labels(vi),'predictions':pred});save('validation.json.gz',arrays)
                plans.append(plan);banks.append({n:fit(n,train,block,'final') for n in IDS})
            assert state['fits']==90
            state['lock_sha256']=save('selection_lock.json.gz',plans)
            reports=[];outer=[]
            for plan,bank in zip(plans,banks):
                ix=list(range(plan['block']*120+100,plan['block']*120+120));y=labels(ix);pred={n:predict(n,bank[n],ix) for n in IDS};ls={n:mse(y,pred[n]) for n in IDS}
                correlations={s:rho([plan['validation'][s][n] for n in IDS],[ls[n] for n in IDS]) for s in ('random','time')}
                a,t=(plan['choices'][s] for s in ('random','time'));v=plan['variance'];best=min(ls.values())
                reports.append(dict(plan,future_mse=ls,rho=correlations,D=None if None in correlations.values() else correlations['time']-correlations['random'],E=(ls[a]-ls[t])/v,regret={s:(ls[n]-best)/v for s,n in plan['choices'].items()},near_hit={s:ls[n]<=best+.01*v for s,n in plan['choices'].items()}))
                outer.append({'block':plan['block'],'indices':ix,'y':y,'predictions':pred});save('outer.json.gz',outer);state['reports_sha256']=save('reports.json.gz',reports)
            ds=[r['D'] for r in reports];state.update(status='pilot_complete_not_family_validity',D=ds,screen_pass=None not in ds and sum(d>0 for d in ds)>=4 and statistics.median(ds)>=.20)
    except Exception as e:state['error_type']=type(e).__name__
    state['seconds']=time.monotonic()-start;save('summary.json.gz',state);print(json.dumps(state))
if __name__=='__main__':
    import subprocess,sys
    if '--child' in sys.argv:run()
    else:
        reason=None
        try:
            p=subprocess.run([sys.executable,__file__,'--child'],timeout=540)
            if p.returncode:reason='child_exit'
        except subprocess.TimeoutExpired:reason='timeout'
        if reason or not Path('summary.json.gz').exists():
            state={'status':'failed','fits':0,'cash':0,'source_sha256':sha(Path(__file__).read_bytes())}
            if Path('progress.json.gz').exists():state.update(json.loads(gzip.decompress(Path('progress.json.gz').read_bytes())))
            state.update(status='failed',reason=reason or 'missing_summary');save('summary.json.gz',state);print(json.dumps(state))
