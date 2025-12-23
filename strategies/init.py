# strategies/__init__.py
from .registry import STRATEGY_REGISTRY, get_registered_strategies
from .weighted.extreme_shrink import *  # 导出注册的函数
