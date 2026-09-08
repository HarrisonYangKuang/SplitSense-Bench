"""Reproduce published aggregate evidence, not model training or raw-prediction MSE."""
import csv,io,json,math,statistics
from pathlib import Path

def rank(v):return [1+sum(w<x for w in v)+(sum(w==x for w in v)-1)/2 for x in v]
def render(doc):
 rows=doc['records'];assert len(rows)==30
 assert len({(r['study'],r['instance']) for r in rows})==len(rows)
 assert {s:sum(r['study']==s for r in rows) for s in doc['sources']}=={'synthetic-v26':20,'capital-v28':5,'multiwindow-v36':5}
 out=io.StringIO(newline='');writer=csv.writer(out);writer.writerow(['study','instance','random_selected','time_selected','E','D_if_originally_reported'])
 for r in rows:
  ls=r['future_mse'];v=r['variance'];a,b=r['choices']['random'],r['choices']['time'];assert v>0
  assert all(math.isfinite(x) and x>=0 for x in ls.values())
  e=(ls[a]-ls[b])/v;assert math.isclose(e,r['reported_E'],abs_tol=1e-12,rel_tol=1e-10)
  d=''
  if r['reported_D'] is not None:
   names=sorted(ls);actual=rank([ls[n] for n in names]);corr={s:statistics.correlation(rank([r['validation_mse'][s][n] for n in names]),actual) for s in ['random','time']}
   d=corr['time']-corr['random'];assert math.isclose(d,r['reported_D'],abs_tol=1e-12)
  writer.writerow([r['study'],r['instance'],a,b,e,d])
 return out.getvalue()
if __name__=='__main__':
 root=Path(__file__).resolve().parent;doc=json.loads((root/'cases.json').read_text());actual=render(doc)
 assert actual.encode()==(root/'results.csv').read_bytes(),'Published table mismatch'
 print('PASS: 30 E values and 10 originally reported ranking differences; no pooled scientific conclusion')
