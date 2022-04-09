import sys
from pyspark.sql import SparkSession, functions as f, types
from unidecode import unidecode

datalake = (sys.argv[1])
bq_temp_bucket = (sys.argv[2])
dataset = (sys.argv[3])
source_table = (sys.argv[4])

# Extract hashtags from the text
def evaluate_hashtags(x):
    hashtags = []
    a = eval(str(x))
    if a:
        for item in a:
            hashtags.append((str(unidecode(item["text"])).lower()))
            hashtags = list(set(hashtags))
    return hashtags

evaluateHashtags = f.udf(lambda t: evaluate_hashtags(t), types.ArrayType(types.StringType()))

spark = SparkSession.builder \
    .master('yarn') \
    .appName('ingest_data') \
    .getOrCreate() 

# Use the Cloud Storage bucket for temporary BigQuery export data used by the connector.
spark.conf.set("temporaryGcsBucket", bq_temp_bucket)

# Load data from Datalake.
df = spark.read \
  .option('dataset', dataset) \
  .option('table', source_table) \
  .format('bigquery') \
  .load()    

# Create overall sentiment ratio.
averall_sentiment_ratio = df \
    .groupby('sentiment') \
    .count()

# Create overall sentiment ratio over time.
averall_sentiment_ratio_over_time = df \
    .groupby('date', 'sentiment')\
    .count() 

# Count tweets over time.
count_tweets_over_time = df \
    .groupby('date')\
    .count()     

# Get top 10 hashtags.
top10Hashtags = df \
    .withColumn('hashtags', evaluateHashtags("hashtags")) \
    .where("language = 'en'") \
    .withColumn("hashtags", f.explode("hashtags")) \
    .groupby("hashtags") \
    .count() \
    .orderBy(f.col('count').desc()) \
    .limit(10)

# Write the data to Bigquery
averall_sentiment_ratio \
    .write.format('bigquery') \
    .mode('overwrite') \
    .option('dataset', dataset) \
    .option('table', 'overall_sentiment_ratio') \
    .save() 

averall_sentiment_ratio_over_time \
    .write.format('bigquery') \
    .mode('overwrite') \
    .option('dataset', dataset) \
    .option('table', 'averall_sentiment_ratio_over_time') \
    .save()

count_tweets_over_time \
    .write.format('bigquery') \
    .mode('overwrite') \
    .option('dataset', dataset) \
    .option('table', 'count_tweets_over_time') \
    .save()

top10Hashtags \
    .write.format('bigquery') \
    .mode('overwrite') \
    .option('dataset', dataset) \
    .option('table', 'top10Hashtags') \
    .save()               
