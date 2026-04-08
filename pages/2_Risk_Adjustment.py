# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# PAGE 2: RISK ADJUSTMENT
# CMS-HCC v28 RAF scoring, revenue exposure, constrained coefficients
# Actions: RAF audit report, export coefficients, flag coding gaps
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Risk Adjustment | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_audit_package,
                           render_connection_status)

apply_styles()

from utils.data_cache import get_connection

session, session_available = get_connection()

# SIDEBAR
with st.sidebar:
    render_nav_blade(current_page_index=3)
    st.divider()
    st.markdown("### Filters")

# DATA
@st.cache_data(ttl=300)
def load_risk_scores(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT line_of_business, member_state, age_band, primary_hcc,
                   member_count, avg_raf_score, median_raf_score,
                   min_raf_score, max_raf_score, avg_premium_pmpm, avg_risk_adjusted_pmpm
            FROM GOLD.RISK_SCORE_SUMMARY
        """).to_pandas()
    else:
        np.random.seed(42)
        lobs = ['ACA_INDIVIDUAL', 'ACA_SMALL_GROUP', 'MEDICARE_ADVANTAGE', 'MEDICAID_MANAGED']
        states = ['TX', 'MN', 'FL', 'CA']
        bands = ['PEDIATRIC', 'ADULT_YOUNG', 'ADULT_MATURE', 'SENIOR']
        hccs = [None, 'HCC 37', 'HCC 225', 'HCC 18', 'HCC 112']
        rows = []
        for lob in lobs:
            for s in states:
                for b in bands:
                    for h in hccs:
                        base = 0.8 if lob == 'MEDICARE_ADVANTAGE' else 0.6 if lob == 'MEDICAID_MANAGED' else 0.5
                        raf = base + np.random.uniform(0, 1.0)
                        rows.append({
                            'LINE_OF_BUSINESS': lob, 'MEMBER_STATE': s, 'AGE_BAND': b,
                            'PRIMARY_HCC': h, 'MEMBER_COUNT': np.random.randint(10, 500),
                            'AVG_RAF_SCORE': round(raf, 3), 'MEDIAN_RAF_SCORE': round(raf - 0.05, 3),
                            'MIN_RAF_SCORE': round(max(0.1, raf - 0.4), 3),
                            'MAX_RAF_SCORE': round(raf + 0.6, 3),
                            'AVG_PREMIUM_PMPM': round(np.random.uniform(350, 1100), 2),
                            'AVG_RISK_ADJUSTED_PMPM': round(np.random.uniform(400, 1500), 2)
                        })
        return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_hcc_reference(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("SELECT * FROM GOLD.HCC_REFERENCE").to_pandas()
    else:
        return pd.DataFrame({
            'HCC_CODE': ['HCC 18', 'HCC 19', 'HCC 36', 'HCC 37', 'HCC 38', 'HCC 48',
                         'HCC 112', 'HCC 134', 'HCC 224', 'HCC 225', 'HCC 226', 'HCC 280'],
            'HCC_DESCRIPTION': ['Pancreatic Cancer', 'Lung/Brain/GI Cancer',
                                'Diabetes w/ Chronic Complication', 'Diabetes w/ Complication',
                                'Diabetes w/o Complication', 'Coagulation Defects',
                                'COPD', 'CKD Stage 5', 'HF High Severity',
                                'HF Medium Severity', 'HF Low Severity', 'Acute Stroke'],
            'V28_COEFFICIENT': [0.981, 0.493, 0.302, 0.302, 0.302, 0.220, 0.335, 0.289, 0.431, 0.431, 0.431, 0.297],
            'CATEGORY': ['Cancer', 'Cancer', 'Diabetes', 'Diabetes', 'Diabetes', 'Blood',
                         'Respiratory', 'Renal', 'CHF', 'CHF', 'CHF', 'Stroke'],
            'IS_CONSTRAINED': [False, False, True, True, True, False, False, False, True, True, True, False]
        })

risk_df = load_risk_scores(session_available)
hcc_df = load_hcc_reference(session_available)

# Sidebar filters
with st.sidebar:
    if not risk_df.empty:
        lob_filter = st.multiselect("Line of Business", sorted(risk_df['LINE_OF_BUSINESS'].unique()),
                                     default=sorted(risk_df['LINE_OF_BUSINESS'].unique()))
        state_filter = st.multiselect("State", sorted(risk_df['MEMBER_STATE'].unique()),
                                       default=sorted(risk_df['MEMBER_STATE'].unique()))
    render_connection_status(session_available)

if not risk_df.empty:
    filtered = risk_df[risk_df['LINE_OF_BUSINESS'].isin(lob_filter) & risk_df['MEMBER_STATE'].isin(state_filter)]
else:
    filtered = risk_df

# HEADER + NAV
render_page_header_nav(current_page_index=3)
render_header("Risk Adjustment", "CMS-HCC v28 RAF scoring and revenue exposure analysis")
technical = is_technical_mode()

# v28 constraint explanation
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.6); padding: 1rem 1.25rem; border-radius: 10px;
            margin-bottom: 1.5rem; border-left: 4px solid #f59e0b;">
    <strong style="color: #f59e0b;">CMS-HCC v28 Update:</strong>
    <span style="color: #ccd6f6;"> The v28 model constrains Diabetes (HCC 36/37/38) and CHF (HCC 224/225/226)
    to equal coefficients within each group, reducing coding intensity gaming.
    This is reflected in the RAF scores below.</span>
</div>
""", unsafe_allow_html=True)

