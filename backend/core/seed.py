from core import db as db_module
from core.db import POLICY_COLLECTION_BY_CATEGORY
from core.stores import news_store as _news_store_alias
from core import stores

FINANCIAL_POLICIES = [
  
]

FINANCIAL_NEWS = [{
        "news_id": "news-001",
        "title": "UAE Central Bank Holds Interest Rate Steady at 4.5%",
        "summary": "The UAE Central Bank maintained its base rate at 4.5%, following the US Federal Reserve's decision. Analysts expect this stability to support lending and mortgage markets in H1 2026.",
        "category": "monetary_policy",
        "date": "2026-01-14",
        "source": "Gulf News",
        "image_key": "dubai_skyline_news_1",
        "impact": "Positive for borrowers. Fixed-rate products remain attractive."
    },
    {
        "news_id": "news-002",
        "title": "Dubai Real Estate Hits Record AED 500B in 2025 Transactions",
        "summary": "Dubai's property market achieved record transaction volumes in 2025, driven by foreign investor demand and new golden visa regulations.",
        "category": "real_estate",
        "date": "2026-01-12",
        "source": "Arabian Business",
        "image_key": "dubai_skyline_news_2",
        "impact": "Home loan demand expected to rise. Compare mortgage rates now."
    },
    {
        "news_id": "news-003",
        "title": "New Sharia-Compliant Investment Products Launch in Abu Dhabi",
        "summary": "ADGM announces new regulatory framework enabling innovative sukuk and Islamic fintech products, expanding options for Sharia-conscious investors.",
        "category": "investment",
        "date": "2026-01-10",
        "source": "The National",
        "image_key": "investment_chart",
        "impact": "More choice for Sharia-compliant investing. Review your portfolio allocation."
    },
    {
        "news_id": "news-004",
        "title": "Credit Card Spending in UAE Grows 18% Year-on-Year",
        "summary": "Card spending surged driven by digital payments adoption and reward program enhancements by major banks.",
        "category": "banking",
        "date": "2026-01-08",
        "source": "Khaleej Times",
        "image_key": "arabic_business",
        "impact": "Maximize rewards by switching to higher-cashback cards."
    },
    {
        "news_id": "news-005",
        "title": "UAE Insurance Sector Posts 12% Premium Growth",
        "summary": "Health and motor insurance led growth as new mandatory coverage requirements and population expansion drive demand.",
        "category": "insurance",
        "date": "2026-01-06",
        "source": "Insurance Business ME",
        "image_key": "arabic_business",
        "impact": "Review your health cover. New entrants mean more competitive premiums."
    },
    {
        "news_id": "news-006",
        "title": "Personal Loan Interest Rates Drop to 3-Year Low",
        "summary": "Competition among UAE banks has driven personal loan flat rates below 4% for salary transfer customers, offering significant savings.",
        "category": "lending",
        "date": "2026-01-04",
        "source": "Gulf News",
        "image_key": "lending_finance",
        "impact": "Excellent time to consolidate debt or finance major purchases."
    }

 
]


async def seed_data():
    """Populate the in-memory news store and seed Mongo policies (idempotent)."""
    stores.news_store.clear()
    stores.news_store.extend(FINANCIAL_NEWS)

    total_seeded = 0
    for category, collection_name in POLICY_COLLECTION_BY_CATEGORY.items():
        collection = db_module.db[collection_name]
        count = await collection.count_documents({})
        if count == 0:
            docs = [dict(p) for p in FINANCIAL_POLICIES if p.get("category") == category]
            if docs:
                await collection.insert_many(docs)
                total_seeded += len(docs)
                print(f"Seeded {len(docs)} policies into {collection_name}")
        else:
            print(f"{collection_name} already has {count} documents — skipping seed")

    if total_seeded:
        print(f"Total seeded policies: {total_seeded}")

    print(f"Loaded {len(stores.news_store)} news items into in-memory store")
