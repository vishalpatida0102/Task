"""
Standalone script to fetch stock data and populate the database.
Run this ONCE before starting the FastAPI server:

    python collect_data.py
"""

from app.services.data_collector import fetch_and_store_all

if __name__ == "__main__":
    fetch_and_store_all()
