import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')

class TestNewsEndpoint:
    def test_get_all_news(self):
        response = requests.get(f"{BASE_URL}/api/news")
        assert response.status_code == 200
        data = response.json()
        assert "news" in data
        assert data["count"] > 0
    
    def test_news_pagination(self):
        response = requests.get(f"{BASE_URL}/api/news", params={"page": 2})
        assert response.status_code == 200
        assert "news" in response.json()
