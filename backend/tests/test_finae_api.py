"""
Fin-ae API Backend Tests
Tests for all API endpoints including:
- Health check
- Policies (CRUD, filtering)
- News
- Chat (avatar and open)
- Profile extraction
- Recommendations
- Policy comparison
- Applications
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session ID for all tests
TEST_SESSION_ID = f"test_session_{uuid.uuid4().hex[:8]}"


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_ok(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "finae-api"
        print("✓ Health endpoint returns ok")


class TestPoliciesEndpoint:
    """Policies endpoint tests - GET /api/policies"""
    
    def test_get_all_policies_returns_12(self):
        """GET /api/policies returns list of 12 financial products"""
        response = requests.get(f"{BASE_URL}/api/policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert "count" in data
        assert data["count"] == 12
        assert len(data["policies"]) == 12
        print(f"✓ GET /api/policies returns {data['count']} policies")
    
    def test_filter_by_insurance_category(self):
        """GET /api/policies?category=insurance returns only insurance policies"""
        response = requests.get(f"{BASE_URL}/api/policies", params={"category": "insurance"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for policy in data["policies"]:
            assert policy["category"] == "insurance"
        print(f"✓ Insurance filter returns {data['count']} insurance policies")
    
    def test_filter_by_loan_category(self):
        """GET /api/policies?category=loan returns only loan policies"""
        response = requests.get(f"{BASE_URL}/api/policies", params={"category": "loan"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for policy in data["policies"]:
            assert policy["category"] == "loan"
        print(f"✓ Loan filter returns {data['count']} loan policies")
    
    def test_filter_by_credit_card_category(self):
        """GET /api/policies?category=credit_card returns only credit card policies"""
        response = requests.get(f"{BASE_URL}/api/policies", params={"category": "credit_card"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for policy in data["policies"]:
            assert policy["category"] == "credit_card"
        print(f"✓ Credit card filter returns {data['count']} credit card policies")
    
    def test_filter_by_sharia_compliant(self):
        """GET /api/policies?sharia_compliant=true returns only sharia compliant policies"""
        response = requests.get(f"{BASE_URL}/api/policies", params={"sharia_compliant": "true"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        for policy in data["policies"]:
            assert policy["sharia_compliant"] == True
        print(f"✓ Sharia compliant filter returns {data['count']} policies")
    
    def test_get_single_policy(self):
        """GET /api/policies/{policy_id} returns single policy"""
        response = requests.get(f"{BASE_URL}/api/policies/ins-001")
        assert response.status_code == 200
        data = response.json()
        assert "policy" in data
        assert data["policy"]["policy_id"] == "ins-001"
        assert data["policy"]["name"] == "ADNIC Premium Health Cover"
        print("✓ GET /api/policies/ins-001 returns correct policy")
    
    def test_get_nonexistent_policy_returns_404(self):
        """GET /api/policies/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/policies/nonexistent-policy")
        assert response.status_code == 404
        print("✓ Nonexistent policy returns 404")


class TestNewsEndpoint:
    """News endpoint tests - GET /api/news"""
    
    def test_get_all_news_returns_6(self):
        """GET /api/news returns list of 6 news articles"""
        response = requests.get(f"{BASE_URL}/api/news")
        assert response.status_code == 200
        data = response.json()
        assert "news" in data
        assert "count" in data
        assert data["count"] == 6
        assert len(data["news"]) == 6
        # Verify news structure
        for article in data["news"]:
            assert "news_id" in article
            assert "title" in article
            assert "summary" in article
            assert "category" in article
            assert "date" in article
            assert "source" in article
        print(f"✓ GET /api/news returns {data['count']} news articles")
    
    def test_news_filter_by_category(self):
        """GET /api/news?category=banking returns filtered news"""
        response = requests.get(f"{BASE_URL}/api/news", params={"category": "banking"})
        assert response.status_code == 200
        data = response.json()
        for article in data["news"]:
            assert article["category"] == "banking"
        print(f"✓ News category filter works, returned {data['count']} articles")


