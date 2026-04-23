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
    FakeCache,
    FakeCollection,
    FakeDatabase,
    FakeHTTPClient,
    FakeResponse,
    QuestionBuilder,
    UserBuilder,
    assert_contains_keys,
    assert_irt_params_valid,
    assert_iso_datetime,
    assert_json_equal,
    # Assertions
    assert_valid_uuid,
    create_service_stub,
    fake_cache,
    # Fixtures
    fake_db,
    fake_http,
    question_builder,
    user_builder,
)

__all__ = [
    "FakeCache",
    "FakeCollection",
    "FakeDatabase",
    "FakeHTTPClient",
    "FakeResponse",
    "QuestionBuilder",
    "UserBuilder",
    "assert_contains_keys",
    "assert_irt_params_valid",
    "assert_iso_datetime",
    "assert_json_equal",
    "assert_valid_uuid",
    "create_service_stub",
    "fake_cache",
    "fake_db",
    "fake_http",
    "question_builder",
    "user_builder",
]
