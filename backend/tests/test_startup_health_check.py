"""
Test Startup Health Check - Task 16
Learning Path Video Yükleme Sorunu Çözümü

Startup health check fonksiyonalitesini test eder.

Requirements: 0.1, 0.2, 0.6, 0.7, 1.9, 4.6, 4.9
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from services.health_check_service import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    StartupHealthCheck,
)


@pytest.mark.asyncio
async def test_startup_health_check_all_healthy():
    """Test startup health check when all components are healthy"""

    # Arrange
    service = HealthCheckService()

    # Mock all health check methods to return healthy
    healthy_component = ComponentHealth(
        name="Test Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=healthy_component)
    service._check_cache = AsyncMock(return_value=healthy_component)
    service._check_youtube_api = AsyncMock(return_value=healthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    assert isinstance(result, StartupHealthCheck)
    assert result.success is True
    assert len(result.components) == 3
    assert len(result.warnings) == 0
    assert len(result.errors) == 0
    # Startup time can be 0 in tests with mocks (immediate return)
    assert result.startup_time_ms >= 0
    assert all(c.status == HealthStatus.HEALTHY for c in result.components)


@pytest.mark.asyncio
async def test_startup_health_check_with_degraded():
    """Test startup health check when one component is degraded"""

    # Arrange
    service = HealthCheckService()

    healthy_component = ComponentHealth(
        name="Healthy Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    degraded_component = ComponentHealth(
        name="Degraded Component",
        status=HealthStatus.DEGRADED,
        response_time_ms=100.0,
        error_message="Service degraded",
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=healthy_component)
    service._check_cache = AsyncMock(return_value=degraded_component)
    service._check_youtube_api = AsyncMock(return_value=healthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    assert isinstance(result, StartupHealthCheck)
    assert result.success is True  # Still successful if at least one is healthy
    assert len(result.components) == 3
    assert len(result.warnings) == 1
    assert "degraded" in result.warnings[0].lower()
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_startup_health_check_with_unhealthy():
    """Test startup health check when one component is unhealthy"""

    # Arrange
    service = HealthCheckService()

    healthy_component = ComponentHealth(
        name="Healthy Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    unhealthy_component = ComponentHealth(
        name="Unhealthy Component",
        status=HealthStatus.UNHEALTHY,
        response_time_ms=0.0,
        error_message="Connection failed",
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=healthy_component)
    service._check_cache = AsyncMock(return_value=unhealthy_component)
    service._check_youtube_api = AsyncMock(return_value=healthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    assert isinstance(result, StartupHealthCheck)
    assert result.success is True  # Still successful if at least one is healthy
    assert len(result.components) == 3
    assert len(result.errors) == 1
    assert "unhealthy" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_startup_health_check_all_unhealthy():
    """Test startup health check when all components are unhealthy"""

    # Arrange
    service = HealthCheckService()

    unhealthy_component = ComponentHealth(
        name="Unhealthy Component",
        status=HealthStatus.UNHEALTHY,
        response_time_ms=0.0,
        error_message="Connection failed",
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=unhealthy_component)
    service._check_cache = AsyncMock(return_value=unhealthy_component)
    service._check_youtube_api = AsyncMock(return_value=unhealthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    assert isinstance(result, StartupHealthCheck)
    assert result.success is False  # Failed if all are unhealthy
    assert len(result.components) == 3
    assert len(result.errors) == 3
    assert all(c.status == HealthStatus.UNHEALTHY for c in result.components)


@pytest.mark.asyncio
async def test_startup_health_check_with_exception():
    """Test startup health check when an exception occurs"""

    # Arrange
    service = HealthCheckService()

    healthy_component = ComponentHealth(
        name="Healthy Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=healthy_component)
    service._check_cache = AsyncMock(side_effect=Exception("Connection error"))
    service._check_youtube_api = AsyncMock(return_value=healthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    assert isinstance(result, StartupHealthCheck)
    assert result.success is True  # Still successful if at least one is healthy
    assert len(result.components) == 2  # Only 2 components (cache check failed)
    assert len(result.errors) == 1
    assert "Connection error" in result.errors[0]


@pytest.mark.asyncio
async def test_startup_health_check_to_dict():
    """Test StartupHealthCheck to_dict conversion"""

    # Arrange
    component = ComponentHealth(
        name="Test Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    result = StartupHealthCheck(
        success=True,
        components=[component],
        warnings=["Test warning"],
        errors=[],
        startup_time_ms=100.5,
        timestamp=datetime.now(),
    )

    # Act
    result_dict = result.to_dict()

    # Assert
    assert isinstance(result_dict, dict)
    assert result_dict["success"] is True
    assert len(result_dict["components"]) == 1
    assert result_dict["warnings"] == ["Test warning"]
    assert result_dict["errors"] == []
    assert result_dict["startup_time_ms"] == 100.5
    assert "timestamp" in result_dict


@pytest.mark.asyncio
async def test_startup_health_check_performance():
    """Test that startup health check completes in reasonable time"""

    # Arrange
    service = HealthCheckService()

    healthy_component = ComponentHealth(
        name="Test Component",
        status=HealthStatus.HEALTHY,
        response_time_ms=50.0,
        last_check=datetime.now(),
    )

    service._check_database = AsyncMock(return_value=healthy_component)
    service._check_cache = AsyncMock(return_value=healthy_component)
    service._check_youtube_api = AsyncMock(return_value=healthy_component)

    # Act
    result = await service.startup_health_check()

    # Assert
    # Startup health check should complete in less than 5 seconds
    assert result.startup_time_ms < 5000
    assert result.success is True
