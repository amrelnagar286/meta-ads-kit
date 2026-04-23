# Technical Spec — Meta Ads Ultimate Dashboard

> **Document ID:** 02_TECHNICAL_SPEC
> **Methodology:** BMAD + SPEKIT
> **Version:** 1.0.0
> **Status:** Canonical

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     LAYER 7: PRESENTATION                        │
│          Streamlit Dashboard (Windows 11 Theme)                   │
│          + HTML Local BI Dashboard                                │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 6: COMPARISON                          │
│              Period-over-Period Analysis                          │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 5: ANALYTICS                           │
│              KPIEngine / FormulaParser                           │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 4: EXPORT                              │
│       CSV / JSON / Excel / ZIP / Google Sheets / Power BI        │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 3: EXTRACTION                          │
│         MetaAdsExtractor (parallel, paginated, retry)            │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 2: API CLIENT                          │
│     Rate Limiter / Session Management / Error Handling            │
├──────────────────────────────────────────────────────────────────┤
│                     LAYER 1: CONFIGURATION                       │
│          Config / .env / config.json / Meta Catalog               │
└──────────────────────────────────────────────────────────────────┘
```

## Query Plan Philosophy

- If user selects multiple breakdowns:
  - `mode=separate_files` => each breakdown is extracted independently
  - `mode=combinations` => only compatible combinations are attempted
- Action breakdowns are activated only with appropriate fields (e.g., `actions`)
- Summary fields are stored in metadata
- Campaign filtering uses `effective_status` + selected IDs

## Output Contract

```
output/run_YYYYMMDD_HHMMSS/
├── entities/
│   ├── account_info.csv + .json
│   ├── campaigns.csv + .json
│   ├── adsets.csv + .json
│   └── ads.csv + .json
├── raw/
│   ├── {level}__{breakdown}.csv + .json
│   └── ...
├── MASTER_ALL_DATA.xlsx
├── MASTER_ALL_DATA.json
├── manifest.json
└── powerbi/
    ├── power_query_folder_import.m
    └── dax_suggestions.json
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Dashboard | Streamlit |
| API Client | requests + urllib3 retry |
| Data Processing | pandas |
| Excel | openpyxl |
| Scheduling | APScheduler |
| Google Sheets | google-api-python-client |
| Charts | plotly |
| HTML Dashboard | Vanilla HTML/CSS/JS |

## API Configuration

- API Version: v25.0
- Base URL: `https://graph.facebook.com/v25.0`
- Page Limit: 500 rows per request
- Max Workers: 5 concurrent threads
- Max Retries: 6 with exponential backoff
- Rate limit monitoring via `x-ad-account-usage` header
