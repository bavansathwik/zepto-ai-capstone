# Zepto Data & AI Platform — Data Pipeline
## 1. Overview
The `data_pipeline` module is an end-to-end data engineering pipeline that extracts book data from the public [Books to Scrape](https://books.toscrape.com/) website, cleans and transforms the scraped data, converts prices from GBP to INR using the project-defined fixed exchange rate, stores the data in a normalized SQLite database, executes SQL queries, and verifies database results using Pandas.
The pipeline follows this flow:
Books to Scrape
       │
       ▼
   Scraping
       │
       ▼
 Raw CSV Data
       │
       ▼
 Data Cleaning
       │
       ▼
Currency Conversion
       │
       ▼
 Cleaned CSV
       │
       ▼
 SQLite Database
       │
       ▼
    SQL Queries
       │
       ▼
 Pandas Verification
```
---
## 2. Technologies Used
The following Python libraries and tools are used:
* Python
* `requests`
* `BeautifulSoup`
* `pandas`
* `sqlite3`
`sqlite3` is part of Python's standard library, so it does not require a separate installation.
---
# 3. Step 1 — Web Scraping
## Objective
The first stage extracts book information from the Books to Scrape website.
The scraper uses the `requests` library to retrieve web pages and `BeautifulSoup` to parse the HTML content.
The project scrapes books from at least three different categories and collects the following fields:
* `title`
* `price`
* `star_rating`
* `availability`
* `category`
The raw price and rating are intentionally retained in their original text form during this stage because cleaning and type conversion are performed in the next stage.
### Scraped fields
| Field          | Description                                              |
| -------------- | -------------------------------------------------------- |
| `title`        | Book title                                               |
| `price`        | Price as listed on the website, including the GBP symbol |
| `star_rating`  | Rating as text such as One, Two, Three, Four, or Five    |
| `availability` | Availability text as displayed on the website            |
| `category`     | Category to which the book belongs                       |
The scraped records are saved to:
```text
raw_books.csv
```
### Scraping approach
The scraper checks the HTTP response before attempting to parse the page. If a page cannot be accessed successfully, the pipeline handles the failure without immediately crashing.
A short delay between requests is used to avoid sending requests too rapidly.
---
# 4. Step 2 — Data Cleaning
The raw scraped fields contain text representations of values that are required to be converted into appropriate data types.
The following transformations are performed.
## Price Cleaning
The original price field contains values such as:
```text
£51.77
```
The currency symbol and any unexpected non-numeric characters are removed, and the value is converted to a floating-point number.
The resulting column is:
```text
price_gbp
```
For example:
```text
£51.77 → 51.77
```
The conversion uses Pandas numeric parsing with error handling so unexpected values do not crash the pipeline.
## Rating Conversion
The website provides star ratings as text.
For example:
```text
One
Two
Three
Four
Five
```
These values are converted into integers:
| Text  | Integer |
| ----- | ------: |
| One   |       1 |
| Two   |       2 |
| Three |       3 |
| Four  |       4 |
| Five  |       5 |
The resulting column is:
```text
rating
```
## Availability Conversion
The availability text is converted into a Boolean column:
```text
in_stock
```
For example:
text
In stock → True

If the availability text does not contain the expected stock information, the parsing logic handles it without causing the entire pipeline to fail.
## Handling Parsing Errors
Numeric parsing errors are converted to missing values using Pandas' error-coercion mechanism.
For numeric columns such as `price_gbp` and `rating`, missing values resulting from parsing errors are handled using **median imputation**.
Median imputation was selected because it:
* Preserves the scraped record.
* Prevents a single malformed value from stopping the pipeline.
* Is less sensitive to extreme values than mean imputation.
* Satisfies the project's requirement for handling failed numeric parsing.
The cleaned dataset is saved as:
```text
cleaned_books.csv
```
---
# 5. Step 3 — GBP to INR Conversion
The project requires a fixed conversion rate rather than a live currency API.
The exact project-defined conversion rate is:
```text
1 GBP = 105.50 INR
```
This is an artificial baseline specified by the assignment.
No external API or network request is required for this conversion.
The conversion is performed using:
```text
price_inr = price_gbp × 105.50
```
The resulting column is:
```text
price_inr
```
Both `price_gbp` and `price_inr` are retained because the database schema requires both values.
For example:
```text
price_gbp = 10.00
price_inr = 10.00 × 105.50
          = 1055.00
```
The INR values are rounded to two decimal places.
---
# 6. Step 4 — Normalized SQLite Schema
The cleaned and converted data is stored in a SQLite database named:
```text
books.db
```
A normalized two-table schema is used.
## Categories Table
```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL
);
```
The `categories` table stores each category only once.
## Books Table
```sql
CREATE TABLE books (
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
```
## Relationship
The relationship between the tables is:
```text
categories
-----------------
category_id (PK)
category_name

       │
       │ 1
       │
       │
       │ many
       ▼

books
-----------------
book_id (PK)
title
price_gbp
price_inr
rating
in_stock
category_id (FK)
```
A category can contain multiple books, while each book belongs to one category.
The `category_id` in the `books` table is a foreign key referencing `categories.category_id`.
This normalization avoids repeatedly storing the same category name for every book and provides referential integrity.
Foreign-key support is explicitly enabled in SQLite using:
```sql
PRAGMA foreign_keys = ON;
```
---
# 7. Data Insertion
The cleaned dataset is read from:
```text
cleaned_books.csv
```
Categories are inserted into the `categories` table first.
The corresponding `category_id` values are then obtained and used when inserting books into the `books` table.
This ensures that every book references a valid category.
The database can be created and populated by running:
```bash
python database.py
```
Expected terminal output:
```text
Database Created Successfully!
Data Inserted Successfully!
```
---
# 8. Step 5 — SQL Queries
At least five SQL queries are executed against the SQLite database.
The queries collectively demonstrate:
* `SELECT`
* `WHERE`
* `ORDER BY`
* `LIMIT`
* `DISTINCT`
* `BETWEEN`
* `JOIN`
## Query 1 — SELECT and WHERE
This query finds books with a rating of at least four stars.
```sql
SELECT title, price_gbp
FROM books
WHERE rating >= 4;
```
This demonstrates:
```text
SELECT
WHERE
```
---
## Query 2 — ORDER BY and LIMIT
This query retrieves the ten most expensive books.
```sql
SELECT title, price_gbp
FROM books
ORDER BY price_gbp DESC
LIMIT 10;
```
This demonstrates:
```text
ORDER BY
LIMIT
```
---
## Query 3 — DISTINCT
This query returns the unique categories stored in the database.
```sql
SELECT DISTINCT category_name
FROM categories;
```
This demonstrates:
```text
DISTINCT
```
---
## Query 4 — BETWEEN
This query finds books whose GBP price is between £20 and £40.
```sql
SELECT title, price_gbp
FROM books
WHERE price_gbp BETWEEN 20 AND 40;
```
This demonstrates:
```text
BETWEEN
```
---
## Query 5 — JOIN
This query combines the `books` and `categories` tables using their primary/foreign-key relationship.
```sql
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
```
This demonstrates:
```text
JOIN
ORDER BY
LIMIT
```
The query returns the top ten highest-rated books along with their category names.
---
# 9. Saving Query Strings and Outputs
Each SQL query is stored as a Python string variable.
For example:
```python
query1 = """
SELECT title, price_gbp
FROM books
WHERE rating >= 4;
"""
```
The variable `query1` is a Python string containing the SQL statement.
The query is executed using:
python
pd.read_sql(query1, conn)
The query string and its resulting DataFrame are printed so that both the SQL statement and its output can be inspected.
The project does not require separate CSV files for each query result.
---
# 10. Step 6 — Pandas Verification
The final stage verifies that database operations can also be reproduced using Pandas.
At least two SQL query results are read into Pandas DataFrames using:
```python
pd.read_sql(...)
```
For example:
```python
df_query1 = pd.read_sql(query1, conn)
df_query2 = pd.read_sql(query2, conn)
```
---
# 11. SQL JOIN vs Pandas Merge
The JOIN query is first executed directly in SQLite.
```python
sql_join = pd.read_sql(join_query, conn)
```
The two database tables are then independently loaded into Pandas:
```python
books_df = pd.read_sql("SELECT * FROM books;", conn)
categories_df = pd.read_sql(
    "SELECT * FROM categories;",
    conn
)
```
The same relationship is reproduced using `pd.merge()`:
```python
merge_result = pd.merge(
    books_df,
    categories_df,
    on="category_id",
    how="inner"
)
```
No SQL JOIN is used for this Pandas operation.
The columns are then selected and both outputs are sorted consistently before comparison.
```python
sql_join = (
    sql_join
    .sort_values("title")
    .reset_index(drop=True)
)
merge_result = (
    merge_result[
        ["title", "category_name", "rating", "price_gbp"]
    ]
    .sort_values("title")
    .reset_index(drop=True)
)
```
The results are compared using:
```python
sql_join.equals(merge_result)
```
Expected result:
```text
True
```
A result of `True` confirms that the SQL JOIN and the equivalent Pandas merge produced the same data.
Sorting and resetting the index before comparison ensures that the comparison is not affected by differences in row ordering or index values.
---
# 12. Files in This Module
The `data_pipeline` directory contains the following main files:
```text
### `scraper.py`
Extracts book information from the Books to Scrape website and creates the raw dataset.
### `preprocess.py`
Cleans the scraped fields, converts prices and ratings to appropriate types, handles parsing errors, and performs the GBP-to-INR conversion.
### `database.py`
Creates the normalized SQLite schema and inserts the cleaned data.
### `queries.py`
Executes the required SQL queries demonstrating filtering, sorting, limiting, distinct values, range filtering, and table joins.
### `verification.py`
Reads SQL results into Pandas and verifies the SQL JOIN against an equivalent `pd.merge()` operation.
### `raw_books.csv`
Contains the original scraped values before cleaning.
### `cleaned_books.csv`
Contains the cleaned and converted dataset.
### `books.db`
SQLite database containing the normalized `categories` and `books` tables.
---
# 13. How to Run the Pipeline
Open a terminal inside the `data_pipeline` directory.
## Install dependencies
```bash
pip install requests beautifulsoup4 pandas
```
## Run the scraper
```bash
python scraper.py
```
This creates:
```text
raw_books.csv
```
## Run preprocessing
```bash
python preprocess.py
```
This creates:
```text
cleaned_books.csv
```
## Create and populate the database
```bash
python database.py
```
This creates:
```text
books.db
```
## Execute SQL queries
```bash
python queries.py
```
This executes the five required SQL queries and displays their query strings and outputs.
## Run verification
```bash
python verification.py
```
This reads SQL results into Pandas, reproduces the JOIN using `pd.merge()`, and checks whether both approaches produce equivalent output.
Expected final verification:
```text
Are both outputs identical?
True
```
---
# 14. Design Decisions
### Web Scraping
`requests` and `BeautifulSoup` were selected because they are lightweight and directly satisfy the project requirements. The scraper checks HTTP responses before parsing pages.
### Data Cleaning
Raw website values are converted into appropriate numerical and Boolean representations. Numeric parsing failures are handled through median imputation rather than allowing malformed rows to crash the pipeline.
### Currency Conversion
The project-defined fixed rate of **1 GBP = 105.50 INR** is used. No external currency API is required because the assignment explicitly defines this rate as the grading baseline.
### Database Design
The database uses two normalized tables instead of repeatedly storing category names in every book record. A primary/foreign-key relationship connects books to categories.
### SQL Analysis
Five queries were selected to collectively demonstrate all required SQL operations while also providing useful information about the scraped books.
### Pandas Verification
Pandas is used to independently reproduce database operations and verify that the SQL JOIN and Pandas merge produce equivalent results.
---
# 15. Final Outcome
The completed data pipeline provides an end-to-end workflow:
```text
Extract
  ↓
Transform
  ↓
Load
  ↓
Query
  ↓
Verify
```
The pipeline starts with raw web data and ends with a cleaned, converted, normalized relational dataset that can be queried using SQL and independently verified using Pandas.
This module therefore provides a structured data foundation for the wider Zepto Data & AI Platform capstone project.





# Analytics Module — Titanic Data Science Workflow
## Overview
This module implements a complete analyst-to-data-scientist workflow using the classic Titanic dataset. The workflow starts with dataset profiling and data cleaning, continues through exploratory data analysis and visualization, and then builds, evaluates, tunes, and saves machine-learning models.
The entire workflow is implemented in a single Python script:
```text
analytics/
├── analytics.py
├── titanic.csv
├── best_random_forest_pipeline.pkl
└── README.md
```
The Titanic dataset is loaded from Seaborn using `sns.load_dataset("titanic")` exactly once. Immediately after loading, the raw dataset is saved as `titanic.csv` so that the project can still be graded offline using `pd.read_csv("titanic.csv")`.
The later analysis and modeling stages continue from the same cleaned dataset.
---
# Task 1 — Dataset Loading and Profiling
The Titanic dataset was loaded using Seaborn's built-in dataset loader:
```python
df = sns.load_dataset("titanic")
```
This is the only call to `sns.load_dataset("titanic")` in the project.
Immediately after loading, the dataset was saved as an offline fallback:
```python
df.to_csv("titanic.csv", index=False)
```
The dataset was then profiled using:
```python
df.info()
df.describe()
df.shape
```
Missing-value percentages were calculated for every column containing missing values using:
```python
missing_percentage = (df.isnull().sum() / len(df)) * 100
```
Only columns with a missing percentage greater than zero were reported.
The saved `titanic.csv` provides an offline copy of the raw dataset for grading and later processing.
---
# Task 2 — Missing-Value Handling
Missing values were handled according to the required threshold:
* Less than 5% missing → drop rows containing missing values.
* 5%–30% missing → impute missing values.
* More than 30% missing → explicitly decide whether to drop the column or treat missingness as its own category.
The affected Titanic columns were:
| Column        | Approx. Missing Rate | Strategy           |
| ------------- | -------------------: | ------------------ |
| `age`         |               19.87% | Median imputation  |
| `embarked`    |                0.22% | Drop affected rows |
| `embark_town` |                0.22% | Drop affected rows |
| `deck`        |               77.22% | Drop column        |
### `age`
Approximately 19.87% of `age` values were missing. This falls within the 5%–30% range, so the missing values were imputed using the median.
```python
df["age"] = df["age"].fillna(df["age"].median())
```
The median was selected because it is less sensitive to extreme values than the mean.
### `embarked` and `embark_town`
Both columns had less than 5% missing values, so rows containing missing values were removed.
```python
df = df.dropna(subset=["embarked", "embark_town"])
```
### `deck`
Approximately 77.22% of the `deck` values were missing. Because such a large proportion of the column was unavailable, imputing the values would be unreliable and could introduce artificial information. Therefore, the column was dropped.
```python
df = df.drop(columns=["deck"])
```
The cleaned dataset was then used for the remainder of the analysis.
---
# Task 3 — Univariate Analysis
Univariate analysis was performed on `age` and `fare`.
For each variable, both a histogram and a box plot were produced.
### Age
The age histogram shows the distribution of passenger ages, while the box plot highlights possible extreme values.
### Fare
The fare histogram shows that most passengers paid relatively low fares, while a smaller number of passengers paid substantially higher fares.
The box plot makes these high-fare observations visible as potential outliers.
## IQR Outlier Detection
Outliers were identified using the IQR rule:
```text
Lower Bound = Q1 − 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
```
The number of outliers was calculated separately for `age` and `fare`.
The analysis produced:
```text
Age Outliers: 65
```
The exact fare outlier count is generated directly by the script from the cleaned dataset.
## Fare Statistics
The mean, median, and mode of `fare` were calculated.
The fare distribution is interpreted using the ordering of these three statistics. A right-skewed distribution is indicated when:
```text
Mean > Median > Mode
```
The Titanic fare distribution is right-skewed because a relatively small number of passengers paid much higher fares than the majority.
---
# Task 4 — Bivariate Analysis
Survival rates were analyzed using boolean masking.
## Survival by Sex
Survival rates were calculated separately for male and female passengers.
The analysis shows that female passengers had a substantially higher survival rate than male passengers.
## Survival by Passenger Class
Survival rates were calculated for first-, second-, and third-class passengers.
First-class passengers had the highest survival rate, while third-class passengers had the lowest.
## Survival by Sex and Passenger Class
Combined boolean conditions using `&` were used to calculate survival rates for each sex/class combination.
For example:
```python
mask = (df["sex"] == sex) & (df["pclass"] == pclass)
```
This demonstrated how survival varied jointly with sex and passenger class.
## Correlation Matrix
A correlation matrix was calculated using exactly these six columns:
```python
[
    "survived",
    "pclass",
    "age",
    "sibsp",
    "parch",
    "fare"
]
```
The boolean columns `adult_male` and `alone` were excluded because they are derived/redundant flags rather than independent measured features.
The resulting 6×6 correlation matrix was displayed using:
```python
sns.heatmap()
```
The two strongest correlations were identified by ranking all off-diagonal feature pairs by the absolute value of their correlation coefficient.
A strong negative relationship exists between `pclass` and `fare`, reflecting the fact that lower-numbered passenger classes generally paid higher fares.
The relationship between `survived` and `pclass` is also negative, indicating that passengers in higher-numbered classes had lower survival rates.
---
# Task 5 — Multivariate Data Story
Four distinct charts were produced to create a coherent explanation of Titanic survival patterns.
## 1. Survival Rate by Sex
The chart shows a substantially higher survival rate among female passengers.
This indicates that sex was an important factor associated with survival.
## 2. Survival Rate by Passenger Class
First-class passengers had the highest survival rate, while third-class passengers had the lowest.
This suggests that passenger class was strongly associated with survival.
## 3. Age Distribution by Survival
A box plot was used to compare age distributions between survivors and non-survivors.
The distributions overlap, but age also appears to have some relationship with survival, particularly for younger passengers.
## 4. Fare vs Age by Survival
A scatter plot was used to examine age and fare together while distinguishing survival status.
Passengers paying higher fares generally had better survival outcomes, linking fare and passenger class to survival.
### Overall Data Story
Together, the charts suggest that survival was strongly associated with sex and passenger class. Female passengers and passengers from higher classes were more likely to survive. Age also had some influence, while fare provides another indication of the socioeconomic differences represented by passenger class.
---
# Task 6 — EDA Standardization Check
As an exploratory sanity check, `age` and `fare` were standardized using z-score normalization:
```text
z = (x − mean) / standard deviation
```
A copy of the cleaned DataFrame was used so that the original modeling data was not modified.
```python
eda_df = df.copy()
```
`StandardScaler` was then used:
```python
scaler = StandardScaler()
eda_df[["age_z", "fare_z"]] = scaler.fit_transform(
    eda_df[["age", "fare"]]
)
```
The transformed variables were checked to confirm that their means were approximately zero and their standard deviations were approximately one.
This was strictly an EDA-stage sanity check.
The standardized columns were **not used in the classification modeling pipeline**. The modeling pipeline performs its own train-only scaling later to prevent data leakage.
---
# Task 7 — Stratified Train/Test Split
The classification target was:
python
y = df["survived"]
The data was split into training and testing sets using a stratified 80/20 split:
```python
train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)
```
The resulting split was:
```text
Training Features : (711, 13)
Testing Features  : (178, 13)
Training Labels   : (711,)
Testing Labels    : (178,)
```
Stratification was used because the Titanic dataset is not perfectly balanced: the number of passengers who did not survive is greater than the number who survived.
Stratification preserves approximately the same class proportions in both training and testing datasets. This ensures that both sets are representative of the original class distribution and provides a more reliable evaluation of model performance.
---
# Task 8 — Training-Only Preprocessing
The classification preprocessing pipeline was designed to prevent data leakage.
The modeling features included:
```text
pclass
sex
age
sibsp
parch
fare
embarked
```
Numerical features:
```python
[
    "pclass",
    "age",
    "sibsp",
    "parch",
    "fare"
]
```
Categorical features:
```python
[
    "sex",
    "embarked"
]
```
## Numerical preprocessing
Missing numerical values were imputed using the median:
```python
SimpleImputer(strategy="median")
```
Numerical features were then standardized:
```python
StandardScaler()
```
## Categorical preprocessing
Missing categorical values were replaced with the most frequent category:
```python
SimpleImputer(strategy="most_frequent")
```
`sex` and `embarked` were then one-hot encoded:
```python
OneHotEncoder(handle_unknown="ignore")
```
A `ColumnTransformer` and `Pipeline` were used so that preprocessing was fitted only on the training split.
The training data uses:
```python
fit_transform()
```
while the test data uses:
```python
transform()
```
The test data was never used to fit an imputer, encoder, or scaler.
This prevents test-set information from leaking into model training.
---
# Task 9 — Classification Models
Three classifiers were trained on the same train/test split:
1. Logistic Regression
2. Decision Tree
3. Random Forest
Each classifier was combined with the preprocessing `ColumnTransformer` inside a scikit-learn `Pipeline`.
This ensured that the same train-only preprocessing procedure was applied consistently to all three models.
The Decision Tree was also visualized using `plot_tree()` with feature names and class names.
---
# Task 10 — Model Evaluation
All three classifiers were evaluated using:
* Accuracy
* Precision
* Recall
* F1 Score
* ROC Curve
* AUC
* Confusion Matrix
The classification results were:
| Model               | Accuracy | Precision | Recall | F1 Score |   AUC |
| ------------------- | -------: | --------: | -----: | -------: | ----: |
| Logistic Regression |    0.809 |     0.783 |  0.691 |    0.734 | 0.861 |
| Decision Tree       |    0.770 |     0.690 |  0.721 |    0.705 | 0.754 |
| Random Forest       |    0.820 |     0.781 |  0.735 |    0.758 | 0.818 |
### Interpretation
Random Forest achieved the highest accuracy and F1 score among the three models.
Logistic Regression achieved the highest AUC, indicating strong overall discrimination between survivors and non-survivors across classification thresholds.
Decision Tree had the weakest overall performance among the three models.
---
# Task 11 — Class Imbalance Handling
The survival target is moderately imbalanced, with non-survivors forming the majority class and survivors forming the minority class.
One classifier, Logistic Regression, was compared under three imbalance strategies:
1. Baseline with no imbalance handling.
2. `class_weight="balanced"`.
3. SMOTE oversampling.
SMOTE was applied **only to the training data**.
The test data was never oversampled.
This is important because applying SMOTE before the train/test split would allow information derived from the test distribution to influence training and would therefore create data leakage.
Precision, recall, and F1 score were compared across the three approaches.
The strategy with the strongest F1 score was considered the best balance between precision and recall for the experiment.
---
# Task 12 — Random Forest Hyperparameter Tuning
The Random Forest classifier was tuned using `GridSearchCV`.
The following parameters were searched:
```python
n_estimators
max_depth
max_features
```
The estimator was explicitly constructed with:
```python
RandomForestClassifier(
    random_state=42,
    bootstrap=True,
    oob_score=True
)
```
This was necessary because the task requires an Out-of-Bag score.
The grid search used 5-fold cross-validation and optimized classification accuracy.
The best parameter combination was reported using:
```python
grid_search.best_params_
```
The fitted Random Forest estimator was extracted from:
```python
grid_search.best_estimator_
```
and its OOB score was reported using:
```python
best_rf.oob_score_
```
The OOB score provides an additional estimate of Random Forest performance using samples that were not selected in each bootstrap training sample.
---
# Task 13 — Regression Side Task
A separate regression task was performed using the same cleaned Titanic dataset.
The target variable was:
```text
fare
```
The regression model attempted to predict fare from the other available passenger features.
A multivariate Linear Regression model was used with preprocessing for numerical and categorical features.
The model was evaluated using:
* MAE
* RMSE
* R²
* Adjusted R²
## Metrics
The values produced by the script are printed during execution:
```text
MAE         : ...
RMSE        : ...
R²          : ...
Adjusted R² : ...
```
### Metric meanings
**MAE** measures the average absolute prediction error.
**RMSE** measures prediction error while giving greater weight to larger errors.
**R²** measures the proportion of variation in the target explained by the model.
**Adjusted R²** adjusts R² for the number of predictors used by the regression model.
## Residual Analysis
A residual plot was produced by plotting:
```text
Predicted Fare vs Residuals
```
Residuals were calculated as:
```python
residuals = y_test_reg - y_pred
```
A random cloud of residuals around zero with approximately constant spread would indicate little evidence of heteroscedasticity.
A funnel-shaped or systematic residual pattern would indicate heteroscedasticity.
The residual plot was inspected to determine whether the residual spread changed with the predicted fare values.
---
# Task 14 — Final Model Comparison and Recommendation
The classification models were compared using their classification-specific metrics:
text
Accuracy
Precision
Recall
F1
AUC
The regression model was reported separately using:
```text
MAE
RMSE
R²
Adjusted R²
```
Classification and regression metrics were intentionally kept as separate metric groups because they measure fundamentally different tasks and are not directly comparable.
## Classification Comparison
| Model               | Accuracy | Precision | Recall |    F1 |   AUC |
| ------------------- | -------: | --------: | -----: | ----: | ----: |
| Logistic Regression |    0.809 |     0.783 |  0.691 | 0.734 | 0.861 |
| Decision Tree       |    0.770 |     0.690 |  0.721 | 0.705 | 0.754 |
| Random Forest       |    0.820 |     0.781 |  0.735 | 0.758 | 0.818 |
## Deployment Recommendation
Random Forest is the preferred classifier for deployment because it achieved the highest test accuracy of 0.820 and the highest F1 score of 0.758. It also achieved the highest recall of 0.735 among the three classifiers, making it better at identifying surviving passengers while maintaining reasonable precision. Logistic Regression achieved the highest AUC of 0.861, so it demonstrated excellent ranking/discrimination performance, but Random Forest performed better on accuracy, recall, and F1. Therefore, Random Forest provides the strongest overall balance for this classification task based on the selected evaluation metrics.
---
# Task 15 — Save and Reload the Complete Pipeline
The best-performing classification pipeline was saved using `joblib`.
The important requirement was to save the **complete pipeline**, rather than saving only the Random Forest estimator.
The complete pipeline contains:
```text
Raw Input
   ↓
Missing-Value Imputation
   ↓
One-Hot Encoding
   ↓
Feature Scaling
   ↓
Random Forest Classifier
   ↓
Prediction
```
The pipeline was saved using:
```python
joblib.dump(
    random_forest_model,
    "best_random_forest_pipeline.pkl"
)
```
If the tuned Random Forest is selected as the final best model, the tuned pipeline can instead be saved using:
python
joblib.dump(
    grid_search.best_estimator_,
    "best_random_forest_pipeline.pkl"
)
The saved pipeline was then reloaded:
```python
loaded_pipeline = joblib.load(
    "best_random_forest_pipeline.pkl"
)
```
The reloaded pipeline was tested directly on raw, unpreprocessed test data:
```python
sample = X_test.iloc[:5]
predictions = loaded_pipeline.predict(sample)
```
The verification produced:
```text
Predictions
[0 0 0 0 0]
Predictions identical: True
```
This confirms that the saved artifact can perform end-to-end predictions on raw input and produces the same predictions as the original fitted pipeline.
---
# Complete Analytics Workflow
The complete workflow can be summarized as:
```text
Titanic Dataset
      │
      ▼
Load Dataset Once
sns.load_dataset("titanic")
      │
      ▼
Immediately Save titanic.csv
      │
      ▼
Profile Dataset
info / describe / shape / missing values
      │
      ▼
Clean Missing Values
      │
      ▼
Exploratory Data Analysis
      │
      ├── Univariate Analysis
      ├── Bivariate Analysis
      ├── Multivariate Data Story
      └── Standardization Sanity Check
      │
      ▼
Stratified Train/Test Split
      │
      ▼
Training-Only Preprocessing
      │
      ├── Imputation
      ├── One-Hot Encoding
      └── StandardScaler
      │
      ▼
Three Classifiers
      │
      ├── Logistic Regression
      ├── Decision Tree
      └── Random Forest
      │
      ▼
Model Evaluation
      │
      ├── Confusion Matrix
      ├── Accuracy
      ├── Precision
      ├── Recall
      ├── F1
      └── ROC/AUC
      │
      ▼
Imbalance Comparison
      │
      ├── Baseline
      ├── Class Weight
      └── SMOTE
      │
      ▼
Random Forest GridSearchCV
      │
      ├── n_estimators
      ├── max_depth
      └── max_features
      │
      ▼
OOB Score
      │
      ▼
Fare Regression
      │
      ├── Linear Regression
      ├── MAE
      ├── RMSE
      ├── R²
      ├── Adjusted R²
      └── Residual Analysis
      │
      ▼
Final Model Comparison
      │
      ▼
Save Complete Pipeline
      │
      ▼
Reload and Predict on Raw Data
```
---
# Key Data-Science Practices Demonstrated
This module demonstrates the following practices:
* Loading a dataset once and maintaining a reproducible workflow.
* Creating an offline CSV fallback.
* Systematic data profiling.
* Defensible missing-value handling.
* IQR-based outlier detection.
* Univariate, bivariate, and multivariate analysis.
* Data visualization with written interpretations.
* Stratified train/test splitting.
* Prevention of data leakage.
* Training-only preprocessing.
* Imputation and categorical encoding.
* Feature scaling.
* Classification using multiple algorithms.
* Confusion matrices and threshold-independent ROC/AUC evaluation.
* Class imbalance handling.
* SMOTE applied only to training data.
* Hyperparameter tuning with `GridSearchCV`.
* Random Forest out-of-bag evaluation.
* Multivariate regression.
* Residual analysis and heteroscedasticity assessment.
* Model comparison and deployment recommendation.
* Saving and reloading an end-to-end machine-learning pipeline with Joblib.
---
# Reproducibility
The main script uses fixed random seeds such as:
```python
random_state=42
```
for train/test splitting and machine-learning models where applicable.
The train/test split is therefore reproducible, and the same preprocessing and modeling workflow can be rerun consistently.
---
# Files
| File                              | Purpose                                          |
| --------------------------------- | ------------------------------------------------ |
| `analytics.py`                    | Complete Tasks 1–15 analytics workflow           |
| `titanic.csv`                     | Offline copy of the Titanic dataset              |
| `best_random_forest_pipeline.pkl` | Saved end-to-end Random Forest pipeline          |
| `README.md`                       | Documentation of the complete analytics workflow |
---
# Final Result
The Analytics module completes the full workflow from raw data to deployable machine-learning artifact:
**Load → Profile → Clean → Explore → Split → Preprocess → Train → Evaluate → Handle Imbalance → Tune → Regress → Compare → Save → Reload → Predict**
The final saved pipeline can accept raw passenger features and automatically perform the required preprocessing before generating a survival prediction.







# Zepto Support Assistant
A small Retrieval-Augmented Generation (RAG) support assistant for Zepto delivery, returns, membership, tracking, cancellation, gift cards, damaged/missing items, and customer support policies.
The system uses local document embeddings with `all-MiniLM-L6-v2`, ChromaDB for vector storage and retrieval, LangGraph for query routing and orchestration, Pydantic for structured output validation, and FastAPI for the API layer.
The required graded path uses a deterministic offline mock mode controlled by the `MOCK_LLM` environment variable.
---
## 1. Project Overview
The Support Assistant follows this pipeline:
```text
Zepto Policy Documents
        |
        v
Document Ingestion
        |
        v
Chunking
        |
        v
all-MiniLM-L6-v2 Embeddings
        |
        v
ChromaDB Vector Store
        |
        v
Customer Query
        |
        v
LangGraph Intent Classification
        |
        +-----------------------------+
        |                             |
        v                             v
policy_question                general_question
        |                             |
        v                             v
retrieve_and_answer             direct_answer
        |
        v
Top-3 Retrieved Chunks
        |
        v
Mock / Optional Real LLM
        |
        v
Pydantic Structured Response
        |
        v
FastAPI POST /ask
```
---
# 2. Document Corpus
The Support Assistant uses eight Zepto policy documents.
They are stored in:
```text
support_assistant/docs/
```
The documents are:
```text
doc_01.txt  - Delivery Policy
doc_02.txt  - Returns & Refunds
doc_03.txt  - Membership Tiers
doc_04.txt  - Order Tracking
doc_05.txt  - Order Cancellation Policy
doc_06.txt  - Damaged or Missing Items
doc_07.txt  - Gift Cards
doc_08.txt  - Customer Support Hours
```
Each document contains the exact policy text provided for the project.
The documents are kept as separate files so that their filenames can be used as source identifiers in retrieval results.
---
# 3. Task 1 — Document Ingestion, Chunking, Embedding and ChromaDB
## Objective
Load all eight documents, chunk them, generate embeddings using `all-MiniLM-L6-v2`, and store the embeddings in ChromaDB.
## Document Loading
The documents are loaded from:
text
support_assistant/docs/
The `load_documents()` function in `support_assistant.py` finds files matching:
```text
doc_*.txt
```
Because the documents are short, each document is treated as one chunk.
Therefore:
```text
8 documents
     |
     v
8 chunks
     |
     v
8 embeddings
```
Each chunk receives a document ID based on its filename and metadata containing the source filename.
For example:
```text
doc_01.txt
```
is stored with a corresponding document ID and source metadata:
```text
source: doc_01.txt
```
## Embedding Model
The open-source Sentence Transformers model:
```text
all-MiniLM-L6-v2
```
is used to generate local embeddings.
The model is loaded using:
```python
SentenceTransformer("all-MiniLM-L6-v2")
```
No LLM API key is required for embeddings.
## ChromaDB
The embeddings are stored in a persistent ChromaDB collection named:
```text
zepto_support
```
The collection uses cosine similarity.
The local database is stored in:
```text
support_assistant/chroma_db/
```
The indexing process stores:
- Document IDs
- Document text
- Embeddings
- Source metadata
Example:
```text
ID          : doc_01
Document    : Delivery policy text
Embedding   : all-MiniLM-L6-v2 vector
Metadata    : source = doc_01.txt
```
---
# 4. Task 2 — Structured Prompt Template
A structured prompt template is defined in:
```text
support_assistant/prompts.py
```
The prompt follows the required:
```text
Role
Context
Task
Format
Length
```
structure.
## Role
The assistant is instructed to behave as a Zepto customer support assistant and answer using the provided Zepto policy context.
## Context
The retrieved ChromaDB chunks are inserted into the prompt using:
```text
{context}
```
## Task
The prompt instructs the assistant to answer the customer's question using only the retrieved context.
## Negative Constraint
The prompt explicitly prevents unsupported information from being introduced.
The prompt also instructs the assistant not to invent Zepto policies, prices, timings, refunds, or other details.
## Format
The expected structured response contains:
```text
Answer
Sources
Confidence
```
## Length
The prompt instructs the assistant to keep the answer concise and directly relevant.
## Few-Shot Example
The prompt includes a question, context, and answer example demonstrating how a policy question should be answered using retrieved context.
---
# 5. Task 3 — LangGraph StateGraph
The LangGraph implementation is located in:
```text
support_assistant/graph.py
```
A LangGraph `StateGraph` is used to orchestrate the support workflow.
## State
The graph uses a `TypedDict` state:
```python
class SupportState(TypedDict, total=False):
    query: str
    intent: str
    context: list[str]
    sources: list[str]
    answer: str
    confidence: float
    final_response: str
```
## Graph Nodes
The graph contains three main nodes.
### Node 1 — `classify_intent`
This node classifies the incoming query as either:
```text
policy_question
```
or:
```text
general_question
```
In the required mock mode, classification uses a keyword heuristic.
The following keywords trigger a `policy_question`:
```text
delivery
return
refund
membership
tracking
cancel
gift card
support hours
```
If none of these keywords occur in the lowercased query, the query is classified as:
No LLM call is made in mock mode.
---
### Node 2 — `retrieve_and_answer`
This node handles policy questions.
First, the customer query is embedded using:
```text
all-MiniLM-L6-v2
```
The query embedding is sent to the ChromaDB collection:
```text
zepto_support
```
The top three most similar chunks are retrieved using cosine similarity.
The retrieved documents and their source IDs are stored in the graph state.
In mock mode, no LLM is called.
Instead, the answer is generated deterministically using the first approximately 200 characters of the most similar retrieved chunk:
```text
Based on the retrieved context: <top chunk snippet>
```
---
### Node 3 — `direct_answer`
This node handles `general_question` queries.
In mock mode it returns the fixed response:
```text
I can only answer questions about Zepto policies right now.
```
No retrieval is performed for these queries.
---
## Conditional Routing
A conditional edge is connected to `classify_intent`.
The routing is:
```text
classify_intent
       |
       +-----------------------------+
       |                             |
       v                             v
policy_question                general_question
       |                             |
       v                             v
retrieve_and_answer             direct_answer
```
The routing itself does not depend on the `MOCK_LLM` value.
Only the generation steps inside the nodes branch based on `MOCK_LLM`.
---
# 6. Task 4 — Pydantic Structured Output
The final response is validated using a Pydantic model named:
```text
SupportResponse
```
The schema contains:
```python
class SupportResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
```
The confidence field is restricted to:
```text
0 <= confidence <= 1
```
## Policy Question Response
For a policy question:
```json
{
  "answer": "Based on the retrieved context: ...",
  "sources": [
    "doc_01.txt",
    "doc_04.txt",
    "doc_05.txt"
  ],
  "confidence": 1.0
}
```
The `sources` field contains the IDs of the retrieved documents/chunks.
## General Question Response
For a general question:
```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```
The `sources` list is empty because no retrieval occurs.
## Mock Mode Validation
In mock mode, the Pydantic model is populated directly by the application.
There is no LLM-generated output to validate.
The mock mode uses:
```text
confidence = 1.0
```
for deterministic behavior.
## Optional Real LLM Validation
When:
```text
MOCK_LLM=0
```
the optional real-LLM path can generate the response.
The raw response is parsed as JSON and validated using the `SupportResponse` Pydantic model.
If validation fails, the application retries up to two additional times with corrective instructions.
Therefore:
```text
Attempt 1
    |
    v
Invalid?
    |
    v
Attempt 2
    |
    v
Invalid?
    |
    v
Attempt 3
    |
    v
Error response
```
If all three attempts fail, the application returns a clearly marked validation error.
---
# 7. Task 5 — FastAPI Application
The FastAPI application is located in:
```text
support_assistant/api.py
```
The application exposes:
```text
POST /ask
```
## Request Model
The endpoint accepts a Pydantic request model:
```json
{
  "query": "How long does delivery take?"
}
```
The request model is:
```python
class AskRequest(BaseModel):
    query: str
```
## Response Model
The endpoint returns the validated:
```text
SupportResponse
```
model.
The response contains:
```text
answer
sources
confidence
```
## Running Locally
From the `support_assistant` directory:
```bash
uvicorn api:api --reload
```
The API is available at:
```text
http://127.0.0.1:8000
```
Swagger documentation is available at:
```text
http://127.0.0.1:8000/docs
```
---
## Example API Call 1 — Policy Question
Request:
```json
{
  "query": "How long does delivery take?"
}
```
This query contains the keyword:
```text
delivery
```
Therefore:
```text
policy_question
```
is selected and ChromaDB retrieval is performed.
Example raw response:
```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes...",
  "sources": [
    "doc_01.txt",
    "doc_04.txt",
    "doc_05.txt"
  ],
  "confidence": 1.0
}
```
The exact retrieved source ordering may vary depending on similarity results.
---
## Example API Call 2 — General Question
Request:
```json
{
  "query": "What is the capital of India?"
}
```
This query does not contain any of the policy keywords.
Therefore:
```text
general_question
```
is selected.
No ChromaDB retrieval is performed.
Example raw response:
```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```
---
# 8. Task 6 — Docker Containerization
The FastAPI application is containerized using:
```text
support_assistant/Dockerfile
```
The Docker image is based on:
```text
python:3.11-slim
```
The container installs the required packages:
```text
fastapi
uvicorn
pydantic
chromadb
sentence-transformers
langgraph
```
The Dockerfile also sets:
```text
MOCK_LLM=1
```
so the required deterministic mock mode is used.
## Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    chromadb \
    sentence-transformers \
    langgraph
ENV MOCK_LLM=1
EXPOSE 7860
CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "7860"]
```
## Build
From the `support_assistant` directory:
```bash
docker build -t zepto-support .
```
## Run
```bash
docker run --rm -p 7860:7860 zepto-support
```
The FastAPI application is then available locally at:
```text
http://127.0.0.1:7860
```
Swagger documentation is available at:
```text
http://127.0.0.1:7860/docs
```
The Docker container serves the same:
```text
POST /ask
```
endpoint.
## Docker Requirements
The Docker container needs access to:
```text
api.py
graph.py
prompts.py
docs/
chroma_db/
```
The Dockerfile uses:
```dockerfile
COPY . .
```
to copy the application files and local resources into the container.
The optional Hugging Face Spaces deployment is not required for the graded submission.
---
# 9. Task 7 — Full RAG Architecture
The complete Support Assistant is a Retrieval-Augmented Generation pipeline.
## Stage 1 — Ingestion
The eight Zepto policy documents are stored in:
```text
support_assistant/docs/
```
The `load_documents()` function in:
```text
support_assistant.py
```
reads all `doc_*.txt` files.
Because the documents are short, each document is treated as one chunk.
```text
8 documents
    |
    v
