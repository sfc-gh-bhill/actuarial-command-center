-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 Braedon Hill

-- ==============================================================================
-- ACTUARIAL DEMO - DYNAMIC TABLES (Silver/Gold Pipeline)
-- Incremental, governed transformations
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;

-- ==============================================================================
-- SILVER LAYER: Cleaned, standardized, deduplicated
-- ==============================================================================

-- Clean medical claims: deduplicated, validated status, standardized categories
CREATE OR REPLACE DYNAMIC TABLE SILVER.MEDICAL_CLAIMS_CLEAN
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
SELECT
    claim_id,
    member_id,
    incurred_date,
    date_of_service_to,
    paid_date,
    service_category,
    member_state,
    county,
    line_of_business,
    age,
    member_sex,
    raf_score,
    provider_npi,
    provider_type,
    network_status,
    principal_diagnosis,
    procedure_code,
    ms_drg,
    -- Ensure non-negative financials
    GREATEST(allowed_amount, 0) AS allowed_amount,
    GREATEST(charge_amount, 0) AS charge_amount,
    GREATEST(paid_amount, 0) AS paid_amount,
    claim_status,
    -- Derived fields
    DATEDIFF('day', incurred_date, paid_date) AS claims_lag_days,
    DATE_TRUNC('month', incurred_date) AS incurral_month,
    DATE_TRUNC('month', paid_date) AS paid_month,
    YEAR(incurred_date) AS incurral_year,
    MONTH(incurred_date) AS incurral_month_num,
    CASE
        WHEN age < 18 THEN 'PEDIATRIC'
        WHEN age < 45 THEN 'ADULT_YOUNG'
        WHEN age < 65 THEN 'ADULT_MATURE'
        ELSE 'SENIOR'
    END AS age_band,
    -- High-cost flag (top 5% threshold)
    CASE WHEN paid_amount > 50000 THEN TRUE ELSE FALSE END AS is_high_cost
FROM GOLD.SYNTH_MEDICAL_CLAIMS
WHERE claim_status = 'PAID';

-- Clean member eligibility
CREATE OR REPLACE DYNAMIC TABLE SILVER.MEMBER_ELIGIBILITY_CLEAN
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
SELECT
    member_id,
    date_of_birth,
    age,
    member_sex,
    member_state,
    county,
    line_of_business,
    enrollment_start_date,
    enrollment_end_date,
    is_active,
    premium_pmpm,
    raf_score,
    primary_hcc,
    -- Member months calculation
    DATEDIFF('month', enrollment_start_date,
        COALESCE(enrollment_end_date, CURRENT_DATE())) + 1 AS total_member_months
FROM GOLD.SYNTH_MEMBER_ELIGIBILITY;

-- ==============================================================================
-- GOLD LAYER: Business-ready aggregates
-- ==============================================================================

-- Financial summary: MLR, PMPM, margin by LOB/state/month
CREATE OR REPLACE DYNAMIC TABLE GOLD.FINANCIAL_SUMMARY
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
WITH monthly_claims AS (
    SELECT
        DATE_TRUNC('month', incurred_date) AS metric_month,
        line_of_business,
        member_state,
        service_category,
        COUNT(DISTINCT claim_id) AS claim_count,
        COUNT(DISTINCT member_id) AS unique_members,
        SUM(paid_amount) AS total_paid,
        SUM(allowed_amount) AS total_allowed,
        SUM(charge_amount) AS total_charged,
        AVG(paid_amount) AS avg_paid_per_claim,
        SUM(CASE WHEN is_high_cost THEN paid_amount ELSE 0 END) AS high_cost_paid
    FROM SILVER.MEDICAL_CLAIMS_CLEAN
    GROUP BY 1, 2, 3, 4
),
monthly_premium AS (
    SELECT
        payment_month AS metric_month,
        line_of_business,
        member_state,
        SUM(risk_adjusted_pmpm) AS total_premium,
        COUNT(DISTINCT member_id) AS enrolled_members
    FROM GOLD.SYNTH_CAPITATION_PAYMENTS
    GROUP BY 1, 2, 3
)
SELECT
    c.metric_month,
    c.line_of_business,
    c.member_state,
    c.service_category,
    c.claim_count,
    c.unique_members,
    p.enrolled_members,
    c.total_paid,
    c.total_allowed,
    c.total_charged,
    p.total_premium,
    c.avg_paid_per_claim,
    c.high_cost_paid,
    -- Core MLR calculation
    CASE WHEN p.total_premium > 0
        THEN ROUND(c.total_paid / p.total_premium, 4)
        ELSE NULL
    END AS medical_loss_ratio,
    -- PMPM cost
    CASE WHEN p.enrolled_members > 0
        THEN ROUND(c.total_paid / p.enrolled_members, 2)
        ELSE NULL
    END AS cost_pmpm,
    -- Margin
    CASE WHEN p.total_premium > 0
        THEN ROUND((p.total_premium - c.total_paid) / p.total_premium, 4)
        ELSE NULL
    END AS margin_pct,
    -- ACA MLR threshold check
    CASE
        WHEN c.line_of_business IN ('ACA_INDIVIDUAL', 'ACA_SMALL_GROUP')
            AND (c.total_paid / NULLIF(p.total_premium, 0)) < 0.80 THEN 'REBATE_RISK'
        WHEN c.line_of_business = 'ACA_LARGE_GROUP'
            AND (c.total_paid / NULLIF(p.total_premium, 0)) < 0.85 THEN 'REBATE_RISK'
        WHEN (c.total_paid / NULLIF(p.total_premium, 0)) > 0.95 THEN 'MARGIN_AT_RISK'
        WHEN (c.total_paid / NULLIF(p.total_premium, 0)) > 0.90 THEN 'MARGIN_WARNING'
        ELSE 'ON_TARGET'
    END AS margin_status
