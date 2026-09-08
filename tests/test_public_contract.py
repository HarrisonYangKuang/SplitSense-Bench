import json,math,subprocess,sys,tempfile,unittest
from pathlib import Path
from tasks import common
from graders.metrics import grade_submission
import benchmark

class PublicContract(unittest.TestCase):
 def test_four_task_nine_candidate_demos(self):
  for task in common.TASK_IDS:
   with self.subTest(task=task):
    result=benchmark.demo(task,101)
    self.assertEqual(len(result['hidden_mse']),9)
    self.assertTrue(all(math.isfinite(v) and v>=0 for v in result['hidden_mse'].values()))
    self.assertTrue(set(result['choices'].values())<=set(result['hidden_mse']))
 def test_pair_training_and_export_boundary(self):
  for left,right in [('temporal_iid','temporal_future'),('entity_seen','entity_unseen')]:
   a,b=common.generate(left,101),common.generate(right,101)
   self.assertEqual(a['train'],b['train'])
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);common.export_instance(a,root/'agent',root/'evaluator')
   self.assertEqual({p.name for p in (root/'agent').iterdir()},{'train.csv','test.csv','sample_submission.csv','task_description.md'})
   self.assertTrue((root/'evaluator/hidden_labels.csv').is_file())
 def test_grader_alignment_and_rejections(self):
  truth=[{'row_id':'a','target':1.0},{'row_id':'b','target':2.0}]
  self.assertEqual(grade_submission(truth[::-1],truth)['mse'],0)
  cases=[truth[:1],truth+[truth[0]],[{'row_id':'c','target':1},truth[1]],[{'row_id':'a','target':float('nan')},truth[1]]]
  for rows in cases:self.assertFalse(grade_submission(rows,truth)['valid'])
 def test_cli_lists_development_status(self):
  p=subprocess.run([sys.executable,'benchmark.py','list'],check=True,capture_output=True,text=True)
  self.assertFalse(json.loads(p.stdout)['validity_gate_passed'])
if __name__=='__main__':unittest.main()
