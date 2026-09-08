"""v0.2 的有限强候选挑战（finite stronger-candidate challenge）。

保留 v0.1 的五个候选及其顺序，只增加四个事先声明的常规模型。
所有拟合、归一化和时间结点只读 train；rows 的 target 从不读取。
这仍是可信评估端代码，不应放进被测 Agent 的文件权限域。
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from tasks import common

CANDIDATE_LIBRARY_VERSION = "0.2.0-strong-candidate-challenge"
EXTRA_CANDIDATE_IDS = (
    "global_linear_entity_residual",
    "entity_fixed_effects_linear",
    "time_linear_interaction",
    "time_hinge_interaction",
)
CANDIDATE_IDS = common.CANDIDATE_IDS + EXTRA_CANDIDATE_IDS
RIDGE_EPSILON = 1e-10  # 标准化后平均平方损失中的数值稳定惩罚，非调参结果。
HINGE_KNOT = 0.5  # 当前拟合训练时间跨度的中点；不读生成器的漂移起点。


@dataclass(frozen=True)
class _Scale:
    """先除最大绝对值再中心化，避免直接对巨大数值求平方。

    这是数值缩放（numerical scaling），不声称具有抗离群点统计性质。
    常数列的 span 固定为 1，所以训练列变成 0，且不会除以 0。
    """

    magnitude: float
    offset: float
    span: float

    @classmethod
    def fit(cls, values: list[float], *, time_range: bool = False) -> "_Scale":
        if not values:
            raise ValueError("Cannot fit a scaler on an empty sample")
        magnitude = max(abs(value) for value in values) or 1.0
        normalized = [value / magnitude for value in values]
        if time_range:
            offset = min(normalized)
            span = max(normalized) - offset
        else:
            offset = common._mean(normalized)
            span = max(abs(value - offset) for value in normalized)
        return cls(magnitude, offset, span or 1.0)

    def transform(self, value: float) -> float:
        return common._number((value / self.magnitude - self.offset) / self.span)

    def inverse(self, value: float) -> float:
        return common._number((self.offset + self.span * value) * self.magnitude)


def _solve_ridge(design: list[list[float]], targets: list[float]) -> list[float]:
    """小矩阵的部分主元高斯消元（Gaussian elimination with partial pivoting）。

    design 第一列恒为 1，表示不惩罚的截距；其他列加固定 ridge epsilon。
    矩阵用平均而不是总和，使 epsilon 不随训练行数隐式变化。
    """
    width = len(design[0])
    count = len(design)
    augmented = []
    for j in range(width):
        row = [math.fsum(values[j] * values[k] for values in design) / count
               for k in range(width)]
        if j:
            row[j] += RIDGE_EPSILON
        row.append(math.fsum(values[j] * target for values, target in zip(design, targets)) / count)
        augmented.append(row)
    for column in range(width):
        pivot = max(range(column, width), key=lambda index: abs(augmented[index][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        if divisor == 0.0 or not math.isfinite(divisor):
            raise ValueError("The regularized training system is not numerically solvable")
        augmented[column] = [value / divisor for value in augmented[column]]
        for index in range(column + 1, width):
            factor = augmented[index][column]
            augmented[index] = [value - factor * pivot_value
                                for value, pivot_value in zip(augmented[index], augmented[column])]
    coefficients = [0.0] * width
    for index in range(width - 1, -1, -1):
        coefficients[index] = common._number(augmented[index][-1] - math.fsum(
            augmented[index][column] * coefficients[column]
            for column in range(index + 1, width)
        ))
    return coefficients


def _temporal_predictions(
    train: list[dict[str, Any]], rows: list[dict[str, Any]], *, hinge: bool,
) -> list[float]:
    x_scale = _Scale.fit([common._number(row["x"]) for row in train])
    time_scale = _Scale.fit([common._number(row["timestamp"]) for row in train], time_range=True)
    y_scale = _Scale.fit([common._number(row["target"]) for row in train])

    def basis(row: dict[str, Any]) -> list[float]:
        z = x_scale.transform(common._number(row["x"]))
        u = time_scale.transform(common._number(row["timestamp"]))
        features = [z, u, common._number(z * u)]
        if hinge:
            h = max(0.0, u - HINGE_KNOT)
            features.extend((h, common._number(z * h)))
        return features

    training_basis = [basis(row) for row in train]
    column_scales = [_Scale.fit(list(column)) for column in zip(*training_basis)]

    def design_row(features: list[float]) -> list[float]:
        return [1.0] + [scale.transform(value) for scale, value in zip(column_scales, features)]

    design = [design_row(features) for features in training_basis]
    targets = [y_scale.transform(common._number(row["target"])) for row in train]
    coefficients = _solve_ridge(design, targets)
    return [y_scale.inverse(math.fsum(coefficient * value for coefficient, value in
                                    zip(coefficients, design_row(basis(row))))) for row in rows]


def _fixed_effects_predictions(
    train: list[dict[str, Any]], rows: list[dict[str, Any]],
) -> list[float]:
    """组内去均值估计共享斜率；实体截距不收缩，未知实体偏移固定为 0。"""
    x_scale = _Scale.fit([common._number(row["x"]) for row in train])
    y_scale = _Scale.fit([common._number(row["target"]) for row in train])
    grouped: dict[str, list[tuple[float, float]]] = {}
    for row in train:
        grouped.setdefault(str(row["entity_id"]), []).append((
            x_scale.transform(common._number(row["x"])),
            y_scale.transform(common._number(row["target"])),
        ))
    means = {entity: (common._mean([point[0] for point in points]),
                      common._mean([point[1] for point in points]))
             for entity, points in grouped.items()}
    within = [(x - means[entity][0], y - means[entity][1])
              for entity, points in grouped.items() for x, y in points]
    denominator = math.fsum(x * x for x, _ in within)
    slope = math.fsum(x * y for x, y in within) / denominator if denominator else 0.0
    # 行数加权的总体截距；不把某个已见实体的偏移套给未知实体。
    all_points = [point for points in grouped.values() for point in points]
    global_intercept = common._mean([y for _, y in all_points]) - slope * common._mean(
        [x for x, _ in all_points])
    intercepts = {entity: y_mean - slope * x_mean for entity, (x_mean, y_mean) in means.items()}
    return [y_scale.inverse(intercepts.get(str(row["entity_id"]), global_intercept)
                            + slope * x_scale.transform(common._number(row["x"]))) for row in rows]


def candidate_predictions(
    train: list[dict[str, Any]], rows: list[dict[str, Any]],
) -> dict[str, list[float]]:
    """返回九个固定候选的预测；原五候选直接调用 v0.1，保持结果与顺序。"""
    if not train:
        raise ValueError("Training rows cannot be empty")
    predictions = common.candidate_predictions(train, rows)
    intercept, slope = common._fit_linear(train)
    residuals: dict[str, list[float]] = {}
    for row in train:
        residuals.setdefault(str(row["entity_id"]), []).append(common._number(row["target"])
            - (intercept + slope * common._number(row["x"])))
    residual_means = {entity: common._mean(values) for entity, values in residuals.items()}
    predictions["global_linear_entity_residual"] = [
        value + residual_means.get(str(row["entity_id"]), 0.0)
        for value, row in zip(predictions["global_linear"], rows)
    ]
    predictions["entity_fixed_effects_linear"] = _fixed_effects_predictions(train, rows)
    predictions["time_linear_interaction"] = _temporal_predictions(train, rows, hinge=False)
    predictions["time_hinge_interaction"] = _temporal_predictions(train, rows, hinge=True)
    return {candidate_id: [common._number(value) for value in predictions[candidate_id]]
            for candidate_id in CANDIDATE_IDS}


def select_candidate(
    task_id: str, train: list[dict[str, Any]], strategy: str = "aligned",
) -> dict[str, Any]:
    """训练内 MSE 选模；共享 v0.1 切分，完全并列时按固定九候选顺序选。"""
    split = common.validation_split(task_id, train, strategy)
    fitting_rows = [train[index] for index in split["fit_indices"]]
    validation_rows = [train[index] for index in split["validation_indices"]]
    predictions = candidate_predictions(fitting_rows, validation_rows)
    scores = {candidate_id: common._mean([
        (prediction - common._number(row["target"])) ** 2
        for prediction, row in zip(values, validation_rows)
    ]) for candidate_id, values in predictions.items()}
    selected = min(CANDIDATE_IDS, key=lambda candidate_id: scores[candidate_id])
    return {
        "candidate_id": selected,
        "validation_mse": scores[selected],
        "validation_scores": scores,
        "validation_split": split,
    }
