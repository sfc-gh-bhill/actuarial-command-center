# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# PAGE 8: ARCHITECTURE
# Visual architecture diagram with SVG, module data flows, and object inventory
# ==============================================================================

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Architecture | Actuarial Command Center", page_icon="❄", layout="wide")

from utils.styles import apply_styles, render_header
from utils.actions import (render_nav_blade, render_page_header_nav,
                           render_connection_status)
from utils.data_cache import get_connection

apply_styles()

# ------------------------------------------------------------------------------
# SNOWFLAKE SESSION
# ------------------------------------------------------------------------------
session, session_available = get_connection()

# ------------------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------------------
with st.sidebar:
    render_nav_blade(current_page_index=9)
    render_connection_status(session_available)

# ------------------------------------------------------------------------------
# HEADER
# ------------------------------------------------------------------------------
render_header("Architecture", "Interactive system architecture, data flows, and object inventory", "◇")

render_page_header_nav(9)

# ==============================================================================
# SECTION 1: VISUAL ARCHITECTURE DIAGRAM
# ==============================================================================
st.markdown("### System Architecture")
st.markdown('<p style="color:#8892b0;font-size:0.85rem;">Hover over any component for details. '
            'Data flows left-to-right from synthetic source tables through the medallion pipeline '
            'to consumers.</p>', unsafe_allow_html=True)

# View mode selector + zoom controls
_view_col, _zoom_col = st.columns([3, 1])

ALL_PAGES = ["Executive Summary", "Margin Forecast", "Risk Adjustment",
             "Claims Analytics", "IBNR Reserves", "Contract Repricing",
             "Trend Surveillance", "Intelligence Agent"]

with _view_col:
    view_mode = st.selectbox(
        "View Mode", ["Overview", "Detailed"] + [f"Flow: {p}" for p in ALL_PAGES],
        key="arch_view", label_visibility="collapsed"
    )
with _zoom_col:
    zoom_pct = st.slider("Zoom", 50, 150, 85, 5, key="arch_zoom", label_visibility="collapsed",
                         help="Zoom in/out on the diagram")

# Determine mode
highlight_page = None
if view_mode.startswith("Flow: "):
    highlight_page = view_mode.replace("Flow: ", "")
    detailed = True
else:
    detailed = view_mode == "Detailed"

# Build the SVG architecture diagram as an HTML component
# Layout: Sources (left) → Snowflake [ RAW | SILVER | GOLD | ANALYTICS ] → Consumers (right)
#         with AGENTS below and SEMANTIC VIEW as a cross-cutting layer

