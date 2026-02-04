from unittest.mock import Mock, patch, AsyncMock

"""
Async tests for FastAPI endpoints using httpx AsyncClient
"""
import asyncio
import os
import sys

import pytest
from httpx import AsyncClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


class TestAPIEndpointsAsync:
    """Test FastAPI REST endpoints with AsyncClient"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns system info"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "running"
            assert data["version"] == "1.0.0"
            assert "agents" in data
            assert "endpoints" in data
            assert len(data["agents"]) >= 3

    @pytest.mark.asyncio
    async def test_get_agents_endpoint(self):
        """Test get agents endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/agents")
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert len(data["agents"]) >= 3

            # Check agent structure
            for agent in data["agents"]:
                assert "id" in agent
                assert "name" in agent
                assert "description" in agent
                assert "icon" in agent

            # Check specific agents
            agent_ids = [a["id"] for a in data["agents"]]
            assert "learning" in agent_ids
            assert "study" in agent_ids
            assert "exam" in agent_ids

    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self):
        """Test successful chat endpoint request"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "agent": "learning",
                "message": "Test message",
                "session_id": "test_123",
            }

            response = await client.post("/api/chat", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "response" in data
            assert "agent" in data
            assert "timestamp" in data
            assert data["agent"] == "learning"
            assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_endpoint_invalid_agent(self):
        """Test chat endpoint with invalid agent"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {"agent": "invalid_agent", "message": "Test message"}

            response = await client.post("/api/chat", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "Geçersiz ajan" in data["response"]

    @pytest.mark.asyncio
    async def test_chat_endpoint_all_agents(self):
        """Test chat endpoint with all agents"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            agents_to_test = ["learning", "study", "exam"]

            for agent_id in agents_to_test:
                request_data = {
                    "agent": agent_id,
                    "message": f"Test message for {agent_id}",
                }

                response = await client.post("/api/chat", json=request_data)
                assert response.status_code == 200

                data = response.json()
                assert data["agent"] == agent_id
                assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_chat_endpoint_session_storage(self):
        """Test chat endpoint stores messages in session"""
        session_id = "test_session_456"

        # Clear sessions first
        sessions.clear()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send first message
            request_data = {
                "agent": "study",
                "message": "First message",
                "session_id": session_id,
            }
            response = await client.post("/api/chat", json=request_data)
            assert response.status_code == 200

            # Check session storage
            assert session_id in sessions
            assert len(sessions[session_id]) == 2  # User message + agent response
            assert sessions[session_id][0]["role"] == "user"
            assert sessions[session_id][1]["role"] == "agent"

    @pytest.mark.asyncio
    async def test_get_session_endpoint(self):
        """Test get session endpoint"""
        # Setup test session
        session_id = "test_get_789"
        sessions[session_id] = [
            {"role": "user", "content": "Test message"},
            {"role": "agent", "content": "Test response"},
        ]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/sessions/{session_id}")
            assert response.status_code == 200

            data = response.json()
            assert data["session_id"] == session_id
            assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Test get session with non-existent session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/sessions/nonexistent")
            assert response.status_code == 200

            data = response.json()
            assert data["session_id"] == "nonexistent"
            assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_clear_sessions_endpoint(self):
        """Test clear sessions endpoint"""
        # Add some test data
        sessions["test1"] = ["data1"]
        sessions["test2"] = ["data2"]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/clear")
            assert response.status_code == 200

            data = response.json()
            assert "cleared" in data["message"].lower()
            assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_chat_without_session(self):
        """Test chat endpoint without session_id"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {"agent": "exam", "message": "Test without session"}

            response = await client.post("/api/chat", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "response" in data
            assert data["session_id"] is None


class TestLearningPathEndpointsAsync:
    """Test Learning Path API endpoints"""

    @pytest.mark.asyncio
    async def test_create_student_profile(self):
        """Test creating a student profile"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "name": "Test Student",
                "grade": 10,
                "subjects": ["matematik", "fizik"],
                "goals": ["YKS hazırlık"],
                "learning_style": "visual",
                "available_time": 120,
            }

            response = await client.post(
                "/api/learning-path/create-profile", json=request_data
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] == True
            assert "profile" in data
            assert data["profile"]["name"] == "Test Student"
            assert data["profile"]["grade"] == 10

    @pytest.mark.asyncio
    async def test_search_resources(self):
        """Test searching educational resources"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "topic": "Python programlama",
                "learning_style": "VISUAL",
                "level": "BEGINNER",
                "language": "tr",
                "limit": 5,
            }

            response = await client.post(
                "/api/learning-path/search-resources", json=request_data
            )
            assert response.status_code == 200

            data = response.json()
            assert data["success"] == True
            assert "resources" in data
            assert isinstance(data["resources"], list)


class TestRAGEndpointsAsync:
    """Test RAG API endpoints"""

    @pytest.mark.asyncio
    async def test_add_document(self):
        """Test adding document to RAG"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {
                "content": "Test document content for RAG",
                "metadata": {"type": "test", "subject": "math"},
            }

            response = await client.post("/api/rag/add_document", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "success" in data

    @pytest.mark.asyncio
    async def test_search_documents(self):
        """Test searching documents in RAG"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            request_data = {"query": "matematik", "k": 3, "score_threshold": 0.5}

            response = await client.post("/api/rag/search", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert "success" in data
            if data["success"]:
                assert "results" in data

    @pytest.mark.asyncio
    async def test_clear_rag_database(self):
        """Test clearing RAG database"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete("/api/rag/clear")
            assert response.status_code == 200

            data = response.json()
            assert "success" in data


class TestIntegrationAsync:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a full conversation flow with multiple agents"""
        session_id = "integration_test"

        # Clear sessions
        sessions.clear()

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Ask learning agent for a plan
            response = await client.post(
                "/api/chat",
                json={
                    "agent": "learning",
                    "message": "Bana bir öğrenme planı oluştur",
                    "session_id": session_id,
                },
            )
            assert response.status_code == 200

            # Step 2: Ask study agent for help
            response = await client.post(
                "/api/chat",
                json={
                    "agent": "study",
                    "message": "Python nedir?",
                    "session_id": session_id,
                },
            )
            assert response.status_code == 200
            assert len(response.json()["response"]) > 50

            # Step 3: Ask exam agent for a quiz
            response = await client.post(
                "/api/chat",
                json={
                    "agent": "exam",
                    "message": "Quiz oluştur",
                    "session_id": session_id,
                },
            )
            assert response.status_code == 200

            # Step 4: Check session history
            response = await client.get(f"/api/sessions/{session_id}")
            assert response.status_code == 200
            history = response.json()["messages"]
            assert len(history) == 6  # 3 user messages + 3 agent responses

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            tasks = [
                client.post("/api/chat", json={"agent": "learning", "message": "plan"}),
                client.post("/api/chat", json={"agent": "study", "message": "quiz"}),
                client.post("/api/chat", json={"agent": "exam", "message": "sınav"}),
            ]

            responses = await asyncio.gather(*tasks)

            assert len(responses) == 3
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """Test system recovers from errors"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send invalid data
            response = await client.post("/api/chat", json={})
            assert response.status_code == 422  # Validation error

            # System should still work after error
            response = await client.post(
                "/api/chat", json={"agent": "learning", "message": "Test after error"}
            )
            assert response.status_code == 200
            assert len(response.json()["response"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
