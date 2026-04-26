"""
Deep Analysis Panel — Full AXIOM 50-metric engine + 7-layer framework.
Select any entity (campaign/adset/ad), compute all metrics, get benchmarks & scores.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, render_quick_add_metric, downloadable_dataframe

st.set_page_config(page_title="Deep Analysis", page_icon="🔬", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#0078D4;">AXIOM Deep Analysis Engine</h1>'
    '<p style="color:#666;">50-Metric Computation + 7-Layer Strategic Framework — All Levels</p>',
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
# COLUMN DETECTION HELPER
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


def safe_val(col_name, agg="sum"):
    if col_name and col_name in analysis_df.columns:
        try:
            s = pd.to_numeric(analysis_df[col_name], errors="coerce")
            return float(s.sum()) if agg == "sum" else float(s.mean())
        except Exception:
            return 0.0
    return 0.0


def safe_div(a, b, mult=1):
    try:
        if b == 0:
            return 0.0
        return (a / b) * mult
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# Detect columns
impressions_col = find_col("impressions")
reach_col = find_col("reach")
frequency_col = find_col("frequency")
spend_col = find_col("spend", "amount_spent")
clicks_col = find_col("clicks", "link_clicks")
outbound_clicks_col = find_col("outbound_clicks")
all_clicks_col = find_col("clicks", "all_clicks", "total_clicks")
lpv_col = find_col("landing_page_views")
video_3s_col = find_col("video_plays_3s", "3_second_video_plays", "video_watched_3s", "video_play_actions")
thruplay_col = find_col("thruplays", "thruplay")
engagements_col = find_col("post_engagements", "engagements", "total_engagements")
shares_col = find_col("post_shares", "shares")
saves_col = find_col("post_saves", "saves")
atc_col = find_col("adds_to_cart", "add_to_cart", "website_adds_to_cart")
unique_atc_col = find_col("unique_adds_to_cart")
checkout_col = find_col("initiated_checkouts", "checkouts_initiated", "initiate_checkout")
purchases_col = find_col("purchases", "results")
purchase_value_col = find_col("purchase_conversion_value", "conversion_value", "purchase_value")
leads_col = find_col("leads")
cpc_col = find_col("cpc", "cost_per_link_click")
cpm_col = find_col("cpm")
ctr_col = find_col("ctr")
msg_connections_col = find_col("new_messaging_connections", "messaging_connections", "messaging_conversations_started")
campaign_col = find_col("campaign_name", "campaign_id")
adset_col = find_col("adset_name", "adset_id", "ad_set_name")
ad_col = find_col("ad_name", "ad_id")

# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY SELECTOR
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title">Select Entity to Analyze</div>', unsafe_allow_html=True)

level_options = ["All Data (Aggregated)"]
if campaign_col:
    level_options.append("Campaign")
if adset_col:
    level_options.append("Ad Set")
if ad_col:
    level_options.append("Ad")

sel_cols = st.columns([1, 2])
with sel_cols[0]:
    level = st.selectbox("Level", level_options, key="deep_level")

level_col_map = {"Campaign": campaign_col, "Ad Set": adset_col, "Ad": ad_col}
analysis_df = df.copy()
selected_entity_name = "All Data"

if level != "All Data (Aggregated)" and level in level_col_map and level_col_map[level]:
    gcol = level_col_map[level]
    entities = sorted(analysis_df[gcol].dropna().unique().astype(str).tolist())
    with sel_cols[1]:
        chosen = st.multiselect(f"Select {level}(s)", entities, default=entities[:1] if entities else [])
    if chosen:
        analysis_df = analysis_df[analysis_df[gcol].astype(str).isin(chosen)]
        selected_entity_name = ", ".join(chosen[:3]) + ("..." if len(chosen) > 3 else "")

if analysis_df.empty:
    st.warning("No data after filtering.")
    st.stop()

st.markdown(f"**Entity:** {selected_entity_name} | **Rows:** {len(analysis_df):,} | **Columns:** {len(analysis_df.columns)}")

# User inputs for advanced metrics
with st.expander("User Inputs (COGS, Breakeven ROAS, AOV, LTV Rate)", expanded=False):
    ui_cols = st.columns(4)
    with ui_cols[0]:
        user_cogs = st.number_input("COGS per unit ($)", value=0.0, min_value=0.0, key="deep_cogs")
    with ui_cols[1]:
        user_breakeven_roas = st.number_input("Breakeven ROAS", value=0.0, min_value=0.0, key="deep_be_roas")
    with ui_cols[2]:
        user_aov = st.number_input("Blended AOV ($)", value=0.0, min_value=0.0, key="deep_aov")
    with ui_cols[3]:
        user_ltv_rate = st.number_input("Monthly Repurchase Rate", value=0.0, min_value=0.0, max_value=1.0, key="deep_ltv_rate")

# ═══════════════════════════════════════════════════════════════════════════════
# COMPUTE ALL 50 AXIOM METRICS
# ═══════════════════════════════════════════════════════════════════════════════

# Raw values
imp = safe_val(impressions_col)
rch = safe_val(reach_col)
spd = safe_val(spend_col)
clk = safe_val(clicks_col)
obc = safe_val(outbound_clicks_col)
all_clk = safe_val(all_clicks_col)
lpv = safe_val(lpv_col)
v3s = safe_val(video_3s_col)
tp = safe_val(thruplay_col)
eng = safe_val(engagements_col)
shr = safe_val(shares_col)
sav = safe_val(saves_col)
atc = safe_val(atc_col)
uatc = safe_val(unique_atc_col)
chk = safe_val(checkout_col)
pur = safe_val(purchases_col)
pval = safe_val(purchase_value_col)
lds = safe_val(leads_col)
msg = safe_val(msg_connections_col)
cpc_v = safe_val(cpc_col, "mean")
freq = safe_div(imp, rch) if rch > 0 else safe_val(frequency_col, "mean")

# WEB ENGINE: 25 Metrics
metrics = {}


def add_metric(num, name, value, unit, benchmark, status_fn, tier, requires_missing=None):
    if requires_missing:
        metrics[num] = {
            "num": num, "name": name, "value": None, "display": "N/A",
            "unit": unit, "benchmark": benchmark, "status": "Uncomputable",
            "color": "#888", "tier": tier, "missing": requires_missing,
        }
        return
    s, c = status_fn(value)
    if unit == "%":
        display = f"{value:.2f}%"
    elif unit == "$":
        display = f"${value:,.2f}"
    elif unit == "x" or unit == "ratio":
        display = f"{value:.2f}"
    else:
        display = f"{value:,.2f}"
    metrics[num] = {
        "num": num, "name": name, "value": value, "display": display,
        "unit": unit, "benchmark": benchmark, "status": s, "color": c, "tier": tier,
    }


def healthy_above(good, mid):
    def fn(v):
        if v >= good:
            return "Healthy", "#107C10"
        elif v >= mid:
            return "Warning", "#FF8C00"
        return "Critical", "#D13438"
    return fn


def healthy_below(good, mid):
    def fn(v):
        if v <= good:
            return "Healthy", "#107C10"
        elif v <= mid:
            return "Warning", "#FF8C00"
        return "Critical", "#D13438"
    return fn


def info_only(v):
    return "Info", "#0078D4"


# TIER 1: CREATIVE & ATTENTION
hook_rate = safe_div(v3s, imp, 100)
hold_rate = safe_div(tp, v3s, 100)
fatigue_idx = freq * (1 - safe_div(obc, imp)) if imp > 0 else 0
eng_to_imp = safe_div(eng, imp, 100)
earned_eng = safe_div(shr + sav, imp, 100)
ghost_rate = safe_div(imp - rch, imp, 100) if rch > 0 else 0

if v3s > 0:
    add_metric(1, "Hook Rate", hook_rate, "%", ">30% Strong | 15-30% Avg | <15% Weak", healthy_above(30, 15), "Creative & Attention")
else:
    add_metric(1, "Hook Rate", 0, "%", ">30% Strong", healthy_above(30, 15), "Creative & Attention", "3-Second Video Plays")

if tp > 0 and v3s > 0:
    add_metric(2, "Absolute Hold Rate", hold_rate, "%", ">40% Strong | 20-40% Avg | <20% Weak", healthy_above(40, 20), "Creative & Attention")
else:
    add_metric(2, "Absolute Hold Rate", 0, "%", ">40% Strong", healthy_above(40, 20), "Creative & Attention", "ThruPlays")

add_metric(3, "Creative Fatigue Index", fatigue_idx, "", "<1.5 Safe | 1.5-2.5 Monitor | >2.5 Danger", healthy_below(1.5, 2.5), "Creative & Attention")
add_metric(4, "Engagement-to-Impression Ratio", eng_to_imp, "%", ">3% Strong | 1-3% Normal | <1% Low", healthy_above(3, 1), "Creative & Attention")
add_metric(5, "Earned Engagement Ratio", earned_eng, "%", ">0.5% Exceptional | 0.1-0.5% Good", healthy_above(0.5, 0.1), "Creative & Attention")
add_metric(6, "Ghost Impression Rate", ghost_rate, "%", "<40% Controlled | 40-60% Warning | >60% Critical", healthy_below(40, 60), "Creative & Attention")

# TIER 2: TRAFFIC QUALITY
dropoff = safe_div(clk - lpv, clk, 100) if clk > 0 and lpv > 0 else 0
bounce_tax = (clk - lpv) * cpc_v if clk > 0 and lpv > 0 and cpc_v > 0 else 0
pure_intent_ctr = safe_div(obc, imp, 100)
click_to_content = safe_div(obc, all_clk, 100) if all_clk > 0 else 0
scroll_commit = safe_div(atc, lpv if lpv > 0 else clk, 100)
intent_click = safe_div(atc, obc, 100) if obc > 0 else 0
micro_conv_cost = safe_div(spd, lpv if lpv > 0 else clk)

if lpv > 0:
    add_metric(7, "Click-to-View Drop-off Rate", dropoff, "%", "<15% Healthy | 15-30% Friction | >30% Critical", healthy_below(15, 30), "Traffic Quality")
else:
    add_metric(7, "Click-to-View Drop-off Rate", 0, "%", "<15% Healthy", healthy_below(15, 30), "Traffic Quality", "Landing Page Views")

add_metric(8, "Bounce Tax (Wasted Spend)", bounce_tax, "$", "Any value is a red flag", info_only, "Traffic Quality")
add_metric(9, "Pure Intent CTR", pure_intent_ctr, "%", ">1.5% Buying Intent | 0.5-1.5% Curious | <0.5% Window Shoppers", healthy_above(1.5, 0.5), "Traffic Quality")
add_metric(10, "Click-to-Content Ratio", click_to_content, "%", ">40% Quality | <20% Low Intent", healthy_above(40, 20), "Traffic Quality")
add_metric(11, "Scroll-to-Commit Ratio", scroll_commit, "%", ">5% Strong | 2-5% Avg | <2% LP Problem", healthy_above(5, 2), "Traffic Quality")
add_metric(12, "Intent Click Rate", intent_click, "%", ">8% High | 3-8% Normal | <3% Low Intent", healthy_above(8, 3), "Traffic Quality")
add_metric(13, "Micro-Conversion Cost", micro_conv_cost, "$", "Should be <10% of CPA target", info_only, "Traffic Quality")

# TIER 3: FINANCIAL EFFICIENCY
roas_val = safe_div(pval, spd)
if user_cogs > 0 and pur > 0:
    true_poas = safe_div(pval - (pur * user_cogs), spd)
    add_metric(14, "True POAS", true_poas, "ratio", ">1.0 Profitable | 0.5-1.0 Marginal | <0.5 Loss", healthy_above(1.0, 0.5), "Financial Efficiency")
else:
    add_metric(14, "True POAS", 0, "ratio", ">1.0 Profitable", healthy_above(1.0, 0.5), "Financial Efficiency", "COGS per unit")

if user_breakeven_roas > 0:
    be_delta = roas_val - user_breakeven_roas
    add_metric(15, "Breakeven ROAS Delta", be_delta, "ratio", "Positive = Profitable | Negative = Losing Money", lambda v: ("Healthy", "#107C10") if v > 0 else ("Critical", "#D13438"), "Financial Efficiency")
else:
    add_metric(15, "Breakeven ROAS Delta", 0, "ratio", "Needs Breakeven ROAS", info_only, "Financial Efficiency", "Breakeven ROAS input")

nc_roas = safe_div(pval * 0.70, spd)
add_metric(16, "New Customer ROAS Proxy", nc_roas, "ratio", "Compare to total ROAS", info_only, "Financial Efficiency")

if uatc > 0:
    cpu_atc = safe_div(spd, uatc)
    add_metric(17, "Cost Per Unique Add-to-Cart", cpu_atc, "$", "Should be <15% of AOV", info_only, "Financial Efficiency")
else:
    add_metric(17, "Cost Per Unique Add-to-Cart", 0, "$", "Needs Unique ATC data", info_only, "Financial Efficiency", "Unique Adds to Cart")

add_metric(18, "Frequency-to-ROAS Delta", 0, "ratio", "Requires 2 time periods", info_only, "Financial Efficiency", "Comparative data")

# TIER 4: ALGORITHMIC HEALTH
aud_exhaust = freq * safe_div(spd, rch) if rch > 0 else 0
net_new_reach = safe_div(rch, imp, 100) if imp > 0 else 0
first_imp_density = safe_div(1, freq) if freq > 0 else 0

add_metric(19, "Audience Exhaustion Index", aud_exhaust, "$", "Track trend — rising + flat ROAS = exhaustion", info_only, "Algorithm Health")
add_metric(20, "Net New Reach %", net_new_reach, "%", ">35% Healthy | <25% Saturation | <15% Critical", healthy_above(35, 15), "Algorithm Health")
add_metric(21, "CPM Inflation Delta", 0, "%", "Requires 2 periods", info_only, "Algorithm Health", "Comparative data")
add_metric(22, "First Impression Density", first_imp_density, "ratio", ">0.5 Fresh | 0.25-0.5 Mid | <0.25 Recycled", healthy_above(0.5, 0.25), "Algorithm Health")
add_metric(23, "Retargeting Saturation Flag", 0, "%", "Requires ad set level spend breakdown", info_only, "Algorithm Health", "Ad set level data")

# TIER 5: STRATEGIC
add_metric(24, "Purchase Intent Velocity", 0, "%", "Requires 3-day vs 7-day ATC data", info_only, "Strategic & Unit Economics", "Two date ranges")

if user_aov > 0 and user_ltv_rate > 0 and pur > 0:
    cpa = safe_div(spd, pur)
    ltv = user_aov * user_ltv_rate * 12
    ltv_cac = safe_div(ltv, cpa) if cpa > 0 else 0
    add_metric(25, "LTV to CAC Proxy", ltv_cac, "ratio", ">3:1 Healthy | 1-3:1 Marginal | <1:1 Unsustainable", healthy_above(3, 1), "Strategic & Unit Economics")
else:
    add_metric(25, "LTV to CAC Proxy", 0, "ratio", "Needs AOV + Repurchase Rate", info_only, "Strategic & Unit Economics", "AOV + Repurchase Rate")

# CHAT ENGINE: Metrics 26-50
is_chat = msg > 0

if is_chat:
    ghost_drop = safe_div(clk - msg, clk, 100) if clk > 0 else 0
    wasted_chat = (clk - msg) * cpc_v if clk > 0 and cpc_v > 0 else 0
    chat_intent_ctr = safe_div(msg, imp, 100)
    cpth = safe_div(spd, msg)
    pre_chat_friction = cpth - cpc_v if cpc_v > 0 else 0
    window_shopper = safe_div(msg - lds, msg, 100) if lds > 0 else 0
    qual_lead_cvr = safe_div(lds, msg, 100)
    cpqc = safe_div(spd, lds) if lds > 0 else 0
    qual_dropoff_cost = (msg - lds) * safe_div(spd, msg) if lds > 0 and msg > 0 else 0
    sales_close = safe_div(pur, lds, 100) if lds > 0 else 0
    overall_chat_close = safe_div(pur, msg, 100)
    rpc = safe_div(pval, msg)
    simp_idx = safe_div(cpth, safe_div(spd, pur)) if pur > 0 else 0
    msg_freq_exhaust = freq * safe_div(spd, msg) if msg > 0 else 0

    add_metric(26, "Ghost Drop-off Rate", ghost_drop, "%", "<25% Healthy | 25-40% Friction | >40% Critical", healthy_below(25, 40), "Chat — Ghost Detection")
    add_metric(27, "Wasted Chat Spend", wasted_chat, "$", "Pure waste — clicks that never connected", info_only, "Chat — Ghost Detection")
    add_metric(28, "True Chat Intent CTR", chat_intent_ctr, "%", ">0.5% Quality | 0.2-0.5% Avg | <0.2% Wrong Audience", healthy_above(0.5, 0.2), "Chat — Ghost Detection")
    add_metric(29, "Cost Per True Hello (CPTH)", cpth, "$", "Should be <15% of product price", info_only, "Chat — Ghost Detection")
    add_metric(30, "Pre-Chat Friction Index", pre_chat_friction, "$", "<0.5 Low | 0.5-2 Medium | >2 High Friction", healthy_below(0.5, 2), "Chat — Ghost Detection")

    if lds > 0:
        add_metric(31, "Window Shopper Ratio", window_shopper, "%", "<40% Good | 40-60% Avg | >60% Price-shop Audience", healthy_below(40, 60), "Chat — Lead Quality")
        add_metric(32, "Qualified Lead Conversion Rate", qual_lead_cvr, "%", ">30% Strong | 15-30% Avg | <15% Failure", healthy_above(30, 15), "Chat — Lead Quality")
        add_metric(33, "Cost Per Qualified Chat (CPQC)", cpqc, "$", "True CPL — not Meta's reported CPL", info_only, "Chat — Lead Quality")
        add_metric(34, "Qualification Drop-off Cost", qual_dropoff_cost, "$", "Wasted spend on unqualified conversations", info_only, "Chat — Lead Quality")
    else:
        for n, nm in [(31, "Window Shopper Ratio"), (32, "Qualified Lead CVR"), (33, "CPQC"), (34, "Qual Drop-off Cost")]:
            add_metric(n, nm, 0, "%", "Needs Lead data", info_only, "Chat — Lead Quality", "Leads")

    add_metric(35, "Lead-to-Intent Velocity", safe_div(atc, lds, 100) if lds > 0 else 0, "%", ">20% Effective | <10% Dead End", healthy_above(20, 10), "Chat — Lead Quality")

    if pur > 0 and lds > 0:
        add_metric(36, "Sales Team Close Rate", sales_close, "%", ">20% High | 10-20% Avg | <10% Problem", healthy_above(20, 10), "Chat — Sales ROI")
    else:
        add_metric(36, "Sales Team Close Rate", 0, "%", "Needs Purchases + Leads", info_only, "Chat — Sales ROI", "Purchases + Leads")

    add_metric(37, "Overall Chat Close Rate", overall_chat_close, "%", "2-5% Healthy | <1% Broken", healthy_above(2, 1), "Chat — Sales ROI")
    add_metric(38, "Revenue Per Chat Conversation", rpc, "$", "RPC defines max acceptable CPTH", info_only, "Chat — Sales ROI")

    if user_cogs > 0 and pur > 0:
        chat_poas = safe_div(pval - (pur * user_cogs), spd)
        add_metric(39, "True Chat POAS", chat_poas, "ratio", ">1.0 Profitable | <0.5 Loss", healthy_above(1.0, 0.5), "Chat — Sales ROI")
    else:
        add_metric(39, "True Chat POAS", 0, "ratio", "Needs COGS", info_only, "Chat — Sales ROI", "COGS")

    if lds > 0 and pur > 0:
        lost_deal = (lds - pur) * safe_div(spd, lds) if lds > pur else 0
        add_metric(40, "Cost of Indecision", lost_deal, "$", "Recoverable sales — follow-up can recover 15-25%", info_only, "Chat — Sales ROI")
    else:
        add_metric(40, "Cost of Indecision", 0, "$", "Needs Leads + Purchases", info_only, "Chat — Sales ROI", "Leads + Purchases")

    add_metric(41, "Simp Algorithm Index", simp_idx, "ratio", "<0.05 Cheap-click bias | 0.05-0.15 Normal | >0.15 Good", healthy_above(0.15, 0.05), "Chat — Algorithm Saturation")
    add_metric(42, "Message Frequency Exhaustion", msg_freq_exhaust, "$", "Rising + declining conversations = saturated", info_only, "Chat — Algorithm Saturation")

    garbage = 0
    if msg > obc and obc > 0:
        garbage = safe_div(msg - obc, msg, 100)
    add_metric(43, "Garbage Data Ratio", garbage, "%", "Should be 0 — if >0 flag Meta support", healthy_below(0.1, 5), "Chat — Algorithm Saturation")

    if user_aov > 0 and pur > 0:
        chat_aov_defl = safe_div(safe_div(pval, pur), user_aov)
        add_metric(44, "Chat AOV Deflection Index", chat_aov_defl, "ratio", ">1.0 Chat spends MORE | <0.8 Bargain hunters", healthy_above(1.0, 0.8), "Chat — Algorithm Saturation")
    else:
        add_metric(44, "Chat AOV Deflection Index", 0, "ratio", "Needs AOV + Purchases", info_only, "Chat — Algorithm Saturation", "Blended AOV")

    add_metric(45, "High-Ticket Chat Resistance", 0, "$", "Needs product-level purchase tracking", info_only, "Chat — Algorithm Saturation", "Product-level data")

    # TIER 5: OPERATIONAL
    for n, nm, miss in [
        (46, "First Response Death Rate", "CRM integration"),
        (47, "Follow-up Rescue Rate", "Retargeting data"),
    ]:
        add_metric(n, nm, 0, "%", f"Requires {miss}", info_only, "Chat — Operations", miss)

    if user_aov > 0 and user_ltv_rate > 0 and pur > 0:
        chat_cpa = safe_div(spd, pur)
        chat_ltv = user_aov * user_ltv_rate * 12
        chat_ltv_proxy = safe_div(chat_ltv, chat_cpa) if chat_cpa > 0 else 0
        add_metric(48, "Chat Customer LTV Proxy", chat_ltv_proxy, "ratio", ">3:1 Healthy | <1:1 Unsustainable", healthy_above(3, 1), "Chat — Operations")
    else:
        add_metric(48, "Chat Customer LTV Proxy", 0, "ratio", "Needs AOV + Repurchase Rate", info_only, "Chat — Operations", "AOV + Repurchase Rate")

    add_metric(49, "Chat-to-Call Escalation Rate", 0, "%", "Needs phone call data", info_only, "Chat — Operations", "Phone call data")
    add_metric(50, "Total Chat System ROI", 0, "ratio", "Needs COGS + Chatbot cost + Agent salary", info_only, "Chat — Operations", "Full cost data")
else:
    # No chat data — mark 26-50 as not applicable
    for n in range(26, 51):
        metrics[n] = {
            "num": n, "name": f"Chat Metric #{n}", "value": None, "display": "N/A",
            "unit": "", "benchmark": "Chat campaign data required", "status": "N/A",
            "color": "#888", "tier": "Chat Engine", "missing": "Messaging Connections data",
        }

# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY — COMPUTED METRICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

computed = sum(1 for m in metrics.values() if m.get("value") is not None)
total = len(metrics)
confidence = "HIGH" if computed >= 35 else "MEDIUM" if computed >= 20 else "LOW"

st.markdown(
    f'<div style="background:#001428; border-radius:8px; padding:1rem; margin:1rem 0; color:white; text-align:center;">'
    f'<h3 style="color:#00B7C3; margin:0;">AXIOM Computed Metrics Dashboard</h3>'
    f'<p style="margin:0.5rem 0 0;">Entity: <b>{selected_entity_name}</b> | '
    f'Computed: <b>{computed}/{total}</b> | '
    f'Confidence: <b style="color:{"#107C10" if confidence == "HIGH" else "#FF8C00" if confidence == "MEDIUM" else "#D13438"}">{confidence}</b></p>'
    f'</div>',
    unsafe_allow_html=True,
)

# Group by tier
tiers = {}
for m in metrics.values():
    tier = m["tier"]
    if tier not in tiers:
        tiers[tier] = []
    tiers[tier].append(m)

deep_tabs = st.tabs(list(tiers.keys()) + ["Missing Data Registry", "Raw Variable Registry"])

for idx, (tier_name, tier_metrics) in enumerate(tiers.items()):
    with deep_tabs[idx]:
        st.markdown(f'<div class="section-title">{tier_name}</div>', unsafe_allow_html=True)

        cols_per_row = 3
        for i in range(0, len(tier_metrics), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(tier_metrics):
                    m = tier_metrics[i + j]
                    with col:
                        border_color = m.get("color", "#888")
                        st.markdown(
                            f'<div class="metric-card" style="border-left: 4px solid {border_color};">'
                            f'<h4 style="font-size:0.8rem;">#{m["num"]} {m["name"]}</h4>'
                            f'<div class="metric-value" style="font-size:1.3rem;">{m["display"]}</div>'
                            f'<div class="metric-trend" style="font-size:0.65rem;">'
                            f'<span style="color:{border_color}; font-weight:700;">{m["status"]}</span> — {m["benchmark"]}'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

# Missing Data Registry tab
with deep_tabs[-2]:
    st.markdown('<div class="section-title">Missing Data Registry</div>', unsafe_allow_html=True)
    missing_list = [m for m in metrics.values() if m.get("missing")]
    if missing_list:
        miss_rows = []
        for m in missing_list:
            miss_rows.append({
                "Metric #": m["num"],
                "Metric Name": m["name"],
                "Missing Input": m.get("missing", ""),
                "Impact": "HIGH" if m["num"] <= 25 else "MEDIUM",
            })
        miss_df = pd.DataFrame(miss_rows).sort_values("Impact")
        downloadable_dataframe(miss_df, key="deep_missing", label="missing_data_registry", use_container_width=True, hide_index=True)

        # Most critical missing input
        if miss_rows:
            from collections import Counter
            missing_counts = Counter(r["Missing Input"] for r in miss_rows)
            top_missing = missing_counts.most_common(1)[0]
            st.warning(
                f"**Most critical missing input:** {top_missing[0]} — "
                f"affects {top_missing[1]} metric(s). Providing this unlocks the most analytical value."
            )
    else:
        st.success("All metrics computed — no missing data.")

# Raw Variable Registry tab
with deep_tabs[-1]:
    st.markdown('<div class="section-title">Raw Variable Registry</div>', unsafe_allow_html=True)
    raw_vars = [
        ("Impressions", imp), ("Reach", rch), ("Frequency", freq),
        ("Amount Spent", spd), ("Link Clicks", clk), ("Outbound Clicks", obc),
        ("All Clicks", all_clk), ("Landing Page Views", lpv),
        ("3-Second Video Plays", v3s), ("ThruPlays", tp),
        ("Total Engagements", eng), ("Post Shares", shr), ("Post Saves", sav),
        ("Adds to Cart", atc), ("Unique Adds to Cart", uatc),
        ("Initiated Checkouts", chk), ("Purchases", pur),
        ("Purchase Conversion Value", pval), ("Leads", lds),
        ("CPC (Link)", cpc_v), ("New Messaging Connections", msg),
        ("User COGS", user_cogs), ("User Breakeven ROAS", user_breakeven_roas),
        ("User AOV", user_aov), ("User LTV Rate", user_ltv_rate),
    ]
    reg_data = []
    for name, val in raw_vars:
        status = "CONFIRMED" if val > 0 else "N/A"
        reg_data.append({"Variable": name, "Value": f"{val:,.2f}" if val > 0 else "N/A", "Status": status})
    downloadable_dataframe(pd.DataFrame(reg_data), key="deep_raw_vars", label="raw_variable_registry", use_container_width=True, hide_index=True)

st.markdown("---")
render_quick_add_metric("deep_analysis")
