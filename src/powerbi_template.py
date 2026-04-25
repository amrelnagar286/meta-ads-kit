"""
Power BI Template Generator — Creates a complete .pbit-compatible template package
with data model, DAX measures, Power Query M code, report page definitions,
and star schema documentation.
"""
import json
import os
from typing import Dict, List


# ═══════════════════════════════════════════════════════════════════════════════
# STAR SCHEMA DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════════

DATA_MODEL = {
    "tables": {
        "FactInsights": {
            "description": "Central fact table containing all ad performance metrics",
            "columns": [
                {"name": "date_start", "type": "DateTime", "role": "Date FK"},
                {"name": "date_stop", "type": "DateTime", "role": "Date FK"},
                {"name": "account_id", "type": "Text", "role": "Dimension FK"},
                {"name": "account_name", "type": "Text", "role": "Dimension"},
                {"name": "campaign_id", "type": "Text", "role": "Dimension FK"},
                {"name": "campaign_name", "type": "Text", "role": "Dimension"},
                {"name": "adset_id", "type": "Text", "role": "Dimension FK"},
                {"name": "adset_name", "type": "Text", "role": "Dimension"},
                {"name": "ad_id", "type": "Text", "role": "Dimension FK"},
                {"name": "ad_name", "type": "Text", "role": "Dimension"},
                {"name": "objective", "type": "Text", "role": "Dimension"},
                {"name": "spend", "type": "Decimal", "role": "Measure"},
                {"name": "impressions", "type": "Int64", "role": "Measure"},
                {"name": "clicks", "type": "Int64", "role": "Measure"},
                {"name": "reach", "type": "Int64", "role": "Measure"},
                {"name": "frequency", "type": "Decimal", "role": "Measure"},
                {"name": "ctr", "type": "Decimal", "role": "Measure"},
                {"name": "cpc", "type": "Decimal", "role": "Measure"},
                {"name": "cpm", "type": "Decimal", "role": "Measure"},
                {"name": "conversions", "type": "Int64", "role": "Measure"},
                {"name": "purchase_value", "type": "Decimal", "role": "Measure"},
                {"name": "purchases", "type": "Int64", "role": "Measure"},
                {"name": "leads", "type": "Int64", "role": "Measure"},
                {"name": "video_views", "type": "Int64", "role": "Measure"},
                {"name": "thruplay", "type": "Int64", "role": "Measure"},
                {"name": "quality_ranking", "type": "Text", "role": "Dimension"},
                {"name": "engagement_rate_ranking", "type": "Text", "role": "Dimension"},
                {"name": "conversion_rate_ranking", "type": "Text", "role": "Dimension"},
                {"name": "_level", "type": "Text", "role": "Metadata"},
                {"name": "_breakdown_key", "type": "Text", "role": "Metadata"},
                {"name": "_extracted_at", "type": "DateTime", "role": "Metadata"},
            ],
        },
        "DimDate": {
            "description": "Date dimension table for time intelligence",
            "columns": [
                {"name": "Date", "type": "DateTime", "role": "Key"},
                {"name": "Year", "type": "Int64", "role": "Hierarchy"},
                {"name": "Quarter", "type": "Text", "role": "Hierarchy"},
                {"name": "QuarterNum", "type": "Int64", "role": "Sort"},
                {"name": "Month", "type": "Text", "role": "Hierarchy"},
                {"name": "MonthNum", "type": "Int64", "role": "Sort"},
                {"name": "MonthYear", "type": "Text", "role": "Display"},
                {"name": "Week", "type": "Int64", "role": "Hierarchy"},
                {"name": "DayOfWeek", "type": "Text", "role": "Hierarchy"},
                {"name": "DayOfWeekNum", "type": "Int64", "role": "Sort"},
                {"name": "DayOfMonth", "type": "Int64", "role": "Detail"},
                {"name": "IsWeekend", "type": "Boolean", "role": "Flag"},
                {"name": "IsCurrentMonth", "type": "Boolean", "role": "Flag"},
                {"name": "IsCurrentQuarter", "type": "Boolean", "role": "Flag"},
                {"name": "FiscalYear", "type": "Int64", "role": "Hierarchy"},
                {"name": "FiscalQuarter", "type": "Text", "role": "Hierarchy"},
            ],
        },
        "DimCampaign": {
            "description": "Campaign dimension table",
            "columns": [
                {"name": "campaign_id", "type": "Text", "role": "Key"},
                {"name": "campaign_name", "type": "Text", "role": "Display"},
                {"name": "objective", "type": "Text", "role": "Attribute"},
                {"name": "buying_type", "type": "Text", "role": "Attribute"},
                {"name": "status", "type": "Text", "role": "Attribute"},
                {"name": "daily_budget", "type": "Decimal", "role": "Attribute"},
                {"name": "lifetime_budget", "type": "Decimal", "role": "Attribute"},
                {"name": "bid_strategy", "type": "Text", "role": "Attribute"},
                {"name": "created_time", "type": "DateTime", "role": "Attribute"},
            ],
        },
        "DimAdSet": {
            "description": "Ad Set dimension table",
            "columns": [
                {"name": "adset_id", "type": "Text", "role": "Key"},
                {"name": "adset_name", "type": "Text", "role": "Display"},
                {"name": "campaign_id", "type": "Text", "role": "FK"},
                {"name": "optimization_goal", "type": "Text", "role": "Attribute"},
                {"name": "billing_event", "type": "Text", "role": "Attribute"},
                {"name": "bid_strategy", "type": "Text", "role": "Attribute"},
                {"name": "daily_budget", "type": "Decimal", "role": "Attribute"},
                {"name": "status", "type": "Text", "role": "Attribute"},
            ],
        },
        "DimAd": {
            "description": "Ad dimension table",
            "columns": [
                {"name": "ad_id", "type": "Text", "role": "Key"},
                {"name": "ad_name", "type": "Text", "role": "Display"},
                {"name": "adset_id", "type": "Text", "role": "FK"},
                {"name": "campaign_id", "type": "Text", "role": "FK"},
                {"name": "creative_id", "type": "Text", "role": "Attribute"},
                {"name": "status", "type": "Text", "role": "Attribute"},
            ],
        },
        "DimBreakdown": {
            "description": "Breakdown dimension for demographic/placement analysis",
            "columns": [
                {"name": "breakdown_key", "type": "Text", "role": "Key"},
                {"name": "breakdown_value", "type": "Text", "role": "Display"},
                {"name": "breakdown_type", "type": "Text", "role": "Category"},
            ],
        },
    },
    "relationships": [
        {"from": "FactInsights.date_start", "to": "DimDate.Date", "cardinality": "many-to-one"},
        {"from": "FactInsights.campaign_id", "to": "DimCampaign.campaign_id", "cardinality": "many-to-one"},
        {"from": "FactInsights.adset_id", "to": "DimAdSet.adset_id", "cardinality": "many-to-one"},
        {"from": "FactInsights.ad_id", "to": "DimAd.ad_id", "cardinality": "many-to-one"},
        {"from": "DimAdSet.campaign_id", "to": "DimCampaign.campaign_id", "cardinality": "many-to-one"},
        {"from": "DimAd.adset_id", "to": "DimAdSet.adset_id", "cardinality": "many-to-one"},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# DAX MEASURES — 35+ MEASURES WITH TIME INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════════

DAX_MEASURES = {
    # Core Metrics
    "Total Spend": "SUM(FactInsights[spend])",
    "Total Impressions": "SUM(FactInsights[impressions])",
    "Total Clicks": "SUM(FactInsights[clicks])",
    "Total Reach": "SUM(FactInsights[reach])",
    "Total Conversions": "SUM(FactInsights[conversions])",
    "Total Revenue": "SUM(FactInsights[purchase_value])",
    "Total Purchases": "SUM(FactInsights[purchases])",
    "Total Leads": "SUM(FactInsights[leads])",
    "Total Video Views": "SUM(FactInsights[video_views])",

    # Calculated KPIs
    "CTR %": "DIVIDE(SUM(FactInsights[clicks]), SUM(FactInsights[impressions])) * 100",
    "CPC": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[clicks]))",
    "CPM": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[impressions])) * 1000",
    "ROAS": "DIVIDE(SUM(FactInsights[purchase_value]), SUM(FactInsights[spend]))",
    "CPA": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[conversions]))",
    "CVR %": "DIVIDE(SUM(FactInsights[conversions]), SUM(FactInsights[clicks])) * 100",
    "AOV": "DIVIDE(SUM(FactInsights[purchase_value]), SUM(FactInsights[purchases]))",
    "Frequency": "DIVIDE(SUM(FactInsights[impressions]), SUM(FactInsights[reach]))",
    "Cost Per Lead": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[leads]))",
    "ThruPlay Rate %": "DIVIDE(SUM(FactInsights[thruplay]), SUM(FactInsights[impressions])) * 100",
    "Cost Per ThruPlay": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[thruplay]))",

    # Time Intelligence — Previous Period
    "Spend PP": "CALCULATE([Total Spend], DATEADD(DimDate[Date], -1, MONTH))",
    "Impressions PP": "CALCULATE([Total Impressions], DATEADD(DimDate[Date], -1, MONTH))",
    "Clicks PP": "CALCULATE([Total Clicks], DATEADD(DimDate[Date], -1, MONTH))",
    "Revenue PP": "CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, MONTH))",
    "Conversions PP": "CALCULATE([Total Conversions], DATEADD(DimDate[Date], -1, MONTH))",

    # Time Intelligence — YoY
    "Spend YoY": "CALCULATE([Total Spend], DATEADD(DimDate[Date], -1, YEAR))",
    "Revenue YoY": "CALCULATE([Total Revenue], DATEADD(DimDate[Date], -1, YEAR))",

    # Change Calculations
    "Spend Change %": "DIVIDE([Total Spend] - [Spend PP], [Spend PP]) * 100",
    "Revenue Change %": "DIVIDE([Total Revenue] - [Revenue PP], [Revenue PP]) * 100",
    "Clicks Change %": "DIVIDE([Total Clicks] - [Clicks PP], [Clicks PP]) * 100",
    "ROAS Change %": """
VAR CurrentROAS = [ROAS]
VAR PreviousROAS = CALCULATE([ROAS], DATEADD(DimDate[Date], -1, MONTH))
RETURN DIVIDE(CurrentROAS - PreviousROAS, PreviousROAS) * 100""",

    # Running Totals
    "Spend YTD": "TOTALYTD([Total Spend], DimDate[Date])",
    "Revenue YTD": "TOTALYTD([Total Revenue], DimDate[Date])",
    "Spend MTD": "TOTALMTD([Total Spend], DimDate[Date])",
    "Revenue MTD": "TOTALMTD([Total Revenue], DimDate[Date])",

    # Moving Averages
    "Spend 7-Day MA": """
AVERAGEX(
    DATESINPERIOD(DimDate[Date], MAX(DimDate[Date]), -7, DAY),
    [Total Spend]
)""",
    "CPC 7-Day MA": """
AVERAGEX(
    DATESINPERIOD(DimDate[Date], MAX(DimDate[Date]), -7, DAY),
    [CPC]
)""",
}


