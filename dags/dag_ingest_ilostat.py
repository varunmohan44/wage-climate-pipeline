# Airflow DAG for ILOSTAT wage and labor indicator ingestion.

from datetime import datetime

from airflow.sdk import DAG
from airflow.operators.python import PythonOperator

from config import DEFAULT_ARGS
from ingestion.ilostat_ingestion import run_ingestion

with DAG(
    dag_id="dag_ingest_ilostat",
    description="Ingest ILOSTAT wage and labor indicators into raw.raw_labor",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule="@monthly",
    catchup=False,
    max_active_runs=1,
    tags=["raw", "labor", "ilostat"],
) as dag:

    ingest_ilostat = PythonOperator(
        task_id="ingest_ilostat",
        python_callable=run_ingestion,
    )
