"""严格评分与可解释指标。只由运行结束后的外部 evaluator 调用。"""
from __future__ import annotations

import math
import statistics


def _indexed(rows, name):
    if not rows:
        raise ValueError(f"{name}: empty rows")
    result = {}
    for row in rows:
        if set(row) != {"row_id", "target"}:
            raise ValueError(f"{name}: require exactly row_id,target")
        key = str(row["row_id"])
        if not key or key in result:
            raise ValueError(f"{name}: empty or duplicate row_id")
        if isinstance(row["target"], bool):
            raise ValueError(f"{name}: boolean target is invalid")
        value = float(row["target"])
        if not math.isfinite(value):
            raise ValueError(f"{name}: target must be finite")
        result[key] = value
    return result


def grade_submission(submission_rows, hidden_rows):
    """按 ID 对齐；缺行、多行、重复、非数值或无穷值均拒绝，不静默修复。"""
    # 隐藏标签错误是 evaluator 错误，不能算作 Agent 失败。
    truth = _indexed(hidden_rows, "hidden")
    try:
        predicted = _indexed(submission_rows, "submission")
        if set(truth) != set(predicted):
            raise ValueError("submission: row_id set does not match hidden labels")
        squared_errors = [(predicted[key] - truth[key]) ** 2 for key in truth]
        mse = statistics.fmean(squared_errors)
        if not math.isfinite(mse):
            raise ValueError("submission: squared error overflow")
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        return {"valid": False, "mse": None, "utility": None, "errors": [str(error)]}
    # MSE = mean squared error，均方误差越小越好；取负数统一成越大越好。
    return {"valid": True, "mse": mse, "utility": -mse, "errors": []}


def selection_metrics(candidate_utilities, chosen_id, aligned_id, baseline_id,
                      local_validation_utility=None, minimum_denominator=1e-9):
    """固定候选库指标；所有 utility 都应来自同一 hidden deployment 数据。"""
    if not candidate_utilities or not all(math.isfinite(v) for v in candidate_utilities.values()):
        raise ValueError("candidate utilities must be nonempty and finite")
    if minimum_denominator <= 0 or not math.isfinite(minimum_denominator):
        raise ValueError("minimum_denominator must be positive and finite")
    chosen = candidate_utilities[chosen_id]
    aligned = candidate_utilities[aligned_id]
    baseline = candidate_utilities[baseline_id]
    oracle = max(candidate_utilities.values())
    denominator = aligned - baseline
    # 1e-9 只是浮点除法保护，不是研究上的最小有效差异阈值。
    normalized = ((chosen - baseline) / denominator
                  if denominator > minimum_denominator else None)
    if local_validation_utility is not None and not math.isfinite(local_validation_utility):
        raise ValueError("local validation utility must be finite")
    return {
        "hidden_deployment_utility": chosen,
        "aligned_reference_gap": aligned - chosen,
        "fixed_library_oracle_regret": oracle - chosen,
        "normalized_performance": normalized,
        "normalization_reason": None if normalized is not None else "reference_not_above_baseline",
        "validation_optimism_gap": (None if local_validation_utility is None
                                    else local_validation_utility - chosen),
    }


def reliability(records):
    """分母含全部运行；无有效成绩时返回 null，不把失败伪装为 0 分。"""
    if not records:
        return {"runs": 0, "valid_submission_rate": None, "median_utility": None,
                "worst_utility": None, "sample_sd_utility": None}
    valid = [r["utility"] for r in records if r["valid"]]
    if not all(v is not None and math.isfinite(v) for v in valid):
        raise ValueError("valid records must have finite utilities")
    return {"runs": len(records), "valid_submission_rate": len(valid) / len(records),
            "median_utility": statistics.median(valid) if valid else None,
            "worst_utility": min(valid) if valid else None,
            "sample_sd_utility": statistics.stdev(valid) if len(valid) > 1 else None}
