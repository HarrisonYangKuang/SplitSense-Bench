"""纯标准库的四任务原型。此模块属于可信评估端，不能放进被测 Agent 工作区。

generate 只在内存中生成记录；export_instance / CLI 才会写出 CSV。
这里的 aligned reference 通过训练内部验证选模型，从不读取 hidden labels。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

TASK_IDS = ("temporal_iid", "temporal_future", "entity_seen", "entity_unseen")
CANDIDATE_IDS = (
    "train_mean", "global_linear", "recent_linear_25pct",
    "recent_linear_50pct", "entity_mean",
)
FEATURE_COLUMNS = ("row_id", "x", "entity_id", "timestamp")
TARGET_COLUMN = "target"
GENERATOR_VERSION = "0.1.0-prototype"
# smoke = 功能检查规模；pilot 仅预留云端规模，当前不在本机生成。
SCALES = {"smoke": (320, 128, 20), "pilot": (3200, 1280, 80)}
VALIDATION_FRACTION = 0.20
SPLIT_SEED = 1729  # 仅固定切分随机数；不是数据种子或隐藏答案。
ENTITY_GLOBAL_SLOPE = 2.5
ENTITY_OFFSET_STANDARD_DEVIATION = 6.0
OBSERVATION_NOISE_STANDARD_DEVIATION = 0.25
TEMPORAL_INITIAL_SLOPE = 1.5
TEMPORAL_DRIFT_START_FRACTION = 0.45
TEMPORAL_TRAIN_SLOPE_INCREASE = 4.0


def _rng(seed: int, namespace: str) -> random.Random:
    """独立随机流（random stream），避免修改 test 生成消耗 train 的随机数。"""
    digest = hashlib.sha256(f"{seed}:{namespace}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean values are not numeric observations")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("All numeric values must be finite")
    return result


def _rounded(value: float) -> float:
    return round(value, 10)


def _slope_at(timestamp: int, train_count: int) -> float:
    """历史前 45% 斜率稳定，其后连续漂移，未来延续同一规律。"""
    progress = timestamp / (train_count - 1)
    drift_progress = max(0.0, progress - TEMPORAL_DRIFT_START_FRACTION)
    return TEMPORAL_INITIAL_SLOPE + (
        TEMPORAL_TRAIN_SLOPE_INCREASE * drift_progress
        / (1.0 - TEMPORAL_DRIFT_START_FRACTION)
    )


def generate(task_id: str, seed: int, scale: str = "smoke") -> dict[str, Any]:
    """生成内存数据；test 没有 target，hidden 仅有 row_id 和 target。

    同一 family、seed、scale 的 train 完全相同；部署采样和任务说明改变。
    seed 是实例随机种子，scale 控制行数，均属于可信评估端元数据。
    """
    if task_id not in TASK_IDS:
        raise ValueError(f"Unknown task_id: {task_id}")
    if scale not in SCALES:
        raise ValueError(f"Unknown scale: {scale}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    train_count, test_count, entity_count = SCALES[scale]
    family = task_id.split("_")[0]
    train_random = _rng(seed, f"{family}:train:{scale}")
    test_random = _rng(seed, f"{family}:test:{scale}")
    offset_random = _rng(seed, f"{family}:offsets:{scale}")
    offsets = [
        offset_random.gauss(0.0, ENTITY_OFFSET_STANDARD_DEVIATION)
        for _ in range(2 * entity_count)
    ]

    def make_row(index: int, is_train: bool) -> dict[str, Any]:
        stream = train_random if is_train else test_random
        if family == "temporal":
            if is_train:
                timestamp = index
            elif task_id == "temporal_iid":
                timestamp = stream.randrange(train_count)
            else:
                timestamp = train_count + index
            entity_index = timestamp % entity_count
            feature = _rounded(stream.gauss(0.0, 1.0))
            signal = _slope_at(timestamp, train_count) * feature
        else:
            timestamp = index if is_train else train_count + index
            entity_index = index % entity_count if is_train else stream.randrange(entity_count)
            if not is_train and task_id == "entity_unseen":
                entity_index += entity_count
            feature = _rounded(stream.gauss(0.0, 1.0))
            signal = ENTITY_GLOBAL_SLOPE * feature + offsets[entity_index]
        target = _rounded(signal + stream.gauss(0.0, OBSERVATION_NOISE_STANDARD_DEVIATION))
        return {
            "row_id": f"{'train' if is_train else 'test'}_{index:06d}",
            "x": feature,
            "entity_id": f"entity_{entity_index:04d}",
            "timestamp": timestamp,
            "target": target,
        }

    train = [make_row(index, True) for index in range(train_count)]
    deployment = [make_row(index, False) for index in range(test_count)]
    test = [{column: row[column] for column in FEATURE_COLUMNS} for row in deployment]
    hidden = [{"row_id": row["row_id"], "target": row["target"]} for row in deployment]
    return {
        "train": train,
        "test": test,
        "hidden": hidden,
        "metadata": {
            "generator_version": GENERATOR_VERSION,
            "task_id": task_id,
            "family": family,
            "seed": seed,
            "scale": scale,
            "train_rows": train_count,
            "test_rows": test_count,
            "candidate_ids": list(CANDIDATE_IDS),
            "evaluation_track": "deployment_observed",
            "reference_status": "training-validation-selected aligned reference; not a true oracle",
            "limitations": [
                "Visible test covariates reveal the deployment time/entity population.",
                "This track does not isolate prompt-only causal effects.",
                "Restricted candidate library and synthetic generator need independent pilot review.",
                "Export directory separation alone is not an agent access-control boundary.",
            ],
        },
    }


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot fit or score an empty sample")
    return math.fsum(values) / len(values)


def _fit_linear(train: list[dict[str, Any]]) -> tuple[float, float]:
    """最小二乘（ordinary least squares）：返回截距 intercept 和斜率 slope。"""
    features = [_number(row["x"]) for row in train]
    targets = [_number(row["target"]) for row in train]
    feature_mean, target_mean = _mean(features), _mean(targets)
    sum_squared_deviation = math.fsum((value - feature_mean) ** 2 for value in features)
    if sum_squared_deviation == 0.0:
        return target_mean, 0.0
    covariance_sum = math.fsum(
        (feature - feature_mean) * (target - target_mean)
        for feature, target in zip(features, targets)
    )
    slope = covariance_sum / sum_squared_deviation
    return target_mean - slope * feature_mean, slope


def candidate_predictions(
    train: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> dict[str, list[float]]:
    """共享、合法的候选模型库；所有统计量只由传入的 train 拟合。

    entity_mean 对训练中出现过的实体预测其训练均值；新实体回退到全局训练均值。
    这是常规实体均值模型，不添加故意错误的输出，也不读取待预测行的 target。
    """
    if not train:
        raise ValueError("Training rows cannot be empty")
    train_mean = _mean([_number(row["target"]) for row in train])
    features = [_number(row["x"]) for row in rows]
    ordered = sorted(train, key=lambda row: (_number(row["timestamp"]), str(row["row_id"])))
    predictions = {"train_mean": [train_mean] * len(rows)}
    for candidate_id, fraction in (
        ("global_linear", 1.0), ("recent_linear_25pct", 0.25), ("recent_linear_50pct", 0.50)
    ):
        retained_count = max(2, math.ceil(len(train) * fraction))
        fit_rows = ordered[-retained_count:]
        intercept, slope = _fit_linear(fit_rows)
        predictions[candidate_id] = [intercept + slope * feature for feature in features]
    entity_targets: dict[str, list[float]] = {}
    for row in train:
        entity_targets.setdefault(str(row["entity_id"]), []).append(_number(row["target"]))
    entity_means = {entity: _mean(values) for entity, values in entity_targets.items()}
    predictions["entity_mean"] = [
        entity_means.get(str(row["entity_id"]), train_mean) for row in rows
    ]
    return {candidate_id: predictions[candidate_id] for candidate_id in CANDIDATE_IDS}


def validation_split(
    task_id: str,
    train: list[dict[str, Any]],
    strategy: str = "aligned",
    seed: int = SPLIT_SEED,
) -> dict[str, Any]:
    """返回训练内切分行号，供过程审计；任何分支都不访问 deployment 行。"""
    if task_id not in TASK_IDS or strategy not in ("aligned", "random"):
        raise ValueError("Unsupported task or validation strategy")
    if len(train) < 4:
        raise ValueError("At least four training rows are required for validation")
    shuffled = list(range(len(train)))
    stream = random.Random(seed)
    if strategy == "aligned" and task_id == "temporal_future":
        timestamps = sorted({_number(row["timestamp"]) for row in train})
        if len(timestamps) < 2:
            raise ValueError("Forward validation requires at least two distinct timestamps")
        validation_times = max(1, math.ceil(len(timestamps) * VALIDATION_FRACTION))
        boundary = timestamps[-validation_times]
        validation_indices = [i for i, row in enumerate(train) if _number(row["timestamp"]) >= boundary]
        name = "forward_time_holdout"
    elif strategy == "aligned" and task_id == "entity_unseen":
        entities = sorted({str(row["entity_id"]) for row in train})
        if len(entities) < 2:
            raise ValueError("Group validation requires at least two entities")
        stream.shuffle(entities)
        validation_entities = set(entities[:max(1, math.ceil(len(entities) * VALIDATION_FRACTION))])
        validation_indices = [i for i, row in enumerate(train) if str(row["entity_id"]) in validation_entities]
        name = "unseen_entity_holdout"
    elif strategy == "aligned" and task_id == "entity_seen":
        groups: dict[str, list[int]] = {}
        for index, row in enumerate(train):
            groups.setdefault(str(row["entity_id"]), []).append(index)
        if any(len(indices) < 2 for indices in groups.values()):
            raise ValueError("Seen-entity validation requires repeated rows per entity")
        validation_indices = []
        for entity in sorted(groups):
            indices = groups[entity][:]
            stream.shuffle(indices)
            selected_count = min(len(indices) - 1, max(1, math.ceil(len(indices) * VALIDATION_FRACTION)))
            validation_indices.extend(indices[:selected_count])
        name = "within_seen_entity_holdout"
    else:
        stream.shuffle(shuffled)
        validation_indices = shuffled[:max(1, math.ceil(len(train) * VALIDATION_FRACTION))]
        name = "random_row_holdout"
    validation_set = set(validation_indices)
    fitting_indices = [index for index in range(len(train)) if index not in validation_set]
    if not fitting_indices or not validation_set:
        raise ValueError("Validation must contain nonempty disjoint fitting and validation sets")
    return {
        "strategy": name,
        "split_seed": seed,
        "fit_indices": fitting_indices,
        "validation_indices": sorted(validation_set),
    }


def select_candidate(
    task_id: str, train: list[dict[str, Any]], strategy: str = "aligned"
) -> dict[str, Any]:
    """用训练内部的 MSE（mean squared error，均方误差）选择候选。

    validation_mse 越小越好。并列时按固定 CANDIDATE_IDS 顺序选择，保证复现。
    这是参考选择规则；它不保证部署效果最好，更不是真正 oracle。
    """
    split = validation_split(task_id, train, strategy)
    fitting_rows = [train[index] for index in split["fit_indices"]]
    validation_rows = [train[index] for index in split["validation_indices"]]
    predictions = candidate_predictions(fitting_rows, validation_rows)
    scores = {
        candidate_id: _mean([
            (prediction - _number(row["target"])) ** 2
            for prediction, row in zip(values, validation_rows)
        ])
        for candidate_id, values in predictions.items()
    }
    selected = min(CANDIDATE_IDS, key=lambda candidate_id: scores[candidate_id])
    return {
        "candidate_id": selected,
        "validation_mse": scores[selected],
        "validation_scores": scores,
        "validation_split": split,
    }


def solve(
    task_id: str, train: list[dict[str, Any]], test: list[dict[str, Any]], strategy: str
) -> dict[str, Any]:
    selected = select_candidate(task_id, train, strategy)
    predictions = candidate_predictions(train, test)[selected["candidate_id"]]
    return {
        **selected,
        "submission": [{"row_id": row["row_id"], "target": prediction} for row, prediction in zip(test, predictions)],
    }


def noop_submission(train: list[dict[str, Any]], test: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """NOP（no-op）诊断基线：仅预测训练 target 均值，不选择模型。"""
    train_mean = _mean([_number(row["target"]) for row in train])
    return [{"row_id": row["row_id"], "target": train_mean} for row in test]


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def export_instance(bundle: dict[str, Any], agent_dir: str | Path, evaluator_dir: str | Path) -> dict[str, str]:
    """显式写出两个独立目录；分目录不能替代云端容器/权限隔离。

    被测 Agent 目录只含四个输入文件，不含代码、seed、baseline、reference 或 hidden。
    """
    public_path, private_path = Path(agent_dir).resolve(), Path(evaluator_dir).resolve()
    if public_path == private_path or public_path in private_path.parents or private_path in public_path.parents:
        raise ValueError("Agent and evaluator directories must be disjoint, with neither nested in the other")
    for directory in (public_path, private_path):
        if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
            raise FileExistsError(f"Output directory must be absent or empty: {directory}")
    task_id = bundle["metadata"]["task_id"]
    if task_id not in TASK_IDS:
        raise ValueError("Unknown task identifier in metadata")
    description = (Path(__file__).parent / task_id / "task_description.md").read_text(encoding="utf-8")
    public_path.mkdir(parents=True, exist_ok=True)
    private_path.mkdir(parents=True, exist_ok=True)
    _write_csv(public_path / "train.csv", bundle["train"], FEATURE_COLUMNS + (TARGET_COLUMN,))
    _write_csv(public_path / "test.csv", bundle["test"], FEATURE_COLUMNS)
    _write_csv(public_path / "sample_submission.csv", [
        {"row_id": row["row_id"], "target": 0.0} for row in bundle["test"]
    ], ("row_id", "target"))
    (public_path / "task_description.md").write_text(description, encoding="utf-8")
    _write_csv(private_path / "hidden_labels.csv", bundle["hidden"], ("row_id", "target"))
    (private_path / "metadata.json").write_text(json.dumps(bundle["metadata"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"agent_dir": str(public_path), "evaluator_dir": str(private_path)}


def generator_cli(task_id: str) -> None:
    parser = argparse.ArgumentParser(description="Export one bounded SplitSense prototype instance")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--scale", choices=tuple(SCALES), default="smoke")
    parser.add_argument("--agent-dir", type=Path, required=True)
    parser.add_argument("--evaluator-dir", type=Path, required=True)
    parser.add_argument("--max-total-rows", type=int, default=500,
                        help="Explicit disk-output row bound; default 500 permits only smoke scale")
    args = parser.parse_args()
    total_rows = sum(SCALES[args.scale][:2])
    if total_rows > args.max_total_rows:
        parser.error(f"This scale has {total_rows} rows, above --max-total-rows={args.max_total_rows}; use a cloud run or an explicit larger row bound")
    bundle = generate(task_id, args.seed, args.scale)
    print(json.dumps(export_instance(bundle, args.agent_dir, args.evaluator_dir), ensure_ascii=False))


def solution_cli(task_id: str, strategy: str) -> None:
    parser = argparse.ArgumentParser(description=f"Run trusted {strategy} validation reference")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    with args.train.open(encoding="utf-8", newline="") as handle:
        train = list(csv.DictReader(handle))
    with args.test.open(encoding="utf-8", newline="") as handle:
        test = list(csv.DictReader(handle))
    result = solve(task_id, train, test, strategy)
    _write_csv(args.submission, result.pop("submission"), ("row_id", "target"))
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
