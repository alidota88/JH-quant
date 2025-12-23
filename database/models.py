# database/models.py
from sqlalchemy import Column, String, Float, Date
from sqlalchemy.orm import declarative_base

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
