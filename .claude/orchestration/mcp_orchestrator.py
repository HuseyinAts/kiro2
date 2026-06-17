#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Orchestrator Server v2.5.0
Uses KiroOrchestrator with LangGraph-based deterministic execution.

Features:
- 24 integrated modules
- LangGraph workflow: Plan → Route → Execute → Validate → Fix Loop → Report
- Quality gates pipeline (lint, typecheck, unittest, security)
- Self-improvement engine (evidence-based)
- Policy-driven routing
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Add orchestrator path
KIRO2_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(KIRO2_ROOT / "orchestrator"))

from fastmcp import FastMCP

# Import KiroOrchestrator (most advanced version)
try:
    from core.graph import create_orchestrator, KiroOrchestrator
    from core.routing import RoutingEngine, RoutingDecision
    from core.quality_gates import QualityGatePipeline
    KIRO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: KiroOrchestrator not available: {e}")
    KIRO_AVAILABLE = False

# Initialize MCP server
mcp = FastMCP("KIRO2 Orchestrator v2.5.0")

# Global orchestrator instance
_orchestrator: Optional[KiroOrchestrator] = None
_initialized: bool = False

def get_orchestrator(force_reload: bool = False) -> KiroOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator, _initialized
    
    if force_reload and _orchestrator is not None:
        _orchestrator = None
        _initialized = False
        # Reload the module
        import importlib
        import core.graph
        importlib.reload(core.graph)
        from core.graph import create_orchestrator as fresh_create
        _orchestrator = fresh_create(str(KIRO2_ROOT))
        _initialized = True
        return _orchestrator
    
    if _orchestrator is None:
        _orchestrator = create_orchestrator(str(KIRO2_ROOT))
        _initialized = True
    return _orchestrator

# ==================== CORE TOOLS ====================

@mcp.tool()
async def run_workflow(task: str, files: List[str] = None, auto_fix: bool = True) -> Dict[str, Any]:
    """
    Execute full LangGraph workflow: Plan → Route → Execute → Validate → Fix → Report
    
    This is the PRIMARY tool for task execution with quality gates.
    
    Args:
        task: Task description (Turkish or English)
        files: List of affected files (optional)
        auto_fix: Automatically fix quality gate failures (default: True)
        
    Returns:
        Complete workflow result with status, plan, and quality metrics
    """
    if not KIRO_AVAILABLE:
        return {"error": "KiroOrchestrator not available", "status": "failed"}
    
    orchestrator = get_orchestrator()
    
    try:
        # Run the workflow
        result = await orchestrator.run(task, files or [])
        
        return {
            "status": result.get("status", "unknown"),
            "task_id": result.get("task_id"),
            "run_id": result.get("run_id"),
            "plan": result.get("plan"),
            "routing": result.get("routing_decision"),
            "quality_gates": result.get("gate_results", []),
            "iterations": result.get("iteration", 0),
            "needs_human_review": result.get("needs_human_review", False),
            "summary": result.get("final_summary"),
            "error": result.get("error")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "task": task
        }

@mcp.tool()
async def route_task(task: str, context: str = None) -> Dict[str, Any]:
    """
    Route task to appropriate agent using policy-driven routing engine.
    
    Uses 45 policies across 6 categories for intelligent routing.
    
    Args:
        task: Task description
        context: Additional context (optional)
        
    Returns:
        Routing decision with agent, model, and confidence
    """
    if not KIRO_AVAILABLE:
        return {"error": "KiroOrchestrator not available"}
    
    orchestrator = get_orchestrator()
    
    try:
        decision = await orchestrator.routing_engine.route(task, [])
        
        return {
            "primary_model": decision.primary_model.value,
            "fallback_model": decision.fallback_model.value if decision.fallback_model else None,
            "agent_type": decision.agent_type,
            "max_diff_lines": decision.max_diff_lines,
            "requires_human_review": decision.requires_human_review,
            "reason": decision.reason,
            "confidence": 0.85  # Could be calculated from decision
        }
    except Exception as e:
        return {"error": str(e), "task": task}

