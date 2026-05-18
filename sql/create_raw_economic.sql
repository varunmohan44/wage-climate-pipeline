-- Raw World Bank WDI data
-- Upsert key: (country_code, indicator_code, year)
-- Run once to initialize; safe to re-run (CREATE TABLE IF NOT EXISTS)

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_economic (
    id                  SERIAL PRIMARY KEY,
    country_code        VARCHAR(3)      NOT NULL,   -- ISO 3166-1 alpha-3
    country_name        TEXT            NOT NULL,
    indicator_code      VARCHAR(50)     NOT NULL,
    indicator_name      TEXT            NOT NULL,
    year                SMALLINT        NOT NULL,
    value               DOUBLE PRECISION,           -- NULL when WB reports no data
    loaded_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_economic_country_indicator_year
        UNIQUE (country_code, indicator_code, year)
);

-- Index for join on country_code + year
CREATE INDEX IF NOT EXISTS idx_raw_economic_country_year
    ON raw.raw_economic (country_code, year);

