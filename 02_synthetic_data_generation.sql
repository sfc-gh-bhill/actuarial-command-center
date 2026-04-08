-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 Braedon Hill

-- ==============================================================================
-- ACTUARIAL DEMO - SYNTHETIC DATA GENERATION
-- APCD-CDL standard tables with actuarially realistic distributions
-- Gamma (outpatient), Lognormal (inpatient), Poisson (frequency)
-- Geographic scenarios: Texas BH anomaly + Hennepin County MN Health Plan Co.id
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;
USE SCHEMA GOLD;

-- ==============================================================================
-- 1. MEMBER ELIGIBILITY (APCD-CDL Enrollment File)
-- 10,000 members across ACA, Health Plan Co.re Advantage, Health Plan Co.id
-- Geographic split: TX (~50%), MN (~25%), Other (~25%)
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.SYNTH_MEMBER_ELIGIBILITY AS
WITH member_seed AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) AS member_seq,
        'MBR-' || LPAD(ROW_NUMBER() OVER (ORDER BY SEQ4()), 8, '0') AS member_id,
        DATEADD('year', -UNIFORM(18, 85, RANDOM()), CURRENT_DATE()) AS date_of_birth,
        DATEDIFF('year', DATEADD('year', -UNIFORM(18, 85, RANDOM()), CURRENT_DATE()), CURRENT_DATE()) AS age,
        CASE WHEN UNIFORM(0, 100, RANDOM()) < 52 THEN 'F' ELSE 'M' END AS member_sex,
        -- Geographic distribution: 50% TX, 25% MN, 25% other
        CASE
            WHEN UNIFORM(0, 100, RANDOM()) < 50 THEN 'TX'
            WHEN UNIFORM(0, 100, RANDOM()) < 75 THEN 'MN'
            ELSE ARRAY_CONSTRUCT('FL','CA','NY','OH','PA','IL','GA','NC')[UNIFORM(0,7,RANDOM())]::VARCHAR
        END AS member_state,
        -- LOB assignment weighted by age and state
        CASE
            WHEN UNIFORM(0, 100, RANDOM()) < 40 THEN 'ACA_INDIVIDUAL'
            WHEN UNIFORM(0, 100, RANDOM()) < 65 THEN 'ACA_SMALL_GROUP'
            WHEN UNIFORM(0, 100, RANDOM()) < 80 THEN 'ACA_LARGE_GROUP'
            WHEN UNIFORM(0, 100, RANDOM()) < 92 THEN 'MEDICARE_ADVANTAGE'
            ELSE 'MEDICAID_MANAGED'
        END AS line_of_business
    FROM TABLE(GENERATOR(ROWCOUNT => 10000))
),
-- Override: MN members skew toward Health Plan Co.id
adjusted AS (
    SELECT
        member_id,
        date_of_birth,
        DATEDIFF('year', date_of_birth, CURRENT_DATE()) AS age,
        member_sex,
        member_state,
        -- MN members: 60% Health Plan Co.id, rest split
        CASE
            WHEN member_state = 'MN' AND UNIFORM(0, 100, RANDOM()) < 60 THEN 'MEDICAID_MANAGED'
            WHEN member_state = 'MN' AND UNIFORM(0, 100, RANDOM()) < 80 THEN 'ACA_INDIVIDUAL'
            WHEN member_state = 'MN' THEN 'ACA_SMALL_GROUP'
            -- MA members must be 65+
            WHEN line_of_business = 'MEDICARE_ADVANTAGE' AND DATEDIFF('year', date_of_birth, CURRENT_DATE()) < 65
                THEN 'ACA_INDIVIDUAL'
            ELSE line_of_business
        END AS line_of_business,
        -- Hennepin County flag for MN Health Plan Co.id
        CASE
            WHEN member_state = 'MN' AND UNIFORM(0, 100, RANDOM()) < 45 THEN 'HENNEPIN'
            WHEN member_state = 'MN' THEN ARRAY_CONSTRUCT('RAMSEY','DAKOTA','ANOKA','WASHINGTON')[UNIFORM(0,3,RANDOM())]::VARCHAR
            WHEN member_state = 'TX' THEN ARRAY_CONSTRUCT('HARRIS','DALLAS','TARRANT','BEXAR','TRAVIS')[UNIFORM(0,4,RANDOM())]::VARCHAR
            ELSE NULL
        END AS county,
        DATEADD('month', -UNIFORM(1, 36, RANDOM()), CURRENT_DATE()) AS enrollment_start_date,
        CASE WHEN UNIFORM(0, 100, RANDOM()) < 85 THEN NULL
             ELSE DATEADD('month', -UNIFORM(0, 6, RANDOM()), CURRENT_DATE())
        END AS enrollment_end_date
    FROM member_seed
)
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
    CASE WHEN enrollment_end_date IS NULL THEN TRUE ELSE FALSE END AS is_active,
    -- Monthly premium revenue varies by LOB
    CASE
        WHEN line_of_business = 'ACA_INDIVIDUAL' THEN ROUND(450 + UNIFORM(0, 350, RANDOM()), 2)
        WHEN line_of_business = 'ACA_SMALL_GROUP' THEN ROUND(550 + UNIFORM(0, 250, RANDOM()), 2)
        WHEN line_of_business = 'ACA_LARGE_GROUP' THEN ROUND(500 + UNIFORM(0, 200, RANDOM()), 2)
        WHEN line_of_business = 'MEDICARE_ADVANTAGE' THEN ROUND(900 + UNIFORM(0, 400, RANDOM()), 2)
        WHEN line_of_business = 'MEDICAID_MANAGED' THEN ROUND(350 + UNIFORM(0, 200, RANDOM()), 2)
    END AS premium_pmpm,
    -- CMS-HCC RAF score (v28 constrained)
    ROUND(
        CASE
            WHEN line_of_business = 'MEDICARE_ADVANTAGE' THEN 0.8 + (UNIFORM(0, 200, RANDOM()) / 100.0)
            WHEN line_of_business = 'MEDICAID_MANAGED' THEN 0.6 + (UNIFORM(0, 150, RANDOM()) / 100.0)
            ELSE 0.5 + (UNIFORM(0, 100, RANDOM()) / 100.0)
        END
    , 3) AS raf_score,
    -- HCC conditions (v28 model - constrained diabetes and CHF)
    CASE
        WHEN UNIFORM(0, 100, RANDOM()) < 25 THEN 'HCC 37'   -- Diabetes (constrained equal to HCC 36, 38)
        WHEN UNIFORM(0, 100, RANDOM()) < 15 THEN 'HCC 225'  -- CHF (constrained equal to HCC 224, 226)
        WHEN UNIFORM(0, 100, RANDOM()) < 10 THEN 'HCC 18'   -- Pancreatic Cancer
        WHEN UNIFORM(0, 100, RANDOM()) < 8  THEN 'HCC 112'  -- COPD
        WHEN UNIFORM(0, 100, RANDOM()) < 5  THEN 'HCC 48'   -- Coagulation Defects
        ELSE NULL
    END AS primary_hcc
