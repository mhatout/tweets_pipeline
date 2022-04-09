import sys
import re
from pyspark.sql import SparkSession, types
from pyspark.sql.functions import col, udf, to_date
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
from html import unescape

source_path = (sys.argv[1])
output_path = (sys.argv[2])

nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# removing URLS from our text
def remove_urls(x):
    cleaned_string = re.sub(r'(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b', '', str(x), flags=re.MULTILINE)
    return cleaned_string

# unescape characters
def unescape_stuff(x):
    soup = BeautifulSoup(unescape(x), 'lxml')
    return soup.text    

# remove emoticons
def deEmojify(x):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'', x)    

# replace consecutive whitespaces as one
def unify_whitespaces(x):
    cleaned_string = re.sub(' +', ' ', x)
    return cleaned_string

# remove unwanted symbols but preserve sentence structure by maintaining "?" , ",", "!", and "."
def remove_symbols(x):
    cleaned_string = re.sub(r"[^a-zA-Z0-9?!.,]+", ' ', x)
    return cleaned_string  

# clean the text
def clean_text(x):
    cleaned_string = remove_urls(x)
    cleaned_string = unescape_stuff(cleaned_string)
    cleaned_string = deEmojify(cleaned_string)
    cleaned_string = unify_whitespaces(cleaned_string)
    cleaned_string = remove_symbols(cleaned_string)
    return cleaned_string


def decide_sentiment(score):
    if score['neg'] > 0.6:
        return 'NEGATIVE'
    elif score['pos'] > 0.6:
        return 'POSITIVE'
    elif score['neu'] > 0.95:
        return 'NEUTRAL'
    else:
        score['neg'] += score['neu']/2
        score['pos'] += score['neu']/2
        return decide_sentiment(score)
    
# predict tweet sentiment
def sentiment_prediction(sentence):
    try:        
        sentiment_score = sid.polarity_scores(sentence)
        return decide_sentiment(sentiment_score)
    except Exception:
        print(sentence)
        pass  # or you could use 'continue'
    
    return "NEUTRAL" 


# Convert functions to UDFs
cleanString = udf(lambda t: clean_text(t))
predictSentiment = udf(lambda t: sentiment_prediction(t))    

spark = SparkSession.builder \
    .master('yarn') \
    .appName('ingest_data') \
    .getOrCreate()  

# Set DataFrame schema
schema = types.StructType([
    types.StructField("index", types.IntegerType(), True),
    types.StructField("userid", types.LongType(), True),
    types.StructField("username", types.StringType(), True),
    types.StructField("acctdesc", types.StringType(), True),
    types.StructField("location", types.StringType(), True),
    types.StructField("following", types.IntegerType(), True),
    types.StructField("followers", types.IntegerType(), True),
    types.StructField("totaltweets", types.IntegerType(), True),
    types.StructField("usercreatedts", types.TimestampType(), True),
    types.StructField("tweetid", types.LongType(), True),
    types.StructField("tweetcreatedts", types.TimestampType(), True),
    types.StructField("retweetcount", types.IntegerType(), True),
    types.StructField("text", types.StringType(), True),
    types.StructField("hashtags", types.StringType(), True),
    types.StructField("language", types.StringType(), True),
    types.StructField("coordinates", types.StringType(), True),
    types.StructField("favorite_count", types.IntegerType(), True),
    types.StructField("extractedts", types.TimestampType(), True),
])

# Load data from Source.
df = spark.read \
    .option("header", "true") \
    .option("multiline","true") \
    .option("quote", "\"") \
    .option("escape", "\"") \
    .schema(schema) \
    .csv(source_path)

# Drop unwanted columns, Clean tweet text and make sentiment prediction
columns_to_drop = [
    'index', 'userid', 'username',
    'acctdesc', 'usercreatedts',
    'tweetid', 'coordinates',
    'favorite_count', 'extractedts']    
df = df \
    .drop(*columns_to_drop) \
    .withColumn('text', cleanString(col('text'))) \
    .withColumn('sentiment', predictSentiment(col('text')))\
    .withColumn('date', to_date(col('tweetcreatedts'))) \
    .drop('tweetcreatedts') \
    .dropna(subset=('date'))    

# Saving the data to DataLake
df \
    .repartition(24) \
    .write \
    .mode('overwrite') \
    .parquet(output_path)
           
