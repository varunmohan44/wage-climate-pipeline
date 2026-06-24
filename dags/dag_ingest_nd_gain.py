# Airflow DAG for ND-GAIN vulnerability ingestion.

from datetime import datetime

from airflow.sdk import DAG
from airflow.operators.python import PythonOperator

from config import DEFAULT_ARGS
from ingestion.nd_gain_ingestion import run_ingestion

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
