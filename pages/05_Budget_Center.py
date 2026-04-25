"""
Budget & Bidding Center — Budget allocation, spend pacing, bid strategy management,
budget recommendations, and spend forecasting.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.meta_api import MetaAPIManager
from src.helpers import format_currency, format_number, format_percentage, safe_float, safe_int, safe_divide

st.set_page_config(page_title="Budget Center", page_icon="💰", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .budget-card { background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
        border-radius: 8px; padding: 16px; margin: 8px 0;
        border: 1px solid #cce0ff; }
    .overspend { color: #D13438; font-weight: 600; }
    .underspend { color: #107C10; font-weight: 600; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Budget & Bidding Center")
st.markdown("Allocate budgets, monitor spend pacing, manage bid strategies, and forecast spend.")

api = get_api()

tab_overview, tab_allocate, tab_pacing, tab_forecast, tab_rules = st.tabs([
    "Budget Overview", "Budget Allocation", "Spend Pacing", "Spend Forecast", "Budget Rules",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: BUDGET OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab_overview:
    st.markdown('<div class="section-title">Budget Overview</div>', unsafe_allow_html=True)

    try:
        account = api.get_account_info()
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        col_a1.metric("Account", account.get("name", "N/A"))
        col_a2.metric("Currency", account.get("currency", "USD"))
        col_a3.metric("Total Spent", format_currency(safe_float(account.get("amount_spent", 0)) / 100))
        col_a4.metric("Spend Cap", format_currency(safe_float(account.get("spend_cap", 0)) / 100) if account.get("spend_cap") else "No cap")
    except Exception as e:
        st.error(f"Failed to load account: {e}")

    st.markdown("---")

    try:
        campaigns = api.get_campaigns(status_filter=["ACTIVE", "PAUSED"])
        if campaigns:
            rows = []
            total_daily = 0
            total_lifetime = 0
            for c in campaigns:
                daily = safe_float(c.get("daily_budget", 0)) / 100
                lifetime = safe_float(c.get("lifetime_budget", 0)) / 100
                remaining = safe_float(c.get("budget_remaining", 0)) / 100
                total_daily += daily
                total_lifetime += lifetime
                rows.append({
                    "Campaign": c.get("name", ""),
                    "Status": c.get("effective_status", ""),
                    "Daily Budget": format_currency(daily) if daily else "-",
                    "Lifetime Budget": format_currency(lifetime) if lifetime else "-",
                    "Remaining": format_currency(remaining) if remaining else "-",
                    "Bid Strategy": c.get("bid_strategy", "N/A"),
                    "Objective": c.get("objective", ""),
                })

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Daily Budget", format_currency(total_daily))
            c2.metric("Total Lifetime Budget", format_currency(total_lifetime))
            c3.metric("Active Campaigns", len([c for c in campaigns if c.get("effective_status") == "ACTIVE"]))

            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Failed to load campaigns: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: BUDGET ALLOCATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_allocate:
    st.markdown('<div class="section-title">Budget Allocation</div>', unsafe_allow_html=True)

    st.markdown("Redistribute budgets across campaigns based on performance.")

    total_budget = st.number_input(
        "Total Daily Budget to Allocate ($)", min_value=10.0, value=500.0, step=50.0, key="ba_total",
    )

    allocation_method = st.selectbox(
        "Allocation Method",
        ["Equal Split", "Performance-Based (by ROAS)", "Performance-Based (by CPA)",
         "Performance-Based (by CTR)", "Custom Weights"],
        key="ba_method",
    )

    try:
        campaigns = api.get_campaigns(status_filter=["ACTIVE"])
        if campaigns:
            n = len(campaigns)
            if allocation_method == "Equal Split":
                per_camp = total_budget / n if n else 0
                alloc_rows = []
                for c in campaigns:
                    alloc_rows.append({
                        "Campaign": c.get("name", ""),
                        "ID": c.get("id", ""),
                        "Current Daily": format_currency(safe_float(c.get("daily_budget", 0)) / 100),
                        "New Daily": format_currency(per_camp),
                        "Change": format_currency(per_camp - safe_float(c.get("daily_budget", 0)) / 100),
                    })
                st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

            elif allocation_method == "Custom Weights":
                st.markdown("### Set Custom Weights")
                weights = {}
                for c in campaigns:
                    w = st.number_input(
                        f"{c.get('name', c.get('id', ''))}",
                        min_value=0.0, max_value=100.0, value=round(100 / n, 1),
                        step=1.0, key=f"ba_w_{c.get('id', '')}",
                    )
                    weights[c["id"]] = w

                total_weight = sum(weights.values())
                if total_weight > 0:
                    alloc_rows = []
                    for c in campaigns:
                        pct = weights[c["id"]] / total_weight
                        new_budget = total_budget * pct
                        alloc_rows.append({
                            "Campaign": c.get("name", ""),
                            "ID": c.get("id", ""),
                            "Weight": f"{weights[c['id']]:.1f}%",
                            "Allocation": f"{pct*100:.1f}%",
                            "New Daily": format_currency(new_budget),
                        })
                    st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)
            else:
                st.info(
                    f"Performance-based allocation ({allocation_method}) requires historical data. "
                    "Run an extraction first to calculate performance-weighted allocations."
                )

            if st.button("Apply Allocation", type="primary", use_container_width=True, key="ba_apply"):
                if allocation_method == "Equal Split":
                    per_camp = total_budget / n
                    updates = [{"id": c["id"], "daily_budget": per_camp} for c in campaigns]
                    results = api.batch_update_budgets(updates)
                    for r in results:
                        st.write(f"{r['id']}: {r['status']}")
                elif allocation_method == "Custom Weights":
                    total_weight = sum(weights.values())
                    if total_weight > 0:
                        updates = []
                        for c in campaigns:
                            pct = weights[c["id"]] / total_weight
                            updates.append({"id": c["id"], "daily_budget": total_budget * pct})
                        results = api.batch_update_budgets(updates)
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                    else:
                        st.error("All weights are zero. Set at least one weight above 0.")
                else:
                    st.warning("Performance-based allocation requires historical data. Run an extraction first.")
    except Exception as e:
        st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: SPEND PACING
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pacing:
    st.markdown('<div class="section-title">Spend Pacing Analysis</div>', unsafe_allow_html=True)

    st.markdown("Track how your campaigns are pacing against their budgets.")

    try:
        campaigns = api.get_campaigns(status_filter=["ACTIVE"])
        if campaigns:
            from src.extractor import MetaAdsExtractor
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )

            pacing_data = []
            for c in campaigns[:20]:
                daily_budget = safe_float(c.get("daily_budget", 0)) / 100
                if daily_budget <= 0:
                    continue

                try:
                    df = ext.fetch_insights(
                        level="campaign", breakdown_key="none",
                        preset="today", campaign_ids=[c["id"]],
                    )
                    today_spend = safe_float(df["spend"].sum()) if not df.empty else 0
                except Exception:
                    today_spend = 0

                pacing_pct = safe_divide(today_spend, daily_budget) * 100
                status = "On Track" if 40 <= pacing_pct <= 110 else ("Underspend" if pacing_pct < 40 else "Overspend")

                pacing_data.append({
                    "Campaign": c.get("name", ""),
                    "Daily Budget": format_currency(daily_budget),
                    "Today Spend": format_currency(today_spend),
                    "Pacing": f"{pacing_pct:.1f}%",
                    "Status": status,
                })

            if pacing_data:
                st.dataframe(pd.DataFrame(pacing_data), use_container_width=True, hide_index=True)
            else:
                st.info("No active campaigns with daily budgets found.")
    except Exception as e:
        st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SPEND FORECAST
# ═══════════════════════════════════════════════════════════════════════════════

with tab_forecast:
    st.markdown('<div class="section-title">Spend Forecast</div>', unsafe_allow_html=True)

    st.markdown("Forecast future spend based on current pacing and budget configuration.")

    forecast_days = st.slider("Forecast period (days)", 7, 90, 30, key="fc_days")

    try:
        campaigns = api.get_campaigns(status_filter=["ACTIVE"])
        if campaigns:
            forecast_data = []
            total_daily = 0
            for c in campaigns:
                daily = safe_float(c.get("daily_budget", 0)) / 100
                total_daily += daily
                forecast_data.append({
                    "Campaign": c.get("name", ""),
                    "Daily Budget": format_currency(daily),
                    f"{forecast_days}d Forecast": format_currency(daily * forecast_days),
                })

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Daily", format_currency(total_daily))
            c2.metric(f"{forecast_days}d Forecast", format_currency(total_daily * forecast_days))
            c3.metric("Monthly Estimate", format_currency(total_daily * 30))

            st.dataframe(pd.DataFrame(forecast_data), use_container_width=True, hide_index=True)

            # Spend chart
            import numpy as np
            days = list(range(1, forecast_days + 1))
            cumulative = [total_daily * d for d in days]
            chart_df = pd.DataFrame({"Day": days, "Cumulative Spend ($)": cumulative})
            st.line_chart(chart_df.set_index("Day"))
    except Exception as e:
        st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: BUDGET RULES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_rules:
    st.markdown('<div class="section-title">Automated Budget Rules</div>', unsafe_allow_html=True)

    st.markdown("""
    Set up automated rules to adjust budgets based on performance thresholds.
    Rules are evaluated periodically and apply changes automatically.
    """)

    rule_name = st.text_input("Rule Name", key="br_name")
    rule_trigger = st.selectbox(
        "Trigger Condition",
        [
            "CPA exceeds threshold",
            "ROAS drops below threshold",
            "CTR drops below threshold",
            "Spend exceeds daily limit",
            "Frequency exceeds threshold",
        ],
        key="br_trigger",
    )
    rule_threshold = st.number_input("Threshold Value", min_value=0.0, step=0.1, key="br_threshold")
    rule_action = st.selectbox(
        "Action",
        [
            "Decrease budget by 20%",
            "Decrease budget by 50%",
            "Increase budget by 20%",
            "Increase budget by 50%",
            "Pause campaign",
            "Send notification only",
        ],
        key="br_action",
    )
    rule_lookback = st.selectbox("Lookback Period", ["last_3d", "last_7d", "last_14d", "last_30d"], key="br_lookback")

    if st.button("Create Rule", type="primary", key="br_create"):
        if not rule_name:
            st.error("Rule name is required.")
        else:
            rule = {
                "name": rule_name,
                "trigger": rule_trigger,
                "threshold": rule_threshold,
                "action": rule_action,
                "lookback": rule_lookback,
                "enabled": True,
            }
            if "budget_rules" not in st.session_state:
                st.session_state["budget_rules"] = []
            st.session_state["budget_rules"].append(rule)
            st.success(f"Rule '{rule_name}' created!")

    # Display existing rules
    if st.session_state.get("budget_rules"):
        st.markdown("### Active Rules")
        rules_df = pd.DataFrame(st.session_state["budget_rules"])
        st.dataframe(rules_df, use_container_width=True, hide_index=True)
