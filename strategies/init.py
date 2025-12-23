# strategies/__init__.py
from .registry import STRATEGY_REGISTRY, get_registered_strategies
from .weighted import *  # 导入 weighted 包中 __all__ 定义的所有内容

__all__ = [
    "STRATEGY_REGISTRY",
    "get_registered_strategies",
    "run_standard",           # 来自 weighted
    "run_relaxed",            # 来自 weighted
    "WeightedScoringStrategy"
]
