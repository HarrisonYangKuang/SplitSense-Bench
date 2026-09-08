"""temporal_future 的内存生成和显式 CSV 导出入口。"""
from tasks.common import generate as _generate, generator_cli

TASK_ID = "temporal_future"


def generate(seed: int, scale: str = "smoke"):
    return _generate(TASK_ID, seed, scale)


if __name__ == "__main__":
    generator_cli(TASK_ID)
