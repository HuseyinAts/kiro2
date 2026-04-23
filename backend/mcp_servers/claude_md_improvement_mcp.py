"""
CLAUDE.md Self-Improvement MCP Server

Bu MCP server, CLAUDE.md otomatik iyileştirme mekanizması için
dış servislerle entegrasyon sağlar.

Tools:
- record_feedback: Task feedback kaydet
- get_effectiveness: Rule effectiveness getir
- trigger_analysis: Manuel analiz tetikle
- check_safety: Safety guardrails kontrol

Entegrasyonlar:
- chromadb-mcp: Rule embedding'leri için semantic search
- zemberek-mcp: Türkçe metin analizi

Spec: claude-md-self-improvement REQ-9, REQ-10
- Boris Cherny verification feedback loops
- Daisy Stanton Exit Code 2 mekanizması

Author: KIRO2 Team
Date: 2026-01-17
"""

import json
from typing import Any

# MCP imports
try:
    from mcp.server import Server
    from mcp.types import TextContent, Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None  # type: ignore

# FastMCP for easy server creation
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None  # type: ignore

# Rate limiting
import time
from collections import defaultdict


class RateLimiter:
    """Rate limiter for MCP tools."""

    def __init__(self, max_requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str = "global") -> tuple[bool, int]:
        """Check if request is allowed."""
        now = time.time()
        cutoff = now - self.window

        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

        if len(self._requests[key]) >= self.max_requests:
            return False, 0

        self._requests[key].append(now)
        remaining = self.max_requests - len(self._requests[key])
        return True, remaining


# Global instances
_rate_limiter = RateLimiter()


# Create MCP server
if FASTMCP_AVAILABLE:
    mcp = FastMCP("claude-md-improvement")
else:
    mcp = None


# Tool implementations
async def record_feedback_impl(
    task_id: str,
    success: bool,
    rule_id: str | None = None,
    rating: int | None = None,
    comment: str | None = None,
    execution_time: float = 0.0,
) -> dict[str, Any]:
    """
    Task feedback kaydeder.

    Args:
        task_id: Task ID
        success: Başarılı mı
        rule_id: İlgili CLAUDE.md rule ID
        rating: Kullanıcı puanı (1-5)
        comment: Kullanıcı yorumu
        execution_time: Çalışma süresi

    Returns:
        Kayıt sonucu
    """
    # Rate limiting
    allowed, remaining = _rate_limiter.is_allowed("record_feedback")
    if not allowed:
        return {
            "success": False,
            "error": "Rate limit exceeded",
            "retry_after": 60,
        }

    # Import here to avoid circular dependency
    try:
        from backend.hooks.claude_md_improvement import get_orchestrator

        orchestrator = get_orchestrator()

        if rating is not None:
            # User feedback
            result = await orchestrator.feedback_hook.record_user_feedback(
                task_id=task_id,
                rating=rating,
                comment=comment,
                rule_id=rule_id,
            )
        else:
            # Automatic feedback
            result = await orchestrator.record_task_completion(
                task_id=task_id,
                success=success,
                rule_id=rule_id,
                execution_time=execution_time,
            )

        return {
            "success": True,
            "exit_code": result.exit_code,
            "message": result.message,
            "remaining_requests": remaining,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "exit_code": 2,  # Blocking error
        }