8 chunks
```
---
## Stage 2 — Embedding
The document chunks are passed to:
```text
all-MiniLM-L6-v2
```
using Sentence Transformers.
The embeddings are generated locally.
The `build_index()` function stores the resulting embeddings in:
```text
ChromaDB collection: zepto_support
```
The persistent database is stored in:
```text
support_assistant/chroma_db/
```
---
## Stage 3 — Retrieval
When a customer submits a query, the LangGraph node:
```text
retrieve_and_answer
```
performs retrieval for policy questions.
The query is embedded using:
```text
all-MiniLM-L6-v2
```
and the top three most similar chunks are retrieved from:
```text
zepto_support
```
using cosine similarity.
The retrieved chunks and their source document IDs are then available for answer generation.
---
## Stage 4 — Generation
For the required mock mode, the `retrieve_and_answer` node generates a deterministic response from the most similar retrieved chunk.
The `direct_answer` node handles general questions and returns the fixed mock response.
For the optional real-LLM mode:
```text
MOCK_LLM=0
```
the retrieved context and user question are passed through the structured prompt in:
```text
prompts.py
```
The real LLM can then generate a grounded answer.
---
# 10. Complete RAG Data Flow
```text
+---------------------------+
| Zepto Policy Documents    |
| docs/doc_01.txt ... 08    |
+-------------+-------------+
              |
              v
