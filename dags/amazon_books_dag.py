from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.bash import BashOperator

from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable


import json
import requests

from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

JSON_BATCH_COUNT = 0


def fetch_and_save_reviews(**kwargs):

    response = requests.get("http://datagen:5000/reviews")
    reviews = response.json()

    json_batch_count = int(Variable.get("json_batch_count", default_var=0))
    print(json_batch_count)

    completion_status = reviews["is_json_completed"]
    book_review_data = reviews["book_reviews"]
    # save the data to a json file
    file_path = f"/tmp/reviews_data_{json_batch_count}.json"
    with open(file_path, "w") as f:
        json.dump(book_review_data, f)

    # push the file path to xcom
    kwargs["ti"].xcom_push(key="file_path", value=file_path)
    kwargs["ti"].xcom_push(key="completion", value=completion_status)

    json_batch_count += 1
    Variable.set("json_batch_count", json_batch_count)


def check_json_completion(**kwargs):
    ti = kwargs["ti"]
    completion_status = ti.xcom_pull(
        key="completion", task_ids="fetch_and_save_reviews"
    )
    return completion_status


def branch_on_completion(**kwargs):
    ti = kwargs["ti"]
    completion_status = ti.xcom_pull(key="completion", task_ids="check_json_completion")
    if completion_status:
        return "end_task"
    else:
        return "full_etl_job"


dag = DAG(
    "single_spark_etl_workflow",
    default_args=default_args,
    description="ETL workflow using a single Spark job",
    schedule_interval=timedelta(minutes=2),
    start_date=datetime.now() - timedelta(minutes=2),
    catchup=False,
)

fetch_reviews_task = PythonOperator(
    task_id="fetch_and_save_reviews",
    python_callable=fetch_and_save_reviews,
    dag=dag,
)


check_completion_task = PythonOperator(
    task_id="check_json_completion",
    python_callable=check_json_completion,
    provide_context=True,
    dag=dag,
)

branch_op = BranchPythonOperator(
    task_id="branch_on_completion",
    python_callable=branch_on_completion,
    provide_context=True,
    dag=dag,
)

# Dummy task to end the DAG gracefully
end_task = DummyOperator(
    task_id="end_task",
    dag=dag,
)


# Task: Run the full ETL job in a single Spark job
etl_task = SparkSubmitOperator(
    task_id="full_etl_job",
    application="/opt/jobs/spark_etl.py",
    name="full_etl_job",
    conn_id="SPARK_LOCAL",
    verbose=1,
    application_args=[
        "{{ ti.xcom_pull(key='file_path', task_ids='fetch_and_save_reviews') }}"
    ],
    dag=dag,
    conf={
        "spark.master": "spark://spark-master:7077",
        "spark.driver.memory": "8g",
        "spark.executor.memory": "8g",
        "spark.executor.cores": "6",
        "spark.driver.cores": "6",
        "spark.network.timeout": "10000s",
        "spark.driver.maxResultSize": "2G",
        "spark.executor.heartbeatInterval": "10000",
        "spark.core.connection.ack.wait.timeout": "3600",
        "spark.executor.logs.rolling.maxRetainedFiles": "5",
        "spark.executor.logs.rolling.enableCompression": "true",
        "spark.executor.logs.rolling.maxSize": "128m",
        "spark.executor.logs.rolling.strategy": "size",
    },
    jars="/opt/spark/jars/postgresql-42.2.20.jar",
)


cleanup_task = BashOperator(
    task_id="cleanup_json_file",
    bash_command="rm {{ ti.xcom_pull(key='file_path', task_ids='fetch_and_save_reviews') }}",
    dag=dag,
)


fetch_reviews_task >> check_completion_task >> branch_op
branch_op >> etl_task >> cleanup_task
branch_op >> end_task
