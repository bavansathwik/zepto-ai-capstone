import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LinearRegression
import joblib
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score
)

# Load Titanic dataset (ONLY ONCE)
df = sns.load_dataset("titanic")

# Save offline fallback immediately
df.to_csv("titanic.csv", index=False)
print("Titanic dataset saved as 'titanic.csv'.")

# Dataset Information
print("\n========== DATASET INFO ==========")
df.info()

# Statistical Summary
print("\n========== NUMERICAL SUMMARY ==========")
print(df.describe())

# Dataset Shape
print("\n========== DATASET SHAPE ==========")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

# Missing Value Percentage
print("\n========== MISSING VALUE PERCENTAGE ==========")

missing_percentage = (df.isnull().sum() / len(df)) * 100
missing_percentage = missing_percentage[missing_percentage > 0].sort_values(ascending=False)

for column, percentage in missing_percentage.items():
    print(f"{column}: {percentage:.2f}%")


# Task 2: Missing Value Handling


print("\n========== MISSING VALUE HANDLING ==========")

# Calculate missing percentages
missing_percentage = (df.isnull().sum() / len(df)) * 100

# Display strategy for each affected column
for column in missing_percentage[missing_percentage > 0].index:
    percentage = missing_percentage[column]

    print(f"\nColumn: {column}")
    print(f"Missing: {percentage:.2f}%")

    if percentage < 5:
        print("Strategy: Drop rows containing missing values.")

    elif percentage <= 30:
        print("Strategy: Impute missing values.")

    else:
        print("Strategy: Drop the column (missing rate too high).")

# Apply the strategies

# Under 5% missing -> drop rows
df = df.dropna(subset=["embarked", "embark_town"])

# 5%–30% missing -> impute
df["age"] = df["age"].fillna(df["age"].median())

# Above 30% missing -> drop column
df = df.drop(columns=["deck"])

print("\nMissing value handling completed.")

# Task 3: Univariate Analysis

# Histogram and Box Plot - Age

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.histplot(df["age"], bins=20, kde=True)
plt.title("Age Distribution")

plt.subplot(1, 2, 2)
sns.boxplot(x=df["age"])
plt.title("Age Box Plot")

plt.tight_layout()
plt.show()

# Histogram and Box Plot - Fare

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.histplot(df["fare"], bins=20, kde=True)
plt.title("Fare Distribution")

plt.subplot(1, 2, 2)
sns.boxplot(x=df["fare"])
plt.title("Fare Box Plot")

plt.tight_layout()
plt.show()

# IQR Outlier Detection Function

