#!/usr/bin/env bash
# Chạy dashboard backtest trên macOS/Linux.
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
streamlit run dashboard/app.py
