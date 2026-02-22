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

def main():
    pdf_path = os.environ["PDF_PATH"]
    pdf_text = extract_text_from_pdf(pdf_path)
    clean_pdf_text = clean_text(pdf_text)
    print(clean_pdf_text)

if __name__ == "__main__":
    main()