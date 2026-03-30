"""
SQLAlchemy ORM model for the stock_data table.
Each row = one day of trading data for one company.
"""

from sqlalchemy import Column, Integer, String, Float, Date
from app.database.connection import Base


class StockData(Base):
    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, nullable=False, index=True)       # e.g. "INFY"
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    daily_return = Column(Float)        # (Close - Open) / Open
    moving_avg_7 = Column(Float)        # 7-day moving average of Close
    high_52w = Column(Float)            # 52-week rolling high
    low_52w = Column(Float)             # 52-week rolling low
    volatility = Column(Float)          # 20-day rolling std-dev of daily_return
