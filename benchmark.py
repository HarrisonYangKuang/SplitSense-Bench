"""SplitSense development runner. Trusted evaluator only; not an Agent sandbox."""
import argparse,csv,json
from tasks import common,strong_candidates_v02 as library
from graders.metrics import grade_submission

def demo(task,seed):
 b=common.generate(task,seed);pred=library.candidate_predictions(b['train'],b['test']);scores={}
 for name,values in pred.items():
  submission=[{'row_id':r['row_id'],'target':v} for r,v in zip(b['test'],values)]
  scores[name]=grade_submission(submission,b['hidden'])['mse']
 choices={s:library.select_candidate(task,b['train'],s)['candidate_id'] for s in ('random','aligned')}
 return {'status':'development_example_not_agent_score','task':task,'seed':seed,'candidate_library':library.CANDIDATE_LIBRARY_VERSION,'choices':choices,'hidden_mse':scores,'finite_sample_best':min(scores,key=scores.get)}

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 s.add_parser('list');d=s.add_parser('demo');d.add_argument('--task',choices=common.TASK_IDS,default='temporal_future');d.add_argument('--seed',type=int,default=101)
 g=s.add_parser('grade');g.add_argument('--submission',required=True);g.add_argument('--hidden',required=True)
 a=p.parse_args()
 if a.command=='list':out={'version':'0.1.4-dev','validity_gate_passed':False,'development_tasks':common.TASK_IDS}
 elif a.command=='demo':out=demo(a.task,a.seed)
 else:
  with open(a.submission,newline='') as f:submission=list(csv.DictReader(f))
  with open(a.hidden,newline='') as f:hidden=list(csv.DictReader(f))
  out=grade_submission(submission,hidden)
 print(json.dumps(out,indent=2,allow_nan=False))
if __name__=='__main__':main()