def count_outliers(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = series[(series < lower) | (series > upper)]

    return len(outliers)

age_outliers = count_outliers(df["age"])
fare_outliers = count_outliers(df["fare"])

print("\n========== OUTLIER ANALYSIS ==========")
print(f"Age Outliers  : {age_outliers}")
print(f"Fare Outliers : {fare_outliers}")

# Mean, Median and Mode of Fare

fare_mean = df["fare"].mean()
fare_median = df["fare"].median()
fare_mode = df["fare"].mode()[0]

print("\n========== FARE STATISTICS ==========")
print(f"Mean   : {fare_mean:.2f}")
print(f"Median : {fare_median:.2f}")
print(f"Mode   : {fare_mode:.2f}")

# Distribution Interpretation
print("\n========== DISTRIBUTION INTERPRETATION ==========")

if fare_mean > fare_median > fare_mode:
    print("Fare distribution is Right-Skewed (Mean > Median > Mode).")

elif fare_mean < fare_median < fare_mode:
    print("Fare distribution is Left-Skewed (Mean < Median < Mode).")

else:
    print("Fare distribution is approximately Symmetric or does not follow a perfect ordering.")



# ======================================
# Task 4: Bivariate Analysis
# ======================================

import matplotlib.pyplot as plt
import seaborn as sns

print("\n========== SURVIVAL RATE BY SEX ==========")

# (a) Survival Rate by Sex (Boolean Masking)

male = df[df["sex"] == "male"]
female = df[df["sex"] == "female"]

male_survival = (male["survived"] == 1).mean() * 100
female_survival = (female["survived"] == 1).mean() * 100

print(f"Male Survival Rate   : {male_survival:.2f}%")
print(f"Female Survival Rate : {female_survival:.2f}%")

# (b) Survival Rate by Passenger Class

print("\n========== SURVIVAL RATE BY PCLASS ==========")

for pclass in sorted(df["pclass"].unique()):
    rate = (df[df["pclass"] == pclass]["survived"] == 1).mean() * 100
    print(f"Class {pclass}: {rate:.2f}%")

# (c) Survival Rate by Sex AND Pclass
# (Boolean Masking using &)

print("\n========== SURVIVAL RATE BY SEX AND PCLASS ==========")

for sex in ["male", "female"]:
    for pclass in sorted(df["pclass"].unique()):

        mask = (df["sex"] == sex) & (df["pclass"] == pclass)

        rate = (df.loc[mask, "survived"] == 1).mean() * 100

        print(f"{sex.capitalize()} | Class {pclass} : {rate:.2f}%")

# Correlation Matrix

corr_columns = [
    "survived",
    "pclass",
    "age",
    "sibsp",
    "parch",
    "fare"
]

corr_matrix = df[corr_columns].corr()

print("\n========== CORRELATION MATRIX ==========")
print(corr_matrix)

# Heatmap

plt.figure(figsize=(8,6))

sns.heatmap(
    corr_matrix,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)

plt.title("Correlation Heatmap")
plt.show()
# Strongest Correlations

corr_pairs = (
    corr_matrix.where(~(corr_matrix == 1))
               .stack()
               .reset_index()
)

corr_pairs.columns = ["Feature 1", "Feature 2", "Correlation"]

# Remove duplicate pairs
corr_pairs["Pair"] = corr_pairs.apply(
    lambda row: tuple(sorted([row["Feature 1"], row["Feature 2"]])),
    axis=1
)

corr_pairs = corr_pairs.drop_duplicates("Pair")

corr_pairs["Absolute Correlation"] = corr_pairs["Correlation"].abs()

top2 = corr_pairs.sort_values(
    by="Absolute Correlation",
    ascending=False
).head(2)

print("\n========== TWO STRONGEST CORRELATIONS ==========")

for _, row in top2.iterrows():
    print(
        f"{row['Feature 1']} <-> {row['Feature 2']} : "
        f"{row['Correlation']:.3f}"
    )


# ======================================
# Task 5: Multivariate Data Story
# ======================================

# Chart 1: Survival by Sex

plt.figure(figsize=(6,5))

sns.barplot(
    data=df,
    x="sex",
    y="survived"
)

plt.title("Survival Rate by Sex")
plt.ylabel("Average Survival Rate")
plt.show()


# Chart 2: Survival by Passenger Class

plt.figure(figsize=(6,5))

sns.barplot(
    data=df,
    x="pclass",
    y="survived"
)

plt.title("Survival Rate by Passenger Class")
plt.ylabel("Average Survival Rate")
plt.show()


# Chart 3: Age Distribution by Survival

plt.figure(figsize=(8,5))

sns.boxplot(
    data=df,
    x="survived",
    y="age"
)

plt.title("Age Distribution by Survival")
plt.show()

# Chart 4: Fare vs Age by Survival

plt.figure(figsize=(8,6))

sns.scatterplot(
    data=df,
    x="age",
    y="fare",
    hue="survived"
)

plt.title("Fare vs Age by Survival")
plt.show()


# ======================================
# Task 6: EDA Standardization Check
# ======================================

from sklearn.preprocessing import StandardScaler

print("\n========== STANDARDIZATION (EDA CHECK) ==========")

# Create a copy so the original dataset remains unchanged
eda_df = df.copy()

# Initialize StandardScaler
scaler = StandardScaler()

# Standardize Age and Fare
eda_df[["age_z", "fare_z"]] = scaler.fit_transform(
    eda_df[["age", "fare"]]
)

# Before Standardization

print("\nBefore Standardization")

print(f"Age  Mean : {df['age'].mean():.4f}")
print(f"Age  Std  : {df['age'].std():.4f}")

print(f"Fare Mean : {df['fare'].mean():.4f}")
print(f"Fare Std  : {df['fare'].std():.4f}")

# After Standardization

print("\nAfter Standardization")

print(f"Age_z Mean : {eda_df['age_z'].mean():.4f}")
print(f"Age_z Std  : {eda_df['age_z'].std(ddof=0):.4f}")

print(f"Fare_z Mean : {eda_df['fare_z'].mean():.4f}")
print(f"Fare_z Std  : {eda_df['fare_z'].std(ddof=0):.4f}")


# ======================================
# Task 7: Train-Test Split
# ======================================

from sklearn.model_selection import train_test_split

# Features and Target

X = df.drop(columns=["survived"])
y = df["survived"]

# Stratified Train-Test Split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\n========== TRAIN TEST SPLIT ==========")

print("Training Features :", X_train.shape)
print("Testing Features  :", X_test.shape)

print("Training Labels   :", y_train.shape)
print("Testing Labels    :", y_test.shape)


# ======================================
# Task 8: Preprocessing
# ======================================
numeric_features = [
    "pclass",
    "age",
    "sibsp",
    "parch",
    "fare"
]

categorical_features = [
    "sex",
    "embarked"
]

numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]
)

