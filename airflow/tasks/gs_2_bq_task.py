import sys
from pyspark.sql import SparkSession

datalake = (sys.argv[1])
bq_temp_bucket = (sys.argv[2])
dataset = (sys.argv[3])
table = (sys.argv[4])

spark = SparkSession.builder \
    .master('yarn') \
    .appName('create_bigquery_table') \
    .getOrCreate()

# Use the Cloud Storage bucket for temporary BigQuery export data used by the connector.
spark.conf.set("temporaryGcsBucket", bq_temp_bucket)    

# Load data from Datalake.
df = spark.read \
    .parquet(datalake)

# Write the data to Bigquery
df \
    .write.format('bigquery') \
    .mode('overwrite') \
    .option('dataset', dataset) \
    .option('table', table) \
    .option('partitionField', 'date') \
    .save()    
