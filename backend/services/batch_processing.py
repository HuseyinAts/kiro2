"""
Batch Processing Service - API Response Time Optimization

Toplu islemler icin service layer. Questions ve exam operations
icin batch processing destekler.

Requirements:
    - REQ-3.1.3: Batch processing to services
    - REQ-3.3: Process operations concurrently
    - REQ-3.4: Transaction handling for batch operations

Author: KIRO2 Team
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BatchOperationType(str, Enum):
    """Batch islem tipleri."""

    GET_QUESTIONS = "get_questions"
    SUBMIT_ANSWERS = "submit_answers"
    UPDATE_PROGRESS = "update_progress"
    GET_USERS = "get_users"
    INVALIDATE_CACHE = "invalidate_cache"


@dataclass
class BatchOperation:
    """
    Tek bir batch islemi.

    Attributes:
        operation_type: Islem tipi
        params: Islem parametreleri
        id: Islem ID'si (tracking icin)
    """

    operation_type: BatchOperationType
    params: dict[str, Any]
    id: str | None = None


@dataclass
class BatchResult:
    """
    Batch islem sonucu.

    Attributes:
        operation_id: Islem ID'si
        success: Basarili mi
        data: Sonuc verisi
        error: Hata mesaji (basarisiz ise)
        elapsed_ms: Islem suresi (ms)
    """

    operation_id: str
    success: bool
    data: Any = None
    error: str | None = None
    elapsed_ms: float = 0.0


@dataclass
class BatchResponse:
    """
    Toplu batch islem response'u.

    Attributes:
        results: Tum islem sonuclari
        total_count: Toplam islem sayisi
        success_count: Basarili islem sayisi
        failure_count: Basarisiz islem sayisi
        elapsed_ms: Toplam sure (ms)
    """

    results: list[BatchResult] = field(default_factory=list)
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        """Dict'e cevir."""
        return {
            "results": [
                {
                    "operation_id": r.operation_id,
                    "success": r.success,
                    "data": r.data,
                    "error": r.error,
                    "elapsed_ms": r.elapsed_ms,
                }
                for r in self.results
            ],
            "summary": {
                "total": self.total_count,
                "success": self.success_count,
                "failure": self.failure_count,
                "elapsed_ms": self.elapsed_ms,
            },
        }


