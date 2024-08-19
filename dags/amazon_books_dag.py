from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.models.connection import Connection
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "single_spark_etl_workflow",
    default_args=default_args,
    description="ETL workflow using a single Spark job",
    schedule_interval=timedelta(minutes=2),
    start_date=datetime.now() - timedelta(minutes=2),
    catchup=False,
)


# Task: Run the full ETL job in a single Spark job
etl_task = SparkSubmitOperator(
    task_id="full_etl_job",
    application="/opt/jobs/spark_etl.py",
    name="full_etl_job",
    conn_id="SPARK_LOCAL",
    verbose=1,
    application_args=[],
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
