"""
KIRO2 Agent SDK - Claude Code 2026 Entegrasyonu

Bu modül Claude Agent SDK'yı KIRO2 platformuna entegre eder.
Domain-specific agent'lar, tool tanımları ve workflow'lar içerir.

Kullanım:
    from backend.sdk import KIRO2Agent, create_workflow

    agent = KIRO2Agent(domain="backend")
    result = await agent.execute("Analiz yap")

Modüller:
    - claude_agent_wrapper: KIRO2Agent sınıfı
    - tool_definitions: Tool registry ve tanımları
    - workflow_definitions: Workflow decorator'ları
"""

from backend.sdk.claude_agent_wrapper import AgentConfig, KIRO2Agent
from backend.sdk.tool_definitions import (
    BACKEND_TOOLS,
    FRONTEND_TOOLS,
    RESEARCH_TOOLS,
    TESTING_TOOLS,
    ToolRegistry,
    get_domain_tools,
    register_tool,
)
from backend.sdk.workflow_definitions import (
    WorkflowRegistry,
    WorkflowStep,
    create_workflow,
    workflow,
)

__version__ = "1.0.0"
__author__ = "KIRO2 Team"

__all__ = [
    # Agent
    "KIRO2Agent",
    "AgentConfig",
    # Tools
    "ToolRegistry",
    "get_domain_tools",
    "register_tool",
    "BACKEND_TOOLS",
    "FRONTEND_TOOLS",
    "TESTING_TOOLS",
    "RESEARCH_TOOLS",
    # Workflows
    "workflow",
    "create_workflow",
    "WorkflowRegistry",
    "WorkflowStep",
]
