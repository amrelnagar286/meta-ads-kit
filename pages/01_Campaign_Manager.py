"""
Campaign Manager — Full Meta Ads Manager replacement for campaigns.
CRUD, duplicate, status control, insights, performance trends, quick actions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.meta_api import MetaAPIManager
from src.kpi_engine import compute_kpis
from src.helpers import (
    format_currency, format_number, format_percentage,
    safe_float, safe_int, safe_divide,
)
from src.meta_catalog import CAMPAIGN_OBJECTIVES, BID_STRATEGIES, CAMPAIGN_STATUSES

st.set_page_config(page_title="Campaign Manager", page_icon="📊", layout="wide")

# ─── Windows 11 Theme ─────────────────────────────────────────────────────────
st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap');
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .camp-card { background: white; border-radius: 8px; padding: 16px; margin: 4px;
        border: 1px solid #e0e0e0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .status-active { color: #107C10; font-weight: 600; }
    .status-paused { color: #FFB900; font-weight: 600; }
    .status-deleted { color: #D13438; font-weight: 600; }
    .action-bar { display: flex; gap: 8px; margin: 8px 0; }
    .metric-mini { font-size: 0.85rem; color: #555; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
</style>""", unsafe_allow_html=True)


def get_api() -> MetaAPIManager:
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


def get_status_color(status: str) -> str:
    s = status.upper()
    if s == "ACTIVE":
        return "#107C10"
    if s == "PAUSED":
        return "#FFB900"
    return "#D13438"


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Campaign Manager")
st.markdown("Full campaign lifecycle management — create, edit, monitor, optimize, duplicate.")

api = get_api()

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════

