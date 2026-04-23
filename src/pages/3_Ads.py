"""
Ads Page — Individual ad management and creative preview.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.extractor import MetaAdsExtractor
from src.helpers import ads_to_dataframe

st.set_page_config(page_title="Ads", page_icon="📱", layout="wide")

if not st.session_state.get("connected", False):
    st.warning("Please connect to Meta API first.")
    st.stop()

st.markdown("# Ad Management")

ext = MetaAdsExtractor(
    st.session_state.access_token,
    st.session_state.ad_account_id,
)

tab_list, tab_create, tab_insights = st.tabs([
    "All Ads", "Create Ad", "Ad Performance",
])

with tab_list:
    st.markdown("### All Ads")
    try:
        with st.spinner("Loading ads..."):
            ads = ext.get_ads()
        if ads:
            df = ads_to_dataframe(ads)

            search = st.text_input("Search ads...", key="ad_search")
            if search:
                df = df[df["Name"].str.contains(search, case=False, na=False)]

            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"Showing {len(df)} ads")
        else:
            st.info("No ads found.")
    except Exception as e:
        st.error(f"Failed to load ads: {str(e)[:200]}")

with tab_create:
    st.markdown("### Create New Ad")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        ad_name = st.text_input("Ad Name *", key="new_ad_name")
        ad_status = st.selectbox("Initial Status", ["PAUSED", "ACTIVE"], key="new_ad_status")
    with col_c2:
        primary_text = st.text_area("Primary Text", height=100, key="new_ad_text")
        headline = st.text_input("Headline", key="new_ad_headline")
        cta = st.selectbox(
            "Call to Action",
            ["LEARN_MORE", "SHOP_NOW", "SIGN_UP", "DOWNLOAD",
             "CONTACT_US", "GET_OFFER", "ORDER_NOW"],
            key="new_ad_cta",
        )

    if st.button("Create Ad", type="primary"):
        st.warning("Ad creation via API requires write permissions and a creative.")

with tab_insights:
    st.markdown("### Ad Performance")
    if st.button("Fetch Ad Insights", key="fetch_ad_insights"):
        with st.spinner("Fetching..."):
            df = ext.fetch_insights(level="ad", breakdown_key="none")
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No insights data returned")
