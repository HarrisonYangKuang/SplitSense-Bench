"""Bounded arithmetic and declarative execution without semantic correction."""

from __future__ import annotations

import copy
import ast
import hashlib
import json
import math
from decimal import Decimal, getcontext


getcontext().prec = 50
EXECUTOR_VERSION = "diagnostic-d2-executor-v1"
MAX_ABS_VALUE = Decimal("1000000")
MAX_AST_DEPTH = 8
MAX_AST_NODES = 127
MAX_EXPRESSIONS = 12


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_public_task(task):
    required = {"task_id", "alpha", "variance", "candidate_ids", "predictor_lock", "pool_order", "pools"}
    if set(task) != required:
        raise ValueError("task_fields")
    if task["alpha"] not in (0.25, 0.75) or not finite_number(task["variance"]) or task["variance"] <= 0:
        raise ValueError("task_numeric")
    candidates, pool_order = task["candidate_ids"], task["pool_order"]
    if len(candidates) != 12 or len(set(candidates)) != 12 or task["predictor_lock"].get("candidate_ids") != candidates:
        raise ValueError("candidate_lock")
    if len(pool_order) != 2 or len(set(pool_order)) != 2:
        raise ValueError("pool_order")
    memberships = []
    for pool_id in pool_order:
        pool = task["pools"].get(pool_id)
        if not isinstance(pool, dict) or set(pool) != {"membership", "rows", "risks", "receipt_sha256"}:
            raise ValueError("pool_fields")
        if pool["membership"] not in ("seen", "unseen") or type(pool["rows"]) is not int or pool["rows"] <= 0:
            raise ValueError("pool_contract")
        if len(pool["risks"]) != 12 or not all(finite_number(value) and value >= 0 for value in pool["risks"]):
            raise ValueError("pool_risks")
        memberships.append(pool["membership"])
    if set(memberships) != {"seen", "unseen"}:
        raise ValueError("membership_bijection")
    return True


def task_view(task):
    validate_public_task(task)
    return {
        "task_id": task["task_id"],
        "deployment": {
            "alpha": task["alpha"],
            "alpha_definition": "fraction of deployment records from entities represented in training",
            "loss": "mean_squared_error",
        },
        "candidate_ids": copy.deepcopy(task["candidate_ids"]),
        "predictor_lock": copy.deepcopy(task["predictor_lock"]),
        "pool_order": copy.deepcopy(task["pool_order"]),
        "evidence": [
            {
                "pool_id": pool_id,
                "membership": task["pools"][pool_id]["membership"],
                "rows": task["pools"][pool_id]["rows"],
                "risks": copy.deepcopy(task["pools"][pool_id]["risks"]),
                "candidate_ids": copy.deepcopy(task["candidate_ids"]),
                "receipt_sha256": task["pools"][pool_id]["receipt_sha256"],
            }
            for pool_id in task["pool_order"]
        ],
        "array_binding": "weights follow pool_order; risks follow candidate_ids",
        "source": "VISIBLE_EVIDENCE_ONLY",
    }


def validate_submission(action, task):
    issues = []
    if not isinstance(action, dict) or set(action) != {"op", "weights", "risks"}:
        return ["submission_fields"]
    if action.get("op") != "submit":
        issues.append("op")
    weights, risks = action.get("weights"), action.get("risks")
    if not isinstance(weights, list) or len(weights) != 2:
        issues.append("weights_length")
    elif not all(finite_number(value) and value >= 0 for value in weights) or not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
        issues.append("weights_values")
    if not isinstance(risks, list) or len(risks) != len(task["candidate_ids"]):
        issues.append("risks_length")
    elif not all(finite_number(value) and value >= 0 for value in risks):
        issues.append("risks_values")
    return sorted(set(issues))


