"""
Ad Sets Page — Ad set management: list, create, performance insights.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.extractor import MetaAdsExtractor
from src.helpers import adsets_to_dataframe, format_currency
from src.meta_catalog import ADSET_STATUSES, BID_STRATEGIES

st.set_page_config(page_title="Ad Sets", page_icon="📦", layout="wide")

if not st.session_state.get("connected", False):
    st.warning("Please connect to Meta API first.")
    st.stop()

st.markdown("# Ad Set Management")

ext = MetaAdsExtractor(
    st.session_state.access_token,
    st.session_state.ad_account_id,
)

tab_list, tab_create, tab_insights = st.tabs([
    "All Ad Sets", "Create Ad Set", "Performance",
])

with tab_list:
    st.markdown("### All Ad Sets")
    try:
        with st.spinner("Loading ad sets..."):
            adsets = ext.get_adsets()
        if adsets:
            df = adsets_to_dataframe(adsets)

            search = st.text_input("Search ad sets...", key="adset_search")
            if search:
                df = df[df["Name"].str.contains(search, case=False, na=False)]

            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"Showing {len(df)} ad sets")

            st.markdown("### Bulk Actions")
            selected_ids = st.multiselect(
                "Select ad sets",
                options=[a.get("id", "") for a in adsets],
                format_func=lambda x: next(
                    (f"{a['name']} ({a['id']})" for a in adsets if a.get("id") == x), x
                ),
                key="adset_select_action",
            )
            if selected_ids:
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    new_budget = st.number_input(
                        "Set Daily Budget ($)", min_value=0.0, step=1.0, key="bulk_budget_adset"
                    )
                with col_a2:
                    st.info(f"Selected {len(selected_ids)} ad sets")
        else:
            st.info("No ad sets found.")
    except Exception as e:
        st.error(f"Failed to load ad sets: {str(e)[:200]}")

with tab_create:
    st.markdown("### Create New Ad Set")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        adset_name = st.text_input("Ad Set Name *", key="new_adset_name")
        optimization_goal = st.selectbox(
            "Optimization Goal",
            ["REACH", "LINK_CLICKS", "OFFSITE_CONVERSIONS", "LANDING_PAGE_VIEWS",
             "IMPRESSIONS", "LEAD_GENERATION", "APP_INSTALLS"],
            key="new_adset_opt",
        )
    with col_f2:
        budget_type = st.radio("Budget Type", ["Daily", "Lifetime"], horizontal=True, key="adset_budget_type")
        budget_amount = st.number_input("Budget ($)", min_value=1.0, value=25.0, step=5.0, key="adset_budget")
        bid_strategy = st.selectbox("Bid Strategy", list(BID_STRATEGIES.keys()), key="new_adset_bid")

    if st.button("Create Ad Set", type="primary"):
        st.warning("Ad set creation via API requires write permissions.")

with tab_insights:
    st.markdown("### Ad Set Performance")
    if st.button("Fetch Ad Set Insights", key="fetch_adset_insights"):
        with st.spinner("Fetching..."):
            df = ext.fetch_insights(level="adset", breakdown_key="none")
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No insights data returned")