tab_all, tab_create, tab_insights, tab_compare, tab_bulk = st.tabs([
    "All Campaigns", "Create Campaign", "Deep Insights", "Compare", "Bulk Actions",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ALL CAMPAIGNS — Full listing with inline actions
# ═══════════════════════════════════════════════════════════════════════════════

with tab_all:
    st.markdown('<div class="section-title">Campaign Overview</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
    with col_f1:
        status_filter = st.multiselect(
            "Status Filter", CAMPAIGN_STATUSES,
            default=["ACTIVE", "PAUSED"], key="cm_status",
        )
    with col_f2:
        obj_filter = st.multiselect(
            "Objective Filter", list(CAMPAIGN_OBJECTIVES.keys()),
            default=[], key="cm_obj",
        )
    with col_f3:
        search = st.text_input("Search campaigns", key="cm_search")
    with col_f4:
        st.write("")
        st.write("")
        refresh = st.button("Refresh", use_container_width=True, key="cm_refresh")

    try:
        with st.spinner("Loading campaigns..."):
            campaigns = api.get_campaigns(status_filter=status_filter if status_filter else None)

        if campaigns:
            rows = []
            for c in campaigns:
                daily_b = safe_float(c.get("daily_budget", 0)) / 100
                lifetime_b = safe_float(c.get("lifetime_budget", 0)) / 100
                budget_remaining = safe_float(c.get("budget_remaining", 0)) / 100
                rows.append({
                    "ID": c.get("id", ""),
                    "Name": c.get("name", ""),
                    "Status": c.get("effective_status", c.get("status", "")),
                    "Objective": c.get("objective", ""),
                    "Daily Budget": format_currency(daily_b) if daily_b else "-",
                    "Lifetime Budget": format_currency(lifetime_b) if lifetime_b else "-",
                    "Budget Remaining": format_currency(budget_remaining) if budget_remaining else "-",
                    "Bid Strategy": c.get("bid_strategy", ""),
                    "Created": (c.get("created_time") or "")[:10],
                    "Updated": (c.get("updated_time") or "")[:10],
                })

            df = pd.DataFrame(rows)
            if obj_filter:
                api_objs = [CAMPAIGN_OBJECTIVES[o] for o in obj_filter]
                df = df[df["Objective"].isin(api_objs)]
            if search:
                df = df[df["Name"].str.contains(search, case=False, na=False)]

            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            active_count = len(df[df["Status"] == "ACTIVE"])
            paused_count = len(df[df["Status"] == "PAUSED"])
            c1.metric("Total Campaigns", len(df))
            c2.metric("Active", active_count)
            c3.metric("Paused", paused_count)
            c4.metric("Other", len(df) - active_count - paused_count)

            st.dataframe(df, use_container_width=True, hide_index=True, height=400)

            # ── Inline Campaign Actions ──
            st.markdown("---")
            st.markdown('<div class="section-title">Campaign Actions</div>', unsafe_allow_html=True)

            camp_options = {c["id"]: f"{c.get('name', '')} ({c['id']})" for c in campaigns}
            selected_camps = st.multiselect(
                "Select campaigns for action",
                options=list(camp_options.keys()),
                format_func=lambda x: camp_options.get(x, x),
                key="cm_select_action",
            )

            if selected_camps:
                col_a1, col_a2, col_a3, col_a4, col_a5 = st.columns(5)
                with col_a1:
                    if st.button("Activate", type="primary", use_container_width=True):
                        results = api.batch_update_status(selected_camps, "ACTIVE")
                        for r in results:
                            if r["status"] == "success":
                                st.success(f"Activated {r['id']}")
                            else:
                                st.error(f"Failed {r['id']}: {r['error']}")
                with col_a2:
                    if st.button("Pause", use_container_width=True):
                        results = api.batch_update_status(selected_camps, "PAUSED")
                        for r in results:
                            if r["status"] == "success":
                                st.info(f"Paused {r['id']}")
                            else:
                                st.error(f"Failed {r['id']}: {r['error']}")
                with col_a3:
                    if st.button("Duplicate", use_container_width=True):
                        for cid in selected_camps:
                            try:
                                result = api.duplicate_campaign(cid)
                                st.success(f"Duplicated {cid}")
                            except Exception as e:
                                st.error(f"Failed to duplicate {cid}: {e}")
                with col_a4:
                    if st.button("Delete", use_container_width=True):
                        for cid in selected_camps:
                            try:
                                api.delete_campaign(cid)
                                st.warning(f"Deleted {cid}")
                            except Exception as e:
                                st.error(f"Failed {cid}: {e}")
                with col_a5:
                    new_budget = st.number_input("New Daily Budget ($)", min_value=1.0, step=5.0, key="cm_budget_chg")
                    if st.button("Update Budget", use_container_width=True):
                        updates = [{"id": cid, "daily_budget": new_budget} for cid in selected_camps]
                        results = api.batch_update_budgets(updates)
                        for r in results:
                            st.info(f"{r['id']}: {r['status']}")

            # ── Inline Edit ──
            st.markdown("---")
            st.markdown('<div class="section-title">Quick Edit</div>', unsafe_allow_html=True)

            edit_camp = st.selectbox(
                "Select campaign to edit",
                options=[c["id"] for c in campaigns],
                format_func=lambda x: next(
                    (f"{c.get('name', '')} ({c['id']})" for c in campaigns if c["id"] == x), x
                ),
                key="cm_edit_select",
            )
            if edit_camp:
                camp_data = next((c for c in campaigns if c["id"] == edit_camp), {})
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    new_name = st.text_input("Name", value=camp_data.get("name", ""), key="cm_edit_name")
                    new_status = st.selectbox(
                        "Status", CAMPAIGN_STATUSES,
                        index=CAMPAIGN_STATUSES.index(camp_data.get("status", "PAUSED"))
                        if camp_data.get("status", "PAUSED") in CAMPAIGN_STATUSES else 0,
                        key="cm_edit_status",
                    )
                with col_e2:
                    cur_daily = safe_float(camp_data.get("daily_budget", 0)) / 100
                    new_daily = st.number_input(
                        "Daily Budget ($)", value=cur_daily, min_value=0.0, step=5.0, key="cm_edit_daily"
                    )
                    bid_options = list(BID_STRATEGIES.keys())
                    new_bid = st.selectbox("Bid Strategy", bid_options, key="cm_edit_bid")

                if st.button("Save Changes", type="primary", key="cm_save_edit"):
                    try:
                        api.update_campaign(
                            edit_camp,
                            name=new_name,
                            status=new_status,
                            daily_budget=new_daily if new_daily > 0 else None,
                            bid_strategy=BID_STRATEGIES.get(new_bid),
                        )
                        st.success(f"Campaign {edit_camp} updated!")
                    except Exception as e:
                        st.error(f"Update failed: {e}")
        else:
            st.info("No campaigns found for the selected filters.")
    except Exception as e:
        st.error(f"Failed to load campaigns: {str(e)[:300]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: CREATE CAMPAIGN
# ═══════════════════════════════════════════════════════════════════════════════

with tab_create:
    st.markdown('<div class="section-title">Create New Campaign</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        camp_name = st.text_input("Campaign Name *", key="cc_name")
        camp_objective = st.selectbox(
            "Objective *", list(CAMPAIGN_OBJECTIVES.keys()),
            key="cc_obj",
            help="Choose the outcome you want from this campaign",
        )
        camp_status = st.selectbox("Initial Status", ["PAUSED", "ACTIVE"], key="cc_status")
        special_cats = st.multiselect(
            "Special Ad Categories",
            ["NONE", "EMPLOYMENT", "HOUSING", "CREDIT", "ISSUES_ELECTIONS_POLITICS"],
            default=["NONE"], key="cc_special",
        )

    with col_c2:
        budget_type = st.radio("Budget Type", ["Daily", "Lifetime"], horizontal=True, key="cc_btype")
        budget_amount = st.number_input("Budget ($)", min_value=1.0, value=50.0, step=5.0, key="cc_budget")
        bid_strategy = st.selectbox("Bid Strategy", list(BID_STRATEGIES.keys()), key="cc_bid")
        buying_type = st.selectbox("Buying Type", ["AUCTION", "RESERVED"], key="cc_buying")

    st.markdown("---")
    st.markdown("**Campaign Preview:**")
    preview_data = {
        "Name": camp_name or "(unnamed)",
        "Objective": f"{camp_objective} ({CAMPAIGN_OBJECTIVES[camp_objective]})",
        "Budget": f"${budget_amount:.2f} ({budget_type})",
        "Bid Strategy": f"{bid_strategy} ({BID_STRATEGIES[bid_strategy]})",
        "Initial Status": camp_status,
        "Special Categories": ", ".join([s for s in special_cats if s != "NONE"]) or "None",
    }
    for k, v in preview_data.items():
        st.write(f"**{k}:** {v}")

    if st.button("Create Campaign", type="primary", use_container_width=True, key="cc_create"):
        if not camp_name:
            st.error("Campaign name is required.")
        else:
            try:
                result = api.create_campaign(
                    name=camp_name,
                    objective=CAMPAIGN_OBJECTIVES[camp_objective],
                    status=camp_status,
                    daily_budget=budget_amount if budget_type == "Daily" else None,
                    lifetime_budget=budget_amount if budget_type == "Lifetime" else None,
                    bid_strategy=BID_STRATEGIES[bid_strategy],
                    special_ad_categories=[s for s in special_cats if s != "NONE"],
                )
                st.success(f"Campaign created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed to create campaign: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: DEEP INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_insights:
    st.markdown('<div class="section-title">Campaign Deep Insights</div>', unsafe_allow_html=True)

    try:
        campaigns = api.get_campaigns()
        if campaigns:
            camp_map = {c["id"]: c.get("name", c["id"]) for c in campaigns}

            col_i1, col_i2, col_i3 = st.columns([3, 2, 2])
            with col_i1:
                sel_camp = st.selectbox(
                    "Select Campaign", list(camp_map.keys()),
                    format_func=lambda x: camp_map[x], key="ci_select",
                )
            with col_i2:
                date_preset = st.selectbox(
                    "Date Range", ["last_7d", "last_14d", "last_30d", "last_60d", "last_90d"],
                    index=2, key="ci_date",
                )
            with col_i3:
                breakdown = st.selectbox(
                    "Breakdown", ["none", "age", "gender", "age_gender", "placement", "device"],
                    key="ci_breakdown",
                )

            if st.button("Fetch Insights", type="primary", key="ci_fetch"):
                with st.spinner("Fetching campaign insights..."):
                    from src.extractor import MetaAdsExtractor
                    ext = MetaAdsExtractor(
                        st.session_state.access_token,
                        st.session_state.ad_account_id,
                    )
                    df = ext.fetch_insights(
                        level="campaign",
                        breakdown_key=breakdown,
                        preset=date_preset,
                        campaign_ids=[sel_camp],
                    )

                    if not df.empty:
                        df = compute_kpis(df)

                        # KPI summary cards
                        st.markdown("### Performance Summary")
                        c1, c2, c3, c4, c5, c6 = st.columns(6)
                        c1.metric("Spend", format_currency(safe_float(df["spend"].sum())))
                        c2.metric("Impressions", format_number(safe_int(df["impressions"].sum())))
                        c3.metric("Clicks", format_number(safe_int(df["clicks"].sum())))
                        c4.metric("CTR", format_percentage(
                            safe_divide(df["clicks"].sum(), df["impressions"].sum()) * 100
                        ))
                        c5.metric("CPC", format_currency(
                            safe_divide(df["spend"].sum(), df["clicks"].sum())
                        ))
                        c6.metric("CPM", format_currency(
                            safe_divide(df["spend"].sum(), df["impressions"].sum()) * 1000
                        ))

                        st.markdown("### Detailed Data")
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Trend chart
                        if "date_start" in df.columns and len(df) > 1:
                            st.markdown("### Spend Over Time")
                            chart_df = df.groupby("date_start")[["spend"]].sum().reset_index()
                            chart_df["spend"] = chart_df["spend"].astype(float)
                            st.line_chart(chart_df.set_index("date_start")["spend"])
                    else:
                        st.info("No insights data returned for this campaign.")
    except Exception as e:
        st.error(f"Failed: {str(e)[:200]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: COMPARE CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_compare:
    st.markdown('<div class="section-title">Compare Campaigns</div>', unsafe_allow_html=True)

    try:
        campaigns = api.get_campaigns()
        if campaigns:
            camp_map = {c["id"]: c.get("name", c["id"]) for c in campaigns}
            compare_ids = st.multiselect(
                "Select campaigns to compare (2-5)",
                options=list(camp_map.keys()),
                format_func=lambda x: camp_map[x],
                max_selections=5, key="cmp_select",
            )

            if len(compare_ids) >= 2:
                date_preset = st.selectbox(
                    "Date Range", ["last_7d", "last_14d", "last_30d"], index=2, key="cmp_date",
                )
                if st.button("Compare", type="primary", key="cmp_go"):
                    with st.spinner("Fetching comparison data..."):
                        from src.extractor import MetaAdsExtractor
                        ext = MetaAdsExtractor(
                            st.session_state.access_token,
                            st.session_state.ad_account_id,
                        )

                        rows = []
                        for cid in compare_ids:
                            df = ext.fetch_insights(
                                level="campaign", breakdown_key="none",
                                preset=date_preset, campaign_ids=[cid],
                            )
                            if not df.empty:
                                spend = safe_float(df["spend"].sum())
                                imps = safe_int(df["impressions"].sum())
                                clicks = safe_int(df["clicks"].sum())
                                reach = safe_int(df.get("reach", pd.Series([0])).sum())
                                rows.append({
                                    "Campaign": camp_map.get(cid, cid),
                                    "Spend": spend,
                                    "Impressions": imps,
                                    "Clicks": clicks,
                                    "Reach": reach,
                                    "CTR %": round(safe_divide(clicks, imps) * 100, 2),
                                    "CPC": round(safe_divide(spend, clicks), 2),
                                    "CPM": round(safe_divide(spend, imps) * 1000, 2),
                                    "Frequency": round(safe_divide(imps, reach), 2) if reach else 0,
                                })

                        if rows:
                            comp_df = pd.DataFrame(rows)
                            st.dataframe(comp_df, use_container_width=True, hide_index=True)

                            st.markdown("### Comparison Charts")
                            chart_metrics = ["Spend", "CTR %", "CPC", "CPM"]
                            for metric in chart_metrics:
                                if metric in comp_df.columns:
                                    st.bar_chart(comp_df.set_index("Campaign")[metric])
                        else:
                            st.info("No data returned for comparison.")
            elif compare_ids:
                st.info("Select at least 2 campaigns to compare.")
    except Exception as e:
        st.error(f"Failed: {str(e)[:200]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: BULK ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_bulk:
    st.markdown('<div class="section-title">Bulk Campaign Operations</div>', unsafe_allow_html=True)

    bulk_action = st.selectbox(
        "Bulk Action Type",
        ["Status Update", "Budget Update", "Bid Strategy Update", "Name Prefix/Suffix"],
        key="cb_action",
    )

    uploaded_csv = st.file_uploader(
        "Upload CSV with campaign IDs (column: campaign_id)", type=["csv"], key="cb_csv",
    )

    if uploaded_csv:
        bulk_df = pd.read_csv(uploaded_csv)
        st.dataframe(bulk_df, use_container_width=True, hide_index=True)
        st.info(f"Loaded {len(bulk_df)} rows")

        if "campaign_id" in bulk_df.columns:
            ids = bulk_df["campaign_id"].astype(str).tolist()

            if bulk_action == "Status Update":
                new_status = st.selectbox("New Status", ["ACTIVE", "PAUSED"], key="cb_status")
                if st.button("Apply Status Update", type="primary", key="cb_apply_status"):
                    results = api.batch_update_status(ids, new_status)
                    for r in results:
                        st.write(f"{r['id']}: {r['status']}")

            elif bulk_action == "Budget Update":
                if "daily_budget" in bulk_df.columns:
                    updates = [
                        {"id": str(row["campaign_id"]), "daily_budget": row["daily_budget"]}
                        for _, row in bulk_df.iterrows()
                    ]
                    if st.button("Apply Budget Updates", type="primary", key="cb_apply_budget"):
                        results = api.batch_update_budgets(updates)
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                else:
                    st.warning("CSV must have a 'daily_budget' column for budget updates.")

            elif bulk_action == "Bid Strategy Update":
                new_bid = st.selectbox(
                    "New Bid Strategy", list(BID_STRATEGIES.keys()), key="cb_bid",
                )
                if st.button("Apply Bid Strategy", type="primary", key="cb_apply_bid"):
                    for cid in ids:
                        try:
                            api.update_campaign(cid, bid_strategy=BID_STRATEGIES[new_bid])
                            st.success(f"{cid}: updated")
                        except Exception as e:
                            st.error(f"{cid}: {e}")

            elif bulk_action == "Name Prefix/Suffix":
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    prefix = st.text_input("Add Prefix", key="cb_prefix")
                with col_n2:
                    suffix = st.text_input("Add Suffix", key="cb_suffix")
                if st.button("Apply Name Changes", type="primary", key="cb_apply_name"):
                    campaigns = api.get_campaigns()
                    camp_names = {c["id"]: c.get("name", "") for c in campaigns}
                    for cid in ids:
                        old_name = camp_names.get(cid, "")
                        new_name = f"{prefix}{old_name}{suffix}"
                        try:
                            api.update_campaign(cid, name=new_name)
                            st.success(f"{cid}: '{old_name}' -> '{new_name}'")
                        except Exception as e:
                            st.error(f"{cid}: {e}")
        else:
            st.error("CSV must contain a 'campaign_id' column.")

    st.markdown("---")
    st.markdown("**Template CSV format:**")
    st.code("campaign_id,daily_budget\n123456789,50\n987654321,100", language="csv")
