"""
Advanced Automated Rules Engine — Create, manage, and execute automated optimization rules.
Covers: stop-loss, budget scaling, creative rotation, audience refresh, and custom triggers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Rules Engine", page_icon="⚙️", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .rule-card { background: white; border-radius: 8px; padding: 16px; margin: 8px 0;
        border: 1px solid #e0e0e0; }
    .rule-active { border-left: 4px solid #107C10; }
    .rule-paused { border-left: 4px solid #FFB900; }
</style>""", unsafe_allow_html=True)

RULES_FILE = "config/automation_rules.json"


def load_rules():
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_rules(rules):
    os.makedirs(os.path.dirname(RULES_FILE) or ".", exist_ok=True)
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Automated Rules Engine")
st.markdown("Set up sophisticated automation rules to optimize campaigns 24/7.")

rules = load_rules()

tab_create, tab_manage, tab_templates, tab_log, tab_schedule = st.tabs([
    "Create Rule", "Manage Rules", "Rule Templates", "Execution Log", "Schedule",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: CREATE RULE
# ═══════════════════════════════════════════════════════════════════════════════

METRICS = ["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "reach",
           "frequency", "roas", "cpa", "cvr", "cost_per_lead"]

OPERATORS = [
    "greater than", "less than", "greater than or equal",
    "less than or equal", "between", "changed by more than %",
]

ACTIONS = [
    "Pause campaign", "Pause ad set", "Pause ad",
    "Activate campaign", "Activate ad set", "Activate ad",
    "Increase daily budget by %", "Decrease daily budget by %",
    "Increase daily budget by fixed amount",
    "Decrease daily budget by fixed amount",
    "Set daily budget to fixed amount",
    "Increase bid by %", "Decrease bid by %",
    "Send notification", "Send email alert",
    "Duplicate campaign", "Duplicate ad set",
    "Log only (no action)",
]

ENTITY_LEVELS = ["Campaign", "Ad Set", "Ad"]

LOOKBACK_PERIODS = [
    "today", "yesterday", "last_3d", "last_7d",
    "last_14d", "last_30d", "lifetime",
]

with tab_create:
    st.markdown('<div class="section-title">Create Automation Rule</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        rule_name = st.text_input("Rule Name *", key="rc_name")
        rule_description = st.text_area("Description", key="rc_desc")
        rule_entity = st.selectbox("Apply to", ENTITY_LEVELS, key="rc_entity")
        rule_filter = st.text_input(
            "Entity filter (optional, e.g. campaign name contains 'Retarget')",
            key="rc_filter",
        )
    with col_c2:
        rule_enabled = st.toggle("Enabled", value=True, key="rc_enabled")
        rule_priority = st.slider("Priority (1=highest)", 1, 10, 5, key="rc_priority")

    st.markdown("### Conditions")
    st.markdown("All conditions must be met (AND logic). Add multiple conditions for complex rules.")

    n_conditions = st.number_input("Number of conditions", 1, 5, 1, key="rc_n_cond")
    conditions = []
    for i in range(int(n_conditions)):
        st.markdown(f"**Condition {i + 1}:**")
        col_m, col_o, col_v, col_p = st.columns([2, 2, 2, 2])
        with col_m:
            metric = st.selectbox(f"Metric", METRICS, key=f"rc_metric_{i}")
        with col_o:
            operator = st.selectbox(f"Operator", OPERATORS, key=f"rc_op_{i}")
        with col_v:
            value = st.number_input(f"Value", step=0.1, key=f"rc_val_{i}")
        with col_p:
            lookback = st.selectbox(f"Period", LOOKBACK_PERIODS, index=3, key=f"rc_look_{i}")
        conditions.append({
            "metric": metric,
            "operator": operator,
            "value": value,
            "lookback": lookback,
        })

    st.markdown("### Action")
    rule_action = st.selectbox("Action to take", ACTIONS, key="rc_action")
    action_value = None
    if "%" in rule_action or "fixed" in rule_action.lower():
        action_value = st.number_input("Action value", step=1.0, key="rc_action_val")

    st.markdown("### Execution Settings")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        exec_frequency = st.selectbox(
            "Check frequency",
            ["Every 30 minutes", "Every hour", "Every 4 hours", "Every 12 hours", "Daily"],
            index=1, key="rc_freq",
        )
    with col_e2:
        max_executions = st.number_input(
            "Max executions per entity (0=unlimited)", min_value=0, value=3, key="rc_max_exec",
        )
        cooldown_hours = st.number_input(
            "Cooldown between executions (hours)", min_value=0, value=24, key="rc_cooldown",
        )

    require_approval = st.checkbox("Require manual approval before executing", key="rc_approval")

    st.markdown("### Rule Preview")
    rule_preview = {
        "name": rule_name,
        "entity": rule_entity,
        "conditions": conditions,
        "action": rule_action,
        "action_value": action_value,
        "frequency": exec_frequency,
        "enabled": rule_enabled,
    }
    st.json(rule_preview)

    if st.button("Create Rule", type="primary", use_container_width=True, key="rc_create"):
        if not rule_name:
            st.error("Rule name is required.")
        else:
            rule = {
                "id": f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": rule_name,
                "description": rule_description,
                "entity_level": rule_entity,
                "entity_filter": rule_filter,
                "conditions": conditions,
                "action": rule_action,
                "action_value": action_value,
                "frequency": exec_frequency,
                "max_executions": max_executions,
                "cooldown_hours": cooldown_hours,
                "require_approval": require_approval,
                "enabled": rule_enabled,
                "priority": rule_priority,
                "created_at": datetime.now().isoformat(),
                "execution_count": 0,
                "last_executed": None,
            }
            rules.append(rule)
            save_rules(rules)
            st.success(f"Rule '{rule_name}' created!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: MANAGE RULES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_manage:
    st.markdown('<div class="section-title">Active Rules</div>', unsafe_allow_html=True)

    rules = load_rules()
    if rules:
        rows = []
        for r in rules:
            rows.append({
                "ID": r.get("id", ""),
                "Name": r.get("name", ""),
                "Entity": r.get("entity_level", ""),
                "Action": r.get("action", ""),
                "Enabled": r.get("enabled", False),
                "Priority": r.get("priority", 5),
                "Executions": r.get("execution_count", 0),
                "Last Run": r.get("last_executed", "Never"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Toggle/Delete
        rule_to_modify = st.selectbox(
            "Select rule",
            options=range(len(rules)),
            format_func=lambda i: rules[i].get("name", f"Rule {i}"),
            key="rm_select",
        )

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            if st.button("Toggle Enabled", key="rm_toggle"):
                rules[rule_to_modify]["enabled"] = not rules[rule_to_modify].get("enabled", True)
                save_rules(rules)
                st.rerun()
        with col_m2:
            if st.button("Execute Now", type="primary", key="rm_exec"):
                st.info(f"Rule '{rules[rule_to_modify]['name']}' would be executed against live data.")
                st.warning("Connect to Meta API and run the scheduler to execute rules.")
        with col_m3:
            if st.button("Delete Rule", key="rm_delete"):
                del rules[rule_to_modify]
                save_rules(rules)
                st.rerun()

        # Rule details
        st.markdown("### Rule Details")
        st.json(rules[rule_to_modify])
    else:
        st.info("No automation rules created yet. Use 'Create Rule' tab to add one.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: RULE TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

TEMPLATES = [
    {
        "name": "Stop-Loss: Pause High-Spend Low-CTR Ads",
        "entity_level": "Ad",
        "conditions": [
            {"metric": "spend", "operator": "greater than", "value": 20, "lookback": "last_3d"},
            {"metric": "ctr", "operator": "less than", "value": 0.5, "lookback": "last_3d"},
        ],
        "action": "Pause ad",
        "description": "Automatically pause ads that have spent more than $20 in 3 days with CTR below 0.5%.",
    },
    {
        "name": "Scale Winners: Increase Budget for High ROAS",
        "entity_level": "Campaign",
        "conditions": [
            {"metric": "roas", "operator": "greater than", "value": 3.0, "lookback": "last_7d"},
            {"metric": "spend", "operator": "greater than", "value": 50, "lookback": "last_7d"},
        ],
        "action": "Increase daily budget by %",
        "action_value": 20,
        "description": "Increase budget by 20% for campaigns with ROAS above 3.0 and at least $50 spent.",
    },
    {
        "name": "Creative Fatigue: Pause High-Frequency Ads",
        "entity_level": "Ad",
        "conditions": [
            {"metric": "frequency", "operator": "greater than", "value": 4.0, "lookback": "last_7d"},
        ],
        "action": "Pause ad",
        "description": "Pause ads when frequency exceeds 4.0, indicating audience fatigue.",
    },
    {
        "name": "Budget Guard: Cap Daily Spend",
        "entity_level": "Campaign",
        "conditions": [
            {"metric": "spend", "operator": "greater than", "value": 100, "lookback": "today"},
        ],
        "action": "Pause campaign",
        "description": "Pause campaigns that exceed $100 in daily spend.",
    },
    {
        "name": "CPA Watchdog: Cut Budget on Expensive Campaigns",
        "entity_level": "Campaign",
        "conditions": [
            {"metric": "cpa", "operator": "greater than", "value": 50, "lookback": "last_7d"},
            {"metric": "spend", "operator": "greater than", "value": 100, "lookback": "last_7d"},
        ],
        "action": "Decrease daily budget by %",
        "action_value": 30,
        "description": "Reduce budget by 30% when CPA exceeds $50 on campaigns with significant spend.",
    },
    {
        "name": "Scaling Guard: Limit Budget Increase",
        "entity_level": "Campaign",
        "conditions": [
            {"metric": "ctr", "operator": "greater than", "value": 2.0, "lookback": "last_7d"},
            {"metric": "cpa", "operator": "less than", "value": 20, "lookback": "last_7d"},
        ],
        "action": "Increase daily budget by %",
        "action_value": 15,
        "description": "Carefully scale budget by 15% for campaigns with CTR above 2% and CPA below $20.",
    },
]

with tab_templates:
    st.markdown('<div class="section-title">Rule Templates</div>', unsafe_allow_html=True)
    st.markdown("Pre-built rule templates for common optimization scenarios. Click to use any template.")

    for i, tmpl in enumerate(TEMPLATES):
        with st.expander(f"📋 {tmpl['name']}"):
            st.markdown(f"**Description:** {tmpl['description']}")
            st.markdown(f"**Entity Level:** {tmpl['entity_level']}")
            st.markdown(f"**Action:** {tmpl['action']}")
            if tmpl.get("action_value"):
                st.markdown(f"**Action Value:** {tmpl['action_value']}")
            st.markdown("**Conditions:**")
            for cond in tmpl["conditions"]:
                st.markdown(f"- `{cond['metric']}` {cond['operator']} `{cond['value']}` (over {cond['lookback']})")

            if st.button(f"Use This Template", key=f"tmpl_{i}"):
                rule = {
                    "id": f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    "name": tmpl["name"],
                    "description": tmpl["description"],
                    "entity_level": tmpl["entity_level"],
                    "conditions": tmpl["conditions"],
                    "action": tmpl["action"],
                    "action_value": tmpl.get("action_value"),
                    "frequency": "Every hour",
                    "enabled": True,
                    "priority": 5,
                    "created_at": datetime.now().isoformat(),
                    "execution_count": 0,
                    "last_executed": None,
                }
                rules.append(rule)
                save_rules(rules)
                st.success(f"Template '{tmpl['name']}' added to rules!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: EXECUTION LOG
# ═══════════════════════════════════════════════════════════════════════════════

with tab_log:
    st.markdown('<div class="section-title">Execution Log</div>', unsafe_allow_html=True)

    log_file = "config/rule_execution_log.json"
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                log_data = json.load(f)
            if log_data:
                st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
            else:
                st.info("No rule executions logged yet.")
        except Exception:
            st.info("No rule executions logged yet.")
    else:
        st.info("No rule executions logged yet. Rules will be logged here when they run.")

    if st.button("Clear Log", key="rl_clear"):
        with open(log_file, "w") as f:
            json.dump([], f)
        st.success("Execution log cleared.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_schedule:
    st.markdown('<div class="section-title">Rule Execution Schedule</div>', unsafe_allow_html=True)

    st.markdown("""
    Configure the automated rule execution schedule. Rules are checked at the specified
    intervals and actions are taken when conditions are met.
    """)

    scheduler_enabled = st.toggle("Enable Rule Scheduler", value=False, key="rs_enabled")

    if scheduler_enabled:
        check_interval = st.selectbox(
            "Check Interval",
            ["Every 15 minutes", "Every 30 minutes", "Every hour", "Every 4 hours", "Daily"],
            index=2, key="rs_interval",
        )
        quiet_hours = st.checkbox("Enable Quiet Hours (no actions during off-hours)", key="rs_quiet")
        if quiet_hours:
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                quiet_start = st.time_input("Quiet Start", value=None, key="rs_quiet_start")
            with col_q2:
                quiet_end = st.time_input("Quiet End", value=None, key="rs_quiet_end")

        max_daily_actions = st.number_input("Max actions per day", min_value=1, value=50, key="rs_max_daily")

        if st.button("Save Schedule Settings", type="primary", key="rs_save"):
            schedule_config = {
                "enabled": scheduler_enabled,
                "interval": check_interval,
                "quiet_hours": quiet_hours,
                "max_daily_actions": max_daily_actions,
            }
            os.makedirs("config", exist_ok=True)
            with open("config/scheduler_config.json", "w") as f:
                json.dump(schedule_config, f, indent=2)
            st.success("Schedule settings saved!")
    else:
        st.info("Rule scheduler is disabled. Enable it to automatically execute rules.")
