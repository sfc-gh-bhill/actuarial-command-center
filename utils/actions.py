# ==============================================================================
# ACTIONS MODULE - Futuristic Action-Oriented UI Components
# Export, email drafting, audit packages, code blocks, alerts
# ==============================================================================

import streamlit as st
import pandas as pd
import io
import base64
import datetime

# ==============================================================================
# PAGE REGISTRY
# ==============================================================================
PAGE_REGISTRY = [
    {"path": "streamlit_app.py", "label": "Home", "icon": "\u2302", "short": "Home"},
    {"path": "pages/0_Executive_Summary.py", "label": "Executive Summary", "icon": "\u25C8", "short": "Exec Summary"},
    {"path": "pages/1_Margin_Forecast.py", "label": "Margin Forecast", "icon": "\u25B2", "short": "Margin"},
    {"path": "pages/2_Risk_Adjustment.py", "label": "Risk Adjustment", "icon": "\u2694", "short": "Risk Adj"},
    {"path": "pages/3_Claims_Analytics.py", "label": "Claims Analytics", "icon": "\u2637", "short": "Claims"},
    {"path": "pages/4_IBNR_Reserves.py", "label": "IBNR Reserves", "icon": "\u2234", "short": "IBNR"},
    {"path": "pages/5_Contract_Repricing.py", "label": "Contract Repricing", "icon": "\u2696", "short": "Repricing"},
    {"path": "pages/6_Trend_Surveillance.py", "label": "Trend Surveillance", "icon": "\u26A0", "short": "Trends"},
    {"path": "pages/7_Intelligence_Agent.py", "label": "Intelligence Agent", "icon": "\u2604", "short": "Agent"},
    {"path": "pages/8_Architecture.py", "label": "Architecture", "icon": "\u25C7", "short": "Architecture"},
    {"path": "pages/9_Demo_Guide.py", "label": "Demo Guide", "icon": "\u25A4", "short": "Demo Guide"},
]


