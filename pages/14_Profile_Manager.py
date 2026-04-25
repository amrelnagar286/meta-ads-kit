"""
Profile Manager — Multi-business/brand profile system.
Create, switch, edit, delete, import/export profiles for managing multiple ad accounts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import streamlit as st
import pandas as pd
from datetime import datetime

from src.profile_manager import (
    create_profile, update_profile, delete_profile,
    get_all_profiles, get_active_profile, get_active_profile_id,
    set_active_profile, duplicate_profile, toggle_favorite, is_favorite,
    get_favorites, export_profiles, import_profiles,
    get_recent_activity, get_profile_stats, BRAND_COLORS,
    add_custom_kpi, remove_custom_kpi,
)

st.set_page_config(page_title="Profile Manager", page_icon="👤", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .profile-card {
        background: white; border-radius: 12px; padding: 20px; margin: 8px 0;
        border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .profile-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
    .profile-active {
        border-left: 4px solid #107C10;
        background: linear-gradient(135deg, #f0fff0 0%, #ffffff 100%);
    }
    .profile-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.75rem; font-weight: 600; color: white;
    }
    .brand-dot {
        display: inline-block; width: 14px; height: 14px; border-radius: 50%;
        margin-right: 6px; vertical-align: middle;
    }
    .stat-card {
        background: linear-gradient(135deg, #0078D4 0%, #106EBE 100%);
        border-radius: 8px; padding: 16px; color: white; text-align: center;
    }
    .stat-card .stat-value { font-size: 2rem; font-weight: 700; }
    .stat-card .stat-label { font-size: 0.85rem; opacity: 0.85; }
    .activity-item {
        padding: 8px 12px; border-left: 3px solid #0078D4;
        margin: 4px 0; background: #f9f9f9; border-radius: 0 6px 6px 0;
    }
</style>""", unsafe_allow_html=True)

st.markdown("# Profile Manager")
st.markdown("Manage multiple businesses and brands — switch between ad accounts instantly.")

# ═══════════════════════════════════════════════════════════════════════════════
# TOP BAR — STATS
# ═══════════════════════════════════════════════════════════════════════════════

stats = get_profile_stats()
col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
col_s1.metric("Total Profiles", stats["total_profiles"])
col_s2.metric("Configured", stats["configured"])
col_s3.metric("Total Extractions", stats["total_extractions"])
col_s4.metric("Industries", len(stats["industries"]))
col_s5.metric("Favorites", stats["favorites_count"])

st.markdown("---")

