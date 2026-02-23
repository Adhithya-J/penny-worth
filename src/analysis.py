import pandas as pd

from dotenv import load_dotenv
import json

import os
load_dotenv()

def get_value_counts(df):
    return df["Description"].value_counts()
    

def load_category_rules(path=".\config\config.json"):
    with open(path, "r") as f:
        return json.load(f)
    
CATEGORY_RULES = load_category_rules()["categories"]
OFFICE_COMMUTE = load_category_rules()["office_commute"]

def top_k_merchants(df,k=5):
    return (
        df[df["Type"]=="DEBIT"]
        .groupby("Description")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )[:k]

def top_k_merchants_by_transactions(df,k=5):
    return (
        df[df["Type"]=="DEBIT"]
        .groupby("Description")["Amount"]
        .count()
        .sort_values(ascending=False)
    )[:k]

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

def add_office_commute(df):
    to_office_start = pd.to_datetime(OFFICE_COMMUTE["to_office"]["start"]).time() 
    to_office_end = pd.to_datetime(OFFICE_COMMUTE["to_office"]["end"]).time()
    from_office_start = pd.to_datetime(OFFICE_COMMUTE["from_office"]["start"]).time() 
    from_office_end = pd.to_datetime(OFFICE_COMMUTE["from_office"]["start"]).time()
    working_days = OFFICE_COMMUTE["working_days"] # week starts from monday
    max_amount = OFFICE_COMMUTE["max_amount"]
    
    df["Date"] = pd.to_datetime(df["Date"])
    df["Time"] = pd.to_datetime(df["Time"]).dt.time
    
    df["DateTime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str)
    )

    is_debit = df["Type"] == "DEBIT"
    is_category_other = df["Category"] == "Other"
    is_workday = df["DateTime"].dt.weekday.isin(working_days)
    is_valid_amount = df["Amount"] <= max_amount

    is_commute_time = (
        ((df["DateTime"].dt.time >= to_office_start) & 
         (df["DateTime"].dt.time <= to_office_end)) |
        ((df["DateTime"].dt.time >= from_office_start) & 
         (df["DateTime"].dt.time <= from_office_end))
    )

    base_mask = is_debit & is_workday & is_commute_time & is_valid_amount & is_category_other
    df.loc[base_mask, "Category"] = "Commute"
    return df

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
    df = add_office_commute(df)
    print(highest_spending_category(df).head(20))
    

if __name__ == "__main__":
    main()