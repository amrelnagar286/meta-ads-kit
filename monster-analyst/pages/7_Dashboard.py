"""
Ultimate Dashboard -- Fully flexible analysis dashboard.
Custom charts, pivot tables, statistical analysis, trend detection, 
comparisons, and everything a data analyst needs.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe
from src.formula_engine import evaluate_formula, validate_formula, apply_formula_to_df

st.set_page_config(page_title="Ultimate Dashboard", page_icon="📈", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#0078D4;">Ultimate Dashboard</h1>'
    '<p style="color:#666;">Fully Flexible Analysis -- Charts, Pivots, Stats, Trends, Comparisons</p>',
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


active_df = get_active_df()
if active_df.empty:
    st.info("No data loaded. Go to the main page to import data.")
    st.stop()

_computed = st.session_state.get("computed_metrics_df")
if _computed is not None:
    for _fk in ["entity_filter_campaign", "entity_filter_ad_set", "entity_filter_ad"]:
        _fv = st.session_state.get(_fk)
        if _fv:
            _fc, _vs = _fv
            if _fc in _computed.columns:
                _computed = _computed[_computed[_fc].astype(str).isin(_vs)]
df = _computed if _computed is not None else active_df

# Identify column types
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "day" in c.lower()]
all_cols = df.columns.tolist()

st.markdown(f"**Working with:** {len(df):,} rows x {len(df.columns)} columns")

# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD SECTIONS
# ═══════════════════════════════════════════════════════════════════════════

dash_tabs = st.tabs([
    "Custom Charts",
    "Pivot Tables",
    "Statistical Summary",
    "Trend Analysis",
    "Comparisons",
    "Calculated Fields",
    "Data Quality",
])


# ─────────────────────────────────────────────────────────────────────────
# TAB 1: CUSTOM CHARTS
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[0]:
    st.markdown('<div class="section-title">Custom Chart Builder</div>', unsafe_allow_html=True)

    chart_type = st.selectbox(
        "Chart Type",
        ["Bar", "Line", "Scatter", "Pie", "Histogram", "Box", "Heatmap", "Sunburst", "Treemap", "Funnel", "Area"],
        key="dash_chart_type",
    )

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        x_col = st.selectbox("X Axis", ["(none)"] + all_cols, key="dash_x")
        color_col = st.selectbox("Color / Group By", ["(none)"] + categorical_cols, key="dash_color")
    with col_cfg2:
        y_col = st.selectbox("Y Axis", ["(none)"] + numeric_cols, key="dash_y")
        size_col = st.selectbox("Size (bubble/scatter)", ["(none)"] + numeric_cols, key="dash_size")

    agg_func = st.selectbox("Aggregation", ["None (raw)", "Sum", "Mean", "Median", "Count", "Min", "Max"], key="dash_agg")

    if st.button("Generate Chart", type="primary", key="dash_gen"):
        try:
            chart_df = df.copy()

            # Apply aggregation if needed
            if agg_func != "None (raw)" and x_col != "(none)" and y_col != "(none)":
                agg_map = {"Sum": "sum", "Mean": "mean", "Median": "median", "Count": "count", "Min": "min", "Max": "max"}
                group_cols = [x_col]
                if color_col != "(none)":
                    group_cols.append(color_col)
                chart_df = chart_df.groupby(group_cols, as_index=False)[y_col].agg(agg_map[agg_func])

            x = x_col if x_col != "(none)" else None
            y = y_col if y_col != "(none)" else None
            color = color_col if color_col != "(none)" else None
            size = size_col if size_col != "(none)" else None

            fig = None
            if chart_type == "Bar":
                fig = px.bar(chart_df, x=x, y=y, color=color, template="plotly_white", barmode="group")
            elif chart_type == "Line":
                fig = px.line(chart_df, x=x, y=y, color=color, template="plotly_white")
            elif chart_type == "Scatter":
                fig = px.scatter(chart_df, x=x, y=y, color=color, size=size, template="plotly_white")
            elif chart_type == "Pie":
                fig = px.pie(chart_df, names=x, values=y, template="plotly_white")
            elif chart_type == "Histogram":
                fig = px.histogram(chart_df, x=x or y, color=color, template="plotly_white")
            elif chart_type == "Box":
                fig = px.box(chart_df, x=x, y=y, color=color, template="plotly_white")
            elif chart_type == "Heatmap":
                if x and y:
                    pivot = chart_df.pivot_table(values=y, index=x, aggfunc="mean")
                    fig = px.imshow(pivot, template="plotly_white", aspect="auto")
            elif chart_type == "Sunburst":
                path_cols = [c for c in [x, color] if c]
                if path_cols and y:
                    fig = px.sunburst(chart_df, path=path_cols, values=y, template="plotly_white")
            elif chart_type == "Treemap":
                path_cols = [c for c in [x, color] if c]
                if path_cols and y:
                    fig = px.treemap(chart_df, path=path_cols, values=y, template="plotly_white")
            elif chart_type == "Funnel":
                fig = px.funnel(chart_df, x=y, y=x, color=color, template="plotly_white")
            elif chart_type == "Area":
                fig = px.area(chart_df, x=x, y=y, color=color, template="plotly_white")

            if fig:
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Cannot generate chart with these settings. Check your axis selections.")
        except Exception as e:
            st.error(f"Chart error: {e}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 2: PIVOT TABLES
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[1]:
    st.markdown('<div class="section-title">Pivot Table Builder</div>', unsafe_allow_html=True)

    col_pv1, col_pv2, col_pv3 = st.columns(3)
    with col_pv1:
        pivot_rows = st.multiselect("Row Fields", all_cols, key="pivot_rows")
    with col_pv2:
        pivot_cols = st.multiselect("Column Fields", categorical_cols, key="pivot_cols")
    with col_pv3:
        pivot_values = st.multiselect("Value Fields", numeric_cols, key="pivot_vals")

    pivot_agg = st.selectbox("Aggregation", ["sum", "mean", "median", "count", "min", "max", "std"], key="pivot_agg")
    show_margins = st.checkbox("Show Totals (margins)", value=True, key="pivot_margins")

    if st.button("Build Pivot Table", type="primary", key="pivot_build"):
        if pivot_rows and pivot_values:
            try:
                pivot = pd.pivot_table(
                    df,
                    index=pivot_rows,
                    columns=pivot_cols if pivot_cols else None,
                    values=pivot_values,
                    aggfunc=pivot_agg,
                    margins=show_margins,
                    margins_name="TOTAL",
                )
                downloadable_dataframe(pivot, key="dash_pivot", label="pivot_table", use_container_width=True)

                csv_data = pivot.to_csv().encode("utf-8-sig")
                st.download_button("Download Pivot (CSV)", csv_data, file_name="pivot_table.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Pivot error: {e}")
        else:
            st.warning("Select at least Row Fields and Value Fields.")


# ─────────────────────────────────────────────────────────────────────────
# TAB 3: STATISTICAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[2]:
    st.markdown('<div class="section-title">Statistical Analysis</div>', unsafe_allow_html=True)

    if numeric_cols:
        stat_cols = st.multiselect("Select columns for analysis", numeric_cols, default=numeric_cols[:5], key="stat_cols")

        if stat_cols:
            stats_df = df[stat_cols].describe().T
            stats_df["median"] = df[stat_cols].median()
            stats_df["variance"] = df[stat_cols].var()
            stats_df["skewness"] = df[stat_cols].skew()
            stats_df["kurtosis"] = df[stat_cols].kurtosis()
            stats_df["missing"] = df[stat_cols].isnull().sum()
            stats_df["missing_%"] = (df[stat_cols].isnull().sum() / len(df) * 100).round(2)
            stats_df["zeros"] = (df[stat_cols] == 0).sum()
            stats_df["zeros_%"] = ((df[stat_cols] == 0).sum() / len(df) * 100).round(2)

            downloadable_dataframe(stats_df.style.format("{:.2f}"), key="dash_stats", label="statistics", use_container_width=True)

            # Distribution plots
            st.markdown("#### Distributions")
            dist_col = st.selectbox("Column", stat_cols, key="dist_col")
            if dist_col:
                col_hist, col_box = st.columns(2)
                with col_hist:
                    fig = px.histogram(df, x=dist_col, template="plotly_white", title=f"Distribution: {dist_col}", nbins=30)
                    st.plotly_chart(fig, use_container_width=True)
                with col_box:
                    fig = px.box(df, y=dist_col, template="plotly_white", title=f"Box Plot: {dist_col}")
                    st.plotly_chart(fig, use_container_width=True)

            # Correlation matrix
            st.markdown("#### Correlation Matrix")
            if len(stat_cols) >= 2:
                corr = df[stat_cols].corr()
                fig = px.imshow(
                    corr,
                    text_auto=".2f",
                    color_continuous_scale="RdBu_r",
                    template="plotly_white",
                    title="Correlation Matrix",
                    aspect="auto",
                )
                st.plotly_chart(fig, use_container_width=True)

                # Top correlations
                pairs = []
                for i in range(len(corr.columns)):
                    for j in range(i + 1, len(corr.columns)):
                        pairs.append({
                            "Variable 1": corr.columns[i],
                            "Variable 2": corr.columns[j],
                            "Correlation": round(corr.iloc[i, j], 4),
                            "Strength": "Strong" if abs(corr.iloc[i, j]) > 0.7 else "Moderate" if abs(corr.iloc[i, j]) > 0.4 else "Weak",
                        })
                pairs_df = pd.DataFrame(pairs).sort_values("Correlation", key=abs, ascending=False)
                downloadable_dataframe(pairs_df, key="dash_corr_pairs", label="correlation_pairs", use_container_width=True, hide_index=True)
    else:
        st.warning("No numeric columns found for statistical analysis.")


# ─────────────────────────────────────────────────────────────────────────
# TAB 4: TREND ANALYSIS
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[3]:
    st.markdown('<div class="section-title">Trend Analysis</div>', unsafe_allow_html=True)

    possible_date_cols = date_cols if date_cols else all_cols
    trend_date = st.selectbox("Date Column", ["(auto-detect)"] + possible_date_cols, key="trend_date")
    trend_metrics = st.multiselect("Metrics to Track", numeric_cols, default=numeric_cols[:3] if numeric_cols else [], key="trend_metrics")
    trend_group = st.selectbox("Group By (optional)", ["(none)"] + categorical_cols, key="trend_group")

    if trend_metrics:
        try:
            trend_df = df.copy()

            # Auto-detect or use selected date column
            date_col = None
            if trend_date == "(auto-detect)":
                for c in df.columns:
                    if "date" in c.lower():
                        try:
                            pd.to_datetime(trend_df[c])
                            date_col = c
                            break
                        except Exception:
                            continue
            else:
                date_col = trend_date

            if date_col and date_col in trend_df.columns:
                trend_df[date_col] = pd.to_datetime(trend_df[date_col], errors="coerce")
                trend_df = trend_df.dropna(subset=[date_col])
                trend_df = trend_df.sort_values(date_col)

                if trend_group != "(none)":
                    grouped = trend_df.groupby([date_col, trend_group], as_index=False)[trend_metrics].sum()
                else:
                    grouped = trend_df.groupby(date_col, as_index=False)[trend_metrics].sum()

                for metric in trend_metrics:
                    fig = px.line(
                        grouped, x=date_col, y=metric,
                        color=trend_group if trend_group != "(none)" else None,
                        template="plotly_white",
                        title=f"Trend: {metric}",
                    )
                    # Add moving average
                    if trend_group == "(none)" and len(grouped) > 5:
                        grouped[f"{metric}_MA7"] = grouped[metric].rolling(7, min_periods=1).mean()
                        fig.add_scatter(
                            x=grouped[date_col], y=grouped[f"{metric}_MA7"],
                            name=f"7-day MA", line=dict(dash="dash", width=2),
                        )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                # Day-over-day change
                st.markdown("#### Day-over-Day Changes")
                if trend_group == "(none)":
                    dod = grouped[trend_metrics].pct_change() * 100
                    dod.insert(0, "Date", grouped[date_col])
                    downloadable_dataframe(dod.tail(14).style.format("{:.2f}%", subset=trend_metrics), key="dash_dod", label="day_over_day", use_container_width=True, hide_index=True)
            else:
                st.warning("No suitable date column found. Select one manually or ensure your data has date columns.")
        except Exception as e:
            st.error(f"Trend analysis error: {e}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 5: COMPARISONS
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[4]:
    st.markdown('<div class="section-title">Comparisons & Benchmarking</div>', unsafe_allow_html=True)

    if not categorical_cols:
        st.warning("No categorical columns for comparison. Import data with campaign names, ad names, etc.")
    else:
        compare_by = st.selectbox("Compare By", categorical_cols, key="compare_by")
        compare_metrics = st.multiselect("Metrics", numeric_cols, default=numeric_cols[:4] if numeric_cols else [], key="compare_metrics")

        if compare_metrics and compare_by:
            top_n = st.slider("Top N entities", 5, 50, 15, key="compare_top_n")
            sort_metric = st.selectbox("Sort By", compare_metrics, key="compare_sort")

            grouped = df.groupby(compare_by, as_index=False)[compare_metrics].sum()
            grouped = grouped.sort_values(sort_metric, ascending=False).head(top_n)

            # Comparison table
            downloadable_dataframe(grouped, key="dash_topn", label="top_entities", use_container_width=True, hide_index=True)

            # Radar / comparison chart
            st.markdown("#### Visual Comparison")
            col_bar, col_scatter = st.columns(2)
            with col_bar:
                for metric in compare_metrics[:2]:
                    fig = px.bar(
                        grouped, x=compare_by, y=metric,
                        color=metric, template="plotly_white",
                        title=f"{metric} by {compare_by}",
                        color_continuous_scale="Viridis",
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)

            with col_scatter:
                if len(compare_metrics) >= 2:
                    fig = px.scatter(
                        grouped, x=compare_metrics[0], y=compare_metrics[1],
                        size=compare_metrics[2] if len(compare_metrics) >= 3 else None,
                        hover_name=compare_by,
                        template="plotly_white",
                        title=f"{compare_metrics[0]} vs {compare_metrics[1]}",
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)

            # Pareto analysis (80/20 rule)
            st.markdown("#### Pareto Analysis (80/20)")
            pareto_metric = st.selectbox("Pareto Metric", compare_metrics, key="pareto_metric")
            pareto_df = df.groupby(compare_by, as_index=False)[pareto_metric].sum()
            pareto_df = pareto_df.sort_values(pareto_metric, ascending=False)
            pareto_df["cumulative_%"] = (pareto_df[pareto_metric].cumsum() / pareto_df[pareto_metric].sum() * 100).round(2)
            pareto_df["rank"] = range(1, len(pareto_df) + 1)

            fig = go.Figure()
            fig.add_bar(x=pareto_df[compare_by].head(20), y=pareto_df[pareto_metric].head(20), name=pareto_metric)
            fig.add_scatter(
                x=pareto_df[compare_by].head(20), y=pareto_df["cumulative_%"].head(20),
                name="Cumulative %", yaxis="y2", line=dict(color="red", width=2),
            )
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", title="Cumulative %", range=[0, 105]),
                template="plotly_white", height=400,
                title=f"Pareto: {pareto_metric} by {compare_by}",
            )
            st.plotly_chart(fig, use_container_width=True)

            entities_80 = pareto_df[pareto_df["cumulative_%"] <= 80]
            st.info(f"**{len(entities_80)}** out of **{len(pareto_df)}** entities ({len(entities_80)/len(pareto_df)*100:.1f}%) account for 80% of {pareto_metric}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 6: CALCULATED FIELDS
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[5]:
    st.markdown('<div class="section-title">Calculated Fields & Formulas</div>', unsafe_allow_html=True)

    with st.expander("Available columns"):
        st.code(", ".join(all_cols))

    st.markdown("Create temporary calculated columns using formulas.")

    calc_name = st.text_input("Column Name", placeholder="custom_roas", key="calc_name")
    calc_formula = st.text_input("Formula", placeholder="purchase_conversion_value / spend", key="calc_formula")

    if st.button("Add Calculated Field", type="primary", key="calc_add"):
        if calc_name and calc_formula:
            error = validate_formula(calc_formula)
            if error:
                st.error(f"Invalid formula: {error}")
            else:
                try:
                    result = apply_formula_to_df(df, calc_formula, calc_name)
                    df = df.copy()
                    df[calc_name] = result
                    st.session_state.computed_metrics_df = df
                    st.success(f"Added column '{calc_name}'")
                    downloadable_dataframe(df[[all_cols[0], calc_name]].head(10), key="dash_calc", label="calculated_field", use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    # Quick formulas
    st.markdown("#### Quick Formulas")
    quick_formulas = {
        "CTR (%)": "clicks / impressions * 100",
        "CPC": "spend / clicks",
        "CPA": "spend / actions",
        "ROAS": "purchase_conversion_value / spend",
        "CPM": "spend / impressions * 1000",
        "Conv. Rate (%)": "actions / clicks * 100",
        "Frequency": "impressions / reach",
    }
    for name, formula in quick_formulas.items():
        cols_needed = set(formula.replace("*", " ").replace("/", " ").replace("+", " ").replace("-", " ").replace("100", "").replace("1000", "").split())
        available = cols_needed.issubset(set(all_cols))
        status = "Available" if available else "Missing columns"
        st.markdown(f"- **{name}** = `{formula}` ({status})")


# ─────────────────────────────────────────────────────────────────────────
# TAB 7: DATA QUALITY
# ─────────────────────────────────────────────────────────────────────────
with dash_tabs[6]:
    st.markdown('<div class="section-title">Data Quality Report</div>', unsafe_allow_html=True)

    quality_data = []
    for col in df.columns:
        missing = df[col].isnull().sum()
        unique = df[col].nunique()
        dtype = str(df[col].dtype)
        try:
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
        except Exception:
            is_numeric = False
        zeros = int((df[col] == 0).sum()) if is_numeric else 0

        quality_data.append({
            "Column": col,
            "Type": dtype,
            "Non-Null": f"{len(df) - missing:,}",
            "Missing": f"{missing:,}",
            "Missing %": f"{missing / len(df) * 100:.1f}%",
            "Unique": f"{unique:,}",
            "Zeros": f"{zeros:,}",
        })

    quality_df = pd.DataFrame(quality_data)
    downloadable_dataframe(quality_df, key="dash_quality", label="data_quality", use_container_width=True, hide_index=True)

    # Outlier detection
    st.markdown("#### Outlier Detection")
    outlier_col = st.selectbox("Column", numeric_cols, key="outlier_col")
    if outlier_col:
        q1 = df[outlier_col].quantile(0.25)
        q3 = df[outlier_col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[outlier_col] < lower) | (df[outlier_col] > upper)]

        col_info, col_chart = st.columns(2)
        with col_info:
            st.markdown(f"""
            | Statistic | Value |
            |-----------|-------|
            | Q1 (25th) | {q1:,.2f} |
            | Q3 (75th) | {q3:,.2f} |
            | IQR | {iqr:,.2f} |
            | Lower fence | {lower:,.2f} |
            | Upper fence | {upper:,.2f} |
            | Outliers | {len(outliers):,} ({len(outliers)/len(df)*100:.1f}%) |
            """)
        with col_chart:
            fig = px.box(df, y=outlier_col, template="plotly_white", title=f"Outliers: {outlier_col}")
            st.plotly_chart(fig, use_container_width=True)

        if not outliers.empty:
            st.markdown(f"**{len(outliers)} outliers detected:**")
            downloadable_dataframe(outliers.head(20), key="dash_outliers", label="outliers", use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────
# FOOTER: Quick Add Custom Metric
# ─────────────────────────────────────────────────────────────────────────
st.markdown("---")
render_quick_add_metric("dashboard")
