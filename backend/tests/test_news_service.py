"""
Tests for NewsService
"""

import pytest
from unittest.mock import AsyncMock, patch
from news.integration.news_service import NewsService, NewsFilterRequest


class TestNewsService:
    """Test NewsService functionality"""

    @pytest.fixture
    def service(self):
        return NewsService()

    def test_init(self, service):
        assert service.news_store == []
        assert service.cache_ttl == 3600

    def test_seed_mock_data(self, service):
        service.seed_mock_data()
        assert len(service.news_store) > 0
        assert service.last_fetch_time is not None

    @pytest.mark.asyncio
    @patch('news.integration.news_service.NewsClient')
    @patch('news.integration.news_service.RSSFetcher')
    @patch('news.integration.news_service.UAENewsFilter')
    async def test_fetch_live_news_success(self, mock_filter, mock_rss, mock_client, service):
        # Mock NewsClient
        mock_client_instance = AsyncMock()
        mock_client_instance.fetch_and_normalize_news.return_value = [
            {
                "title": "Test NewsAPI Article",
                "description": "Description",
                "source": {"name": "Test Source"},
                "publishedAt": "2024-01-01",
                "url": "https://test.com"
            }
        ]
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client.return_value.__aexit__.return_value = None

        # Mock RSSFetcher
        mock_rss_instance = AsyncMock()
        mock_rss_instance.fetch_all_feeds.return_value = [
            {
                "title": "Test RSS Article",
                "description": "RSS Description",
                "source": "RSS Source",
                "date": "2024-01-01",
                "url": "https://rss.com"
            }
        ]
        mock_rss.return_value.__aenter__.return_value = mock_rss_instance
        mock_rss.return_value.__aexit__.return_value = None

        # Mock UAENewsFilter
        mock_filter_instance = AsyncMock()
        mock_filter_instance.filter_by_uae_relevance.return_value = [
            {
                "title": "Test Filtered Article",
                "description": "Filtered Description",
                "source": "Filtered Source",
                "publishedAt": "2024-01-01",
                "url": "https://filtered.com",
                "uae_relevance_score": 0.8
            }
        ]
        mock_filter_instance.enrich_article.return_value = {
            "title": "Test Enriched Article",
            "description": "Enriched Description",
            "source": "Enriched Source",
            "publishedAt": "2024-01-01",
            "url": "https://enriched.com",
            "uae_entities": ["Test Entity"],
            "locations": ["UAE"],
            "financial_topics": ["banking"]
        }
        mock_filter.return_value = mock_filter_instance

        articles = await service.fetch_live_news()

        assert len(articles) > 0
        assert articles[0]["title"] == "Test Enriched Article"

    @pytest.mark.asyncio
    @patch('news.integration.news_service.NewsClient')
    async def test_fetch_live_news_api_failure(self, mock_client, service):
        # Mock NewsClient to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.fetch_and_normalize_news.side_effect = Exception("API Error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client.return_value.__aexit__.return_value = None

        # Should fall back to mock data
        articles = await service.fetch_live_news()

        assert len(articles) > 0  # Mock data loaded

    def test_get_news_with_filters(self, service):
        service.seed_mock_data()

        # Test category filter
        news_list, total = service.get_news(category="banking", limit=10)
        assert all(article["category"] == "banking" for article in news_list)

        # Test relevance filter
        filtered, total = service.get_news_by_filter(NewsFilterRequest(min_relevance_score=0.9, limit=10))
        assert all(article["relevance_score"] >= 0.9 for article in filtered)

    def test_get_news_pagination(self, service):
        service.seed_mock_data()

        # Test limit and offset
        news_list, total = service.get_news(limit=2, offset=1)
        assert len(news_list) == 2
        assert total == len(service.news_store)