# ==============================================================================
# PAGE 4: IBNR RESERVES
# Claims lag triangles, completion factors, chain-ladder reserving
# Actions: Reserve opinion package, export triangle, email completion update
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="IBNR Reserves | Actuarial Command Center", page_icon="\u2744", layout="wide")

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
    render_nav_blade(current_page_index=5)
    render_connection_status(session_available)

# DATA
@st.cache_data(ttl=300)
def load_lag_triangle(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT incurral_month, development_month, completion_factor,
                   cumulative_paid, estimated_ultimate, ibnr_reserve, age_to_age_factor
            FROM GOLD.IBNR_DEVELOPMENT
            ORDER BY incurral_month, development_month
        """).to_pandas()
    else:
        np.random.seed(42)
        months = pd.date_range(end=pd.Timestamp.today(), periods=24, freq='MS')
        completion_curve = [0.28, 0.52, 0.71, 0.82, 0.89, 0.93, 0.955, 0.97, 0.98, 0.988, 0.993, 0.997, 1.0]
        rows = []
        for i, m in enumerate(months):
            max_dev = min(12, 24 - i - 1)
            ultimate = np.random.uniform(2e6, 5e6)
            for d in range(max_dev + 1):
                cf = completion_curve[d] + np.random.uniform(-0.02, 0.02)
                cf = min(cf, 1.0)
                paid = ultimate * cf
                rows.append({
                    'INCURRAL_MONTH': m, 'DEVELOPMENT_MONTH': d,
                    'COMPLETION_FACTOR': round(cf, 4), 'CUMULATIVE_PAID': round(paid, 2),
                    'ESTIMATED_ULTIMATE': round(paid / cf, 2) if cf > 0 else None,
                    'IBNR_RESERVE': round((paid / cf) - paid, 2) if cf > 0 else None,
                    'AGE_TO_AGE_FACTOR': None
                })
        return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def load_ibnr_forecast(_session_available):
    if _session_available:
        from utils.data_cache import get_session as _gs
        return _gs().sql("""
            SELECT incurral_month, current_development_month, paid_to_date,
                   current_completion_factor, estimated_ultimate_claims,
                   ibnr_reserve, ibnr_lower_bound, ibnr_upper_bound, maturity_status
            FROM ANALYTICS.IBNR_FORECAST
            ORDER BY incurral_month
        """).to_pandas()
    else:
        np.random.seed(42)
        months = pd.date_range(end=pd.Timestamp.today(), periods=24, freq='MS')
        rows = []
        completion_curve = [0.28, 0.52, 0.71, 0.82, 0.89, 0.93, 0.955, 0.97, 0.98, 0.988, 0.993, 0.997, 1.0]
        for i, m in enumerate(months):
            max_dev = min(12, 24 - i - 1)
            cf = completion_curve[max_dev]
            paid = np.random.uniform(2e6, 5e6) * cf
            ultimate = paid / cf if cf > 0 else paid
            ibnr = ultimate - paid
            mat = 'MATURE' if cf >= 0.98 else 'DEVELOPING' if cf >= 0.90 else 'IMMATURE' if cf >= 0.70 else 'VERY_IMMATURE'
            rows.append({
                'INCURRAL_MONTH': m, 'CURRENT_DEVELOPMENT_MONTH': max_dev,
                'PAID_TO_DATE': round(paid, 2), 'CURRENT_COMPLETION_FACTOR': round(cf, 4),
                'ESTIMATED_ULTIMATE_CLAIMS': round(ultimate, 2), 'IBNR_RESERVE': round(ibnr, 2),
                'IBNR_LOWER_BOUND': round(ultimate * 0.95, 2), 'IBNR_UPPER_BOUND': round(ultimate * 1.05, 2),
                'MATURITY_STATUS': mat
            })
        return pd.DataFrame(rows)

triangle_df = load_lag_triangle(session_available)
forecast_df = load_ibnr_forecast(session_available)

# HEADER + NAV
render_page_header_nav(current_page_index=5)
render_header("IBNR Reserves", "Claims lag triangles, completion factors, and chain-ladder reserving")
technical = is_technical_mode()

# Methodology note
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.6); padding: 1rem 1.25rem; border-radius: 10px;
            margin-bottom: 1.5rem; border-left: 4px solid #29B5E8;">
    <strong style="color: #29B5E8;">IBNR Methodology:</strong>
    <span style="color: #ccd6f6;"> Chain-ladder method applied to claims run-off triangle.
    Estimated Ultimate = Paid-to-Date / Completion Factor. IBNR Reserve = Ultimate - Paid.
    Immature months (&lt;70% complete) carry the largest reserve uncertainty.</span>
</div>
""", unsafe_allow_html=True)

