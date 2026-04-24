"""
News API Service Module
Handles all news-related API functionality for FastAPI integration
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from news.integration.news_client import NewsClient
from news.integration.rss_fetcher import RSSFetcher
from news.integration.uae_filter import UAENewsFilter

logger = logging.getLogger(__name__)


# ─── Response Models ───────────────────────────────────────

class NewsArticleResponse(BaseModel):
    """API response model for a news article"""
    news_id: str
    title: str
    summary: str
    category: str
    source: str
    url: Optional[str] = None
    date: str
    sentiment: str = "neutral"
    impact: str = ""
    image_key: Optional[str] = None
    keywords: List[str] = []
    relevance_score: float = 1.0
    uae_entities: List[str] = []
    locations: List[str] = []
    financial_topics: List[str] = []


class NewsListResponse(BaseModel):
    """API response model for news list"""
    news: List[NewsArticleResponse]
    count: int
    total_count: int
    filters_applied: Dict[str, Any] = {}
    fetched_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class NewsFilterRequest(BaseModel):
    """Request model for filtering news"""
    category: Optional[str] = None
    min_relevance_score: float = Field(default=0.3, ge=0.0, le=1.0)
    days_back: int = Field(default=7, ge=1, le=90)
    entities: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ─── News Service ───────────────────────────────────────

class NewsService:
    """Service for managing news operations"""

    def __init__(self):
        self.news_store: List[Dict[str, Any]] = []
        self.cache_ttl = 3600  # 1 hour
        self.last_fetch_time = None

    def seed_mock_data(self):
        """Initialize with mock UAE financial news"""
        mock_news = [
            {
                "news_id": "news-001",
                "title": "UAE Central Bank Holds Interest Rate Steady at 4.5%",
                "summary": "The UAE Central Bank maintained its base rate at 4.5%, following the US Federal Reserve's decision.",
                "category": "monetary_policy",
                "date": "2026-01-14",
                "source": "Gulf News",
                "url": "https://www.gulf-news.com/...",
                "sentiment": "neutral",
                "impact": "Positive for borrowers. Fixed-rate products remain attractive.",
                "keywords": ["interest rate", "central bank", "monetary policy"],
                "relevance_score": 0.95,
                "uae_entities": ["Central Bank of UAE"],
                "locations": ["Abu Dhabi"],
                "financial_topics": ["interest_rates", "banking"]
            },
            {
                "news_id": "news-002",
                "title": "Dubai Real Estate Hits Record AED 500B in 2025 Transactions",
                "summary": "Dubai's property market achieved record transaction volumes in 2025.",
                "category": "real_estate",
                "date": "2026-01-12",
                "source": "Arabian Business",
                "url": "https://www.arabianbusiness.com/...",
                "sentiment": "positive",
                "impact": "Home loan demand expected to rise. Compare mortgage rates now.",
                "keywords": ["real estate", "property", "Dubai"],
                "relevance_score": 0.92,
                "uae_entities": ["Emaar"],
                "locations": ["Dubai"],
                "financial_topics": ["real_estate", "investment"]
            },
            {
                "news_id": "news-003",
                "title": "Credit Card Spending in UAE Grows 18% Year-on-Year",
                "summary": "Card spending surged driven by digital payments adoption.",
                "category": "banking",
                "date": "2026-01-08",
                "source": "Khaleej Times",
                "url": "https://www.khaleejtimes.com/...",
                "sentiment": "positive",
                "impact": "Maximize rewards by switching to higher-cashback cards.",
                "keywords": ["credit cards", "banking", "digital payments"],
                "relevance_score": 0.88,
                "uae_entities": ["Emirates NBD", "FAB"],
                "locations": ["UAE"],
                "financial_topics": ["banking", "lending"]
            },
            {
                "news_id": "news-004",
                "title": "New Sharia-Compliant Investment Products Launch in Abu Dhabi",
                "summary": "ADGM announces new regulatory framework enabling Islamic fintech.",
                "category": "investment",
                "date": "2026-01-10",
                "source": "The National",
                "url": "https://www.thenational.ae/...",
                "sentiment": "positive",
                "impact": "More choice for Sharia-compliant investing.",
                "keywords": ["Islamic finance", "investment", "ADGM"],
                "relevance_score": 0.9,
                "uae_entities": ["ADGM", "ADIB"],
                "locations": ["Abu Dhabi"],
                "financial_topics": ["investment", "banking"]
            },
            {
                "news_id": "news-005",
                "title": "Personal Loan Interest Rates Drop to 3-Year Low",
                "summary": "Competition among UAE banks has driven personal loan rates below 4%.",
                "category": "lending",
                "date": "2026-01-06",
                "source": "Gulf News",
                "url": "https://www.gulf-news.com/...",
                "sentiment": "positive",
                "impact": "Excellent time to consolidate debt or finance purchases.",
                "keywords": ["loans", "interest rates", "UAE banks"],
                "relevance_score": 0.87,
                "uae_entities": ["Emirates NBD", "FAB", "RAK Bank"],
                "locations": ["UAE"],
                "financial_topics": ["lending", "interest_rates"]
            },
            {
                "news_id": "news-006",
                "title": "UAE Insurance Sector Posts 12% Premium Growth",
                "summary": "Health and motor insurance led growth in the UAE market.",
                "category": "insurance",
                "date": "2026-01-04",
                "source": "Insurance Business ME",
                "url": "https://www.insurancebusinessme.com/...",
                "sentiment": "positive",
                "impact": "Review your health cover. New entrants mean competitive premiums.",
                "keywords": ["insurance", "health insurance", "UAE"],
                "relevance_score": 0.85,
                "uae_entities": ["AXA", "Allianz"],
                "locations": ["UAE"],
                "financial_topics": ["insurance", "employment"]
            },
        ]

        self.news_store = mock_news
        self.last_fetch_time = datetime.now()
        logger.info(f"Seeded {len(mock_news)} mock news articles")

    async def fetch_live_news(self) -> List[Dict[str, Any]]:
        """
        Fetch news from live sources (NewsAPI and RSS)
        Falls back to mock data if APIs fail
        """
        try:
            combined_articles = []

            # Fetch from NewsAPI
            try:
                async with NewsClient() as news_client:
                    articles = await news_client.fetch_and_normalize_news(
                        query="UAE financial news stocks banking",
                        page_size=50
                    )
                    logger.info(f"Fetched {len(articles)} articles from NewsAPI")
                    combined_articles.extend([a.dict() for a in articles])
            except Exception as e:
                logger.warning(f"NewsAPI fetch failed, using mock data: {e}")

            # Fetch from RSS feeds
            try:
                async with RSSFetcher() as rss_fetcher:
                    rss_articles = await rss_fetcher.fetch_all_feeds()
                    logger.info(f"Fetched {len(rss_articles)} articles from RSS feeds")
                    combined_articles.extend(rss_articles)
            except Exception as e:
                logger.warning(f"RSS fetch failed: {e}")

            # Apply UAE filtering
            if combined_articles:
                uae_filter = UAENewsFilter()
                filtered = uae_filter.filter_by_uae_relevance(
                    combined_articles,
                    min_score=0.3
                )

                # Enrich articles
                enriched = [uae_filter.enrich_article(article) for article in filtered]

                # Convert to standardized format
                standardized = []
                for idx, article in enumerate(enriched):
                    try:
                        standardized.append({
                            "news_id": f"live-{datetime.now().strftime('%s')}-{idx}",
                            "title": article.get("title", "")[:500],
                            "summary": article.get("description", article.get("summary", ""))[:2000],
                            "category": article.get("category", "market_updates"),
                            "source": article.get("source", {}).get("name", "Unknown") if isinstance(article.get("source"), dict) else article.get("source", "Unknown"),
                            "url": article.get("url"),
                            "date": article.get("publishedAt", article.get("date", datetime.now().strftime('%Y-%m-%d')))[:10],
                            "sentiment": article.get("sentiment", "neutral"),
                            "keywords": article.get("uae_entities", []) + article.get("financial_topics", []),
                            "relevance_score": article.get("uae_relevance_score", 0.5),
                            "uae_entities": article.get("uae_entities", []),
                            "locations": article.get("locations", []),
                            "financial_topics": article.get("financial_topics", [])
                        })
                    except Exception as e:
                        logger.warning(f"Failed to standardize article: {e}")
                        continue

                self.news_store = standardized
                self.last_fetch_time = datetime.now()
                logger.info(f"Updated news store with {len(standardized)} articles")
                return standardized

        except Exception as e:
            logger.error(f"Error fetching live news: {e}")

        # Fall back to mock data
        if not self.news_store:
            self.seed_mock_data()

        return self.news_store

    def get_news(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get news with optional filtering"""
        filtered = list(self.news_store)

        if category:
            filtered = [n for n in filtered if n.get("category") == category]

        total = len(filtered)

        # Sort by date (newest first)
        filtered.sort(key=lambda x: x.get("date", ""), reverse=True)

        # Apply pagination
        paginated = filtered[offset : offset + limit]

        return paginated, total

    def get_news_by_filter(
        self,
        filter_request: NewsFilterRequest
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get news with advanced filtering"""
        uae_filter = UAENewsFilter()

        filtered = list(self.news_store)

        # Apply relevance filter
        filtered = uae_filter.filter_by_uae_relevance(
            filtered,
            min_score=filter_request.min_relevance_score
        )

        # Apply category filter
        if filter_request.category:
            filtered = [n for n in filtered if n.get("category") == filter_request.category]

        # Apply entity filter
        if filter_request.entities:
            filtered = uae_filter.filter_by_entities(filtered, filter_request.entities)

        # Apply location filter
        if filter_request.locations:
            filtered = uae_filter.filter_by_locations(filtered, filter_request.locations)

        # Apply topic filter
        if filter_request.topics:
            filtered = uae_filter.filter_by_topics(filtered, filter_request.topics)

        # Apply date range filter
        filtered = uae_filter.filter_by_date_range(
            filtered,
            days=filter_request.days_back
        )

        total = len(filtered)

        # Sort by relevance score
        filtered.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Apply pagination
        paginated = filtered[filter_request.offset : filter_request.offset + filter_request.limit]

        return paginated, total

    def get_news_categories(self) -> List[str]:
        """Get list of available news categories"""
        categories = set()
        for article in self.news_store:
            category = article.get("category")
            if category:
                categories.add(category)
        return sorted(list(categories))

    def get_trending_entities(self, limit: int = 10) -> List[tuple[str, int]]:
        """Get most mentioned UAE entities"""
        entity_counts: Dict[str, int] = {}

        for article in self.news_store:
            for entity in article.get("uae_entities", []):
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_entities[:limit]

    def get_trending_topics(self, limit: int = 10) -> List[tuple[str, int]]:
        """Get most covered financial topics"""
        topic_counts: Dict[str, int] = {}

        for article in self.news_store:
            for topic in article.get("financial_topics", []):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[:limit]


# ─── Singleton Instance ───────────────────────────────────

_news_service = None


def get_news_service() -> NewsService:
    """Get or create news service singleton"""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
