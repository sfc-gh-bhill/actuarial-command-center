# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# PAGE 6: TREND SURVEILLANCE
# Cortex ML anomaly detection - surfaces Texas BH cost spike
# Actions: Create alert rule, email trend report, export surveillance data
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Trend Surveillance | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card, render_alert_card, render_status_badge
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_proactive_alert,
                           render_connection_status)

apply_styles()

from utils.data_cache import get_connection, load_anomaly_alerts

session, session_available = get_connection()

# SIDEBAR
with st.sidebar:
    render_nav_blade(current_page_index=7)
    st.divider()
    st.markdown("### Filters")

# DATA
@st.cache_data(ttl=300)
def load_trend_data(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT trend_month, member_state, service_category, line_of_business,
                   claim_count, total_paid, avg_unit_cost, median_unit_cost,
                   p90_unit_cost, p95_unit_cost, unique_members, pmpm_cost
            FROM GOLD.TREND_SURVEILLANCE
            ORDER BY trend_month
        """).to_pandas()
    else:
        np.random.seed(42)
        months = pd.date_range(end=pd.Timestamp.today(), periods=18, freq='MS')
        states = ['TX', 'MN', 'FL', 'CA']
        cats = ['INPATIENT', 'OUTPATIENT_PROFESSIONAL', 'BEHAVIORAL_HEALTH', 'EMERGENCY']
        rows = []
        for m in months:
            for s in states:
                for c in cats:
                    base = {'INPATIENT': 13000, 'OUTPATIENT_PROFESSIONAL': 250,
                            'BEHAVIORAL_HEALTH': 300, 'EMERGENCY': 1200}[c]
                    trend = 1 + np.random.normal(0, 0.03)
                    if s == 'TX' and c == 'BEHAVIORAL_HEALTH' and m >= months[-6]:
                        trend *= 1.08
                    avg_cost = base * trend
                    rows.append({
                        'TREND_MONTH': m, 'MEMBER_STATE': s, 'SERVICE_CATEGORY': c,
                        'LINE_OF_BUSINESS': 'ALL',
                        'CLAIM_COUNT': np.random.randint(500, 5000),
                        'TOTAL_PAID': avg_cost * np.random.randint(500, 5000),
                        'AVG_UNIT_COST': round(avg_cost, 2),
                        'MEDIAN_UNIT_COST': round(avg_cost * 0.85, 2),
                        'P90_UNIT_COST': round(avg_cost * 2.1, 2),
                        'P95_UNIT_COST': round(avg_cost * 3.0, 2),
                        'UNIQUE_MEMBERS': np.random.randint(200, 2000),
                        'PMPM_COST': round(avg_cost * np.random.uniform(0.5, 1.5), 2)
                    })
        return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_cost_forecast(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT trend_month, member_state, service_category,
                   avg_unit_cost, trailing_6mo_avg, mom_pct_change,
                   pricing_trend_assumption, annualized_trend
            FROM ANALYTICS.COST_TREND_FORECAST
            ORDER BY trend_month
        """).to_pandas()
    else:
        return pd.DataFrame()

trend_df = load_trend_data(session_available)
alerts_df = load_anomaly_alerts(session_available)
forecast_df = load_cost_forecast(session_available)

# Sidebar filters
with st.sidebar:
    if not trend_df.empty:
        state_filter = st.selectbox("State", ['ALL'] + sorted(trend_df['MEMBER_STATE'].unique().tolist()))
        cat_filter = st.selectbox("Service Category",
                                   ['ALL'] + sorted(trend_df['SERVICE_CATEGORY'].unique().tolist()))
    render_connection_status(session_available)

# HEADER + NAV
render_page_header_nav(current_page_index=7)
render_header("Trend Surveillance", "Cortex ML anomaly detection and cost trend monitoring")
technical = is_technical_mode()

# ANOMALY ALERTS
st.markdown("### Cortex ML Anomaly Alerts")

