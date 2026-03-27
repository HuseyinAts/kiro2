"""
KIRO2 Orchestrator - Main Orchestration Graph (LangGraph)
=========================================================
Deterministik orkestrasyon: Plan → İcra → Doğrulama → Düzeltme

StateGraph ile kontrol:
- Standart akış: Planner → Implementer → Quality Gates → Reviewer → Fix Loop → Reporter
- Her adımın çıktısı "kontratlıdır"
- Stop conditions: max iterasyon + no-progress detection
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal, TypedDict

# LangGraph imports
from langgraph.graph import END, StateGraph

try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        # Fallback: in-memory checkpoint without persistence
        MemorySaver = None

from .quality_gates import QualityGatePipeline
from .routing import RoutingEngine
from .state import RunState, TaskStatus, get_state_store


class OrchestratorState(TypedDict):
    """LangGraph state for orchestrator"""

    # Kimlik
    run_id: str
    task_id: str

    # Giriş
    task_description: str
    affected_files: list[str]

    # Plan
    plan: str | None
    routing_decision: dict | None

    # Yürütme
    current_step: str
    iteration: int
    max_iterations: int

    # Sonuçlar
    implementation_result: str | None
    gate_results: list[dict]
    review_comments: list[str]

    # Durum
    status: str
    error: str | None
    needs_human_review: bool

    # Çıktı
    final_summary: str | None


def create_initial_state(
    task_description: str, affected_files: list[str] = None, task_id: str = None
) -> OrchestratorState:
    """Başlangıç state'i oluştur"""
    return OrchestratorState(
        run_id=str(uuid.uuid4()),
        task_id=task_id or str(uuid.uuid4()),
        task_description=task_description,
        affected_files=affected_files or [],
        plan=None,
        routing_decision=None,
        current_step="init",
        iteration=0,
        max_iterations=10,
        implementation_result=None,
        gate_results=[],
        review_comments=[],
        status="pending",
        error=None,
        needs_human_review=False,
        final_summary=None,
    )


