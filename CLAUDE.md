# CLAUDE.md

Guidelines for AI assistants working in this repository. The behavioral section is
adapted from the [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
CLAUDE.md (common LLM coding pitfalls); the project section is specific to this pipeline.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- Map dbt model dependencies **before** editing a model — know what is downstream.

## 2. Simplicity First

**Minimum that solves the problem. Nothing speculative.**

- No sources, models, columns, or tooling beyond what was asked.
- Specifically out of scope: streaming/Kafka, Spark, dbt incremental models (the data is
  a few thousand country-year rows), or a second validation framework on top of dbt tests.
- No configurability or abstraction that wasn't requested.
- If a transform is 200 lines and could be 50, rewrite it.

Ask: "Would a senior data engineer call this overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent models, SQL, or formatting.
- Match the existing dbt/SQL style, even if you'd do it differently.
- Remove only the imports/CTEs/columns that YOUR change orphaned.
- If you spot pre-existing dead code, mention it — don't delete it unless asked.

The test: every changed line traces directly to the request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

- "Add a data-quality check" → write the dbt test, run `dbt build`, confirm it passes.
- "Trim a source" → map every reference first, remove, then confirm `dbt build` and
  `dbt docs generate` still run clean.
- "Fix the model" → reproduce the problem with a failing test, then make it pass.

State a brief plan for multi-step tasks:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

---

**Working if:** fewer unnecessary lines in diffs, fewer rewrites from overcomplication, and
clarifying questions arrive before implementation rather than after mistakes.

---

## Project context

An automated batch pipeline integrating three heterogeneous public sources (labor,
economic, climate-vulnerability) into a reconciled, tested PostgreSQL warehouse. The
product is the data — a documented country-year mart — not a dashboard or a model.
`README.md` is the source of truth for how the project is described.

```
dags/                 Airflow ingestion DAGs (Python)
  dag_ingest_ilostat.py    ILOSTAT REST API  → raw.raw_labor
  dag_ingest_economic.py   World Bank WDI API → raw.raw_economic
  dag_ingest_nd_gain.py    ND-GAIN static CSV → raw.raw_gain
dbt/models/
  staging/            One model per source: clean, type, reshape (1:1, no joins)
  dimensions/         dim_countries — ISO reconciliation, conformed key
  facts/              fct_labor_conditions (deliverable);
                      fct_wage_climate_vulnerability (illustrative only)
dashboard/            Streamlit app (optional explorer, not the deliverable)
docker-compose.yaml   Airflow + two Postgres (pipeline data :5433, Airflow metadata :5432)
```

Data flow: `sources → Airflow DAGs → raw.* (immutable) → dbt staging → dim_countries → facts`

## Project guardrails (do not violate without asking)

- Raw layer is **immutable**; never transform in `raw.*`.
- Staging models are **1:1 with their source, no joins**; all cross-source joining happens
  at or after `dim_countries`.
- **Do not reframe `fct_wage_climate_vulnerability` as a finding.** It is an optional
  illustrative composite — never a validated index or a causal/correlational claim. Do not
  reintroduce "climate depresses wages"–style language anywhere.
- **Three sources only** (ILOSTAT, World Bank, ND-GAIN). Do not add sources; do not
  reintroduce the trimmed World Bank "climate proxy" indicators.

## Commands

```
make up        # start Airflow + both Postgres instances
make ingest    # trigger the three ingestion DAGs
make build     # dbt build — models + tests
make docs      # generate & serve the dbt docs catalog
```

## Design rationale — FILL IN (these answers should be yours)

> The "why" questions an interviewer will ask. Write them in your own words; this also
> stops an assistant from guessing wrong.

- **Why this project / what real question does it answer?** …
- **Why dbt** rather than plain SQL scripts or pandas? …
- **Why Airflow**, given annual/monthly batch data? (Be honest where it's heavier than needed.) …
- **Why two separate Postgres instances?** …
- **Why PostgreSQL** here vs. a lighter embedded store like DuckDB? …
- **Why these three sources, and why not more?** …
- **Why no statistical/ML modeling** in this project? …
