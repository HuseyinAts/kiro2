"""
Test Helpers - Reduce Mock Overuse
===================================
Provides reusable test utilities to reduce excessive mocking in tests.

Instead of sys.modules mocking, use these lightweight helpers:
- FakeDatabase: In-memory data storage
- FakeCache: Dict-based cache
- FakeHTTPClient: Predefined responses
- ServiceStub: Auto-generate service stubs

Usage:
    from tests.utils.test_helpers import FakeDatabase, FakeCache

    def test_something(fake_db):
        fake_db.add_user({"id": "1", "email": "test@test.com"})
        result = await service.get_user("1")
        assert result.email == "test@test.com"
"""
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar
from unittest.mock import MagicMock

T = TypeVar("T")


# ============================================================================
# Fake Database - In-Memory Storage
# ============================================================================


@dataclass
class FakeDatabase:
    """
    In-memory database for fast tests.
    Avoids need for SQLite or PostgreSQL in unit tests.

    Usage:
        db = FakeDatabase()
        db.users.add({"id": "1", "email": "test@example.com"})
        user = db.users.get("1")
    """
    _storage: dict[str, dict[str, Any]] = field(default_factory=dict)

    def collection(self, name: str) -> "FakeCollection":
        """Get or create a collection."""
        if name not in self._storage:
            self._storage[name] = {}
        return FakeCollection(name, self._storage[name])

    @property
    def users(self) -> "FakeCollection":
        return self.collection("users")

    @property
    def questions(self) -> "FakeCollection":
        return self.collection("questions")

    @property
    def exams(self) -> "FakeCollection":
        return self.collection("exams")

    @property
    def learning_paths(self) -> "FakeCollection":
        return self.collection("learning_paths")

    def clear(self) -> None:
        """Clear all data."""
        self._storage.clear()

    def seed(self, collection: str, items: list[dict[str, Any]]) -> None:
        """Bulk add items to a collection."""
        coll = self.collection(collection)
        for item in items:
            coll.add(item)


@dataclass
class FakeCollection:
    """Collection within FakeDatabase."""
    name: str
    _data: dict[str, Any]

    def add(self, item: dict[str, Any]) -> str:
        """Add item, auto-generate ID if missing."""
        item_id = item.get("id") or str(uuid.uuid4())
        item["id"] = item_id
        item.setdefault("created_at", datetime.now(UTC).isoformat())
        item.setdefault("updated_at", datetime.now(UTC).isoformat())
        self._data[item_id] = item
        return item_id

    def get(self, item_id: str) -> dict[str, Any] | None:
        """Get item by ID."""
        return self._data.get(item_id)

    def find(self, **filters) -> list[dict[str, Any]]:
        """Find items matching filters."""
        results = []
        for item in self._data.values():
            match = all(item.get(k) == v for k, v in filters.items())
            if match:
                results.append(item)
        return results

    def find_one(self, **filters) -> dict[str, Any] | None:
        """Find first item matching filters."""
        items = self.find(**filters)
        return items[0] if items else None

    def update(self, item_id: str, updates: dict[str, Any]) -> bool:
        """Update item by ID."""
        if item_id not in self._data:
            return False
        self._data[item_id].update(updates)
        self._data[item_id]["updated_at"] = datetime.now(UTC).isoformat()
        return True

    def delete(self, item_id: str) -> bool:
        """Delete item by ID."""
        if item_id in self._data:
            del self._data[item_id]
            return True
        return False

    def count(self) -> int:
        """Count items."""
        return len(self._data)

    def all(self) -> list[dict[str, Any]]:
        """Get all items."""
        return list(self._data.values())


# ============================================================================
# Fake Cache - Dict-based
# ============================================================================


