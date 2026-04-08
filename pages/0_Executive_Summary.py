# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# PAGE 0: EXECUTIVE SUMMARY
# High-level anchor: MLR, margin, anomaly alerts across all LOBs
# Actions: Email summary, export LOB breakdown, view governance SQL
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Executive Summary | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card, render_alert_card, render_status_badge
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_proactive_alert,
                           render_connection_status)

apply_styles()

# ------------------------------------------------------------------------------
# SNOWFLAKE SESSION
# ------------------------------------------------------------------------------
from utils.data_cache import get_connection, load_financial_summary, load_anomaly_alerts, compute_lob_summary, compute_monthly_mlr, compute_state_summary, df_hash

session, session_available = get_connection()

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    render_nav_blade(current_page_index=1)
    render_connection_status(session_available)

# ------------------------------------------------------------------------------
# DATA LOADING (centralized cache)
# ------------------------------------------------------------------------------
df = load_financial_summary(session_available)
alerts_df = load_anomaly_alerts(session_available)

# ------------------------------------------------------------------------------
# HEADER + NAV
# ------------------------------------------------------------------------------
render_page_header_nav(current_page_index=1)
render_header("Executive Summary", "Enterprise-wide financial health at a glance")

# Audience toggle
technical = is_technical_mode()

# Sourcing badge
st.markdown("""
<div style="background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4);
            padding: 0.6rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; display: inline-block;">
    <span style="color: #8b5cf6; font-weight: 600; font-size: 0.8rem;">
        DATA SOURCE: Semantic View ACTUARIAL_FINANCIAL_TRUTH
    </span>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TOP-LINE KPIs
# ------------------------------------------------------------------------------
if not df.empty:
    latest_months = sorted(df['METRIC_MONTH'].unique())[-3:]
    recent = df[df['METRIC_MONTH'].isin(latest_months)]

    total_paid = recent['TOTAL_PAID'].sum()
    total_premium = recent['TOTAL_PREMIUM'].sum()
    overall_mlr = total_paid / total_premium if total_premium > 0 else 0
    overall_margin = 1 - overall_mlr
    total_claims = recent['CLAIM_COUNT'].sum()
    avg_pmpm = recent['COST_PMPM'].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card(
            f"{overall_mlr:.1%}", "Health Plan Co.l Loss Ratio",
            "3-month rolling" if overall_mlr < 0.90 else "Above 90% threshold",
            "positive" if overall_mlr < 0.90 else "negative"
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(
            f"{overall_margin:.1%}", "Operating Margin",
            "On target" if overall_margin > 0.10 else "Below target",
            "positive" if overall_margin > 0.10 else "negative"
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(
            f"${avg_pmpm:,.0f}", "Avg Cost PMPM", "Per Member Per Month"
        ), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card(
            f"{total_claims:,.0f}", "Total Claims", "Last 3 months"
        ), unsafe_allow_html=True)

    # --- ACTION BAR ---
    actions = render_action_bar([
        {"label": "Email Summary", "icon": "\u2709", "callback_key": "email_summary"},
        {"label": "Export LOB Data", "icon": "\u2B07", "callback_key": "export_lob"},
        {"label": "Navigate to Repricing", "icon": "\u2696", "callback_key": "goto_reprice"},
    ], key_prefix="exec_actions")

    if actions.get("email_summary"):
        render_email_composer(
            subject=f"Executive Summary — MLR {overall_mlr:.1%} | Margin {overall_margin:.1%}",
            body_markdown=f"""Executive Summary (3-month rolling):

- Health Plan Co.l Loss Ratio: {overall_mlr:.1%}
- Operating Margin: {overall_margin:.1%}
- Avg Cost PMPM: ${avg_pmpm:,.0f}
- Total Claims: {total_claims:,}

Active Alert: TX Behavioral Health +8.0% above pricing assumptions.""",
            insights=[
                {"label": "Health Plan Co.l Loss Ratio", "value": f"{overall_mlr:.1%}", "checked": True},
                {"label": "Operating Margin", "value": f"{overall_margin:.1%}", "checked": True},
                {"label": "Avg Cost PMPM", "value": f"${avg_pmpm:,.0f}", "checked": True},
                {"label": "Total Claims", "value": f"{total_claims:,}", "checked": False},
                {"label": "TX BH Alert", "value": "+8.0% above pricing", "checked": True},
            ],
            page_context="the latest Executive Summary from the Actuarial Command Center",
            key_prefix="exec_email"
        )

    if actions.get("goto_reprice"):
        st.switch_page("pages/5_Contract_Repricing.py")

    if actions.get("export_lob"):
        lob_export = compute_lob_summary(df_hash(df), df)
        render_export_buttons(lob_export, "LOB_Summary", key_prefix="exec_lob_topbar")

else:
    st.warning("No financial data available.")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ANOMALY ALERTS
# ------------------------------------------------------------------------------
st.markdown("### Active Anomaly Alerts")

if not alerts_df.empty:
    for _, alert in alerts_df.head(5).iterrows():
        severity = "critical" if abs(alert.get('PCT_DEVIATION', 0)) > 7 else "warning"
        state = alert.get('MEMBER_STATE', 'N/A')
        cat = alert.get('SERVICE_CATEGORY', 'N/A')
        dev = alert.get('PCT_DEVIATION', 0)
        obs = alert.get('OBSERVED_VALUE', 0)
        exp = alert.get('EXPECTED_VALUE', 0)

        render_proactive_alert(
            f"{state} {cat.replace('_', ' ').title()} — {dev:+.1f}% Deviation",
            f"Observed: ${obs:,.2f} | Expected: ${exp:,.2f} | Type: {alert.get('ANOMALY_TYPE', 'N/A')}",
            actions=[
                {"label": "View Details", "page_link": "pages/6_Trend_Surveillance.py"},
            ],
            severity=severity,
            key_prefix=f"exec_alert_{_}"
        )
else:
    st.markdown(render_alert_card(
        "No Active Anomalies", "All cost trends are within expected bounds.", "success"
    ), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MLR BY LINE OF BUSINESS
# ------------------------------------------------------------------------------
st.markdown("### MLR by Line of Business")

if not df.empty:
    lob_summary = compute_lob_summary(df_hash(df), df)

    cols = st.columns(len(lob_summary))
    for i, (_, row) in enumerate(lob_summary.iterrows()):
        with cols[i]:
            mlr_val = row['MLR']
            status = "at-risk" if mlr_val > 0.95 else "warning" if mlr_val > 0.90 else "on-target"
            badge = render_status_badge(status, status.replace('-', ' ').upper())
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <p style="color: #8892b0; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">
                    {row['LINE_OF_BUSINESS'].replace('_', ' ')}
                </p>
                <p class="metric-value" style="font-size: 1.8rem;">{mlr_val:.1%}</p>
                <p style="color: #8892b0; font-size: 0.8rem; margin: 0.25rem 0;">
                    Margin: {row['MARGIN']:.1%}
                </p>
                {badge}
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# MLR TREND CHART
# ------------------------------------------------------------------------------
st.markdown("### MLR Trend (Rolling 12 Months)")

if not df.empty:
    monthly_mlr = compute_monthly_mlr(df_hash(df), df)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_mlr['METRIC_MONTH'], y=monthly_mlr['MLR'],
        mode='lines+markers', name='MLR',
        line=dict(color='#29B5E8', width=3),
        marker=dict(size=8, color='#29B5E8')
    ))
    fig.add_hline(y=0.85, line_dash="dash", line_color="#FFB74D",
                  annotation_text="85% Large Group", annotation_position="top right")
    fig.add_hline(y=0.80, line_dash="dash", line_color="#4ECDC4",
                  annotation_text="80% Ind/Small", annotation_position="bottom right")

    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_tickformat='.0%', yaxis_title='Health Plan Co.l Loss Ratio', xaxis_title='',
        height=400, margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------------------
# MARGIN BY STATE
# ------------------------------------------------------------------------------
st.markdown("### Margin by State")

if not df.empty:
    state_summary = compute_state_summary(df_hash(df), df)

    fig2 = go.Figure()
    colors = ['#FF6B6B' if m < 0.05 else '#FFB74D' if m < 0.10 else '#4ECDC4' for m in state_summary['MARGIN']]
    fig2.add_trace(go.Bar(
        x=state_summary['MEMBER_STATE'], y=state_summary['MARGIN'],
        marker_color=colors,
        text=[f"{m:.1%}" for m in state_summary['MARGIN']],
        textposition='outside'
    ))
    fig2.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_tickformat='.0%', yaxis_title='Operating Margin', xaxis_title='State',
        height=350, margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------------------
# TECHNICAL: SQL GOVERNANCE
# ------------------------------------------------------------------------------
if technical:
    render_code_block("""-- MLR Calculation (governed by Semantic View)
SELECT metric_month, line_of_business, member_state,
       SUM(total_paid) / SUM(total_premium) AS medical_loss_ratio,
       1 - SUM(total_paid) / SUM(total_premium) AS operating_margin
FROM GOLD.FINANCIAL_SUMMARY  -- Powered by ACTUARIAL_FINANCIAL_TRUTH
GROUP BY 1, 2, 3
ORDER BY metric_month DESC;""", "Semantic View: MLR Governance SQL")

    render_code_block("""-- ACA MLR Rebate Threshold Check
SELECT line_of_business,
       SUM(total_paid) / SUM(total_premium) AS mlr,
       CASE WHEN line_of_business LIKE '%LARGE%' THEN 0.85 ELSE 0.80 END AS aca_min,
       IFF(SUM(total_paid) / SUM(total_premium) < aca_min, 'REBATE_RISK', 'COMPLIANT') AS status
FROM GOLD.FINANCIAL_SUMMARY
GROUP BY 1;""", "ACA Rebate Compliance Check")
