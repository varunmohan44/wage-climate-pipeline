# Data Dictionary — `fct_labor_conditions`

The pipeline's deliverable mart. Wide, one row per `(country_code, year)`. `stg_labor` is
the spine — every row has at least one ILOSTAT observation for that country-year; World
Bank economic context and ND-GAIN vulnerability scores are left-joined and null where the
source has no data for that country-year. Schema: `dev_facts.fct_labor_conditions` (dbt
target `dev`; `prod` in production).

For full column-level tests and freshness config, see `dbt/models/facts/schema.yml` and
`dbt/models/staging/sources.yml` — this file is the plain-English companion, not a
replacement.

## Keys

| Column | Source | Units | Coverage |
| --- | --- | --- | --- |
| `country_code` | `dim_countries` | ISO 3166-1 alpha-3 | 100% (grain key) |
| `country_name` | `dim_countries` (World Bank → ND-GAIN → ILOSTAT preference) | Text | 100% (grain key) |
| `year` | ILOSTAT (drives the spine) | Calendar year | 100% (grain key) |
| `dbt_updated_at` | dbt | Timestamp | 100%, set on every build |

## Pipeline coverage flags

| Column | Source | Units | Coverage |
| --- | --- | --- | --- |
| `in_economic` | `dim_countries` | Boolean | 100% — true if the country appears anywhere in the World Bank WDI pipeline |
| `in_gain` | `dim_countries` | Boolean | 100% — true if the country appears anywhere in the ND-GAIN pipeline |
| `in_labor` | `dim_countries` | Boolean | Always true here — `fct_labor_conditions` uses ILOSTAT as its spine |

These are **country-level** pipeline coverage, not year-level. A country with `in_economic=true`
can still have null economic columns for individual years where the World Bank has no
observation.

## ILOSTAT labor indicators

| Column | Source (SDMX indicator) | Units | Coverage |
| --- | --- | --- | --- |
| `avg_nominal_earnings_total` | `EAR_EHRA_SEX_ECO_CUR_NB`, sex=total — "Average hourly earnings of employees" | **Not currency-standardized.** ILOSTAT's SDMX response carries an additional currency/unit dimension that `dag_ingest_ilostat.py` does not extract. Do not treat as comparable across countries without checking ILOSTAT directly. | Low (~30–40% of developing-country rows; many low-income countries don't conduct wage surveys or report to ILO) |
| `avg_nominal_earnings_male` | same indicator, sex=male | Same caveat as above | Low |
| `avg_nominal_earnings_female` | same indicator, sex=female | Same caveat as above | Low |
| `gender_wage_gap_pct` | `EAR_GGAP_OCU_RT` — "Gender pay gap" | Percent | Low. Derived from occupation-level data, sparse for countries without detailed labor surveys. **Not range-tested**: real values run from -1104% to 97% (e.g. COD, EGY, WSM, ZAF, LBR) — this is the raw ILOSTAT indicator, not an ingestion artifact. |
| `informality_rate_total` | `EMP_2IFL_SEX_RT`, sex=total — "Informal employment rate (ILO modelled estimates)" | Percent, 0–100 | Medium. Better coverage than earnings — ILO modeled estimates fill gaps for countries without direct surveys. |
| `informality_rate_male` | same indicator, sex=male | Percent, 0–100 | Medium |
| `informality_rate_female` | same indicator, sex=female | Percent, 0–100 | Medium |
| `total_employment_nb` | `EMP_2EMP_SEX_STE_NB`, sex=total, status_in_employment=`STE_AGGREGATE_TOTAL` — "Employment (ILO modelled estimates)" | Count of persons | High (99.9% of `stg_labor` rows). Previously always null: `stg_labor.sql` filtered `status_in_employment = '_T'`, which never matched any real ILOSTAT code. Fixed to filter on `STE_AGGREGATE_TOTAL`, ILO's current ICSE-18-based total classification. The legacy `STE_ICSE93_TOTAL` code carries near-identical values (agrees to the raw figure in ~59% of rows, differs only at the last decimal place otherwise) and was not used. |

## World Bank economic context

| Column | Source (WDI indicator) | Units | Coverage |
| --- | --- | --- | --- |
| `gdp_per_capita_usd` | `NY.GDP.PCAP.CD` | Current USD | High (~95% of countries, recent years) |
| `poverty_headcount_ratio` | `SI.POV.DDAY` | Percent of population below $2.15/day | Low. Survey-based — most countries report every 3–5 years; long null runs between surveys are expected, not a gap. |
| `rural_population_pct` | `SP.RUR.TOTL.ZS` | Percent of total population | High |
| `oda_received_usd` | `DT.ODA.ALLD.CD` | Current USD (can be negative — net aid after debt repayment) | Medium. Null for high-income countries that don't receive ODA — not a data gap. |

## ND-GAIN structural vulnerability

| Column | Source | Units | Coverage |
| --- | --- | --- | --- |
| `gain_vulnerability_score` | ND-GAIN Country Index | 0–1 (higher = more vulnerable) | High |
| `gain_readiness_score` | ND-GAIN Country Index | 0–1 (higher = more ready) | High |
| `gain_overall_score` | ND-GAIN Country Index (readiness minus vulnerability, rescaled) | 0–100 | High |

ND-GAIN's `vulnerability_rank`, `readiness_rank`, `overall_rank`, `region`, and `income_group`
fields are **not** in this mart — they were removed because the ingestion DAG never
populated them (0 of 6,899 rows had values in any of the five).
