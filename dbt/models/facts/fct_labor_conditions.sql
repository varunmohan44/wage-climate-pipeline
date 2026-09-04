-- Wide analytical labor table. Joins all three staging models through dim_countries.
-- stg_labor is the spine — only rows where ILOSTAT has data are included.
-- All other sources are left-joined so nulls are preserved for the composite index.
--
-- Grain: one row per (country_code, year)

WITH labor AS (
    SELECT * FROM {{ ref('stg_labor') }}
),

economic AS (
    SELECT * FROM {{ ref('stg_economic') }}
),

gain AS (
    SELECT * FROM {{ ref('stg_gain') }}
),

countries AS (
    SELECT * FROM {{ ref('dim_countries') }}
),

final AS (
    SELECT
        -- keys
        c.country_code,
        c.country_name,
        l.year,

        -- source coverage flags (from dim_countries)
        c.in_economic,
        c.in_gain,
        c.in_labor,

        -- labor indicators (ILOSTAT)
        l.avg_nominal_earnings_total,
        l.avg_nominal_earnings_male,
        l.avg_nominal_earnings_female,
        l.gender_wage_gap_pct,
        l.informality_rate_total,
        l.informality_rate_male,
        l.informality_rate_female,
        l.total_employment_nb,

        -- economic context (World Bank WDI)
        e.gdp_per_capita_usd,
        e.poverty_headcount_ratio,
        e.rural_population_pct,
        e.oda_received_usd,

        -- structural vulnerability (ND-GAIN)
        g.vulnerability_score AS gain_vulnerability_score,
        g.readiness_score AS gain_readiness_score,
        g.overall_score AS gain_overall_score,

        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM labor l
    INNER JOIN countries c ON l.country_code = c.country_code
    LEFT JOIN  economic e ON l.country_code = e.country_code AND l.year = e.year
    LEFT JOIN  gain g ON l.country_code = g.country_code AND l.year = g.year
)

SELECT * FROM final
ORDER BY country_code, year
