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
            text += page.extract_text() + "\n"
    return text

def clean_text(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def parse_gpay_text(text):

    lines = text.split("\n")
    
    transactions = []
    i = 0

    while i < len(lines): # iterating through line items
        line = lines[i].strip() # cleaning line text

        def get_transaction_details(text):
            date_pattern = r'(\d{2}[A-Za-z]{3},\d{4})'
            merchant_pattern = r'Paidto(.+?)'
            amount_pattern = r'₹([\d,]+(?:\.\d+)?)'
            pattern = date_pattern + r'\s+' + merchant_pattern + r'\s+' + amount_pattern

            match = re.match(pattern, text)
            return match


        match = get_transaction_details(line)

        
        if match: # appears in input order
            raw_date = match.group(1)
            merchant = match.group(2).strip()
            amount = match.group(3)

            date_obj = datetime.strptime(raw_date, "%d%b,%Y") # string parse time
            formatted_date = date_obj.strftime("%Y-%m-%d") # string format time

            # next line has time and UPI ID
            time_line = lines[i+1] if i+1 < len(lines) else ""
            time_pattern = r'(\d{2}:\d{2}[AP]M)'
            upi_id_pattern = r'UPITransactionID:(\d+)'

            pattern = time_pattern + '\s+' + upi_id_pattern
            time_match = re.match(pattern, time_line)

            if time_match:
                raw_time = time_match.group(1)
                upi_id = time_match.group(2)

                time_obj = datetime.strptime(raw_time, "%I:%M%p")
                formatted_time = time_obj.strftime("%H:%M")

            # bank name
            bank_line = lines[i+2] if i+2 < len(lines) else ""
            pattern = r'Paidby(.+)'
            bank_match = re.match(pattern, bank_line)

            bank = bank_match.group(1).strip() if bank_match else ""

            transactions.append({
                "Date": formatted_date,
                "Time": formatted_time,
                "Description": merchant,
                "Amount": float(amount.replace(",", "")),
                "UPI_ID": upi_id,
                "Bank": bank
            })

            i += 3
        else:
            i += 1

    return pd.DataFrame(transactions)

def main():
    pdf_path = os.environ["PDF_PATH"]
    pdf_text = extract_text_from_pdf(pdf_path)
    clean_pdf_text = clean_text(pdf_text)
    df = parse_gpay_text(clean_pdf_text)
    df.to_csv(".\artefacts\text.csv")
    print(df.head())



if __name__ == "__main__":
    main()