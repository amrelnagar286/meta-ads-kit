# Monster Data Analyst

**Ultimate MarTech Expert Analysis Platform** — Import, link, and deeply analyze marketing data from multiple sources.

## Quick Start

```bash
# Clone
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit
git checkout devin/<branch-name>

# Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate
pip install -r requirements.txt

# Launch
streamlit run app.py
```

Opens at **http://localhost:8501**

## Features

### Multi-Source Data Import
- **CSV, JSON, Excel** — drag-and-drop upload
- **Google Sheets** — paste any public sharing link
- **Meta Dashboard Output** — auto-reads manifest.json, MASTER_ALL_DATA files
- **Auto column normalization** — recognizes 30+ common column name aliases

### Data Linking & Merging
- Join datasets on any column (ad_id ↔ order_id, campaign_name, etc.)
- Auto-suggests join columns based on name similarity
- Join preview with match statistics before executing
- Support for inner, left, right, and outer joins

### 125+ Pre-Built MarTech Metrics

| Category | Metrics | Examples |
|----------|---------|----------|
| Standard KPIs | 10 | ROAS, CPA, CTR, CPC, CPM, CVR, AOV, Frequency |
| Creative & Attention | 6 | Hook Rate, Hold Rate, Fatigue Index, Ghost Impressions |
| Traffic Quality | 6 | Drop-off Rate, Pure Intent CTR, Bounce Tax |
| Intent & Conversions | 6 | Cart Abandonment, Purchase Intent Velocity, True CPA |
| Algorithm Health | 7 | Audience Exhaustion, Signal-to-Noise Loss, First-Time Impression Ratio |
| Unit Economics | 7 | True POAS, NC-ROAS, Break-even Delta, LTV-to-CAC |
| Messaging & Leads | 5 | Message-to-Order %, Cost Per Conversation, Messaging ROAS |
| Audience & Reach | 3 | Reach Efficiency, Cost Per Educated Prospect |

### Analysis Pages

- **KPI Dashboard** — aggregated and row-level metric computation
- **Data Explorer** — table view, pivot tables, charts, statistics, period comparison
- **Financial Analysis** — POAS, break-even, COGS integration, per-entity profitability
- **Funnel Analysis** — full conversion funnel, bottleneck detection, drop-off analysis
- **Creative Audit** — hook/hold rates, fatigue detection, action alerts
- **Algorithm Health** — audience exhaustion, ghost impressions, frequency trends
- **Messaging Analysis** — conversation-to-order tracking with CRM linking guide
- **Report Builder** — aggregate, breakdown, comparison, and trend reports
- **Metric Lab** — custom formulas, bulk computation, DAX export
- **Settings** — benchmarks, metric library, column aliases

### Safe Formula Engine
- AST-based arithmetic evaluator (no eval/exec)
- Supports: `+`, `-`, `*`, `/`, `()`, `round()`, `sqrt()`, `abs()`, `min()`, `max()`, `log()`, `pow()`
- Column references by name
- DAX-like measure export for Power BI

## Linking Orders with Ad Data

1. Import your **Meta ads export** (CSV/Excel)
2. Import your **order sheet** (CSV/Excel/Google Sheets)
3. Go to **Link & Merge** tab
4. Select the join columns (e.g., `ad_id` from both)
5. Click **Execute Merge**
6. All analysis pages now use the combined dataset

## Sample Data

Sample files are included in `data/sample/`:
- `meta_ads_sample.csv` — 10 ads across 5 campaigns
- `orders_sample.csv` — 15 orders linked by ad_id

## Project Structure

```
monster-data-analyst/
├── app.py                    # Main Streamlit app (6 tabs)
├── requirements.txt
├── src/
│   ├── metric_catalog.py     # 125+ metric definitions
│   ├── formula_engine.py     # Safe AST-based evaluator
│   ├── data_importer.py      # Multi-source import engine
│   ├── data_linker.py        # Join/merge operations
│   └── helpers.py            # UI helpers, Windows 11 CSS
├── pages/
│   ├── 1_Financial_Analysis.py
│   ├── 2_Funnel_Analysis.py
│   ├── 3_Creative_Audit.py
│   ├── 4_Algorithm_Health.py
│   ├── 5_Multi_Source_Report.py
│   ├── 6_Messaging_Analysis.py
│   └── 7_Settings.py
├── data/
│   ├── sample/               # Sample CSV files
│   ├── uploads/              # User uploads (gitignored)
│   └── exports/              # Export output (gitignored)
└── scripts/
    └── run.sh                # Launch script
```
