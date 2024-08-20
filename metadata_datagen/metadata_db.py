import os

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, regexp_extract
from pyspark.sql.types import *

import psycopg2
from dotenv import load_dotenv

load_dotenv()
MAX_MEMORY = "12G"


class MetadataProcessor:
    def __init__(self, spark):
        self.spark = spark
        self.df = None

    def load_metadata(self, filename):
        print(filename)
        self.df = self.spark.read.json(filename, mode="DROPMALFORMED")

    def clean_metadata(self):
        self.df = self.df.withColumn(
            "brand", regexp_extract(col("brand"), r"^Visit Amazon's(.*?) Page$", 1)
        )
        self.df = self.df.filter(col("price") != "")
        self.df = self.df.filter(col("brand") != "")
        self.df = self.df.withColumn(
            "price (USD)", regexp_replace(col("price"), r"^\$", "").cast("float")
        )
        self.df = self.df.drop("price")

        self.df = self.df.filter(
            col("brand").isNotNull()
            & col("asin").isNotNull()
            & col("title").isNotNull()
            & col("price (USD)").isNotNull()
        )
        self.df = self.df.dropDuplicates(["asin"])
        print(self.df.count())

    def save_to_db(self):
        self.df = (
            self.df.withColumnRenamed("brand", "author")
            .withColumnRenamed("price (USD)", "price")
            .select("asin", "author", "price", "title")
        )
        print("About to save")
        self.df.write.mode("append").format("jdbc").option(
            "url", "jdbc:postgresql://postgres:5432/book_reviews"
        ).option("driver", "org.postgresql.Driver").option(
            "dbtable", "book_metadata"
        ).option(
            "user", os.getenv("METADATA_DB_USER")
        ).option(
            "password", os.getenv("METADATA_DB_PWD")
        ).save()


def setup_spark_session():
    conf = (
        pyspark.SparkConf()
        .setMaster("local[*]")
        .set("spark.executor.heartbeatInterval", 100)
        .set("spark.network.timeout", 10000)
        .set("spark.core.connection.ack.wait.timeout", "3600")
        .set("spark.executor.memory", MAX_MEMORY)
        .set("spark.driver.maxResultSize", "2G")
        .set("spark.driver.extraClassPath", "/opt/spark/jars/postgresql-42.2.20.jar")
        .set("spark.executor.extraClassPath", "/opt/spark/jars/postgresql-42.2.20.jar")
    )

    spark = (
        SparkSession.builder.appName("Load Metadata").config(conf=conf).getOrCreate()
    )
    return spark


if __name__ == "__main__":
    spark = setup_spark_session()
    metadata_processor = MetadataProcessor(spark=spark)
    metadata_processor.load_metadata(os.getenv("METADATA_FILENAME"))
    metadata_processor.clean_metadata()
    metadata_processor.save_to_db()
