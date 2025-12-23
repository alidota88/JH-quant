# database.py
import os
from sqlalchemy import create_engine, Column, String, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StockDaily(Base):
    __tablename__ = "stock_daily"
    ts_code = Column(String(20), primary_key=True, index=True)
    trade_date = Column(Date, primary_key=True, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    vol = Column(Float)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ [Database] Schema initialized successfully.")
    except Exception as e:
        print(f"❌ [Database] Initialization failed: {e}")
