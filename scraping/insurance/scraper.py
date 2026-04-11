import requests
from bs4 import BeautifulSoup
import json
import os

def scrape(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    data = []

    for item in soup.find_all("div"):
        text = item.get_text(strip=True)

        if "AED" in text:
            data.append({
                "plan_name": text,
                "premium": text
            })

    return data


def clean(data):
    cleaned = []

    for item in data:
        premium = item.get("premium", "")
        premium = premium.replace("AED", "").strip()

        cleaned.append({
            "provider": "Takaful Emarat",
            "plan_name": item.get("plan_name"),
            "premium": premium,
            "currency": "AED",
            "coverage": "",
            "eligibility": "",
            "benefits": []
        })

    return cleaned


def save(data):
    os.makedirs("output", exist_ok=True)

    with open("output/data.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    url = "https://www.takafulemarat.com"

    raw = scrape(url)
    cleaned = clean(raw)
    save(cleaned)

    print("Done ✅")