"""仅修正动作说明与错误反馈；保留 v0.3 原始实现及失败运行不变。"""
import copy
from harness.controlled_session_v03 import ControlledSession as OriginalSession, SPLITS, parse_action
from tasks.strong_candidates_v02 import CANDIDATE_IDS


class ControlledSession(OriginalSession):
    def introduction(self):
        result = super().introduction()
        has_evaluation = bool(self._evaluations)
        result["wire_contract"] = {
            "evaluate": {"type": "object", "additionalProperties": False,
                         "required": ["action", "split"],
                         "properties": {"action": {"const": "evaluate"}, "split": {"enum": list(SPLITS)}}},
            "commit": {"type": "object", "additionalProperties": False,
                       "required": ["action", "split", "candidate_id", "reason"],
                       "properties": {"action": {"const": "commit"}, "split": {"enum": list(self._evaluations)},
                                      "candidate_id": {"enum": list(CANDIDATE_IDS)},
                                      "reason": {"type": "string", "minLength": 1, "maxLength": 1200}}},
        }
        result["permitted_actions_now"] = ["evaluate", "commit"] if has_evaluation else ["evaluate"]
        result["model_requests_remaining"] = 3 - self._attempts
        result["rule"] = (
            'Output one JSON object using the exact field name "action" and required field "split". '
            'The first action must evaluate a split. Its only two keys are "action" and "split". '
            'Choose a split from split_options according to the deployment brief. '
            'After observing evaluation results, commit using exactly action, split, candidate_id, reason. '
            'Use a previously evaluated split; no extra keys. No test feedback is available. '
            'There are at most 3 model requests for this entire session, including errors.'
        )
        return result

    def dispatch(self, text):
        if self._attempts >= 3:
            raise RuntimeError("Model action budget exhausted")
        result = super().dispatch(text)
        if not result["ok"]:
            result["attempts_remaining"] = 3 - self._attempts
            codes = []
            try:
                action = parse_action(text)
                if "action" not in action:
                    codes.append("missing_required_field_action")
                if "split" not in action:
                    codes.append("missing_required_field_split")
                kind = action.get("action")
                if kind == "evaluate":
                    allowed = {"action", "split"}
                elif kind == "commit":
                    allowed = {"action", "split", "candidate_id", "reason"}
                    if not self._evaluations:
                        codes.append("commit_requires_prior_evaluation")
                    for field in ("candidate_id", "reason"):
                        if field not in action:
                            codes.append("missing_required_field_" + field)
                else:
                    allowed = {"action", "split", "candidate_id", "reason"}
                    codes.append("action_must_be_evaluate_or_commit")
                if set(action) - allowed:
                    codes.append("unexpected_fields")
                result["allowed_fields_for_action"] = sorted(allowed)
            except (ValueError, TypeError, RecursionError):
                codes.append("expected_plain_utf8_json_object")
            result["contract_errors"] = codes or ["invalid_value_or_unavailable_split"]
            result["permitted_actions_now"] = ["evaluate", "commit"] if self._evaluations else ["evaluate"]
            # 只反馈格式和执行前置条件；不替模型选择 split/candidate。
            self._events[-1]["response"] = copy.deepcopy(result)
        return copy.deepcopy(result)