+---------------------------+
| load_documents()          |
| support_assistant.py      |
+-------------+-------------+
              |
              v
+---------------------------+
| One chunk per document    |
+-------------+-------------+
              |
              v
+---------------------------+
| all-MiniLM-L6-v2          |
| Local Embedding Model     |
+-------------+-------------+
              |
              v
+---------------------------+
| ChromaDB                  |
| Collection: zepto_support |
+-------------+-------------+
              |
              |
              | Customer Query
              v
+---------------------------+
| classify_intent           |
| LangGraph Node            |
+-------------+-------------+
              |
        +-----+-----+
        |           |
        v           v
+---------------+  +----------------+
| policy_       |  | general_       |
| question      |  | question       |
+-------+-------+  +-------+--------+
        |                  |
        v                  v
+---------------+  +----------------+
| retrieve_and_ |  | direct_answer  |
| answer        |  |                |
+-------+-------+  +-------+--------+
        |                  |
        v                  |
+---------------+           |
| Query         |           |
| Embedding     |           |
+-------+-------+           |
        |                   |
        v                   |
+---------------+           |
| Top-3 ChromaDB|           |
| Chunks        |           |
+-------+-------+           |
        |                   |
        v                   |
+---------------+           |
| Mock / Real   |<----------+
| Generation    |
+-------+-------+
        |
        v
