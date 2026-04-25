"""
Settings — System configuration, API connection, cache management,
KPI definitions, and system information.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.config import Config
from src.kpi_engine import STANDARD_KPIS
from src.meta_catalog import (
    API_VERSION, PAGE_LIMIT, MAX_WORKERS, MAX_RETRIES,
    ALL_METRICS, BREAKDOWN_CONFIGS, LEVELS, DATE_PRESETS,
    DELIVERY_METRICS, ACTION_METRICS, VIDEO_METRICS,
    QUALITY_METRICS, ENGAGEMENT_METRICS, CATALOG_METRICS,
)

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .setting-card { background: white; border-radius: 8px; padding: 16px; margin: 8px 0;
        border: 1px solid #e0e0e0; }
</style>""", unsafe_allow_html=True)

st.markdown("# Settings")

cfg = Config()

tab_api, tab_kpis, tab_catalog, tab_cache, tab_about = st.tabs([
    "API Configuration", "KPI Definitions", "Metric Catalog", "Cache & Data", "About",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: API CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_api:
    st.markdown('<div class="section-title">API Configuration</div>', unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("### Connection Settings")
        st.text_input("API Version", value=cfg.META_API_VERSION, disabled=True, key="set_api_ver")
        st.text_input("Base URL", value=f"https://graph.facebook.com/{cfg.META_API_VERSION}", disabled=True, key="set_base_url")
        st.number_input("Page Limit", value=PAGE_LIMIT, disabled=True, key="set_page_limit")
        st.number_input("Max Workers", value=MAX_WORKERS, disabled=True, key="set_max_workers")
        st.number_input("Max Retries", value=MAX_RETRIES, disabled=True, key="set_max_retries")

    with col_a2:
        st.markdown("### Rate Limiting")
        st.number_input("Calls per Hour", value=cfg.RATE_LIMIT_CALLS_PER_HOUR, disabled=True, key="set_calls_hr")
        st.number_input("Retry Max", value=cfg.RATE_LIMIT_RETRY_MAX, disabled=True, key="set_retry_max")
        st.number_input("Backoff Base", value=cfg.RATE_LIMIT_BACKOFF_BASE, disabled=True, key="set_backoff")
        st.number_input("Cache TTL (seconds)", value=cfg.CACHE_TTL_SECONDS, disabled=True, key="set_cache_ttl")
        st.number_input("Insights Cache TTL", value=cfg.INSIGHTS_CACHE_TTL, disabled=True, key="set_insights_ttl")

    st.markdown("### Connection Status")
    connected = st.session_state.get("connected", False)
    if connected:
        st.success(f"Connected to account: {st.session_state.get('ad_account_id', 'N/A')}")
    else:
        st.warning("Not connected. Enter credentials on the main dashboard.")

    st.markdown("### Environment Variables")
    import os
    env_vars = {
        "META_ACCESS_TOKEN": "Set" if os.environ.get("META_ACCESS_TOKEN") else "Not set",
        "META_AD_ACCOUNT_ID": os.environ.get("META_AD_ACCOUNT_ID", "Not set"),
        "META_APP_ID": os.environ.get("META_APP_ID", "Not set"),
        "META_APP_SECRET": "Set" if os.environ.get("META_APP_SECRET") else "Not set",
        "GOOGLE_SHEETS_CREDENTIALS": "Set" if os.environ.get("GOOGLE_SHEETS_CREDENTIALS") else "Not set",
    }
    st.dataframe(
        pd.DataFrame([{"Variable": k, "Status": v} for k, v in env_vars.items()]),
        use_container_width=True, hide_index=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: KPI DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_kpis:
    st.markdown('<div class="section-title">Standard KPI Definitions</div>', unsafe_allow_html=True)

    kpi_rows = []
    for key, kpi in STANDARD_KPIS.items():
        kpi_rows.append({
            "Key": key,
            "Name": kpi["name"],
            "Formula": kpi["formula"],
            "Unit": kpi["unit"],
        })

    st.dataframe(pd.DataFrame(kpi_rows), use_container_width=True, hide_index=True)

    st.markdown(f"**Total KPIs:** {len(STANDARD_KPIS)}")

    st.markdown("### KPI Benchmarks")
    benchmarks = {
        "CTR": {"Good": "> 2.0%", "Average": "1.0% - 2.0%", "Poor": "< 1.0%"},
        "CPC": {"Good": "< $1.00", "Average": "$1.00 - $3.00", "Poor": "> $3.00"},
        "CPM": {"Good": "< $10.00", "Average": "$10.00 - $30.00", "Poor": "> $30.00"},
        "ROAS": {"Good": "> 3.0x", "Average": "1.5x - 3.0x", "Poor": "< 1.5x"},
        "CPA": {"Good": "< $20", "Average": "$20 - $50", "Poor": "> $50"},
        "Frequency": {"Good": "< 2.0", "Average": "2.0 - 3.5", "Poor": "> 3.5"},
        "CVR": {"Good": "> 5.0%", "Average": "2.0% - 5.0%", "Poor": "< 2.0%"},
    }
    bench_rows = []
    for kpi, thresholds in benchmarks.items():
        bench_rows.append({"KPI": kpi, **thresholds})
    st.dataframe(pd.DataFrame(bench_rows), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: METRIC CATALOG
# ═══════════════════════════════════════════════════════════════════════════════

with tab_catalog:
    st.markdown('<div class="section-title">Meta API Metric Catalog</div>', unsafe_allow_html=True)

    st.markdown(f"**API Version:** {API_VERSION}")

    metric_groups = {
        "Delivery": DELIVERY_METRICS,
        "Actions": ACTION_METRICS,
        "Video": VIDEO_METRICS,
        "Quality": QUALITY_METRICS,
        "Engagement": ENGAGEMENT_METRICS,
        "Catalog": CATALOG_METRICS,
    }

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Metrics", len(ALL_METRICS))
    c2.metric("Breakdowns", len(BREAKDOWN_CONFIGS))
    c3.metric("Metric Groups", len(metric_groups))

    for group_name, metrics in metric_groups.items():
        with st.expander(f"{group_name} ({len(metrics)} metrics)"):
            for m in metrics:
                st.write(f"• `{m}`")

    st.markdown("### Breakdowns")
    for key, cfg_item in BREAKDOWN_CONFIGS.items():
        st.write(f"• **{cfg_item['label']}** (`{key}`) — fields: {', '.join(cfg_item['breakdowns']) or 'none'}")

    st.markdown("### Date Presets")
    for k, v in DATE_PRESETS.items():
        st.write(f"• `{k}` → `{v}`")

    st.markdown("### Data Levels")
    for level in LEVELS:
        st.write(f"• `{level}`")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: CACHE & DATA
# ═══════════════════════════════════════════════════════════════════════════════

with tab_cache:
    st.markdown('<div class="section-title">Cache & Data Management</div>', unsafe_allow_html=True)

    st.markdown("### Output Directory")
    output_dir = "output"
    if os.path.exists(output_dir):
        runs = sorted([d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))], reverse=True)
        st.info(f"Found {len(runs)} extraction runs")
        for run in runs[:10]:
            run_path = os.path.join(output_dir, run)
            files = []
            for root, dirs, fnames in os.walk(run_path):
                files.extend(fnames)
            st.write(f"• **{run}** — {len(files)} files")
    else:
        st.info("No output data yet. Run an extraction to generate data.")

    st.markdown("---")
    st.markdown("### Session State")
    state_keys = list(st.session_state.keys())
    st.write(f"Session variables: {len(state_keys)}")
    with st.expander("View session state"):
        for k in sorted(state_keys):
            v = st.session_state[k]
            if "token" in k.lower() or "secret" in k.lower():
                st.write(f"• `{k}`: ****")
            else:
                st.write(f"• `{k}`: {str(v)[:100]}")

    if st.button("Clear Session State", key="clear_session"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ABOUT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_about:
    st.markdown('<div class="section-title">About Ultimate Meta Ads Dashboard</div>', unsafe_allow_html=True)

    st.markdown("""
    ### Ultimate Meta Ads Dashboard v2.0

    **A complete replacement for Meta Ads Manager** with advanced analytics,
    automation, and Power BI integration.

    **Core Features:**
    - Full Campaign/Ad Set/Ad CRUD (create, read, update, delete)
    - Audience Manager with custom, lookalike, and saved audiences
    - Creative Library with image/video upload
    - Budget & Bidding Center with allocation and forecasting
    - Real-time Performance Monitor with alerts and anomaly detection
    - Advanced Rules Engine with 6 templates
    - A/B Testing Framework with statistical significance
    - Funnel & Attribution Analysis
    - Custom Report Builder with scheduling
    - Activity Log & Audit Trail
    - Data Studio with pivot tables and formula lab
    - Full Power BI integration (.pbit template)

    **Technology Stack:**
    - Python 3.10+ / Streamlit
    - Meta Graph API v25.0
    - pandas / plotly / openpyxl
    - APScheduler for automation

    **Architecture:**
    - 7-layer spec-driven (BMAD + SPEKIT)
    - ThreadPoolExecutor (5 workers) for parallel extraction
    - Exponential backoff with rate limit monitoring
    - DataFrame-centric data flow
    - Fail-soft execution model

    **Built with BMAD-METHOD — Build More Architect Dreams**
    """)

    st.markdown("### System Information")
    import platform
    info = {
        "Python": platform.python_version(),
        "Platform": platform.platform(),
        "Streamlit": st.__version__,
        "Pandas": pd.__version__,
        "API Version": API_VERSION,
    }
    st.dataframe(
        pd.DataFrame([{"Component": k, "Version": v} for k, v in info.items()]),
        use_container_width=True, hide_index=True,
    )
