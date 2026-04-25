"""
Report Builder — Custom report creation, scheduling, and export.
Build reports with any combination of metrics, breakdowns, and date ranges.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

from src.extractor import MetaAdsExtractor
from src.kpi_engine import compute_kpis
from src.helpers import format_currency, format_number, format_percentage, safe_float, safe_int, safe_divide
from src.meta_catalog import (
    LEVELS, BREAKDOWN_CONFIGS, DATE_PRESETS,
    DELIVERY_METRICS, ACTION_METRICS, VIDEO_METRICS,
    QUALITY_METRICS, ENGAGEMENT_METRICS,
)

st.set_page_config(page_title="Report Builder", page_icon="📄", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
</style>""", unsafe_allow_html=True)

REPORTS_DIR = "config/saved_reports"

if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Report Builder")
st.markdown("Create custom reports with any combination of metrics, breakdowns, and filters.")

tab_build, tab_saved, tab_templates, tab_schedule = st.tabs([
    "Build Report", "Saved Reports", "Report Templates", "Scheduled Reports",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: BUILD REPORT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_build:
    st.markdown('<div class="section-title">Build Custom Report</div>', unsafe_allow_html=True)

    report_name = st.text_input("Report Name", key="rb_name")

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        report_level = st.selectbox("Report Level", LEVELS, index=1, key="rb_level")
        report_date = st.selectbox(
            "Date Range",
            list(DATE_PRESETS.keys()),
            index=list(DATE_PRESETS.keys()).index("last_30d"),
            key="rb_date",
        )
    with col_b2:
        report_breakdown = st.selectbox(
            "Breakdown",
            list(BREAKDOWN_CONFIGS.keys()),
            format_func=lambda x: BREAKDOWN_CONFIGS[x]["label"],
            key="rb_breakdown",
        )
        group_by = st.multiselect(
            "Group By (columns)",
            ["campaign_name", "adset_name", "ad_name", "date_start", "age", "gender",
             "country", "publisher_platform", "platform_position", "device_platform"],
            default=["campaign_name"],
            key="rb_group",
        )
    with col_b3:
        report_metrics = st.multiselect(
            "Metrics",
            ["spend", "impressions", "clicks", "reach", "frequency",
             "ctr", "cpc", "cpm", "conversions", "roas", "cpa"],
            default=["spend", "impressions", "clicks", "ctr", "cpc"],
            key="rb_metrics",
        )
        sort_by = st.selectbox("Sort By", report_metrics if report_metrics else ["spend"], key="rb_sort")
        sort_order = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True, key="rb_order")

    # Filters
    with st.expander("Filters"):
        min_spend = st.number_input("Min Spend ($)", value=0.0, step=1.0, key="rb_min_spend")
        min_impressions = st.number_input("Min Impressions", value=0, step=100, key="rb_min_imps")
        campaign_filter = st.text_input("Campaign name contains", key="rb_camp_filter")
        top_n = st.number_input("Top N results (0=all)", value=0, step=5, key="rb_top_n")

    if st.button("Generate Report", type="primary", use_container_width=True, key="rb_generate"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )

            with st.spinner("Generating report..."):
                df = ext.fetch_insights(
                    level=report_level,
                    breakdown_key=report_breakdown,
                    preset=report_date,
                )

            if not df.empty:
                df = compute_kpis(df)

                # Apply filters
                if min_spend > 0 and "spend" in df.columns:
                    df["spend"] = df["spend"].astype(float)
                    df = df[df["spend"] >= min_spend]
                if min_impressions > 0 and "impressions" in df.columns:
                    df["impressions"] = df["impressions"].astype(float)
                    df = df[df["impressions"] >= min_impressions]
                if campaign_filter and "campaign_name" in df.columns:
                    df = df[df["campaign_name"].str.contains(campaign_filter, case=False, na=False)]

                # Select and sort columns
                available_cols = [c for c in group_by + report_metrics if c in df.columns]
                if available_cols:
                    report_df = df[available_cols].copy()
                else:
                    report_df = df.copy()

                if sort_by in report_df.columns:
                    report_df[sort_by] = report_df[sort_by].astype(float)
                    report_df = report_df.sort_values(sort_by, ascending=(sort_order == "Ascending"))

                if top_n > 0:
                    report_df = report_df.head(int(top_n))

                # Display
                st.markdown(f"### {report_name or 'Custom Report'}")
                st.info(f"{len(report_df)} rows | Level: {report_level} | "
                        f"Breakdown: {BREAKDOWN_CONFIGS[report_breakdown]['label']} | Period: {report_date}")
                st.dataframe(report_df, use_container_width=True, hide_index=True, height=500)

                # Summary row
                st.markdown("### Summary")
                summary = {}
                for col in report_metrics:
                    if col in report_df.columns:
                        try:
                            vals = report_df[col].astype(float)
                            summary[col] = {
                                "Total": f"{vals.sum():,.2f}",
                                "Average": f"{vals.mean():,.2f}",
                                "Min": f"{vals.min():,.2f}",
                                "Max": f"{vals.max():,.2f}",
                            }
                        except (ValueError, TypeError):
                            pass
                if summary:
                    st.dataframe(pd.DataFrame(summary).T, use_container_width=True)

                # Export options
                st.markdown("### Export")
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    csv = report_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, f"{report_name or 'report'}.csv", "text/csv")
                with col_e2:
                    json_data = report_df.to_json(orient="records", indent=2)
                    st.download_button("Download JSON", json_data, f"{report_name or 'report'}.json", "application/json")
                with col_e3:
                    if report_name:
                        if st.button("Save Report Config", key="rb_save"):
                            os.makedirs(REPORTS_DIR, exist_ok=True)
                            config = {
                                "name": report_name,
                                "level": report_level,
                                "date_range": report_date,
                                "breakdown": report_breakdown,
                                "metrics": report_metrics,
                                "group_by": group_by,
                                "sort_by": sort_by,
                                "sort_order": sort_order,
                                "filters": {
                                    "min_spend": min_spend,
                                    "min_impressions": min_impressions,
                                    "campaign_filter": campaign_filter,
                                    "top_n": top_n,
                                },
                                "created_at": datetime.now().isoformat(),
                            }
                            with open(os.path.join(REPORTS_DIR, f"{report_name}.json"), "w") as f:
                                json.dump(config, f, indent=2)
                            st.success(f"Report '{report_name}' saved!")
            else:
                st.info("No data returned for this report configuration.")
        except Exception as e:
            st.error(f"Report generation failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: SAVED REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_saved:
    st.markdown('<div class="section-title">Saved Reports</div>', unsafe_allow_html=True)

    if os.path.exists(REPORTS_DIR):
        report_files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")]
        if report_files:
            rows = []
            for rf in report_files:
                with open(os.path.join(REPORTS_DIR, rf)) as f:
                    config = json.load(f)
                rows.append({
                    "Name": config.get("name", ""),
                    "Level": config.get("level", ""),
                    "Date Range": config.get("date_range", ""),
                    "Breakdown": config.get("breakdown", ""),
                    "Metrics": ", ".join(config.get("metrics", [])),
                    "Created": config.get("created_at", "")[:10],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            selected_report = st.selectbox(
                "Select report to view/run",
                report_files,
                format_func=lambda x: x.replace(".json", ""),
                key="sr_select",
            )
            if selected_report:
                with open(os.path.join(REPORTS_DIR, selected_report)) as f:
                    config = json.load(f)
                st.json(config)

                col_sr1, col_sr2 = st.columns(2)
                with col_sr1:
                    if st.button("Run Report", type="primary", key="sr_run"):
                        st.info("Switch to 'Build Report' tab and use the same settings to re-run.")
                with col_sr2:
                    if st.button("Delete Report", key="sr_delete"):
                        os.remove(os.path.join(REPORTS_DIR, selected_report))
                        st.success("Report deleted!")
                        st.rerun()
        else:
            st.info("No saved reports. Build a report and save it.")
    else:
        st.info("No saved reports yet.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: REPORT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

REPORT_TEMPLATES = [
    {
        "name": "Executive Summary",
        "level": "campaign",
        "date_range": "last_30d",
        "breakdown": "none",
        "metrics": ["spend", "impressions", "clicks", "ctr", "cpc", "cpm"],
        "group_by": ["campaign_name"],
        "sort_by": "spend",
    },
    {
        "name": "Age & Gender Performance",
        "level": "campaign",
        "date_range": "last_30d",
        "breakdown": "age_gender",
        "metrics": ["spend", "impressions", "clicks", "ctr", "cpc"],
        "group_by": ["age", "gender"],
        "sort_by": "spend",
    },
    {
        "name": "Placement Analysis",
        "level": "campaign",
        "date_range": "last_30d",
        "breakdown": "placement",
        "metrics": ["spend", "impressions", "clicks", "ctr", "cpc"],
        "group_by": ["publisher_platform", "platform_position"],
        "sort_by": "spend",
    },
    {
        "name": "Daily Spend Tracker",
        "level": "account",
        "date_range": "last_30d",
        "breakdown": "none",
        "metrics": ["spend", "impressions", "clicks", "ctr"],
        "group_by": ["date_start"],
        "sort_by": "date_start",
    },
    {
        "name": "Top Performing Ads",
        "level": "ad",
        "date_range": "last_14d",
        "breakdown": "none",
        "metrics": ["spend", "impressions", "clicks", "ctr", "cpc"],
        "group_by": ["ad_name", "campaign_name"],
        "sort_by": "ctr",
    },
    {
        "name": "Country Performance",
        "level": "campaign",
        "date_range": "last_30d",
        "breakdown": "country",
        "metrics": ["spend", "impressions", "clicks", "ctr", "cpc"],
        "group_by": ["country"],
        "sort_by": "spend",
    },
]

with tab_templates:
    st.markdown('<div class="section-title">Report Templates</div>', unsafe_allow_html=True)

    for i, tmpl in enumerate(REPORT_TEMPLATES):
        with st.expander(f"📋 {tmpl['name']}"):
            st.markdown(f"**Level:** {tmpl['level']}")
            st.markdown(f"**Date Range:** {tmpl['date_range']}")
            st.markdown(f"**Breakdown:** {tmpl['breakdown']}")
            st.markdown(f"**Metrics:** {', '.join(tmpl['metrics'])}")
            st.markdown(f"**Group By:** {', '.join(tmpl['group_by'])}")

            if st.button(f"Use Template", key=f"rt_{i}"):
                os.makedirs(REPORTS_DIR, exist_ok=True)
                tmpl["created_at"] = datetime.now().isoformat()
                with open(os.path.join(REPORTS_DIR, f"{tmpl['name']}.json"), "w") as f:
                    json.dump(tmpl, f, indent=2)
                st.success(f"Template '{tmpl['name']}' saved to reports!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SCHEDULED REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_schedule:
    st.markdown('<div class="section-title">Scheduled Reports</div>', unsafe_allow_html=True)

    st.markdown("""
    Set up automatic report generation and delivery.
    Reports are generated at the scheduled time and saved to the output directory.
    """)

    sched_report = st.selectbox(
        "Report to Schedule",
        [f.replace(".json", "") for f in os.listdir(REPORTS_DIR)] if os.path.exists(REPORTS_DIR) and os.listdir(REPORTS_DIR) else ["No saved reports"],
        key="sched_report",
    )

    col_sch1, col_sch2 = st.columns(2)
    with col_sch1:
        sched_freq = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"], key="sched_freq")
        sched_time = st.time_input("Time", key="sched_time")
    with col_sch2:
        sched_format = st.multiselect("Output Format", ["CSV", "JSON", "Excel"], default=["CSV"], key="sched_format")
        sched_email = st.text_input("Email notification (optional)", key="sched_email")

    if st.button("Schedule Report", type="primary", key="sched_create"):
        schedule = {
            "report": sched_report,
            "frequency": sched_freq,
            "time": str(sched_time),
            "formats": sched_format,
            "email": sched_email,
            "created_at": datetime.now().isoformat(),
            "enabled": True,
        }
        sched_file = "config/report_schedules.json"
        schedules = []
        if os.path.exists(sched_file):
            with open(sched_file) as f:
                schedules = json.load(f)
        schedules.append(schedule)
        os.makedirs("config", exist_ok=True)
        with open(sched_file, "w") as f:
            json.dump(schedules, f, indent=2)
        st.success(f"Report '{sched_report}' scheduled {sched_freq} at {sched_time}!")
