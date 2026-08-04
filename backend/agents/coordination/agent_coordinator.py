"""
Agent Coordinator - Routing & Sequential Multi-Domain Processing (ULTRA LEVEL)
REQ-7.4, REQ-7.5
Teknofest 2025 - KIRO2 YKS Platformu

LangGraph Agent Orkestrasyonu:
- StateGraph ile reaktif ve stateful orkestrasyon
- Single-domain & Multi-domain node'lar
- Edge routing ve Conditional Handoff
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, TypedDict, Annotated, Sequence
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from ..domain_experts.base_domain_agent import (
    BaseDomainAgent,
    DomainResponse,
    DomainType,
)
from .blackboard import DomainBlackboard
from .question_classifier import DomainClassification, QuestionClassifier

logger = logging.getLogger(__name__)


@dataclass
class CoordinationResult:
    """Koordinasyon sonucu"""

    classification: DomainClassification
    responses: list[DomainResponse]
    total_time_ms: float
    agents_called: list[str]
    is_multi_domain: bool


class GraphState(TypedDict):
    """LangGraph State Object"""
    question: str
    student_id: str | None
    preferred_domain: DomainType | None
    classification: DomainClassification | None
    responses: Annotated[list[DomainResponse], operator.add]
    agents_called: Annotated[list[str], operator.add]
    shared_context: dict[str, Any]
    current_agent_index: int
    domains_to_call: list[DomainType]
    start_time: float


class AgentCoordinator:
    """
    Agent Koordinatoru (LangGraph Ultra Sürümü - REQ-7.4, REQ-7.5)

    Sorulari LangGraph StateGraph yapısı ile stateful olarak yönetir.
    Multi-domain sorular için State üzerinden context paslar ve Blackboard entegrasyonu yapar.
    """

    def __init__(
        self,
        agents: dict[DomainType, BaseDomainAgent],
        classifier: QuestionClassifier | None = None,
        blackboard: DomainBlackboard | None = None,
    ):
        self.agents = agents
        self.classifier = classifier or QuestionClassifier()
        self.blackboard = blackboard

        # Metrics
        self.total_questions_processed = 0
        self.multi_domain_questions = 0

        # MemorySaver for checkpointing (Ultra Standard)
        self.memory = MemorySaver()

        # Build LangGraph
        self.graph = self._build_graph()

        logger.info(
            f"AgentCoordinator (LangGraph ULTRA) initialized with {len(agents)} agents: "
            f"{[d.value for d in agents]}"
        )

    def _build_graph(self):
        """LangGraph Workflow'unu oluşturur."""
        workflow = StateGraph(GraphState)

        # 1. Siniflandirma Nodu
        def classify_node(state: GraphState):
            if state.get("preferred_domain"):
                classification = DomainClassification(
                    primary_domain=state["preferred_domain"],
                    primary_confidence=1.0,
                    is_multi_domain=False,
                )
            else:
                classification = self.classifier.classify(state["question"])
            
            domains_to_call = [classification.primary_domain]
            if classification.is_multi_domain and classification.secondary_domain:
                domains_to_call.append(classification.secondary_domain)
            
            return {
                "classification": classification,
                "domains_to_call": domains_to_call,
                "current_agent_index": 0,
                "shared_context": {}
            }

        # 2. Agent Çalıştırma Nodu
        async def agent_execution_node(state: GraphState):
            idx = state["current_agent_index"]
            if idx >= len(state["domains_to_call"]):
                return {} # Bitti
            
            domain = state["domains_to_call"][idx]
            agent = self.agents.get(domain)
            
            if not agent:
                logger.warning(f"No agent registered for domain: {domain.value}")
                return {"current_agent_index": idx + 1}
            
            shared_ctx = state["shared_context"]
            if self.blackboard and shared_ctx:
                await agent.update_context_from_blackboard(shared_ctx)

            response = await agent.solve_question(state["question"], shared_ctx)
            
            new_ctx = dict(shared_ctx)
            if state["classification"].is_multi_domain and response.context_additions:
                new_ctx.update(response.context_additions)
                if self.blackboard:
                    await self.blackboard.share_context(
                        source_agent=domain.value,
                        data=response.context_additions,
                    )
            
            return {
                "responses": [response],
                "agents_called": [domain.value],
                "shared_context": new_ctx,
                "current_agent_index": idx + 1
            }

        # 3. Yönlendirme (Edge)
        def route_next_agent(state: GraphState):
            if state["current_agent_index"] < len(state["domains_to_call"]):
                return "execute_agent"
            return "end"

        workflow.add_node("classify", classify_node)
        workflow.add_node("execute_agent", agent_execution_node)

        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "execute_agent")
        workflow.add_conditional_edges(
            "execute_agent",
            route_next_agent,
            {
                "execute_agent": "execute_agent",
                "end": END
            }
        )

        return workflow.compile(checkpointer=self.memory)

    async def process_question(
        self,
        question: str,
        student_id: str | None = None,
        preferred_domain: DomainType | None = None,
    ) -> CoordinationResult:
        """
        Soruyu LangGraph ile isle ve sonucu dondur
        """
        start_time = time.perf_counter()

        initial_state = {
            "question": question,
            "student_id": student_id,
            "preferred_domain": preferred_domain,
            "classification": None,
            "responses": [],
            "agents_called": [],
            "shared_context": {},
            "current_agent_index": 0,
            "domains_to_call": [],
            "start_time": start_time
        }

        # Set thread_id for checkpointing (resumable state)
        config = {"configurable": {"thread_id": student_id or "anonymous"}}
        
        # LangGraph çalıştır
        final_state = await self.graph.ainvoke(initial_state, config=config)

        total_time_ms = (time.perf_counter() - start_time) * 1000
        classification = final_state["classification"]

        # Metrics
        self.total_questions_processed += 1
        if classification.is_multi_domain:
            self.multi_domain_questions += 1

        result = CoordinationResult(
            classification=classification,
            responses=final_state["responses"],
            total_time_ms=total_time_ms,
            agents_called=final_state["agents_called"],
            is_multi_domain=classification.is_multi_domain,
        )

        logger.info(
            f"[LangGraph ULTRA] Processed question in {total_time_ms:.2f}ms "
            f"(domains: {result.agents_called}, multi-domain: {classification.is_multi_domain})"
        )

        return result

    def register_agent(self, domain: DomainType, agent: BaseDomainAgent):
        """Agent kaydet"""
        self.agents[domain] = agent
        logger.info(f"Registered agent for domain: {domain.value}")

    def get_agent(self, domain: DomainType) -> BaseDomainAgent | None:
        """Domain icin agent al"""
        return self.agents.get(domain)

    def get_metrics(self) -> dict[str, Any]:
        """Koordinator metriklerini al"""
        return {
            "total_questions_processed": self.total_questions_processed,
            "multi_domain_questions": self.multi_domain_questions,
            "registered_agents": [d.value for d in self.agents.keys()],
            "agent_count": len(self.agents),
            "orchestration_engine": "LangGraph StateGraph (Ultra)"
        }