# ═══════════════════════════════════════════════════════════════════════════════
# POWER QUERY M CODE
# ═══════════════════════════════════════════════════════════════════════════════

POWER_QUERY_SCRIPTS = {
    "FactInsights_FolderImport": """let
    FolderPath = "{{FOLDER_PATH}}",
    Source = Folder.Files(FolderPath),
    FilteredCSV = Table.SelectRows(Source, each Text.EndsWith([Extension], ".csv")),
    FilteredVisible = Table.SelectRows(FilteredCSV, each [Attributes]?[Hidden]? <> true),
    AddedData = Table.AddColumn(FilteredVisible, "ParsedData",
        each Csv.Document([Content], [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])),
    PromotedHeaders = Table.AddColumn(AddedData, "PromotedTable",
        each Table.PromoteHeaders([ParsedData], [PromoteAllScalars=true])),
    ExpandedTables = Table.Combine(PromotedHeaders[PromotedTable]),
    // Type conversions
    TypedColumns = Table.TransformColumnTypes(ExpandedTables, {
        {"spend", type number},
        {"impressions", Int64.Type},
        {"clicks", Int64.Type},
        {"reach", Int64.Type},
        {"frequency", type number},
        {"ctr", type number},
        {"cpc", type number},
        {"cpm", type number},
        {"date_start", type date}
    })
in
    TypedColumns""",

    "DimDate_Generate": """let
    StartDate = #date(2020, 1, 1),
    EndDate = Date.From(DateTime.LocalNow()),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    TypedDate = Table.TransformColumnTypes(DateTable, {{"Date", type date}}),
    AddYear = Table.AddColumn(TypedDate, "Year", each Date.Year([Date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "Quarter",
        each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),
    AddQuarterNum = Table.AddColumn(AddQuarter, "QuarterNum",
        each Date.QuarterOfYear([Date]), Int64.Type),
    AddMonth = Table.AddColumn(AddQuarterNum, "Month",
        each Date.ToText([Date], "MMM"), type text),
    AddMonthNum = Table.AddColumn(AddMonth, "MonthNum",
        each Date.Month([Date]), Int64.Type),
    AddMonthYear = Table.AddColumn(AddMonthNum, "MonthYear",
        each Date.ToText([Date], "MMM yyyy"), type text),
    AddWeek = Table.AddColumn(AddMonthYear, "Week",
        each Date.WeekOfYear([Date]), Int64.Type),
    AddDayOfWeek = Table.AddColumn(AddWeek, "DayOfWeek",
        each Date.DayOfWeekName([Date]), type text),
    AddDayOfWeekNum = Table.AddColumn(AddDayOfWeek, "DayOfWeekNum",
        each Date.DayOfWeek([Date]), Int64.Type),
    AddDayOfMonth = Table.AddColumn(AddDayOfWeekNum, "DayOfMonth",
        each Date.Day([Date]), Int64.Type),
    AddIsWeekend = Table.AddColumn(AddDayOfMonth, "IsWeekend",
        each Date.DayOfWeek([Date]) >= 5, type logical),
    AddIsCurrentMonth = Table.AddColumn(AddIsWeekend, "IsCurrentMonth",
        each Date.IsInCurrentMonth([Date]), type logical),
    AddIsCurrentQuarter = Table.AddColumn(AddIsCurrentMonth, "IsCurrentQuarter",
        each Date.IsInCurrentQuarter([Date]), type logical),
    AddFiscalYear = Table.AddColumn(AddIsCurrentQuarter, "FiscalYear",
        each if Date.Month([Date]) >= 10 then Date.Year([Date]) + 1 else Date.Year([Date]), Int64.Type),
    AddFiscalQuarter = Table.AddColumn(AddFiscalYear, "FiscalQuarter",
        each "FQ" & Text.From(Number.RoundUp((Date.Month([Date]) + 2) / 3)), type text)
in
    AddFiscalQuarter""",

    "DimCampaign_FromEntities": """let
    Source = Csv.Document(File.Contents("{{FOLDER_PATH}}/entities/campaigns.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    TypedColumns = Table.TransformColumnTypes(PromotedHeaders, {
        {"campaign_id", type text},
        {"campaign_name", type text},
        {"daily_budget", type number},
        {"lifetime_budget", type number}
    }),
    Deduplicated = Table.Distinct(TypedColumns, {"campaign_id"})
in
    Deduplicated""",

    "DimAdSet_FromEntities": """let
    Source = Csv.Document(File.Contents("{{FOLDER_PATH}}/entities/adsets.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Deduplicated = Table.Distinct(PromotedHeaders, {"adset_id"})
in
    Deduplicated""",

    "DimAd_FromEntities": """let
    Source = Csv.Document(File.Contents("{{FOLDER_PATH}}/entities/ads.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Deduplicated = Table.Distinct(PromotedHeaders, {"ad_id"})
in
    Deduplicated""",
}


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT PAGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

