"""
Audience Manager — Custom audiences, lookalike audiences, saved audiences,
targeting browser, and reach estimation. Full replacement for Meta Ads Manager audience tools.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import json

from src.meta_api import MetaAPIManager
from src.helpers import format_number

st.set_page_config(page_title="Audiences", page_icon="👥", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .audience-card { background: white; border-radius: 8px; padding: 16px; margin: 8px 0;
        border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Audience Manager")
st.markdown("Create and manage custom audiences, lookalikes, and saved audiences.")

api = get_api()

tab_custom, tab_lookalike, tab_saved, tab_browse, tab_overlap = st.tabs([
    "Custom Audiences", "Lookalike Audiences", "Saved Audiences",
    "Interest Browser", "Audience Overlap",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: CUSTOM AUDIENCES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_custom:
    st.markdown('<div class="section-title">Custom Audiences</div>', unsafe_allow_html=True)

    if st.button("Load Custom Audiences", key="ca_load"):
        try:
            audiences = api.get_custom_audiences()
            if audiences:
                rows = []
                for a in audiences:
                    rows.append({
                        "ID": a.get("id", ""),
                        "Name": a.get("name", ""),
                        "Subtype": a.get("subtype", ""),
                        "Approx. Size": format_number(a.get("approximate_count", 0)),
                        "Delivery Status": str(a.get("delivery_status", {}).get("status", "")) if isinstance(a.get("delivery_status"), dict) else "",
                        "Created": (a.get("time_created") or "")[:10],
                        "Updated": (a.get("time_updated") or "")[:10],
                    })
                df = pd.DataFrame(rows)

                c1, c2 = st.columns(2)
                c1.metric("Total Audiences", len(df))
                c2.metric("Total Reach", format_number(
                    sum(a.get("approximate_count", 0) for a in audiences)
                ))

                st.dataframe(df, use_container_width=True, hide_index=True, height=400)
            else:
                st.info("No custom audiences found.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown('<div class="section-title">Create Custom Audience</div>', unsafe_allow_html=True)

    AUDIENCE_SUBTYPES = [
        "CUSTOM", "WEBSITE", "APP", "OFFLINE_CONVERSION",
        "ENGAGEMENT", "VIDEO", "IG_BUSINESS", "LEAD_GEN_FORM",
        "FB_EVENT", "PAGE", "SHOPPING", "STORE_VISIT",
    ]

    CUSTOMER_FILE_SOURCES = [
        "USER_PROVIDED_ONLY", "PARTNER_PROVIDED_ONLY", "BOTH_USER_AND_PARTNER_PROVIDED",
    ]

    col_ca1, col_ca2 = st.columns(2)
    with col_ca1:
        ca_name = st.text_input("Audience Name *", key="ca_name")
        ca_desc = st.text_area("Description", key="ca_desc")
    with col_ca2:
        ca_subtype = st.selectbox("Audience Type", AUDIENCE_SUBTYPES, key="ca_subtype")
        ca_source = st.selectbox("Data Source", CUSTOMER_FILE_SOURCES, key="ca_source")
        ca_retention = st.number_input("Retention Days", min_value=1, max_value=365, value=30, key="ca_retention")

    if ca_subtype == "WEBSITE":
        st.markdown("### Website Audience Rules")
        st.markdown("Configure pixel-based audience rules")
        rule_url = st.text_input("URL Contains", key="ca_rule_url")
        rule_days = st.number_input("Within last N days", min_value=1, max_value=180, value=30, key="ca_rule_days")

    if ca_subtype == "ENGAGEMENT":
        st.markdown("### Engagement Rules")
        eng_type = st.selectbox(
            "Engagement Type",
            ["page", "ig_business", "video", "lead_gen_form", "canvas"],
            key="ca_eng_type",
        )

    if st.button("Create Custom Audience", type="primary", use_container_width=True, key="ca_create"):
        if not ca_name:
            st.error("Audience name is required.")
        else:
            try:
                result = api.create_custom_audience(
                    name=ca_name,
                    description=ca_desc,
                    subtype=ca_subtype,
                    customer_file_source=ca_source if ca_subtype == "CUSTOM" else None,
                )
                st.success(f"Audience created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed: {e}")

    # Upload customer list
    st.markdown("---")
    st.markdown("### Upload Customer List")
    st.markdown("Upload a CSV with customer data (emails, phone numbers, etc.) to populate a custom audience.")
    customer_csv = st.file_uploader("Customer list CSV", type=["csv"], key="ca_customer_csv")
    if customer_csv:
        cust_df = pd.read_csv(customer_csv)
        st.dataframe(cust_df.head(10), use_container_width=True, hide_index=True)
        st.info(f"Loaded {len(cust_df)} records. Columns: {', '.join(cust_df.columns)}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LOOKALIKE AUDIENCES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_lookalike:
    st.markdown('<div class="section-title">Lookalike Audiences</div>', unsafe_allow_html=True)

    st.markdown("""
    Create lookalike audiences based on your best-performing custom audiences.
    The lookalike ratio determines the audience size (1% = most similar, 10% = largest).
    """)

    col_la1, col_la2 = st.columns(2)
    with col_la1:
        la_name = st.text_input("Lookalike Name *", key="la_name")
        la_source_id = st.text_input("Source Audience ID *", key="la_source_id")
    with col_la2:
        la_country = st.text_input("Target Country Code *", value="US", key="la_country")
        la_ratio = st.slider(
            "Lookalike Ratio (%)", min_value=1, max_value=10, value=1,
            help="1% = most similar to source, 10% = broadest reach",
            key="la_ratio",
        )

    st.markdown(f"**Estimated audience:** {la_ratio}% of {la_country} population")

    if st.button("Create Lookalike", type="primary", use_container_width=True, key="la_create"):
        if not la_name or not la_source_id or not la_country:
            st.error("All fields are required.")
        else:
            try:
                result = api.create_lookalike_audience(
                    name=la_name,
                    origin_audience_id=la_source_id,
                    country=la_country.upper(),
                    ratio=la_ratio / 100.0,
                )
                st.success(f"Lookalike created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed: {e}")

    # Multi-country lookalikes
    st.markdown("---")
    st.markdown("### Multi-Country Lookalikes")
    la_multi_countries = st.text_input(
        "Countries (comma-separated)", value="US,GB,CA,AU", key="la_multi_countries",
    )
    la_multi_ratio = st.slider("Ratio (%)", 1, 10, 1, key="la_multi_ratio")
    la_multi_source = st.text_input("Source Audience ID", key="la_multi_source")

    if st.button("Create All Lookalikes", type="primary", key="la_multi_create"):
        countries = [c.strip().upper() for c in la_multi_countries.split(",") if c.strip()]
        for country in countries:
            try:
                result = api.create_lookalike_audience(
                    name=f"LAL {la_multi_ratio}% - {country} - {la_multi_source[:8]}",
                    origin_audience_id=la_multi_source,
                    country=country,
                    ratio=la_multi_ratio / 100.0,
                )
                st.success(f"{country}: Created (ID: {result.get('id', '')})")
            except Exception as e:
                st.error(f"{country}: Failed - {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: SAVED AUDIENCES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_saved:
    st.markdown('<div class="section-title">Saved Audiences</div>', unsafe_allow_html=True)

    if st.button("Load Saved Audiences", key="sa_load"):
        try:
            saved = api.get_saved_audiences()
            if saved:
                rows = []
                for a in saved:
                    rows.append({
                        "ID": a.get("id", ""),
                        "Name": a.get("name", ""),
                        "Approx. Size": format_number(a.get("approximate_count", 0)),
                        "Status": a.get("run_status", ""),
                        "Created": (a.get("time_created") or "")[:10],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No saved audiences found.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("### Create Saved Audience")

    col_sa1, col_sa2, col_sa3 = st.columns(3)
    with col_sa1:
        sa_name = st.text_input("Audience Name *", key="sa_name")
        sa_age_min = st.slider("Min Age", 13, 65, 18, key="sa_age_min")
        sa_age_max = st.slider("Max Age", 13, 65, 65, key="sa_age_max")
    with col_sa2:
        sa_genders = st.multiselect("Genders", ["All", "Male", "Female"], default=["All"], key="sa_genders")
        sa_countries = st.text_input("Countries", value="US", key="sa_countries")
    with col_sa3:
        sa_interests_search = st.text_input("Search for interests", key="sa_int_search")
        if sa_interests_search and st.button("Search", key="sa_int_btn"):
            try:
                results = api.get_targeting_search(sa_interests_search)
                for r in results[:10]:
                    st.write(f"- {r.get('name', '')} (ID: {r.get('id', '')})")
            except Exception as e:
                st.error(f"Search failed: {e}")

    sa_targeting = {
        "age_min": sa_age_min,
        "age_max": sa_age_max,
        "geo_locations": {
            "countries": [c.strip().upper() for c in sa_countries.split(",") if c.strip()],
        },
    }
    if "All" not in sa_genders and sa_genders:
        sa_targeting["genders"] = [{"Male": 1, "Female": 2}[g] for g in sa_genders if g in {"Male", "Female"}]

    st.json(sa_targeting)

    if st.button("Save Audience", type="primary", use_container_width=True, key="sa_create"):
        if not sa_name:
            st.error("Name is required.")
        else:
            try:
                result = api.create_saved_audience(sa_name, sa_targeting)
                st.success(f"Saved audience created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: INTEREST BROWSER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_browse:
    st.markdown('<div class="section-title">Interest & Behavior Browser</div>', unsafe_allow_html=True)

    search_types = {
        "Interests": "adinterest",
        "Behaviors": "adbehavior",
        "Demographics": "addemographic",
        "Employers": "adworkemployer",
        "Job Titles": "adworkposition",
        "Education Schools": "adeducationschool",
        "Education Majors": "adeducationmajor",
    }

    col_br1, col_br2 = st.columns([3, 2])
    with col_br1:
        browse_query = st.text_input("Search query", key="br_query")
    with col_br2:
        browse_type = st.selectbox("Category", list(search_types.keys()), key="br_type")

    if browse_query and st.button("Search", type="primary", key="br_search"):
        try:
            results = api.get_targeting_search(browse_query, search_types[browse_type])
            if results:
                rows = []
                for r in results:
                    rows.append({
                        "ID": r.get("id", ""),
                        "Name": r.get("name", ""),
                        "Type": r.get("type", ""),
                        "Path": " > ".join(r.get("path", [])),
                        "Audience Size": format_number(r.get("audience_size", 0)),
                        "Description": r.get("description", ""),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # Copy-paste JSON for targeting
                st.markdown("### Targeting JSON")
                selected_interests = [{"id": r.get("id"), "name": r.get("name")} for r in results[:5]]
                st.code(json.dumps(selected_interests, indent=2), language="json")
            else:
                st.info("No results found.")
        except Exception as e:
            st.error(f"Search failed: {e}")

    st.markdown("---")
    st.markdown("### Browse Categories")
    if st.button("Load Targeting Categories", key="br_browse"):
        try:
            categories = api.get_targeting_browse()
            if categories:
                for cat in categories[:50]:
                    st.write(f"- **{cat.get('name', '')}** ({cat.get('type', '')})")
            else:
                st.info("No categories available.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: AUDIENCE OVERLAP
# ═══════════════════════════════════════════════════════════════════════════════

with tab_overlap:
    st.markdown('<div class="section-title">Audience Overlap Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    Compare audiences to identify overlap. High overlap between ad sets
    means you're competing against yourself in the auction.
    """)

    col_ov1, col_ov2 = st.columns(2)
    with col_ov1:
        ov_audience_1 = st.text_input("Audience ID 1", key="ov_a1")
    with col_ov2:
        ov_audience_2 = st.text_input("Audience ID 2", key="ov_a2")

    if ov_audience_1 and ov_audience_2:
        if st.button("Check Overlap", type="primary", key="ov_check"):
            st.info(
                "Audience overlap analysis requires the Audience Insights API. "
                "Use the Meta Business Suite for visual overlap analysis, or compare "
                "targeting specs side-by-side below."
            )

    st.markdown("---")
    st.markdown("### Reach Estimator")
    st.markdown("Test targeting combinations to estimate reach before creating ad sets.")

    col_re1, col_re2, col_re3 = st.columns(3)
    with col_re1:
        re_countries = st.text_input("Countries", value="US", key="re_countries")
        re_age_min = st.slider("Min Age", 13, 65, 25, key="re_age_min")
        re_age_max = st.slider("Max Age", 13, 65, 45, key="re_age_max")
    with col_re2:
        re_genders = st.multiselect("Genders", ["All", "Male", "Female"], default=["All"], key="re_genders")
    with col_re3:
        re_opt = st.selectbox(
            "Optimization Goal",
            ["LINK_CLICKS", "IMPRESSIONS", "REACH", "OFFSITE_CONVERSIONS", "LANDING_PAGE_VIEWS"],
            key="re_opt",
        )

    re_targeting = {
        "age_min": re_age_min,
        "age_max": re_age_max,
        "geo_locations": {
            "countries": [c.strip().upper() for c in re_countries.split(",") if c.strip()],
        },
    }
    if "All" not in re_genders and re_genders:
        re_targeting["genders"] = [{"Male": 1, "Female": 2}[g] for g in re_genders if g in {"Male", "Female"}]

    if st.button("Estimate Reach", type="primary", key="re_estimate"):
        try:
            est = api.estimate_reach(re_targeting, re_opt)
            data = est.get("data", est)
            if isinstance(data, dict):
                users_lower = data.get("users_lower_bound", data.get("users", "N/A"))
                users_upper = data.get("users_upper_bound", "N/A")
                st.success(f"Estimated reach: {format_number(users_lower)} - {format_number(users_upper)}")
            else:
                st.json(est)
        except Exception as e:
            st.error(f"Estimation failed: {e}")
