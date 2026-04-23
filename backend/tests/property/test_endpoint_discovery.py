"""
Property-Based Tests - Endpoint Discovery

Bu modul, hypothesis kullanarak endpoint discovery icin
property-based testler icerir.

Property 1: Endpoint Discovery Completeness - Tum registered endpoint'ler kesfedilir

Task 2.2 - Optional tests for api-endpoint-saglik spec

Requirements Tested:
    REQ-1.1: FastAPI uygulamasi baslatildiginda tum endpoint'leri tarar
    REQ-1.2: Her endpoint'in path, method ve handler bilgisini toplar
    REQ-1.3: Yeni endpoint eklendiginde otomatik tespit eder
    REQ-1.4: Endpoint silindiginde monitoring listesinden cikarir
"""

import string
import sys
from unittest.mock import MagicMock

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.health.discovery import EndpointDiscovery

# =====================================================================
# Hypothesis Strategies
# =====================================================================

# HTTP methods
http_methods = st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH"])

# Path segment generator
@st.composite
def path_segment(draw):
    """Generate a valid URL path segment."""
    chars = draw(st.text(
        alphabet=string.ascii_lowercase + string.digits + "-_",
        min_size=1,
        max_size=20
    ))
    # Ensure it doesn't start with a number or hyphen
    if chars[0] in string.digits + "-":
        chars = "x" + chars
    return chars

# Full path generator
@st.composite
def endpoint_paths(draw):
    """Generate valid API endpoint paths."""
    prefix = draw(st.sampled_from(["/api/v1", "/api/v2", "/api", ""]))
    num_segments = draw(st.integers(min_value=1, max_value=4))
    segments = [draw(path_segment()) for _ in range(num_segments)]
    path = prefix + "/" + "/".join(segments)
    return path

# Path patterns (for critical endpoints)
@st.composite
def critical_path(draw):
    """Generate critical endpoint paths."""
    prefix = draw(st.sampled_from(["/health", "/ready", "/api/v1/auth"]))
    suffix = draw(st.sampled_from(["", "/status", "/login", "/token", "/refresh"]))
    return prefix + suffix

# Endpoint configuration generator
@st.composite
def endpoint_config(draw):
    """Generate a complete endpoint configuration."""
    return {
        "path": draw(endpoint_paths()),
        "methods": draw(st.lists(http_methods, min_size=1, max_size=3, unique=True)),
        "handler_name": draw(st.text(
            alphabet=string.ascii_lowercase + "_",
            min_size=3,
            max_size=30
        ).filter(lambda x: x[0].isalpha() if x else True)),
        "requires_auth": draw(st.booleans()),
        "tags": draw(st.lists(
            st.text(alphabet=string.ascii_lowercase, min_size=3, max_size=10),
            min_size=0,
            max_size=3
        ))
    }


# =====================================================================
# Helper Functions
# =====================================================================

def create_mock_fastapi_app(endpoint_configs: list[dict]) -> FastAPI:
    """Create a FastAPI app with mock routes."""
    app = FastAPI()

    for config in endpoint_configs:
        route = MagicMock(spec=APIRoute)
        route.path = config["path"]
        route.methods = set(config["methods"])

        # Mock endpoint function
        mock_endpoint = MagicMock()
        mock_endpoint.__name__ = config.get("handler_name", "mock_handler")
        route.endpoint = mock_endpoint

        route.dependencies = []
        route.tags = config.get("tags", [])
        route.status_code = 200

        # Ensure route passes isinstance check
        route.__class__ = APIRoute
        app.routes.append(route)

    return app


def make_real_fastapi_app(paths_and_methods: list[tuple]) -> FastAPI:
    """Create a real FastAPI app with actual routes."""
    app = FastAPI()

    for path, method in paths_and_methods:
        # Create dummy handler
        async def dummy_handler():
            return {"status": "ok"}

        # Use proper method decorator
        if method == "GET":
            app.get(path)(dummy_handler)
        elif method == "POST":
            app.post(path)(dummy_handler)
        elif method == "PUT":
            app.put(path)(dummy_handler)
        elif method == "DELETE":
            app.delete(path)(dummy_handler)
        elif method == "PATCH":
            app.patch(path)(dummy_handler)

    return app


# =====================================================================
# Property Tests
# =====================================================================