FROM adjusted;


-- ==============================================================================
-- 2. MEDICAL CLAIMS (APCD-CDL Health Plan Co.l Claims File)
-- ~500K claims with proper severity distributions
-- Gamma for outpatient, Lognormal for inpatient
-- Texas BH anomaly injected into recent months
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.SYNTH_MEDICAL_CLAIMS AS
WITH claim_base AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) AS claim_seq,
        'CLM-' || LPAD(ROW_NUMBER() OVER (ORDER BY SEQ4()), 10, '0') AS claim_id,
        -- Random member assignment
        'MBR-' || LPAD(UNIFORM(1, 10000, RANDOM()), 8, '0') AS member_id,
        -- Service date: last 24 months
        DATEADD('day', -UNIFORM(0, 730, RANDOM()), CURRENT_DATE()) AS date_of_service_from,
        -- Service category distribution
        CASE
            WHEN UNIFORM(0, 100, RANDOM()) < 45 THEN 'OUTPATIENT_PROFESSIONAL'
            WHEN UNIFORM(0, 100, RANDOM()) < 65 THEN 'OUTPATIENT_FACILITY'
            WHEN UNIFORM(0, 100, RANDOM()) < 80 THEN 'INPATIENT'
            WHEN UNIFORM(0, 100, RANDOM()) < 90 THEN 'BEHAVIORAL_HEALTH'
            WHEN UNIFORM(0, 100, RANDOM()) < 95 THEN 'EMERGENCY'
            ELSE 'OTHER'
        END AS service_category
    FROM TABLE(GENERATOR(ROWCOUNT => 500000))
),
-- Join to get member demographics
with_member AS (
    SELECT
        c.*,
        m.member_state,
        m.county,
        m.line_of_business,
        m.age,
        m.member_sex,
        m.raf_score
    FROM claim_base c
    LEFT JOIN GOLD.SYNTH_MEMBER_ELIGIBILITY m ON c.member_id = m.member_id
),
-- Apply actuarial cost distributions
with_costs AS (
    SELECT
        claim_id,
        member_id,
        date_of_service_from,
        CASE
            WHEN service_category = 'INPATIENT'
                THEN DATEADD('day', UNIFORM(1, 14, RANDOM()), date_of_service_from)
            ELSE date_of_service_from
        END AS date_of_service_to,
        service_category,
        member_state,
        county,
        line_of_business,
        age,
        member_sex,
        raf_score,

        -- Provider assignment
        'NPI-' || LPAD(UNIFORM(1, 500, RANDOM()), 10, '0') AS provider_npi,
        CASE
            WHEN service_category IN ('INPATIENT','EMERGENCY') THEN 'FACILITY'
            WHEN service_category = 'BEHAVIORAL_HEALTH' THEN 'BEHAVIORAL_HEALTH_PROVIDER'
            ELSE 'PROFESSIONAL'
        END AS provider_type,

        -- Network status (90% in-network)
        CASE WHEN UNIFORM(0, 100, RANDOM()) < 90 THEN 'IN' ELSE 'OUT' END AS network_status,

        -- Diagnosis codes
        CASE
            WHEN service_category = 'BEHAVIORAL_HEALTH'
                THEN ARRAY_CONSTRUCT('F32.1','F33.0','F41.1','F43.10','F90.0')[UNIFORM(0,4,RANDOM())]::VARCHAR
            WHEN service_category = 'INPATIENT'
                THEN ARRAY_CONSTRUCT('I50.9','J18.9','S72.001A','K80.10','N17.9')[UNIFORM(0,4,RANDOM())]::VARCHAR
            WHEN service_category = 'EMERGENCY'
                THEN ARRAY_CONSTRUCT('R07.9','S01.01XA','R55','T78.2XXA','R10.9')[UNIFORM(0,4,RANDOM())]::VARCHAR
            ELSE ARRAY_CONSTRUCT('E11.9','I10','J06.9','M54.5','Z00.00')[UNIFORM(0,4,RANDOM())]::VARCHAR
        END AS principal_diagnosis,

        -- Procedure codes
        CASE
            WHEN service_category = 'BEHAVIORAL_HEALTH'
                THEN ARRAY_CONSTRUCT('90837','90834','90847','90791','H0032')[UNIFORM(0,4,RANDOM())]::VARCHAR
            WHEN service_category = 'INPATIENT'
                THEN ARRAY_CONSTRUCT('99223','99291','43239','27236','47562')[UNIFORM(0,4,RANDOM())]::VARCHAR
            WHEN service_category = 'EMERGENCY'
                THEN ARRAY_CONSTRUCT('99285','99284','99283','99282','99281')[UNIFORM(0,4,RANDOM())]::VARCHAR
            ELSE ARRAY_CONSTRUCT('99213','99214','99215','99203','99204')[UNIFORM(0,4,RANDOM())]::VARCHAR
        END AS procedure_code,

        -- MS-DRG for inpatient
        CASE
            WHEN service_category = 'INPATIENT'
                THEN ARRAY_CONSTRUCT('470','871','291','392','481','194','065','690')[UNIFORM(0,7,RANDOM())]::VARCHAR
            ELSE NULL
        END AS ms_drg,

        -- ============================================================
        -- COST DISTRIBUTIONS: The actuarial heart of the data
        -- ============================================================
        -- Gamma distribution via Box-Muller approximation:
        --   X ~ Gamma(shape, scale) approximated via transformed normals
        -- Lognormal: exp(mu + sigma * Z) where Z ~ N(0,1)
        --
        -- Box-Muller: Z = SQRT(-2 * LN(U1)) * COS(2 * PI * U2)
        -- ============================================================

        UNIFORM(0.0001, 0.9999, RANDOM()) AS u1,
        UNIFORM(0.0001, 0.9999, RANDOM()) AS u2,

        -- ============================================================
        -- TEXAS BEHAVIORAL HEALTH ANOMALY INJECTION
        -- For TX + BH + recent 6 months: inflate costs 8% above baseline
        -- CPT 90837 baseline: ~$154.29
        -- Psych per diem baseline: ~$540-$563
        -- ============================================================
        CASE
            WHEN member_state = 'TX'
                 AND service_category = 'BEHAVIORAL_HEALTH'
                 AND date_of_service_from >= DATEADD('month', -6, CURRENT_DATE())
                THEN 1.08
            ELSE 1.00
        END AS tx_bh_anomaly_factor

    FROM with_member
)
SELECT
    claim_id,
    member_id,
    date_of_service_from AS incurred_date,
    date_of_service_to,
    -- Paid date: claims lag (Poisson-distributed days after service)
    DATEADD('day',
        LEAST(GREATEST(ROUND(
            CASE
                WHEN service_category = 'INPATIENT' THEN 30 + UNIFORM(0, 90, RANDOM())
                WHEN service_category = 'BEHAVIORAL_HEALTH' THEN 21 + UNIFORM(0, 60, RANDOM())
                ELSE 14 + UNIFORM(0, 45, RANDOM())
            END
        ), 1), 180),
        date_of_service_from
    ) AS paid_date,
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

    -- ============================================================
    -- ALLOWED AMOUNT (the contracted rate ceiling)
    -- Outpatient: Gamma distribution (shape=2, scale varies)
    -- Inpatient: Lognormal distribution
    -- BH: anchored to real TX benchmarks
    -- ============================================================
    ROUND(
        CASE
            -- INPATIENT: Lognormal(mu=9.5, sigma=0.8) -> median ~$13,360
            WHEN service_category = 'INPATIENT' THEN
                EXP(9.5 + 0.8 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
                * tx_bh_anomaly_factor

            -- BEHAVIORAL HEALTH: Anchored to TX benchmarks
            -- Outpatient BH (90837): ~$154.29 base via Gamma
            -- Inpatient psych: ~$540-563 per diem * LOS
            WHEN service_category = 'BEHAVIORAL_HEALTH' AND procedure_code = '90837' THEN
                (154.29 * (0.7 + 0.6 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)))
                * tx_bh_anomaly_factor
            WHEN service_category = 'BEHAVIORAL_HEALTH' THEN
                (540 + 23 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
                * UNIFORM(3, 14, RANDOM())
                * tx_bh_anomaly_factor

            -- EMERGENCY: Gamma-like, higher mean
            WHEN service_category = 'EMERGENCY' THEN
                ABS(800 + 600 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))

            -- OUTPATIENT: Gamma distribution (shape~2, mean~$250)
            ELSE
                ABS(125 + 125 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
        END
    , 2) AS allowed_amount,

    -- Billed amount: 1.5-3x allowed (hospitals bill above contracted rate)
    ROUND(
        CASE
            WHEN service_category = 'INPATIENT' THEN
                EXP(9.5 + 0.8 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * UNIFORM(200, 300, RANDOM()) / 100.0
            WHEN service_category = 'BEHAVIORAL_HEALTH' AND procedure_code = '90837' THEN
                (154.29 * (0.7 + 0.6 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))) * 1.8
            WHEN service_category = 'BEHAVIORAL_HEALTH' THEN
                (540 + 23 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * UNIFORM(3, 14, RANDOM()) * 1.6
            WHEN service_category = 'EMERGENCY' THEN
                ABS(800 + 600 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * 2.2
            ELSE
                ABS(125 + 125 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * 1.7
        END
    , 2) AS charge_amount,

    -- Plan paid amount: allowed minus member cost-sharing
    -- Network discount already in allowed; member pays copay/coinsurance
    ROUND(
        CASE
            WHEN service_category = 'INPATIENT' THEN
                EXP(9.5 + 0.8 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
                * tx_bh_anomaly_factor * 0.85  -- 15% member cost-share
            WHEN service_category = 'BEHAVIORAL_HEALTH' AND procedure_code = '90837' THEN
                (154.29 * (0.7 + 0.6 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)))
                * tx_bh_anomaly_factor * 0.80
            WHEN service_category = 'BEHAVIORAL_HEALTH' THEN
                (540 + 23 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
                * UNIFORM(3, 14, RANDOM()) * tx_bh_anomaly_factor * 0.80
            WHEN service_category = 'EMERGENCY' THEN
                ABS(800 + 600 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * 0.80
            ELSE
                ABS(125 + 125 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)) * 0.80
        END
    , 2) AS paid_amount,

    -- Claim status
    CASE
        WHEN UNIFORM(0, 100, RANDOM()) < 90 THEN 'PAID'
        WHEN UNIFORM(0, 100, RANDOM()) < 95 THEN 'DENIED'
        ELSE 'PENDING'
    END AS claim_status

FROM with_costs
WHERE -- Filter out unreasonable negatives from normal approximation
    (CASE
        WHEN service_category = 'INPATIENT' THEN EXP(9.5 + 0.8 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
        WHEN service_category = 'BEHAVIORAL_HEALTH' AND procedure_code = '90837' THEN 154.29 * (0.7 + 0.6 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2))
        ELSE 125 + 125 * SQRT(-2 * LN(u1)) * COS(2 * 3.14159265 * u2)
    END) > 0;


-- ==============================================================================
-- 3. PHARMACY CLAIMS (APCD-CDL Pharmacy File)
-- ~200K claims, faster lag profile
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.SYNTH_PHARMACY_CLAIMS AS
SELECT
    'RX-' || LPAD(ROW_NUMBER() OVER (ORDER BY SEQ4()), 10, '0') AS rx_claim_id,
    'MBR-' || LPAD(UNIFORM(1, 10000, RANDOM()), 8, '0') AS member_id,
    DATEADD('day', -UNIFORM(0, 730, RANDOM()), CURRENT_DATE()) AS fill_date,
    -- Paid date: pharmacy claims lag is short (3-14 days)
    DATEADD('day', UNIFORM(3, 14, RANDOM()),
        DATEADD('day', -UNIFORM(0, 730, RANDOM()), CURRENT_DATE())) AS paid_date,
    -- NDC codes (synthetic but formatted correctly)
    LPAD(UNIFORM(10000, 99999, RANDOM()), 5, '0') || '-' ||
    LPAD(UNIFORM(1000, 9999, RANDOM()), 4, '0') || '-' ||
    LPAD(UNIFORM(10, 99, RANDOM()), 2, '0') AS ndc_code,
    -- Drug category
    CASE
        WHEN UNIFORM(0, 100, RANDOM()) < 25 THEN 'DIABETES'
        WHEN UNIFORM(0, 100, RANDOM()) < 45 THEN 'CARDIOVASCULAR'
        WHEN UNIFORM(0, 100, RANDOM()) < 55 THEN 'BEHAVIORAL_HEALTH'
        WHEN UNIFORM(0, 100, RANDOM()) < 65 THEN 'RESPIRATORY'
        WHEN UNIFORM(0, 100, RANDOM()) < 75 THEN 'SPECIALTY'
        ELSE 'OTHER'
    END AS drug_category,
    UNIFORM(1, 90, RANDOM()) AS days_supply,
    UNIFORM(1, 3, RANDOM()) AS quantity_dispensed,
    -- Pharmacy costs: Gamma-like distribution
    ROUND(ABS(50 + 80 * SQRT(-2 * LN(UNIFORM(0.0001, 0.9999, RANDOM())))
        * COS(2 * 3.14159265 * UNIFORM(0.0001, 0.9999, RANDOM()))), 2) AS ingredient_cost,
    ROUND(UNIFORM(2, 15, RANDOM()) + UNIFORM(0, 99, RANDOM()) / 100.0, 2) AS dispensing_fee,
    ROUND(UNIFORM(0, 75, RANDOM()) + UNIFORM(0, 99, RANDOM()) / 100.0, 2) AS member_copay,
    'PAID' AS claim_status
FROM TABLE(GENERATOR(ROWCOUNT => 200000));


-- ==============================================================================
-- 4. CAPITATION PAYMENTS (PMPM Revenue by Member-Month)
-- Drives premium revenue side of MLR
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.SYNTH_CAPITATION_PAYMENTS AS
WITH months AS (
    SELECT DATEADD('month', -seq4(), CURRENT_DATE()) AS payment_month
    FROM TABLE(GENERATOR(ROWCOUNT => 24))
)
SELECT
    'CAP-' || LPAD(ROW_NUMBER() OVER (ORDER BY m.payment_month, e.member_id), 10, '0') AS payment_id,
    e.member_id,
    DATE_TRUNC('month', m.payment_month) AS payment_month,
    e.line_of_business,
    e.member_state,
    e.premium_pmpm,
    -- Adjust for RAF score in MA
    ROUND(
        CASE
            WHEN e.line_of_business = 'MEDICARE_ADVANTAGE'
                THEN e.premium_pmpm * e.raf_score
            ELSE e.premium_pmpm
        END
    , 2) AS risk_adjusted_pmpm,
    e.raf_score
FROM GOLD.SYNTH_MEMBER_ELIGIBILITY e
CROSS JOIN months m
WHERE e.enrollment_start_date <= m.payment_month
  AND (e.enrollment_end_date IS NULL OR e.enrollment_end_date >= m.payment_month);


-- ==============================================================================
-- 5. PHARMACY REBATES
-- Retrospective manufacturer rebates offsetting gross pharmacy spend
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.SYNTH_PHARMACY_REBATES AS
SELECT
    'REB-' || LPAD(ROW_NUMBER() OVER (ORDER BY SEQ4()), 8, '0') AS rebate_id,
    DATE_TRUNC('quarter', DATEADD('quarter', -UNIFORM(0, 7, RANDOM()), CURRENT_DATE())) AS rebate_quarter,
    CASE
        WHEN UNIFORM(0, 100, RANDOM()) < 40 THEN 'DIABETES'
        WHEN UNIFORM(0, 100, RANDOM()) < 65 THEN 'CARDIOVASCULAR'
        WHEN UNIFORM(0, 100, RANDOM()) < 80 THEN 'SPECIALTY'
        ELSE 'OTHER'
    END AS drug_category,
    ROUND(UNIFORM(50000, 500000, RANDOM()) + UNIFORM(0, 99, RANDOM()) / 100.0, 2) AS gross_rebate_amount,
    ROUND(UNIFORM(10000, 200000, RANDOM()) + UNIFORM(0, 99, RANDOM()) / 100.0, 2) AS net_rebate_amount,
    ROUND(UNIFORM(15, 45, RANDOM()) + UNIFORM(0, 9, RANDOM()) / 10.0, 1) AS rebate_percentage
FROM TABLE(GENERATOR(ROWCOUNT => 200));


-- ==============================================================================
-- 6. CLAIMS LAG TRIANGLE (for IBNR modeling)
-- Run-off triangle: incurral month x development month
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.CLAIMS_LAG_TRIANGLE AS
WITH incurral_months AS (
    SELECT DATEADD('month', -seq4(), DATE_TRUNC('month', CURRENT_DATE())) AS incurral_month
    FROM TABLE(GENERATOR(ROWCOUNT => 24))
),
dev_months AS (
    SELECT seq4() AS development_month
    FROM TABLE(GENERATOR(ROWCOUNT => 13))  -- 0 through 12 months development
),
base_triangle AS (
    SELECT
        i.incurral_month,
        d.development_month,
        -- Only show development that has elapsed
        DATEDIFF('month', i.incurral_month, CURRENT_DATE()) AS months_elapsed
    FROM incurral_months i
    CROSS JOIN dev_months d
    WHERE d.development_month <= DATEDIFF('month', i.incurral_month, CURRENT_DATE())
)
SELECT
    incurral_month,
    development_month,
    -- Simulated cumulative completion factors (realistic S-curve)
    ROUND(
        CASE
            WHEN development_month = 0 THEN 0.28 + UNIFORM(-3, 3, RANDOM()) / 100.0
            WHEN development_month = 1 THEN 0.52 + UNIFORM(-3, 3, RANDOM()) / 100.0
            WHEN development_month = 2 THEN 0.71 + UNIFORM(-2, 2, RANDOM()) / 100.0
            WHEN development_month = 3 THEN 0.82 + UNIFORM(-2, 2, RANDOM()) / 100.0
            WHEN development_month = 4 THEN 0.89 + UNIFORM(-1, 1, RANDOM()) / 100.0
            WHEN development_month = 5 THEN 0.93 + UNIFORM(-1, 1, RANDOM()) / 100.0
            WHEN development_month = 6 THEN 0.955 + UNIFORM(-5, 5, RANDOM()) / 1000.0
            WHEN development_month = 7 THEN 0.970 + UNIFORM(-3, 3, RANDOM()) / 1000.0
            WHEN development_month = 8 THEN 0.980 + UNIFORM(-2, 2, RANDOM()) / 1000.0
            WHEN development_month = 9 THEN 0.988 + UNIFORM(-1, 1, RANDOM()) / 1000.0
            WHEN development_month = 10 THEN 0.993 + UNIFORM(-1, 1, RANDOM()) / 1000.0
            WHEN development_month = 11 THEN 0.997 + UNIFORM(0, 2, RANDOM()) / 1000.0
            ELSE 1.000
        END
    , 4) AS completion_factor,
    -- Cumulative paid amount based on a simulated ultimate of $2M-$5M per incurral month
    ROUND(
        (UNIFORM(2000000, 5000000, RANDOM())) *
        CASE
            WHEN development_month = 0 THEN 0.28 + UNIFORM(-3, 3, RANDOM()) / 100.0
            WHEN development_month = 1 THEN 0.52 + UNIFORM(-3, 3, RANDOM()) / 100.0
            WHEN development_month = 2 THEN 0.71 + UNIFORM(-2, 2, RANDOM()) / 100.0
            WHEN development_month = 3 THEN 0.82 + UNIFORM(-2, 2, RANDOM()) / 100.0
            WHEN development_month = 4 THEN 0.89 + UNIFORM(-1, 1, RANDOM()) / 100.0
            WHEN development_month = 5 THEN 0.93 + UNIFORM(-1, 1, RANDOM()) / 100.0
            WHEN development_month = 6 THEN 0.955 + UNIFORM(-5, 5, RANDOM()) / 1000.0
            WHEN development_month = 7 THEN 0.970 + UNIFORM(-3, 3, RANDOM()) / 1000.0
            WHEN development_month = 8 THEN 0.980 + UNIFORM(-2, 2, RANDOM()) / 1000.0
            WHEN development_month = 9 THEN 0.988 + UNIFORM(-1, 1, RANDOM()) / 1000.0
            WHEN development_month = 10 THEN 0.993 + UNIFORM(-1, 1, RANDOM()) / 1000.0
            WHEN development_month = 11 THEN 0.997 + UNIFORM(0, 2, RANDOM()) / 1000.0
            ELSE 1.000
        END
    , 2) AS cumulative_paid
FROM base_triangle
ORDER BY incurral_month, development_month;


-- ==============================================================================
-- 7. HCC REFERENCE TABLE (CMS-HCC v28 with coefficient constraints)
-- ==============================================================================

CREATE OR REPLACE TABLE GOLD.HCC_REFERENCE AS
SELECT * FROM VALUES
    ('HCC 18',  'Pancreatic Cancer',              0.981, 'Cancer',        FALSE),
    ('HCC 19',  'Lung/Brain/GI/Urinary Cancer',   0.493, 'Cancer',        FALSE),
    ('HCC 36',  'Diabetes with Chronic Complication', 0.302, 'Diabetes',  TRUE),
    ('HCC 37',  'Diabetes with Complication',      0.302, 'Diabetes',     TRUE),
    ('HCC 38',  'Diabetes without Complication',   0.302, 'Diabetes',     TRUE),
    ('HCC 48',  'Coagulation Defects',             0.220, 'Blood',        FALSE),
    ('HCC 112', 'COPD',                            0.335, 'Respiratory',  FALSE),
    ('HCC 134', 'Chronic Kidney Disease Stage 5',  0.289, 'Renal',        FALSE),
    ('HCC 224', 'Heart Failure, High Severity',    0.431, 'CHF',          TRUE),
    ('HCC 225', 'Heart Failure, Medium Severity',  0.431, 'CHF',          TRUE),
    ('HCC 226', 'Heart Failure, Low Severity',     0.431, 'CHF',          TRUE),
    ('HCC 280', 'Acute Stroke',                    0.297, 'Stroke',       FALSE)
    AS t(hcc_code, hcc_description, v28_coefficient, category, is_constrained);


-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'Synthetic data generation complete' AS STATUS,
    (SELECT COUNT(*) FROM GOLD.SYNTH_MEMBER_ELIGIBILITY) AS members,
    (SELECT COUNT(*) FROM GOLD.SYNTH_MEDICAL_CLAIMS) AS medical_claims,
    (SELECT COUNT(*) FROM GOLD.SYNTH_PHARMACY_CLAIMS) AS rx_claims,
    (SELECT COUNT(*) FROM GOLD.SYNTH_CAPITATION_PAYMENTS) AS cap_payments,
    (SELECT COUNT(*) FROM GOLD.CLAIMS_LAG_TRIANGLE) AS lag_triangle_rows;
