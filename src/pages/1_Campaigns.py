"""
Campaigns Page — Full campaign management: list, create, insights, bulk actions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.extractor import MetaAdsExtractor
from src.helpers import campaigns_to_dataframe, format_currency, format_number, get_status_emoji
from src.meta_catalog import CAMPAIGN_OBJECTIVES, BID_STRATEGIES, CAMPAIGN_STATUSES

st.set_page_config(page_title="Campaigns", page_icon="📊", layout="wide")

if not st.session_state.get("connected", False):
    st.warning("Please connect to Meta API first from the main page.")
    st.stop()

st.markdown("# Campaign Management")

tab_list, tab_create, tab_insights, tab_bulk = st.tabs([
    "All Campaigns", "Create Campaign", "Campaign Insights", "Bulk Actions",
])

ext = MetaAdsExtractor(
    st.session_state.access_token,
    st.session_state.ad_account_id,
)

# TAB 1: LIST
with tab_list:
    st.markdown("### All Campaigns")

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        status_filter = st.multiselect(
            "Filter by Status", CAMPAIGN_STATUSES,
            default=["ACTIVE", "PAUSED"], key="camp_status_filter",
        )
    with col_f2:
        objective_filter = st.multiselect(
            "Filter by Objective", list(CAMPAIGN_OBJECTIVES.values()),
            default=[], key="camp_obj_filter",
        )
    with col_f3:
        if st.button("Refresh", use_container_width=True, key="camp_refresh"):
            st.rerun()

    try:
        with st.spinner("Loading campaigns..."):
            campaigns = ext.get_campaigns()
        if campaigns:
            df = campaigns_to_dataframe(campaigns)
            if status_filter:
                df = df[df["Status"].isin(status_filter)]
            if objective_filter:
                df = df[df["Objective"].isin(objective_filter)]

            search = st.text_input("Search campaigns...", key="camp_search")
            if search:
                df = df[df["Name"].str.contains(search, case=False, na=False)]

            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"Showing {len(df)} campaigns")

            st.markdown("### Campaign Actions")
            selected_ids = st.multiselect(
                "Select campaigns",
                options=[c["id"] for c in campaigns],
                format_func=lambda x: next(
                    (c["name"] for c in campaigns if c["id"] == x), x
                ),
                key="camp_select_action",
            )
            if selected_ids:
                st.info(f"Selected {len(selected_ids)} campaigns")
        else:
            st.info("No campaigns found.")
    except Exception as e:
        st.error(f"Failed to load campaigns: {str(e)[:200]}")

# TAB 2: CREATE
with tab_create:
    st.markdown("### Create New Campaign")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        camp_name = st.text_input("Campaign Name *", key="new_camp_name")
        camp_objective = st.selectbox(
            "Objective *", list(CAMPAIGN_OBJECTIVES.keys()), key="new_camp_obj"
        )
        camp_status = st.selectbox(
            "Initial Status", ["PAUSED", "ACTIVE"], key="new_camp_status"
        )
    with col_c2:
        budget_type = st.radio("Budget Type", ["Daily", "Lifetime"], horizontal=True)
        budget_amount = st.number_input("Budget ($)", min_value=1.0, value=50.0, step=5.0)
        bid_strategy = st.selectbox(
            "Bid Strategy", list(BID_STRATEGIES.keys()), key="new_camp_bid"
        )

    if st.button("Create Campaign", type="primary"):
        st.info(
            f"Campaign creation: {camp_name} | "
            f"Objective: {CAMPAIGN_OBJECTIVES[camp_objective]} | "
            f"Budget: ${budget_amount:.2f} ({budget_type}) | "
            f"Bid: {BID_STRATEGIES[bid_strategy]}"
        )
        st.warning("Campaign creation via API requires write permissions.")

# TAB 3: INSIGHTS
with tab_insights:
    st.markdown("### Campaign Insights")
    try:
        campaigns = ext.get_campaigns()
        if campaigns:
            camp_map = {c["id"]: c.get("name", c["id"]) for c in campaigns}
            selected_camp = st.selectbox(
                "Select Campaign",
                options=list(camp_map.keys()),
                format_func=lambda x: camp_map[x],
                key="insights_camp_select",
            )
            if st.button("Fetch Insights", key="fetch_camp_insights"):
                with st.spinner("Fetching..."):
                    df = ext.fetch_insights(
                        level="campaign",
                        breakdown_key="none",
                        campaign_ids=[selected_camp],
                    )
                    if not df.empty:
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No insights data returned")
    except Exception as e:
        st.error(f"Error: {str(e)[:200]}")

# TAB 4: BULK
with tab_bulk:
    st.markdown("### Bulk Campaign Actions")
    st.info("Upload a CSV with campaign IDs and desired actions.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"], key="camp_bulk_upload")
    if uploaded:
        df = pd.read_csv(uploaded)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.warning("Bulk actions require write permissions to the Meta API.")
