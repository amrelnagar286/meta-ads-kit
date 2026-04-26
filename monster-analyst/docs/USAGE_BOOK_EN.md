# Monster Data Analyst — Complete Usage Book

**Version 1.0** | **The Ultimate MarTech Expert Analysis Platform**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation on Windows 11](#2-installation-on-windows-11)
3. [First Launch](#3-first-launch)
4. [Application Overview](#4-application-overview)
5. [Tab 1: Import Data](#5-tab-1-import-data)
6. [Tab 2: Link & Merge](#6-tab-2-link--merge)
7. [Tab 3: KPI Dashboard](#7-tab-3-kpi-dashboard)
8. [Tab 4: Data Explorer](#8-tab-4-data-explorer)
9. [Tab 5: Metric Lab](#9-tab-5-metric-lab)
10. [Tab 6: Export](#10-tab-6-export)
11. [Page: Financial Analysis](#11-page-financial-analysis)
12. [Page: Funnel Analysis](#12-page-funnel-analysis)
13. [Page: Creative Audit](#13-page-creative-audit)
14. [Page: Algorithm Health](#14-page-algorithm-health)
15. [Page: Multi-Source Report](#15-page-multi-source-report)
16. [Page: Messaging Analysis](#16-page-messaging-analysis)
17. [Page: Settings](#17-page-settings)
18. [The Metric Library](#18-the-metric-library)
19. [Safe Formula Engine](#19-safe-formula-engine)
20. [Data Linking Strategies](#20-data-linking-strategies)
21. [Working with Google Sheets](#21-working-with-google-sheets)
22. [Working with Meta Dashboard Output](#22-working-with-meta-dashboard-output)
23. [Threshold Badges & Health Indicators](#23-threshold-badges--health-indicators)
24. [DAX Export for Power BI](#24-dax-export-for-power-bi)
25. [Tips & Best Practices](#25-tips--best-practices)
26. [Troubleshooting](#26-troubleshooting)
27. [Glossary](#27-glossary)

---

## 1. Introduction

Monster Data Analyst is a **standalone marketing analytics platform** that lets you import data from any source (CSV, JSON, Excel, Google Sheets, Meta Ads Dashboard), link datasets together, and perform deep analysis using 51+ pre-built MarTech metrics.

**Key Capabilities:**
- Import data from 5+ source types with automatic column normalization
- Link and merge datasets from different sources (Meta Ads + CRM + Order Sheets + Google Ads)
- 51 pre-built metrics across 8 categories with bilingual names (English + Arabic)
- Safe formula engine for custom metrics (no eval/exec — fully sandboxed)
- 7 specialized analysis pages (Financial, Funnel, Creative, Algorithm, Report Builder, Messaging, Settings)
- DAX export for Power BI integration
- Windows 11-inspired UI theme

**Who is this for?**
- Performance marketers managing Meta, Google, or multi-channel campaigns
- Media buyers who need to link ad data with CRM/order data
- Marketing analysts who want flexible pivot tables, charts, and custom metrics
- Agencies managing multiple brands and data sources

---

## 2. Installation on Windows 11

### Prerequisites

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - **IMPORTANT:** During installation, check the box **"Add Python to PATH"**
   - To verify: Open PowerShell and type `python --version`

2. **Git** (optional, for cloning)
   - Download from: https://git-scm.com/download/win

### Method 1: Quick Start (Recommended)

Open **PowerShell** and run:

```powershell
# Clone the repository
git clone https://github.com/amrelnagar286/meta-ads-kit.git
cd meta-ads-kit\monster-analyst

# Run the setup script
.\scripts\setup.ps1

# Launch the app
.\scripts\start.bat
```

### Method 2: Double-Click Launch

1. Navigate to `meta-ads-kit\monster-analyst\scripts\` in File Explorer
2. Double-click **`start.bat`**
3. The app will install dependencies and open in your browser automatically

### Method 3: Manual Setup

```powershell
cd meta-ads-kit\monster-analyst

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Launch
streamlit run app.py
```

### What Gets Installed

| Package | Purpose |
|---------|---------|
| streamlit | Web UI framework |
| pandas | Data manipulation |
| plotly | Interactive charts |
| openpyxl | Excel file reading |
| xlsxwriter | Excel file writing |
| numpy | Numerical computing |
| scipy | Statistical functions |
| matplotlib | Correlation matrix rendering |
| requests | Google Sheets fetching |

---

## 3. First Launch

When you start the app, your default browser opens to **http://localhost:8501**.

You'll see:
- **Left sidebar:** Monster Analyst branding, dataset selector (empty until you import data), and loaded sources list
- **Main area:** 6 tabs across the top — Import Data, Link & Merge, KPI Dashboard, Data Explorer, Metric Lab, Export
- **Sidebar navigation:** 7 analysis pages accessible from the sidebar — Financial Analysis, Funnel Analysis, Creative Audit, Algorithm Health, Multi Source Report, Messaging Analysis, Settings

**First steps:**
1. Go to the **Import Data** tab
2. Upload a CSV, Excel, or JSON file (or paste a Google Sheets URL)
3. Your data appears in the sidebar under "Loaded Sources"
4. Switch to **KPI Dashboard** to see computed metrics

---

## 4. Application Overview

### Main Tabs (6)

| Tab | Purpose |
|-----|---------|
| **Import Data** | Upload files (CSV, JSON, Excel), import Google Sheets, load Meta Dashboard output |
| **Link & Merge** | Join two datasets on a common column (ad_id, campaign_name, etc.) |
| **KPI Dashboard** | View aggregated metrics with health badges, compute row-level metrics |
| **Data Explorer** | Table view, pivot tables, charts, statistics, period comparison |
| **Metric Lab** | Browse pre-built metrics, create custom formulas, bulk compute, DAX export |
| **Export** | Download individual datasets or all data as CSV, JSON, or Excel |

### Sidebar Pages (7)

| Page | Purpose |
|------|---------|
| **Financial Analysis** | Unit economics, POAS, break-even analysis, COGS integration |
| **Funnel Analysis** | Conversion funnel visualization, bottleneck detection |
| **Creative Audit** | Hook/hold rates, fatigue index, ghost impressions |
| **Algorithm Health** | Audience exhaustion, signal-to-noise, frequency trends |
| **Multi Source Report** | Aggregate, breakdown, comparison, and trend reports |
| **Messaging Analysis** | Conversation-to-order tracking, WhatsApp/Messenger metrics |
| **Settings** | Benchmarks, metric library browser, column aliases |

---

## 5. Tab 1: Import Data

### Uploading Files

1. Click **"Browse files"** or drag-and-drop onto the upload area
2. Supported formats: **CSV**, **JSON**, **Excel (.xlsx, .xls)**
3. You can upload multiple files at once
4. Each file becomes a separate dataset in the sidebar

**What happens on import:**
- Column names are **normalized** (lowercased, spaces → underscores)
- 30+ common aliases are recognized (e.g., "Amount Spent" → `spend`, "Link Clicks" → `clicks`)
- Column types are auto-detected (numeric, date, text)
- Numeric columns stored as text are automatically converted

### Importing Google Sheets

1. Open your Google Sheet
2. Click **Share** → **Anyone with the link** → **Viewer**
3. Copy the URL
4. Paste it in the **"Google Sheet URL"** field
5. Give it a name (e.g., "CRM Orders")
6. Click **"Import Google Sheet"**

**URL format:** `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

### Importing Meta Dashboard Output

If you have exported data from the Meta Ads Dashboard (PR #1):
1. Enter the output folder path (e.g., `C:\output\run_20250426_120000`)
2. Click **"Import Meta Dashboard Output"**
3. It reads the `manifest.json` and imports all available datasets

### Dataset Preview

After importing, each dataset shows:
- **Row count and column count**
- **Column information** (name, detected type, sample value)
- **First 5 rows** of data
- **Remove button** to delete a dataset

### Active Dataset

- Use the **sidebar dropdown** to switch between loaded datasets
- If you have merged data, it appears as **[Merged Dataset]**
- All analysis tabs use the currently active dataset

---

## 6. Tab 2: Link & Merge

### When to Use

Use Link & Merge when you have data from **multiple sources** that share a common identifier. Common scenarios:

| Scenario | Left Dataset | Right Dataset | Join Column |
|----------|-------------|---------------|-------------|
| Ads + Orders | Meta Ads Export | Order Sheet | `ad_id` |
| Ads + CRM | Google Ads | CRM Contacts | `campaign_name` |
| Multi-platform | Meta Ads | Google Ads | `date_start` + `campaign_name` |

### How to Merge

1. Upload **at least 2 datasets** via the Import tab
2. Go to **Link & Merge** tab
3. Select **Left Dataset** (your primary data) and **Right Dataset** (secondary)
4. Choose **Join Columns** — the system auto-suggests based on column name similarity
5. Select **Join Type**:
   - **Left:** Keep all rows from the left, add matching right rows (most common)
   - **Inner:** Only keep rows that match in both datasets
   - **Right:** Keep all rows from the right
   - **Outer:** Keep everything from both datasets
6. Click **"Preview Join"** to see match statistics:
   - Matched keys count
   - Match rate for left and right datasets
   - Sample matched keys
   - Preview of the first 5 merged rows
7. If the preview looks good, click **"Execute Merge"**

### After Merging

- The merged dataset becomes the active dataset
- You can save it as a named dataset with the **"Save Merged as New Dataset"** button
- All analysis tabs and pages will use the merged data
- You can merge additional datasets on top of the merged result

### Auto-Suggested Join Columns

The system suggests join columns based on:
- Exact column name matches
- Common alias patterns (e.g., `ad_id` ↔ `ad_id`)
- Name similarity scoring
- Confidence levels: High (>70%), Medium (40-70%), Low (<40%)

---

## 7. Tab 3: KPI Dashboard

### Aggregated Metrics

The KPI Dashboard computes metrics by **summing all rows** in the active dataset. For each metric:
- The **formula** is applied to the aggregated totals
- A **health badge** appears based on thresholds (Healthy/Warning/Critical)
- Metrics are grouped by **category** with color-coded headers

### Health Badges

| Badge | Meaning |
|-------|---------|
| **Healthy** (green) | Value is within the target range |
| **Warning** (orange) | Value is approaching problematic levels |
| **Critical** (red) | Value needs immediate attention |

**Important:** Some metrics are "lower is better" (e.g., Ghost Impression Rate, Drop-off Rate). The system automatically detects this from the threshold configuration and displays badges correctly.

### Row-Level Metrics

Click **"Compute All Available Metrics"** to:
- Calculate every available metric for **each row** individually (per campaign, per ad, etc.)
- New metric columns are added to the dataset
- Use these in Data Explorer for filtering, sorting, and visualization

### Available Metrics

The system automatically determines which metrics can be computed based on your data's columns. For example:
- If you have `spend` and `purchase_conversion_value` → ROAS can be computed
- If you have `impressions` and `clicks` → CTR can be computed
- If you have `video_p25_watched_actions` and `impressions` → Hook Rate can be computed

---

## 8. Tab 4: Data Explorer

### Table View

- **Column selector:** Choose which columns to display
- **Search filter:** Type to search across all visible columns
- **Sortable columns:** Click any column header to sort
- Shows row count: "Showing X of Y rows"

### Pivot Table

Create aggregated views:
1. **Row Dimensions:** Select text columns to group by (e.g., `campaign_name`)
2. **Value Columns:** Select numeric columns to aggregate (e.g., `spend`, `clicks`)
3. **Aggregation:** Sum, Mean, Median, Min, Max, or Count

**Example:** Group by `campaign_name`, sum `spend` and `purchases` → see total spend and purchases per campaign.

### Charts

6 chart types available:
- **Bar:** Compare values across categories
- **Line:** Show trends over time or sequence
- **Scatter:** Find correlations between two metrics
- **Pie:** Show proportional distribution
- **Heatmap:** Correlation matrix between numeric columns
- **Funnel:** Visualize conversion flow

All charts are interactive (zoom, pan, hover for details).

### Statistics

- **Descriptive statistics:** Count, mean, std, min, 25%, 50%, 75%, max for all numeric columns
- **Coefficient of Variation (CV%):** Shows how spread out values are
- **Correlation Matrix:** Color-coded heatmap showing relationships between metrics (blue = positive, red = negative)

### Period Comparison

If your data has a date column (e.g., `date_start`):
- Select the date column and a metric
- See the metric plotted over time
- Useful for spotting trends, seasonality, and anomalies

---

## 9. Tab 5: Metric Lab

### Pre-built Library

Browse all 51 pre-built metrics organized by category. Each metric shows:
- **ID:** Unique identifier
- **Name:** English name
- **Arabic:** Arabic name
- **Formula:** Calculation formula using column names
- **Level:** Where it applies (campaign, ad set, ad, or all)
- **Unit:** Type of value (ratio, percentage, currency, number)
- **Description:** What the metric measures

Use the **category filter** to focus on specific metric groups.

### Custom Formula

Create your own metrics:
1. Enter a **Metric Name** (e.g., "My Custom ROAS")
2. Enter a **Formula** using column names from your data
3. Click **"Validate Formula"** to check syntax
4. Click **"Apply to Data"** to compute and add the metric as a new column

**Supported functions:**
```
+, -, *, /           Basic arithmetic
()                   Grouping
round(value, digits) Round to N decimal places
sqrt(value)          Square root
abs(value)           Absolute value
min(a, b)            Minimum of two values
max(a, b)            Maximum of two values
log(value)           Natural logarithm
pow(base, exp)       Power / exponentiation
```

**Example formulas:**
```
purchase_conversion_value / spend                    → ROAS
(clicks / impressions) * 100                        → CTR %
round(spend / purchases, 2)                          → CPA (rounded)
sqrt(pow(ctr - target_ctr, 2))                      → CTR deviation
```

### Bulk Metrics

Apply **all available pre-built metrics** to your dataset at once:
1. Click **"Bulk Compute"**
2. All computable metrics are added as new columns
3. Results are saved to session state for use across all tabs and pages

### DAX Export

Export your metrics as **DAX measures** for Power BI:
1. Select metrics to export
2. Click **"Generate DAX"**
3. Copy the DAX code and paste into Power BI Desktop → Modeling → New Measure

**Example output:**
```dax
ROAS = DIVIDE(SUM('purchase_conversion_value'), SUM('spend'), 0)
CTR = DIVIDE(SUM('clicks'), SUM('impressions'), 0) * 100
```

---

## 10. Tab 6: Export

### Individual Dataset Export

For each loaded dataset:
- **CSV** download button
- **JSON** download button
- Click to download the full dataset

### Export All Datasets

- **Export All as Excel** — Creates a multi-sheet Excel workbook with each dataset on a separate sheet
- **Export All as ZIP** — Creates a ZIP archive with each dataset as a separate CSV file

### Merged Data Export

If you have merged data, it appears as an additional download option.

---

## 11. Page: Financial Analysis

Access from the sidebar. Provides unit economics and profitability analysis.

### Financial Configuration

Set your business parameters:
- **Average COGS per unit ($):** Cost of goods sold per item (default: $15)
- **Break-even ROAS:** ROAS needed to break even (default: 2.5)
- **Est. New Customer %:** Percentage of purchases from new customers (default: 70%)
- **Avg Repeat Rate:** How many times a customer buys on average (default: 2.5)

### Financial KPIs

| KPI | Formula |
|-----|---------|
| **ROAS** | Revenue / Spend |
| **True POAS** | (Revenue - COGS) / Spend |
| **New Customer ROAS** | ROAS × New Customer % |
| **Break-even Delta** | ROAS - Break-even ROAS |
| **Gross Profit** | Revenue - Spend - COGS |

### Visualizations

- **Revenue vs Cost Breakdown:** Bar chart comparing Revenue, Ad Spend, COGS, and Gross Profit
- **Analyze by Entity:** Select a dimension (campaign, ad set) to see profitability per entity
- **Profit on Ad Spend by Entity:** Per-entity profit analysis chart

---

## 12. Page: Funnel Analysis

Visualizes your conversion funnel and identifies bottlenecks.

### Funnel Stages

The standard funnel:
```
Impressions → Clicks → Landing Page Views → Add to Cart → Purchases
```

### What You See

- **Stage-by-stage drop-off rates** — Where are you losing people?
- **Conversion rates between stages** — How efficient is each step?
- **Bottleneck detection** — Which stage has the biggest drop-off?
- **Funnel visualization** — Interactive funnel chart

### Using with Merged Data

If you merge Meta ads data with order data, the funnel can track all the way from impression to purchase to revenue.

---

## 13. Page: Creative Audit

Evaluates the health and performance of your ad creatives.

### Key Metrics

| Metric | What It Measures |
|--------|-----------------|
| **Hook Rate** | % of impressions that watch 25% of video — measures initial attention |
| **Hold Rate** | % of impressions that watch 50% of video — measures sustained attention |
| **Fatigue Index** | Frequency ÷ CTR — high values mean the audience is tired of the ad |
| **Ghost Impression Rate** | Impressions that generated zero engagement — wasted reach |
| **ThruPlay Rate** | % completing the full video |

### Action Alerts

The Creative Audit page flags creatives that need attention:
- **High Fatigue:** Frequency too high relative to CTR
- **Low Hook Rate:** Not grabbing attention in the first 3 seconds
- **High Ghost Rate:** Too many impressions with zero engagement

---

## 14. Page: Algorithm Health

Monitors whether the Meta algorithm is working efficiently for your account.

### Key Metrics

| Metric | What It Measures |
|--------|-----------------|
| **Audience Exhaustion Rate** | How quickly your target audience is being used up |
| **Signal-to-Noise Loss** | Ratio of useful signals vs wasted spend |
| **First-Time Impression Ratio** | % of impressions going to new people |
| **Frequency Trend** | Is frequency increasing over time? |
| **Cost Efficiency Trend** | Is CPA/CPM getting worse? |

### What to Look For

- **Rising frequency + dropping CTR** → Audience fatigue
- **Declining first-time impressions** → Audience exhaustion
- **Increasing CPA over time** → Algorithm losing efficiency

---

## 15. Page: Multi-Source Report

Build custom reports from your data with flexible configurations.

### Report Types

1. **Aggregate Report:** Summary statistics across all data
2. **Breakdown Report:** Group by a dimension (campaign, date, platform)
3. **Comparison Report:** Side-by-side comparison of segments
4. **Trend Report:** Time-series analysis of key metrics

### Building a Report

1. Select **Report Type**
2. Choose **Dimensions** (what to group by)
3. Choose **Metrics** (what to measure)
4. Choose **Date Range** (if applicable)
5. Click **Generate**

---

## 16. Page: Messaging Analysis

For businesses using WhatsApp or Messenger for sales.

### Key Metrics

| Metric | What It Measures |
|--------|-----------------|
| **Message-to-Order %** | Percentage of conversations that result in an order |
| **Cost Per Conversation** | How much you pay for each messaging conversation |
| **Messaging ROAS** | Revenue from messaging ÷ messaging ad spend |
| **Avg Response Time** | How quickly you respond to leads |
| **Conversation Quality Score** | Composite score of messaging performance |

### CRM Linking Guide

The page includes a step-by-step guide for linking your messaging ad data with your CRM/order data:
1. Export your order data with the `ad_id` column
2. Import both datasets into Monster Analyst
3. Use Link & Merge to join on `ad_id`
4. The messaging metrics will now use the combined data

---

## 17. Page: Settings

### Benchmarks Tab

Configure your target benchmarks for health status indicators:

**Performance Targets:**
- Target CTR % (default: 2.0)
- Target ROAS (default: 3.0)
- Max Frequency (default: 3.5)
- Max CPA (default: $50)

**Alert Thresholds:**
- Bleeder CTR < % (default: 1.0)
- Bleeder Min Spend (default: $10)
- Hook Rate Healthy > % (default: 25.0)
- Hold Rate Healthy > % (default: 30.0)
- Fatigue Critical > (default: 2.5)

**Financial Settings:**
- Break-even ROAS, Avg COGS, New Customer %, Avg Repeat Rate

Click **"Save Benchmarks"** to persist your settings.

### Metric Library Tab

Browse all 51 pre-built metrics organized by 8 categories. Each category is expandable and shows the metrics with their English/Arabic names and count.

### Column Aliases Tab

View and manage column name aliases. The system recognizes 30+ common column name variations:
- "Amount Spent" → `spend`
- "Link Clicks" → `clicks`
- "Results" → `purchases`
- "Cost per Result" → `cost_per_result`

### About Tab

Shows version information, dependencies, and project details.

---

## 18. The Metric Library

### 8 Categories, 51 Metrics

| # | Category | Arabic | Count |
|---|----------|--------|-------|
| 1 | Standard KPIs | المقاييس الأساسية | 10 |
| 2 | Creative & Attention | الانتباه والكرييتف | 6 |
| 3 | Traffic Quality | جودة الترافيك | 6 |
| 4 | Intent & Conversions | النية والتحويل | 6 |
| 5 | Algorithm Health | صحة الخوارزمية | 8 |
| 6 | Unit Economics & Profitability | الاقتصاد والربحية | 7 |
| 7 | Messaging & Lead Conversion | الرسائل وتحويل العملاء | 5 |
| 8 | Audience & Reach | الجمهور والوصول | 3 |

### Key Metrics Explained

**ROAS (Return on Ad Spend):** `purchase_conversion_value / spend`
The most important metric. A ROAS of 3.0 means $3 revenue for every $1 spent.

**CTR (Click-Through Rate):** `(clicks / impressions) * 100`
Percentage of people who click after seeing your ad. Industry average: 1-2%.

**CPA (Cost Per Acquisition):** `spend / purchases`
How much you pay for each purchase. Lower is better.

**Hook Rate:** `(video_p25_watched_actions / impressions) * 100`
How well your ad grabs attention in the first 3 seconds. Target: >25%.

**Fatigue Index:** `frequency / (ctr / 100)`
High values mean your audience is tired of the ad. Refresh creative when > 2.5.

**Ghost Impression Rate:** `((impressions - clicks - video_p25_watched_actions) / impressions) * 100`
Impressions with zero engagement. Warning if > 30%, Critical if > 50%.

---

## 19. Safe Formula Engine

Monster Analyst uses a **sandboxed AST-based formula engine**. This means:

- **No `eval()` or `exec()`** — formulas are parsed as syntax trees
- **Only arithmetic operations** are allowed — no code injection possible
- **Column references** are resolved against the actual dataset
- **Error messages** tell you exactly what went wrong

### Supported Operations

| Operation | Syntax | Example |
|-----------|--------|---------|
| Addition | `+` | `spend + cogs` |
| Subtraction | `-` | `revenue - spend` |
| Multiplication | `*` | `impressions * 0.001` |
| Division | `/` | `clicks / impressions` |
| Parentheses | `()` | `(clicks / impressions) * 100` |
| Round | `round(x, n)` | `round(spend / purchases, 2)` |
| Square Root | `sqrt(x)` | `sqrt(impressions)` |
| Absolute Value | `abs(x)` | `abs(profit)` |
| Minimum | `min(a, b)` | `min(cpa, 100)` |
| Maximum | `max(a, b)` | `max(roas, 0)` |
| Logarithm | `log(x)` | `log(spend)` |
| Power | `pow(x, n)` | `pow(ctr, 2)` |

### Division by Zero

If the denominator is zero, the formula returns `0` instead of raising an error.

---

## 20. Data Linking Strategies

### Strategy 1: Ad ID Linking

Best for tracking which ad generated which order.

**Setup:**
1. In your order tracking system, capture the `ad_id` from the UTM parameter
2. Export your orders with the `ad_id` column
3. Import both the Meta ads export and your order sheet
4. Link & Merge on `ad_id`

### Strategy 2: Campaign Name Linking

Best for matching campaign-level data across platforms.

**Setup:**
1. Use consistent campaign naming across Meta, Google, etc.
2. Import exports from each platform
3. Link & Merge on `campaign_name`

### Strategy 3: Date-Based Linking

Best for matching daily aggregate data.

**Setup:**
1. Import daily reports from each source
2. Link & Merge on `date_start` or `date`
3. This gives you a combined daily view across sources

### Strategy 4: CRM Contact Linking

Best for matching leads/contacts with ad engagement.

**Setup:**
1. Export your CRM contacts with lead source information
2. Import alongside your ads data
3. Link on any matching identifier (email, phone hash, lead_id)

---

## 21. Working with Google Sheets

### Making a Sheet Public

1. Open your Google Sheet
2. Click **File → Share → Share with others**
3. Under **General access**, change to **"Anyone with the link"**
4. Set permission to **Viewer**
5. Click **Copy link**

### What Gets Imported

- The **first sheet** of the spreadsheet is imported
- All rows and columns are included
- Column headers from the first row are used
- Data types are auto-detected

### Use Cases

| Use Case | Google Sheet Contents |
|----------|---------------------|
| CRM Orders | Order ID, Customer, Ad ID, Revenue, Date |
| Sales Log | Date, Product, Qty, Revenue, Source |
| WhatsApp Orders | Conversation ID, Ad ID, Order Status, Amount |
| External KPIs | Date, Benchmark CTR, Target ROAS, Budget |

---

## 22. Working with Meta Dashboard Output

If you also have the Meta Ads Dashboard (PR #1), you can import its output directly:

1. Run an extraction in the Meta Ads Dashboard
2. The output folder is at: `output/run_YYYYMMDD_HHMMSS/`
3. In Monster Analyst, go to **Import Data → Import Meta Dashboard Output Folder**
4. Enter the full path to the output folder
5. Click **Import**

The system reads:
- `manifest.json` for metadata
- `MASTER_ALL_DATA.csv` for the main dataset
- Any additional breakdown files

---

## 23. Threshold Badges & Health Indicators

### How Badges Work

Each metric has optional thresholds defining Healthy, Warning, and Critical ranges.

**Higher-is-better metrics** (ROAS, CTR, Hook Rate):
- Healthy: value >= healthy threshold
- Warning: value >= warning threshold
- Critical: value <= critical threshold

**Lower-is-better metrics** (Ghost Rate, Drop-off Rate, CPA):
- Healthy: value <= healthy threshold
- Warning: value <= warning threshold  
- Critical: value >= critical threshold

The system automatically detects the direction by comparing the healthy and critical threshold values.

### Customizing Thresholds

Go to **Settings → Benchmarks** to change the default thresholds for your industry/account.

---

## 24. DAX Export for Power BI

### What Is DAX?

DAX (Data Analysis Expressions) is the formula language for Power BI. Monster Analyst can export your metrics as DAX measures.

### How to Export

1. Go to **Metric Lab → DAX Export** tab
2. Select the metrics you want to export
3. Click **"Generate DAX"**
4. Copy the generated code

### Using in Power BI

1. Open Power BI Desktop
2. Go to **Modeling → New Measure**
3. Paste the DAX formula
4. The measure will compute against your Power BI data model

### Column Name Handling

DAX export uses `SUM('column_name')` syntax. The system handles substring column names correctly — for example, `outbound_clicks` and `clicks` are treated as separate columns using regex word boundaries.

---

## 25. Tips & Best Practices

### Data Preparation

1. **Clean column names:** The system normalizes automatically, but consistent naming helps
2. **Include date columns:** Enables time-series analysis and period comparison
3. **Use consistent IDs:** If linking data, ensure the join column values match exactly
4. **Remove summary rows:** Don't include "Total" rows in your data — the system computes totals

### Analysis Workflow

1. **Start with KPI Dashboard:** Get the big picture first
2. **Drill into Data Explorer:** Use pivot tables to find patterns
3. **Check Financial Analysis:** Understand true profitability
4. **Audit Creatives:** Identify fatigued or underperforming ads
5. **Monitor Algorithm Health:** Catch efficiency drops early
6. **Build Custom Metrics:** Use the Metric Lab for unique KPIs

### Performance

- **Large datasets:** Files up to 200 MB are supported
- **Many columns:** Only the first 15 columns are shown by default in Table View — use the column selector to show more
- **Correlation matrix:** Select up to 8-10 columns at a time for readability

---

## 26. Troubleshooting

| Issue | Solution |
|-------|----------|
| "python is not recognized" | Install Python and check "Add to PATH". Restart PowerShell. |
| App doesn't open in browser | Manually go to http://localhost:8501 |
| "No module named streamlit" | Run `pip install -r requirements.txt` in the activated venv |
| Google Sheets import fails | Make sure the sheet is public ("Anyone with the link → Viewer") |
| No metrics computed | Your columns might not match expected names. Check Settings → Column Aliases |
| Financial Analysis shows error | Make sure you have data imported — the page needs at least one dataset active |
| Correlation matrix error | This requires matplotlib. Run `pip install matplotlib` |
| Merge shows 0 matched keys | The join column values don't match. Check for leading/trailing spaces, different cases |

---

## 27. Glossary

| Term | Definition |
|------|-----------|
| **ROAS** | Return on Ad Spend — Revenue ÷ Ad Spend |
| **CPA** | Cost Per Acquisition — Spend ÷ Purchases |
| **CTR** | Click-Through Rate — (Clicks ÷ Impressions) × 100 |
| **CPC** | Cost Per Click — Spend ÷ Clicks |
| **CPM** | Cost Per Mille — (Spend ÷ Impressions) × 1000 |
| **CVR** | Conversion Rate — (Purchases ÷ Clicks) × 100 |
| **POAS** | Profit on Ad Spend — (Revenue - COGS) ÷ Spend |
| **COGS** | Cost of Goods Sold — Direct cost of producing/buying the product |
| **AOV** | Average Order Value — Revenue ÷ Purchases |
| **LTV** | Lifetime Value — AOV × Repeat Rate |
| **CAC** | Customer Acquisition Cost — Same as CPA |
| **Hook Rate** | % of viewers who watch 25% of video ad |
| **Hold Rate** | % of viewers who watch 50% of video ad |
| **Fatigue Index** | Frequency ÷ CTR — Measures audience exhaustion |
| **Ghost Impressions** | Impressions with zero engagement |
| **DAX** | Data Analysis Expressions — Power BI formula language |
| **AST** | Abstract Syntax Tree — How formulas are safely parsed |

---

*Monster Data Analyst v1.0 — Built with The Oracle Protocol v1.0*
