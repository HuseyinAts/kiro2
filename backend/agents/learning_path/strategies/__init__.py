"""
Strategy Pattern Implementations

This package contains strategy implementations for various aspects:
- ResourceSearchStrategy: Abstract base class for resource search strategies
- LearningStyleStrategy: Learning style matching and filtering
- DifficultyAdapter: Dynamic difficulty adjustment
- TimePlanner: Schedule and milestone planning
- RAGSearchStrategy: RAG-based semantic search using ChromaDB
- KhanSearchStrategy: Khan Academy API search integration
- OERSearchStrategy: OER Commons API search integration
"""

from .resource_search import ResourceSearchStrategy
from .learning_style_strategy import LearningStyleStrategy
from .difficulty_adapter import DifficultyAdapter
from .time_planner import TimePlanner
from .rag_strategy import RAGSearchStrategy
from .khan_strategy import KhanSearchStrategy
from .oer_strategy import OERSearchStrategy

__all__ = [
    "ResourceSearchStrategy",
    "LearningStyleStrategy",
    "DifficultyAdapter",
    "TimePlanner",
    "RAGSearchStrategy",
    "KhanSearchStrategy",
    "OERSearchStrategy",
]
