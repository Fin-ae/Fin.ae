"""
Tests for UAE News Filter
"""

import pytest
from news.integration.uae_filter import UAENewsFilter, UAEEntity


class TestUAENewsFilter:
    """Test UAE news filtering functionality"""

    @pytest.fixture
    def filter_instance(self):
        return UAENewsFilter()

    def test_init(self, filter_instance):
        assert filter_instance.uae_keywords is not None
        assert len(filter_instance.uae_keywords) > 0

    def test_calculate_uae_relevance_high(self, filter_instance):
        title = "Emirates NBD announces new banking services in UAE"
        description = "The UAE bank expands its digital offerings"
        score = filter_instance.calculate_uae_relevance_score(title, description, "Gulf News")
        assert score > 0.7  # High relevance

    def test_calculate_uae_relevance_low(self, filter_instance):
        title = "US bank announces new services"
        description = "American bank expands offerings"
        score = filter_instance.calculate_uae_relevance_score(title, description, "Reuters")
        assert score < 0.3  # Low relevance

    def test_filter_by_uae_relevance(self, filter_instance):
        articles = [
            {"title": "UAE banking news", "description": "UAE content"},
            {"title": "International news", "description": "Non-UAE content"}
        ]

        filtered = filter_instance.filter_by_uae_relevance(articles, min_score=0.5)
        assert len(filtered) == 1
        assert "UAE" in filtered[0]["title"]

    def test_extract_entities(self, filter_instance):
        text = "Emirates NBD and FAB are major UAE banks"
        entities = filter_instance.get_uae_entity_matches(text)

        assert "Emirates NBD" in entities
        assert "FAB" in entities

    def test_enrich_article(self, filter_instance):
        article = {
            "title": "Emirates NBD banking news",
            "description": "UAE banking developments",
            "content": "Emirates NBD announces new services"
        }

        enriched = filter_instance.enrich_article(article)

        assert "uae_entities" in enriched
        assert "locations" in enriched
        assert "financial_topics" in enriched
        assert len(enriched["uae_entities"]) > 0

    def test_categorize_article(self, filter_instance):
        # Test filtering by topics
        banking_article = {
            "title": "Bank interest rates in UAE",
            "description": "Banking news"
        }

        topics = filter_instance.get_financial_topics("Bank interest rates in UAE")
        assert "banking" in topics

    def test_analyze_sentiment(self, filter_instance):
        pass