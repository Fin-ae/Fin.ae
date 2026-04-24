"""
Tests for NewsClient
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from news.integration.news_client import NewsClient, RateLimiter, NewsApiResponse


class TestRateLimiter:
    """Test rate limiter functionality"""

    def test_rate_limiter_init(self):
        limiter = RateLimiter(max_requests=10, window=60)
        assert limiter.max_requests == 10
        assert limiter.window == 60
        assert limiter.requests == []

    def test_rate_limiter_allowed(self):
        limiter = RateLimiter(max_requests=2, window=60)
        assert limiter.is_allowed() == True
        assert limiter.is_allowed() == True
        assert limiter.is_allowed() == False

    def test_rate_limiter_retry_after(self):
        limiter = RateLimiter(max_requests=1, window=60)
        limiter.requests = [datetime.now().timestamp() - 30]  # 30 seconds ago
        assert 29 <= limiter.get_retry_after() <= 30


class TestNewsClient:
    """Test NewsClient functionality"""

    @pytest.fixture
    def client(self):
        return NewsClient(api_key="test_key")

    @pytest.mark.asyncio
    async def test_init_client(self, client):
        await client.init_client()
        assert client.client is not None
        await client.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.news_client.httpx.AsyncClient')
    async def test_fetch_news_success(self, mock_http_client, client):
        # Mock response
        mock_response = {
            "articles": [
                {
                    "title": "Test Article",
                    "description": "Test description",
                    "source": {"name": "Test Source"},
                    "publishedAt": "2024-01-01T00:00:00Z",
                    "url": "https://test.com"
                }
            ],
            "totalResults": 1,
            "status": "ok"
        }

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.return_value = None
        mock_response_obj.json.return_value = mock_response

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response_obj
        mock_http_client.return_value = mock_client_instance

        await client.init_client()
        articles = await client.fetch_news("test query")
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        await client.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.news_client.httpx.AsyncClient')
    async def test_fetch_news_rate_limited(self, mock_http_client, client):
        # Exhaust rate limit
        for _ in range(100):
            client.rate_limiter.is_allowed()

        await client.init_client()
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await client.fetch_news("test query")
        await client.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.news_client.httpx.AsyncClient')
    async def test_fetch_news_api_error(self, mock_http_client, client):
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("API Error")
        mock_http_client.return_value = mock_client_instance

        await client.init_client()
        articles = await client.fetch_news("test query")
        assert articles == []  # Should handle error gracefully
        await client.close_client()

    def test_cache(self, client):
        # Test cache functionality
        key = "test_key"
        assert not client._is_cache_valid(key)

        # Add to cache
        client.cache[key] = {"timestamp": datetime.now().timestamp(), "data": "test"}
        assert client._is_cache_valid(key)

        # Expire cache
        client.cache[key]["timestamp"] = datetime.now().timestamp() - 7200  # 2 hours ago
        assert not client._is_cache_valid(key)