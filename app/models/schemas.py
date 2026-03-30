"""
Pydantic response models for API endpoints.
These define the shape of JSON responses and show up in Swagger docs.
"""

from pydantic import BaseModel
from datetime import date
from typing import List, Optional


class StockRecord(BaseModel):
    """Single day of stock data."""
    symbol: str
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]
    daily_return: Optional[float]
    moving_avg_7: Optional[float]
    high_52w: Optional[float]
    low_52w: Optional[float]
    volatility: Optional[float]

    model_config = {"from_attributes": True}


class CompanyItem(BaseModel):
    """Company entry in the /companies list."""
    symbol: str
    name: str


class SummaryResponse(BaseModel):
    """Summary stats for one stock."""
    symbol: str
    high_52w: Optional[float]
    low_52w: Optional[float]
    avg_close: Optional[float]
    latest_close: Optional[float]
    latest_volatility: Optional[float]


class CompareRecord(BaseModel):
    """One date-point when comparing two stocks."""
    date: date
    close_1: Optional[float]
    close_2: Optional[float]


class CompareResponse(BaseModel):
    """Full comparison response."""
    symbol1: str
    symbol2: str
    data: List[CompareRecord]