categorical_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)

# Fit ONLY on training data
X_train_processed = preprocessor.fit_transform(X_train)

# Transform ONLY on test data
X_test_processed = preprocessor.transform(X_test)

print("\n========== PREPROCESSING COMPLETE ==========")
print("Training Shape :", X_train_processed.shape)
print("Testing Shape  :", X_test_processed.shape)


# ======================================
# Task 9: Train Classification Models
# ======================================

# Logistic Regression
logistic_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(random_state=42))
    ]
)

# Decision Tree
decision_tree_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", DecisionTreeClassifier(random_state=42))
    ]
)

# Random Forest
random_forest_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(random_state=42))
    ]
)

# Train Models
logistic_model.fit(X_train, y_train)

decision_tree_model.fit(X_train, y_train)

random_forest_model.fit(X_train, y_train)

print("\nAll three models trained successfully.")

# Predictions
logistic_predictions = logistic_model.predict(X_test)

decision_tree_predictions = decision_tree_model.predict(X_test)

random_forest_predictions = random_forest_model.predict(X_test)

# Plot Decision Tree
tree = decision_tree_model.named_steps["classifier"]

feature_names = (
    decision_tree_model
    .named_steps["preprocessor"]
    .get_feature_names_out()
)

plt.figure(figsize=(20,10))

plot_tree(
    tree,
    feature_names=feature_names,
    class_names=["Not Survived", "Survived"],
    filled=True,
    rounded=True,
    fontsize=8
)

plt.title("Decision Tree Classifier")

plt.show()

models = {
    "Logistic Regression": logistic_model,
    "Decision Tree": decision_tree_model,
    "Random Forest": random_forest_model
}
results = []

plt.figure(figsize=(8,6))

for name, model in models.items():

    # Predictions
    y_pred = model.predict(X_test)

    # Probability for ROC
    y_prob = model.predict_proba(X_test)[:, 1]

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1,
        "AUC": auc
    })

    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)

    plt.plot(
        fpr,
        tpr,
        label=f"{name} (AUC={auc:.3f})"
    )

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)

    ConfusionMatrixDisplay(
        confusion_matrix=cm
    ).plot()

    plt.title(f"{name} Confusion Matrix")
    plt.show()


# ROC Curve Comparison

plt.figure(figsize=(8,6))

for name, model in models.items():

    y_prob = model.predict_proba(X_test)[:, 1]

    fpr, tpr, _ = roc_curve(y_test, y_prob)

    auc = roc_auc_score(y_test, y_prob)

    plt.plot(
        fpr,
        tpr,
        label=f"{name} (AUC = {auc:.3f})"
    )

plt.plot([0,1], [0,1], "k--")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve Comparison")

plt.legend()

plt.show()

results_df = pd.DataFrame(results)

print("\n========== MODEL COMPARISON ==========\n")

print(results_df)


# ======================================
# Task 11: Class Imbalance Handling
# ======================================

print("\n========== CLASS BALANCE ==========")

print(df["survived"].value_counts())

print("\nPercentage Distribution")

print((df["survived"].value_counts(normalize=True) * 100).round(2))

baseline_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(random_state=42))
    ]
)

baseline_model.fit(X_train, y_train)

baseline_pred = baseline_model.predict(X_test)

balanced_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            LogisticRegression(
                random_state=42,
                class_weight="balanced"
            )
        )
    ]
)

balanced_model.fit(X_train, y_train)

balanced_pred = balanced_model.predict(X_test)

X_train_processed = preprocessor.fit_transform(X_train)

X_test_processed = preprocessor.transform(X_test)

smote = SMOTE(random_state=42)

X_train_smote, y_train_smote = smote.fit_resample(
    X_train_processed,
    y_train
)

smote_model = LogisticRegression(random_state=42)

smote_model.fit(
    X_train_smote,
    y_train_smote
)

smote_pred = smote_model.predict(X_test_processed)
comparison = pd.DataFrame({

    "Method":[
        "Baseline",
        "Class Weight",
        "SMOTE"
    ],

    "Precision":[
        precision_score(y_test, baseline_pred),
        precision_score(y_test, balanced_pred),
        precision_score(y_test, smote_pred)
    ],

    "Recall":[
        recall_score(y_test, baseline_pred),
        recall_score(y_test, balanced_pred),
        recall_score(y_test, smote_pred)
    ],

    "F1 Score":[
        f1_score(y_test, baseline_pred),
        f1_score(y_test, balanced_pred),
        f1_score(y_test, smote_pred)
    ]

})

