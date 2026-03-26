"""
Expert Agents API - Konu Bazli Subagent Sistemi API Endpoints
REQ-1 to REQ-8
Teknofest 2025 - KIRO2 YKS Platformu

Endpoints:
- POST /api/v1/ask-question - Soru sor
- GET /api/v1/agents/{agent_name}/performance - Agent performansi
- GET /api/v1/agents/specialization-scores - Tum skorlar
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

try:
    from api.schemas.expert_agents import (
        QuestionRequest,
        QuestionResponse,
        AgentResponse,
        DomainClassification,
        AgentPerformance,
        AllAgentsScores,
        SpecializationScore,
        DomainTypeEnum,
    )
except (ImportError, TypeError):
    QuestionRequest = None
    QuestionResponse = None
    AgentResponse = None
    DomainClassification = None
    AgentPerformance = None
    AllAgentsScores = None
    SpecializationScore = None
    DomainTypeEnum = None

try:
    from agents.domain_experts import (
        DomainType,
        MatematikAgent,
        FizikAgent,
        TurkceAgent,
        SosyalAgent,
        BiyolojiAgent,
        YabanciDilAgent,
    )
except (ImportError, TypeError):
    DomainType = None
    MatematikAgent = None
    FizikAgent = None
    TurkceAgent = None
    SosyalAgent = None
    BiyolojiAgent = None
    YabanciDilAgent = None

try:
    from agents.coordination import (
        QuestionClassifier,
        AgentCoordinator,
        ResponseSynthesizer,
        DomainBlackboard,
    )
except (ImportError, TypeError):
    QuestionClassifier = None
    AgentCoordinator = None
    ResponseSynthesizer = None
    DomainBlackboard = None

try:
    from agents.scoring import SpecializationScorer, PerformanceTracker
except (ImportError, TypeError):
    SpecializationScorer = None
    PerformanceTracker = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Expert Agents"])

# Global instances
_coordinator: Optional[AgentCoordinator] = None
_scorer: Optional[SpecializationScorer] = None
_tracker: Optional[PerformanceTracker] = None
_blackboard: Optional[DomainBlackboard] = None


async def get_coordinator() -> AgentCoordinator:
    """Agent coordinator instance'ini al"""
    global _coordinator, _blackboard

    if _coordinator is None:
        # Initialize blackboard
        _blackboard = DomainBlackboard()
        await _blackboard.connect()

        # Initialize agents
        agents = {
            DomainType.MATEMATIK: MatematikAgent(),
            DomainType.FIZIK: FizikAgent(),
            DomainType.TURKCE: TurkceAgent(),
            DomainType.SOSYAL: SosyalAgent(),
            DomainType.BIYOLOJI: BiyolojiAgent(),
            DomainType.YABANCI_DIL: YabanciDilAgent(),
        }

        # Initialize coordinator
        _coordinator = AgentCoordinator(
            agents=agents,
            classifier=QuestionClassifier(),
            blackboard=_blackboard,
        )

        logger.info("AgentCoordinator initialized with 6 domain agents")

    return _coordinator


async def get_scorer() -> SpecializationScorer:
    """Specialization scorer instance'ini al"""
    global _scorer
    if _scorer is None:
        _scorer = SpecializationScorer()
    return _scorer


async def get_tracker() -> PerformanceTracker:
    """Performance tracker instance'ini al"""
    global _tracker
    if _tracker is None:
        _tracker = PerformanceTracker()
    return _tracker


