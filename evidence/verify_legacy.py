"""Verify all 40 development instances under both original candidate libraries."""
import csv,io,json,math
from pathlib import Path

def render(doc):
 records=doc['records'];assert len(records)==40
 indexed={(r['seed_group'],r['task_id'],r['seed']):r for r in records};assert len(indexed)==40
 out=io.StringIO(newline='');w=csv.writer(out);w.writerow(['seed_group','task','seed','candidate_library','random_choice','aligned_choice','E'])
 for r in records:
  v=r['train_target_variance'];assert v>0
  for lib,data in r['libraries'].items():
   u=data['candidate_utilities'];assert set(u)==set(doc['candidate_libraries'][lib])
   assert all(math.isfinite(a) for a in u.values())
   difference=u[data['aligned_candidate']]-u[data['random_candidate']];e=difference/v
   assert math.isclose(difference,data['aligned_minus_random'],abs_tol=1e-10)
   assert math.isclose(e,data['relative_effect'],abs_tol=1e-10)
   assert math.isclose(u[data['hidden_best']],max(u.values()),abs_tol=1e-10)
   w.writerow([r['seed_group'],r['task_id'],r['seed'],lib,data['random_candidate'],data['aligned_candidate'],e])
 for group,seeds in doc['seed_groups'].items():
  for lib in doc['candidate_libraries']:
   for family,easy,hard in [('temporal','temporal_iid','temporal_future'),('entity','entity_seen','entity_unseen')]:
    effect=ranking=0
    for seed in seeds:
     a,b=indexed[group,easy,seed],indexed[group,hard,seed];assert a['train_sha256']==b['train_sha256']
     left,right=a['libraries'][lib],b['libraries'][lib]
     effect+=right['relative_effect']>doc['threshold'];ranking+=left['hidden_best']!=right['hidden_best']
    expected=doc['reported_gates'][group][lib][family]
    assert effect==expected['effect_passes'] and ranking==expected['ranking_passes']
    assert (effect>=doc['required_passes'] and ranking>=doc['required_passes'])==expected['pass']
 return out.getvalue()
if __name__=='__main__':
 root=Path(__file__).resolve().parent;doc=json.loads((root/'legacy_cases.json').read_text());result=render(doc)
 assert result.encode()==(root/'legacy_results.csv').read_bytes()
 print('PASS: 40 instances, both candidate libraries, 80 effects and eight group-family-library gates; no Agent capability conclusion')
