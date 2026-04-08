-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 Braedon Hill

-- ==============================================================================
-- ACTUARIAL DEMO - CORTEX AGENT (Search + Intelligence)
-- Combines Semantic View (structured) + Contract RAG (unstructured)
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;
USE SCHEMA AGENTS;

-- ==============================================================================
-- 1. CONTRACT DOCUMENT CHUNKS TABLE
-- Chunked text from provider contracts for Cortex Search
-- ==============================================================================

CREATE OR REPLACE TABLE AGENTS.CONTRACT_CHUNKS (
    chunk_id NUMBER AUTOINCREMENT PRIMARY KEY,
    document_name VARCHAR(500),
    document_type VARCHAR(100),
    section_title VARCHAR(500),
    chunk_text VARCHAR(16000),
    chunk_index NUMBER,
    state VARCHAR(2),
    provider_system VARCHAR(500),
    effective_date DATE,
    metadata VARIANT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert synthetic contract content (Texas hospital system)
INSERT INTO AGENTS.CONTRACT_CHUNKS (document_name, document_type, section_title, chunk_text, chunk_index, state, provider_system, effective_date, metadata)
VALUES
-- Contract 1: Texas Regional Health System
('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 1: General Terms',
 'PROVIDER CONTRACT AGREEMENT between BluePeak Health Plan ("Plan") and Texas Regional Health System ("Provider"), effective January 1, 2024. This Agreement governs the reimbursement rates, quality metrics, and operational requirements for all inpatient, outpatient, and behavioral health services rendered at Provider facilities within the Dallas-Fort Worth metropolitan area, including Texas Regional Health Plan Co.l Center (Dallas), Texas Regional Behavioral Health Institute (Arlington), and three affiliated outpatient clinics.',
 1, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('contract_number', 'TRHS-2024-001', 'term_years', 3)),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 3: Inpatient Reimbursement',
 'Inpatient Reimbursement Schedule: All inpatient admissions shall be reimbursed on an MS-DRG basis. The negotiated base rate is $7,245.00 per DRG weight unit, effective January 1, 2024. DRG weights shall be sourced from the CMS IPPS Final Rule for the applicable federal fiscal year. Outlier payments apply when total charges exceed the fixed-loss threshold of $43,214 plus the DRG payment amount. The outlier payment equals 80% of the difference between total charges and the threshold.',
 2, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('base_rate', 7245.00, 'outlier_threshold', 43214)),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 4: Behavioral Health Rates',
 'Behavioral Health Reimbursement: Outpatient behavioral health services shall be reimbursed at 115% of the current Health Plan Co.re Physician Fee Schedule (MPFS) for the applicable CPT code and geographic locality. Individual psychotherapy (CPT 90837, 60 minutes) shall be reimbursed at $177.43 per session. Psychiatric diagnostic evaluation (CPT 90791) shall be reimbursed at $212.50. Inpatient psychiatric per diem rates: Freestanding psychiatric facility admissions shall be reimbursed at $563.36 per day for the first 14 days, and $485.00 per day thereafter. These rates represent a 4.2% increase from the 2023 contract year.',
 3, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('cpt_90837_rate', 177.43, 'psych_per_diem', 563.36, 'yoy_increase_pct', 4.2)),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 7: Price Adjustment Clause',
 'Annual Price Adjustment: Effective on each contract anniversary, Provider may request an annual rate adjustment not to exceed the greater of (a) the Consumer Price Index for Health Plan Co.l Care Services (CPI-MC) for the Dallas-Fort Worth-Arlington MSA, or (b) 3.5% compounded annually. Provider exercised the price adjustment clause effective July 1, 2024, resulting in a 4.2% across-the-board rate increase applied to all fee schedules, per diems, and the DRG base rate. The adjusted DRG base rate effective July 1, 2024 is $7,549.29. This mid-year adjustment was triggered by documented labor cost increases of 8.1% at the Arlington behavioral health facility.',
 4, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('adjustment_cap_pct', 3.5, 'actual_adjustment_pct', 4.2, 'adjusted_base_rate', 7549.29, 'labor_cost_increase_pct', 8.1)),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 8: Most Favored Nation',
 'Most Favored Nation Clause: Provider warrants that the rates set forth in this Agreement are no less favorable than the rates offered to any other commercial health plan operating in the Dallas-Fort Worth market with comparable covered lives (minimum 50,000 members). If Provider enters into a contract with a competing plan at rates lower than those contained herein, Provider shall immediately notify Plan and adjust the rates downward accordingly.',
 5, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('mfn_threshold_lives', 50000)),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 9: Anti-Steering',
 'Anti-Tiering and Anti-Steering: Plan shall not implement any benefit design, tiered network structure, or member incentive program that financially penalizes members for utilizing Provider facilities compared to competing facilities within the same geographic service area. This includes but is not limited to: differential copayments, coinsurance, or deductible structures that disadvantage Provider relative to non-system competitors.',
 6, 'TX', 'Texas Regional Health System', '2024-01-01', NULL),