class TestChatMessageEndpoint:
    """Chat message endpoint tests - POST /api/chat/message"""
    
    def test_chat_message_sends_and_receives_response(self):
        """POST /api/chat/message with session_id and message returns AI response"""
        payload = {
            "session_id": TEST_SESSION_ID,
            "message": "Hello, I'm looking for health insurance"
        }
        response = requests.post(f"{BASE_URL}/api/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == TEST_SESSION_ID
        assert len(data["response"]) > 0
        print(f"✓ Chat message returns AI response (length: {len(data['response'])} chars)")
    
    def test_chat_message_maintains_conversation(self):
        """POST /api/chat/message maintains conversation context"""
        session_id = f"test_conv_{uuid.uuid4().hex[:8]}"
        
        # First message
        payload1 = {"session_id": session_id, "message": "My name is Ahmed"}
        response1 = requests.post(f"{BASE_URL}/api/chat/message", json=payload1)
        assert response1.status_code == 200
        
        # Second message - should remember context
        payload2 = {"session_id": session_id, "message": "I earn 15000 AED monthly"}
        response2 = requests.post(f"{BASE_URL}/api/chat/message", json=payload2)
        assert response2.status_code == 200
        assert len(response2.json()["response"]) > 0
        print("✓ Chat maintains conversation context")


class TestExtractProfileEndpoint:
    """Profile extraction endpoint tests - POST /api/chat/extract-profile"""
    
    def test_extract_profile_from_conversation(self):
        """POST /api/chat/extract-profile extracts user profile from conversation"""
        # First create a conversation with profile info
        session_id = f"test_profile_{uuid.uuid4().hex[:8]}"
        
        # Send messages to build profile
        messages = [
            "Hi, I'm looking for insurance",
            "My name is Ahmed and I'm 35 years old",
            "I earn 20000 AED per month and I'm a UAE resident"
        ]
        
        for msg in messages:
            requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_id,
                "message": msg
            })
            time.sleep(1)  # Wait for LLM response
        
        # Extract profile
        response = requests.post(f"{BASE_URL}/api/chat/extract-profile", json={
            "session_id": session_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "session_id" in data
        print(f"✓ Profile extraction works, completeness: {data['profile'].get('completeness_score', 'N/A')}%")
    
    def test_extract_profile_no_conversation_returns_404(self):
        """POST /api/chat/extract-profile with no conversation returns 404"""
        response = requests.post(f"{BASE_URL}/api/chat/extract-profile", json={
            "session_id": f"nonexistent_{uuid.uuid4().hex}"
        })
        assert response.status_code == 404
        print("✓ Extract profile with no conversation returns 404")


class TestRecommendEndpoint:
    """Recommendations endpoint tests - POST /api/policies/recommend"""
    
    def test_recommend_without_profile_returns_404(self):
        """POST /api/policies/recommend without profile returns 404"""
        response = requests.post(f"{BASE_URL}/api/policies/recommend", json={
            "session_id": f"no_profile_{uuid.uuid4().hex}"
        })
        assert response.status_code == 404
        print("✓ Recommend without profile returns 404")


class TestCompareEndpoint:
    """Policy comparison endpoint tests - POST /api/policies/compare"""
    
    def test_compare_two_policies(self):
        """POST /api/policies/compare with 2 policy_ids returns comparison data"""
        payload = {"policy_ids": ["ins-001", "ins-002"]}
        response = requests.post(f"{BASE_URL}/api/policies/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["policies"]) == 2
        # Verify both policies are returned
        policy_ids = [p["policy_id"] for p in data["policies"]]
        assert "ins-001" in policy_ids
        assert "ins-002" in policy_ids
        print("✓ Compare 2 policies returns comparison data")
    
    def test_compare_three_policies(self):
        """POST /api/policies/compare with 3 policy_ids works"""
        payload = {"policy_ids": ["ins-001", "ins-002", "loan-001"]}
        response = requests.post(f"{BASE_URL}/api/policies/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        print("✓ Compare 3 policies works")
    
    def test_compare_less_than_two_returns_400(self):
        """POST /api/policies/compare with <2 policies returns 400"""
        payload = {"policy_ids": ["ins-001"]}
        response = requests.post(f"{BASE_URL}/api/policies/compare", json=payload)
        assert response.status_code == 400
        print("✓ Compare with <2 policies returns 400")
    
    def test_compare_more_than_four_returns_400(self):
        """POST /api/policies/compare with >4 policies returns 400"""
        payload = {"policy_ids": ["ins-001", "ins-002", "ins-003", "loan-001", "loan-002"]}
        response = requests.post(f"{BASE_URL}/api/policies/compare", json=payload)
        assert response.status_code == 400
        print("✓ Compare with >4 policies returns 400")


class TestApplicationsEndpoint:
    """Applications endpoint tests - POST/GET /api/applications"""
    
    def test_create_application(self):
        """POST /api/applications creates an application"""
        session_id = f"test_app_{uuid.uuid4().hex[:8]}"
        payload = {
            "session_id": session_id,
            "policy_id": "ins-001",
            "user_profile": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+971501234567",
                "age": 30,
                "nationality": "UAE",
                "monthly_salary": 15000,
                "employment_type": "salaried"
            }
        }
        response = requests.post(f"{BASE_URL}/api/applications", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "application" in data
        app = data["application"]
        assert "application_id" in app
        assert app["session_id"] == session_id
        assert app["policy_id"] == "ins-001"
        assert app["status"] == "submitted"
        assert "status_history" in app
        print(f"✓ Application created with ID: {app['application_id']}")
        return session_id, app["application_id"]
    
    def test_get_applications_for_session(self):
        """GET /api/applications/{session_id} returns applications for session"""
        # First create an application
        session_id = f"test_get_app_{uuid.uuid4().hex[:8]}"
        payload = {
            "session_id": session_id,
            "policy_id": "loan-001",
            "user_profile": {"name": "Test User", "email": "test@example.com"}
        }
        create_response = requests.post(f"{BASE_URL}/api/applications", json=payload)
        assert create_response.status_code == 200
        
        # Get applications
        response = requests.get(f"{BASE_URL}/api/applications/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "count" in data
        assert data["count"] >= 1
        # Verify the created application is in the list
        app_ids = [a["policy_id"] for a in data["applications"]]
        assert "loan-001" in app_ids
        print(f"✓ GET applications returns {data['count']} applications for session")
    
    def test_get_applications_empty_session(self):
        """GET /api/applications/{session_id} returns empty list for new session"""
        response = requests.get(f"{BASE_URL}/api/applications/empty_session_{uuid.uuid4().hex}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["applications"] == []
        print("✓ Empty session returns empty applications list")
    
    def test_create_application_invalid_policy_returns_404(self):
        """POST /api/applications with invalid policy_id returns 404"""
        payload = {
            "session_id": "test_session",
            "policy_id": "invalid-policy-id",
            "user_profile": {"name": "Test"}
        }
        response = requests.post(f"{BASE_URL}/api/applications", json=payload)
        assert response.status_code == 404
        print("✓ Application with invalid policy returns 404")


class TestOpenChatEndpoint:
    """Open chat endpoint tests - POST /api/chat/open"""
    
    def test_open_chat_works(self):
        """POST /api/chat/open works for open-ended chat"""
        payload = {
            "session_id": f"open_chat_{uuid.uuid4().hex[:8]}",
            "message": "What are the benefits of saving in UAE?"
        }
        response = requests.post(f"{BASE_URL}/api/chat/open", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert len(data["response"]) > 0
        print(f"✓ Open chat returns response (length: {len(data['response'])} chars)")
    
    def test_open_chat_maintains_context(self):
        """POST /api/chat/open maintains conversation context"""
        session_id = f"open_context_{uuid.uuid4().hex[:8]}"
        
        # First message
        response1 = requests.post(f"{BASE_URL}/api/chat/open", json={
            "session_id": session_id,
            "message": "Tell me about credit cards in UAE"
        })
        assert response1.status_code == 200
        
        # Follow-up
        response2 = requests.post(f"{BASE_URL}/api/chat/open", json={
            "session_id": session_id,
            "message": "What about cashback options?"
        })
        assert response2.status_code == 200
        assert len(response2.json()["response"]) > 0
        print("✓ Open chat maintains conversation context")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
