-- Pivots raw.raw_economic from long format (one row per country/indicator/year)
-- to wide format (one row per country/year, each indicator as its own column).
--
-- Null values are passed through — filtering happens at the fact layer
-- where full cross-source context is available.
--
-- Grain: one row per (country_code, year)

WITH source AS (
    SELECT
        country_code,
        country_name,
        indicator_code,
        value,
        year
    FROM {{ source('raw', 'raw_economic') }}),

pivoted AS (
    SELECT
        country_code, MAX(country_name) AS country_name, year,

        -- GDP per capita (current USD)
        MAX(CASE WHEN indicator_code = 'NY.GDP.PCAP.CD'
            THEN value END) AS gdp_per_capita_usd,

        -- Poverty headcount ratio at $2.15/day (% of population)
        MAX(CASE WHEN indicator_code = 'SI.POV.DDAY'
            THEN value END) AS poverty_headcount_ratio,

        -- Rural population (% of total)
        MAX(CASE WHEN indicator_code = 'SP.RUR.TOTL.ZS'
            THEN value END) AS rural_population_pct,

        -- Net ODA received (current USD)
        MAX(CASE WHEN indicator_code = 'DT.ODA.ALLD.CD'
            THEN value END) AS oda_received_usd

    FROM source
    GROUP BY country_code, year),

final AS (
    SELECT
        -- keys
        country_code, country_name, year,

        -- indicators
        gdp_per_capita_usd,
        poverty_headcount_ratio,
        rural_population_pct,
        oda_received_usd,

        -- audit
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM pivoted)

SELECT * FROM final