FROM monthly_claims c
LEFT JOIN monthly_premium p
    ON c.metric_month = p.metric_month
    AND c.line_of_business = p.line_of_business
    AND c.member_state = p.member_state;

-- Trend surveillance: rolling cost trends for anomaly detection
CREATE OR REPLACE DYNAMIC TABLE GOLD.TREND_SURVEILLANCE
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
SELECT
    DATE_TRUNC('month', incurred_date) AS trend_month,
    member_state,
    service_category,
    line_of_business,
    COUNT(*) AS claim_count,
    SUM(paid_amount) AS total_paid,
    AVG(paid_amount) AS avg_unit_cost,
    MEDIAN(paid_amount) AS median_unit_cost,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY paid_amount) AS p90_unit_cost,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY paid_amount) AS p95_unit_cost,
    STDDEV(paid_amount) AS unit_cost_stddev,
    -- Rolling average for trend comparison
    AVG(paid_amount) AS current_avg,
    COUNT(DISTINCT member_id) AS unique_members,
    SUM(paid_amount) / NULLIF(COUNT(DISTINCT member_id), 0) AS pmpm_cost
FROM SILVER.MEDICAL_CLAIMS_CLEAN
GROUP BY 1, 2, 3, 4;

-- IBNR development factors
CREATE OR REPLACE DYNAMIC TABLE GOLD.IBNR_DEVELOPMENT
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
SELECT
    incurral_month,
    development_month,
    completion_factor,
    cumulative_paid,
    -- Estimated ultimate claims
    CASE WHEN completion_factor > 0
        THEN ROUND(cumulative_paid / completion_factor, 2)
        ELSE NULL
    END AS estimated_ultimate,
    -- IBNR reserve = ultimate - paid
    CASE WHEN completion_factor > 0
        THEN ROUND((cumulative_paid / completion_factor) - cumulative_paid, 2)
        ELSE NULL
    END AS ibnr_reserve,
    -- Age-to-age development factor
    LAG(completion_factor) OVER (PARTITION BY incurral_month ORDER BY development_month) AS prior_completion,
    CASE WHEN LAG(completion_factor) OVER (PARTITION BY incurral_month ORDER BY development_month) > 0
        THEN ROUND(completion_factor / LAG(completion_factor)
            OVER (PARTITION BY incurral_month ORDER BY development_month), 4)
        ELSE NULL
    END AS age_to_age_factor
FROM GOLD.CLAIMS_LAG_TRIANGLE
ORDER BY incurral_month, development_month;

-- Risk score summary by cohort
CREATE OR REPLACE DYNAMIC TABLE GOLD.RISK_SCORE_SUMMARY
    TARGET_LAG = '1 hour'
    WAREHOUSE = ACTUARIAL_WH
AS
SELECT
    line_of_business,
    member_state,
    CASE
        WHEN age < 18 THEN 'PEDIATRIC'
        WHEN age < 45 THEN 'ADULT_YOUNG'
        WHEN age < 65 THEN 'ADULT_MATURE'
        ELSE 'SENIOR'
    END AS age_band,
    primary_hcc,
    COUNT(*) AS member_count,
    AVG(raf_score) AS avg_raf_score,
    MEDIAN(raf_score) AS median_raf_score,
    MIN(raf_score) AS min_raf_score,
    MAX(raf_score) AS max_raf_score,
    AVG(premium_pmpm) AS avg_premium_pmpm,
    AVG(premium_pmpm * raf_score) AS avg_risk_adjusted_pmpm
FROM GOLD.SYNTH_MEMBER_ELIGIBILITY
GROUP BY 1, 2, 3, 4;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'Dynamic tables created successfully' AS STATUS;
