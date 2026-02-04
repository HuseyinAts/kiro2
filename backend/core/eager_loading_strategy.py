"""
Eager Loading Strategy Configuration
PERFORMANCE FIX: Centralized eager loading patterns for all models
"""

from typing import Dict, List

from sqlalchemy.orm import joinedload, selectinload, subqueryload

# Eager loading strategy map
# Format: {model_name: {relationship_name: loading_strategy}}
#
# Loading strategies:
# - selectinload: Separate SELECT query (good for collections, prevents cartesian product)
# - joinedload: Single JOIN query (good for single objects, may cause cartesian product)
# - subqueryload: Separate subquery (good for large collections)

EAGER_LOADING_STRATEGIES: Dict[str, Dict[str, str]] = {
    # User model
    "User": {
        "student_profile": "joinedload",  # One-to-one relationship
        "parent_profile": "joinedload",  # One-to-one relationship
        "teacher_profile": "joinedload",  # One-to-one relationship
        "exam_sessions": "selectinload",  # One-to-many
        "study_sessions": "selectinload",  # One-to-many
    },
    # ExamSession model
    "ExamSession": {
        "student": "joinedload",  # Many-to-one (single object)
        "exam_answers": "selectinload",  # One-to-many (collection)
        "exam_answers.question": "selectinload",  # Nested eager load
        "performance_analysis": "selectinload",  # One-to-many
    },
    # ExamAnswer model
    "ExamAnswer": {
        "exam_session": "joinedload",  # Many-to-one
        "student": "joinedload",  # Many-to-one
        "question": "joinedload",  # Many-to-one
    },
    # Question model
    "Question": {
        "exam_answers": "selectinload",  # One-to-many
        "learning_objectives": "selectinload",  # Many-to-many
    },
    # StudentProfile model
    "StudentProfile": {
        "user": "joinedload",  # One-to-one
        "exam_sessions": "selectinload",  # One-to-many
        "learning_analytics": "selectinload",  # One-to-many
        "parent_relations": "selectinload",  # One-to-many
    },
    # ParentChildRelation model
    "ParentChildRelation": {
        "parent": "joinedload",  # Many-to-one
        "child": "joinedload",  # Many-to-one
        "child.student_profile": "joinedload",  # Nested
    },
    # ParentNotification model
    "ParentNotification": {
        "parent": "joinedload",  # Many-to-one
        "child": "joinedload",  # Many-to-one
    },
    # WeeklyReport model
    "WeeklyReport": {
        "student": "joinedload",  # Many-to-one
        "parent": "joinedload",  # Many-to-one
    },
    # PerformanceAnalysis model
    "PerformanceAnalysis": {
        "student": "joinedload",  # Many-to-one
        "exam_session": "joinedload",  # Many-to-one
        "subject_weaknesses": "selectinload",  # One-to-many
    },
    # StudySession model
    "StudySession": {
        "student": "joinedload",  # Many-to-one
        "content_items": "selectinload",  # One-to-many
    },
}


# Common query patterns with pre-configured eager loading
COMMON_QUERY_PATTERNS = {
    # User dashboard queries
    "user_with_profile": {
        "model": "User",
        "eager_load": ["student_profile", "exam_sessions"],
        "joined_load": [],
    },
    # Exam performance queries
    "exam_with_answers": {
        "model": "ExamSession",
        "eager_load": ["exam_answers", "exam_answers.question", "performance_analysis"],
        "joined_load": ["student"],
    },
    "exam_detailed": {
        "model": "ExamSession",
        "eager_load": [
            "exam_answers",
            "exam_answers.question",
            "performance_analysis",
            "performance_analysis.subject_weaknesses",
        ],
        "joined_load": ["student", "student.student_profile"],
    },
    # Parent dashboard queries
    "parent_children": {
        "model": "ParentChildRelation",
        "eager_load": ["child.exam_sessions", "child.student_profile"],
        "joined_load": ["parent", "child"],
    },
    "parent_notifications": {
        "model": "ParentNotification",
        "eager_load": [],
        "joined_load": ["parent", "child"],
    },
    # Student dashboard queries
    "student_dashboard": {
        "model": "User",
        "eager_load": [
            "exam_sessions",
            "exam_sessions.performance_analysis",
            "study_sessions",
            "student_profile",
        ],
        "joined_load": [],
    },
    "student_exam_history": {
        "model": "ExamSession",
        "eager_load": ["exam_answers", "performance_analysis"],
        "joined_load": ["student"],
    },
}


