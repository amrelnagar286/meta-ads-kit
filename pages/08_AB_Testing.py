"""
A/B Testing Framework — Set up, monitor, and analyze split tests.
Includes statistical significance calculation, winner declaration,
and automated test completion.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import json
import math
import os
from datetime import datetime, timedelta

from src.helpers import format_currency, format_percentage, safe_float, safe_divide

st.set_page_config(page_title="A/B Testing", page_icon="🔬", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .winner { background: #DFF6DD; border: 2px solid #107C10; border-radius: 8px;
        padding: 16px; text-align: center; }
    .loser { background: #FDE7E9; border: 2px solid #D13438; border-radius: 8px;
        padding: 16px; text-align: center; }
    .inconclusive { background: #FFF4CE; border: 2px solid #FFB900; border-radius: 8px;
        padding: 16px; text-align: center; }
</style>""", unsafe_allow_html=True)

TESTS_FILE = "config/ab_tests.json"


def load_tests():
    if os.path.exists(TESTS_FILE):
        try:
            with open(TESTS_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_tests(tests):
    os.makedirs(os.path.dirname(TESTS_FILE) or ".", exist_ok=True)
    with open(TESTS_FILE, "w") as f:
        json.dump(tests, f, indent=2, default=str)


def z_test_proportions(p1, n1, p2, n2):
    """Two-proportion z-test for A/B testing."""
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_pool == 0 or p_pool == 1:
        return 0.0, 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    # Approximate p-value from z-score (two-tailed)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return z, p_value


Z_LOOKUP = {0.10: 1.282, 0.05: 1.960, 0.01: 2.576}
POWER_LOOKUP = {0.80: 0.842, 0.90: 1.282}


def calculate_sample_size(baseline_rate, mde, alpha=0.05, power=0.80):
    """Calculate required sample size per variant."""
    if baseline_rate <= 0 or mde <= 0:
        return 0
    z_alpha = Z_LOOKUP.get(alpha, 1.960)
    z_beta = POWER_LOOKUP.get(power, 0.842)
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    n = ((z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))) / ((p1 - p2) ** 2)
    return int(math.ceil(n))


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# A/B Testing Framework")
st.markdown("Set up controlled experiments, monitor results, and declare winners with statistical confidence.")

