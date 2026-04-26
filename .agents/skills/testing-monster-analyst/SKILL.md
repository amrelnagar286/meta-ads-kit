# Testing Monster Data Analyst

## Overview
The Monster Data Analyst is a Streamlit app in `monster-analyst/` that imports multi-source marketing data, links datasets, and computes 51 pre-built metrics across 8 categories.

## Launch
```bash
cd monster-analyst
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```
Use port 8502 to avoid conflicts with other Streamlit apps.

## Sample Data
- `data/sample/meta_ads_sample.csv` — 10 rows, 32 columns (Meta ads export)
- `data/sample/orders_sample.csv` — 15 rows (order/CRM data with ad_id for linking)

## Test Checklist

### 1. App Structure
- 6 main tabs: Import Data, Link & Merge, KPI Dashboard, Data Explorer, Metric Lab, Export
- 7 sidebar pages: Financial Analysis, Funnel Analysis, Creative Audit, Algorithm Health, Multi Source Report, Messaging Analysis, Settings

### 2. CSV Upload
- Go to Import Data tab → Upload `meta_ads_sample.csv`
- Expect: success message, data preview with 10 rows × 32 columns

### 3. KPI Dashboard (Expected Values from Sample Data)
- ROAS = 2.49
- CPA = $56.08
- CTR = 1.74%
- CPC = $1.44
- CPM = $24.92
- CVR = 2.56%

### 4. Threshold Badges
- Ghost Impression Rate should show "Warning" badge (orange) at 35.24%
- Lower-is-better metrics use descending thresholds — verify badge color is correct direction

### 5. Metric Lab
- Click Metric Lab tab → Pre-built Library section should render without crash
- The multiselect default values must use tuple format matching the options list

### 6. DAX Export
- In Metric Lab, check DAX formula for `click_to_content`
- Should read `SUM('outbound_clicks') / SUM('clicks')` — `clicks` must NOT be corrupted by substring replacement

### 7. Link & Merge
- Upload both sample files → Link & Merge tab
- Join on `ad_id` column
- Expected: 23 rows, 41 columns, 2 matched keys, 20% left match rate, 100% right match rate

### 8. Export Tab
- Should render without NameError — `import io` and `import re` must be at module level in app.py

### 9. Financial Analysis Page
- Navigate via sidebar → should load with Financial Configuration inputs and Financial KPIs
- With sample data: ROAS=1.36, True POAS=0.22, Gross Profit=$18,270

### 10. Settings → Metric Library
- Shows "51 pre-built metrics across 8 categories"
- Categories: Creative & Attention (6), Traffic Quality (6), Intent & Conversions (6), Algorithm Health (8), Unit Economics & Profitability (7), Standard KPIs (10), Messaging & Lead Conversion (5), Audience & Reach (3)

## Known Pitfalls

### session_state None Handling
`st.session_state.get("key", fallback)` does NOT use the fallback if the key exists with a `None` value. Use `st.session_state.get("key") or fallback` instead. This might affect any sidebar page that reads `computed_metrics_df` from session state.

### matplotlib Dependency
`pandas.Styler.background_gradient()` (used in Data Explorer correlation matrix) requires matplotlib. If you see an ImportError about matplotlib, add `matplotlib>=3.7.0` to requirements.txt.

### Streamlit Hot Reload
After pushing fixes to page files, Streamlit may not auto-reload sidebar pages. Click "Rerun" in the top-right banner or restart the server.

## Not Testable Offline
- Google Sheets import (needs a public Google Sheets URL)
- Meta Dashboard folder import (needs output from the Meta Ads Dashboard project)
- These require real data sources and cannot be tested with sample files alone

## Devin Secrets Needed
None required for offline testing with sample data. For Google Sheets testing, a public sheet URL would be needed (no secret, just a URL).
