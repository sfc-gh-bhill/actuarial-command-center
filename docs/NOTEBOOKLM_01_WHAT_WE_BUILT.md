# Document 1: What We Built — The Actuarial Command Center, Explained

## For NotebookLM Podcast Generation

---

## The One-Liner

We built a fully functional actuarial operating system — nine interactive pages covering every core workflow a health plan actuary touches — running entirely inside Snowflake AI Data Cloud using Streamlit in Snowflake. No external tools. No data movement. No spreadsheet archaeology.

## What It Actually Is

The Actuarial Command Center is a production-grade data application that consolidates the actuarial workflow for a health plan into a single, governed, AI-powered interface. It is not a dashboard. Dashboards show you what happened. This application shows you what happened, tells you why, recommends what to do, models the financial impact of your options, drafts the communication to your leadership, and lets you ask follow-up questions in plain English.

Think of it as the difference between a weather report and a weather *system*. A weather report tells you it's raining. A weather system tells you it's raining, predicts when it'll stop, warns you about the flood risk, suggests rerouting your commute, and texts your boss that you'll be late. That's what we built — but for actuaries.

## The Nine Pages (Plus Home)

### Home Page — Mission Control
The front door. A gradient hero banner, proactive alerts (the system tells you something is wrong before you ask), four top-line KPIs (MLR, Operating Margin, Avg Cost PMPM, Total Claims), quick actions (Draft CFO Briefing, Generate Audit Package, Run Repricing Scenario), and a guided demo workflow. There's an email composer that lets you send a professionally formatted CFO briefing in 30 seconds with selectable insight bullet points.

The home page also includes a "Problem Statement" section and a technical architecture overview with animated pipeline cards for the nerds in the room.

### Page 1: Executive Summary
The financial cockpit. MLR by Line of Business with ACA threshold compliance badges. Rolling 12-month MLR trend chart with regulatory threshold lines (80% Individual/Small Group, 85% Large Group). Margin by state visualization. Cortex ML anomaly alerts with severity badges. An action bar with Email Summary, Export LOB Data, and Navigate to Repricing. Technical mode shows the actual governance SQL and ACA rebate compliance check query.

### Page 2: Margin Forecast
Forward-looking projections. Current MLR by LOB with target comparison metrics. Interactive IBNR completion factor adjustment — actuaries can change assumptions and watch projections update in real-time. MLR trend by LOB multi-line chart. Margin waterfall (premium to margin bridge). Year-end margin projection using 6-month annualization. Sidebar filters for LOB and State.

### Page 3: Risk Adjustment
CMS-HCC v28 risk score analysis. Average RAF score, Premium PMPM, Risk-Adjusted PMPM, and Annual Revenue Impact KPIs. RAF distribution by LOB with baseline 1.0 reference line. A color-coded CMS-HCC v28 coefficient reference chart distinguishing constrained (red) vs. unconstrained (blue) coefficients — this is critical because CMS changed the model and health plans that don't adjust their projections are building budgets on deprecated numbers. RAF Score by State with HCC Coding Rate analysis. Action bar includes RAF Audit Report, Export Coefficients, and Flag Coding Gaps.

### Page 4: Claims Analytics
Deep-dive claims analysis across 433,000+ medical claims. Five KPIs including the critical "High-Cost %" metric. Four analytical tabs: Cost Distribution (histograms by service category showing the long-tail problem), Service Category Mix (pie + bar showing BH growth), High-Cost Analysis (claims >$50K, top 20 detail table), and Claims Lag (average and median processing time by category — crucial for IBNR). Proactive alert when high-cost claims exceed 5%. Action bar includes Draft Stop-Loss Alert — one click to generate a formatted email to your reinsurance carrier.

### Page 5: IBNR Reserves
Chain-ladder reserving, automated end-to-end. KPIs: Total IBNR Reserve, Paid to Date, Estimated Ultimate, Immature Months. Three tabs: IBNR Reserve Waterfall (stacked bars with maturity color coding), Completion Factor S-Curve (the classic actuarial visualization with 70%/90%/98% threshold lines), and Run-Off Triangle Heatmap (the development triangle, but interactive and visual instead of static Excel). The Reserve Opinion Package generates a six-component audit package including Bornhuetter-Ferguson comparison, data quality certification, methodology disclosure, sensitivity analysis, and management discussion points.

