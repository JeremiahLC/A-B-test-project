SELECT
    *
FROM
    `ab-test-analytics-475502.analytics_509184411.events_20251017`
LIMIT 10;

SELECT
    COUNT(*) AS total_event_rows,
    COUNT(DISTINCT user_pseudo_id) AS unique_users,
    COUNT(DISTINCT (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')) AS unique_sessions
FROM
    `ab-test-analytics-475502.analytics_509184411.events_20251017`;

SELECT
    event_name,
    COUNT(*) AS event_count
FROM
    `ab-test-analytics-475502.analytics_509184411.events_20251017`
GROUP BY
    event_name
ORDER BY
    event_count DESC;

WITH prepped_data AS (
    SELECT
        user_pseudo_id,
        event_name,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'test_version') AS test_version,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id
    FROM
    `ab-test-analytics-475502.analytics_509184411.events_20251017`
)
SELECT
    test_version,
    event_name,
    COUNT(DISTINCT user_pseudo_id) AS unique_users_count
FROM
    prepped_data
WHERE
    test_version IS NOT NULL
GROUP BY
    test_version,
    event_name
ORDER BY
    test_version,
    unique_users_count DESC;
