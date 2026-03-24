# Actuarial Command Center — End-to-End Demonstration Guide

**Product:** Actuarial Command Center  
**Platform:** Snowflake AI Data Cloud (Streamlit in Snowflake)  
**Version:** 1.0 | February 2026  
**Duration:** 25-35 minutes (or modular by page)  
**Audience:** Chief Actuaries, CFOs, VP of Analytics, Health Plan Leadership  

---

## Pre-Demo Setup Checklist

- [ ] Log in to your Snowflake account (e.g. `https://app.snowflake.com/<YOUR_ORG>/<YOUR_ACCOUNT>/`)
- [ ] Navigate to **Streamlit Apps > ACTUARIAL_DEMO.GOLD.ACTUARIAL_COMMAND_CENTER**
- [ ] Clear any saved scenarios in Contract Repricing (fresh start)
- [ ] Ensure warehouse `ACTUARIAL_WH` is active (auto-resumes on query)
- [ ] Have a second browser tab open to Snowsight for "peek behind the curtain" moments
- [ ] Optional: Create a demo user for live audience follow-along:
  - **User:** `<DEMO_USER>` | **Password:** `<SET_TEMP_PASSWORD>`
  - **Role:** `ACTUARIAL_DEMO_USER` | **Network:** Open (any IP)

---

## The 60-Second Elevator Pitch (Memorize This)

> "What if your actuarial team's entire workflow — from claims surveillance to IBNR reserving to contract negotiation — lived in one governed application, powered by the same AI that Fortune 500 companies use for fraud detection, but purpose-built for health plan actuaries? No more spreadsheet archaeology. No more 'let me pull that from the data warehouse and get back to you next Tuesday.' We built that. It runs on Snowflake. And it takes about 4 seconds to answer questions that used to take 4 days."

---

## Act I: "The Front Door" — Mission Control (Home Page)

**Time:** 3-4 minutes  
**Vibe:** Confident, establishing credibility  

### What to Show

1. **Hero Banner** — The gradient header with "Actuarial Command Center" and shimmer animation. This isn't just a title; it's setting the tone that this is a *product*, not a proof-of-concept taped together with duct tape and VLOOKUP prayers.

2. **Proactive BH Alert** — A red alert banner surfaces *before anyone asks*: "Behavioral Health Unit Cost Anomaly — Texas." This is the app telling you something is wrong rather than you discovering it in a board meeting.

   > **Talking Point:** "Notice how nobody had to run a query to find this. The system detected a cost anomaly using Cortex ML — Snowflake's built-in machine learning — and surfaced it the moment you opened the app. It's like having a really diligent junior actuary who never sleeps, never takes PTO, and never accidentally overwrites the production spreadsheet."

3. **Mission Control KPIs** — Four tiles: MLR (87.2%), Operating Margin, Avg Cost PMPM, Total Claims. These pull from a governed Semantic View, which means every number on every page traces back to one source of truth.

   > **Talking Point:** "These aren't cached from last quarter. These are *live* — computed from a Dynamic Table pipeline that refreshes automatically. If a claim adjudicates at 2 AM, this number updates. No ETL jobs to babysit. No 'the data will be ready by Thursday.'"

4. **Quick Actions** — Show "Draft CFO Briefing." Click it. An email composer appears with pre-populated insights, selectable bullet points, and a professional tone.

   > **Talking Point:** "Your CFO asks for a financial summary at 4:47 PM on a Friday. Instead of panic, you click one button, select which insights to include, and send a professionally drafted email in 30 seconds. That's not automation — that's *liberation*."

5. **Demo Workflow Strip** — Four steps guiding the recommended demo path. This is the app being self-aware enough to onboard its own users.

### Transition

> "That's the front door. Now let's walk through what each room in this house actually does."

---

## Act II: "The Financial Cockpit" — Executive Summary (Page 1)

**Time:** 3-4 minutes  
**Vibe:** Authoritative, "single pane of glass"  

### What to Show

1. **Top-Line KPIs** — MLR, Operating Margin, Avg Cost PMPM, Total Claims. Same data as home page but with more context.

