import pandas as pd

from dotenv import load_dotenv
import json

import os
load_dotenv()

def get_value_counts(df):
    return df["Description"].value_counts()
    

def load_category_rules(path=".\config\categories.json"):
    with open(path, "r") as f:
        return json.load(f)
CATEGORY_RULES = load_category_rules()




def highest_spending_category(df):
    expenses = df[df["Type"] == "DEBIT"]

    totals = (
        expenses
        .groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    total_spend = totals.sum()

    breakdown = pd.DataFrame({
        "Total": totals,
        "Percent": (totals / total_spend * 100).round(2)
    })
    return breakdown



def add_category(df):
    def categorize(description):
        description = description.upper()

        for category, keywords in CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword.upper() in description:
                    return category
        return "Other"

    df["Category"] = df["Description"].apply(categorize)
    return df

def main():
    csv_path = os.environ["CSV_PATH"]
    df = pd.read_csv(csv_path)
    df = add_category(df)
    print(highest_spending_category(df).head(20))
    

if __name__ == "__main__":
    main()