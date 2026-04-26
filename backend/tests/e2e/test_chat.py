import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')
TEST_SESSION_ID = f"test_session_{uuid.uuid4().hex[:8]}"

class TestChatEndpoint:
    def test_chat_message(self):
        payload = {"session_id": TEST_SESSION_ID, "message": "Hello"}
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        assert "response" in response.json()

    def test_open_chat(self):
        payload = {"session_id": f"open_{TEST_SESSION_ID}", "message": "What is saving?"}
        response = requests.post(f"{BASE_URL}/api/chat/open", json=payload)
        assert response.status_code == 200
        assert "response" in response.json()
