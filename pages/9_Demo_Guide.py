# ==============================================================================
# PAGE 9: DEMO GUIDE
# Embedded 15-minute demo guide with download button
# ==============================================================================

import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Demo Guide | Actuarial Command Center", page_icon="❄", layout="wide")

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
    render_nav_blade(current_page_index=10)
    render_connection_status(session_available)

# ------------------------------------------------------------------------------
# HEADER
# ------------------------------------------------------------------------------
render_header("Demo Guide", "15-minute step-by-step presentation guide with talk tracks", "▤")

render_page_header_nav(10)

# ==============================================================================
# LOAD DEMO GUIDE HTML
# ==============================================================================
guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "DEMO_GUIDE.html")

try:
    with open(guide_path, "r", encoding="utf-8") as f:
        guide_html = f.read()
    guide_loaded = True
except FileNotFoundError:
    guide_html = ""
    guide_loaded = False

# ==============================================================================
# DOWNLOAD BUTTON
# ==============================================================================
if guide_loaded:
    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(41,181,232,0.08), rgba(0,212,170,0.08));
                border:1px solid rgba(41,181,232,0.2); border-radius:12px; padding:1.25rem 1.5rem;
                margin-bottom:1.5rem;">
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.5rem;">
            <span style="font-size:1.5rem;">📋</span>
            <span style="font-size:1.1rem; font-weight:700; color:#29B5E8;">
                15-Minute Executive Demo Guide</span>
        </div>
        <p style="color:#B0BEC5; font-size:0.9rem; margin:0;">
            Download the guide as an HTML file, then open in any browser and print/save as PDF.
            The full guide is also embedded below for quick reference.</p>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        label="Download Demo Guide (.html)",
        data=guide_html,
        file_name="Actuarial_Command_Center_Demo_Guide.html",
        mime="text/html",
        use_container_width=True,
    )

    st.markdown("---")

    # ==============================================================================
    # EMBEDDED VIEWER
    # ==============================================================================
    st.markdown("""
    <p style="color:#8892b0; font-size:0.85rem; margin-bottom:0.5rem;">
        Scroll through the guide below, or download and open in a separate browser tab for the
        best viewing and printing experience.</p>
    """, unsafe_allow_html=True)

    components.html(guide_html, height=2200, scrolling=True)
else:
    st.warning("DEMO_GUIDE.html not found. Please ensure it is in the project root directory.")
    st.info(f"Expected path: `{guide_path}`")
