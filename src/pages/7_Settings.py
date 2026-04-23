"""
Settings Page — System configuration, API info, cache management.
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from src.config import config
from src.meta_catalog import (
    API_VERSION, ALL_METRICS, BREAKDOWN_CONFIGS,
    LEVELS, DATE_PRESETS, CAMPAIGN_OBJECTIVES, BID_STRATEGIES,
    DELIVERY_METRICS, ACTION_METRICS, VIDEO_METRICS,
    QUALITY_METRICS, ENGAGEMENT_METRICS, CATALOG_METRICS,
)
from src.rate_limiter import rate_limiter
from src.kpi_engine import STANDARD_KPIS

st.set_page_config(page_title="Settings", page_icon="🔧", layout="wide")

st.markdown("# Settings & Configuration")

tab_api, tab_kpis, tab_catalog, tab_cache, tab_about = st.tabs([
    "API Config", "KPI Definitions", "Field Catalog", "Cache", "About",
])

with tab_api:
    st.markdown("### API Configuration")
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("**Current Settings:**")
        st.text(f"API Version: {API_VERSION}")
        st.text(f"Rate Limit: {config.RATE_LIMIT_CALLS_PER_HOUR}/hour")
        st.text(f"Max Retries: {config.RATE_LIMIT_RETRY_MAX}")
        st.text(f"Backoff Base: {config.RATE_LIMIT_BACKOFF_BASE}s")
        st.text(f"Cache TTL: {config.CACHE_TTL_SECONDS}s")
        st.text(f"Insights Cache TTL: {config.INSIGHTS_CACHE_TTL}s")

    with col_a2:
        st.markdown("**Rate Limiter Status:**")
        status = rate_limiter.status
        for k, v in status.items():
            st.text(f"{k}: {v}")

    st.markdown("---")
    st.markdown("### Environment Variables")
    env_vars = [
        "META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "META_API_VERSION",
        "META_APP_ID", "META_APP_SECRET", "APP_ENV", "LOG_LEVEL",
    ]
    for var in env_vars:
        val = os.getenv(var, "")
        masked = "***" + val[-4:] if val and "TOKEN" in var else val or "(not set)"
        st.text(f"{var}: {masked}")

with tab_kpis:
    st.markdown("### Standard KPI Definitions")
    for kpi_id, kpi in STANDARD_KPIS.items():
        with st.expander(f"{kpi['name']} ({kpi_id})"):
            st.text(f"Formula: {kpi['formula']}")
            st.text(f"Required: {', '.join(kpi['required'])}")
            st.text(f"Unit: {kpi['unit']}")
            st.text(f"Format: {kpi['format']}")

    st.markdown("---")
    st.markdown("### Custom KPI Builder")
    custom_name = st.text_input("KPI Name", key="custom_kpi_name")
    custom_formula = st.text_input(
        "Formula", placeholder="e.g., (revenue - spend) / spend * 100",
        key="custom_kpi_formula",
    )
    custom_fields = st.text_input(
        "Required Fields (comma-separated)",
        placeholder="e.g., revenue, spend",
        key="custom_kpi_fields",
    )
    custom_unit = st.selectbox("Unit", ["ratio", "currency", "percentage", "count"], key="custom_kpi_unit")

    if st.button("Preview KPI"):
        if custom_name and custom_formula:
            st.json({
                "kpi_id": custom_name.lower().replace(" ", "_"),
                "name": custom_name,
                "formula": custom_formula,
                "required_fields": [f.strip() for f in (custom_fields or "").split(",") if f.strip()],
                "unit": custom_unit,
                "format": ".2f",
            })

with tab_catalog:
    st.markdown("### Complete Field Catalog")

    metric_groups = {
        "Delivery": DELIVERY_METRICS,
        "Actions": ACTION_METRICS,
        "Video": VIDEO_METRICS,
        "Quality": QUALITY_METRICS,
        "Engagement": ENGAGEMENT_METRICS,
        "Catalog": CATALOG_METRICS,
    }

    st.markdown(f"**Total Metrics:** {len(ALL_METRICS)}")
    for group_name, metrics in metric_groups.items():
        with st.expander(f"{group_name} ({len(metrics)} fields)"):
            for i, m in enumerate(metrics, 1):
                st.text(f"  {i}. {m}")

    st.markdown("---")
    st.markdown("### Breakdowns")
    for k, v in BREAKDOWN_CONFIGS.items():
        with st.expander(f"{v['label']} ({k})"):
            st.text(f"Fields: {', '.join(v['breakdowns']) if v['breakdowns'] else 'None'}")
            st.text(f"Compatible metrics: {len(v['metrics'])}")

    st.markdown("---")
    st.markdown("### Data Levels")
    for level in LEVELS:
        st.text(f"  {level}")

    st.markdown("### Date Presets")
    for k, v in DATE_PRESETS.items():
        st.text(f"  {k} -> {v}")

    st.markdown("### Campaign Objectives")
    for k, v in CAMPAIGN_OBJECTIVES.items():
        st.text(f"  {k}: {v}")

with tab_cache:
    st.markdown("### Cache Management")
    st.info("Cache files are stored in the output directory as CSV/JSON bundles.")

    cache_dir = Path("output")
    if cache_dir.exists():
        runs = sorted(cache_dir.iterdir(), reverse=True)
        st.markdown(f"**Found {len(runs)} run directories:**")
        for run_dir in runs[:10]:
            if run_dir.is_dir():
                size = sum(f.stat().st_size for f in run_dir.rglob("*") if f.is_file())
                st.text(f"  {run_dir.name}  ({size:,} bytes)")

        if st.button("Clear All Output", type="secondary"):
            import shutil
            for run_dir in runs:
                if run_dir.is_dir():
                    shutil.rmtree(run_dir)
            st.success("All output directories cleared.")
            st.rerun()
    else:
        st.info("No output directory found yet.")

with tab_about:
    st.markdown("### About Meta Ads Ultimate Dashboard")
    st.markdown("""
**Version:** 1.0.0
**Architecture:** 7-Layer (Config -> API -> Extraction -> Export -> Analytics -> Comparison -> Presentation)
**API Version:** v25.0
**Framework:** Streamlit + pandas + openpyxl + plotly

**Principles:**
1. Edge Configuration Sovereignty
2. Nothing Is Mandatory
3. Brand Isolation
4. View-Only External Sources
5. Transparent Data Pipeline
6. Fail-Soft Execution
7. Local-First, Free-Forever
8. GUI-First Configuration

**All Metrics:** 70+ fields across Delivery, Actions, Video, Quality, Engagement, Catalog
**All Levels:** Account, Campaign, Ad Set, Ad
**All Breakdowns:** 20+ breakdown configurations including demographics, placement, device, hourly, and asset breakdowns
    """)
