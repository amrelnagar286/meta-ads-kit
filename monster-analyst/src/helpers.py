"""Shared utility functions."""

import os
import json
import pandas as pd
import numpy as np
from typing import Any


def strip_timezone_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with timezone-aware datetime columns made naive."""
    out = df.copy()
    for c in out.columns:
        if hasattr(out[c], "dt") and hasattr(out[c].dt, "tz") and out[c].dt.tz is not None:
            out[c] = out[c].dt.tz_localize(None)
    return out

# ---------------------------------------------------------------------------
# PERSISTENT CUSTOM METRICS
# ---------------------------------------------------------------------------
CUSTOM_METRICS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "custom_metrics.json")


def load_custom_metrics() -> list:
    """Load user-defined custom metrics from local JSON file."""
    if os.path.exists(CUSTOM_METRICS_FILE):
        try:
            with open(CUSTOM_METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_custom_metrics(metrics: list):
    """Save user-defined custom metrics to local JSON file."""
    os.makedirs(os.path.dirname(CUSTOM_METRICS_FILE), exist_ok=True)
    with open(CUSTOM_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


def render_quick_add_metric(page_key: str):
    """Render a 'Quick Add Custom Metric' expander. Call from any page."""
    import streamlit as st
    from src.formula_engine import validate_formula

    with st.expander("Quick Add Custom Metric"):
        qc_name = st.text_input("Name", placeholder="My Custom Metric", key=f"{page_key}_qc_name")
        qc_formula = st.text_input("Formula", placeholder="purchase_conversion_value / spend", key=f"{page_key}_qc_formula")
        qc_unit = st.selectbox("Unit", ["number", "currency", "percentage", "ratio"], key=f"{page_key}_qc_unit")
        if st.button("Save Permanently", type="primary", key=f"{page_key}_qc_save"):
            if qc_name and qc_formula:
                error = validate_formula(qc_formula)
                if error:
                    st.error(f"Invalid formula: {error}")
                else:
                    metrics = load_custom_metrics()
                    new_cm = {
                        "id": qc_name.lower().replace(" ", "_"),
                        "name": qc_name,
                        "name_ar": qc_name,
                        "formula": qc_formula,
                        "category": "custom",
                        "unit": qc_unit,
                    }
                    existing_ids = {m["id"] for m in metrics}
                    if new_cm["id"] not in existing_ids:
                        metrics.append(new_cm)
                        save_custom_metrics(metrics)
                        if "custom_metrics" in st.session_state:
                            st.session_state.custom_metrics = metrics
                        st.success(f"Saved '{qc_name}' permanently")
                        st.rerun()
                    else:
                        st.info(f"Metric '{qc_name}' already exists.")
            else:
                st.warning("Enter both a name and a formula.")


def downloadable_dataframe(data, key: str, label: str = "table", **kwargs):
    """Display a dataframe with CSV/Excel/JSON download buttons.

    Wraps st.dataframe() and adds a row of download buttons below it.
    *data* can be a DataFrame, a Styler, or anything st.dataframe accepts.
    *key* must be unique across the page to avoid widget id collisions.
    Extra **kwargs are forwarded to st.dataframe().
    """
    import io
    import streamlit as st

    st.dataframe(data, **kwargs)

    # Extract the raw DataFrame from Styler if needed
    if isinstance(data, pd.DataFrame):
        raw_df = data
    elif hasattr(data, "data") and isinstance(data.data, pd.DataFrame):
        raw_df = data.data
    else:
        return  # can't export non-DataFrame objects

    if raw_df.empty:
        return

    dl_cols = st.columns([1, 1, 1, 4])
    csv_bytes = raw_df.to_csv(index=False).encode("utf-8")
    with dl_cols[0]:
        st.download_button(
            "CSV", csv_bytes, file_name=f"{label}.csv",
            mime="text/csv", key=f"dl_csv_{key}",
        )
    with dl_cols[1]:
        buf = io.BytesIO()
        export_df = strip_timezone_for_excel(raw_df)
        export_df.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            "Excel", buf.getvalue(), file_name=f"{label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_xlsx_{key}",
        )
    with dl_cols[2]:
        json_str = raw_df.to_json(orient="records", indent=2, default_handler=str)
        st.download_button(
            "JSON", json_str.encode("utf-8"), file_name=f"{label}.json",
            mime="application/json", key=f"dl_json_{key}",
        )


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
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown h4,
section[data-testid="stSidebar"] .stMarkdown strong,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    color: #e8f0fe !important;
}
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] * {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.15) !important;
}
section[data-testid="stSidebar"] .metric-card {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
}
section[data-testid="stSidebar"] .metric-card h3 {
    color: #7ec8e3 !important;
}
section[data-testid="stSidebar"] .metric-card .metric-value {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .metric-card .metric-trend {
    color: #a0c4e8 !important;
}
section[data-testid="stSidebar"] .stAlert {
    background: rgba(255, 255, 255, 0.08);
    color: #e8f0fe !important;
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
