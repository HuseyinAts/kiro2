"""
Learning Path Circuit Breakers
P1.4 Implementation - Circuit breaker protection for Learning Path operations

Protects against:
- AI agent failures (LLM API timeouts)
- YouTube API failures (quota exceeded, network issues)
- Database failures (connection pool exhausted)
- Resource search failures

Requirements: P1.4, 5.18, 4.11
"""

import logging
from typing import Any

from core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    circuit_breaker_manager,
)

logger = logging.getLogger(__name__)


# ==================== Circuit Breaker Configurations ====================

# AI Agent Circuit Breaker Config
AI_AGENT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,  # Open after 3 consecutive failures
    success_threshold=2,  # Close after 2 consecutive successes in half-open
    timeout=120,  # Wait 2 minutes before trying again
    half_open_max_calls=2,  # Allow 2 test calls in half-open state
    excluded_exceptions=(KeyboardInterrupt,),  # Don't count these as failures
)

# YouTube API Circuit Breaker Config
YOUTUBE_API_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,  # More tolerant for external API
    success_threshold=3,
    timeout=60,  # 1 minute timeout
    half_open_max_calls=3,
    excluded_exceptions=(KeyboardInterrupt,),
)

# Database Circuit Breaker Config
DATABASE_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout=30,  # Quick recovery for database
    half_open_max_calls=2,
    excluded_exceptions=(KeyboardInterrupt,),
)

# Resource Search Circuit Breaker Config
RESOURCE_SEARCH_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=3,
    timeout=60,
    half_open_max_calls=3,
    excluded_exceptions=(KeyboardInterrupt,),
)


# ==================== Circuit Breaker Registry ====================


def initialize_learning_path_circuit_breakers():
    """
    Initialize all Learning Path circuit breakers

    Call this during application startup to register all circuit breakers.
    """
    logger.info("Initializing Learning Path circuit breakers...")

    # Register AI Agent circuit breaker
    circuit_breaker_manager.register(
        name="learning_path_ai_agent", config=AI_AGENT_CONFIG
    )
    logger.info("✅ AI Agent circuit breaker registered")

    # Register YouTube API circuit breaker
    circuit_breaker_manager.register(
        name="learning_path_youtube_api", config=YOUTUBE_API_CONFIG
    )
    logger.info("✅ YouTube API circuit breaker registered")

    # Register Database circuit breaker
    circuit_breaker_manager.register(
        name="learning_path_database", config=DATABASE_CONFIG
    )
    logger.info("✅ Database circuit breaker registered")

    # Register Resource Search circuit breaker
    circuit_breaker_manager.register(
        name="learning_path_resource_search", config=RESOURCE_SEARCH_CONFIG
    )
    logger.info("✅ Resource Search circuit breaker registered")

    logger.info("Learning Path circuit breakers initialized successfully")


# ==================== Circuit Breaker Getters ====================


def get_ai_agent_circuit_breaker() -> CircuitBreaker:
    """Get AI Agent circuit breaker"""
    breaker = circuit_breaker_manager.get("learning_path_ai_agent")
    if breaker is None:
        logger.warning("AI Agent circuit breaker not initialized, creating default...")
        breaker = circuit_breaker_manager.register(
            "learning_path_ai_agent", AI_AGENT_CONFIG
        )
    return breaker


def get_youtube_api_circuit_breaker() -> CircuitBreaker:
    """Get YouTube API circuit breaker"""
    breaker = circuit_breaker_manager.get("learning_path_youtube_api")
    if breaker is None:
        logger.warning(
            "YouTube API circuit breaker not initialized, creating default..."
        )
        breaker = circuit_breaker_manager.register(
            "learning_path_youtube_api", YOUTUBE_API_CONFIG
        )
    return breaker


def get_database_circuit_breaker() -> CircuitBreaker:
    """Get Database circuit breaker"""
    breaker = circuit_breaker_manager.get("learning_path_database")
    if breaker is None:
        logger.warning("Database circuit breaker not initialized, creating default...")
        breaker = circuit_breaker_manager.register(
            "learning_path_database", DATABASE_CONFIG
        )
    return breaker


def get_resource_search_circuit_breaker() -> CircuitBreaker:
    """Get Resource Search circuit breaker"""
    breaker = circuit_breaker_manager.get("learning_path_resource_search")
    if breaker is None:
        logger.warning(
            "Resource Search circuit breaker not initialized, creating default..."
        )
        breaker = circuit_breaker_manager.register(
            "learning_path_resource_search", RESOURCE_SEARCH_CONFIG
        )
    return breaker


