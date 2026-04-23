"""
Meta Ads API Field Catalog — Complete reference of all available fields,
breakdowns, date presets, levels, and action types.
Official API docs: https://developers.facebook.com/docs/marketing-api/reference/ads-insights/
"""

API_VERSION = "v25.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
PAGE_LIMIT = 500
MAX_WORKERS = 5
MAX_RETRIES = 6
DEFAULT_OUTPUT_DIR = "output"

# ═══════════════════════════════════════════════════════════════════════════════
# DATE PRESETS
# ═══════════════════════════════════════════════════════════════════════════════

DATE_PRESETS = {
    "today": "today",
    "yesterday": "yesterday",
    "last_3d": "last_3d",
    "last_7d": "last_7d",
    "last_14d": "last_14d",
    "last_28d": "last_28d",
    "last_30d": "last_30d",
    "last_60d": "last_60d",
    "last_90d": "last_90d",
    "this_month": "this_month",
    "last_month": "last_month",
    "this_quarter": "this_quarter",
    "this_year": "this_year",
    "last_year": "last_year",
    "lifetime": "maximum",
    "maximum": "maximum",
}

TIME_INCREMENTS = [1, 7, 14, 30, "monthly", "all_days"]

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LEVELS
# ═══════════════════════════════════════════════════════════════════════════════

LEVELS = ["account", "campaign", "adset", "ad"]

