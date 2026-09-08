"""Independent public saved-prediction audit; standard library, no fitting."""
import gzip,hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NAMES=['mean','delayed_persistence','seasonal_144','ridge_1','ridge_100','hist_boost','extra_trees']
def main():
 s=json.loads((ROOT/'appliances_v38_results.json').read_text());folder=ROOT/'appliances_v38'
 raw=(folder/'predictions.json.gz').read_bytes();coverage=(folder/'coverage.json').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==s['raw_sha256'] and hashlib.sha256(coverage).hexdigest()==s['coverage_sha256']
 data=json.loads(gzip.decompress(raw));plans=json.loads(coverage);locks=json.loads((folder/'choice_lock.json').read_text())
 assert len(data)==len(plans)==len(locks)==len(s['reports'])==5
 checked=0
 def mse(p,t):
  assert len(p)==len(t)>0 and all(math.isfinite(x) for x in p+t)
  return statistics.mean((x-y)**2 for x,y in zip(p,t))
 def close(x,y):assert math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-8),(x,y)
 for i,(d,p,l,r) in enumerate(zip(data,plans,locks,s['reports'])):
  assert d['episode']==p['episode']==l['episode']==r['episode']==i
  assert d['choices']==l['choices']==r['choices'] and len(p['future'])==len(d['future_target'])==1008
  assert len(p['pool'])==2015 and max(p['pool'])==min(p['future'])-2
  for strategy in ['random','forward']:
   split=p['splits'][strategy];v=d['validation'][strategy]
   assert len(split['fit'])==1726 and len(split['val'])==len(v['target'])==288
   assert not set(split['fit'])&set(split['val'])
   if strategy=='forward':assert max(split['fit'])==min(split['val'])-2 and split['lag_overlap_entries']==0
   for n in NAMES:
    close(mse(v['predictions'][n],v['target']),r['validation_mse'][strategy][n]);checked+=1
    close(mse(d['retained'][strategy][n],d['future_target']),r['retained_mse'][strategy][n]);checked+=1
   assert min(NAMES,key=lambda n:r['validation_mse'][strategy][n])==r['choices'][strategy]
  for n in NAMES:close(mse(d['common'][n],d['future_target']),r['future_mse'][n]);checked+=1
 assert checked==175
 print(json.dumps({'public_prediction_audit':'pass','losses':checked,'episodes':5,'scope':'saved predictions and index contracts; no retraining or Agent claims'}))
if __name__=='__main__':main()
