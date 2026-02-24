import pandas as pd
from datetime import datetime, time
from dotenv import load_dotenv
import json

import os
load_dotenv()

def load_category_rules(path=".\config\config.json"):
    with open(path, "r") as f:
        return json.load(f)


CONFIG = load_category_rules()


def _time_in_window(value, window): # to be used
    if value is None:
        return False
    start, end = window
    return start <= value <= end

def get_value_counts(df):
    return df["Description"].value_counts()

def top_k_merchants(df,k=5, txn_type="DEBIT"):
    return (
        df[df["Type"]==txn_type]
        .groupby("Description")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )[:k]

def top_k_merchants_by_transactions(df,k=5, txn_type="DEBIT"):
    return (
        df[df["Type"]==txn_type]
        .groupby("Description")["Amount"]
        .count()
        .sort_values(ascending=False)
    )[:k]

def highest_spending_category(df):
    expenses = df[df["Type"] == "DEBIT"]
    totals = expenses.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    total_spend = totals.sum()
    percent = (totals / total_spend * 100).round(2) if total_spend else totals * 0
    
    return pd.DataFrame({"Total": totals, "Percent": percent})


def add_commute_category(df,category_name="Commute",overwrite_existing=True):
    OFFICE_COMMUTE = CONFIG["office_commute"]
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce").dt.time


    to_office_start = pd.to_datetime(OFFICE_COMMUTE["to_office"]["start"]).time() 
    to_office_end = pd.to_datetime(OFFICE_COMMUTE["to_office"]["end"]).time()
    from_office_start = pd.to_datetime(OFFICE_COMMUTE["from_office"]["start"]).time() 
    from_office_end = pd.to_datetime(OFFICE_COMMUTE["from_office"]["end"]).time()
    
    is_debit = df["Type"] == "DEBIT"
    is_category_other = df["Category"] == "Other"
    is_workday = df["Date"].dt.weekday.isin(OFFICE_COMMUTE["working_days"]) # week starts from monday
    is_valid_amount = df["Amount"] <= OFFICE_COMMUTE["max_amount"]

    is_commute_time = (
        ((df["Time"] >= to_office_start) & (df["Time"] <= to_office_end)) |
        ((df["Time"] >= from_office_start) & (df["Time"] <= from_office_end))
    )

    mask = is_debit & is_workday & is_commute_time & is_valid_amount & is_category_other
    df.loc[mask, "Category"] = category_name
    return df

def categorize_transactions(df):
    CATEGORY_RULES = CONFIG["categories"]

    def categorize(description):
        desc_upper = description.upper()

        for category, keywords in CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword.upper() in desc_upper:
                    return category
        return "Other"

    df["Category"] = df["Description"].apply(categorize)
    return df

def main():
    csv_path = os.environ["CSV_PATH"]
    if not csv_path:
        raise RuntimeError("CSV_PATH must be set in the environment.")

    df = pd.read_csv(csv_path)
    df = categorize_transactions(df)
    df = add_commute_category(df)
    print(highest_spending_category(df).head(20))
    

if __name__ == "__main__":
    main()