2. **Anomaly Alerts Section** — Cortex ML-detected anomalies with severity badges. The Texas BH spike is flagged as "CRITICAL."

   > **Talking Point:** "Traditional actuarial workflows discover anomalies when someone eyeballs a spreadsheet and says 'that number looks funny.' This system runs anomaly detection models continuously. It's the difference between a smoke detector and hoping you smell something burning."

3. **MLR by Line of Business** — Tiles showing Individual (91.2% — above ACA threshold), Small Group (84.1%), Large Group (82.7%), Health Plan Co.re Advantage (88.5%). Status badges (green/yellow/red) instantly communicate health.

4. **MLR Trend Chart** — 12-month rolling trend with ACA threshold lines at 80% and 85%. Show how Individual has been creeping above the 80% line.

   > **Talking Point:** "See that Individual line crossing 80%? That's not just a trend — that's a rebate trigger. Under the ACA, if your Individual MLR exceeds 80%, you owe money back to members. This chart isn't decorative; it's an early warning system for a regulatory obligation that can cost millions."

5. **Margin by State** — Color-coded bar chart. Texas is underperforming.

6. **Action Bar** — Show "Email Summary" and "Navigate to Repricing" buttons. These aren't afterthoughts — they're embedded workflow.

7. **Technical Mode Toggle** — Flip the audience toggle to "Technical." Show the MLR Governance SQL and ACA Rebate Compliance Check. This is the "show your work" mode for auditors and regulators.

   > **Talking Point:** "Every visualization has a 'show me the SQL' button. Because when a regulator asks 'how did you calculate this?', the answer shouldn't be 'let me find the analyst who built the spreadsheet three years ago.' The answer is right here, governed, version-controlled, and auditable."

### Transition

> "So we can see the current state. But actuaries don't get paid for hindsight — they get paid for foresight. Let's look forward."

---

## Act III: "The Crystal Ball" — Margin Forecast (Page 2)

**Time:** 3-4 minutes  
**Vibe:** Forward-looking, slightly nerdy  

### What to Show

1. **ACA MLR Thresholds Banner** — Reference card: Individual/Small Group 80%, Large Group 85%. Always visible because these aren't suggestions — they're law.

2. **Current MLR by LOB** — Metric cards with target comparison. Individual is 6.2 ppts above target. That's the one keeping the CFO up at night.

3. **IBNR Adjustment Factors** — Interactive completion factor inputs. Change a factor and watch the projection update.

   > **Talking Point:** "This is where it gets fun for the actuaries in the room. Those completion factors? You can adjust them right here. No round-trip to the data team. No 'can you re-run the model with 95% instead of 92%?' Just slide, see, decide. It's like a flight simulator for your reserve estimates."

4. **MLR Trend by LOB** — Multi-line chart showing each LOB's trajectory. Individual is diverging upward.

5. **Margin Waterfall** — Bridge chart from premium to margin, showing where money leaks out.

6. **Year-End Projection** — 6-month annualized view. This is the "will we hit our targets?" answer.

7. **Sidebar Filters** — Change LOB, change State. Everything re-renders instantly.

   > **Talking Point:** "Every chart on this page responds to the filters in real-time. Want to see just Florida Health Plan Co.re Advantage? Two clicks. Want to compare Texas Small Group? Two more clicks. In a traditional environment, each of those would be a separate report request."

### Transition

> "Now, MLR is driven by two things: what you collect (premium) and what you pay (claims). Premium is set. But the 'what you pay' side? That's where risk adjustment enters the chat."

---

## Act IV: "The RAF Score Whisperer" — Risk Adjustment (Page 3)

**Time:** 3-4 minutes  
**Vibe:** Technical but accessible, "this is where money hides"  

### What to Show

1. **CMS-HCC v28 Banner** — Explain that CMS just updated the risk adjustment model with constrained coefficients. This isn't academic — it directly changes how much revenue health plans receive.

   > **Talking Point:** "CMS-HCC v28 is like the IRS changing the tax code, but for health insurance. Every diagnosis code maps to a coefficient that determines how much CMS pays you per member. Get the coding wrong, and you're leaving money on the table. Get it intentionally wrong, and the DOJ comes knocking. This page helps you get it *exactly* right."

