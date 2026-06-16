-- Pivots raw.raw_labor from long format (one row per country/indicator/sex/year)
-- to wide format (one row per country/year, each indicator×sex combination as its own column).
--
-- Null values are passed through — filtering happens at the fact layer.
--
-- Grain: one row per (country_code, year)

WITH source AS (
    SELECT
        country_code,
        country_name,
        indicator_code,
        sex,
        status_in_employment,
        year,
        value
    FROM {{ source('raw', 'raw_labor') }}
),

pivoted AS (
    SELECT
        country_code,
        MAX(country_name) AS country_name,
        year,

        -- Average nominal earnings by sex (EAR_EHRA_SEX_ECO_CUR_NB)
        MAX(CASE WHEN indicator_code = 'EAR_EHRA_SEX_ECO_CUR_NB' AND sex = 'SEX_T' THEN value END) AS avg_nominal_earnings_total,
        MAX(CASE WHEN indicator_code = 'EAR_EHRA_SEX_ECO_CUR_NB' AND sex = 'SEX_M' THEN value END) AS avg_nominal_earnings_male,
        MAX(CASE WHEN indicator_code = 'EAR_EHRA_SEX_ECO_CUR_NB' AND sex = 'SEX_F' THEN value END) AS avg_nominal_earnings_female,

        -- Gender wage gap by occupation (EAR_GGAP_OCU_RT) — single ratio, no sex split
        MAX(CASE WHEN indicator_code = 'EAR_GGAP_OCU_RT' THEN value END) AS gender_wage_gap_pct,

        -- Informal employment rate by sex (EMP_2IFL_SEX_RT)
        MAX(CASE WHEN indicator_code = 'EMP_2IFL_SEX_RT' AND sex = 'SEX_T' THEN value END) AS informality_rate_total,
        MAX(CASE WHEN indicator_code = 'EMP_2IFL_SEX_RT' AND sex = 'SEX_M' THEN value END) AS informality_rate_male,
        MAX(CASE WHEN indicator_code = 'EMP_2IFL_SEX_RT' AND sex = 'SEX_F' THEN value END) AS informality_rate_female,

        -- Total employment count (EMP_2EMP_SEX_STE_NB) — total sex, total status in employment
        MAX(CASE WHEN indicator_code = 'EMP_2EMP_SEX_STE_NB' AND sex = 'SEX_T' AND status_in_employment = '_T' THEN value END) AS total_employment_nb

    FROM source
    GROUP BY country_code, year
),

final AS (
    SELECT
        country_code,
        country_name,
        year,
        avg_nominal_earnings_total,
        avg_nominal_earnings_male,
        avg_nominal_earnings_female,
        gender_wage_gap_pct,
        informality_rate_total,
        informality_rate_male,
        informality_rate_female,
        total_employment_nb,
        CURRENT_TIMESTAMP AS dbt_updated_at
    FROM pivoted
)

SELECT * FROM final
