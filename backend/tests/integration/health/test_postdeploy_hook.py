"""
PostDeploy Hook Integration Tests

Bu modul, PostDeployHook sinifi icin integration testlerini icerir.
Task 8.2 - Optional tests for api-endpoint-saglik spec

Requirements Tested:
    REQ-7.1: Deploy sonrasi otomatik tetikleme
    REQ-7.2: Kritik endpoint'lere smoke test
    REQ-7.3: Basarisiz smoke test -> rollback
    REQ-7.4: Basarili smoke test -> full health check
    REQ-7.5: Deployment sonuc raporu
    REQ-7.6: Basarisiz deployment -> incident ticket
"""

import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from httpx import Response

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.hooks.postdeploy_hook import (
    DeploymentReport,
    DeploymentStatus,
    PostDeployHook,
    SmokeTestResult,
)
from app.health.models import EndpointMetadata

# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def mock_critical_endpoints():
    """Mock critical endpoints for smoke testing."""
    return [
        EndpointMetadata(
            path="/health",
            method="GET",
            handler="health_check",
            is_critical=True,
            expected_status_codes=[200]
        ),
        EndpointMetadata(
            path="/api/v1/auth/login",
            method="POST",
            handler="login",
            is_critical=True,
            expected_status_codes=[200, 401]
        ),
    ]


@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    client = AsyncMock()
    client.set = AsyncMock(return_value=True)
    client.lpush = AsyncMock(return_value=1)
    client.ltrim = AsyncMock(return_value=True)
    return client


@pytest.fixture
def postdeploy_hook(mock_redis_client, mock_critical_endpoints):
    """Create PostDeployHook with mocked dependencies."""
    return PostDeployHook(
        base_url="http://localhost:8000",
        redis_client=mock_redis_client,
        critical_endpoints=mock_critical_endpoints,
        timeout=5
    )


# =====================================================================
# Smoke Testing Tests
# =====================================================================

