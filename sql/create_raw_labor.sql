-- Raw ILOSTAT wage and labor indicators
-- Upsert key: (country_code, indicator_code, sex, economic_activity, year)
-- Run once to initialize; safe to re-run

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_labor (
    id                  SERIAL PRIMARY KEY,
    country_code        VARCHAR(3)      NOT NULL,   -- ISO 3166-1 alpha-3
    country_name        TEXT            NOT NULL,
    indicator_code      VARCHAR(50)     NOT NULL,
    indicator_name      TEXT            NOT NULL,
    sex                 VARCHAR(50)     NOT NULL,   -- 'SEX_T' | 'SEX_M' | 'SEX_F'
    economic_activity   VARCHAR(50)     NOT NULL,   -- ISIC code or '_T' for total
    status_in_employment VARCHAR(50)    NOT NULL DEFAULT '_T',  -- STE code or '_T' for total
    year                SMALLINT        NOT NULL,
    value               DOUBLE PRECISION,           -- NULL when ILO reports no data
    loaded_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_labor_country_indicator_sex_activity_ste_year
        UNIQUE (country_code, indicator_code, sex, economic_activity, status_in_employment, year)
);

-- Index for join on country_code + year
CREATE INDEX IF NOT EXISTS idx_raw_labor_country_year
    ON raw.raw_labor (country_code, year);

-- Index for filtering to total-sex / total-activity aggregates
CREATE INDEX IF NOT EXISTS idx_raw_labor_sex_activity
    ON raw.raw_labor (sex, economic_activity);
