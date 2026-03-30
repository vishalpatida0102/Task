"""
Stock API routes — all endpoints live under the /api prefix (added in main.py).
"""

from datetime import date, timedelta
from typing import List
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.connection import get_db
from app.models.stock import StockData
from app.models.schemas import (
    StockRecord, CompanyItem, SummaryResponse,
    CompareResponse, CompareRecord,
)
from app.services.data_collector import COMPANIES

router = APIRouter()


# ─── GET /companies ─────────────────────────────────────────────
@router.get("/companies", response_model=List[CompanyItem],
            summary="List all tracked companies")
def get_companies():
    """Returns the list of stock symbols available in the platform."""
    return [
        CompanyItem(symbol=sym, name=sym) for sym in COMPANIES
    ]


# ─── GET /data/{symbol} ─────────────────────────────────────────
@router.get("/data/{symbol}", response_model=List[StockRecord],
            summary="Get recent stock data for a symbol")
def get_stock_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of past days to return"),
    db: Session = Depends(get_db),
):
    """
    Returns daily stock data for the given symbol.
    Use the `days` query param to control the window (default 30).
    """
    symbol = symbol.upper()
    if symbol not in COMPANIES:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(StockData)
        .filter(StockData.symbol == symbol, StockData.date >= cutoff)
        .order_by(StockData.date.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No data available for this period")
    return rows


# ─── GET /summary/{symbol} ──────────────────────────────────────
@router.get("/summary/{symbol}", response_model=SummaryResponse,
            summary="52-week summary stats for a symbol")
def get_summary(symbol: str, db: Session = Depends(get_db)):
    """
    Returns:
    - 52-week high & low
    - Average closing price
    - Latest close and volatility
    """
    symbol = symbol.upper()
    if symbol not in COMPANIES:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

    stats = (
        db.query(
            func.max(StockData.high_52w).label("high_52w"),
            func.min(StockData.low_52w).label("low_52w"),
            func.avg(StockData.close).label("avg_close"),
        )
        .filter(StockData.symbol == symbol)
        .first()
    )

    latest = (
        db.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(StockData.date.desc())
        .first()
    )

    if not latest:
        raise HTTPException(status_code=404, detail="No data found")

    return SummaryResponse(
        symbol=symbol,
        high_52w=round(stats.high_52w, 2) if stats.high_52w else None,
        low_52w=round(stats.low_52w, 2) if stats.low_52w else None,
        avg_close=round(stats.avg_close, 2) if stats.avg_close else None,
        latest_close=latest.close,
        latest_volatility=latest.volatility,
    )


# ─── GET /compare ───────────────────────────────────────────────
@router.get("/compare", response_model=CompareResponse,
            summary="Compare closing prices of two stocks")
def compare_stocks(
    symbol1: str = Query(..., description="First stock symbol"),
    symbol2: str = Query(..., description="Second stock symbol"),
    days: int = Query(30, ge=1, le=365, description="Comparison window in days"),
    db: Session = Depends(get_db),
):
    """
    Returns date-aligned closing prices for two symbols so you can
    overlay them on a chart.
    """
    symbol1, symbol2 = symbol1.upper(), symbol2.upper()
    for s in (symbol1, symbol2):
        if s not in COMPANIES:
            raise HTTPException(status_code=404, detail=f"Symbol '{s}' not found")

    cutoff = date.today() - timedelta(days=days)

    rows1 = {
        r.date: r.close
        for r in db.query(StockData)
        .filter(StockData.symbol == symbol1, StockData.date >= cutoff)
        .all()
    }
    rows2 = {
        r.date: r.close
        for r in db.query(StockData)
        .filter(StockData.symbol == symbol2, StockData.date >= cutoff)
        .all()
    }

    # Merge on common dates
    common_dates = sorted(set(rows1.keys()) & set(rows2.keys()))
    data = [
        CompareRecord(date=d, close_1=rows1[d], close_2=rows2[d])
        for d in common_dates
    ]

    return CompareResponse(symbol1=symbol1, symbol2=symbol2, data=data)