# KPIs
if not forecast_df.empty:
    total_ibnr = forecast_df['IBNR_RESERVE'].sum()
    total_paid = forecast_df['PAID_TO_DATE'].sum()
    total_ultimate = forecast_df['ESTIMATED_ULTIMATE_CLAIMS'].sum()
    immature_count = len(forecast_df[forecast_df['MATURITY_STATUS'].isin(['IMMATURE', 'VERY_IMMATURE'])])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card(f"${total_ibnr/1e6:,.1f}M", "Total IBNR Reserve", "All incurral months"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card(f"${total_paid/1e6:,.1f}M", "Paid to Date", "Cumulative paid"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card(f"${total_ultimate/1e6:,.1f}M", "Est. Ultimate", "Chain-ladder estimate"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card(f"{immature_count}", "Immature Months", "Completion < 70%",
                                        "negative" if immature_count > 3 else "positive"), unsafe_allow_html=True)

    # --- ACTION BAR ---
    actions = render_action_bar([
        {"label": "Reserve Opinion Package", "icon": "\u2611", "callback_key": "reserve_pkg"},
        {"label": "Export Triangle", "icon": "\u2B07", "callback_key": "export_triangle"},
        {"label": "Email Completion Update", "icon": "\u2709", "callback_key": "email_ibnr"},
    ], key_prefix="ibnr_actions")

    if actions.get("reserve_pkg"):
        render_audit_package([
            {"name": "IBNR Summary", "description": "Total reserve, paid-to-date, ultimate estimates", "included": True},
            {"name": "Run-Off Triangle", "description": "Full completion factor triangle (heatmap)", "included": True},
            {"name": "Completion S-Curve", "description": "Average completion by development month", "included": True},
            {"name": "Chain-Ladder Methodology", "description": "Age-to-age factors, selected factors, tail factor", "included": True},
            {"name": "Maturity Classification", "description": "Month-by-month maturity status", "included": True},
            {"name": "Bornhuetter-Ferguson Comparison", "description": "BF vs chain-ladder variance analysis", "included": False},
        ], package_name="Actuarial Reserve Opinion Package", key_prefix="ibnr_reserve_audit")

    if actions.get("export_triangle"):
        render_export_buttons(triangle_df, "IBNR_Triangle", key_prefix="ibnr_tri_export")

    if actions.get("email_ibnr"):
        render_email_composer(
            subject=f"IBNR Reserve Update — ${total_ibnr/1e6:,.1f}M ({pd.Timestamp.today().strftime('%b %Y')})",
            body_markdown=f"""IBNR Reserve Update:

- Total IBNR Reserve: ${total_ibnr/1e6:,.1f}M
- Paid to Date: ${total_paid/1e6:,.1f}M
- Estimated Ultimate: ${total_ultimate/1e6:,.1f}M
- Immature Months (<70% complete): {immature_count}

Methodology: Chain-ladder (deterministic). Immature months carry highest uncertainty.
Reserve adequacy confidence: 75th percentile.""",
            insights=[
                {"label": "IBNR Reserve", "value": f"${total_ibnr/1e6:,.1f}M", "checked": True},
                {"label": "Paid to Date", "value": f"${total_paid/1e6:,.1f}M", "checked": True},
                {"label": "Estimated Ultimate", "value": f"${total_ultimate/1e6:,.1f}M", "checked": True},
                {"label": "Immature Months", "value": f"{immature_count}", "checked": True},
            ],
            page_context="an IBNR Reserve update from the Actuarial Command Center",
            key_prefix="ibnr_email"
        )

    st.markdown("<br>", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3 = st.tabs(["IBNR Reserve Waterfall", "Completion Factor Curve", "Run-Off Triangle"])

with tab1:
    st.markdown("### IBNR Reserve by Incurral Month")
    if not forecast_df.empty:
        plot_df = forecast_df.sort_values('INCURRAL_MONTH').tail(18)
        maturity_colors = {
            'MATURE': '#4ECDC4', 'DEVELOPING': '#29B5E8',
            'IMMATURE': '#FFB74D', 'VERY_IMMATURE': '#FF6B6B'
        }
        bar_colors = [maturity_colors.get(m, '#8892b0') for m in plot_df['MATURITY_STATUS']]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plot_df['INCURRAL_MONTH'].astype(str).str[:7],
            y=plot_df['PAID_TO_DATE'],
            name='Paid to Date', marker_color='#29B5E8', opacity=0.8
        ))
        fig.add_trace(go.Bar(
            x=plot_df['INCURRAL_MONTH'].astype(str).str[:7],
            y=plot_df['IBNR_RESERVE'],
            name='IBNR Reserve', marker_color=bar_colors, opacity=0.9
        ))
        fig.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='stack', yaxis_title='Dollars ($)', height=450,
            margin=dict(l=40, r=20, t=20, b=60), xaxis_tickangle=-45,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div style="display: flex; gap: 1.5rem; justify-content: center; margin-top: 0.5rem;">
            <span style="color: #4ECDC4;">&#9632; Mature (98%+)</span>
            <span style="color: #29B5E8;">&#9632; Developing (90-98%)</span>
            <span style="color: #FFB74D;">&#9632; Immature (70-90%)</span>
            <span style="color: #FF6B6B;">&#9632; Very Immature (&lt;70%)</span>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Completion Factor S-Curve")
    if not triangle_df.empty:
        avg_cf = triangle_df.groupby('DEVELOPMENT_MONTH')['COMPLETION_FACTOR'].agg(['mean', 'min', 'max']).reset_index()

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=avg_cf['DEVELOPMENT_MONTH'], y=avg_cf['max'],
            mode='lines', name='Max', line=dict(width=0), showlegend=False
        ))
        fig2.add_trace(go.Scatter(
            x=avg_cf['DEVELOPMENT_MONTH'], y=avg_cf['min'],
            mode='lines', name='Range', fill='tonexty',
            fillcolor='rgba(41,181,232,0.15)', line=dict(width=0)
        ))
        fig2.add_trace(go.Scatter(
            x=avg_cf['DEVELOPMENT_MONTH'], y=avg_cf['mean'],
            mode='lines+markers', name='Avg Completion',
            line=dict(color='#29B5E8', width=3), marker=dict(size=8, color='#29B5E8')
        ))
        fig2.add_hline(y=0.70, line_dash="dot", line_color="#FFB74D", annotation_text="70% Immature Threshold")
        fig2.add_hline(y=0.90, line_dash="dot", line_color="#29B5E8", annotation_text="90% Developing")
        fig2.add_hline(y=0.98, line_dash="dot", line_color="#4ECDC4", annotation_text="98% Mature")

        fig2.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Development Month', yaxis_title='Completion Factor',
            yaxis_tickformat='.0%', height=450,
            margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### Claims Run-Off Triangle (Heatmap)")
    if not triangle_df.empty:
        pivot = triangle_df.pivot_table(
            index='INCURRAL_MONTH', columns='DEVELOPMENT_MONTH',
            values='COMPLETION_FACTOR', aggfunc='mean'
        )
        pivot_display = pivot.copy()
        pivot_display.index = pivot_display.index.astype(str).str[:7]

        fig3 = go.Figure(go.Heatmap(
            z=pivot_display.values,
            x=[f"Dev {c}" for c in pivot_display.columns],
            y=pivot_display.index,
            colorscale=[[0, '#0a192f'], [0.5, '#29B5E8'], [1, '#4ECDC4']],
            text=[[f"{v:.1%}" if pd.notna(v) else "" for v in row] for row in pivot_display.values],
            texttemplate="%{text}", textfont=dict(size=9),
            zmin=0, zmax=1,
            colorbar=dict(title="Completion", tickformat='.0%')
        ))
        fig3.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            height=600, margin=dict(l=80, r=20, t=20, b=40),
            yaxis=dict(autorange='reversed')
        )
        st.plotly_chart(fig3, use_container_width=True)

# Technical SQL
if technical:
    render_code_block("""-- Chain-Ladder IBNR Calculation
WITH triangle AS (
    SELECT incurral_month, development_month,
           cumulative_paid,
           cumulative_paid / LAG(cumulative_paid) OVER (
               PARTITION BY incurral_month ORDER BY development_month
           ) AS age_to_age_factor
    FROM GOLD.CLAIMS_LAG_TRIANGLE
)
SELECT incurral_month,
       MAX(cumulative_paid) AS paid_to_date,
       MAX(cumulative_paid) / completion_factor AS estimated_ultimate,
       (MAX(cumulative_paid) / completion_factor) - MAX(cumulative_paid) AS ibnr_reserve
FROM triangle
GROUP BY incurral_month, completion_factor;""", "Chain-Ladder IBNR SQL")

# Detail table
with st.expander("View IBNR Forecast Details"):
    if not forecast_df.empty:
        display = forecast_df.copy()
        display['INCURRAL_MONTH'] = display['INCURRAL_MONTH'].astype(str).str[:7]
        st.dataframe(display.sort_values('INCURRAL_MONTH', ascending=False),
                     use_container_width=True, hide_index=True)
        render_export_buttons(display, "IBNR_Forecast", key_prefix="ibnr_forecast_export")
