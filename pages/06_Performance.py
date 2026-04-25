"""
Real-time Performance Monitor — Live metrics, alerts, performance trends,
anomaly detection, and health scoring for all campaigns.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.meta_api import MetaAPIManager
from src.extractor import MetaAdsExtractor
from src.kpi_engine import compute_kpis, STANDARD_KPIS
from src.helpers import (
    format_currency, format_number, format_percentage, format_ratio,
    safe_float, safe_int, safe_divide,
)

st.set_page_config(page_title="Performance Monitor", page_icon="📈", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .alert-critical { background: #FDE7E9; border-left: 4px solid #D13438;
        padding: 12px; border-radius: 4px; margin: 8px 0; }
    .alert-warning { background: #FFF4CE; border-left: 4px solid #FFB900;
        padding: 12px; border-radius: 4px; margin: 8px 0; }
    .alert-success { background: #DFF6DD; border-left: 4px solid #107C10;
        padding: 12px; border-radius: 4px; margin: 8px 0; }
    .health-score { font-size: 2rem; font-weight: 700; text-align: center; }
    .health-good { color: #107C10; }
    .health-warning { color: #FFB900; }
    .health-critical { color: #D13438; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Real-time Performance Monitor")

api = get_api()

tab_live, tab_trends, tab_alerts, tab_health, tab_anomaly = st.tabs([
    "Live Dashboard", "Performance Trends", "Alerts", "Health Score", "Anomaly Detection",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: LIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_live:
    st.markdown('<div class="section-title">Live Performance</div>', unsafe_allow_html=True)

    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        date_range = st.selectbox("Date Range", ["today", "yesterday", "last_3d", "last_7d", "last_14d", "last_30d"], index=3, key="lv_date")
    with col_ctrl2:
        st.write("")
        st.write("")
        refresh = st.button("Refresh Data", type="primary", use_container_width=True, key="lv_refresh")

    try:
        ext = MetaAdsExtractor(
            st.session_state.access_token,
            st.session_state.ad_account_id,
        )

        with st.spinner("Loading performance data..."):
            df = ext.fetch_insights(level="campaign", breakdown_key="none", preset=date_range)

        if not df.empty:
            df = compute_kpis(df)

            # Aggregate KPIs
            total_spend = safe_float(df["spend"].sum())
            total_imps = safe_int(df["impressions"].sum())
            total_clicks = safe_int(df["clicks"].sum())
            total_reach = safe_int(df.get("reach", pd.Series([0])).sum())
            ctr = safe_divide(total_clicks, total_imps) * 100
            cpc = safe_divide(total_spend, total_clicks)
            cpm = safe_divide(total_spend, total_imps) * 1000
            freq = safe_divide(total_imps, total_reach) if total_reach else 0

            # KPI Cards
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Spend", format_currency(total_spend))
            c2.metric("Impressions", format_number(total_imps))
            c3.metric("Clicks", format_number(total_clicks))
            c4.metric("Reach", format_number(total_reach))

            c5, c6, c7, c8 = st.columns(4)
            c5.metric("CTR", format_percentage(ctr))
            c6.metric("CPC", format_currency(cpc))
            c7.metric("CPM", format_currency(cpm))
            c8.metric("Frequency", format_ratio(freq))

            # Campaign breakdown
            st.markdown("### Campaign Performance")
            if "campaign_name" in df.columns:
                camp_df = df.groupby("campaign_name").agg({
                    "spend": "sum",
                    "impressions": "sum",
                    "clicks": "sum",
                }).reset_index()
                camp_df["CTR %"] = camp_df.apply(
                    lambda r: round(safe_divide(r["clicks"], r["impressions"]) * 100, 2), axis=1
                )
                camp_df["CPC"] = camp_df.apply(
                    lambda r: round(safe_divide(r["spend"], r["clicks"]), 2), axis=1
                )
                camp_df.columns = ["Campaign", "Spend", "Impressions", "Clicks", "CTR %", "CPC"]
                camp_df = camp_df.sort_values("Spend", ascending=False)
                st.dataframe(camp_df, use_container_width=True, hide_index=True)

            # Spend distribution chart
            if "campaign_name" in df.columns:
                st.markdown("### Spend Distribution")
                chart_df = df.groupby("campaign_name")["spend"].sum().sort_values(ascending=False)
                st.bar_chart(chart_df)
        else:
            st.info("No performance data available for this period.")
    except Exception as e:
        st.error(f"Failed to load data: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PERFORMANCE TRENDS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_trends:
    st.markdown('<div class="section-title">Performance Trends</div>', unsafe_allow_html=True)

    trend_metric = st.selectbox(
        "Metric to trend",
        ["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "reach"],
        key="tr_metric",
    )
    trend_period = st.selectbox("Period", ["last_7d", "last_14d", "last_30d", "last_60d", "last_90d"], index=2, key="tr_period")

    if st.button("Load Trends", type="primary", key="tr_load"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )
            df = ext.fetch_insights(level="account", breakdown_key="none", preset=trend_period)

            if not df.empty and "date_start" in df.columns:
                if trend_metric in df.columns:
                    trend_df = df[["date_start", trend_metric]].copy()
                    trend_df[trend_metric] = trend_df[trend_metric].astype(float)
                    trend_df = trend_df.sort_values("date_start")

                    st.line_chart(trend_df.set_index("date_start")[trend_metric])

                    # Period-over-period comparison
                    if len(trend_df) > 1:
                        mid = len(trend_df) // 2
                        first_half = trend_df.iloc[:mid][trend_metric].sum()
                        second_half = trend_df.iloc[mid:][trend_metric].sum()
                        change = safe_divide(second_half - first_half, first_half) * 100

                        col_t1, col_t2, col_t3 = st.columns(3)
                        col_t1.metric("First Half", f"{first_half:,.2f}")
                        col_t2.metric("Second Half", f"{second_half:,.2f}")
                        col_t3.metric("Change", f"{change:+.1f}%")
                else:
                    st.warning(f"Metric '{trend_metric}' not found in data.")
            else:
                st.info("No trend data available.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_alerts:
    st.markdown('<div class="section-title">Performance Alerts</div>', unsafe_allow_html=True)

    st.markdown("### Alert Configuration")
    col_al1, col_al2, col_al3 = st.columns(3)
    with col_al1:
        ctr_threshold = st.number_input("Min CTR % (bleeder threshold)", value=1.0, step=0.1, key="al_ctr")
        freq_threshold = st.number_input("Max Frequency (fatigue threshold)", value=3.5, step=0.1, key="al_freq")
    with col_al2:
        cpc_threshold = st.number_input("Max CPC ($)", value=5.0, step=0.5, key="al_cpc")
        min_spend = st.number_input("Min Spend for alerts ($)", value=10.0, step=5.0, key="al_min_spend")
    with col_al3:
        alert_period = st.selectbox("Alert Period", ["today", "last_3d", "last_7d"], key="al_period")

    if st.button("Run Alert Scan", type="primary", use_container_width=True, key="al_scan"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )
            df = ext.fetch_insights(level="ad", breakdown_key="none", preset=alert_period)

            if not df.empty:
                df["spend"] = df["spend"].astype(float)
                df["impressions"] = df["impressions"].astype(float)
                df["clicks"] = df["clicks"].astype(float)

                # Bleeders: high spend, low CTR
                bleeders = df[
                    (df["spend"] >= min_spend) &
                    (df.apply(lambda r: safe_divide(r["clicks"], r["impressions"]) * 100, axis=1) < ctr_threshold)
                ]
                if not bleeders.empty:
                    st.markdown(f'<div class="alert-critical"><b>Bleeders Found ({len(bleeders)})</b><br>'
                                f'Ads spending money with CTR below {ctr_threshold}%</div>',
                                unsafe_allow_html=True)
                    st.dataframe(bleeders[["ad_name", "campaign_name", "spend", "impressions", "clicks"]].head(20),
                                 use_container_width=True, hide_index=True)

                # High frequency (creative fatigue)
                if "frequency" in df.columns:
                    fatigued = df[df["frequency"].astype(float) > freq_threshold]
                    if not fatigued.empty:
                        st.markdown(f'<div class="alert-warning"><b>Creative Fatigue ({len(fatigued)})</b><br>'
                                    f'Ads with frequency above {freq_threshold}</div>',
                                    unsafe_allow_html=True)
                        st.dataframe(fatigued[["ad_name", "campaign_name", "frequency", "spend"]].head(20),
                                     use_container_width=True, hide_index=True)

                # High CPC
                df["_cpc"] = df.apply(lambda r: safe_divide(r["spend"], r["clicks"]), axis=1)
                expensive = df[(df["_cpc"] > cpc_threshold) & (df["spend"] >= min_spend)]
                if not expensive.empty:
                    st.markdown(f'<div class="alert-warning"><b>Expensive Clicks ({len(expensive)})</b><br>'
                                f'Ads with CPC above ${cpc_threshold}</div>',
                                unsafe_allow_html=True)
                    st.dataframe(expensive[["ad_name", "campaign_name", "_cpc", "spend", "clicks"]].head(20),
                                 use_container_width=True, hide_index=True)

                # Winners: top performers
                df["_ctr"] = df.apply(lambda r: safe_divide(r["clicks"], r["impressions"]) * 100, axis=1)
                winners = df[(df["spend"] >= min_spend) & (df["_ctr"] > ctr_threshold * 2)].sort_values("_ctr", ascending=False)
                if not winners.empty:
                    st.markdown(f'<div class="alert-success"><b>Top Performers ({len(winners)})</b><br>'
                                f'Ads with CTR above {ctr_threshold * 2}%</div>',
                                unsafe_allow_html=True)
                    st.dataframe(winners[["ad_name", "campaign_name", "_ctr", "spend", "clicks"]].head(10),
                                 use_container_width=True, hide_index=True)

                if bleeders.empty and expensive.empty:
                    st.markdown('<div class="alert-success"><b>All Clear!</b><br>'
                                'No performance alerts detected.</div>',
                                unsafe_allow_html=True)
            else:
                st.info("No data available for alert analysis.")
        except Exception as e:
            st.error(f"Alert scan failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: HEALTH SCORE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_health:
    st.markdown('<div class="section-title">Account Health Score</div>', unsafe_allow_html=True)

    st.markdown("""
    A composite health score (0-100) based on:
    - Budget utilization (are you spending efficiently?)
    - CTR performance (are ads engaging?)
    - Frequency management (is audience fatigued?)
    - Campaign diversity (enough campaigns running?)
    - Conversion efficiency (cost per result acceptable?)
    """)

    if st.button("Calculate Health Score", type="primary", use_container_width=True, key="hs_calc"):
        try:
            campaigns = api.get_campaigns(status_filter=["ACTIVE"])
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )
            df = ext.fetch_insights(level="campaign", breakdown_key="none", preset="last_7d")

            scores = {}

            # Campaign diversity (max 20 pts)
            n_active = len(campaigns) if campaigns else 0
            scores["Campaign Diversity"] = min(n_active * 4, 20)

            if not df.empty:
                total_spend = safe_float(df["spend"].sum())
                total_imps = safe_int(df["impressions"].sum())
                total_clicks = safe_int(df["clicks"].sum())
                total_reach = safe_int(df.get("reach", pd.Series([0])).sum())

                # CTR health (max 25 pts)
                avg_ctr = safe_divide(total_clicks, total_imps) * 100
                if avg_ctr >= 2.0:
                    scores["CTR Performance"] = 25
                elif avg_ctr >= 1.0:
                    scores["CTR Performance"] = 15
                elif avg_ctr >= 0.5:
                    scores["CTR Performance"] = 8
                else:
                    scores["CTR Performance"] = 0

                # Frequency health (max 20 pts)
                avg_freq = safe_divide(total_imps, total_reach) if total_reach else 0
                if avg_freq <= 2.0:
                    scores["Frequency Management"] = 20
                elif avg_freq <= 3.5:
                    scores["Frequency Management"] = 12
                elif avg_freq <= 5.0:
                    scores["Frequency Management"] = 5
                else:
                    scores["Frequency Management"] = 0

                # CPC efficiency (max 20 pts)
                avg_cpc = safe_divide(total_spend, total_clicks)
                if avg_cpc <= 1.0:
                    scores["CPC Efficiency"] = 20
                elif avg_cpc <= 2.0:
                    scores["CPC Efficiency"] = 15
                elif avg_cpc <= 5.0:
                    scores["CPC Efficiency"] = 8
                else:
                    scores["CPC Efficiency"] = 0

                # Budget utilization (max 15 pts)
                if campaigns:
                    total_budget = sum(safe_float(c.get("daily_budget", 0)) / 100 for c in campaigns) * 7
                    util = safe_divide(total_spend, total_budget) * 100 if total_budget else 0
                    if 70 <= util <= 100:
                        scores["Budget Utilization"] = 15
                    elif 50 <= util < 70:
                        scores["Budget Utilization"] = 10
                    else:
                        scores["Budget Utilization"] = 5
                else:
                    scores["Budget Utilization"] = 0
            else:
                scores["CTR Performance"] = 0
                scores["Frequency Management"] = 0
                scores["CPC Efficiency"] = 0
                scores["Budget Utilization"] = 0

            total_score = sum(scores.values())

            # Display
            if total_score >= 70:
                css_class = "health-good"
                label = "Healthy"
            elif total_score >= 40:
                css_class = "health-warning"
                label = "Needs Attention"
            else:
                css_class = "health-critical"
                label = "Critical"

            st.markdown(f'<div class="health-score {css_class}">{total_score}/100 — {label}</div>',
                        unsafe_allow_html=True)

            st.markdown("### Score Breakdown")
            score_df = pd.DataFrame([
                {"Category": k, "Score": v, "Max": {"Campaign Diversity": 20, "CTR Performance": 25,
                 "Frequency Management": 20, "CPC Efficiency": 20, "Budget Utilization": 15}[k]}
                for k, v in scores.items()
            ])
            st.dataframe(score_df, use_container_width=True, hide_index=True)
            st.bar_chart(score_df.set_index("Category")["Score"])

        except Exception as e:
            st.error(f"Health score calculation failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_anomaly:
    st.markdown('<div class="section-title">Anomaly Detection</div>', unsafe_allow_html=True)

    st.markdown("""
    Detect unusual changes in key metrics compared to recent averages.
    Anomalies are flagged when a metric deviates more than 2 standard deviations from the mean.
    """)

    anomaly_metric = st.selectbox(
        "Metric to analyze", ["spend", "impressions", "clicks", "ctr", "cpc", "reach"],
        key="an_metric",
    )
    anomaly_period = st.selectbox("Lookback Period", ["last_14d", "last_30d", "last_60d"], index=1, key="an_period")
    anomaly_threshold = st.slider("Sensitivity (std deviations)", 1.0, 4.0, 2.0, 0.5, key="an_threshold")

    if st.button("Detect Anomalies", type="primary", key="an_detect"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )
            df = ext.fetch_insights(level="account", breakdown_key="none", preset=anomaly_period)

            if not df.empty and anomaly_metric in df.columns and "date_start" in df.columns:
                df[anomaly_metric] = df[anomaly_metric].astype(float)
                df = df.sort_values("date_start")

                mean_val = df[anomaly_metric].mean()
                std_val = df[anomaly_metric].std()

                if std_val > 0:
                    df["z_score"] = (df[anomaly_metric] - mean_val) / std_val
                    df["is_anomaly"] = df["z_score"].abs() > anomaly_threshold

                    anomalies = df[df["is_anomaly"]]

                    st.markdown(f"**Mean:** {mean_val:,.2f} | **Std Dev:** {std_val:,.2f}")

                    if not anomalies.empty:
                        st.markdown(f'<div class="alert-warning"><b>{len(anomalies)} Anomalies Detected</b></div>',
                                    unsafe_allow_html=True)
                        st.dataframe(
                            anomalies[["date_start", anomaly_metric, "z_score"]],
                            use_container_width=True, hide_index=True,
                        )
                    else:
                        st.markdown('<div class="alert-success"><b>No anomalies detected</b></div>',
                                    unsafe_allow_html=True)

                    # Chart with anomaly highlights
                    st.line_chart(df.set_index("date_start")[anomaly_metric])
                else:
                    st.info("Not enough variance in data for anomaly detection.")
            else:
                st.info("No data available for anomaly detection.")
        except Exception as e:
            st.error(f"Anomaly detection failed: {e}")
