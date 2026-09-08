"""随机记录验证（random-row validation）的朴素模型选择基线。"""
from tasks.common import solve as _solve, solution_cli

TASK_ID = "temporal_iid"


def solve(train, test):
    return _solve(TASK_ID, train, test, strategy="random")


if __name__ == "__main__":
    solution_cli(TASK_ID, strategy="random")
