"""
Tests for api/agents.py
Tests AI agents API endpoints
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.dependencies import AuthenticatedUser, get_current_user
from models.enums_db import UserRole


@pytest.fixture
def test_app():
    """Create test app with agents router"""

    async def _override_user() -> AuthenticatedUser:
        return AuthenticatedUser(
            id="test-user-1",
            username="tester",
            role=UserRole.STUDENT,
            email=None,
            permissions=[],
            exp=None,
        )

    from api.agents import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = _override_user
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


class TestAgentsTestEndpoint:
    """Test /agents/test endpoint"""

    def test_agents_test_endpoint_exists(self, client):
        """Test /agents/test endpoint exists"""
        response = client.get("/agents/test")
        assert response.status_code == 200

    def test_agents_test_returns_json(self, client):
        """Test /agents/test returns JSON"""
        response = client.get("/agents/test")
        assert response.headers["content-type"] == "application/json"

    def test_agents_test_response_structure(self, client):
        """Test /agents/test response structure"""
        response = client.get("/agents/test")
        data = response.json()

        assert "test" in data
        assert "count" in data

    def test_agents_test_values(self, client):
        """Test /agents/test response values"""
        response = client.get("/agents/test")
        data = response.json()

        assert data["test"] == "ok"
        assert data["count"] == 8


class TestGetAgents:
    """Test /agents endpoint"""

    def test_get_agents_endpoint_exists(self, client):
        """Test /agents endpoint exists"""
        response = client.get("/agents")
        assert response.status_code == 200

    def test_get_agents_returns_list(self, client):
        """Test /agents returns a list"""
        response = client.get("/agents")
        data = response.json()

        assert isinstance(data, list)

    def test_get_agents_not_empty(self, client):
        """Test /agents returns non-empty list"""
        response = client.get("/agents")
        data = response.json()

        assert len(data) > 0

    def test_agent_structure(self, client):
        """Test agent object structure"""
        response = client.get("/agents")
        data = response.json()
        agent = data[0]

        assert "id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "type" in agent
        assert "available" in agent
        assert "specialties" in agent
        assert "model" in agent

    def test_matematik_uzman_agent(self, client):
        """Test matematik uzman agent exists"""
        response = client.get("/agents")
        data = response.json()

        matematik_agent = next((a for a in data if a["id"] == "matematik_uzman"), None)
        assert matematik_agent is not None
        assert matematik_agent["name"] == "Matematik Uzman"
        assert matematik_agent["type"] == "subject_expert"
        assert matematik_agent["available"] is True

    def test_agent_specialties_is_list(self, client):
        """Test agent specialties is a list"""
        response = client.get("/agents")
        data = response.json()
        agent = data[0]

        assert isinstance(agent["specialties"], list)
        assert len(agent["specialties"]) > 0

    def test_agent_uses_gpt4(self, client):
        """Test agent uses GPT-4 model"""
        response = client.get("/agents")
        data = response.json()
        agent = data[0]

        assert agent["model"] == "gpt-4"
