# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# SHARED STYLES - Modern Dark Theme for Actuarial Command Center
# Adapted from clinical registry design system
# ==============================================================================

SHARED_CSS = """
<style>
    /* Snowflake Brand Font - Lato */
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap');

    /* Theme colors - Actuarial Command Center */
    :root {
        --primary-color: #29B5E8;
        --secondary-color: #667eea;
        --accent-color: #00D4AA;
        --warning-color: #FF6B6B;
        --success-color: #4ECDC4;
        --processing-color: #FFB74D;
        --background-dark: #0E1117;
        --card-background: #1E2130;
        --text-light: #FAFAFA;
        --text-muted: #8892b0;
        --text-body: #ccd6f6;
        --highlight: #64ffda;
        --sf-brand: #29B5E8;
        --sf-dark-blue: #11567F;
    }

    /* Snowflake brand font applied globally */
    .main, .main *, [data-testid="stSidebar"], [data-testid="stSidebar"] * {
        font-family: 'Lato', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'Lato', sans-serif !important;
        font-weight: 700 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hide sidebar collapse button text fallback (Material Icons ligature) */
    [data-testid="stSidebar"] button[kind="header"] {
        font-size: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="collapsedControl"] {
        font-size: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-header"],
    [data-testid="collapsedControl"] [data-testid="stBaseButton-header"] {
        font-size: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-header"] span,
    [data-testid="collapsedControl"] [data-testid="stBaseButton-header"] span {
        font-size: 0 !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-header"] svg,
    [data-testid="collapsedControl"] [data-testid="stBaseButton-header"] svg {
        visibility: visible !important;
        width: 1.5rem !important;
        height: 1.5rem !important;
    }

    /* Hide default Streamlit sidebar page navigation (we use custom nav blade) */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* POWERED BY SNOWFLAKE sidebar footer */
    [data-testid="stSidebar"] > div:first-child::after {
        content: "POWERED BY SNOWFLAKE";
        position: absolute;
        bottom: 25px;
        left: 0;
        right: 0;
        text-align: center;
        color: #29B5E8;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1.2px;
        font-family: 'Lato', sans-serif;
        padding: 8px 16px;
        background: rgba(41, 181, 232, 0.08);
        border-radius: 12px;
        margin: 0 20px;
        border: 1px solid rgba(41, 181, 232, 0.2);
    }

    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    /* Custom header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Section headers */
    h2, h3 {
        color: #FAFAFA;
        border-bottom: 2px solid rgba(41, 181, 232, 0.3);
        padding-bottom: 0.5rem;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 48px rgba(41, 181, 232, 0.2);
    }

    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #29B5E8 0%, #00D4AA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }

    .metric-label {
        color: #8892b0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }

    .metric-delta-positive {
        color: #4ECDC4;
        font-size: 0.8rem;
    }

    .metric-delta-negative {
        color: #FF6B6B;
        font-size: 0.8rem;
    }

    /* Override Streamlit default metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    [data-testid="metric-container"] label {
        color: #8892b0 !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #29B5E8 !important;
        font-weight: 700;
    }

    /* Alert cards */
    .alert-card {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
        transition: all 0.3s ease;
    }

    .alert-card:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }

    .alert-critical { border-left-color: #FF6B6B; }
    .alert-warning { border-left-color: #FFB74D; }
    .alert-info { border-left-color: #29B5E8; }
    .alert-success { border-left-color: #4ECDC4; }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-on-target { background: rgba(78,205,196,0.2); color: #4ECDC4; }
    .status-warning { background: rgba(255,183,77,0.2); color: #FFB74D; }
    .status-at-risk { background: rgba(255,107,107,0.2); color: #FF6B6B; }
    .status-info { background: rgba(41,181,232,0.2); color: #29B5E8; }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    }

    [data-testid="stSidebar"] * {
        color: #FAFAFA !important;
    }

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #8892b0 !important;
    }

    /* DataFrames */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #8892b0;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #29B5E8 0%, #667eea 100%);
        color: white;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #29B5E8 0%, #00D4AA 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.25rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 24px rgba(41,181,232,0.4);
    }

    /* Info/Warning boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        background: rgba(41, 181, 232, 0.1);
    }

    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, rgba(41,181,232,0.5), transparent);
        margin: 1.5rem 0;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-in {
        animation: fadeIn 0.5s ease-out forwards;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }

    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 5px rgba(41,181,232,0.2); }
        50% { box-shadow: 0 0 20px rgba(41,181,232,0.4); }
    }

    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }

    .glow-pulse { animation: glowPulse 3s ease-in-out infinite; }
    .slide-in { animation: slideInRight 0.4s ease-out forwards; }

    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #29B5E8; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #667eea; }

    /* Pipeline cards */
    .pipeline-step {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
    }

    .pipeline-step-number {
        background: linear-gradient(135deg, #29B5E8 0%, #667eea 100%);
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        margin-right: 1rem;
        color: white;
    }

    /* Action bar styling */
    .stButton > button {
        font-size: 0.8rem;
        padding: 0.5rem 0.75rem;
    }

    /* Radio button audience toggle styling */
    div[data-testid="stRadio"] > div {
        background: rgba(17,34,64,0.5);
        border-radius: 25px;
        padding: 4px;
        border: 1px solid rgba(41,181,232,0.2);
    }

    div[data-testid="stRadio"] > div > label {
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.8rem;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #112240 0%, #1a365d 100%);
        border: 1px solid rgba(41,181,232,0.3);
        color: #29B5E8;
        font-size: 0.75rem;
    }

    .stDownloadButton > button:hover {
        border-color: #29B5E8;
        box-shadow: 0 4px 12px rgba(41,181,232,0.2);
    }

    /* Code blocks */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid rgba(41,181,232,0.15);
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(17,34,64,0.4);
        border-radius: 8px;
        border: 1px solid rgba(41,181,232,0.15);
    }

    /* Quick action card */
    .quick-action {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid rgba(41,181,232,0.15);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .quick-action:hover {
        border-color: rgba(41,181,232,0.5);
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(41,181,232,0.15);
    }

    /* Mission control KPI tile */
    .kpi-tile {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }

    .kpi-tile::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #29B5E8, #00D4AA);
    }

    .kpi-tile:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(41,181,232,0.2);
    }

    /* ================================================================
       CLICKABLE TILES — entire tile is the click target
       ================================================================ */

    /* Navigation tiles (st.page_link styled as tile) */
    div[data-testid="stPageLink-nav"] > a,
    .clickable-tile-link > div > a {
        text-decoration: none !important;
    }

    /* Make page_link containers look like tiles */
    .tile-nav .stPageLink > a {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%) !important;
        border-radius: 14px !important;
        padding: 1.25rem !important;
        border: 1px solid rgba(41,181,232,0.15) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        display: block !important;
        text-decoration: none !important;
        color: #FAFAFA !important;
        min-height: 140px !important;
    }

    .tile-nav .stPageLink > a:hover {
        border-color: rgba(41,181,232,0.5) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(41,181,232,0.15) !important;
    }

    /* Action tiles (st.button styled as tile) */
    .tile-action .stButton > button {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%) !important;
        border-radius: 14px !important;
        padding: 1.25rem !important;
        border: 1px solid rgba(41,181,232,0.15) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        text-align: left !important;
        min-height: 140px !important;
        white-space: pre-wrap !important;
        line-height: 1.5 !important;
        color: #FAFAFA !important;
        font-size: 0.85rem !important;
    }

    .tile-action .stButton > button:hover {
        border-color: rgba(41,181,232,0.5) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(41,181,232,0.15) !important;
    }

    /* Demo workflow step tiles */
    .tile-step .stPageLink > a {
        background: linear-gradient(135deg, #112240 0%, #1a365d 100%) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(41,181,232,0.2) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        display: block !important;
        text-decoration: none !important;
        color: #FAFAFA !important;
        min-height: 180px !important;
    }

    .tile-step .stPageLink > a:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 25px rgba(41,181,232,0.2) !important;
    }

    /* Step tile color variants */
    .tile-step-1 .stPageLink > a {
        background: linear-gradient(135deg, #112240 0%, #1a365d 100%) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
    }
    .tile-step-1 .stPageLink > a:hover { border-color: rgba(59, 130, 246, 0.6) !important; }

    .tile-step-2 .stPageLink > a {
        background: linear-gradient(135deg, #112240 0%, #2d1b4e 100%) !important;
        border-color: rgba(139, 92, 246, 0.3) !important;
    }
    .tile-step-2 .stPageLink > a:hover { border-color: rgba(139, 92, 246, 0.6) !important; }

    .tile-step-3 .stPageLink > a {
        background: linear-gradient(135deg, #112240 0%, #134e4a 100%) !important;
        border-color: rgba(16, 185, 129, 0.3) !important;
    }
    .tile-step-3 .stPageLink > a:hover { border-color: rgba(16, 185, 129, 0.6) !important; }

    .tile-step-4 .stPageLink > a {
        background: linear-gradient(135deg, #112240 0%, #451a03 100%) !important;
        border-color: rgba(245, 158, 11, 0.3) !important;
    }
    .tile-step-4 .stPageLink > a:hover { border-color: rgba(245, 158, 11, 0.6) !important; }

    /* ================================================================
       ARCHITECTURE DIAGRAMS — flow nodes, arrows, layers
       ================================================================ */

    .arch-layer {
        background: linear-gradient(145deg, #1a1f35 0%, #0d1117 100%);
        border-radius: 14px;
        padding: 1.25rem;
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
    }
    .arch-layer:hover {
        border-color: rgba(41,181,232,0.4);
        box-shadow: 0 6px 24px rgba(41,181,232,0.1);
    }
    .arch-layer-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Schema color coding */
    .arch-raw { border-left: 4px solid #3b82f6; }
    .arch-raw .arch-layer-title { color: #3b82f6; }
    .arch-silver { border-left: 4px solid #8b5cf6; }
    .arch-silver .arch-layer-title { color: #8b5cf6; }
    .arch-gold { border-left: 4px solid #f59e0b; }
    .arch-gold .arch-layer-title { color: #f59e0b; }
    .arch-analytics { border-left: 4px solid #10b981; }
    .arch-analytics .arch-layer-title { color: #10b981; }
    .arch-agents { border-left: 4px solid #ef4444; }
    .arch-agents .arch-layer-title { color: #ef4444; }
    .arch-semantic { border-left: 4px solid #00D4AA; }
    .arch-semantic .arch-layer-title { color: #00D4AA; }
    .arch-streamlit { border-left: 4px solid #29B5E8; }
    .arch-streamlit .arch-layer-title { color: #29B5E8; }

    .arch-object {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin: 0.35rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .arch-object:hover {
        background: rgba(41,181,232,0.05);
        border-color: rgba(41,181,232,0.25);
    }
    .arch-obj-name {
        color: #ccd6f6;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'Courier New', monospace;
    }
    .arch-obj-meta {
        color: #8892b0;
        font-size: 0.7rem;
    }
    .arch-obj-type {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .type-table { background: rgba(59,130,246,0.15); color: #60a5fa; }
    .type-dt { background: rgba(139,92,246,0.15); color: #a78bfa; }
    .type-view { background: rgba(16,185,129,0.15); color: #34d399; }
    .type-semantic { background: rgba(0,212,170,0.15); color: #00D4AA; }
    .type-search { background: rgba(239,68,68,0.15); color: #f87171; }
    .type-proc { background: rgba(245,158,11,0.15); color: #fbbf24; }
    .type-streamlit { background: rgba(41,181,232,0.15); color: #29B5E8; }

    /* Flow arrow between layers */
    .arch-flow-arrow {
        text-align: center;
        color: #64ffda;
        font-size: 1.4rem;
        padding: 0.3rem 0;
        opacity: 0.7;
    }

    /* Module architecture cards */
    .arch-module-card {
        background: linear-gradient(145deg, #112240 0%, #0a192f 100%);
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid rgba(41,181,232,0.15);
        margin-bottom: 0.5rem;
    }
    .arch-module-title {
        color: #29B5E8;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .arch-module-flow {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        flex-wrap: wrap;
        padding: 0.5rem 0;
    }
    .arch-flow-node {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 6px;
        padding: 0.35rem 0.6rem;
        color: #ccd6f6;
        font-size: 0.7rem;
        font-family: 'Courier New', monospace;
        white-space: nowrap;
    }
    .arch-flow-connector {
        color: #64ffda;
        font-size: 0.9rem;
    }

    /* ================================================================
       EMAIL COMPOSER — professional email drafting UI
       ================================================================ */

    .email-composer {
        background: linear-gradient(145deg, #112240 0%, #0a192f 100%);
        border: 1px solid rgba(139,92,246,0.25);
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .email-composer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(139,92,246,0.2);
    }
    .email-composer-badge {
        background: linear-gradient(135deg, rgba(139,92,246,0.15) 0%, rgba(41,181,232,0.08) 100%);
        padding: 0.4rem 0.75rem;
        border-radius: 8px;
        border: 1px solid rgba(139,92,246,0.25);
        color: #8b5cf6;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .email-field-label {
        color: #8892b0;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .email-insights-section {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(41,181,232,0.15);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .email-insights-title {
        color: #29B5E8;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .email-action-bar {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 0.75rem;
        border-top: 1px solid rgba(255,255,255,0.06);
    }
</style>
"""


