"""Loop Guardrails System for AI Agent Protection.

This package provides comprehensive protection against infinite loops,
resource exhaustion, and other failure modes in AI agent execution.

Main Components:
- GuardrailManager: Orchestrates all guards
- Guards: Individual protection mechanisms
- Models: Data models for configuration and reporting
- Utils: Resource monitoring and lock tracking utilities

Usage:
    from app.guardrails import GuardrailManager, GuardConfig

    config = GuardConfig(
        max_turns=100,
        timeout_seconds=300,
        memory_limit_mb=1024,
    )

    manager = GuardrailManager(config)
    manager.start_execution()

    while not done:
        result = await manager.check_all_guards(context)
        if result["should_stop"]:
            break
        # ... do work ...

    report = manager.generate_report()
"""
from .exceptions import (
    CircuitBreakerOpen,
    DeadlockDetected,
    EmergencyStopTriggered,
    GuardrailError,
    MaxTurnsExceeded,
    RecursionLimitExceeded,
    ResourceLimitExceeded,
    StallDetected,
    TimeoutExceeded,
)
from .guards import (
    BaseGuard,
    CircuitBreakerGuard,
    DeadlockDetectionGuard,
    EmergencyStopGuard,
    MaxTurnsGuard,
    ProgressMonitorGuard,
    RecursionDepthGuard,
    ResourceLimitGuard,
    TimeoutGuard,
)
from .manager import GuardrailManager, with_guardrails
from .models import GuardConfig, GuardResult, GuardStatus, TerminationReport
from .utils import LockTracker, ResourceMonitor

__version__ = "1.0.0"

__all__ = [
    # Manager
    "GuardrailManager",
    "with_guardrails",
    # Models
    "GuardConfig",
    "GuardResult",
    "GuardStatus",
    "TerminationReport",
    # Exceptions
    "GuardrailError",
    "MaxTurnsExceeded",
    "TimeoutExceeded",
    "CircuitBreakerOpen",
    "RecursionLimitExceeded",
    "ResourceLimitExceeded",
    "DeadlockDetected",
    "EmergencyStopTriggered",
    "StallDetected",
    # Guards
    "BaseGuard",
    "MaxTurnsGuard",
    "TimeoutGuard",
    "CircuitBreakerGuard",
    "RecursionDepthGuard",
    "ProgressMonitorGuard",
    "ResourceLimitGuard",
    "DeadlockDetectionGuard",
    "EmergencyStopGuard",
    # Utils
    "ResourceMonitor",
    "LockTracker",
]