+---------------------------+
| SupportResponse           |
| Pydantic Validation       |
+-------------+-------------+
              |
              v
+---------------------------+
| FastAPI POST /ask         |
+-------------+-------------+
              |
              v
+---------------------------+
| JSON Response             |
| answer / sources /        |
| confidence                |
+---------------------------+
```
---
# 11. MOCK_LLM Behavior
The environment variable:
```text
MOCK_LLM
```
controls the LLM-dependent parts of the application.
## Default Mock Mode
If `MOCK_LLM` is:
```text
unset
```
or:
```text
MOCK_LLM=1
```
the required deterministic mock path is used.
### Intent Classification
The `classify_intent` node uses the required keyword heuristic.
No LLM API call is made.
### Policy Answer Generation
The `retrieve_and_answer` node still performs real embedding and ChromaDB retrieval.
However, the final answer is generated by deterministic application code:
```text
Based on the retrieved context: <top chunk snippet>
```
### General Answer Generation
The `direct_answer` node returns:
```text
I can only answer questions about Zepto policies right now.
```
No LLM call is made.
This is the graded baseline.
---
## Optional Real LLM Mode
When:
```text
MOCK_LLM=0
```
the optional real-LLM branches are enabled.
The differences are:
```text
classify_intent
    |
    +--> Real LLM classification