if not alerts_df.empty:
    tx_bh = alerts_df[alerts_df['SERVICE_CATEGORY'] == 'BEHAVIORAL_HEALTH']
    if not tx_bh.empty:
        top = tx_bh.iloc[0]
        render_proactive_alert(
            "Behavioral Health Unit Cost Anomaly — Texas",
            f"BH unit cost trending {top['PCT_DEVIATION']:+.1f}% above pricing assumptions. "
            f"Observed: ${top['OBSERVED_VALUE']:,.2f} | Expected: ${top['EXPECTED_VALUE']:,.2f}. "
            f"Contract reference: CPT 90837 negotiated at $177.43 (Texas Regional Health System). "
            f"Provider exercised 4.2% price adjustment clause effective July 1, 2024.",
            actions=[
                {"label": "Run Repricing Scenario", "page_link": "pages/5_Contract_Repricing.py"},
                {"label": "Ask the Agent", "page_link": "pages/7_Intelligence_Agent.py"},
            ],
            severity="critical",
            key_prefix="trend_bh_alert"
        )

    other_alerts = alerts_df[alerts_df['SERVICE_CATEGORY'] != 'BEHAVIORAL_HEALTH'].head(3)
    for idx, alert in other_alerts.iterrows():
        severity = "warning" if abs(alert['PCT_DEVIATION']) > 5 else "info"
        st.markdown(render_alert_card(
            f"{alert['MEMBER_STATE']} {alert['SERVICE_CATEGORY'].replace('_', ' ').title()} — {alert['PCT_DEVIATION']:+.1f}%",
            f"Observed: ${alert['OBSERVED_VALUE']:,.2f} | Expected: ${alert['EXPECTED_VALUE']:,.2f}",
            severity
        ), unsafe_allow_html=True)
else:
    st.markdown(render_alert_card("No Anomalies Detected", "All series within expected bounds.", "success"),
                unsafe_allow_html=True)

# --- ACTION BAR ---
actions = render_action_bar([
    {"label": "Email Trend Report", "icon": "\u2709", "callback_key": "email_trend"},
    {"label": "Export Surveillance Data", "icon": "\u2B07", "callback_key": "export_trend"},
    {"label": "Create Alert Rule", "icon": "\u26A0", "callback_key": "create_rule"},
], key_prefix="trend_actions")

if actions.get("email_trend"):
    render_email_composer(
        subject=f"Trend Surveillance Report — {pd.Timestamp.today().strftime('%B %Y')}",
        body_markdown=f"""Trend Surveillance Report:

Active Anomalies: {len(alerts_df)}

Primary Alert: TX Behavioral Health +8.0% above pricing assumptions
- Observed unit cost: $166.63
- Expected (pricing): $154.29
- Root cause: 4.2% mid-year price adjustment (Section 7 contract clause)
- Annualized exposure: ~$1.46M

Recommended Actions:
1. Review TX BH provider network adequacy
2. Model -200 bps repricing scenario
3. Evaluate MFN clause applicability""",
        insights=[
            {"label": "Active Anomalies", "value": f"{len(alerts_df)}", "checked": True},
            {"label": "Primary Alert", "value": "TX BH +8.0% above pricing", "checked": True},
            {"label": "Observed Unit Cost", "value": "$166.63", "checked": True},
            {"label": "Expected (Pricing)", "value": "$154.29", "checked": False},
            {"label": "Annualized Exposure", "value": "~$1.46M", "checked": True},
        ],
        page_context="the latest Trend Surveillance report from the Actuarial Command Center",
        key_prefix="trend_email"
    )

if actions.get("export_trend"):
    render_export_buttons(trend_df, "Trend_Surveillance", key_prefix="trend_data_export")

if actions.get("create_rule"):
    with st.expander("Configure Alert Rule", expanded=True):
        st.markdown("""
        <div style="background:rgba(41,181,232,0.1);border:1px solid rgba(41,181,232,0.3);
                    padding:0.75rem;border-radius:10px;margin-bottom:0.75rem;">
            <span style="color:#29B5E8;font-size:0.75rem;font-weight:600;">CORTEX ML ALERT CONFIGURATION</span>
        </div>
        """, unsafe_allow_html=True)
        rule_state = st.selectbox("State", ['TX', 'MN', 'FL', 'CA', 'ALL'], key="rule_state")
        rule_cat = st.selectbox("Category", ['BEHAVIORAL_HEALTH', 'INPATIENT', 'EMERGENCY', 'ALL'], key="rule_cat")
        rule_threshold = st.slider("Deviation Threshold (%)", 3, 15, 5, key="rule_thresh")
        if st.button("Save Alert Rule", key="save_rule"):
            st.success(f"Alert rule saved: {rule_state} | {rule_cat} | >{rule_threshold}% deviation. "
                       "In live mode, this would configure a Snowflake Task to monitor and send notifications.")

st.markdown("<br>", unsafe_allow_html=True)

# TREND CHARTS
st.markdown("### Cost Trend by Service Category")

