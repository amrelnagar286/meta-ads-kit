"""
Bulk Operations Page — CSV-based bulk create, update, pause, delete.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bulk Operations", page_icon="🔧", layout="wide")

if not st.session_state.get("connected", False):
    st.warning("Please connect to Meta API first.")
    st.stop()

st.markdown("# Bulk Operations")

tab_upload, tab_templates, tab_history = st.tabs([
    "Upload & Execute", "Download Templates", "History",
])

with tab_upload:
    st.markdown("### Bulk Upload")

    operation = st.selectbox(
        "Operation Type",
        ["Pause Campaigns", "Activate Campaigns", "Update Budgets",
         "Create Campaigns", "Delete Campaigns",
         "Pause Ad Sets", "Activate Ad Sets", "Update Ad Set Budgets"],
        key="bulk_operation",
    )

    st.markdown("---")
    uploaded = st.file_uploader("Upload CSV", type=["csv"], key="bulk_upload")

    if uploaded:
        df = pd.read_csv(uploaded)
        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.info(f"{len(df)} rows loaded")

        dry_run = st.checkbox("Dry Run (preview only)", value=True)

        if st.button("Execute Bulk Operation", type="primary"):
            if dry_run:
                st.info(
                    f"DRY RUN: Would {operation} on {len(df)} items. "
                    "Uncheck 'Dry Run' to execute."
                )
            else:
                st.warning("Bulk operations require write permissions to the Meta API.")
    else:
        st.info("Upload a CSV file to begin")

with tab_templates:
    st.markdown("### Download CSV Templates")

    templates = {
        "Campaign Template": pd.DataFrame({
            "campaign_id": [""],
            "campaign_name": [""],
            "objective": ["OUTCOME_SALES"],
            "status": ["PAUSED"],
            "daily_budget": [5000],
        }),
        "Ad Set Template": pd.DataFrame({
            "adset_id": [""],
            "adset_name": [""],
            "campaign_id": [""],
            "daily_budget": [2500],
            "optimization_goal": ["OFFSITE_CONVERSIONS"],
            "bid_strategy": ["LOWEST_COST_WITHOUT_CAP"],
            "status": ["PAUSED"],
        }),
        "Ad Template": pd.DataFrame({
            "ad_id": [""],
            "ad_name": [""],
            "adset_id": [""],
            "status": ["PAUSED"],
            "primary_text": [""],
            "headline": [""],
            "call_to_action": ["LEARN_MORE"],
        }),
    }

    for name, template_df in templates.items():
        st.markdown(f"#### {name}")
        st.dataframe(template_df, use_container_width=True, hide_index=True)
        csv_data = template_df.to_csv(index=False)
        st.download_button(
            f"Download {name}",
            csv_data,
            file_name=f"{name.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

with tab_history:
    st.markdown("### Operation History")
    st.info("Bulk operation history will appear here after execution.")
