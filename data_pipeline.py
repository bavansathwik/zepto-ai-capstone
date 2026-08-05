import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np
import sqlite3


BASE_URL = "https://books.toscrape.com/"
# Select any 3 categories
CATEGORIES = {
    "Travel": "catalogue/category/books/travel_2/index.html",
    "Mystery": "catalogue/category/books/mystery_3/index.html",
    "Historical Fiction": "catalogue/category/books/historical-fiction_4/index.html"
}
def get_soup(url):
    """
    Sends a GET request and returns BeautifulSoup object.
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to access {url}")
        return None
    return BeautifulSoup(response.text, "html.parser")

def scrape_category(category_name, category_url):
    """
    Scrape all books from a given category.
    """
    books = []
    next_page = BASE_URL + category_url
    while next_page:
        print(f"Scraping: {next_page}")
        soup = get_soup(next_page)
        if soup is None:
            break
        articles = soup.find_all("article", class_="product_pod")
        for article in articles:
            title = article.h3.a["title"]
            price = article.find("p", class_="price_color").text.strip()
            star_rating = article.find("p")["class"][1]
            availability = article.find(
                "p",
                class_="instock availability"
            ).text.strip()
            books.append({
                "title": title,
                "price": price,
                "star_rating": star_rating,
                "availability": availability,
                "category": category_name
            })

        # Check for next page
        next_btn = soup.find("li", class_="next")
        if next_btn:

            next_href = next_btn.a["href"]

            current_url = next_page.rsplit("/", 1)[0]

            next_page = current_url + "/" + next_href
        else:
            next_page = None
        time.sleep(1)
    return books

def scrape_books():
    all_books = []
    for category, link in CATEGORIES.items():
        books = scrape_category(category, link)
        all_books.extend(books)
    df = pd.DataFrame(all_books)
    print("\nTotal Books Scraped :", len(df))
    df.to_csv("raw_books.csv", index=False)
    print("Saved as raw_books.csv")
    return df
if __name__ == "__main__":
    scrape_books()







# Load Raw Data
df = pd.read_csv("raw_books.csv")
df["price_gbp"] = (
    df["price"]
    .str.replace(r"[^\d.]", "", regex=True)
)
df["price_gbp"] = pd.to_numeric(df["price_gbp"])
df["price_gbp"] = pd.to_numeric(df["price_gbp"], errors="coerce")
# Convert Rating
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}
df["rating"] = df["star_rating"].map(rating_map)
# Convert Availability
df["in_stock"] = (
    df["availability"]
    .str.lower()
    .str.contains("in stock")
)
# Handle Missing Values
# Numeric columns → Median Imputation
numeric_cols = ["price_gbp", "rating"]
for col in numeric_cols:
    median_value = df[col].median()
    df[col] = df[col].fillna(median_value)
df["in_stock"] = df["in_stock"].fillna(False)
# Remove Original Columns
df = df.drop(
    columns=["price", "star_rating", "availability"]
)
# Save Cleaned Dataset
df.to_csv("cleaned_books.csv", index=False)
print("Cleaning Completed Successfully")






GBP_TO_INR = 105.50
df["price_inr"] = (df["price_gbp"] * GBP_TO_INR).round(2)
df.to_csv("cleaned_books.csv", index=False)
print(df.head())






DATABASE_NAME = "books.db"

def create_database():
    """
    Creates the SQLite database and normalized tables.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Enable Foreign Key Support
    cursor.execute("PRAGMA foreign_keys = ON;")
    # Categories Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL
        );
    """)
    # Books Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            price_inr REAL NOT NULL,
            rating INTEGER NOT NULL,
            in_stock INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY(category_id)
                REFERENCES categories(category_id)
        );
    """)
    conn.commit()
    conn.close()

def load_data(csv_file="cleaned_books.csv"):
    """
    Reads cleaned CSV.
    """
    return pd.read_csv(csv_file)

