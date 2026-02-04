"""
Async API Integration Test - Sprint 3
Tests Celery task integration with FastAPI endpoints

Run: pytest test_async_api_integration.py -v
"""
import pytest
from httpx import AsyncClient
from main import app
from tasks.email_tasks import send_welcome_email
from celery.result import AsyncResult

@pytest.mark.asyncio
async def test_user_creation_with_async_email():
    """
    Test that user creation now returns instantly with email sent in background
    
    BEFORE Sprint 3: ~3s (email blocks response)
    AFTER Sprint 3: ~50ms (email queued, instant response)
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create user - should return instantly
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
            "ad": "Test",
            "soyad": "User",
            "role": "student"
        }
        
        import time
        start_time = time.time()
        
        response = await client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": "Bearer admin_token"}  # Mock auth
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Assert response is fast (< 100ms instead of 3000ms)
        assert duration_ms < 100, f"API response took {duration_ms}ms (should be < 100ms)"
        
        # Assert success
        assert response.status_code == 201
        result = response.json()
        assert result["success"] == True
        
        print(f"PERFORMANCE: User creation API returned in {duration_ms:.2f}ms")
        print(f"IMPROVEMENT: {(3000 - duration_ms) / 3000 * 100:.1f}% faster than before")


@pytest.mark.asyncio
async def test_task_status_api():
    """
    Test task status checking endpoint
    """
    # Queue a test task
    task = send_welcome_email.delay(
        user_email="test@example.com",
        user_name="Test User"
    )
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Check task status
        response = await client.get(f"/api/v1/tasks/{task.id}/status")
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["task_id"] == task.id
        assert result["status"] in ["PENDING", "STARTED", "SUCCESS", "FAILURE"]
        
        print(f"Task Status: {result['status']}")
        

@pytest.mark.asyncio
async def test_active_tasks_listing():
    """
    Test listing active tasks
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks/active")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "active_tasks" in result
        assert "total_count" in result
        assert isinstance(result["active_tasks"], list)
        
        print(f"Active Tasks: {result['total_count']}")


@pytest.mark.asyncio  
async def test_task_stats():
    """
    Test Celery worker statistics endpoint
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks/stats")
        
        assert response.status_code == 200
        result = response.json()
        
        assert "workers" in result
        assert "active_tasks" in result
        assert "scheduled_tasks" in result
        
        print(f"Worker Stats: {result}")


def test_celery_task_execution():
    """
    Test that Celery task actually executes (synchronous test)
    """
    # Send email task
    task = send_welcome_email.delay(
        user_email="test@example.com",
        user_name="Test User"
    )
    
    # Wait for result (max 10 seconds)
    try:
        result = task.get(timeout=10)
        
        assert result["success"] == True
        assert result["email"] == "test@example.com"
        assert "message" in result
        
        print(f"Task Result: {result}")
        
    except Exception as e:
        pytest.fail(f"Task execution failed: {str(e)}")


if __name__ == "__main__":
    print("=" * 80)
    print("SPRINT 3: ASYNC API INTEGRATION TESTS")
    print("=" * 80)
    print()
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
