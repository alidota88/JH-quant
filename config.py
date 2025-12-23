# config.py
import os
import json

# ==================== 基础配置 ====================
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

TS_TOKEN = os.getenv("TS_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# ==================== 策略配置 ====================
# 激活策略列表
ACTIVE_STRATEGIES = os.getenv("ACTIVE_STRATEGIES", "加权评分-极致缩量（标准）")
ACTIVE_STRATEGIES = [s.strip() for s in ACTIVE_STRATEGIES.split(",") if s.strip()]

# 自定义参数覆盖（JSON字符串）
custom_params_str = os.getenv("STRATEGY_PARAMS", "{}")
try:
    STRATEGY_CUSTOM_PARAMS = json.loads(custom_params_str)
except json.JSONDecodeError:
    print("⚠️ STRATEGY_PARAMS 格式错误，已忽略")
    STRATEGY_CUSTOM_PARAMS = {}