LEVEL_CONFIGS = {
    "account": {"level": "account", "label": "Account"},
    "campaign": {"level": "campaign", "label": "Campaign"},
    "adset": {"level": "adset", "label": "Ad Set"},
    "ad": {"level": "ad", "label": "Ad"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# ACTION REPORT TIMES
# ═══════════════════════════════════════════════════════════════════════════════

ACTION_REPORT_TIMES = ["impression", "conversion", "mixed"]

# ═══════════════════════════════════════════════════════════════════════════════
# METRICS — ALL VALID META API TOP-LEVEL FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

DELIVERY_METRICS = [
    "account_id", "account_name",
    "campaign_id", "campaign_name",
    "adset_id", "adset_name",
    "ad_id", "ad_name",
    "date_start", "date_stop",
    "impressions", "reach", "frequency",
    "spend", "cpm", "cpc", "cpp", "ctr",
    "clicks", "inline_link_clicks", "inline_link_click_ctr",
    "outbound_clicks", "outbound_clicks_ctr",
    "objective", "buying_type",
]

ACTION_METRICS = [
    "actions", "action_values", "cost_per_action_type",
    "conversions", "conversion_values", "cost_per_conversion",
    "purchase_roas", "website_purchase_roas",
]

VIDEO_METRICS = [
    "video_play_actions",
    "video_avg_time_watched_actions",
    "video_p25_watched_actions",
    "video_p50_watched_actions",
    "video_p75_watched_actions",
    "video_p100_watched_actions",
    "video_thruplay_watched_actions",
]

QUALITY_METRICS = [
    "quality_ranking", "engagement_rate_ranking",
    "conversion_rate_ranking",
    "estimated_ad_recallers", "estimated_ad_recall_rate",
]

ENGAGEMENT_METRICS = [
    "social_spend",
    "canvas_avg_view_time", "canvas_avg_view_percent",
    "instant_experience_clicks_to_open",
    "instant_experience_clicks_to_start",
    "instant_experience_outbound_clicks",
]

CATALOG_METRICS = ["catalog_segment_actions", "catalog_segment_value"]

ALL_METRICS = list(dict.fromkeys(
    DELIVERY_METRICS + ACTION_METRICS + VIDEO_METRICS +
    QUALITY_METRICS + ENGAGEMENT_METRICS + CATALOG_METRICS
))

IDENTIFIERS = [
    "account_id", "account_name",
    "campaign_id", "campaign_name",
    "adset_id", "adset_name",
    "ad_id", "ad_name",
    "date_start", "date_stop",
]

HOURLY_METRICS = [m for m in ALL_METRICS if m not in ("reach", "frequency")]
REGION_METRICS = [m for m in ALL_METRICS if m not in ACTION_METRICS + CATALOG_METRICS]
FREQUENCY_METRICS = ["reach", "impressions", "frequency"]

# ═══════════════════════════════════════════════════════════════════════════════
# CORE FIELDS (for config.json compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

CORE_FIELDS = [
    "account_id", "account_name", "campaign_id", "campaign_name",
    "adset_id", "adset_name", "ad_id", "ad_name",
    "objective", "buying_type", "spend", "impressions", "reach",
    "frequency", "clicks", "unique_clicks", "ctr", "unique_ctr",
    "cpc", "cpm", "cpp", "actions", "action_values",
    "cost_per_action_type", "conversions", "conversion_values",
    "purchase_roas", "website_purchase_roas", "outbound_clicks",
    "cost_per_outbound_click", "quality_ranking",
    "engagement_rate_ranking", "conversion_rate_ranking",
    "video_play_actions", "video_p25_watched_actions",
    "video_p50_watched_actions", "video_p75_watched_actions",
    "video_p95_watched_actions", "video_p100_watched_actions",
    "estimated_ad_recallers", "date_start", "date_stop",
]

# ═══════════════════════════════════════════════════════════════════════════════
# BREAKDOWN CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

COMMON_BREAKDOWNS = [
    "age", "gender", "country", "region", "dma", "impression_device",
    "publisher_platform", "platform_position", "device_platform", "product_id",
    "hourly_stats_aggregated_by_advertiser_time_zone",
    "hourly_stats_aggregated_by_audience_time_zone",
]

COMMON_ACTION_BREAKDOWNS = [
    "action_type", "action_device", "action_destination",
    "action_reaction", "action_video_sound",
    "action_target_id", "action_carousel_card_id",
]

BREAKDOWN_CONFIGS = {
    "none": {
        "label": "No Breakdown",
        "breakdowns": [],
        "metrics": ALL_METRICS,
    },
    "age": {
        "label": "Age",
        "breakdowns": ["age"],
        "metrics": ALL_METRICS,
    },
    "gender": {
        "label": "Gender",
        "breakdowns": ["gender"],
        "metrics": ALL_METRICS,
    },
    "age_gender": {
        "label": "Age + Gender",
        "breakdowns": ["age", "gender"],
        "metrics": ALL_METRICS,
    },
    "country": {
        "label": "Country",
        "breakdowns": ["country"],
        "metrics": ALL_METRICS,
    },
    "region": {
        "label": "Region",
        "breakdowns": ["region"],
        "metrics": REGION_METRICS,
    },
    "dma": {
        "label": "DMA",
        "breakdowns": ["dma"],
        "metrics": REGION_METRICS,
    },
    "placement": {
        "label": "Publisher + Position",
        "breakdowns": ["publisher_platform", "platform_position"],
        "metrics": ALL_METRICS,
    },
    "publisher_platform": {
        "label": "Publisher Platform",
        "breakdowns": ["publisher_platform"],
        "metrics": ALL_METRICS,
    },
    "platform_position": {
        "label": "Platform Position",
        "breakdowns": ["platform_position"],
        "metrics": ALL_METRICS,
    },
    "device": {
        "label": "Device Platform",
        "breakdowns": ["device_platform"],
        "metrics": ALL_METRICS,
    },
    "impression_device": {
        "label": "Impression Device",
        "breakdowns": ["impression_device"],
        "metrics": ALL_METRICS,
    },
    "hourly": {
        "label": "Hourly (Advertiser TZ)",
        "breakdowns": ["hourly_stats_aggregated_by_advertiser_time_zone"],
        "metrics": HOURLY_METRICS,
    },
    "hourly_audience": {
        "label": "Hourly (Audience TZ)",
        "breakdowns": ["hourly_stats_aggregated_by_audience_time_zone"],
        "metrics": HOURLY_METRICS,
    },
    "frequency_value": {
        "label": "Frequency Value",
        "breakdowns": ["frequency_value"],
        "metrics": FREQUENCY_METRICS,
    },
    "image_asset": {
        "label": "Image Asset",
        "breakdowns": ["image_asset"],
        "metrics": ALL_METRICS,
    },
    "video_asset": {
        "label": "Video Asset",
        "breakdowns": ["video_asset"],
        "metrics": ALL_METRICS,
    },
    "body_asset": {
        "label": "Body Text Asset",
        "breakdowns": ["body_asset"],
        "metrics": ALL_METRICS,
    },
    "title_asset": {
        "label": "Title Asset",
        "breakdowns": ["title_asset"],
        "metrics": ALL_METRICS,
    },
    "description_asset": {
        "label": "Description Asset",
        "breakdowns": ["description_asset"],
        "metrics": ALL_METRICS,
    },
    "cta_asset": {
        "label": "CTA Button Asset",
        "breakdowns": ["call_to_action_asset"],
        "metrics": ALL_METRICS,
    },
    "product_id": {
        "label": "Product ID",
        "breakdowns": ["product_id"],
        "metrics": [m for m in ALL_METRICS if "catalog" in m or m in [
            "impressions", "reach", "spend", "clicks",
            "account_id", "account_name", "campaign_id", "campaign_name",
            "adset_id", "adset_name", "ad_id", "ad_name",
            "date_start", "date_stop",
        ]],
    },
}

BREAKDOWN_FIELDS = sorted({
    b for cfg in BREAKDOWN_CONFIGS.values() for b in cfg["breakdowns"]
})

BREAKDOWN_INCOMPATIBILITY_HINTS = {
    "product_id": ["high cardinality, may fail on long ranges"],
    "hourly_stats_aggregated_by_advertiser_time_zone": ["use shorter date ranges"],
    "hourly_stats_aggregated_by_audience_time_zone": ["use shorter date ranges"],
}

# ═══════════════════════════════════════════════════════════════════════════════
# ACTION ARRAY FLATTENING PREFIXES
# ═══════════════════════════════════════════════════════════════════════════════

ARRAY_PREFIXES = {
    "actions": "action",
    "action_values": "action_value",
    "cost_per_action_type": "cost_per_action",
    "conversions": "conversion",
    "conversion_values": "conversion_value",
    "cost_per_conversion": "cost_per_conversion",
    "video_play_actions": "video_play",
    "video_avg_time_watched_actions": "video_avg_time",
    "video_p25_watched_actions": "video_p25",
    "video_p50_watched_actions": "video_p50",
    "video_p75_watched_actions": "video_p75",
    "video_p100_watched_actions": "video_p100",
    "video_thruplay_watched_actions": "video_thruplay",
    "outbound_clicks": "outbound_click",
    "outbound_clicks_ctr": "outbound_click_ctr",
    "purchase_roas": "purchase_roas",
    "website_purchase_roas": "website_purchase_roas",
    "catalog_segment_actions": "catalog_action",
    "catalog_segment_value": "catalog_value",
}

# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGN MANAGEMENT CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

CAMPAIGN_OBJECTIVES = {
    "Awareness": "OUTCOME_AWARENESS",
    "Traffic": "OUTCOME_TRAFFIC",
    "Engagement": "OUTCOME_ENGAGEMENT",
    "Leads": "OUTCOME_LEADS",
    "App Promotion": "OUTCOME_APP_PROMOTION",
    "Sales": "OUTCOME_SALES",
}

BID_STRATEGIES = {
    "Lowest Cost (No Cap)": "LOWEST_COST_WITHOUT_CAP",
    "Lowest Cost (Bid Cap)": "LOWEST_COST_WITH_BID_CAP",
    "Cost Cap": "COST_CAP",
    "Minimum ROAS": "MIN_ROAS",
}

CAMPAIGN_STATUSES = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]
ADSET_STATUSES = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]
AD_STATUSES = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED"]

# ═══════════════════════════════════════════════════════════════════════════════
# POWER BI DAX SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════════

DAX_SUGGESTIONS = {
    "Total Spend": "SUM(FactInsights[spend])",
    "CTR %": "DIVIDE(SUM(FactInsights[clicks]), SUM(FactInsights[impressions]))",
    "CPC": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[clicks]))",
    "CPM": "DIVIDE(SUM(FactInsights[spend]) * 1000, SUM(FactInsights[impressions]))",
    "ROAS": "DIVIDE(SUM(FactInsights[purchase_value]), SUM(FactInsights[spend]))",
    "CPA": "DIVIDE(SUM(FactInsights[spend]), SUM(FactInsights[purchases]))",
}
