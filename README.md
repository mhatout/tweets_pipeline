# TWEETS_ANALYSIS_PIPELINE
A data pipeline to ingest datasets consist of tweets about Russian/Ukrainian war then perform some data cleaning and preprocessing and lastly perform sentiment analysis to build a general understanding of the sentiment of the tweets. 

## Project Description
This is the end-to-end project to gain insight into the main sentiment of the Russian/Ukrainian war in the Twitter realm. In this project, I covered the scope of data engineering (building the data pipeline) & data analytics (building a visualization dashboard). I used Terraform to provision my cloud infrastructure, Apache Airflow to orchestrate the workflow of the pipeline, Apache Spark for data ingestion, preprocessing and extracting insights, and Google Data Studio to build the visualization dashboard.

## Objective
  * Perform sentiment analysis on +15M tweets about the Russian/Ukrainian war to gain a rough understanding of What is the public sentiment in Twitterverse about the ongoing conflict.
  * Build A visualization dashboard to visualize the extracted insights.

## Dataset
Datasets contain tweets monitoring the current ongoing Ukraine-Russia conflict. Context and history of the current ongoing conflict can be found [here](https://en.wikipedia.org/wiki/2022RussianinvasionofUkraine). The dataset is available on [Kaggle](https://www.kaggle.com/datasets/bwandowando/ukraine-russian-crisis-twitter-dataset-1-2-m-rows)


## Tools & Technology
* Terraform (IaC)
* Cloud: Google Cloud Platform (GCP)
  * Managed Cloud Scheduling: Google Composer
  * Managed Proccesing Cluster: Google Dataproc
  * Data Lake: Google Cloud Storage (GCS)
  * Data Warehouse: Google Big Query (GBQ)
  * Data Visualization: Google Data Studio (GDS)
* Orchestration: Apache Airflow
* Data Transformation: Apache Spark (Pyspark)
* Scripting Language: Python

## Data Pipeline
I have created a an Airflow DAG that will create a dataproc cluster and run the data run Spark jobs that will perform the entire ETL process. The DAG consists of the following steps:
 * create_dataproc_cluster:
    * Create a DataProc cluster by useing "DataprocCreateClusterOperator" Airflow operator.
 * ingest_data:
    * read the data from the GCS bucket and ingest it into a Spark dataframe.
    * perform some data cleaning, preprocessing.
    * run the pretrained model to extract the sentiment of the tweets.
    * upload the datafram data lake, google cloud storage (GCS) in parquet format.
 * create_bigquery_table:
    * gcs_bigquery: create the table in data warehouse, google big query (GBQ) by the parquet files in datalake.
 * create_insights:
    * read the data from the bigquery table and ingest it into a Spark dataframe.
    * perform analysis on the dataframe to gain some useful insights.
    * bigquery: create 4 tables in data warehouse containing the insights extracted from the datafram.
 * delete_dataproc_cluster:
    * Delete the Dataproc cluster after finishing all the jobs submitted to avoid any unnecessary costs.      
<img alt = "image" src = "https://i.ibb.co/zswN4FF/tweets-dag.png">

## Data Visualization
I created a visualization dashboard consest of 4 tiles showing the end result of the project. <br>
Tweets Sentiment Analysis Dashboard: [url](https://datastudio.google.com/reporting/931e263a-3c17-45f3-b03a-12c4f1193262/page/Fl5pC)

<img alt = "image" src = "https://i.ibb.co/4McMtSg/tweets-setiment-dashboard.png">

## Reproductivity

# Step 1: Setup the Base Environment <br>
Required Services: <br>
* [Google Cloud Platform](https://console.cloud.google.com/) - register an account with credit card GCP will free us $300 for 3 months
    * Create a service account & download the keys as json file. The json file will be useful for further steps.
    * Enable the API related to the services (Google Compute Engine, Google Cloud Storage, Cloud Composer, Cloud Dataproc & Google Big Query)
    * follow the Local Setup for Terraform and GCP [here](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/week_1_basics_n_setup/1_terraform_gcp)

# Step 2: Provision your cloud infrastructure useing Terraform<br>
* copy your GCP project name into "project" var in variable.tf.
* run the following commands:
```console
terraform init
```
```console
terraform apply -auto-approve
```
> Provisioning the cloud infrastructure may take up to 20 minutes.

# Step 3: Run the data pipeline using Airflow<br>
* Copy the "pip-install.sh" file from your local storage into GS bucket scripts folder.
```console
gsutil cp path_to_the_project/tweets_pipeline/airflow/scripts/pip-install.sh gs://GS_Bucket/scripts/
```

* Copy the airflow dag file into the airflow/dags folder.
```console
gsutil cp path_to_the_project/tweets_pipeline/airflow/dags/pipeline_dag.py gs://CLOUD_COMPOSER_BUCKET/dags/
```
> You can find the Airflow dag floder by going to Cloud Composer page and clicking on the "DAGs" tab and you can access Airflow UI web server by clicking on "Airflow" tab.
<img alt = "image" src = "https://i.ibb.co/4VnJcFF/composer-dags.png">

* Copy the Airflow dag tasks into GS bucket.
```console
gsutil cp path_to_the_project/tweets_pipeline/airflow/tasks/* gs://GS_Bucket/pipeline_jobs/
```
* From the Airflow UI page triger the pipeline_dag DAG and wait for it to finish.
> This process may take up to 2.5 hours.

# Setup 4: Create the visualization dashboard<br>
* Open Google Data Studio and create blank report then connect with bigquery.
> It will ask you to authorise the access to Bigquery - do as instructed.
* Choose the project and add the following tables to the report:
   * top10Hashtags
   * count_tweets_over_time
   * averall_sentiment_ratio_over_time
   * overall_sentiment_ratio
* Add the 4 charts as shown on the dashboard I'm sharing [here](https://datastudio.google.com/reporting/931e263a-3c17-45f3-b03a-12c4f1193262) or you can just take copy of the shared dashboard and connect it to your tables.

## Further Improvements:
* Add Streaming Pipeline (Apache Kafka) in this project to extract live tweets and procees them in realtime.
* Train a more accurate model to extract the sentiment of the tweets.

## Special Thanks:
Huge thanks for [DataTalks.Club](https://datatalks.club) for putting so much effort into these courses to contribute to the community. Can't thank you enough <br>

Besides, Thanks to bwandowando for providing the Tweets Dataset. You're very kind to share your work with the public for academic purposes.<br>
