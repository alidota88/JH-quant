# main.py
import time
import schedule
from datetime import datetime
from database import init_db, check_data_count, get_data
from data_fetcher import backfill_data
from strategies import STRATEGY_REGISTRY
from notifier import send_message
from config import ACTIVE_STRATEGIES, STRATEGY_CUSTOM_PARAMS

def execute():
    print(f"🔥 JH-quant 执行 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        backfill_data(200)
    except Exception as e:
        print(f"Backfill error: {e}")

    if check_data_count() < 10000:
        send_message("❌ 数据量不足，无法运行策略")
        return

    df = get_data(250)
    date_str = datetime.now().strftime("%Y-%m-%d")
    sent = 0

    for name in ACTIVE_STRATEGIES:
        if name not in STRATEGY_REGISTRY:
            print(f"⚠️ 策略未注册: {name}")
            continue

        entry = STRATEGY_REGISTRY[name]
        params = entry['default_params'].copy()
        if name in STRATEGY_CUSTOM_PARAMS:
            params.update(STRATEGY_CUSTOM_PARAMS[name])

        print(f"🧠 运行 {name}")
        results = entry['func'](df, params=params)

        if results.empty:
            send_message(f"📭 **{name}** ({date_str})\n\n今日无信号")
            continue

        top = results.head(10)
        lines = [f"🏆 **{name} TOP 10** ({date_str})", "---", f"入选：{len(results)}只\n"]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            icon = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
            lines.append(
                f"{icon} `{row['ts_code']}` 💰{row['close']:.2f}\n"
                f"   **{row.get('总分', '?')}分** | {row.get('reason', '信号')}"
            )
        send_message("\n".join(lines))
        sent += 1

    if sent == 0:
        send_message(f"⚠️ 今日无任何策略信号 ({date_str})")
    print("✅ 执行完成\n")

if __name__ == "__main__":
    print("🚀 JH-quant 启动")
    init_db()
    execute()  # 启动立即执行一次
    schedule.every().day.at("08:30").do(execute)
    while True:
        schedule.run_pending()
        time.sleep(60)
