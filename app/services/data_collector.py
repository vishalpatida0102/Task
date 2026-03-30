"""
Data collection service.
- PRIMARY:  Fetches 1 year of daily stock data from Yahoo Finance (FREE public API via yfinance)
- FALLBACK: If yfinance fails (network issues, rate-limit, geo-block), generates
            realistic mock data so the project still works offline.

No API key needed! yfinance uses Yahoo Finance's public endpoints.
"""

import numpy as np
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.connection import engine, SessionLocal, Base
from app.models.stock import StockData

# ─── Companies to track ─────────────────────────────────────────
# Yahoo Finance uses .NS suffix for NSE (National Stock Exchange, India)
# yfinance automatically hits Yahoo's FREE public API — no key required.
COMPANIES = {
    "INFY":      "INFY.NS",
    "TCS":       "TCS.NS",
    "RELIANCE":  "RELIANCE.NS",
    "HDFCBANK":  "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
}

# Realistic base prices for mock data generation (in INR)
_MOCK_BASE_PRICES = {
    "INFY": 1500, "TCS": 3800, "RELIANCE": 2500,
    "HDFCBANK": 1600, "ICICIBANK": 1100,
}


def fetch_and_store_all():
    """Main entry point — fetches, cleans, and stores data for every company."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for symbol, ticker in COMPANIES.items():
            print(f"[+] Fetching data for {symbol} ({ticker}) ...")

            # --- Try live API first, fall back to mock ---
            df = _fetch_stock_data(ticker)

            if df.empty:
                print(f"[!] yfinance returned no data for {symbol}. Using mock data instead.")
                df = _generate_mock_data(symbol)

            df = _clean_data(df)
            df = _add_metrics(df)
            _save_to_db(db, symbol, df)
            print(f"[OK] Saved {len(df)} rows for {symbol}")

        db.commit()
        print("\n=== All data collected and stored successfully! ===")
    finally:
        db.close()


# ─── DATA SOURCES ────────────────────────────────────────────────

def _fetch_stock_data(ticker: str) -> pd.DataFrame:
    """
    Download last 1 year of daily OHLCV data from Yahoo Finance.
    This is a FREE public API — no API key or account needed.
    yfinance just scrapes Yahoo Finance endpoints behind the scenes.
    """
    try:
        end = datetime.today()
        start = end - timedelta(days=365)
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            progress=False,
        )
        return df
    except Exception as e:
        print(f"[!] yfinance error: {e}")
        return pd.DataFrame()


def _generate_mock_data(symbol: str) -> pd.DataFrame:
    """
    Generate 1 year of realistic-looking stock data.
    Used as fallback when yfinance can't connect.
    Uses random walk with drift to simulate real price movement.
    """
    np.random.seed(hash(symbol) % 2**31)  # reproducible per symbol

    base_price = _MOCK_BASE_PRICES.get(symbol, 1000)
    days = 252  # ~1 year of trading days
    dates = pd.bdate_range(end=datetime.today(), periods=days)  # business days only

    # Random walk: daily returns ~ N(0.0004, 0.018) ≈ realistic Indian market
    daily_returns = np.random.normal(0.0004, 0.018, days)
    close_prices = base_price * np.cumprod(1 + daily_returns)

    # Build OHLCV from close prices
    df = pd.DataFrame({
        "Date":   dates,
        "Open":   close_prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        "High":   close_prices * (1 + np.random.uniform(0.001, 0.025, days)),
        "Low":    close_prices * (1 - np.random.uniform(0.001, 0.025, days)),
        "Close":  close_prices,
        "Volume": np.random.randint(500_000, 10_000_000, days),
    })

    return df


# ─── CLEANING & METRICS ─────────────────────────────────────────

def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values and ensure proper types."""
    # Flatten multi-level columns that yfinance sometimes returns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Reset index so Date becomes a regular column
    if "Date" not in df.columns:
        df = df.reset_index()
    df["Date"] = pd.to_datetime(df["Date"])

    # Forward-fill then back-fill small gaps (holidays / missing rows)
    df = df.ffill().bfill()

    # Drop rows where Close is still NaN
    df = df.dropna(subset=["Close"])

    return df


def _add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived columns on the cleaned dataframe."""
    # Daily Return = intraday percentage change
    df["Daily_Return"] = (df["Close"] - df["Open"]) / df["Open"]

    # 7-day simple moving average of Close
    df["MA_7"] = df["Close"].rolling(window=7, min_periods=1).mean()

    # 52-week (252 trading days) rolling High and Low
    df["High_52W"] = df["High"].rolling(window=252, min_periods=1).max()
    df["Low_52W"] = df["Low"].rolling(window=252, min_periods=1).min()

    # CUSTOM METRIC — Volatility: 20-day rolling std-dev of Daily Return
    df["Volatility"] = df["Daily_Return"].rolling(window=20, min_periods=1).std()

    return df


# ─── DATABASE ────────────────────────────────────────────────────

def _save_to_db(db: Session, symbol: str, df: pd.DataFrame):
    """Insert cleaned rows into the stock_data table (replaces old data)."""
    # Delete previous rows for this symbol to avoid duplicates on re-run
    db.query(StockData).filter(StockData.symbol == symbol).delete()

    records = [
        StockData(
            symbol=symbol,
            date=row["Date"].date(),
            open=round(float(row["Open"]), 2),
            high=round(float(row["High"]), 2),
            low=round(float(row["Low"]), 2),
            close=round(float(row["Close"]), 2),
            volume=int(row["Volume"]),
            daily_return=round(float(row["Daily_Return"]), 6) if pd.notna(row["Daily_Return"]) else None,
            moving_avg_7=round(float(row["MA_7"]), 2) if pd.notna(row["MA_7"]) else None,
            high_52w=round(float(row["High_52W"]), 2) if pd.notna(row["High_52W"]) else None,
            low_52w=round(float(row["Low_52W"]), 2) if pd.notna(row["Low_52W"]) else None,
            volatility=round(float(row["Volatility"]), 6) if pd.notna(row["Volatility"]) else None,
        )
        for _, row in df.iterrows()
    ]
    db.bulk_save_objects(records)
