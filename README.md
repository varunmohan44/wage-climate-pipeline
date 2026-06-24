<h3>Developing World Wage & Labor Vulnerability Pipeline</h3>

<p>A data engineering pipeline that tracks how climate shocks, food insecurity, and structural vulnerability translate into wage depression and labor market deterioration in developing countries. <br /> <a href="#about-the-project"><strong>Explore the docs »</strong></a> <br /><br /> <a href="#roadmap">View Roadmap</a> · <a href="https://github.com/varunmohan44/wage-climate-pipeline/issues/new?labels=bug">Report Bug</a> · <a href="https://github.com/varunmohan44/wage-climate-pipeline/issues/new?labels=enhancement">Request Feature</a></p>

------------------------------------------------------------------------

## Table of Contents

1.  [About The Project](#about-the-project)
    -   [Built With](#built-with)
2.  [Getting Started](#getting-started)
    -   [Prerequisites](#prerequisites)
    -   [Installation](#installation)
3.  [Usage](#usage)
4.  [Roadmap](#roadmap)
5.  [Data Sources](#data-sources)
6.  [Pipeline Architecture](#pipeline-architecture)
7.  [Contact](#contact)
8.  [Acknowledgments](#acknowledgments)

------------------------------------------------------------------------

## About The Project

The academic literature establishes that climate stress depresses wages in developing countries. This pipeline makes that relationship trackable in near real-time. Specifically I ask:

How do climate shocks, food insecurity, and structural vulnerability translate into wage depression and labor market deterioration in developing countries?

Climate and food signals are the explanatory variables. Wages and labor conditions, informed by things like informality rates, working poverty, and gender wage gaps, are what is being explained. The output is a composite country-level index (`fct_wage_climate_vulnerability`) that tracks which countries in the global south are caught in cycles where climate stress worsens wages and deteriorates the labor market and which are showing resilience.

This project fuses multiple publicly available datasets to produce that index. Specifically I join ILOSTAT wage data with World Bank indicators and ND-GAIN vulnerability scores.

### Built With

[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/) [![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://www.getdbt.com/) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/) [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/) [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

------------------------------------------------------------------------

## Getting Started

### Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   Python 3.10+
-   dbt Core (`pip install dbt-postgres`)

### Installation

1.  Clone the repo

    ``` sh
    git clone https://github.com/varunmohan44/wage-climate-pipeline.git
    cd wage-climate-pipeline
    ```

2.  Copy the example environment file

    ``` sh
    cp .env.example .env
    ```

    The defaults match the Docker Compose setup — no changes are required. ND-GAIN data is downloaded automatically when the DAG runs.

3.  Start Airflow and the pipeline database

    ``` sh
    docker compose up -d
    ```

    This starts two Postgres instances: one for Airflow metadata (`localhost:5432`) and one for pipeline data (`localhost:5433`).

4.  Create the raw schema tables

    ``` sh
    psql postgresql://pipeline:pipeline@localhost:5433/pipeline -f sql/create_raw_labor.sql
    psql postgresql://pipeline:pipeline@localhost:5433/pipeline -f sql/create_raw_economic.sql
    psql postgresql://pipeline:pipeline@localhost:5433/pipeline -f sql/create_raw_gain.sql
    ```

5.  Trigger ingestion DAGs in the Airflow UI at `http://localhost:8080` (login: `airflow` / `airflow`)

    Run these three DAGs in order or let them execute on their default schedules:
    - `dag_ingest_economic` — World Bank WDI indicators
    - `dag_ingest_ilostat` — ILOSTAT wages and labor conditions
    - `dag_ingest_nd_gain` — ND-GAIN vulnerability and readiness scores

6.  Run dbt to build the analytical models

    ``` sh
    cd dbt
    dbt run
    dbt test
    ```

7.  Launch the dashboard

    ``` sh
    cd dashboard
    pip install -r ../requirements.txt
    streamlit run app.py
    ```

    Open `http://localhost:8501` in your browser.

------------------------------------------------------------------------

## Usage

The pipeline produces a composite country-level index (`fct_wage_climate_vulnerability`) in the `dev_facts` schema, queryable directly in PostgreSQL or via the Streamlit dashboard.

The dashboard has three pages:

- **Overview** — top 20 most vulnerable countries in the latest year, with GDP and climate vulnerability scores, plus a tier distribution chart
- **Trends** — global P10/average/P90 vulnerability over time (2000–present) and a per-country time series for the top 10 most consistently vulnerable countries
- **Country Explorer** — select any country to view its composite index over time, component breakdown for the most recent year, and a scatter plot of informality vs. vulnerability

![Overview](screenshots/overview.png)
![Trends](screenshots/trends.png)
![Country Explorer](screenshots/explorer.png)

**Data coverage notes:**
- The composite index uses up to 6 components. Rows with fewer than 2 contributing components are excluded. Most countries with full coverage score 4–5 components.
- `informality_rate_total` is currently unpopulated — ILO coverage for the informal employment indicator is sparse and was not ingested. This is a known gap.
- `region` and `income_group` are stored in the schema but not yet populated. They come from the ND-GAIN CSV which does not include those fields directly.

------------------------------------------------------------------------

## Roadmap

- [x] Airflow DAG skeleton & Docker Compose setup
- [x] World Bank API ingestion (`stg_economic`, `stg_climate`)
- [x] ILOSTAT API ingestion (`stg_labor`)
- [x] ND-GAIN CSV ingestion (`stg_gain`)
- [x] `dim_countries` — ISO code reconciliation across all sources
- [x] `fct_labor_conditions` — wide-format analytical labor table
- [x] `fct_wage_climate_vulnerability` — composite index (main output)
- [x] dbt tests & data quality documentation
- [x] Streamlit dashboard (Overview, Trends, Country Explorer)
- [ ] Populate `region` and `income_group` from World Bank country metadata
- [ ] Ingest informal employment rate (`EMP_2IFL_SEX_RT`) from ILOSTAT

------------------------------------------------------------------------

## Data Sources

All sources are fully automatable with no scraping required.

| Source | Role | Cadence | Type |
|----|----|----|----|
| [ILOSTAT](https://ilostat.ilo.org/data/) | **Anchor** — wages, informality, working poverty, gender wage gap | Monthly | REST API |
| [World Bank WDI](https://data.worldbank.org/) | Structural economic context (GDP, poverty headcount, rural pop, ODA) | Annual | REST API |
| [World Bank WDI climate proxies](https://data.worldbank.org/) | Climate exposure/adaptation proxies: electricity access, freshwater withdrawal, precipitation, arable land, forest cover | Annual | REST API |
| [ND-GAIN](https://gain.nd.edu/our-work/country-index/) | Structural climate vulnerability & adaptive readiness | Annual | Static CSV |

> ND-GAIN data is downloaded automatically from [gain.nd.edu](https://gain.nd.edu/our-work/country-index/download-data/) when the DAG runs. No manual download required.

------------------------------------------------------------------------

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Sources                               │
│         ILOSTAT API   │   World Bank API   │   ND-GAIN CSV          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Airflow DAGs (Python)
┌──────────────────────────────▼──────────────────────────────────────┐
│                    PostgreSQL — Raw Layer (raw.*)                   │
│          raw_labor  │  raw_economic  │  raw_gain                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ dbt Core
┌──────────────────────────────▼──────────────────────────────────────┐
│                   dbt — Staging Layer (dev_staging.*)               │
│       stg_labor  │  stg_economic  │  stg_climate  │  stg_gain       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│               dbt — Dimensions & Facts                              │
│   dim_countries → fct_labor_conditions                              │
│                 → fct_wage_climate_vulnerability  ← MAIN OUTPUT     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                        Streamlit Dashboard                          │
│               Overview  │  Trends  │  Country Explorer              │
└─────────────────────────────────────────────────────────────────────┘
```

### dbt Model Structure

```
dbt/models/
├── staging/
│   ├── stg_labor.sql         # ILOSTAT: pivoted to wide format
│   ├── stg_economic.sql      # World Bank: GDP, poverty, ODA
│   ├── stg_climate.sql       # World Bank: climate exposure proxies
│   └── stg_gain.sql          # ND-GAIN: vulnerability & readiness scores
├── dimensions/
│   └── dim_countries.sql     # ISO code reconciliation across sources
└── facts/
    ├── fct_labor_conditions.sql           # wide analytical labor table
    └── fct_wage_climate_vulnerability.sql # composite index (main output)
```

------------------------------------------------------------------------

## Contact

Varun Mohan — varunmohann@gmail.com

Project Link: <https://github.com/varunmohan44/wage-climate-pipeline>

------------------------------------------------------------------------

## Acknowledgments

-   [ILOSTAT — International Labour Organization](https://ilostat.ilo.org/)
-   [World Bank Open Data](https://data.worldbank.org/)
-   [ND-GAIN Country Index — Notre Dame Global Adaptation Initiative](https://gain.nd.edu/)
-   [shields.io](https://shields.io)
