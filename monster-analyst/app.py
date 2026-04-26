"""
Monster Data Analyst -- Ultimate MarTech Expert Analysis Platform
Main application entry point.
"""
import io
import os
import json
import re
import logging
import streamlit as st
import pandas as pd

from src.helpers import WINDOWS_11_CSS, load_custom_metrics, save_custom_metrics, strip_timezone_for_excel, downloadable_dataframe
from src.data_importer import (
    import_csv, import_excel, import_json, import_google_sheet,
    normalize_columns, detect_column_types, coerce_column_types,
    auto_import,
)
from src.metric_catalog import CATEGORIES, METRICS, METRICS_BY_CATEGORY, get_metrics_for_available_columns
from src.formula_engine import apply_formula_to_df, evaluate_formula, validate_formula, bulk_apply_metrics

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MonsterAnalyst")


st.set_page_config(
    page_title="Monster Data Analyst",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

if "datasets" not in st.session_state:
    st.session_state.datasets = {}  # {name: DataFrame}
if "dataset_sources" not in st.session_state:
    st.session_state.dataset_sources = {}  # {name: source_type}
if "merged_data" not in st.session_state:
    st.session_state.merged_data = None
if "custom_metrics" not in st.session_state:
    st.session_state.custom_metrics = load_custom_metrics()
if "active_dataset" not in st.session_state:
    st.session_state.active_dataset = None
if "computed_metrics_df" not in st.session_state:
    st.session_state.computed_metrics_df = None


def _apply_entity_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar entity filters to any DataFrame."""
    for key in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        filt = st.session_state.get(key)
        if filt:
            col, vals = filt
            if col in df.columns:
                df = df[df[col].astype(str).isin(vals)]
    return df


def get_active_df() -> pd.DataFrame:
    """Get the currently active dataset, with entity filters applied."""
    name = st.session_state.active_dataset
    if name and name in st.session_state.datasets:
        df = st.session_state.datasets[name]
    elif st.session_state.merged_data is not None:
        df = st.session_state.merged_data
    else:
        return pd.DataFrame()
    return _apply_entity_filters(df)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div style="text-align:center; padding: 1rem 0;">'
        '<h2 style="color:#00B7C3; margin:0;">Monster Analyst</h2>'
        '<p style="color:#8899aa; font-size:0.8rem; margin:0;">MarTech Expert Analysis</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Dataset selector
    ds_names = list(st.session_state.datasets.keys())
    has_merged = st.session_state.merged_data is not None
    options = ds_names + (["[Merged Dataset]"] if has_merged else [])

    if options:
        active = st.selectbox(
            "Active Dataset",
            options,
            index=0 if not st.session_state.active_dataset else (
                options.index(st.session_state.active_dataset)
                if st.session_state.active_dataset in options else 0
            ),
            key="sidebar_dataset",
        )
        prev_active = st.session_state.active_dataset
        if active == "[Merged Dataset]":
            st.session_state.active_dataset = None
        else:
            st.session_state.active_dataset = active
        if st.session_state.active_dataset != prev_active:
            st.session_state.computed_metrics_df = None

        active_df = get_active_df()
        if not active_df.empty:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>Active Data</h3>'
                f'<div class="metric-value">{len(active_df):,}</div>'
                f'<div class="metric-trend">{len(active_df.columns)} columns</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Entity filter (campaign / ad set / ad)
            st.markdown("**Filter by Entity**")
            entity_cols = {
                "Campaign": ["campaign_name", "campaign_id"],
                "Ad Set": ["adset_name", "adset_id"],
                "Ad": ["ad_name", "ad_id"],
            }
            for label, col_candidates in entity_cols.items():
                matching_col = None
                for c in col_candidates:
                    if c in active_df.columns:
                        matching_col = c
                        break
                if matching_col:
                    unique_vals = sorted(active_df[matching_col].dropna().unique().astype(str).tolist())
                    if unique_vals:
                        selected = st.multiselect(
                            f"{label}",
                            unique_vals,
                            key=f"filter_{label.lower().replace(' ', '_')}",
                        )
                        if selected:
                            st.session_state[f"entity_filter_{label.lower().replace(' ', '_')}"] = (matching_col, selected)
                        else:
                            st.session_state.pop(f"entity_filter_{label.lower().replace(' ', '_')}", None)
    else:
        st.info("No datasets loaded yet. Upload data to begin.")

    st.markdown("---")

    # Quick stats
    if st.session_state.datasets:
        st.markdown("**Loaded Sources**")
        for name, df in st.session_state.datasets.items():
            src_type = st.session_state.dataset_sources.get(name, "")
            st.markdown(f"- **{name}** ({len(df):,} rows) `{src_type}`")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT -- TABS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(
    '<h1 style="color:#0078D4; font-weight:700;">Monster Data Analyst</h1>'
    '<p style="color:#666; margin-top:-10px;">Import, Link, and Deeply Analyze Your Marketing Data</p>',
    unsafe_allow_html=True,
)

tab_import, tab_link, tab_kpi, tab_explore, tab_metrics, tab_export = st.tabs([
    "Import Data",
    "Link & Merge",
    "KPI Dashboard",
    "Data Explorer",
    "Metric Lab",
    "Export",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: IMPORT DATA
# ═══════════════════════════════════════════════════════════════════════════════

with tab_import:
    st.markdown('<div class="section-title">Import Data from Any Source</div>', unsafe_allow_html=True)

    col_file, col_gsheet = st.columns(2)

    with col_file:
        st.markdown("#### Upload Files")
        st.markdown("Supports CSV, JSON, Excel (.xlsx)")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["csv", "json", "xlsx", "xls"],
            accept_multiple_files=True,
            key="file_uploader",
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name in st.session_state.datasets:
                    continue
                try:
                    src_type, data = auto_import(uploaded_file)
                    if isinstance(data, dict):
                        # Multi-sheet (Excel or JSON with datasets)
                        for sheet_name, df in data.items():
                            if not df.empty:
                                key = f"{uploaded_file.name} :: {sheet_name}"
                                normalized = normalize_columns(df)
                                types = detect_column_types(normalized)
                                st.session_state.datasets[key] = coerce_column_types(normalized, types)
                                st.session_state.dataset_sources[key] = src_type
                                if not st.session_state.active_dataset:
                                    st.session_state.active_dataset = key
                    elif isinstance(data, pd.DataFrame) and not data.empty:
                        normalized = normalize_columns(data)
                        types = detect_column_types(normalized)
                        st.session_state.datasets[uploaded_file.name] = coerce_column_types(normalized, types)
                        st.session_state.dataset_sources[uploaded_file.name] = src_type
                        if not st.session_state.active_dataset:
                            st.session_state.active_dataset = uploaded_file.name
                    if uploaded_file.name in st.session_state.datasets or any(k.startswith(f"{uploaded_file.name} :: ") for k in st.session_state.datasets):
                        st.success(f"Imported: {uploaded_file.name}")
                    else:
                        st.warning(f"No data found in: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Failed to import {uploaded_file.name}: {e}")

    with col_gsheet:
        st.markdown("#### Google Sheets (Public Link)")
        st.markdown("Paste a public Google Sheets URL")
        gsheet_url = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...", key="gsheet_url")
        gsheet_name = st.text_input("Dataset Name", placeholder="CRM Orders", key="gsheet_name")
        if st.button("Import Google Sheet", type="primary", key="btn_gsheet"):
            if gsheet_url and gsheet_name:
                try:
                    df = import_google_sheet(gsheet_url)
                    normalized = normalize_columns(df)
                    types = detect_column_types(normalized)
                    st.session_state.datasets[gsheet_name] = coerce_column_types(normalized, types)
                    st.session_state.dataset_sources[gsheet_name] = "google_sheet"
                    if not st.session_state.active_dataset:
                        st.session_state.active_dataset = gsheet_name
                    st.success(f"Imported {len(df):,} rows from Google Sheets")
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.warning("Enter both a URL and a name for the dataset.")

    # Meta Dashboard Import
    st.markdown("---")
    st.markdown("#### Import Meta Dashboard Output Folder")
    st.markdown("If you have exported data from the Meta Ads Dashboard, paste the output folder path:")
    meta_folder = st.text_input("Output Folder Path", placeholder="/path/to/output/run_YYYYMMDD_HHMMSS", key="meta_folder")
    if st.button("Import Meta Dashboard Output", key="btn_meta_import"):
        if meta_folder and os.path.isdir(meta_folder):
            try:
                from src.data_importer import import_meta_dashboard_output
                datasets = import_meta_dashboard_output(meta_folder)
                for name, df in datasets.items():
                    if not df.empty:
                        key = f"Meta :: {name}"
                        normalized = normalize_columns(df)
                        types = detect_column_types(normalized)
                        st.session_state.datasets[key] = coerce_column_types(normalized, types)
                        st.session_state.dataset_sources[key] = "meta_dashboard"
                        if not st.session_state.active_dataset:
                            st.session_state.active_dataset = key
                st.success(f"Imported {len(datasets)} datasets from Meta Dashboard")
            except Exception as e:
                st.error(f"Failed: {e}")
        else:
            st.warning("Enter a valid folder path.")

    # Preview loaded datasets
    if st.session_state.datasets:
        st.markdown("---")
        st.markdown("#### Loaded Datasets")
        for name, df in st.session_state.datasets.items():
            with st.expander(f"{name} ({len(df):,} rows, {len(df.columns)} columns)"):
                types = detect_column_types(df)
                col_info = pd.DataFrame([
                    {"Column": col, "Type": types.get(col, "unknown"), "Sample": str(df[col].iloc[0]) if len(df) > 0 else ""}
                    for col in df.columns
                ])
                downloadable_dataframe(col_info, key=f"colinfo_{name}", label=f"columns_{name}", use_container_width=True, hide_index=True)
                downloadable_dataframe(df.head(5), key=f"preview_{name}", label=f"preview_{name}", use_container_width=True, hide_index=True)

                if st.button(f"Remove {name}", key=f"rm_{name}"):
                    del st.session_state.datasets[name]
                    if st.session_state.active_dataset == name:
                        st.session_state.active_dataset = None
                    st.session_state.computed_metrics_df = None
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: LINK & MERGE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_link:
    st.markdown('<div class="section-title">Link & Merge Multi-Source Data</div>', unsafe_allow_html=True)
    st.markdown("Combine data from Meta Ads, Google Ads, CRM, Order Sheets, and any other source.")

    ds_names = list(st.session_state.datasets.keys())

    if len(ds_names) < 2:
        st.info("**This step is optional.** You can analyze a single dataset without linking. "
                "To link/merge, upload 2+ datasets in the Import tab (e.g. Meta CSV + Orders sheet).")
    else:
        from src.data_linker import suggest_join_columns, join_datasets, join_preview as _join_preview

        col_l, col_r = st.columns(2)
        with col_l:
            left_ds = st.selectbox("Left Dataset (Primary)", ds_names, key="link_left")
        with col_r:
            right_ds = st.selectbox("Right Dataset (Secondary)", [n for n in ds_names if n != left_ds], key="link_right")

        if left_ds and right_ds:
            df_left = st.session_state.datasets[left_ds]
            df_right = st.session_state.datasets[right_ds]

            # Auto-suggest join columns
            suggestions = suggest_join_columns(df_left, df_right)

            st.markdown("#### Column Mapping")
            col_map_l, col_map_r, col_map_how = st.columns(3)

            default_left = suggestions[0]["left_column"] if suggestions else df_left.columns[0]
            default_right = suggestions[0]["right_column"] if suggestions else df_right.columns[0]

            with col_map_l:
                left_col = st.selectbox(
                    "Left Join Column",
                    df_left.columns.tolist(),
                    index=df_left.columns.tolist().index(default_left) if default_left in df_left.columns else 0,
                    key="join_left_col",
                )
            with col_map_r:
                right_col = st.selectbox(
                    "Right Join Column",
                    df_right.columns.tolist(),
                    index=df_right.columns.tolist().index(default_right) if default_right in df_right.columns else 0,
                    key="join_right_col",
                )
            with col_map_how:
                join_type = st.selectbox(
                    "Join Type",
                    ["left", "inner", "right", "outer"],
                    index=0,
                    key="join_type",
                    help="Left: Keep all left rows. Inner: Only matched. Outer: Keep all.",
                )

            if suggestions:
                with st.expander("Auto-Detected Column Suggestions"):
                    for s in suggestions[:5]:
                        conf_label = "High" if s["confidence"] > 0.7 else "Medium" if s["confidence"] > 0.4 else "Low"
                        st.markdown(f"- `{s['left_column']}` ↔ `{s['right_column']}` (confidence: {conf_label})")

            col_preview, col_merge = st.columns(2)
            with col_preview:
                if st.button("Preview Join", key="btn_preview_join"):
                    preview = _join_preview(df_left, df_right, left_col, right_col, join_type)
                    st.markdown(f"""
                    **Join Preview:**
                    - Left rows: {preview['left_rows']:,} | Right rows: {preview['right_rows']:,}
                    - Matched keys: {preview['matched_keys']:,}
                    - Match rate (left): {preview['match_rate_left']}% | Match rate (right): {preview['match_rate_right']}%
                    - Left-only keys: {preview['left_only_keys']:,} | Right-only keys: {preview['right_only_keys']:,}
                    """)
                    if preview["sample_matched"]:
                        st.markdown(f"Sample matched keys: `{'`, `'.join(preview['sample_matched'][:5])}`")
                    downloadable_dataframe(preview["preview_df"].head(5), key="join_preview", label="join_preview", use_container_width=True, hide_index=True)

            with col_merge:
                if st.button("Execute Merge", type="primary", key="btn_merge"):
                    try:
                        merged = join_datasets(df_left, df_right, left_col, right_col, join_type)
                        st.session_state.merged_data = merged
                        st.session_state.active_dataset = None  # Switch to merged view
                        st.success(f"Merged! Result: {len(merged):,} rows, {len(merged.columns)} columns")
                    except Exception as e:
                        st.error(f"Merge failed: {e}")

        if st.session_state.merged_data is not None:
            st.markdown("---")
            st.markdown("#### Merged Dataset Preview")
            merged = st.session_state.merged_data
            st.markdown(f"**{len(merged):,} rows** x **{len(merged.columns)} columns**")
            downloadable_dataframe(merged.head(20), key="merged_preview", label="merged_data", use_container_width=True, hide_index=True)

            merged_name = st.text_input("Save merged as dataset:", value="merged_data", key="merged_name")
            if st.button("Save Merged as New Dataset", key="btn_save_merged"):
                st.session_state.datasets[merged_name] = merged
                st.session_state.dataset_sources[merged_name] = "merged"
                st.session_state.active_dataset = merged_name
                st.success(f"Saved merged dataset as '{merged_name}'")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: KPI DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_kpi:
    st.markdown('<div class="section-title">KPI Dashboard</div>', unsafe_allow_html=True)

    active_df = get_active_df()
    if active_df.empty:
        st.info("No data loaded. Import data first.")
    else:
        available_cols = [c.lower() for c in active_df.columns]
        computable = get_metrics_for_available_columns(available_cols)

        if not computable:
            st.warning("No standard metrics can be computed from the available columns. Try importing ad performance data with columns like spend, impressions, clicks, etc.")
        else:
            # Group by category
            cat_metrics = {}
            for m in computable:
                cat = m["category"]
                if cat not in cat_metrics:
                    cat_metrics[cat] = []
                cat_metrics[cat].append(m)

            # Compute aggregated values
            # Non-additive (rate/ratio) columns are recomputed from their additive constituents
            RATE_COLUMNS = {
                "cpc": ("spend", "clicks"),
                "cpm": ("spend", "impressions"),
                "ctr": ("clicks", "impressions"),
                "frequency": ("impressions", "reach"),
                "outbound_ctr": ("outbound_clicks", "impressions"),
                "cost_per_action_type": ("spend", "actions"),
            }
            agg_ctx = {}
            for col in active_df.columns:
                col_lower = col.lower()
                if col_lower in RATE_COLUMNS:
                    num_col, den_col = RATE_COLUMNS[col_lower]
                    if num_col in [c.lower() for c in active_df.columns] and den_col in [c.lower() for c in active_df.columns]:
                        num_actual = [c for c in active_df.columns if c.lower() == num_col][0]
                        den_actual = [c for c in active_df.columns if c.lower() == den_col][0]
                        try:
                            den_sum = float(active_df[den_actual].sum())
                            if den_sum != 0:
                                if col_lower == "cpm":
                                    agg_ctx[col_lower] = float(active_df[num_actual].sum()) / den_sum * 1000
                                elif col_lower == "ctr" or col_lower == "outbound_ctr":
                                    agg_ctx[col_lower] = float(active_df[num_actual].sum()) / den_sum * 100
                                else:
                                    agg_ctx[col_lower] = float(active_df[num_actual].sum()) / den_sum
                            else:
                                agg_ctx[col_lower] = 0.0
                        except (ValueError, TypeError):
                            pass
                    else:
                        # Constituents unavailable — use mean (not sum) for rate columns
                        try:
                            agg_ctx[col_lower] = float(active_df[col].mean())
                        except (ValueError, TypeError):
                            pass
                    continue
                try:
                    agg_ctx[col_lower] = float(active_df[col].sum())
                except (ValueError, TypeError):
                    pass

            for cat_id, metrics_list in cat_metrics.items():
                cat_info = CATEGORIES.get(cat_id, {"name": cat_id, "color": "#0078D4"})
                st.markdown(
                    f'<div class="section-title" style="background: {cat_info["color"]};">'
                    f'{cat_info["name"]} / {cat_info.get("name_ar", "")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                cols = st.columns(min(len(metrics_list), 5))
                for i, metric in enumerate(metrics_list):
                    with cols[i % len(cols)]:
                        try:
                            value = evaluate_formula(metric["formula"], agg_ctx)
                            unit = metric.get("unit", "")
                            if unit == "currency":
                                display = f"${value:,.2f}"
                            elif unit == "percentage":
                                display = f"{value:.2f}%"
                            elif unit == "ratio":
                                display = f"{value:.2f}"
                            else:
                                display = f"{value:,.2f}"

                            # Threshold badge
                            badge = ""
                            thresholds = metric.get("thresholds")
                            if thresholds:
                                healthy_t = thresholds.get("healthy", None)
                                warning_t = thresholds.get("warning", None)
                                critical_t = thresholds.get("critical", None)
                                if healthy_t is not None and critical_t is not None and healthy_t < critical_t:
                                    # Lower is better (e.g. fatigue, drop-off)
                                    if value <= healthy_t:
                                        badge = '<span class="badge-healthy">Healthy</span>'
                                    elif warning_t is not None and value <= warning_t:
                                        badge = '<span class="badge-warning">Warning</span>'
                                    elif value >= critical_t:
                                        badge = '<span class="badge-critical">Critical</span>'
                                    else:
                                        badge = '<span class="badge-warning">Warning</span>'
                                else:
                                    # Higher is better (e.g. ROAS, hook rate)
                                    if healthy_t is not None and value >= healthy_t:
                                        badge = '<span class="badge-healthy">Healthy</span>'
                                    elif warning_t is not None and value >= warning_t:
                                        badge = '<span class="badge-warning">Warning</span>'
                                    elif critical_t is not None and value <= critical_t:
                                        badge = '<span class="badge-critical">Critical</span>'
                                    else:
                                        badge = '<span class="badge-warning">Warning</span>'

                            st.markdown(
                                f'<div class="metric-card">'
                                f'<h3>{metric["name"]}</h3>'
                                f'<div class="metric-value">{display}</div>'
                                f'<div class="metric-trend">{metric.get("name_ar", "")} {badge}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        except Exception:
                            st.markdown(
                                f'<div class="metric-card">'
                                f'<h3>{metric["name"]}</h3>'
                                f'<div class="metric-value">N/A</div>'
                                f'<div class="metric-trend">{metric.get("description", "")}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

            # Show saved custom metrics in KPI dashboard too
            if st.session_state.custom_metrics:
                st.markdown(
                    '<div class="section-title" style="background: #00B7C3;">Custom Metrics (Saved)</div>',
                    unsafe_allow_html=True,
                )
                custom_cols = st.columns(min(len(st.session_state.custom_metrics), 5))
                for i, cm in enumerate(st.session_state.custom_metrics):
                    with custom_cols[i % len(custom_cols)]:
                        try:
                            val = evaluate_formula(cm["formula"], agg_ctx)
                            unit = cm.get("unit", "number")
                            if unit == "currency":
                                disp = f"${val:,.2f}"
                            elif unit == "percentage":
                                disp = f"{val:.2f}%"
                            elif unit == "ratio":
                                disp = f"{val:.2f}"
                            else:
                                disp = f"{val:,.2f}"
                            st.markdown(
                                f'<div class="metric-card"><h3>{cm["name"]}</h3>'
                                f'<div class="metric-value">{disp}</div>'
                                f'<div class="metric-trend">{cm.get("name_ar", "")}</div></div>',
                                unsafe_allow_html=True,
                            )
                        except Exception:
                            st.markdown(
                                f'<div class="metric-card"><h3>{cm["name"]}</h3>'
                                f'<div class="metric-value">N/A</div>'
                                f'<div class="metric-trend">{cm.get("description", "")}</div></div>',
                                unsafe_allow_html=True,
                            )

            # Quick add custom metric inline
            with st.expander("Quick Add Custom Metric"):
                qc_name = st.text_input("Name", placeholder="My ROAS", key="kpi_qc_name")
                qc_formula = st.text_input("Formula", placeholder="purchase_conversion_value / spend", key="kpi_qc_formula")
                qc_unit = st.selectbox("Unit", ["number", "currency", "percentage", "ratio"], key="kpi_qc_unit")
                if st.button("Save & Add", type="primary", key="kpi_qc_save"):
                    if qc_name and qc_formula:
                        error = validate_formula(qc_formula)
                        if error:
                            st.error(f"Invalid formula: {error}")
                        else:
                            new_cm = {
                                "id": qc_name.lower().replace(" ", "_"),
                                "name": qc_name,
                                "name_ar": qc_name,
                                "formula": qc_formula,
                                "category": "custom",
                                "unit": qc_unit,
                            }
                            existing_ids = {m["id"] for m in st.session_state.custom_metrics}
                            if new_cm["id"] not in existing_ids:
                                st.session_state.custom_metrics.append(new_cm)
                            save_custom_metrics(st.session_state.custom_metrics)
                            st.success(f"Saved '{qc_name}'")
                            st.rerun()

            # Row-level metric computation
            st.markdown("---")
            st.markdown("#### Row-Level Metrics")
            st.markdown("Compute metrics for each row (campaign, ad set, ad, etc.)")
            if st.button("Compute All Available Metrics", type="primary", key="btn_compute_kpis"):
                result_df = bulk_apply_metrics(active_df, computable)
                st.session_state.computed_metrics_df = result_df
                new_cols = [c for c in result_df.columns if c not in active_df.columns]
                st.success(f"Computed {len(new_cols)} metrics across {len(result_df):,} rows")
                downloadable_dataframe(result_df[list(active_df.columns[:3]) + new_cols].head(20), key="row_metrics", label="row_metrics", use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_explore:
    st.markdown('<div class="section-title">Data Explorer</div>', unsafe_allow_html=True)

    active_df = get_active_df()
    if active_df.empty:
        st.info("No data loaded. Import data first.")
    else:
        # Use computed metrics if available
        df_display = _apply_entity_filters(st.session_state.computed_metrics_df) if st.session_state.computed_metrics_df is not None else active_df

        explore_tabs = st.tabs(["Table View", "Pivot Table", "Charts", "Statistics", "Period Comparison"])

        # ------ Table View ------
        with explore_tabs[0]:
            st.markdown("#### Filter & Sort")
            filter_cols = st.multiselect("Select columns to display", df_display.columns.tolist(), default=df_display.columns.tolist()[:15], key="table_cols")
            if filter_cols:
                # Add text filter
                text_filter = st.text_input("Search rows (any column)", key="table_search")
                filtered = df_display[filter_cols]
                if text_filter:
                    mask = filtered.astype(str).apply(lambda x: x.str.contains(text_filter, case=False, na=False)).any(axis=1)
                    filtered = filtered[mask]
                downloadable_dataframe(filtered, key="data_explorer", label="data_explorer", use_container_width=True, hide_index=True, height=500)
                st.markdown(f"Showing {len(filtered):,} of {len(df_display):,} rows")

        # ------ Pivot Table ------
        with explore_tabs[1]:
            st.markdown("#### Pivot Table")
            numeric_cols = df_display.select_dtypes(include=["number"]).columns.tolist()
            text_cols = df_display.select_dtypes(exclude=["number"]).columns.tolist()

            col_idx, col_val, col_agg = st.columns(3)
            with col_idx:
                pivot_rows = st.multiselect("Row Dimensions", text_cols, default=text_cols[:1] if text_cols else [], key="pivot_rows")
            with col_val:
                pivot_values = st.multiselect("Value Columns", numeric_cols, default=numeric_cols[:3] if numeric_cols else [], key="pivot_values")
            with col_agg:
                pivot_agg = st.selectbox("Aggregation", ["sum", "mean", "median", "min", "max", "count"], key="pivot_agg")

            if pivot_rows and pivot_values:
                try:
                    pivot = df_display.groupby(pivot_rows, as_index=False)[pivot_values].agg(pivot_agg)
                    downloadable_dataframe(pivot, key="pivot_table", label="pivot_table", use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Pivot error: {e}")

        # ------ Charts ------
        with explore_tabs[2]:
            import plotly.express as px

            st.markdown("#### Visualize Data")
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie", "Heatmap", "Funnel"], key="chart_type")

            all_cols = df_display.columns.tolist()
            numeric_cols = df_display.select_dtypes(include=["number"]).columns.tolist()

            col_x, col_y, col_color = st.columns(3)
            with col_x:
                x_col = st.selectbox("X Axis", all_cols, key="chart_x")
            with col_y:
                y_col = st.selectbox("Y Axis", numeric_cols if numeric_cols else all_cols, key="chart_y")
            with col_color:
                color_col = st.selectbox("Color / Group", ["None"] + all_cols, key="chart_color")

            color = color_col if color_col != "None" else None

            try:
                if chart_type == "Bar":
                    fig = px.bar(df_display, x=x_col, y=y_col, color=color, template="plotly_white")
                elif chart_type == "Line":
                    fig = px.line(df_display, x=x_col, y=y_col, color=color, template="plotly_white")
                elif chart_type == "Scatter":
                    fig = px.scatter(df_display, x=x_col, y=y_col, color=color, template="plotly_white")
                elif chart_type == "Pie":
                    fig = px.pie(df_display, names=x_col, values=y_col, template="plotly_white")
                elif chart_type == "Heatmap":
                    if len(numeric_cols) >= 2:
                        corr = df_display[numeric_cols[:10]].corr()
                        import plotly.graph_objects as go
                        fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.columns, colorscale="RdBu"))
                    else:
                        fig = px.bar(df_display, x=x_col, y=y_col, template="plotly_white")
                elif chart_type == "Funnel":
                    fig = px.funnel(df_display.head(10), x=y_col, y=x_col, template="plotly_white")
                else:
                    fig = px.bar(df_display, x=x_col, y=y_col, template="plotly_white")

                fig.update_layout(
                    font_family="Segoe UI",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Chart error: {e}")

        # ------ Statistics ------
        with explore_tabs[3]:
            st.markdown("#### Statistical Summary")
            numeric_cols = df_display.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                stats = df_display[numeric_cols].describe().T
                stats["cv%"] = (stats["std"] / stats["mean"] * 100).round(2)
                downloadable_dataframe(stats, key="statistics", label="statistics", use_container_width=True)

                # Correlation matrix
                st.markdown("#### Correlation Matrix")
                if len(numeric_cols) >= 2:
                    sel_corr_cols = st.multiselect("Select columns", numeric_cols, default=numeric_cols[:8], key="corr_cols")
                    if len(sel_corr_cols) >= 2:
                        corr = df_display[sel_corr_cols].corr()
                        try:
                            downloadable_dataframe(corr.style.background_gradient(cmap="RdBu", vmin=-1, vmax=1), key="correlation", label="correlation_matrix", use_container_width=True)
                        except ImportError:
                            downloadable_dataframe(corr, key="correlation_plain", label="correlation_matrix", use_container_width=True)
            else:
                st.info("No numeric columns found for statistical analysis.")

        # ------ Period Comparison ------
        with explore_tabs[4]:
            st.markdown("#### Period-over-Period Comparison")
            date_cols = [c for c in df_display.columns if df_display[c].dtype in ("datetime64[ns]", "object") and any(kw in c.lower() for kw in ("date", "day", "time", "period"))]
            if date_cols:
                date_col = st.selectbox("Date Column", date_cols, key="period_date")
                compare_metric = st.selectbox("Metric to Compare", numeric_cols if numeric_cols else [], key="period_metric")
                if date_col and compare_metric:
                    try:
                        df_temp = df_display.copy()
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
                        df_temp = df_temp.dropna(subset=[date_col])
                        daily = df_temp.groupby(df_temp[date_col].dt.date)[compare_metric].sum().reset_index()
                        daily.columns = ["date", compare_metric]
                        fig = px.line(daily, x="date", y=compare_metric, template="plotly_white", title=f"{compare_metric} Over Time")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("No date columns detected. Ensure your data has a column like 'date_start', 'date', or 'day'.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: METRIC LAB
# ═══════════════════════════════════════════════════════════════════════════════

with tab_metrics:
    st.markdown('<div class="section-title">Metric Lab -- Custom Metrics & DAX-like Formulas</div>', unsafe_allow_html=True)

    metric_tabs = st.tabs(["Pre-built Library", "Custom Formula", "Bulk Metrics", "DAX Export"])

    # ------ Pre-built Library ------
    with metric_tabs[0]:
        st.markdown("#### 125+ Pre-Built MarTech Metrics")
        st.markdown("Select categories to browse available metrics:")

        selected_cats = st.multiselect(
            "Categories",
            [(cid, f"{ci['name']} / {ci['name_ar']}") for cid, ci in CATEGORIES.items()],
            format_func=lambda x: x[1],
            default=[(cid, f"{ci['name']} / {ci['name_ar']}") for cid, ci in list(CATEGORIES.items())[:3]],
            key="metric_cats",
        )
        selected_cat_ids = [c[0] for c in selected_cats] if selected_cats else list(CATEGORIES.keys())

        for cat_id in selected_cat_ids:
            cat_info = CATEGORIES[cat_id]
            metrics_in_cat = METRICS_BY_CATEGORY.get(cat_id, [])
            if not metrics_in_cat:
                continue
            st.markdown(
                f'<div class="section-title" style="background: {cat_info["color"]};">'
                f'{cat_info["name"]} ({len(metrics_in_cat)} metrics)</div>',
                unsafe_allow_html=True,
            )
            metric_data = []
            for m in metrics_in_cat:
                metric_data.append({
                    "ID": m["id"],
                    "Name": m["name"],
                    "Arabic": m.get("name_ar", ""),
                    "Formula": m["formula"],
                    "Level": m.get("level", "all"),
                    "Unit": m.get("unit", ""),
                    "Description": m.get("description", ""),
                })
            downloadable_dataframe(pd.DataFrame(metric_data), key=f"metric_catalog_{cat_id}", label=f"metric_catalog_{cat_id}", use_container_width=True, hide_index=True)

    # ------ Custom Formula ------
    with metric_tabs[1]:
        st.markdown("#### Create Custom Metric")
        st.markdown("Write formulas using column names from your data. Supported: `+`, `-`, `*`, `/`, `()`, `round()`, `sqrt()`, `abs()`, `min()`, `max()`, `log()`, `pow()`")

        active_df = get_active_df()
        if not active_df.empty:
            with st.expander("Available columns"):
                st.code(", ".join(active_df.columns.tolist()))

        custom_name = st.text_input("Metric Name", placeholder="My Custom ROAS", key="custom_name")
        custom_name_ar = st.text_input("Arabic Name (optional)", placeholder="", key="custom_name_ar")
        custom_formula = st.text_input("Formula", placeholder="purchase_conversion_value / spend", key="custom_formula")
        custom_unit = st.selectbox("Unit", ["number", "currency", "percentage", "ratio"], key="custom_unit")
        custom_desc = st.text_input("Description (optional)", placeholder="What this metric measures", key="custom_desc")

        col_validate, col_apply, col_save = st.columns(3)
        with col_validate:
            if st.button("Validate Formula", key="btn_validate"):
                if custom_formula:
                    error = validate_formula(custom_formula)
                    if error:
                        st.error(f"Invalid: {error}")
                    else:
                        from src.formula_engine import extract_variables
                        vars_used = extract_variables(custom_formula)
                        st.success(f"Valid! References: {', '.join(vars_used)}")
        with col_apply:
            if st.button("Apply to Data", type="primary", key="btn_apply_custom"):
                if custom_formula and custom_name and not active_df.empty:
                    try:
                        result = apply_formula_to_df(active_df, custom_formula, custom_name)
                        preview = active_df.copy()
                        preview[custom_name] = result
                        downloadable_dataframe(preview[[active_df.columns[0], custom_name]].head(10), key="metric_preview", label="metric_preview", use_container_width=True, hide_index=True)
                        st.success(f"Applied '{custom_name}' to {len(active_df):,} rows")
                    except Exception as e:
                        st.error(f"Error: {e}")
        with col_save:
            if st.button("Save Permanently", key="btn_save_custom"):
                if custom_formula and custom_name:
                    new_metric = {
                        "id": custom_name.lower().replace(" ", "_"),
                        "name": custom_name,
                        "name_ar": custom_name_ar or custom_name,
                        "formula": custom_formula,
                        "category": "custom",
                        "unit": custom_unit,
                        "description": custom_desc or "",
                    }
                    existing_ids = {m["id"] for m in st.session_state.custom_metrics}
                    if new_metric["id"] in existing_ids:
                        st.session_state.custom_metrics = [
                            m if m["id"] != new_metric["id"] else new_metric
                            for m in st.session_state.custom_metrics
                        ]
                        st.success(f"Updated '{custom_name}' (saved permanently)")
                    else:
                        st.session_state.custom_metrics.append(new_metric)
                        st.success(f"Saved '{custom_name}' permanently")
                    save_custom_metrics(st.session_state.custom_metrics)
                else:
                    st.warning("Enter both a name and a formula.")

        # Show saved custom metrics
        if st.session_state.custom_metrics:
            st.markdown("---")
            st.markdown("#### Saved Custom Metrics")
            cm_data = []
            for m in st.session_state.custom_metrics:
                cm_data.append({
                    "Name": m["name"],
                    "Arabic": m.get("name_ar", ""),
                    "Formula": m["formula"],
                    "Unit": m.get("unit", "number"),
                    "Description": m.get("description", ""),
                })
            downloadable_dataframe(pd.DataFrame(cm_data), key="custom_metrics", label="custom_metrics", use_container_width=True, hide_index=True)

            # Delete custom metric
            del_metric = st.selectbox(
                "Remove a saved metric",
                ["(none)"] + [m["name"] for m in st.session_state.custom_metrics],
                key="del_custom_metric",
            )
            if del_metric != "(none)" and st.button("Delete Selected Metric", key="btn_del_custom"):
                st.session_state.custom_metrics = [
                    m for m in st.session_state.custom_metrics if m["name"] != del_metric
                ]
                save_custom_metrics(st.session_state.custom_metrics)
                st.success(f"Deleted '{del_metric}'")
                st.rerun()

    # ------ Bulk Metrics ------
    with metric_tabs[2]:
        st.markdown("#### Bulk Metric Application")
        st.markdown("Apply all computable pre-built metrics to your dataset at once.")

        active_df = get_active_df()
        if not active_df.empty:
            available_cols = [c.lower() for c in active_df.columns]
            computable = get_metrics_for_available_columns(available_cols)
            st.markdown(f"**{len(computable)} metrics** can be computed from your {len(active_df.columns)} columns.")

            if computable:
                selected_metrics = st.multiselect(
                    "Select metrics to compute",
                    [(m["id"], f"{m['name']} -- {m['formula']}") for m in computable],
                    format_func=lambda x: x[1],
                    default=[(m["id"], f"{m['name']} -- {m['formula']}") for m in computable],
                    key="bulk_metrics_select",
                )
                selected_ids = [s[0] for s in selected_metrics]
                selected = [m for m in computable if m["id"] in selected_ids]

                if st.button(f"Compute {len(selected)} Metrics", type="primary", key="btn_bulk_compute"):
                    result = bulk_apply_metrics(active_df, selected)
                    new_cols = [c for c in result.columns if c not in active_df.columns]
                    st.session_state.computed_metrics_df = result
                    st.success(f"Computed {len(new_cols)} metrics across {len(result):,} rows!")
                    downloadable_dataframe(result[new_cols].head(20), key="bulk_metrics", label="bulk_metrics", use_container_width=True, hide_index=True)
        else:
            st.info("Import data first.")

    # ------ DAX Export ------
    with metric_tabs[3]:
        st.markdown("#### Export Metrics as DAX Measures")
        st.markdown("Generate Power BI DAX measures for all your metrics.")

        active_df = get_active_df()
        if not active_df.empty:
            available_cols = [c.lower() for c in active_df.columns]
            computable = get_metrics_for_available_columns(available_cols)

            if computable:
                dax_measures = []
                for m in computable:
                    formula = m["formula"]
                    # Convert Python-style to DAX-style
                    dax_formula = formula
                    for col in sorted(m.get("required_columns", []), key=len, reverse=True):
                        dax_formula = re.sub(r'\b' + re.escape(col) + r'\b', f"SUM('{col}')", dax_formula)
                    dax_measures.append(f'{m["name"]} = {dax_formula}')

                dax_text = "\n\n".join(dax_measures)
                st.text_area("DAX Measures", dax_text, height=400, key="dax_output")
                st.download_button(
                    "Download DAX Measures",
                    dax_text,
                    file_name="monster_dax_measures.dax",
                    mime="text/plain",
                )
        else:
            st.info("Import data first.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

with tab_export:
    st.markdown('<div class="section-title">Export Analysis Results</div>', unsafe_allow_html=True)

    active_df = get_active_df()
    df_export = _apply_entity_filters(st.session_state.computed_metrics_df) if st.session_state.computed_metrics_df is not None else active_df

    if df_export.empty:
        st.info("No data to export. Import and analyze data first.")
    else:
        st.markdown(f"**{len(df_export):,} rows** x **{len(df_export.columns)} columns**")

        export_cols = st.multiselect("Select columns to export", df_export.columns.tolist(), default=df_export.columns.tolist(), key="export_cols")

        if export_cols:
            export_data = df_export[export_cols]

            col_csv, col_excel, col_json = st.columns(3)

            with col_csv:
                csv_data = export_data.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "Download CSV",
                    csv_data,
                    file_name="monster_analysis.csv",
                    mime="text/csv",
                )

            with col_excel:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    strip_timezone_for_excel(export_data).to_excel(writer, index=False, sheet_name="Analysis")
                st.download_button(
                    "Download Excel",
                    buffer.getvalue(),
                    file_name="monster_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            with col_json:
                json_data = export_data.to_json(orient="records", force_ascii=False, indent=2)
                st.download_button(
                    "Download JSON",
                    json_data,
                    file_name="monster_analysis.json",
                    mime="application/json",
                )

        # Export all datasets
        st.markdown("---")
        st.markdown("#### Export All Datasets")
        if st.session_state.datasets:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for name, df in st.session_state.datasets.items():
                    sheet_name = name[:31].replace("/", "_").replace(":", "_")
                    strip_timezone_for_excel(df).to_excel(writer, index=False, sheet_name=sheet_name)
            st.download_button(
                "Download All Datasets (Excel)",
                buffer.getvalue(),
                file_name="monster_all_datasets.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
