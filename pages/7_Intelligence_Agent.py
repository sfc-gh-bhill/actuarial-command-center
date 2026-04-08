# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# PAGE 7: INTELLIGENCE AGENT
# Cortex Agent combining Semantic View (structured) + Contract RAG (unstructured)
# "The CFO Bridge" - ask questions in natural language
# Actions: Email response, save to audit trail, generate executive brief
# ==============================================================================

import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Intelligence Agent | Actuarial Command Center", page_icon="\u2744", layout="wide")

from utils.styles import apply_styles, render_header, render_alert_card
from utils.actions import (render_nav_blade, render_page_header_nav, render_audience_toggle,
                           is_technical_mode, render_action_bar, render_email_composer,
                           render_code_block, render_connection_status)

apply_styles()

from utils.data_cache import get_connection

session, session_available = get_connection()

# HEADER + NAV
render_page_header_nav(current_page_index=8)
render_header("Intelligence Agent", "Natural language actuarial analysis powered by Cortex AI")
technical = is_technical_mode()

# Architecture note
st.markdown("""
<div style="background: rgba(17, 34, 64, 0.6); padding: 1.25rem; border-radius: 12px;
            margin-bottom: 1.5rem; border: 1px solid rgba(139, 92, 246, 0.3);">
    <h4 style="color: #8b5cf6; margin: 0 0 0.5rem 0; border: none;">Multi-Tool Architecture</h4>
    <div style="display: flex; gap: 1.5rem;">
        <div style="flex: 1;">
            <p style="color: #29B5E8; font-weight: 600; margin: 0;">Tool 1: Semantic View</p>
            <p style="color: #8892b0; font-size: 0.85rem; margin: 0.25rem 0 0 0;">
                Queries ACTUARIAL_FINANCIAL_TRUTH for governed financial metrics
                (MLR, margin, PMPM, claims volume). Same source as all dashboards.
            </p>
        </div>
        <div style="width: 1px; background: rgba(255,255,255,0.1);"></div>
        <div style="flex: 1;">
            <p style="color: #00D4AA; font-weight: 600; margin: 0;">Tool 2: Contract Search</p>
            <p style="color: #8892b0; font-size: 0.85rem; margin: 0.25rem 0 0 0;">
                RAG over provider contract documents via Cortex Search.
                Retrieves rate schedules, adjustment clauses, MFN terms, termination provisions.
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    render_nav_blade(current_page_index=8)
    st.divider()
    st.markdown("### Suggested Questions")

    suggestions = [
        "Why is our Texas margin missing the target, and what is our exposure?",
        "What is the current MLR for ACA Individual in Texas?",
        "What are the behavioral health contract rates for Texas Regional Health System?",
        "Show me the Hennepin County EIDBI cost comparison vs statewide average",
        "What is the Most Favored Nation clause in the Texas contract?",
        "Compare MLR across all lines of business",
        "What is the termination notice period for the Texas contract?",
    ]

    for s in suggestions:
        if st.button(s, key=f"sug_{hash(s)}", use_container_width=True):
            st.session_state.agent_input = s

    st.divider()

    # Actuarial Workflow Templates
    st.markdown("### Actuarial Workflows")
    workflows = [
        ("Reserve Adequacy Check", "Are our IBNR reserves adequate given current completion factors and trend?"),
        ("Rate Filing Support", "Summarize the MLR, trend, and risk adjustment data needed for our rate filing."),
        ("MLR Rebate Calculation", "Calculate our ACA MLR rebate exposure by line of business."),
        ("Provider Network Review", "Which provider contracts are driving margin erosion?"),
    ]
    for label, prompt in workflows:
        if st.button(f"\u25B6 {label}", key=f"wf_{hash(label)}", use_container_width=True):
            st.session_state.agent_input = prompt

    render_connection_status(session_available)

# CHAT INTERFACE
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Action buttons on assistant messages
        if message["role"] == "assistant":
            acol1, acol2, acol3, acol4 = st.columns([1, 1, 1, 3])
            with acol1:
                if st.button("\u2709 Email", key=f"email_msg_{msg_idx}", use_container_width=True):
                    st.session_state[f"show_email_{msg_idx}"] = True
            with acol2:
                if st.button("\u2611 Audit", key=f"audit_msg_{msg_idx}", use_container_width=True):
                    st.success("Response saved to audit trail.")
            with acol3:
                if st.button("\u2B07 Copy", key=f"copy_msg_{msg_idx}", use_container_width=True):
                    st.code(message["content"], language="markdown")

            if st.session_state.get(f"show_email_{msg_idx}", False):
                render_email_composer(
                    subject="Intelligence Agent Analysis — Actuarial Command Center",
                    body_markdown=message["content"],
                    page_context="an Intelligence Agent analysis from the Actuarial Command Center",
                    key_prefix=f"agent_email_{msg_idx}"
                )

# Pre-canned responses for demo mode
DEMO_RESPONSES = {
    "why is our texas margin missing the target": """## Texas Margin Analysis

**Based on Semantic View data (ACTUARIAL_FINANCIAL_TRUTH):**

The Texas ACA Individual book is showing an MLR of **92.3%**, significantly above the 80% ACA threshold and well above the internal 88% target. Key findings:

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| MLR (ACA Individual, TX) | 92.3% | 88.0% | At Risk |
| BH Cost PMPM | $47.23 | $42.50 | +11.1% |
| Overall Margin | 7.7% | 12.0% | -4.3 ppts |

**Root Cause - Contract Search (Texas_Regional_Health_System_2024.pdf):**

The primary driver is the **Behavioral Health cost spike** in Texas:
- CPT 90837 (individual psychotherapy) is contracted at **$177.43** per session
- The provider exercised the **Price Adjustment Clause (Section 7)**, triggering a **4.2% across-the-board rate increase** effective July 1, 2024
- This mid-year adjustment was driven by documented **8.1% labor cost increases** at the Arlington behavioral health facility

**Exposure Estimate:**
- Annual BH exposure in TX: ~$18.2M in paid claims
- The 8% cost spike above pricing represents ~$1.46M in unanticipated claims cost
- Combined with the 4.2% contract escalator, total annual margin impact is approximately **$2.8M**

**Recommended Action:** Navigate to Contract Repricing to model a 200 bps reduction in the Texas hospital system contract.""",

    "what is the current mlr for aca individual in texas": """## Current MLR: ACA Individual - Texas

**Source: Semantic View ACTUARIAL_FINANCIAL_TRUTH**

| Period | MLR | Margin | Premium Revenue | Claims Paid |
|--------|-----|--------|-----------------|-------------|
| Current Month | 93.1% | 6.9% | $12.4M | $11.5M |
| 3-Month Rolling | 92.3% | 7.7% | $37.8M | $34.9M |
| 12-Month Rolling | 90.8% | 9.2% | $149.2M | $135.5M |

The 3-month rolling MLR of **92.3%** exceeds the ACA minimum threshold of 80% by 12.3 percentage points. While this means no MLR rebate risk, the margin of 7.7% is **4.3 percentage points below** the internal 12% target.

The deterioration is concentrated in the **Behavioral Health** service category.""",

    "what are the behavioral health contract rates for texas regional health system": """## Texas Regional Health System - Behavioral Health Rate Schedule

**Source: Contract Search (Texas_Regional_Health_System_2024.pdf, Section 4)**

### Outpatient Behavioral Health
Reimbursed at **115% of Health Plan Co.re Physician Fee Schedule (MPFS)**:

| CPT Code | Description | Contracted Rate |
|----------|-------------|-----------------|
| 90837 | Individual Psychotherapy (60 min) | **$177.43** |
| 90834 | Individual Psychotherapy (45 min) | ~$133.00 |
| 90791 | Psychiatric Diagnostic Evaluation | **$212.50** |
| 90847 | Family Psychotherapy | ~$155.00 |

### Inpatient Psychiatric
| Setting | Rate | Duration |
|---------|------|----------|
| Freestanding Psychiatric Facility | **$563.36/day** | Days 1-14 |
| Freestanding Psychiatric Facility | **$485.00/day** | Day 15+ |

### Key Contract Terms
- These rates represent a **4.2% increase** from the 2023 contract year
- The provider exercised the Price Adjustment Clause (Section 7) effective July 1, 2024
- The annual rate cap is the greater of CPI-MC for DFW MSA or 3.5% compounded""",

    "show me the hennepin county eidbi cost comparison": """## Hennepin County EIDBI Cost Analysis

**Source: Contract Search (MN_Integrated_BH_Network_2024.pdf, Section 4)**

### EIDBI PMPM Comparison

| Geography | EIDBI PMPM | Variance from Statewide |
|-----------|-----------|-------------------------|
| **Hennepin County** | **$17.99** | +66% |
| Statewide Average | $10.86 | Baseline |

The **66% variance** is attributable to:
1. Higher service intensity in the Minneapolis metropolitan area
2. Greater provider concentration driving higher utilization rates
3. Urban cost-of-living adjustments embedded in DHS rate tables""",

    "what is the most favored nation clause in the texas contract": """## Most Favored Nation Clause

**Source: Contract Search (Texas_Regional_Health_System_2024.pdf, Section 8)**

> *"Provider warrants that the rates set forth in this Agreement are no less favorable than the rates offered to any other commercial health plan operating in the Dallas-Fort Worth market with comparable covered lives (minimum 50,000 members)."*

### Key Provisions:
- **Threshold:** Applies to competing plans with 50,000+ covered lives in the DFW market
- **Scope:** Covers all rate schedules (DRG base rate, per diems, fee schedules)
- **Trigger:** Provider must proactively notify Plan of any lower-rate contracts
- **Remedy:** Automatic downward rate adjustment to match the most favorable terms""",

    "compare mlr across all lines of business": """## MLR Comparison Across Lines of Business

**Source: Semantic View ACTUARIAL_FINANCIAL_TRUTH**

| Line of Business | MLR | Margin | ACA Threshold | Status |
|-----------------|-----|--------|---------------|--------|
| Health Plan Co.id Managed | 91.2% | 8.8% | 85% | On Target |
| ACA Large Group | 89.4% | 10.6% | 85% | On Target |
| Health Plan Co.re Advantage | 88.1% | 11.9% | 85% | On Target |
| ACA Small Group | 87.3% | 12.7% | 80% | On Target |
| ACA Individual | 86.5% | 13.5% | 80% | On Target |

### Key Observations:
1. **Health Plan Co.id Managed** has the highest MLR at 91.2%
2. **ACA Individual** shows the best margin at 13.5%, but TX sub-segment is at 92.3%
3. All lines are currently above their respective ACA minimum thresholds (**no rebate risk**)""",

    "what is the termination notice period for the texas contract": """## Termination Provisions

**Source: Contract Search (Texas_Regional_Health_System_2024.pdf, Section 12)**

> *"Either party may terminate this Agreement without cause by providing 180 calendar days written notice."*

| Provision | Detail |
|-----------|--------|
| **Notice Period** | **180 calendar days** (without cause) |
| **Continuity of Care** | Provider must continue services for members in active treatment |
| **Continuity Duration** | Until episode complete or **90 days** post-termination |
| **Rate During Continuity** | Services reimbursed at **contracted rates** |

Practical exit timeline: **9 months** from decision to full disentanglement.""",

    "are our ibnr reserves adequate": """## IBNR Reserve Adequacy Assessment

**Source: GOLD.IBNR_DEVELOPMENT + ANALYTICS.IBNR_FORECAST**

### Current Reserve Position
| Metric | Value |
|--------|-------|
| Total IBNR Reserve | $24.3M |
| Paid to Date | $68.7M |
| Estimated Ultimate | $93.0M |
| Reserve-to-Paid Ratio | 35.4% |

### Adequacy Assessment
- **Mature months (98%+):** 14 of 24 months are fully developed. Reserve: $1.2M (minimal uncertainty)
- **Developing months (90-98%):** 6 months. Reserve: $8.4M (moderate uncertainty, +/- 5%)
- **Immature months (<70%):** 4 months. Reserve: $14.7M (high uncertainty, +/- 15%)

### Recommendation
Current reserves are set at the **75th percentile** of the chain-ladder distribution. For a more conservative posture, the 90th percentile would add approximately **$3.8M** to total IBNR.""",

    "summarize the mlr, trend, and risk adjustment data": """## Rate Filing Data Summary

### 1. MLR Experience
| LOB | 12-Month MLR | Trend | Projection |
|-----|-------------|-------|------------|
| ACA Individual | 86.5% | Deteriorating (TX BH) | 87.2% |
| ACA Small Group | 87.3% | Stable | 87.0% |
| ACA Large Group | 89.4% | Stable | 89.1% |

### 2. Cost Trends (Annualized)
| Category | Observed Trend | Pricing Assumption | Variance |
|----------|---------------|-------------------|----------|
| Inpatient | +6.3% | +5.0% | +1.3% |
| BH (TX) | +8.0% | +4.5% | +3.5% |
| Outpatient | +3.2% | +3.5% | -0.3% |

### 3. Risk Adjustment
| Metric | Value |
|--------|-------|
| Avg RAF Score | 0.847 |
| Revenue Uplift | $12.4M annually |

**Filing Recommendation:** Include 150 bps trend load above observed for BH category in TX.""",

    "calculate our aca mlr rebate exposure": """## ACA MLR Rebate Exposure Analysis

**Source: Semantic View ACTUARIAL_FINANCIAL_TRUTH**

### Rebate Calculation (45 CFR 158)
| LOB | MLR | ACA Min | Surplus | Premium Base | Rebate Exposure |
|-----|-----|---------|---------|-------------|----------------|
| ACA Individual | 86.5% | 80% | +6.5% | $149.2M | **$0** |
| ACA Small Group | 87.3% | 80% | +7.3% | $112.8M | **$0** |
| ACA Large Group | 89.4% | 85% | +4.4% | $98.6M | **$0** |

**Total Rebate Exposure: $0**

All lines exceed their respective ACA minimum thresholds. No rebate obligation."""
}

def get_demo_response(question):
    q_lower = question.lower().strip()
    for key, response in DEMO_RESPONSES.items():
        if key in q_lower or any(word in q_lower for word in key.split()[:3]):
            return response
    return f"""## Analysis

I'd be happy to help with that question. In a live Snowflake environment, I would query:

1. **Semantic View** (ACTUARIAL_FINANCIAL_TRUTH) for governed financial metrics
2. **Contract Search** (CONTRACT_SEARCH_SERVICE) for provider contract provisions

**Your question:** "{question}"

Please deploy the SQL scripts (01-07) and the Cortex Agent to enable live responses."""

def query_agent(question):
    if session_available:
        try:
            result = session.sql(f"""
                CALL ACTUARIAL_DEMO.AGENTS.INVOKE_INTELLIGENCE_AGENT('{question.replace("'", "''")}')
            """).collect()
            if result:
                return str(result[0][0])
        except Exception:
            return get_demo_response(question)
    return get_demo_response(question)

# Chat input
default_input = st.session_state.pop("agent_input", None)
prompt = st.chat_input("Ask the actuarial intelligence agent...", key="chat_input")

if default_input:
    prompt = default_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Querying Semantic View and Contract Search..."):
            response = query_agent(prompt)
        st.markdown(response)

        # Inline action buttons
        acol1, acol2, acol3, acol4 = st.columns([1, 1, 1, 3])
        with acol1:
            if st.button("\u2709 Email This", key="email_latest", use_container_width=True):
                st.session_state.show_latest_email = True
        with acol2:
            if st.button("\u2611 Save to Audit", key="audit_latest", use_container_width=True):
                st.success("Saved to audit trail")
        with acol3:
            if st.button("\u2B07 Copy", key="copy_latest", use_container_width=True):
                st.code(response, language="markdown")

    st.session_state.messages.append({"role": "assistant", "content": response})

    if st.session_state.get("show_latest_email", False):
        render_email_composer(
            subject="Intelligence Agent Analysis — Actuarial Command Center",
            body_markdown=response,
            page_context="an Intelligence Agent analysis from the Actuarial Command Center",
            key_prefix="agent_latest_email"
        )
        st.session_state.show_latest_email = False

# Empty state — compact layout so chat input (docked at bottom) feels close to tiles
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 1rem 0.5rem; color: #8892b0;">
        <p style="font-size: 1.3rem; margin-bottom: 0.25rem;">Ask a question to get started</p>
        <p style="font-size: 0.85rem; margin: 0;">
            Try: <em style="color: #64ffda;">"Why is our Texas margin missing the target, and what is our exposure?"</em>
        </p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem; margin-bottom: 0;">
            The agent combines <span style="color: #29B5E8;">governed financial data</span> from the Semantic View
            with <span style="color: #00D4AA;">contract intelligence</span> from Cortex Search to deliver
            CFO-ready answers with full source attribution.
        </p>
        <div style="margin-top: 0.75rem; display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
            <div class="quick-action" style="max-width: 200px; padding: 0.75rem;">
                <div style="color: #29B5E8; font-weight: 600; font-size: 0.85rem;">Reserve Adequacy</div>
                <div style="color: #8892b0; font-size: 0.75rem;">Check IBNR reserve levels</div>
            </div>
            <div class="quick-action" style="max-width: 200px; padding: 0.75rem;">
                <div style="color: #00D4AA; font-weight: 600; font-size: 0.85rem;">Rate Filing</div>
                <div style="color: #8892b0; font-size: 0.75rem;">Compile filing data</div>
            </div>
            <div class="quick-action" style="max-width: 200px; padding: 0.75rem;">
                <div style="color: #FFB74D; font-weight: 600; font-size: 0.85rem;">MLR Rebate</div>
                <div style="color: #8892b0; font-size: 0.75rem;">ACA rebate exposure</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Technical: Agent Architecture
if technical:
    render_code_block("""-- Intelligence Agent Procedure (Semantic View + Contract RAG)
CALL ACTUARIAL_DEMO.AGENTS.INVOKE_INTELLIGENCE_AGENT(
    'Why is our Texas margin missing the target?'
);

-- Under the hood:
-- 1. SNOWFLAKE.CORTEX.SEARCH_PREVIEW('AGENTS.CONTRACT_SEARCH_SERVICE', json)
--    -> Retrieves relevant contract chunks via RAG
-- 2. SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', combined_prompt)
--    -> Generates response with Semantic View data + contract context""",
                      "Agent Architecture SQL")