comparison = comparison.round(3)

print("\n========== IMBALANCE COMPARISON ==========\n")

print(comparison.to_string(index=False))

# ======================================
# Task 12: Hyperparameter Tuning
# ======================================
rf = RandomForestClassifier(
    random_state=42,
    bootstrap=True,
    oob_score=True
)

rf_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", rf)
    ]
)

param_grid = {

    "classifier__n_estimators": [
        50,
        100,
        200
    ],

    "classifier__max_depth": [
        None,
        5,
        10,
        20
    ],

    "classifier__max_features": [
        "sqrt",
        "log2"
    ]

}

grid_search = GridSearchCV(

    estimator=rf_pipeline,

    param_grid=param_grid,

    cv=5,

    scoring="accuracy",

    n_jobs=-1

)

grid_search.fit(X_train, y_train)

print("\n========== BEST PARAMETERS ==========\n")

print(grid_search.best_params_)

best_rf = grid_search.best_estimator_.named_steps["classifier"]

print("\n========== OOB SCORE ==========\n")

print(best_rf.oob_score_)

# ======================================
# Task 13: Regression Side Task
# ======================================

regression_features = [
    "pclass",
    "sex",
    "age",
    "sibsp",
    "parch",
    "embarked"
]

X_reg = df[regression_features]

y_reg = df["fare"]
X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
    X_reg,
    y_reg,
    test_size=0.20,
    random_state=42
)
numeric_features = [
    "pclass",
    "age",
    "sibsp",
    "parch"
]

categorical_features = [
    "sex",
    "embarked"
]
numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]
)

categorical_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ]
)
preprocessor_reg = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ]
)
regression_model = Pipeline(
    steps=[
        ("preprocessor", preprocessor_reg),
        ("regressor", LinearRegression())
    ]
)
regression_model.fit(
    X_train_reg,
    y_train_reg
)
y_pred = regression_model.predict(
    X_test_reg
)
import numpy as np

mae = mean_absolute_error(
    y_test_reg,
    y_pred
)

rmse = np.sqrt(
    mean_squared_error(
        y_test_reg,
        y_pred
    )
)

r2 = r2_score(
    y_test_reg,
    y_pred
)

# Number of predictors
p = X_train_reg.shape[1]

# Number of observations
n = len(y_test_reg)

adjusted_r2 = 1 - (
    (1-r2)*(n-1)/(n-p-1)
)

print("\n========== REGRESSION METRICS ==========\n")

print(f"MAE         : {mae:.3f}")

print(f"RMSE        : {rmse:.3f}")

print(f"R²          : {r2:.3f}")

print(f"Adjusted R² : {adjusted_r2:.3f}")
residuals = y_test_reg - y_pred

plt.figure(figsize=(8,6))

plt.scatter(
    y_pred,
    residuals,
    alpha=0.7
)

plt.axhline(
    y=0,
    color="red",
    linestyle="--"
)

plt.xlabel("Predicted Fare")

plt.ylabel("Residuals")

plt.title("Residual Plot")

plt.show()
classification_table = results_df.copy()

classification_table = classification_table.round(3)

print("\n========== CLASSIFICATION MODELS ==========\n")

print(classification_table.to_string(index=False))
regression_table = pd.DataFrame({

    "Model":[
        "Linear Regression"
    ],

    "MAE":[
        round(mae,3)
    ],

    "RMSE":[
        round(rmse,3)
    ],

    "R²":[
        round(r2,3)
    ],

    "Adjusted R²":[
        round(adjusted_r2,3)
    ]

})

print("\n========== REGRESSION MODEL ==========\n")

print(regression_table.to_string(index=False))

# ======================================
# Task 15: Save and Reload Pipeline
# ======================================

import joblib

# Save Pipeline
joblib.dump(
    random_forest_model,
    "best_random_forest_pipeline.pkl"
)

print("Pipeline saved successfully.")

# Load Pipeline
loaded_pipeline = joblib.load(
    "best_random_forest_pipeline.pkl"
)

print("Pipeline loaded successfully.")

# Predict on raw input
sample = X_test.iloc[:5]

predictions = loaded_pipeline.predict(sample)

print("\nPredictions")

print(predictions)

# Verify predictions
original = random_forest_model.predict(sample)

loaded = loaded_pipeline.predict(sample)

print(
    "\nPredictions identical:",
    (original == loaded).all()
)

