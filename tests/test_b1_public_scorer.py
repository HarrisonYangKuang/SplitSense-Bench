"""Behavioral checks for the public B1 scorer; no Kaggle SDK or model calls."""

import copy
import unittest
from decimal import Decimal

from benchmark.demo_scorer import constructed_response, load_example
from benchmark.scorer import evaluate_arithmetic_expressions, score


class B1PublicScorerTests(unittest.TestCase):
    def setUp(self):
        self.task = load_example()
        self.plan, self.expressions, self.vector = constructed_response(self.task)

    def test_swapped_pool_membership_and_known_arithmetic(self):
        # Public t10 has kappa=unseen, zeta=seen, alpha=0.25.
        # This known result checks the visible contract independently of target().
        self.assertEqual(self.plan["pool_weights"], {
            "pool_kappa": "0.75000000", "pool_zeta": "0.25000000"
        })
        self.assertEqual(Decimal(self.vector["c01"]), Decimal("2.8975"))
        result = score(self.task, self.plan, self.vector, valid_lock=True)
        self.assertEqual((result["S"], result["X"], result["J"]), (1, 1, 1))

    def test_correct_numbers_do_not_repair_wrong_candidate_binding(self):
        plan = copy.deepcopy(self.plan)
        plan["candidate_refs"]["c01"] = ["pool_kappa:c02", "pool_zeta:c02"]
        result = score(self.task, plan, self.vector, valid_lock=True)
        self.assertEqual(result["semantic_components"]["C"], 0)
        self.assertEqual((result["S"], result["X"], result["J"]), (0, 1, 0))

    def test_pool_name_cannot_replace_membership(self):
        plan = copy.deepcopy(self.plan)
        plan["pool_weights"] = {"pool_kappa": "0.25", "pool_zeta": "0.75"}
        result = score(self.task, plan, self.vector, valid_lock=True)
        self.assertEqual(result["semantic_components"]["W"], 0)
        self.assertEqual(result["J"], 0)

    def test_incomplete_candidate_vector_fails_execution(self):
        vector = dict(self.vector)
        vector.pop("c12")
        result = score(self.task, self.plan, vector, valid_lock=True)
        self.assertEqual((result["S"], result["X"], result["J"]), (1, 0, 0))

    def test_invalid_lock_does_not_pass_with_correct_numbers(self):
        result = score(self.task, self.plan, self.vector, valid_lock=False)
        self.assertEqual((result["S"], result["X"], result["J"]), (1, 0, 0))

    def test_calculator_rejects_calls_names_attributes_and_power(self):
        for expression in ("open('example.txt')", "value", "(1).real", "2 ** 10", "1 / 0"):
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    evaluate_arithmetic_expressions({"c01": expression}, ["c01"])


if __name__ == "__main__":
    unittest.main()
