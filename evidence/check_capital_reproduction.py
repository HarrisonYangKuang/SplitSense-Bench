"""Recompare saved independent-run losses; no fitting or network."""
from pathlib import Path
import json,math,hashlib,statistics
ROOT=Path(__file__).resolve().parents[1]
NAMES=['mean','ridge_calendar','ridge_trend','ridge_trend_100','hist_boost','extra_trees']
def main():
 new=json.loads((ROOT/'evidence/capital_reproduction.json').read_text())
 old=[r for r in json.loads((ROOT/'evidence/cases.json').read_text())['records'] if r['study']=='capital-v28']
 assert len(old)==len(new['reports'])==5
 assert hashlib.sha256((ROOT/'experiments/capital_independent_v33.py').read_bytes()).hexdigest()==new['source_sha256']
 diffs=[]
 def close(a,b):
  assert math.isfinite(a) and math.isfinite(b)
  assert math.isclose(a,b,abs_tol=new['comparison']['mse_atol'],rel_tol=new['comparison']['mse_rtol'])
 for a,b in zip(old,new['reports']):
  assert str(b['block'])==str(a['instance']).split(':')[-1]
  assert a['choices']==b['choices']
  for s in ('random','time'):
   assert len(b['validation'][s])==6 and set(a['validation_mse'][s])==set(NAMES)
   for n,v in zip(NAMES,b['validation'][s]):
    close(a['validation_mse'][s][n],v);diffs.append(abs(a['validation_mse'][s][n]-v))
  assert set(a['future_mse'])==set(b['future_mse'])==set(NAMES)
  for n in NAMES:
   close(a['future_mse'][n],b['future_mse'][n]);diffs.append(abs(a['future_mse'][n]-b['future_mse'][n]))
  for k,target in [('variance','variance'),('reported_E','E'),('reported_D','D')]:close(a[k],b[target])
 ds=[r['D'] for r in new['reports']]
 gate=sum(d>0 for d in ds)>=4 and statistics.median(ds)>=.20
 assert new['screen_pass']==gate==False and len(diffs)==90
 print(json.dumps({'saved_loss_comparison':'pass','mse_count':90,'max_absolute_difference':max(diffs),'research_gate_pass':gate,'new_fits':0}))
if __name__=='__main__':main()
