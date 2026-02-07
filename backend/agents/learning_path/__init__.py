"""
Learning Path Agent Module.

This module provides a comprehensive learning path generation and management system.

Main Entry Point:
    LearningPathFacade - Unified interface for all learning path operations

Services:
    PathGenerationService - Creates personalized learning paths
    ResourceDiscoveryService - Discovers educational resources
    PathAdaptationService - Adapts paths based on performance

Integrations:
    ChatIntegrationService - Chat-based interactions
    FormIntegrationService - Form handling

Strategies:
    YouTubeSearchStrategy - YouTube video search
    KhanSearchStrategy - Khan Academy search
    OERSearchStrategy - OER Commons search
    RAGSearchStrategy - RAG/ChromaDB search

Teknofest 2025 - Eğitim Eylemci Projesi
"""

__version__ = "2.0.0"
__author__ = "Teknofest 2025 Team"

from .agent import LearningPathAgent
from .facade import (
    LearningPathFacade,
    FacadeConfig,
    get_learning_path_facade,
)
from .models import (
    StudentProfile,
    LearningResource,
    LearningPath,
    LearningPhase,
    PathNode,
    LearningStyle,
    KnowledgeLevel,
)
from .config import LearningPathConfig, get_learning_path_config, config

__all__ = [
    # Legacy Agent (to be replaced)
    "LearningPathAgent",
    # Facade (Main Entry)
    "LearningPathFacade",
    "FacadeConfig",
    "get_learning_path_facade",
    # Models
    "StudentProfile",
    "LearningResource",
    "LearningPath",
    "LearningPhase",
    "PathNode",
    "LearningStyle",
    "KnowledgeLevel",
    # Config
    "LearningPathConfig",
    "get_learning_path_config",
    "config",
]
