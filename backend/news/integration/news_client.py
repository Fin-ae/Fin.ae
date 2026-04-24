"""
News API Client for Fin.ae
Integrates multiple news sources with UAE-specific filtering
"""

import os
import math
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "").strip()
NEWS_API_URL = "https://newsapi.org/v2"

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100  # requests per day for free tier
RATE_LIMIT_WINDOW = 86400  # 24 hours in seconds
REQUEST_TIMEOUT = 10  # seconds

# ─── Enums ───────────────────────────────────────────────

class NewsCategory(str, Enum):
    BANKING = "banking"
    INSURANCE = "insurance"
    LENDING = "lending"
    INVESTMENT = "investment"
    REAL_ESTATE = "real_estate"
    MONETARY_POLICY = "monetary_policy"
    STOCKS = "stocks"
    CRYPTOCURRENCIES = "cryptocurrencies"
    MARKET_UPDATES = "market_updates"


class NewsSentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


# ─── Pydantic Models ───────────────────────────────────────

class NewsArticleModel(BaseModel):
    """Validated news article model"""
    news_id: str = Field(..., description="Unique identifier for the article")
    title: str = Field(..., min_length=5, max_length=500, description="Article title")
    summary: str = Field(..., min_length=10, max_length=2000, description="Article summary")
    category: NewsCategory = Field(..., description="News category")
    source: str = Field(..., description="News source name")
    url: Optional[str] = Field(None, description="Source URL")
    date: str = Field(..., description="Publication date (YYYY-MM-DD)")
    sentiment: NewsSentiment = Field(default=NewsSentiment.NEUTRAL, description="Article sentiment")
    impact: str = Field(default="", description="Financial impact summary")
    image_key: Optional[str] = Field(None, description="Image key for display")
    keywords: List[str] = Field(default_factory=list, description="Relevant keywords")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="UAE relevance score")

    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @validator('keywords')
    def validate_keywords(cls, v):
        return [k.lower().strip() for k in v][:10]  # Max 10 keywords


class NewsApiResponse(BaseModel):
    """Response model from NewsAPI"""
    articles: List[Dict[str, Any]] = []
    totalResults: int = 0
    status: str = "ok"


# ─── Rate Limiter ───────────────────────────────────────

class RateLimiter:
    """Simple rate limiter for API requests"""

    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self.requests: List[float] = []

    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = datetime.now().timestamp()
        # Remove old requests outside the window
        self.requests = [req for req in self.requests if now - req < self.window]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def get_retry_after(self) -> int:
        """Get seconds until next request is allowed"""
        if not self.requests:
            return 0
        oldest = self.requests[0]
        retry_after = math.ceil(self.window - (datetime.now().timestamp() - oldest))
        return max(0, retry_after)


# ─── UAE-Specific Keywords and Filters ───────────────────

UAE_KEYWORDS = {
    "banking": ["UAE bank", "Emirates NBD", "FIB", "ADIB", "RAK Bank", "FAB", "DiBu"],
    "insurance": ["UAE insurance", "AXA", "Allianz", "Takaful", "ENBD Insurance"],
    "real_estate": ["Dubai", "Abu Dhabi", "Sharjah", "UAE property", "REDFIN", "DAMAC", "Emaar"],
    "stocks": ["DFM", "ADX", "UAE stock", "stock exchange", "equities"],
    "investment": ["UAE investment", "ADGM", "sukuk", "Islamic finance"],
    "lending": ["UAE loan", "mortgage", "UAE credit"],
    "monetary_policy": ["UAE Central Bank", "CBUAE", "interest rate", "monetary policy"],
}

UAE_SOURCES = [
    "Gulf News",
    "Arabian Business",
    "The National",
    "Khaleej Times",
    "Emirates 24/7",
    "UAE Business News",
    "Zawya",
    "Insurance Business ME",
    "CoinTribune",  # For crypto news
]


# ─── News Client ───────────────────────────────────────