def _build_diagram_html(detailed, highlight_page=None):
    """Build the full interactive SVG architecture diagram.
    If highlight_page is set, only nodes/arrows in that page's flow are fully visible.
    """

    # Page-to-node mapping: which SVG node IDs are relevant per page
    PAGE_FLOWS = {
        "Executive Summary": {
            "nodes": {"src_members", "src_medical", "raw_members", "raw_medical",
                      "silver_member_elig", "silver_medical_claims",
                      "gold_financial_summary", "gold_semantic_view",
                      "ml_anomaly_alerts", "cons_app", "page_Executive Summary"},
            "zones": {"zone_raw", "zone_silver", "zone_gold", "zone_ml"},
        },
        "Margin Forecast": {
            "nodes": {"src_members", "src_medical", "raw_members", "raw_medical",
                      "silver_member_elig", "silver_medical_claims",
                      "gold_financial_summary", "gold_semantic_view",
                      "cons_app", "page_Margin Forecast"},
            "zones": {"zone_raw", "zone_silver", "zone_gold"},
        },
        "Risk Adjustment": {
            "nodes": {"src_members", "src_hcc_ref", "raw_members", "raw_hcc_ref",
                      "silver_member_elig",
                      "gold_risk_score_summary", "gold_semantic_view",
                      "cons_app", "page_Risk Adjustment"},
            "zones": {"zone_raw", "zone_silver", "zone_gold"},
        },
        "Claims Analytics": {
            "nodes": {"src_medical", "raw_medical",
                      "silver_medical_claims",
                      "gold_financial_summary", "gold_semantic_view",
                      "cons_app", "page_Claims Analytics"},
            "zones": {"zone_raw", "zone_silver", "zone_gold"},
        },
        "IBNR Reserves": {
            "nodes": {"src_medical", "src_lag_triangle", "raw_medical", "raw_lag_triangle",
                      "silver_medical_claims",
                      "gold_ibnr_development", "gold_semantic_view",
                      "ml_ibnr_forecast", "cons_app", "page_IBNR Reserves"},
            "zones": {"zone_raw", "zone_silver", "zone_gold", "zone_ml"},
        },
        "Contract Repricing": {
            "nodes": {"src_medical", "raw_medical",
                      "silver_medical_claims",
                      "gold_financial_summary", "gold_semantic_view", "gold_reprice_proc",
                      "cons_app", "page_Contract Repricing"},
            "zones": {"zone_raw", "zone_silver", "zone_gold"},
        },
        "Trend Surveillance": {
            "nodes": {"src_medical", "raw_medical",
                      "silver_medical_claims",
                      "gold_trend_surveillance", "gold_semantic_view",
                      "ml_cost_trend_forecast", "ml_anomaly_alerts", "ml_trend_timeseries",
                      "cons_app", "page_Trend Surveillance"},
            "zones": {"zone_raw", "zone_silver", "zone_gold", "zone_ml"},
        },
        "Intelligence Agent": {
            "nodes": {"gold_semantic_view",
                      "agent_contract_chunks", "agent_cortex_search", "agent_intelligence_agent",
                      "cons_app", "page_Intelligence Agent"},
            "zones": {"zone_gold", "zone_agents"},
        },
    }

    flow = PAGE_FLOWS.get(highlight_page) if highlight_page else None
    flow_nodes = flow["nodes"] if flow else None
    flow_zones = flow["zones"] if flow else None

    # Dimensions
    W = 1200
    H = 820 if detailed else 700

    # Column x-positions (center of each column)
    SRC_X = 100       # Source data column
    RAW_X = 310       # RAW/Bronze column
    SILVER_X = 500    # SILVER column
    GOLD_X = 690      # GOLD column
    ML_X = 880        # ANALYTICS/ML column
    CONS_X = 1080     # Consumer column

    # Colors
    C_SRC = "#60a5fa"     # Blue - source tables
    C_RAW = "#3b82f6"     # Blue - raw
    C_SILVER = "#8b5cf6"  # Purple - silver
    C_GOLD = "#f59e0b"    # Amber - gold
    C_SEMANTIC = "#00D4AA" # Teal - semantic view
    C_ML = "#10b981"      # Green - analytics/ML
    C_AGENT = "#ef4444"   # Red - agents
    C_APP = "#29B5E8"     # Snowflake blue - streamlit
    C_PROC = "#fbbf24"    # Yellow - procedures
    C_BG = "#0a192f"      # Dark background
    C_BORDER = "rgba(41,181,232,0.25)"
    C_TEXT = "#ccd6f6"
    C_DIM = "#8892b0"
    C_ARROW = "#64ffda"

    # --- Helper functions ---
    # Opacity helper for flow highlighting
    def _node_opacity(nid):
        if not flow_nodes:
            return 1.0
        return 1.0 if nid in flow_nodes else 0.12

    def _zone_opacity(zid):
        if not flow_zones:
            return 0.8
        return 0.8 if zid in flow_zones else 0.08

    def _arrow_opacity(src_id, dst_id):
        """Arrow is visible if both endpoints are in the flow, or if no flow filter."""
        if not flow_nodes:
            return 0.6
        return 0.7 if (src_id in flow_nodes and dst_id in flow_nodes) else 0.06

    def node_box(x, y, w, h, label, sublabel, color, node_id="", detail_text="", icon=""):
        """Render a node box with hover tooltip."""
        rx = 8
        opacity = _node_opacity(node_id)
        tooltip = f"<title>{detail_text}</title>" if detail_text else ""
        icon_html = f'<text x="{x+12}" y="{y+h/2+1}" font-size="13" fill="{color}" dominant-baseline="middle">{icon}</text>' if icon else ""
        text_x = x + (22 if icon else 10)
        sub_y = y + h/2 + 12 if sublabel else 0
        sublabel_html = f'<text x="{text_x}" y="{sub_y}" font-size="9" fill="{C_DIM}" font-family="Lato, sans-serif">{sublabel}</text>' if sublabel else ""
        glow = ' filter="url(#glow)"' if (flow_nodes and node_id in flow_nodes) else ""
        return f'''
        <g class="node" id="{node_id}" opacity="{opacity}">
            {tooltip}
            <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"
                  fill="rgba(26,31,53,0.9)" stroke="{color}" stroke-width="1.5"
                  class="node-rect" data-color="{color}"{glow}/>
            {icon_html}
            <text x="{text_x}" y="{y+h/2 - (4 if sublabel else 0)}" font-size="11"
                  fill="{C_TEXT}" font-weight="600" font-family="Lato, sans-serif"
                  dominant-baseline="middle">{label}</text>
            {sublabel_html}
        </g>'''

    def zone_box(x, y, w, h, label, color, sublabel="", zone_id=""):
        """Render a background zone/lane."""
        opacity = _zone_opacity(zone_id)
        sub_html = f'<text x="{x+w-10}" y="{y+22}" font-size="9" fill="{C_DIM}" text-anchor="end" font-family="Lato, sans-serif">{sublabel}</text>' if sublabel else ""
        return f'''
        <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"
              fill="rgba(17,34,64,0.35)" stroke="{color}" stroke-width="1" stroke-dasharray="4,3"
              opacity="{opacity}"/>
        <text x="{x+12}" y="{y+22}" font-size="11" fill="{color}" font-weight="700"
              font-family="Lato, sans-serif" letter-spacing="1.5" opacity="{opacity}">{label}</text>
        {sub_html}'''

    def arrow(x1, y1, x2, y2, color=C_ARROW, dashed=False, label="", src_id="", dst_id=""):
        """Draw an arrow between two points."""
        dash = 'stroke-dasharray="5,3"' if dashed else ""
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        opacity = _arrow_opacity(src_id, dst_id)
        label_html = f'<text x="{mid_x}" y="{mid_y - 6}" font-size="8" fill="{C_DIM}" text-anchor="middle" font-family="Lato, sans-serif">{label}</text>' if label else ""
        return f'''
        <line x1="{x1}" y1="{y1}" x2="{x2-8}" y2="{y2}"
              stroke="{color}" stroke-width="1.5" {dash} opacity="{opacity}"
              marker-end="url(#arrowhead)"/>
        {label_html}'''

    def arrow_curved(x1, y1, x2, y2, color=C_ARROW, label="", curve_dir=1, src_id="", dst_id=""):
        """Draw a curved arrow (for cross-layer connections)."""
        ctrl_x = (x1 + x2) / 2
        ctrl_y = (y1 + y2) / 2 + (40 * curve_dir)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2 + (15 * curve_dir)
        opacity = _arrow_opacity(src_id, dst_id)
        label_html = f'<text x="{mid_x}" y="{mid_y}" font-size="8" fill="{C_DIM}" text-anchor="middle" font-family="Lato, sans-serif">{label}</text>' if label else ""
        return f'''
        <path d="M{x1},{y1} Q{ctrl_x},{ctrl_y} {x2},{y2}"
              stroke="{color}" stroke-width="1.5" fill="none" opacity="{opacity}"
              marker-end="url(#arrowhead)" stroke-dasharray="5,3"/>
        {label_html}'''

    # --- Build SVG ---
    svg_parts = []

    # Defs (arrowhead marker)
    svg_parts.append(f'''
    <defs>
        <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="{C_ARROW}" opacity="0.7"/>
        </marker>
        <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
    </defs>''')

    # ==========================================
    # ZONE BACKGROUNDS
    # ==========================================
    # Main Snowflake container
    sf_x, sf_y, sf_w = 230, 30, 730
    sf_h = H - 60
    svg_parts.append(f'''
    <rect x="{sf_x}" y="{sf_y}" width="{sf_w}" height="{sf_h}" rx="16"
          fill="rgba(10,25,47,0.5)" stroke="{C_APP}" stroke-width="2" opacity="0.9"/>
    <text x="{sf_x + sf_w/2}" y="{sf_y + 18}" font-size="10" fill="{C_APP}" font-weight="700"
          text-anchor="middle" font-family="Lato, sans-serif" letter-spacing="3">
        ❄  SNOWFLAKE AI DATA CLOUD</text>''')

    # Schema lanes
    lane_y = sf_y + 30
    lane_h = sf_h - 45
    lane_w = 160

    svg_parts.append(zone_box(RAW_X - 75, lane_y, lane_w, lane_h, "RAW", C_RAW, "source tables", zone_id="zone_raw"))
    svg_parts.append(zone_box(SILVER_X - 75, lane_y, lane_w, lane_h, "SILVER", C_SILVER, "dynamic tables", zone_id="zone_silver"))
    svg_parts.append(zone_box(GOLD_X - 75, lane_y, lane_w, lane_h, "GOLD", C_GOLD, "models + truth", zone_id="zone_gold"))
    svg_parts.append(zone_box(ML_X - 75, lane_y, lane_w, lane_h, "ANALYTICS", C_ML, "Cortex ML", zone_id="zone_ml"))

    # ==========================================
    # SOURCE NODES (left side, outside Snowflake)
    # ==========================================
    src_nodes = [
        ("SYNTH_MEMBER\nELIGIBILITY", "10K rows", "Member enrollment data — APCD-CDL v3.0.1 standard", 90, "src_members"),
        ("SYNTH_MEDICAL\nCLAIMS", "433K rows", "Health Plan Co.l claims — diagnosis, procedure, paid amounts", 155, "src_medical"),
        ("SYNTH_PHARMACY\nCLAIMS", "200K rows", "Pharmacy claims — NDC, quantity, paid amounts", 220, "src_pharmacy"),
    ]
    if detailed:
        src_nodes.extend([
            ("SYNTH_CAPITATION", "164K rows", "Capitation payments — PMPM by LOB, state, month", 285, "src_capitation"),
            ("SYNTH_REBATES", "200 rows", "Pharmacy rebates — manufacturer, state", 345, "src_rebates"),
            ("CLAIMS_LAG\nTRIANGLE", "234 rows", "Historical claims run-off development data", 405, "src_lag_triangle"),
            ("HCC_REFERENCE", "12 rows", "CMS-HCC v28 risk adjustment coefficients", 465, "src_hcc_ref"),
        ])
    else:
        src_nodes.append(("+ 4 more tables", "365K rows", "Capitation, Rebates, Lag Triangle, HCC Reference", 285, "src_extra"))

    # Source group box
    src_box_h = (src_nodes[-1][3] + 55) - 65
    src_grp_opacity = 1.0 if not flow_nodes else (0.8 if any(nid in flow_nodes for _, _, _, _, nid in src_nodes) else 0.12)
    svg_parts.append(f'''
    <g opacity="{src_grp_opacity}">
    <rect x="15" y="65" width="175" height="{src_box_h}" rx="12"
          fill="rgba(59,130,246,0.06)" stroke="{C_SRC}" stroke-width="1" stroke-dasharray="4,3"/>
    <text x="102" y="82" font-size="9" fill="{C_SRC}" font-weight="700"
          text-anchor="middle" font-family="Lato, sans-serif" letter-spacing="1.5">
        SOURCE DATA</text>
    <text x="102" y="94" font-size="8" fill="{C_DIM}" text-anchor="middle"
          font-family="Lato, sans-serif">APCD-CDL v3.0.1</text>
    </g>''')

    for label, sub, tip, y, nid in src_nodes:
        opacity = _node_opacity(nid)
        lines = label.split("\n")
        if len(lines) > 1:
            glow = ' filter="url(#glow)"' if (flow_nodes and nid in flow_nodes) else ""
            svg_parts.append(f'''
            <g class="node" id="{nid}" opacity="{opacity}">
                <title>{tip}</title>
                <rect x="25" y="{y}" width="155" height="48" rx="8"
                      fill="rgba(26,31,53,0.9)" stroke="{C_SRC}" stroke-width="1.5" class="node-rect" data-color="{C_SRC}"{glow}/>
                <text x="35" y="{y+18}" font-size="10" fill="{C_TEXT}" font-weight="600" font-family="Lato, sans-serif">{lines[0]}</text>
                <text x="35" y="{y+30}" font-size="10" fill="{C_TEXT}" font-weight="600" font-family="Lato, sans-serif">{lines[1]}</text>
                <text x="35" y="{y+42}" font-size="9" fill="{C_DIM}" font-family="Lato, sans-serif">{sub}</text>
            </g>''')
        else:
            svg_parts.append(node_box(25, y, 155, 42, label, sub, C_SRC, node_id=nid, detail_text=tip))

    # ==========================================
    # RAW COLUMN (inside Snowflake)
    # ==========================================
    # In this demo, source tables live in GOLD but conceptually act as RAW
    raw_y_start = lane_y + 45
    svg_parts.append(f'''
    <text x="{RAW_X}" y="{raw_y_start - 8}" font-size="8" fill="{C_DIM}" text-anchor="middle"
          font-family="Lato, sans-serif">Ingestion Layer</text>''')

    raw_nodes_y = []
    raw_items = [
        ("Members", "10K", raw_y_start, "raw_members"),
        ("Health Plan Co.l Claims", "433K", raw_y_start + 55, "raw_medical"),
        ("Pharmacy Claims", "200K", raw_y_start + 110, "raw_pharmacy"),
    ]
    if detailed:
        raw_items.extend([
            ("Capitation", "164K", raw_y_start + 165, "raw_capitation"),
            ("Rebates", "200", raw_y_start + 220, "raw_rebates"),
            ("Lag Triangle", "234", raw_y_start + 275, "raw_lag_triangle"),
            ("HCC Ref", "12", raw_y_start + 330, "raw_hcc_ref"),
        ])
    else:
        raw_items.append(("+ 4 tables", "365K", raw_y_start + 165, "raw_extra"))

    for label, count, y, nid in raw_items:
        svg_parts.append(node_box(RAW_X - 65, y, 130, 40, label, count, C_RAW, node_id=nid))
        raw_nodes_y.append(y + 20)

    # ==========================================
    # SILVER COLUMN
    # ==========================================
    silver_y_start = lane_y + 65
    svg_parts.append(f'''
    <text x="{SILVER_X}" y="{silver_y_start - 28}" font-size="8" fill="{C_DIM}" text-anchor="middle"
          font-family="Lato, sans-serif">Cleansing &amp; Dedup</text>''')

    silver_items = [
        ("MEMBER_ELIG_CLEAN", "DT  10K", "Deduplicated, type-standardized member eligibility", silver_y_start, "silver_member_elig"),
        ("MEDICAL_CLAIMS_CLEAN", "DT  386K", "Cleansed medical claims — NULL handling, dedup", silver_y_start + 70, "silver_medical_claims"),
    ]
    silver_nodes_y = []
    for label, sub, tip, y, nid in silver_items:
        svg_parts.append(node_box(SILVER_X - 70, y, 140, 46, label, sub, C_SILVER, node_id=nid, detail_text=tip))
        silver_nodes_y.append(y + 23)

    # ==========================================
    # GOLD COLUMN
    # ==========================================
    gold_y_start = lane_y + 50
    svg_parts.append(f'''
    <text x="{GOLD_X}" y="{gold_y_start - 13}" font-size="8" fill="{C_DIM}" text-anchor="middle"
          font-family="Lato, sans-serif">Aggregation Models</text>''')

    gold_items = [
        ("FINANCIAL_SUMMARY", "DT 3.9K", "MLR, margin, cost PMPM by LOB/state/month", gold_y_start, "gold_financial_summary"),
        ("TREND_SURVEILLANCE", "DT 3.9K", "Cost trend time series for anomaly detection", gold_y_start + 60, "gold_trend_surveillance"),
        ("RISK_SCORE_SUMMARY", "DT 452", "CMS-HCC v28 risk scores by member cohort", gold_y_start + 120, "gold_risk_score_summary"),
        ("IBNR_DEVELOPMENT", "DT 234", "Chain-ladder development factors by service month", gold_y_start + 180, "gold_ibnr_development"),
    ]
    gold_nodes_y = []
    for label, sub, tip, y, nid in gold_items:
        svg_parts.append(node_box(GOLD_X - 68, y, 136, 44, label, sub, C_GOLD, node_id=nid, detail_text=tip))
        gold_nodes_y.append(y + 22)

    # Semantic View — special cross-cutting node
    sem_y = gold_y_start + 260
    sem_opacity = _node_opacity("gold_semantic_view")
    sem_glow = ' filter="url(#glow)"' if (flow_nodes and "gold_semantic_view" in flow_nodes) else ""
    svg_parts.append(f'''
    <g class="node" id="gold_semantic_view" opacity="{sem_opacity}">
        <title>Governed single source of truth — MLR, margin, IBNR, cost PMPM definitions</title>
        <rect x="{GOLD_X - 72}" y="{sem_y}" width="144" height="52" rx="10"
              fill="rgba(0,212,170,0.08)" stroke="{C_SEMANTIC}" stroke-width="2"
              class="node-rect" data-color="{C_SEMANTIC}"{sem_glow}/>
        <text x="{GOLD_X}" y="{sem_y + 18}" font-size="10" fill="{C_SEMANTIC}" font-weight="700"
              text-anchor="middle" font-family="Lato, sans-serif">SEMANTIC VIEW</text>
        <text x="{GOLD_X}" y="{sem_y + 32}" font-size="9" fill="{C_TEXT}" text-anchor="middle"
              font-family="Lato, sans-serif">ACTUARIAL_FINANCIAL</text>
        <text x="{GOLD_X}" y="{sem_y + 44}" font-size="9" fill="{C_TEXT}" text-anchor="middle"
              font-family="Lato, sans-serif">_TRUTH</text>
    </g>''')

    # Procedure node
    proc_y = sem_y + 68
    svg_parts.append(node_box(GOLD_X - 68, proc_y, 136, 42, "REPRICE_CONTRACT", "Stored Proc", C_PROC,
                              node_id="gold_reprice_proc",
                              detail_text="MS-DRG contract repricing: base rate x DRG weight + BPS adjustment"))

    # ==========================================
    # ANALYTICS / ML COLUMN
    # ==========================================
    ml_y_start = lane_y + 50
    svg_parts.append(f'''
    <text x="{ML_X}" y="{ml_y_start - 13}" font-size="8" fill="{C_DIM}" text-anchor="middle"
          font-family="Lato, sans-serif">Cortex ML Functions</text>''')

    ml_items = [
        ("COST_TREND\nFORECAST", "1.9K rows", "Cortex ML FORECAST — cost PMPM projections by cohort", ml_y_start, "ml_cost_trend_forecast"),
        ("ANOMALY_ALERTS", "2.8K rows", "Cortex ML ANOMALY_DETECTION — flagged cost spikes", ml_y_start + 70, "ml_anomaly_alerts"),
        ("IBNR_FORECAST", "24 rows", "Cortex ML FORECAST — IBNR reserve projections", ml_y_start + 140, "ml_ibnr_forecast"),
    ]
    if detailed:
        ml_items.append(("TREND_TIMESERIES", "View", "Time series view input for Cortex ML functions", ml_y_start + 210, "ml_trend_timeseries"))

    ml_nodes_y = []
    for label, sub, tip, y, nid in ml_items:
        opacity = _node_opacity(nid)
        lines = label.split("\n")
        if len(lines) > 1:
            glow = ' filter="url(#glow)"' if (flow_nodes and nid in flow_nodes) else ""
            svg_parts.append(f'''
            <g class="node" id="{nid}" opacity="{opacity}">
                <title>{tip}</title>
                <rect x="{ML_X - 68}" y="{y}" width="136" height="48" rx="8"
                      fill="rgba(26,31,53,0.9)" stroke="{C_ML}" stroke-width="1.5"
                      class="node-rect" data-color="{C_ML}"{glow}/>
                <text x="{ML_X - 56}" y="{y+17}" font-size="10" fill="{C_TEXT}" font-weight="600"
                      font-family="Lato, sans-serif">{lines[0]}</text>
                <text x="{ML_X - 56}" y="{y+29}" font-size="10" fill="{C_TEXT}" font-weight="600"
                      font-family="Lato, sans-serif">{lines[1]}</text>
                <text x="{ML_X - 56}" y="{y+42}" font-size="9" fill="{C_DIM}"
                      font-family="Lato, sans-serif">{sub}</text>
            </g>''')
        else:
            svg_parts.append(node_box(ML_X - 68, y, 136, 44, label, sub, C_ML, node_id=nid, detail_text=tip))
        ml_nodes_y.append(y + 22)

    # ==========================================
    # AGENTS ROW (bottom of Snowflake box)
    # ==========================================
    agent_y = H - 120 if detailed else H - 110
    agent_x_start = RAW_X - 40

    agent_zone_opacity = _zone_opacity("zone_agents")
    svg_parts.append(f'''
    <rect x="{agent_x_start}" y="{agent_y}" width="460" height="68" rx="10"
          fill="rgba(239,68,68,0.04)" stroke="{C_AGENT}" stroke-width="1" stroke-dasharray="4,3"
          opacity="{agent_zone_opacity}"/>
    <text x="{agent_x_start + 12}" y="{agent_y + 16}" font-size="9" fill="{C_AGENT}" font-weight="700"
          font-family="Lato, sans-serif" letter-spacing="1.5" opacity="{agent_zone_opacity}">AGENTS SCHEMA</text>''')

    # Agent nodes
    svg_parts.append(node_box(agent_x_start + 10, agent_y + 24, 130, 34,
                              "CONTRACT_CHUNKS", "9 chunks", C_AGENT,
                              node_id="agent_contract_chunks",
                              detail_text="Contract document chunks for RAG retrieval"))
    svg_parts.append(node_box(agent_x_start + 155, agent_y + 24, 140, 34,
                              "CORTEX SEARCH", "9 indexed", C_AGENT,
                              node_id="agent_cortex_search",
                              detail_text="SEARCH_PREVIEW() vector search on contract clauses"))
    svg_parts.append(node_box(agent_x_start + 310, agent_y + 24, 140, 34,
                              "INTELLIGENCE AGENT", "Procedure", C_AGENT,
                              node_id="agent_intelligence_agent",
                              detail_text="INVOKE_INTELLIGENCE_AGENT — Cortex Complete + Search + Semantic View"))

    # ==========================================
    # CONSUMER NODES (right side, outside Snowflake)
    # ==========================================
    cons_y_start = lane_y + 50

    # Streamlit App
    cons_app_opacity = _node_opacity("cons_app")
    cons_app_glow = ' filter="url(#glow)"' if (flow_nodes and "cons_app" in flow_nodes) else ""
    svg_parts.append(f'''
    <g class="node" id="cons_app" opacity="{cons_app_opacity}">
        <title>Streamlit in Snowflake — 9 analytics pages, zero data movement</title>
        <rect x="{CONS_X - 68}" y="{cons_y_start}" width="150" height="65" rx="10"
              fill="rgba(41,181,232,0.08)" stroke="{C_APP}" stroke-width="2"
              class="node-rect" data-color="{C_APP}"{cons_app_glow}/>
        <text x="{CONS_X + 7}" y="{cons_y_start + 18}" font-size="10" fill="{C_APP}" font-weight="700"
              text-anchor="middle" font-family="Lato, sans-serif">❄ STREAMLIT APP</text>
        <text x="{CONS_X + 7}" y="{cons_y_start + 33}" font-size="9" fill="{C_TEXT}" text-anchor="middle"
              font-family="Lato, sans-serif">Actuarial Command Center</text>
        <text x="{CONS_X + 7}" y="{cons_y_start + 48}" font-size="9" fill="{C_DIM}" text-anchor="middle"
              font-family="Lato, sans-serif">9 pages · SiS</text>
    </g>''')

    # Page list (detailed mode)
    if detailed:
        pages = ["Executive Summary", "Margin Forecast", "Risk Adjustment",
                 "Claims Analytics", "IBNR Reserves", "Contract Repricing",
                 "Trend Surveillance", "Intelligence Agent"]
        for i, page in enumerate(pages):
            py = cons_y_start + 80 + i * 26
            page_nid = f"page_{page}"
            page_opacity = _node_opacity(page_nid)
            is_active = (highlight_page == page)
            fill = "rgba(41,181,232,0.15)" if is_active else "rgba(41,181,232,0.05)"
            stroke = C_APP if is_active else "rgba(41,181,232,0.2)"
            sw = "2" if is_active else "1"
            text_color = C_APP if is_active else C_DIM
            glow = ' filter="url(#glow)"' if is_active else ""
            svg_parts.append(f'''
            <g class="node" id="{page_nid}" opacity="{page_opacity}">
                <rect x="{CONS_X - 58}" y="{py}" width="130" height="22" rx="4"
                      fill="{fill}" stroke="{stroke}" stroke-width="{sw}"
                      class="node-rect" data-color="{C_APP}"{glow}/>
                <text x="{CONS_X + 7}" y="{py + 14}" font-size="8" fill="{text_color}" text-anchor="middle"
                      font-family="Lato, sans-serif" font-weight="{"700" if is_active else "400"}">{page}</text>
            </g>''')
    else:
        # Cortex ML badge
        svg_parts.append(f'''
        <g class="node">
            <title>Cortex ML FORECAST + ANOMALY_DETECTION for predictive analytics</title>
            <rect x="{CONS_X - 60}" y="{cons_y_start + 90}" width="134" height="48" rx="8"
                  fill="rgba(16,185,129,0.08)" stroke="{C_ML}" stroke-width="1.5"
                  class="node-rect" data-color="{C_ML}"/>
            <text x="{CONS_X + 7}" y="{cons_y_start + 108}" font-size="10" fill="{C_ML}" font-weight="600"
                  text-anchor="middle" font-family="Lato, sans-serif">Cortex ML</text>
            <text x="{CONS_X + 7}" y="{cons_y_start + 122}" font-size="8" fill="{C_DIM}" text-anchor="middle"
                  font-family="Lato, sans-serif">FORECAST + ANOMALY</text>
        </g>''')

        # Cortex Agent badge
        svg_parts.append(f'''
        <g class="node">
            <title>Cortex Agent — RAG + LLM + Semantic View for natural language Q&amp;A</title>
            <rect x="{CONS_X - 60}" y="{cons_y_start + 155}" width="134" height="48" rx="8"
                  fill="rgba(239,68,68,0.08)" stroke="{C_AGENT}" stroke-width="1.5"
                  class="node-rect" data-color="{C_AGENT}"/>
            <text x="{CONS_X + 7}" y="{cons_y_start + 173}" font-size="10" fill="{C_AGENT}" font-weight="600"
                  text-anchor="middle" font-family="Lato, sans-serif">Cortex Agent</text>
            <text x="{CONS_X + 7}" y="{cons_y_start + 187}" font-size="8" fill="{C_DIM}" text-anchor="middle"
                  font-family="Lato, sans-serif">RAG + LLM + SV</text>
        </g>''')

        # Negotiation Brief badge
        svg_parts.append(f'''
        <g class="node">
            <title>Contract repricing simulation with multi-scenario comparison</title>
            <rect x="{CONS_X - 60}" y="{cons_y_start + 220}" width="134" height="48" rx="8"
                  fill="rgba(245,158,11,0.08)" stroke="{C_PROC}" stroke-width="1.5"
                  class="node-rect" data-color="{C_PROC}"/>
            <text x="{CONS_X + 7}" y="{cons_y_start + 238}" font-size="10" fill="{C_PROC}" font-weight="600"
                  text-anchor="middle" font-family="Lato, sans-serif">Repricing Engine</text>
            <text x="{CONS_X + 7}" y="{cons_y_start + 252}" font-size="8" fill="{C_DIM}" text-anchor="middle"
                  font-family="Lato, sans-serif">MS-DRG + Scenarios</text>
        </g>''')

    # ==========================================
    # ARROWS — Data Flow Connections
    # ==========================================

    # Sources → RAW (left to RAW column)
    for i, (_, _, _, sy, src_nid) in enumerate(src_nodes):
        target_y_idx = min(i, len(raw_items) - 1)
        ry = raw_items[target_y_idx][2] + 20
        dst_nid = raw_items[target_y_idx][3]
        svg_parts.append(arrow(180, sy + 20, RAW_X - 65, ry, color=C_SRC, label="",
                               src_id=src_nid, dst_id=dst_nid))

    # RAW → SILVER
    # Members → MEMBER_ELIG_CLEAN
    svg_parts.append(arrow(RAW_X + 65, raw_nodes_y[0], SILVER_X - 70, silver_nodes_y[0], label="dedup",
                           src_id="raw_members", dst_id="silver_member_elig"))
    # Health Plan Co.l Claims → MEDICAL_CLAIMS_CLEAN
    svg_parts.append(arrow(RAW_X + 65, raw_nodes_y[1], SILVER_X - 70, silver_nodes_y[1], label="cleanse",
                           src_id="raw_medical", dst_id="silver_medical_claims"))

    # SILVER → GOLD
    svg_parts.append(arrow(SILVER_X + 70, silver_nodes_y[0], GOLD_X - 68, gold_nodes_y[0], label="aggregate",
                           src_id="silver_member_elig", dst_id="gold_financial_summary"))
    svg_parts.append(arrow(SILVER_X + 70, silver_nodes_y[0], GOLD_X - 68, gold_nodes_y[2], color=C_SILVER, dashed=True,
                           src_id="silver_member_elig", dst_id="gold_risk_score_summary"))
    svg_parts.append(arrow(SILVER_X + 70, silver_nodes_y[1], GOLD_X - 68, gold_nodes_y[0], color=C_SILVER, dashed=True,
                           src_id="silver_medical_claims", dst_id="gold_financial_summary"))
    svg_parts.append(arrow(SILVER_X + 70, silver_nodes_y[1], GOLD_X - 68, gold_nodes_y[1], label="time series",
                           src_id="silver_medical_claims", dst_id="gold_trend_surveillance"))
    svg_parts.append(arrow(SILVER_X + 70, silver_nodes_y[1], GOLD_X - 68, gold_nodes_y[3], color=C_SILVER, dashed=True,
                           src_id="silver_medical_claims", dst_id="gold_ibnr_development"))

    # GOLD → Semantic View
    gold_nids = ["gold_financial_summary", "gold_trend_surveillance", "gold_risk_score_summary", "gold_ibnr_development"]
    for gi, gy in enumerate(gold_nodes_y):
        svg_parts.append(arrow(GOLD_X, gy + 22, GOLD_X, sem_y, color=C_SEMANTIC, dashed=True,
                               src_id=gold_nids[gi], dst_id="gold_semantic_view"))

    # GOLD → ANALYTICS (ML)
    svg_parts.append(arrow(GOLD_X + 68, gold_nodes_y[0], ML_X - 68, ml_nodes_y[0], label="FORECAST",
                           src_id="gold_financial_summary", dst_id="ml_cost_trend_forecast"))
    svg_parts.append(arrow(GOLD_X + 68, gold_nodes_y[1], ML_X - 68, ml_nodes_y[1], label="ANOMALY",
                           src_id="gold_trend_surveillance", dst_id="ml_anomaly_alerts"))
    svg_parts.append(arrow(GOLD_X + 68, gold_nodes_y[3], ML_X - 68, ml_nodes_y[2], label="FORECAST",
                           src_id="gold_ibnr_development", dst_id="ml_ibnr_forecast"))

    # Semantic View → Streamlit App
    svg_parts.append(arrow(GOLD_X + 72, sem_y + 26, CONS_X - 68, cons_y_start + 32, color=C_SEMANTIC, label="governed",
                           src_id="gold_semantic_view", dst_id="cons_app"))

    # ML → Streamlit App
    if not detailed:
        svg_parts.append(arrow(ML_X + 68, ml_nodes_y[0], CONS_X - 60, cons_y_start + 114, color=C_ML,
                               src_id="ml_cost_trend_forecast", dst_id="cons_app"))
        svg_parts.append(arrow(ML_X + 68, ml_nodes_y[1], CONS_X - 60, cons_y_start + 114, color=C_ML, dashed=True,
                               src_id="ml_anomaly_alerts", dst_id="cons_app"))
    else:
        svg_parts.append(arrow(ML_X + 68, ml_nodes_y[0], CONS_X - 58, cons_y_start + 32, color=C_ML, dashed=True,
                               src_id="ml_cost_trend_forecast", dst_id="cons_app"))

    # Proc → Streamlit App
    if not detailed:
        svg_parts.append(arrow(GOLD_X + 68, proc_y + 21, CONS_X - 60, cons_y_start + 262, color=C_PROC,
                               src_id="gold_reprice_proc", dst_id="cons_app"))

    # Agents → Semantic View (upward connection)
    svg_parts.append(arrow_curved(agent_x_start + 450, agent_y + 41,
                                  GOLD_X + 72, sem_y + 40,
                                  color=C_AGENT, label="queries SV", curve_dir=1,
                                  src_id="agent_intelligence_agent", dst_id="gold_semantic_view"))

    # Agents → Streamlit
    if not detailed:
        svg_parts.append(arrow(agent_x_start + 450, agent_y + 20,
                               CONS_X - 60, cons_y_start + 179, color=C_AGENT, dashed=True,
                               src_id="agent_intelligence_agent", dst_id="cons_app"))

    # RAW direct → GOLD (for tables that skip SILVER like lag triangle, HCC ref)
    if detailed and len(raw_nodes_y) > 4:
        svg_parts.append(arrow_curved(RAW_X + 65, raw_nodes_y[5],
                                      GOLD_X - 68, gold_nodes_y[3],
                                      color=C_RAW, label="direct", curve_dir=-1,
                                      src_id="raw_lag_triangle", dst_id="gold_ibnr_development"))
        svg_parts.append(arrow_curved(RAW_X + 65, raw_nodes_y[6],
                                      GOLD_X - 68, gold_nodes_y[2],
                                      color=C_RAW, label="direct", curve_dir=-1,
                                      src_id="raw_hcc_ref", dst_id="gold_risk_score_summary"))

    # ==========================================
    # LEGEND
    # ==========================================
    leg_y = H - 40
    legend_items = [
        (C_SRC, "Source Table"), (C_SILVER, "Dynamic Table"), (C_GOLD, "Gold Model"),
        (C_SEMANTIC, "Semantic View"), (C_ML, "Cortex ML"), (C_AGENT, "Cortex Agent"),
        (C_APP, "Streamlit App"), (C_PROC, "Procedure"),
    ]
    leg_x = 30
    for color, label in legend_items:
        svg_parts.append(f'''
        <rect x="{leg_x}" y="{leg_y}" width="10" height="10" rx="2" fill="{color}" opacity="0.8"/>
        <text x="{leg_x + 14}" y="{leg_y + 9}" font-size="8" fill="{C_DIM}"
              font-family="Lato, sans-serif">{label}</text>''')
        leg_x += len(label) * 6 + 30

    svg_content = "\n".join(svg_parts)

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            overflow: auto;
        }}
        .diagram-container {{
            transform-origin: top left;
        }}
        svg {{
            display: block;
            width: 100%;
            height: auto;
        }}
        .node-rect {{
            transition: all 0.25s ease;
            cursor: pointer;
        }}
        .node:hover .node-rect {{
            filter: url(#glow);
            stroke-width: 2.5;
            fill: rgba(41, 55, 95, 0.95);
        }}
        .node:hover text {{
            fill: #e6f1ff;
        }}
    </style>
    </head>
    <body>
    <div class="diagram-container">
    <svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
         style="font-family: Lato, -apple-system, sans-serif;">
        {svg_content}
    </svg>
    </div>
    </body>
    </html>
    '''


diagram_html = _build_diagram_html(detailed, highlight_page=highlight_page)
# Scale diagram height by zoom
base_height = 860 if detailed else 740
diagram_height = int(base_height * zoom_pct / 100)
components.html(diagram_html, height=diagram_height, scrolling=(zoom_pct > 100))


st.divider()

# ==============================================================================
# SECTION 2: MODULE DATA FLOWS
# ==============================================================================
st.markdown("### Module Data Flows")
st.markdown('<p style="color:#8892b0;font-size:0.85rem;">Each module\'s data lineage — '
            'from source tables through transforms to the dashboard page.</p>', unsafe_allow_html=True)


def flow_node(text):
    return f'<span class="arch-flow-node">{text}</span>'


def flow_arrow():
    return '<span class="arch-flow-connector">\u2192</span>'


def render_flow(nodes):
    """Render a horizontal flow: node -> node -> node"""
    parts = []
    for i, n in enumerate(nodes):
        parts.append(flow_node(n))
        if i < len(nodes) - 1:
            parts.append(flow_arrow())
    return f'<div class="arch-module-flow">{"".join(parts)}</div>'


# --- Executive Summary ---
with st.expander("Executive Summary", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["FINANCIAL_SUMMARY (DT)", "Semantic View", "LOB Aggregation", "MLR KPIs"])}
        {render_flow(["ANOMALY_ALERTS", "Severity Filter", "Alert Cards"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> MLR by LOB, operating margin, state heatmap, anomaly count<br>
            <strong style="color:#ccd6f6;">Cached functions:</strong> compute_lob_summary, compute_monthly_mlr, compute_state_summary
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Margin Forecast ---
with st.expander("Margin Forecast", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["FINANCIAL_SUMMARY (DT)", "LOB + State Filter", "Monthly Trend", "Year-End Projection"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Annualized margin, MLR trend by LOB, premium vs paid<br>
            <strong style="color:#ccd6f6;">Cached functions:</strong> compute_lob_summary, compute_monthly_lob_mlr
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Risk Adjustment ---
with st.expander("Risk Adjustment", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["RISK_SCORE_SUMMARY (DT)", "CMS-HCC v28 Coefficients", "RAF Score Distribution"])}
        {render_flow(["HCC_REFERENCE", "Category Mapping", "Revenue Impact"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Average RAF score, HCC prevalence, revenue impact per HCC<br>
            <strong style="color:#ccd6f6;">Model:</strong> CMS-HCC v28 — Diabetes (0.302), CHF (0.431), COPD (0.328)
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Claims Analytics ---
with st.expander("Claims Analytics", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["MEDICAL_CLAIMS_CLEAN (DT)", "Category + State Filter", "Cost Distribution"])}
        {render_flow(["FINANCIAL_SUMMARY (DT)", "Category Aggregation", "Lag Analysis"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Paid PMPM by category, claims volume, processing lag<br>
            <strong style="color:#ccd6f6;">Cached functions:</strong> compute_category_summary, compute_lag_by_category
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- IBNR Reserves ---
with st.expander("IBNR Reserves", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["CLAIMS_LAG_TRIANGLE", "IBNR_DEVELOPMENT (DT)", "Completion Factors", "Run-Off Triangle"])}
        {render_flow(["IBNR_FORECAST", "Cortex ML FORECAST", "Reserve Projections"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Ultimate loss, IBNR reserve, completion factors by lag<br>
            <strong style="color:#ccd6f6;">Method:</strong> Chain-ladder with Cortex ML augmentation
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Contract Repricing ---
with st.expander("Contract Repricing", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["User Input (bps, state)", "REPRICE_CONTRACT proc", "MS-DRG Weight Lookup", "Margin Impact"])}
        {render_flow(["FINANCIAL_SUMMARY (DT)", "Baseline Comparison", "Delta Analysis"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Base rate x DRG weight, repriced total, margin delta<br>
            <strong style="color:#ccd6f6;">Procedure:</strong> REPRICE_CONTRACT(basis_points, state) RETURNS VARIANT
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Trend Surveillance ---
with st.expander("Trend Surveillance", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["TREND_SURVEILLANCE (DT)", "TREND_TIMESERIES (View)", "Cortex ML ANOMALY_DETECTION"])}
        {render_flow(["ANOMALY_ALERTS", "Severity Ranking", "Alert Dashboard"])}
        {render_flow(["COST_TREND_FORECAST", "Cortex ML FORECAST", "Projection Charts"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Key metrics:</strong> Cost PMPM anomalies, forecast confidence intervals<br>
            <strong style="color:#ccd6f6;">ML:</strong> Cortex ANOMALY_DETECTION + FORECAST on time series by LOB x State x Category
        </div>
    </div>
    ''', unsafe_allow_html=True)

