"""Tests for DungeonProgress ORM model."""

from models.dungeon_models import DungeonProgress


def test_dungeon_progress_table_name():
    assert DungeonProgress.__tablename__ == "dungeon_progress"


def test_dungeon_progress_columns():
    cols = {c.name for c in DungeonProgress.__table__.columns}
    expected = {
        "user_id",
        "topic_id",
        "attempt_count",
        "best_score",
        "last_score",
        "completed",
        "first_attempt",
        "last_attempt",
    }
    assert expected == cols


def test_dungeon_progress_primary_key():
    pk_cols = [c.name for c in DungeonProgress.__table__.primary_key.columns]
    assert sorted(pk_cols) == ["topic_id", "user_id"]
