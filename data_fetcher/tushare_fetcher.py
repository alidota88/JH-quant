# data_fetcher/tushare_fetcher.py
import os
import time
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from database import save_data, engine
from config import TS_TOKEN

if TS_TOKEN:
    ts.set_token(TS_TOKEN)
    pro = ts.pro_api()
else:
    print("⚠️ TS_TOKEN not found.")
    pro = None

def fetch_daily_data(trade_date_str: str):
    if not pro: return
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"⬇️ Fetching {trade_date_str} (Attempt {attempt+1})")
            df = pro.daily(trade_date=trade_date_str)
            if df.empty:
                print(f"   No data (holiday?)")
                return
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            save_data(df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']])
            return
        except Exception as e:
            print(f"   Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

def backfill_data(lookback_days: int = 200):
    print(f"🔄 Backfilling last {lookback_days} days...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    target_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d').tolist()

    try:
        query = f"SELECT DISTINCT trade_date::text FROM stock_daily WHERE trade_date >= '{start_date.date()}'"
        existing = pd.read_sql(query, engine)['trade_date'].str.replace("-", "").tolist()
    except:
        existing = []

    missing = [d for d in target_dates if d not in existing]
    missing.sort()

    if not missing:
        print("✅ Data complete.")
        return

    for date_str in missing:
        fetch_daily_data(date_str)
        time.sleep(0.5)
    print("✅ Backfill complete.")