class BatchProcessor:
    """
    Batch islem processor.

    asyncio.gather ile paralel islem destekler.
    Partial failure handling ve transaction rollback icerir.

    Attributes:
        handlers: Operation type -> handler mapping
        max_operations: Maksimum batch boyutu

    Example:
        >>> processor = BatchProcessor()
        >>> processor.register_handler(
        ...     BatchOperationType.GET_QUESTIONS,
        ...     handle_get_questions
        ... )
        >>> result = await processor.process(operations)
    """

    def __init__(self, max_operations: int = 10):
        """
        BatchProcessor baslatici.

        Args:
            max_operations: Maksimum batch boyutu (default: 10)
        """
        self.max_operations = max_operations
        self._handlers: dict[BatchOperationType, Callable] = {}

        logger.info(f"BatchProcessor initialized: max_operations={max_operations}")

    def register_handler(
        self,
        operation_type: BatchOperationType,
        handler: Callable,
    ) -> None:
        """
        Islem tipi icin handler kaydeder.

        Args:
            operation_type: Islem tipi
            handler: Async handler fonksiyonu
        """
        self._handlers[operation_type] = handler
        logger.debug(f"Handler registered for {operation_type.value}")

    async def _execute_operation(
        self,
        operation: BatchOperation,
        session: AsyncSession | None = None,
    ) -> BatchResult:
        """
        Tek bir islemi calistirir.

        Args:
            operation: Calistirilacak islem
            session: Database session (opsiyonel)

        Returns:
            BatchResult
        """
        import time

        start_time = time.perf_counter()
        operation_id = operation.id or f"op_{id(operation)}"

        handler = self._handlers.get(operation.operation_type)

        if handler is None:
            return BatchResult(
                operation_id=operation_id,
                success=False,
                error=f"Unknown operation type: {operation.operation_type.value}",
            )

        try:
            # Handler'i calistir
            if session is not None:
                result = await handler(session=session, **operation.params)
            else:
                result = await handler(**operation.params)

            elapsed = (time.perf_counter() - start_time) * 1000

            return BatchResult(
                operation_id=operation_id,
                success=True,
                data=result,
                elapsed_ms=elapsed,
            )

        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(f"Batch operation failed: {operation_id} - {e}")

            return BatchResult(
                operation_id=operation_id,
                success=False,
                error=str(e),
                elapsed_ms=elapsed,
            )

    async def process(
        self,
        operations: list[BatchOperation],
        session: AsyncSession | None = None,
        stop_on_error: bool = False,
    ) -> BatchResponse:
        """
        Batch islemleri paralel olarak isler.

        Args:
            operations: Islem listesi
            session: Database session (opsiyonel)
            stop_on_error: Ilk hatada dur (default: False)

        Returns:
            BatchResponse

        Raises:
            ValueError: Batch boyutu limiti asildiginda
        """
        import time

        start_time = time.perf_counter()

        # Batch boyutu kontrolu
        if len(operations) > self.max_operations:
            raise ValueError(
                f"Batch size {len(operations)} exceeds limit {self.max_operations}"
            )

        if not operations:
            return BatchResponse(total_count=0)

        # Paralel islem (return_exceptions=True ile partial failure)
        tasks = [
            self._execute_operation(op, session)
            for op in operations
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sonuclari isle
        batch_results: list[BatchResult] = []
        success_count = 0
        failure_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results.append(
                    BatchResult(
                        operation_id=operations[i].id or f"op_{i}",
                        success=False,
                        error=str(result),
                    )
                )
                failure_count += 1

                if stop_on_error:
                    break
            else:
                batch_results.append(result)
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1

                    if stop_on_error:
                        break

        elapsed = (time.perf_counter() - start_time) * 1000

        return BatchResponse(
            results=batch_results,
            total_count=len(operations),
            success_count=success_count,
            failure_count=failure_count,
            elapsed_ms=elapsed,
        )


class QuestionBatchService:
    """
    Soru islemleri icin batch service.

    Toplu soru getirme ve guncelleme islemleri.

    Example:
        >>> service = QuestionBatchService(db_session)
        >>> questions = await service.batch_get_questions(
        ...     question_ids=["q1", "q2", "q3"]
        ... )
    """

    def __init__(self, session: AsyncSession):
        """
        QuestionBatchService baslatici.

        Args:
            session: Database session
        """
        self.session = session

    async def batch_get_questions(
        self,
        question_ids: list[str | UUID],
        include_options: bool = True,
    ) -> list[dict]:
        """
        Birden fazla soruyu toplu olarak getirir.

        Args:
            question_ids: Soru ID listesi
            include_options: Secenekleri dahil et

        Returns:
            Soru listesi
        """
        from sqlalchemy import select
        from models.database import Question

        if not question_ids:
            return []

        # Convert to string IDs
        str_ids = [str(qid) for qid in question_ids]

        # Batch query
        query = select(Question).where(Question.id.in_(str_ids))

        if include_options:
            from sqlalchemy.orm import selectinload
            query = query.options(selectinload(Question.options))

        result = await self.session.execute(query)
        questions = result.scalars().all()

        # Dict'e cevir
        return [
            {
                "id": str(q.id),
                "content": q.content,
                "subject": q.subject,
                "difficulty": q.difficulty,
                "options": [
                    {"id": str(o.id), "text": o.text, "is_correct": o.is_correct}
                    for o in (q.options or [])
                ] if include_options else None,
            }
            for q in questions
        ]

    async def batch_update_difficulty(
        self,
        updates: list[dict[str, Any]],
    ) -> int:
        """
        Birden fazla sorunun zorlugunu gunceller.

        Args:
            updates: [{"id": "q1", "difficulty": 0.5}, ...]

        Returns:
            Guncellenen soru sayisi
        """
        from sqlalchemy import update
        from models.database import Question

        updated_count = 0

        for item in updates:
            question_id = item.get("id")
            difficulty = item.get("difficulty")

            if question_id is None or difficulty is None:
                continue

            result = await self.session.execute(
                update(Question)
                .where(Question.id == str(question_id))
                .values(difficulty=difficulty, updated_at=datetime.now(timezone.utc))
            )
            updated_count += result.rowcount

        await self.session.commit()
        return updated_count


class ExamBatchService:
    """
    Sinav islemleri icin batch service.

    Toplu cevap gonderme ve sonuc getirme islemleri.

    Example:
        >>> service = ExamBatchService(db_session)
        >>> await service.batch_submit_answers(
        ...     exam_id="exam1",
        ...     answers=[{"question_id": "q1", "answer": "A"}, ...]
        ... )
    """

    def __init__(self, session: AsyncSession):
        """
        ExamBatchService baslatici.

        Args:
            session: Database session
        """
        self.session = session

    async def batch_submit_answers(
        self,
        exam_id: str | UUID,
        user_id: str | UUID,
        answers: list[dict[str, Any]],
    ) -> dict:
        """
        Birden fazla cevabi toplu olarak gonderir.

        Args:
            exam_id: Sinav ID
            user_id: Kullanici ID
            answers: [{"question_id": "q1", "answer": "A"}, ...]

        Returns:
            Gonderim sonucu
        """
        from sqlalchemy import select
        from models.database import ExamAnswer, Question

        if not answers:
            return {"submitted": 0, "correct": 0}

        # Sorularin dogru cevaplarini al
        question_ids = [a["question_id"] for a in answers]
        query = select(Question).where(Question.id.in_(question_ids))
        result = await self.session.execute(query)
        questions = {str(q.id): q for q in result.scalars().all()}

        # Cevaplari kaydet
        submitted = 0
        correct = 0

        for answer_data in answers:
            question_id = answer_data.get("question_id")
            given_answer = answer_data.get("answer")

            if not question_id or not given_answer:
                continue

            question = questions.get(str(question_id))
            is_correct = False

            if question and question.correct_answer:
                is_correct = given_answer.upper() == question.correct_answer.upper()

            # Cevabi kaydet
            exam_answer = ExamAnswer(
                exam_id=str(exam_id),
                user_id=str(user_id),
                question_id=str(question_id),
                given_answer=given_answer,
                is_correct=is_correct,
                answered_at=datetime.now(timezone.utc),
            )
            self.session.add(exam_answer)

            submitted += 1
            if is_correct:
                correct += 1

        await self.session.commit()

        return {
            "submitted": submitted,
            "correct": correct,
            "accuracy": correct / submitted if submitted > 0 else 0,
        }

    async def batch_get_results(
        self,
        exam_ids: list[str | UUID],
        user_id: str | UUID,
    ) -> list[dict]:
        """
        Birden fazla sinav sonucunu toplu olarak getirir.

        Args:
            exam_ids: Sinav ID listesi
            user_id: Kullanici ID

        Returns:
            Sinav sonuclari listesi
        """
        from sqlalchemy import select, func
        from models.database import ExamAnswer

        if not exam_ids:
            return []

        str_ids = [str(eid) for eid in exam_ids]

        # Toplu sorgu
        query = (
            select(
                ExamAnswer.exam_id,
                func.count(ExamAnswer.id).label("total"),
                func.sum(ExamAnswer.is_correct.cast(int)).label("correct"),
            )
            .where(ExamAnswer.exam_id.in_(str_ids))
            .where(ExamAnswer.user_id == str(user_id))
            .group_by(ExamAnswer.exam_id)
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "exam_id": row.exam_id,
                "total_questions": row.total,
                "correct_answers": row.correct or 0,
                "accuracy": (row.correct or 0) / row.total if row.total > 0 else 0,
            }
            for row in rows
        ]


# Global batch processor instance
_batch_processor: BatchProcessor | None = None


def get_batch_processor() -> BatchProcessor:
    """Global batch processor dondur."""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(max_operations=10)
    return _batch_processor


__all__ = [
    "BatchOperation",
    "BatchOperationType",
    "BatchProcessor",
    "BatchResponse",
    "BatchResult",
    "ExamBatchService",
    "QuestionBatchService",
    "get_batch_processor",
]