class KiroOrchestrator:
    """
    Ana orkestrasyon sınıfı.

    LangGraph StateGraph ile deterministik yürütme.
    """

    def __init__(self, working_dir: Path):
        self.working_dir = working_dir
        self.routing_engine = RoutingEngine()
        self.quality_pipeline = QualityGatePipeline(working_dir)
        self.state_store = get_state_store()

        # Loop guardrail — sonsuz döngü koruması
        from .loop_guardrail import GuardrailAction, LoopGuardrail

        self.loop_guardrail = LoopGuardrail()
        self._GuardrailAction = GuardrailAction

        # Checkpointer ÖNCE oluştur (graph'ın kullanması için)
        self.checkpointer = MemorySaver() if MemorySaver is not None else None

        # Graph oluştur
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph akışını oluştur"""

        # StateGraph tanımla
        workflow = StateGraph(OrchestratorState)

        # Node'ları ekle
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("route", self._route_node)
        workflow.add_node("implement", self._implement_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("review", self._review_node)
        workflow.add_node("fix", self._fix_node)
        workflow.add_node("report", self._report_node)

        # Başlangıç
        workflow.set_entry_point("plan")

        # Kenarları ekle
        workflow.add_edge("plan", "route")
        workflow.add_edge("route", "implement")
        workflow.add_edge("implement", "quality_check")

        # Quality check sonrası conditional
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_check_router,
            {
                "review": "review",
                "fix": "fix",
                "blocked": "report",
            },
        )

        # Review sonrası conditional
        workflow.add_conditional_edges(
            "review",
            self._review_router,
            {
                "complete": "report",
                "fix": "fix",
            },
        )

        # Fix sonrası quality_check'e dön
        workflow.add_edge("fix", "quality_check")

        # Report → END
        workflow.add_edge("report", END)

        return workflow.compile(checkpointer=self.checkpointer)

    # ==================== NODES ====================

    async def _plan_node(self, state: OrchestratorState) -> OrchestratorState:
        """Planlama node'u"""
        state["current_step"] = "planning"
        state["status"] = "planning"

        # TODO: LLM ile plan oluştur
        # Şimdilik basit plan
        state["plan"] = f"""
Plan for: {state["task_description"]}

Affected files: {", ".join(state["affected_files"]) or "To be determined"}

Steps:
1. Analyze the task requirements
2. Implement necessary changes
3. Run quality gates
4. Review and finalize
"""

        return state

    async def _route_node(self, state: OrchestratorState) -> OrchestratorState:
        """Routing node'u"""
        state["current_step"] = "routing"

        decision = await self.routing_engine.route(
            state["task_description"], state["affected_files"]
        )

        state["routing_decision"] = {
            "primary_model": decision.primary_model.value,
            "fallback_model": decision.fallback_model.value if decision.fallback_model else None,
            "agent_type": decision.agent_type,
            "max_diff_lines": decision.max_diff_lines,
            "requires_human_review": decision.requires_human_review,
            "reason": decision.reason,
        }

        state["needs_human_review"] = decision.requires_human_review

        return state

    async def _implement_node(self, state: OrchestratorState) -> OrchestratorState:
        """İmplementasyon node'u"""
        state["current_step"] = "implementing"
        state["status"] = "executing"
        state["iteration"] += 1

        # TODO: LLM ile implementasyon
        # Model seçimine göre Claude/Codex çağır

        state["implementation_result"] = (
            f"Implementation completed (iteration {state['iteration']})"
        )

        return state

    async def _quality_check_node(self, state: OrchestratorState) -> OrchestratorState:
        """Kalite kapıları node'u"""
        state["current_step"] = "quality_checking"
        state["status"] = "quality_gates"

        # Loop guardrail kontrolü
        run_state_for_guard = RunState(
            run_id=state["run_id"],
            task_id=state["task_id"],
            status=TaskStatus.QUALITY_GATES,
            current_iteration=state["iteration"],
            max_iterations=state["max_iterations"],
        )
        guard_result = self.loop_guardrail.check(run_state_for_guard)
        if guard_result.action == self._GuardrailAction.HALT:
            state["status"] = "blocked"
            state["error"] = f"Loop guardrail: {guard_result.message}"
            return state

        # RunState oluştur (quality gates için)
        run_state = RunState(
            run_id=state["run_id"],
            task_id=state["task_id"],
            status=TaskStatus.QUALITY_GATES,
            current_iteration=state["iteration"],
            max_iterations=state["max_iterations"],
        )

        # Quality gates çalıştır
        all_passed, outputs = await self.quality_pipeline.run_all(run_state)

        # Sonuçları kaydet
        state["gate_results"] = [
            {
                "gate": self.quality_pipeline.gates[i].config.name
                if i < len(self.quality_pipeline.gates)
                else "unknown",
                "success": out.success,
                "action": out.action.value,
                "duration_ms": out.duration_ms,
            }
            for i, out in enumerate(outputs)
        ]

        # Durum güncelle
        if run_state.status == TaskStatus.BLOCKED:
            state["status"] = "blocked"
            state["error"] = "Quality gates failed after max retries"
        elif all_passed:
            state["status"] = "gates_passed"
        else:
            state["status"] = "gates_failed"

        return state

    async def _review_node(self, state: OrchestratorState) -> OrchestratorState:
        """Review node'u"""
        state["current_step"] = "reviewing"
        state["status"] = "reviewing"

        # TODO: LLM ile code review
        # Şimdilik otomatik onay

        state["review_comments"] = ["Code review passed"]

        return state

    async def _fix_node(self, state: OrchestratorState) -> OrchestratorState:
        """Fix node'u"""
        state["iteration"] += 1
        state["current_step"] = "fixing"
        state["status"] = "fixing"

        # İterasyon kontrolü
        if state["iteration"] >= state["max_iterations"]:
            state["status"] = "blocked"
            state["error"] = "Max iterations reached"
            return state

        # TODO: Hata analizine göre fix stratejisi seç
        # Minimal patch veya alternative approach

        return state

    async def _report_node(self, state: OrchestratorState) -> OrchestratorState:
        """Rapor node'u"""
        state["current_step"] = "reporting"

        # Final durumu belirle
        if state["status"] == "blocked":
            final_status = "BLOCKED - Human intervention required"
        elif state["status"] == "gates_passed" or state["status"] == "reviewing":
            state["status"] = "completed"
            final_status = "COMPLETED"
        else:
            final_status = f"UNKNOWN: {state['status']}"

        # Özet oluştur
        state["final_summary"] = f"""
=== KIRO2 Orchestrator Report ===

Task ID: {state["task_id"]}
Run ID: {state["run_id"]}
Status: {final_status}

Description: {state["task_description"]}

Plan:
{state["plan"]}

Routing Decision:
- Model: {state["routing_decision"].get("primary_model") if state["routing_decision"] else "N/A"}
- Agent: {state["routing_decision"].get("agent_type") if state["routing_decision"] else "N/A"}

Quality Gates:
{self._format_gate_results(state["gate_results"])}

Iterations: {state["iteration"]}
Human Review Required: {state["needs_human_review"]}

{f"Error: {state['error']}" if state["error"] else ""}
"""

        # Self-improvement: başarılı run'ları kaydet
        if state["status"] == "completed":
            # TODO: Self-improvement engine'e bildir
            pass

        return state

    # ==================== ROUTERS ====================

    def _quality_check_router(
        self, state: OrchestratorState
    ) -> Literal["review", "fix", "blocked"]:
        """Quality check sonrası yönlendirme"""
        if state["status"] == "blocked":
            return "blocked"
        elif state["status"] == "gates_passed":
            return "review"
        else:
            return "fix"

    def _review_router(self, state: OrchestratorState) -> Literal["complete", "fix"]:
        """Review sonrası yönlendirme"""
        # TODO: Review sonucuna göre
        return "complete"

    # ==================== HELPERS ====================

    def _format_gate_results(self, results: list[dict]) -> str:
        """Gate sonuçlarını formatla"""
        if not results:
            return "- No gates executed"

        lines = []
        for r in results:
            status = "✅" if r["success"] else "❌"
            lines.append(f"- {r['gate']}: {status} ({r['duration_ms']}ms)")
        return "\n".join(lines)

    # ==================== PUBLIC API ====================

    async def run(self, task_description: str, files: list[str] = None) -> OrchestratorState:
        """
        Görevi çalıştır.

        Args:
            task_description: Görev açıklaması
            files: Etkilenen dosyalar

        Returns:
            Final state
        """
        initial_state = create_initial_state(task_description, files)

        # Graph'ı çalıştır
        config = {"configurable": {"thread_id": initial_state["run_id"]}}

        async for event in self.graph.astream(initial_state, config):
            # Progress logging
            for node_name, node_state in event.items():
                print(f"[{node_name}] Status: {node_state.get('status', 'N/A')}")

        # Final state'i al
        final_state = self.graph.get_state(config)
        return final_state.values

    async def get_status(self, run_id: str) -> OrchestratorState | None:
        """Çalışma durumunu al"""
        config = {"configurable": {"thread_id": run_id}}
        state = self.graph.get_state(config)
        return state.values if state else None


# Factory function
def create_orchestrator(working_dir: str = None) -> KiroOrchestrator:
    """Orchestrator oluştur"""
    if working_dir is None:
        working_dir = Path.cwd()
    else:
        working_dir = Path(working_dir)

    return KiroOrchestrator(working_dir)
