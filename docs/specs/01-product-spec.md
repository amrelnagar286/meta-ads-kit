# Product Spec — Meta Ads Ultimate Dashboard

> **Document ID:** 01_PRODUCT_SPEC
> **Methodology:** BMAD + SPEKIT Spec-Driven Development
> **Version:** 1.0.0
> **Status:** Canonical

---

## Vision

A sovereign, local-first Meta Ads extraction and analytics engine that provides
maximum optionality for data extraction, analysis, and visualization.
Windows 11 themed UI. Power BI ready outputs. Free forever.

## Core Principles

- Maximum optionality — user controls every parameter
- Schema-first extraction — validate before requesting
- Fail-soft execution — never crash on partial failures
- Power BI first-class compatibility
- Granular outputs + master outputs
- Local-first and free-forever execution path

## Key User Stories

1. As an analyst, I want to choose any date period: preset, custom range, daily, weekly, monthly, quarterly, yearly, or lifetime.
2. I want to choose any data level: account / campaign / adset / ad.
3. I want to fetch the campaign catalog first, then select specific campaigns or all.
4. I want each breakdown in a separate file when multiple breakdowns are selected.
5. I want CSV + JSON for each result, plus master Excel workbook and master JSON.
6. I want to connect Power BI directly without complex intermediaries.
7. I want flexible background scheduling.
8. I want full CRUD operations on campaigns, ad sets, and ads.
9. I want bulk operations (create, update, pause, delete) via CSV upload.
10. I want automation rules (stop-loss, budget scaling, scheduling).
11. I want a local HTML-based BI dashboard for quick analysis without Power BI.
12. I want Google Sheets export for collaborative reporting.

## Feature Matrix

| Feature | Description |
|---------|-------------|
| 70+ Metrics | All Meta API insights fields including actions, video, quality, engagement |
| 4 Data Levels | Account, Campaign, Ad Set, Ad |
| 16+ Breakdowns | Age, Gender, Country, Region, DMA, Placement, Device, Hourly, Assets, etc. |
| Flexible Dates | 12+ presets, custom ranges, time increments |
| Campaign CRUD | Create, read, update, delete campaigns |
| Ad Set CRUD | Full ad set management with targeting |
| Ad CRUD | Ad creation and management |
| Bulk Operations | CSV-based bulk create/update/pause/delete |
| Automation | Stop-loss rules, budget scaling, time-based scheduling |
| Data Studio | Interactive charts, pivot tables, formula lab |
| Scheduling | Background extraction on configurable intervals |
| Multi-format Export | CSV, JSON, Excel, ZIP, Google Sheets |
| Power BI Integration | Direct import path with DAX suggestions |
| HTML Dashboard | Local BI with KPIs, charts, custom formulas |
| Control Panel | System health, extraction management |

## Non-Goals

- Not bypassing Meta API permissions or rate limits
- Not claiming metrics that Meta blocks for certain level/breakdown combinations
- Not blindly combining incompatible breakdown combinations
- Not a production-grade enterprise scheduler
