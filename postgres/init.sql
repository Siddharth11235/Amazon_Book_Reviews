CREATE TABLE book_metadata(
    asin VARCHAR (100) PRIMARY KEY,
    author VARCHAR (256),
    price FLOAT,
    title VARCHAR (1000)
    );

CREATE TABLE book_data_enriched(
    review_id SERIAL PRIMARY KEY,  -- auto-incrementing integer
    asin VARCHAR (100),
    author VARCHAR (256),
    price FLOAT,
    title VARCHAR (1000),
    review_date TIMESTAMP,
    rating INT,
    review_text TEXT,
    review_sentiment_score FLOAT,
    FOREIGN KEY (asin) REFERENCES book_metadata(asin)
);