def apply_styles():
    """Apply shared styles to a Streamlit page."""
    import streamlit as st
    st.markdown(SHARED_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str, icon: str = ""):
    """Render a styled page header."""
    import streamlit as st
    st.markdown(f"""
    <div class="main-header animate-in">
        <h1>{icon} {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(value: str, label: str, delta: str = "", delta_type: str = "positive"):
    """Render a styled metric card. Returns HTML string."""
    delta_class = f"metric-delta-{delta_type}"
    return f"""
    <div class="metric-card">
        <p class="metric-value">{value}</p>
        <p class="metric-label">{label}</p>
        {f'<p class="{delta_class}">{delta}</p>' if delta else ''}
    </div>
    """


def render_alert_card(title: str, message: str, severity: str = "info"):
    """Render an alert card. severity: critical, warning, info, success."""
    icon = {"critical": "!!!", "warning": "!", "info": "i", "success": "OK"}
    return f"""
    <div class="alert-card alert-{severity}">
        <strong style="color: #FAFAFA;">[{icon.get(severity, 'i')}] {title}</strong>
        <p style="color: #8892b0; margin: 0.25rem 0 0 0; font-size: 0.9rem;">{message}</p>
    </div>
    """


def render_status_badge(status: str, text: str):
    """Render a status badge."""
    return f'<span class="status-badge status-{status}">{text}</span>'


def render_sidebar_branding():
    """Render Snowflake-branded sidebar with logo, header, and app title."""
    import streamlit as st
    import os

    # Snowflake logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snowflake_bug.png")
        try:
            st.image(logo_path, width=60)
        except Exception:
            st.markdown("""
            <div style="text-align: center; margin: 20px 0;">
                <div style="font-size: 48px; color: #29B5E8;
                     text-shadow: 0 2px 4px rgba(41, 181, 232, 0.3);">&#10052;</div>
            </div>
            """, unsafe_allow_html=True)

    # SNOWFLAKE / SOLUTION ENGINEERING header
    st.markdown("""
    <div style="text-align: center; padding: 15px 0 25px 0;
                position: relative; z-index: 10;">
        <div style="font-size: 22px; font-weight: 700; color: #29B5E8;
                    letter-spacing: 2px; font-family: 'Lato', sans-serif;
                    margin-bottom: 8px;">
            SNOWFLAKE
        </div>
        <div style="font-size: 11px; color: #8892b0; letter-spacing: 1.5px;
                    font-weight: 500;">
            SOLUTION ENGINEERING
        </div>
        <div style="width: 60px; height: 2px; background: #29B5E8;
                    margin: 15px auto 0; border-radius: 1px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # App title
    st.markdown("""
    <div style="text-align: center; padding: 0 0 1rem 0;">
        <h2 style="background: linear-gradient(135deg, #29B5E8 0%, #00D4AA 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 1.2rem; margin: 0; border: none;">
            Actuarial Command Center
        </h2>
    </div>
    """, unsafe_allow_html=True)
