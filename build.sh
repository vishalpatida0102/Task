#!/usr/bin/env bash
# Render build script — runs during every deploy

set -e

# Install Python dependencies
pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Fetch stock data and populate the database
python collect_data.py