# --- Intelligence Agent ---
with st.expander("Intelligence Agent", expanded=False):
    st.markdown(f'''
    <div class="arch-module-card">
        <div class="arch-module-title">Data Flow</div>
        {render_flow(["User Question", "INVOKE_INTELLIGENCE_AGENT proc", "Cortex Complete (claude-3-5-sonnet)"])}
        {render_flow(["CONTRACT_SEARCH_SERVICE", "SEARCH_PREVIEW()", "RAG Context"])}
        {render_flow(["ACTUARIAL_FINANCIAL_TRUTH", "Semantic View Query", "Governed Data Context"])}
        <div style="color:#8892b0;font-size:0.75rem;margin-top:0.5rem;">
            <strong style="color:#ccd6f6;">Capabilities:</strong> Natural language Q&A, contract lookup, governed metric retrieval<br>
            <strong style="color:#ccd6f6;">Stack:</strong> Cortex Search (RAG) + Cortex Complete (LLM) + Semantic View (truth)
        </div>
    </div>
    ''', unsafe_allow_html=True)

st.divider()

# ==============================================================================
# SECTION 3: DATA OBJECT INVENTORY
# ==============================================================================
st.markdown("### Data Object Inventory")
st.markdown('<p style="color:#8892b0;font-size:0.85rem;">Complete inventory of all deployed Snowflake objects '
            'in the ACTUARIAL_DEMO database.</p>', unsafe_allow_html=True)

