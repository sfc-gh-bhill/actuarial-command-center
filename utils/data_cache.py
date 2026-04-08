# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Braedon Hill

# ==============================================================================
# CENTRALIZED DATA CACHE — Shared session-level caching for performance at scale
# All data loaders cached at session level with TTL. Pages import from here
# instead of defining their own duplicate loaders.
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np


# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================
@st.cache_resource
def get_session():
    """Get Snowflake session — cached once per app lifetime."""
    from snowflake.snowpark.context import get_active_session
    return get_active_session()


def get_connection():
    """Return (session, session_available) tuple."""
    try:
        session = get_session()
        return session, True
    except Exception:
        return None, False


# ==============================================================================
# SHARED DATA LOADERS — Used by multiple pages
# ==============================================================================
@st.cache_data(ttl=300)
def load_financial_summary(_session_available, _session_id=None):
    """Load GOLD.FINANCIAL_SUMMARY — used by Home, Executive Summary, Margin Forecast."""
    if _session_available:
        session = get_session()
        return session.sql("""
            SELECT metric_month, line_of_business, member_state, service_category,
                   total_paid, total_premium, medical_loss_ratio, cost_pmpm,
                   margin_pct, margin_status, claim_count, enrolled_members
            FROM GOLD.FINANCIAL_SUMMARY
            ORDER BY metric_month DESC
        """).to_pandas()
    else:
        np.random.seed(42)
        months = pd.date_range(end=pd.Timestamp.today(), periods=24, freq='MS')
        lobs = ['ACA_INDIVIDUAL', 'ACA_SMALL_GROUP', 'ACA_LARGE_GROUP', 'MEDICARE_ADVANTAGE', 'MEDICAID_MANAGED']
        states = ['TX', 'MN', 'FL', 'CA']
        rows = []
        for m in months:
            for lob in lobs:
                for st_ in states:
                    base_mlr = {'ACA_INDIVIDUAL': 0.86, 'ACA_SMALL_GROUP': 0.87,
                                'ACA_LARGE_GROUP': 0.89, 'MEDICARE_ADVANTAGE': 0.88,
                                'MEDICAID_MANAGED': 0.91}.get(lob, 0.88)
                    if st_ == 'TX' and lob in ('ACA_INDIVIDUAL', 'ACA_SMALL_GROUP'):
                        base_mlr += 0.04
                    mlr = base_mlr + np.random.normal(0, 0.03)
                    paid = np.random.uniform(500000, 2000000)
                    premium = paid / mlr
                    rows.append({
                        'METRIC_MONTH': m, 'LINE_OF_BUSINESS': lob, 'MEMBER_STATE': st_,
                        'SERVICE_CATEGORY': 'ALL',
                        'TOTAL_PAID': paid, 'TOTAL_PREMIUM': premium,
                        'MEDICAL_LOSS_RATIO': mlr, 'COST_PMPM': np.random.uniform(300, 600),
                        'MARGIN_PCT': 1 - mlr,
                        'MARGIN_STATUS': 'MARGIN_AT_RISK' if mlr > 0.95 else 'MARGIN_WARNING' if mlr > 0.90 else 'ON_TARGET',
                        'CLAIM_COUNT': np.random.randint(500, 5000),
                        'ENROLLED_MEMBERS': np.random.randint(1000, 5000)
                    })
        return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def load_anomaly_alerts(_session_available, _session_id=None):
    """Load ANALYTICS.ANOMALY_ALERTS — used by Executive Summary, Trend Surveillance."""
    if _session_available:
        session = get_session()
        return session.sql("""
            SELECT series_id, ts, observed_value, expected_value,
                   lower_bound, upper_bound, anomaly_type, pct_deviation,
                   member_state, service_category, is_anomaly
            FROM ANALYTICS.ANOMALY_ALERTS
            WHERE is_anomaly = TRUE
            ORDER BY ABS(pct_deviation) DESC
            LIMIT 25
        """).to_pandas()
    else:
        return pd.DataFrame([
            {'SERIES_ID': 'TX|BEHAVIORAL_HEALTH', 'TS': pd.Timestamp.today() - pd.Timedelta(days=15),
             'OBSERVED_VALUE': 166.63, 'EXPECTED_VALUE': 154.29, 'LOWER_BOUND': 145.0, 'UPPER_BOUND': 163.0,
             'ANOMALY_TYPE': 'COST_SPIKE', 'PCT_DEVIATION': 8.0,
             'MEMBER_STATE': 'TX', 'SERVICE_CATEGORY': 'BEHAVIORAL_HEALTH', 'IS_ANOMALY': True},
            {'SERIES_ID': 'TX|BEHAVIORAL_HEALTH', 'TS': pd.Timestamp.today() - pd.Timedelta(days=45),
             'OBSERVED_VALUE': 164.12, 'EXPECTED_VALUE': 154.29, 'LOWER_BOUND': 146.0, 'UPPER_BOUND': 162.5,
             'ANOMALY_TYPE': 'COST_SPIKE', 'PCT_DEVIATION': 6.4,
             'MEMBER_STATE': 'TX', 'SERVICE_CATEGORY': 'BEHAVIORAL_HEALTH', 'IS_ANOMALY': True},
            {'SERIES_ID': 'TX|INPATIENT', 'TS': pd.Timestamp.today() - pd.Timedelta(days=30),
             'OBSERVED_VALUE': 14200, 'EXPECTED_VALUE': 13360, 'LOWER_BOUND': 12500, 'UPPER_BOUND': 14100,
             'ANOMALY_TYPE': 'COST_SPIKE', 'PCT_DEVIATION': 6.3,
             'MEMBER_STATE': 'TX', 'SERVICE_CATEGORY': 'INPATIENT', 'IS_ANOMALY': True}
        ])


