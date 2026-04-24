"""
UAE News Filtering Module
Implements UAE-specific news filtering and categorization
"""

import logging
from typing import List, Optional, Set
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ─── UAE-Specific Keywords and Entities ───────────────────

class UAEEntity(str, Enum):
    """Major UAE entities and companies"""
    # Banks
    EMIRATES_NBD = "Emirates NBD"
    FAB = "First Abu Dhabi Bank"
    ADIB = "Abu Dhabi Islamic Bank"
    RAK_BANK = "RAK Bank"
    FIB = "Fujairah Islamic Bank"
    DIB = "Dubai Islamic Bank"
    
    # Insurance
    AXA = "AXA"
    ALLIANZ = "Allianz"
    TAKAFUL = "Takaful"
    
    # Real Estate
    EMAAR = "Emaar"
    DAMAC = "DAMAC"
    DEYAAR = "Deyaar"
    REDFIN = "Redfin"
    
    # Government & Regulatory
    CBUAE = "Central Bank of UAE"
    ADGM = "Abu Dhabi Global Market"
    DFSA = "Dubai Financial Services Authority"
    SCA = "Securities and Commodities Authority"


class UAELocation(str, Enum):
    """Major UAE locations for filtering"""
    DUBAI = "Dubai"
    ABU_DHABI = "Abu Dhabi"
    SHARJAH = "Sharjah"
    AJMAN = "Ajman"
    FUJAIRAH = "Fujairah"
    RAS_AL_KHAIMAH = "Ras Al Khaimah"
    UMM_AL_QUWAIN = "Umm Al Quwain"


class NewsFinancialTopic(str, Enum):
    """Financial topics relevant to UAE"""
    INTEREST_RATES = "interest_rates"
    STOCK_MARKET = "stock_market"
    CRYPTOCURRENCY = "cryptocurrency"
    REAL_ESTATE = "real_estate"
    INSURANCE = "insurance"
    BANKING = "banking"
    LENDING = "lending"
    INVESTMENT = "investment"
    TAXATION = "taxation"
    EMPLOYMENT = "employment"
    EXPAT_FINANCE = "expat_finance"
    GOLD_PRICES = "gold_prices"
    OIL_PRICES = "oil_prices"


# ─── UAE Filtering Utility ───────────────────────────────

