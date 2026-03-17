<h3>Developing World Wage & Labor Vulnerability Pipeline</h3>

<p>A data engineering pipeline that tracks how climate shocks, food insecurity, and structural vulnerability translate into wage depression and labor market deterioration in developing countries. <br /> <a href="#about-the-project"><strong>Explore the docs »</strong></a> <br /><br /> <a href="#roadmap">View Roadmap</a> · <a href="https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues/new?labels=bug">Report Bug</a> · <a href="https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues/new?labels=enhancement">Request Feature</a></p>

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

This project fuses five publicly available, freely accessible datasets to produce that index. Specifically I join ILOSTAT wage data with CHIRPS drought indices, FAOSTAT food security indicators, and ND-GAIN vulnerability scores.

</p>

### Built With

[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/) [![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://www.getdbt.com/) [![BigQuery](https://img.shields.io/badge/BigQuery-4285F4?style=for-the-badge&logo=googlebigquery&logoColor=white)](https://cloud.google.com/bigquery) [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

</p>

------------------------------------------------------------------------

## Getting Started

Follow these steps for a local copy.

### Prerequisites

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
-   [Google Cloud account](https://cloud.google.com/) with a BigQuery project set up
-   A Google Cloud service account key (JSON) with BigQuery permissions
-   Python 3.10+

### Installation

> **In Progress** — full setup instructions will be added as the pipeline is built.

1.  Clone the repo

    ``` sh
    git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    cd YOUR_REPO_NAME
    ```

2.  Copy the example environment file and fill in your credentials

    ``` sh
    cp .env.example .env
    ```

3.  Add your Google Cloud service account key to the project root

    ``` sh
    # Place your key file at: ./gcp-keyfile.json
    ```

4.  Start Airflow with Docker Compose

    ``` sh
    docker compose up -d
    ```

5.  Access the Airflow UI at `http://localhost:8080`

6.  Install dbt dependencies

    ``` sh
    cd dbt
    dbt deps
    dbt debug  # verify BigQuery connection
    ```

</p>

------------------------------------------------------------------------

## Usage

> **In Progress** — usage examples and screenshots will be added as the pipeline and dashboard are built.

The pipeline produces a composite country-level index (`fct_wage_climate_vulnerability`) queryable directly in BigQuery or via the dashboard. The index tracks:

-   Real wage trends vs. drought severity (SPI)
-   Informality rate changes following food price shocks
-   Working poverty correlation with ND-GAIN vulnerability scores
-   Temporal lag structure between climate events and wage responses

</p>

------------------------------------------------------------------------

## Roadmap

-   Airflow DAG skeleton & Docker Compose setup
-   World Bank API ingestion (`stg_economic`)
-   ILOSTAT API ingestion (`stg_labor`)
-   FAOSTAT API ingestion (`stg_food`)
-   ND-GAIN CSV ingestion (`stg_vulnerability`)
-   CHIRPS rainfall ingestion (`stg_climate`)
-   `dim_countries` — ISO code reconciliation across all sources
-   `fct_labor_conditions` — wide-format analytical labor table
-   `fct_wage_climate_vulnerability` — composite index (main output)
-   dbt tests & data quality documentation
-   Dashboard (Metabase or Evidence.dev)
-   Full setup documentation

</p>

------------------------------------------------------------------------

## Data Sources

All five sources are fully automatable with no scraping required.

| Source | Role | Cadence | Type |
|----|----|----|----|
| [ILOSTAT](https://ilostat.ilo.org/data/) | **Anchor** — wages, informality, working poverty, gender wage gap | Monthly | REST API |
| [World Bank WDI](https://data.worldbank.org/) | Structural economic context (GDP, poverty headcount, rural pop, ODA) | Annual | REST API |
| [CHIRPS (UCSB)](https://www.chc.ucsb.edu/data/chirps) | Drought severity — Standardized Precipitation Index (SPI) | Monthly | Pre-aggregated CSV |
| [FAOSTAT](https://www.fao.org/faostat/) | Food insecurity, undernourishment prevalence, cereal yield | Annual | REST API |
| [ND-GAIN](https://gain.nd.edu/our-work/country-index/) | Structural climate vulnerability & adaptive readiness (slowly changing dimension) | Annual | Static CSV |

</p>

------------------------------------------------------------------------

## Pipeline Architecture {#pipeline-architecture}

> **In Progress** - Preliminary pipeline architecture.

```         
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Sources                               │
│  ILOSTAT API │ World Bank API │ CHIRPS CSV │ FAOSTAT API │ ND-GAIN  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Airflow DAGs (Python)
┌──────────────────────────────▼──────────────────────────────────────┐
│                      BigQuery — Raw Layer                           │
│        raw_labor │ raw_economic │ raw_climate │ raw_food │ raw_gain │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ dbt Core
┌──────────────────────────────▼──────────────────────────────────────┐
│                     dbt — Staging Layer                             │
│stg_labor │ stg_economic │ stg_climate │ stg_food │ stg_vulnerability│
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                  dbt — Dimensions & Facts                           │
│    dim_countries → fct_labor_conditions                             │
│                  → fct_wage_climate_vulnerability  ← MAIN OUTPUT    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                          Dashboard                                  │
│                    Metabase / Evidence.dev                          │
└─────────────────────────────────────────────────────────────────────┘
```

### dbt Model Structure

```         
models/
├── staging/
│   ├── stg_labor.sql            # ILOSTAT: pivoted to wide format
│   ├── stg_economic.sql         # World Bank: GDP, poverty, ODA
│   ├── stg_climate.sql          # CHIRPS: SPI drought classification
│   ├── stg_food.sql             # FAOSTAT: undernourishment, cereal yield
│   └── stg_vulnerability.sql    # ND-GAIN: vulnerability & readiness scores
├── dimensions/
│   └── dim_countries.sql        # ISO code reconciliation (SCD)
└── facts/
    ├── fct_labor_conditions.sql
    └── fct_wage_climate_vulnerability.sql
```

</p>

------------------------------------------------------------------------

## Contact {#contact}

Varun Mohan — [LinkedIn](https://linkedin.com/in/YOUR_HANDLE) — varunmohann\@gmail.com

Project Link: <https://github.com/YOUR_USERNAME/YOUR_REPO_NAME>

------------------------------------------------------------------------

## Acknowledgments {#acknowledgments}

-   [ILOSTAT — International Labour Organization](https://ilostat.ilo.org/)
-   [World Bank Open Data](https://data.worldbank.org/)
-   [CHIRPS — Climate Hazards Center, UC Santa Barbara](https://www.chc.ucsb.edu/data/chirps)
-   [FAOSTAT — UN Food and Agriculture Organization](https://www.fao.org/faostat/)
-   [ND-GAIN Country Index — Notre Dame Global Adaptation Initiative](https://gain.nd.edu/)
-   [shields.io](https://shields.io)
