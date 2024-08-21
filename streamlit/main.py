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
        "Average Rating per Author",
        "Average Rating per Book",
        "Average Sentiment Score per Author",
        "Average Sentiment Score per Book",
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

    avg_rating_author_df = query_db(
        f"""
        SELECT author, avg_rating, rating_count
        FROM author_rating_aggregates
        ORDER BY rating_count DESC
        LIMIT 50;
    """
    )

    st.dataframe(avg_rating_author_df)

elif page == "Books with Most Ratings":
    st.header("Books with the Most Ratings")

    avg_rating_book_df = query_db(
        f"""
        SELECT title, avg_rating, rating_count
        FROM book_rating_aggregates
        ORDER BY rating_count DESC
        LIMIT 50;"""
    )
    st.dataframe(avg_rating_book_df)

# 2. average rating per author
elif page == "Average Rating per Author":
    st.header("Average Rating per Author")

    # search for author
    author_query = st.sidebar.text_input("Search for Author")

    if author_query:
        avg_rating_author_df = query_db(
            f"""
                select author, year, avg_rating
                from avg_rating_per_author_year
                where author ilike '%{author_query}%'
            """
        )

        if not avg_rating_author_df.empty:
            st.subheader(f"Average Rating per year for {author_query}")
            st.plotly_chart(
                px.line(
                    avg_rating_author_df,
                    x="year",
                    y="avg_rating",
                    title="Average Rating per Author",
                    markers=True,
                )
            )
        else:
            st.subheader(f"Average Rating per year for {author_query}")
            st.write("No authors found matching your search criteria.")
    else:
        st.write("Please enter an author name to search.")

# 3. average rating per book
elif page == "Average Rating per Book":
    st.header("Average Rating per Book")

    # search for book
    book_query = st.sidebar.text_input("Search for Book")

    if book_query:
        st.subheader(f"Average Rating per year for {book_query}")
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
                avg_rating_book_df = query_db(
                    f"""
                    select title, year, avg_rating
                    from avg_rating_per_book_year
                    where title = '{title}'
                """
                )
                st.plotly_chart(
                    px.line(
                        avg_rating_book_df,
                        x="year",
                        y="avg_rating",
                        title=f"Average Rating per Book: {title}",
                        markers=True,
                    )
                )
        else:
            st.write("No books found matching your search criteria.")
    else:
        st.write("Please enter a book title to search.")

# 4. average review sentiment score per author
elif page == "Average Sentiment Score per Author":
    st.header("Average Sentiment Score per Author")
    # search for author
    author_query = st.sidebar.text_input("Search for Author")

    if author_query:
        avg_rating_author_df = query_db(
            f"""
                select author, year, avg_sentiment
                from avg_sentiment_per_author_year
                where author ilike '%{author_query}%'
            """
        )

        if not avg_rating_author_df.empty:
            st.subheader(f"Average Sentiment Score per year for {author_query}")
            st.plotly_chart(
                px.line(
                    avg_rating_author_df,
                    x="year",
                    y="avg_sentiment",
                    title="Average Sentiment Score per Author",
                    markers=True,
                )
            )
        else:
            st.subheader(f"Average Sentiment Score per year for {author_query}")
            st.write("No authors found matching your search criteria.")
    else:
        st.write("Please enter an author name to search.")


# 5. average review sentiment score per book
elif page == "Average Sentiment Score per Book":
    st.header("Average Sentiment Score per Book")

    # search for book
    book_query = st.sidebar.text_input("Search for Book")

    if book_query:
        # get distinct titles matching the query
        titles_df = query_db(
            f"""
            select distinct title
            from avg_sentiment_per_book_year
            where title ilike '%{book_query}%'
        """
        )
        st.subheader(f"Average Sentiment Score per year for {book_query}")
        if not titles_df.empty:
            for title in titles_df["title"]:
                title = title.replace("'", "''")
                avg_rating_book_df = query_db(
                    f"""
                    select title, year, avg_sentiment
                    from avg_sentiment_per_book_year
                    where title = '{title}'
                """
                )
                st.plotly_chart(
                    px.line(
                        avg_rating_book_df,
                        x="year",
                        y="avg_rating",
                        title=f"Average Sentiment Score per Book: {title}",
                        markers=True,
                    )
                )
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