def insert_data(df):
    """
    Inserts categories and books into the database.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Insert Categories
    categories = df["category"].unique()

    for category in categories:
        cursor.execute("""
            INSERT OR IGNORE INTO categories(category_name)
            VALUES (?);
        """, (category,))

    conn.commit()
    # Get Category IDs
    cursor.execute("""
        SELECT category_id, category_name
        FROM categories;
    """)
    category_map = {
        name: cid
        for cid, name in cursor.fetchall()
    }
    # Insert Books
    for _, row in df.iterrows():

        cursor.execute("""
            INSERT INTO books(
                title,
                price_gbp,
                price_inr,
                rating,
                in_stock,
                category_id
            )
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            row["title"],
            row["price_gbp"],
            row["price_inr"],
            int(row["rating"]),
            int(row["in_stock"]),
            category_map[row["category"]]
        ))
    conn.commit()
    conn.close()
def main():
    create_database()
    df = load_data()
    insert_data(df)
    print("Database Created Successfully!")
    print("Data Inserted Successfully!")
if __name__ == "__main__":
    main()





DATABASE = "books.db"

conn = sqlite3.connect(DATABASE)
# Query 1
# SELECT + WHERE
query1 = """
SELECT title, price_gbp
FROM books
WHERE rating >= 4;
"""

print("\n========== QUERY 1 ==========")
print(query1)
print(pd.read_sql(query1, conn))
# Query 2
# ORDER BY + LIMIT
query2 = """
SELECT title, price_gbp
FROM books
ORDER BY price_gbp DESC
LIMIT 10;
"""

print("\n========== QUERY 2 ==========")
print(query2)
print(pd.read_sql(query2, conn))
# Query 3
# DISTINCT
query3 = """
SELECT DISTINCT category_name
FROM categories;
"""

print("\n========== QUERY 3 ==========")
print(query3)
print(pd.read_sql(query3, conn))
# Query 4
# BETWEEN
query4 = """
SELECT title, price_gbp
FROM books
WHERE price_gbp BETWEEN 20 AND 40;
"""
print("\n========== QUERY 4 ==========")
print(query4)
print(pd.read_sql(query4, conn))

# Query 5
# JOIN
query5 = """
SELECT
    b.title,
    c.category_name,
    b.rating,
    b.price_gbp
FROM books b
JOIN categories c
ON b.category_id = c.category_id
ORDER BY b.rating DESC
LIMIT 10;
"""

print("\n========== QUERY 5 ==========")
print(query5)
print(pd.read_sql(query5, conn))
conn.close()






# Connect to Database
conn = sqlite3.connect("books.db")

# PART 1: Read SQL Query Results into Pandas

# Query 1
query1 = """
SELECT title, price_gbp, rating
FROM books
WHERE rating >= 4;
"""

df_query1 = pd.read_sql(query1, conn)

print("\n===== SQL Query 1 Result =====")
print(df_query1)

# Query 2
query2 = """
SELECT title, price_gbp
FROM books
ORDER BY price_gbp DESC
LIMIT 10;
"""

df_query2 = pd.read_sql(query2, conn)

print("\n===== SQL Query 2 Result =====")
print(df_query2)
# PART 2: SQL JOIN
join_query = """
SELECT
    b.title,
    c.category_name,
    b.rating,
    b.price_gbp
FROM books b
JOIN categories c
ON b.category_id = c.category_id
ORDER BY b.title;
"""

sql_join = pd.read_sql(join_query, conn)

print("\n===== SQL JOIN Result =====")
print(sql_join)
# PART 3: Pandas Merge (No SQL JOIN)

books_df = pd.read_sql("SELECT * FROM books;", conn)
categories_df = pd.read_sql("SELECT * FROM categories;", conn)

merge_result = pd.merge(
    books_df,
    categories_df,
    on="category_id",
    how="inner"
)

merge_result = merge_result[
    ["title", "category_name", "rating", "price_gbp"]
].sort_values("title").reset_index(drop=True)

print("\n===== Pandas Merge Result =====")
print(merge_result)
# PART 4: Verify Equality

sql_join = sql_join.reset_index(drop=True)

print("\nAre both outputs identical?")
print(sql_join.equals(merge_result))
conn.close()