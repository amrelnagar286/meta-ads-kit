"""
Utility Helpers — Common helper functions used across the application.
Formatting, parsing, data conversion, and safe computation utilities.
"""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE TYPE CASTING
# ═══════════════════════════════════════════════════════════════════════════════

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_divide(
    numerator: Union[int, float],
    denominator: Union[int, float],
    default: float = 0.0,
) -> float:
    try:
        if denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

def format_currency(amount: Union[str, float, int], currency: str = "USD") -> str:
    try:
        amount = float(amount)
        symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}
        prefix = symbols.get(currency, f"{currency} ")
        return f"{prefix}{amount:,.2f}"
    except (ValueError, TypeError):
        return str(amount)


def format_number(value: Union[str, float, int], decimals: int = 0) -> str:
    try:
        if decimals == 0:
            return f"{int(float(value)):,}"
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: Union[str, float, int], decimals: int = 2) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_ratio(value: Union[str, float, int], decimals: int = 2) -> str:
    try:
        return f"{float(value):.{decimals}f}x"
    except (ValueError, TypeError):
        return str(value)


# ═══════════════════════════════════════════════════════════════════════════════
# META-SPECIFIC PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_meta_actions(actions: Optional[List[Dict]], action_type: str) -> float:
    """Extract a specific action value from Meta's actions array."""
    if not actions:
        return 0.0
    for action in actions:
        if action.get("action_type") == action_type:
            try:
                return float(action.get("value", 0))
            except (ValueError, TypeError):
                return 0.0
    return 0.0


def calculate_roas(insight: Dict) -> float:
    try:
        purchase_roas = insight.get("purchase_roas", [])
        if purchase_roas:
            return float(purchase_roas[0].get("value", 0))
        spend = float(insight.get("spend", 0))
        action_values = insight.get("action_values", [])
        revenue = parse_meta_actions(action_values, "omni_purchase")
        return safe_divide(revenue, spend)
    except (ValueError, TypeError):
        return 0.0


def calculate_cpa(
    insight: Dict, action_type: str = "offsite_conversion"
) -> float:
    try:
        spend = float(insight.get("spend", 0))
        actions = insight.get("actions", [])
        action_count = parse_meta_actions(actions, action_type)
        return safe_divide(spend, action_count)
    except (ValueError, TypeError):
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# DATAFRAME CONVERTERS
# ═══════════════════════════════════════════════════════════════════════════════

def insights_to_dataframe(insights: List[Dict]) -> pd.DataFrame:
    """Convert raw Meta API insights to a clean DataFrame."""
    if not insights:
        return pd.DataFrame()

    rows = []
    for insight in insights:
        row = {
            "Date": insight.get("date_start", ""),
            "Campaign": insight.get("campaign_name", ""),
            "Campaign ID": insight.get("campaign_id", ""),
            "Ad Set": insight.get("adset_name", ""),
            "Ad Set ID": insight.get("adset_id", ""),
            "Ad": insight.get("ad_name", ""),
            "Ad ID": insight.get("ad_id", ""),
            "Spend": safe_float(insight.get("spend", 0)),
            "Impressions": safe_int(insight.get("impressions", 0)),
            "Clicks": safe_int(insight.get("clicks", 0)),
            "CTR": safe_float(insight.get("ctr", 0)),
            "Reach": safe_int(insight.get("reach", 0)),
            "Frequency": safe_float(insight.get("frequency", 0)),
        }

        actions = insight.get("actions", [])
        row["Link Clicks"] = parse_meta_actions(actions, "link_click")
        row["Conversions"] = parse_meta_actions(actions, "offsite_conversion")
        row["Leads"] = parse_meta_actions(actions, "lead")
        row["Purchases"] = parse_meta_actions(actions, "omni_purchase")
        row["Add to Cart"] = parse_meta_actions(actions, "omni_add_to_cart")

        cost_per_action = insight.get("cost_per_action_type", [])
        row["Cost per Link Click"] = parse_meta_actions(cost_per_action, "link_click")
        row["Cost per Conversion"] = parse_meta_actions(
            cost_per_action, "offsite_conversion"
        )

        row["ROAS"] = calculate_roas(insight)
        rows.append(row)

    return pd.DataFrame(rows)


def campaigns_to_dataframe(campaigns: List[Dict]) -> pd.DataFrame:
    rows = []
    for c in campaigns:
        rows.append({
            "ID": c.get("id", ""),
            "Name": c.get("name", ""),
            "Status": c.get("status", ""),
            "Objective": c.get("objective", ""),
            "Buying Type": c.get("buying_type", ""),
            "Daily Budget": safe_float(c.get("daily_budget", 0)) / 100,
            "Lifetime Budget": safe_float(c.get("lifetime_budget", 0)) / 100,
        })
    return pd.DataFrame(rows)


def adsets_to_dataframe(adsets: List[Dict]) -> pd.DataFrame:
    rows = []
    for a in adsets:
        rows.append({
            "ID": a.get("id", ""),
            "Name": a.get("name", ""),
            "Status": a.get("status", ""),
            "Campaign ID": a.get("campaign_id", ""),
            "Daily Budget": safe_float(a.get("daily_budget", 0)) / 100,
            "Lifetime Budget": safe_float(a.get("lifetime_budget", 0)) / 100,
            "Bid Strategy": a.get("bid_strategy", ""),
            "Optimization Goal": a.get("optimization_goal", ""),
        })
    return pd.DataFrame(rows)


def ads_to_dataframe(ads: List[Dict]) -> pd.DataFrame:
    rows = []
    for a in ads:
        rows.append({
            "ID": a.get("id", ""),
            "Name": a.get("name", ""),
            "Status": a.get("status", ""),
            "Ad Set ID": a.get("adset_id", ""),
            "Campaign ID": a.get("campaign_id", ""),
            "Created": a.get("created_time", ""),
        })
    return pd.DataFrame(rows)


def get_status_emoji(status: str) -> str:
    return {
        "ACTIVE": "🟢",
        "PAUSED": "🟡",
        "DELETED": "🔴",
        "ARCHIVED": "⚪",
    }.get(status, "⚫")


def generate_date_ranges() -> Dict[str, Dict[str, str]]:
    today = datetime.now().date()
    return {
        "Today": {"since": str(today), "until": str(today)},
        "Yesterday": {
            "since": str(today - timedelta(days=1)),
            "until": str(today - timedelta(days=1)),
        },
        "Last 7 Days": {
            "since": str(today - timedelta(days=7)),
            "until": str(today),
        },
        "Last 14 Days": {
            "since": str(today - timedelta(days=14)),
            "until": str(today),
        },
        "Last 30 Days": {
            "since": str(today - timedelta(days=30)),
            "until": str(today),
        },
        "This Month": {
            "since": str(today.replace(day=1)),
            "until": str(today),
        },
    }


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
