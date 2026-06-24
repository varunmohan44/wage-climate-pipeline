-- ND-GAIN vulnerability and readiness scores.
-- Grain: one row per (country_code, year)

SELECT
    country_code,
    country_name,
    year,
    vulnerability_score,
    vulnerability_rank,
    readiness_score,
    readiness_rank,
    overall_score,
    overall_rank,
    region,
    income_group,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM {{ source('raw', 'raw_gain') }}
