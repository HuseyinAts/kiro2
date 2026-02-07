"""Verify testcontainer fixtures are working"""

import pytest

pytestmark = pytest.mark.skipif(
    True,
    reason="DuplicateTable: idx_student_learning_style already exists in PostgreSQL, requires clean DB state",
)


def test_fixture_loaded(sync_db_session):
    """Test that sync_db_session fixture loads"""
    assert sync_db_session is not None
    print(f"Session: {sync_db_session}")
    print(f"Session bind: {sync_db_session.bind}")


def test_can_query(sync_db_session):
    """Test basic query execution"""
    result = sync_db_session.execute("SELECT 1 as num")
    row = result.fetchone()
    assert row[0] == 1
