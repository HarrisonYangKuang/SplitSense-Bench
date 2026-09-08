"""外部评分器薄封装；只在 Agent 结束后由可信评估端调用。"""


def grade(submission_rows, hidden_rows):
    from graders.metrics import grade_submission
    return grade_submission(submission_rows, hidden_rows)
