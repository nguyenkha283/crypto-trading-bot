@echo off
REM Chạy dashboard backtest trên Windows.
REM Lần đầu nhớ: python -m venv .venv  &&  pip install -r requirements.txt
call .venv\Scripts\activate
streamlit run dashboard\app.py
