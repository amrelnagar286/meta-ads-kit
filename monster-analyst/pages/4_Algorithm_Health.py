"""
Algorithm Health -- Audience Exhaustion, Retargeting Saturation, Signal-to-Noise.
Monitors Meta's algorithm behavior and detects manipulation.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe

st.set_page_config(page_title="Algorithm Health", page_icon="🤖", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#881798;">Algorithm Health Monitor</h1>'
    '<p style="color:#666;">Audience Exhaustion, Signal Quality, Retargeting Saturation</p>',
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


df = get_active_df()
if df.empty:
    st.info("No data loaded. Go to the main page to import data.")
    st.stop()

cols_lower = {c.lower(): c for c in df.columns}

# ═══════════════════════════════════════════════════════════════════════════════
# ALGORITHM HEALTH METRICS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title" style="background:#881798;">Algorithm Health Indicators</div>', unsafe_allow_html=True)

computed_metrics = {}

# Audience Exhaustion Index
if all(k in cols_lower for k in ("frequency", "spend", "reach")):
    freq = pd.to_numeric(df[cols_lower["frequency"]], errors="coerce").fillna(0)
    spend = pd.to_numeric(df[cols_lower["spend"]], errors="coerce").fillna(0)
    reach = pd.to_numeric(df[cols_lower["reach"]], errors="coerce").fillna(0)
    total_freq = freq.mean()
    total_spend = spend.sum()
    total_reach = reach.sum()
    exhaustion = total_freq * safe_divide(total_spend, total_reach)
    computed_metrics["Audience Exhaustion Index"] = {
        "value": exhaustion,
        "display": f"{exhaustion:.4f}",
        "status": "Healthy" if exhaustion < 0.5 else "Warning" if exhaustion < 1.0 else "Critical",
        "explanation": "Frequency x Cost-per-Reach. Spikes = algo ran out of new people.",
    }

# First-Time Impression Ratio
if "frequency" in cols_lower:
    avg_freq = pd.to_numeric(df[cols_lower["frequency"]], errors="coerce").mean()
    fti = safe_divide(1, avg_freq)
    computed_metrics["First-Time Impression Ratio"] = {
        "value": fti,
        "display": f"{fti:.2f}",
        "status": "Prospecting" if fti > 0.7 else "Mixed" if fti > 0.4 else "Retargeting",
        "explanation": "Close to 1 = prospecting new users. Close to 0.3 = disguised retargeting.",
    }

# Ghost Impression Rate
if all(k in cols_lower for k in ("impressions", "reach")):
    total_imp = pd.to_numeric(df[cols_lower["impressions"]], errors="coerce").sum()
    total_reach = pd.to_numeric(df[cols_lower["reach"]], errors="coerce").sum()
    ghost = safe_divide(total_imp - total_reach, total_imp) * 100
    computed_metrics["Ghost Impression Rate"] = {
        "value": ghost,
        "display": f"{ghost:.1f}%",
        "status": "Clean" if ghost < 25 else "Wasteful" if ghost < 40 else "Toxic",
        "explanation": "% of impressions shown to same people. Above 40% = Meta milking budget.",
    }

# Signal-to-Noise Loss
if all(k in cols_lower for k in ("outbound_clicks", "landing_page_views")):
    oc = pd.to_numeric(df[cols_lower["outbound_clicks"]], errors="coerce").sum()
    lpv = pd.to_numeric(df[cols_lower["landing_page_views"]], errors="coerce").sum()
    snl = safe_divide(oc - lpv, oc) * 100
    computed_metrics["Signal-to-Noise Loss"] = {
        "value": snl,
        "display": f"{snl:.1f}%",
        "status": "Healthy" if snl < 15 else "Warning" if snl < 30 else "Broken",
        "explanation": "Rising = Pixel/CAPI broken, algo learning on garbage data.",
    }

# Average Frequency
if "frequency" in cols_lower:
    avg_freq = pd.to_numeric(df[cols_lower["frequency"]], errors="coerce").mean()
    computed_metrics["Average Frequency"] = {
        "value": avg_freq,
        "display": f"{avg_freq:.2f}",
        "status": "Healthy" if avg_freq < 2 else "Warning" if avg_freq < 3.5 else "Critical",
        "explanation": "Above 3.5 = audience fatigue, CPA spikes incoming.",
    }

if not computed_metrics:
    st.warning("Need frequency, spend, reach, impressions, or outbound_clicks for algorithm health analysis.")
    st.stop()

# Display KPI cards
cols = st.columns(min(len(computed_metrics), 5))
for i, (name, data) in enumerate(computed_metrics.items()):
    with cols[i % len(cols)]:
        badge_class = "badge-healthy" if data["status"] in ("Healthy", "Clean", "Prospecting", "Fresh") else "badge-warning" if data["status"] in ("Warning", "Wasteful", "Mixed", "Fatiguing") else "badge-critical"
        st.markdown(
            f'<div class="metric-card">'
            f'<h3>{name}</h3>'
            f'<div class="metric-value">{data["display"]}</div>'
            f'<div class="metric-trend"><span class="{badge_class}">{data["status"]}</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Trend Analysis")

date_cols = [c for c in df.columns if any(kw in c.lower() for kw in ("date", "day", "time", "period"))]
if date_cols:
    date_col = st.selectbox("Date Column", date_cols, key="algo_date")
    df_trend = df.copy()
    df_trend[date_col] = pd.to_datetime(df_trend[date_col], errors="coerce")
    df_trend = df_trend.dropna(subset=[date_col])

    if not df_trend.empty:
        # Plot frequency over time
        if "frequency" in cols_lower:
            daily_freq = df_trend.groupby(df_trend[date_col].dt.date)[cols_lower["frequency"]].mean().reset_index()
            daily_freq.columns = ["date", "frequency"]
            fig = px.line(daily_freq, x="date", y="frequency", template="plotly_white", title="Average Frequency Over Time")
            fig.add_hline(y=3.5, line_dash="dash", line_color="#D13438", annotation_text="Critical Threshold (3.5)")
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)

        # Plot CPM trend
        if all(k in cols_lower for k in ("spend", "impressions")):
            daily_cpm = df_trend.groupby(df_trend[date_col].dt.date).agg({
                cols_lower["spend"]: "sum",
                cols_lower["impressions"]: "sum",
            }).reset_index()
            daily_cpm.columns = ["date", "spend", "impressions"]
            daily_cpm["cpm"] = daily_cpm["spend"] / daily_cpm["impressions"].replace(0, float("nan")) * 1000
            fig = px.line(daily_cpm, x="date", y="cpm", template="plotly_white", title="CPM Trend")
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No date columns found. Add date data for trend analysis.")

# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY-LEVEL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Algorithm Health by Entity")

group_cols = [c for c in df.columns if c.lower() in ("campaign_name", "adset_name", "ad_name")]
if group_cols:
    group_by = st.selectbox("Group by", group_cols, key="algo_group")
    agg_cols = {}
    if "frequency" in cols_lower:
        agg_cols[cols_lower["frequency"]] = "mean"
    if "impressions" in cols_lower:
        agg_cols[cols_lower["impressions"]] = "sum"
    if "reach" in cols_lower:
        agg_cols[cols_lower["reach"]] = "sum"
    if "spend" in cols_lower:
        agg_cols[cols_lower["spend"]] = "sum"

    if agg_cols:
        grouped = df.groupby(group_by, as_index=False).agg(agg_cols)
        if "impressions" in cols_lower and "reach" in cols_lower:
            imp_col = cols_lower["impressions"]
            reach_col = cols_lower["reach"]
            grouped["ghost_rate_%"] = ((grouped[imp_col] - grouped[reach_col]) / grouped[imp_col].replace(0, float("nan")) * 100).round(2)
        grouped = grouped.sort_values(list(agg_cols.keys())[0], ascending=False)
        downloadable_dataframe(grouped.head(30), key="algo_grouped", label="algorithm_health", use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Diagnostic Recommendations")

recommendations = []
for name, data in computed_metrics.items():
    if data["status"] in ("Critical", "Toxic", "Broken"):
        recommendations.append(f"**{name}** is {data['status']} ({data['display']}): {data['explanation']}")
    elif data["status"] in ("Warning", "Wasteful"):
        recommendations.append(f"**{name}** needs attention ({data['display']}): {data['explanation']}")

if recommendations:
    for rec in recommendations:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #FF8C00;">{rec}</div>', unsafe_allow_html=True)
else:
    st.success("Algorithm health is stable. No critical issues detected.")

st.markdown("---")
render_quick_add_metric("algo")