2. **KPIs** — Avg RAF Score (1.12), Premium PMPM, Risk-Adjusted PMPM, Annual Revenue Impact. That revenue impact number is the one that makes CFOs lean forward.

3. **RAF Distribution by LOB** — Bar chart with a baseline 1.0 line. Anything above 1.0 means your population is sicker (and more expensive) than average.

4. **CMS-HCC v28 Coefficient Reference** — Color-coded chart showing constrained (red) vs. unconstrained (blue) coefficients. Diabetes HCC 36/37/38 = 0.302, CHF HCC 224/225/226 = 0.431.

   > **Talking Point:** "See the red bars? Those are the constrained coefficients — CMS is saying 'we think these were being over-coded, so we're capping them.' If your revenue projections don't account for this constraint, you're building your budget on a number that CMS has already told you is wrong."

5. **Action Bar — "Flag Coding Gaps"** — Shows where documentation may be incomplete, representing potential revenue recovery.

6. **RAF Score by State + HCC Coding Rate** — Identifies geographic variation in coding completeness.

### Transition

> "So we know our risk scores. We know our MLR. But where exactly is the money going? Let's look at the claims."

---

## Act V: "Follow the Money" — Claims Analytics (Page 4)

**Time:** 3-4 minutes  
**Vibe:** Detective story, finding the signal in the noise  

### What to Show

1. **KPIs** — Total Claims (433K+), Total Paid, Avg Per Claim, Median Per Claim, High-Cost %. That high-cost percentage is the canary in the coal mine.

2. **Proactive Alert** — If high-cost claims exceed 5%, a warning appears automatically. "The system is telling you before you have to ask."

3. **Four Tabs:**

   **a. Cost Distribution** — Histograms by service category. Show the long tail on Inpatient.
   
   > **Talking Point:** "See that tail stretching to the right on Inpatient? Those are your $200K+ cases. They're 3% of claims and 22% of cost. In actuarial terms, that's where your stop-loss attachment point lives. In normal terms, that's the tail wagging the dog."

   **b. Service Category Mix** — Pie chart + bar chart. Behavioral Health is growing faster than other categories.

   **c. High-Cost Analysis** — Claims over $50K. Top 20 table with member details. This is where you find the specific cases driving your numbers.

   **d. Claims Lag** — Average and median processing time by category. Behavioral Health has the longest lag, which matters for IBNR.

4. **Action Bar — "Draft Stop-Loss Alert"** — One-click email to your reinsurer with pre-populated high-cost data.

   > **Talking Point:** "Your stop-loss carrier calls and asks for a large-loss report. Instead of spending two hours pulling data, you click 'Draft Stop-Loss Alert,' review the pre-built email, and send. The data is governed, timestamped, and sourced from the same pipeline that feeds everything else."

5. **Sidebar Filters** — Service Category, State, Network (IN/OUT). Show how filtering to OUT-of-network reveals cost outliers.

### Transition

> "We found the expensive claims. Now let's make sure we have enough money set aside to pay the ones we haven't seen yet."

---

## Act VI: "The Piggy Bank" — IBNR Reserves (Page 5)

**Time:** 3-4 minutes  
**Vibe:** Serious (this is reserve adequacy), with a dash of "we made chain-ladder cool"  

### What to Show

1. **IBNR Methodology Banner** — Chain-ladder method, completion factors, run-off triangle. This is the standard, and we're implementing it properly.

   > **Talking Point:** "IBNR — Incurred But Not Reported. It's the actuarial equivalent of knowing you ate something questionable but not knowing the bill yet. The chain-ladder method uses historical claim development patterns to estimate what's still coming. It's been the gold standard for decades, and we've automated it end-to-end."

2. **KPIs** — Total IBNR Reserve, Paid to Date, Estimated Ultimate, Immature Months. "Immature months" = recent months where claims are still developing.

