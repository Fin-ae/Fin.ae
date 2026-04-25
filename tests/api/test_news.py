"""News endpoint tests — GET /api/news"""

import requests

NEWS_CATEGORIES = ["monetary_policy", "real_estate", "investment", "banking", "insurance", "lending"]
NEWS_REQUIRED_FIELDS = {"news_id", "title", "summary", "category", "date", "source"}


class TestGetAllNews:
    def test_returns_200(self, base_url):
        r = requests.get(f"{base_url}/api/news")
        assert r.status_code == 200

    def test_response_has_required_keys(self, base_url):
        data = requests.get(f"{base_url}/api/news").json()
        assert "news" in data
        assert "count" in data

    def test_seed_count_is_6(self, base_url):
        data = requests.get(f"{base_url}/api/news").json()
        assert data["count"] == 6
        assert len(data["news"]) == 6

    def test_each_article_has_required_fields(self, base_url):
        articles = requests.get(f"{base_url}/api/news").json()["news"]
        for article in articles:
            missing = NEWS_REQUIRED_FIELDS - article.keys()
            assert not missing, f"Article {article.get('news_id')} missing: {missing}"

    def test_dates_are_strings(self, base_url):
        articles = requests.get(f"{base_url}/api/news").json()["news"]
        for article in articles:
            assert isinstance(article["date"], str)

    def test_ids_are_unique(self, base_url):
        articles = requests.get(f"{base_url}/api/news").json()["news"]
        ids = [a["news_id"] for a in articles]
        assert len(ids) == len(set(ids))


class TestNewsCategoryFilter:
    def test_banking_filter(self, base_url):
        data = requests.get(f"{base_url}/api/news", params={"category": "banking"}).json()
        for article in data["news"]:
            assert article["category"] == "banking"

    def test_insurance_filter(self, base_url):
        data = requests.get(f"{base_url}/api/news", params={"category": "insurance"}).json()
        for article in data["news"]:
            assert article["category"] == "insurance"

    def test_unknown_category_returns_empty(self, base_url):
        data = requests.get(f"{base_url}/api/news", params={"category": "sports"}).json()
        assert data["count"] == 0