# ==================== Circuit Breaker Status ====================


def get_all_circuit_breaker_status() -> dict[str, dict[str, Any]]:
    """
    Get status of all Learning Path circuit breakers

    Returns:
        Dict with circuit breaker names as keys and their stats as values
    """
    breaker_names = [
        "learning_path_ai_agent",
        "learning_path_youtube_api",
        "learning_path_database",
        "learning_path_resource_search",
    ]

    status = {}
    for name in breaker_names:
        breaker = circuit_breaker_manager.get(name)
        if breaker:
            status[name] = breaker.get_stats().to_dict()
        else:
            status[name] = {"error": "Circuit breaker not initialized"}

    return status


def reset_all_learning_path_circuit_breakers():
    """Reset all Learning Path circuit breakers (for testing/recovery)"""
    breaker_names = [
        "learning_path_ai_agent",
        "learning_path_youtube_api",
        "learning_path_database",
        "learning_path_resource_search",
    ]

    for name in breaker_names:
        breaker = circuit_breaker_manager.get(name)
        if breaker:
            breaker.reset()
            logger.info(f"Circuit breaker '{name}' reset")


# ==================== Fallback Handlers ====================


async def ai_agent_fallback_handler(
    error: Exception, student_id: str, subject: str
) -> dict[str, Any]:
    """
    Fallback handler when AI Agent circuit is open

    Returns a simplified learning path without AI recommendations.
    """
    logger.warning(
        f"AI Agent circuit breaker is OPEN - returning fallback path for "
        f"student={student_id}, subject={subject}"
    )

    return {
        "success": True,
        "learning_path": {
            "path_id": f"FALLBACK_{student_id}_{subject}",
            "student_id": student_id,
            "subject": subject,
            "difficulty_level": "orta",
            "modules": [
                {
                    "module_id": "FALLBACK_MOD1",
                    "title": f"{subject.title()} - Temel Kavramlar",
                    "order": 1,
                    "estimated_duration": "7 gün",
                    "topics": [
                        {
                            "topic_id": "FALLBACK_TOP1",
                            "name": "Temel konular",
                            "duration_minutes": 60,
                        }
                    ],
                }
            ],
            "progress": {
                "completed_modules": 0,
                "total_modules": 1,
                "completed_topics": 0,
                "total_topics": 1,
                "overall_progress": 0,
            },
            "resources": [],
            "ai_generated": False,
            "fallback": True,
            "fallback_reason": "AI Agent circuit breaker is OPEN",
        },
        "message": "Öğrenme yolu oluşturuldu (temel şablon - AI geçici olarak kullanılamıyor)",
        "warning": "AI agent geçici olarak kullanılamıyor. Basitleştirilmiş öğrenme yolu sunuluyor.",
    }


async def resource_search_fallback_handler(
    error: Exception, subject: str, topic: str | None = None
) -> dict[str, Any]:
    """
    Fallback handler when Resource Search circuit is open

    Returns empty results with helpful message.
    """
    logger.warning(
        f"Resource Search circuit breaker is OPEN - returning empty results for "
        f"subject={subject}, topic={topic}"
    )

    return {
        "success": False,
        "resources": [],
        "total": 0,
        "filters": {"subject": subject, "topic": topic},
        "error": {
            "message": "Video arama servisi geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
            "code": "CIRCUIT_BREAKER_OPEN",
            "retry_after": 60,
        },
        "fallback": True,
    }


# ==================== Health Check ====================


def check_circuit_breaker_health() -> dict[str, Any]:
    """
    Check health of all Learning Path circuit breakers

    Returns:
        Dict with overall health status and individual breaker statuses
    """
    all_status = get_all_circuit_breaker_status()

    open_breakers = []
    half_open_breakers = []
    closed_breakers = []

    for name, status in all_status.items():
        if "error" in status:
            continue

        state = status.get("state")
        if state == "open":
            open_breakers.append(name)
        elif state == "half_open":
            half_open_breakers.append(name)
        elif state == "closed":
            closed_breakers.append(name)

    # Overall health
    is_healthy = len(open_breakers) == 0

    return {
        "healthy": is_healthy,
        "circuit_breakers": {
            "total": len(all_status),
            "open": len(open_breakers),
            "half_open": len(half_open_breakers),
            "closed": len(closed_breakers),
        },
        "open_breakers": open_breakers,
        "half_open_breakers": half_open_breakers,
        "details": all_status,
    }
