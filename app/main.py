"""
FastAPI application entry point.
Run with:  uvicorn app.main:app --reload
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database.connection import engine, SessionLocal, Base
from app.models.stock import StockData
from app.routes.stocks import router as stock_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run once on server startup — create tables and auto-fetch data if DB is empty."""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Auto-fetch data if database is empty (useful for fresh deploys on Render)
    db = SessionLocal()
    try:
        count = db.query(StockData).count()
        if count == 0:
            print("[*] Database is empty — auto-fetching stock data...")
            from app.services.data_collector import fetch_and_store_all
            fetch_and_store_all()
    finally:
        db.close()

    yield  # app runs here


app = FastAPI(
    title="Mini Stock Market Platform",
    description="Collect, analyse, and visualise Indian stock data — "
                "built with FastAPI, SQLite, and Chart.js.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- API routes ---
app.include_router(stock_router, prefix="/api", tags=["Stocks"])

# --- Serve frontend static files ---
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the HTML dashboard at the root URL."""
    return FileResponse("static/index.html")
