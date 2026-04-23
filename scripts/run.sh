#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
#  Meta Ads Ultimate Dashboard — Unix Launch Script
# ─────────────────────────────────────────────────────
set -euo pipefail

echo ""
echo "  ===================================================="
echo "    ULTIMATE Meta Ads Dashboard"
echo "  ===================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Install Python 3.10+"
    exit 1
fi
python3 --version

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt --quiet

# Create directories
mkdir -p logs output config data

# Launch
echo ""
echo "[INFO] Starting Streamlit dashboard..."
echo "[INFO] Open http://localhost:8501 in your browser"
echo ""

streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
