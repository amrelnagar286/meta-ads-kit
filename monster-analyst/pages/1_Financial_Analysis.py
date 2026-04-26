"""
Financial Analysis -- Unit Economics, Profitability, Break-even, COGS Integration.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe
from src.formula_engine import apply_formula_to_df, evaluate_formula

st.set_page_config(page_title="Financial Analysis", page_icon="💰", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#D13438;">Financial Analysis</h1>'
    '<p style="color:#666;">Unit Economics, Profitability, Break-even Analysis</p>',
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

# Check if we have computed metrics — apply entity filters to cached snapshot too
_computed = st.session_state.get("computed_metrics_df")
if _computed is not None:
    for _fk in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        _fv = st.session_state.get(_fk)
        if _fv:
            _fc, _vs = _fv
            if _fc in _computed.columns:
                _computed = _computed[_computed[_fc].astype(str).isin(_vs)]
df = _computed if _computed is not None else active_df

st.markdown('<div class="section-title" style="background:#D13438;">Financial Configuration</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    cogs_value = st.number_input("Average COGS per unit ($)", value=15.0, min_value=0.0, step=0.5, key="fin_cogs")
with col2:
    breakeven_roas = st.number_input("Break-even ROAS", value=2.5, min_value=0.1, step=0.1, key="fin_be_roas")
with col3:
    new_customer_pct = st.number_input("Est. New Customer %", value=70, min_value=0, max_value=100, step=5, key="fin_nc_pct")
with col4:
    repeat_rate = st.number_input("Avg Repeat Rate", value=2.5, min_value=1.0, step=0.1, key="fin_repeat")

# Compute financial metrics
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
has_spend = "spend" in [c.lower() for c in df.columns]
has_revenue = any(c.lower() in ("purchase_conversion_value", "revenue", "conversion_value") for c in df.columns)
purchases_col = next((c for c in df.columns if c.lower() == "purchases"), None)
has_purchases = purchases_col is not None

if has_spend and has_revenue:
    # Find actual column names
    spend_col = next(c for c in df.columns if c.lower() == "spend")
    rev_col = next(c for c in df.columns if c.lower() in ("purchase_conversion_value", "revenue", "conversion_value"))

    total_spend = df[spend_col].sum()
    total_revenue = df[rev_col].sum()
    total_purchases = df[purchases_col].sum() if has_purchases else 0

    # KPI Cards
    st.markdown('<div class="section-title" style="background:#D13438;">Financial KPIs (Account Level)</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    with cols[0]:
        roas = safe_divide(total_revenue, total_spend)
        st.markdown(f'<div class="metric-card"><h3>ROAS</h3><div class="metric-value">{roas:.2f}</div></div>', unsafe_allow_html=True)
    with cols[1]:
        cogs_total = total_purchases * cogs_value
        poas = safe_divide(total_revenue - cogs_total - total_spend, total_spend)
        color = "#107C10" if poas > 0 else "#D13438"
        st.markdown(f'<div class="metric-card"><h3>True POAS</h3><div class="metric-value" style="color:{color};">{poas:.2f}</div></div>', unsafe_allow_html=True)
    with cols[2]:
        nc_revenue = total_revenue * (new_customer_pct / 100)
        nc_roas = safe_divide(nc_revenue, total_spend)
        st.markdown(f'<div class="metric-card"><h3>New Customer ROAS</h3><div class="metric-value">{nc_roas:.2f}</div></div>', unsafe_allow_html=True)
    with cols[3]:
        be_delta = roas - breakeven_roas
        color = "#107C10" if be_delta > 0 else "#D13438"
        st.markdown(f'<div class="metric-card"><h3>Break-even Delta</h3><div class="metric-value" style="color:{color};">{be_delta:+.2f}</div></div>', unsafe_allow_html=True)
    with cols[4]:
        gross_profit = total_revenue - cogs_total - total_spend
        st.markdown(f'<div class="metric-card"><h3>Gross Profit</h3><div class="metric-value">${gross_profit:,.0f}</div></div>', unsafe_allow_html=True)

    # Revenue vs Cost breakdown
    st.markdown("---")
    st.markdown("#### Revenue vs Cost Breakdown")

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Revenue", x=["Total"], y=[total_revenue], marker_color="#107C10"))
    fig.add_trace(go.Bar(name="Ad Spend", x=["Total"], y=[total_spend], marker_color="#D13438"))
    fig.add_trace(go.Bar(name="COGS", x=["Total"], y=[cogs_total], marker_color="#FF8C00"))
    fig.add_trace(go.Bar(name="Gross Profit", x=["Total"], y=[gross_profit], marker_color="#0078D4"))
    fig.update_layout(barmode="group", template="plotly_white", font_family="Segoe UI")
    st.plotly_chart(fig, use_container_width=True)

    # Per-entity analysis
    group_cols = [c for c in df.columns if c.lower() in ("campaign_name", "campaign_id", "adset_name", "ad_name")]
    if group_cols:
        st.markdown("---")
        group_by = st.selectbox("Analyze by", group_cols, key="fin_group")
        agg_dict = {spend_col: "sum", rev_col: "sum"}
        if has_purchases:
            agg_dict[purchases_col] = "sum"
        grouped = df.groupby(group_by, as_index=False).agg(agg_dict)
        if has_purchases:
            grouped = grouped.rename(columns={purchases_col: "purchases"})

        grouped["ROAS"] = grouped[rev_col] / grouped[spend_col].replace(0, float("nan"))
        grouped["POAS"] = (grouped[rev_col] - (grouped.get("purchases", 0) * cogs_value) - grouped[spend_col]) / grouped[spend_col].replace(0, float("nan"))
        grouped["BE_Delta"] = grouped["ROAS"] - breakeven_roas
        grouped = grouped.sort_values("ROAS", ascending=False)

        downloadable_dataframe(grouped.style.format({
            spend_col: "${:,.2f}",
            rev_col: "${:,.2f}",
            "ROAS": "{:.2f}",
            "POAS": "{:.2f}",
            "BE_Delta": "{:+.2f}",
        }), key="financial_grouped", label="financial_analysis", use_container_width=True, hide_index=True)

        # Waterfall chart
        fig = px.bar(
            grouped.head(15),
            x=group_by, y="POAS",
            color="POAS",
            color_continuous_scale=["#D13438", "#FFB900", "#107C10"],
            template="plotly_white",
            title="Profit on Ad Spend by Entity",
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Need columns: `spend` and `purchase_conversion_value` (or `revenue`) for financial analysis.")

st.markdown("---")
render_quick_add_metric("fin")