REPORT_PAGES = [
    {
        "name": "Executive Summary",
        "description": "High-level KPI overview for stakeholders",
        "visuals": [
            {"type": "KPI Card", "measure": "Total Spend", "trend": "Spend Change %", "position": "top-left"},
            {"type": "KPI Card", "measure": "Total Revenue", "trend": "Revenue Change %", "position": "top-center-left"},
            {"type": "KPI Card", "measure": "ROAS", "trend": "ROAS Change %", "position": "top-center-right"},
            {"type": "KPI Card", "measure": "Total Conversions", "trend": "Clicks Change %", "position": "top-right"},
            {"type": "Line Chart", "x": "DimDate[Date]", "y": ["Total Spend", "Total Revenue"], "position": "middle-left"},
            {"type": "Bar Chart", "x": "DimCampaign[campaign_name]", "y": "Total Spend", "position": "middle-right"},
            {"type": "Donut Chart", "category": "DimCampaign[objective]", "value": "Total Spend", "position": "bottom-left"},
            {"type": "Table", "columns": ["Campaign", "Spend", "ROAS", "CPA", "CTR %"], "position": "bottom-right"},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[campaign_name]", "DimCampaign[objective]"],
    },
    {
        "name": "Campaign Deep Dive",
        "description": "Detailed campaign-level performance analysis",
        "visuals": [
            {"type": "Matrix", "rows": "DimCampaign[campaign_name]",
             "values": ["Total Spend", "Total Impressions", "Total Clicks", "CTR %", "CPC", "ROAS", "CPA"]},
            {"type": "Clustered Bar", "x": "DimCampaign[campaign_name]", "y": ["Total Spend", "Total Revenue"]},
            {"type": "Line Chart", "x": "DimDate[Date]", "y": "CTR %", "legend": "DimCampaign[campaign_name]"},
            {"type": "Scatter", "x": "CPC", "y": "CTR %", "size": "Total Spend", "color": "DimCampaign[objective]"},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[status]", "DimCampaign[objective]"],
        "drillthrough": {"field": "DimCampaign[campaign_name]"},
    },
    {
        "name": "Creative Analysis",
        "description": "Ad creative performance comparison",
        "visuals": [
            {"type": "Matrix", "rows": "DimAd[ad_name]",
             "values": ["Total Spend", "Total Impressions", "CTR %", "CPC", "Total Conversions"]},
            {"type": "Bar Chart", "x": "DimAd[ad_name]", "y": "CTR %", "sort": "descending"},
            {"type": "Line Chart", "x": "DimDate[Date]", "y": "CTR %", "legend": "DimAd[ad_name]"},
            {"type": "KPI Card", "measure": "Frequency", "target": 3.5},
            {"type": "Conditional Formatting", "field": "Frequency", "rules": [
                {"condition": "> 3.5", "color": "#D13438"},
                {"condition": "> 2.0", "color": "#FFB900"},
                {"condition": "<= 2.0", "color": "#107C10"},
            ]},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[campaign_name]", "FactInsights[quality_ranking]"],
    },
    {
        "name": "Audience Insights",
        "description": "Demographic and geographic performance breakdown",
        "visuals": [
            {"type": "Stacked Bar", "x": "age", "y": "Total Spend", "legend": "gender"},
            {"type": "Map", "location": "country", "value": "Total Spend"},
            {"type": "Matrix", "rows": ["age", "gender"], "values": ["Total Spend", "CTR %", "CPC", "CPA"]},
            {"type": "Pie Chart", "category": "gender", "value": "Total Spend"},
            {"type": "Bar Chart", "x": "device_platform", "y": "Total Clicks"},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[campaign_name]"],
        "note": "Requires data extracted with age, gender, country, device breakdowns",
    },
    {
        "name": "Time Analysis",
        "description": "Time-based trends, seasonality, and day-of-week patterns",
        "visuals": [
            {"type": "Line Chart", "x": "DimDate[Date]", "y": ["Spend 7-Day MA", "Total Spend"]},
            {"type": "Heatmap", "x": "DimDate[DayOfWeek]", "y": "Hour", "value": "Total Spend"},
            {"type": "Clustered Column", "x": "DimDate[Month]", "y": ["Total Spend", "Spend PP"]},
            {"type": "Waterfall", "category": "DimDate[MonthYear]", "value": "Total Spend"},
            {"type": "KPI Card", "measure": "Spend YTD"},
            {"type": "KPI Card", "measure": "Revenue YTD"},
            {"type": "KPI Card", "measure": "Spend MTD"},
        ],
        "slicers": ["DimDate[Year]", "DimDate[Quarter]", "DimDate[IsWeekend]"],
    },
    {
        "name": "Funnel & ROAS",
        "description": "Conversion funnel and return on ad spend analysis",
        "visuals": [
            {"type": "Funnel", "stages": [
                {"label": "Impressions", "measure": "Total Impressions"},
                {"label": "Clicks", "measure": "Total Clicks"},
                {"label": "Conversions", "measure": "Total Conversions"},
                {"label": "Purchases", "measure": "Total Purchases"},
            ]},
            {"type": "Gauge", "measure": "ROAS", "target": 3.0, "min": 0, "max": 10},
            {"type": "Line Chart", "x": "DimDate[Date]", "y": ["ROAS", "CPA"]},
            {"type": "Matrix", "rows": "DimCampaign[campaign_name]",
             "values": ["ROAS", "CPA", "CVR %", "AOV", "Total Revenue"]},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[objective]"],
    },
    {
        "name": "Placement Performance",
        "description": "Performance by publisher platform and placement position",
        "visuals": [
            {"type": "Stacked Bar", "x": "publisher_platform", "y": "Total Spend", "legend": "platform_position"},
            {"type": "Matrix", "rows": ["publisher_platform", "platform_position"],
             "values": ["Total Spend", "Total Impressions", "CTR %", "CPC"]},
            {"type": "Donut Chart", "category": "publisher_platform", "value": "Total Impressions"},
        ],
        "slicers": ["DimDate[Date]", "DimCampaign[campaign_name]"],
        "note": "Requires data extracted with placement breakdown",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL FORMATTING RULES
# ═══════════════════════════════════════════════════════════════════════════════

CONDITIONAL_FORMATTING = {
    "CTR %": {
        "rules": [
            {"type": "background", "condition": "< 0.5", "color": "#FDE7E9"},
            {"type": "background", "condition": "0.5-1.0", "color": "#FFF4CE"},
            {"type": "background", "condition": "> 1.0", "color": "#DFF6DD"},
        ],
    },
    "ROAS": {
        "rules": [
            {"type": "icon", "condition": "< 1.0", "icon": "red_down_arrow"},
            {"type": "icon", "condition": "1.0-3.0", "icon": "yellow_dash"},
            {"type": "icon", "condition": "> 3.0", "icon": "green_up_arrow"},
        ],
    },
    "Frequency": {
        "rules": [
            {"type": "data_bar", "min_color": "#DFF6DD", "max_color": "#FDE7E9"},
        ],
    },
    "Spend Change %": {
        "rules": [
            {"type": "font_color", "condition": "< 0", "color": "#D13438"},
            {"type": "font_color", "condition": "> 0", "color": "#107C10"},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════════════════

THEME = {
    "name": "Meta Ads Dashboard - Windows 11",
    "dataColors": [
        "#0078D4", "#107C10", "#FFB900", "#D13438", "#881798",
        "#00B7C3", "#E3008C", "#4F6BED", "#CA5010", "#498205",
        "#005B70", "#8764B8", "#867365", "#038387", "#515C6B",
    ],
    "background": "#FFFFFF",
    "foreground": "#323130",
    "tableAccent": "#0078D4",
    "visualStyles": {
        "page": {"background": {"color": "#F3F2F1"}},
        "title": {"fontFamily": "Segoe UI", "fontSize": 14, "fontColor": "#323130"},
        "header": {"fontFamily": "Segoe UI Semibold", "fontSize": 12, "fontColor": "#0078D4"},
        "card": {"background": "#FFFFFF", "borderRadius": 8, "shadow": "0 1px 3px rgba(0,0,0,0.12)"},
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def generate_powerbi_template(output_dir: str, data_folder: str = "{{FOLDER_PATH}}") -> Dict[str, str]:
    """Generate complete Power BI template package."""
    os.makedirs(output_dir, exist_ok=True)

    files = {}

    # 1. Data Model
    model_path = os.path.join(output_dir, "data_model.json")
    with open(model_path, "w", encoding="utf-8") as f:
        json.dump(DATA_MODEL, f, indent=2, ensure_ascii=False)
    files["data_model"] = model_path

    # 2. DAX Measures
    dax_path = os.path.join(output_dir, "dax_measures.json")
    with open(dax_path, "w", encoding="utf-8") as f:
        json.dump(DAX_MEASURES, f, indent=2, ensure_ascii=False)
    files["dax_measures"] = dax_path

    # DAX as .dax text file for easy copy-paste
    dax_text_path = os.path.join(output_dir, "dax_measures.dax")
    with open(dax_text_path, "w", encoding="utf-8") as f:
        f.write("// ═══════════════════════════════════════════════════════════════\n")
        f.write("// META ADS DASHBOARD — DAX MEASURES\n")
        f.write(f"// Total measures: {len(DAX_MEASURES)}\n")
        f.write("// ═══════════════════════════════════════════════════════════════\n\n")
        for name, formula in DAX_MEASURES.items():
            f.write(f"// {name}\n")
            f.write(f"{name} = {formula.strip()}\n\n")
    files["dax_text"] = dax_text_path

    # 3. Power Query M Code
    pq_dir = os.path.join(output_dir, "power_query")
    os.makedirs(pq_dir, exist_ok=True)
    for name, code in POWER_QUERY_SCRIPTS.items():
        pq_path = os.path.join(pq_dir, f"{name}.m")
        with open(pq_path, "w", encoding="utf-8") as f:
            f.write(code.replace("{{FOLDER_PATH}}", data_folder))
        files[f"pq_{name}"] = pq_path

    # 4. Report Pages
    pages_path = os.path.join(output_dir, "report_pages.json")
    with open(pages_path, "w", encoding="utf-8") as f:
        json.dump(REPORT_PAGES, f, indent=2, ensure_ascii=False)
    files["report_pages"] = pages_path

    # 5. Theme
    theme_path = os.path.join(output_dir, "theme.json")
    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(THEME, f, indent=2, ensure_ascii=False)
    files["theme"] = theme_path

    # 6. Conditional Formatting
    cf_path = os.path.join(output_dir, "conditional_formatting.json")
    with open(cf_path, "w", encoding="utf-8") as f:
        json.dump(CONDITIONAL_FORMATTING, f, indent=2, ensure_ascii=False)
    files["conditional_formatting"] = cf_path

    # 7. Star Schema Documentation (Markdown)
    schema_path = os.path.join(output_dir, "STAR_SCHEMA.md")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write("# Power BI Star Schema — Meta Ads Dashboard\n\n")
        f.write(f"**Total Tables:** {len(DATA_MODEL['tables'])}\n")
        f.write(f"**Total Relationships:** {len(DATA_MODEL['relationships'])}\n")
        f.write(f"**Total DAX Measures:** {len(DAX_MEASURES)}\n")
        f.write(f"**Report Pages:** {len(REPORT_PAGES)}\n\n")

        for table_name, table_def in DATA_MODEL["tables"].items():
            f.write(f"## {table_name}\n")
            f.write(f"_{table_def['description']}_\n\n")
            f.write("| Column | Type | Role |\n")
            f.write("|--------|------|------|\n")
            for col in table_def["columns"]:
                f.write(f"| {col['name']} | {col['type']} | {col['role']} |\n")
            f.write("\n")

        f.write("## Relationships\n\n")
        for rel in DATA_MODEL["relationships"]:
            f.write(f"- `{rel['from']}` → `{rel['to']}` ({rel['cardinality']})\n")

        f.write("\n## DAX Measures\n\n")
        for name, formula in DAX_MEASURES.items():
            f.write(f"### {name}\n```dax\n{formula.strip()}\n```\n\n")

        f.write("\n## Report Pages\n\n")
        for page in REPORT_PAGES:
            f.write(f"### {page['name']}\n")
            f.write(f"_{page['description']}_\n\n")
            f.write("**Visuals:**\n")
            for v in page["visuals"]:
                f.write(f"- {v['type']}: {v.get('measure', v.get('y', v.get('stages', '')))}\n")
            f.write(f"\n**Slicers:** {', '.join(page.get('slicers', []))}\n\n")
    files["star_schema_docs"] = schema_path

    # 8. Setup Guide
    guide_path = os.path.join(output_dir, "SETUP_GUIDE.md")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write("""# Power BI Setup Guide — Meta Ads Dashboard

## Quick Start

### Step 1: Open Power BI Desktop
Download from https://powerbi.microsoft.com/desktop/

### Step 2: Import Data
1. Open Power BI Desktop
2. Click "Get Data" → "Folder"
3. Navigate to your extracted data folder (e.g., `output/run_YYYYMMDD_HHMMSS/raw/`)
4. Click "Combine & Transform"
5. Alternatively, use the Power Query M code from `power_query/FactInsights_FolderImport.m`

### Step 3: Create Date Table
1. Go to "Modeling" → "New Table"
2. Paste the M code from `power_query/DimDate_Generate.m`
3. Or create a calculated table using DAX

### Step 4: Set Up Relationships
1. Go to Model view
2. Drag `FactInsights[date_start]` to `DimDate[Date]`
3. Drag `FactInsights[campaign_id]` to `DimCampaign[campaign_id]`
4. Set all relationships as many-to-one

### Step 5: Import DAX Measures
1. Go to "Modeling" → "New Measure"
2. Copy measures from `dax_measures.dax`
3. Create all 35+ measures

### Step 6: Apply Theme
1. Go to "View" → "Themes" → "Browse for themes"
2. Select `theme.json`

### Step 7: Build Report Pages
Follow the layout specifications in `report_pages.json` to create:
1. Executive Summary
2. Campaign Deep Dive
3. Creative Analysis
4. Audience Insights
5. Time Analysis
6. Funnel & ROAS
7. Placement Performance

### Step 8: Apply Conditional Formatting
Use the rules in `conditional_formatting.json` to highlight:
- CTR (red/yellow/green backgrounds)
- ROAS (icon sets)
- Frequency (data bars)
- Change metrics (font colors)

## Data Refresh
- Set up a scheduled refresh for the data source folder
- New extractions will be automatically picked up on refresh
- Recommended refresh frequency: every 4-6 hours

## Tips
- Use bookmarks for different views (executive, operational, tactical)
- Set up row-level security for multi-user access
- Export to PDF for stakeholder reports
- Pin key visuals to a shared dashboard
""")
    files["setup_guide"] = guide_path

    return files
