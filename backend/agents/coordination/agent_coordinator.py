"""
Agent Coordinator - Routing & Sequential Multi-Domain Processing
REQ-7.4, REQ-7.5
Teknofest 2025 - KIRO2 YKS Platformu

Agent routing ve multi-domain soru islemesi:
- Single-domain: Direkt agent cagrilir
- Multi-domain: Sequential cagri (paralel DEGIL!)
- Context sharing via blackboard
"""

import logging
import time
from dataclasses import dataclass
from typing import Any

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


class AgentCoordinator:
    """
    Agent Koordinatoru (REQ-7.4, REQ-7.5)

    Sorulari uygun agent'lara yonlendirir ve sonuclari toplar.
    Multi-domain sorular SEQUENTIAL islenir (paralel degil!).

    Attributes:
        agents: Domain -> Agent mapping
        classifier: Question classifier
        blackboard: Inter-agent communication
    """

    def __init__(
        self,
        agents: dict[DomainType, BaseDomainAgent],
        classifier: QuestionClassifier | None = None,
        blackboard: DomainBlackboard | None = None,
    ):
        """
        AgentCoordinator olustur

        Args:
            agents: Domain -> Agent mapping
            classifier: Question classifier (default: new instance)
            blackboard: Blackboard instance (default: new instance)
        """
        self.agents = agents
        self.classifier = classifier or QuestionClassifier()
        self.blackboard = blackboard

        # Metrics
        self.total_questions_processed = 0
        self.multi_domain_questions = 0

        logger.info(
            f"AgentCoordinator initialized with {len(agents)} agents: "
            f"{[d.value for d in agents]}"
        )

    async def process_question(
        self,
        question: str,
        student_id: str | None = None,
        preferred_domain: DomainType | None = None,
    ) -> CoordinationResult:
        """
        Soruyu isle ve sonucu dondur

        Args:
            question: Soru metni
            student_id: Ogrenci ID (opsiyonel)
            preferred_domain: Tercih edilen domain (opsiyonel)

        Returns:
            CoordinationResult: Koordinasyon sonucu
        """
        start_time = time.perf_counter()

        # 1. Classify question
        if preferred_domain:
            classification = DomainClassification(
                primary_domain=preferred_domain,
                primary_confidence=1.0,
                is_multi_domain=False,
            )
        else:
            classification = self.classifier.classify(question)

        # 2. Determine agents to call
        domains_to_call = [classification.primary_domain]
        if classification.is_multi_domain and classification.secondary_domain:
            domains_to_call.append(classification.secondary_domain)

        # 3. Process with agent(s) - SEQUENTIAL for multi-domain
        responses = []
        agents_called = []
        shared_context = {}

        for domain in domains_to_call:
            agent = self.agents.get(domain)
            if not agent:
                logger.warning(f"No agent registered for domain: {domain.value}")
                continue

            # Get shared context from blackboard
            if self.blackboard and shared_context:
                await agent.update_context_from_blackboard(shared_context)

            # Process question
            response = await agent.solve_question(question, shared_context)
            responses.append(response)
            agents_called.append(domain.value)

            # Share context for next agent (if multi-domain)
            if classification.is_multi_domain and response.context_additions:
                shared_context.update(response.context_additions)
                if self.blackboard:
                    await self.blackboard.share_context(
                        source_agent=domain.value,
                        data=response.context_additions,
                    )

        # 4. Calculate total time
        total_time_ms = (time.perf_counter() - start_time) * 1000

        # 5. Update metrics
        self.total_questions_processed += 1
        if classification.is_multi_domain:
            self.multi_domain_questions += 1

        result = CoordinationResult(
            classification=classification,
            responses=responses,
            total_time_ms=total_time_ms,
            agents_called=agents_called,
            is_multi_domain=classification.is_multi_domain,
        )

        logger.info(
            f"Processed question in {total_time_ms:.2f}ms "
            f"(domains: {agents_called}, multi-domain: {classification.is_multi_domain})"
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
        }