# ==============================================================================
# NAVIGATION BLADE (collapsible left-side)
# ==============================================================================
def render_nav_blade(current_page_index: int = 0):
    """Render collapsible navigation blade in the sidebar with page links and branding."""
    import os

    # Snowflake logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snowflake_bug.png")
        try:
            st.image(logo_path, width=55)
        except Exception:
            st.markdown('<div style="text-align:center;font-size:42px;color:#29B5E8;">&#10052;</div>',
                        unsafe_allow_html=True)

    # Brand header
    st.markdown("""
    <div style="text-align:center;padding:8px 0 18px 0;">
        <div style="font-size:20px;font-weight:700;color:#29B5E8;letter-spacing:2px;
                    font-family:'Lato',sans-serif;">SNOWFLAKE</div>
        <div style="font-size:10px;color:#8892b0;letter-spacing:1.5px;font-weight:500;">
            SOLUTION ENGINEERING</div>
        <div style="width:50px;height:2px;background:#29B5E8;margin:10px auto 0;border-radius:1px;"></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:0 0 0.75rem 0;">
        <div style="background:linear-gradient(135deg,#29B5E8 0%,#00D4AA 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    font-size:1.05rem;font-weight:700;margin:0;">
            Actuarial Command Center</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation links
    st.markdown('<p style="color:#8892b0;font-size:0.7rem;letter-spacing:1.5px;'
                'text-transform:uppercase;margin-bottom:0.5rem;">NAVIGATION</p>',
                unsafe_allow_html=True)

    for i, page in enumerate(PAGE_REGISTRY):
        is_active = (i == current_page_index)
        label = f"{page['icon']}  {page['label']}"
        if is_active:
            label = f"**{label}**"
        st.page_link(page["path"], label=label, use_container_width=True)

    st.divider()

    # Audience toggle (Executive / Technical)
    st.markdown('<p style="color:#8892b0;font-size:0.7rem;letter-spacing:1.5px;'
                'text-transform:uppercase;margin-bottom:0.5rem;">VIEW MODE</p>',
                unsafe_allow_html=True)

    if "audience_mode" not in st.session_state:
        st.session_state.audience_mode = "Executive"

    mode = st.radio("View Mode", ["Executive", "Technical"],
                    index=0 if st.session_state.audience_mode == "Executive" else 1,
                    horizontal=True, label_visibility="collapsed",
                    key=f"audience_toggle_{current_page_index}")
    st.session_state.audience_mode = mode

    st.divider()


def render_page_header_nav(current_page_index: int):
    """Render back/forward navigation bar at the top of a page."""
    prev_page = PAGE_REGISTRY[current_page_index - 1] if current_page_index > 0 else None
    next_page = PAGE_REGISTRY[current_page_index + 1] if current_page_index < len(PAGE_REGISTRY) - 1 else None

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if prev_page:
            st.page_link(prev_page["path"],
                         label=f"\u2190 {prev_page['short']}",
                         use_container_width=True)
    with col3:
        if next_page:
            st.page_link(next_page["path"],
                         label=f"{next_page['short']} \u2192",
                         use_container_width=True)


# ==============================================================================
# AUDIENCE TOGGLE (Executive vs Technical)
# ==============================================================================
def render_audience_toggle():
    """Return True if technical mode. Toggle now lives in the nav blade sidebar."""
    return is_technical_mode()


def is_technical_mode():
    """Check if technical mode is active."""
    return st.session_state.get("audience_mode", "Executive") == "Technical"


# ==============================================================================
# ACTION BAR - Per-section action strip
# ==============================================================================
def render_action_bar(actions: list, key_prefix: str = "action"):
    """Render a futuristic action bar with toggle buttons.
    
    actions: list of dicts with keys: label, icon, callback_key
    Returns dict of {callback_key: bool} indicating which are active.
    
    Uses session_state to persist active state across reruns so that
    panels (email composer, export buttons, etc.) stay open when the
    user interacts with widgets inside them.
    """
    state_key = f"_action_bar_{key_prefix}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None  # tracks which action is currently active

    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(10,25,47,0.8) 0%,rgba(17,34,64,0.6) 100%);
                border:1px solid rgba(41,181,232,0.2);border-radius:12px;
                padding:0.6rem 1rem;margin:1rem 0;
                display:flex;align-items:center;gap:0.5rem;">
        <span style="color:#8892b0;font-size:0.7rem;text-transform:uppercase;
                     letter-spacing:1px;margin-right:0.5rem;">ACTIONS</span>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(actions))
    for i, action in enumerate(actions):
        with cols[i]:
            cb_key = action["callback_key"]
            is_active = st.session_state[state_key] == cb_key
            clicked = st.button(
                f"{action.get('icon', '')} {action['label']}",
                key=f"{key_prefix}_{cb_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            )
            if clicked:
                if is_active:
                    st.session_state[state_key] = None  # toggle off
                else:
                    st.session_state[state_key] = cb_key  # toggle on
                st.rerun()

    results = {}
    for action in actions:
        results[action["callback_key"]] = (st.session_state[state_key] == action["callback_key"])

    return results


# ==============================================================================
# EXPORT FUNCTIONS
# ==============================================================================
def render_export_buttons(df: pd.DataFrame, filename: str, key_prefix: str = "export"):
    """Render CSV and Excel download buttons for a dataframe."""
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{filename}_{datetime.date.today().isoformat()}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True
        )
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        st.download_button(
            label="Download Excel",
            data=buffer.getvalue(),
            file_name=f"{filename}_{datetime.date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_xlsx",
            use_container_width=True
        )


# ==============================================================================
# EMAIL COMPOSER (Cortex-drafted)
# ==============================================================================
def render_email_composer(subject: str, body_markdown: str, insights: list = None,
                          page_context: str = "", key_prefix: str = "email"):
    """Render a professional email composer with insight selection, multi-recipient,
    copy-to-clipboard, and open-in-email-client capabilities.

    Args:
        subject: Pre-filled email subject line
        body_markdown: Core data/analysis content for the email body
        insights: Optional list of dicts with keys: label, value, checked (bool).
                  Renders checkboxes so user picks which data points to include.
        page_context: Introductory sentence describing the email context
                      (e.g., "the latest Executive Summary from the Actuarial Command Center")
        key_prefix: Unique key prefix for all widgets in this composer instance
    """
    import urllib.parse
    import streamlit.components.v1 as components

    with st.expander("✉  Compose Email", expanded=True):
        # Header badge
        st.markdown("""
        <div class="email-composer-header">
            <span style="color:#ccd6f6;font-size:0.95rem;font-weight:600;">Email Composer</span>
            <span class="email-composer-badge">AI-DRAFTED BY CORTEX</span>
        </div>
        """, unsafe_allow_html=True)

        # --- Insight selection ---
        selected_insights = []
        if insights:
            st.markdown("""
            <div class="email-insights-title">Select Insights to Include</div>
            """, unsafe_allow_html=True)
            cols_per_row = 2
            for row_start in range(0, len(insights), cols_per_row):
                row_items = insights[row_start:row_start + cols_per_row]
                cols = st.columns(cols_per_row)
                for ci, insight in enumerate(row_items):
                    with cols[ci]:
                        checked = st.checkbox(
                            f"{insight['label']}: {insight['value']}",
                            value=insight.get("checked", True),
                            key=f"{key_prefix}_insight_{row_start + ci}"
                        )
                        if checked:
                            selected_insights.append(insight)

        # --- Recipients ---
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            to_field = st.text_input("To (separate multiple with commas):",
                                     value="", placeholder="cfo@company.com, cao@company.com",
                                     key=f"{key_prefix}_to")
        with rcol2:
            cc_field = st.text_input("CC (optional):",
                                     value="", placeholder="actuary@company.com",
                                     key=f"{key_prefix}_cc")

        # --- Subject ---
        subject_field = st.text_input("Subject:", value=subject, key=f"{key_prefix}_subject")

        # --- Build professional body ---
        intro = page_context if page_context else "the latest analysis from the Actuarial Command Center"

        body_parts = []
        body_parts.append("Dear Team,")
        body_parts.append("")
        body_parts.append(f"Please find below {intro}. This summary is generated from "
                          "governed data sources and reflects the most current figures available.")
        body_parts.append("")

        if selected_insights:
            body_parts.append("Key Highlights:")
            for ins in selected_insights:
                body_parts.append(f"  - {ins['label']}: {ins['value']}")
            body_parts.append("")

        body_parts.append(body_markdown.strip())
        body_parts.append("")
        body_parts.append("Please don't hesitate to reach out if you have questions or would like "
                          "to schedule a review of these findings.")
        body_parts.append("")
        body_parts.append("Best regards,")
        body_parts.append("Actuarial Command Center")
        body_parts.append("Snowflake AI Data Cloud")
        body_parts.append("")
        body_parts.append("---")
        body_parts.append("Source: Governed Semantic View (ACTUARIAL_FINANCIAL_TRUTH)")
        body_parts.append("This email was drafted by Cortex AI and may have been edited by the sender.")

        assembled_body = "\n".join(body_parts)

        # --- Editable body ---
        body_field = st.text_area("Body:", value=assembled_body, height=350,
                                  key=f"{key_prefix}_body")

        # --- Action buttons ---
        full_email = f"To: {to_field}"
        if cc_field.strip():
            full_email += f"\nCC: {cc_field}"
        full_email += f"\nSubject: {subject_field}\n\n{body_field}"

        col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 2.4])

        with col1:
            # Copy to clipboard via JS
            if st.button("📋 Copy Email", key=f"{key_prefix}_copy", use_container_width=True):
                escaped = full_email.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                js_code = f"""
                <script>
                    const text = `{escaped}`;
                    navigator.clipboard.writeText(text).then(function() {{
                        window.parent.document.querySelector('[data-testid="stNotification"]') ||
                        console.log('Copied to clipboard');
                    }});
                </script>
                """
                components.html(js_code, height=0)
                st.success("Email copied to clipboard")

        with col2:
            # Open in email client via mailto
            if st.button("📧 Open in Email", key=f"{key_prefix}_mailto", use_container_width=True):
                to_encoded = urllib.parse.quote(to_field)
                subject_encoded = urllib.parse.quote(subject_field)
                body_encoded = urllib.parse.quote(body_field)
                cc_encoded = urllib.parse.quote(cc_field) if cc_field.strip() else ""
                mailto = f"mailto:{to_encoded}?subject={subject_encoded}&body={body_encoded}"
                if cc_encoded:
                    mailto += f"&cc={cc_encoded}"
                # Open mailto link via JS
                components.html(
                    f'<script>window.open("{mailto}", "_blank");</script>',
                    height=0
                )
                st.info("Opening your email client...")

        with col3:
            if st.button("🔄 Reset Draft", key=f"{key_prefix}_regen", use_container_width=True):
                for k in list(st.session_state.keys()):
                    if k.startswith(f"{key_prefix}_"):
                        del st.session_state[k]
                st.rerun()


# ==============================================================================
# CODE BLOCK (Technical View)
# ==============================================================================
def render_code_block(code: str, title: str = "SQL Query", language: str = "sql"):
    """Render a syntax-highlighted code block with a title."""
    st.markdown(f"""
    <div style="background:rgba(17,34,64,0.4);border:1px solid rgba(41,181,232,0.2);
                border-radius:8px;padding:0.5rem 0.75rem;margin:0.5rem 0;">
        <span style="color:#29B5E8;font-size:0.7rem;font-weight:600;letter-spacing:1px;
                     text-transform:uppercase;">{title}</span>
    </div>
    """, unsafe_allow_html=True)
    st.code(code, language=language)


# ==============================================================================
# AUDIT PACKAGE BUILDER
# ==============================================================================
def render_audit_package(sections: list, package_name: str = "Actuarial Audit Package",
                         key_prefix: str = "audit"):
    """Render an audit package builder.
    
    sections: list of dicts with keys: name, description, included (bool)
    """
    with st.expander(f"Generate {package_name}", expanded=False):
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(16,185,129,0.1) 0%,rgba(41,181,232,0.05) 100%);
                    padding:0.75rem;border-radius:10px;margin-bottom:0.75rem;
                    border:1px solid rgba(16,185,129,0.2);">
            <span style="color:#10b981;font-size:0.75rem;font-weight:600;letter-spacing:1px;">
                COMPLIANCE-READY EXPORT</span>
            <p style="color:#8892b0;font-size:0.8rem;margin:0.25rem 0 0 0;">
                Select sections to include in the audit package. All data is sourced from the
                governed Semantic View (ACTUARIAL_FINANCIAL_TRUTH).</p>
        </div>
        """, unsafe_allow_html=True)

        selected = []
        for i, section in enumerate(sections):
            checked = st.checkbox(section["name"],
                                   value=section.get("included", True),
                                   help=section.get("description", ""),
                                   key=f"{key_prefix}_{i}")
            if checked:
                selected.append(section["name"])

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Generate Package", key=f"{key_prefix}_gen", use_container_width=True):
                st.success(f"Audit package generated with {len(selected)} sections: {', '.join(selected)}")
                st.info("In live mode, this would compile a branded PDF document with all selected sections, "
                        "data lineage proof, and Semantic View governance attestation.")

        return selected


