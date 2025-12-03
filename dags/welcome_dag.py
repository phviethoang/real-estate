from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests

def call_fastapi():
    url = "http://fastapi:8000/run-crawler/"
    params = {
        "min_page": 1,
        "max_page": 1,
        "province": "ha-noi",
        "jump_to_page": 1,
        "estate_type": 2,
        "batch": 1
    }
    response = requests.post(url, params=params)
    response.raise_for_status()  # để DAG fail nếu request lỗi
    print(response.json())

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="run_crawler_hourly",
    default_args=default_args,
    description="Gửi request đến FastAPI crawler mỗi giờ",
    schedule="@hourly",  # Đổi từ schedule_interval sang schedule
    start_date=datetime(2025, 5, 25),
    catchup=False,
    tags=["crawler"],
) as dag:

    run_crawler_task = PythonOperator(
        task_id="call_fastapi_run_crawler",
        python_callable=call_fastapi
    )

    run_crawler_task