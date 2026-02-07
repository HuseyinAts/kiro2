"""
KIRO2 Orchestrator - Tam Otonom Multi-Agent Orkestrasyon Sistemi

Bu modül, KIRO2 platformu için LangGraph tabanlı deterministic
orchestration sağlar. "Doğru Kod" prensipleri ile tasarlanmıştır:

- STATE her şeyin üstünde
- Minimum değişiklik prensibi
- Kanıt olmadan öğrenme yok
- Güvenlik whitelist tabanlı

Kullanım:
    from orchestrator import create_orchestrator, run_task
    
    # Orchestrator oluştur
    orch = create_orchestrator()
    
    # Task çalıştır
    result = await run_task(orch, "Fix authentication bug in login.py")

Modüller:
    - core.state: Redis run-scoped state yönetimi
    - core.memory: PostgreSQL persistent learning
    - core.quality_gates: Lint→TypeCheck→Test→Security pipeline
    - core.routing: Policy-driven task→model routing
    - core.self_improvement: Kanıt tabanlı iyileştirme
    - core.graph: LangGraph workflow orchestration
    - core.llm_gateway: Multi-provider LLM gateway
    - core.tool_executor: Sandboxed tool execution
    - core.agents: Specialized agent implementations
"""

__version__ = "2.0.0"
__author__ = "KIRO2 Team"

# Core state management
from orchestrator.core.state import (
    RunState,
    DiffStats,
    TaskStatus,
)

# Diff guard
from orchestrator.core.diff_guard import (
    DiffLimits,
    DiffGuard,
    DIFF_LIMITS,
)

# Persistent memory/learning
from orchestrator.core.memory import (
    Lesson,
    ConfidenceLevel,
    MemoryStore,
)

# Quality gates
from orchestrator.core.quality_gates import (
    QualityGate,
    GateResult,
    LintGate,
    TypeCheckGate,
    UnitTestGate,
    SecurityGate,
    QualityGatePipeline,
)

# Routing
from orchestrator.core.routing import (
    TaskType,
    RiskLevel,
    ModelChoice,
    RoutingDecision,
    RoutingEngine,
)

# Self-improvement
from orchestrator.core.self_improvement import (
    ImprovementAction,
    SelfImprovementEngine,
)

# LLM Gateway
from orchestrator.core.llm_gateway import (
    LLMResponse,
    ClaudeClient,
    OpenAIClient,
    LLMGateway,
    MODEL_PRICING,
)

# Tool Executor
from orchestrator.core.tool_executor import (
    ToolCategory,
    ToolResult,
    FileOperations,
    ShellExecutor,
    LintRunner,
    TestRunner,
    SandboxToolExecutor,
    TOOL_ALLOWLIST,
    TOOL_BLOCKLIST,
)

# Agents
from orchestrator.core.agents import (
    AgentRole,
    AgentOutput,
    Agent,
    PlannerAgent,
    ImplementerAgent,
    ReviewerAgent,
    FixerAgent,
    TesterAgent,
    SecurityAuditorAgent,
    DocumentWriterAgent,
    AgentFactory,
    get_agent,
    AGENT_PROMPTS,
)

# Graph orchestration - disabled (LangGraph dependency missing)
# from orchestrator.core.graph import (
#     GraphState,
#     OrchestratorGraph,
#     create_orchestrator,
# )

# Convenience exports
__all__ = [
    # Version
    "__version__",
    
    # State
    "RunState",
    "DiffStats", 
    "TaskStatus",
    
    # Diff Guard
    "DiffLimits",
    "DiffGuard",
    "DIFF_LIMITS",
    
    # Memory
    "Lesson",
    "ConfidenceLevel",
    "MemoryStore",
    
    # Quality Gates
    "QualityGate",
    "GateResult",
    "LintGate",
    "TypeCheckGate",
    "UnitTestGate",
    "SecurityGate",
    "QualityGatePipeline",
    
    # Routing
    "TaskType",
    "RiskLevel",
    "ModelChoice",
    "RoutingDecision",
    "RoutingEngine",
    
    # Self-improvement
    "ImprovementAction",
    "SelfImprovementEngine",
    
    # LLM Gateway
    "LLMResponse",
    "ClaudeClient",
    "OpenAIClient",
    "LLMGateway",
    "MODEL_PRICING",
    
    # Tool Executor
    "ToolCategory",
    "ToolResult",
    "FileOperations",
    "ShellExecutor",
    "LintRunner",
    "TestRunner",
    "SandboxToolExecutor",
    "TOOL_ALLOWLIST",
    "TOOL_BLOCKLIST",
    
    # Agents
    "AgentRole",
    "AgentOutput",
    "Agent",
    "PlannerAgent",
    "ImplementerAgent",
    "ReviewerAgent",
    "FixerAgent",
    "TesterAgent",
    "SecurityAuditorAgent",
    "DocumentWriterAgent",
    "AgentFactory",
    "get_agent",
    "AGENT_PROMPTS",
    
    # Graph - disabled (LangGraph dependency missing)
    # "GraphState",
    # "OrchestratorGraph",
    # "create_orchestrator",
]


# Quick start helper
async def run_task(task_description: str, project_root: str = ".") -> dict:
    """
    Hızlı başlangıç için yardımcı fonksiyon.

    Args:
        task_description: Yapılacak görevin açıklaması
        project_root: Proje kök dizini

    Returns:
        Orchestration sonucu (success, output, iterations, cost)

    Example:
        result = await run_task("Fix the login bug", "/path/to/project")
        if result["success"]:
            print(f"Task completed in {result['iterations']} iterations")
    """
    from pathlib import Path
    from orchestrator.core.graph import create_orchestrator

    # Orchestrator oluştur
    orchestrator = create_orchestrator(project_root)

    # Graph'ı çalıştır
    final_state = await orchestrator.run(
        task_description=task_description,
        files=[]
    )

    return {
        "success": final_state.get("status") == "completed",
        "status": final_state.get("status"),
        "iterations": final_state.get("iteration", 0),
        "files_changed": final_state.get("affected_files", []),
        "errors": [final_state.get("error")] if final_state.get("error") else [],
        "cost_total": 0.0,  # TODO: Track cost in orchestrator
    }
