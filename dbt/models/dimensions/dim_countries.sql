-- Canonical country dimension. Unions all unique ISO alpha-3 codes across the
-- three raw sources and canonicalizes country names (World Bank preferred, then
-- ND-GAIN, then ILOSTAT). Boolean flags indicate which pipelines cover each country.
--
-- Grain: one row per country_code.

WITH economic_countries AS (
    SELECT DISTINCT
        country_code,
        MAX(country_name) AS country_name
    FROM {{ source('raw', 'raw_economic') }}
    WHERE country_code IS NOT NULL AND country_code != ''
    GROUP BY country_code
),

gain_countries AS (
    SELECT DISTINCT
        country_code,
        MAX(country_name) AS country_name
    FROM {{ source('raw', 'raw_gain') }}
    WHERE country_code IS NOT NULL AND country_code != ''
    GROUP BY country_code
),

labor_countries AS (
    SELECT DISTINCT
        country_code,
        MAX(country_name) AS country_name
    FROM {{ source('raw', 'raw_labor') }}
    WHERE country_code IS NOT NULL AND country_code != ''
    GROUP BY country_code
),

all_codes AS (
    SELECT country_code FROM economic_countries
    UNION
    SELECT country_code FROM gain_countries
    UNION
    SELECT country_code FROM labor_countries
),

final AS (
    SELECT
        a.country_code,

        -- Prefer World Bank name, then ND-GAIN, then ILOSTAT
        COALESCE(e.country_name, g.country_name, l.country_name) AS country_name,

        -- Source presence flags
        (e.country_code IS NOT NULL) AS in_economic,
        (g.country_code IS NOT NULL) AS in_gain,
        (l.country_code IS NOT NULL) AS in_labor,

        -- Audit
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM all_codes a
    LEFT JOIN economic_countries e ON a.country_code = e.country_code
    LEFT JOIN gain_countries     g ON a.country_code = g.country_code
    LEFT JOIN labor_countries    l ON a.country_code = l.country_code
)

SELECT * FROM final
ORDER BY country_code
