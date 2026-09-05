# Multi-Source Labor & Development Data Pipeline

An automated, containerized batch pipeline that integrates three heterogeneous public data sources — different APIs, formats, cadences, and country-coding schemes — into a reconciled, tested, analysis-ready data warehouse.

[Built With](#built-with) · [Integration Challenges](#integration-challenges-handled) · [Architecture](#pipeline-architecture) · [The Deliverable](#the-deliverable) · [Getting Started](#getting-started)

---

## What this project does

Public data on labor markets, economic structure, and climate vulnerability lives in three different institutions, in three different formats, on three different update cadences, and under three different country-identification schemes. Any analysis that wants to use them together first has to solve an *integration* problem.

This pipeline solves that problem: it ingests each source, lands it immutably, cleans and conforms it, reconciles every source to a single country key, and builds a wide, tested, documented country-year mart that a downstream analyst or model can consume directly.

The variables are reconciled and co-located, not collapsed into a single score — interpretation is left to whoever queries the mart.

### Built with

![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## Integration challenges handled

Each of the three sources presents a distinct ingestion and reconciliation problem:

| Source | Ingestion pattern | Engineering challenge |
| --- | --- | --- |
| **ILOSTAT** | REST API, monthly, long format | Pagination; reshaping long → wide; high-frequency indicators |
| **World Bank WDI** | REST API, annual, indicator-coded | Different API contract; indicator-code lookups; annual cadence to align with monthly labor data |
| **ND-GAIN** | Static CSV download | File-based ingestion, no API; a country-naming scheme that must be reconciled to the API sources |

Reconciling three country-identification schemes (ISO-2 / ISO-3 / names) into one conformed key is the core integration task, handled once in `dim_countries` so every downstream model joins cleanly.

---

## Pipeline architecture

```
        ILOSTAT API        World Bank API        ND-GAIN CSV
             │                   │                    │
             └─────────── Airflow DAGs (Python) ──────┘
                                 │
                 PostgreSQL — Raw layer (immutable landing)
                                 │
                              dbt Core
                                 │
        Staging (one model per source: clean, type, reshape)
                                 │
             dim_countries  (ISO reconciliation, conformed key)
                                 │
        fct_labor_conditions  ← wide, reconciled, tested
                                 country-year analytical mart
```

Two separate Postgres instances are used by design — one for Airflow's own metadata, one for pipeline data — so orchestration state never contends with the analytical tables.

---

## The deliverable

The product of this pipeline is the data itself:

1. **`fct_labor_conditions`** — a wide, reconciled, tested country-year mart integrating labor and economic indicators, with climate-vulnerability context from the reconciled sources, documented column-by-column.
2. **An interactive lineage graph and data catalog** via dbt docs, which renders the full raw → staging → dimension → fact flow and documents every model and column:
   ```
   make docs
   ```
3. **A data dictionary** (`docs/data_dictionary.md`) describing each column, its source, units, and coverage — what makes the mart usable by someone who didn't build it.

*(An optional derived view, `fct_wage_climate_vulnerability`, illustrates one way the mart could be consumed — a weighted composite, not a validated index or an analytical claim.)*

---

## Data quality

Quality is enforced declaratively and runs on every build:

- **Model & column documentation** — every model and column is described in `schema.yml`, feeding the dbt docs catalog.
- **Tests** (`dbt test`) — `unique` and `not_null` on keys, `relationships` (referential integrity) against `dim_countries`, and `accepted_values` / accepted-range checks on categorical and indicator columns.
- **Source freshness** — `dbt source freshness` checks the raw tables against expected update windows, so stale ingestion is caught rather than silently served.

A broken, drifted, or stale source fails the build loudly instead of corrupting the mart.

---

## Getting started

### Prerequisites
- Docker Desktop
- Python 3.10+
- dbt Core (`pip install dbt-postgres`)

### Quick start

A `Makefile` wraps the common commands:

```bash
git clone https://github.com/varunmohan44/wage-climate-pipeline.git
cd wage-climate-pipeline
cp .env.example .env     # defaults match the Docker Compose setup

make up                  # start Airflow + both Postgres instances
make ingest              # trigger the three ingestion DAGs
make build               # dbt build — runs models + tests
make docs                # generate & serve the dbt docs catalog
```

The Airflow UI is at `http://localhost:8080`; the dbt docs site opens locally after `make docs`.

---

## Data sources

| Source | Role | Cadence | Type |
| --- | --- | --- | --- |
| [ILOSTAT](https://ilostat.ilo.org/data/) | Labor: wages, informality, working poverty, gender wage gap | Monthly | REST API |
| [World Bank WDI](https://data.worldbank.org/) | Economic & structural context (GDP, poverty headcount, rural population, ODA) | Annual | REST API |
| [ND-GAIN](https://gain.nd.edu/our-work/country-index/) | Climate vulnerability & adaptive readiness | Annual | Static CSV |

All three are fully automatable — no scraping required. ND-GAIN downloads automatically when its DAG runs.

---

## Design notes

A few decisions worth surfacing:

- **Immutable raw layer.** Ingestion writes each source to `raw.*` untouched, so every transformation can be replayed without re-pulling from the APIs.
- **Dual Postgres.** Airflow metadata and pipeline data are kept in separate instances so orchestration churn never contends with the analytical tables.
- **Conformed dimension.** Country-key reconciliation across three identification schemes happens once, in `dim_countries`, rather than being re-solved in every join.
- **Cadence alignment.** Monthly labor indicators and annual structural indicators are aligned to a common country-year grain in staging, before they meet in the facts.

---

## Roadmap

- [x] Containerized Airflow + dual-Postgres setup
- [x] Three-source ingestion (ILOSTAT API, World Bank API, ND-GAIN CSV)
- [x] `dim_countries` — ISO reconciliation across all sources
- [x] `fct_labor_conditions` — reconciled analytical mart
- [x] dbt tests, source freshness & column documentation
- [x] dbt docs lineage graph & data dictionary
- [ ] CI: run `dbt build` against a Postgres service on every push

---

## Contact

Varun Mohan — varunmohann@gmail.com
