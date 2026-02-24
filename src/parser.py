import pandas as pd
import re
import pdfplumber
from datetime import datetime

from dotenv import load_dotenv
import os
load_dotenv()


def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def get_transaction_details(text):
    date_pattern = r'(\d{2}[A-Za-z]{3},\d{4})'
    merchant_pattern = r'(Paidto|Receivedfrom)(.+?)'
    amount_pattern = r'₹([\d,]+(?:\.\d+)?)'
    pattern = date_pattern + r'\s+' + merchant_pattern + r'\s+' + amount_pattern

    match = re.search(pattern, text)
    return match

def parse_gpay_text(text):

    lines = text.split("\n")
    transactions = []
    i = 0

    while i < len(lines): # iterating through line items
        line = lines[i].strip() # cleaning line text
        match = get_transaction_details(line)

        if not match:
            i+=1
            continue

        raw_date, prefix, merchant, amount = match.groups()
        txn_type = "DEBIT" if prefix == "Paidto" else "CREDIT"
        merchant = merchant.strip()

        date_obj = datetime.strptime(raw_date, "%d%b,%Y") # string parse time
        formatted_date = date_obj.strftime("%Y-%m-%d") # string format time

        # next line has time and UPI ID
        time_line = lines[i+1] if i+1 < len(lines) else ""
        time_pattern = r'(\d{2}:\d{2}[AP]M)'
        upi_id_pattern = r'UPITransactionID:(\d+)'

        pattern = time_pattern + '\s+' + upi_id_pattern
        time_match = re.search(pattern, time_line)

        formatted_time = None
        upi_id = None
        bank = None
        
        if time_match:
            raw_time, upi_id = time_match.groups()

            time_obj = datetime.strptime(raw_time, "%I:%M%p")
            formatted_time = time_obj.strftime("%H:%M")

        # bank name
        bank_line = lines[i+2] if i+2 < len(lines) else ""
        pattern = r'Paidby(.+)'
        bank_match = re.search(pattern, bank_line)

        bank = bank_match.group(1).strip() if bank_match else ""

        transactions.append({
            "Date": formatted_date,
            "Time": formatted_time,
            "Description": merchant,
            "Type": txn_type,
            "Amount": float(amount.replace(",", "")),
            "UPI_ID": upi_id,
            "Bank": bank
        })

        i += 3
    
    return pd.DataFrame(transactions)

def main():
    pdf_path = os.environ["PDF_PATH"]
    csv_path = os.environ["CSV_PATH"]
    if not pdf_path or not csv_path:
        raise RuntimeError("PDF_PATH and CSV_PATH must be set in the environment.")

    pdf_text = extract_text_from_pdf(pdf_path)
    clean_pdf_text = clean_text(pdf_text)
    
    df = parse_gpay_text(clean_pdf_text)
    
    df.to_csv(csv_path)
    
    print(df.head())



if __name__ == "__main__":
    main()