3. **Three Tabs:**

   **a. IBNR Reserve Waterfall** — Stacked bar chart with maturity colors (mature months in green, developing months in amber, immature months in red). Visual instant-read of where reserve uncertainty lives.

   **b. Completion Factor S-Curve** — The classic actuarial visualization. Threshold lines at 70%, 90%, 98% completion. Shows how quickly claims develop to ultimate.
   
   > **Talking Point:** "This S-curve is every actuary's best friend. It tells you: at 6 months, you've seen 70% of claims. At 12 months, 90%. At 18 months, 98%. The steeper the curve, the faster claims develop, and the less reserve uncertainty you carry. It's like watching bread rise — you know it's going to get there, the question is how fast."

   **c. Run-Off Triangle Heatmap** — The classic development triangle, but rendered as an interactive heatmap instead of a static Excel table. Colors indicate development speed.

4. **Action Bar — "Reserve Opinion Package"** — Generates a 6-component audit package including Bornhuetter-Ferguson comparison, data quality certification, and methodology disclosure.

   > **Talking Point:** "That 'Reserve Opinion Package' button just generated what would normally take an actuarial team two weeks to compile for an external audit. Six components: methodology documentation, data quality certification, BF comparison, sensitivity analysis, management discussion points, and a sign-off template. All sourced from governed data."

5. **IBNR Forecast Detail Table** — Exportable, sortable, filterable. The raw numbers behind the visuals.

### Transition

> "We know what we owe. Now the big question: can we pay less? That's where contract repricing comes in — and this is where the demo gets *really* fun."

---

## Act VII: "The Art of the Deal" — Contract Repricing (Page 6)

**Time:** 5-7 minutes (THIS IS THE "WOW" MOMENT — spend time here)  
**Vibe:** Showstopper energy, interactive, audience participation encouraged  

### What to Show

1. **"The Wow Moment" Banner** — The page literally introduces itself as the wow moment. Own it.

   > **Talking Point:** "Okay, this is the page where people usually put their phones down and start paying attention. Here's the scenario: Your network team just told you the Texas hospital system wants a rate increase. The CFO wants to know what happens if you push back with a 200 basis point reduction instead. In a traditional environment, that analysis takes a week. Here, it takes about 4 seconds. Watch."

2. **Scenario Parameters** — Five inline controls:
   - **Target State:** TX (default)
   - **Basis Point Adjustment:** Slider from -500 to +500 (default -200)
   - **Service Scope:** All Services / Inpatient Only / Outpatient Only
   - **Inpatient Pass-Through %:** 0-100% (default 100%)
   - **Outpatient Pass-Through %:** 0-100% (default 50%)

3. **Rate Factor Strip** — Shows `0.9800x` with color coding. This updates live as you move sliders.

   > **Talking Point:** "Five parameters, infinite combinations. Want to reduce only inpatient rates by 300 bps but leave outpatient alone? Three slider moves. Want to model a 150 bps increase limited to outpatient facility claims? Same thing. This isn't a one-size-fits-all model — it's a flight simulator for contract negotiations."

4. **Before vs. After KPIs** — Current MLR, Repriced MLR, Projected Savings, Scenario Counter.

5. **INTERACTIVE DEMO MOMENT — Move the sliders!**
   - Start at -200 bps. Show the savings.
   - Move to -350 bps. Watch savings increase.
   - Change to "Inpatient Only." Watch outpatient drop out.
   - Adjust IP Pass-Through to 75%. Savings decrease proportionally.
   
   > **Talking Point:** "Every time you move a slider, a stored procedure fires against the governed data in Snowflake. Same data. Same governance. Same audit trail. But now you're running 'what-if' scenarios in real-time instead of waiting for someone to update a spreadsheet."

6. **Save Scenario (UP TO 3)** — Save the current scenario as "Scenario A." Change parameters, save as "Scenario B." Change again, save as "Scenario C."

7. **Scenario Comparison** — Side-by-side KPI cards and a grouped bar chart comparing savings by service category across all saved scenarios.

   > **Talking Point:** "Three scenarios, side by side. Which one do you bring to the negotiation table? Scenario A is aggressive but realistic. Scenario B is conservative. Scenario C splits the difference. In the old world, each of these would be a separate analyst request. Here, you built all three in 90 seconds."