retrieve_and_answer
    |
    +--> Real LLM answer generation
          using prompts.py
          and retrieved context

direct_answer
    |
    +--> Real LLM generation
```
The embedding and retrieval stages remain local:
```text
all-MiniLM-L6-v2
        |
        v
ChromaDB
```
and do not require an LLM API.
The real-LLM mode is optional and is not required for the graded baseline.
---
# 12. Technologies Used
| Component | Technology |
|---|---|
| Programming Language | Python |
| Document Format | `.txt` |
| Embedding Library | Sentence Transformers |
| Embedding Model | `all-MiniLM-L6-v2` |
| Vector Database | ChromaDB |
| Orchestration | LangGraph |
| State | Python `TypedDict` |
| Structured Output | Pydantic |
| API | FastAPI |
| Server | Uvicorn |
| Containerization | Docker |
| Required LLM Mode | Deterministic Mock |
| Optional LLM Mode | Real LLM |
---
# 13. Project Structure
```text
support_assistant/
│
├── api.py
├── graph.py
├── prompts.py
├── support_assistant.py
├── Dockerfile
│
├── docs/
│   ├── doc_01.txt
│   ├── doc_02.txt
│   ├── doc_03.txt
│   ├── doc_04.txt
│   ├── doc_05.txt
│   ├── doc_06.txt
│   ├── doc_07.txt
│   └── doc_08.txt
│
└── chroma_db/
```
---
# 14. Running the Support Assistant
## Build the Document Index
From the `support_assistant` directory:
```bash
python support_assistant.py
```
This loads the eight documents, generates embeddings, and stores them in ChromaDB.
Expected result:
```text
Documents loaded: 8
Embeddings stored: 8
ChromaDB collection: zepto_support
Total items in collection: 8
```
---
## Test the LangGraph
```bash
python graph.py
```
This tests both:
- policy question routing
- general question routing
---
## Start FastAPI
```bash
uvicorn api:api --reload
```
Open:
```text
http://127.0.0.1:8000/docs
```
---
## Build Docker Image
```bash
docker build -t zepto-support .
```
---
## Run Docker Container
```bash
docker run --rm -p 7860:7860 zepto-support
```
Open:
```text
http://127.0.0.1:7860/docs
```
---
# 15. Graded Baseline
The required graded configuration is:
```text
MOCK_LLM unset
```
or:
```text
MOCK_LLM=1
```
The graded pipeline therefore requires:
```text
Local Documents
      |
      v
