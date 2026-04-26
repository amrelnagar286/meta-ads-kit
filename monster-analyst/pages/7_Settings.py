"""
Settings -- Configuration for benchmarks, thresholds, and metric library management.
"""
import json
import streamlit as st
import pandas as pd

from src.helpers import WINDOWS_11_CSS, downloadable_dataframe
from src.metric_catalog import CATEGORIES, METRICS, METRICS_BY_CATEGORY

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#605E5C;">Settings</h1>'
    '<p style="color:#666;">Configure Benchmarks, Thresholds, and Metric Library</p>',
    unsafe_allow_html=True,
)

settings_tabs = st.tabs(["Benchmarks", "Metric Library", "Column Aliases", "About"])

# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARKS
# ═══════════════════════════════════════════════════════════════════════════════

with settings_tabs[0]:
    st.markdown('<div class="section-title">Performance Benchmarks</div>', unsafe_allow_html=True)
    st.markdown("Set your target benchmarks for health status indicators.")

    if "benchmarks" not in st.session_state:
        st.session_state.benchmarks = {
            "target_ctr": 2.0,
            "target_roas": 3.0,
            "max_frequency": 3.5,
            "max_cpa": 50.0,
            "bleeder_ctr": 1.0,
            "bleeder_spend": 10.0,
            "hook_rate_healthy": 25.0,
            "hold_rate_healthy": 30.0,
            "fatigue_critical": 2.5,
            "ghost_rate_critical": 40.0,
            "dropoff_critical": 30.0,
            "breakeven_roas": 2.5,
            "cogs_avg": 15.0,
            "new_customer_pct": 70.0,
            "repeat_rate": 2.5,
        }

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Performance Targets**")
        st.session_state.benchmarks["target_ctr"] = st.number_input("Target CTR %", value=st.session_state.benchmarks["target_ctr"], step=0.1, key="bm_ctr")
        st.session_state.benchmarks["target_roas"] = st.number_input("Target ROAS", value=st.session_state.benchmarks["target_roas"], step=0.1, key="bm_roas")
        st.session_state.benchmarks["max_frequency"] = st.number_input("Max Frequency", value=st.session_state.benchmarks["max_frequency"], step=0.1, key="bm_freq")
        st.session_state.benchmarks["max_cpa"] = st.number_input("Max CPA ($)", value=st.session_state.benchmarks["max_cpa"], step=1.0, key="bm_cpa")

    with col2:
        st.markdown("**Alert Thresholds**")
        st.session_state.benchmarks["bleeder_ctr"] = st.number_input("Bleeder CTR < %", value=st.session_state.benchmarks["bleeder_ctr"], step=0.1, key="bm_bl_ctr")
        st.session_state.benchmarks["bleeder_spend"] = st.number_input("Bleeder Min Spend ($)", value=st.session_state.benchmarks["bleeder_spend"], step=1.0, key="bm_bl_spend")
        st.session_state.benchmarks["hook_rate_healthy"] = st.number_input("Hook Rate Healthy > %", value=st.session_state.benchmarks["hook_rate_healthy"], step=1.0, key="bm_hook")
        st.session_state.benchmarks["hold_rate_healthy"] = st.number_input("Hold Rate Healthy > %", value=st.session_state.benchmarks["hold_rate_healthy"], step=1.0, key="bm_hold")
        st.session_state.benchmarks["fatigue_critical"] = st.number_input("Fatigue Critical >", value=st.session_state.benchmarks["fatigue_critical"], step=0.1, key="bm_fatigue")

    with col3:
        st.markdown("**Financial Settings**")
        st.session_state.benchmarks["breakeven_roas"] = st.number_input("Break-even ROAS", value=st.session_state.benchmarks["breakeven_roas"], step=0.1, key="bm_be_roas")
        st.session_state.benchmarks["cogs_avg"] = st.number_input("Avg COGS ($)", value=st.session_state.benchmarks["cogs_avg"], step=0.5, key="bm_cogs")
        st.session_state.benchmarks["new_customer_pct"] = st.number_input("New Customer %", value=st.session_state.benchmarks["new_customer_pct"], step=1.0, key="bm_nc")
        st.session_state.benchmarks["repeat_rate"] = st.number_input("Avg Repeat Rate", value=st.session_state.benchmarks["repeat_rate"], step=0.1, key="bm_repeat")

    if st.button("Save Benchmarks", type="primary", key="btn_save_bm"):
        st.success("Benchmarks saved!")

