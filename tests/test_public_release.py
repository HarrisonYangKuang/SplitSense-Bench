import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicReleaseTests(unittest.TestCase):
    def run_json(self, script):
        result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def test_frozen_statistics(self):
        result = self.run_json("reproduce_public_results.py")
        self.assertEqual(result["main"]["modes"]["N0_DIRECT_OUTPUT"]["successes"], 0)
        self.assertEqual(result["main"]["modes"]["N1_CALCULATOR"]["successes"], 13)
        self.assertEqual(result["main"]["modes"]["N2_DECLARATIVE_EXECUTION"]["successes"], 14)
        self.assertEqual(result["replication"]["modes"]["N0_DIRECT_OUTPUT"]["successes"], 0)
        self.assertEqual(result["replication"]["modes"]["N1_CALCULATOR"]["successes"], 7)
        self.assertEqual(result["replication"]["modes"]["N2_DECLARATIVE_EXECUTION"]["successes"], 12)
        self.assertEqual(result["main"]["comparisons"]["N2_MINUS_N0"]["bootstrap95_percentage_points"], [12.5, 32.8125])
        self.assertEqual(result["replication"]["comparisons"]["N2_MINUS_N0"]["bootstrap95_percentage_points"], [18.75, 56.25])

    def test_demo(self):
        result = self.run_json("demo.py")
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["sealed"])
        self.assertEqual(result["risk_count"], 12)


if __name__ == "__main__":
    unittest.main()
