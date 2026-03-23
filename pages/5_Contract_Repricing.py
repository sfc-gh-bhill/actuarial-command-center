# ==============================================================================
# PAGE 5: CONTRACT REPRICING - "The Wow Moment"
# Interactive repricing simulation with adjustable parameters,
# multi-scenario comparison (up to 3), and mock negotiation brief
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import json
import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Contract Repricing | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_metric_card
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_export_buttons,
                           render_email_composer, render_code_block, render_connection_status)

apply_styles()

from utils.data_cache import get_connection

session, session_available = get_connection()

# ==============================================================================
# HEADER + NAV
# ==============================================================================
render_header("Contract Repricing", "Real-time margin impact simulation with basis point adjustment")

st.markdown("""
<div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(41, 181, 232, 0.1) 100%);
            padding: 1.25rem; border-radius: 12px; margin-bottom: 1.5rem;
            border: 1px solid rgba(16, 185, 129, 0.3);">
    <h4 style="color: #10b981; margin: 0 0 0.5rem 0; border: none;">The "Wow" Moment</h4>
    <p style="color: #ccd6f6; margin: 0; line-height: 1.5;">
        <em>"What if we renegotiate the Texas hospital system contract down by 200 basis points?"</em><br>
        Configure the scenario below, review the impact, then save up to 3 scenarios
        to compare side-by-side. Email or export when ready.
    </p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR — Navigation only
# ==============================================================================
with st.sidebar:
    render_nav_blade(current_page_index=6)
    render_connection_status(session_available)

render_page_header_nav(current_page_index=6)
technical = is_technical_mode()

# ==============================================================================
# REPRICING CONTROLS — Inline on the page
# ==============================================================================
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.5); border: 1px solid rgba(41, 181, 232, 0.2);
            border-radius: 12px; padding: 1rem 1.25rem 0.25rem 1.25rem; margin-bottom: 1.25rem;">
    <p style="color: #29B5E8; font-size: 0.7rem; letter-spacing: 2px; font-weight: 600;
              margin: 0 0 0.5rem 0; text-transform: uppercase;">SCENARIO PARAMETERS</p>
</div>
""", unsafe_allow_html=True)

ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4, ctrl_c5 = st.columns([1, 1.4, 1, 1, 1])
with ctrl_c1:
    target_state = st.selectbox("Target State", ['TX', 'MN', 'FL', 'CA'], index=0,
                                 key="reprice_state")
with ctrl_c2:
    basis_points = st.slider("Basis Point Adjustment", min_value=-500, max_value=500,
                              value=-200, step=25, key="reprice_bps",
                              help="Negative = rate decrease, Positive = rate increase")
with ctrl_c3:
    service_scope = st.selectbox("Service Scope", ["All Services", "Inpatient Only", "Outpatient Only"],
                                  index=0, key="reprice_scope")
with ctrl_c4:
    ip_passthrough = st.slider("Inpatient Pass-Through %", min_value=0, max_value=100,
                                value=100, step=5, key="reprice_ip_pct",
                                help="% of BPS adjustment applied to inpatient claims")
with ctrl_c5:
    op_passthrough = st.slider("Outpatient Pass-Through %", min_value=0, max_value=100,
                                value=50, step=5, key="reprice_op_pct",
                                help="% of BPS adjustment applied to outpatient claims")

