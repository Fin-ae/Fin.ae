from core import db as db_module
from core.db import POLICY_COLLECTION_BY_CATEGORY
from core.stores import news_store as _news_store_alias
from core import stores

FINANCIAL_POLICIES = [
  
]

FINANCIAL_NEWS = [
 
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

    print(f"Loaded {len(stores.news_store)} static news articles")
