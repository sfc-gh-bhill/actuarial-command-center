# ==============================================================================
# PAGE 1: MARGIN FORECAST
# MLR tracking vs ACA targets, margin projection by LOB
# Actions: Share forecast, export projection, schedule alert
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Margin Forecast | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card, render_status_badge
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_connection_status)

apply_styles()

from utils.data_cache import get_connection, load_financial_summary, compute_lob_summary, compute_monthly_lob_mlr, df_hash

session, session_available = get_connection()

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    render_nav_blade(current_page_index=2)
    st.divider()
    st.markdown("### Filters")

# ------------------------------------------------------------------------------
# DATA (centralized cache)
# ------------------------------------------------------------------------------
df = load_financial_summary(session_available)

# Sidebar filters
with st.sidebar:
    lob_options = sorted(df['LINE_OF_BUSINESS'].unique()) if not df.empty else []
    selected_lobs = st.multiselect("Line of Business", lob_options, default=lob_options)
    state_options = sorted(df['MEMBER_STATE'].unique()) if not df.empty else []
    selected_states = st.multiselect("State", state_options, default=state_options)
    render_connection_status(session_available)

if not df.empty:
    filtered = df[df['LINE_OF_BUSINESS'].isin(selected_lobs) & df['MEMBER_STATE'].isin(selected_states)]
else:
    filtered = df

# ------------------------------------------------------------------------------
# HEADER + NAV
# ------------------------------------------------------------------------------
render_page_header_nav(current_page_index=2)
render_header("Margin Forecast", "MLR tracking versus ACA regulatory targets by Line of Business")
technical = is_technical_mode()

# ACA reference
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.6); padding: 1rem 1.25rem; border-radius: 10px;
            margin-bottom: 1.5rem; border-left: 4px solid #29B5E8;">
    <strong style="color: #29B5E8;">ACA MLR Thresholds:</strong>
    <span style="color: #ccd6f6;"> Individual & Small Group: 80% minimum | Large Group: 85% minimum |
    Below threshold = MLR rebate obligation to policyholders</span>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# KPI TILES - BY LOB
