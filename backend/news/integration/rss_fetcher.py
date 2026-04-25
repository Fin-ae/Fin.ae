"""
RSS Feed Fetcher for Fin.ae
Alternative news source using RSS feeds for UAE financial news
"""

import asyncio
import httpx
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree as ET
 

logger = logging.getLogger(__name__)

# ─── UAE Financial News RSS Feeds ───────────────────────

UAE_RSS_FEEDS = {
    "gulf_news": "https://www.gulf-news.com/rss/business/",
    "arabian_business": "https://www.arabianbusiness.com/feed/",
    "the_national": "https://www.thenational.ae/rss/",
    "khaleej_times": "https://www.khaleejtimes.com/rss/",
    "emirates_24_7": "https://www.emirates247.com/feeds/",
    "zawya": "https://www.zawya.com/feeds/",
}

REQUEST_TIMEOUT = 15  # seconds


class RSSFetcher:
    """Fetches and parses RSS feeds for financial news"""

    def __init__(self):
        self.client = None
        self.feeds = UAE_RSS_FEEDS

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

    async def fetch_feed(self, feed_url: str) -> Optional[str]:
        """
        Fetch RSS feed content
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            Feed XML content or None if failed
        """
        try:
            await self.init_client()
            response = await self.client.get(feed_url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch feed {feed_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching feed {feed_url}: {e}")
            return None

    def parse_rss(self, xml_content: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Parse RSS feed XML and extract articles
        
        Args:
            xml_content: RSS feed XML content
            source_name: Name of the RSS source
            
        Returns:
            List of parsed articles
        """
        articles = []
        try:
            root = ET.fromstring(xml_content)
            
            # Handle different RSS namespaces
            namespaces = {
                '': 'http://www.rss.org/rss/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'atom': 'http://www.w3.org/2005/Atom',
            }

            # Find all items
            items = root.findall('.//item') or root.findall('.//{http://www.rss.org/rss/}item')
            
            for item in items:
                try:
                    # Extract basic fields
                    title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    description_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
                    pubDate_elem = item.find('pubDate') or item.find('{http://www.w3.org/2005/Atom}published')

                    title = title_elem.text if title_elem is not None and title_elem.text else "No Title"
                    description = description_elem.text if description_elem is not None and description_elem.text else ""
                    link = link_elem.text if link_elem is not None and link_elem.text else link_elem.get('href') if link_elem is not None else ""
                    pub_date = pubDate_elem.text if pubDate_elem is not None and pubDate_elem.text else datetime.now().isoformat()

                    # Parse publication date
                    try:
                        # Try to parse RFC 2822 format (typical RSS)
                        from email.utils import parsedate_to_datetime
                        pub_datetime = parsedate_to_datetime(pub_date)
                        pub_date = pub_datetime.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        try:
                            # Try ISO format
                            pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                            pub_date = pub_datetime.strftime('%Y-%m-%d')
                        except (ValueError, TypeError):
                            pub_date = datetime.now().strftime('%Y-%m-%d')

                    # Clean description (remove HTML tags)
                    description = self._strip_html(description)[:2000]

                    article = {
                        "title": title[:500],
                        "description": description,
                        "url": link,
                        "publishedAt": pub_date,
                        "source": {
                            "name": source_name,
                            "id": source_name.lower().replace(" ", "_")
                        }
                    }

                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Error parsing RSS item from {source_name}: {e}")
                    continue

        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS from {source_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing RSS from {source_name}: {e}")

        return articles

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text"""
        try:
            root = ET.fromstring(f"<root>{text}</root>")
            return ''.join(root.itertext())
        except ET.ParseError:
            # If not valid XML, just remove common HTML tags
            import re
            text = re.sub(r'<[^>]+>', '', text)
            return text

    async def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """
        Fetch and parse all configured RSS feeds
        
        Returns:
            List of all articles from all feeds
        """
        all_articles = []

        try:
            await self.init_client()

            # Fetch all feeds concurrently
            tasks = [self.fetch_feed(url) for url in self.feeds.values()]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for (source_name, feed_url), result in zip(self.feeds.items(), results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching {source_name}: {result}")
                    continue

                if result:
                    articles = self.parse_rss(result, source_name.replace("_", " ").title())
                    all_articles.extend(articles)
                    logger.info(f"Fetched {len(articles)} articles from {source_name}")

        except Exception as e:
            logger.error(f"Error fetching all feeds: {e}")

        return all_articles

    def add_feed(self, name: str, url: str):
        """Add a new RSS feed to the fetcher"""
        self.feeds[name] = url
        logger.info(f"Added RSS feed: {name} -> {url}")

    def remove_feed(self, name: str):
        """Remove an RSS feed from the fetcher"""
        if name in self.feeds:
            del self.feeds[name]
            logger.info(f"Removed RSS feed: {name}")
