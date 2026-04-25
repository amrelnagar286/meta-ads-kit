@echo off
REM ─────────────────────────────────────────────────────
REM  Meta Ads Ultimate Dashboard — Windows Launch Script
REM ─────────────────────────────────────────────────────
title Meta Ads Dashboard

echo.
echo  ====================================================
echo    ULTIMATE Meta Ads Dashboard
echo    Windows 11 Edition
echo  ====================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM Ensure venv exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt --quiet

REM Create directories
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "config" mkdir config
if not exist "data" mkdir data

REM Launch
echo.
echo [INFO] Starting Streamlit dashboard...
echo [INFO] Open http://localhost:8501 in your browser
echo.
streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