tab_profiles, tab_create, tab_active, tab_import, tab_activity = st.tabs([
    "All Profiles", "Create Profile", "Active Profile", "Import / Export", "Activity Log",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ALL PROFILES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_profiles:
    st.markdown('<div class="section-title">Your Profiles</div>', unsafe_allow_html=True)

    profiles = get_all_profiles()
    active_id = get_active_profile_id()

    if not profiles:
        st.info("No profiles yet. Create one in the 'Create Profile' tab.")
    else:
        # Quick filter
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            search = st.text_input("Search profiles", key="pm_search", placeholder="Name, industry, tags...")
        with col_f2:
            filter_industry = st.selectbox(
                "Filter by Industry",
                ["All"] + list({p.get("industry", "") for p in profiles.values() if p.get("industry")}),
                key="pm_industry",
            )
        with col_f3:
            show_favorites_only = st.checkbox("Favorites only", key="pm_fav_only")

        # Apply filters
        filtered = {}
        for pid, p in profiles.items():
            if search:
                search_text = f"{p.get('name', '')} {p.get('business_name', '')} {p.get('industry', '')} {' '.join(p.get('tags', []))}"
                if search.lower() not in search_text.lower():
                    continue
            if filter_industry != "All" and p.get("industry", "") != filter_industry:
                continue
            if show_favorites_only and not is_favorite(pid):
                continue
            filtered[pid] = p

        st.write(f"Showing {len(filtered)} of {len(profiles)} profiles")

        for pid, profile in filtered.items():
            is_active = pid == active_id
            is_fav = is_favorite(pid)
            card_class = "profile-card profile-active" if is_active else "profile-card"
            color = profile.get("brand_color", "#0078D4")

            col_main, col_actions = st.columns([4, 1])

            with col_main:
                fav_icon = "★" if is_fav else "☆"
                active_badge = " (ACTIVE)" if is_active else ""
                configured = bool(profile.get("access_token") and profile.get("ad_account_id"))
                config_badge = "Configured" if configured else "Not configured"
                config_color = "#107C10" if configured else "#FFB900"

                st.markdown(
                    f'<div class="{card_class}">'
                    f'<span class="brand-dot" style="background:{color}"></span>'
                    f'<strong>{profile["name"]}</strong>{active_badge} {fav_icon}'
                    f'<br><span style="color:#605E5C">{profile.get("business_name", "")}</span>'
                    f' | <span style="color:#605E5C">{profile.get("industry", "N/A")}</span>'
                    f' | <span class="profile-badge" style="background:{config_color}">{config_badge}</span>'
                    f' | <span style="color:#605E5C">{profile.get("currency", "USD")}</span>'
                    f' | Extractions: {profile.get("total_extractions", 0)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Tags
                tags = profile.get("tags", [])
                if tags:
                    st.write("Tags: " + ", ".join(f"`{t}`" for t in tags))

            with col_actions:
                st.write("")
                if not is_active:
                    if st.button("Switch", key=f"pm_switch_{pid}", use_container_width=True):
                        set_active_profile(pid)
                        st.session_state.access_token = profile.get("access_token", "")
                        st.session_state.ad_account_id = profile.get("ad_account_id", "")
                        st.session_state.connected = False
                        st.rerun()
                else:
                    st.success("Active")

                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if st.button("★" if not is_fav else "☆", key=f"pm_fav_{pid}"):
                        toggle_favorite(pid)
                        st.rerun()
                with col_a2:
                    if st.button("Copy", key=f"pm_dup_{pid}"):
                        duplicate_profile(pid)
                        st.rerun()

        # Bulk actions
        st.markdown("---")
        st.markdown('<div class="section-title">Bulk Actions</div>', unsafe_allow_html=True)
        all_ids = list(profiles.keys())
        selected_for_delete = st.multiselect(
            "Select profiles to delete",
            options=all_ids,
            format_func=lambda x: profiles[x]["name"],
            key="pm_bulk_delete",
        )
        if selected_for_delete and st.button("Delete Selected", type="primary", key="pm_delete_bulk"):
            for pid in selected_for_delete:
                delete_profile(pid)
            st.success(f"Deleted {len(selected_for_delete)} profile(s)")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: CREATE PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_create:
    st.markdown('<div class="section-title">Create New Profile</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown("### Brand Identity")
        new_name = st.text_input("Profile Name *", placeholder="e.g., Nike US", key="pm_new_name")
        new_business = st.text_input("Business Name", placeholder="e.g., Nike, Inc.", key="pm_new_biz")
        new_industry = st.selectbox(
            "Industry",
            ["", "E-Commerce", "SaaS", "Finance", "Healthcare", "Education",
             "Real Estate", "Travel", "Food & Beverage", "Fashion",
             "Technology", "Entertainment", "Automotive", "Fitness",
             "Non-Profit", "Agency", "Other"],
            key="pm_new_industry",
        )
        new_color = st.selectbox(
            "Brand Color",
            list(BRAND_COLORS.keys()),
            key="pm_new_color",
        )
        st.markdown(
            f'<span class="brand-dot" style="background:{BRAND_COLORS[new_color]}"></span> Preview',
            unsafe_allow_html=True,
        )
        new_tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., sportswear, DTC, US market",
            key="pm_new_tags",
        )

    with col_c2:
        st.markdown("### Credentials")
        new_token = st.text_input("Access Token", type="password", key="pm_new_token")
        new_account = st.text_input("Ad Account ID", placeholder="act_XXXXXXXXX", key="pm_new_account")

        st.markdown("### Settings")
        new_currency = st.selectbox(
            "Currency", ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR", "BRL", "AED", "SAR", "EGP"],
            key="pm_new_currency",
        )
        new_timezone = st.selectbox(
            "Timezone",
            ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
             "Europe/London", "Europe/Berlin", "Europe/Paris", "Asia/Tokyo", "Asia/Dubai",
             "Asia/Kolkata", "Australia/Sydney", "Africa/Cairo"],
            key="pm_new_tz",
        )
        new_budget = st.number_input("Monthly Budget ($)", min_value=0.0, step=500.0, key="pm_new_budget")

    st.markdown("### Notes")
    new_notes = st.text_area("Profile Notes", placeholder="Any important notes about this brand/business...", key="pm_new_notes")

    st.markdown("### Performance Benchmarks")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bench_ctr = st.number_input("Target CTR (%)", value=2.0, step=0.1, key="pm_bench_ctr")
        bench_roas = st.number_input("Target ROAS", value=3.0, step=0.5, key="pm_bench_roas")
    with col_b2:
        bench_freq = st.number_input("Max Frequency", value=3.5, step=0.5, key="pm_bench_freq")
        bench_cpa = st.number_input("Max CPA ($)", value=50.0, step=5.0, key="pm_bench_cpa")
    with col_b3:
        bench_bleed_ctr = st.number_input("Bleeder CTR Threshold (%)", value=1.0, step=0.1, key="pm_bench_bleed_ctr")
        bench_bleed_spend = st.number_input("Bleeder Spend Threshold ($)", value=10.0, step=5.0, key="pm_bench_bleed_spend")

    if st.button("Create Profile", type="primary", use_container_width=True, key="pm_create"):
        if not new_name:
            st.error("Profile name is required.")
        else:
            tags = [t.strip() for t in new_tags.split(",") if t.strip()] if new_tags else []
            profile = create_profile(
                name=new_name,
                access_token=new_token,
                ad_account_id=new_account,
                business_name=new_business,
                brand_color=BRAND_COLORS[new_color],
                notes=new_notes,
                industry=new_industry,
                currency=new_currency,
                timezone=new_timezone,
                monthly_budget=new_budget,
                benchmarks={
                    "target_ctr": bench_ctr,
                    "max_frequency": bench_freq,
                    "target_roas": bench_roas,
                    "max_cpa": bench_cpa,
                    "bleeder_ctr": bench_bleed_ctr,
                    "bleeder_spend": bench_bleed_spend,
                },
                tags=tags,
            )
            st.success(f"Profile '{new_name}' created! ID: {profile['id']}")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: ACTIVE PROFILE — DETAILED VIEW + EDIT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_active:
    active = get_active_profile()
    active_id = get_active_profile_id()

    if not active:
        st.info("No active profile. Create or select one.")
    else:
        color = active.get("brand_color", "#0078D4")
        st.markdown(
            f'<div style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%); '
            f'padding: 20px 30px; border-radius: 12px; margin-bottom: 16px;">'
            f'<h2 style="color: white; margin: 0;">{active["name"]}</h2>'
            f'<p style="color: rgba(255,255,255,0.85); margin: 4px 0 0 0;">'
            f'{active.get("business_name", "")} | {active.get("industry", "N/A")} | {active.get("currency", "USD")}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Quick stats
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        col_q1.metric("Extractions", active.get("total_extractions", 0))
        col_q2.metric("Monthly Budget", f"${active.get('monthly_budget', 0):,.0f}")
        last_conn = active.get("last_connected")
        col_q3.metric("Last Connected", last_conn[:10] if last_conn else "Never")
        col_q4.metric("Created", active.get("created_at", "")[:10])

        st.markdown("---")

        edit_tab, bench_tab, kpi_tab, workspace_tab = st.tabs([
            "Edit Profile", "Benchmarks", "Custom KPIs", "Workspace",
        ])

        with edit_tab:
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                edit_name = st.text_input("Name", value=active.get("name", ""), key="pm_edit_name")
                edit_biz = st.text_input("Business Name", value=active.get("business_name", ""), key="pm_edit_biz")
                edit_industry = st.text_input("Industry", value=active.get("industry", ""), key="pm_edit_ind")
                edit_notes = st.text_area("Notes", value=active.get("notes", ""), key="pm_edit_notes")
            with col_e2:
                edit_token = st.text_input("Access Token", value=active.get("access_token", ""), type="password", key="pm_edit_token")
                edit_account = st.text_input("Ad Account ID", value=active.get("ad_account_id", ""), key="pm_edit_account")
                edit_currency = st.text_input("Currency", value=active.get("currency", "USD"), key="pm_edit_currency")
                edit_budget = st.number_input("Monthly Budget ($)", value=float(active.get("monthly_budget", 0)), key="pm_edit_budget")
                edit_tags = st.text_input("Tags", value=", ".join(active.get("tags", [])), key="pm_edit_tags")

            if st.button("Save Changes", type="primary", key="pm_save_edit"):
                tags = [t.strip() for t in edit_tags.split(",") if t.strip()] if edit_tags else []
                update_profile(
                    active_id,
                    name=edit_name,
                    business_name=edit_biz,
                    industry=edit_industry,
                    notes=edit_notes,
                    access_token=edit_token,
                    ad_account_id=edit_account,
                    currency=edit_currency,
                    monthly_budget=edit_budget,
                    tags=tags,
                )
                st.success("Profile updated!")
                st.rerun()

            st.markdown("---")
            if st.button("Delete This Profile", key="pm_delete_active"):
                delete_profile(active_id)
                st.warning("Profile deleted.")
                st.rerun()

        with bench_tab:
            st.markdown("### Performance Benchmarks")
            benchmarks = active.get("benchmarks", {})

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                b_ctr = st.number_input("Target CTR (%)", value=float(benchmarks.get("target_ctr", 2.0)), key="pm_b_ctr")
                b_roas = st.number_input("Target ROAS", value=float(benchmarks.get("target_roas", 3.0)), key="pm_b_roas")
            with col_b2:
                b_freq = st.number_input("Max Frequency", value=float(benchmarks.get("max_frequency", 3.5)), key="pm_b_freq")
                b_cpa = st.number_input("Max CPA ($)", value=float(benchmarks.get("max_cpa", 50.0)), key="pm_b_cpa")
            with col_b3:
                b_bleed_ctr = st.number_input("Bleeder CTR (%)", value=float(benchmarks.get("bleeder_ctr", 1.0)), key="pm_b_bleed_ctr")
                b_bleed_spend = st.number_input("Bleeder Spend ($)", value=float(benchmarks.get("bleeder_spend", 10.0)), key="pm_b_bleed_spend")

            if st.button("Save Benchmarks", type="primary", key="pm_save_bench"):
                update_profile(active_id, benchmarks={
                    "target_ctr": b_ctr,
                    "max_frequency": b_freq,
                    "target_roas": b_roas,
                    "max_cpa": b_cpa,
                    "bleeder_ctr": b_bleed_ctr,
                    "bleeder_spend": b_bleed_spend,
                })
                st.success("Benchmarks updated!")

        with kpi_tab:
            st.markdown("### Custom KPI Formulas")
            st.markdown("Define brand-specific KPIs using column names from your data.")

            custom_kpis = active.get("custom_kpi_formulas", [])
            if custom_kpis:
                for i, kpi in enumerate(custom_kpis):
                    col_k1, col_k2, col_k3 = st.columns([2, 3, 1])
                    with col_k1:
                        st.write(f"**{kpi['name']}**")
                    with col_k2:
                        st.code(kpi["formula"])
                    with col_k3:
                        if st.button("Remove", key=f"pm_rm_kpi_{i}"):
                            remove_custom_kpi(active_id, kpi["name"])
                            st.rerun()
            else:
                st.info("No custom KPIs defined yet.")

            st.markdown("### Add Custom KPI")
            col_nk1, col_nk2, col_nk3 = st.columns([2, 3, 1])
            with col_nk1:
                kpi_name = st.text_input("KPI Name", placeholder="e.g., Blended CPA", key="pm_kpi_name")
            with col_nk2:
                kpi_formula = st.text_input("Formula", placeholder="e.g., spend / conversions", key="pm_kpi_formula")
            with col_nk3:
                kpi_unit = st.selectbox("Unit", ["$", "%", "x", "", "count"], key="pm_kpi_unit")
            if st.button("Add KPI", key="pm_add_kpi"):
                if kpi_name and kpi_formula:
                    add_custom_kpi(active_id, kpi_name, kpi_formula, kpi_unit)
                    st.success(f"Added KPI: {kpi_name}")
                    st.rerun()

        with workspace_tab:
            st.markdown("### Workspace Settings")
            st.markdown("These settings auto-restore when you switch to this profile.")

            ws = active.get("workspace", {})
            st.write(f"**Last Page:** {ws.get('last_page', 'N/A')}")
            st.write(f"**Last Date Preset:** {ws.get('last_date_preset', 'last_30d')}")
            st.write(f"**Last Levels:** {', '.join(ws.get('last_levels', ['ad']))}")
            st.write(f"**Last Breakdowns:** {', '.join(ws.get('last_breakdowns', ['none']))}")

            st.markdown("### Favorite Pages")
            fav_pages = active.get("favorite_pages", [])
            all_pages = [
                "Campaign Manager", "Ad Sets", "Ads", "Audiences",
                "Budget Center", "Performance", "Rules Engine", "A/B Testing",
                "Funnel & Attribution", "Report Builder", "Activity Log",
                "Data Studio", "Settings",
            ]
            selected_pages = st.multiselect(
                "Pin your most-used pages",
                all_pages,
                default=fav_pages,
                key="pm_fav_pages",
            )
            if st.button("Save Favorite Pages", key="pm_save_fav_pages"):
                update_profile(active_id, favorite_pages=selected_pages)
                st.success("Favorite pages updated!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: IMPORT / EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_import:
    st.markdown('<div class="section-title">Import / Export Profiles</div>', unsafe_allow_html=True)

    col_ie1, col_ie2 = st.columns(2)

    with col_ie1:
        st.markdown("### Export")
        st.markdown("Export profiles as JSON for backup or sharing. Credentials are excluded for security.")

        profiles = get_all_profiles()
        export_selection = st.multiselect(
            "Select profiles to export",
            options=list(profiles.keys()),
            default=list(profiles.keys()),
            format_func=lambda x: profiles[x]["name"],
            key="pm_export_sel",
        )

        if st.button("Generate Export", type="primary", key="pm_export"):
            if export_selection:
                export_data = export_profiles(export_selection)
                st.download_button(
                    "Download JSON",
                    data=export_data,
                    file_name=f"meta_profiles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="pm_download",
                )
                with st.expander("Preview export"):
                    st.json(json.loads(export_data))
            else:
                st.warning("Select at least one profile to export.")

    with col_ie2:
        st.markdown("### Import")
        st.markdown("Import profiles from a JSON file. You'll need to re-enter credentials after importing.")

        uploaded = st.file_uploader("Upload profiles JSON", type=["json"], key="pm_upload")
        overwrite = st.checkbox("Overwrite existing profiles with same ID", key="pm_overwrite")

        if uploaded and st.button("Import Profiles", type="primary", key="pm_import"):
            try:
                data = uploaded.read().decode("utf-8")
                imported = import_profiles(data, overwrite=overwrite)
                st.success(f"Imported {len(imported)} profile(s): {', '.join(imported)}")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: ACTIVITY LOG
# ═══════════════════════════════════════════════════════════════════════════════

with tab_activity:
    st.markdown('<div class="section-title">Recent Activity</div>', unsafe_allow_html=True)

    activity = get_recent_activity(50)
    if activity:
        rows = []
        for entry in activity:
            rows.append({
                "Time": entry.get("timestamp", "")[:19].replace("T", " "),
                "Action": entry.get("action", "").title(),
                "Profile": entry.get("profile", ""),
                "Details": entry.get("details", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=500)
    else:
        st.info("No activity recorded yet. Create a profile to get started.")
