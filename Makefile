.PHONY: up ingest build docs

# Start Airflow + both Postgres instances, then create the raw.* tables
# (safe to re-run — the SQL scripts are CREATE TABLE IF NOT EXISTS).
up:
	docker compose up -d --wait
	docker compose exec -T pipeline-db psql -U pipeline -d pipeline < sql/create_raw_economic.sql
	docker compose exec -T pipeline-db psql -U pipeline -d pipeline < sql/create_raw_labor.sql
	docker compose exec -T pipeline-db psql -U pipeline -d pipeline < sql/create_raw_gain.sql

# Trigger the three ingestion DAGs.
# Unpause first — DAGs are paused at creation (see docker-compose.yaml), so a
# trigger against a never-unpaused DAG would otherwise queue and never run.
ingest:
	docker compose exec -T airflow-apiserver airflow dags unpause dag_ingest_economic
	docker compose exec -T airflow-apiserver airflow dags trigger dag_ingest_economic
	docker compose exec -T airflow-apiserver airflow dags unpause dag_ingest_ilostat
	docker compose exec -T airflow-apiserver airflow dags trigger dag_ingest_ilostat
	docker compose exec -T airflow-apiserver airflow dags unpause dag_ingest_nd_gain
	docker compose exec -T airflow-apiserver airflow dags trigger dag_ingest_nd_gain

# Run dbt models + tests.
build:
	cd dbt && dbt build

# Generate and serve the dbt docs catalog.
docs:
	cd dbt && dbt docs generate && dbt docs serve --port 8081
