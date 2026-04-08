-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 Braedon Hill

-- ==============================================================================
-- ACTUARIAL DEMO - SEMANTIC VIEW (Truth Layer)
-- Single source of truth for both Streamlit dashboard and Cortex Agent
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;
USE SCHEMA GOLD;

-- ==============================================================================
-- THE ACTUARIAL FINANCIAL TRUTH SEMANTIC VIEW
-- This is the "secret weapon" - both the dashboard and the AI agent
-- query this exact same governed object
-- ==============================================================================

CREATE OR REPLACE SEMANTIC VIEW GOLD.ACTUARIAL_FINANCIAL_TRUTH

    TABLES (
        claims AS ACTUARIAL_DEMO.SILVER.MEDICAL_CLAIMS_CLEAN
            PRIMARY KEY (claim_id)
            COMMENT = 'Cleaned medical claims with standardized categories and cost fields',

        enrollment AS ACTUARIAL_DEMO.SILVER.MEMBER_ELIGIBILITY_CLEAN
            PRIMARY KEY (member_id)
            COMMENT = 'Member enrollment with demographics, LOB, and risk scores',

        financial AS ACTUARIAL_DEMO.GOLD.FINANCIAL_SUMMARY
            PRIMARY KEY (metric_month, line_of_business, member_state, service_category)
            COMMENT = 'Pre-aggregated financial metrics by LOB, state, month, and service category'
    )

    RELATIONSHIPS (
        claims (member_id) REFERENCES enrollment
    )

    -- ================================================================
    -- FACTS: Row-level numerical attributes
    -- ================================================================
    FACTS (
        -- Claims financial fields
        claims.paid_amount
            COMMENT = 'Plan paid amount after member cost-sharing (APCD-CDL CDLMC125)',
        claims.allowed_amount
            COMMENT = 'Contracted reimbursement ceiling (APCD-CDL CDLMC131)',
        claims.charge_amount
            COMMENT = 'Raw billed amount from provider (APCD-CDL CDLMC123)',
        claims.incurred_date
            COMMENT = 'Date of service (APCD-CDL CDLMC119)',
        claims.paid_date
            COMMENT = 'Claim adjudication/payment date (APCD-CDL CDLMC024)',
        claims.claims_lag_days
            COMMENT = 'Days between incurred and paid date for IBNR modeling',

        -- Enrollment financial fields
        enrollment.premium_pmpm
            COMMENT = 'Monthly premium revenue per member',
        enrollment.raf_score
            COMMENT = 'CMS-HCC v28 Risk Adjustment Factor score',

        -- Pre-aggregated financials
        financial.total_paid
            COMMENT = 'Aggregate paid claims for the period',
        financial.total_premium
            COMMENT = 'Aggregate premium revenue for the period',
        financial.medical_loss_ratio
            COMMENT = 'Pre-calculated MLR = total_paid / total_premium',
        financial.cost_pmpm
            COMMENT = 'Per Member Per Month medical cost',
        financial.margin_pct
            COMMENT = 'Margin percentage = (premium - paid) / premium'
    )

    -- ================================================================
    -- DIMENSIONS: Categorical attributes for filtering and grouping
    -- ================================================================
    DIMENSIONS (
        -- Business dimensions
        enrollment.line_of_business
            WITH SYNONYMS = ('LOB', 'market', 'product', 'segment', 'business line')
            COMMENT = 'Line of business: ACA_INDIVIDUAL, ACA_SMALL_GROUP, ACA_LARGE_GROUP, MEDICARE_ADVANTAGE, MEDICAID_MANAGED',

        claims.service_category
            WITH SYNONYMS = ('claim type', 'service type', 'category of service', 'type of care')
            COMMENT = 'Service category: INPATIENT, OUTPATIENT_PROFESSIONAL, OUTPATIENT_FACILITY, BEHAVIORAL_HEALTH, EMERGENCY, OTHER',

        -- Geographic dimensions
        claims.member_state
            WITH SYNONYMS = ('state', 'geography', 'region', 'location')
            COMMENT = 'Member state of residence (e.g., TX, MN, FL)',
        claims.county
            COMMENT = 'County within state (e.g., HENNEPIN, HARRIS, DALLAS)',

        -- Provider dimensions
        claims.provider_type
            WITH SYNONYMS = ('provider category', 'provider class')
            COMMENT = 'Provider type: FACILITY, PROFESSIONAL, BEHAVIORAL_HEALTH_PROVIDER',
        claims.network_status
            WITH SYNONYMS = ('in network', 'out of network', 'network')
            COMMENT = 'Network status: IN or OUT',

        -- Clinical dimensions
        claims.principal_diagnosis
            WITH SYNONYMS = ('diagnosis', 'ICD-10', 'dx code')
            COMMENT = 'Primary ICD-10 diagnosis code',
        claims.procedure_code
            WITH SYNONYMS = ('CPT', 'HCPCS', 'procedure')
            COMMENT = 'CPT/HCPCS procedure code',
        claims.ms_drg
            WITH SYNONYMS = ('DRG', 'diagnosis related group')
            COMMENT = 'MS-DRG code for inpatient claims',
        enrollment.primary_hcc
            WITH SYNONYMS = ('HCC', 'condition category', 'risk category')
            COMMENT = 'Primary CMS-HCC v28 condition category',

        -- Demographic dimensions
        claims.age_band
            COMMENT = 'Age band: PEDIATRIC, ADULT_YOUNG, ADULT_MATURE, SENIOR',
        enrollment.member_sex
            WITH SYNONYMS = ('sex', 'gender')
            COMMENT = 'Member sex: M or F',

        -- Time dimensions
        claims.incurral_month
            WITH SYNONYMS = ('month', 'service month', 'incurred month')
            COMMENT = 'Month the service was incurred',

        -- Status dimensions
        financial.margin_status
            WITH SYNONYMS = ('MLR status', 'margin alert', 'financial status')
            COMMENT = 'Margin status: ON_TARGET, MARGIN_WARNING, MARGIN_AT_RISK, REBATE_RISK'
    )

    -- ================================================================
    -- METRICS: Aggregate measures with governed calculation logic
    -- These are THE source of truth for all financial reporting
    -- ================================================================
    METRICS (
        -- Core financial metrics
        claims.total_medical_expense AS SUM(claims.paid_amount)
            COMMENT = 'Total aggregate claim liability across all paid claims',

        enrollment.total_premium_revenue AS SUM(enrollment.premium_pmpm)
            COMMENT = 'Total aggregate premium revenue',

        claims.mlr AS SUM(claims.paid_amount) / NULLIF(SUM(enrollment.premium_pmpm), 0)
            COMMENT = 'Health Plan Co.l Loss Ratio: total paid claims / total premium revenue. ACA threshold: 80% individual/small group, 85% large group',

        claims.margin AS (SUM(enrollment.premium_pmpm) - SUM(claims.paid_amount)) / NULLIF(SUM(enrollment.premium_pmpm), 0)
            COMMENT = 'Operating margin: (premium - claims) / premium',

        claims.avg_cost_per_claim AS AVG(claims.paid_amount)
            COMMENT = 'Average paid amount per claim',

        claims.claim_volume AS COUNT(claims.claim_id)
            COMMENT = 'Total number of claims',

        claims.high_cost_claim_pct AS SUM(CASE WHEN claims.is_high_cost THEN 1 ELSE 0 END) / NULLIF(COUNT(claims.claim_id), 0)
            COMMENT = 'Percentage of claims exceeding high-cost threshold ($50K)',

        claims.avg_claims_lag AS AVG(claims.claims_lag_days)
            COMMENT = 'Average days between service and payment for IBNR estimation'
    )

    COMMENT = 'Governed actuarial truth layer. Both the Streamlit dashboard and the Cortex Intelligence Agent query this single semantic view to ensure reconcilable, CFO-level financial reporting. MLR, margin, PMPM, and risk metrics are centrally defined here.';

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'Semantic view ACTUARIAL_FINANCIAL_TRUTH created successfully' AS STATUS;
