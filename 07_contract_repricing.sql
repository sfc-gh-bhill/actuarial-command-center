-- ==============================================================================
-- ACTUARIAL DEMO - CONTRACT REPRICING STORED PROCEDURE
-- The "Wow Moment": Interactive slider drives real-time repricing
-- ==============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE ACTUARIAL_DEMO;
USE WAREHOUSE ACTUARIAL_WH;
USE SCHEMA GOLD;

-- ==============================================================================
-- PYTHON STORED PROCEDURE: Contract Repricing Simulation
-- Called by Streamlit slider to recalculate margin impact
-- ==============================================================================

CREATE OR REPLACE PROCEDURE GOLD.REPRICE_CONTRACT(
    basis_point_change FLOAT,        -- e.g., -200 for 2% reduction
    target_state VARCHAR,             -- e.g., 'TX'
    target_provider_system VARCHAR    -- e.g., 'ALL' or specific NPI prefix
)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'pandas', 'numpy')
HANDLER = 'reprice'
AS
$$
import pandas as pd
import numpy as np
import json

def reprice(session, basis_point_change: float, target_state: str, target_provider_system: str):
    """
    Reprice provider contracts by applying a basis point adjustment to allowed amounts.
    
    The procedure:
    1. Identifies all claims for the targeted state/provider
    2. Applies the BPS adjustment to allowed amounts (especially MS-DRG inpatient)
    3. Recalculates paid amounts with member cost-sharing
    4. Aggregates the new financial metrics
    5. Returns the margin impact as JSON for Streamlit
    """
    
    bps_factor = 1 + (basis_point_change / 10000.0)  # -200 bps = 0.98
    
    # Get current claims for the target state
    claims_df = session.sql(f"""
        SELECT 
            claim_id,
            member_id,
            service_category,
            ms_drg,
            allowed_amount,
            paid_amount,
            charge_amount,
            line_of_business,
            incurral_month
        FROM SILVER.MEDICAL_CLAIMS_CLEAN
        WHERE member_state = '{target_state}'
    """).to_pandas()
    
    if claims_df.empty:
        return {"error": "No claims found for target state"}
    
    # Current totals
    current_total_paid = float(claims_df['PAID_AMOUNT'].sum())
    current_total_allowed = float(claims_df['ALLOWED_AMOUNT'].sum())
    
    # Apply repricing
    # Inpatient MS-DRG claims get full BPS adjustment
    # Other claims get partial adjustment (50% pass-through)
    claims_df['NEW_ALLOWED'] = np.where(
        claims_df['SERVICE_CATEGORY'] == 'INPATIENT',
        claims_df['ALLOWED_AMOUNT'] * bps_factor,
        claims_df['ALLOWED_AMOUNT'] * (1 + (basis_point_change / 10000.0) * 0.5)
    )
    
    # Recalculate paid (allowed minus member cost-share, ~15-20%)
    cost_share_pct = np.where(
        claims_df['SERVICE_CATEGORY'] == 'INPATIENT', 0.15, 0.20
    )
    claims_df['NEW_PAID'] = claims_df['NEW_ALLOWED'] * (1 - cost_share_pct)
    
    # New totals
    new_total_paid = float(claims_df['NEW_PAID'].sum())
    new_total_allowed = float(claims_df['NEW_ALLOWED'].sum())
    
    # Get premium revenue for the state
    premium_row = session.sql(f"""
        SELECT SUM(risk_adjusted_pmpm) AS total_premium
        FROM SYNTH_CAPITATION_PAYMENTS
        WHERE member_state = '{target_state}'
    """).to_pandas()
    
    total_premium = float(premium_row['TOTAL_PREMIUM'].iloc[0]) if not premium_row.empty else 0
    
    # Calculate metrics
    current_mlr = current_total_paid / total_premium if total_premium > 0 else 0
    new_mlr = new_total_paid / total_premium if total_premium > 0 else 0
    
    current_margin = (total_premium - current_total_paid) / total_premium if total_premium > 0 else 0
    new_margin = (total_premium - new_total_paid) / total_premium if total_premium > 0 else 0
    
    savings = current_total_paid - new_total_paid
    
    # Breakdown by service category
    by_category = claims_df.groupby('SERVICE_CATEGORY').agg({
        'PAID_AMOUNT': 'sum',
        'NEW_PAID': 'sum',
        'CLAIM_ID': 'count'
    }).reset_index()
    
    by_category['SAVINGS'] = by_category['PAID_AMOUNT'] - by_category['NEW_PAID']
    
    category_impact = []
    for _, row in by_category.iterrows():
        category_impact.append({
            "service_category": row['SERVICE_CATEGORY'],
            "current_paid": round(float(row['PAID_AMOUNT']), 2),
            "repriced_paid": round(float(row['NEW_PAID']), 2),
            "savings": round(float(row['SAVINGS']), 2),
            "claim_count": int(row['CLAIM_ID'])
        })
    
    # Monthly margin forecast
    monthly = claims_df.groupby('INCURRAL_MONTH').agg({
        'PAID_AMOUNT': 'sum',
        'NEW_PAID': 'sum'
    }).reset_index().sort_values('INCURRAL_MONTH')
    
    monthly_forecast = []
    for _, row in monthly.iterrows():
        monthly_forecast.append({
            "month": str(row['INCURRAL_MONTH']),
            "current_paid": round(float(row['PAID_AMOUNT']), 2),
            "repriced_paid": round(float(row['NEW_PAID']), 2)
        })
    
    result = {
        "target_state": target_state,
        "basis_point_change": basis_point_change,
        "bps_factor": round(bps_factor, 4),
        "total_claims_repriced": len(claims_df),
        "current": {
            "total_paid": round(current_total_paid, 2),
            "total_allowed": round(current_total_allowed, 2),
            "total_premium": round(total_premium, 2),
            "mlr": round(current_mlr, 4),
            "margin": round(current_margin, 4)
        },
        "repriced": {
            "total_paid": round(new_total_paid, 2),
            "total_allowed": round(new_total_allowed, 2),
            "total_premium": round(total_premium, 2),
            "mlr": round(new_mlr, 4),
            "margin": round(new_margin, 4)
        },
        "impact": {
            "total_savings": round(savings, 2),
            "mlr_improvement": round((current_mlr - new_mlr) * 100, 2),
            "margin_improvement": round((new_margin - current_margin) * 100, 2)
        },
        "by_category": category_impact,
        "monthly_forecast": monthly_forecast
    }
    
    return result
$$;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

-- Test the procedure with a -200 bps adjustment for Texas
-- CALL GOLD.REPRICE_CONTRACT(-200, 'TX', 'ALL');

SELECT 'Contract repricing stored procedure created successfully' AS STATUS;
