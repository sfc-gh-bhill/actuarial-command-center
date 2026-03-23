# ==============================================================================
# PAGE 3: CLAIMS ANALYTICS
# High-cost claim analysis, service category drill-down, episode clustering
# Actions: Export high-cost report, draft stop-loss alert, download data
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Claims Analytics | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_proactive_alert,
                           render_connection_status)

apply_styles()

from utils.data_cache import get_connection, compute_category_summary, compute_lag_by_category, df_hash

session, session_available = get_connection()

# SIDEBAR
with st.sidebar:
    render_nav_blade(current_page_index=4)
    st.divider()
    st.markdown("### Filters")

# DATA
@st.cache_data(ttl=300)
def load_claims_data(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT service_category, member_state, line_of_business,
                   age_band, network_status, is_high_cost,
                   paid_amount, allowed_amount, charge_amount,
                   claims_lag_days, incurral_month, procedure_code, ms_drg
            FROM SILVER.MEDICAL_CLAIMS_CLEAN
            SAMPLE (50000 ROWS)
        """).to_pandas()
    else:
        np.random.seed(42)
        n = 50000
        cats = ['OUTPATIENT_PROFESSIONAL', 'OUTPATIENT_FACILITY', 'INPATIENT',
                'BEHAVIORAL_HEALTH', 'EMERGENCY', 'OTHER']
        states = ['TX', 'MN', 'FL', 'CA', 'NY']
        lobs = ['ACA_INDIVIDUAL', 'ACA_SMALL_GROUP', 'ACA_LARGE_GROUP', 'MEDICARE_ADVANTAGE', 'MEDICAID_MANAGED']
        bands = ['PEDIATRIC', 'ADULT_YOUNG', 'ADULT_MATURE', 'SENIOR']
        cat_probs = [0.35, 0.20, 0.15, 0.12, 0.10, 0.08]
        service_cat = np.random.choice(cats, n, p=cat_probs)
        paid = np.where(service_cat == 'INPATIENT',
                        np.random.lognormal(9.0, 0.7, n),
                        np.where(service_cat == 'BEHAVIORAL_HEALTH',
                                 np.abs(np.random.gamma(2, 100, n)),
                                 np.abs(np.random.gamma(2, 125, n))))
        return pd.DataFrame({
            'SERVICE_CATEGORY': service_cat,
            'MEMBER_STATE': np.random.choice(states, n, p=[0.4, 0.25, 0.15, 0.12, 0.08]),
            'LINE_OF_BUSINESS': np.random.choice(lobs, n),
            'AGE_BAND': np.random.choice(bands, n),
            'NETWORK_STATUS': np.random.choice(['IN', 'OUT'], n, p=[0.9, 0.1]),
            'IS_HIGH_COST': paid > 50000,
            'PAID_AMOUNT': np.round(paid, 2),
            'ALLOWED_AMOUNT': np.round(paid * np.random.uniform(1.0, 1.2, n), 2),
            'CHARGE_AMOUNT': np.round(paid * np.random.uniform(1.5, 2.5, n), 2),
            'CLAIMS_LAG_DAYS': np.random.randint(7, 120, n),
            'INCURRAL_MONTH': np.random.choice(pd.date_range(end=pd.Timestamp.today(), periods=24, freq='MS'), n),
            'PROCEDURE_CODE': np.random.choice(['99213', '99214', '99215', '90837', '99223', '99285'], n),
            'MS_DRG': np.where(service_cat == 'INPATIENT', np.random.choice(['470', '871', '291', '392'], n), None)
        })

df = load_claims_data(session_available)

with st.sidebar:
    if not df.empty:
        cat_filter = st.multiselect("Service Category", sorted(df['SERVICE_CATEGORY'].unique()),
                                     default=sorted(df['SERVICE_CATEGORY'].unique()))
        state_filter = st.multiselect("State", sorted(df['MEMBER_STATE'].unique()),
                                       default=sorted(df['MEMBER_STATE'].unique()))
        network_filter = st.multiselect("Network", ['IN', 'OUT'], default=['IN', 'OUT'])
    render_connection_status(session_available)

if not df.empty:
    filtered = df[df['SERVICE_CATEGORY'].isin(cat_filter) &
                  df['MEMBER_STATE'].isin(state_filter) &
                  df['NETWORK_STATUS'].isin(network_filter)]
else:
    filtered = df

# HEADER + NAV
render_page_header_nav(current_page_index=4)
render_header("Claims Analytics", "Deep-dive into claim distributions, high-cost outliers, and service mix")
technical = is_technical_mode()

# KPIs
if not filtered.empty:
    total_paid = filtered['PAID_AMOUNT'].sum()
    avg_paid = filtered['PAID_AMOUNT'].mean()
    median_paid = filtered['PAID_AMOUNT'].median()
    high_cost_pct = filtered['IS_HIGH_COST'].mean()
    total_claims = len(filtered)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Claims", f"{total_claims:,}")
    with col2:
        st.metric("Total Paid", f"${total_paid/1e6:,.1f}M")
    with col3:
        st.metric("Avg Per Claim", f"${avg_paid:,.0f}")
    with col4:
        st.metric("Median Per Claim", f"${median_paid:,.0f}")
    with col5:
        st.metric("High-Cost %", f"{high_cost_pct:.1%}")

    # --- ACTION BAR ---
    actions = render_action_bar([
        {"label": "Export High-Cost Report", "icon": "\u2B07", "callback_key": "export_highcost"},
        {"label": "Draft Stop-Loss Alert", "icon": "\u26A0", "callback_key": "stoploss_alert"},
        {"label": "Download Distribution", "icon": "\u2B07", "callback_key": "export_dist"},
    ], key_prefix="claims_actions")

    if actions.get("stoploss_alert"):
        high_cost = filtered[filtered['IS_HIGH_COST'] == True]
        hc_total = high_cost['PAID_AMOUNT'].sum() if not high_cost.empty else 0
        render_email_composer(
            subject=f"Stop-Loss Alert: {len(high_cost)} High-Cost Claims ({pd.Timestamp.today().strftime('%b %Y')})",
            body_markdown=f"""Stop-Loss / Large Claim Alert:

- High-cost claims (>$50K): {len(high_cost):,}
- Total high-cost spend: ${hc_total/1e6:,.1f}M
- % of total spend: {hc_total/total_paid:.1%}
- Specific attachment point analysis recommended for claims >$250K

Top service categories:
- Inpatient (DRG-based): Primary driver of high-cost claims
- Emergency: Secondary contributor

Recommended: Review reinsurance attachment points and pooling thresholds.""",
            insights=[
                {"label": "High-Cost Claims", "value": f"{len(high_cost):,} claims", "checked": True},
                {"label": "High-Cost Spend", "value": f"${hc_total/1e6:,.1f}M", "checked": True},
                {"label": "% of Total Spend", "value": f"{hc_total/total_paid:.1%}", "checked": True},
                {"label": "Total Paid", "value": f"${total_paid/1e6:,.1f}M", "checked": False},
                {"label": "Total Claims", "value": f"{total_claims:,}", "checked": False},
            ],
            page_context="a Stop-Loss alert from the Claims Analytics module",
            key_prefix="claims_stoploss_email"
        )

    if actions.get("export_highcost"):
        high_cost_df = filtered[filtered['IS_HIGH_COST'] == True]
        if not high_cost_df.empty:
            top_claims = high_cost_df.nlargest(100, 'PAID_AMOUNT')[
                ['SERVICE_CATEGORY', 'MEMBER_STATE', 'LINE_OF_BUSINESS', 'PAID_AMOUNT',
                 'ALLOWED_AMOUNT', 'CHARGE_AMOUNT', 'PROCEDURE_CODE', 'MS_DRG']
            ]
            render_export_buttons(top_claims, "High_Cost_Claims", key_prefix="claims_hc_export_top")
        else:
            st.info("No high-cost claims in the current filter selection.")

    if actions.get("export_dist"):
        dist_summary = filtered.groupby('SERVICE_CATEGORY').agg(
            CLAIM_COUNT=('PAID_AMOUNT', 'count'),
            TOTAL_PAID=('PAID_AMOUNT', 'sum'),
            AVG_PAID=('PAID_AMOUNT', 'mean'),
            MEDIAN_PAID=('PAID_AMOUNT', 'median'),
            P95_PAID=('PAID_AMOUNT', lambda x: x.quantile(0.95)),
        ).reset_index()
        render_export_buttons(dist_summary, "Claims_Distribution", key_prefix="claims_dist_export")

    # Stop-loss proactive alert if high-cost > 5%
    if high_cost_pct > 0.05:
        render_proactive_alert(
            "High-Cost Claims Concentration",
            f"{high_cost_pct:.1%} of claims exceed $50K threshold. "
            f"Review specific attachment points and reinsurance adequacy.",
            severity="warning",
            key_prefix="claims_hc_alert"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # TABS
    tab1, tab2, tab3, tab4 = st.tabs([
        "Cost Distribution", "Service Category Mix", "High-Cost Analysis", "Claims Lag"
    ])

    cat_colors = {
        'INPATIENT': '#FF6B6B', 'BEHAVIORAL_HEALTH': '#FFB74D',
        'EMERGENCY': '#f59e0b', 'OUTPATIENT_PROFESSIONAL': '#29B5E8',
        'OUTPATIENT_FACILITY': '#667eea', 'OTHER': '#8892b0'
    }

    with tab1:
        st.markdown("### Paid Amount Distribution by Service Category")
        if technical:
            st.markdown("""
            <div style="background: rgba(17, 34, 64, 0.6); padding: 0.75rem 1rem; border-radius: 8px;
                        margin-bottom: 1rem; border-left: 4px solid #29B5E8;">
                <span style="color: #ccd6f6; font-size: 0.85rem;">
                    Inpatient claims follow a <strong style="color: #29B5E8;">Lognormal</strong> distribution
                    (heavy right tail). Outpatient follows a <strong style="color: #00D4AA;">Gamma</strong> distribution.
                </span>
            </div>
            """, unsafe_allow_html=True)

        fig = go.Figure()
        for cat in filtered['SERVICE_CATEGORY'].unique():
            cat_data = filtered[filtered['SERVICE_CATEGORY'] == cat]['PAID_AMOUNT']
            fig.add_trace(go.Histogram(
                x=cat_data, name=cat.replace('_', ' ').title(),
                marker_color=cat_colors.get(cat, '#8892b0'),
                opacity=0.7, nbinsx=50
            ))
        fig.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='overlay', xaxis_title='Paid Amount ($)', yaxis_title='Count',
            height=450, margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            xaxis_range=[0, min(filtered['PAID_AMOUNT'].quantile(0.98), 100000)]
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Spend by Service Category")
        cat_summary = compute_category_summary(df_hash(filtered), filtered)

        col1, col2 = st.columns(2)
        with col1:
            fig2 = go.Figure(go.Pie(
                labels=cat_summary['SERVICE_CATEGORY'].str.replace('_', ' ').str.title(),
                values=cat_summary['TOTAL_PAID'], hole=0.4,
                marker_colors=[cat_colors.get(c, '#8892b0') for c in cat_summary['SERVICE_CATEGORY']]
            ))
            fig2.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=400,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=cat_summary['SERVICE_CATEGORY'].str.replace('_', ' ').str.title(),
                y=cat_summary['AVG_PAID'],
                marker_color=[cat_colors.get(c, '#8892b0') for c in cat_summary['SERVICE_CATEGORY']],
                text=[f"${v:,.0f}" for v in cat_summary['AVG_PAID']], textposition='outside'
            ))
            fig3.update_layout(
                template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis_title='Avg Paid Per Claim', height=400, margin=dict(l=40, r=20, t=20, b=80),
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.markdown("### High-Cost Claims (> $50K)")
        high_cost = filtered[filtered['IS_HIGH_COST'] == True]

        if not high_cost.empty:
            hc_total = high_cost['PAID_AMOUNT'].sum()
            hc_pct_spend = hc_total / total_paid
            hc_count = len(high_cost)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High-Cost Claims", f"{hc_count:,}")
            with col2:
                st.metric("High-Cost Spend", f"${hc_total/1e6:,.1f}M")
            with col3:
                st.metric("% of Total Spend", f"{hc_pct_spend:.1%}")

            st.markdown("#### Top 20 Highest-Cost Claims")
            top_claims = high_cost.nlargest(20, 'PAID_AMOUNT')[
                ['SERVICE_CATEGORY', 'MEMBER_STATE', 'LINE_OF_BUSINESS', 'PAID_AMOUNT',
                 'ALLOWED_AMOUNT', 'CHARGE_AMOUNT', 'PROCEDURE_CODE', 'MS_DRG']
            ]
            st.dataframe(top_claims, use_container_width=True, hide_index=True)
        else:
            st.info("No high-cost claims in the filtered selection.")

    with tab4:
        st.markdown("### Claims Lag Distribution")
        if technical:
            st.markdown("""
            <div style="background: rgba(17, 34, 64, 0.6); padding: 0.75rem 1rem; border-radius: 8px;
                        margin-bottom: 1rem; border-left: 4px solid #00D4AA;">
                <span style="color: #ccd6f6; font-size: 0.85rem;">
                    Claims lag = days between service date and payment date.
                    Longer lags increase <strong style="color: #00D4AA;">IBNR reserve</strong> requirements.
                </span>
            </div>
            """, unsafe_allow_html=True)

        lag_by_cat = compute_lag_by_category(df_hash(filtered), filtered)

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=lag_by_cat['SERVICE_CATEGORY'].str.replace('_', ' ').str.title(),
            y=lag_by_cat['AVG_LAG'], name='Average Lag', marker_color='#29B5E8'
        ))
        fig4.add_trace(go.Bar(
            x=lag_by_cat['SERVICE_CATEGORY'].str.replace('_', ' ').str.title(),
            y=lag_by_cat['MEDIAN_LAG'], name='Median Lag', marker_color='#667eea'
        ))
        fig4.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='group', yaxis_title='Days', height=400,
            margin=dict(l=40, r=20, t=20, b=80), xaxis_tickangle=-30,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Technical SQL
    if technical:
        render_code_block("""-- Claims distribution analysis
SELECT service_category,
       COUNT(*) AS claim_count,
       AVG(paid_amount) AS avg_paid,
       MEDIAN(paid_amount) AS median_paid,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY paid_amount) AS p95_paid,
       SUM(CASE WHEN paid_amount > 50000 THEN 1 ELSE 0 END) AS high_cost_count,
       SUM(CASE WHEN paid_amount > 50000 THEN paid_amount ELSE 0 END) AS high_cost_spend
FROM SILVER.MEDICAL_CLAIMS_CLEAN
GROUP BY 1
ORDER BY avg_paid DESC;""", "Claims Distribution SQL")
