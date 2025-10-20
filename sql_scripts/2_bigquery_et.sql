WITH prepped_data AS (
    SELECT
        user_pseudo_id,
        event_name,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'test_version') AS test_version
    FROM
        `ab-test-analytics-475502.analytics_509184411.events_*`
)
SELECT
    user_pseudo_id,
    event_name,
    test_version
FROM
    prepped_data
WHERE
    test_version IS NOT NULL