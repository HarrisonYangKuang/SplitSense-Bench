"""Trusted post-commit grading. No Agent model client or OS sandbox."""
import argparse,csv,json,statistics
from pathlib import Path
from harness.phase_session_v04 import PhaseSession
from tasks.strong_candidates_v02 import candidate_predictions
from graders.metrics import grade_submission

def verified_commit(train,brief,receipt):
 transcript=receipt.get('transcript')
 if not isinstance(transcript,list) or not 1<=len(transcript)<=3:raise ValueError('Invalid transcript count')
 session=PhaseSession(train,brief)
 for event in transcript:
  response=session.dispatch(event['model_action'])
  if response!=event['training_tool_response']:raise ValueError('Recorded feedback does not replay')
 if not session.committed or session.receipt()!=receipt.get('session'):raise ValueError('No matching sealed session')
 return session.receipt()['commit']

def grade_files(train_path,brief_path,receipt_path,test_path,hidden_path):
 with open(train_path,newline='') as f:train=list(csv.DictReader(f))
 for row in train:
  for k in ['x','timestamp','target']:row[k]=float(row[k])
 with open(receipt_path,'rb') as f:packed=f.read(1048577)
 if len(packed)>1048576:raise ValueError('Receipt exceeds 1 MiB')
 receipt=json.loads(packed)
 commit=verified_commit(train,Path(brief_path).read_text(),receipt)
 # Only a verified commit permits access to test features and hidden labels.
 with open(test_path,newline='') as f:test=list(csv.DictReader(f))
 with open(hidden_path,newline='') as f:hidden=list(csv.DictReader(f))
 predictions=candidate_predictions(train,test);scores={}
 for name,values in predictions.items():
  submitted=[{'row_id':r['row_id'],'target':v} for r,v in zip(test,values)]
  score=grade_submission(submitted,hidden)
  if not score['valid']:raise ValueError('Invalid trusted prediction or scoring data')
  scores[name]=score['mse']
 chosen=commit['candidate_id'];v=statistics.pvariance(r['target'] for r in train)
 validation=receipt['session']['evaluations'][commit['split']]['candidate_mse'][chosen]
 return {'status':'graded_development_session','candidate_id':chosen,'split':commit['split'],'mse':scores[chosen],'candidate_mse':scores,'finite_library_regret':scores[chosen]-min(scores.values()),'normalized_regret':None if v==0 else (scores[chosen]-min(scores.values()))/v,'validation_optimism_gap':scores[chosen]-validation,'model_identity':'unverified','scientific_validity_gate_passed':False}

def main():
 p=argparse.ArgumentParser()
 for name in ['train','brief','receipt','test','hidden']:p.add_argument('--'+name,required=True)
 a=p.parse_args();print(json.dumps(grade_files(a.train,a.brief,a.receipt,a.test,a.hidden),indent=2,allow_nan=False))
if __name__=='__main__':main()
