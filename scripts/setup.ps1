# ─────────────────────────────────────────────────────
#  Meta Ads Ultimate Dashboard — Windows 11 Setup
# ─────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host "    ULTIMATE Meta Ads Dashboard — Setup" -ForegroundColor White
Write-Host "  ====================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "  Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found." -ForegroundColor Red
    Write-Host "  Install Python 3.10+ from https://python.org" -ForegroundColor Yellow
    Write-Host "  Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
    exit 1
}

# 2. Create virtual environment
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  Created venv/" -ForegroundColor Green
} else {
    Write-Host "  venv/ already exists" -ForegroundColor Green
}

# 3. Activate and install dependencies
Write-Host "[3/6] Installing dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet
Write-Host "  Dependencies installed" -ForegroundColor Green

# 4. Create directories
Write-Host "[4/6] Creating directories..." -ForegroundColor Yellow
@("logs", "output", "config", "data", "templates") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ | Out-Null
        Write-Host "  Created $_/" -ForegroundColor Green
    }
}

# 5. Create .env if not exists
Write-Host "[5/6] Checking .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env" -ErrorAction SilentlyContinue
    if (Test-Path ".env") {
        Write-Host "  Created .env from .env.example" -ForegroundColor Green
    } else {
        @"
# Meta API Credentials
META_ACCESS_TOKEN=your_access_token_here
META_AD_ACCOUNT_ID=act_your_account_id
META_API_VERSION=v25.0
"@ | Set-Content ".env"
        Write-Host "  Created default .env" -ForegroundColor Green
    }
    Write-Host "  Edit .env with your Meta API credentials" -ForegroundColor Yellow
} else {
    Write-Host "  .env already exists" -ForegroundColor Green
}

# 6. Verify
Write-Host "[6/6] Verifying setup..." -ForegroundColor Yellow
python -c "import streamlit; import pandas; import openpyxl; print('All dependencies OK')"

Write-Host ""
Write-Host "  ====================================================" -ForegroundColor Green
Write-Host "    Setup Complete!" -ForegroundColor White
Write-Host "  ====================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  To start the dashboard:" -ForegroundColor Cyan
Write-Host "    .\scripts\run.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  Or manually:" -ForegroundColor Cyan
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "    streamlit run app.py" -ForegroundColor White
Write-Host ""
