from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator

# Airflow runs inside WSL, but the project, Python, the libraries and PostgreSQL are on Windows.
# So each task starts the Windows Python (python.exe) from WSL, inside the project folder.
PROJECT = "/mnt/c/Users/Admin/Downloads/CAPSTONE PROJECT"
PYTHON = "/mnt/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe"

default_args = {
    "owner": "mgm",
    "retries": 1,                          # safe, because every step can be re-run without side effects
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="kenya_cashflow_pipeline_mgm",
    description="Kenya Financial Diaries: extract, transform, load, then dbt build and test",
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule="@weekly",                    # the brief asks for weekly refreshes; you can also trigger it by hand
    catchup=False,
    tags=["capstone", "cashflow"],
) as dag:

    start = EmptyOperator(task_id="start")

    # EXTRACT: check the raw file (exists, not empty, right columns) and log what was read
    extract = BashOperator(
        task_id="extract",
        retries=0,                         # a missing or broken file will not fix itself in 2 minutes
        bash_command=f'cd "{PROJECT}" && "{PYTHON}" -X utf8 extract.py',
    )

    # TRANSFORM: clean the data, build the tables, save the five CSV files
    transform = BashOperator(
        task_id="transform",
        bash_command=f'cd "{PROJECT}" && "{PYTHON}" -X utf8 build_tables.py',
    )

    # LOAD: copy the CSV files into PostgreSQL and check the row counts
    load = BashOperator(
        task_id="load",
        bash_command=f'cd "{PROJECT}" && "{PYTHON}" -X utf8 load_postgres.py',
    )

    # MODEL AND TEST: dbt builds the dashboard tables and runs the data tests
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(f'cd "{PROJECT}/cashflow_dbt" && '
                      f'"{PYTHON}" -X utf8 -W ignore -m dbt.cli.main build --no-use-colors'),
    )

    end = EmptyOperator(task_id="end")

    start >> extract >> transform >> load >> dbt_build >> end
