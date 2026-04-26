"""
Messaging & Lead Analysis -- For message-based campaigns.
Links conversation data with order/CRM data from external sources.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from src.helpers import WINDOWS_11_CSS, safe_divide, render_quick_add_metric, downloadable_dataframe

st.set_page_config(page_title="Messaging Analysis", page_icon="💬", layout="wide")
st.markdown(WINDOWS_11_CSS, unsafe_allow_html=True)

st.markdown(
    '<h1 style="color:#00B7C3;">Messaging & Lead Analysis</h1>'
    '<p style="color:#666;">Message-to-Order Conversion, Conversation Costs, Lead Quality</p>',
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

cols_lower = {c.lower(): c for c in df.columns}

# Detect messaging-related columns
msg_cols = [c for c in df.columns if any(kw in c.lower() for kw in ("message", "conversation", "reply", "chat", "whatsapp", "messenger"))]
lead_cols = [c for c in df.columns if any(kw in c.lower() for kw in ("lead", "contact", "inquiry", "form"))]
order_cols = [c for c in df.columns if any(kw in c.lower() for kw in ("order", "sale", "purchase", "transaction", "revenue"))]

st.markdown('<div class="section-title" style="background:#00B7C3;">Messaging Performance</div>', unsafe_allow_html=True)

if not msg_cols and not lead_cols:
    st.info("""
    **No messaging or lead columns detected.**
    
    To use this analysis, make sure your data includes columns like:
    - `messaging_conversations_started` (from Meta ads export)
    - `leads` (from Meta ads export)
    - `orders_from_messages` (from your CRM/order sheet -- link via the Link & Merge tab)
    - `message_revenue` (from your order data)
    
    **Tip:** Import your Meta ads data AND your order sheet, then use **Link & Merge** to join them 
    on a shared column (like `ad_id` or `campaign_name`). Then come back here for analysis.
    """)

    # Show available columns for debugging
    with st.expander("Available Columns"):
        st.code(", ".join(sorted(df.columns.tolist())))
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGING KPIs
# ═══════════════════════════════════════════════════════════════════════════════

metrics_computed = {}

spend_col = cols_lower.get("spend")
conversations_col = None
for candidate in ["messaging_conversations_started", "messaging_first_reply", "conversations"]:
    if candidate in cols_lower:
        conversations_col = cols_lower[candidate]
        break

leads_col = cols_lower.get("leads")
orders_col = None
for candidate in ["orders_from_messages", "orders", "total_orders", "purchases"]:
    if candidate in cols_lower:
        orders_col = cols_lower[candidate]
        break

revenue_col = None
for candidate in ["message_revenue", "revenue", "purchase_conversion_value", "order_value"]:
    if candidate in cols_lower:
        revenue_col = cols_lower[candidate]
        break

link_clicks_col = cols_lower.get("link_clicks") or cols_lower.get("clicks")

# Compute what we can
if conversations_col:
    total_conversations = pd.to_numeric(df[conversations_col], errors="coerce").sum()
    metrics_computed["Total Conversations"] = f"{total_conversations:,.0f}"

    if spend_col:
        total_spend = pd.to_numeric(df[spend_col], errors="coerce").sum()
        cpc_conv = safe_divide(total_spend, total_conversations)
        metrics_computed["Cost Per Conversation"] = f"${cpc_conv:,.2f}"

    if link_clicks_col:
        total_clicks = pd.to_numeric(df[link_clicks_col], errors="coerce").sum()
        msg_rate = safe_divide(total_conversations, total_clicks) * 100
        metrics_computed["Message Open Rate"] = f"{msg_rate:.1f}%"

    if orders_col:
        total_orders = pd.to_numeric(df[orders_col], errors="coerce").sum()
        msg_to_order = safe_divide(total_orders, total_conversations) * 100
        metrics_computed["Message-to-Order %"] = f"{msg_to_order:.1f}%"
        if spend_col:
            total_spend = pd.to_numeric(df[spend_col], errors="coerce").sum()
            cost_per_order = safe_divide(total_spend, total_orders)
            metrics_computed["Cost Per Order"] = f"${cost_per_order:,.2f}"

    if revenue_col:
        total_revenue = pd.to_numeric(df[revenue_col], errors="coerce").sum()
        rev_per_conv = safe_divide(total_revenue, total_conversations)
        metrics_computed["Revenue Per Conversation"] = f"${rev_per_conv:,.2f}"
        if spend_col:
            total_spend = pd.to_numeric(df[spend_col], errors="coerce").sum()
            msg_roas = safe_divide(total_revenue, total_spend)
            metrics_computed["Messaging ROAS"] = f"{msg_roas:.2f}"

if leads_col:
    total_leads = pd.to_numeric(df[leads_col], errors="coerce").sum()
    metrics_computed["Total Leads"] = f"{total_leads:,.0f}"
    if spend_col:
        total_spend = pd.to_numeric(df[spend_col], errors="coerce").sum()
        cpl = safe_divide(total_spend, total_leads)
        metrics_computed["Cost Per Lead"] = f"${cpl:,.2f}"

# Display KPI cards
if metrics_computed:
    cols = st.columns(min(len(metrics_computed), 5))
    for i, (name, value) in enumerate(metrics_computed.items()):
        with cols[i % len(cols)]:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{name}</h3>'
                f'<div class="metric-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# PER-ENTITY MESSAGING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("#### Messaging Performance by Entity")

group_cols = [c for c in df.columns if c.lower() in ("campaign_name", "adset_name", "ad_name", "campaign_id")]
if group_cols:
    group_by = st.selectbox("Group by", group_cols, key="msg_group")
    agg_dict = {}
    if spend_col:
        agg_dict[spend_col] = "sum"
    if conversations_col:
        agg_dict[conversations_col] = "sum"
    if leads_col:
        agg_dict[leads_col] = "sum"
    if orders_col:
        agg_dict[orders_col] = "sum"
    if revenue_col:
        agg_dict[revenue_col] = "sum"

    if agg_dict:
        grouped = df.groupby(group_by, as_index=False).agg(agg_dict)
        if conversations_col and spend_col:
            grouped["Cost_Per_Conversation"] = (grouped[spend_col] / grouped[conversations_col].replace(0, float("nan"))).round(2)
        if orders_col and conversations_col:
            grouped["Msg_to_Order_%"] = (grouped[orders_col] / grouped[conversations_col].replace(0, float("nan")) * 100).round(1)
        grouped = grouped.sort_values(spend_col if spend_col else list(agg_dict.keys())[0], ascending=False)
        downloadable_dataframe(grouped, key="msg_grouped", label="messaging_analysis", use_container_width=True, hide_index=True)

        # Chart
        if conversations_col and spend_col:
            fig = px.scatter(
                grouped,
                x="Cost_Per_Conversation" if "Cost_Per_Conversation" in grouped.columns else spend_col,
                y=conversations_col,
                size=spend_col if spend_col in grouped.columns else None,
                hover_name=group_by,
                template="plotly_white",
                title="Cost vs Conversations by Entity",
            )
            fig.update_layout(font_family="Segoe UI")
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LINKING GUIDE
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
with st.expander("How to Link Orders with Ad Data"):
    st.markdown("""
    **Step-by-step:**
    
    1. **Export your Meta ads data** with columns like `campaign_id`, `ad_id`, `messaging_conversations_started`
    2. **Prepare your order sheet** (Excel/Google Sheets) with columns like `ad_id`, `order_id`, `order_value`, `customer_name`
    3. **Import both** in the Import tab
    4. **Go to Link & Merge** tab:
       - Select Meta data as "Left Dataset"
       - Select your order sheet as "Right Dataset"
       - Map `ad_id` from both sides
       - Click "Execute Merge"
    5. **Come back here** -- all messaging + order metrics will now be available!
    
    **Example Order Sheet format:**
    | ad_id | order_date | order_value | customer_name | product |
    |-------|-----------|-------------|---------------|---------|
    | 123456 | 2024-01-15 | 150.00 | Ahmed | Product A |
    """)

st.markdown("---")
render_quick_add_metric("msg")
