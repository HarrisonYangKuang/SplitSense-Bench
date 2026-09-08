"""文件名兼容总纲；实际为 aligned reference，绝非真正 oracle。

参考解只依据训练内验证（training-only validation）选模型，不读取隐藏标签。
它不保证部署表现最好，研究结果中应称“部署对齐参考解”。
"""
from tasks.common import solve as _solve, solution_cli

TASK_ID = "temporal_iid"


def solve(train, test):
    return _solve(TASK_ID, train, test, strategy="aligned")


if __name__ == "__main__":
    solution_cli(TASK_ID, strategy="aligned")