# ==============================================================================
# CACHED AGGREGATIONS — Prevent redundant groupby recomputation
# ==============================================================================
@st.cache_data(ttl=300)
def compute_lob_summary(_df_hash, df):
    """MLR by LOB — used by Executive Summary, Margin Forecast."""
    lob_summary = df.groupby('LINE_OF_BUSINESS').agg(
        TOTAL_PAID=('TOTAL_PAID', 'sum'),
        TOTAL_PREMIUM=('TOTAL_PREMIUM', 'sum'),
        CLAIM_COUNT=('CLAIM_COUNT', 'sum')
    ).reset_index()
    lob_summary['MLR'] = lob_summary['TOTAL_PAID'] / lob_summary['TOTAL_PREMIUM']
    lob_summary['MARGIN'] = 1 - lob_summary['MLR']
    return lob_summary.sort_values('MLR', ascending=False)


@st.cache_data(ttl=300)
def compute_monthly_mlr(_df_hash, df):
    """Monthly MLR trend — used by Executive Summary."""
    monthly_mlr = df.groupby('METRIC_MONTH').agg(
        TOTAL_PAID=('TOTAL_PAID', 'sum'),
        TOTAL_PREMIUM=('TOTAL_PREMIUM', 'sum')
    ).reset_index()
    monthly_mlr['MLR'] = monthly_mlr['TOTAL_PAID'] / monthly_mlr['TOTAL_PREMIUM']
    return monthly_mlr.sort_values('METRIC_MONTH').tail(12)


@st.cache_data(ttl=300)
def compute_state_summary(_df_hash, df):
    """Margin by state — used by Executive Summary."""
    state_summary = df.groupby('MEMBER_STATE').agg(
        TOTAL_PAID=('TOTAL_PAID', 'sum'),
        TOTAL_PREMIUM=('TOTAL_PREMIUM', 'sum')
    ).reset_index()
    state_summary['MARGIN'] = (state_summary['TOTAL_PREMIUM'] - state_summary['TOTAL_PAID']) / state_summary['TOTAL_PREMIUM']
    return state_summary.sort_values('MARGIN')


@st.cache_data(ttl=300)
def compute_monthly_lob_mlr(_df_hash, df):
    """Monthly MLR by LOB — used by Margin Forecast."""
    monthly_lob = df.groupby(['METRIC_MONTH', 'LINE_OF_BUSINESS']).agg(
        TOTAL_PAID=('TOTAL_PAID', 'sum'),
        TOTAL_PREMIUM=('TOTAL_PREMIUM', 'sum')
    ).reset_index()
    monthly_lob['MLR'] = monthly_lob['TOTAL_PAID'] / monthly_lob['TOTAL_PREMIUM']
    return monthly_lob


@st.cache_data(ttl=300)
def compute_category_summary(_df_hash, df):
    """Service category summary — used by Claims Analytics."""
    cat_summary = df.groupby('SERVICE_CATEGORY').agg(
        TOTAL_PAID=('PAID_AMOUNT', 'sum'),
        AVG_PAID=('PAID_AMOUNT', 'mean'),
        CLAIMS=('PAID_AMOUNT', 'count')
    ).reset_index()
    cat_summary['PCT_SPEND'] = cat_summary['TOTAL_PAID'] / cat_summary['TOTAL_PAID'].sum()
    return cat_summary.sort_values('TOTAL_PAID', ascending=False)


@st.cache_data(ttl=300)
def compute_lag_by_category(_df_hash, df):
    """Claims lag by category — used by Claims Analytics."""
    lag_by_cat = df.groupby('SERVICE_CATEGORY')['CLAIMS_LAG_DAYS'].agg(['mean', 'median']).reset_index()
    lag_by_cat.columns = ['SERVICE_CATEGORY', 'AVG_LAG', 'MEDIAN_LAG']
    return lag_by_cat.sort_values('AVG_LAG', ascending=False)


def df_hash(df):
    """Generate a lightweight hash for cache keying on filtered DataFrames."""
    return hash((len(df), tuple(df.columns), df.iloc[0].values.tobytes() if len(df) > 0 else b''))
