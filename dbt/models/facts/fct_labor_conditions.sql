-- Wide analytical labor table. Joins all four staging models through dim_countries.
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

climate AS (
    SELECT * FROM {{ ref('stg_climate') }}
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

        -- climate proxies (World Bank WDI)
        cl.access_to_electricity_pct,
        cl.freshwater_withdrawal_pct_internal_resources,
        cl.precipitation_mm,
        cl.arable_land_pct,
        cl.forest_area_pct,

        -- structural vulnerability (ND-GAIN)
        g.vulnerability_score       AS gain_vulnerability_score,
        g.vulnerability_rank        AS gain_vulnerability_rank,
        g.readiness_score           AS gain_readiness_score,
        g.readiness_rank            AS gain_readiness_rank,
        g.overall_score             AS gain_overall_score,
        g.overall_rank              AS gain_overall_rank,
        g.region,
        g.income_group,

        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM labor l
    INNER JOIN countries c  ON l.country_code = c.country_code
    LEFT JOIN  economic e   ON l.country_code = e.country_code AND l.year = e.year
    LEFT JOIN  climate cl   ON l.country_code = cl.country_code AND l.year = cl.year
    LEFT JOIN  gain g       ON l.country_code = g.country_code AND l.year = g.year
)

SELECT * FROM final
ORDER BY country_code, year
