# database/manager.py
import pandas as pd
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from .engine import engine

def upsert_method(table, conn, keys, data_iter):
    data = [dict(zip(keys, row)) for row in data_iter]
    if not data:
        return
    stmt = insert(table.table).values(data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['ts_code', 'trade_date'])
    conn.execute(stmt)

def save_data(df: pd.DataFrame):
    if df.empty:
        return
    try:
        df.to_sql('stock_daily', engine, if_exists='append', index=False, chunksize=2000, method=upsert_method)
    except Exception as e:
        print(f"❌ [DB] Save failed: {e}")

def get_data(n_days: int = 250) -> pd.DataFrame:
    query = f"""
    SELECT * FROM stock_daily 
    WHERE trade_date >= current_date - INTERVAL '{n_days} days'
    ORDER BY ts_code, trade_date
    """
    try:
        df = pd.read_sql(query, engine)
        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df
    except Exception as e:
        print(f"❌ [DB] Load failed: {e}")
        return pd.DataFrame()

def check_data_count() -> int:
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT count(*) FROM stock_daily")).scalar()
    except:
        return 0
