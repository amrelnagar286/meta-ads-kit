# Power BI Spec — Meta Ads Ultimate Dashboard

> **Document ID:** 05_POWERBI_SPEC
> **Version:** 1.0.0
> **Status:** Canonical

---

## Import Modes

- **Folder import** for all CSV outputs
- **Single workbook import** for master Excel workbook
- **JSON import** for metadata/audit

## Recommended Star Schema

```
                    ┌──────────────┐
                    │  Dim_Date    │
                    │  date        │
                    │  year        │
                    │  quarter     │
                    │  month       │
                    │  week        │
                    │  day_of_week │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────┴───────┐    ┌──────────────┐
│ Dim_Campaign │────│ Fact_Insights│────│ Dim_Breakdown│
│ campaign_id  │    │ date_start   │    │ breakdown_key│
│ campaign_name│    │ campaign_id  │    │ breakdown_val│
│ objective    │    │ adset_id     │    └──────────────┘
│ buying_type  │    │ ad_id        │
└──────────────┘    │ spend        │    ┌──────────────┐
                    │ impressions  │    │  Dim_AdSet   │
┌──────────────┐    │ clicks       │    │  adset_id    │
│  Dim_Ad      │────│ reach        │────│  adset_name  │
│  ad_id       │    │ frequency    │    │  bid_strategy│
│  ad_name     │    │ ctr          │    └──────────────┘
│  creative_id │    │ cpc          │
└──────────────┘    │ cpm          │
                    │ actions      │
                    │ conversions  │
                    │ roas         │
                    └──────────────┘
```

## Power Query M Code for Folder Import

```m
let
    Source = Folder.Files("{{FOLDER_PATH}}"),
    Filtered = Table.SelectRows(Source, each Text.EndsWith([Extension], ".csv")),
    WithTables = Table.AddColumn(Filtered, "Data",
        each Csv.Document([Content], [Delimiter=",", Encoding=65001])),
    Promoted = Table.AddColumn(WithTables, "Promoted",
        each Table.PromoteHeaders([Data], [PromoteAllScalars=true]))
in
    Promoted
```

## Separation of Concerns

The approach separates extraction from analysis:

- **Extraction engine** is responsible for maximum reliable data pull
- **Power BI** is responsible for modeling + DAX + visualization

This is superior to a single dashboard that tries to do everything but chokes at scale.
