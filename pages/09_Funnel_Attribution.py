"""
Funnel & Attribution Analysis — Conversion funnel visualization, attribution modeling,
touchpoint analysis, and customer journey mapping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.meta_api import MetaAPIManager
from src.extractor import MetaAdsExtractor
from src.helpers import format_currency, format_number, format_percentage, safe_float, safe_int, safe_divide

st.set_page_config(page_title="Funnel & Attribution", page_icon="🔀", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .funnel-step { background: white; border-radius: 8px; padding: 16px; margin: 4px;
        border: 1px solid #e0e0e0; text-align: center; }
    .funnel-arrow { text-align: center; font-size: 1.5rem; color: #0078D4; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Funnel & Attribution Analysis")

api = get_api()

tab_funnel, tab_attribution, tab_touchpoints, tab_journey, tab_pixel = st.tabs([
    "Conversion Funnel", "Attribution Models", "Touchpoint Analysis",
    "Customer Journey", "Pixel & Events",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: CONVERSION FUNNEL
# ═══════════════════════════════════════════════════════════════════════════════

with tab_funnel:
    st.markdown('<div class="section-title">Conversion Funnel</div>', unsafe_allow_html=True)

    date_range = st.selectbox("Date Range", ["last_7d", "last_14d", "last_30d", "last_60d"], index=2, key="fn_date")

    if st.button("Build Funnel", type="primary", key="fn_build"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )
            df = ext.fetch_insights(level="account", breakdown_key="none", preset=date_range)

            if not df.empty:
                impressions = safe_int(df["impressions"].sum())
                clicks = safe_int(df["clicks"].sum())
                reach = safe_int(df.get("reach", pd.Series([0])).sum())
                spend = safe_float(df["spend"].sum())

                # Try to get action data
                conversions = 0
                purchases = 0
                for col in df.columns:
                    if "conversion" in col.lower() and "value" not in col.lower():
                        conversions += safe_int(df[col].sum())
                    if "purchase" in col.lower() and "value" not in col.lower() and "roas" not in col.lower():
                        purchases += safe_int(df[col].sum())

                estimated = False
                if conversions == 0:
                    conversions = int(clicks * 0.03)
                    estimated = True
                if purchases == 0:
                    purchases = int(conversions * 0.4)
                    estimated = True

                if estimated:
                    st.warning(
                        "Conversion and purchase data not found in your account. "
                        "Values shown below are **estimates** based on industry averages "
                        "(3% click-to-conversion, 40% conversion-to-purchase). "
                        "Set up the Meta Pixel or Conversions API for real data."
                    )

                # Funnel visualization
                funnel_steps = [
                    ("Impressions", impressions),
                    ("Reach", reach),
                    ("Clicks", clicks),
                    ("Conversions", conversions),
                    ("Purchases", purchases),
                ]

                cols = st.columns(len(funnel_steps))
                for i, (label, value) in enumerate(funnel_steps):
                    with cols[i]:
                        drop_rate = ""
                        if i > 0:
                            prev = funnel_steps[i-1][1]
                            rate = safe_divide(value, prev) * 100
                            drop_rate = f"({rate:.1f}% of prev)"
                        st.markdown(f"""
                        <div class="funnel-step">
                            <div style="font-size: 0.85rem; color: #666;">{label}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #0078D4;">{format_number(value)}</div>
                            <div style="font-size: 0.75rem; color: #999;">{drop_rate}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # Conversion metrics
                st.markdown("### Funnel Metrics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CTR", format_percentage(safe_divide(clicks, impressions) * 100))
                c2.metric("Click-to-Conv", format_percentage(safe_divide(conversions, clicks) * 100))
                c3.metric("Conv-to-Purchase", format_percentage(safe_divide(purchases, conversions) * 100))
                c4.metric("Overall Conv Rate", format_percentage(safe_divide(purchases, impressions) * 100))

                # Cost metrics
                st.markdown("### Cost Per Stage")
                c5, c6, c7, c8 = st.columns(4)
                c5.metric("Cost per Click", format_currency(safe_divide(spend, clicks)))
                c6.metric("Cost per Conv", format_currency(safe_divide(spend, conversions)))
                c7.metric("Cost per Purchase", format_currency(safe_divide(spend, purchases)))
                c8.metric("Total Spend", format_currency(spend))

                # Bar chart
                st.bar_chart(pd.DataFrame(funnel_steps, columns=["Stage", "Count"]).set_index("Stage"))
            else:
                st.info("No data available for funnel analysis.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: ATTRIBUTION MODELS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_attribution:
    st.markdown('<div class="section-title">Attribution Model Comparison</div>', unsafe_allow_html=True)

    st.markdown("""
    Compare how different attribution windows affect your ROAS and conversion counts.
    Meta supports click and view attribution with various windows.
    """)

    attr_windows = {
        "1-day click": "1d_click",
        "7-day click": "7d_click",
        "28-day click": "28d_click",
        "1-day view": "1d_view",
        "7-day view": "7d_view",
        "28-day view": "28d_view",
    }

    selected_windows = st.multiselect(
        "Attribution Windows to Compare",
        list(attr_windows.keys()),
        default=["1-day click", "7-day click", "1-day view"],
        key="attr_windows",
    )

    if selected_windows and st.button("Compare Attribution", type="primary", key="attr_compare"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )

            attr_results = []
            for window_name in selected_windows:
                window_key = attr_windows[window_name]
                df = ext.fetch_insights(
                    level="campaign", breakdown_key="none", preset="last_30d",
                    attribution_windows=[window_key],
                )
                if not df.empty:
                    spend = safe_float(df["spend"].sum())
                    imps = safe_int(df["impressions"].sum())
                    clicks = safe_int(df["clicks"].sum())
                    attr_results.append({
                        "Attribution Window": window_name,
                        "Spend": format_currency(spend),
                        "Impressions": format_number(imps),
                        "Clicks": format_number(clicks),
                        "CTR %": round(safe_divide(clicks, imps) * 100, 2),
                        "CPC": format_currency(safe_divide(spend, clicks)),
                    })

            if attr_results:
                st.dataframe(pd.DataFrame(attr_results), use_container_width=True, hide_index=True)
            else:
                st.info("No attribution data available.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("### Attribution Model Guide")
    st.markdown("""
    | Model | Description | Best For |
    |-------|-------------|----------|
    | **1-day click** | Conversions within 1 day of clicking | Direct response, impulse purchases |
    | **7-day click** | Conversions within 7 days of clicking | E-commerce, considered purchases |
    | **28-day click** | Conversions within 28 days of clicking | High-value products, long sales cycles |
    | **1-day view** | Conversions within 1 day of viewing (no click) | Brand awareness, remarketing |
    | **7-day view** | Conversions within 7 days of viewing | Display/video campaigns |
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: TOUCHPOINT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_touchpoints:
    st.markdown('<div class="section-title">Touchpoint Analysis</div>', unsafe_allow_html=True)

    st.markdown("Analyze performance by placement and platform to understand the customer journey.")

    if st.button("Load Placement Data", type="primary", key="tp_load"):
        try:
            ext = MetaAdsExtractor(
                st.session_state.access_token,
                st.session_state.ad_account_id,
            )

            # Fetch by placement breakdown
            df = ext.fetch_insights(level="campaign", breakdown_key="placement", preset="last_30d")

            if not df.empty:
                if "publisher_platform" in df.columns and "platform_position" in df.columns:
                    tp_df = df.groupby(["publisher_platform", "platform_position"]).agg({
                        "spend": "sum",
                        "impressions": "sum",
                        "clicks": "sum",
                    }).reset_index()
                    tp_df["CTR %"] = tp_df.apply(
                        lambda r: round(safe_divide(r["clicks"], r["impressions"]) * 100, 2), axis=1
                    )
                    tp_df["CPC"] = tp_df.apply(
                        lambda r: round(safe_divide(r["spend"], r["clicks"]), 2), axis=1
                    )
                    tp_df.columns = ["Platform", "Position", "Spend", "Impressions", "Clicks", "CTR %", "CPC"]
                    tp_df = tp_df.sort_values("Spend", ascending=False)

                    st.dataframe(tp_df, use_container_width=True, hide_index=True)

                    # Charts
                    st.markdown("### Spend by Platform")
                    platform_spend = tp_df.groupby("Platform")["Spend"].sum()
                    st.bar_chart(platform_spend)

                    st.markdown("### CTR by Position")
                    st.bar_chart(tp_df.set_index("Position")["CTR %"])
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No placement data available.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: CUSTOMER JOURNEY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_journey:
    st.markdown('<div class="section-title">Customer Journey Map</div>', unsafe_allow_html=True)

    st.markdown("""
    Visualize how users move through your ad campaigns across different stages.
    Map campaigns to funnel stages for a complete journey view.
    """)

    STAGES = ["Awareness", "Consideration", "Conversion", "Retention"]

    try:
        campaigns = api.get_campaigns(status_filter=["ACTIVE", "PAUSED"])
        if campaigns:
            st.markdown("### Assign Campaigns to Journey Stages")

            stage_assignments = {}
            for stage in STAGES:
                assigned = st.multiselect(
                    f"{stage} Stage",
                    options=[c["id"] for c in campaigns],
                    format_func=lambda x: next(
                        (f"{c.get('name', '')} ({c['id']})" for c in campaigns if c["id"] == x), x
                    ),
                    key=f"jrn_{stage}",
                )
                stage_assignments[stage] = assigned

            if st.button("Analyze Journey", type="primary", key="jrn_analyze"):
                ext = MetaAdsExtractor(
                    st.session_state.access_token,
                    st.session_state.ad_account_id,
                )

                journey_data = []
                for stage, camp_ids in stage_assignments.items():
                    if camp_ids:
                        df = ext.fetch_insights(
                            level="campaign", breakdown_key="none",
                            preset="last_30d", campaign_ids=camp_ids,
                        )
                        if not df.empty:
                            spend = safe_float(df["spend"].sum())
                            imps = safe_int(df["impressions"].sum())
                            clicks = safe_int(df["clicks"].sum())
                            journey_data.append({
                                "Stage": stage,
                                "Campaigns": len(camp_ids),
                                "Spend": format_currency(spend),
                                "Impressions": format_number(imps),
                                "Clicks": format_number(clicks),
                                "CTR %": round(safe_divide(clicks, imps) * 100, 2),
                                "CPC": format_currency(safe_divide(spend, clicks)),
                            })

                if journey_data:
                    st.dataframe(pd.DataFrame(journey_data), use_container_width=True, hide_index=True)
        else:
            st.info("No campaigns found.")
    except Exception as e:
        st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: PIXEL & EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_pixel:
    st.markdown('<div class="section-title">Pixel & Conversion Events</div>', unsafe_allow_html=True)

    if st.button("Load Pixels", type="primary", key="px_load"):
        try:
            pixels = api.get_pixels()
            if pixels:
                rows = []
                for p in pixels:
                    rows.append({
                        "ID": p.get("id", ""),
                        "Name": p.get("name", ""),
                        "Last Fired": p.get("last_fired_time", "Never"),
                        "Status": "Unavailable" if p.get("is_unavailable") else "Active",
                        "Created": (p.get("creation_time") or "")[:10],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # Pixel stats
                for p in pixels[:3]:
                    with st.expander(f"Stats: {p.get('name', p.get('id', ''))}"):
                        try:
                            stats = api.get_pixel_stats(p["id"])
                            st.json(stats)
                        except Exception as e:
                            st.error(f"Failed to get stats: {e}")
            else:
                st.info("No pixels found.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("### Custom Conversions")
    if st.button("Load Custom Conversions", key="cc_load"):
        try:
            conversions = api.get_custom_conversions()
            if conversions:
                rows = []
                for c in conversions:
                    rows.append({
                        "ID": c.get("id", ""),
                        "Name": c.get("name", ""),
                        "Event Source": c.get("event_source_type", ""),
                        "Default Value": c.get("default_conversion_value", ""),
                        "First Fired": c.get("first_fired_time", "Never"),
                        "Last Fired": c.get("last_fired_time", "Never"),
                        "Archived": c.get("is_archived", False),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No custom conversions found.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.markdown("---")
    st.markdown("### Pixel Installation Check")
    st.markdown("""
    Verify your Meta Pixel is correctly installed on your website.

    **Your Pixel base code:**
    ```html
    <!-- Meta Pixel Code -->
    <script>
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', 'YOUR_PIXEL_ID');
    fbq('track', 'PageView');
    </script>
    ```

    **Standard Events:**
    | Event | When to fire |
    |-------|-------------|
    | `ViewContent` | Product page view |
    | `AddToCart` | Item added to cart |
    | `InitiateCheckout` | Checkout started |
    | `Purchase` | Purchase completed |
    | `Lead` | Lead form submitted |
    | `CompleteRegistration` | Sign-up completed |
    """)
