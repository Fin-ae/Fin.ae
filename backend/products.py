"""
products.py
Loads the UAE financial product catalogue from products.json
and provides filtering and lookup functions used by the API routes.

The product list is cached in memory after the first load —
no need to read the file on every request.
"""

import json
import time
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── In-memory cache ──────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 300  # 5 minutes — matching Guide Book 1 capstone pattern

DATA_FILE = Path(__file__).parent / "data" / "products.json"


def _load_products() -> list[dict]:
    """Load products from JSON file, using cache when valid."""
    now = time.time()
    if "products" in _cache and now - _cache["loaded_at"] < CACHE_TTL:
        log.info("Product cache HIT")
        return _cache["products"]

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    _cache["products"] = products
    _cache["loaded_at"] = now
    log.info(f"Loaded {len(products)} products from {DATA_FILE}")
    return products


def get_all_products(
    category: str | None = None,
    sharia: bool | None = None,
    min_salary: int | None = None,
    residency: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """
    Return a filtered, paginated list of products.
    Used by GET /api/policies.
    """
    products = _load_products()

    # Apply filters
    if category:
        products = [p for p in products if p["category"] == category]
    if sharia is not None:
        products = [p for p in products if p["sharia"] == sharia]
    if min_salary is not None:
        # Return products whose minimum salary requirement is at or below this value
        products = [p for p in products if p["min_salary"] <= min_salary]
    if residency:
        products = [p for p in products if residency in p["residency"]]

    total = len(products)
    paginated = products[offset: offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": paginated,
    }


def get_product_by_id(product_id: str) -> dict | None:
    """Return a single product by its ID, or None if not found."""
    products = _load_products()
    for product in products:
        if product["id"] == product_id:
            return product
    return None


def get_products_by_ids(product_ids: list[str]) -> list[dict]:
    """Return multiple products by their IDs, preserving input order."""
    result = []
    for pid in product_ids:
        product = get_product_by_id(pid)
        if product:
            result.append(product)
    return result
