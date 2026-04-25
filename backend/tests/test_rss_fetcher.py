"""
Tests for RSSFetcher
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from news.integration.rss_fetcher import RSSFetcher


class TestRSSFetcher:
    """Test RSS fetcher functionality"""

    @pytest.fixture
    def fetcher(self):
        return RSSFetcher()

    @pytest.mark.asyncio
    async def test_init_client(self, fetcher):
        await fetcher.init_client()
        assert fetcher.client is not None
        await fetcher.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.rss_fetcher.httpx.AsyncClient')
    async def test_fetch_feed_success(self, mock_http_client, fetcher):
        # Mock RSS XML response
        mock_rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article</title>
                    <description>Test description</description>
                    <link>https://test.com/article</link>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.return_value = None
        mock_response_obj.text = mock_rss_xml

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response_obj
        mock_http_client.return_value = mock_client_instance

        await fetcher.init_client()
        xml_result = await fetcher.fetch_feed("https://test.com/rss")
        assert isinstance(xml_result, str)
        articles = fetcher.parse_rss(xml_result, "Test Source")
        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["url"] == "https://test.com/article"
        await fetcher.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.rss_fetcher.httpx.AsyncClient')
    async def test_fetch_feed_invalid_xml(self, mock_http_client, fetcher):
        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.return_value = None
        mock_response_obj.text = "Invalid XML"

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response_obj
        mock_http_client.return_value = mock_client_instance

        await fetcher.init_client()
        xml_result = await fetcher.fetch_feed("https://test.com/rss")
        assert isinstance(xml_result, str)
        articles = fetcher.parse_rss(xml_result, "Test Source")
        assert articles == []  # Should handle invalid XML
        await fetcher.close_client()

    @pytest.mark.asyncio
    @patch('news.integration.rss_fetcher.httpx.AsyncClient')
    async def test_fetch_all_feeds(self, mock_http_client, fetcher):
        # Mock multiple feeds
        mock_rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Test Article</title>
                    <description>Test description</description>
                    <link>https://test.com/article</link>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.return_value = None
        mock_response_obj.text = mock_rss_xml

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response_obj
        mock_http_client.return_value = mock_client_instance

        await fetcher.init_client()
        all_articles = await fetcher.fetch_all_feeds()

        assert len(all_articles) > 0  # Should fetch from multiple feeds
        await fetcher.close_client()