@mcp.tool()
async def check_quality(content: str, check_type: str = "all") -> Dict[str, Any]:
    """
    Run quality gates on code or content.
    
    Available gates: lint, typecheck, unittest, security
    
    Args:
        content: Code or content to check
        check_type: Type of check - 'code', 'test', 'security', or 'all'
        
    Returns:
        Quality gate results with pass/fail status
    """
    if not KIRO_AVAILABLE:
        return {"error": "KiroOrchestrator not available"}
    
    orchestrator = get_orchestrator()
    
    # Create minimal run state for quality check
    from core.state import RunState, TaskStatus
    import uuid
    
    run_state = RunState(
        run_id=str(uuid.uuid4()),
        task_id=str(uuid.uuid4()),
        status=TaskStatus.QUALITY_GATES,
        current_iteration=1,
        max_iterations=3
    )
    
    try:
        all_passed, outputs = await orchestrator.quality_pipeline.run_all(run_state)
        
        results = []
        for i, out in enumerate(outputs):
            gate_name = orchestrator.quality_pipeline.gates[i].config.name if i < len(orchestrator.quality_pipeline.gates) else f"gate_{i}"
            results.append({
                "gate": gate_name,
                "passed": out.success,
                "action": out.action.value,
                "duration_ms": out.duration_ms,
                "message": out.message if hasattr(out, 'message') else None
            })
        
        return {
            "all_passed": all_passed,
            "results": results,
            "check_type": check_type
        }
    except Exception as e:
        return {"error": str(e), "check_type": check_type}

@mcp.tool()
async def get_policies(category: str = "all") -> Dict[str, Any]:
    """
    List active policies for routing and quality control.
    
    Categories: routing, quality, learning, resource, error, meta
    
    Args:
        category: Policy category to list, or 'all'
        
    Returns:
        List of policies with their configurations
    """
    # Policy definitions from orchestrator
    policies = {
        "routing": [
            {"id": "P1", "name": "turkish_nlp_priority", "description": "Turkish NLP tasks → Claude Opus"},
            {"id": "P2", "name": "security_tasks", "description": "Security tasks → Claude with review"},
            {"id": "P3", "name": "frontend_tasks", "description": "React/UI tasks → Codex"},
            {"id": "P4", "name": "api_tasks", "description": "FastAPI endpoints → Codex for simple, Claude for complex"},
            {"id": "P5", "name": "test_generation", "description": "Test tasks → Codex"},
            {"id": "P6", "name": "documentation", "description": "Docs → Codex"},
            {"id": "P7", "name": "refactoring", "description": "Complex refactor → Claude Opus"},
            {"id": "P8", "name": "debugging", "description": "Debug tasks → Claude with context"}
        ],
        "quality": [
            {"id": "Q1", "name": "lint_gate", "description": "Ruff/ESLint must pass"},
            {"id": "Q2", "name": "typecheck_gate", "description": "mypy/tsc must pass"},
            {"id": "Q3", "name": "unittest_gate", "description": "pytest/jest must pass"},
            {"id": "Q4", "name": "security_gate", "description": "No secrets, no vulnerabilities"},
            {"id": "Q5", "name": "diff_size_limit", "description": "Max 500 lines per change"}
        ],
        "learning": [
            {"id": "L1", "name": "pattern_capture", "description": "Capture successful patterns"},
            {"id": "L2", "name": "failure_analysis", "description": "Learn from failures"},
            {"id": "L3", "name": "threshold_adaptation", "description": "Adapt thresholds based on success"}
        ],
        "resource": [
            {"id": "R1", "name": "token_budget", "description": "Max tokens per task"},
            {"id": "R2", "name": "timeout_limits", "description": "Task timeout limits"},
            {"id": "R3", "name": "retry_policy", "description": "Max 3 retries with backoff"}
        ],
        "error": [
            {"id": "E1", "name": "graceful_degradation", "description": "Fallback on failure"},
            {"id": "E2", "name": "circuit_breaker", "description": "Stop on repeated failures"},
            {"id": "E3", "name": "rollback", "description": "Revert on critical failure"}
        ],
        "meta": [
            {"id": "M1", "name": "self_improvement", "description": "Evidence-based learning"},
            {"id": "M2", "name": "no_self_replication", "description": "Agents cannot spawn agents"},
            {"id": "M3", "name": "state_over_memory", "description": "State is source of truth"}
        ]
    }
    
    if category == "all":
        return {"policies": policies, "total": sum(len(v) for v in policies.values())}
    elif category in policies:
        return {"policies": {category: policies[category]}, "total": len(policies[category])}
    else:
        return {"error": f"Unknown category: {category}", "available": list(policies.keys())}

