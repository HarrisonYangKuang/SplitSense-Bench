"""Public, key-free plan-to-locked-artifact component for D2 W6."""

from __future__ import annotations

from .core import execute_plan


TASK_FIELDS = {"task_id", "alpha", "variance", "candidate_ids", "predictor_lock", "pool_order", "pools"}
PLAN_FIELDS = {"op", "weights", "outputs"}


def run_locked_plan(task, plan):
    """Return UNKNOWN for missing inputs, ERROR for violations, or a sealed artifact."""
    if not isinstance(task, dict):
        return {"status": "UNKNOWN", "error": "missing_information", "missing": ["task"]}
    missing_task = sorted(TASK_FIELDS - set(task))
    if missing_task:
        return {"status": "UNKNOWN", "error": "missing_information", "missing": missing_task}
    if not isinstance(plan, dict):
        return {"status": "UNKNOWN", "error": "missing_information", "missing": ["plan"]}
    missing_plan = sorted(PLAN_FIELDS - set(plan))
    if missing_plan:
        return {"status": "UNKNOWN", "error": "missing_information", "missing": missing_plan}
    try:
        result = execute_plan(task, plan)
    except (KeyError, TypeError, ValueError) as error:
        return {"status": "ERROR", "error": "contract_violation", "detail": str(error)}
    if result.get("status") != "PASS":
        return {"status": "ERROR", **{key: value for key, value in result.items() if key != "status"}}
    return result
