import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt


# function to query the database
def query_db(query):
    conn = psycopg2.connect(
        host="postgres",
        port="5432",
        database="book_reviews",
        user="postgres",
        password="postgres",
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# navigation menu
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Home",
        "Authors with Most Ratings",
        "Books with Most Ratings",
        "Average Rating and Sentiment Score per Author",
        "Average Rating and Sentiment Score per Book",
        "Word Clouds for Authors",
        "Word Clouds for Books",
    ],
)

# home page content
if page == "Home":
    st.title("Book Reviews Dashboard")
    st.write(
        "Welcome to the Amazon Book Reviews Dashboard. This dashboard gives you access to a few interesting analyses."
    )

elif page == "Authors with Most Ratings":
    st.header("Authors with Most Ratings")

    num_authors = st.sidebar.slider(
        "Number of Authors to Display", min_value=1, max_value=500, value=250
    )

    avg_rating_author_df = query_db(
        f"""
        SELECT author, avg_rating, rating_count
        FROM author_rating_aggregates
        ORDER BY rating_count DESC
        LIMIT {num_authors};
    """
    )
    st.dataframe(avg_rating_author_df, use_container_width=True)

elif page == "Books with Most Ratings":
    st.header("Books with the Most Ratings")
    num_books = st.sidebar.slider(
        "Number of Books to Display", min_value=1, max_value=500, value=250
    )

    avg_rating_book_df = query_db(
        f"""
        SELECT title, avg_rating, rating_count
        FROM book_rating_aggregates
        ORDER BY rating_count DESC
        LIMIT {num_books};"""
    )
    st.dataframe(avg_rating_book_df, use_container_width=True)

# 2. average rating per author
# 1. average rating and sentiment score per author
elif page == "Average Rating and Sentiment Score per Author":
    st.header("Average Rating and Sentiment Score per Author")

    # search for author
    author_query = st.sidebar.text_input("Search for Author")

    if author_query:
        # Fetch average rating data
        avg_rating_author_df = query_db(
            f"""
                select author, year, avg_rating
                from avg_rating_per_author_year
                where author ilike '%{author_query}%'
            """
        )

        # Fetch average sentiment score data
        avg_sentiment_author_df = query_db(
            f"""
                select author, year, avg_sentiment
                from avg_sentiment_per_author_year
                where author ilike '%{author_query}%'
            """
        )

        if not avg_rating_author_df.empty and not avg_sentiment_author_df.empty:
            st.subheader(
                f"Average Rating and Sentiment Score per year for {author_query}"
            )
            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(
                    px.line(
                        avg_rating_author_df,
                        x="year",
                        y="avg_rating",
                        title="Average Rating per Author",
                        labels={"year": "Year", "avg_rating": "Average Rating"},
                        markers=True,
                    )
                )

            with col2:
                st.plotly_chart(
                    px.line(
                        avg_sentiment_author_df,
                        x="year",
                        y="avg_sentiment",
                        title="Average Sentiment Score per Author",
                        labels={
                            "year": "Year",
                            "avg_sentiment": "Average Sentiment Score",
                        },
                        markers=True,
                    )
                )
        else:
            st.write("No data found for the selected author.")
    else:
        st.write("Please enter an author name to search.")

# 2. average rating and sentiment score per book
elif page == "Average Rating and Sentiment Score per Book":
    st.header("Average Rating and Sentiment Score per Book")

    # search for book
    book_query = st.sidebar.text_input("Search for Book")

    if book_query:
        st.subheader(f"Average Rating and Sentiment Score per year for {book_query}")
        # get distinct titles matching the query
        titles_df = query_db(
            f"""
            select distinct title
            from avg_rating_per_book_year
            where title ilike '%{book_query}%'
        """
        )

        if not titles_df.empty:
            for title in titles_df["title"]:
                title = title.replace("'", "''")

                # Fetch average rating data
                avg_rating_book_df = query_db(
                    f"""
                    select title, year, avg_rating
                    from avg_rating_per_book_year
                    where title = '{title}'
                """
                )

                # Fetch average sentiment score data
                avg_sentiment_book_df = query_db(
                    f"""
                    select title, year, avg_sentiment
                    from avg_sentiment_per_book_year
                    where title = '{title}'
                """
                )

                if not avg_rating_book_df.empty and not avg_sentiment_book_df.empty:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.plotly_chart(
                            px.line(
                                avg_rating_book_df,
                                x="year",
                                y="avg_rating",
                                title=f"Average Rating per Book: {title}",
                                labels={"year": "Year", "avg_rating": "Average Rating"},
                                markers=True,
                            )
                        )

                    with col2:
                        st.plotly_chart(
                            px.line(
                                avg_sentiment_book_df,
                                x="year",
                                y="avg_sentiment",
                                title=f"Average Sentiment Score per Book: {title}",
                                labels={
                                    "year": "Year",
                                    "avg_sentiment": "Average Sentiment Score",
                                },
                                markers=True,
                            )
                        )
                else:
                    st.write(f"No data found for the book: {title}")

        else:
            st.write("No books found matching your search criteria.")
    else:
        st.write("Please enter a book title to search.")

elif page == "Word Clouds for Authors":
    st.header("Word Clouds for Authors")

    # search for author
    author_query = st.sidebar.text_input("Search for Author")

    if author_query:
        adjectives_df = query_db(
            f"SELECT aggregated_adjectives as adjectives FROM wordcloud_data_author_year WHERE author ILIKE '%{author_query}%'"
        )
    else:
        adjectives_df = pd.DataFrame()  # empty dataframe if no selection

    if not adjectives_df.empty:
        st.subheader(f"Word Clouds for {author_query}")
        # Combine all adjectives into a single string
        all_adjectives = " ".join(adjectives_df["adjectives"])

        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400).generate(all_adjectives)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        st.pyplot(plt)

    else:
        st.write(f"No adjectives found for {author_query}.")

# 4. word cloud for reviews
elif page == "Word Clouds for Books":
    st.header("Word Clouds for Books")

    # search for book
    book_query = st.sidebar.text_input("Search for Book")

    if book_query:
        adjectives_df = query_db(
            f"SELECT aggregated_adjectives as adjectives FROM wordcloud_data_book_year WHERE title ILIKE '%{book_query}%'"
        )
    else:
        adjectives_df = pd.DataFrame()  # empty dataframe if no selection

    if not adjectives_df.empty:
        st.subheader(f"Word Clouds for {book_query}")
        # Combine all adjectives into a single string
        all_adjectives = " ".join(adjectives_df["adjectives"])

        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400).generate(all_adjectives)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        st.pyplot(plt)

    else:
        st.write(f"No adjectives found for {book_query}.")