class UAENewsFilter:
    """Filters and scores news for UAE relevance"""

    def __init__(self):
        self.uae_keywords = self._build_uae_keywords()
        self.location_keywords = self._build_location_keywords()
        self.financial_keywords = self._build_financial_keywords()

    @staticmethod
    def _build_uae_keywords() -> dict:
        """Build UAE entity keywords for matching"""
        return {
            "banks": {
                "Emirates NBD": ["Emirates NBD", "ENBD", "Emirates National Bank"],
                "FAB": ["First Abu Dhabi", "FAB", "NBAD", "NBD"],
                "ADIB": ["Abu Dhabi Islamic", "ADIB"],
                "RAK Bank": ["RAK Bank", "Ras Al Khaimah Bank"],
                "FIB": ["Fujairah Islamic"],
                "DIB": ["Dubai Islamic Bank"],
            },
            "insurance": {
                "AXA": ["AXA Insurance", "AXA"],
                "Allianz": ["Allianz", "Allianz Gulf"],
                "Takaful": ["Takaful", "Islamic insurance"],
                "ENBD Insurance": ["ENBD Insurance"],
            },
            "real_estate": {
                "Emaar": ["Emaar", "Emaar Properties"],
                "DAMAC": ["DAMAC", "DAMAC Properties"],
                "Deyaar": ["Deyaar"],
                "Redfin": ["Redfin"],
            },
            "regulatory": {
                "CBUAE": ["Central Bank of UAE", "CBUAE", "UAE Central Bank"],
                "ADGM": ["Abu Dhabi Global Market", "ADGM"],
                "DFSA": ["Dubai Financial Services Authority", "DFSA"],
                "SCA": ["Securities and Commodities Authority", "SCA"],
                "DFM": ["Dubai Financial Market", "DFM"],
                "ADX": ["Abu Dhabi Securities Exchange", "ADX"],
            }
        }

    @staticmethod
    def _build_location_keywords() -> dict:
        """Build location keywords for filtering"""
        return {
            "Dubai": ["Dubai", "DXB", "Dubai Marina", "Downtown Dubai", "JBR"],
            "Abu Dhabi": ["Abu Dhabi", "AUH", "Yas Island", "Saadiyat"],
            "Sharjah": ["Sharjah", "SHJ"],
            "Ajman": ["Ajman"],
            "Fujairah": ["Fujairah"],
            "Ras Al Khaimah": ["Ras Al Khaimah", "RAK"],
            "Umm Al Quwain": ["Umm Al Quwain"],
        }

    @staticmethod
    def _build_financial_keywords() -> dict:
        """Build financial topic keywords"""
        return {
            "interest_rates": ["interest rate", "base rate", "borrowing cost", "lending rate"],
            "stock_market": ["stock", "equities", "shares", "index", "IPO", "listing"],
            "cryptocurrency": ["Bitcoin", "Ethereum", "crypto", "blockchain", "digital currency"],
            "real_estate": ["property", "real estate", "housing", "rent", "lease", "mortgage"],
            "insurance": ["insurance", "premium", "coverage", "claim", "policy"],
            "banking": ["bank", "banking", "deposit", "account", "ATM"],
            "lending": ["loan", "credit", "borrowing", "financing", "installment"],
            "investment": ["investment", "portfolio", "fund", "securities", "mutual fund"],
            "taxation": ["tax", "VAT", "tariff", "duty", "corporate tax"],
            "employment": ["job", "employment", "salary", "wages", "recruitment"],
            "expat_finance": ["expat", "overseas worker", "remittance", "expatriate"],
            "gold_prices": ["gold", "precious metal", "bullion"],
            "oil_prices": ["oil", "crude", "petroleum", "OPEC"],
        }

    def get_uae_entity_matches(self, text: str) -> List[str]:
        """Extract mentioned UAE entities from text"""
        text_lower = text.lower()
        matches = set()

        for category, entities in self.uae_keywords.items():
            for entity_name, keywords in entities.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        matches.add(entity_name)

        return list(matches)

    def get_location_mentions(self, text: str) -> List[str]:
        """Extract mentioned locations from text"""
        text_lower = text.lower()
        mentions = set()

        for location, keywords in self.location_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    mentions.add(location)

        return list(mentions)

    def get_financial_topics(self, text: str) -> List[str]:
        """Extract financial topics from text"""
        text_lower = text.lower()
        topics = set()

        for topic, keywords in self.financial_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    topics.add(topic)

        return list(topics)

    def calculate_uae_relevance_score(
        self,
        title: str,
        description: str,
        source: str = "",
    ) -> float:
        """
        Calculate UAE relevance score (0-1) for an article
        
        Args:
            title: Article title
            description: Article description
            source: News source name
            
        Returns:
            Relevance score between 0 and 1
        """
        content = f"{title} {description}".lower()
        source_lower = source.lower()
        
        score = 0.0

        # Check for UAE location mentions (high weight)
        locations = self.get_location_mentions(content)
        if locations:
            score += 0.4
        elif "uae" in content or "emirates" in content:
            score += 0.3

        # Check for UAE entities (high weight)
        entities = self.get_uae_entity_matches(content)
        if entities:
            score += 0.3

        # Check for financial topics (medium weight)
        topics = self.get_financial_topics(content)
        if topics:
            score += 0.2

        # Check source reputation for UAE news (low weight)
        uae_sources = [
            "gulf news", "arabian business", "the national",
            "khaleej times", "emirates 24/7", "zawya",
            "insurance business me"
        ]
        if any(src in source_lower for src in uae_sources):
            score += 0.1

        return min(score, 1.0)

    def filter_by_uae_relevance(
        self,
        articles: List[dict],
        min_score: float = 0.3
    ) -> List[dict]:
        """
        Filter articles by UAE relevance score
        
        Args:
            articles: List of articles with 'title', 'description', 'source'
            min_score: Minimum relevance score (0-1)
            
        Returns:
            Filtered list of articles
        """
        filtered = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            source = article.get("source", {}).get("name", "") if isinstance(article.get("source"), dict) else article.get("source", "")

            score = self.calculate_uae_relevance_score(title, description, source)

            if score >= min_score:
                article["uae_relevance_score"] = score
                filtered.append(article)

        # Sort by relevance score
        filtered.sort(key=lambda x: x.get("uae_relevance_score", 0), reverse=True)

        return filtered

    def filter_by_entities(
        self,
        articles: List[dict],
        entities: List[str]
    ) -> List[dict]:
        """Filter articles mentioning specific UAE entities"""
        filtered = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}".lower()

            for entity in entities:
                if entity.lower() in content:
                    filtered.append(article)
                    break

        return filtered

    def filter_by_locations(
        self,
        articles: List[dict],
        locations: List[str]
    ) -> List[dict]:
        """Filter articles mentioning specific locations"""
        filtered = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}".lower()

            for location in locations:
                if location.lower() in content:
                    filtered.append(article)
                    break

        return filtered

    def filter_by_topics(
        self,
        articles: List[dict],
        topics: List[str]
    ) -> List[dict]:
        """Filter articles covering specific financial topics"""
        filtered = []

        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            content = f"{title} {description}".lower()

            article_topics = self.get_financial_topics(content)

            if any(topic in topics for topic in article_topics):
                filtered.append(article)

        return filtered

    def filter_by_date_range(
        self,
        articles: List[dict],
        days: int = 7,
        date_field: str = "publishedAt"
    ) -> List[dict]:
        """Filter articles from last N days"""
        cutoff = (datetime.now() - timedelta(days=days)).date()
        filtered = []

        for article in articles:
            try:
                pub_date_str = article.get(date_field, "")
                if isinstance(pub_date_str, str):
                    pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00")).date()
                else:
                    pub_date = pub_date_str

                if pub_date >= cutoff:
                    filtered.append(article)
            except (ValueError, TypeError, AttributeError):
                # If date parsing fails, include the article
                filtered.append(article)

        return filtered

    def enrich_article(self, article: dict) -> dict:
        """Enrich article with UAE-specific metadata"""
        title = article.get("title", "")
        description = article.get("description", "")
        source = article.get("source", {}).get("name", "") if isinstance(article.get("source"), dict) else article.get("source", "")

        enriched = article.copy()
        enriched["uae_relevance_score"] = self.calculate_uae_relevance_score(title, description, source)
        enriched["uae_entities"] = self.get_uae_entity_matches(f"{title} {description}")
        enriched["locations"] = self.get_location_mentions(f"{title} {description}")
        enriched["financial_topics"] = self.get_financial_topics(f"{title} {description}")

        return enriched
