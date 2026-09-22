"""Independent deterministic scorer for SplitSense B1."""

from __future__ import annotations

import ast
import json
import math
from decimal import Decimal, InvalidOperation, getcontext


getcontext().prec = 50


def dec(value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("boolean")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("number") from error
    if not result.is_finite():
        raise ValueError("nonfinite")
    return result


def parse_json_object(text: object) -> dict[str, object] | None:
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1])
            if stripped.lstrip().startswith("json"):
                stripped = stripped.lstrip()[4:].lstrip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _eval_arithmetic_node(node: ast.AST, depth: int = 0) -> Decimal:
    if depth > 8:
        raise ValueError("depth")
    if isinstance(node, ast.Expression):
        return _eval_arithmetic_node(node.body, depth + 1)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return dec(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_arithmetic_node(node.operand, depth + 1)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _eval_arithmetic_node(node.left, depth + 1)
        right = _eval_arithmetic_node(node.right, depth + 1)
        if isinstance(node.op, ast.Add):
            return dec(left + right)
        if isinstance(node.op, ast.Sub):
            return dec(left - right)
        if isinstance(node.op, ast.Mult):
            return dec(left * right)
        if right == 0:
            raise ValueError("division_by_zero")
        return dec(left / right)
    raise ValueError("ast")


def evaluate_arithmetic_expressions(expressions: object, output_ids: list[str]) -> dict[str, str]:
    """Independently evaluate the bounded Calculator response language."""
    if not isinstance(expressions, dict) or set(expressions) != set(output_ids):
        raise ValueError("keys")
    result: dict[str, str] = {}
    for candidate_id in output_ids:
        expression = expressions[candidate_id]
        if not isinstance(expression, str) or not 1 <= len(expression) <= 256:
            raise ValueError("expression")
        try:
            parsed = ast.parse(expression, mode="eval")
        except SyntaxError as error:
            raise ValueError("syntax") from error
        result[candidate_id] = str(_eval_arithmetic_node(parsed))
    return result


def pools_by_id(task: dict[str, object]) -> dict[str, dict[str, object]]:
    return task["pools"]  # type: ignore[return-value]


def candidate_ids(task: dict[str, object]) -> list[str]:
    return task["predictor_lock"]["output_candidate_ids"]  # type: ignore[index,return-value]


def risk_lookup(task: dict[str, object]) -> dict[str, dict[str, Decimal]]:
    result: dict[str, dict[str, Decimal]] = {}
    for pool_id, pool in pools_by_id(task).items():
        result[pool_id] = {row["candidate_id"]: dec(row["risk_mse"]) for row in pool["risk_rows"]}  # type: ignore[index]
    return result


def expected_weights(task: dict[str, object]) -> dict[str, Decimal]:
    alpha = dec(task["deployment"]["seen_record_fraction"])  # type: ignore[index]
    return {pool_id: alpha if pool["membership"] == "seen" else Decimal(1) - alpha for pool_id, pool in pools_by_id(task).items()}


def target(task: dict[str, object]) -> dict[str, Decimal]:
    weights = expected_weights(task)
    risks = risk_lookup(task)
    return {
        candidate_id: sum(weights[pool_id] * risks[pool_id][candidate_id] for pool_id in task["pool_order"])  # type: ignore[index]
        for candidate_id in candidate_ids(task)
    }


def semantic_components(task: dict[str, object], plan: object) -> dict[str, int]:
    result = {"M": 0, "W": 0, "C": 0, "A": 0}
    if not isinstance(plan, dict) or set(plan) != {"pool_weights", "candidate_refs", "aggregation"}:
        return result
    pools = set(task["pool_order"])  # type: ignore[arg-type]
    weights = plan.get("pool_weights")
    if isinstance(weights, dict) and set(weights) == pools:
        try:
            wanted = expected_weights(task)
            tol = dec(task["weight_tolerance"])
            result["W"] = int(all(abs(dec(weights[pool]) - wanted[pool]) <= tol for pool in pools))
        except ValueError:
            pass
    refs = plan.get("candidate_refs")
    outputs = set(candidate_ids(task))
    if isinstance(refs, dict) and set(refs) == outputs:
        memberships_ok = True
        candidate_ok = True
        for output_id, references in refs.items():
            if not isinstance(references, list) or len(references) != len(pools):
                memberships_ok = candidate_ok = False
                continue
            parsed = []
            for reference in references:
                if not isinstance(reference, str) or ":" not in reference:
                    memberships_ok = candidate_ok = False
                    continue
                parsed.append(reference.split(":", 1))
            memberships_ok &= {part[0] for part in parsed} == pools
            candidate_ok &= all(part[1] == output_id for part in parsed)
        result["M"] = int(memberships_ok)
        result["C"] = int(candidate_ok)
    result["A"] = int(plan.get("aggregation") == task["aggregation"])
    return result


def score(task: dict[str, object], plan: object, risk_by_candidate: object, valid_lock: bool) -> dict[str, object]:
    components = semantic_components(task, plan)
    semantic = math.prod(components.values())
    output_ids = candidate_ids(task)
    execution = 0
    component_passes = 0
    max_error: float | None = None
    if valid_lock and isinstance(risk_by_candidate, dict) and set(risk_by_candidate) == set(output_ids):
        try:
            wanted = target(task)
            scale = dec(task["scale"]["value"])  # type: ignore[index]
            errors = {candidate_id: abs(dec(risk_by_candidate[candidate_id]) - wanted[candidate_id]) / scale for candidate_id in output_ids}
            tolerance = dec(task["normalized_numeric_tolerance"])
            component_passes = sum(error <= tolerance for error in errors.values())
            max_error = float(max(errors.values()))
            execution = int(component_passes == len(output_ids))
        except ValueError:
            pass
    return {
        "semantic_components": components,
        "semantic_partial": sum(components.values()) / 4,
        "S": semantic,
        "X": execution,
        "J": semantic * execution,
        "component_passes": component_passes,
        "component_total": len(output_ids),
        "max_normalized_error": max_error,
        "valid_lock": bool(valid_lock),
    }
