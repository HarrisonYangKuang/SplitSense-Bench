#!/usr/bin/env python3
"""Run the public toy declarative-execution example without network access."""

import json
from pathlib import Path

from executors import run_locked_plan


ROOT = Path(__file__).resolve().parent


def main():
    task = json.loads((ROOT / "examples" / "task_examples.json").read_text())["examples"][0]
    plan = json.loads((ROOT / "examples" / "executor_examples.json").read_text())["examples"][0]["plan"]
    artifact = run_locked_plan(task, plan)
    summary = {
        "flow": ["deployment contract", "validation evidence", "agent-style plan", "restricted declarative executor", "locked risk vector", "audit"],
        "status": artifact.get("status"),
        "sealed": artifact.get("sealed"),
        "source": artifact.get("source"),
        "risk_count": len(artifact.get("risks", [])),
        "artifact_sha256": artifact.get("artifact_sha256"),
        "note": "Public toy demonstration only; this is not a D2 formal episode.",
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["status"] != "PASS" or not summary["sealed"] or summary["risk_count"] != 12:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
