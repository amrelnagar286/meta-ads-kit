@echo off
REM Monster Data Analyst -- Quick Start (Windows)
REM Double-click this file to launch the app

cd /d "%~dp0\.."

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo ============================================
echo   Monster Data Analyst is starting...
echo   Opening in your browser at:
echo   http://localhost:8501
echo ============================================
echo.

streamlit run app.py
pause
