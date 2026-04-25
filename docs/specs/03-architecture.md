# Architecture — Meta Ads Ultimate Dashboard

> **Document ID:** 03_ARCHITECTURE
> **Version:** 1.0.0
> **Status:** Canonical

---

## 1. System Overview

The Meta Ads Ultimate Dashboard is a 7-layer architecture that ingests advertising data
from Meta Ads API, processes it through extraction and analytics pipelines, and presents
everything through an interactive Streamlit dashboard with Windows 11 theming.

### Layer Responsibilities

| Layer | Name | Responsibility | Primary Module |
|-------|------|---------------|----------------|
| 1 | Configuration | Load, validate config from .env and JSON | `config.py` |
| 2 | API Client | HTTP session, rate limiting, retry logic | `api_client.py`, `rate_limiter.py` |
| 3 | Extraction | Parallel insights extraction with pagination | `extractor.py` |
| 4 | Export | Multi-format output (CSV/JSON/Excel/Sheets) | `sheets_exporter.py`, `powerbi_helper.py` |
| 5 | Analytics | KPI computation and custom formulas | `kpi_engine.py` |
| 6 | Comparison | Period-over-period analysis | Built into dashboard |
| 7 | Presentation | Interactive dashboard + HTML BI | `app.py`, `pages/*` |

### Key Design Decisions

1. **DataFrame-centric.** All data flows through `pandas.DataFrame` objects.
2. **Pull-based architecture.** Dashboard pulls data on demand.
3. **Stateless pipeline.** Each layer operates on DataFrames without maintaining internal state.
4. **Concurrent extraction.** ThreadPoolExecutor with max 5 workers for parallel API calls.
5. **Fail-soft.** Individual API failures don't crash the extraction run.

## 2. Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Meta Ads    │     │  Config      │     │  Google      │
│  API         │     │  (.env/JSON) │     │  Sheets      │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    │
┌──────────────┐     ┌──────────────┐            │
│  Extractor   │     │  ConfigStore │            │
│  (Layer 3)   │     │  (Layer 1)   │            │
└──────┬───────┘     └──────────────┘            │
       │                                         │
       ▼                                         ▼
┌──────────────┐                          ┌──────────────┐
│  DataFrames  │                          │  Sheets      │
│  (raw data)  │                          │  Exporter    │
└──────┬───────┘                          └──────────────┘
       │
       ├──► CSV / JSON / Excel / ZIP
       │
       ├──► Power BI Pack (M Query + DAX)
       │
       ├──► KPI Engine (computed metrics)
       │
       └──► Streamlit Dashboard (presentation)
```

## 3. Module Dependencies

```
config.py ──► meta_catalog.py
    │
    ▼
rate_limiter.py ──► api_client.py
                        │
                        ▼
                    extractor.py
                        │
                        ├──► helpers.py
                        ├──► powerbi_helper.py
                        ├──► sheets_exporter.py
                        └──► kpi_engine.py
                                │
                                ▼
                            app.py ──► pages/*
```

## 4. Concurrency Model

- **Extraction:** `ThreadPoolExecutor(max_workers=5)` for parallel level × breakdown tasks
- **Rate Limiting:** Thread-safe with `threading.Lock`, proactive throttling via API headers
- **Retry:** Exponential backoff with jitter, max 6 retries per request
- **Pagination:** Cursor-based with `after` parameter, 500 rows per page

## 5. Security Model

- Credentials stored in `.env` files (never committed)
- Session-based token input in Streamlit UI
- No credential persistence to disk from UI
- Rate limit headers monitored to prevent account throttling
