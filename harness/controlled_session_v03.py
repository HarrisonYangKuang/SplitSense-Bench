"""训练数据上的窄 JSON 接口；不接受代码、文件路径、网络地址或隐藏测试输入。

这是应用层能力边界（capability boundary），不是任意 Python 的操作系统沙箱。
可信驱动持有这个对象；模型只收到返回的文本，不能获取对象引用或执行 Python。
"""
from __future__ import annotations

import copy
import hashlib
import json
import math

from tasks.common import validation_split
from tasks.strong_candidates_v02 import CANDIDATE_IDS, candidate_predictions

MAX_ACTION_BYTES = 4096  # 每条模型动作的 UTF-8 字节上限。
MAX_ACTIONS = 6  # 错误动作也计数，避免无限尝试。
MAX_EVALUATIONS = 2  # 每次给出固定九候选，不能新增或改写候选。
SPLITS = {
    "random_rows": "temporal_iid",
    "forward_time": "temporal_future",
    "unseen_entities": "entity_unseen",
    "within_entities": "entity_seen",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def parse_action(text):
    if not isinstance(text, str) or len(text.encode()) > MAX_ACTION_BYTES:
        raise ValueError("Action must be a bounded JSON string")
    def reject_constant(_):
        raise ValueError("Nonfinite JSON constant")
    value = json.loads(text, object_pairs_hook=_object, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("Action must be an object")
    return value


class ControlledSession:
    """会话只接收训练表和可见部署说明；无测试、隐藏标签或任务类别参数。"""

    def __init__(self, training_rows, deployment_brief):
        if not isinstance(deployment_brief, str) or not 1 <= len(deployment_brief) <= 3000:
            raise ValueError("Invalid visible deployment brief")
        if not isinstance(training_rows, list) or not 4 <= len(training_rows) <= 1000:
            raise ValueError("Expected 4 to 1000 training rows")
        expected = {"row_id", "x", "timestamp", "entity_id", "target"}
        row_ids = set()
        for row in training_rows:
            if not isinstance(row, dict) or set(row) != expected:
                raise ValueError("Unexpected training schema")
            for key in ("row_id", "entity_id"):
                if not isinstance(row[key], str) or not 1 <= len(row[key]) <= 80:
                    raise ValueError("Invalid identifier")
            if row["row_id"] in row_ids:
                raise ValueError("Duplicate training row")
            row_ids.add(row["row_id"])
            for key in ("x", "timestamp", "target"):
                if isinstance(row[key], bool) or not isinstance(row[key], (int, float)):
                    raise ValueError("Invalid numeric observation")
                if not math.isfinite(row[key]) or abs(row[key]) > 1e9:
                    raise ValueError("Numeric observation outside supported range")
        self._train = copy.deepcopy(training_rows)
        self._brief = deployment_brief
        self._evaluations = {}
        self._commit = None
        self._events = []
        self._attempts = 0

    @property
    def committed(self):
        return self._commit is not None

    def introduction(self):
        """固定可见信息；不会根据私有任务类型提示推荐划分。"""
        counts = {}
        for row in self._train:
            counts[row["entity_id"]] = counts.get(row["entity_id"], 0) + 1
        return copy.deepcopy({
            "deployment_brief": self._brief,
            "training_rows": len(self._train),
            "columns": ["row_id", "x", "timestamp", "entity_id", "target"],
            "time_range": [min(r["timestamp"] for r in self._train), max(r["timestamp"] for r in self._train)],
            "entity_counts": counts,
            "training_preview": self._train[:8],
            "candidate_ids": list(CANDIDATE_IDS),
            "split_options": {
                "random_rows": "hold out roughly 20% of rows at random",
                "forward_time": "hold out the latest roughly 20% of unique times",
                "unseen_entities": "hold out roughly 20% of entire entities",
                "within_entities": "hold out roughly 20% within each entity; retain fitting rows for each",
            },
            "metric": "mean squared error (MSE); lower is better; training-internal only",
            "actions": [
                {"action": "evaluate", "split": "one split option"},
                {"action": "commit", "split": "a previously evaluated option", "candidate_id": "one listed candidate", "reason": "brief deployment rationale"},
            ],
            "max_evaluations": MAX_EVALUATIONS,
            "rule": "Return one plain JSON action. Evaluate before committing. Commit is irreversible. No test feedback is available.",
        })

    def dispatch(self, text):
        """每次返回可序列化结果；失败不回显未验证输入，锁定后不再产生反馈。"""
        if self.committed:
            raise RuntimeError("Session is sealed")
        if self._attempts >= MAX_ACTIONS:
            raise RuntimeError("Action budget exhausted")
        self._attempts += 1
        action = None
        try:
            action = parse_action(text)
            kind = action.get("action")
            if kind == "evaluate":
                if set(action) != {"action", "split"} or action["split"] not in SPLITS:
                    raise ValueError("Invalid evaluation action")
                split_name = action["split"]
                if split_name in self._evaluations:
                    result = copy.deepcopy(self._evaluations[split_name])
                else:
                    if len(self._evaluations) >= MAX_EVALUATIONS:
                        raise ValueError("Evaluation budget exhausted")
                    split = validation_split(SPLITS[split_name], self._train)
                    fit = [self._train[i] for i in split["fit_indices"]]
                    validation = [self._train[i] for i in split["validation_indices"]]
                    features = [{k: v for k, v in row.items() if k != "target"} for row in validation]
                    predictions = candidate_predictions(fit, features)
                    scores = {name: math.fsum((p - r["target"]) ** 2 for p, r in zip(values, validation)) / len(validation)
                              for name, values in predictions.items()}
                    result = {"ok": True, "split": split_name, "fit_indices": split["fit_indices"],
                              "validation_indices": split["validation_indices"], "candidate_mse": scores,
                              "fit_rows": len(fit), "validation_rows": len(validation),
                              "preprocessing_fit_indices": split["fit_indices"],
                              "feedback_scope": "training_internal_only"}
                    canonical(result)  # 拒绝数值溢出产生的非有限结果。
                    self._evaluations[split_name] = copy.deepcopy(result)
            elif kind == "commit":
                if set(action) != {"action", "split", "candidate_id", "reason"}:
                    raise ValueError("Invalid commit fields")
                if action["split"] not in self._evaluations or action["candidate_id"] not in CANDIDATE_IDS:
                    raise ValueError("Commit must refer to an evaluated split and listed candidate")
                if not isinstance(action["reason"], str) or not 1 <= len(action["reason"].strip()) <= 1200:
                    raise ValueError("Invalid rationale")
                pending_commit = {**copy.deepcopy(action), "training_sha256": digest(self._train),
                                  "prior_trace_sha256": digest(self._events)}
                result = {"ok": True, "sealed": True, "commit_sha256": digest(pending_commit)}
                self._commit = pending_commit  # 完整校验后才原子锁定。
            else:
                raise ValueError("Unknown action")
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            result = {"ok": False, "error": "invalid_action_or_unavailable_split", "attempts_remaining": MAX_ACTIONS - self._attempts}
        # 原始输入单独留给可信驱动；本轨迹只保留有界哈希及已验证输出。
        raw_hash = hashlib.sha256(text.encode(errors="backslashreplace")).hexdigest() if isinstance(text, str) else None
        self._events.append({"sequence": self._attempts, "request_sha256": raw_hash, "response": copy.deepcopy(result)})
        return copy.deepcopy(result)

    def receipt(self):
        """仅由可信驱动读取；深复制防止调用者更改已锁定选择。"""
        return copy.deepcopy({"status": "committed" if self.committed else "incomplete",
                              "training_sha256": digest(self._train), "commit": self._commit,
                              "events": self._events, "evaluations": self._evaluations,
                              "trace_sha256": digest(self._events)})


def run_text_agent(session, respond, *, max_calls=3):
    """respond 只收到有界 JSON 文本；不接收会话对象。无重试，无内置代码工具。

    max_calls 是整个会话模型请求上限；格式错误也消耗一次，不额外重试。
    提示采用显式 transcript，避免 SDK 隐式聊天历史夹带其它上下文。
    """
    if isinstance(max_calls, bool) or not isinstance(max_calls, int) or not 1 <= max_calls <= 3:
        raise ValueError("Unsupported call budget")
    transcript = []
    for _ in range(max_calls):
        prompt = canonical({"instructions": session.introduction(), "history": transcript})
        if len(prompt.encode()) > 24000:
            raise ValueError("Prompt budget exceeded")
        response = respond(prompt)
        if not isinstance(response, str) or len(response.encode()) > MAX_ACTION_BYTES:
            raise ValueError("Model response exceeds action boundary")
        result = session.dispatch(response)
        transcript.append({"model_action": response, "training_tool_response": result})
        if session.committed:
            break
    return {"session": session.receipt(), "transcript": transcript, "model_calls": len(transcript)}
