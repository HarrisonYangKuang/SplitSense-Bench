#!/usr/bin/env python3
"""Show semantic/numeric separation using an open B1 fixture, offline."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

from .scorer import candidate_ids, evaluate_arithmetic_expressions, score


ROOT = Path(__file__).resolve().parent


def load_example():
    """Use the public paired task with deliberately swapped pool memberships."""
    tasks = json.loads((ROOT / "task_inputs_b1_1_0_2.json").read_text())["tasks"]
    return next(task for task in tasks if task["task_id"] == "ss-b1-t10-v1")


def constructed_response(task):
    """Construct an illustrative correct response; no agent/model is called."""
    alpha = Decimal(task["deployment"]["seen_record_fraction"])
    weights = {
        pool_id: alpha if pool["membership"] == "seen" else Decimal(1) - alpha
        for pool_id, pool in task["pools"].items()
    }
    plan = {
        "pool_weights": {pool_id: str(value) for pool_id, value in weights.items()},
        "candidate_refs": {
            candidate_id: [f"{pool_id}:{candidate_id}" for pool_id in task["pool_order"]]
            for candidate_id in candidate_ids(task)
        },
        "aggregation": "record_weighted_mean",
    }
    # Bind risk rows by candidate identity, not array position or pool name.
    risks = {
        pool_id: {row["candidate_id"]: row["risk_mse"] for row in pool["risk_rows"]}
        for pool_id, pool in task["pools"].items()
    }
    expressions = {
        candidate_id: " + ".join(
            f"({weights[pool_id]} * {risks[pool_id][candidate_id]})"
            for pool_id in task["pool_order"]
        )
        for candidate_id in candidate_ids(task)
    }
    vector = evaluate_arithmetic_expressions(expressions, candidate_ids(task))
    return plan, expressions, vector


def main():
    task = load_example()
    plan, expressions, vector = constructed_response(task)
    correct = score(task, plan, vector, valid_lock=True)

    wrong_binding = copy.deepcopy(plan)
    wrong_binding["candidate_refs"]["c01"] = [
        f"{pool_id}:c02" for pool_id in task["pool_order"]
    ]
    wrong_semantics = score(task, wrong_binding, vector, valid_lock=True)

    incomplete_vector = dict(vector)
    incomplete_vector.pop("c12")
    incomplete = score(task, plan, incomplete_vector, valid_lock=True)

    rejected = False
    try:
        evaluate_arithmetic_expressions({"c01": "open('example.txt')"}, ["c01"])
    except ValueError:
        rejected = True

    assert Decimal(vector["c01"]) == Decimal("2.8975")
    assert (correct["S"], correct["X"], correct["J"]) == (1, 1, 1)
    assert (wrong_semantics["S"], wrong_semantics["X"], wrong_semantics["J"]) == (0, 1, 0)
    assert (incomplete["S"], incomplete["X"], incomplete["J"]) == (1, 0, 0)
    assert rejected
    print(json.dumps({
        "schema": "splitsense-b1-offline-scorer-demo-v1",
        "task_id": task["task_id"],
        "source": task["source"],
        "response_origin": "CONSTRUCTED_FROM_VISIBLE_SYNTHETIC_FIXTURE",
        "first_candidate_expression": expressions["c01"],
        "first_candidate_value": vector["c01"],
        "cases": {
            "correct": correct,
            "wrong_binding_correct_numbers": wrong_semantics,
            "incomplete_vector": incomplete,
        },
        "function_call_expression_rejected": rejected,
        "note": "Offline scoring walkthrough only; not a new model run or formal D2 episode.",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
