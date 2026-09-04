-- Raw ND-GAIN vulnerability and readiness scores
-- Upsert key: (country_code, year)
-- Run once to initialize; safe to re-run

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_gain (
    id                  SERIAL PRIMARY KEY,
    country_code        VARCHAR(3)      NOT NULL,
    country_name        TEXT            NOT NULL,
    year                SMALLINT        NOT NULL,
    vulnerability_score DOUBLE PRECISION,
    readiness_score     DOUBLE PRECISION,
    overall_score       DOUBLE PRECISION,
    loaded_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_gain_country_year
        UNIQUE (country_code, year)
);

-- Index for join on country_code + year
CREATE INDEX IF NOT EXISTS idx_raw_gain_country_year
    ON raw.raw_gain (country_code, year);
