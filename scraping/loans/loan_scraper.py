import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 1: Define target websites (example UAE banks / aggregators)
urls = [
    "https://www.policybazaar.ae/personal-loan/",
    "https://yallacompare.com/uae/en/personal-loans/"
]

loan_data = []

# Step 2: Scrape data
for url in urls:
    print(f"Scraping: {url}")
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, "html.parser")

        # NOTE: This is generic — may need adjustment per site
        cards = soup.find_all("div")

        for card in cards:
            text = card.get_text(strip=True)

            # Simple filtering logic
            if "loan" in text.lower():
                loan_data.append({
                    "source": url,
                    "details": text[:200]  # limit text size
                })

    except Exception as e:
        print(f"Error scraping {url}: {e}")

# Step 3: Convert to DataFrame
df = pd.DataFrame(loan_data)

# Step 4: Remove duplicates
df = df.drop_duplicates()

# Step 5: Save output
df.to_csv("scraping/loans/loan_data.csv", index=False)
df.to_json("scraping/loans/loan_data.json", orient="records", indent=4)

print("✅ Data saved successfully!")
