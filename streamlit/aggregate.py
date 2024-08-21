import psycopg2
import re
from textblob import TextBlob
from psycopg2.extras import execute_values
import nltk

nltk.download("punkt_tab")
print("Downloaded punkt_tab")
nltk.download("averaged_perceptron_tagger_eng")
print("Downloaded averaged_perceptron_tagger_eng")


def extract_adjectives(text):
    blob = TextBlob(text)
    # Extract words that are tagged as adjectives (JJ)
    adjectives = [word for word, pos in blob.tags if pos == "JJ"]
    return " ".join(adjectives)


def create_aggregation_tables():
    conn = psycopg2.connect(
        host="postgres",
        port="5432",
        database="book_reviews",
        user="postgres",
        password="postgres",
    )
    cursor = conn.cursor()

    print("About to Execute")

    # Create average rating per author per year
    cursor.execute(
        """
        DROP TABLE IF EXISTS avg_rating_per_author_year;
        CREATE TABLE avg_rating_per_author_year AS
        SELECT
            author,
            EXTRACT(YEAR FROM review_date) as year,
            AVG(rating) as avg_rating
        FROM
            book_data_enriched
        GROUP BY
            author, year;
    """
    )

    conn.commit()
    cursor.close()

    print("average rating per author per year table done")
    # Create average rating per book per year
    cursor = conn.cursor()
    cursor.execute(
        """
        DROP TABLE IF EXISTS avg_rating_per_book_year;
        CREATE TABLE avg_rating_per_book_year AS
        SELECT
            title,
            EXTRACT(YEAR FROM review_date) as year,
            AVG(rating) as avg_rating
        FROM
            book_data_enriched
        GROUP BY
            title, year;
    """
    )
    conn.commit()
    cursor.close()
    print("average rating per book per year table done")

    # Create average sentiment score per author per year
    cursor = conn.cursor()
    cursor.execute(
        """
        DROP TABLE IF EXISTS avg_sentiment_per_author_year;
        CREATE TABLE avg_sentiment_per_author_year AS
        SELECT
            author,
            EXTRACT(YEAR FROM review_date) as year,
            AVG(review_sentiment_score) as avg_sentiment
        FROM
            book_data_enriched
        GROUP BY
            author, year;
    """
    )

    conn.commit()
    cursor.close()
    print("average sentiment score per author per year table done")
    # Create average sentiment score per book per year
    cursor = conn.cursor()
    cursor.execute(
        """
        DROP TABLE IF EXISTS avg_sentiment_per_book_year;
        CREATE TABLE avg_sentiment_per_book_year AS
        SELECT
            title,
            EXTRACT(YEAR FROM review_date) as year,
            AVG(review_sentiment_score) as avg_sentiment
        FROM
            book_data_enriched
        GROUP BY
            title, year;
    """
    )

    print("average sentiment score per book per year table done")

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Aggregation tables created successfully.")


def create_wordcloud_tables():
    conn = psycopg2.connect(
        host="postgres",
        port="5432",
        database="book_reviews",
        user="postgres",
        password="postgres",
    )
    cursor = conn.cursor()

    # Create the word cloud table
    cursor.execute(
        """
        DROP TABLE IF EXISTS wordcloud_agg_data;
        CREATE TABLE wordcloud_data (
            author VARCHAR,
            title VARCHAR,
            year INTEGER,
            adjectives TEXT
        );
    """
    )

    # Process and aggregate the data in batches
    offset = 0
    batch_size = 100000  # Adjust batch size based on available memory
    aggregated_data = {}

    while True:
        cursor.execute(
            f"SELECT author, title, review_date, review_text FROM book_data_enriched LIMIT {batch_size} OFFSET {offset}"
        )
        rows = cursor.fetchall()

        if not rows:
            break

        for row in rows:
            author, title, review_date, review_text = row
            year = review_date.year
            key = (author, title, year)
            adjectives = extract_adjectives(review_text)

            if key in aggregated_data:
                aggregated_data[key] += " " + adjectives
            else:
                aggregated_data[key] = adjectives

        offset += batch_size
        print(f"Processed {offset} rows")

    # Prepare the aggregated data for insertion
    data_to_insert = [
        (author, title, year, adjectives)
        for (author, title, year), adjectives in aggregated_data.items()
    ]

    execute_values(
        cursor,
        """
        INSERT INTO wordcloud_data (author, title, year, adjectives)
        VALUES %s
    """,
        data_to_insert,
    )

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Word cloud table with aggregated adjectives created successfully.")


if __name__ == "__main__":
    # create_aggregation_tables()
    # create_wordcloud_tables()
    print("Done")
