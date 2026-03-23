-- ==============================================================================
-- ACTUARIAL DEMO - DATA FOUNDATION
-- Database, schemas, warehouse, stages, file formats, roles, and grants
-- Run this FIRST against the DEMO connection
-- ==============================================================================

USE ROLE ACCOUNTADMIN;

-- ==============================================================================
-- DATABASE
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS ACTUARIAL_DEMO
    COMMENT = 'Health plan actuarial analytics: MLR, IBNR, risk adjustment, contract repricing';

USE DATABASE ACTUARIAL_DEMO;

-- ==============================================================================
-- SCHEMAS (Medallion Architecture)
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Raw ingested data and staged files';

CREATE SCHEMA IF NOT EXISTS SILVER
    COMMENT = 'Cleaned, standardized, deduplicated data';

CREATE SCHEMA IF NOT EXISTS GOLD
    COMMENT = 'Business-ready aggregates, metrics, and governed models';

CREATE SCHEMA IF NOT EXISTS ANALYTICS
    COMMENT = 'ML outputs, anomaly alerts, forecasts, and IBNR estimates';

CREATE SCHEMA IF NOT EXISTS AGENTS
    COMMENT = 'Cortex Agent artifacts: search indices, contract chunks, agent configs';

-- ==============================================================================
-- WAREHOUSE
-- ==============================================================================

CREATE WAREHOUSE IF NOT EXISTS ACTUARIAL_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute for actuarial demo workloads';

USE WAREHOUSE ACTUARIAL_WH;

-- ==============================================================================
-- STAGES
-- ==============================================================================

USE SCHEMA RAW;

-- Internal stage for provider contract PDFs
CREATE STAGE IF NOT EXISTS CONTRACT_DOCS_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for provider contract PDFs and regulatory documents';

-- Internal stage for exported artifacts
CREATE STAGE IF NOT EXISTS EXPORT_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for exported data files and reports';

-- ==============================================================================
-- FILE FORMATS
-- ==============================================================================

CREATE FILE FORMAT IF NOT EXISTS CSV_FORMAT
    TYPE = CSV
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    NULL_IF = ('NULL', 'null', '');

CREATE FILE FORMAT IF NOT EXISTS PARQUET_FORMAT
    TYPE = PARQUET
    COMPRESSION = SNAPPY;

CREATE FILE FORMAT IF NOT EXISTS JSON_FORMAT
    TYPE = JSON
    STRIP_OUTER_ARRAY = TRUE;

-- ==============================================================================
-- ROLE AND GRANTS
-- ==============================================================================

CREATE ROLE IF NOT EXISTS ACTUARIAL_DEMO_ROLE
    COMMENT = 'Role for actuarial demo application access';

-- Database and warehouse
GRANT USAGE ON DATABASE ACTUARIAL_DEMO TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE ACTUARIAL_DEMO TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT USAGE ON WAREHOUSE ACTUARIAL_WH TO ROLE ACTUARIAL_DEMO_ROLE;

-- Schema-level grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA RAW TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA SILVER TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA GOLD TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ANALYTICS TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA AGENTS TO ROLE ACTUARIAL_DEMO_ROLE;

-- Future grants
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA RAW TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA SILVER TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA GOLD TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA ANALYTICS TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA AGENTS TO ROLE ACTUARIAL_DEMO_ROLE;

-- Stage access
GRANT READ, WRITE ON STAGE RAW.CONTRACT_DOCS_STAGE TO ROLE ACTUARIAL_DEMO_ROLE;
GRANT READ, WRITE ON STAGE RAW.EXPORT_STAGE TO ROLE ACTUARIAL_DEMO_ROLE;

-- Semantic view access
GRANT SELECT ON FUTURE VIEWS IN SCHEMA GOLD TO ROLE ACTUARIAL_DEMO_ROLE;

-- Grant role to ACCOUNTADMIN
GRANT ROLE ACTUARIAL_DEMO_ROLE TO ROLE ACCOUNTADMIN;

-- ==============================================================================
-- VERIFICATION
-- ==============================================================================

SELECT 'ACTUARIAL_DEMO foundation created successfully' AS STATUS;
