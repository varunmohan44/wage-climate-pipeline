-- ND-GAIN vulnerability and readiness scores staging model
-- Grain: one row per country/year

WITH source AS (
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
        income_group
    FROM {{ source('raw', 'raw_gain') }}
)

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
FROM source
