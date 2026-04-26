"""
Video Content Deep Analysis — Select level + breakdowns, get all standard + custom metrics.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, render_quick_add_metric, downloadable_dataframe

st.set_page_config(page_title="Video Analysis", page_icon="🎬", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#0078D4;">Video Content Deep Analysis</h1>'
    '<p style="color:#666;">Hook Rate, Hold Rate, Completion, Fatigue — All Levels & Breakdowns</p>',
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

# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

col_lower = {c: c.lower().replace(" ", "_") for c in df.columns}
col_reverse = {v: k for k, v in col_lower.items()}


def find_col(*candidates):
    for c in candidates:
        if c in col_reverse:
            return col_reverse[c]
        for orig, norm in col_lower.items():
            if c in norm:
                return orig
    return None


# Video columns
impressions_col = find_col("impressions")
video_3s_col = find_col("video_plays_3s", "3_second_video_plays", "video_watched_3s", "video_play_actions_video_view")
thruplay_col = find_col("thruplays", "thruplay", "video_thruplay_watched_actions")
video_p25_col = find_col("video_p25", "video_25", "video_watched_25")
video_p50_col = find_col("video_p50", "video_50", "video_watched_50")
video_p75_col = find_col("video_p75", "video_75", "video_watched_75")
video_p95_col = find_col("video_p95", "video_95", "video_watched_95")
video_p100_col = find_col("video_p100", "video_100", "video_watched_100")
reach_col = find_col("reach")
frequency_col = find_col("frequency")
spend_col = find_col("spend", "amount_spent")
clicks_col = find_col("clicks", "link_clicks")
outbound_clicks_col = find_col("outbound_clicks")
ctr_col = find_col("ctr", "outbound_ctr")
engagements_col = find_col("post_engagements", "engagements", "total_engagements")
shares_col = find_col("post_shares", "shares")
saves_col = find_col("post_saves", "saves")
purchase_value_col = find_col("purchase_conversion_value", "conversion_value", "purchase_value")
purchases_col = find_col("purchases", "results")

# Level columns for breakdown
campaign_col = find_col("campaign_name", "campaign_id")
adset_col = find_col("adset_name", "adset_id", "ad_set_name")
ad_col = find_col("ad_name", "ad_id")

# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL & BREAKDOWN SELECTOR
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title">Select Analysis Scope</div>', unsafe_allow_html=True)

level_options = ["All Data"]
if campaign_col:
    level_options.append("Campaign")
if adset_col:
    level_options.append("Ad Set")
if ad_col:
    level_options.append("Ad")

level_sel, breakdown_sel = st.columns(2)

with level_sel:
    level = st.selectbox("Analysis Level", level_options)

# Apply level filtering
level_col_map = {"Campaign": campaign_col, "Ad Set": adset_col, "Ad": ad_col}
analysis_df = df.copy()
group_col = None

if level != "All Data" and level in level_col_map and level_col_map[level]:
    group_col = level_col_map[level]
    with breakdown_sel:
        unique_entities = sorted(analysis_df[group_col].dropna().unique().astype(str).tolist())
        selected_entities = st.multiselect(
            f"Select {level}(s)", unique_entities,
            default=unique_entities[:5] if len(unique_entities) > 5 else unique_entities,
        )
        if selected_entities:
            analysis_df = analysis_df[analysis_df[group_col].astype(str).isin(selected_entities)]

if analysis_df.empty:
    st.warning("No data after filtering.")
    st.stop()

st.markdown(f"**Analyzing:** {len(analysis_df):,} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO METRICS COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

video_tabs = st.tabs([
    "Video Funnel",
    "Performance Metrics",
    "Creative Fatigue",
    "Benchmarks & Scores",
    "Breakdown Comparison",
])


def safe_div(a, b, mult=1):
    try:
        a_val = float(a) if not isinstance(a, (pd.Series, np.ndarray)) else a
        b_val = float(b) if not isinstance(b, (pd.Series, np.ndarray)) else b
        if isinstance(b_val, (int, float)) and b_val == 0:
            return 0.0
        return (a_val / b_val) * mult
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def safe_sum(col_name):
    if col_name and col_name in analysis_df.columns:
        try:
            return float(pd.to_numeric(analysis_df[col_name], errors="coerce").sum())
        except Exception:
            return 0.0
    return 0.0


# Aggregate values
total_impressions = safe_sum(impressions_col)
total_3s = safe_sum(video_3s_col)
total_thruplay = safe_sum(thruplay_col)
total_p25 = safe_sum(video_p25_col)
total_p50 = safe_sum(video_p50_col)
total_p75 = safe_sum(video_p75_col)
total_p95 = safe_sum(video_p95_col)
total_p100 = safe_sum(video_p100_col)
total_reach = safe_sum(reach_col)
total_spend = safe_sum(spend_col)
total_clicks = safe_sum(clicks_col)
total_outbound = safe_sum(outbound_clicks_col)
total_engagements = safe_sum(engagements_col)
total_shares = safe_sum(shares_col)
total_saves = safe_sum(saves_col)
total_purchase_value = safe_sum(purchase_value_col)
total_purchases = safe_sum(purchases_col)

# Computed metrics
hook_rate = safe_div(total_3s, total_impressions, 100)
hold_rate = safe_div(total_thruplay, total_3s, 100)
completion_rate = safe_div(total_thruplay, total_impressions, 100)
cost_per_thruplay = safe_div(total_spend, total_thruplay)
cost_per_3s = safe_div(total_spend, total_3s)
ghost_rate = safe_div(total_impressions - total_reach, total_impressions, 100) if total_reach else 0.0
freq = safe_div(total_impressions, total_reach) if total_reach else 0.0
fatigue_index = freq * (1 - (safe_div(total_outbound, total_impressions, 100) / 100)) if total_outbound else 0.0
earned_engagement = safe_div(total_shares + total_saves, total_impressions, 100) if (total_shares + total_saves) > 0 else 0.0

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: VIDEO FUNNEL
# ═══════════════════════════════════════════════════════════════════════════════

with video_tabs[0]:
    st.markdown('<div class="section-title">Video View Funnel</div>', unsafe_allow_html=True)

    funnel_stages = []
    funnel_values = []
    if total_impressions > 0:
        funnel_stages.append("Impressions")
        funnel_values.append(total_impressions)
    if total_3s > 0:
        funnel_stages.append("3-Second Views")
        funnel_values.append(total_3s)
    if total_p25 > 0:
        funnel_stages.append("25% Watched")
        funnel_values.append(total_p25)
    if total_p50 > 0:
        funnel_stages.append("50% Watched")
        funnel_values.append(total_p50)
    if total_p75 > 0:
        funnel_stages.append("75% Watched")
        funnel_values.append(total_p75)
    if total_thruplay > 0:
        funnel_stages.append("ThruPlays (15s+)")
        funnel_values.append(total_thruplay)
    if total_p95 > 0:
        funnel_stages.append("95% Watched")
        funnel_values.append(total_p95)
    if total_p100 > 0:
        funnel_stages.append("100% Watched")
        funnel_values.append(total_p100)

    if len(funnel_stages) >= 2:
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textinfo="value+percent initial+percent previous",
            marker=dict(color=["#0078D4", "#00B7C3", "#107C10", "#FF8C00", "#E3008C", "#881798", "#D13438", "#002050"][:len(funnel_stages)]),
        ))
        fig_funnel.update_layout(
            title="Video View Drop-off Funnel",
            font_family="Segoe UI",
            height=500,
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Drop-off table
        drop_data = []
        for i in range(1, len(funnel_stages)):
            prev_val = funnel_values[i - 1]
            curr_val = funnel_values[i]
            drop_pct = ((prev_val - curr_val) / prev_val * 100) if prev_val > 0 else 0
            retain_pct = (curr_val / prev_val * 100) if prev_val > 0 else 0
            drop_data.append({
                "Stage": f"{funnel_stages[i - 1]} → {funnel_stages[i]}",
                "From": f"{prev_val:,.0f}",
                "To": f"{curr_val:,.0f}",
                "Retention": f"{retain_pct:.1f}%",
                "Drop-off": f"{drop_pct:.1f}%",
            })
        downloadable_dataframe(pd.DataFrame(drop_data), key="video_dropoff", label="video_dropoff", use_container_width=True, hide_index=True)
    else:
        st.info("Need at least Impressions + 3-Second Video Views to build the funnel. Check if your data includes video columns.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PERFORMANCE METRICS
# ═══════════════════════════════════════════════════════════════════════════════

with video_tabs[1]:
    st.markdown('<div class="section-title">Video Performance Metrics</div>', unsafe_allow_html=True)

    metrics_data = [
        ("Hook Rate (3s Views / Impressions)", hook_rate, "%", ">30% Strong | 15-30% Avg | <15% Weak"),
        ("Hold Rate (ThruPlays / 3s Views)", hold_rate, "%", ">40% Strong | 20-40% Avg | <20% Weak"),
        ("Completion Rate (ThruPlays / Impressions)", completion_rate, "%", "Context-dependent"),
        ("Cost Per ThruPlay", cost_per_thruplay, "$", "Lower is better"),
        ("Cost Per 3s View", cost_per_3s, "$", "Lower is better"),
        ("Ghost Impression Rate", ghost_rate, "%", "<40% Healthy | 40-60% Warning | >60% Critical"),
        ("Creative Fatigue Index", fatigue_index, "", "<1.5 Safe | 1.5-2.5 Monitor | >2.5 Danger"),
        ("Frequency", freq, "x", "<2 Fresh | 2-3.5 Normal | >3.5 Saturation"),
        ("Earned Engagement Ratio", earned_engagement, "%", ">0.5% Exceptional | 0.1-0.5% Good"),
    ]

    cols_per_row = 3
    for i in range(0, len(metrics_data), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(metrics_data):
                name, value, unit, benchmark = metrics_data[i + j]
                with col:
                    display_val = f"{value:,.2f}{unit}" if unit != "$" else f"${value:,.4f}"
                    st.markdown(
                        f'<div class="metric-card">'
                        f'<h4>{name}</h4>'
                        f'<div class="metric-value">{display_val}</div>'
                        f'<div class="metric-trend" style="font-size:0.7rem;">{benchmark}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # Additional video-specific metrics
    st.markdown("#### Detailed Video Metrics Table")
    detail_rows = []
    if total_impressions > 0:
        detail_rows.append({"Metric": "Impressions", "Value": f"{total_impressions:,.0f}"})
    if total_3s > 0:
        detail_rows.append({"Metric": "3-Second Video Views", "Value": f"{total_3s:,.0f}"})
    if total_thruplay > 0:
        detail_rows.append({"Metric": "ThruPlays (15s+)", "Value": f"{total_thruplay:,.0f}"})
    if total_p25 > 0:
        detail_rows.append({"Metric": "25% Video Views", "Value": f"{total_p25:,.0f}"})
    if total_p50 > 0:
        detail_rows.append({"Metric": "50% Video Views", "Value": f"{total_p50:,.0f}"})
    if total_p75 > 0:
        detail_rows.append({"Metric": "75% Video Views", "Value": f"{total_p75:,.0f}"})
    if total_p95 > 0:
        detail_rows.append({"Metric": "95% Video Views", "Value": f"{total_p95:,.0f}"})
    if total_p100 > 0:
        detail_rows.append({"Metric": "100% Video Views", "Value": f"{total_p100:,.0f}"})
    detail_rows.append({"Metric": "Hook Rate", "Value": f"{hook_rate:.2f}%"})
    detail_rows.append({"Metric": "Hold Rate", "Value": f"{hold_rate:.2f}%"})
    detail_rows.append({"Metric": "Completion Rate", "Value": f"{completion_rate:.2f}%"})
    detail_rows.append({"Metric": "Cost Per ThruPlay", "Value": f"${cost_per_thruplay:.4f}"})
    if total_spend > 0:
        detail_rows.append({"Metric": "Total Video Spend", "Value": f"${total_spend:,.2f}"})
    downloadable_dataframe(pd.DataFrame(detail_rows), key="video_performance", label="video_performance", use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: CREATIVE FATIGUE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

with video_tabs[2]:
    st.markdown('<div class="section-title">Creative Fatigue Analysis</div>', unsafe_allow_html=True)

    fatigue_cols = st.columns(3)
    with fatigue_cols[0]:
        status = "Safe" if fatigue_index < 1.5 else "Monitor" if fatigue_index < 2.5 else "DANGER"
        color = "#107C10" if fatigue_index < 1.5 else "#FF8C00" if fatigue_index < 2.5 else "#D13438"
        st.markdown(
            f'<div class="metric-card" style="border-left: 4px solid {color};">'
            f'<h4>Fatigue Index</h4>'
            f'<div class="metric-value" style="color:{color};">{fatigue_index:.2f}</div>'
            f'<div class="metric-trend">{status}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with fatigue_cols[1]:
        st.markdown(
            f'<div class="metric-card">'
            f'<h4>Frequency</h4>'
            f'<div class="metric-value">{freq:.2f}x</div>'
            f'<div class="metric-trend">{"Fresh" if freq < 2 else "Mid-saturation" if freq < 3.5 else "HIGH SATURATION"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with fatigue_cols[2]:
        ghost_status = "Healthy" if ghost_rate < 40 else "Warning" if ghost_rate < 60 else "CRITICAL"
        st.markdown(
            f'<div class="metric-card">'
            f'<h4>Ghost Impressions</h4>'
            f'<div class="metric-value">{ghost_rate:.1f}%</div>'
            f'<div class="metric-trend">{ghost_status} — recycled eyeballs</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Per-entity fatigue if group_col exists
    if group_col and group_col in analysis_df.columns:
        st.markdown("#### Fatigue by Entity")
        numeric_agg = {}
        if impressions_col:
            numeric_agg[impressions_col] = "sum"
        if reach_col:
            numeric_agg[reach_col] = "sum"
        if video_3s_col:
            numeric_agg[video_3s_col] = "sum"
        if thruplay_col:
            numeric_agg[thruplay_col] = "sum"
        if spend_col:
            numeric_agg[spend_col] = "sum"
        if outbound_clicks_col:
            numeric_agg[outbound_clicks_col] = "sum"

        if numeric_agg:
            entity_df = analysis_df.groupby(group_col, as_index=False).agg(numeric_agg)
            rows = []
            for _, row in entity_df.iterrows():
                imp = float(row.get(impressions_col, 0)) if impressions_col else 0
                rch = float(row.get(reach_col, 0)) if reach_col else 0
                obc = float(row.get(outbound_clicks_col, 0)) if outbound_clicks_col else 0
                v3s = float(row.get(video_3s_col, 0)) if video_3s_col else 0
                tp = float(row.get(thruplay_col, 0)) if thruplay_col else 0
                sp = float(row.get(spend_col, 0)) if spend_col else 0
                f_val = imp / rch if rch > 0 else 0
                fi = f_val * (1 - (obc / imp)) if imp > 0 and obc > 0 else 0
                hr = (v3s / imp * 100) if imp > 0 else 0
                hlr = (tp / v3s * 100) if v3s > 0 else 0
                cpt = sp / tp if tp > 0 else 0
                rows.append({
                    level: str(row[group_col]),
                    "Hook Rate %": round(hr, 2),
                    "Hold Rate %": round(hlr, 2),
                    "Frequency": round(f_val, 2),
                    "Fatigue Index": round(fi, 2),
                    "Cost/ThruPlay": round(cpt, 4),
                    "Spend": round(sp, 2),
                })
            fatigue_df = pd.DataFrame(rows).sort_values("Fatigue Index", ascending=False)
            downloadable_dataframe(fatigue_df, key="video_fatigue", label="video_fatigue", use_container_width=True, hide_index=True)

            # Chart
            if len(fatigue_df) > 1:
                fig = px.bar(
                    fatigue_df, x=level, y="Fatigue Index",
                    color="Fatigue Index",
                    color_continuous_scale=["#107C10", "#FF8C00", "#D13438"],
                    template="plotly_white",
                )
                fig.update_layout(font_family="Segoe UI")
                st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: BENCHMARKS & SCORES
# ═══════════════════════════════════════════════════════════════════════════════

with video_tabs[3]:
    st.markdown('<div class="section-title">Benchmark Scorecard</div>', unsafe_allow_html=True)

    def score(val, good, mid, invert=False):
        if invert:
            if val <= good:
                return "Healthy", "#107C10"
            elif val <= mid:
                return "Warning", "#FF8C00"
            else:
                return "Critical", "#D13438"
        else:
            if val >= good:
                return "Healthy", "#107C10"
            elif val >= mid:
                return "Warning", "#FF8C00"
            else:
                return "Critical", "#D13438"

    scorecard = [
        ("Hook Rate", hook_rate, "%", 30, 15, False),
        ("Hold Rate", hold_rate, "%", 40, 20, False),
        ("Ghost Impression Rate", ghost_rate, "%", 40, 60, True),
        ("Creative Fatigue Index", fatigue_index, "", 1.5, 2.5, True),
        ("Frequency", freq, "x", 2.0, 3.5, True),
        ("Earned Engagement", earned_engagement, "%", 0.5, 0.1, False),
    ]

    for name, val, unit, good_t, mid_t, inv in scorecard:
        status, color = score(val, good_t, mid_t, inv)
        st.markdown(
            f'<div style="display:flex; align-items:center; padding:0.5rem; margin:0.3rem 0; '
            f'background: linear-gradient(90deg, {color}22 0%, transparent 100%); '
            f'border-left: 4px solid {color}; border-radius:4px;">'
            f'<span style="flex:1; font-weight:600;">{name}</span>'
            f'<span style="width:120px; text-align:right; font-weight:700;">{val:.2f}{unit}</span>'
            f'<span style="width:100px; text-align:center; color:{color}; font-weight:700;">{status}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: BREAKDOWN COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

with video_tabs[4]:
    st.markdown('<div class="section-title">Breakdown Comparison</div>', unsafe_allow_html=True)

    # Auto-detect breakdown columns
    breakdown_candidates = []
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in ["age", "gender", "country", "region", "device", "placement", "platform", "publisher"]):
            if df[c].nunique() < 50:
                breakdown_candidates.append(c)

    if group_col and group_col not in breakdown_candidates:
        breakdown_candidates.insert(0, group_col)

    if breakdown_candidates:
        bd_col = st.selectbox("Breakdown Dimension", breakdown_candidates)
        numeric_agg = {}
        if impressions_col:
            numeric_agg[impressions_col] = "sum"
        if video_3s_col:
            numeric_agg[video_3s_col] = "sum"
        if thruplay_col:
            numeric_agg[thruplay_col] = "sum"
        if spend_col:
            numeric_agg[spend_col] = "sum"
        if reach_col:
            numeric_agg[reach_col] = "sum"

        if numeric_agg:
            bd_df = analysis_df.groupby(bd_col, as_index=False).agg(numeric_agg)
            rows = []
            for _, row in bd_df.iterrows():
                imp = float(row.get(impressions_col, 0)) if impressions_col else 0
                v3s = float(row.get(video_3s_col, 0)) if video_3s_col else 0
                tp = float(row.get(thruplay_col, 0)) if thruplay_col else 0
                sp = float(row.get(spend_col, 0)) if spend_col else 0
                hr = (v3s / imp * 100) if imp > 0 else 0
                hlr = (tp / v3s * 100) if v3s > 0 else 0
                cpt = sp / tp if tp > 0 else 0
                rows.append({
                    bd_col: str(row[bd_col]),
                    "Impressions": int(imp),
                    "3s Views": int(v3s),
                    "ThruPlays": int(tp),
                    "Hook Rate %": round(hr, 2),
                    "Hold Rate %": round(hlr, 2),
                    "Cost/ThruPlay": round(cpt, 4),
                    "Spend": round(sp, 2),
                })
            result_df = pd.DataFrame(rows).sort_values("Hook Rate %", ascending=False)
            downloadable_dataframe(result_df, key="video_breakdown", label="video_breakdown", use_container_width=True, hide_index=True)

            # Comparative chart
            metric_choice = st.selectbox("Chart Metric", ["Hook Rate %", "Hold Rate %", "Cost/ThruPlay", "Spend"])
            fig = px.bar(
                result_df.head(20), x=bd_col, y=metric_choice,
                color=metric_choice,
                color_continuous_scale=["#0078D4", "#00B7C3"],
                template="plotly_white",
            )
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No breakdown columns detected (age, gender, country, device, placement, etc.).")

st.markdown("---")
render_quick_add_metric("video")