### Page 6: Contract Repricing — "The Wow Moment"
Interactive real-time contract repricing with five configurable parameters: Target State, Basis Point Adjustment (-500 to +500), Service Scope (All/Inpatient/Outpatient), Inpatient Pass-Through %, and Outpatient Pass-Through %. A stored procedure (REPRICE_CONTRACT) fires against governed data with every parameter change. Before/After KPIs update live. Save up to three scenarios for side-by-side comparison with grouped bar charts.

The Negotiation Brief is the crown jewel: a full professional document with executive summary, contract clauses retrieved via Cortex Search (RAG over indexed provider agreements), financial impact table by service category, market benchmark comparison, and five customized negotiation talking points. Copy-to-clipboard for immediate use. Every number is sourced from the governed Semantic View with full data provenance.

### Page 7: Trend Surveillance
Cortex ML anomaly detection and cost trend monitoring. The system identified a Texas Behavioral Health cost spike — 8% above expectations — traced it to a 4.2% mid-year price adjustment clause in the provider contract, and linked it to CPT 90837 negotiated rates. Multi-line cost trend charts by service category. A dedicated Texas BH deep dive with baseline reference lines, contract rate markers, anomaly period shading, and a root cause analysis card. Alert rule configuration for custom monitoring.

### Page 8: Intelligence Agent
Natural language interface powered by Cortex Agents. Ask questions in plain English: "What is our MLR by line of business?" "Why is Texas BH cost trending up?" "What contract clauses affect reimbursement rates?" The agent queries the governed Semantic View for financial data and searches indexed contract documents via Cortex Search. Responses include citations. Conversation memory maintains context across questions. Three quick-action tiles for common actuarial queries: Reserve Adequacy, Rate Filing, MLR Rebate.

### Page 9: Architecture
Interactive SVG architecture diagram with Overview and Detailed modes. Zoom slider (50-150%). Flow highlighting: select any page from a dropdown and watch the relevant pipeline nodes glow while non-relevant components dim to 12% opacity. Trace exactly which data sources, transformations, ML models, and services power each page. Hover effects on all nodes. This is full data lineage visualization for both technical and non-technical audiences.

## The Data Foundation

The application runs on the APCD-CDL v3.0.1 standard (All-Payer Claims Database Common Data Layout) — the same schema used by state regulators. The synthetic dataset includes:

- 10,000 member eligibility records
- 433,155 medical claims
- 200,000 pharmacy claims  
- 164,459 capitation payments
- 200 pharmacy rebate records
- Claims lag triangles (234 development cells)
- 12 CMS-HCC reference coefficients
- 9 indexed contract chunks for RAG

All data flows through a Medallion Architecture: RAW (ingestion) > SILVER (cleansed via Dynamic Tables) > GOLD (business-ready aggregates via Dynamic Tables + Semantic View) > ANALYTICS (ML outputs) > AGENTS (contract index + search service).

## Cross-Page Workflow: The "Story"

The demo tells a cohesive story, not a series of disconnected dashboards:

1. **Trend Surveillance detects** the Texas BH anomaly (Cortex ML)
2. **Executive Summary quantifies** the financial impact (governed KPIs)
3. **Claims Analytics reveals** the underlying cost patterns (distribution analysis)
4. **Risk Adjustment contextualizes** the population risk (CMS-HCC v28)
5. **IBNR Reserves ensures** adequate reserving for developing claims (chain-ladder)
6. **Margin Forecast projects** the year-end impact (annualized projections)
7. **Contract Repricing models** the negotiation response (real-time what-if)
8. **Intelligence Agent answers** follow-up questions (natural language AI)
9. **Architecture shows** how it all connects (interactive lineage)

Every page links to the next. Every action bar includes navigation. Every insight can be emailed, exported, or escalated without leaving the application.

## Technical Features That Matter

**Audience Toggle:** Every page has a "Technical/Executive" toggle. In Executive mode, you see the business insights. In Technical mode, you see the SQL, the methodology, and the data governance details. Same page, two audiences.

**Proactive Alerts:** The system doesn't wait for you to discover problems. If MLR exceeds ACA thresholds, an alert appears. If high-cost claims exceed 5%, a warning surfaces. If an anomaly is detected, it's front and center on login.

**Email Composers:** Every page can generate formatted emails with selectable insights. CFO briefing, stop-loss alert, trend report, scenario analysis — one click each.

**Export Everywhere:** CSV and Excel export on every data view.

**Demo Mode Fallback:** Every page works without a Snowflake connection using inline numpy/pandas data generation. The application gracefully degrades from live data to realistic synthetic data.

**Snowflake Brand Compliance:** Lato font, #29B5E8 primary blue, #11567F dark blue, snowflake emoji page icon, "POWERED BY SNOWFLAKE" sidebar footer.
