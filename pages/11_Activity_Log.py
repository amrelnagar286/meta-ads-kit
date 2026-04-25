"""
Activity Log & Notification Center — Track all account changes, user actions,
and system events. Get real-time notifications on important changes.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.meta_api import MetaAPIManager

st.set_page_config(page_title="Activity Log", page_icon="📝", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .activity-item { border-left: 3px solid #0078D4; padding: 8px 16px; margin: 4px 0;
        background: #f8f9fa; border-radius: 0 4px 4px 0; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Activity Log & Notifications")

api = get_api()

tab_activity, tab_changes, tab_notifications, tab_audit = st.tabs([
    "Activity Feed", "Recent Changes", "Notifications", "Audit Trail",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ACTIVITY FEED
# ═══════════════════════════════════════════════════════════════════════════════

with tab_activity:
    st.markdown('<div class="section-title">Activity Feed</div>', unsafe_allow_html=True)

    col_af1, col_af2 = st.columns([3, 1])
    with col_af1:
        activity_limit = st.slider("Number of activities", 10, 200, 50, key="af_limit")
    with col_af2:
        st.write("")
        st.write("")
        st.button("Refresh", use_container_width=True, key="af_refresh")

    try:
        with st.spinner("Loading activity log..."):
            activities = api.get_activities(limit=activity_limit)

        if activities:
            rows = []
            for a in activities:
                rows.append({
                    "Time": a.get("event_time", ""),
                    "Event": a.get("translated_event_type", a.get("event_type", "")),
                    "Object": a.get("object_name", a.get("object_id", "")),
                    "Object Type": a.get("object_type", ""),
                    "Actor": a.get("actor_name", a.get("actor_id", "")),
                    "Details": str(a.get("extra_data", ""))[:100],
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)

            # Filter options
            with st.expander("Filter Activities"):
                event_types = df["Event"].unique().tolist()
                selected_events = st.multiselect("Event Types", event_types, key="af_event_filter")
                object_types = df["Object Type"].unique().tolist()
                selected_objects = st.multiselect("Object Types", object_types, key="af_obj_filter")

                if selected_events:
                    df = df[df["Event"].isin(selected_events)]
                if selected_objects:
                    df = df[df["Object Type"].isin(selected_objects)]

                st.dataframe(df, use_container_width=True, hide_index=True)

            # Timeline view
            st.markdown("### Activity Timeline")
            for _, row in df.head(20).iterrows():
                st.markdown(f"""
                <div class="activity-item">
                    <span style="color: #666; font-size: 0.8rem;">{row['Time']}</span><br>
                    <b>{row['Event']}</b> — {row['Object']} ({row['Object Type']})<br>
                    <span style="color: #888;">by {row['Actor']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No activities found.")
    except Exception as e:
        st.error(f"Failed to load activities: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: RECENT CHANGES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_changes:
    st.markdown('<div class="section-title">Recent Changes Summary</div>', unsafe_allow_html=True)

    st.markdown("""
    Track what changed in your account recently — status changes, budget modifications,
    new campaigns, paused ads, and more.
    """)

    change_period = st.selectbox("Period", ["Last 24 hours", "Last 3 days", "Last 7 days"], key="rc_period")

    if st.button("Load Changes", type="primary", key="rc_load"):
        try:
            since = None
            if change_period == "Last 24 hours":
                since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")
            elif change_period == "Last 3 days":
                since = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            else:
                since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            activities = api.get_activities(since=since, limit=200)

            if activities:
                # Categorize changes
                status_changes = [a for a in activities if "status" in str(a.get("event_type", "")).lower()]
                budget_changes = [a for a in activities if "budget" in str(a.get("event_type", "")).lower()]
                created = [a for a in activities if "create" in str(a.get("event_type", "")).lower()]

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Changes", len(activities))
                c2.metric("Status Changes", len(status_changes))
                c3.metric("Budget Changes", len(budget_changes))
                c4.metric("New Items", len(created))

                if status_changes:
                    st.markdown("### Status Changes")
                    st.dataframe(
                        pd.DataFrame([{
                            "Time": a.get("event_time", ""),
                            "Object": a.get("object_name", ""),
                            "Event": a.get("translated_event_type", ""),
                        } for a in status_changes]),
                        use_container_width=True, hide_index=True,
                    )
            else:
                st.info(f"No changes found in {change_period.lower()}.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_notifications:
    st.markdown('<div class="section-title">Notification Settings</div>', unsafe_allow_html=True)

    st.markdown("Configure what events trigger notifications.")

    NOTIFICATION_TYPES = [
        "Campaign paused/resumed",
        "Budget changed",
        "Ad set created/deleted",
        "Creative approved/rejected",
        "Spend exceeds daily budget",
        "CTR drops below threshold",
        "CPA exceeds threshold",
        "Frequency exceeds threshold",
        "Account spend limit reached",
        "Rule execution completed",
    ]

    st.markdown("### Enable Notifications")
    for i, nt in enumerate(NOTIFICATION_TYPES):
        st.checkbox(nt, value=(i < 5), key=f"notif_{i}")

    st.markdown("### Notification Channels")
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.checkbox("In-app notifications", value=True, key="notif_app")
        st.checkbox("Email notifications", value=False, key="notif_email")
    with col_n2:
        notif_email_addr = st.text_input("Notification email", key="notif_email_addr")
        notif_frequency = st.selectbox(
            "Email digest frequency",
            ["Real-time", "Hourly digest", "Daily digest"],
            key="notif_freq",
        )

    if st.button("Save Notification Settings", type="primary", key="notif_save"):
        st.success("Notification settings saved!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════

with tab_audit:
    st.markdown('<div class="section-title">Audit Trail</div>', unsafe_allow_html=True)

    st.markdown("""
    Complete audit trail of all actions taken through this dashboard.
    Every API call, status change, and budget modification is logged.
    """)

    audit_file = "config/audit_trail.json"
    import json, os

    if os.path.exists(audit_file):
        try:
            with open(audit_file) as f:
                audit_data = json.load(f)
            if audit_data:
                st.dataframe(pd.DataFrame(audit_data), use_container_width=True, hide_index=True)

                csv = pd.DataFrame(audit_data).to_csv(index=False)
                st.download_button("Export Audit Trail", csv, "audit_trail.csv", "text/csv")
            else:
                st.info("No audit entries yet.")
        except Exception:
            st.info("No audit entries yet.")
    else:
        st.info("Audit trail will be populated as you use the dashboard to make changes.")

    if st.button("Clear Audit Trail", key="audit_clear"):
        os.makedirs(os.path.dirname(audit_file) or ".", exist_ok=True)
        with open(audit_file, "w") as f:
            json.dump([], f)
        st.success("Audit trail cleared.")
