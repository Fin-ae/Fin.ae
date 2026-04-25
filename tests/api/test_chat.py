"""Chat endpoint tests — POST /api/chat/message and POST /api/chat/open"""

import uuid
import requests


def _new_session():
    return f"test_{uuid.uuid4().hex[:10]}"


class TestAvatarChat:
    def test_message_returns_200(self, base_url):
        r = requests.post(f"{base_url}/api/chat/message",
                          json={"session_id": _new_session(), "message": "Hello"})
        assert r.status_code == 200

    def test_response_shape(self, base_url):
        sid = _new_session()
        data = requests.post(f"{base_url}/api/chat/message",
                             json={"session_id": sid, "message": "Hello"}).json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == sid

    def test_response_is_non_empty_string(self, base_url):
        data = requests.post(f"{base_url}/api/chat/message",
                             json={"session_id": _new_session(), "message": "I need health insurance"}).json()
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    def test_conversation_context_persists(self, base_url):
        sid = _new_session()
        requests.post(f"{base_url}/api/chat/message",
                      json={"session_id": sid, "message": "My name is Sara"})
        r2 = requests.post(f"{base_url}/api/chat/message",
                           json={"session_id": sid, "message": "I earn 12000 AED"})
        assert r2.status_code == 200
        assert len(r2.json()["response"]) > 0

    def test_independent_sessions_are_isolated(self, base_url):
        sid_a = _new_session()
        sid_b = _new_session()
        requests.post(f"{base_url}/api/chat/message",
                      json={"session_id": sid_a, "message": "I need a home loan"})
        r_b = requests.post(f"{base_url}/api/chat/message",
                            json={"session_id": sid_b, "message": "Hello"})
        assert r_b.status_code == 200


class TestOpenChat:
    def test_open_chat_returns_200(self, base_url):
        r = requests.post(f"{base_url}/api/chat/open",
                          json={"session_id": _new_session(), "message": "What is a sukuk?"})
        assert r.status_code == 200

    def test_response_shape(self, base_url):
        sid = _new_session()
        data = requests.post(f"{base_url}/api/chat/open",
                             json={"session_id": sid, "message": "Tell me about UAE savings accounts"}).json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == sid

    def test_response_is_non_empty(self, base_url):
        data = requests.post(f"{base_url}/api/chat/open",
                             json={"session_id": _new_session(),
                                   "message": "What are the benefits of saving in UAE?"}).json()
        assert len(data["response"]) > 0

    def test_open_chat_context_persists_across_turns(self, base_url):
        sid = _new_session()
        requests.post(f"{base_url}/api/chat/open",
                      json={"session_id": sid, "message": "Tell me about credit cards"})
        r2 = requests.post(f"{base_url}/api/chat/open",
                           json={"session_id": sid, "message": "What about cashback options?"})
        assert r2.status_code == 200
        assert len(r2.json()["response"]) > 0


class TestExtractProfile:
    def test_no_conversation_returns_404(self, base_url):
        r = requests.post(f"{base_url}/api/chat/extract-profile",
                          json={"session_id": f"ghost_{uuid.uuid4().hex}"})
        assert r.status_code == 404

    def test_extract_after_conversation(self, base_url):
        import time
        sid = _new_session()
        for msg in ["I need health insurance", "I am 30 years old", "I earn 20000 AED"]:
            requests.post(f"{base_url}/api/chat/message", json={"session_id": sid, "message": msg})
            time.sleep(0.5)

        r = requests.post(f"{base_url}/api/chat/extract-profile", json={"session_id": sid})
        assert r.status_code == 200
        data = r.json()
        assert "profile" in data
        assert "session_id" in data
        assert data["session_id"] == sid
