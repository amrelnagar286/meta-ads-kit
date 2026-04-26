#!/bin/bash
# Monster Data Analyst -- Launch Script (Linux/Mac)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
pip install -r requirements.txt --quiet

# Launch
echo "Starting Monster Data Analyst..."
streamlit run app.py --server.port 8502 --server.headless true