def _decimal(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("number")
    result = Decimal(str(value))
    if abs(result) > MAX_ABS_VALUE:
        raise ValueError("number_range")
    return result


def _evaluate_ast(node, depth=0, counter=None):
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_AST_NODES or depth > MAX_AST_DEPTH:
        raise ValueError("expression_complexity")
    if isinstance(node, ast.Expression):
        return _evaluate_ast(node.body, depth + 1, counter)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return _decimal(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_ast(node.operand, depth + 1, counter)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _evaluate_ast(node.left, depth + 1, counter)
        right = _evaluate_ast(node.right, depth + 1, counter)
        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        else:
            if right == 0:
                raise ValueError("division_by_zero")
            result = left / right
        if not result.is_finite() or abs(result) > MAX_ABS_VALUE:
            raise ValueError("result_range")
        return result
    raise ValueError("expression_ast")


def evaluate_expression(node, depth=0, counter=None):
    if isinstance(node, str):
        if not 1 <= len(node) <= 256:
            raise ValueError("expression_length")
        try:
            parsed = ast.parse(node, mode="eval")
        except SyntaxError:
            raise ValueError("expression_syntax") from None
        return _evaluate_ast(parsed)
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_AST_NODES or depth > MAX_AST_DEPTH:
        raise ValueError("expression_complexity")
    if type(node) in (int, float):
        return _decimal(node)
    if not isinstance(node, dict) or set(node) != {"op", "args"}:
        raise ValueError("expression_node")
    op, args = node["op"], node["args"]
    if op not in {"add", "sub", "mul", "div"} or not isinstance(args, list) or len(args) != 2:
        raise ValueError("expression_operation")
    left = evaluate_expression(args[0], depth + 1, counter)
    right = evaluate_expression(args[1], depth + 1, counter)
    if op == "add":
        result = left + right
    elif op == "sub":
        result = left - right
    elif op == "mul":
        result = left * right
    else:
        if right == 0:
            raise ValueError("division_by_zero")
        result = left / right
    if not result.is_finite() or abs(result) > MAX_ABS_VALUE:
        raise ValueError("result_range")
    return result


def calculate(expressions):
    if not isinstance(expressions, list) or not 1 <= len(expressions) <= MAX_EXPRESSIONS:
        return {"status": "FAIL", "error": "expressions_length"}
    try:
        values = [evaluate_expression(expression) for expression in expressions]
    except ValueError as error:
        return {"status": "FAIL", "error": str(error)}
    return {
        "status": "PASS",
        "source": "BOUNDED_CALCULATOR",
        "values": [float(value) for value in values],
        "expression_sha256": digest(expressions),
        "executor_version": EXECUTOR_VERSION,
    }


def execute_plan(task, plan):
    """Execute a structurally legal plan exactly, including semantically wrong choices."""
    validate_public_task(task)
    if not isinstance(plan, dict) or set(plan) != {"op", "weights", "outputs"} or plan.get("op") != "execute_plan":
        return {"status": "FAIL", "error": "plan_fields"}
    weights, outputs = plan["weights"], plan["outputs"]
    if not isinstance(weights, list) or len(weights) != 2 or not all(finite_number(value) and value >= 0 for value in weights) or not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
        return {"status": "FAIL", "error": "weights"}
    if not isinstance(outputs, list) or len(outputs) != len(task["candidate_ids"]):
        return {"status": "FAIL", "error": "outputs_length"}
    by_candidate = {}
    provenance = {}
    try:
        for output in outputs:
            if not isinstance(output, dict) or set(output) != {"candidate_id", "terms"}:
                raise ValueError("output_fields")
            candidate_id, terms = output["candidate_id"], output["terms"]
            if candidate_id not in task["candidate_ids"] or candidate_id in by_candidate:
                raise ValueError("output_candidate")
            if not isinstance(terms, list) or len(terms) != 2:
                raise ValueError("terms_length")
            if {term.get("pool_id") for term in terms if isinstance(term, dict)} != set(task["pool_order"]):
                raise ValueError("pool_references")
            if {term.get("weight_index") for term in terms if isinstance(term, dict)} != {0, 1}:
                raise ValueError("weight_indices")
            value = Decimal(0)
            detail = []
            for term in terms:
                if not isinstance(term, dict) or set(term) != {"pool_id", "source_candidate_id", "weight_index"}:
                    raise ValueError("term_fields")
                pool_id = term["pool_id"]
                source_candidate_id = term["source_candidate_id"]
                if source_candidate_id not in task["candidate_ids"]:
                    raise ValueError("source_candidate")
                source_index = task["candidate_ids"].index(source_candidate_id)
                source_value = Decimal(str(task["pools"][pool_id]["risks"][source_index]))
                weight = Decimal(str(weights[term["weight_index"]]))
                value += weight * source_value
                detail.append(
                    {
                        "pool_id": pool_id,
                        "source_candidate_id": source_candidate_id,
                        "weight_index": term["weight_index"],
                        "source_value": float(source_value),
                        "weight": float(weight),
                    }
                )
            if not value.is_finite() or value < 0 or abs(value) > MAX_ABS_VALUE:
                raise ValueError("result_range")
            by_candidate[candidate_id] = float(value)
            provenance[candidate_id] = detail
    except ValueError as error:
        return {"status": "FAIL", "error": str(error)}
    if set(by_candidate) != set(task["candidate_ids"]):
        return {"status": "FAIL", "error": "candidate_coverage"}
    risks = [by_candidate[candidate_id] for candidate_id in task["candidate_ids"]]
    artifact = {
        "schema": "diagnostic-d2-locked-artifact-v1",
        "status": "PASS",
        "sealed": True,
        "source": "AGENT_PLUS_EXECUTOR",
        "task_id": task["task_id"],
        "evidence_sha256": digest(task_view(task)),
        "plan_sha256": digest(plan),
        "executor_version": EXECUTOR_VERSION,
        "weights": copy.deepcopy(weights),
        "candidate_ids": copy.deepcopy(task["candidate_ids"]),
        "risks": risks,
        "provenance": provenance,
    }
    artifact["artifact_sha256"] = digest(artifact)
    return artifact
