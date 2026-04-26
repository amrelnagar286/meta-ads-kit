"""
Funnel Analysis -- Full conversion funnel from impression to purchase.
Identifies bottlenecks and drop-off points.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe

st.set_page_config(page_title="Funnel Analysis", page_icon="🔻", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#881798;">Funnel Analysis</h1>'
    '<p style="color:#666;">Conversion Funnel, Bottleneck Detection, Drop-off Analysis</p>',
    unsafe_allow_html=True,
)


def get_active_df():
    name = st.session_state.get("active_dataset")
    if name and name in st.session_state.get("datasets", {}):
        df = st.session_state.datasets[name]
    elif st.session_state.get("merged_data") is not None:
        df = st.session_state.merged_data
    else:
        return pd.DataFrame()
    for key in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        filt = st.session_state.get(key)
        if filt:
            col, vals = filt
            if col in df.columns:
                df = df[df[col].astype(str).isin(vals)]
    return df


active_df = get_active_df()
if active_df.empty:
    st.info("No data loaded. Go to the main page to import data.")
    st.stop()

_computed = st.session_state.get("computed_metrics_df")
if _computed is not None:
    for _fk in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        _fv = st.session_state.get(_fk)
        if _fv:
            _fc, _vs = _fv
            if _fc in _computed.columns:
                _computed = _computed[_computed[_fc].astype(str).isin(_vs)]
df = _computed if _computed is not None else active_df

# Define funnel stages with common column name variations
FUNNEL_STAGES = [
    {"name": "Impressions", "columns": ["impressions"], "color": "#0078D4"},
    {"name": "Reach", "columns": ["reach"], "color": "#106EBE"},
    {"name": "Clicks", "columns": ["clicks", "link_clicks"], "color": "#00B7C3"},
    {"name": "Outbound Clicks", "columns": ["outbound_clicks"], "color": "#107C10"},
    {"name": "Landing Page Views", "columns": ["landing_page_views"], "color": "#FFB900"},
    {"name": "Adds to Cart", "columns": ["adds_to_cart", "add_to_cart"], "color": "#FF8C00"},
    {"name": "Initiated Checkouts", "columns": ["initiated_checkouts", "checkout"], "color": "#E3008C"},
    {"name": "Purchases", "columns": ["purchases", "purchase"], "color": "#D13438"},
    {"name": "Leads", "columns": ["leads"], "color": "#881798"},
    {"name": "Conversations Started", "columns": ["messaging_conversations_started", "messaging_first_reply"], "color": "#002050"},
]


def find_column(df_cols, candidates):
    """Find the first matching column from candidates."""
    lower_map = {c.lower(): c for c in df_cols}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


# Detect available funnel stages
available_stages = []
for stage in FUNNEL_STAGES:
    col = find_column(df.columns, stage["columns"])
    if col:
        total = df[col].sum()
        if total > 0:
            available_stages.append({
                "name": stage["name"],
                "column": col,
                "total": total,
                "color": stage["color"],
            })

if len(available_stages) < 2:
    st.warning("Need at least 2 funnel stages (e.g., impressions and clicks) for funnel analysis.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# FUNNEL VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title" style="background:#881798;">Full Conversion Funnel</div>', unsafe_allow_html=True)

# Funnel chart
fig = go.Figure(go.Funnel(
    y=[s["name"] for s in available_stages],
    x=[s["total"] for s in available_stages],
    textinfo="value+percent initial+percent previous",
    marker=dict(color=[s["color"] for s in available_stages]),
    connector=dict(line=dict(color="#e1e5ee", dash="dot", width=2)),
))
fig.update_layout(
    template="plotly_white",
    font_family="Segoe UI",
    height=500,
)
st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DROP-OFF ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title" style="background:#D13438;">Drop-off Analysis</div>', unsafe_allow_html=True)

dropoff_data = []
for i in range(1, len(available_stages)):
    prev = available_stages[i - 1]
    curr = available_stages[i]
    drop = prev["total"] - curr["total"]
    drop_pct = safe_divide(drop, prev["total"]) * 100
    conv_pct = safe_divide(curr["total"], prev["total"]) * 100
    dropoff_data.append({
        "Stage Transition": f"{prev['name']} -> {curr['name']}",
        "From": f"{prev['total']:,.0f}",
        "To": f"{curr['total']:,.0f}",
        "Drop-off": f"{drop:,.0f}",
        "Drop-off %": f"{drop_pct:.1f}%",
        "Conversion %": f"{conv_pct:.1f}%",
        "_drop_pct": drop_pct,
    })

dropoff_df = pd.DataFrame(dropoff_data)

# Highlight worst drop-offs
downloadable_dataframe(dropoff_df.drop(columns=["_drop_pct"]), key="funnel_dropoff", label="funnel_dropoff", use_container_width=True, hide_index=True)

# Find biggest bottleneck
worst = max(dropoff_data, key=lambda x: x["_drop_pct"])
st.markdown(
    f'<div class="metric-card" style="border-left: 4px solid #D13438;">'
    f'<h3>Biggest Bottleneck</h3>'
    f'<div class="metric-value">{worst["Stage Transition"]}</div>'
    f'<div class="metric-trend">Drop-off: {worst["Drop-off %"]} ({worst["Drop-off"]} lost)</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# Bar chart of drop-off rates
fig = px.bar(
    dropoff_df,
    x="Stage Transition",
    y="_drop_pct",
    color="_drop_pct",
    color_continuous_scale=["#107C10", "#FFB900", "#D13438"],
    template="plotly_white",
    title="Drop-off % at Each Stage",
    labels={"_drop_pct": "Drop-off %"},
)
fig.update_layout(font_family="Segoe UI")
st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PER-ENTITY FUNNEL
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Funnel by Entity")

group_cols = [c for c in df.columns if c.lower() in ("campaign_name", "adset_name", "ad_name", "campaign_id")]
if group_cols:
    group_by = st.selectbox("Group by", group_cols, key="funnel_group")
    stage_cols = [s["column"] for s in available_stages]

    grouped = df.groupby(group_by, as_index=False)[stage_cols].sum()

    # Compute conversion rates between stages
    for i in range(1, len(available_stages)):
        prev_col = available_stages[i - 1]["column"]
        curr_col = available_stages[i]["column"]
        rate_name = f"{available_stages[i - 1]['name']}_to_{available_stages[i]['name']}_%"
        grouped[rate_name] = (grouped[curr_col] / grouped[prev_col].replace(0, float("nan")) * 100).round(2)

    downloadable_dataframe(grouped, key="funnel_grouped", label="funnel_by_entity", use_container_width=True, hide_index=True)

st.markdown("---")
render_quick_add_metric("funnel")
