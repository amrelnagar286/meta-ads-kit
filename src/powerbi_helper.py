"""
Power BI Helper — Generate Power Query M code, DAX measure suggestions,
and data model documentation for Power BI Desktop.
"""
import json
import os
from typing import Dict, List


def generate_power_query_m(folder_path: str) -> str:
    """Generate Power Query M code for folder import."""
    return (
        "let\n"
        f'    Source = Folder.Files("{folder_path}"),\n'
        '    Filtered = Table.SelectRows(Source, each Text.EndsWith([Extension], ".csv")),\n'
        '    Visible = Table.SelectRows(Filtered, each [Attributes]?[Hidden]? <> true),\n'
        '    WithTables = Table.AddColumn(Visible, "Data",\n'
        '        each Csv.Document([Content], [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])),\n'
        '    Promoted = Table.AddColumn(WithTables, "Promoted",\n'
        "        each Table.PromoteHeaders([Data], [PromoteAllScalars=true]))\n"
        "in\n"
        "    Promoted"
    )


def generate_dax_suggestions() -> Dict[str, str]:
    """Return DAX measure suggestions for common KPIs."""
    return {
        "Total Spend": "SUM(FactInsights[spend])",
        "Total Impressions": "SUM(FactInsights[impressions])",
        "Total Clicks": "SUM(FactInsights[clicks])",
        "Total Reach": "SUM(FactInsights[reach])",
        "CTR %": (
            "DIVIDE(SUM(FactInsights[clicks]), "
            "SUM(FactInsights[impressions])) * 100"
        ),
        "CPC": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[clicks]))",
        "CPM": (
            "DIVIDE(SUM(FactInsights[spend]) * 1000, "
            "SUM(FactInsights[impressions]))"
        ),
        "ROAS": (
            "DIVIDE(SUM(FactInsights[purchase_value]), "
            "SUM(FactInsights[spend]))"
        ),
        "CPA": (
            "DIVIDE(SUM(FactInsights[spend]), "
            "SUM(FactInsights[purchases]))"
        ),
        "Frequency": (
            "DIVIDE(SUM(FactInsights[impressions]), "
            "SUM(FactInsights[reach]))"
        ),
        "CVR %": (
            "DIVIDE(SUM(FactInsights[conversions]), "
            "SUM(FactInsights[clicks])) * 100"
        ),
    }


def generate_star_schema_docs() -> str:
    """Return star schema documentation for the Power BI data model."""
    return """
# Power BI Star Schema — Meta Ads

## Fact Table: FactInsights
| Column | Type | Source |
|--------|------|--------|
| date_start | Date | API |
| account_id | Text | API |
| campaign_id | Text | API |
| adset_id | Text | API |
| ad_id | Text | API |
| spend | Decimal | API |
| impressions | Integer | API |
| clicks | Integer | API |
| reach | Integer | API |
| frequency | Decimal | API |
| ctr | Decimal | API |
| cpc | Decimal | API |
| cpm | Decimal | API |
| conversions | Integer | Flattened |
| purchase_value | Decimal | Flattened |
| purchases | Integer | Flattened |

## Dimension Tables

### DimDate
date, year, quarter, month, week, day_of_week, is_weekend

### DimCampaign
campaign_id, campaign_name, objective, buying_type, status

### DimAdSet
adset_id, adset_name, campaign_id, bid_strategy, optimization_goal

### DimAd
ad_id, ad_name, adset_id, campaign_id, creative_id

### DimBreakdown
breakdown_key, breakdown_value, breakdown_type

## Relationships
- FactInsights[date_start] -> DimDate[date] (many-to-one)
- FactInsights[campaign_id] -> DimCampaign[campaign_id] (many-to-one)
- FactInsights[adset_id] -> DimAdSet[adset_id] (many-to-one)
- FactInsights[ad_id] -> DimAd[ad_id] (many-to-one)
"""


def write_powerbi_pack(output_dir: str) -> Dict[str, str]:
    """Write complete Power BI integration pack to disk."""
    os.makedirs(output_dir, exist_ok=True)

    pq_path = os.path.join(output_dir, "power_query_folder_import.m")
    with open(pq_path, "w", encoding="utf-8") as f:
        f.write(generate_power_query_m("{{FOLDER_PATH}}"))

    dax_path = os.path.join(output_dir, "dax_suggestions.json")
    with open(dax_path, "w", encoding="utf-8") as f:
        json.dump(generate_dax_suggestions(), f, ensure_ascii=False, indent=2)

    schema_path = os.path.join(output_dir, "star_schema.md")
    with open(schema_path, "w", encoding="utf-8") as f:
        f.write(generate_star_schema_docs())

    return {"pq": pq_path, "dax": dax_path, "schema": schema_path}