def get_eager_loading_strategy(model_name: str, relationship: str) -> str:
    """
    Get the recommended eager loading strategy for a relationship

    Args:
        model_name: Name of the SQLAlchemy model
        relationship: Name of the relationship attribute

    Returns:
        Loading strategy name: 'selectinload', 'joinedload', or 'subqueryload'
    """
    model_strategies = EAGER_LOADING_STRATEGIES.get(model_name, {})
    return model_strategies.get(relationship, "selectinload")  # Default to selectinload


def apply_common_pattern(optimizer, pattern_name: str):
    """
    Apply a common query pattern to QueryOptimizer

    Args:
        optimizer: QueryOptimizer instance
        pattern_name: Name of the pattern from COMMON_QUERY_PATTERNS

    Returns:
        QueryOptimizer with eager loading applied

    Example:
        optimizer = QueryOptimizer(session)
        optimizer = apply_common_pattern(optimizer, "exam_with_answers")
        results = await optimizer.select(ExamSession).all()
    """
    pattern = COMMON_QUERY_PATTERNS.get(pattern_name)
    if not pattern:
        raise ValueError(f"Unknown query pattern: {pattern_name}")

    # Apply eager loads
    if pattern.get("eager_load"):
        optimizer.eager_load(*pattern["eager_load"])

    # Apply joined loads
    if pattern.get("joined_load"):
        optimizer.joined_load(*pattern["joined_load"])

    return optimizer


# Endpoint-specific optimization recommendations
ENDPOINT_OPTIMIZATIONS = {
    # Exam Performance API
    "GET /api/v1/exam-performance/{exam_session_id}/detailed-analysis": {
        "pattern": "exam_detailed",
        "description": "Load exam with all related data for detailed analysis",
        "estimated_queries": "3 queries (down from 50+ without optimization)",
    },
    "GET /api/v1/exam-performance/{exam_session_id}/weaknesses": {
        "pattern": "exam_with_answers",
        "description": "Load exam with answers and questions for weakness analysis",
        "estimated_queries": "2-3 queries",
    },
    "GET /api/v1/exam-performance/student/{student_id}/improvement-trends": {
        "pattern": "student_exam_history",
        "description": "Load student's exam history with performance data",
        "estimated_queries": "2-3 queries",
    },
    # Parent API
    "GET /api/v1/parent/children": {
        "pattern": "parent_children",
        "description": "Load parent's children with profiles",
        "estimated_queries": "2 queries",
    },
    "GET /api/v1/parent/children/{child_id}/performance": {
        "pattern": "student_dashboard",
        "description": "Load child's complete performance data",
        "estimated_queries": "3-4 queries",
    },
    "GET /api/v1/parent/dashboard": {
        "pattern": "parent_children",
        "description": "Load complete parent dashboard data",
        "estimated_queries": "3-4 queries",
    },
    # Student Dashboard API
    "GET /api/v1/student-dashboard/istatistikler": {
        "pattern": "student_dashboard",
        "description": "Load student dashboard statistics",
        "estimated_queries": "3-4 queries",
    },
    "GET /api/v1/student-dashboard/sinav-gecmisi": {
        "pattern": "student_exam_history",
        "description": "Load student's exam history",
        "estimated_queries": "2 queries",
    },
}


def get_endpoint_optimization(endpoint: str) -> Dict:
    """
    Get optimization recommendations for an endpoint

    Args:
        endpoint: API endpoint path

    Returns:
        Optimization configuration dict
    """
    return ENDPOINT_OPTIMIZATIONS.get(endpoint, {})
