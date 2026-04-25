# ─────────────────────────────────────────────────────
#  Meta Ads Ultimate Dashboard — PowerShell Launch
# ─────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host "    ULTIMATE Meta Ads Dashboard" -ForegroundColor White
Write-Host "    Windows 11 Edition" -ForegroundColor Gray
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ from python.org" -ForegroundColor Red
    exit 1
}

# Create venv if needed
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

# Create directories
@("logs", "output", "config", "data") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ | Out-Null }
}

# Launch
Write-Host ""
Write-Host "[INFO] Starting Streamlit dashboard..." -ForegroundColor Green
Write-Host "[INFO] Open http://localhost:8501 in your browser" -ForegroundColor Cyan
Write-Host ""

streamlit run app.py --server.port 8501 --server.headless $true --browser.gatherUsageStats $false
