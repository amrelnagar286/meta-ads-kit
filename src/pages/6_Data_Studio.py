"""
Data Studio Page — Interactive charts, pivot tables, formula lab, comparisons.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd

from src.kpi_engine import KPIEngine, STANDARD_KPIS, evaluate_formula
from src.helpers import safe_divide, format_currency, format_number, format_percentage

st.set_page_config(page_title="Data Studio", page_icon="📈", layout="wide")

st.markdown("# Data Studio")

tab_charts, tab_pivot, tab_formula, tab_compare = st.tabs([
    "Charts", "Pivot Table", "Formula Lab", "Period Comparison",
])

# Helper to load data
def load_data() -> pd.DataFrame:
    result = st.session_state.get("last_result")
    if not result or "output_dir" not in result:
        return pd.DataFrame()
    raw_dir = os.path.join(result["output_dir"], "raw")
    if not os.path.exists(raw_dir):
        return pd.DataFrame()
    csv_files = [f for f in os.listdir(raw_dir) if f.endswith(".csv")]
    if not csv_files:
        return pd.DataFrame()
    return pd.read_csv(os.path.join(raw_dir, csv_files[0]))


with tab_charts:
    st.markdown("### Interactive Charts")
    df = load_data()
    if df.empty:
        st.info("Run an extraction first to generate charts.")
    else:
        chart_source = st.selectbox("Select Dataset", ["Current"], key="chart_source")
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        if numeric_cols:
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                x_axis = st.selectbox("X Axis", df.columns.tolist(), key="chart_x")
            with col_c2:
                y_axis = st.selectbox("Y Axis", numeric_cols, key="chart_y")

            chart_type = st.radio(
                "Chart Type", ["Bar", "Line", "Area", "Scatter"], horizontal=True
            )

            chart_df = df[[x_axis, y_axis]].dropna()
            if not chart_df.empty:
                chart_df = chart_df.set_index(x_axis)
                if chart_type == "Bar":
                    st.bar_chart(chart_df)
                elif chart_type == "Line":
                    st.line_chart(chart_df)
                elif chart_type == "Area":
                    st.area_chart(chart_df)
                elif chart_type == "Scatter":
                    st.scatter_chart(chart_df)
        else:
            st.info("No numeric columns found in the data.")

with tab_pivot:
    st.markdown("### Pivot Table")
    df = load_data()
    if df.empty:
        st.info("Run an extraction first.")
    else:
        all_cols = df.columns.tolist()
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            pivot_rows = st.multiselect("Row Fields", all_cols, key="pivot_rows")
        with col_p2:
            pivot_values = st.multiselect("Value Fields", numeric_cols, key="pivot_values")
        with col_p3:
            pivot_agg = st.selectbox("Aggregation", ["sum", "mean", "count", "min", "max"], key="pivot_agg")

        if pivot_rows and pivot_values:
            try:
                pivot = df.pivot_table(
                    index=pivot_rows, values=pivot_values,
                    aggfunc=pivot_agg,
                ).reset_index()
                st.dataframe(pivot, use_container_width=True, hide_index=True)
                csv_data = pivot.to_csv(index=False)
                st.download_button("Download Pivot", csv_data, "pivot_table.csv", "text/csv")
            except Exception as e:
                st.error(f"Pivot error: {e}")

with tab_formula:
    st.markdown("### Formula Lab")
    st.info("Write custom formulas using column names from your data.")

    df = load_data()
    if df.empty:
        st.info("Run an extraction first.")
    else:
        st.markdown("**Available columns:**")
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        st.write(", ".join(numeric_cols[:30]))

        formula = st.text_input(
            "Formula",
            placeholder="e.g., spend / clicks",
            key="formula_lab_input",
        )

        if formula:
            totals = {}
            for col in numeric_cols:
                totals[col] = float(df[col].sum())

            result_val = evaluate_formula(formula, totals)
            st.metric("Result (on totals)", f"{result_val:,.4f}")

            try:
                row_results = df.apply(
                    lambda row: evaluate_formula(
                        formula, {c: float(row.get(c, 0) or 0) for c in numeric_cols}
                    ),
                    axis=1,
                )
                df_with_formula = df.copy()
                df_with_formula["formula_result"] = row_results
                st.dataframe(df_with_formula, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Row-level formula error: {e}")

        st.markdown("---")
        st.markdown("### Standard KPI Reference")
        for kpi_id, kpi in STANDARD_KPIS.items():
            st.text(f"{kpi['name']}: {kpi['formula']} ({kpi['unit']})")

with tab_compare:
    st.markdown("### Period-over-Period Comparison")
    st.info(
        "Run two extractions with different date ranges and upload both CSV files "
        "to compare performance across periods."
    )

    col_up1, col_up2 = st.columns(2)
    with col_up1:
        st.markdown("**Period 1**")
        file1 = st.file_uploader("Upload Period 1 CSV", type=["csv"], key="compare_file1")
    with col_up2:
        st.markdown("**Period 2**")
        file2 = st.file_uploader("Upload Period 2 CSV", type=["csv"], key="compare_file2")

    if file1 and file2:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        common_numeric = [
            c for c in df1.select_dtypes(include=["number"]).columns
            if c in df2.columns
        ]

        if common_numeric:
            comparison = pd.DataFrame({
                "Metric": common_numeric,
                "Period 1": [df1[c].sum() for c in common_numeric],
                "Period 2": [df2[c].sum() for c in common_numeric],
            })
            comparison["Change"] = comparison["Period 2"] - comparison["Period 1"]
            comparison["Change %"] = comparison.apply(
                lambda r: safe_divide(r["Change"], r["Period 1"]) * 100, axis=1
            )
            st.dataframe(comparison, use_container_width=True, hide_index=True)
        else:
            st.warning("No common numeric columns found between the two files.")
