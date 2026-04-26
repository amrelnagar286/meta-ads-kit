"""
Creative Audit -- Hook Rate, Hold Rate, Fatigue Index, Ghost Impressions.
Identifies winning and dying creatives.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe
from src.formula_engine import evaluate_formula

st.set_page_config(page_title="Creative Audit", page_icon="🎨", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#E3008C;">Creative Audit</h1>'
    '<p style="color:#666;">Hook Rate, Hold Rate, Fatigue Index, Ghost Impressions</p>',
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

# Compute creative metrics per row
cols_lower = {c.lower(): c for c in df.columns}
result = df.copy()

computed = []

# Hook Rate
if "impressions" in cols_lower and any(k in cols_lower for k in ("video_3s_plays", "video_play_actions", "3s_plays")):
    imp_col = cols_lower["impressions"]
    play_col = cols_lower.get("video_3s_plays") or cols_lower.get("video_play_actions") or cols_lower.get("3s_plays")
    result["hook_rate"] = (pd.to_numeric(result[play_col], errors="coerce") / pd.to_numeric(result[imp_col], errors="coerce").replace(0, float("nan")) * 100).round(2)
    computed.append("hook_rate")

# Hold Rate
thruplay_col = cols_lower.get("video_thruplay") or cols_lower.get("video_thruplay_watched_actions")
play_3s_col = cols_lower.get("video_3s_plays") or cols_lower.get("video_play_actions")
if thruplay_col and play_3s_col:
    result["hold_rate"] = (pd.to_numeric(result[thruplay_col], errors="coerce") / pd.to_numeric(result[play_3s_col], errors="coerce").replace(0, float("nan")) * 100).round(2)
    computed.append("hold_rate")

# Creative Fatigue Index
freq_col = cols_lower.get("frequency")
ctr_col = cols_lower.get("outbound_ctr") or cols_lower.get("ctr")
if freq_col and ctr_col:
    freq = pd.to_numeric(result[freq_col], errors="coerce").fillna(0)
    ctr = pd.to_numeric(result[ctr_col], errors="coerce").fillna(0)
    result["fatigue_index"] = (freq * (1 - ctr / 100)).round(2)
    computed.append("fatigue_index")

# Ghost Impression Rate
if "impressions" in cols_lower and "reach" in cols_lower:
    imp = pd.to_numeric(result[cols_lower["impressions"]], errors="coerce").fillna(0)
    reach = pd.to_numeric(result[cols_lower["reach"]], errors="coerce").fillna(0)
    result["ghost_rate"] = (((imp - reach) / imp.replace(0, float("nan"))) * 100).round(2)
    computed.append("ghost_rate")

# Drop-off Rate
lc_col = cols_lower.get("link_clicks")
lpv_col = cols_lower.get("landing_page_views")
if lc_col and lpv_col:
    lc = pd.to_numeric(result[lc_col], errors="coerce").fillna(0)
    lpv = pd.to_numeric(result[lpv_col], errors="coerce").fillna(0)
    result["dropoff_rate"] = (((lc - lpv) / lc.replace(0, float("nan"))) * 100).round(2)
    computed.append("dropoff_rate")

if not computed:
    st.warning("Need video metrics (3s plays, ThruPlays) or engagement metrics for creative audit.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATE KPIs
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="section-title" style="background:#E3008C;">Creative Health Overview</div>', unsafe_allow_html=True)

metric_cards = []
if "hook_rate" in computed:
    avg_hook = result["hook_rate"].mean()
    badge = "Healthy" if avg_hook >= 25 else "Warning" if avg_hook >= 15 else "Critical"
    badge_class = "badge-healthy" if avg_hook >= 25 else "badge-warning" if avg_hook >= 15 else "badge-critical"
    metric_cards.append(("Hook Rate", f"{avg_hook:.1f}%", f'<span class="{badge_class}">{badge}</span>', "> 25% healthy"))

if "hold_rate" in computed:
    avg_hold = result["hold_rate"].mean()
    badge = "Healthy" if avg_hold >= 30 else "Warning" if avg_hold >= 20 else "Critical"
    badge_class = "badge-healthy" if avg_hold >= 30 else "badge-warning" if avg_hold >= 20 else "badge-critical"
    metric_cards.append(("Hold Rate", f"{avg_hold:.1f}%", f'<span class="{badge_class}">{badge}</span>', "> 30% healthy"))

if "fatigue_index" in computed:
    avg_fatigue = result["fatigue_index"].mean()
    badge = "Fresh" if avg_fatigue < 1.5 else "Fatiguing" if avg_fatigue < 2.5 else "Exhausted"
    badge_class = "badge-healthy" if avg_fatigue < 1.5 else "badge-warning" if avg_fatigue < 2.5 else "badge-critical"
    metric_cards.append(("Fatigue Index", f"{avg_fatigue:.2f}", f'<span class="{badge_class}">{badge}</span>', "< 2.5 safe"))

if "ghost_rate" in computed:
    avg_ghost = result["ghost_rate"].mean()
    badge = "Clean" if avg_ghost < 25 else "Wasteful" if avg_ghost < 40 else "Toxic"
    badge_class = "badge-healthy" if avg_ghost < 25 else "badge-warning" if avg_ghost < 40 else "badge-critical"
    metric_cards.append(("Ghost Rate", f"{avg_ghost:.1f}%", f'<span class="{badge_class}">{badge}</span>', "< 25% clean"))

cols = st.columns(len(metric_cards))
for i, (name, value, badge, hint) in enumerate(metric_cards):
    with cols[i]:
        st.markdown(
            f'<div class="metric-card">'
            f'<h3>{name}</h3>'
            f'<div class="metric-value">{value}</div>'
            f'<div class="metric-trend">{badge} | {hint}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════════════════
# CREATIVE RANKINGS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Creative Rankings")

name_col = None
for candidate in ["ad_name", "ad_id", "adset_name", "campaign_name"]:
    if candidate in cols_lower:
        name_col = cols_lower[candidate]
        break

display_cols = [name_col] if name_col else []
display_cols += [c for c in computed if c in result.columns]

if display_cols:
    sort_by = st.selectbox("Sort by", computed, key="creative_sort")
    ascending = st.checkbox("Ascending", value=False, key="creative_asc")
    sorted_df = result[display_cols].dropna(subset=[sort_by]).sort_values(sort_by, ascending=ascending)
    downloadable_dataframe(sorted_df.head(50), key="creative_audit", label="creative_audit", use_container_width=True, hide_index=True)

    # Scatter plot
    if len(computed) >= 2:
        st.markdown("#### Creative Performance Map")
        x_metric = st.selectbox("X Axis", computed, index=0, key="creative_x")
        y_metric = st.selectbox("Y Axis", computed, index=min(1, len(computed) - 1), key="creative_y")
        fig = px.scatter(
            result,
            x=x_metric,
            y=y_metric,
            hover_name=name_col if name_col else None,
            color=computed[0] if computed else None,
            color_continuous_scale=["#D13438", "#FFB900", "#107C10"],
            template="plotly_white",
            title=f"{x_metric} vs {y_metric}",
        )
        fig.update_layout(font_family="Segoe UI")
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ACTION ALERTS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Action Alerts")

alerts = []
if "hook_rate" in computed:
    dead_creatives = result[result["hook_rate"] < 15]
    if not dead_creatives.empty:
        alerts.append(f"**{len(dead_creatives)} creatives** have Hook Rate < 15% (dead creatives, pause immediately)")
if "fatigue_index" in computed:
    fatigued = result[result["fatigue_index"] > 2.5]
    if not fatigued.empty:
        alerts.append(f"**{len(fatigued)} creatives** have Fatigue Index > 2.5 (CPM penalty incoming)")
if "ghost_rate" in computed:
    ghosts = result[result["ghost_rate"] > 40]
    if not ghosts.empty:
        alerts.append(f"**{len(ghosts)} creatives** have Ghost Rate > 40% (Meta milking your budget)")
if "dropoff_rate" in computed:
    drops = result[result["dropoff_rate"] > 30]
    if not drops.empty:
        alerts.append(f"**{len(drops)} entries** have Drop-off Rate > 30% (slow site or accidental clicks)")

if alerts:
    for alert in alerts:
        st.markdown(f'<div class="metric-card" style="border-left: 4px solid #D13438;">{alert}</div>', unsafe_allow_html=True)
else:
    st.success("No critical alerts. Creative health looks good!")

st.markdown("---")
render_quick_add_metric("creative")
