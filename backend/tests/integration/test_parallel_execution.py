from unittest.mock import Mock, patch, AsyncMock
import pytest

"""
Test parallel execution capabilities and shared resource isolation
"""
import asyncio
import os
import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
def test_worker_isolation(worker_id):
    """Test that each worker has isolated environment"""
    assert worker_id is not None
    assert isinstance(worker_id, str)
    print(f"Running on worker: {worker_id}")


@pytest.mark.unit
def test_database_isolation(test_database_url, worker_id):
    """Test database isolation between workers"""
    assert worker_id in test_database_url or worker_id == "master"
    assert "test_" in test_database_url
    print(f"Worker {worker_id} database: {test_database_url}")


@pytest.mark.unit
def test_cache_key_isolation(isolated_cache_key, worker_id):
    """Test cache key isolation"""
    base_key = "test_key"
    isolated_key = isolated_cache_key(base_key)

    if worker_id == "master":
        assert isolated_key == f"{base_key}_master"
    else:
        assert worker_id in isolated_key
        assert isolated_key == f"{base_key}_{worker_id}"


@pytest.mark.unit
async def test_async_execution():
    """Test async test execution in parallel"""
    await asyncio.sleep(0.1)  # Simulate async work
    result = await async_calculation()
    assert result == 42


async def async_calculation():
    """Simulated async calculation"""
    await asyncio.sleep(0.01)
    return 42


@pytest.mark.serial
def test_serial_execution():
    """Test that must run serially (not in parallel)"""
    # This test should not run in parallel with others
    temp_file = Path("serial_test_marker.tmp")

    # Check if another serial test is running
    assert not temp_file.exists(), "Another serial test is already running"

    # Create marker file
    temp_file.touch()

    try:
        # Simulate work that requires serial execution
        import time

        time.sleep(0.1)
        assert True
    finally:
        # Clean up marker file
        if temp_file.exists():
            temp_file.unlink()


@pytest.mark.shared_resource
def test_shared_resource_with_isolation(isolated_cache_key):
    """Test shared resource access with proper isolation"""
    shared_resource_key = isolated_cache_key("shared_resource")

    # Simulate shared resource access
    os.environ[f"SHARED_{shared_resource_key}"] = "test_value"

    try:
        value = os.environ.get(f"SHARED_{shared_resource_key}")
        assert value == "test_value"
    finally:
        # Cleanup
        if f"SHARED_{shared_resource_key}" in os.environ:
            del os.environ[f"SHARED_{shared_resource_key}"]


@pytest.mark.unit
def test_environment_variables(worker_id):
    """Test environment variable isolation"""
    test_worker_id = os.environ.get("TEST_WORKER_ID")
    assert test_worker_id == worker_id

    use_test_db = os.environ.get("USE_TEST_DB")
    assert use_test_db == "true"


@pytest.mark.unit
def test_file_isolation():
    """Test file system isolation between workers"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".test") as f:
        f.write("test data")
        temp_path = f.name

    try:
        # Each worker should be able to create and access its own files
        assert Path(temp_path).exists()
        with open(temp_path, "r") as f:
            content = f.read()
        assert content == "test data"
    finally:
        # Cleanup
        if Path(temp_path).exists():
            Path(temp_path).unlink()


@pytest.mark.parametrize("test_id", range(5))
@pytest.mark.unit
def test_parallel_parameter_execution(test_id, worker_id):
    """Test parametrized tests running in parallel"""
    # Each parameter should potentially run on different workers
    assert test_id in range(5)
    assert worker_id is not None
    print(f"Test ID {test_id} running on worker {worker_id}")


@pytest.mark.unit
def test_coverage_collection_in_parallel():
    """Test that coverage is properly collected in parallel execution"""

    # This function should be covered by the coverage report
    def covered_function():
        return "This function should appear in coverage"

    result = covered_function()
    assert result == "This function should appear in coverage"
