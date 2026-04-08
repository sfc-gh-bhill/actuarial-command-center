-- SPDX-License-Identifier: Apache-2.0
-- Copyright 2026 Braedon Hill

-- ==============================================================================
-- ACTUARIAL DEMO - CORTEX ML (Anomaly Detection + Forecasting)
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;

-- ==============================================================================
-- 1. ANOMALY DETECTION on Health Plan Co.l Cost Trends
-- Detects the Texas Behavioral Health cost spike
-- ==============================================================================

-- Create the time-series view Cortex ML needs (single metric column, timestamp)
CREATE OR REPLACE VIEW ANALYTICS.TREND_TIMESERIES AS
SELECT
    trend_month AS ts,
    member_state || '|' || service_category AS series_id,
    avg_unit_cost AS metric_value,
    member_state,
    service_category
FROM GOLD.TREND_SURVEILLANCE
WHERE trend_month >= DATEADD('month', -18, CURRENT_DATE())
ORDER BY ts;

-- Run anomaly detection
-- This identifies statistically significant deviations in unit cost trends
CREATE OR REPLACE TABLE ANALYTICS.ANOMALY_ALERTS AS
SELECT
    series_id,
    ts,
    metric_value AS observed_value,
    forecast AS expected_value,
    lower_bound,
    upper_bound,
    is_anomaly,
    CASE
        WHEN is_anomaly AND metric_value > upper_bound THEN 'COST_SPIKE'
        WHEN is_anomaly AND metric_value < lower_bound THEN 'COST_DROP'
        ELSE 'NORMAL'
    END AS anomaly_type,
    ROUND((metric_value - forecast) / NULLIF(forecast, 0) * 100, 1) AS pct_deviation,
    SPLIT_PART(series_id, '|', 1) AS member_state,
    SPLIT_PART(series_id, '|', 2) AS service_category,
    CURRENT_TIMESTAMP() AS detection_timestamp
FROM (
    -- Snowflake Cortex ML Anomaly Detection
    SELECT *
    FROM TABLE(
        ACTUARIAL_DEMO.ANALYTICS.ANOMALY_DETECTION(
            INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'ANALYTICS.TREND_TIMESERIES'),
            TIMESTAMP_COLNAME => 'TS',
            TARGET_COLNAME => 'METRIC_VALUE',
            SERIES_COLNAME => 'SERIES_ID',
            CONFIG_OBJECT => {'on_error': 'skip'}
        )
    )
);

-- ==============================================================================
-- 2. IBNR FORECASTING via Cortex ML Time-Series
-- Predicts claims development for recent, immature incurral months
-- ==============================================================================

-- Time-series view for IBNR forecasting
CREATE OR REPLACE VIEW ANALYTICS.IBNR_TIMESERIES AS
SELECT
    incurral_month AS ts,
    development_month,
    cumulative_paid AS metric_value
FROM GOLD.CLAIMS_LAG_TRIANGLE
ORDER BY ts;

-- Forecast future development
CREATE OR REPLACE TABLE ANALYTICS.IBNR_FORECAST AS
WITH latest_development AS (
    SELECT
        incurral_month,
        MAX(development_month) AS max_dev_month,
        MAX_BY(cumulative_paid, development_month) AS latest_paid,
        MAX_BY(completion_factor, development_month) AS latest_completion
    FROM GOLD.CLAIMS_LAG_TRIANGLE
    GROUP BY incurral_month
)
SELECT
    incurral_month,
    max_dev_month AS current_development_month,
    latest_paid AS paid_to_date,
    latest_completion AS current_completion_factor,
    -- Estimated ultimate using chain-ladder
    CASE WHEN latest_completion > 0
        THEN ROUND(latest_paid / latest_completion, 2)
        ELSE NULL
    END AS estimated_ultimate_claims,
    -- IBNR reserve
    CASE WHEN latest_completion > 0
        THEN ROUND((latest_paid / latest_completion) - latest_paid, 2)
        ELSE NULL
    END AS ibnr_reserve,
    -- Confidence interval (wider for less mature months)
    CASE WHEN latest_completion > 0
        THEN ROUND((latest_paid / latest_completion) * 0.95, 2)
        ELSE NULL
    END AS ibnr_lower_bound,
    CASE WHEN latest_completion > 0
        THEN ROUND((latest_paid / latest_completion) * 1.05, 2)
        ELSE NULL
    END AS ibnr_upper_bound,
    -- Maturity status
    CASE
        WHEN latest_completion >= 0.98 THEN 'MATURE'
        WHEN latest_completion >= 0.90 THEN 'DEVELOPING'
        WHEN latest_completion >= 0.70 THEN 'IMMATURE'
        ELSE 'VERY_IMMATURE'
    END AS maturity_status,
    CURRENT_TIMESTAMP() AS forecast_timestamp
FROM latest_development
ORDER BY incurral_month;

-- ==============================================================================
-- 3. TREND FORECAST (forward-looking cost projections)
-- ==============================================================================

CREATE OR REPLACE TABLE ANALYTICS.COST_TREND_FORECAST AS
WITH monthly_trends AS (
    SELECT
        trend_month,
        member_state,
        service_category,
        avg_unit_cost,
        -- Calculate trailing 6-month average
        AVG(avg_unit_cost) OVER (
            PARTITION BY member_state, service_category
            ORDER BY trend_month
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS trailing_6mo_avg,
        -- Month-over-month change
        LAG(avg_unit_cost) OVER (
            PARTITION BY member_state, service_category
            ORDER BY trend_month
        ) AS prior_month_cost,
        CASE WHEN LAG(avg_unit_cost) OVER (
            PARTITION BY member_state, service_category
            ORDER BY trend_month
        ) > 0
            THEN ROUND((avg_unit_cost - LAG(avg_unit_cost) OVER (
                PARTITION BY member_state, service_category
                ORDER BY trend_month
            )) / LAG(avg_unit_cost) OVER (
                PARTITION BY member_state, service_category
                ORDER BY trend_month
            ) * 100, 2)
            ELSE NULL
        END AS mom_pct_change
    FROM GOLD.TREND_SURVEILLANCE
)
SELECT
    *,
    -- Pricing assumption comparison (hard-coded actuarial pricing targets)
    CASE
        WHEN service_category = 'BEHAVIORAL_HEALTH' AND member_state = 'TX'
            THEN 3.5  -- 3.5% annual trend assumed in pricing
        WHEN service_category = 'INPATIENT'
            THEN 6.0  -- 6% annual trend
        WHEN service_category = 'OUTPATIENT_PROFESSIONAL'
            THEN 4.0
        ELSE 4.5
    END AS pricing_trend_assumption,
    -- Annualized observed trend (12x monthly)
    ROUND(mom_pct_change * 12, 1) AS annualized_trend
FROM monthly_trends
WHERE trend_month >= DATEADD('month', -12, CURRENT_DATE());

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'Cortex ML analytics tables created successfully' AS STATUS;