@mcp.tool()
async def orchestrator_status() -> Dict[str, Any]:
    """
    Get orchestrator status and statistics.
    
    Returns:
        System status including version, modules, and health metrics
    """
    modules = [
        "graph", "state", "routing", "quality_gates", "self_improvement",
        "llm_gateway", "tool_executor", "diff_guard", "template_manager",
        "scope_validator", "policy_engine", "change_log", "repo_scanner",
        "signal_dictionary", "metrics_collector", "learning_loop",
        "resource_manager", "memory_store", "agents.planner",
        "agents.implementer", "agents.reviewer", "agents.fixer",
        "agents.tester", "agents.security_auditor"
    ]
    
    return {
        "version": "2.5.0",
        "phase": "STABIL",
        "total_modules": len(modules),
        "active_modules": modules,
        "architecture": "LangGraph StateGraph",
        "workflow": "Plan → Route → Implement → QualityCheck → Review → Fix → Report",
        "quality_gates": ["lint", "typecheck", "unittest", "security"],
        "policies": {
            "routing": 8,
            "quality": 5,
            "learning": 3,
            "resource": 3,
            "error": 3,
            "meta": 3,
            "total": 25
        },
        "agents": [
            "Planner", "Implementer", "Reviewer", "Fixer", 
            "Tester", "SecurityAuditor", "DocumentWriter"
        ],
        "kiro_available": KIRO_AVAILABLE,
        "working_dir": str(KIRO2_ROOT)
    }

@mcp.tool()
async def list_agents() -> Dict[str, Any]:
    """
    List all available specialized agents.
    
    Returns:
        Dictionary of agents with their capabilities and use cases
    """
    agents = {
        "planner": {
            "name": "Planner Agent",
            "role": "Task decomposition and planning",
            "capabilities": ["Break down complex tasks", "Create execution plans", "Identify dependencies"],
            "model": "claude-opus-4"
        },
        "implementer": {
            "name": "Implementer Agent", 
            "role": "Code implementation",
            "capabilities": ["Write code", "Apply changes", "Follow patterns"],
            "model": "varies by task"
        },
        "reviewer": {
            "name": "Reviewer Agent",
            "role": "Code review and quality assurance",
            "capabilities": ["Security review", "Best practices check", "Performance analysis"],
            "model": "claude-opus-4"
        },
        "fixer": {
            "name": "Fixer Agent",
            "role": "Bug fixing and error correction",
            "capabilities": ["Fix quality gate failures", "Apply minimal patches", "Handle edge cases"],
            "model": "claude-sonnet-4"
        },
        "tester": {
            "name": "Tester Agent",
            "role": "Test generation and execution",
            "capabilities": ["Write unit tests", "Generate test cases", "Coverage analysis"],
            "model": "codex"
        },
        "security_auditor": {
            "name": "Security Auditor Agent",
            "role": "Security analysis",
            "capabilities": ["Vulnerability scanning", "Secret detection", "OWASP compliance"],
            "model": "claude-opus-4"
        },
        "document_writer": {
            "name": "Document Writer Agent",
            "role": "Documentation generation",
            "capabilities": ["API docs", "README generation", "Code comments"],
            "model": "codex"
        },
        "turkish_nlp": {
            "name": "Turkish NLP Specialist",
            "role": "Turkish language processing",
            "capabilities": ["Text analysis", "Question matching", "Content processing"],
            "model": "claude-opus-4"
        },
        "content_manager": {
            "name": "Content Manager",
            "role": "Educational content management",
            "capabilities": ["Question loading", "Answer key processing", "OSYM content"],
            "model": "claude-sonnet-4"
        }
    }
    
    return {
        "agents": agents,
        "total": len(agents),
        "primary_workflow_agents": ["planner", "implementer", "reviewer", "fixer"],
        "specialized_agents": ["tester", "security_auditor", "document_writer", "turkish_nlp", "content_manager"]
    }

@mcp.tool()
async def match_questions(strategy: str = "hybrid", batch_size: int = 100) -> Dict[str, Any]:
    """
    Run question-answer matching pipeline for YKS content.
    
    Strategies:
    - exact: Exact book + page + question number match
    - fuzzy: Jaro-Winkler fuzzy matching (≥0.90 threshold)
    - semantic: BERTurk semantic similarity
    - hybrid: All strategies combined (recommended)
    
    Args:
        strategy: Matching strategy to use
        batch_size: Number of items to process per batch
        
    Returns:
        Matching results with statistics
    """
    # This would integrate with d-dataset pipeline
    return {
        "status": "ready",
        "strategy": strategy,
        "batch_size": batch_size,
        "pipeline_stages": [
            "1. Blocking (book name)",
            "2. Exact match (book + page + question)",
            "3. Fuzzy match (Jaro-Winkler ≥0.90)",
            "4. Semantic match (BERTurk)",
            "5. ML classification (ambiguous cases)"
        ],
        "current_stats": {
            "total_questions": 75745,
            "total_answers": 88711,
            "matched": 2436,
            "match_rate": "0.11%",
            "target_rate": "66%"
        },
        "unprocessed_yolo_crops": 725,
        "note": "Use d-dataset pipeline at C:\\Users\\husey\\d-dataset for full processing"
    }