class FakeCache:
    """
    In-memory cache for tests.
    Replaces Redis without network overhead.

    Usage:
        cache = FakeCache()
        await cache.set("key", "value", ttl=300)
        value = await cache.get("key")
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._ttls: dict[str, datetime] = {}

    async def get(self, key: str) -> Any | None:
        """Get value, checking TTL."""
        if key in self._ttls:
            if datetime.now(UTC) > self._ttls[key]:
                del self._data[key]
                del self._ttls[key]
                return None
        return self._data.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value with optional TTL."""
        self._data[key] = value
        if ttl:
            self._ttls[key] = datetime.now(UTC).replace(
                second=datetime.now(UTC).second + ttl
            )
        return True

    async def delete(self, key: str) -> bool:
        """Delete key."""
        if key in self._data:
            del self._data[key]
            self._ttls.pop(key, None)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    async def clear(self) -> None:
        """Clear all data."""
        self._data.clear()
        self._ttls.clear()

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching pattern (simplified)."""
        if pattern == "*":
            return list(self._data.keys())
        prefix = pattern.rstrip("*")
        return [k for k in self._data.keys() if k.startswith(prefix)]

    # Sync aliases for compatibility
    def get_sync(self, key: str) -> Any | None:
        return self._data.get(key)

    def set_sync(self, key: str, value: Any) -> bool:
        self._data[key] = value
        return True


# ============================================================================
# Fake HTTP Client - Predefined Responses
# ============================================================================


@dataclass
class FakeResponse:
    """Fake HTTP response."""
    status_code: int = 200
    json_data: dict[str, Any] | None = None
    text: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict[str, Any]:
        return self.json_data or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class FakeHTTPClient:
    """
    Fake HTTP client for tests.
    Avoids real network calls.

    Usage:
        client = FakeHTTPClient()
        client.add_response("GET", "/api/data", {"result": "ok"})
        response = await client.get("/api/data")
    """

    def __init__(self):
        self._responses: dict[str, FakeResponse] = {}
        self._calls: list[dict[str, Any]] = []

    def add_response(
        self,
        method: str,
        url: str,
        json_data: dict[str, Any] | None = None,
        status_code: int = 200,
        text: str = ""
    ) -> None:
        """Register a response for a URL."""
        key = f"{method.upper()}:{url}"
        self._responses[key] = FakeResponse(
            status_code=status_code,
            json_data=json_data,
            text=text
        )

    def _get_response(self, method: str, url: str) -> FakeResponse:
        """Get registered response or default."""
        key = f"{method.upper()}:{url}"
        self._calls.append({"method": method, "url": url})
        return self._responses.get(key, FakeResponse(status_code=404))

    async def get(self, url: str, **kwargs) -> FakeResponse:
        return self._get_response("GET", url)

    async def post(self, url: str, **kwargs) -> FakeResponse:
        return self._get_response("POST", url)

    async def put(self, url: str, **kwargs) -> FakeResponse:
        return self._get_response("PUT", url)

    async def delete(self, url: str, **kwargs) -> FakeResponse:
        return self._get_response("DELETE", url)

    async def aclose(self) -> None:
        pass

    @property
    def call_count(self) -> int:
        return len(self._calls)

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self._calls


# ============================================================================
# Service Stub Generator
# ============================================================================


def create_service_stub(service_class: type[T], **method_returns) -> T:
    """
    Create a stub of a service class with predefined returns.

    Usage:
        stub = create_service_stub(
            QuestionService,
            get_question={"id": "1", "text": "What is 2+2?"},
            list_questions=[{"id": "1"}, {"id": "2"}]
        )
    """
    stub = MagicMock(spec=service_class)

    for method_name, return_value in method_returns.items():
        method = getattr(stub, method_name)
        if asyncio_return(return_value):
            method.return_value = return_value
        else:
            method.return_value = return_value

    return stub


def asyncio_return(value: Any) -> bool:
    """Check if value should be returned as async."""
    return isinstance(value, (dict, list, str, int, float, bool, type(None)))


# ============================================================================
# Test Data Builders
# ============================================================================


class UserBuilder:
    """
    Fluent builder for test users.

    Usage:
        user = UserBuilder().with_email("test@test.com").as_admin().build()
    """

    def __init__(self):
        self._data = {
            "id": str(uuid.uuid4()),
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "role": "student",
            "is_active": True,
            "is_verified": True,
        }

    def with_id(self, id: str) -> "UserBuilder":
        self._data["id"] = id
        return self

    def with_email(self, email: str) -> "UserBuilder":
        self._data["email"] = email
        return self

    def with_username(self, username: str) -> "UserBuilder":
        self._data["username"] = username
        return self

    def as_student(self) -> "UserBuilder":
        self._data["role"] = "student"
        return self

    def as_teacher(self) -> "UserBuilder":
        self._data["role"] = "teacher"
        return self

    def as_admin(self) -> "UserBuilder":
        self._data["role"] = "admin"
        return self

    def inactive(self) -> "UserBuilder":
        self._data["is_active"] = False
        return self

    def unverified(self) -> "UserBuilder":
        self._data["is_verified"] = False
        return self

    def build(self) -> dict[str, Any]:
        return self._data.copy()


class QuestionBuilder:
    """
    Fluent builder for test questions.

    Usage:
        question = QuestionBuilder().matematik().difficulty(0.5).build()
    """

    def __init__(self):
        self._data = {
            "id": str(uuid.uuid4()),
            "question_text": "Test sorusu?",
            "option_a": "A şıkkı",
            "option_b": "B şıkkı",
            "option_c": "C şıkkı",
            "option_d": "D şıkkı",
            "correct_answer": "A",
            "subject_area": "MATEMATIK",
            "exam_type": "TYT",
            "topic": "Test Topic",
            "difficulty": "MEDIUM",
            "irt_difficulty": 0.0,
            "irt_discrimination": 1.0,
            "irt_guessing": 0.25,
        }

    def with_id(self, id: str) -> "QuestionBuilder":
        self._data["id"] = id
        return self

    def with_text(self, text: str) -> "QuestionBuilder":
        self._data["question_text"] = text
        return self

    def matematik(self) -> "QuestionBuilder":
        self._data["subject_area"] = "MATEMATIK"
        return self

    def turkce(self) -> "QuestionBuilder":
        self._data["subject_area"] = "TURKCE"
        return self

    def fizik(self) -> "QuestionBuilder":
        self._data["subject_area"] = "FIZIK"
        return self

    def tyt(self) -> "QuestionBuilder":
        self._data["exam_type"] = "TYT"
        return self

    def ayt(self) -> "QuestionBuilder":
        self._data["exam_type"] = "AYT"
        return self

    def difficulty(self, value: float) -> "QuestionBuilder":
        """Set IRT difficulty (-4.0 to 4.0)."""
        if not -4.0 <= value <= 4.0:
            raise ValueError("Difficulty must be between -4.0 and 4.0")
        self._data["irt_difficulty"] = value
        return self

    def easy(self) -> "QuestionBuilder":
        self._data["difficulty"] = "EASY"
        self._data["irt_difficulty"] = -1.5
        return self

    def medium(self) -> "QuestionBuilder":
        self._data["difficulty"] = "MEDIUM"
        self._data["irt_difficulty"] = 0.0
        return self

    def hard(self) -> "QuestionBuilder":
        self._data["difficulty"] = "HARD"
        self._data["irt_difficulty"] = 1.5
        return self

    def with_correct_answer(self, answer: str) -> "QuestionBuilder":
        self._data["correct_answer"] = answer
        return self

    def build(self) -> dict[str, Any]:
        return self._data.copy()


# ============================================================================
# Pytest Fixtures
# ============================================================================

import pytest


@pytest.fixture
def fake_db() -> FakeDatabase:
    """Provide a fresh FakeDatabase for each test."""
    db = FakeDatabase()
    yield db
    db.clear()


@pytest.fixture
def fake_cache() -> FakeCache:
    """Provide a fresh FakeCache for each test."""
    cache = FakeCache()
    return cache


@pytest.fixture
def fake_http() -> FakeHTTPClient:
    """Provide a fresh FakeHTTPClient for each test."""
    return FakeHTTPClient()


@pytest.fixture
def user_builder() -> UserBuilder:
    """Provide a UserBuilder."""
    return UserBuilder()


@pytest.fixture
def question_builder() -> QuestionBuilder:
    """Provide a QuestionBuilder."""
    return QuestionBuilder()


# ============================================================================
# Assertion Helpers
# ============================================================================


def assert_valid_uuid(value: str) -> None:
    """Assert value is a valid UUID."""
    try:
        uuid.UUID(value)
    except ValueError:
        raise AssertionError(f"'{value}' is not a valid UUID")


def assert_iso_datetime(value: str) -> None:
    """Assert value is a valid ISO datetime string."""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AssertionError(f"'{value}' is not a valid ISO datetime")


def assert_json_equal(actual: Any, expected: Any) -> None:
    """Assert two values are equal when serialized to JSON."""
    actual_json = json.dumps(actual, sort_keys=True)
    expected_json = json.dumps(expected, sort_keys=True)
    assert actual_json == expected_json, f"JSON mismatch:\nActual: {actual_json}\nExpected: {expected_json}"


def assert_contains_keys(data: dict, *keys: str) -> None:
    """Assert dictionary contains all specified keys."""
    missing = [k for k in keys if k not in data]
    if missing:
        raise AssertionError(f"Missing keys: {missing}")


def assert_irt_params_valid(
    difficulty: float,
    discrimination: float,
    guessing: float
) -> None:
    """Assert IRT parameters are within valid ranges."""
    assert -4.0 <= difficulty <= 4.0, f"Difficulty {difficulty} out of range [-4.0, 4.0]"
    assert 0.2 <= discrimination <= 4.0, f"Discrimination {discrimination} out of range [0.2, 4.0]"
    assert 0.0 <= guessing <= 0.35, f"Guessing {guessing} out of range [0.0, 0.35]"
