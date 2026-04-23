@echo off
REM Quick-start launcher for Windows
REM Double-click this file to launch the dashboard

cd /d "%~dp0\.."

if not exist "venv\Scripts\python.exe" (
    echo First time setup — running setup script...
    powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
)

call venv\Scripts\activate.bat
echo Starting Meta Ads Dashboard...
start http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
pause