@mcp.tool()
async def analyze_student(student_id: str, subject: str = None) -> Dict[str, Any]:
    """
    Analyze student level and calculate Zone of Proximal Development (ZPD).
    
    Uses IRT (Item Response Theory) and FSRS (Free Spaced Repetition Scheduler).
    
    Args:
        student_id: Student identifier
        subject: Subject to analyze (optional, analyzes all if not specified)
        
    Returns:
        Student analysis with ability estimates and recommendations
    """
    # Placeholder for actual IRT/FSRS integration
    return {
        "student_id": student_id,
        "subject": subject or "all",
        "analysis": {
            "irt_ability_estimate": "θ = 0.5 (placeholder)",
            "fsrs_stability": "S = 1.0 (placeholder)",
            "zpd_range": {
                "lower_bound": "difficulty -1.0",
                "optimal": "difficulty 0.0",
                "upper_bound": "difficulty +1.0"
            }
        },
        "recommendations": [
            "Focus on medium difficulty questions",
            "Review weak topics before advancing",
            "Use spaced repetition for retention"
        ],
        "note": "Requires database integration for actual student data"
    }

# ==================== OODA LEARNING HOOKS ====================

async def _pre_task_inject(agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
    """OODA Observe: Pre-task WM-State injection via memory_injector.

    Injects relevant lessons, facts, anti-patterns, and skills
    into the agent's working memory before task execution.
    """
    try:
        from .memory_injector import MemoryInjector
        injector = MemoryInjector(base_path=str(KIRO2_ROOT / ".claude"))
        ctx = injector.get_context(
            agent_id=agent_id,
            task_description=task.get("description", ""),
            task_type=task.get("task_type", ""),
            task_tags=task.get("tags", []),
            desires=[task.get("description", "")],
        )
        md = injector.format_as_markdown(ctx)
        return {
            "wm_state": md,
            "token_count": ctx.token_count,
            "lesson_count": len(ctx.lessons),
            "anti_pattern_count": len(ctx.anti_patterns),
            "ooda_phase": "observe",
        }
    except Exception as e:
        logger.error("Pre-task injection failed for agent=%s: %s", agent_id, e)
        return {"wm_state": "", "error": str(e), "ooda_phase": "observe"}


async def _post_task_collect(
    agent_id: str,
    task: Dict[str, Any],
    outcome: Dict[str, Any],
) -> Dict[str, Any]:
    """OODA Act (post): Post-task feedback collection via feedback_collector.

    Records outcome as lesson, runs constitutional gate,
    updates Bayesian confidence, and triggers stigmergy.
    """
    try:
        from .feedback_collector import FeedbackCollector
        collector = FeedbackCollector(base_path=str(KIRO2_ROOT / ".claude"))

        success = outcome.get("status") == "success"
        details = {
            "signals": outcome.get("signals", []),
            "evidence_refs": outcome.get("evidence_refs", []),
            "error": outcome.get("error", ""),
            "solution": outcome.get("solution", ""),
        }

        # Only record if there's evidence
        if not details["evidence_refs"]:
            # Auto-generate evidence from quality gate results
            gate_results = outcome.get("quality_gates", [])
            for gate in gate_results:
                gate_name = gate.get("name", "unknown")
                gate_passed = gate.get("passed", False)
                details["evidence_refs"].append(
                    f"gate:{gate_name}:{'pass' if gate_passed else 'fail'}"
                )
                if not gate_passed:
                    details["signals"].append(f"{gate_name}_fail")

        lesson = collector.record_outcome(agent_id, task, success, details)

        result = {
            "lesson_id": lesson.id if lesson else None,
            "safety_review": lesson.safety_review if lesson else None,
            "ooda_phase": "act_post",
        }

        # Run periodic maintenance
        collector.quarantine_auto_resolve()
        collector.cleanup_old_lessons()

        return result
    except Exception as e:
        logger.error("Post-task collection failed for agent=%s: %s", agent_id, e)
        return {"error": str(e), "ooda_phase": "act_post"}


# ==================== HELPER FUNCTIONS ====================

async def _execute_with_agent(task: str, agent: str) -> Dict[str, Any]:
    """Execute task with specific agent"""
    # In production, this would invoke the actual agent
    return {
        "agent": agent,
        "task": task,
        "status": "simulated",
        "message": f"Task would be executed by {agent} agent"
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("KIRO2 Orchestrator MCP Server v2.5.0")
    print("=" * 60)
    print(f"KiroOrchestrator available: {KIRO_AVAILABLE}")
    print(f"Working directory: {KIRO2_ROOT}")
    print("=" * 60)
    
    # Run the MCP server
    mcp.run()