8. **Negotiation Brief** — Click "Negotiation Brief" in the action bar. A full professional document appears:
   - Executive Summary with financial impact
   - Contract clauses retrieved from **Cortex Search** (RAG over indexed contract PDFs)
   - Financial impact by service category in a formatted table
   - Market benchmark comparison (regional avg base rate, percentile rank, regional MLR, YoY cost trend)
   - Five recommended negotiation talking points tailored to the scenario
   - Data governance footer citing the Semantic View source
   - Copy-to-clipboard functionality

   > **Talking Point:** "Let me say that again: the system just wrote a negotiation brief. It pulled contract clauses using Cortex Search — that's Snowflake's RAG engine querying indexed provider agreements. It generated market benchmarks. It wrote five talking points customized to your specific scenario. And at the bottom, it tells you exactly where every number came from. This is AI you can actually trust because the data provenance is baked in."

9. **Category Impact / Monthly Forecast / Details Tabs** — Waterfall chart, monthly trend (current vs. repriced with shaded savings area), raw JSON for the technical audience.

10. **Technical Mode** — Show the REPRICE_CONTRACT stored procedure SQL, including the custom pass-through factor calculation.

### Transition

> "So we built the scenario, compared the options, and generated the negotiation brief. But how did we know to focus on Texas in the first place? That's where Trend Surveillance — our early warning system — comes in."

---

## Act VIII: "The Smoke Detector" — Trend Surveillance (Page 7)

**Time:** 3-4 minutes  
**Vibe:** "The system found this before we did"  

### What to Show

1. **Cortex ML Anomaly Alerts** — The Texas Behavioral Health alert is front and center, marked CRITICAL. It includes:
   - Percentage deviation from expected
   - Observed vs. expected unit cost
   - Contract reference (CPT 90837 at $177.43)
   - Root cause: 4.2% mid-year price adjustment clause

   > **Talking Point:** "This is where the story started. Cortex ML — Snowflake's built-in machine learning — analyzed 18 months of cost data, built a time-series model for every state-and-category combination, and flagged Texas Behavioral Health as statistically anomalous. It didn't just say 'costs went up.' It said 'costs went up 8% more than the model predicted, and here's the contract clause that caused it.' That's not a dashboard — that's an investigation report."

2. **Action Bar** — "Email Trend Report," "Export Surveillance Data," "Create Alert Rule."

3. **Create Alert Rule** — Click it. Configure state, category, and deviation threshold. This demonstrates that the system is extensible — you can set up custom monitoring rules.

   > **Talking Point:** "In production, this alert rule would configure a Snowflake Task — a serverless scheduled job — that monitors for anomalies and sends notifications. No cron jobs. No third-party scheduling tools. Just Snowflake, watching your data, 24/7."

4. **Cost Trend by Service Category** — Multi-line chart with all categories. Behavioral Health (orange line) diverges upward in recent months.

5. **Texas BH Deep Dive** — Dedicated chart with:
   - CPT 90837 baseline at $154.29 (blue dashed line)
   - Contract rate at $177.43 (red dotted line)
   - Anomaly period shaded in red
   - Root Cause Analysis card explaining the 4.2% price adjustment
   - Recommended Action card linking to Contract Repricing

   > **Talking Point:** "This is the 'aha' moment. The anomaly detection flagged it. The deep dive shows exactly when costs diverged. The root cause analysis explains *why* — a mid-year price adjustment clause in the provider contract. And the recommended action sends you directly to Contract Repricing to model the response. That's an end-to-end analytical workflow that connects detection to action without ever leaving the application."

6. **Observed vs. Pricing Assumptions** — Data table comparing actual costs to the assumptions baked into premiums. This is where trend breaks show up.

7. **Technical Mode** — Show the Cortex ML ANOMALY_DETECTION SQL.

### Transition

> "We've gone from detection to analysis to scenario modeling. But what if you just want to *ask a question* in plain English? That's what the Intelligence Agent is for."

---

## Act IX: "Ask It Anything" — Intelligence Agent (Page 8)

**Time:** 3-5 minutes  
**Vibe:** Futuristic, conversational, "this is the future of actuarial work"  

