# Testing the ULTIMATE Meta Ads Dashboard

## Overview

The dashboard has two main interfaces:
1. **Streamlit app** (`app.py`) — main dashboard with 5 tabs and 7 sub-pages
2. **HTML dashboard** (`templates/dashboard.html`) — standalone zero-dependency local BI

## Environment Setup

```bash
cd <repo-root>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Launch Streamlit:
```bash
streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Open HTML dashboard directly in browser:
```
file:///<repo-root>/templates/dashboard.html
```

## Devin Secrets Needed

- `META_ACCESS_TOKEN` — Required for real API extraction testing
- `META_AD_ACCOUNT_ID` — Required for real API extraction testing (format: `act_XXXXXXXXX`)
- `GOOGLE_SHEETS_CREDENTIALS` — Optional, only for Google Sheets export testing

## What Can Be Tested Without API Credentials

- Streamlit app launch and UI rendering (all 5 tabs render)
- Settings tab: verify config values (API Version, Rate Limit, Max Retries, Cache TTL, KPI list, Breakdowns table)
- Sidebar controls: Date Preset defaults, Data Level checkboxes, Breakdown multiselect
- Connect validation: clicking Connect with empty fields shows warning
- KPI Dashboard and Data Preview empty-state messages
- HTML dashboard: CSV/JSON file loading, KPI card calculations, Data Table, Charts, Formula Lab
- KPI engine correctness via Python shell with synthetic DataFrames

## Creating Synthetic Test Data

```python
import pandas as pd
data = {
    'date_start': ['2025-04-01','2025-04-02','2025-04-03','2025-04-04','2025-04-05'],
    'campaign_name': ['Campaign A','Campaign A','Campaign B','Campaign B','Campaign C'],
    'spend': [100.0, 150.0, 200.0, 50.0, 300.0],
    'impressions': [10000, 15000, 20000, 5000, 30000],
    'clicks': [200, 300, 400, 100, 600],
    'reach': [8000, 12000, 16000, 4000, 25000],
    'conversions': [10, 15, 20, 5, 30],
    'revenue': [500, 750, 1000, 250, 1500],
    'purchases': [8, 12, 16, 4, 24],
}
df = pd.DataFrame(data)
df.to_csv('test_data.csv', index=False)
```

Expected KPI values on row 0 (spend=100, impressions=10000, clicks=200):
- CTR = 2.0%, CPC = $0.50, CPM = $10.00, ROAS = 5.0, CPA = $10.00, Frequency = 1.25

Expected aggregated totals: Spend=$800, Impressions=80K, Clicks=1.6K, CTR=2.00%, CPC=$0.50

## Known Issues to Watch For

- **Streamlit sub-pages**: Pages in `src/pages/` might not be auto-discovered by Streamlit multipage nav. Streamlit expects a `pages/` directory relative to `app.py`. If sub-pages don't appear in nav, they may need to be moved to a top-level `pages/` directory or configured with `st.navigation()`.
- **HTML dashboard date parsing**: Date columns like `date_start` with values "2025-04-01" may be parsed as numbers (showing "2025.00") in the HTML Data Table. This is a minor display issue in the CSV parser's auto-type-detection.
- **START EXTRACTION button**: Correctly disabled when not connected — this is expected behavior, not a bug.

## Testing the KPI Engine Programmatically

```python
from src.kpi_engine import KPIEngine, evaluate_formula

engine = KPIEngine()
result = engine.compute_all(df)  # df is the synthetic DataFrame

# Verify KPI columns exist
assert all(f'kpi_{k}' in result.columns for k in ['roas','cpa','ctr','cpc','cpm','cvr','aov','frequency','cpl','thruplay_rate'])

# Test formula evaluator safety
assert evaluate_formula('spend / clicks', {'spend': 800, 'clicks': 0}) == 0.0  # division by zero
```

## Config Values to Verify in Settings Tab

| Setting | Expected Value |
|---------|---------------|
| API Version | v25.0 |
| Rate Limit | 180/hour |
| Max Retries | 5 |
| Cache TTL | 300s |
| Configured | No (without credentials) |
| Standard KPIs | 10 entries |
| Breakdowns | 22 rows in table |
| Metric groups | 6 expandable sections |
