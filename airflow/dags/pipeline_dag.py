import os
from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.dataproc import  DataprocCreateClusterOperator, DataprocSubmitJobOperator, DataprocDeleteClusterOperator, ClusterGenerator

default_args = {
    'depends_on_past': False   
}

CLUSTER_NAME = 'dataproc-cluster'
REGION = os.environ["region"]
PROJECT_ID = os.environ["project"]
BQ_DATASET = os.environ["bq_dataset"]
GS_BUCKET = os.environ["gs_bucket"]
DATA_SRC = os.environ["data_source"]
INGEST_TASK_URI=f'gs://{GS_BUCKET}/pipeline_jobs/ingest_task.py'
GS_2_BQ_TASK_URI=f'gs://{GS_BUCKET}/pipeline_jobs/gs_2_bq_task.py'
CREATE_INSIGHTS_URI=f'gs://{GS_BUCKET}/pipeline_jobs/create_insights.py'
INIT_ACTION_URIs=[f'gs://{GS_BUCKET}/scripts/pip-install.sh']

CLUSTER_CONFIG = ClusterGenerator(
    project_id=PROJECT_ID,
    master_machine_type="n1-standard-2",
    master_disk_size= 200,
    worker_machine_type="n1-standard-2",
    worker_disk_size= 200,
    num_workers=2,
    init_actions_uris=INIT_ACTION_URIs,
    metadata={'PIP_PACKAGES': 'nltk beautifulsoup4 lxml'},
).make()

INGEST_JOB = {
    "reference": {"project_id": PROJECT_ID},
    "placement": {"cluster_name": CLUSTER_NAME},
    "pyspark_job": {
        "main_python_file_uri": INGEST_TASK_URI,
        "args": [
            f'gs://{DATA_SRC}/*',
            f'gs://{GS_BUCKET}/datalake/'
        ],
    },
}

CREATE_BIGQUERY_TABLE_JOB = {
    "reference": {"project_id": PROJECT_ID},
    "placement": {"cluster_name": CLUSTER_NAME},
    "pyspark_job": {
        "main_python_file_uri": GS_2_BQ_TASK_URI,
        "jar_file_uris": ["gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar"],
        "args": [
            f'gs://{GS_BUCKET}/datalake/*',
            f'{GS_BUCKET}/data_warehouse/temp/',
            BQ_DATASET,
            'all_tweets_partitioned',
        ],
    },
}

CREATE_ISIGHTS_JOB = {
    "reference": {"project_id": PROJECT_ID},
    "placement": {"cluster_name": CLUSTER_NAME},
    "pyspark_job": {
        "main_python_file_uri": CREATE_INSIGHTS_URI,
        "jar_file_uris": ["gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar"],
        "args": [
            f'gs://{GS_BUCKET}/datalake/*',
            f'{GS_BUCKET}/data_warehouse/temp/',
            BQ_DATASET,
            'all_tweets_partitioned',
        ],
    },
}

with DAG(
    'pipeline_dag',
    default_args=default_args,
    description='A simple DAG to ingest tweets dataset and store it in BigQuery',
    schedule_interval=None,
    start_date = days_ago(2)
) as dag:

    create_cluster = DataprocCreateClusterOperator(
        task_id="create_dataproc_cluster",
        project_id=PROJECT_ID,
        cluster_config=CLUSTER_CONFIG,
        region=REGION,
        cluster_name=CLUSTER_NAME,
    )

    ingest_data = DataprocSubmitJobOperator(
        task_id="ingest_data", 
        job=INGEST_JOB, 
        location=REGION, 
        project_id=PROJECT_ID
    )

    create_bigquery_table = DataprocSubmitJobOperator(
        task_id="create_bigquery_table", 
        job=CREATE_BIGQUERY_TABLE_JOB, 
        location=REGION, 
        project_id=PROJECT_ID
    )

    create_insights = DataprocSubmitJobOperator(
        task_id="create_insights", 
        job=CREATE_ISIGHTS_JOB, 
        location=REGION, 
        project_id=PROJECT_ID
    )

    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_dataproc_cluster", 
        project_id=PROJECT_ID, 
        cluster_name=CLUSTER_NAME, 
        region=REGION
    )

    create_cluster >> ingest_data >> create_bigquery_table >> create_insights >> delete_cluster