import pandas as pd

inventory = pd.DataFrame([
    {"Schema": "GOLD", "Object": "SYNTH_MEMBER_ELIGIBILITY", "Type": "TABLE", "Rows": "10,000", "Purpose": "Member enrollment & demographics"},
    {"Schema": "GOLD", "Object": "SYNTH_MEDICAL_CLAIMS", "Type": "TABLE", "Rows": "433,155", "Purpose": "Health Plan Co.l claims (APCD-CDL)"},
    {"Schema": "GOLD", "Object": "SYNTH_PHARMACY_CLAIMS", "Type": "TABLE", "Rows": "200,000", "Purpose": "Pharmacy claims"},
    {"Schema": "GOLD", "Object": "SYNTH_CAPITATION_PAYMENTS", "Type": "TABLE", "Rows": "164,459", "Purpose": "Capitation payments"},
    {"Schema": "GOLD", "Object": "SYNTH_PHARMACY_REBATES", "Type": "TABLE", "Rows": "200", "Purpose": "Pharmacy rebates"},
    {"Schema": "GOLD", "Object": "CLAIMS_LAG_TRIANGLE", "Type": "TABLE", "Rows": "234", "Purpose": "Claims development triangle"},
    {"Schema": "GOLD", "Object": "HCC_REFERENCE", "Type": "TABLE", "Rows": "12", "Purpose": "CMS-HCC v28 coefficients"},
    {"Schema": "SILVER", "Object": "MEMBER_ELIGIBILITY_CLEAN", "Type": "DYNAMIC TABLE", "Rows": "10,000", "Purpose": "Cleansed member eligibility"},
    {"Schema": "SILVER", "Object": "MEDICAL_CLAIMS_CLEAN", "Type": "DYNAMIC TABLE", "Rows": "386,185", "Purpose": "Cleansed medical claims"},
    {"Schema": "GOLD", "Object": "FINANCIAL_SUMMARY", "Type": "DYNAMIC TABLE", "Rows": "3,924", "Purpose": "MLR, margin, cost PMPM by LOB/state/month"},
    {"Schema": "GOLD", "Object": "TREND_SURVEILLANCE", "Type": "DYNAMIC TABLE", "Rows": "3,924", "Purpose": "Trend monitoring time series"},
    {"Schema": "GOLD", "Object": "RISK_SCORE_SUMMARY", "Type": "DYNAMIC TABLE", "Rows": "452", "Purpose": "CMS-HCC risk scores by member"},
    {"Schema": "GOLD", "Object": "IBNR_DEVELOPMENT", "Type": "DYNAMIC TABLE", "Rows": "234", "Purpose": "Claims development factors"},
    {"Schema": "GOLD", "Object": "ACTUARIAL_FINANCIAL_TRUTH", "Type": "SEMANTIC VIEW", "Rows": "\u2014", "Purpose": "Governed metric definitions (MLR, margin, IBNR)"},
    {"Schema": "ANALYTICS", "Object": "TREND_TIMESERIES", "Type": "VIEW", "Rows": "\u2014", "Purpose": "Time series input for Cortex ML"},
    {"Schema": "ANALYTICS", "Object": "COST_TREND_FORECAST", "Type": "TABLE", "Rows": "1,875", "Purpose": "Cortex ML cost forecast output"},
    {"Schema": "ANALYTICS", "Object": "IBNR_FORECAST", "Type": "TABLE", "Rows": "24", "Purpose": "Cortex ML IBNR forecast output"},
    {"Schema": "ANALYTICS", "Object": "ANOMALY_ALERTS", "Type": "TABLE", "Rows": "2,777", "Purpose": "Cortex ML anomaly detection results"},
    {"Schema": "AGENTS", "Object": "CONTRACT_CHUNKS", "Type": "TABLE", "Rows": "9", "Purpose": "Contract document chunks for RAG"},
    {"Schema": "AGENTS", "Object": "CONTRACT_SEARCH_SERVICE", "Type": "CORTEX SEARCH", "Rows": "9", "Purpose": "Vector search index on contract chunks"},
    {"Schema": "AGENTS", "Object": "INVOKE_INTELLIGENCE_AGENT", "Type": "PROCEDURE", "Rows": "\u2014", "Purpose": "Cortex Agent invocation wrapper"},
    {"Schema": "GOLD", "Object": "REPRICE_CONTRACT", "Type": "PROCEDURE", "Rows": "\u2014", "Purpose": "MS-DRG contract repricing engine"},
    {"Schema": "GOLD", "Object": "ACTUARIAL_COMMAND_CENTER", "Type": "STREAMLIT", "Rows": "\u2014", "Purpose": "Streamlit in Snowflake application"},
])


# Color-code type column
def style_type(val):
    colors = {
        "TABLE": "#60a5fa", "DYNAMIC TABLE": "#a78bfa", "VIEW": "#34d399",
        "SEMANTIC VIEW": "#00D4AA", "CORTEX SEARCH": "#f87171",
        "PROCEDURE": "#fbbf24", "STREAMLIT": "#29B5E8"
    }
    color = colors.get(val, "#8892b0")
    return f"color: {color}; font-weight: 600"


styled = inventory.style
try:
    styled = styled.map(style_type, subset=["Type"])
except AttributeError:
    styled = styled.applymap(style_type, subset=["Type"])

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    height=840,
)