async def get_effectiveness_impl(rule_id: str) -> dict[str, Any]:
    """
    Rule effectiveness skorunu getirir.

    Args:
        rule_id: CLAUDE.md rule ID

    Returns:
        Effectiveness bilgisi
    """
    allowed, remaining = _rate_limiter.is_allowed("get_effectiveness")
    if not allowed:
        return {"success": False, "error": "Rate limit exceeded"}

    try:
        from backend.hooks.claude_md_improvement import get_orchestrator

        orchestrator = get_orchestrator()
        effectiveness = await orchestrator.get_rule_effectiveness(rule_id)

        if effectiveness is None:
            return {
                "success": False,
                "error": f"Rule not found: {rule_id}",
            }

        return {
            "success": True,
            "rule_id": rule_id,
            "effectiveness_score": effectiveness.effectiveness_score,
            "confidence": effectiveness.confidence,
            "total_feedback": effectiveness.total_feedback,
            "success_count": effectiveness.success_count,
            "failure_count": effectiveness.failure_count,
            "needs_improvement": effectiveness.needs_improvement,
            "last_updated": effectiveness.last_updated.isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def trigger_analysis_impl() -> dict[str, Any]:
    """
    Manuel analiz tetikler.

    Returns:
        Analiz sonuçları
    """
    allowed, remaining = _rate_limiter.is_allowed("trigger_analysis")
    if not allowed:
        return {"success": False, "error": "Rate limit exceeded"}

    try:
        from backend.hooks.claude_md_improvement import get_orchestrator

        orchestrator = get_orchestrator()
        analysis = await orchestrator.trigger_manual_analysis()

        return {
            "success": True,
            "analyzed_at": analysis["analyzed_at"],
            "pending_improvements": len(analysis["pending_improvements"]),
            "average_effectiveness": analysis["average_effectiveness"],
            "improvements": analysis["pending_improvements"][:5],  # Top 5
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def check_safety_impl(
    action: str, rule_id: str | None = None
) -> dict[str, Any]:
    """
    Safety guardrails kontrol eder.

    Args:
        action: Yapılacak aksiyon
        rule_id: İlgili rule ID

    Returns:
        Safety kontrol sonucu
    """
    allowed, remaining = _rate_limiter.is_allowed("check_safety")
    if not allowed:
        return {"success": False, "error": "Rate limit exceeded"}

    # Risky keywords
    risky_keywords = [
        "delete",
        "drop",
        "truncate",
        "remove all",
        "force",
        "rm -rf",
        "eval",
        "exec",
    ]

    action_lower = action.lower()
    detected_risks = [kw for kw in risky_keywords if kw in action_lower]

    if detected_risks:
        return {
            "success": False,
            "safe": False,
            "exit_code": 2,
            "message": f"Riskli pattern tespit edildi: {', '.join(detected_risks)}",
            "requires_approval": True,
        }

    return {
        "success": True,
        "safe": True,
        "exit_code": 0,
        "message": "Safety check geçti",
        "requires_approval": False,
    }


async def get_status_impl() -> dict[str, Any]:
    """
    Orchestrator durumunu getirir.

    Returns:
        Durum bilgisi
    """
    try:
        from backend.hooks.claude_md_improvement import get_orchestrator

        orchestrator = get_orchestrator()
        status = await orchestrator.get_status()

        return {
            "success": True,
            **status,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Register tools with FastMCP
if mcp is not None:

    @mcp.tool()
    async def record_feedback(
        task_id: str,
        success: bool,
        rule_id: str = "",
        rating: int = 0,
        comment: str = "",
        execution_time: float = 0.0,
    ) -> str:
        """
        Task feedback kaydeder.

        Args:
            task_id: Task ID
            success: Başarılı mı
            rule_id: İlgili CLAUDE.md rule ID
            rating: Kullanıcı puanı (1-5), 0 = yok
            comment: Kullanıcı yorumu
            execution_time: Çalışma süresi

        Returns:
            JSON format feedback kaydı sonucu
        """
        result = await record_feedback_impl(
            task_id=task_id,
            success=success,
            rule_id=rule_id if rule_id else None,
            rating=rating if rating > 0 else None,
            comment=comment if comment else None,
            execution_time=execution_time,
        )
        return json.dumps(result, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def get_rule_effectiveness(rule_id: str) -> str:
        """
        Rule effectiveness skorunu getirir.

        Args:
            rule_id: CLAUDE.md rule ID

        Returns:
            JSON format effectiveness bilgisi
        """
        result = await get_effectiveness_impl(rule_id)
        return json.dumps(result, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def analyze_improvements() -> str:
        """
        Manuel iyileştirme analizi tetikler.

        Returns:
            JSON format analiz sonuçları
        """
        result = await trigger_analysis_impl()
        return json.dumps(result, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def safety_check(action: str, rule_id: str = "") -> str:
        """
        Safety guardrails kontrol eder.

        Args:
            action: Yapılacak aksiyon
            rule_id: İlgili rule ID

        Returns:
            JSON format safety kontrol sonucu
        """
        result = await check_safety_impl(action, rule_id if rule_id else None)
        return json.dumps(result, indent=2, ensure_ascii=False)

    @mcp.tool()
    async def orchestrator_status() -> str:
        """
        Self-improvement orchestrator durumunu getirir.

        Returns:
            JSON format durum bilgisi
        """
        result = await get_status_impl()
        return json.dumps(result, indent=2, ensure_ascii=False)


def create_mcp_server():
    """Create and return MCP server instance."""
    return mcp


if __name__ == "__main__":
    if mcp is not None:
        mcp.run()
    else:
        print("MCP dependencies not available. Install with: pip install mcp fastmcp")