class NewsClient:
    """Client for fetching and processing news from multiple sources"""

    def __init__(self, api_key: str = NEWS_API_KEY):
        self.api_key = api_key
        self.rate_limiter = RateLimiter()
        self.base_url = NEWS_API_URL
        self.client = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hour

    async def init_client(self):
        """Initialize async HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def close_client(self):
        """Close async HTTP client"""
        if self.client:
            await self.client.aclose()

    async def __aenter__(self):
        await self.init_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_client()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self.cache:
            return False
        entry = self.cache[key]
        if datetime.now().timestamp() - entry["timestamp"] > self.cache_ttl:
            del self.cache[key]
            return False
        return True

    async def fetch_news(
        self,
        query: str,
        category: Optional[str] = None,
        sort_by: str = "publishedAt",
        language: str = "en",
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch news from NewsAPI with rate limiting and caching
        
        Args:
            query: Search query
            category: News category filter
            sort_by: Sort order (publishedAt, relevancy, popularity)
            language: Language code
            page_size: Number of articles to fetch
            
        Returns:
            List of news articles
        """
        if not self.api_key:
            logger.warning("NEWS_API_KEY not configured. Using mock data.")
            return []

        if not self.rate_limiter.is_allowed():
            retry_after = self.rate_limiter.get_retry_after()
            logger.error(f"Rate limit exceeded. Retry after {retry_after} seconds")
            raise Exception(f"Rate limit exceeded. Try again in {retry_after} seconds")

        # Check cache
        cache_key = f"news:{query}:{category}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]["data"]

        try:
            await self.init_client()
            
            params = {
                "q": query,
                "language": language,
                "pageSize": page_size,
                "sortBy": sort_by,
                "apiKey": self.api_key,
            }

            response = await self.client.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the result
            self.cache[cache_key] = {
                "data": data.get("articles", []),
                "timestamp": datetime.now().timestamp()
            }
            
            return data.get("articles", [])

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching news: {e}")
            return []

    async def fetch_uae_news(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """Fetch UAE-specific financial news"""
        try:
            articles = await self.fetch_news(
                query="UAE financial news",
                page_size=page_size
            )
            return articles
        except Exception as e:
            logger.error(f"Error fetching UAE news: {e}")
            return []

    def _categorize_article(self, article: Dict[str, Any]) -> str:
        """Categorize article based on keywords"""
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        content = f"{title} {description}"

        # Check against category keywords
        for category, keywords in UAE_KEYWORDS.items():
            if any(keyword.lower() in content for keyword in keywords):
                return category

        return NewsCategory.MARKET_UPDATES.value

    def _calculate_relevance_score(self, article: Dict[str, Any]) -> float:
        """Calculate UAE relevance score (0-1)"""
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        source = (article.get("source", {}).get("name") or "").lower()
        
        score = 0.0

        # Check source
        if any(uae_source.lower() in source for uae_source in UAE_SOURCES):
            score += 0.5

        # Check for UAE keywords
        content = f"{title} {description}"
        uae_indicator_score = 0
        for keywords in UAE_KEYWORDS.values():
            if any(keyword.lower() in content for keyword in keywords):
                uae_indicator_score += 0.3
                break

        score += min(uae_indicator_score, 0.5)

        # Check date (recent news is more relevant)
        try:
            pub_date = datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00"))
            days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
            if days_old < 1:
                score += 0.2
            elif days_old < 7:
                score += 0.1
        except (ValueError, TypeError):
            pass

        return min(score, 1.0)

    def _extract_keywords(self, article: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords from article"""
        title = (article.get("title") or "").lower()
        description = (article.get("description") or "").lower()
        content = f"{title} {description}"

        keywords = set()
        for category_keywords in UAE_KEYWORDS.values():
            for keyword in category_keywords:
                if keyword.lower() in content:
                    keywords.add(keyword.lower())

        return list(keywords)[:10]

    def normalize_article(self, article: Dict[str, Any], article_id: str) -> Optional[NewsArticleModel]:
        """
        Normalize and validate raw API article to NewsArticleModel
        
        Args:
            article: Raw article from API
            article_id: Unique article ID
            
        Returns:
            Normalized NewsArticleModel or None if validation fails
        """
        try:
            # Extract and validate data
            title = article.get("title", "No title")[:500]
            summary = article.get("description") or article.get("content") or "No summary available"
            summary = summary[:2000]

            # Safely parse date
            date_str = article.get("publishedAt", datetime.now().isoformat())[:10]
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                date_str = datetime.now().strftime('%Y-%m-%d')

            # Create normalized article
            normalized = NewsArticleModel(
                news_id=article_id,
                title=title,
                summary=summary,
                category=self._categorize_article(article),
                source=article.get("source", {}).get("name", "Unknown"),
                url=article.get("url"),
                date=date_str,
                keywords=self._extract_keywords(article),
                relevance_score=self._calculate_relevance_score(article),
            )

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing article {article_id}: {e}")
            return None

    async def fetch_and_normalize_news(self, query: str, page_size: int = 50) -> List[NewsArticleModel]:
        """
        Fetch news from API and normalize to standard format
        
        Args:
            query: Search query
            page_size: Number of articles to fetch
            
        Returns:
            List of normalized NewsArticleModel objects
        """
        try:
            articles = await self.fetch_news(query, page_size=page_size)
            normalized_articles = []

            for idx, article in enumerate(articles):
                article_id = f"api-{datetime.now().strftime('%s')}-{idx}"
                normalized = self.normalize_article(article, article_id)
                if normalized:
                    normalized_articles.append(normalized)

            return normalized_articles

        except Exception as e:
            logger.error(f"Error fetching and normalizing news: {e}")
            return []

    def filter_by_category(
        self,
        articles: List[NewsArticleModel],
        category: str
    ) -> List[NewsArticleModel]:
        """Filter articles by category"""
        return [a for a in articles if a.category == category]

    def filter_by_relevance(
        self,
        articles: List[NewsArticleModel],
        min_score: float = 0.5
    ) -> List[NewsArticleModel]:
        """Filter articles by relevance score"""
        return [a for a in articles if a.relevance_score >= min_score]

    def filter_by_date_range(
        self,
        articles: List[NewsArticleModel],
        days_back: int = 7
    ) -> List[NewsArticleModel]:
        """Filter articles from last N days"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).date()
        return [
            a for a in articles 
            if datetime.strptime(a.date, '%Y-%m-%d').date() >= cutoff_date
        ]
