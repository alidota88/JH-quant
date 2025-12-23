# main.py
import os
import time
import json
import schedule
import requests
import pandas as pd
from datetime import datetime
from database import init_db
from db_manager import get_data, check_data_count
from data_fetcher import backfill_data
from strategy import STRATEGY_REGISTRY

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# ==================== 配置 ====================
# 激活的策略列表（逗号分隔），默认只跑标准版
active_strategies = os.getenv("ACTIVE_STRATEGIES", "加权评分-极致缩量（标准）")
active_strategies = [s.strip() for s in active_strategies.split(",") if s.strip()]

# 自定义参数覆盖（JSON格式），例如：{"加权评分-极致缩量（标准）": {"min_score": 55}}
custom_params_str = os.getenv("STRATEGY_PARAMS", "{}")
try:
    custom_params = json.loads(custom_params_str)
except:
    print("⚠️ STRATEGY_PARAMS 格式错误，已忽略")
    custom_params = {}

def send_telegram(message):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except:
        pass

def execute_logic(is_test=False):
    print("------------------------------------------------")
    print(f"🔥 [JH-quant] Starting... (Test: {is_test}) | 策略: {', '.join(active_strategies)}")
    
    # 数据补全
    try:
        backfill_data(lookback_days=200)
    except Exception as e:
        print(f"⚠️ Backfill interrupted: {e}")

    row_count = check_data_count()
    print(f"📉 Data rows: {row_count}")
    if row_count < 10000:
        send_telegram("❌ 数据量过少，无法运行策略")
        return

    df = get_data(n_days=250)
    date_str = datetime.now().strftime("%Y-%m-%d")

    sent_count = 0
    for strategy_name in active_strategies:
        if strategy_name not in STRATEGY_REGISTRY:
            print(f"⚠️ 未找到策略: {strategy_name}")
            continue

        entry = STRATEGY_REGISTRY[strategy_name]
        run_func = entry['func']
        base_params = entry['default_params'].copy()
        
        # 环境变量参数覆盖
        if strategy_name in custom_params:
            base_params.update(custom_params[strategy_name])

        print(f"🧠 Running: {strategy_name} (params: {base_params.get('min_score', '?')}+)")
        results = run_func(df, params=base_params)

        if results.empty:
            msg = f"📭 **{strategy_name}** ({date_str})\n\n今日无股票命中信号。"
            send_telegram(msg)
            print(f"   无结果")
            continue

        top = results.head(10)
        msg_lines = [
            f"🏆 **{strategy_name} TOP 10** ({date_str})",
            "---",
            f"📊 入选库：{len(results)} 只\n"
        ]

        for i, (_, row) in enumerate(top.iterrows()):
            rank = i + 1
            icon = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"{rank}."
            score = row.get('总分', 'N/A')
            line = (
                f"{icon} `{row['ts_code']}` 💰{row['close']:.2f}\n"
                f"   **总分: {score}** | {row.get('reason', '信号命中')}\n"
            )
            msg_lines.append(line)

        send_telegram("\n".join(msg_lines))
        print(f"✅ {strategy_name}: 已推送 {len(top)} 只")
        sent_count += 1

    if sent_count == 0:
        send_telegram(f"⚠️ 今日所有策略均无信号 ({date_str})")
    
    print("------------------------------------------------")

def main():
    print("🚀 JH-quant System Starting...")
    init_db()
    
    # 启动时立即运行一次
    try:
        execute_logic(is_test=True)
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        send_telegram(f"❌ JH-quant 启动报错: {e}")

    # 每天 08:30 运行
    schedule.every().day.at("08:30").do(execute_logic)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
