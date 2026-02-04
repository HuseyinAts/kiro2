"""
Learning Path Agent - Modular Implementation
Teknofest 2025 - Eğitim Eylemci Projesi

Refactored from monolithic learning_path_agent.py (3278 lines)
into modular, maintainable components.

Main Components:
- agent.py: Main orchestrator
- models.py: Data models
- core/: Core business logic (profiling, assessment, resources, path generation)
- strategies/: Strategy pattern implementations (style, difficulty, time)
- integrations/: External service integrations (YouTube, Khan, OER, chat, forms)
- utils/: Utility functions (validators, formatters)

Usage:
    from backend.agents.learning_path import LearningPathAgent

    agent = LearningPathAgent()
    profile = await agent.analyze_student(student_id, data)
    path = await agent.create_learning_path(student_id, goal)
"""

# Public API will be defined when agent.py is created
# For now, keep this module empty until main agent is implemented

__version__ = "2.0.0"
__author__ = "Teknofest 2025 Team"

from .agent import LearningPathAgent
from .models import (
    StudentProfile,
    LearningResource,
    LearningPath,
    LearningPhase,
    LearningStyle,
    KnowledgeLevel,
)

__all__ = [
    "LearningPathAgent",
    "StudentProfile",
    "LearningResource",
    "LearningPath",
    "LearningPhase",
    "LearningStyle",
    "KnowledgeLevel",
]
