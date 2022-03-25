from airflow import DAG
from datetime import timedelta
from airflow.utils.dates import days_ago
from airflow.providers.google.cloud.operators.dataproc import  DataprocCreateClusterOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocDeleteClusterOperator

default_args = {
    'depends_on_past': False   
}

CLUSTER_NAME = 'demo-airflow-cluster'
REGION='us-central1'
PROJECT_ID='apt-task-314904'
# PYSPARK_URI='gs://apt-task-314904/spark_gcs_demo.py'


CLUSTER_CONFIG = {
    "master_config": {
        "num_instances": 1,
        "machine_type_uri": "n1-standard-2",
        "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 512},
    },
    "worker_config": {
        "num_instances": 2,
        "machine_type_uri": "n1-standard-2",
        "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 512},
    }
}


# PYSPARK_JOB = {
#     "reference": {"project_id": PROJECT_ID},
#     "placement": {"cluster_name": CLUSTER_NAME},
#     "pyspark_job": {"main_python_file_uri": PYSPARK_URI},
# }

with DAG(
    'dataproc-demo',
    default_args=default_args,
    description='A simple DAG to create a Dataproc workflow',
    schedule_interval=None,
    start_date = days_ago(2)
) as dag:

    create_cluster = DataprocCreateClusterOperator(
        task_id="create_cluster",
        project_id=PROJECT_ID,
        cluster_config=CLUSTER_CONFIG,
        region=REGION,
        cluster_name=CLUSTER_NAME,
    )

    # submit_job = DataprocSubmitJobOperator(
    #     task_id="pyspark_task", 
    #     job=PYSPARK_JOB, 
    #     location=REGION, 
    #     project_id=PROJECT_ID
    # )

    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_cluster", 
        project_id=PROJECT_ID, 
        cluster_name=CLUSTER_NAME, 
        region=REGION
    )

    # create_cluster >> submit_job >> delete_cluster
    create_cluster >> delete_cluster