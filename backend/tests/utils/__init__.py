"""
Test utilities package for KIRO2.

Provides:
- FakeDatabase: In-memory database for fast tests
- FakeCache: Dict-based cache (replaces Redis)
- FakeHTTPClient: Predefined HTTP responses
- UserBuilder/QuestionBuilder: Fluent test data builders
- Assertion helpers
"""
from tests.utils.test_helpers import (
    FakeDatabase,
    FakeCollection,
    FakeCache,
    FakeHTTPClient,
    FakeResponse,
    UserBuilder,
    QuestionBuilder,
    create_service_stub,
    # Fixtures
    fake_db,
    fake_cache,
    fake_http,
    user_builder,
    question_builder,
    # Assertions
    assert_valid_uuid,
    assert_iso_datetime,
    assert_json_equal,
    assert_contains_keys,
    assert_irt_params_valid,
)

__all__ = [
    "FakeDatabase",
    "FakeCollection",
    "FakeCache",
    "FakeHTTPClient",
    "FakeResponse",
    "UserBuilder",
    "QuestionBuilder",
    "create_service_stub",
    "fake_db",
    "fake_cache",
    "fake_http",
    "user_builder",
    "question_builder",
    "assert_valid_uuid",
    "assert_iso_datetime",
    "assert_json_equal",
    "assert_contains_keys",
    "assert_irt_params_valid",
]
