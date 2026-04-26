# Monster Data Analyst -- Launch Script (Windows PowerShell)
# Run: .\scripts\run.ps1

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Running setup first..." -ForegroundColor Yellow
    & .\scripts\setup.ps1
}

& .\venv\Scripts\Activate.ps1

Write-Host "Starting Monster Data Analyst..." -ForegroundColor Cyan
Write-Host "Opening at http://localhost:8501" -ForegroundColor Green
streamlit run app.py
