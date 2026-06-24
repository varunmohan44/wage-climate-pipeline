# Airflow DAG for ND-GAIN vulnerability ingestion.

from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.operators.python import PythonOperator

from ingestion.nd_gain_ingestion import run_ingestion

DEFAULT_ARGS = {
    "owner": "varun",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="dag_ingest_nd_gain",
    description="Ingest ND-GAIN vulnerability & readiness scores into raw.raw_gain",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule="@yearly",
    catchup=False,
    max_active_runs=1,
    tags=["raw", "gain", "nd-gain"],
) as dag:

    ingest_nd_gain = PythonOperator(
        task_id="ingest_nd_gain",
        python_callable=run_ingestion,
    )
