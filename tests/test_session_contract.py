import json,unittest,tempfile,subprocess,sys
from pathlib import Path
from tasks.common import export_instance
from tasks.common import generate
from harness.phase_session_v04 import PhaseSession,run_session
class SessionContract(unittest.TestCase):
 def test_evaluate_commit_and_seal(self):
  session=PhaseSession(generate('temporal_future',101)['train'],'Predict future records using earlier observed history.')
  first=session.dispatch(json.dumps({'action':'evaluate','split':'forward_time'}))
  self.assertTrue(first['ok']);self.assertEqual(first['feedback_scope'],'training_internal_only')
  self.assertIn('train_mean',first['candidate_mse'])
  last=session.dispatch(json.dumps({'action':'commit','split':'forward_time','candidate_id':'train_mean','reason':'Fixture choice, not a capability result.'}))
  self.assertTrue(last['sealed']);self.assertTrue(session.committed)
  with self.assertRaises(RuntimeError):session.dispatch('{}')
 def test_early_commit_and_responder_failure(self):
  session=PhaseSession(generate('temporal_future',101)['train'],'Predict future records.')
  self.assertFalse(session.dispatch(json.dumps({'action':'commit','split':'forward_time','candidate_id':'train_mean','reason':'early'}))['ok'])
  fresh=PhaseSession(generate('temporal_future',101)['train'],'Predict future records.')
  def fail(prompt):raise EOFError()
  result=run_session(fresh,fail)
  self.assertEqual(result['session']['status'],'incomplete');self.assertEqual(result['attempted_responses'],1)
  self.assertIsNone(result['session']['commit'])
 def test_pipe_cli_records_explicit_commit(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);export_instance(generate('temporal_future',101),root/'agent',root/'evaluator')
   actions=[{'action':'evaluate','split':'forward_time'},{'action':'commit','split':'forward_time','candidate_id':'train_mean','reason':'Transport fixture.'}]
   p=subprocess.run([sys.executable,'-m','harness.pipe_session','--train',str(root/'agent/train.csv'),'--brief',str(root/'agent/task_description.md'),'--receipt',str(root/'receipt.json')],input=''.join(json.dumps(a)+'\n' for a in actions),capture_output=True,text=True,timeout=15,check=True)
   end=json.loads(p.stdout.splitlines()[-1]);self.assertEqual(end['status'],'committed')
   receipt=json.loads((root/'receipt.json').read_text());self.assertEqual(receipt['session']['commit']['candidate_id'],'train_mean');self.assertEqual(receipt['attempted_responses'],2)
if __name__=='__main__':unittest.main()