@router.post(
    "/ask-question",
    response_model=QuestionResponse,
    summary="Soru Sor",
    description="""
    Verilen soruyu uygun domain expert agent'a yonlendirir ve cevap alir.

    **Domain Detection:**
    - Sorular otomatik olarak 6 domain'den birine siniflandirilir
    - Multi-domain sorular sequential olarak islenir (REQ-7.5)

    **Supported Domains:**
    - `matematik`: Cebir, Geometri, Analiz, Olasilik (REQ-1)
    - `fizik`: Mekanik, Elektrik, Optik, Termodinamik (REQ-2)
    - `turkce`: Dilbilgisi, Edebiyat, Anlam Bilgisi (REQ-3)
    - `sosyal`: Tarih, Cografya, Felsefe (REQ-4)
    - `biyoloji`: Hucre, Genetik, Ekoloji (REQ-5)
    - `yabanci_dil`: Grammar, Vocabulary, Reading (REQ-6)

    **Context Isolation:**
    - Her agent 200K token izole context ile calisir (REQ-7.1)
    - Blackboard pattern ile koordinasyon (REQ-7.3)

    **Specialization Scoring:**
    - Score = 0.4*Relevance + 0.3*Accuracy + 0.2*Completeness + 0.1*Satisfaction (REQ-8.2)
    """,
    responses={
        200: {
            "description": "Basarili yanit",
            "content": {
                "application/json": {
                    "examples": {
                        "matematik": {
                            "summary": "Matematik sorusu yaniti",
                            "value": {
                                "success": True,
                                "classification": {
                                    "primary_domain": "matematik",
                                    "primary_confidence": 0.95,
                                    "secondary_domain": None,
                                    "secondary_confidence": None,
                                    "is_multi_domain": False
                                },
                                "responses": [{
                                    "domain": "matematik",
                                    "content": "2x + 3 = 7 denkleminin cozumu...",
                                    "confidence": 0.92,
                                    "tools_used": ["sympy"],
                                    "step_by_step_solution": ["Adim 1: ...", "Adim 2: ..."],
                                    "latex_expressions": ["x = 2"],
                                    "visualizations": [],
                                    "references": [],
                                    "response_time_ms": 1250.5,
                                    "tokens_used": 1500
                                }],
                                "synthesized_response": "Denklemin cozumu x = 2",
                                "specialization_score": 0.88,
                                "total_response_time_ms": 1250.5,
                                "metadata": {
                                    "agents_called": ["matematik"],
                                    "is_multi_domain": False,
                                    "student_id": "student_001"
                                }
                            }
                        },
                        "multi_domain": {
                            "summary": "Multi-domain soru yaniti",
                            "value": {
                                "success": True,
                                "classification": {
                                    "primary_domain": "matematik",
                                    "primary_confidence": 0.75,
                                    "secondary_domain": "fizik",
                                    "secondary_confidence": 0.68,
                                    "is_multi_domain": True
                                },
                                "responses": [
                                    {"domain": "matematik", "content": "..."},
                                    {"domain": "fizik", "content": "..."}
                                ],
                                "synthesized_response": "Birlesik yanit...",
                                "specialization_score": 0.85,
                                "total_response_time_ms": 2500.0,
                                "metadata": {
                                    "agents_called": ["matematik", "fizik"],
                                    "is_multi_domain": True
                                }
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation Error - Gecersiz istek",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "question_text"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Agent processing failed"
                    }
                }
            }
        }
    },
)
async def ask_question(
    request: QuestionRequest,
    coordinator: AgentCoordinator = Depends(get_coordinator),
    scorer: SpecializationScorer = Depends(get_scorer),
    tracker: PerformanceTracker = Depends(get_tracker),
) -> QuestionResponse:
    """
    Soru sor ve cevap al

    - Soruyu siniflandirir (auto-detect veya preferred_domain)
    - Uygun agent(lar)a yonlendirir
    - Multi-domain sorular sequential islenir
    - Yanitlari birlestirip dondurur
    """
    try:
        # Map preferred domain if provided
        preferred_domain = None
        if request.preferred_domain:
            domain_map = {
                DomainTypeEnum.MATEMATIK: DomainType.MATEMATIK,
                DomainTypeEnum.FIZIK: DomainType.FIZIK,
                DomainTypeEnum.TURKCE: DomainType.TURKCE,
                DomainTypeEnum.SOSYAL: DomainType.SOSYAL,
                DomainTypeEnum.BIYOLOJI: DomainType.BIYOLOJI,
                DomainTypeEnum.YABANCI_DIL: DomainType.YABANCI_DIL,
            }
            preferred_domain = domain_map.get(request.preferred_domain)

        # Process question
        result = await coordinator.process_question(
            question=request.question_text,
            student_id=request.student_id,
            preferred_domain=preferred_domain,
        )

        # Track responses
        for response in result.responses:
            tracker.track_response(response)

        # Calculate specialization scores
        total_score = 0.0
        for response in result.responses:
            score = scorer.calculate_from_response(response)
            total_score += score.total_score

        avg_score = total_score / len(result.responses) if result.responses else 0.0

        # Synthesize response
        synthesizer = ResponseSynthesizer()
        synthesized = synthesizer.synthesize(result.responses, request.question_text)

        # Build response
        agent_responses = []
        for response in result.responses:
            agent_responses.append(
                AgentResponse(
                    domain=DomainTypeEnum(response.domain.value),
                    content=response.content,
                    confidence=response.confidence,
                    tools_used=response.tools_used,
                    step_by_step_solution=response.step_by_step_solution,
                    latex_expressions=response.latex_expressions,
                    visualizations=[],  # Simplified for now
                    references=response.references,
                    response_time_ms=response.response_time_ms,
                    tokens_used=response.tokens_used,
                )
            )

        return QuestionResponse(
            success=True,
            classification=DomainClassification(
                primary_domain=DomainTypeEnum(result.classification.primary_domain.value),
                primary_confidence=result.classification.primary_confidence,
                secondary_domain=DomainTypeEnum(result.classification.secondary_domain.value)
                if result.classification.secondary_domain
                else None,
                secondary_confidence=result.classification.secondary_confidence,
                is_multi_domain=result.classification.is_multi_domain,
            ),
            responses=agent_responses,
            synthesized_response=synthesized,
            specialization_score=avg_score,
            total_response_time_ms=result.total_time_ms,
            metadata={
                "agents_called": result.agents_called,
                "is_multi_domain": result.is_multi_domain,
                "student_id": request.student_id,
            },
        )

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/agents/{agent_name}/performance",
    response_model=AgentPerformance,
    summary="Agent Performansi",
    description="Belirtilen agent'in performans metriklerini dondurur.",
)
async def get_agent_performance(
    agent_name: str,
    tracker: PerformanceTracker = Depends(get_tracker),
    scorer: SpecializationScorer = Depends(get_scorer),
) -> AgentPerformance:
    """
    Agent performans metriklerini al

    - Toplam soru sayisi
    - Basari orani
    - Ortalama yanit suresi
    - Uzmanlik skoru
    """
    try:
        # Map agent name to domain
        domain_map = {
            "matematik": DomainType.MATEMATIK,
            "fizik": DomainType.FIZIK,
            "turkce": DomainType.TURKCE,
            "sosyal": DomainType.SOSYAL,
            "biyoloji": DomainType.BIYOLOJI,
            "yabanci_dil": DomainType.YABANCI_DIL,
        }

        domain = domain_map.get(agent_name.lower())
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_name}",
            )

        metrics = tracker.get_metrics(domain)
        latest_score = scorer.get_latest_score(domain)

        # Get agent info
        coordinator = await get_coordinator()
        agent = coordinator.get_agent(domain)

        return AgentPerformance(
            agent_id=agent.agent_id if agent else agent_name,
            domain=DomainTypeEnum(domain.value),
            specialization_areas=agent.specialization_areas if agent else [],
            total_questions_answered=metrics.total_questions if metrics else 0,
            successful_answers=metrics.successful_responses if metrics else 0,
            failed_answers=metrics.failed_responses if metrics else 0,
            average_response_time_ms=metrics.average_response_time_ms if metrics else 0.0,
            average_confidence=metrics.average_confidence if metrics else 0.0,
            current_specialization_score=SpecializationScore(
                domain=DomainTypeEnum(latest_score.domain.value),
                domain_relevance=latest_score.domain_relevance,
                accuracy=latest_score.accuracy,
                completeness=latest_score.completeness,
                user_satisfaction=latest_score.user_satisfaction,
                total_score=latest_score.total_score,
                calculated_at=latest_score.calculated_at,
            )
            if latest_score
            else None,
            context_usage=agent.context.get_status() if agent else {},
            tools_available=list(agent.tools.keys()) if agent else [],
            last_activity=metrics.last_activity if metrics else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/agents/specialization-scores",
    response_model=AllAgentsScores,
    summary="Tum Uzmanlik Skorlari",
    description="Tum agent'larin uzmanlik skorlarini dondurur.",
)
async def get_all_specialization_scores(
    scorer: SpecializationScorer = Depends(get_scorer),
) -> AllAgentsScores:
    """
    Tum agent'larin uzmanlik skorlarini al

    - Her agent'in son skoru
    - Ortalama skor
    - En iyi performans gosteren domain
    - Yeniden egitim gereken domain'ler
    """
    try:
        all_scores = scorer.get_all_scores()

        scores = []
        for domain, score in all_scores.items():
            scores.append(
                SpecializationScore(
                    domain=DomainTypeEnum(domain.value),
                    domain_relevance=score.domain_relevance,
                    accuracy=score.accuracy,
                    completeness=score.completeness,
                    user_satisfaction=score.user_satisfaction,
                    total_score=score.total_score,
                    calculated_at=score.calculated_at,
                )
            )

        avg_score = 0.0
        if scores:
            avg_score = sum(s.total_score for s in scores) / len(scores)

        best_domain = scorer.get_best_performing_domain()
        needs_retraining = scorer.get_domains_needing_retraining()

        return AllAgentsScores(
            scores=scores,
            average_score=avg_score,
            best_performing_domain=DomainTypeEnum(best_domain.value)
            if best_domain
            else None,
            needs_retraining=[DomainTypeEnum(d.value) for d in needs_retraining],
        )

    except Exception as e:
        logger.error(f"Error getting specialization scores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Islem basarisiz. Lutfen tekrar deneyin.",
        )


@router.get(
    "/agents/metrics",
    summary="Sistem Metrikleri",
    description="Tum sistem metriklerini dondurur.",
)
async def get_system_metrics(
    coordinator: AgentCoordinator = Depends(get_coordinator),
    scorer: SpecializationScorer = Depends(get_scorer),
    tracker: PerformanceTracker = Depends(get_tracker),
):
    """Sistem metriklerini al"""
    return {
        "coordinator": coordinator.get_metrics(),
        "scorer": scorer.get_metrics(),
        "tracker": tracker.get_summary(),
    }
