# Monster Data Analyst -- Windows Setup Script
# Run: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectDir

Write-Host "Monster Data Analyst -- Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Download from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "        Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}
Write-Host "[OK] Virtual environment ready" -ForegroundColor Green

# Activate venv
& .\venv\Scripts\Activate.ps1
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "[OK] All dependencies installed" -ForegroundColor Green

# Create data directories
if (-not (Test-Path "data\uploads")) { New-Item -ItemType Directory -Path "data\uploads" -Force | Out-Null }
if (-not (Test-Path "data\exports")) { New-Item -ItemType Directory -Path "data\exports" -Force | Out-Null }
Write-Host "[OK] Data directories ready" -ForegroundColor Green

Write-Host ""
Write-Host "Setup complete! To launch:" -ForegroundColor Cyan
Write-Host "  .\scripts\start.bat" -ForegroundColor White
Write-Host "  OR" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  streamlit run app.py" -ForegroundColor White
