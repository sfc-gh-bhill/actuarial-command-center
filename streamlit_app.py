# ==============================================================================
# ACTUARIAL COMMAND CENTER — HOME / MISSION CONTROL
# Futuristic command center with proactive alerts, quick actions, and nav blade
# ==============================================================================

import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="Actuarial Command Center",
    page_icon="\u2744",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Actuarial Command Center\nPowered by Snowflake AI Data Cloud"
    }
)

from utils.styles import apply_styles, render_header, render_metric_card
from utils.actions import (render_nav_blade, render_audience_toggle, is_technical_mode,
                           render_proactive_alert, render_action_bar, render_connection_status,
                           render_code_block, render_email_composer)
from utils.data_cache import get_connection

apply_styles()

# ------------------------------------------------------------------------------
# SNOWFLAKE SESSION
# ------------------------------------------------------------------------------
session, session_available = get_connection()

if "session" not in st.session_state:
    st.session_state.session = session

# ------------------------------------------------------------------------------
# SIDEBAR — NAV BLADE
# ------------------------------------------------------------------------------
with st.sidebar:
    render_nav_blade(current_page_index=0)
    render_connection_status(session_available)

# ------------------------------------------------------------------------------
# HERO SECTION
# ------------------------------------------------------------------------------
st.markdown("""
<div style="background: linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%);
            padding: 2.5rem; border-radius: 16px; margin-bottom: 1.5rem;
            border: 1px solid rgba(41, 181, 232, 0.3);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            position: relative; overflow: hidden;">
    <div style="position:absolute;top:0;left:0;right:0;height:3px;
                background:linear-gradient(90deg,#29B5E8,#00D4AA,#667eea,#29B5E8);
                background-size:300% 100%;
                animation:shimmer 3s ease-in-out infinite;"></div>
    <style>@keyframes shimmer{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}</style>
    <div style="text-align: center;">
        <h1 style="background: linear-gradient(135deg, #29B5E8 0%, #00D4AA 50%, #29B5E8 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 2.8rem; margin: 0; font-weight: 700;">
            Actuarial Command Center
        </h1>
        <p style="color: #8892b0; font-size: 1.2rem; margin-top: 0.75rem; margin-bottom: 0;">
            Real-time margin surveillance, risk adjustment, and contract analytics
        </p>
        <p style="color: #64ffda; font-size: 0.9rem; margin-top: 0.5rem;">
            Governed by Snowflake Semantic Views &middot; Powered by Cortex AI
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# AUDIENCE TOGGLE
# ------------------------------------------------------------------------------
technical = is_technical_mode()

# ------------------------------------------------------------------------------
# PROACTIVE ALERTS
# ------------------------------------------------------------------------------
render_proactive_alert(
    "Behavioral Health Cost Spike Detected — Texas",
    "BH unit cost trending +8.0% above pricing assumptions. Annual exposure: ~$2.8M. "
    "Cortex ML flagged this anomaly across 6 consecutive months.",
    actions=[
        {"label": "View Anomaly Details", "page_link": "pages/6_Trend_Surveillance.py"},
        {"label": "Run Repricing Scenario", "page_link": "pages/5_Contract_Repricing.py"},
        {"label": "Ask the Agent", "page_link": "pages/7_Intelligence_Agent.py"},
    ],
    severity="critical",
    key_prefix="home_alert"
)

# ------------------------------------------------------------------------------
# MISSION CONTROL KPIs
# ------------------------------------------------------------------------------
st.markdown("### Mission Control")

@st.cache_data(ttl=300)
def load_home_kpis(_session_available):
    if _session_available:
        from utils.data_cache import get_session
        return get_session().sql("""
            SELECT SUM(total_paid) AS paid, SUM(total_premium) AS premium,
                   SUM(claim_count) AS claims, AVG(cost_pmpm) AS pmpm
            FROM GOLD.FINANCIAL_SUMMARY
            WHERE metric_month >= DATEADD('month', -3, CURRENT_DATE())
        """).to_pandas()
    else:
        return pd.DataFrame({
            'PAID': [245_000_000], 'PREMIUM': [278_000_000],
            'CLAIMS': [156_000], 'PMPM': [442.0]
        })

kpis = load_home_kpis(session_available)
if not kpis.empty:
    row = kpis.iloc[0]
    paid = float(row.get('PAID', 245e6))
    premium = float(row.get('PREMIUM', 278e6))
    mlr = paid / premium if premium > 0 else 0
    margin = 1 - mlr

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-tile">
            <p class="metric-label">MEDICAL LOSS RATIO</p>
            <p class="metric-value">{mlr:.1%}</p>
            <p class="metric-delta-{'positive' if mlr < 0.90 else 'negative'}">
                3-month rolling | {'On target' if mlr < 0.90 else 'Above threshold'}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-tile">
            <p class="metric-label">OPERATING MARGIN</p>
            <p class="metric-value">{margin:.1%}</p>
            <p class="metric-delta-{'positive' if margin > 0.10 else 'negative'}">
                {'Healthy' if margin > 0.10 else 'Below 10% target'}</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        claims = int(row.get('CLAIMS', 156000))
        st.markdown(f"""
        <div class="kpi-tile">
            <p class="metric-label">CLAIMS PROCESSED</p>
            <p class="metric-value">{claims:,}</p>
            <p style="color:#8892b0;font-size:0.8rem;">Last 3 months</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        pmpm = float(row.get('PMPM', 442))
        st.markdown(f"""
        <div class="kpi-tile">
            <p class="metric-label">AVG COST PMPM</p>
            <p class="metric-value">${pmpm:,.0f}</p>
            <p style="color:#8892b0;font-size:0.8rem;">Per Member Per Month</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# QUICK ACTIONS
# ------------------------------------------------------------------------------
st.markdown("### Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown('<div class="tile-action">', unsafe_allow_html=True)
        if st.button("✉  Draft CFO Briefing\n\nCortex AI drafts an executive email with current MLR, margin status, anomaly summary, and recommended actions.",
                      key="home_draft_cfo", use_container_width=True):
            st.session_state.show_cfo_email = True
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="tile-nav">', unsafe_allow_html=True)
        st.page_link("pages/4_IBNR_Reserves.py",
                      label="📋  Generate Audit Package\n\nCompile a compliance-ready package with MLR calculations, IBNR methodology, and data governance attestation.",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown('<div class="tile-nav">', unsafe_allow_html=True)
        st.page_link("pages/5_Contract_Repricing.py",
                      label="⚙  Run Repricing Scenario\n\nModel contract rate adjustments and see instant margin impact. Start with the TX BH anomaly (-200 bps).",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# CFO Email Composer
if st.session_state.get("show_cfo_email", False):
    render_email_composer(
        subject=f"Actuarial Command Center — Weekly Briefing ({pd.Timestamp.today().strftime('%b %d, %Y')})",
        body_markdown=f"""Health Plan Co.l Loss Ratio (3-mo rolling): {mlr:.1%}
Operating Margin: {margin:.1%}
Claims Processed (90 days): {claims:,}

Active Alert: Texas Behavioral Health unit cost trending +8.0% above pricing assumptions.
Annual exposure estimated at $2.8M. Root cause: Texas Regional Health System exercised
Section 7 price adjustment clause (4.2% rate increase effective July 1).

Recommended Actions:
1. Review Contract Repricing scenario (200 bps reduction)
2. Schedule provider network review for Q3
3. Evaluate MFN clause applicability for rate parity""",
        insights=[
            {"label": "Health Plan Co.l Loss Ratio", "value": f"{mlr:.1%}", "checked": True},
            {"label": "Operating Margin", "value": f"{margin:.1%}", "checked": True},
            {"label": "Claims Processed", "value": f"{claims:,}", "checked": True},
            {"label": "Avg Cost PMPM", "value": f"${pmpm:,.0f}", "checked": True},
            {"label": "TX BH Alert", "value": "+8.0% above pricing", "checked": True},
            {"label": "Annual Exposure", "value": "$2.8M", "checked": False},
        ],
        page_context="this week's actuarial briefing from the Actuarial Command Center",
        key_prefix="home_cfo"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# THE PROBLEM (Context)
# ------------------------------------------------------------------------------
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.6); padding: 1.5rem; border-radius: 12px;
            margin-bottom: 2rem; border-left: 4px solid #f59e0b;">
    <h3 style="color: #f59e0b; margin: 0 0 0.5rem 0; border: none;">The Problem</h3>
    <p style="color: #ccd6f6; margin: 0; line-height: 1.6;">
        A Chief Actuary needs <strong style="color: #fff;">one reconcilable truth</strong> across
        dashboards, AI agents, and FP&amp;A systems. If the AI chat and the visual dashboard show different
        MLR figures, credibility is lost immediately. This platform solves that with a
        <strong style="color: #64ffda;">governed Semantic View</strong> as the single source of truth.
    </p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ARCHITECTURE (Technical View)
# ------------------------------------------------------------------------------
if technical:
    st.markdown("### Architecture Overview")

    st.markdown("""
    <style>
    .pipeline-container {
        display: flex; justify-content: space-between; align-items: stretch;
        gap: 0.5rem; margin: 1.5rem 0; flex-wrap: nowrap;
    }
    .pipeline-card {
        flex: 1; min-width: 0;
        background: linear-gradient(180deg, #112240 0%, #0a192f 100%);
        border-radius: 12px; padding: 1.25rem 1rem; text-align: center;
        border: 1px solid rgba(41, 181, 232, 0.2);
        transition: all 0.3s ease;
    }
    .pipeline-card:hover {
        transform: translateY(-4px);
        border-color: rgba(41, 181, 232, 0.6);
        box-shadow: 0 8px 25px rgba(41, 181, 232, 0.2);
    }
    .pipeline-icon { font-size: 2.2rem; margin-bottom: 0.5rem; }
    .pipeline-title {
        color: #29B5E8; font-weight: 700; font-size: 0.85rem;
        margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px;
    }
    .pipeline-desc { color: #8892b0; font-size: 0.75rem; line-height: 1.4; }
    .pipeline-arrow { display: flex; align-items: center; color: #64ffda; font-size: 1.5rem; padding: 0 0.25rem; }
    .card-data { border-top: 3px solid #3b82f6; }
    .card-truth { border-top: 3px solid #8b5cf6; }
    .card-ai { border-top: 3px solid #10b981; }
    .card-viz { border-top: 3px solid #f59e0b; }
    .card-agent { border-top: 3px solid #ef4444; }
    </style>

    <div class="pipeline-container">
        <div class="pipeline-card card-data">
            <div class="pipeline-icon">&#9783;</div>
            <div class="pipeline-title">Foundation</div>
            <div class="pipeline-desc">Dynamic Tables process raw claims into Silver/Gold models</div>
        </div>
        <div class="pipeline-arrow">&rarr;</div>
        <div class="pipeline-card card-truth">
            <div class="pipeline-icon">&#10052;</div>
            <div class="pipeline-title">Truth Layer</div>
            <div class="pipeline-desc">Semantic View defines MLR, IBNR, margin as governed metrics</div>
        </div>
        <div class="pipeline-arrow">&rarr;</div>
        <div class="pipeline-card card-ai">
            <div class="pipeline-icon">&#9881;</div>
            <div class="pipeline-title">AI Engine</div>
            <div class="pipeline-desc">Cortex ML anomaly detection and IBNR forecasting</div>
        </div>
        <div class="pipeline-arrow">&rarr;</div>
        <div class="pipeline-card card-viz">
            <div class="pipeline-icon">&#9783;</div>
            <div class="pipeline-title">Dashboard</div>
            <div class="pipeline-desc">Streamlit Command Center with real-time scenario modeling</div>
        </div>
        <div class="pipeline-arrow">&rarr;</div>
        <div class="pipeline-card card-agent">
            <div class="pipeline-icon">&#128172;</div>
            <div class="pipeline-title">Intelligence</div>
            <div class="pipeline-desc">Cortex Agent answers CAO questions with governed data + contracts</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_code_block("""-- Semantic View: Single Source of Truth
SELECT metric_month, line_of_business, member_state,
       SUM(total_paid) / SUM(total_premium) AS medical_loss_ratio,
       1 - (SUM(total_paid) / SUM(total_premium)) AS operating_margin
FROM GOLD.ACTUARIAL_FINANCIAL_TRUTH
GROUP BY 1, 2, 3;""", "Governed MLR Calculation (Semantic View)")

st.divider()

# ------------------------------------------------------------------------------
# DEMO WORKFLOW
# ------------------------------------------------------------------------------
st.markdown("### Demo Workflow")

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown('<div class="tile-step tile-step-1">', unsafe_allow_html=True)
        st.page_link("pages/0_Executive_Summary.py",
                      label="STEP 1 — The High-Level Anchor\n\nOpen the Executive Summary. Show current MLR and Year-End Margin Forecast. Point out the data is driven by a governed Semantic View.",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="tile-step tile-step-2">', unsafe_allow_html=True)
        st.page_link("pages/6_Trend_Surveillance.py",
                      label="STEP 2 — The Early Warning\n\nShow Cortex ML anomaly alert: \"Behavioral Health unit cost trending 8% above pricing assumptions in Texas.\"",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    with st.container():
        st.markdown('<div class="tile-step tile-step-3">', unsafe_allow_html=True)
        st.page_link("pages/5_Contract_Repricing.py",
                      label="STEP 3 — The \"Wow\" Moment\n\nNavigate to Contract Repricing. Use the slider: \"What if we renegotiate the Texas hospital system contract down by 200 bps?\"",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown('<div class="tile-step tile-step-4">', unsafe_allow_html=True)
        st.page_link("pages/7_Intelligence_Agent.py",
                      label="STEP 4 — The CFO Bridge\n\nOpen the Intelligence Agent. Ask: \"Why is our Texas margin missing the target, and what is our exposure?\"",
                      use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
