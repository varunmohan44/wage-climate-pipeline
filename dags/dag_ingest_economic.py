"""Airflow DAG for World Bank WDI ingestion into raw.raw_economic."""

from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.operators.python import PythonOperator

from ingestion.world_bank_ingestion import run_ingestion

DEFAULT_ARGS = {
    "owner": "varun",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="dag_ingest_economic",
    description="Ingest World Bank WDI indicators into raw.raw_economic",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule="@monthly",
    catchup=False,
    max_active_runs=1,
    tags=["raw", "economic", "world-bank"],
) as dag:

    ingest_world_bank = PythonOperator(
        task_id="ingest_world_bank",
        python_callable=run_ingestion,
    )
