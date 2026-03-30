# Mini Stock Market Data Platform

A full-stack mini financial data platform built with **FastAPI**, **SQLite**, **pandas**, and **Chart.js**.

## Features

- Fetches 1-year daily stock data for 5 Indian companies (INFY, TCS, RELIANCE, HDFCBANK, ICICIBANK)
- Cleans data and computes metrics: Daily Return, 7-day MA, 52-week High/Low, Volatility
- REST APIs with Swagger docs
- Interactive dashboard with price charts, summary cards, and stock comparison

## Project Structure

```
Task/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── routes/stocks.py     # API endpoints
│   ├── services/data_collector.py  # yfinance fetch + pandas cleaning
│   ├── models/stock.py      # SQLAlchemy ORM model
│   ├── models/schemas.py    # Pydantic response schemas
│   └── database/connection.py  # SQLite engine & session
├── static/index.html        # Frontend dashboard
├── data/                    # SQLite DB stored here
├── collect_data.py          # Run once to populate DB
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch stock data (takes ~30 seconds)
python collect_data.py

# 4. Start the server
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the dashboard.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies` | List all tracked companies |
| GET | `/api/data/{symbol}?days=30` | Daily stock data (default 30 days) |
| GET | `/api/summary/{symbol}` | 52-week high, low, avg close, volatility |
| GET | `/api/compare?symbol1=INFY&symbol2=TCS&days=30` | Compare closing prices |

Full interactive docs at **http://127.0.0.1:8000/docs** (Swagger UI).

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Data:** yfinance + pandas + numpy
- **Frontend:** HTML + CSS + Chart.js