Local Embeddings
      |
      v
ChromaDB
      |
      v
LangGraph
      |
      v
Deterministic Mock Generation
      |
      v
Pydantic Validation
      |
      v
FastAPI
```
No LLM API key, account, or network call to an LLM provider is required for the graded baseline.
---
# 16. Optional Extensions
The following are optional and are not required for the graded baseline:
- Using a real LLM with `MOCK_LLM=0`
- Deploying the Docker application to Hugging Face Spaces
- Using a free community CPU tier for deployment
If a real LLM API is used, API keys must be stored securely as environment variables or platform secrets.
API keys must never be hardcoded into the source code or committed to Git.
---
# 17. Task Completion Summary
The Support Assistant module implements all required tasks:
```text
Task 1  -> Documents + Chunking + Embeddings + ChromaDB
Task 2  -> Structured Prompt Template
Task 3  -> LangGraph StateGraph + Intent Routing + Retrieval
Task 4  -> Pydantic JSON Schema + Validation + Retry Logic
Task 5  -> FastAPI POST /ask
Task 6  -> Dockerfile + Local Container
Task 7  -> Complete RAG Architecture Documentation
```
The required graded baseline is fully based on deterministic mock mode with:
```text
MOCK_LLM=1
```
or with `MOCK_LLM` left unset.