class TestPostDeployHookSmokeTesting:
    """Smoke test execution tests."""

    @pytest.mark.asyncio
    async def test_trigger_creates_deployment_report(self, postdeploy_hook):
        """
        trigger() deployment report olusturmali.
        REQ-7.1: Deploy sonrasi otomatik tetikleme
        """
        with patch.object(postdeploy_hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(postdeploy_hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await postdeploy_hook.trigger(
                    deployment_id="deploy-123",
                    version="1.2.3"
                )

        assert report is not None
        assert isinstance(report, DeploymentReport)
        assert report.deployment_id == "deploy-123"
        assert report.version == "1.2.3"

    @pytest.mark.asyncio
    async def test_trigger_sets_deployment_id_and_version(self, postdeploy_hook):
        """Report'ta deployment_id ve version dogru ayarlanmali."""
        with patch.object(postdeploy_hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = []

            with patch.object(postdeploy_hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await postdeploy_hook.trigger(
                    deployment_id="unique-deploy-id",
                    version="2.0.0-beta"
                )

        assert report.deployment_id == "unique-deploy-id"
        assert report.version == "2.0.0-beta"

    @pytest.mark.asyncio
    async def test_trigger_records_start_time(self, postdeploy_hook):
        """Report'ta start time kaydedilmeli."""
        before = datetime.now(UTC)

        with patch.object(postdeploy_hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = []

            with patch.object(postdeploy_hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await postdeploy_hook.trigger(
                    deployment_id="deploy-123",
                    version="1.0.0"
                )

        after = datetime.now(UTC)

        assert report.started_at is not None
        assert before <= report.started_at <= after

    @pytest.mark.asyncio
    async def test_smoke_tests_run_on_critical_endpoints(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """
        Smoke testler kritik endpoint'lerde calistirilmali.
        REQ-7.2: Kritik endpoint'lere smoke test
        """
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        # Mock httpx client
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock successful responses
            mock_client.get.return_value = Response(200, content=b'{"status": "ok"}')
            mock_client.post.return_value = Response(200, content=b'{"token": "abc"}')

            results = await hook._run_smoke_tests()

        # Her kritik endpoint icin test yapilmali
        assert len(results) == len(mock_critical_endpoints)

        # GET /health cagrilmali
        endpoints_tested = {r.endpoint for r in results}
        assert "/health" in endpoints_tested
        assert "/api/v1/auth/login" in endpoints_tested

    @pytest.mark.asyncio
    async def test_smoke_test_records_response_time(
        self,
        mock_redis_client
    ):
        """Smoke test response time'i kaydeder."""
        endpoint = EndpointMetadata(
            path="/health",
            method="GET",
            handler="health",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = Response(200, content=b'{}')

            results = await hook._run_smoke_tests()

        assert len(results) == 1
        assert results[0].response_time_ms >= 0

    @pytest.mark.asyncio
    async def test_smoke_test_handles_timeout(
        self,
        mock_redis_client
    ):
        """Smoke test timeout'u handle eder."""
        endpoint = EndpointMetadata(
            path="/slow-endpoint",
            method="GET",
            handler="slow_handler",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=1
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")

            results = await hook._run_smoke_tests()

        assert len(results) == 1
        assert results[0].success is False
        assert "Timeout" in results[0].error_message

    @pytest.mark.asyncio
    async def test_smoke_test_handles_connection_error(
        self,
        mock_redis_client
    ):
        """Smoke test connection error'u handle eder."""
        endpoint = EndpointMetadata(
            path="/api/endpoint",
            method="GET",
            handler="handler",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")

            results = await hook._run_smoke_tests()

        assert len(results) == 1
        assert results[0].success is False
        assert "Connection refused" in results[0].error_message


# =====================================================================
# Rollback Tests
# =====================================================================

class TestPostDeployHookRollback:
    """Rollback behavior tests."""

    @pytest.mark.asyncio
    async def test_rollback_triggered_on_smoke_test_failure(
        self,
        mock_redis_client
    ):
        """
        Smoke test basarisiz olunca rollback tetiklenmeli.
        REQ-7.3: Basarisiz smoke test -> rollback
        """
        endpoint = EndpointMetadata(
            path="/health",
            method="GET",
            handler="health",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        rollback_called = []
        async def rollback_callback(deployment_id, version):
            rollback_called.append((deployment_id, version))

        hook.set_rollback_callback(rollback_callback)

        # Mock failing smoke test
        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=False,
                    status_code=500,
                    response_time_ms=100.0,
                    error_message="Internal Server Error"
                )
            ]

            report = await hook.trigger("deploy-123", "1.0.0")

        assert report.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]
        assert len(rollback_called) == 1
        assert rollback_called[0] == ("deploy-123", "1.0.0")

    @pytest.mark.asyncio
    async def test_rollback_callback_executed(
        self,
        mock_redis_client
    ):
        """Rollback callback calistirilmali."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            timeout=5
        )

        rollback_executed = []
        async def rollback_fn(deployment_id, version):
            rollback_executed.append(True)

        hook.set_rollback_callback(rollback_fn)

        report = DeploymentReport(
            deployment_id="deploy-123",
            version="1.0.0",
            status=DeploymentStatus.FAILED,
            started_at=datetime.now(UTC)
        )

        await hook._perform_rollback(report)

        assert len(rollback_executed) == 1
        assert report.rollback_performed is True

    @pytest.mark.asyncio
    async def test_no_rollback_on_success(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """Basarili deployment'ta rollback olmamali."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        rollback_called = []
        async def rollback_callback(deployment_id, version):
            rollback_called.append((deployment_id, version))

        hook.set_rollback_callback(rollback_callback)

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await hook.trigger("deploy-123", "1.0.0")

        assert report.status == DeploymentStatus.SUCCESS
        assert len(rollback_called) == 0


# =====================================================================
# Health Check Tests
# =====================================================================

class TestPostDeployHookHealthCheck:
    """Full health check tests."""

    @pytest.mark.asyncio
    async def test_full_health_check_after_smoke_success(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """
        Basarili smoke test'ten sonra full health check yapilmali.
        REQ-7.4: Basarili smoke test -> full health check
        """
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        health_check_called = []

        async def mock_health_check():
            health_check_called.append(True)
            return True

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', mock_health_check):
                report = await hook.trigger("deploy-123", "1.0.0")

        assert len(health_check_called) == 1
        assert report.health_check_passed is True

    @pytest.mark.asyncio
    async def test_deployment_continues_if_health_check_fails(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """Health check basarisiz olsa da deployment devam eder."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = False

                report = await hook.trigger("deploy-123", "1.0.0")

        # Smoke test basarili -> SUCCESS (health check opsiyonel)
        assert report.status == DeploymentStatus.SUCCESS
        assert report.health_check_passed is False


# =====================================================================
# Reporting Tests
# =====================================================================

class TestPostDeployHookReporting:
    """Deployment reporting tests."""

    @pytest.mark.asyncio
    async def test_report_stored_to_redis(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """
        Deployment raporu Redis'e kaydedilmeli.
        REQ-7.5: Deployment sonuc raporu
        """
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                await hook.trigger("deploy-123", "1.0.0")

        # Redis'e kayit yapilmali
        mock_redis_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_report_contains_all_fields(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """Report tum gerekli alanlari icermeli."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await hook.trigger("deploy-123", "1.0.0")

        # Tum gerekli alanlar mevcut
        report_dict = report.to_dict()
        assert "deployment_id" in report_dict
        assert "version" in report_dict
        assert "status" in report_dict
        assert "started_at" in report_dict
        assert "smoke_test_results" in report_dict
        assert "health_check_passed" in report_dict

    @pytest.mark.asyncio
    async def test_incident_created_on_failure(
        self,
        mock_redis_client
    ):
        """
        Basarisiz deployment'ta incident olusturulmali.
        REQ-7.6: Basarisiz deployment -> incident ticket
        """
        endpoint = EndpointMetadata(
            path="/health",
            method="GET",
            handler="health",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=False,
                    status_code=500,
                    response_time_ms=100.0,
                    error_message="Internal Server Error"
                )
            ]

            await hook.trigger("deploy-123", "1.0.0")

        # Incident listesine eklenmeli
        lpush_calls = mock_redis_client.lpush.call_args_list
        incident_calls = [c for c in lpush_calls if "incidents" in str(c)]
        assert len(incident_calls) > 0

    @pytest.mark.asyncio
    async def test_incident_includes_failed_tests(
        self,
        mock_redis_client
    ):
        """Incident basarisiz testleri icermeli."""
        endpoint = EndpointMetadata(
            path="/failing-endpoint",
            method="POST",
            handler="failing_handler",
            is_critical=True,
            expected_status_codes=[200, 201]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/failing-endpoint",
                    method="POST",
                    success=False,
                    status_code=503,
                    response_time_ms=100.0,
                    error_message="Service Unavailable"
                )
            ]

            report = await hook.trigger("deploy-123", "1.0.0")

        # Report'ta basarisiz testler olmali
        failed_tests = [r for r in report.smoke_test_results if not r.success]
        assert len(failed_tests) == 1
        assert failed_tests[0].endpoint == "/failing-endpoint"


# =====================================================================
# Callback Tests
# =====================================================================

class TestPostDeployHookCallbacks:
    """Callback execution tests."""

    @pytest.mark.asyncio
    async def test_success_callbacks_executed(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """Basarili deployment'ta success callback'ler calistirilmali."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        success_reports = []
        async def on_success(report):
            success_reports.append(report)

        hook.on_success(on_success)

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                await hook.trigger("deploy-123", "1.0.0")

        assert len(success_reports) == 1
        assert success_reports[0].status == DeploymentStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_failure_callbacks_executed(
        self,
        mock_redis_client
    ):
        """Basarisiz deployment'ta failure callback'ler calistirilmali."""
        endpoint = EndpointMetadata(
            path="/health",
            method="GET",
            handler="health",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        failure_reports = []
        async def on_failure(report):
            failure_reports.append(report)

        hook.on_failure(on_failure)

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=False,
                    status_code=500,
                    response_time_ms=100.0,
                    error_message="Error"
                )
            ]

            await hook.trigger("deploy-123", "1.0.0")

        assert len(failure_reports) == 1
        assert failure_reports[0].status in [
            DeploymentStatus.FAILED,
            DeploymentStatus.ROLLED_BACK
        ]


# =====================================================================
# End-to-End Tests
# =====================================================================

class TestPostDeployHookEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_successful_deployment_workflow(
        self,
        mock_redis_client,
        mock_critical_endpoints
    ):
        """Basarili deployment tam akisi."""
        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=mock_critical_endpoints,
            timeout=5
        )

        workflow_steps = []

        hook.on_success(lambda r: workflow_steps.append("success"))

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                )
            ]

            with patch.object(hook, '_run_full_health_check', new_callable=AsyncMock) as mock_health:
                mock_health.return_value = True

                report = await hook.trigger("deploy-123", "1.0.0")

        # Workflow tamamlanmali
        assert report.status == DeploymentStatus.SUCCESS
        assert report.completed_at is not None
        assert "success" in workflow_steps

    @pytest.mark.asyncio
    async def test_failed_deployment_with_rollback(
        self,
        mock_redis_client
    ):
        """Basarisiz deployment + rollback tam akisi."""
        endpoint = EndpointMetadata(
            path="/health",
            method="GET",
            handler="health",
            is_critical=True,
            expected_status_codes=[200]
        )

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=[endpoint],
            timeout=5
        )

        workflow_steps = []

        async def rollback_cb(deployment_id, version):
            workflow_steps.append("rollback")

        hook.set_rollback_callback(rollback_cb)
        hook.on_failure(lambda r: workflow_steps.append("failure"))

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=False,
                    status_code=503,
                    response_time_ms=100.0,
                    error_message="Service Unavailable"
                )
            ]

            report = await hook.trigger("deploy-123", "1.0.0")

        # Workflow tamamlanmali (rollback dahil)
        assert report.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]
        assert report.rollback_performed is True
        assert "rollback" in workflow_steps
        assert "failure" in workflow_steps

    @pytest.mark.asyncio
    async def test_partial_smoke_test_failure(
        self,
        mock_redis_client
    ):
        """Kismi smoke test basarisizligi - bir endpoint basarisiz."""
        endpoints = [
            EndpointMetadata(
                path="/health",
                method="GET",
                handler="health",
                is_critical=True,
                expected_status_codes=[200]
            ),
            EndpointMetadata(
                path="/api/v1/users",
                method="GET",
                handler="get_users",
                is_critical=True,
                expected_status_codes=[200]
            )
        ]

        hook = PostDeployHook(
            base_url="http://localhost:8000",
            redis_client=mock_redis_client,
            critical_endpoints=endpoints,
            timeout=5
        )

        with patch.object(hook, '_run_smoke_tests', new_callable=AsyncMock) as mock_smoke:
            mock_smoke.return_value = [
                SmokeTestResult(
                    endpoint="/health",
                    method="GET",
                    success=True,
                    status_code=200,
                    response_time_ms=50.0
                ),
                SmokeTestResult(
                    endpoint="/api/v1/users",
                    method="GET",
                    success=False,  # Bu endpoint basarisiz
                    status_code=500,
                    response_time_ms=100.0,
                    error_message="Database error"
                )
            ]

            report = await hook.trigger("deploy-123", "1.0.0")

        # Bir endpoint bile basarisizsa deployment basarisiz olmali
        assert report.status in [DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]
        assert len(report.smoke_test_results) == 2

        passed_count = sum(1 for r in report.smoke_test_results if r.success)
        failed_count = sum(1 for r in report.smoke_test_results if not r.success)
        assert passed_count == 1
        assert failed_count == 1