### What to Show

1. **Empty State** — Three quick-action tiles: "Reserve Adequacy," "Rate Filing," "MLR Rebate." These are pre-built conversation starters.

2. **Chat Interface** — Type a question in natural language. Suggested questions:
   - "What is our current MLR by line of business?"
   - "Why is Texas behavioral health cost trending up?"
   - "What contract clauses affect our BH reimbursement rates?"
   - "Generate a reserve adequacy summary for Q4"

   > **Talking Point:** "This is Snowflake Cortex Agents — an AI system that can query your governed data, search your indexed contracts, and generate answers grounded in facts, not hallucinations. Ask it about MLR, and it queries the Semantic View. Ask it about contract terms, and it searches the indexed provider agreements using Cortex Search. Ask it to generate a summary, and it uses Cortex Complete with Claude 3.5 Sonnet."

3. **Show the RAG in Action** — Ask about contract clauses. The agent retrieves relevant chunks from `AGENTS.CONTRACT_SEARCH_SERVICE` and cites them in its response.

   > **Talking Point:** "Notice the citations. The agent isn't making this up — it's pulling from indexed contract documents. This is Retrieval-Augmented Generation, running entirely inside Snowflake. Your contract data never leaves your security perimeter. No API calls to OpenAI. No data exfiltration risk. The AI runs where the data lives."

4. **Conversation Memory** — Ask a follow-up question that references the previous answer. The agent maintains context.

5. **Technical Mode** — Show the Cortex Search and Cortex Complete function calls.

### Transition

> "One more thing. Let's peek under the hood and see how all of this is connected."

---

## Act X: "The Blueprint" — Architecture (Page 9)

**Time:** 2-3 minutes  
**Vibe:** Technical credibility, "we didn't just build an app, we built a platform"  

### What to Show

1. **Overview Mode** — The simplified architecture showing Source Data > RAW > SILVER > GOLD > ML/Analytics > Consumers.

2. **Detailed Mode** — Every node, every arrow. Source systems (APCD feeds, enrollment, pharmacy, capitation, contracts). RAW tables. SILVER Dynamic Tables. GOLD Dynamic Tables and Semantic View. ML models (Forecast, Anomaly Detection). Cortex Agents. Consumer applications.

3. **Zoom Slider** — Scale from 50% to 150%. Show that large teams can zoom in on specific sections.

4. **Flow Highlighting** — This is the showstopper for the Architecture page:
   - Select "Flow: Executive Summary" — Watch the relevant nodes light up with a glow effect while everything else dims to 12% opacity. You can trace exactly which data sources, transformations, and models feed that specific page.
   - Select "Flow: Contract Repricing" — Different path lights up: includes the stored procedure, ML models, and Cortex Search.
   - Select "Flow: Intelligence Agent" — Shows how the agent connects to the Semantic View and Cortex Search.

   > **Talking Point:** "This isn't a static diagram. Pick any page from the dropdown, and the architecture highlights exactly which pipeline components power it. Executive Summary? It touches every layer. Intelligence Agent? It connects to the Semantic View and the contract search index. This is full data lineage, visualized interactively, for non-technical stakeholders."

5. **Hover Effects** — Hover over any node to see a glow effect and tooltip with details.

---

## The Closing Argument (2 minutes)

### Key Messages to Land

1. **Single Source of Truth:** "Every number on every page comes from the same governed Semantic View. There is no 'my spreadsheet says different.' There's one truth."

2. **Detection to Action:** "The workflow goes: Trend Surveillance *detects* the anomaly. Executive Summary *quantifies* the impact. Contract Repricing *models* the response. Intelligence Agent *answers* the follow-up questions. That's a complete analytical loop — no context switching, no tool hopping."

3. **AI You Can Trust:** "Cortex ML, Cortex Search, Cortex Complete — all running inside Snowflake's security perimeter. No data leaves. Every answer is grounded in governed data. Every calculation is auditable."

4. **Speed:** "What used to take days now takes seconds. What used to require five tools now requires one. What used to need a team of analysts now needs one actuary with a browser."

