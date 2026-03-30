# Mini Stock Market Data Platform

A full-stack mini financial data platform built with **FastAPI**, **SQLite**, **pandas**, and **Chart.js**.

## Features

- Fetches 1-year daily stock data for 5 Indian NSE companies (INFY, TCS, RELIANCE, HDFCBANK, ICICIBANK)
- Cleans data and computes metrics: Daily Return, 7-day MA, 52-week High/Low, Volatility
- REST APIs with Swagger documentation
- Premium interactive dashboard with price charts, summary cards, and stock comparison

## Project Structure

```
project/
├── app/
│   ├── main.py                       # FastAPI app entry point
│   ├── routes/stocks.py              # API endpoints (4 routes)
│   ├── services/data_collector.py    # yfinance fetch + pandas cleaning
│   ├── models/stock.py               # SQLAlchemy ORM model
│   ├── models/schemas.py             # Pydantic response schemas
│   └── database/connection.py        # SQLite engine & session
├── static/index.html                 # Premium frontend dashboard
├── data/                             # SQLite DB (generated at runtime)
├── collect_data.py                   # Run once to populate DB
├── requirements.txt
└── README.md
```

## Setup Instructions

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <repo-name>

# 2. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Fetch stock data (takes ~30 seconds, downloads from Yahoo Finance)
python collect_data.py

# 5. Start the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the dashboard.
Open **http://127.0.0.1:8000/docs** for Swagger API docs.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies` | List all tracked companies |
| GET | `/api/data/{symbol}?days=30` | Daily stock data (default 30 days, max 365) |
| GET | `/api/summary/{symbol}` | 52-week high, low, avg close, volatility |
| GET | `/api/compare?symbol1=INFY&symbol2=TCS&days=30` | Compare closing prices of two stocks |

### Example API Usage

```bash
# Get all companies
curl http://127.0.0.1:8000/api/companies

# Get 90 days of TCS data
curl http://127.0.0.1:8000/api/data/TCS?days=90

# Get RELIANCE summary
curl http://127.0.0.1:8000/api/summary/RELIANCE

# Compare INFY vs HDFCBANK
curl "http://127.0.0.1:8000/api/compare?symbol1=INFY&symbol2=HDFCBANK&days=30"
```

## Logic & How It Works

### Data Collection (`collect_data.py`)
1. **Fetch** — Uses `yfinance` library to download 1 year of daily OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance's free public API. No API key required.
2. **Clean** — Handles missing values using forward-fill and back-fill. Converts date columns to proper datetime format. Drops any remaining NaN rows.
3. **Enrich** — Adds calculated metrics on the cleaned data:
   - **Daily Return** = `(Close - Open) / Open` — measures intraday price movement
   - **7-Day Moving Average** = rolling mean of Close — smooths out short-term noise
   - **52-Week High/Low** = rolling max/min over 252 trading days — key support/resistance levels
   - **Volatility** (custom metric) = 20-day rolling standard deviation of daily returns — measures how risky/unstable the stock is
4. **Store** — Saves all processed data into a local SQLite database (`data/stocks.db`)
5. **Fallback** — If Yahoo Finance is unreachable (network issues, rate limiting), the system auto-generates realistic mock data using a random walk model so the project works offline too.

### Backend (FastAPI)
- **Modular architecture** — Separated into routes, services, models, and database layers
- **Pydantic schemas** — All API responses are validated through typed Pydantic models
- **Error handling** — Returns proper 404 errors for invalid symbols or empty data
- **Swagger docs** — Auto-generated interactive API documentation at `/docs`

### Frontend (Chart.js Dashboard)
- **Glassmorphism UI** — Modern premium design with backdrop blur, gradients, and animations
- **Interactive charts** — Line charts with gradient fills, hover tooltips, and smooth transitions
- **Company comparison** — Overlay two stocks on the same chart for side-by-side analysis
- **Time filters** — Switch between 30-day, 90-day, and 1-year views

## Key Insights from the Data

1. **Volatility as a risk indicator** — Stocks like RELIANCE tend to show higher volatility during quarterly results, making the 20-day rolling std-dev metric useful for identifying risky periods.

2. **Moving Average crossovers** — When the stock price crosses above/below the 7-day MA, it often signals short-term trend changes. This is visible in the dashboard charts.

3. **52-Week Range positioning** — Stocks trading near their 52-week low (like the summary cards show) may indicate either a buying opportunity or continued downtrend — the comparison feature helps judge relative performance.

4. **Intraday returns distribution** — Most daily returns cluster around 0% (normal distribution), but occasional outliers (>2%) indicate significant market events or earnings announcements.

5. **Correlation between stocks** — The compare feature reveals that banking stocks (HDFCBANK, ICICIBANK) tend to move together, while IT stocks (INFY, TCS) follow a different pattern, demonstrating sector-based correlation.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Data Processing:** yfinance + pandas + numpy
- **Frontend:** HTML + CSS + Chart.js
- **Data Source:** Yahoo Finance (free public API, no key needed)
