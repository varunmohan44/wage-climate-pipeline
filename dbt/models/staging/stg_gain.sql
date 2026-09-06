-- ND-GAIN vulnerability and readiness scores.
-- Grain: one row per (country_code, year)

SELECT
    country_code,
    country_name,
    year,
    vulnerability_score,
    readiness_score,
    overall_score,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM {{ source('raw', 'raw_gain') }}