5. **The Snowflake Difference:** "This entire application — the data pipeline, the ML models, the AI agents, the governed analytics, the interactive UI — runs on *one platform*. Not stitched together with APIs and prayer. One platform, one security model, one governance framework. That's not an incremental improvement. That's a paradigm shift."

### Closing Line

> "We didn't build a dashboard. We built an actuarial operating system. And it runs on the only platform that could make it possible — Snowflake AI Data Cloud."

---

## Appendix: Objection Handling

| Objection | Response |
|-----------|----------|
| "We already have Power BI dashboards." | "Power BI shows you what happened. This shows you what happened, why it happened, what to do about it, and drafts the email to tell your boss. Also, the AI runs *inside* the data platform — no data movement, no governance gaps." |
| "Our actuaries use Excel/R/Python." | "So do ours — this isn't replacing those tools. It's replacing the *glue* between them: the manual data pulls, the copy-paste between systems, the 'which version of the file is current?' conversations. Your actuaries still think in R and Python. Now the platform speaks their language too." |
| "How much does this cost?" | "The entire demo runs on an X-SMALL warehouse with 60-second auto-suspend. That's the smallest compute Snowflake offers. In production, you'd scale the warehouse to match your data volume, but the architecture is the same. Serverless where possible, pay-per-second everywhere else." |
| "Is the data real?" | "The schema follows the APCD-CDL v3.0.1 standard — the same standard used by state All-Payer Claims Databases. The data is synthetic but structurally realistic: 10,000 members, 433,000 medical claims, proper DRG distributions, realistic lag patterns. In production, you'd point this at your actual claims warehouse." |
| "Can we customize it?" | "It's Streamlit — Python code running in Snowflake. Add a page, change a chart, add a filter. No vendor lock-in, no proprietary framework. If your team can write Python, they can extend this." |
| "What about security?" | "Everything runs inside Snowflake. Role-based access control, column-level masking, row-level security — all native. The AI models (Cortex) run inside the platform. No data leaves your account. No API calls to external LLM providers unless you choose to configure them." |

---

## Appendix: Object Inventory Quick Reference

| Schema | Object | Type | Row Count |
|--------|--------|------|-----------|
| GOLD | SYNTH_MEMBER_ELIGIBILITY | Table | 10,000 |
| GOLD | SYNTH_MEDICAL_CLAIMS | Table | 433,155 |
| GOLD | SYNTH_PHARMACY_CLAIMS | Table | 200,000 |
| GOLD | SYNTH_CAPITATION_PAYMENTS | Table | 164,459 |
| GOLD | SYNTH_PHARMACY_REBATES | Table | 200 |
| GOLD | CLAIMS_LAG_TRIANGLE | Table | 234 |
| GOLD | HCC_REFERENCE | Table | 12 |
| SILVER | MEMBER_ELIGIBILITY_CLEAN | Dynamic Table | 10,000 |
| SILVER | MEDICAL_CLAIMS_CLEAN | Dynamic Table | 386,185 |
| GOLD | FINANCIAL_SUMMARY | Dynamic Table | 3,924 |
| GOLD | TREND_SURVEILLANCE | Dynamic Table | 3,924 |
| GOLD | RISK_SCORE_SUMMARY | Dynamic Table | 452 |
| GOLD | IBNR_DEVELOPMENT | Dynamic Table | 234 |
| GOLD | ACTUARIAL_FINANCIAL_TRUTH | Semantic View | — |
| ANALYTICS | TREND_TIMESERIES | View | — |
| ANALYTICS | COST_TREND_FORECAST | Table | 1,875 |
| ANALYTICS | IBNR_FORECAST | Table | 24 |
| ANALYTICS | ANOMALY_ALERTS | Table | 2,777 |
| AGENTS | CONTRACT_CHUNKS | Table | 9 |
| AGENTS | CONTRACT_SEARCH_SERVICE | Cortex Search | 9 indexed |
| AGENTS | INVOKE_INTELLIGENCE_AGENT | Procedure | — |
| GOLD | REPRICE_CONTRACT | Procedure | — |
| GOLD | ACTUARIAL_COMMAND_CENTER | Streamlit | 10 pages |
