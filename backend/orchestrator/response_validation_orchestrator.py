"""
Response Validation Orchestrator

Bu modül, tüm doğrulama bileşenlerini koordine eden
ana orchestrator'dır.

Features:
- Paralel validator çalıştırma (asyncio.gather)
- Result aggregation
- Performance tracking (< 2 saniye hedef)
- Error collection ve reporting

Requirements: REQ-6.1 - REQ-6.6
"""

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from backend.consistency.consistency_checker import ConsistencyChecker
from backend.consistency.response_history_manager import ResponseHistoryManager
from backend.fact_checking.fact_checker import FactChecker
from backend.fact_checking.meb_resource_client import MEBResourceClient
from backend.fact_checking.rag_client import RAGClient
from backend.fact_checking.wikipedia_client import WikipediaClient
from backend.scoring.confidence_scorer import ConfidenceScorer
from backend.validators.base_response_validator import (
    AgentResponse,
    AgentTypeError,
    ValidationAction,
    ValidationReport,
    ValidationResult,
)
from backend.validators.exam_agent_validator import ExamAgentValidator
from backend.validators.learning_path_validator import LearningPathValidator
from backend.validators.study_buddy_validator import StudyBuddyValidator

logger = logging.getLogger(__name__)


class ResponseValidationOrchestrator:
    """
    Ana doğrulama orkestratörü.

    Tüm validator'ları, fact-checker'ı ve consistency checker'ı
    koordine ederek AI yanıtlarını doğrular.
    """

    # Performance hedefi
    MAX_VALIDATION_TIME = 2.0  # saniye

    def __init__(
        self,
        learning_path_validator: LearningPathValidator | None = None,
        study_buddy_validator: StudyBuddyValidator | None = None,
        exam_agent_validator: ExamAgentValidator | None = None,
        fact_checker: FactChecker | None = None,
        consistency_checker: ConsistencyChecker | None = None,
        confidence_scorer: ConfidenceScorer | None = None,
        parallel_validation: bool = False,
    ):
        """
        Args:
            learning_path_validator: LearningPath validator
            study_buddy_validator: StudyBuddy validator
            exam_agent_validator: ExamAgent validator
            fact_checker: Fact-checker
            consistency_checker: Consistency checker
            confidence_scorer: Confidence scorer
            parallel_validation: Paralel doğrulama aktif mi
        """
        # Validator'ları başlat
        self.validators = {
            "learning_path": learning_path_validator or LearningPathValidator(),
            "study_buddy": study_buddy_validator or StudyBuddyValidator(),
            "exam": exam_agent_validator or ExamAgentValidator(),
        }

        # Fact-checker başlat
        if fact_checker:
            self.fact_checker = fact_checker
        else:
            self.fact_checker = FactChecker(
                rag_client=RAGClient(),
                wikipedia_client=WikipediaClient(),
                meb_client=MEBResourceClient(),
            )

        # Consistency checker başlat
        if consistency_checker:
            self.consistency_checker = consistency_checker
        else:
            self.consistency_checker = ConsistencyChecker(
                history_manager=ResponseHistoryManager()
            )

        # Confidence scorer
        self.scorer = confidence_scorer or ConfidenceScorer()

        self.parallel_validation = parallel_validation

    async def validate_response(self, response: AgentResponse) -> dict[str, Any]:
        """
        AI yanıtını tam doğrulama pipeline'ından geçir.

        Args:
            response: Doğrulanacak yanıt

        Returns:
            Dict: Tam doğrulama raporu
        """
        start_time = time.time()

        # Agent tipini kontrol et
        agent_validator = self.validators.get(response.agent_type)
        if not agent_validator:
            raise AgentTypeError(
                f"Unknown agent type: {response.agent_type}",
                validator_name="Orchestrator",
            )

        # Doğrulama görevlerini hazırla
        if self.parallel_validation:
            # Paralel çalıştır
            results = await asyncio.gather(
                agent_validator.validate(response),
                self.fact_checker.check_facts(response),
                self.consistency_checker.check_consistency(response),
                return_exceptions=True,
            )

            # Sonuçları işle
            agent_result = self._handle_result(results[0], "agent_specific")
            fact_result = self._handle_result(results[1], "fact_checking")
            consistency_result = self._handle_result(results[2], "consistency")
        else:
            # Sıralı çalıştır - Token tasarrufu için Short-circuit mantığı
            agent_result = await self._safe_validate(
                agent_validator.validate(response), "agent_specific"
            )

            # Eğer agent_specific doğrulama çok düşükse (fail), fact_checking'i atla
            if agent_result.score < 0.6:
                logger.info(
                    f"[{response.response_id}] Short-circuiting fact_checking due to low agent score ({agent_result.score})"
                )
                fact_result = ValidationResult(
                    is_valid=False,
                    score=agent_result.score,
                    errors=[],
                    warnings=[
                        "Fact-checking skipped to save tokens due to early failure"
                    ],
                    suggestions=[],
                    metadata={},
                )
            else:
                fact_result = await self._safe_validate(
                    self.fact_checker.check_facts(response), "fact_checking"
                )

            # Eğer fact_checking veya agent fail ise consistency'i atla
            if agent_result.score < 0.6 or fact_result.score < 0.6:
                logger.info(
                    f"[{response.response_id}] Short-circuiting consistency due to low earlier scores"
                )
                consistency_result = ValidationResult(
                    is_valid=False,
                    score=min(agent_result.score, fact_result.score),
                    errors=[],
                    warnings=[
                        "Consistency skipped to save tokens due to early failure"
                    ],
                    suggestions=[],
                    metadata={},
                )
            else:
                consistency_result = await self._safe_validate(
                    self.consistency_checker.check_consistency(response), "consistency"
                )

        # Confidence score hesapla
        confidence, action = self.scorer.calculate_and_determine(
            agent_result, fact_result, consistency_result
        )

        # Tüm hata ve uyarıları topla
        all_errors = (
            agent_result.errors + fact_result.errors + consistency_result.errors
        )

        all_warnings = (
            agent_result.warnings + fact_result.warnings + consistency_result.warnings
        )

        all_suggestions = (
            agent_result.suggestions
            + fact_result.suggestions
            + consistency_result.suggestions
        )

        # Süre hesapla
        duration = time.time() - start_time

        # Performance uyarısı
        if duration > self.MAX_VALIDATION_TIME:
            logger.warning(
                f"Validation took {duration:.2f}s, exceeds {self.MAX_VALIDATION_TIME}s target"
            )

        # Rapor oluştur
        report = {
            "response_id": response.response_id,
            "confidence_score": confidence,
            "action": action.value,
            "action_description": self.scorer.get_action_description(action),
            "validation_results": {
                "agent_specific": agent_result.model_dump(),
                "fact_checking": fact_result.model_dump(),
                "consistency": consistency_result.model_dump(),
            },
            "score_breakdown": self.scorer.get_score_breakdown(
                agent_result, fact_result, consistency_result
            ),
            "errors": all_errors,
            "warnings": all_warnings,
            "suggestions": all_suggestions,
            "duration_seconds": round(duration, 3),
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "agent_type": response.agent_type,
                "user_id": response.user_id,
                "parallel_validation": self.parallel_validation,
            },
        }

        logger.info(
            f"Validation complete: response_id={response.response_id}, "
            f"confidence={confidence:.3f}, action={action.value}, "
            f"duration={duration:.2f}s"
        )

        return report

    def _handle_result(
        self,
        result: Any,
        validator_name: str,
    ) -> ValidationResult:
        """
        Doğrulama sonucunu işle (hata yönetimi dahil).

        Args:
            result: Doğrulama sonucu veya exception
            validator_name: Validator ismi

        Returns:
            ValidationResult: İşlenmiş sonuç
        """
        if isinstance(result, ValidationResult):
            return result
        if isinstance(result, Exception):
            logger.error(f"{validator_name} validation error: {result}")
            return ValidationResult(
                is_valid=True,  # Fail-open
                score=0.5,  # Neutral score
                errors=[],
                warnings=[f"{validator_name} doğrulaması başarısız: {result!s}"],
                suggestions=[],
                metadata={"error": str(result)},
            )
        logger.warning(f"Unexpected result type from {validator_name}")
        return ValidationResult(
            is_valid=True,
            score=0.5,
            errors=[],
            warnings=[],
            suggestions=[],
            metadata={},
        )

    async def _safe_validate(
        self,
        coro,
        validator_name: str,
    ) -> ValidationResult:
        """
        Güvenli doğrulama çalıştır (exception handling).

        Args:
            coro: Coroutine
            validator_name: Validator ismi

        Returns:
            ValidationResult: Sonuç
        """
        try:
            return await coro
        except Exception as e:
            logger.error(f"{validator_name} validation error: {e}")
            return ValidationResult(
                is_valid=True,  # Fail-open
                score=0.5,
                errors=[],
                warnings=[f"{validator_name} doğrulaması başarısız: {e!s}"],
                suggestions=[],
                metadata={"error": str(e)},
            )

    def to_validation_report(self, result: dict[str, Any]) -> ValidationReport:
        """
        Dict sonucunu ValidationReport modeline dönüştür.

        Args:
            result: Doğrulama sonucu dict

        Returns:
            ValidationReport: Pydantic model
        """
        return ValidationReport(
            response_id=result["response_id"],
            confidence_score=result["confidence_score"],
            action=ValidationAction(result["action"]),
            validation_results=result["validation_results"],
            errors=result["errors"],
            warnings=result["warnings"],
            suggestions=result["suggestions"],
            duration_seconds=result["duration_seconds"],
            timestamp=datetime.fromisoformat(result["timestamp"]),
        )

    async def quick_validate(
        self, response: AgentResponse
    ) -> tuple[float, ValidationAction]:
        """
        Hızlı doğrulama (sadece agent-specific).

        Args:
            response: Yanıt

        Returns:
            Tuple[float, ValidationAction]: (confidence, action)
        """
        agent_validator = self.validators.get(response.agent_type)
        if not agent_validator:
            return 0.5, ValidationAction.REVIEW

        try:
            result = await agent_validator.validate(response)
            confidence = result.score
            action = self.scorer.determine_action(confidence)
            return confidence, action
        except Exception as e:
            logger.error(f"Quick validation error: {e}")
            return 0.5, ValidationAction.REVIEW
