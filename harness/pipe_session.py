"""Bounded stdin/stdout bridge for a training-only session; no model client."""
import argparse,csv,json,sys
from pathlib import Path
from harness.phase_session_v04 import PhaseSession,run_session
from harness.controlled_session_v03 import MAX_ACTION_BYTES

def main():
 p=argparse.ArgumentParser();p.add_argument('--train',required=True);p.add_argument('--brief',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
 output=Path(a.receipt)
 if output.exists():raise FileExistsError('Receipt already exists; use a fresh run path')
 with open(a.train,newline='') as f:rows=list(csv.DictReader(f))
 for row in rows:
  for k in ['x','timestamp','target']:row[k]=float(row[k])
 session=PhaseSession(rows,Path(a.brief).read_text())
 def respond(prompt):
  print(prompt,flush=True)
  b=sys.stdin.buffer.readline(MAX_ACTION_BYTES+2)
  if not b:raise EOFError('No response')
  if len(b)>MAX_ACTION_BYTES:raise ValueError('Response exceeds limit')
  return b.decode('utf-8').rstrip('\r\n')
 result=run_session(session,respond)
 result['execution_mode']='external_text_responder_identity_unverified'
 with output.open('x') as f:json.dump(result,f,ensure_ascii=False,allow_nan=False)
 print(json.dumps({'event':'session_finished','status':result['session']['status'],'attempted_responses':result['attempted_responses']}),flush=True)
if __name__=='__main__':main()
