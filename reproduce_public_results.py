#!/usr/bin/env python3
"""Reproduce the frozen SplitSense D2 public statistics offline."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODES = ("N0_DIRECT_OUTPUT", "N1_CALCULATOR", "N2_DECLARATIVE_EXECUTION")


def mean(values):
    return sum(values) / len(values)


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def bootstrap(values, seed, draws=20000):
    rng = random.Random(seed)
    samples = [mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(draws)]
    return {
        "worlds": len(values),
        "estimate_percentage_points": 100 * mean(values),
        "bootstrap95_percentage_points": [100 * quantile(samples, 0.025), 100 * quantile(samples, 0.975)],
    }


def load_rows(path):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in ("valid_lock", "semantic_plan_correct_P", "end_to_end_success_J_D2"):
            row[key] = int(row[key])
    return rows


def analyze(rows, seed):
    by_mode = {}
    for mode in MODES:
        selected = [row for row in rows if row["execution_mode"] == mode]
        successes = sum(row["end_to_end_success_J_D2"] for row in selected)
        by_mode[mode] = {
            "successes": successes,
            "sessions": len(selected),
            "percent": 100 * successes / len(selected),
            "P_successes": sum(row["semantic_plan_correct_P"] for row in selected),
            "valid_locks": sum(row["valid_lock"] for row in selected),
        }
    indexed = {(row["world"], row["deployment"], row["execution_mode"]): row for row in rows}
    worlds = sorted({row["world"] for row in rows})
    deployments = sorted({row["deployment"] for row in rows})
    comparisons = {}
    for left, right, label in (
        ("N2_DECLARATIVE_EXECUTION", "N0_DIRECT_OUTPUT", "N2_MINUS_N0"),
        ("N1_CALCULATOR", "N0_DIRECT_OUTPUT", "N1_MINUS_N0"),
        ("N2_DECLARATIVE_EXECUTION", "N1_CALCULATOR", "N2_MINUS_N1"),
    ):
        differences = [
            mean(
                [
                    indexed[(world, deployment, left)]["end_to_end_success_J_D2"]
                    - indexed[(world, deployment, right)]["end_to_end_success_J_D2"]
                    for deployment in deployments
                ]
            )
            for world in worlds
        ]
        comparisons[label] = bootstrap(differences, seed)
    return {"modes": by_mode, "comparisons": comparisons}


def main():
    metadata = json.loads((ROOT / "public_results" / "metadata.json").read_text())
    result = {
        "schema": "splitsense-public-reproduction-v1",
        "main": analyze(load_rows(ROOT / "public_results" / "public_results.csv"), metadata["main"]["bootstrap_seed"]),
        "replication": analyze(load_rows(ROOT / "public_results" / "replication_results.csv"), metadata["replication"]["bootstrap_seed"]),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
