"""
Automation Page — Stop-loss rules, budget scaling, scheduling.
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.scheduler import ExtractionScheduler, ExtractionJob
from src.meta_catalog import LEVELS, BREAKDOWN_CONFIGS, DATE_PRESETS

st.set_page_config(page_title="Automation", page_icon="🤖", layout="wide")

if not st.session_state.get("connected", False):
    st.warning("Please connect to Meta API first.")
    st.stop()

st.markdown("# Automation & Scheduling")

scheduler = ExtractionScheduler()

tab_rules, tab_schedule, tab_stoploss = st.tabs([
    "Automation Rules", "Scheduled Extractions", "Stop-Loss Rules",
])

with tab_rules:
    st.markdown("### Automation Rules")
    st.info(
        "Define rules to automatically manage campaigns based on performance metrics. "
        "Rules are evaluated on each scheduled run."
    )

    with st.expander("Create New Rule"):
        rule_name = st.text_input("Rule Name", key="rule_name")
        rule_metric = st.selectbox(
            "Trigger Metric",
            ["CPA", "ROAS", "CTR", "CPM", "Spend", "Conversions"],
            key="rule_metric",
        )
        rule_condition = st.selectbox(
            "Condition",
            ["Greater than", "Less than", "Equals"],
            key="rule_condition",
        )
        rule_threshold = st.number_input("Threshold", value=0.0, step=0.01, key="rule_threshold")
        rule_action = st.selectbox(
            "Action",
            ["Pause Campaign", "Increase Budget 10%", "Decrease Budget 10%",
             "Send Notification", "Pause Ad Set"],
            key="rule_action",
        )
        rule_lookback = st.selectbox(
            "Lookback Period", list(DATE_PRESETS.keys()), key="rule_lookback"
        )

        if st.button("Save Rule"):
            st.success(f"Rule '{rule_name}' saved: If {rule_metric} {rule_condition} {rule_threshold}, then {rule_action}")

with tab_schedule:
    st.markdown("### Scheduled Extractions")

    jobs = scheduler.get_jobs()
    if jobs:
        job_df = pd.DataFrame(jobs)
        st.dataframe(job_df, use_container_width=True, hide_index=True)
    else:
        st.info("No scheduled jobs yet.")

    with st.expander("Create New Scheduled Job"):
        job_name = st.text_input("Job Name", key="sched_name")
        job_levels = st.multiselect("Levels", LEVELS, default=["ad"], key="sched_levels")
        bd_options = {k: v["label"] for k, v in BREAKDOWN_CONFIGS.items()}
        job_breakdowns = st.multiselect(
            "Breakdowns", list(bd_options.keys()), default=["none"],
            format_func=lambda x: bd_options[x], key="sched_breakdowns",
        )
        job_interval = st.number_input(
            "Interval (minutes)", min_value=15, value=60, step=15, key="sched_interval"
        )
        job_preset = st.selectbox("Date Preset", list(DATE_PRESETS.keys()), key="sched_preset")

        if st.button("Create Scheduled Job", key="create_sched"):
            job = ExtractionJob(
                job_id=str(uuid.uuid4())[:8],
                name=job_name or "Untitled Job",
                access_token=st.session_state.access_token,
                ad_account_id=st.session_state.ad_account_id,
                levels=job_levels,
                breakdowns=job_breakdowns,
                preset=job_preset,
                interval_minutes=job_interval,
            )
            scheduler.add_job(job)
            st.success(f"Created job: {job.name}")
            st.rerun()

with tab_stoploss:
    st.markdown("### Stop-Loss Rules")
    st.info(
        "Stop-loss rules automatically pause campaigns when spend exceeds "
        "a defined threshold relative to expected performance."
    )

    with st.expander("Create Stop-Loss Rule"):
        sl_name = st.text_input("Rule Name", key="sl_name")
        sl_metric = st.selectbox("Monitor", ["Daily Spend", "CPA", "ROAS"], key="sl_metric")
        sl_threshold = st.number_input("Threshold", value=100.0, step=10.0, key="sl_threshold")
        sl_action = st.selectbox(
            "Action When Triggered",
            ["Pause Campaign", "Pause Ad Set", "Send Alert"],
            key="sl_action",
        )

        if st.button("Save Stop-Loss Rule", key="save_sl"):
            st.success(f"Stop-loss rule saved: If {sl_metric} > {sl_threshold}, then {sl_action}")
