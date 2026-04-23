"""
Meta Ads Ultimate Dashboard — Main Application
Windows 11 themed Streamlit dashboard with full Meta Ads API integration.
Extraction, KPI analysis, CRUD, bulk operations, automation, and multi-format export.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from src.config import config, load_env_file
from src.meta_catalog import (
    ALL_METRICS, DELIVERY_METRICS, ACTION_METRICS, VIDEO_METRICS,
    QUALITY_METRICS, ENGAGEMENT_METRICS, CATALOG_METRICS,
    LEVELS, DATE_PRESETS, BREAKDOWN_CONFIGS, TIME_INCREMENTS,
    ACTION_REPORT_TIMES, CAMPAIGN_OBJECTIVES, BID_STRATEGIES,
)
from src.extractor import MetaAdsExtractor
from src.helpers import (
    format_currency, format_number, format_percentage, format_ratio,
    safe_float, safe_int, safe_divide, insights_to_dataframe,
)
from src.kpi_engine import KPIEngine, STANDARD_KPIS

# Configure logging
(Path(__file__).parent / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "logs" / "app.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ULTIMATE Meta Ads Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# WINDOWS 11 THEME CSS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
:root { direction: ltr; }

.main-header {
    background: linear-gradient(135deg, #0078D4 0%, #106EBE 50%, #005A9E 100%);
    padding: 20px 30px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 16px rgba(0, 120, 212, 0.3);
}
.main-header h1 {
    color: white;
    font-size: 28px;
    font-weight: 600;
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
}
.main-header p {
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    margin: 4px 0 0 0;
}

.stApp {
    background-color: #f3f3f3;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
    box-shadow: 2px 0 8px rgba(0,0,0,0.05);
}

[data-testid="stMetricValue"] {
    font-size: 1.8rem;
    font-weight: 700;
    color: #0078D4;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stMetricLabel"] {
    font-size: 0.85rem;
    font-weight: 500;
    color: #605E5C;
}

.kpi-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: box-shadow 0.2s;
}
.kpi-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #0078D4;
}
.kpi-label {
    font-size: 0.85rem;
    color: #605E5C;
    margin-top: 4px;
}

.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #323130;
    border-bottom: 2px solid #0078D4;
    padding-bottom: 8px;
    margin-bottom: 16px;
}

.stDataFrame { font-size: 0.85rem; }

.status-active { color: #107C10; font-weight: 600; }
.status-paused { color: #FFB900; font-weight: 600; }
.status-deleted { color: #D13438; font-weight: 600; }
.status-archived { color: #605E5C; font-weight: 600; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULTS = {
    "connected": False,
    "access_token": "",
    "ad_account_id": "",
    "last_result": None,
    "extraction_running": False,
    "campaigns_cache": None,
}
for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="main-header">'
    "<h1>ULTIMATE Meta Ads Dashboard</h1>"
    "<p>All Metrics x All Levels x All Breakdowns — Windows 11 Edition</p>"
    "</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Connection")

    token = st.text_input(
        "Access Token",
        value=st.session_state.access_token or os.getenv("META_ACCESS_TOKEN", ""),
        type="password",
        key="input_token",
    )
    account_id = st.text_input(
        "Ad Account ID",
        value=st.session_state.ad_account_id or os.getenv("META_AD_ACCOUNT_ID", ""),
        placeholder="act_XXXXXXXXX",
        key="input_account",
    )

    col_conn1, col_conn2 = st.columns(2)
    with col_conn1:
        if st.button("Connect", use_container_width=True):
            if token and account_id:
                st.session_state.access_token = token
                st.session_state.ad_account_id = account_id
                try:
                    ext = MetaAdsExtractor(token, account_id)
                    info = ext.validate_token()
                    st.session_state.connected = True
                    st.success(f"Connected as {info.get('name', 'User')}")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)[:100]}")
            else:
                st.warning("Provide both token and account ID")
    with col_conn2:
        if st.button("Disconnect", use_container_width=True):
            st.session_state.connected = False
            st.session_state.access_token = ""
            st.session_state.ad_account_id = ""
            st.session_state.campaigns_cache = None
            st.rerun()

    if st.session_state.connected:
        st.success("Connected")
    else:
        st.warning("Not connected")

    st.markdown("---")

    # Date Config
    st.markdown("### Date Range")
    date_mode = st.radio("Date Mode", ["Preset", "Custom Range"], horizontal=True)
    if date_mode == "Preset":
        preset = st.selectbox(
            "Date Preset",
            list(DATE_PRESETS.keys()),
            index=list(DATE_PRESETS.keys()).index("last_30d"),
        )
        start_date, end_date = None, None
    else:
        preset = None
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Start Date").strftime("%Y-%m-%d")
        with col_d2:
            end_date = st.date_input("End Date").strftime("%Y-%m-%d")

    st.markdown("---")

    # Levels
    st.markdown("### Data Levels")
    selected_levels = []
    for level in LEVELS:
        if st.checkbox(level.title(), value=(level == "ad"), key=f"level_{level}"):
            selected_levels.append(level)
    if not selected_levels:
        selected_levels = ["ad"]

    st.markdown("---")

    # Breakdowns
    st.markdown("### Breakdowns")
    breakdown_options = {k: v["label"] for k, v in BREAKDOWN_CONFIGS.items()}
    selected_breakdowns = st.multiselect(
        "Select Breakdowns",
        options=list(breakdown_options.keys()),
        default=["none"],
        format_func=lambda x: breakdown_options[x],
    )
    if not selected_breakdowns:
        selected_breakdowns = ["none"]

    st.markdown("---")

    # Metrics
    st.markdown("### Metrics")
    metrics_mode = st.radio("Metrics", ["All", "Custom Selection"], horizontal=True)
    selected_metrics = None
    if metrics_mode == "Custom Selection":
        metric_groups = {
            "Delivery": DELIVERY_METRICS,
            "Actions": ACTION_METRICS,
            "Video": VIDEO_METRICS,
            "Quality": QUALITY_METRICS,
            "Engagement": ENGAGEMENT_METRICS,
            "Catalog": CATALOG_METRICS,
        }
        chosen_groups = st.multiselect(
            "Metric Groups", list(metric_groups.keys()), default=["Delivery"]
        )
        selected_metrics = []
        for g in chosen_groups:
            selected_metrics.extend(metric_groups[g])
        selected_metrics = list(dict.fromkeys(selected_metrics))

    st.markdown("---")

    # Advanced
    with st.expander("Advanced Settings"):
        time_increment = st.selectbox("Time Increment", TIME_INCREMENTS, index=0)
        action_report_time = st.selectbox(
            "Action Report Time", ACTION_REPORT_TIMES, index=2
        )
        attribution_options = [
            "1d_click", "7d_click", "28d_click",
            "1d_view", "7d_view", "28d_view",
        ]
        attribution_windows = st.multiselect(
            "Attribution Windows", attribution_options, default=["7d_click", "1d_view"]
        )
        include_entities = st.checkbox("Include Entity Catalogs", value=True)
        create_zip = st.checkbox("Create ZIP archive", value=False)

    # Campaign Filter
    with st.expander("Campaign Filter"):
        filter_mode = st.radio(
            "Campaign Selection", ["All Campaigns", "Specific IDs"], horizontal=True
        )
        campaign_ids = None
        if filter_mode == "Specific IDs":
            ids_text = st.text_area(
                "Campaign IDs (one per line)", height=100
            )
            if ids_text.strip():
                campaign_ids = [
                    x.strip() for x in ids_text.strip().splitlines() if x.strip()
                ]

        if st.session_state.connected and st.button("Load Campaign List"):
            try:
                ext = MetaAdsExtractor(
                    st.session_state.access_token,
                    st.session_state.ad_account_id,
                )
                campaigns = ext.get_campaigns()
                st.session_state.campaigns_cache = campaigns
                for c in campaigns[:20]:
                    st.write(f"• {c.get('name', 'N/A')} ({c.get('id', '')})")
                if len(campaigns) > 20:
                    st.info(f"... and {len(campaigns) - 20} more")
            except Exception as e:
                st.error(f"Failed: {str(e)[:100]}")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN AREA — TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_extract, tab_preview, tab_kpi, tab_files, tab_settings = st.tabs([
    "Extraction", "Data Preview", "KPI Dashboard", "Files & Export", "Settings",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_extract:
    st.markdown('<div class="section-header">Run Data Extraction</div>', unsafe_allow_html=True)

    col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
    with col_summary1:
        st.metric("Levels", len(selected_levels))
    with col_summary2:
        st.metric("Breakdowns", len(selected_breakdowns))
    with col_summary3:
        st.metric("Total Tasks", len(selected_levels) * len(selected_breakdowns))
    with col_summary4:
        st.metric("Workers", 5)

    st.markdown("**Selected:**")
    st.write(f"Levels: {', '.join(selected_levels)}")
    st.write(f"Breakdowns: {', '.join(selected_breakdowns)}")
    if preset:
        st.write(f"Date: {preset}")
    else:
        st.write(f"Date: {start_date} to {end_date}")

    if st.button(
        "START EXTRACTION",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.connected,
    ):
        if not st.session_state.connected:
            st.error("Please connect first")
        else:
            st.session_state.extraction_running = True
            progress = st.progress(0)
            status = st.empty()

            def update_progress(msg: str, done: int, total: int) -> None:
                progress.progress(done / total if total else 0)
                status.text(msg)

            try:
                ext = MetaAdsExtractor(
                    st.session_state.access_token,
                    st.session_state.ad_account_id,
                    progress_cb=update_progress,
                )
                result = ext.run(
                    levels=selected_levels,
                    breakdowns=selected_breakdowns,
                    campaign_ids=campaign_ids,
                    preset=preset,
                    start_date=start_date,
                    end_date=end_date,
                    time_increment=time_increment,
                    selected_metrics=selected_metrics,
                    attribution_windows=attribution_windows,
                    action_report_time=action_report_time,
                    include_entities=include_entities,
                )
                st.session_state.last_result = result
                st.session_state.extraction_running = False
                progress.progress(1.0)
                status.text("Extraction complete!")
                st.success(
                    f"Extraction finished. Output: {result['output_dir']}"
                )

                if create_zip:
                    zip_path = ext.zip_output(result["output_dir"])
                    st.info(f"ZIP created: {zip_path}")

            except Exception as e:
                st.session_state.extraction_running = False
                st.error(f"Extraction failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: DATA PREVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab_preview:
    st.markdown('<div class="section-header">Data Preview</div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    if result and "output_dir" in result:
        raw_dir = os.path.join(result["output_dir"], "raw")
        if os.path.exists(raw_dir):
            csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
            if csv_files:
                selected_file = st.selectbox("Select Dataset", csv_files)
                path = os.path.join(raw_dir, selected_file)
                df = pd.read_csv(path)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.info(f"{len(df)} rows x {len(df.columns)} columns")

                search = st.text_input("Search columns...")
                if search:
                    matching = [c for c in df.columns if search.lower() in c.lower()]
                    if matching:
                        st.dataframe(df[matching], use_container_width=True, hide_index=True)
            else:
                st.info("No CSV files in output")
        else:
            st.info("No raw output directory found")
    else:
        st.info("Run an extraction first to preview data")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: KPI DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_kpi:
    st.markdown('<div class="section-header">KPI Dashboard</div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    if result and "output_dir" in result:
        raw_dir = os.path.join(result["output_dir"], "raw")
        if os.path.exists(raw_dir):
            csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
            if csv_files:
                kpi_source = st.selectbox(
                    "KPI Data Source", csv_files, key="kpi_source"
                )
                df = pd.read_csv(os.path.join(raw_dir, kpi_source))

                engine = KPIEngine()
                df_with_kpis = engine.compute_all(df)

                col_k1, col_k2, col_k3, col_k4, col_k5, col_k6 = st.columns(6)
                with col_k1:
                    total_spend = df["spend"].sum() if "spend" in df.columns else 0
                    st.metric("Total Spend", format_currency(total_spend))
                with col_k2:
                    total_imp = df["impressions"].sum() if "impressions" in df.columns else 0
                    st.metric("Impressions", format_number(total_imp))
                with col_k3:
                    total_clicks = df["clicks"].sum() if "clicks" in df.columns else 0
                    st.metric("Clicks", format_number(total_clicks))
                with col_k4:
                    total_reach = df["reach"].sum() if "reach" in df.columns else 0
                    st.metric("Reach", format_number(total_reach))
                with col_k5:
                    avg_ctr = safe_divide(total_clicks, total_imp) * 100
                    st.metric("CTR", format_percentage(avg_ctr))
                with col_k6:
                    avg_cpc = safe_divide(total_spend, total_clicks)
                    st.metric("CPC", format_currency(avg_cpc))

                st.markdown("---")
                st.markdown("### Detailed KPIs")
                kpi_cols = [c for c in df_with_kpis.columns if c.startswith("kpi_")]
                if kpi_cols:
                    st.dataframe(
                        df_with_kpis[kpi_cols].describe(),
                        use_container_width=True,
                    )

                # Custom Formula Lab
                st.markdown("---")
                st.markdown("### Formula Lab")
                custom_formula = st.text_input(
                    "Custom Formula",
                    placeholder="e.g., spend / clicks * 100",
                    help="Use column names from the data. Available: " + ", ".join(df.columns[:20].tolist()),
                )
                if custom_formula:
                    try:
                        from src.kpi_engine import evaluate_formula

                        totals = {}
                        for col in df.select_dtypes(include=["number"]).columns:
                            totals[col] = float(df[col].sum())
                        result_val = evaluate_formula(custom_formula, totals)
                        st.metric("Result", f"{result_val:,.4f}")
                    except Exception as e:
                        st.error(f"Formula error: {e}")
            else:
                st.info("No data files available")
        else:
            st.info("No output directory found")
    else:
        st.info("Run an extraction first")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: FILES & EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_files:
    st.markdown('<div class="section-header">Files & Export</div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    if result and "output_dir" in result:
        out_dir = result["output_dir"]
        manifest = result.get("manifest", {})

        st.markdown(f"**Output Directory:** `{out_dir}`")

        # File list
        file_count = 0
        for root, dirs, files in os.walk(out_dir):
            for f in files:
                file_count += 1
                full = os.path.join(root, f)
                rel = os.path.relpath(full, out_dir)
                size = os.path.getsize(full)
                st.text(f"  {rel}  ({size:,} bytes)")
        st.info(f"Total files: {file_count}")

        # Download section
        st.markdown("---")
        st.markdown("### Downloads")

        master_excel = manifest.get("master_excel", "")
        if master_excel and os.path.exists(master_excel):
            with open(master_excel, "rb") as f:
                st.download_button(
                    "Download Master Excel",
                    f.read(),
                    file_name="MASTER_ALL_DATA.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        master_json = manifest.get("master_json", "")
        if master_json and os.path.exists(master_json):
            with open(master_json, "r", encoding="utf-8") as f:
                st.download_button(
                    "Download Master JSON",
                    f.read(),
                    file_name="MASTER_ALL_DATA.json",
                    mime="application/json",
                )

        # Google Sheets export
        st.markdown("---")
        st.markdown("### Google Sheets Export")
        sheet_id = st.text_input("Spreadsheet ID", placeholder="Enter Google Sheets ID")
        if st.button("Export to Google Sheets") and sheet_id:
            try:
                from src.sheets_exporter import export_dataframe_to_sheets

                raw_dir = os.path.join(out_dir, "raw")
                csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
                if csv_files:
                    df = pd.read_csv(os.path.join(raw_dir, csv_files[0]))
                    success = export_dataframe_to_sheets(df, sheet_id)
                    if success:
                        st.success("Exported to Google Sheets!")
                    else:
                        st.error("Export failed")
            except Exception as e:
                st.error(f"Export error: {e}")
    else:
        st.info("Run an extraction to see files")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_settings:
    st.markdown('<div class="section-header">Settings</div>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("### API Configuration")
        st.text(f"API Version: {config.META_API_VERSION}")
        st.text(f"Rate Limit: {config.RATE_LIMIT_CALLS_PER_HOUR}/hour")
        st.text(f"Max Retries: {config.RATE_LIMIT_RETRY_MAX}")
        st.text(f"Cache TTL: {config.CACHE_TTL_SECONDS}s")
        st.text(f"Configured: {'Yes' if config.is_configured() else 'No'}")

    with col_s2:
        st.markdown("### Standard KPIs")
        for kpi_id, kpi in STANDARD_KPIS.items():
            st.text(f"{kpi['name']}: {kpi['formula']}")

    st.markdown("---")
    st.markdown("### Available Breakdowns")
    bd_data = []
    for k, v in BREAKDOWN_CONFIGS.items():
        bd_data.append({
            "Key": k,
            "Label": v["label"],
            "Fields": ", ".join(v["breakdowns"]) if v["breakdowns"] else "—",
            "Metrics Count": len(v["metrics"]),
        })
    st.dataframe(pd.DataFrame(bd_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### All Available Metrics")
    metric_groups = {
        "Delivery": DELIVERY_METRICS,
        "Actions": ACTION_METRICS,
        "Video": VIDEO_METRICS,
        "Quality": QUALITY_METRICS,
        "Engagement": ENGAGEMENT_METRICS,
        "Catalog": CATALOG_METRICS,
    }
    for group_name, metrics in metric_groups.items():
        with st.expander(f"{group_name} ({len(metrics)} fields)"):
            for m in metrics:
                st.text(f"  {m}")