# KPIs
if not filtered.empty:
    total_members = filtered['MEMBER_COUNT'].sum()
    weighted_raf = (filtered['AVG_RAF_SCORE'] * filtered['MEMBER_COUNT']).sum() / total_members
    weighted_premium = (filtered['AVG_PREMIUM_PMPM'] * filtered['MEMBER_COUNT']).sum() / total_members
    weighted_ra_pmpm = (filtered['AVG_RISK_ADJUSTED_PMPM'] * filtered['MEMBER_COUNT']).sum() / total_members
    revenue_at_risk = (weighted_ra_pmpm - weighted_premium) * total_members * 12

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card(f"{weighted_raf:.3f}", "Avg RAF Score", "Population-weighted"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(f"${weighted_premium:,.0f}", "Avg Premium PMPM", "Base rate"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(f"${weighted_ra_pmpm:,.0f}", "Risk-Adjusted PMPM", "After RAF"), unsafe_allow_html=True)
    with col4:
        delta_type = "positive" if revenue_at_risk > 0 else "negative"
        st.markdown(render_metric_card(
            f"${abs(revenue_at_risk)/1e6:,.1f}M", "Annual Revenue Impact",
            "Risk adjustment uplift" if revenue_at_risk > 0 else "Revenue erosion risk",
            delta_type
        ), unsafe_allow_html=True)

    # --- ACTION BAR ---
    actions = render_action_bar([
        {"label": "RAF Audit Report", "icon": "\u2611", "callback_key": "raf_audit"},
        {"label": "Export Coefficients", "icon": "\u2B07", "callback_key": "export_coeff"},
        {"label": "Flag Coding Gaps", "icon": "\u26A0", "callback_key": "coding_gaps"},
    ], key_prefix="risk_actions")

    if actions.get("raf_audit"):
        render_audit_package([
            {"name": "RAF Score Distribution", "description": "Population-weighted RAF by LOB and state", "included": True},
            {"name": "v28 Coefficient Table", "description": "CMS-HCC v28 constrained coefficients", "included": True},
            {"name": "Revenue Impact Analysis", "description": "Risk adjustment uplift/erosion by segment", "included": True},
            {"name": "Coding Intensity Review", "description": "HCC coding rates by state (prospective vs retrospective)", "included": False},
            {"name": "Data Governance Attestation", "description": "Semantic View lineage proof", "included": True},
        ], package_name="RAF Audit Report", key_prefix="raf_audit_pkg")

    if actions.get("export_coeff"):
        render_export_buttons(hcc_df, "HCC_v28_Coefficients", key_prefix="risk_coeff_export")

    if actions.get("coding_gaps"):
        st.markdown("""
        <div style="background:rgba(255,183,77,0.1);border:1px solid rgba(255,183,77,0.3);
                    padding:1rem;border-radius:10px;margin:0.5rem 0;">
            <strong style="color:#FFB74D;">Coding Gap Analysis</strong>
            <p style="color:#ccd6f6;font-size:0.85rem;margin:0.5rem 0 0 0;">
                In live mode, this would query member diagnoses against HCC hierarchies to identify
                members with suspected-but-uncoded conditions (e.g., diabetic members without
                HCC 36/37/38 diagnosis). Estimated revenue recovery: 2-4% of risk-adjusted premium.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # RAF Distribution by LOB
    st.markdown("### RAF Score Distribution by Line of Business")

    lob_raf = filtered.groupby('LINE_OF_BUSINESS').apply(
        lambda x: pd.Series({
            'AVG_RAF': (x['AVG_RAF_SCORE'] * x['MEMBER_COUNT']).sum() / x['MEMBER_COUNT'].sum(),
            'MEMBERS': x['MEMBER_COUNT'].sum()
        })
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=lob_raf['LINE_OF_BUSINESS'].str.replace('_', ' '),
        y=lob_raf['AVG_RAF'],
        marker_color=['#29B5E8', '#667eea', '#00D4AA', '#FFB74D', '#FF6B6B'][:len(lob_raf)],
        text=[f"{r:.3f}" for r in lob_raf['AVG_RAF']],
        textposition='outside'
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="#8892b0", annotation_text="Baseline RAF 1.0")
    fig.update_layout(
        template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title='Average RAF Score', height=380, margin=dict(l=40, r=20, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)

    # HCC Coefficient Table
    st.markdown("### CMS-HCC v28 Coefficient Reference")

    col1, col2 = st.columns([2, 1])
    with col1:
        if not hcc_df.empty:
            fig2 = go.Figure()
            colors = ['#FF6B6B' if c else '#29B5E8' for c in hcc_df['IS_CONSTRAINED']]
            fig2.add_trace(go.Bar(
                x=hcc_df['HCC_CODE'], y=hcc_df['V28_COEFFICIENT'],
                marker_color=colors,
                text=[f"{v:.3f}" for v in hcc_df['V28_COEFFICIENT']],
                textposition='outside', hovertext=hcc_df['HCC_DESCRIPTION']
            ))
            fig2.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis_title='v28 Coefficient', height=400,
                margin=dict(l=40, r=20, t=20, b=80), xaxis_tickangle=-45
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <p style="color: #29B5E8; font-weight: 600; margin-bottom: 0.5rem;">Legend</p>
            <p style="color: #29B5E8; margin: 0.25rem 0;">Blue = Unconstrained</p>
            <p style="color: #FF6B6B; margin: 0.25rem 0;">Red = Constrained (equal coefficients)</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p style="color: #8892b0; font-size: 0.8rem; margin-top: 0.5rem;">
                <strong>Diabetes Group:</strong> HCC 36/37/38 all = 0.302<br>
                <strong>CHF Group:</strong> HCC 224/225/226 all = 0.431<br><br>
                v28 removes prior coding intensity arbitrage between severity levels.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # RAF By State
    st.markdown("### RAF Score by State")

    state_raf = filtered.groupby('MEMBER_STATE').apply(
        lambda x: pd.Series({
            'AVG_RAF': (x['AVG_RAF_SCORE'] * x['MEMBER_COUNT']).sum() / x['MEMBER_COUNT'].sum(),
            'MEMBERS': x['MEMBER_COUNT'].sum(),
            'HCC_CODED': x[x['PRIMARY_HCC'].notna()]['MEMBER_COUNT'].sum()
        })
    ).reset_index()
    state_raf['HCC_RATE'] = state_raf['HCC_CODED'] / state_raf['MEMBERS']

    col1, col2 = st.columns(2)
    with col1:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=state_raf['MEMBER_STATE'], y=state_raf['AVG_RAF'],
            marker_color='#29B5E8', name='Avg RAF',
            text=[f"{r:.3f}" for r in state_raf['AVG_RAF']], textposition='outside'
        ))
        fig3.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Avg RAF Score', height=350, margin=dict(l=40, r=20, t=20, b=40)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=state_raf['MEMBER_STATE'], y=state_raf['HCC_RATE'],
            marker_color='#667eea', name='HCC Coding Rate',
            text=[f"{r:.0%}" for r in state_raf['HCC_RATE']], textposition='outside'
        ))
        fig4.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_tickformat='.0%', yaxis_title='HCC Coding Rate', height=350,
            margin=dict(l=40, r=20, t=20, b=40)
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Technical view
    if technical:
        render_code_block("""-- CMS-HCC v28 RAF Score Calculation
SELECT m.member_id, m.line_of_business,
       m.age_band, m.member_state,
       COALESCE(SUM(h.v28_coefficient), 0) + 
           CASE m.age_band
               WHEN 'SENIOR' THEN 0.35
               WHEN 'ADULT_MATURE' THEN 0.15
               ELSE 0.0
           END AS raf_score
FROM GOLD.SYNTH_MEMBER_ELIGIBILITY m
LEFT JOIN GOLD.HCC_REFERENCE h ON m.primary_hcc = h.hcc_code
GROUP BY 1, 2, 3, 4;""", "RAF Score Computation (v28 Constrained)")

    # Detail table
    with st.expander("View Detailed Risk Score Data"):
        st.dataframe(filtered.sort_values('MEMBER_COUNT', ascending=False).head(100),
                     use_container_width=True, hide_index=True)
        render_export_buttons(filtered.head(100), "Risk_Score_Detail", key_prefix="risk_detail_export")
