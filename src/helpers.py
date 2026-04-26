"""Shared utility functions."""

import pandas as pd
import numpy as np
from typing import Any


def safe_divide(a: Any, b: Any, default: float = 0.0) -> float:
    """Safe division returning default when denominator is zero."""
    try:
        if isinstance(b, (pd.Series, np.ndarray)):
            return np.where(b != 0, a / b, default)
        if b == 0:
            return default
        return a / b
    except (TypeError, ValueError, ZeroDivisionError):
        return default


def format_number(value: float, fmt: str = ",.2f") -> str:
    """Format a number with the given format string."""
    try:
        if pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{value:{fmt}}"
    except (ValueError, TypeError):
        return str(value)


def format_currency(value: float, symbol: str = "$") -> str:
    """Format as currency."""
    try:
        if pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{symbol}{value:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float) -> str:
    """Format as percentage."""
    try:
        if pd.isna(value) or np.isinf(value):
            return "N/A"
        return f"{value:.2f}%"
    except (ValueError, TypeError):
        return str(value)


def get_trend_emoji(current: float, previous: float) -> str:
    """Return trend indicator."""
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return ""
    change = (current - previous) / abs(previous) * 100
    if change > 5:
        return " (+{:.1f}%)".format(change)
    elif change < -5:
        return " ({:.1f}%)".format(change)
    return " (flat)"


WINDOWS_11_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}

.main .block-container {
    max-width: 1400px;
    padding: 1rem 2rem;
}

/* Card style */
.metric-card {
    background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
    border: 1px solid #e1e5ee;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    box-shadow: 0 2px 8px rgba(0, 120, 212, 0.08);
}

.metric-card h3 {
    color: #0078D4;
    font-size: 0.85rem;
    margin: 0;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-card .metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0.3rem 0;
}

.metric-card .metric-trend {
    font-size: 0.8rem;
    color: #666;
}

/* Section headers */
.section-title {
    background: linear-gradient(90deg, #0078D4 0%, #106EBE 100%);
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    margin: 1rem 0 0.5rem 0;
}

/* Status badges */
.badge-healthy { background: #DFF6DD; color: #107C10; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
.badge-warning { background: #FFF4CE; color: #9D5D00; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }
.badge-critical { background: #FDE7E9; color: #D13438; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001f3f 0%, #002050 50%, #001530 100%);
}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
    color: #c0d8f0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: #f0f4ff;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #0078D4 !important;
    color: white !important;
}

/* Tables */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* Buttons */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
}
</style>
"""
