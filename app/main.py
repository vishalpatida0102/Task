"""
FastAPI application entry point.
Run with:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database.connection import engine, Base
from app.routes.stocks import router as stock_router

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Stock Market Platform",
    description="Collect, analyse, and visualise Indian stock data — "
                "built with FastAPI, SQLite, and Chart.js.",
    version="1.0.0",
)

# --- API routes ---
app.include_router(stock_router, prefix="/api", tags=["Stocks"])

# --- Serve frontend static files ---
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serve the HTML dashboard at the root URL."""
    return FileResponse("static/index.html")
