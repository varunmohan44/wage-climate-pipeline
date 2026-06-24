-- Pivots raw.raw_economic from long to wide format (economic context indicators).
-- Grain: one row per (country_code, year)

WITH source AS (
    SELECT country_code, country_name, indicator_code, value, year
    FROM {{ source('raw', 'raw_economic') }}
),

pivoted AS (
    SELECT
        country_code,
        MAX(country_name) AS country_name,
        year,
        MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD' THEN value END) AS gdp_per_capita_usd,
        MAX(CASE WHEN indicator_code = 'SI.POV.DDAY' THEN value END) AS poverty_headcount_ratio,
        MAX(CASE WHEN indicator_code = 'SP.RUR.TOTL.ZS' THEN value END) AS rural_population_pct,
        MAX(CASE WHEN indicator_code = 'DT.ODA.ALLD.CD' THEN value END) AS oda_received_usd
    FROM source
    GROUP BY country_code, year
)

SELECT
    country_code,
    country_name,
    year,
    gdp_per_capita_usd,
    poverty_headcount_ratio,
    rural_population_pct,
    oda_received_usd,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM pivoted
