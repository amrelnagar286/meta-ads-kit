"""
Multi-Source Report Builder -- Combine insights from all linked sources.
Custom report layouts with drag-and-drop metric selection.
"""
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, render_quick_add_metric, strip_timezone_for_excel, downloadable_dataframe
from src.formula_engine import evaluate_formula, bulk_apply_metrics
from src.metric_catalog import METRICS, get_metrics_for_available_columns

st.set_page_config(page_title="Report Builder", page_icon="📊", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#0078D4;">Multi-Source Report Builder</h1>'
    '<p style="color:#666;">Build Custom Reports Across All Your Data Sources</p>',
    unsafe_allow_html=True,
)


def get_active_df():
    name = st.session_state.get("active_dataset")
    if name and name in st.session_state.get("datasets", {}):
        df = st.session_state.datasets[name]
    elif st.session_state.get("merged_data") is not None:
        df = st.session_state.merged_data
    else:
        return pd.DataFrame()
    for key in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        filt = st.session_state.get(key)
        if filt:
            col, vals = filt
            if col in df.columns:
                df = df[df[col].astype(str).isin(vals)]
    return df


df = get_active_df()
if df.empty:
    st.info("No data loaded. Go to the main page to import data.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# REPORT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title">Report Configuration</div>', unsafe_allow_html=True)

report_tabs = st.tabs(["Aggregate Report", "Breakdown Report", "Comparison Report", "Trend Report"])

# ------ Aggregate Report ------
with report_tabs[0]:
    st.markdown("#### Aggregate Summary Across All Data")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    selected_metrics = st.multiselect("Select metrics", numeric_cols, default=numeric_cols[:8], key="agg_metrics")

    if selected_metrics:
        agg_funcs = st.multiselect("Aggregations", ["Sum", "Mean", "Median", "Min", "Max", "Std Dev"], default=["Sum", "Mean"], key="agg_funcs")

        agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Min": "min", "Max": "max", "Std Dev": "std"}
        agg_list = [agg_map[f] for f in agg_funcs]

        summary = df[selected_metrics].agg(agg_list).T
        summary.columns = agg_funcs
        downloadable_dataframe(summary.style.format("{:,.2f}"), key="report_summary", label="report_summary", use_container_width=True)

        # Bar chart of sums
        if "Sum" in agg_funcs:
            sums = df[selected_metrics].sum().reset_index()
            sums.columns = ["Metric", "Total"]
            fig = px.bar(sums, x="Metric", y="Total", template="plotly_white", color="Total",
                         color_continuous_scale=["#0078D4", "#00B7C3"])
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)

# ------ Breakdown Report ------
with report_tabs[1]:
    st.markdown("#### Breakdown Report")

    text_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if text_cols and numeric_cols:
        breakdown_col = st.selectbox("Breakdown Dimension", text_cols, key="bd_dim")
        value_cols = st.multiselect("Value Columns", numeric_cols, default=numeric_cols[:5], key="bd_vals")
        agg_func = st.selectbox("Aggregation", ["sum", "mean", "count"], key="bd_agg")

        if value_cols:
            breakdown = df.groupby(breakdown_col, as_index=False)[value_cols].agg(agg_func)
            breakdown = breakdown.sort_values(value_cols[0], ascending=False)
            downloadable_dataframe(breakdown, key="report_breakdown", label="report_breakdown", use_container_width=True, hide_index=True)

            # Top N chart
            top_n = st.slider("Top N", 5, min(50, len(breakdown)), 10, key="bd_topn")
            fig = px.bar(breakdown.head(top_n), x=breakdown_col, y=value_cols[0], template="plotly_white")
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need both text and numeric columns for breakdown reports.")

# ------ Comparison Report ------
with report_tabs[2]:
    st.markdown("#### Side-by-Side Comparison")
    st.markdown("Compare performance across entities, campaigns, or time periods.")

    text_cols = df.select_dtypes(exclude=["number"]).columns.tolist()
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if text_cols and numeric_cols:
        compare_dim = st.selectbox("Compare by", text_cols, key="cmp_dim")
        unique_vals = df[compare_dim].dropna().unique().tolist()

        if len(unique_vals) >= 2:
            selected_entities = st.multiselect("Select entities to compare", unique_vals, default=unique_vals[:min(5, len(unique_vals))], key="cmp_entities")
            compare_metrics = st.multiselect("Metrics", numeric_cols, default=numeric_cols[:4], key="cmp_metrics")

            if selected_entities and compare_metrics:
                filtered = df[df[compare_dim].isin(selected_entities)]
                comparison = filtered.groupby(compare_dim, as_index=False)[compare_metrics].sum()

                downloadable_dataframe(comparison, key="report_comparison", label="report_comparison", use_container_width=True, hide_index=True)

                # Grouped bar chart
                fig = go.Figure()
                for metric in compare_metrics:
                    fig.add_trace(go.Bar(name=metric, x=comparison[compare_dim], y=comparison[metric]))
                fig.update_layout(barmode="group", template="plotly_white", font_family="Segoe UI")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need both text and numeric columns for comparison reports.")

# ------ Trend Report ------
with report_tabs[3]:
    st.markdown("#### Time-Series Trend Report")

    date_cols = [c for c in df.columns if any(kw in c.lower() for kw in ("date", "day", "time", "period"))]
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if date_cols and numeric_cols:
        date_col = st.selectbox("Date Column", date_cols, key="trend_date")
        trend_metrics = st.multiselect("Metrics to Trend", numeric_cols, default=numeric_cols[:3], key="trend_metrics")

        if trend_metrics:
            df_trend = df.copy()
            df_trend[date_col] = pd.to_datetime(df_trend[date_col], errors="coerce")
            df_trend = df_trend.dropna(subset=[date_col])

            granularity = st.selectbox("Granularity", ["Daily", "Weekly", "Monthly"], key="trend_gran")

            if granularity == "Daily":
                df_trend["_period"] = df_trend[date_col].dt.date
            elif granularity == "Weekly":
                df_trend["_period"] = df_trend[date_col].dt.to_period("W").apply(lambda r: r.start_time.date())
            else:
                df_trend["_period"] = df_trend[date_col].dt.to_period("M").apply(lambda r: r.start_time.date())

            trended = df_trend.groupby("_period", as_index=False)[trend_metrics].sum()

            fig = go.Figure()
            for metric in trend_metrics:
                fig.add_trace(go.Scatter(x=trended["_period"], y=trended[metric], name=metric, mode="lines+markers"))
            fig.update_layout(template="plotly_white", font_family="Segoe UI", title="Metric Trends Over Time")
            st.plotly_chart(fig, use_container_width=True)

            downloadable_dataframe(trended, key="report_trended", label="report_trended", use_container_width=True, hide_index=True)
    else:
        st.info("Need date and numeric columns for trend analysis.")

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT REPORT
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Export Report")

col_csv, col_excel = st.columns(2)
with col_csv:
    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download Full Report (CSV)", csv_data, file_name="monster_report.csv", mime="text/csv")
with col_excel:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        strip_timezone_for_excel(df).to_excel(writer, index=False, sheet_name="Report")
    st.download_button("Download Full Report (Excel)", buffer.getvalue(), file_name="monster_report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
render_quick_add_metric("report")
