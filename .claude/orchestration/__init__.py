"""
KIRO2 Orchestration - Active Modules

Active modules:
- mcp_orchestrator: MCP server for Claude Code integration
- feedback_collector: Task feedback and evidence-based learning
- memory_injector: Pre-task context injection
- schemas: Shared data schemas
- skill_library: Skill storage and retrieval

Legacy modules moved to _legacy/ directory.
"""

__version__ = "2.0.0"
__all__ = [
    "feedback_collector",
    "memory_injector",
    "mcp_orchestrator",
    "schemas",
    "skill_library",
]
