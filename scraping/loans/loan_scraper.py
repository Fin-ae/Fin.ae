import re
import sqlite3
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup


urls = [
    "https://www.emiratesnbd.com/en/loans/personal-loans/salary-transfer-loans-for-expats",
    "https://www.adcb.com/en/personal/loans/personal-loans/personal-loan-expats",
    "https://www.bankfab.com/en-ae/personal/loans/personal-loans/personal-loan",
    "https://www.mashreq.com/en/uae/neo/loans/personal-loans/pl-new-customers/",
    "https://www.dib.ae/personal/financing/personal-finance",
]

manual_values = {
    "emiratesnbd": {"bank": "Emirates NBD", "rate": 5.99, "tenure": 48, "salary": 5000},
    "adcb": {"bank": "ADCB", "rate": 7.25, "tenure": 48, "salary": 5000},
    "bankfab": {"bank": "First Abu Dhabi Bank", "rate": 3.99, "tenure": 48, "salary": 7000},
    "mashreq": {"bank": "Mashreq", "rate": 2.99, "tenure": 60, "salary": 5000},
    "dib": {"bank": "Dubai Islamic Bank", "rate": 2.89, "tenure": 48, "salary": 5000},
}

headers = {"User-Agent": "Mozilla/5.0"}
data = []


def get_manual_value(url):
    for key, value in manual_values.items():
        if key in url:
            return value
    return {"bank": "Unknown", "rate": None, "tenure": None, "salary": None}


def extract_interest_rate(text):
    matches = re.findall(r"(\d{1,2}(?:\.\d+)?)\s*%", text)
    rates = [float(match) for match in matches if 2 <= float(match) <= 40]
    return min(rates) if rates else None


def extract_tenure(text):
    matches = re.findall(r"(\d{1,3})\s*(month|months|year|years)", text, re.IGNORECASE)
    tenures = []

    for number, unit in matches:
        months = int(number)
        if unit.lower().startswith("year"):
            months *= 12
        if 3 <= months <= 300:
            tenures.append(months)

    return max(tenures) if tenures else None


def extract_salary(text):
    matches = re.findall(r"(?:AED|Dhs|Dirhams)\s*([0-9,]+)", text, re.IGNORECASE)
    salaries = []

    for match in matches:
        amount = int(match.replace(",", ""))
        if 1000 <= amount <= 100000:
            salaries.append(amount)

    return min(salaries) if salaries else None


def build_row(bank, url, scraped_rate, scraped_tenure, scraped_salary, status, note=""):
    final_rate = scraped_rate if scraped_rate is not None else bank["rate"]
    final_tenure = scraped_tenure if scraped_tenure is not None else bank["tenure"]
    final_salary = scraped_salary if scraped_salary is not None else bank["salary"]

    manual_used_for = []
    if scraped_rate is None:
        manual_used_for.append("interest_rate")
    if scraped_tenure is None:
        manual_used_for.append("tenure")
    if scraped_salary is None:
        manual_used_for.append("salary")

    if len(manual_used_for) == 0:
        data_quality = "all_fields_scraped"
    elif status.startswith("http_error") or status == "request_error":
        data_quality = "site_blocked_manual_values_used"
    else:
        data_quality = "partial_scrape_manual_values_used"

    return {
        "bank": bank["bank"],
        "source_url": url,
        "scraped_interest_rate": scraped_rate,
        "manual_interest_rate": bank["rate"],
        "final_interest_rate": final_rate,
        "scraped_tenure_months": scraped_tenure,
        "manual_tenure_months": bank["tenure"],
        "final_tenure_months": final_tenure,
        "scraped_minimum_salary_aed": scraped_salary,
        "manual_minimum_salary_aed": bank["salary"],
        "final_minimum_salary_aed": final_salary,
        "manual_used_for": ", ".join(manual_used_for),
        "data_quality": data_quality,
        "status": status,
        "note": note,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


for url in urls:
    print("Scraping:", url)
    manual = get_manual_value(url)

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            data.append(
                build_row(
                    manual,
                    url,
                    None,
                    None,
                    None,
                    f"http_error_{response.status_code}",
                    "Website did not allow direct scraping, so manual values were used.",
                )
            )
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        scraped_rate = extract_interest_rate(text)
        scraped_tenure = extract_tenure(text)
        scraped_salary = extract_salary(text)

        data.append(
            build_row(
                manual,
                url,
                scraped_rate,
                scraped_tenure,
                scraped_salary,
                "page_accessed",
                "Blank scraped fields mean the value was not clearly available in the page text.",
            )
        )

    except Exception as error:
        data.append(
            build_row(
                manual,
                url,
                None,
                None,
                None,
                "request_error",
                str(error),
            )
        )


df = pd.DataFrame(data)

df.to_csv("loan_data.csv", index=False)
df.to_excel("loan_data.xlsx", index=False)

connection = sqlite3.connect("loan_data.db")
df.to_sql("loans", connection, if_exists="replace", index=False)
connection.close()

print("DONE - dataset created")
print("CSV file: loan_data.csv")
print("Excel file: loan_data.xlsx")
print("Database file: loan_data.db")