# ==============================================================================
# PROACTIVE ALERT WITH ACTION BUTTONS
# ==============================================================================
def render_proactive_alert(title: str, message: str, actions: list = None,
                           severity: str = "critical", key_prefix: str = "alert"):
    """Render a proactive alert banner with action buttons.
    
    actions: list of dicts with keys: label, page_link (optional), callback_key
    """
    severity_colors = {
        "critical": ("#FF6B6B", "rgba(255,107,107,0.1)", "!!!"),
        "warning": ("#FFB74D", "rgba(255,183,77,0.1)", "!"),
        "info": ("#29B5E8", "rgba(41,181,232,0.1)", "i"),
        "success": ("#4ECDC4", "rgba(78,205,196,0.1)", "OK"),
    }
    color, bg, icon = severity_colors.get(severity, severity_colors["info"])

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{bg} 0%,rgba(10,25,47,0.6) 100%);
                border:1px solid {color}40;border-left:4px solid {color};
                border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;
                animation:fadeIn 0.5s ease-out;">
        <div style="display:flex;align-items:center;gap:0.75rem;">
            <div style="background:{color}20;border-radius:50%;width:36px;height:36px;
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="color:{color};font-weight:700;font-size:0.8rem;">{icon}</span>
            </div>
            <div style="flex:1;">
                <strong style="color:{color};font-size:0.95rem;">{title}</strong>
                <p style="color:#ccd6f6;margin:0.25rem 0 0 0;font-size:0.85rem;line-height:1.4;">
                    {message}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if actions:
        cols = st.columns(len(actions) + 2)  # padding cols
        results = {}
        for i, action in enumerate(actions):
            with cols[i]:
                if "page_link" in action:
                    st.page_link(action["page_link"], label=action["label"],
                                 use_container_width=True)
                else:
                    clicked = st.button(action["label"],
                                         key=f"{key_prefix}_{action.get('callback_key', i)}",
                                         use_container_width=True)
                    results[action.get("callback_key", str(i))] = clicked
        return results
    return {}


# ==============================================================================
# SESSION / CONNECTION STATUS
# ==============================================================================
def render_connection_status(session_available: bool):
    """Render connection status in sidebar."""
    st.divider()
    if session_available:
        st.markdown("""
        <div style="background:rgba(78,205,196,0.1);border:1px solid rgba(78,205,196,0.3);
                    padding:0.5rem 0.75rem;border-radius:8px;text-align:center;">
            <span style="color:#4ECDC4;font-size:0.8rem;font-weight:600;">
                Snowflake Connected</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(255,183,77,0.1);border:1px solid rgba(255,183,77,0.3);
                    padding:0.5rem 0.75rem;border-radius:8px;text-align:center;">
            <span style="color:#FFB74D;font-size:0.8rem;font-weight:600;">
                Demo Mode (Local)</span>
        </div>
        """, unsafe_allow_html=True)
    st.caption("v2.0 | Snowflake AI Data Cloud")