# Rate factor summary strip
_rf_color = '#4ECDC4' if basis_points < 0 else '#FF6B6B'
st.markdown(f"""
<div style="display:flex; align-items:center; gap:1.5rem; padding:0.5rem 1rem;
            background:rgba(17,34,64,0.4); border-radius:8px; margin:-0.5rem 0 1.25rem 0;">
    <span style="color:#8892b0;font-size:0.8rem;">Rate Factor</span>
    <span style="color:{_rf_color};font-weight:700;font-size:1.1rem;">
        {1 + basis_points/10000:.4f}x</span>
    <span style="color:#8892b0;font-size:0.8rem;">
        {abs(basis_points)} bps {'decrease' if basis_points < 0 else 'increase'}
        &middot; IP {ip_passthrough}% &middot; OP {op_passthrough}%
        &middot; {service_scope}
    </span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# REPRICING ENGINE — with adjustable pass-through rates
# ==============================================================================
@st.cache_data(ttl=60)
def run_repricing(bps, state, ip_pct, op_pct, scope, _session_available):
    """Run repricing with custom pass-through percentages."""
    ip_factor = 1 + (bps / 10000.0) * (ip_pct / 100.0)
    op_factor = 1 + (bps / 10000.0) * (op_pct / 100.0)

    if _session_available:
        try:
            from utils.data_cache import get_session as _gs
            result = _gs().sql(f"CALL ACTUARIAL_DEMO.GOLD.REPRICE_CONTRACT({bps}, '{state}', 'ALL')").collect()
            if result:
                raw = result[0][0]
                if isinstance(raw, str):
                    data = json.loads(raw)
                elif isinstance(raw, dict):
                    data = raw
                else:
                    data = json.loads(str(raw))
                # Re-apply custom pass-through rates on top of category data
                if ip_pct != 100 or op_pct != 50 or scope != "All Services":
                    data = _adjust_passthrough(data, bps, ip_pct, op_pct, scope)
                return data
            return None
        except Exception as e:
            st.warning(f"Stored procedure error: {e}. Using demo mode.")
            return None

    # Demo mode
    np.random.seed(abs(hash((state, bps))) % 2**31)
    n_claims = np.random.randint(40000, 80000)
    current_paid = np.random.uniform(150e6, 250e6)
    current_allowed = current_paid * 1.15
    premium = current_paid / np.random.uniform(0.86, 0.92)

    categories = ['INPATIENT', 'OUTPATIENT_PROFESSIONAL', 'OUTPATIENT_FACILITY',
                  'BEHAVIORAL_HEALTH', 'EMERGENCY', 'OTHER']
    cat_pcts = [0.35, 0.25, 0.15, 0.12, 0.08, 0.05]
    inpatient_cats = {'INPATIENT'}
    outpatient_cats = {'OUTPATIENT_PROFESSIONAL', 'OUTPATIENT_FACILITY', 'BEHAVIORAL_HEALTH', 'EMERGENCY', 'OTHER'}

    by_cat = []
    total_new_paid = 0
    for cat, pct in zip(categories, cat_pcts):
        cp = current_paid * pct
        if scope == "Inpatient Only" and cat not in inpatient_cats:
            factor = 1.0
        elif scope == "Outpatient Only" and cat not in outpatient_cats:
            factor = 1.0
        elif cat in inpatient_cats:
            factor = ip_factor
        else:
            factor = op_factor
        rp = cp * factor
        total_new_paid += rp
        by_cat.append({
            'service_category': cat, 'current_paid': round(cp, 2),
            'repriced_paid': round(rp, 2), 'savings': round(cp - rp, 2),
            'claim_count': int(n_claims * pct)
        })

    current_mlr = current_paid / premium
    new_mlr = total_new_paid / premium
    savings = current_paid - total_new_paid

    months = pd.date_range(end=pd.Timestamp.today(), periods=12, freq='MS')
    monthly = []
    for m in months:
        mp = current_paid / 12 * np.random.uniform(0.9, 1.1)
        rp = mp * (total_new_paid / current_paid) if current_paid > 0 else mp
        monthly.append({'month': str(m.date()), 'current_paid': round(mp, 2), 'repriced_paid': round(rp, 2)})

    return {
        'target_state': state, 'basis_point_change': bps, 'bps_factor': round(1 + bps / 10000.0, 4),
        'ip_passthrough': ip_pct, 'op_passthrough': op_pct, 'scope': scope,
        'total_claims_repriced': n_claims,
        'current': {'total_paid': round(current_paid, 2), 'total_allowed': round(current_allowed, 2),
                    'total_premium': round(premium, 2), 'mlr': round(current_mlr, 4),
                    'margin': round(1 - current_mlr, 4)},
        'repriced': {'total_paid': round(total_new_paid, 2),
                     'total_allowed': round(current_allowed * (total_new_paid / current_paid), 2),
                     'total_premium': round(premium, 2), 'mlr': round(new_mlr, 4),
                     'margin': round(1 - new_mlr, 4)},
        'impact': {'total_savings': round(savings, 2),
                   'mlr_improvement': round((current_mlr - new_mlr) * 100, 2),
                   'margin_improvement': round((1 - new_mlr - (1 - current_mlr)) * 100, 2)},
        'by_category': by_cat, 'monthly_forecast': monthly
    }


def _adjust_passthrough(data, bps, ip_pct, op_pct, scope):
    """Re-calculate category-level impacts with custom pass-through rates."""
    inpatient_cats = {'INPATIENT'}
    ip_factor = 1 + (bps / 10000.0) * (ip_pct / 100.0)
    op_factor = 1 + (bps / 10000.0) * (op_pct / 100.0)
    outpatient_cats = {'OUTPATIENT_PROFESSIONAL', 'OUTPATIENT_FACILITY', 'BEHAVIORAL_HEALTH', 'EMERGENCY', 'OTHER'}

    total_new = 0
    total_current = 0
    for cat_row in data.get('by_category', []):
        cat = cat_row['service_category']
        cp = cat_row['current_paid']
        total_current += cp
        if scope == "Inpatient Only" and cat not in inpatient_cats:
            factor = 1.0
        elif scope == "Outpatient Only" and cat not in outpatient_cats:
            factor = 1.0
        elif cat in inpatient_cats:
            factor = ip_factor
        else:
            factor = op_factor
        rp = cp * factor
        cat_row['repriced_paid'] = round(rp, 2)
        cat_row['savings'] = round(cp - rp, 2)
        total_new += rp

    premium = data['current']['total_premium']
    current_mlr = data['current']['mlr']
    new_mlr = total_new / premium if premium > 0 else 0
    data['repriced']['total_paid'] = round(total_new, 2)
    data['repriced']['mlr'] = round(new_mlr, 4)
    data['repriced']['margin'] = round(1 - new_mlr, 4)
    data['impact']['total_savings'] = round(total_current - total_new, 2)
    data['impact']['mlr_improvement'] = round((current_mlr - new_mlr) * 100, 2)
    data['impact']['margin_improvement'] = round(((1 - new_mlr) - (1 - current_mlr)) * 100, 2)
    data['ip_passthrough'] = ip_pct
    data['op_passthrough'] = op_pct
    data['scope'] = scope
    return data


# ==============================================================================
# NEGOTIATION BRIEF — Full mock document
# ==============================================================================
def _load_contract_clauses(state, session_available):
    """Load contract clauses from CONTRACT_CHUNKS for the selected state."""
    clauses = []
    if session_available:
        try:
            from utils.data_cache import get_session as _gs
            rows = _gs().sql(f"""
                SELECT CHUNK_TEXT, CHUNK_INDEX
                FROM ACTUARIAL_DEMO.AGENTS.CONTRACT_CHUNKS
                WHERE STATE = '{state}'
                ORDER BY CHUNK_INDEX
                LIMIT 4
            """).collect()
            for row in rows:
                text = str(row[0])
                # Extract article title
                if text.startswith("ARTICLE"):
                    dash_pos = text.find(".")
                    title = text[:dash_pos].strip() if dash_pos > 0 else "CONTRACT CLAUSE"
                    body = text[dash_pos+1:].strip() if dash_pos > 0 else text
                else:
                    title = f"CLAUSE {row[1]}"
                    body = text
                # Truncate for display
                if len(body) > 300:
                    body = body[:297] + "..."
                clauses.append({"title": title, "text": body})
        except Exception:
            pass

    if not clauses:
        # Mock clauses for states without contract data
        clauses = [
            {"title": "ARTICLE 1 - REIMBURSEMENT METHODOLOGY",
             "text": f"Provider shall be reimbursed on an MS-DRG basis for inpatient acute care. "
                     f"Base Rate: $6,500/discharge multiplied by applicable CMS DRG weight. "
                     f"Outlier threshold: $150,000 with 80% marginal cost factor."},
            {"title": "ARTICLE 2 - RATE ESCALATORS",
             "text": f"Annual escalator: lesser of 3.5% or CMS Market Basket Index + 0.5%. "
                     f"Behavioral health per diem subject to separate 4.0% workforce adjustment. "
                     f"Interim rate review available if volume exceeds 15% above baseline."},
            {"title": "ARTICLE 3 - MOST FAVORED NATION",
             "text": f"Plan is entitled to the most favorable rate offered to any commercial payer "
                     f"in the {state} market. Provider must disclose any lower rates within 30 days "
                     f"of execution. MFN audit rights quarterly."},
        ]
    return clauses


def _brief_to_plaintext(result, state, bps, ip_pct, op_pct, clauses, bench, talking_points, today_str):
    """Convert the negotiation brief to copyable plain text."""
    import re
    cur = result['current']
    rep = result['repriced']
    imp = result['impact']

    lines = [
        "=" * 60,
        "PROVIDER CONTRACT NEGOTIATION BRIEF",
        f"{state} Provider Network | {today_str} | CONFIDENTIAL",
        "=" * 60,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"Proposed adjustment: {abs(bps)} bps {'reduction' if bps < 0 else 'increase'}",
        f"Estimated annual impact: ${abs(imp['total_savings'])/1e6:,.1f}M",
        f"MLR change: {cur['mlr']:.1%} -> {rep['mlr']:.1%} ({imp['mlr_improvement']:+.1f} ppts)",
        f"Claims repriced: {result.get('total_claims_repriced', 0):,}",
        f"Pass-through: Inpatient {ip_pct}% / Outpatient {op_pct}%",
        "",
        "CONTRACT CONTEXT",
        "-" * 40,
    ]
    for clause in clauses:
        lines.append(f"{clause['title']}")
        lines.append(f"  {clause['text']}")
        lines.append("")

    lines.append("FINANCIAL IMPACT BY CATEGORY")
    lines.append("-" * 40)
    for row in result.get('by_category', []):
        cat = row['service_category'].replace('_', ' ').title()
        lines.append(f"  {cat}: Current ${row['current_paid']/1e6:,.1f}M -> "
                     f"Repriced ${row['repriced_paid']/1e6:,.1f}M "
                     f"(Savings: ${row['savings']/1e6:,.1f}M)")

    lines.extend([
        "",
        "MARKET BENCHMARKS",
        "-" * 40,
        f"  Regional Avg Base Rate: ${bench['avg_ip_base']:,}",
        f"  Plan Percentile Rank: {bench['percentile']}",
        f"  Regional Avg MLR: {bench['regional_avg_mlr']:.0%}",
        f"  Cost Trend (YoY): {bench['trend']}",
        "",
        "RECOMMENDED NEGOTIATION POSITION",
        "-" * 40,
    ])
    for i, point in enumerate(talking_points):
        clean = re.sub(r'<[^>]+>', '', point)
        lines.append(f"  {i+1}. {clean}")

    lines.extend([
        "",
        "-" * 60,
        f"Generated by Snowflake Actuarial Command Center | {today_str}",
        "Source: Governed Semantic View (ACTUARIAL_FINANCIAL_TRUTH)",
    ])

    return "\n".join(lines)


def _render_negotiation_brief(result, state, bps, ip_pct, op_pct, scope, session_available):
    """Render a complete mock negotiation brief with contract clauses and recommendations."""
    import streamlit.components.v1 as components

    cur = result['current']
    rep = result['repriced']
    imp = result['impact']
    by_cat = result.get('by_category', [])
    today_str = datetime.date.today().strftime('%B %d, %Y')

    # Try to load real contract clauses for the selected state
    contract_clauses = _load_contract_clauses(state, session_available)

    # Build category impact rows
    cat_rows_html = ""
    for row in by_cat:
        cat_name = row['service_category'].replace('_', ' ').title()
        sav = row['savings']
        sav_color = "#4ECDC4" if sav > 0 else "#FF6B6B"
        cat_rows_html += f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(136,146,176,0.2);color:#ccd6f6;">{cat_name}</td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(136,146,176,0.2);color:#ccd6f6;text-align:right;">
                ${row['current_paid']/1e6:,.1f}M</td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(136,146,176,0.2);color:#ccd6f6;text-align:right;">
                ${row['repriced_paid']/1e6:,.1f}M</td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(136,146,176,0.2);text-align:right;">
                <span style="color:{sav_color};font-weight:600;">${sav/1e6:,.1f}M</span></td>
            <td style="padding:8px 12px;border-bottom:1px solid rgba(136,146,176,0.2);color:#8892b0;text-align:right;">
                {row['claim_count']:,}</td>
        </tr>"""

    # Contract clause section
    if contract_clauses:
        clauses_html = ""
        for clause in contract_clauses:
            clauses_html += f"""
            <div style="background:rgba(17,34,64,0.4);border-left:3px solid #667eea;
                        padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin-bottom:0.75rem;">
                <p style="color:#667eea;font-size:0.75rem;font-weight:600;margin:0 0 0.25rem 0;
                          letter-spacing:1px;text-transform:uppercase;">
                    {clause['title']}</p>
                <p style="color:#ccd6f6;font-size:0.82rem;margin:0;line-height:1.5;">
                    {clause['text']}</p>
            </div>"""
    else:
        clauses_html = """
        <div style="background:rgba(17,34,64,0.4);padding:0.75rem 1rem;border-radius:8px;">
            <p style="color:#8892b0;font-size:0.85rem;margin:0;">
                No contract data indexed for this state. In production, Cortex Search would
                retrieve relevant clauses from the provider agreement repository.</p>
        </div>"""

    # Market benchmarks (mock)
    state_benchmarks = {
        'TX': {'avg_ip_base': 6800, 'percentile': '62nd', 'regional_avg_mlr': 0.87, 'trend': '+3.2%'},
        'MN': {'avg_ip_base': 7200, 'percentile': '71st', 'regional_avg_mlr': 0.84, 'trend': '+2.8%'},
        'FL': {'avg_ip_base': 6500, 'percentile': '55th', 'regional_avg_mlr': 0.89, 'trend': '+3.5%'},
        'CA': {'avg_ip_base': 8100, 'percentile': '78th', 'regional_avg_mlr': 0.86, 'trend': '+3.0%'},
    }
    bench = state_benchmarks.get(state, state_benchmarks['TX'])

    # Negotiation talking points
    if bps < 0:
        posture = "rate reduction"
        talking_points = [
            f"Current reimbursement rates position the plan at the <strong>{bench['percentile']} percentile</strong> "
            f"of regional payers, above the median — providing leverage for a downward adjustment.",
            f"A <strong>{abs(bps)} bps reduction</strong> would generate <strong>${imp['total_savings']/1e6:,.1f}M "
            f"in annual savings</strong> while maintaining competitive positioning for provider retention.",
            f"The proposed adjustment improves MLR by <strong>{imp['mlr_improvement']:+.1f} percentage points</strong>, "
            f"moving closer to ACA compliance targets and reducing rebate risk.",
            f"Regional medical cost trend is running at <strong>{bench['trend']} YoY</strong> — the proposed "
            f"adjustment partially offsets trend while preserving the provider relationship.",
            "Recommend structuring as a 2-year agreement with annual escalator tied to CMS Market Basket "
            "Index to provide cost predictability for both parties."
        ]
    else:
        posture = "rate increase"
        talking_points = [
            f"Provider retention analysis indicates risk of network disruption without a rate adjustment. "
            f"Current rates position the plan at the <strong>{bench['percentile']} percentile</strong> regionally.",
            f"A controlled <strong>{abs(bps)} bps increase</strong> costs <strong>"
            f"${abs(imp['total_savings'])/1e6:,.1f}M annually</strong> but secures network adequacy "
            f"in a tightening labor market.",
            f"MLR impact of <strong>{imp['mlr_improvement']:+.1f} ppts</strong> remains within "
            f"acceptable bounds relative to the regional average of {bench['regional_avg_mlr']:.0%}.",
            "Recommend tying the increase to quality performance incentives to ensure value alignment.",
            "Structure as a multi-year agreement with step-down escalators to contain long-term exposure."
        ]

    talking_html = ""
    for i, point in enumerate(talking_points):
        talking_html += f"""
        <div style="display:flex;gap:0.75rem;margin-bottom:0.75rem;">
            <div style="background:rgba(41,181,232,0.15);border-radius:50%;width:28px;height:28px;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">
                <span style="color:#29B5E8;font-weight:700;font-size:0.8rem;">{i+1}</span>
            </div>
            <p style="color:#ccd6f6;font-size:0.85rem;margin:0;line-height:1.5;">{point}</p>
        </div>"""

    # Full brief HTML
    savings_color = "#4ECDC4" if imp['total_savings'] > 0 else "#FF6B6B"
    brief_html = f"""
    <div style="background:linear-gradient(180deg,rgba(10,25,47,0.95) 0%,rgba(17,34,64,0.9) 100%);
                border:1px solid rgba(41,181,232,0.3);border-radius:16px;padding:2rem;margin:0.5rem 0;">

        <!-- Header -->
        <div style="text-align:center;border-bottom:2px solid rgba(41,181,232,0.3);padding-bottom:1.5rem;
                    margin-bottom:1.5rem;">
            <div style="font-size:0.7rem;color:#29B5E8;letter-spacing:3px;font-weight:600;
                        margin-bottom:0.5rem;">SNOWFLAKE AI DATA CLOUD</div>
            <h2 style="color:#ccd6f6;margin:0 0 0.25rem 0;font-size:1.5rem;border:none;">
                Provider Contract Negotiation Brief</h2>
            <p style="color:#8892b0;font-size:0.85rem;margin:0;">
                {state} Provider Network &middot; {today_str} &middot; CONFIDENTIAL</p>
        </div>

        <!-- Executive Summary -->
        <div style="margin-bottom:1.5rem;">
            <h3 style="color:#29B5E8;font-size:1rem;border:none;margin:0 0 0.75rem 0;
                       letter-spacing:1px;">EXECUTIVE SUMMARY</h3>
            <p style="color:#ccd6f6;font-size:0.9rem;line-height:1.6;margin:0;">
                This brief analyzes the financial impact of a <strong>{abs(bps)} basis point {posture}</strong>
                for the {state} provider network. The proposed adjustment would
                {'save' if bps < 0 else 'cost'} an estimated
                <strong>${abs(imp['total_savings'])/1e6:,.1f}M annually</strong>,
                moving the Health Plan Co.l Loss Ratio from {cur['mlr']:.1%} to {rep['mlr']:.1%}
                ({imp['mlr_improvement']:+.1f} percentage points).
                The analysis covers {result.get('total_claims_repriced', 0):,} claims with
                inpatient pass-through at {ip_pct}% and outpatient at {op_pct}%.</p>
        </div>

        <!-- Contract Context -->
        <div style="margin-bottom:1.5rem;">
            <h3 style="color:#667eea;font-size:1rem;border:none;margin:0 0 0.75rem 0;
                       letter-spacing:1px;">CONTRACT CONTEXT</h3>
            <p style="color:#8892b0;font-size:0.8rem;margin:0 0 0.75rem 0;">
                Retrieved from Cortex Search &middot; AGENTS.CONTRACT_SEARCH_SERVICE</p>
            {clauses_html}
        </div>

        <!-- Financial Impact -->
        <div style="margin-bottom:1.5rem;">
            <h3 style="color:#4ECDC4;font-size:1rem;border:none;margin:0 0 0.75rem 0;
                       letter-spacing:1px;">FINANCIAL IMPACT ANALYSIS</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:1rem;">
                <thead>
                    <tr style="border-bottom:2px solid rgba(41,181,232,0.3);">
                        <th style="padding:8px 12px;text-align:left;color:#29B5E8;font-size:0.75rem;
                                   letter-spacing:1px;">CATEGORY</th>
                        <th style="padding:8px 12px;text-align:right;color:#29B5E8;font-size:0.75rem;
                                   letter-spacing:1px;">CURRENT</th>
                        <th style="padding:8px 12px;text-align:right;color:#29B5E8;font-size:0.75rem;
                                   letter-spacing:1px;">REPRICED</th>
                        <th style="padding:8px 12px;text-align:right;color:#29B5E8;font-size:0.75rem;
                                   letter-spacing:1px;">SAVINGS</th>
                        <th style="padding:8px 12px;text-align:right;color:#29B5E8;font-size:0.75rem;
                                   letter-spacing:1px;">CLAIMS</th>
                    </tr>
                </thead>
                <tbody>
                    {cat_rows_html}
                    <tr style="border-top:2px solid rgba(41,181,232,0.3);font-weight:700;">
                        <td style="padding:10px 12px;color:#ccd6f6;">TOTAL</td>
                        <td style="padding:10px 12px;color:#ccd6f6;text-align:right;">
                            ${cur['total_paid']/1e6:,.1f}M</td>
                        <td style="padding:10px 12px;color:#ccd6f6;text-align:right;">
                            ${rep['total_paid']/1e6:,.1f}M</td>
                        <td style="padding:10px 12px;text-align:right;">
                            <span style="color:{savings_color};font-weight:700;">
                            ${imp['total_savings']/1e6:,.1f}M</span></td>
                        <td style="padding:10px 12px;color:#8892b0;text-align:right;">
                            {result.get('total_claims_repriced', 0):,}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Market Benchmarks -->
        <div style="margin-bottom:1.5rem;">
            <h3 style="color:#FFB74D;font-size:1rem;border:none;margin:0 0 0.75rem 0;
                       letter-spacing:1px;">MARKET BENCHMARK COMPARISON</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1rem;">
                <div style="background:rgba(17,34,64,0.5);padding:1rem;border-radius:10px;text-align:center;">
                    <p style="color:#8892b0;font-size:0.7rem;letter-spacing:1px;margin:0 0 0.25rem 0;">
                        REGIONAL AVG BASE RATE</p>
                    <p style="color:#FFB74D;font-size:1.3rem;font-weight:700;margin:0;">
                        ${bench['avg_ip_base']:,}</p>
                </div>
                <div style="background:rgba(17,34,64,0.5);padding:1rem;border-radius:10px;text-align:center;">
                    <p style="color:#8892b0;font-size:0.7rem;letter-spacing:1px;margin:0 0 0.25rem 0;">
                        PLAN PERCENTILE RANK</p>
                    <p style="color:#FFB74D;font-size:1.3rem;font-weight:700;margin:0;">
                        {bench['percentile']}</p>
                </div>
                <div style="background:rgba(17,34,64,0.5);padding:1rem;border-radius:10px;text-align:center;">
                    <p style="color:#8892b0;font-size:0.7rem;letter-spacing:1px;margin:0 0 0.25rem 0;">
                        REGIONAL AVG MLR</p>
                    <p style="color:#FFB74D;font-size:1.3rem;font-weight:700;margin:0;">
                        {bench['regional_avg_mlr']:.0%}</p>
                </div>
                <div style="background:rgba(17,34,64,0.5);padding:1rem;border-radius:10px;text-align:center;">
                    <p style="color:#8892b0;font-size:0.7rem;letter-spacing:1px;margin:0 0 0.25rem 0;">
                        COST TREND (YoY)</p>
                    <p style="color:#FFB74D;font-size:1.3rem;font-weight:700;margin:0;">
                        {bench['trend']}</p>
                </div>
            </div>
        </div>

        <!-- Recommended Negotiation Position -->
        <div style="margin-bottom:1.5rem;">
            <h3 style="color:#10b981;font-size:1rem;border:none;margin:0 0 0.75rem 0;
                       letter-spacing:1px;">RECOMMENDED NEGOTIATION POSITION</h3>
            {talking_html}
        </div>

        <!-- Footer -->
        <div style="border-top:1px solid rgba(136,146,176,0.2);padding-top:1rem;margin-top:1rem;">
            <p style="color:#8892b0;font-size:0.75rem;margin:0;line-height:1.6;">
                <strong>Data Governance:</strong> All financial metrics sourced from Semantic View
                ACTUARIAL_FINANCIAL_TRUTH. Contract clauses retrieved via Cortex Search
                (AGENTS.CONTRACT_SEARCH_SERVICE). Market benchmarks are illustrative and based on
                regional rate surveys.<br>
                <strong>Methodology:</strong> MS-DRG inpatient claims receive {ip_pct}% of the
                {abs(bps)} bps adjustment. Outpatient/professional claims receive {op_pct}%
                pass-through. Member cost-sharing held constant.<br>
                <em>Generated by Snowflake Actuarial Command Center &middot; {today_str}</em>
            </p>
        </div>
    </div>
    """

    with st.expander("Negotiation Brief", expanded=True):
        st.markdown(brief_html, unsafe_allow_html=True)

        # Copy brief as plain text
        brief_text = _brief_to_plaintext(result, state, bps, ip_pct, op_pct,
                                          contract_clauses, bench, talking_points, today_str)
        bcol1, bcol2 = st.columns([1, 4])
        with bcol1:
            if st.button("Copy Brief", key="copy_nego_brief", use_container_width=True):
                escaped = brief_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                components.html(f"""
                <script>
                    navigator.clipboard.writeText(`{escaped}`);
                </script>
                """, height=0)
                st.success("Brief copied to clipboard")


# ==============================================================================
# SCENARIO MANAGEMENT (up to 3 saved)
# ==============================================================================
if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = []

SCENARIO_LABELS = ["Scenario A", "Scenario B", "Scenario C"]
SCENARIO_COLORS = ["#29B5E8", "#00D4AA", "#667eea"]

result = run_repricing(basis_points, target_state, ip_passthrough, op_passthrough,
                       service_scope, session_available)

if result and 'error' not in result:
    current = result['current']
    repriced = result['repriced']
    impact = result['impact']

    # ==================================================================
    # BEFORE / AFTER KPIs
    # ==================================================================
    st.markdown("### Before vs. After")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.6])
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #FF6B6B;">
            <p class="metric-label">CURRENT MLR</p>
            <p class="metric-value">{current['mlr']:.1%}</p>
            <p style="color: #8892b0; font-size: 0.8rem;">Paid: ${current['total_paid']/1e6:,.1f}M</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid #4ECDC4;">
            <p class="metric-label">REPRICED MLR</p>
            <p class="metric-value" style="background: linear-gradient(135deg, #4ECDC4 0%, #29B5E8 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{repriced['mlr']:.1%}</p>
            <p style="color: #8892b0; font-size: 0.8rem;">Paid: ${repriced['total_paid']/1e6:,.1f}M</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        savings_color = '#4ECDC4' if impact['total_savings'] > 0 else '#FF6B6B'
        st.markdown(f"""
        <div class="metric-card" style="border-top: 3px solid {savings_color};">
            <p class="metric-label">PROJECTED SAVINGS</p>
            <p class="metric-value" style="background: {savings_color};
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                ${impact['total_savings']/1e6:,.1f}M
            </p>
            <p style="color: #8892b0; font-size: 0.8rem;">
                MLR: {impact['mlr_improvement']:+.1f} ppts | Margin: {impact['margin_improvement']:+.1f} ppts
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        # Save scenario button
        n_saved = len(st.session_state.saved_scenarios)
        st.markdown(f"""
        <div style="text-align:center;padding-top:0.5rem;">
            <p style="color:#8892b0;font-size:0.7rem;letter-spacing:1px;margin-bottom:0.25rem;">
                SCENARIOS</p>
            <p style="color:#ccd6f6;font-size:1.5rem;font-weight:700;margin:0;">
                {n_saved}/3</p>
        </div>
        """, unsafe_allow_html=True)
        if n_saved < 3:
            if st.button("Save Scenario", key="save_scenario", use_container_width=True,
                          type="primary"):
                label = SCENARIO_LABELS[n_saved]
                scenario = {
                    'label': label,
                    'state': target_state,
                    'bps': basis_points,
                    'ip_pct': ip_passthrough,
                    'op_pct': op_passthrough,
                    'scope': service_scope,
                    'result': result
                }
                st.session_state.saved_scenarios.append(scenario)
                st.rerun()
        else:
            st.caption("Max 3 saved")
        if n_saved > 0:
            if st.button("Clear All", key="clear_scenarios", use_container_width=True):
                st.session_state.saved_scenarios = []
                st.rerun()

    # ==================================================================
    # ACTION BAR
    # ==================================================================
    actions = render_action_bar([
        {"label": "Email Scenario", "icon": "\u2709", "callback_key": "email_scenario"},
        {"label": "Export Savings", "icon": "\u2B07", "callback_key": "export_savings"},
        {"label": "Negotiation Brief", "icon": "\u2696", "callback_key": "nego_brief"},
    ], key_prefix="reprice_actions")

    # --- Email handler (scenario-aware) ---
    if actions.get("email_scenario"):
        # Build body including all saved scenarios
        body_lines = [f"Contract Repricing Scenario Analysis:\n"]
        insight_items = []

        all_scenarios = list(st.session_state.saved_scenarios)
        # Include current if not already saved
        current_params = (target_state, basis_points, ip_passthrough, op_passthrough, service_scope)
        already_saved = any(
            (s['state'], s['bps'], s['ip_pct'], s['op_pct'], s['scope']) == current_params
            for s in all_scenarios
        )
        if not already_saved:
            all_scenarios.append({
                'label': 'Current (unsaved)',
                'state': target_state, 'bps': basis_points,
                'ip_pct': ip_passthrough, 'op_pct': op_passthrough,
                'scope': service_scope, 'result': result
            })

        for sc in all_scenarios:
            r = sc['result']
            body_lines.append(f"{sc['label']} — {sc['state']} {sc['bps']:+d} bps "
                              f"(IP {sc['ip_pct']}% / OP {sc['op_pct']}%):")
            body_lines.append(f"  - Current MLR: {r['current']['mlr']:.1%}  |  "
                              f"Repriced MLR: {r['repriced']['mlr']:.1%}")
            body_lines.append(f"  - Savings: ${r['impact']['total_savings']/1e6:,.1f}M  |  "
                              f"MLR improvement: {r['impact']['mlr_improvement']:+.1f} ppts")
            body_lines.append("")
            insight_items.append({
                "label": sc['label'],
                "value": f"${r['impact']['total_savings']/1e6:,.1f}M savings ({sc['state']} {sc['bps']:+d}bps)",
                "checked": True
            })

        body_lines.append("Methodology: Inpatient (configurable pass-through), "
                          "Outpatient (configurable pass-through)")

        render_email_composer(
            subject=f"Contract Repricing Analysis — {len(all_scenarios)} scenario(s) | "
                    f"{target_state} {basis_points:+d} bps",
            body_markdown="\n".join(body_lines),
            insights=insight_items,
            page_context="a contract repricing scenario comparison from the Actuarial Command Center",
            key_prefix="reprice_email"
        )

    # --- Export handler (scenario-aware) ---
    if actions.get("export_savings"):
        all_scenarios = list(st.session_state.saved_scenarios)
        current_params = (target_state, basis_points, ip_passthrough, op_passthrough, service_scope)
        already_saved = any(
            (s['state'], s['bps'], s['ip_pct'], s['op_pct'], s['scope']) == current_params
            for s in all_scenarios
        )
        if not already_saved:
            all_scenarios.append({
                'label': 'Current', 'state': target_state, 'bps': basis_points,
                'ip_pct': ip_passthrough, 'op_pct': op_passthrough,
                'scope': service_scope, 'result': result
            })

        rows = []
        for sc in all_scenarios:
            r = sc['result']
            for cat_row in r['by_category']:
                rows.append({
                    'Scenario': sc['label'],
                    'State': sc['state'],
                    'BPS': sc['bps'],
                    'IP_Passthrough': f"{sc['ip_pct']}%",
                    'OP_Passthrough': f"{sc['op_pct']}%",
                    **cat_row
                })
        export_df = pd.DataFrame(rows)
        render_export_buttons(export_df, f"Repricing_Scenarios_{datetime.date.today().isoformat()}",
                              key_prefix="reprice_export")

    # --- Negotiation Brief (full mock) ---
    if actions.get("nego_brief"):
        _render_negotiation_brief(result, target_state, basis_points,
                                  ip_passthrough, op_passthrough, service_scope,
                                  session_available)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==================================================================
    # SCENARIO COMPARISON (if any saved)
    # ==================================================================
    if st.session_state.saved_scenarios:
        st.markdown("### Scenario Comparison")
        saved = st.session_state.saved_scenarios

        # KPI comparison cards
        scen_cols = st.columns(len(saved))
        for i, sc in enumerate(saved):
            r = sc['result']
            color = SCENARIO_COLORS[i]
            with scen_cols[i]:
                st.markdown(f"""
                <div class="metric-card" style="border-top: 3px solid {color};">
                    <p class="metric-label" style="color:{color};font-weight:700;">
                        {sc['label']}</p>
                    <p style="color:#ccd6f6;font-size:0.8rem;margin:0.25rem 0;">
                        {sc['state']} &middot; {sc['bps']:+d} bps &middot;
                        IP {sc['ip_pct']}% / OP {sc['op_pct']}%</p>
                    <p class="metric-value">${r['impact']['total_savings']/1e6:,.1f}M</p>
                    <p style="color: #8892b0; font-size: 0.8rem;">
                        MLR: {r['current']['mlr']:.1%} &rarr; {r['repriced']['mlr']:.1%}
                        ({r['impact']['mlr_improvement']:+.1f} ppts)</p>
                </div>
                """, unsafe_allow_html=True)

        # Comparison chart
        fig_comp = go.Figure()
        for i, sc in enumerate(saved):
            r = sc['result']
            by_cat = pd.DataFrame(r['by_category'])
            fig_comp.add_trace(go.Bar(
                x=by_cat['service_category'].str.replace('_', ' ').str.title(),
                y=by_cat['savings'],
                name=f"{sc['label']} ({sc['state']} {sc['bps']:+d}bps)",
                marker_color=SCENARIO_COLORS[i], opacity=0.85
            ))
        fig_comp.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='group', yaxis_title='Savings ($)', height=380,
            margin=dict(l=40, r=20, t=20, b=80), xaxis_tickangle=-30,
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            title='Savings Comparison by Service Category'
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    # ==================================================================
    # TABS — Category Impact, Monthly Forecast, Details
    # ==================================================================
    tab1, tab2, tab3 = st.tabs(["Category Impact", "Monthly Forecast", "Details"])

    with tab1:
        st.markdown("### Savings by Service Category")
        by_cat = pd.DataFrame(result['by_category'])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=by_cat['service_category'].str.replace('_', ' ').str.title(),
            y=by_cat['current_paid'], name='Current Paid',
            marker_color='#FF6B6B', opacity=0.7
        ))
        fig.add_trace(go.Bar(
            x=by_cat['service_category'].str.replace('_', ' ').str.title(),
            y=by_cat['repriced_paid'], name='Repriced Paid',
            marker_color='#4ECDC4', opacity=0.9
        ))
        fig.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            barmode='group', yaxis_title='Dollars ($)', height=400,
            margin=dict(l=40, r=20, t=20, b=80), xaxis_tickangle=-30,
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure(go.Waterfall(
            x=by_cat['service_category'].str.replace('_', ' ').str.title(),
            y=by_cat['savings'],
            text=[f"${s/1e6:,.1f}M" for s in by_cat['savings']],
            textposition='outside',
            connector=dict(line=dict(color='rgba(41,181,232,0.3)')),
            increasing=dict(marker=dict(color='#4ECDC4')),
            decreasing=dict(marker=dict(color='#FF6B6B'))
        ))
        fig2.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Savings ($)', height=350, title='Savings Waterfall',
            margin=dict(l=40, r=20, t=40, b=80), xaxis_tickangle=-30
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.markdown("### Monthly Paid Trend: Current vs Repriced")
        monthly = pd.DataFrame(result['monthly_forecast'])
        monthly['month'] = pd.to_datetime(monthly['month'])

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=monthly['month'], y=monthly['current_paid'],
            mode='lines+markers', name='Current',
            line=dict(color='#FF6B6B', width=2, dash='dash'), marker=dict(size=6)
        ))
        fig3.add_trace(go.Scatter(
            x=monthly['month'], y=monthly['repriced_paid'],
            mode='lines+markers', name='Repriced',
            line=dict(color='#4ECDC4', width=3), marker=dict(size=8)
        ))
        fig3.add_trace(go.Scatter(
            x=pd.concat([monthly['month'], monthly['month'][::-1]]),
            y=pd.concat([monthly['current_paid'], monthly['repriced_paid'][::-1]]),
            fill='toself', fillcolor='rgba(78,205,196,0.1)',
            line=dict(width=0), showlegend=False, hoverinfo='skip'
        ))
        fig3.update_layout(
            template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Monthly Paid ($)', height=400,
            margin=dict(l=40, r=20, t=20, b=40),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.markdown("### Repricing Details")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Current State**")
            st.json(current)
        with col2:
            st.markdown("**Repriced State**")
            st.json(repriced)

        st.markdown("**Impact Summary**")
        st.json(impact)

        st.markdown("**By Service Category**")
        st.dataframe(pd.DataFrame(result['by_category']), use_container_width=True, hide_index=True)

    # Technical SQL
    if technical:
        render_code_block(f"""-- Contract Repricing Stored Procedure Call
CALL GOLD.REPRICE_CONTRACT(
    {basis_points},    -- basis_point_change
    '{target_state}',  -- target_state
    'ALL'              -- provider_system_filter
);

-- Custom pass-through applied in Streamlit layer:
-- Inpatient factor:  1 + ({basis_points}/10000) * ({ip_passthrough}/100) = {1 + (basis_points/10000)*(ip_passthrough/100):.4f}
-- Outpatient factor: 1 + ({basis_points}/10000) * ({op_passthrough}/100) = {1 + (basis_points/10000)*(op_passthrough/100):.4f}""",
                          "Repricing Stored Procedure")

else:
    st.error("Repricing engine returned no results. Check that the stored procedure is deployed.")