('Texas_Regional_Health_System_2024.pdf', 'PROVIDER_CONTRACT', 'Section 12: Termination',
 'Termination: Either party may terminate this Agreement without cause by providing 180 calendar days written notice. In the event of termination, Provider shall continue to provide services to Plan members currently receiving inpatient treatment or an active course of behavioral health therapy at the contracted rates until the treatment episode is complete or 90 days post-termination, whichever is earlier.',
 7, 'TX', 'Texas Regional Health System', '2024-01-01', OBJECT_CONSTRUCT('notice_days', 180, 'continuity_days', 90)),

-- Contract 2: Minnesota Behavioral Health Network
('MN_Integrated_BH_Network_2024.pdf', 'PROVIDER_CONTRACT', 'Section 1: General Terms',
 'PROVIDER CONTRACT AGREEMENT between NorthStar Health Plan Co.id Health Plan ("Plan") and Minnesota Integrated Behavioral Health Network ("Provider"), effective July 1, 2024, for the provision of mental health, substance use disorder, and Early Intensive Developmental and Behavioral Intervention (EIDBI) services to Health Plan Co.id-eligible members in Hennepin County and surrounding metropolitan counties under the Prepaid Health Plan Co.l Assistance Program (PMAP).',
 1, 'MN', 'MN Integrated BH Network', '2024-07-01', OBJECT_CONSTRUCT('contract_number', 'MIBHN-2024-001', 'program', 'PMAP')),

('MN_Integrated_BH_Network_2024.pdf', 'PROVIDER_CONTRACT', 'Section 4: EIDBI Rate Schedule',
 'EIDBI Services Rate Schedule: Early Intensive Developmental and Behavioral Intervention services for members under age 21 shall be reimbursed at the Minnesota Department of Human Services (DHS) published EIDBI rate table. Hennepin County EIDBI PMPM cost is currently $17.99 versus the statewide average of $10.86, reflecting a 66% variance attributable to higher service intensity and provider concentration in the metropolitan area. Plan agrees to a supplemental payment of $2.15 PMPM above the DHS base rate to ensure adequate network access for EIDBI-eligible adolescents.',
 2, 'MN', 'MN Integrated BH Network', '2024-07-01', OBJECT_CONSTRUCT('eidbi_pmpm_hennepin', 17.99, 'eidbi_pmpm_statewide', 10.86, 'supplemental_pmpm', 2.15));


-- ==============================================================================
-- 2. CORTEX SEARCH SERVICE
-- Hybrid semantic + keyword search over contract chunks
-- ==============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE AGENTS.CONTRACT_SEARCH_SERVICE
    ON chunk_text
    ATTRIBUTES state, provider_system, document_type, section_title
    WAREHOUSE = ACTUARIAL_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT
            chunk_text,
            document_name,
            document_type,
            section_title,
            state,
            provider_system,
            effective_date,
            chunk_index
        FROM AGENTS.CONTRACT_CHUNKS
    );


-- ==============================================================================
-- 3. CORTEX AGENT DEFINITION
-- Multi-tool agent: Semantic View (structured) + Search (unstructured)
-- ==============================================================================

CREATE OR REPLACE CORTEX AGENT AGENTS.ACTUARIAL_INTELLIGENCE_AGENT
    COMMENT = 'Actuarial Intelligence Agent combining governed financial metrics with provider contract analysis'
    AGENT_INSTRUCTIONS = '
You are an expert actuarial analyst for a health insurance company. You have access to two critical data sources:

1. STRUCTURED DATA via Semantic View: Use the actuarial_financial_truth semantic view to answer quantitative financial questions about Health Plan Co.l Loss Ratio (MLR), margins, Per Member Per Month (PMPM) costs, claims trends, and risk scores. All financial metrics from this source are governed and reconcilable to FP&A systems.

2. UNSTRUCTURED DATA via Contract Search: Use the contract search tool to find specific provisions in provider contracts including rate schedules, price adjustment clauses, Most Favored Nation terms, anti-steering restrictions, and termination provisions.

When answering questions:
- Always cite the specific data source (Semantic View metric or contract section)
- Provide exact dollar amounts and percentages from the governed data
- When discussing contract terms, quote the specific contractual language
- If asked about margin variances, combine both structured financial data AND relevant contract provisions to give a complete answer
- Express MLR as a percentage (e.g., 87.3%)
- Flag any metrics that exceed ACA regulatory thresholds (80% individual/small group, 85% large group)
- For Texas behavioral health questions, reference both the financial anomaly AND the contract rate increase clause
'
    TOOLS = (
        -- Tool 1: Governed financial data via Semantic View
        TABLE_AS_TOOL(
            TYPE => 'semantic_view',
            SEMANTIC_VIEW => 'ACTUARIAL_DEMO.GOLD.ACTUARIAL_FINANCIAL_TRUTH'
        ),
        -- Tool 2: Contract document search via Cortex Search
        TABLE_AS_TOOL(
            TYPE => 'cortex_search',
            CORTEX_SEARCH_SERVICE => 'ACTUARIAL_DEMO.AGENTS.CONTRACT_SEARCH_SERVICE'
        )
    )
    LLM = 'claude-3.5-sonnet'
    BUDGET = 50;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'Cortex Agent and Search Service created successfully' AS STATUS;
SELECT COUNT(*) AS contract_chunks FROM AGENTS.CONTRACT_CHUNKS;