if not trend_df.empty:
    plot_data = trend_df.copy()
    if state_filter != 'ALL':
        plot_data = plot_data[plot_data['MEMBER_STATE'] == state_filter]
    if cat_filter != 'ALL':
        plot_data = plot_data[plot_data['SERVICE_CATEGORY'] == cat_filter]

    monthly_avg = plot_data.groupby(['TREND_MONTH', 'SERVICE_CATEGORY']).agg(
        AVG_COST=('AVG_UNIT_COST', 'mean'),
        P90=('P90_UNIT_COST', 'mean'),
        CLAIMS=('CLAIM_COUNT', 'sum')
    ).reset_index()

    cat_colors = {
        'INPATIENT': '#FF6B6B', 'BEHAVIORAL_HEALTH': '#FFB74D',
        'EMERGENCY': '#f59e0b', 'OUTPATIENT_PROFESSIONAL': '#29B5E8',
        'OUTPATIENT_FACILITY': '#667eea', 'OTHER': '#8892b0'
    }

    fig = go.Figure()
    for cat in monthly_avg['SERVICE_CATEGORY'].unique():
        cat_data = monthly_avg[monthly_avg['SERVICE_CATEGORY'] == cat].sort_values('TREND_MONTH')
        fig.add_trace(go.Scatter(
            x=cat_data['TREND_MONTH'], y=cat_data['AVG_COST'],
            name=cat.replace('_', ' ').title(), mode='lines+markers',
            line=dict(color=cat_colors.get(cat, '#8892b0'), width=2),
            marker=dict(size=5)
        ))

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title='Avg Unit Cost ($)', height=450,
        margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # TX BH DEEP DIVE
    st.markdown("### Texas Behavioral Health Deep Dive")

    tx_bh_data = trend_df[
        (trend_df['MEMBER_STATE'] == 'TX') & (trend_df['SERVICE_CATEGORY'] == 'BEHAVIORAL_HEALTH')
    ].sort_values('TREND_MONTH')

    if not tx_bh_data.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=tx_bh_data['TREND_MONTH'], y=tx_bh_data['AVG_UNIT_COST'],
                mode='lines+markers', name='TX BH Avg Cost',
                line=dict(color='#FFB74D', width=3), marker=dict(size=8)
            ))
            fig2.add_hline(y=154.29, line_dash="dash", line_color="#29B5E8",
                          annotation_text="CPT 90837 Baseline: $154.29")
            fig2.add_hline(y=177.43, line_dash="dot", line_color="#FF6B6B",
                          annotation_text="Contract Rate: $177.43")

            six_months_ago = tx_bh_data['TREND_MONTH'].max() - pd.Timedelta(days=180)
            fig2.add_vrect(x0=six_months_ago, x1=tx_bh_data['TREND_MONTH'].max(),
                          fillcolor="rgba(255,107,107,0.1)", line_width=0,
                          annotation_text="Anomaly Period", annotation_position="top left")

            fig2.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis_title='Avg Unit Cost ($)', height=400,
                margin=dict(l=40, r=20, t=20, b=40)
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.markdown(render_alert_card(
                "Root Cause Analysis",
                "The 4.2% mid-year price adjustment in the TX Regional Health System contract "
                "(effective July 1, 2024) directly correlates with the observed 8% BH cost spike. "
                "The adjustment was triggered by 8.1% labor cost increases at the Arlington behavioral "
                "health facility. Contract section 7 (Price Adjustment Clause) permitted the increase.",
                "warning"
            ), unsafe_allow_html=True)

            st.markdown(render_alert_card(
                "Recommended Action",
                "Navigate to Contract Repricing (page 6) to model the impact of renegotiating "
                "the TX hospital system contract down by 200 basis points.",
                "info"
            ), unsafe_allow_html=True)

# Technical SQL
if technical:
    render_code_block("""-- Cortex ML Anomaly Detection
SELECT *
FROM TABLE(SNOWFLAKE.ML.ANOMALY_DETECTION(
    INPUT_DATA => TABLE(
        SELECT trend_month AS ts, avg_unit_cost AS y, series_id
        FROM ANALYTICS.TREND_TIMESERIES
    ),
    TIMESTAMP_COLNAME => 'ts',
    TARGET_COLNAME => 'y',
    SERIES_COLNAME => 'series_id'
));""", "Cortex ML Anomaly Detection")

# Pricing vs Actual
if not forecast_df.empty:
    st.markdown("### Observed vs Pricing Assumptions")
    st.dataframe(forecast_df.sort_values('TREND_MONTH', ascending=False).head(50),
                 use_container_width=True, hide_index=True)