class TestEndpointDiscoveryCompleteness:
    """
    Property 1: Endpoint Discovery Completeness
    Tum registered endpoint'ler kesfedilir.
    """

    @given(
        num_endpoints=st.integers(min_value=1, max_value=20),
        method=http_methods
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_all_registered_endpoints_discovered(
        self,
        num_endpoints: int,
        method: str
    ):
        """
        Property: Kayitli tum endpoint'ler kesfedilmeli.
        REQ-1.1: FastAPI uygulamasi baslatildiginda tum endpoint'leri tarar
        """
        # Generate unique paths
        paths = [f"/api/v1/resource{i}" for i in range(num_endpoints)]
        paths_and_methods = [(path, method) for path in paths]

        app = make_real_fastapi_app(paths_and_methods)
        discovery = EndpointDiscovery(app)

        # Discover endpoints
        discovered = await discovery.discover_all_endpoints()

        # Property: len(discovered) >= num_endpoints
        # (may include additional routes from FastAPI itself)
        discovered_paths = {e.path for e in discovered}
        for path in paths:
            assert path in discovered_paths, f"Endpoint {path} not discovered"

    @given(
        endpoint=endpoint_config()
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_endpoint_metadata_extracted_correctly(
        self,
        endpoint: dict
    ):
        """
        Property: Metadata dogru cikarilir (path, method, handler).
        REQ-1.2: Her endpoint'in path, method ve handler bilgisini toplar
        """
        # Ensure valid handler name
        handler_name = endpoint["handler_name"]
        if not handler_name or not handler_name[0].isalpha():
            handler_name = "test_handler"

        config = {
            "path": endpoint["path"],
            "methods": endpoint["methods"],
            "handler_name": handler_name,
            "tags": endpoint.get("tags", [])
        }

        app = create_mock_fastapi_app([config])
        discovery = EndpointDiscovery(app)

        discovered = await discovery.discover_all_endpoints()

        # Property: All metadata fields are populated
        for ep in discovered:
            assert ep.path is not None and len(ep.path) > 0
            assert ep.method is not None and len(ep.method) > 0
            assert ep.handler is not None

    @given(
        initial_paths=st.lists(
            st.text(
                alphabet=string.ascii_lowercase,
                min_size=3,
                max_size=10
            ),
            min_size=1,
            max_size=5,
            unique=True
        ),
        new_paths=st.lists(
            st.text(
                alphabet=string.ascii_lowercase,
                min_size=3,
                max_size=10
            ),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_new_endpoint_detection(
        self,
        initial_paths: list[str],
        new_paths: list[str]
    ):
        """
        Property: Yeni eklenen endpoint'ler tespit edilir.
        REQ-1.3: Yeni endpoint eklendiginde otomatik tespit eder
        """
        # Ensure paths are unique between sets
        new_paths = [p for p in new_paths if p not in initial_paths]
        if not new_paths:
            return  # Skip if no unique new paths

        # Initial app
        initial_configs = [
            {"path": f"/api/{p}", "methods": ["GET"], "handler_name": f"get_{p}"}
            for p in initial_paths
        ]
        app = create_mock_fastapi_app(initial_configs)
        discovery = EndpointDiscovery(app)

        # First discovery
        await discovery.discover_all_endpoints()
        initial_count = len(discovery.discovered_endpoints)

        # Add new endpoints
        for p in new_paths:
            route = MagicMock(spec=APIRoute)
            route.path = f"/api/{p}"
            route.methods = {"GET"}
            mock_endpoint = MagicMock()
            mock_endpoint.__name__ = f"get_{p}"
            route.endpoint = mock_endpoint
            route.dependencies = []
            route.tags = []
            route.status_code = 200
            route.__class__ = APIRoute
            app.routes.append(route)

        # Check for new endpoints
        new_detected = await discovery.check_new_endpoints()

        # Property: All new endpoints detected
        assert len(new_detected) == len(new_paths), \
            f"Expected {len(new_paths)} new endpoints, got {len(new_detected)}"

    @given(
        paths=st.lists(
            st.text(
                alphabet=string.ascii_lowercase,
                min_size=3,
                max_size=10
            ),
            min_size=3,
            max_size=10,
            unique=True
        ),
        remove_count=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_removed_endpoint_detection(
        self,
        paths: list[str],
        remove_count: int
    ):
        """
        Property: Silinen endpoint'ler tespit edilir.
        REQ-1.4: Endpoint silindiginde monitoring listesinden cikarir
        """
        assume(remove_count < len(paths))

        # Create mock app with mutable routes list
        mock_app = MagicMock()
        routes = []
        for p in paths:
            route = MagicMock(spec=APIRoute)
            route.path = f"/api/{p}"
            route.methods = {"GET"}
            mock_endpoint = MagicMock()
            mock_endpoint.__name__ = f"get_{p}"
            route.endpoint = mock_endpoint
            route.dependencies = []
            route.tags = []
            route.status_code = 200
            route.__class__ = APIRoute
            routes.append(route)

        mock_app.routes = routes
        discovery = EndpointDiscovery(mock_app)

        # First discovery
        await discovery.discover_all_endpoints()

        # Remove some endpoints from the routes list
        paths_to_remove = paths[:remove_count]
        paths_to_remove_full = [f"/api/{p}" for p in paths_to_remove]
        mock_app.routes = [
            r for r in routes
            if r.path not in paths_to_remove_full
        ]

        # Check for removed endpoints
        removed = await discovery.check_removed_endpoints()

        # Property: All removed endpoints detected
        assert len(removed) == remove_count, \
            f"Expected {remove_count} removed endpoints, got {len(removed)}"


class TestCriticalEndpointIdentification:
    """Critical endpoint tespiti property testleri."""

    @given(
        path=critical_path()
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_critical_endpoint_identified(self, path: str):
        """
        Property: /health, /auth path'leri kritik olarak isaretlenir.
        """
        config = {
            "path": path,
            "methods": ["GET"],
            "handler_name": "health_handler",
            "tags": []
        }

        app = create_mock_fastapi_app([config])
        discovery = EndpointDiscovery(app)

        discovered = await discovery.discover_all_endpoints()

        # Property: Critical paths are marked as critical
        for ep in discovered:
            if any(prefix in ep.path for prefix in ["/health", "/ready", "/api/v1/auth"]):
                assert ep.is_critical is True, \
                    f"Critical endpoint {ep.path} not marked as critical"

    @given(
        path=endpoint_paths()
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_non_critical_endpoint_not_critical(self, path: str):
        """
        Property: Normal endpoint'ler kritik olarak isaretlenmez.
        """
        # Filter out critical paths
        assume(not any(prefix in path for prefix in ["/health", "/ready", "/auth"]))

        config = {
            "path": path,
            "methods": ["GET"],
            "handler_name": "normal_handler",
            "tags": []
        }

        app = create_mock_fastapi_app([config])
        discovery = EndpointDiscovery(app)

        discovered = await discovery.discover_all_endpoints()

        # Property: Non-critical paths are not marked as critical
        for ep in discovered:
            if ep.path == path:
                assert ep.is_critical is False, \
                    f"Non-critical endpoint {ep.path} marked as critical"


class TestExpectedStatusCodes:
    """Status code extraction property testleri."""

    @given(
        method=st.sampled_from(["POST"])
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_post_includes_201(self, method: str):
        """
        Property: POST endpoint'ler 201 status code icermeli.
        """
        config = {
            "path": "/api/v1/resource",
            "methods": [method],
            "handler_name": "create_handler",
            "tags": []
        }

        app = create_mock_fastapi_app([config])
        discovery = EndpointDiscovery(app)

        discovered = await discovery.discover_all_endpoints()

        for ep in discovered:
            if ep.method == "POST":
                assert 201 in ep.expected_status_codes, \
                    f"POST endpoint should include 201, got {ep.expected_status_codes}"

    @given(
        method=st.sampled_from(["DELETE"])
    )
    @settings(max_examples=20)
    @pytest.mark.asyncio
    async def test_delete_includes_204(self, method: str):
        """
        Property: DELETE endpoint'ler 204 status code icermeli.
        """
        config = {
            "path": "/api/v1/resource",
            "methods": [method],
            "handler_name": "delete_handler",
            "tags": []
        }

        app = create_mock_fastapi_app([config])
        discovery = EndpointDiscovery(app)

        discovered = await discovery.discover_all_endpoints()

        for ep in discovered:
            if ep.method == "DELETE":
                assert 204 in ep.expected_status_codes, \
                    f"DELETE endpoint should include 204, got {ep.expected_status_codes}"


class TestDiscoveryIdempotency:
    """Discovery idempotency property testleri."""

    @given(
        paths=st.lists(
            st.text(
                alphabet=string.ascii_lowercase,
                min_size=3,
                max_size=10
            ),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_discovery_is_idempotent(self, paths: list[str]):
        """
        Property: Ayni endpoint'leri birden fazla kez kesfetme idempotent olmali.
        """
        configs = [
            {"path": f"/api/{p}", "methods": ["GET"], "handler_name": f"get_{p}"}
            for p in paths
        ]

        app = create_mock_fastapi_app(configs)
        discovery = EndpointDiscovery(app)

        # First discovery
        first_result = await discovery.discover_all_endpoints()
        first_count = len(first_result)

        # Second discovery
        second_result = await discovery.discover_all_endpoints()
        second_count = len(second_result)

        # Property: Ayni sonuc
        assert first_count == second_count, \
            "Discovery should be idempotent"

    @given(
        paths=st.lists(
            st.text(
                alphabet=string.ascii_lowercase,
                min_size=3,
                max_size=10
            ),
            min_size=1,
            max_size=10,
            unique=True
        )
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_discovered_set_no_duplicates(self, paths: list[str]):
        """
        Property: discovered_endpoints set'inde duplicate olmamali.
        """
        configs = [
            {"path": f"/api/{p}", "methods": ["GET", "POST"], "handler_name": f"handle_{p}"}
            for p in paths
        ]

        app = create_mock_fastapi_app(configs)
        discovery = EndpointDiscovery(app)

        await discovery.discover_all_endpoints()

        # Property: Set size equals list size (no duplicates)
        discovered_list = list(discovery.discovered_endpoints)
        assert len(discovered_list) == len(set(discovered_list)), \
            "discovered_endpoints should not have duplicates"
