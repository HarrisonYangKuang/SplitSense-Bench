"""v0.4 离线阶段控制器；无模型客户端，未获真实云端运行验收。

状态随实际动作更新；不根据最小误差代替模型选择候选。
依赖旧版可信训练工具，旧版源码和原始运行保持不变。
"""
import copy
import hashlib

from harness.controlled_session_v03 import canonical, parse_action, MAX_ACTION_BYTES
from harness.controlled_session_v03a import ControlledSession as PriorSession

REQUEST_BUDGET = 3  # 整个会话最多三次回应机会；包括错误动作。


class PhaseSession(PriorSession):
    def __init__(self, training_rows, deployment_brief):
        super().__init__(training_rows, deployment_brief)
        self._closed_reason = None

    def control(self):
        remaining = REQUEST_BUDGET - self._attempts
        if self.committed:
            phase, allowed = "sealed", []
        elif self._closed_reason:
            phase, allowed = "closed", []
        elif remaining <= 0:
            phase, allowed = "exhausted", []
        elif not self._evaluations:
            # 一次评估之后至少还要有一次回应机会用于提交。
            phase, allowed = ("choose_validation", ["evaluate"]) if remaining >= 2 else ("insufficient_budget", [])
        elif remaining == 1 or len(self._evaluations) == 2:
            phase, allowed = "commit_required", ["commit"]
        else:
            phase, allowed = "review_results", ["evaluate", "commit"]
        return {"phase": phase, "permitted_actions_now": allowed,
                "action_opportunities_remaining": remaining,
                "already_evaluated_splits": list(self._evaluations)}

    def introduction(self):
        intro = super().introduction()
        control = self.control()
        allowed = control["permitted_actions_now"]
        rules = {
            "choose_validation": "Choose a validation split from the listed options. Return exactly action and split, with action=evaluate. A later response will select the candidate.",
            "review_results": "Evaluation results are available in history. Choose a candidate and commit, or evaluate one different split. Repeating an evaluated split is rejected. Commit requires action, split, candidate_id, reason.",
            "commit_required": "Evaluation is complete and only a commit action is permitted now. Choose a candidate yourself using the visible results and deployment brief. Return exactly action, split, candidate_id, reason. Use an already evaluated split.",
            "sealed": "The final choice is sealed; no further action is accepted.",
            "closed": "The session has stopped after a response failure; no further action is accepted.",
            "exhausted": "The action budget is exhausted. No final choice is inferred.",
            "insufficient_budget": "There is insufficient budget for both evaluation and commit. The session stops without a final choice.",
        }
        intro["rule"] = rules[control["phase"]] + " Return plain JSON with exact field names. No hidden test feedback is available."
        intro.update(control)
        intro.pop("model_requests_remaining", None)
        intro["actions"] = [a for a in intro["actions"] if a["action"] in allowed]
        intro["wire_contract"] = {k: v for k, v in intro["wire_contract"].items() if k in allowed}
        if "evaluate" in allowed:
            options = [name for name in intro["split_options"] if name not in self._evaluations]
            intro["wire_contract"]["evaluate"]["properties"]["split"]["enum"] = options
        return intro

    def dispatch(self, text):
        control = self.control()
        if not control["permitted_actions_now"]:
            raise RuntimeError("No further action is permitted")
        error = None
        try:
            action = parse_action(text)
            if action.get("action") in ("evaluate", "commit"):
                if action["action"] not in control["permitted_actions_now"]:
                    error = "action_not_permitted_in_current_phase"
                elif action["action"] == "evaluate" and isinstance(action.get("split"), str) and action["split"] in self._evaluations:
                    error = "split_already_evaluated_use_existing_results"
        except (ValueError, TypeError, RecursionError):
            pass  # 旧版解析器会记录格式错误；不自动修正字段。
        if error:
            self._attempts += 1
            response = {"ok": False, "error": error}
            self._events.append({"sequence": self._attempts,
                                 "request_sha256": hashlib.sha256(text.encode(errors="backslashreplace")).hexdigest(),
                                 "response": response})
        else:
            response = super().dispatch(text)
        response.update(self.control())
        response["attempts_remaining"] = REQUEST_BUDGET - self._attempts
        self._events[-1]["response"] = copy.deepcopy(response)
        return copy.deepcopy(response)

    def close(self, reason):
        if not self.committed:
            self._closed_reason = reason

    def receipt(self):
        value = super().receipt()
        value["controller_version"] = "0.4-offline-only"
        value["control"] = self.control()
        value["closed_reason"] = self._closed_reason
        return value


def run_session(session, respond):
    """用模拟回应或离线记录测试流程；本模块没有真实模型连接。

    请求尝试在回调前计数；回调异常也保留此前轨迹，并关闭本会话。
    未来真实适配器仍需独立核验额度、请求前落盘、硬超时及模型身份。
    """
    if session.receipt()["events"] or session.committed or session._closed_reason:
        raise ValueError("Driver requires a fresh session")
    transcript, errors = [], []
    attempts = 0
    while attempts < REQUEST_BUDGET and session.control()["permitted_actions_now"]:
        prompt = canonical({"instructions": session.introduction(), "history": transcript})
        if len(prompt.encode()) > 24000:
            errors.append({"code": "prompt_budget_exceeded"})
            session.close("prompt_budget_exceeded")
            break
        attempts += 1
        try:
            response = respond(prompt)
            if not isinstance(response, str) or len(response.encode()) > MAX_ACTION_BYTES:
                raise ValueError("Invalid response boundary")
        except Exception as error:
            errors.append({"attempt": attempts, "code": "response_failed", "type": type(error).__name__})
            session.close("response_failed")
            break
        outcome = session.dispatch(response)
        transcript.append({"model_action": response, "training_tool_response": outcome})
    return {"session": session.receipt(), "transcript": transcript,
            "attempted_responses": attempts, "received_responses": len(transcript),
            "errors": errors, "execution_mode": "offline_simulated_or_recorded_responses"}
