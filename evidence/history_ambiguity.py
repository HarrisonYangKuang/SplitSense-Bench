"""Post-hoc finite-library ambiguity bound from frozen v26 results; no fitting."""
from pathlib import Path
import csv,gzip,hashlib,json,math
ROOT=Path(__file__).resolve().parents[1]
def main():
 records=json.loads((ROOT/'evidence/cases.json').read_text())['records'];rows=[]
 records=[dict(r,case=r['instance'].split(':')[0],seed=int(r['instance'].split(':')[1]),future_best=min(r['future_mse'],key=r['future_mse'].get)) for r in records if r['study']=='synthetic-v26']
 assert len(records)==20 and len({(r['case'],r['seed']) for r in records})==20
 for seed in range(201,206):
  pair=[next(r for r in records if r['case']==case and r['seed']==seed) for case in ('decrease','return')]
  a,b=pair;assert a['choices']==b['choices'] and a['validation_mse']==b['validation_mse']
  assert math.isclose(a['variance'],b['variance'],abs_tol=1e-12)
  names=sorted(a['future_mse']);assert names==sorted(b['future_mse'])
  regrets=[[ (r['future_mse'][n]-min(r['future_mse'].values()))/r['variance'] for n in names] for r in pair]
  candidates=[]
  for i,n in enumerate(names):candidates.append((max(regrets[0][i],regrets[1][i]),n,n,1.))
  deterministic=min(candidates)
  # A two-world linear program optimum uses at most two library candidates.
  # Include vertices and every pair's equal-risk intersection.
  for i in range(len(names)):
   for j in range(i+1,len(names)):
    di=regrets[0][i]-regrets[1][i];dj=regrets[0][j]-regrets[1][j]
    if di==dj:continue
    p=-dj/(di-dj)
    if 0<=p<=1:
     risks=[p*v[i]+(1-p)*v[j] for v in regrets]
     candidates.append((max(risks),names[i],names[j],p))
  best=min(candidates)
  rows.append({'seed':seed,'decrease_best':a['future_best'],'return_best':b['future_best'],'deterministic_minimax_regret':deterministic[0],'randomized_minimax_regret':best[0],'mix_first':best[1],'mix_second':best[2],'probability_first':best[3]})
 import io
 out=io.StringIO(newline='')
 w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 expected=(ROOT/'evidence/history_ambiguity.csv').read_bytes()
 assert out.getvalue().encode()==expected, 'published ambiguity table differs from recomputation'
 print('PASS: five paired finite-library ambiguity calculations; conditional post-hoc result, not Agent scores')
if __name__=='__main__':main()