# ═══════════════════════════════════════════════════════════════════════════════
# METRIC LIBRARY
# ═══════════════════════════════════════════════════════════════════════════════

with settings_tabs[1]:
    st.markdown('<div class="section-title">Complete Metric Library</div>', unsafe_allow_html=True)
    st.markdown(f"**{len(METRICS)} pre-built metrics** across **{len(CATEGORIES)} categories**")

    for cat_id, cat_info in CATEGORIES.items():
        metrics_in_cat = METRICS_BY_CATEGORY.get(cat_id, [])
        if not metrics_in_cat:
            continue
        with st.expander(f"{cat_info['name']} / {cat_info['name_ar']} ({len(metrics_in_cat)} metrics)"):
            for m in metrics_in_cat:
                st.markdown(f"""
                **{m['name']}** (`{m['id']}`)  
                {m.get('name_ar', '')}  
                Formula: `{m['formula']}`  
                Level: {m.get('level', 'all')} | Unit: {m.get('unit', '')}  
                {m.get('description', '')}
                """)
                if m.get("thresholds"):
                    t = m["thresholds"]
                    st.markdown(f"Thresholds: Healthy > {t.get('healthy', 'N/A')}, Warning > {t.get('warning', 'N/A')}, Critical < {t.get('critical', 'N/A')}")
                st.markdown("---")

    # Custom metrics
    st.markdown("#### Your Custom Metrics")
    custom = st.session_state.get("custom_metrics", [])
    if custom:
        for i, m in enumerate(custom):
            st.markdown(f"**{m['name']}**: `{m['formula']}`")
    else:
        st.info("No custom metrics created yet. Use the Metric Lab to create them.")

# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN ALIASES
# ═══════════════════════════════════════════════════════════════════════════════

with settings_tabs[2]:
    st.markdown('<div class="section-title">Column Name Aliases</div>', unsafe_allow_html=True)
    st.markdown("The system auto-normalizes common column name variations. Here are the recognized aliases:")

    from src.data_importer import COLUMN_ALIASES
    alias_data = [{"Input Name": k, "Normalized To": v} for k, v in sorted(COLUMN_ALIASES.items())]
    downloadable_dataframe(pd.DataFrame(alias_data), key="settings_aliases", label="column_aliases", use_container_width=True, hide_index=True, height=400)

# ═══════════════════════════════════════════════════════════════════════════════
# ABOUT
# ═══════════════════════════════════════════════════════════════════════════════

with settings_tabs[3]:
    st.markdown('<div class="section-title">About Monster Data Analyst</div>', unsafe_allow_html=True)
    st.markdown("""
    ### Monster Data Analyst
    **Ultimate MarTech Expert Analysis Platform**
    
    Built for marketing professionals who need to deeply analyze data from multiple sources 
    including Meta Ads, Google Ads, CRM systems, order sheets, and any other data source.
    
    #### Key Features:
    - **Multi-Source Import**: CSV, JSON, Excel, Google Sheets (public links)
    - **Data Linking**: Join datasets on any column (ad_id, campaign_name, etc.)
    - **125+ Pre-Built Metrics**: From Hook Rate to True POAS
    - **Custom Formula Engine**: Safe arithmetic with DAX-like syntax
    - **Financial Analysis**: POAS, Break-even, Unit Economics
    - **Creative Audit**: Fatigue detection, ghost impressions, attention metrics
    - **Algorithm Health**: Audience exhaustion, retargeting saturation monitoring
    - **Messaging Analysis**: Conversation-to-order conversion tracking
    - **Report Builder**: Custom reports with export to CSV, Excel, JSON
    
    #### Metric Categories:
    """)
    for cat_id, cat_info in CATEGORIES.items():
        count = len(METRICS_BY_CATEGORY.get(cat_id, []))
        st.markdown(f"- **{cat_info['name']}** ({cat_info['name_ar']}): {count} metrics")

    st.markdown(f"""
    ---
    **Total Metrics**: {len(METRICS)}  
    **Categories**: {len(CATEGORIES)}  
    **Supported Import Formats**: CSV, JSON, Excel, Google Sheets  
    **Formula Engine**: AST-based safe evaluator (no eval/exec)
    """)
