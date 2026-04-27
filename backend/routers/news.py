import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Query

from core.config import NEWS_API_KEY, NEWS_API_URL, NEWS_CACHE_TTL
from core.llm import call_groq
from core.stores import get_news_cache, news_store, set_news_cache

router = APIRouter()

CATEGORY_IMAGE_MAP = {
    "monetary_policy": "dubai_skyline_news_1",
    "real_estate": "dubai_skyline_news_2",
    "investment": "investment_chart",
    "banking": "credit_card_mockup",
    "insurance": "arabic_business",
    "lending": "lending_finance",
}


async def fetch_live_news() -> list:
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(
            NEWS_API_URL,
            json={
                "action": "getArticles",
                "keyword": [
                    "UAE banking", "UAE finance", "UAE insurance",
                    "UAE investment", "UAE mortgage", "UAE loan",
                    "Dubai real estate", "Abu Dhabi economy",
                    "UAE interest rate", "UAE central bank"
                ],
                "keywordOper": "OR",
                "keywordLoc": "body,title",
                "lang": "eng",
                "articlesPage": 1,
                "articlesCount": 10,
                "articlesSortBy": "date",
                "articlesSortByAsc": False,
                "resultType": "articles",
                "dataType": ["news"],
                "forceMaxDataTimeWindow": 14,
                "apiKey": NEWS_API_KEY,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    raw_articles = data.get("articles", {}).get("results", [])
    if not raw_articles:
        print("[News] EventRegistry returned 0 articles")
        return []

    print(f"[News] Fetched {len(raw_articles)} raw articles from EventRegistry")

    usable = [a for a in raw_articles if (a.get("body") or a.get("title"))][:6]

    articles_text = "\n".join([
        f"{i+1}. Title: {a.get('title', '')}\nBody: {(a.get('body') or '')[:400]}"
        for i, a in enumerate(usable)
    ])

    groq_messages = [
        {
            "role": "system",
            "content": (
                "You are a UAE financial news analyst. For each numbered article return a JSON array "
                "where each element has:\n"
                '- "index": 1-based integer\n'
                '- "category": one of monetary_policy, real_estate, investment, banking, insurance, lending\n'
                '- "summary": two-sentence plain-text summary focused on the key financial takeaway\n'
                '- "impact": one actionable sentence for UAE consumers (max 15 words)\n'
                "Return ONLY a valid JSON array, no markdown fences, no extra text."
            ),
        },
        {"role": "user", "content": f"Analyse these articles:\n\n{articles_text}"},
    ]

    enrichment_map: dict = {}
    try:
        raw = await asyncio.to_thread(call_groq, groq_messages, 0.2, 1200)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned).rstrip("`").strip()
        enriched = json.loads(cleaned)
        if isinstance(enriched, list):
            enrichment_map = {item["index"]: item for item in enriched}
        print(f"[News] Groq enriched {len(enrichment_map)} articles")
    except Exception as e:
        print(f"[News] Groq enrichment error: {e}")

    news_items = []
    for i, article in enumerate(usable):
        enr = enrichment_map.get(i + 1, {})
        category = enr.get("category", "banking")
        date_str = (article.get("dateTime") or "")[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        body = (article.get("body") or "")
        url = article.get("url", "")
        news_items.append({
            "news_id": f"live-{i + 1}",
            "title": article.get("title", ""),
            "summary": enr.get("summary") or (body[:250] + "..." if len(body) > 250 else body),
            "category": category,
            "date": date_str,
            "source": (article.get("source") or {}).get("title", "News Source"),
            "url": url,
            "image_key": CATEGORY_IMAGE_MAP.get(category, "dubai_skyline_news_1"),
            "impact": enr.get("impact", ""),
            "is_live": True,
        })

    print(f"[News] Returning {len(news_items)} enriched live articles")
    return news_items


@router.get("/api/news")
async def get_news(category: Optional[str] = Query(None)):
    now_ts = datetime.now(timezone.utc).timestamp()
    cache = get_news_cache()
    cache_stale = (
        cache["fetched_at"] is None
        or (now_ts - cache["fetched_at"]) >= NEWS_CACHE_TTL
    )

    is_live = False
    if cache_stale and NEWS_API_KEY:
        try:
            articles = await fetch_live_news()
            if articles:
                set_news_cache(articles, now_ts)
                cache = get_news_cache()
                is_live = True
        except Exception as e:
            print(f"[News] Live fetch failed: {e}")

    if cache["articles"]:
        news = cache["articles"]
        is_live = True
    else:
        news = list(news_store)

    if category:
        news = [n for n in news if n.get("category") == category]

    fetched_at = (
        datetime.fromtimestamp(cache["fetched_at"], tz=timezone.utc).isoformat()
        if cache["fetched_at"]
        else None
    )
    return {"news": news, "count": len(news), "is_live": is_live, "fetched_at": fetched_at}
