"""
Ad Set Manager — Full CRUD for ad sets with targeting, budgets, optimization goals.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import json

from src.meta_api import MetaAPIManager
from src.helpers import format_currency, safe_float, safe_int
from src.meta_catalog import CAMPAIGN_OBJECTIVES, BID_STRATEGIES, ADSET_STATUSES

st.set_page_config(page_title="Ad Sets", page_icon="📋", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Ad Set Manager")

api = get_api()

OPTIMIZATION_GOALS = [
    "NONE", "APP_INSTALLS", "AD_RECALL_LIFT", "ENGAGED_USERS",
    "EVENT_RESPONSES", "IMPRESSIONS", "LEAD_GENERATION", "QUALITY_LEAD",
    "LINK_CLICKS", "OFFSITE_CONVERSIONS", "PAGE_LIKES", "POST_ENGAGEMENT",
    "QUALITY_CALL", "REACH", "LANDING_PAGE_VIEWS", "VISIT_INSTAGRAM_PROFILE",
    "VALUE", "THRUPLAY", "DERIVED_EVENTS", "APP_INSTALLS_AND_OFFSITE_CONVERSIONS",
    "CONVERSATIONS", "IN_APP_VALUE", "MESSAGING_PURCHASE_CONVERSION",
    "SUBSCRIBERS", "REMINDERS_SET", "MEANINGFUL_CALL_ATTEMPT",
]

BILLING_EVENTS = [
    "IMPRESSIONS", "LINK_CLICKS", "POST_ENGAGEMENT", "PAGE_LIKES",
    "OFFER_CLAIMS", "THRUPLAY", "LISTING_INTERACTION",
]

tab_list, tab_create, tab_targeting, tab_schedule = st.tabs([
    "All Ad Sets", "Create Ad Set", "Targeting Builder", "Schedule & Dayparting",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: LIST ALL AD SETS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_list:
    st.markdown('<div class="section-title">All Ad Sets</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        campaign_filter = st.text_input("Filter by Campaign ID (optional)", key="as_camp_filter")
    with col_f2:
        status_filter = st.multiselect(
            "Status", ADSET_STATUSES, default=["ACTIVE", "PAUSED"], key="as_status",
        )
    with col_f3:
        st.write("")
        st.write("")
        st.button("Refresh", use_container_width=True, key="as_refresh")

    try:
        with st.spinner("Loading ad sets..."):
            adsets = api.get_adsets(
                campaign_id=campaign_filter if campaign_filter else None,
                status_filter=status_filter if status_filter else None,
            )

        if adsets:
            rows = []
            for a in adsets:
                daily_b = safe_float(a.get("daily_budget", 0)) / 100
                lifetime_b = safe_float(a.get("lifetime_budget", 0)) / 100
                rows.append({
                    "ID": a.get("id", ""),
                    "Name": a.get("name", ""),
                    "Status": a.get("effective_status", a.get("status", "")),
                    "Campaign ID": a.get("campaign_id", ""),
                    "Daily Budget": format_currency(daily_b) if daily_b else "-",
                    "Lifetime Budget": format_currency(lifetime_b) if lifetime_b else "-",
                    "Optimization": a.get("optimization_goal", ""),
                    "Bid Strategy": a.get("bid_strategy", ""),
                    "Start": (a.get("start_time") or "")[:10],
                    "End": (a.get("end_time") or "")[:10],
                })

            df = pd.DataFrame(rows)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Ad Sets", len(df))
            c2.metric("Active", len(df[df["Status"] == "ACTIVE"]))
            c3.metric("Paused", len(df[df["Status"] == "PAUSED"]))

            st.dataframe(df, use_container_width=True, hide_index=True, height=400)

            # Inline actions
            st.markdown("---")
            selected_adsets = st.multiselect(
                "Select ad sets for action",
                options=[a["id"] for a in adsets],
                format_func=lambda x: next(
                    (f"{a.get('name', '')} ({a['id']})" for a in adsets if a["id"] == x), x
                ),
                key="as_action_select",
            )

            if selected_adsets:
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                with col_a1:
                    if st.button("Activate", type="primary", use_container_width=True, key="as_activate"):
                        results = api.batch_update_status(selected_adsets, "ACTIVE")
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                with col_a2:
                    if st.button("Pause", use_container_width=True, key="as_pause"):
                        results = api.batch_update_status(selected_adsets, "PAUSED")
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                with col_a3:
                    if st.button("Duplicate", use_container_width=True, key="as_dup"):
                        for aid in selected_adsets:
                            try:
                                api.duplicate_adset(aid)
                                st.success(f"Duplicated {aid}")
                            except Exception as e:
                                st.error(f"Failed {aid}: {e}")
                with col_a4:
                    if st.button("Delete", use_container_width=True, key="as_del"):
                        for aid in selected_adsets:
                            try:
                                api.delete_adset(aid)
                                st.warning(f"Deleted {aid}")
                            except Exception as e:
                                st.error(f"Failed {aid}: {e}")
        else:
            st.info("No ad sets found.")
    except Exception as e:
        st.error(f"Failed to load ad sets: {str(e)[:300]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: CREATE AD SET
# ═══════════════════════════════════════════════════════════════════════════════

with tab_create:
    st.markdown('<div class="section-title">Create New Ad Set</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        as_campaign_id = st.text_input("Campaign ID *", key="asc_camp_id")
        as_name = st.text_input("Ad Set Name *", key="asc_name")
        as_opt_goal = st.selectbox("Optimization Goal *", OPTIMIZATION_GOALS, index=9, key="asc_opt")
        as_billing = st.selectbox("Billing Event *", BILLING_EVENTS, index=0, key="asc_billing")

    with col_c2:
        as_budget = st.number_input("Daily Budget ($) *", min_value=1.0, value=20.0, step=5.0, key="asc_budget")
        as_bid_strategy = st.selectbox("Bid Strategy", list(BID_STRATEGIES.keys()), key="asc_bid")
        as_status = st.selectbox("Initial Status", ["PAUSED", "ACTIVE"], key="asc_status")
        as_start = st.date_input("Start Date", key="asc_start")
        as_end = st.date_input("End Date (optional)", value=None, key="asc_end")

    st.markdown("### Targeting")
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        age_min = st.slider("Min Age", 13, 65, 18, key="asc_age_min")
        age_max = st.slider("Max Age", 13, 65, 65, key="asc_age_max")
    with col_t2:
        genders = st.multiselect("Genders", ["All", "Male", "Female"], default=["All"], key="asc_gender")
    with col_t3:
        countries = st.text_input("Countries (comma-separated codes)", value="US", key="asc_countries")

    targeting = {
        "age_min": age_min,
        "age_max": age_max,
        "geo_locations": {
            "countries": [c.strip().upper() for c in countries.split(",") if c.strip()],
        },
    }
    gender_map = {"Male": 1, "Female": 2}
    if "All" not in genders and genders:
        targeting["genders"] = [gender_map[g] for g in genders if g in gender_map]

    interests_text = st.text_area(
        "Interests (JSON array, e.g. [{\"id\": \"123\", \"name\": \"Fitness\"}])",
        key="asc_interests",
    )
    if interests_text:
        try:
            interests = json.loads(interests_text)
            targeting["flexible_spec"] = [{"interests": interests}]
        except json.JSONDecodeError:
            st.warning("Invalid JSON for interests")

    st.json(targeting)

    if st.button("Create Ad Set", type="primary", use_container_width=True, key="asc_create"):
        if not as_campaign_id or not as_name:
            st.error("Campaign ID and Ad Set name are required.")
        else:
            try:
                result = api.create_adset(
                    campaign_id=as_campaign_id,
                    name=as_name,
                    daily_budget=as_budget,
                    optimization_goal=as_opt_goal,
                    billing_event=as_billing,
                    targeting=targeting,
                    status=as_status,
                    bid_strategy=BID_STRATEGIES.get(as_bid_strategy),
                    start_time=as_start.isoformat() if as_start else None,
                    end_time=as_end.isoformat() if as_end else None,
                )
                st.success(f"Ad Set created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: TARGETING BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_targeting:
    st.markdown('<div class="section-title">Targeting Builder & Reach Estimator</div>', unsafe_allow_html=True)

    st.markdown("Build and test targeting specs before applying them to ad sets.")

    col_tb1, col_tb2 = st.columns(2)
    with col_tb1:
        tb_age_min = st.slider("Min Age", 13, 65, 18, key="tb_age_min")
        tb_age_max = st.slider("Max Age", 13, 65, 55, key="tb_age_max")
        tb_countries = st.text_input("Countries", value="US", key="tb_countries")
        tb_genders = st.multiselect("Genders", ["All", "Male", "Female"], default=["All"], key="tb_gender")

    with col_tb2:
        interest_search = st.text_input("Search interests", key="tb_interest_search")
        if interest_search and st.button("Search", key="tb_search_btn"):
            try:
                results = api.get_targeting_search(interest_search)
                if results:
                    for r in results[:15]:
                        audience = r.get('audience_size', 'N/A')
                        audience_str = f"{audience:,}" if isinstance(audience, (int, float)) else str(audience)
                        st.write(f"- **{r.get('name', '')}** (ID: {r.get('id', '')}, audience: {audience_str})")
                else:
                    st.info("No results found.")
            except Exception as e:
                st.error(f"Search failed: {e}")

    tb_targeting = {
        "age_min": tb_age_min,
        "age_max": tb_age_max,
        "geo_locations": {
            "countries": [c.strip().upper() for c in tb_countries.split(",") if c.strip()],
        },
    }
    if "All" not in tb_genders and tb_genders:
        tb_targeting["genders"] = [{"Male": 1, "Female": 2}[g] for g in tb_genders if g in {"Male", "Female"}]

    st.json(tb_targeting)

    if st.button("Estimate Reach", type="primary", key="tb_estimate"):
        try:
            est = api.estimate_reach(tb_targeting)
            data = est.get("data", {})
            users = data.get("users", data.get("estimate_ready", 0))
            st.success(f"Estimated daily reach: {users:,}" if isinstance(users, int) else f"Reach estimate: {users}")
        except Exception as e:
            st.error(f"Estimate failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SCHEDULE & DAYPARTING
# ═══════════════════════════════════════════════════════════════════════════════

with tab_schedule:
    st.markdown('<div class="section-title">Schedule & Dayparting</div>', unsafe_allow_html=True)

    st.markdown("""
    Configure ad scheduling (dayparting) to run ads only during specific hours.
    Format: 48 entries (0-47) representing half-hour blocks starting at midnight.
    Value 1 = active, 0 = inactive.
    """)

    st.markdown("### Visual Schedule Builder")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(24))

    schedule_data = {}
    for day in days:
        schedule_data[day] = st.multiselect(
            day, hours,
            default=list(range(6, 23)),
            key=f"dp_{day}",
        )

    st.markdown("### Schedule Preview")
    preview_rows = []
    for day in days:
        active_hours = schedule_data[day]
        preview_rows.append({
            "Day": day,
            "Active Hours": f"{min(active_hours)}:00 - {max(active_hours)}:00" if active_hours else "Off",
            "Hours Active": len(active_hours),
        })
    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    adset_for_schedule = st.text_input("Ad Set ID to apply schedule", key="dp_adset_id")
    if adset_for_schedule and st.button("Apply Schedule", type="primary", key="dp_apply"):
        st.info("Dayparting schedule would be applied via pacing_type and adset_schedule parameters.")
        st.warning("Note: Dayparting requires lifetime budget on the ad set.")
