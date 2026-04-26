from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from core.config import MONGO_URL, DB_NAME

db_client: Optional[AsyncIOMotorClient] = None
db = None

POLICY_COLLECTION_BY_CATEGORY = {
    "insurance": "policies_insurance",
    "loan": "policies_loans",
    "credit_card": "policies_credit_cards",
    "investment": "policies_investments",
    "bank_account": "policies_bank_accounts",
}
POLICY_SPLIT_COLLECTIONS = list(POLICY_COLLECTION_BY_CATEGORY.values())
LEGACY_POLICY_COLLECTION = "policies"

POLICY_CATEGORY_NORMALIZATION = {
    "credit card": "credit_card",
    "credit cards": "credit_card",
    "credit-card": "credit_card",
    "bank account": "bank_account",
    "bank accounts": "bank_account",
    "bank-account": "bank_account",
    "investments": "investment",
    "loans": "loan",
}

POLICY_ID_PREFIX_TO_CATEGORY = (
    ("ins-", "insurance"),
    ("loan-", "loan"),
    ("cc-", "credit_card"),
    ("inv-", "investment"),
    ("ba-", "bank_account"),
)


def normalize_policy_category(raw_category: Optional[str]) -> Optional[str]:
    if not raw_category:
        return None
    key = raw_category.strip().lower().replace("-", "_")
    return POLICY_CATEGORY_NORMALIZATION.get(key, key)


def infer_category_from_policy_id(policy_id: str) -> Optional[str]:
    pid = (policy_id or "").strip().lower()
    for prefix, category in POLICY_ID_PREFIX_TO_CATEGORY:
        if pid.startswith(prefix):
            return category
    return None


def policy_query_collections(category: Optional[str] = None) -> list:
    normalized = normalize_policy_category(category)
    if normalized and normalized in POLICY_COLLECTION_BY_CATEGORY:
        return [
            db[POLICY_COLLECTION_BY_CATEGORY[normalized]],
            db[LEGACY_POLICY_COLLECTION],
        ]
    return [*(db[name] for name in POLICY_SPLIT_COLLECTIONS), db[LEGACY_POLICY_COLLECTION]]


async def init_db():
    """Open Mongo client, create indexes, and run seed. Call from app lifespan."""
    global db_client, db
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client[DB_NAME]
    await db.users.create_index("email", unique=True)
    await db.applications.create_index("user_id")
    await db.applications.create_index("application_number", unique=True)
    for collection_name in POLICY_SPLIT_COLLECTIONS:
        await db[collection_name].create_index("policy_id", unique=True)
    await db.policies.create_index("policy_id", unique=True)


def close_db():
    global db_client
    if db_client is not None:
        db_client.close()
