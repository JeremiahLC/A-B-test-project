-- Create database for A/B test project
CREATE DATABASE AB_TEST_PROJECT;

-- Create table to store base A/B test data from Google Analytics
CREATE OR REPLACE TABLE AB_TEST_PROJECT.PUBLIC.AB_TEST_BASE_DATA (
    user_pseudo_id STRING,      -- Anonymous user identifier from GA4
    event_name STRING,          -- Type of event (page_view, purchase_click, etc.)
    test_version STRING         -- A/B test version (Version A or Version B)
);

-- Check if storage integration already exists (descriptive command)
DESCRIBE INTEGRATION GCS_INTEGRATION;

-- Create storage integration to connect Snowflake with Google Cloud Storage
CREATE STORAGE INTEGRATION GCS_INTEGRATION
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'GCS'    -- Specify Google Cloud Storage as provider
    ENABLED = TRUE
    STORAGE_ALLOWED_LOCATIONS = ('*');  -- Allow access to all GCS locations

-- Create external stage pointing to GCS bucket where A/B test data is stored
CREATE OR REPLACE STAGE AB_TEST_PROJECT.PUBLIC.GCS_AB_TEST_STAGE
    STORAGE_INTEGRATION = GCS_INTEGRATION
    URL = 'gcs://ab-test-project-bucket-xxxxxx/ab_test_data/';  -- GCS bucket path

-- Define file format for compressed CSV files from GCS
CREATE OR REPLACE FILE FORMAT AB_TEST_PROJECT.PUBLIC.CSV_GZ_FORMAT
    TYPE = CSV
    COMPRESSION = GZIP                -- Handle gzip compressed files
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'  -- Fields may be quoted
    SKIP_HEADER = 1;                  -- Skip header row in CSV files

-- Load data from GCS stage into Snowflake table using specified file format
COPY INTO AB_TEST_PROJECT.PUBLIC.AB_TEST_BASE_DATA
FROM @AB_TEST_PROJECT.PUBLIC.GCS_AB_TEST_STAGE
FILE_FORMAT = (FORMAT_NAME = 'AB_TEST_PROJECT.PUBLIC.CSV_GZ_FORMAT');

-- Verify data was loaded correctly by sampling first 10 rows
SELECT * FROM AB_TEST_PROJECT.PUBLIC.AB_TEST_BASE_DATA LIMIT 10;

-- Create table for semi-structured user feedback data from MongoDB
-- Using VARIANT data type to store JSON documents natively
CREATE OR REPLACE TABLE AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK (
    data VARIANT  -- Store entire JSON document as semi-structured data
);

-- Sample user feedback data to verify loading
SELECT * FROM AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK LIMIT 10;

-- Create final A/B test results table using CTE for data transformation
CREATE OR REPLACE TABLE AB_TEST_PROJECT.PUBLIC.AB_TEST_RESULTS AS
WITH visitors AS (
    -- Identify unique visitors and their test group assignment
    SELECT DISTINCT
        user_pseudo_id,
        test_version
    FROM
        AB_TEST_PROJECT.PUBLIC.AB_TEST_BASE_DATA
    WHERE
        event_name = 'page_view'  -- Only count users who actually viewed the page
),
conversions AS (
    -- Identify users who converted (clicked purchase button)
    SELECT DISTINCT
        user_pseudo_id
    FROM
        AB_TEST_PROJECT.PUBLIC.AB_TEST_BASE_DATA
    WHERE
        event_name = 'purchase_click'  -- Conversion event
)

-- Combine visitor and conversion data to create final analysis table
SELECT
    v.user_pseudo_id,
    v.test_version,
    (c.user_pseudo_id IS NOT NULL) AS is_converted  -- Boolean flag for conversion
FROM
    visitors v
LEFT JOIN
    conversions c ON v.user_pseudo_id = c.user_pseudo_id;  -- Left join to preserve all visitors

-- Verify the transformed results table
SELECT * FROM AB_TEST_PROJECT.PUBLIC.AB_TEST_RESULTS LIMIT 10;

-- Calculate key A/B test metrics: conversion rates by test version
SELECT
    test_version,
    COUNT(user_pseudo_id) AS total_visitors,                    -- Total visitors per version
    SUM(CASE WHEN is_converted THEN 1 ELSE 0 END) AS total_conversions,  -- Count conversions
    (total_conversions / total_visitors) AS conversion_rate     -- Calculate conversion rate
FROM
    AB_TEST_PROJECT.PUBLIC.AB_TEST_RESULTS
GROUP BY
    test_version;

-- Create parsed view of user feedback by extracting fields from JSON (VARIANT) data
CREATE OR REPLACE VIEW AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK_PARSED AS
SELECT
    DATA:user_pseudo_id::STRING AS user_pseudo_id,              -- Extract user ID
    DATA:test_version::STRING AS test_version,                  -- Extract test version
    DATA:comment_text::STRING AS comment_text,                  -- Extract comment text
    DATA:star_rating::INT AS star_rating,                       -- Extract star rating as integer
    DATA:time_to_convert_seconds::FLOAT AS time_to_convert_seconds,  -- Extract conversion time
    DATA:tags AS tags                                           -- Keep tags as semi-structured array
FROM
    AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK;

-- Verify parsed feedback data
SELECT * FROM AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK_PARSED LIMIT 10;

-- Analyze qualitative metrics: average ratings and conversion times by version
SELECT
    test_version,
    AVG(star_rating) AS average_star_rating,                    -- Average user satisfaction
    AVG(time_to_convert_seconds) AS average_conversion_time,    -- Average time to convert
    COUNT(*) as total_reviews                                   -- Total number of reviews
FROM
    AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK_PARSED
GROUP BY
    test_version;

-- Analyze feedback tags using LATERAL FLATTEN to expand array elements
SELECT
    test_version,
    tag.value::STRING AS feedback_tag,                          -- Extract individual tags from array
    COUNT(*) AS tag_count                                       -- Count occurrences of each tag
FROM
    AB_TEST_PROJECT.PUBLIC.USER_FEEDBACK_PARSED,
    LATERAL FLATTEN(input => tags) AS tag                      -- Flatten tags array into rows
GROUP BY
    test_version,
    feedback_tag
ORDER BY
    test_version,
    tag_count DESC;                                             -- Show most common tags first