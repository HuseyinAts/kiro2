"""Tests for dungeon endpoint."""

from app.api.learning_path_dungeon import (
    CODE_PREFIX_MAP,
    compute_dag_depths,
    compute_question_counts,
)


def test_code_prefix_map_has_nine_subjects():
    assert len(CODE_PREFIX_MAP) == 9
    assert "MATEMATIK" in CODE_PREFIX_MAP
    assert "FIZIK" in CODE_PREFIX_MAP


def test_compute_dag_depths_empty():
    result = compute_dag_depths([], [])
    assert result == {}


def test_compute_dag_depths_chain():
    """A -> B -> C should give depths 0, 1, 2."""
    rooms = [
        {"topic_id": "a"},
        {"topic_id": "b"},
        {"topic_id": "c"},
    ]
    edges = [
        {"from_topic": "a", "to_topic": "b"},
        {"from_topic": "b", "to_topic": "c"},
    ]
    depths = compute_dag_depths(rooms, edges)
    assert depths["a"] == 0
    assert depths["b"] == 1
    assert depths["c"] == 2


def test_compute_question_counts_with_fallback():
    """When direct count is 0, use root_count / sibling_count."""
    direct = {"topic-1": 100, "topic-2": 0}
    root_count = 1000
    sibling_count = 5
    result = compute_question_counts(direct, root_count, sibling_count)
    assert result["topic-1"] == 100
    assert result["topic-2"] == 200  # 1000 // 5
