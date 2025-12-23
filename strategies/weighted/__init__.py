# strategies/weighted/__init__.py
# 这个文件的作用是把子模块中的策略函数导出到上层，方便 strategies/__init__.py 导入
from .extreme_shrink import (
    run_standard,
    run_relaxed,
    WeightedScoringStrategy  # 可选，如果你想直接导入类
)

__all__ = [
    "run_standard",
    "run_relaxed",
    "WeightedScoringStrategy"
]
