"""
Data Studio — Advanced analytics: pivot tables, cross-tab analysis, charts,
formula lab, period comparison, and data export.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import os

from src.kpi_engine import compute_kpis, evaluate_formula, STANDARD_KPIS
from src.helpers import format_currency, format_number, format_percentage, safe_float, safe_divide

st.set_page_config(page_title="Data Studio", page_icon="📊", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
</style>""", unsafe_allow_html=True)

st.markdown("# Data Studio")
st.markdown("Advanced analytics, pivot tables, charts, and custom formulas.")

tab_explore, tab_pivot, tab_charts, tab_formulas, tab_compare = st.tabs([
    "Data Explorer", "Pivot Tables", "Chart Builder", "Formula Lab", "Period Comparison",
])

# Helper: load data
def get_data():
    result = st.session_state.get("last_result")
    if result and "output_dir" in result:
        raw_dir = os.path.join(result["output_dir"], "raw")
        if os.path.exists(raw_dir):
            csvs = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
            if csvs:
                return raw_dir, csvs
    return None, None

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: DATA EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_explore:
    st.markdown('<div class="section-title">Data Explorer</div>', unsafe_allow_html=True)

    data_source = st.radio("Data Source", ["Last Extraction", "Upload CSV"], horizontal=True, key="de_source")

    df = None
    if data_source == "Last Extraction":
        raw_dir, csvs = get_data()
        if csvs:
            selected_file = st.selectbox("Select dataset", csvs, key="de_file")
            df = pd.read_csv(os.path.join(raw_dir, selected_file))
        else:
            st.info("No extraction data. Run an extraction first or upload a CSV.")
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="de_upload")
        if uploaded:
            df = pd.read_csv(uploaded)

    if df is not None:
        st.info(f"{len(df)} rows x {len(df.columns)} columns")

        # Column selector
        all_cols = df.columns.tolist()
        selected_cols = st.multiselect("Select columns to display", all_cols, default=all_cols[:10], key="de_cols")

        if selected_cols:
            display_df = df[selected_cols]
        else:
            display_df = df

        # Search
        search = st.text_input("Search/filter rows", key="de_search")
        if search:
            mask = display_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False))
            display_df = display_df[mask.any(axis=1)]

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

        # Quick stats
        with st.expander("Column Statistics"):
            numeric_cols = display_df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                st.dataframe(display_df[numeric_cols].describe(), use_container_width=True)

        # KPI computation
        if st.button("Compute KPIs", key="de_kpi"):
            kpi_df = compute_kpis(df)
            kpi_cols = [c for c in kpi_df.columns if c.startswith("kpi_")]
            if kpi_cols:
                st.markdown("### Computed KPIs")
                st.dataframe(kpi_df[kpi_cols], use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PIVOT TABLES
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pivot:
    st.markdown('<div class="section-title">Pivot Tables</div>', unsafe_allow_html=True)

    raw_dir, csvs = get_data()
    uploaded_pivot = st.file_uploader("Upload CSV for pivot", type=["csv"], key="pv_upload")

    pv_df = None
    if uploaded_pivot:
        pv_df = pd.read_csv(uploaded_pivot)
    elif csvs:
        pv_file = st.selectbox("Select dataset", csvs, key="pv_file")
        pv_df = pd.read_csv(os.path.join(raw_dir, pv_file))

    if pv_df is not None:
        all_cols = pv_df.columns.tolist()
        numeric_cols = pv_df.select_dtypes(include=["number"]).columns.tolist()
        string_cols = [c for c in all_cols if c not in numeric_cols]

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            pv_index = st.multiselect("Rows (Index)", string_cols, default=string_cols[:1] if string_cols else [], key="pv_index")
        with col_p2:
            pv_columns = st.multiselect("Columns", string_cols, key="pv_columns")
        with col_p3:
            pv_values = st.multiselect("Values", numeric_cols, default=numeric_cols[:2] if numeric_cols else [], key="pv_values")
            pv_aggfunc = st.selectbox("Aggregation", ["sum", "mean", "count", "min", "max", "median"], key="pv_agg")

        if pv_index and pv_values:
            try:
                pivot = pd.pivot_table(
                    pv_df,
                    index=pv_index,
                    columns=pv_columns if pv_columns else None,
                    values=pv_values,
                    aggfunc=pv_aggfunc,
                    fill_value=0,
                )
                st.dataframe(pivot, use_container_width=True, height=500)

                csv = pivot.to_csv()
                st.download_button("Download Pivot", csv, "pivot_table.csv", "text/csv")
            except Exception as e:
                st.error(f"Pivot failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: CHART BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

with tab_charts:
    st.markdown('<div class="section-title">Chart Builder</div>', unsafe_allow_html=True)

    raw_dir, csvs = get_data()
    uploaded_chart = st.file_uploader("Upload CSV for charts", type=["csv"], key="ch_upload")

    ch_df = None
    if uploaded_chart:
        ch_df = pd.read_csv(uploaded_chart)
    elif csvs:
        ch_file = st.selectbox("Select dataset", csvs, key="ch_file")
        ch_df = pd.read_csv(os.path.join(raw_dir, ch_file))

    if ch_df is not None:
        all_cols = ch_df.columns.tolist()
        numeric_cols = ch_df.select_dtypes(include=["number"]).columns.tolist()

        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Area", "Scatter"], key="ch_type")

        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            x_col = st.selectbox("X-Axis", all_cols, key="ch_x")
        with col_ch2:
            y_cols = st.multiselect("Y-Axis (metrics)", numeric_cols, default=numeric_cols[:1] if numeric_cols else [], key="ch_y")

        if x_col and y_cols:
            chart_data = ch_df[[x_col] + y_cols].copy()
            for col in y_cols:
                chart_data[col] = pd.to_numeric(chart_data[col], errors="coerce")
            chart_data = chart_data.set_index(x_col)

            if chart_type == "Line":
                st.line_chart(chart_data)
            elif chart_type == "Bar":
                st.bar_chart(chart_data)
            elif chart_type == "Area":
                st.area_chart(chart_data)
            elif chart_type == "Scatter":
                if len(y_cols) >= 2:
                    st.scatter_chart(ch_df, x=y_cols[0], y=y_cols[1])
                else:
                    st.scatter_chart(chart_data)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: FORMULA LAB
# ═══════════════════════════════════════════════════════════════════════════════

with tab_formulas:
    st.markdown('<div class="section-title">Formula Lab</div>', unsafe_allow_html=True)

    st.markdown("""
    Create custom calculated metrics using formulas. Available operators: `+ - * / ( )`

    **Available variables** (column names from your data): Use exact column names.

    **Examples:**
    - `spend / clicks` — CPC
    - `clicks / impressions * 100` — CTR %
    - `(spend / impressions) * 1000` — CPM
    - `revenue / spend` — ROAS
    """)

    # Show standard KPIs
    st.markdown("### Standard KPI Formulas")
    kpi_rows = []
    for key, kpi in STANDARD_KPIS.items():
        kpi_rows.append({
            "KPI": kpi["name"],
            "Formula": kpi["formula"],
            "Unit": kpi["unit"],
        })
    st.dataframe(pd.DataFrame(kpi_rows), use_container_width=True, hide_index=True)

    st.markdown("### Custom Formula")
    custom_formula = st.text_input("Enter formula", placeholder="spend / clicks", key="fl_formula")

    # Test with sample data
    st.markdown("### Test Formula")
    col_fl1, col_fl2 = st.columns(2)
    with col_fl1:
        test_vars = st.text_area(
            "Test variables (JSON)",
            value='{"spend": 100, "clicks": 200, "impressions": 10000, "reach": 8000, "conversions": 10, "revenue": 500}',
            key="fl_vars",
        )
    with col_fl2:
        if custom_formula and st.button("Evaluate", type="primary", key="fl_eval"):
            import json
            try:
                context = json.loads(test_vars)
                result = evaluate_formula(custom_formula, context, raise_errors=True)
                st.metric("Result", f"{result:,.4f}")
            except Exception as e:
                st.error(f"Evaluation failed: {e}")

    # Apply to dataset
    st.markdown("### Apply Formula to Dataset")
    raw_dir, csvs = get_data()
    uploaded_fl = st.file_uploader("Upload CSV", type=["csv"], key="fl_upload")

    fl_df = None
    if uploaded_fl:
        fl_df = pd.read_csv(uploaded_fl)
    elif csvs:
        fl_file = st.selectbox("Select dataset", csvs, key="fl_file")
        fl_df = pd.read_csv(os.path.join(raw_dir, fl_file))

    if fl_df is not None and custom_formula:
        new_col_name = st.text_input("New column name", value="custom_metric", key="fl_col_name")
        if st.button("Apply to Dataset", key="fl_apply"):
            try:
                results = []
                for _, row in fl_df.iterrows():
                    context = {col: safe_float(row.get(col, 0)) for col in fl_df.columns}
                    results.append(evaluate_formula(custom_formula, context, raise_errors=True))
                fl_df[new_col_name] = results
                st.dataframe(fl_df, use_container_width=True, hide_index=True)

                csv = fl_df.to_csv(index=False)
                st.download_button("Download with custom metric", csv, "data_with_custom.csv", "text/csv")
            except Exception as e:
                st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: PERIOD COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

with tab_compare:
    st.markdown('<div class="section-title">Period Comparison</div>', unsafe_allow_html=True)

    st.markdown("Compare performance across two time periods to identify trends.")

    if st.session_state.get("connected", False):
        from src.extractor import MetaAdsExtractor

        col_pc1, col_pc2 = st.columns(2)
        with col_pc1:
            period_1 = st.selectbox("Period 1", ["last_7d", "last_14d", "last_30d", "last_60d", "last_90d"], index=2, key="pc_p1")
        with col_pc2:
            period_2 = st.selectbox("Period 2 (previous)", ["last_7d", "last_14d", "last_30d", "last_60d", "last_90d"], index=3, key="pc_p2")

        if st.button("Compare Periods", type="primary", key="pc_compare"):
            try:
                ext = MetaAdsExtractor(
                    st.session_state.access_token,
                    st.session_state.ad_account_id,
                )

                df1 = ext.fetch_insights(level="account", breakdown_key="none", preset=period_1)
                df2 = ext.fetch_insights(level="account", breakdown_key="none", preset=period_2)

                if not df1.empty and not df2.empty:
                    metrics = ["spend", "impressions", "clicks", "reach"]
                    comparison = []

                    for m in metrics:
                        if m in df1.columns and m in df2.columns:
                            v1 = safe_float(df1[m].sum())
                            v2 = safe_float(df2[m].sum())
                            change = safe_divide(v1 - v2, v2) * 100
                            comparison.append({
                                "Metric": m.title(),
                                f"Period 1 ({period_1})": f"{v1:,.2f}",
                                f"Period 2 ({period_2})": f"{v2:,.2f}",
                                "Change %": f"{change:+.1f}%",
                            })

                    st.dataframe(pd.DataFrame(comparison), use_container_width=True, hide_index=True)
                else:
                    st.info("Not enough data for comparison.")
            except Exception as e:
                st.error(f"Failed: {e}")
    else:
        st.info("Connect to Meta API first.")
