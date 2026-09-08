"""Post-hoc candidate-menu decomposition from saved losses, not new fits."""
from pathlib import Path
import json,statistics,math
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((ROOT/'evidence/legacy_cases.json').read_text())
 v=json.loads((ROOT/'evidence/legacy_validation_losses.json').read_text())['records']
 key=lambda r:(r['seed_group'],r['seed'],r['task_id'])
 indexed={key(r):r for r in v}
 assert len(indexed)==len(v)==len(d['records'])==40
 base=d['candidate_libraries']['original_five'];full=d['candidate_libraries']['augmented_nine']
 extras=[n for n in full if n not in base]
 menus={'original_five':base,**{'add_'+n:base+[n] for n in extras},'augmented_nine':full}
 out=[]
 for label,menu in menus.items():
  groups={}
  for r in d['records']:
   loss=indexed[key(r)]['validation_mse'];u=r['libraries']['augmented_nine']['candidate_utilities']
   assert all(math.isfinite(x) for s in loss.values() for x in s.values())
   chosen={s:min(menu,key=lambda n:loss[s][n]) for s in ('random','aligned')}
   if label in r['libraries']:
    assert all(chosen[s]==r['libraries'][label][s+'_candidate'] for s in chosen)
   effect=(u[chosen['aligned']]-u[chosen['random']])/r['train_target_variance']
   if r['task_id'] in ('temporal_future','entity_unseen'):
    groups.setdefault((r['seed_group'],r['task_id']),[]).append((effect,chosen['random']==chosen['aligned']))
  for (group,task),vals in sorted(groups.items()):
   assert len(vals)==5
   out.append({'menu':label,'group':group,'task':task,'n':5,'effect_above_0_05':sum(e>.05 for e,s in vals),'median_effect':statistics.median(e for e,s in vals),'same_selection':sum(s for e,s in vals)})
 print(json.dumps({'scope':'post-hoc fixed-score menu restriction; no new-data or Agent claim; not full validity gate','results':out},indent=2))
if __name__=='__main__':main()
