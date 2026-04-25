# KPI Definitions — Meta Ads Ultimate Dashboard

> **Document ID:** 04_KPI_DEFINITIONS
> **Version:** 1.0.0
> **Status:** Canonical

---

## 1. Standard KPIs

### 1.1 ROAS — Return on Ad Spend

| Property | Value |
|----------|-------|
| **KPI ID** | `roas` |
| **Formula** | `revenue / spend` |
| **Required Fields** | `revenue`, `spend` |
| **Unit** | ratio |

| ROAS Range | Assessment |
|-----------|------------|
| < 1.0 | Loss-making |
| 1.0 – 2.0 | Marginal |
| 2.0 – 4.0 | Good |
| > 4.0 | Excellent |

### 1.2 CPA — Cost Per Acquisition

| Property | Value |
|----------|-------|
| **KPI ID** | `cpa` |
| **Formula** | `spend / conversions` |
| **Unit** | currency |

### 1.3 CTR — Click-Through Rate

| Property | Value |
|----------|-------|
| **KPI ID** | `ctr` |
| **Formula** | `clicks / impressions` |
| **Unit** | percentage |

| CTR Range | Assessment |
|-----------|------------|
| < 0.5% | Below average |
| 0.5% – 1.5% | Average |
| 1.5% – 3.0% | Good |
| > 3.0% | Excellent |

### 1.4 CPC — Cost Per Click

| Property | Value |
|----------|-------|
| **KPI ID** | `cpc` |
| **Formula** | `spend / clicks` |
| **Unit** | currency |

### 1.5 CPM — Cost Per Mille

| Property | Value |
|----------|-------|
| **KPI ID** | `cpm` |
| **Formula** | `(spend / impressions) * 1000` |
| **Unit** | currency |

### 1.6 CVR — Conversion Rate

| Property | Value |
|----------|-------|
| **KPI ID** | `cvr` |
| **Formula** | `conversions / clicks` |
| **Unit** | percentage |

### 1.7 AOV — Average Order Value

| Property | Value |
|----------|-------|
| **KPI ID** | `aov` |
| **Formula** | `revenue / purchases` |
| **Unit** | currency |

### 1.8 Frequency

| Property | Value |
|----------|-------|
| **KPI ID** | `frequency` |
| **Formula** | `impressions / reach` |
| **Unit** | ratio |

### 1.9 Cost Per Lead

| Property | Value |
|----------|-------|
| **KPI ID** | `cpl` |
| **Formula** | `spend / leads` |
| **Unit** | currency |

### 1.10 ThruPlay Rate

| Property | Value |
|----------|-------|
| **KPI ID** | `thruplay_rate` |
| **Formula** | `thruplay_actions / impressions` |
| **Unit** | percentage |

## 2. Custom KPI Format

Users can define custom KPIs with the formula syntax:

```python
{
    "kpi_id": "custom_efficiency",
    "name": "Custom Efficiency Score",
    "formula": "(revenue - spend) / spend * 100",
    "required_fields": ["revenue", "spend"],
    "unit": "percentage",
    "format": ".2f"
}
```

## 3. Division-by-Zero Handling

All KPI computations use safe division: if denominator is zero or NaN, result is 0.0.
This is implemented via `safe_divide(numerator, denominator, default=0.0)`.

## 4. DAX Equivalents for Power BI

| KPI | DAX Measure |
|-----|-------------|
| Total Spend | `SUM(FactInsights[spend])` |
| ROAS | `DIVIDE(SUM(FactInsights[purchase_value]), SUM(FactInsights[spend]))` |
| CTR % | `DIVIDE(SUM(FactInsights[clicks]), SUM(FactInsights[impressions]))` |
| CPA | `DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[purchases]))` |
| CPM | `DIVIDE(SUM(FactInsights[spend]) * 1000, SUM(FactInsights[impressions]))` |
| CPC | `DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[clicks]))` |