# ------------------------------------------------------------------------------
if not filtered.empty:
    st.markdown("### Current MLR by Line of Business")

    lob_agg = compute_lob_summary(df_hash(filtered), filtered)
    lob_agg['MLR'] = lob_agg['TOTAL_PAID'] / lob_agg['TOTAL_PREMIUM']
    lob_agg['MARGIN'] = 1 - lob_agg['MLR']

    aca_targets = {
        'ACA_INDIVIDUAL': 0.80, 'ACA_SMALL_GROUP': 0.80, 'ACA_LARGE_GROUP': 0.85,
        'MEDICARE_ADVANTAGE': 0.85, 'MEDICAID_MANAGED': 0.85
    }

    cols = st.columns(len(lob_agg))
    for i, (_, row) in enumerate(lob_agg.iterrows()):
        with cols[i]:
            lob = row['LINE_OF_BUSINESS']
            target = aca_targets.get(lob, 0.85)
            mlr = row['MLR']
            margin = row['MARGIN']
            delta_type = "positive" if margin > 0.08 else "negative"
            st.markdown(render_metric_card(
                f"{mlr:.1%}", lob.replace('_', ' '),
                f"Margin: {margin:.1%} | Target: {target:.0%}",
                delta_type
            ), unsafe_allow_html=True)

    # --- ACTION BAR ---
    actions = render_action_bar([
        {"label": "Email Forecast", "icon": "\u2709", "callback_key": "email_forecast"},
        {"label": "Export Projections", "icon": "\u2B07", "callback_key": "export_proj"},
        {"label": "IBNR Adjustment", "icon": "\u2234", "callback_key": "ibnr_adj"},
    ], key_prefix="margin_actions")

    if actions.get("email_forecast"):
        body_lines = []
        insight_items = []
        for _, r in lob_agg.iterrows():
            lob_name = r['LINE_OF_BUSINESS'].replace('_', ' ')
            body_lines.append(f"- {lob_name}: MLR {r['MLR']:.1%}, Margin {r['MARGIN']:.1%}")
            insight_items.append({"label": lob_name, "value": f"MLR {r['MLR']:.1%} | Margin {r['MARGIN']:.1%}", "checked": True})
        render_email_composer(
            subject=f"Margin Forecast Update — {pd.Timestamp.today().strftime('%B %Y')}",
            body_markdown="MLR by Line of Business (current period):\n\n" + "\n".join(body_lines),
            insights=insight_items,
            page_context="the latest Margin Forecast from the Actuarial Command Center",
            key_prefix="margin_email"
        )

    if actions.get("export_proj"):
        render_export_buttons(lob_agg, "Margin_Projection", key_prefix="margin_proj_topbar")

    if actions.get("ibnr_adj"):
        with st.expander("IBNR Adjustment Factors", expanded=True):
            st.markdown("""
            <div style="background:rgba(41,181,232,0.1);border:1px solid rgba(41,181,232,0.3);
                        padding:1rem;border-radius:10px;margin-bottom:0.75rem;">
                <strong style="color:#29B5E8;">IBNR Completion Factor Adjustment</strong>
                <p style="color:#ccd6f6;font-size:0.85rem;margin:0.5rem 0 0 0;">
                    Apply completion factors to immature months to estimate ultimate claims cost.
                    This adjusts the margin forecast to account for incurred-but-not-reported claims.</p>
            </div>
            """, unsafe_allow_html=True)
            ibnr_col1, ibnr_col2, ibnr_col3 = st.columns(3)
            with ibnr_col1:
                month_1_factor = st.number_input("Month 1 (most recent)", min_value=1.0, max_value=2.0,
                                                  value=1.25, step=0.01, key="ibnr_m1")
            with ibnr_col2:
                month_2_factor = st.number_input("Month 2", min_value=1.0, max_value=1.5,
                                                  value=1.10, step=0.01, key="ibnr_m2")
            with ibnr_col3:
                month_3_factor = st.number_input("Month 3", min_value=1.0, max_value=1.3,
                                                  value=1.03, step=0.01, key="ibnr_m3")

            recent_3 = sorted(filtered['METRIC_MONTH'].unique())[-3:]
            ibnr_factors = {recent_3[-1]: month_1_factor, recent_3[-2]: month_2_factor,
                            recent_3[-3]: month_3_factor} if len(recent_3) >= 3 else {}

            adjusted = filtered.copy()
            for month, factor in ibnr_factors.items():
                mask = adjusted['METRIC_MONTH'] == month
                adjusted.loc[mask, 'TOTAL_PAID'] = adjusted.loc[mask, 'TOTAL_PAID'] * factor

            adj_paid = adjusted['TOTAL_PAID'].sum()
            adj_premium = adjusted['TOTAL_PREMIUM'].sum()
            adj_mlr = adj_paid / adj_premium if adj_premium > 0 else 0
            adj_margin = 1 - adj_mlr
            original_mlr = filtered['TOTAL_PAID'].sum() / filtered['TOTAL_PREMIUM'].sum() if filtered['TOTAL_PREMIUM'].sum() > 0 else 0

            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.metric("IBNR-Adjusted MLR", f"{adj_mlr:.1%}", f"{(adj_mlr - original_mlr)*100:+.1f} ppts")
            with res_col2:
                st.metric("IBNR-Adjusted Margin", f"{adj_margin:.1%}")
            with res_col3:
                ibnr_reserve = adj_paid - filtered['TOTAL_PAID'].sum()
                st.metric("Est. IBNR Reserve", f"${ibnr_reserve/1e6:,.1f}M")

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # MLR TREND BY LOB
    # --------------------------------------------------------------------------
    st.markdown("### MLR Trend by Line of Business")

    tab1, tab2 = st.tabs(["Trend Lines", "Margin Waterfall"])

    with tab1:
        monthly_lob = compute_monthly_lob_mlr(df_hash(filtered), filtered)

        fig = go.Figure()
        colors = {'ACA_INDIVIDUAL': '#29B5E8', 'ACA_SMALL_GROUP': '#667eea',
                  'ACA_LARGE_GROUP': '#00D4AA', 'MEDICARE_ADVANTAGE': '#FFB74D',
                  'MEDICAID_MANAGED': '#FF6B6B'}

        for lob in monthly_lob['LINE_OF_BUSINESS'].unique():
            lob_data = monthly_lob[monthly_lob['LINE_OF_BUSINESS'] == lob].sort_values('METRIC_MONTH')
            fig.add_trace(go.Scatter(
                x=lob_data['METRIC_MONTH'], y=lob_data['MLR'],
                name=lob.replace('_', ' '), mode='lines+markers',
                line=dict(color=colors.get(lob, '#8892b0'), width=2),
                marker=dict(size=5)
            ))

        fig.add_hline(y=0.85, line_dash="dash", line_color="#FFB74D", annotation_text="85%")
        fig.add_hline(y=0.80, line_dash="dash", line_color="#4ECDC4", annotation_text="80%")

        fig.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_tickformat='.0%', yaxis_title='MLR', height=450,
            margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        lob_waterfall = lob_agg.sort_values('MARGIN')
        fig2 = go.Figure(go.Waterfall(
            x=lob_waterfall['LINE_OF_BUSINESS'].str.replace('_', ' '),
            y=lob_waterfall['MARGIN'],
            text=[f"{m:.1%}" for m in lob_waterfall['MARGIN']],
            textposition='outside',
            connector=dict(line=dict(color='rgba(41,181,232,0.3)')),
            increasing=dict(marker=dict(color='#4ECDC4')),
            decreasing=dict(marker=dict(color='#FF6B6B'))
        ))
        fig2.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_tickformat='.0%', yaxis_title='Operating Margin', height=400,
            margin=dict(l=40, r=20, t=20, b=40)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------------------------------
    # YEAR-END MARGIN PROJECTION
    # --------------------------------------------------------------------------
    st.markdown("### Year-End Margin Projection")

    st.markdown("""
    <div style="background: rgba(17, 34, 64, 0.6); padding: 1rem; border-radius: 10px;
                margin-bottom: 1rem; border-left: 4px solid #00D4AA;">
        <span style="color: #00D4AA; font-weight: 600;">Methodology:</span>
        <span style="color: #ccd6f6;"> Trailing 6-month run rate extrapolated to year-end,
        adjusted for IBNR completion factors on immature months.</span>
    </div>
    """, unsafe_allow_html=True)

    recent_6 = sorted(filtered['METRIC_MONTH'].unique())[-6:]
    recent_data = filtered[filtered['METRIC_MONTH'].isin(recent_6)]

    projection = recent_data.groupby('LINE_OF_BUSINESS').agg(
        PAID_6MO=('TOTAL_PAID', 'sum'),
        PREMIUM_6MO=('TOTAL_PREMIUM', 'sum')
    ).reset_index()
    projection['ANNUAL_PAID'] = projection['PAID_6MO'] * 2
    projection['ANNUAL_PREMIUM'] = projection['PREMIUM_6MO'] * 2
    projection['PROJECTED_MLR'] = projection['ANNUAL_PAID'] / projection['ANNUAL_PREMIUM']
    projection['PROJECTED_MARGIN'] = 1 - projection['PROJECTED_MLR']

    col1, col2 = st.columns(2)
    with col1:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=projection['LINE_OF_BUSINESS'].str.replace('_', ' '),
            y=projection['ANNUAL_PAID'], name='Projected Claims', marker_color='#FF6B6B'
        ))
        fig3.add_trace(go.Bar(
            x=projection['LINE_OF_BUSINESS'].str.replace('_', ' '),
            y=projection['ANNUAL_PREMIUM'], name='Projected Premium', marker_color='#4ECDC4'
        ))
        fig3.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='group', height=350, title='Year-End Financial Projection',
            yaxis_title='Dollars', margin=dict(l=40, r=20, t=40, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        fig4 = go.Figure()
        colors = ['#FF6B6B' if m < 0.05 else '#FFB74D' if m < 0.10 else '#4ECDC4'
                  for m in projection['PROJECTED_MARGIN']]
        fig4.add_trace(go.Bar(
            x=projection['LINE_OF_BUSINESS'].str.replace('_', ' '),
            y=projection['PROJECTED_MARGIN'], marker_color=colors,
            text=[f"{m:.1%}" for m in projection['PROJECTED_MARGIN']],
            textposition='outside'
        ))
        fig4.add_hline(y=0.10, line_dash="dash", line_color="#29B5E8", annotation_text="10% Target")
        fig4.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_tickformat='.0%', height=350, title='Projected Year-End Margin',
            yaxis_title='Margin %', margin=dict(l=40, r=20, t=40, b=40)
        )
        st.plotly_chart(fig4, use_container_width=True)

    # --------------------------------------------------------------------------
    # TECHNICAL: SQL + METHODOLOGY
    # --------------------------------------------------------------------------
    if technical:
        render_code_block("""-- Year-End Margin Projection (6-month annualization)
WITH recent AS (
    SELECT line_of_business,
           SUM(total_paid) AS paid_6mo,
           SUM(total_premium) AS premium_6mo
    FROM GOLD.FINANCIAL_SUMMARY
    WHERE metric_month >= DATEADD('month', -6, CURRENT_DATE())
    GROUP BY 1
)
SELECT line_of_business,
       paid_6mo * 2 AS annual_paid_est,
       premium_6mo * 2 AS annual_premium_est,
       (paid_6mo * 2) / (premium_6mo * 2) AS projected_mlr,
       1 - ((paid_6mo * 2) / (premium_6mo * 2)) AS projected_margin
FROM recent;""", "Year-End Projection SQL")

    # --------------------------------------------------------------------------
    # DETAIL TABLE
    # --------------------------------------------------------------------------
    with st.expander("View Detailed Financial Data"):
        display_df = filtered.groupby(['METRIC_MONTH', 'LINE_OF_BUSINESS']).agg(
            TOTAL_PAID=('TOTAL_PAID', 'sum'),
            TOTAL_PREMIUM=('TOTAL_PREMIUM', 'sum'),
            CLAIMS=('CLAIM_COUNT', 'sum')
        ).reset_index()
        display_df['MLR'] = display_df['TOTAL_PAID'] / display_df['TOTAL_PREMIUM']
        display_df['MARGIN'] = 1 - display_df['MLR']
        st.dataframe(display_df.sort_values(['METRIC_MONTH', 'LINE_OF_BUSINESS'], ascending=[False, True]),
                     use_container_width=True, hide_index=True)
        render_export_buttons(display_df, "Margin_Detail", key_prefix="margin_detail_export")