tab_setup, tab_monitor, tab_results, tab_calc, tab_history = st.tabs([
    "Setup Test", "Monitor Tests", "Results & Analysis",
    "Sample Size Calculator", "Test History",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SETUP TEST
# ═══════════════════════════════════════════════════════════════════════════════

with tab_setup:
    st.markdown('<div class="section-title">Setup New A/B Test</div>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        test_name = st.text_input("Test Name *", key="ab_name")
        test_hypothesis = st.text_area("Hypothesis", placeholder="e.g. Changing CTA to 'Shop Now' will increase CTR by 15%", key="ab_hypo")
        test_type = st.selectbox(
            "Test Type",
            ["Ad Creative", "Ad Copy", "Audience", "Placement",
             "Bid Strategy", "Landing Page", "Call to Action", "Custom"],
            key="ab_type",
        )
        primary_metric = st.selectbox(
            "Primary Metric (goal)",
            ["ctr", "cpc", "cpa", "roas", "cvr", "cpm"],
            key="ab_metric",
        )
    with col_s2:
        n_variants = st.number_input("Number of Variants", 2, 5, 2, key="ab_n_var")
        confidence_level = st.selectbox("Confidence Level", ["90%", "95%", "99%"], index=1, key="ab_conf")
        test_duration = st.number_input("Test Duration (days)", 3, 90, 14, key="ab_duration")
        traffic_split = st.selectbox(
            "Traffic Split",
            ["Even (50/50)", "70/30", "80/20", "Custom"],
            key="ab_split",
        )

    st.markdown("### Variant Configuration")
    variants = []
    for i in range(int(n_variants)):
        label = "Control" if i == 0 else f"Variant {chr(65 + i)}"
        col_v1, col_v2 = st.columns([1, 3])
        with col_v1:
            st.markdown(f"**{label}**")
        with col_v2:
            var_desc = st.text_input(f"{label} description", key=f"ab_var_{i}")
            var_id = st.text_input(f"{label} entity ID (campaign/adset/ad)", key=f"ab_var_id_{i}")
        variants.append({
            "label": label,
            "description": var_desc,
            "entity_id": var_id,
        })

    st.markdown("### Test Preview")
    st.json({
        "name": test_name,
        "type": test_type,
        "primary_metric": primary_metric,
        "variants": variants,
        "duration_days": test_duration,
        "confidence": confidence_level,
    })

    if st.button("Create Test", type="primary", use_container_width=True, key="ab_create"):
        if not test_name:
            st.error("Test name is required.")
        elif not all(v["entity_id"] for v in variants):
            st.error("All variants must have entity IDs.")
        else:
            test = {
                "id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": test_name,
                "hypothesis": test_hypothesis,
                "type": test_type,
                "primary_metric": primary_metric,
                "confidence_level": confidence_level,
                "duration_days": test_duration,
                "traffic_split": traffic_split,
                "variants": variants,
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "winner": None,
            }
            tests = load_tests()
            tests.append(test)
            save_tests(tests)
            st.success(f"Test '{test_name}' created and started!")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: MONITOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_monitor:
    st.markdown('<div class="section-title">Running Tests</div>', unsafe_allow_html=True)

    tests = load_tests()
    running = [t for t in tests if t.get("status") == "running"]

    if running:
        for test in running:
            with st.expander(f"📊 {test['name']} — {test['type']}", expanded=True):
                st.markdown(f"**Hypothesis:** {test.get('hypothesis', 'N/A')}")
                st.markdown(f"**Primary Metric:** {test['primary_metric']}")
                st.markdown(f"**Started:** {test['created_at'][:10]}")
                st.markdown(f"**Duration:** {test['duration_days']} days")

                st.markdown("### Variant Performance")
                for var in test.get("variants", []):
                    eid = var.get("entity_id", "")
                    st.markdown(f"**{var['label']}** ({var.get('description', '')}) — ID: `{eid}`")

                if st.button(f"Fetch Live Data", key=f"mon_{test['id']}"):
                    try:
                        from src.extractor import MetaAdsExtractor
                        ext = MetaAdsExtractor(
                            st.session_state.access_token,
                            st.session_state.ad_account_id,
                        )

                        results = []
                        for var in test.get("variants", []):
                            eid = var.get("entity_id", "")
                            end_dt = datetime.now()
                            start_dt = end_dt - timedelta(days=int(test['duration_days']))
                            df = ext.fetch_insights(
                                level="campaign", breakdown_key="none",
                                start_date=start_dt.strftime("%Y-%m-%d"),
                                end_date=end_dt.strftime("%Y-%m-%d"),
                                campaign_ids=[eid],
                            )
                            if not df.empty:
                                spend = safe_float(df["spend"].sum())
                                imps = safe_float(df["impressions"].sum())
                                clicks = safe_float(df["clicks"].sum())
                                results.append({
                                    "Variant": var["label"],
                                    "Spend": format_currency(spend),
                                    "Impressions": int(imps),
                                    "Clicks": int(clicks),
                                    "CTR %": round(safe_divide(clicks, imps) * 100, 3),
                                    "CPC": round(safe_divide(spend, clicks), 2),
                                })

                        if results:
                            st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

                            # Statistical significance
                            if len(results) >= 2:
                                r0, r1 = results[0], results[1]
                                p1 = r0["CTR %"] / 100
                                p2 = r1["CTR %"] / 100
                                n1 = r0["Impressions"]
                                n2 = r1["Impressions"]

                                z_score, p_value = z_test_proportions(p1, n1, p2, n2)

                                conf = 0.95 if test["confidence_level"] == "95%" else (0.99 if test["confidence_level"] == "99%" else 0.90)
                                is_significant = p_value < (1 - conf)

                                st.markdown(f"**Z-Score:** {z_score:.3f} | **P-Value:** {p_value:.4f}")

                                if is_significant:
                                    winner = results[0]["Variant"] if p1 > p2 else results[1]["Variant"]
                                    st.markdown(f'<div class="winner"><b>Winner: {winner}</b><br>'
                                                f'Statistically significant at {test["confidence_level"]} confidence</div>',
                                                unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="inconclusive"><b>Inconclusive</b><br>'
                                                f'Not yet statistically significant (p={p_value:.4f})</div>',
                                                unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Failed to fetch data: {e}")

                col_mt1, col_mt2 = st.columns(2)
                with col_mt1:
                    if st.button(f"Declare Winner", key=f"win_{test['id']}"):
                        test["status"] = "completed"
                        save_tests(tests)
                        st.success("Test marked as completed!")
                with col_mt2:
                    if st.button(f"Stop Test", key=f"stop_{test['id']}"):
                        test["status"] = "stopped"
                        save_tests(tests)
                        st.warning("Test stopped.")
    else:
        st.info("No running tests. Set up a new test in the 'Setup Test' tab.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: RESULTS & ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_results:
    st.markdown('<div class="section-title">Test Results & Analysis</div>', unsafe_allow_html=True)

    st.markdown("""
    Enter your variant data manually to calculate statistical significance.
    Use this for quick analysis of any A/B test data.
    """)

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("### Control (A)")
        a_visitors = st.number_input("Impressions / Visitors", min_value=0, value=10000, key="res_a_n")
        a_conversions = st.number_input("Clicks / Conversions", min_value=0, value=200, key="res_a_conv")
    with col_r2:
        st.markdown("### Variant (B)")
        b_visitors = st.number_input("Impressions / Visitors", min_value=0, value=10000, key="res_b_n")
        b_conversions = st.number_input("Clicks / Conversions", min_value=0, value=250, key="res_b_conv")

    if st.button("Analyze", type="primary", use_container_width=True, key="res_analyze"):
        rate_a = safe_divide(a_conversions, a_visitors)
        rate_b = safe_divide(b_conversions, b_visitors)

        z_score, p_value = z_test_proportions(rate_a, a_visitors, rate_b, b_visitors)
        lift = safe_divide(rate_b - rate_a, rate_a) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Control Rate", format_percentage(rate_a * 100))
        c2.metric("Variant Rate", format_percentage(rate_b * 100))
        c3.metric("Lift", f"{lift:+.2f}%")
        c4.metric("P-Value", f"{p_value:.4f}")

        for conf_name, conf_val in [("90%", 0.10), ("95%", 0.05), ("99%", 0.01)]:
            if p_value < conf_val:
                winner = "Variant B" if rate_b > rate_a else "Control A"
                st.markdown(f'<div class="winner"><b>{conf_name} Confidence: {winner} wins!</b><br>'
                            f'Lift: {lift:+.2f}% | P-value: {p_value:.4f}</div>',
                            unsafe_allow_html=True)
                break
        else:
            st.markdown(f'<div class="inconclusive"><b>Not Significant</b><br>'
                        f'Need more data. P-value: {p_value:.4f}</div>',
                        unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: SAMPLE SIZE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════

with tab_calc:
    st.markdown('<div class="section-title">Sample Size Calculator</div>', unsafe_allow_html=True)

    st.markdown("Calculate how many impressions/visitors you need per variant to detect a given effect.")

    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        baseline_rate = st.number_input(
            "Baseline conversion rate (%)", min_value=0.01, value=2.0, step=0.1, key="calc_baseline",
        )
        mde = st.number_input(
            "Minimum detectable effect (%)", min_value=1.0, value=20.0, step=1.0,
            help="e.g. 20% means detecting a change from 2.0% to 2.4%",
            key="calc_mde",
        )
    with col_calc2:
        calc_confidence = st.selectbox("Confidence Level", ["90%", "95%", "99%"], index=1, key="calc_conf")
        calc_power = st.selectbox("Statistical Power", ["80%", "90%"], index=0, key="calc_power")

    if st.button("Calculate", type="primary", key="calc_go"):
        alpha_map = {"90%": 0.10, "95%": 0.05, "99%": 0.01}
        power_map = {"80%": 0.80, "90%": 0.90}
        alpha_val = alpha_map.get(calc_confidence, 0.05)
        power_val = power_map.get(calc_power, 0.80)
        n = calculate_sample_size(baseline_rate / 100, mde / 100, alpha=alpha_val, power=power_val)
        total = n * 2
        st.metric("Required Sample Size (per variant)", f"{n:,}")
        st.metric("Total Sample Size (both variants)", f"{total:,}")

        # Estimate test duration
        daily_traffic = st.number_input("Daily traffic (impressions/visitors)", min_value=100, value=5000, key="calc_traffic")
        days = math.ceil(total / daily_traffic) if daily_traffic else 0
        st.metric("Estimated Test Duration", f"{days} days")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: TEST HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_history:
    st.markdown('<div class="section-title">Test History</div>', unsafe_allow_html=True)

    tests = load_tests()
    if tests:
        rows = []
        for t in tests:
            rows.append({
                "Name": t.get("name", ""),
                "Type": t.get("type", ""),
                "Status": t.get("status", ""),
                "Primary Metric": t.get("primary_metric", ""),
                "Variants": len(t.get("variants", [])),
                "Duration": f"{t.get('duration_days', 0)}d",
                "Created": t.get("created_at", "")[:10],
                "Winner": t.get("winner", "-"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Export
        if st.button("Export Test History", key="hist_export"):
            st.download_button(
                "Download JSON",
                data=json.dumps(tests, indent=2, default=str),
                file_name="ab_test_history.json",
                mime="application/json",
            )
    else:
        st.info("No tests in history.")
