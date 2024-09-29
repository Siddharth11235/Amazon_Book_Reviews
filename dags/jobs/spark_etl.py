import pyspark
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_timestamp, col, udf
from pyspark.sql.types import StringType
from pyspark.sql.types import *

import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from psycopg2 import extras
import psycopg2
import os
import sys


def main():
    file_name = sys.argv[1]
    # Initialize Spark session and sentiment analyser
    spark = (
        SparkSession.builder.appName("Book_ETL")
        .master("spark://spark-master:7077")
        .getOrCreate()
    )

    df = spark.read.json(file_name)

    analyzer = SentimentIntensityAnalyzer()

    @udf
    def analyze_sentiment(text):
        if text is None:
            return 0.0  # handle nulls gracefully
        score = analyzer.polarity_scores(text)["compound"]
        return float(score)

    # There is a spark function available for this.
    @udf(StringType())
    def clean_text(text):
        if text:
            return text.replace("\x00", "")  # Remove null bytes
        return text

    filtered_data_df = df.filter(
        col("review_text").isNotNull()
        & col("asin").isNotNull()
        & col("review_date").isNotNull()
        & col("rating").isNotNull()
    )

    filtered_data_df = filtered_data_df.filter(col("review_text") != "")

    print(filtered_data_df.count())
    asins = (
        filtered_data_df.select("asin").distinct().rdd.flatMap(lambda x: x).collect()
    )
    db_connection = psycopg2.connect(
        host="postgres",
        port=5432,
        database="book_reviews",
        user="postgres",
        password="postgres",
        connect_timeout=30,
    )

    with db_connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS temp_asins;")
        cur.execute("CREATE TABLE temp_asins (asin VARCHAR);")

        # Insert the ASINs into the temp table
        for asin in asins:
            cur.execute("INSERT INTO temp_asins (asin) VALUES (%s);", (asin,))

        db_connection.commit()

    metadata_query = """
        (SELECT bm.*, ta.asin as temp_asin
        FROM book_metadata bm
        JOIN temp_asins ta ON bm.asin = ta.asin) AS subquery
    """

    # Enrich data with metadata from PostgreSQL
    metadata_df = (
        spark.read.format("jdbc")
        .option("url", "jdbc:postgresql://postgres:5432/book_reviews")
        .option("dbtable", metadata_query)
        .option("user", "postgres")
        .option("password", "postgres")
        .option("driver", "org.postgresql.Driver")
        .load()
    )

    # Transform the data
    enriched_df = filtered_data_df.join(
        metadata_df, filtered_data_df["asin"] == metadata_df["temp_asin"]
    )
    enriched_df = enriched_df.drop("temp_asin")

    # Apply sentiment analysis to the joined dataframe
    enriched_df = enriched_df.withColumn(
        "review_sentiment_score", analyze_sentiment(enriched_df["review_text"])
    )
    enriched_df = enriched_df.drop(metadata_df["asin"])
    enriched_df = enriched_df.withColumn(
        "review_date", to_timestamp(col("review_date"), "yyyy-MM-dd'T'HH:mm:ss")
    )
    enriched_df = enriched_df.withColumn(
        "review_sentiment_score", col("review_sentiment_score").cast("float")
    )
    enriched_df = enriched_df.withColumn("review_text", clean_text(col("review_text")))
    enriched_df.show()

    # Load the transformed data into PostgreSQL
    enriched_df.write.format("jdbc").option(
        "url", "jdbc:postgresql://postgres:5432/book_reviews"
    ).option("dbtable", "book_data_enriched").option("user", "postgres").option(
        "password", "postgres"
    ).option(
        "driver", "org.postgresql.Driver"
    ).mode(
        "append"
    ).save()


if __name__ == "__main__":
    main()
