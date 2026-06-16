-- World Bank climate proxy indicators
-- Grain: one row per country/year

WITH source AS (
    SELECT
        country_code,
        country_name,
        indicator_code,
        value,
        year
    FROM {{ source('raw', 'raw_economic') }}
    WHERE indicator_code IN (
        'EG.ELC.ACCS.ZS',
        'ER.H2O.FWTL.ZS',
        'AG.LND.PRCP.MM',
        'AG.LND.ARBL.ZS',
        'AG.LND.FRST.ZS'
    )
),

pivoted AS (
    SELECT
        country_code,
        MAX(country_name) AS country_name,
        year,

        MAX(CASE WHEN indicator_code = 'EG.ELC.ACCS.ZS' THEN value END) AS access_to_electricity_pct,
        MAX(CASE WHEN indicator_code = 'ER.H2O.FWTL.ZS' THEN value END) AS freshwater_withdrawal_pct_internal_resources,
        MAX(CASE WHEN indicator_code = 'AG.LND.PRCP.MM' THEN value END) AS precipitation_mm,
        MAX(CASE WHEN indicator_code = 'AG.LND.ARBL.ZS' THEN value END) AS arable_land_pct,
        MAX(CASE WHEN indicator_code = 'AG.LND.FRST.ZS' THEN value END) AS forest_area_pct
    FROM source
    GROUP BY country_code, year
)

SELECT
    country_code,
    country_name,
    year,
    access_to_electricity_pct,
    freshwater_withdrawal_pct_internal_resources,
    precipitation_mm,
    arable_land_pct,
    forest_area_pct,
    CURRENT_TIMESTAMP AS dbt_updated_at
FROM pivoted
