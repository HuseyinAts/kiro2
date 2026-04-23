"""
Pipeline Orchestrator
6 Aşamalı Soru Üretim Pipeline Koordinatörü

Requirements (REQ-7.x):
- REQ-7.1: Agent'ları sırayla çağırır
- REQ-7.2: Output'u bir sonraki agent'a input olarak verir
- REQ-7.3: Retry logic uygular (max 3 retry)
- REQ-7.4: Retry başarısız olduğunda pipeline'ı durdurur
- REQ-7.5: Execution time ve süreleri loglar
- REQ-7.6: Paralel işlem mümkün olduğunda agent'ları paralel çalıştırır
"""

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from .agents import (
    ComplianceAgent,
    ContentGeneratorAgent,
    DifficultyAgent,
    DistractorAgent,
    LanguageQAAgent,
    QualityGateAgent,
)
from .pipeline_state import PipelineState, PipelineStatus, StageResult
from .stage_base import BasePipelineStage, StageInput, StageOutput

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Soru Üretim Pipeline Koordinatörü

    6 aşamalı pipeline'ı yönetir:
    1. Content Generator
    2. Difficulty Calibration
    3. Distractor Generator
    4. ÖSYM Compliance
    5. Language QA
    6. Quality Gate

    Özellikler:
    - Sequential/Parallel execution
    - Retry logic
    - State management
    - Performance monitoring
    """

    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # seconds

    # Parallel stage groups (Stage 4 ve 5 paralel çalışabilir)
    PARALLEL_GROUPS = [
        ["osym_compliance", "language_qa"]  # Bu ikisi paralel
    ]

    def __init__(
        self,
        llm_client: Any | None = None,
        redis_client: Any | None = None,
        config: dict[str, Any] | None = None
    ):
        """
        Orchestrator başlat

        Args:
            llm_client: LLM istemcisi
            redis_client: Redis istemcisi (state management)
            config: Ek konfigürasyon
        """
        self.llm = llm_client
        self.redis = redis_client
        self.config = config or {}

        # Stage'leri başlat
        self.stages: dict[str, BasePipelineStage] = {}
        self._initialize_stages()

        # Active pipelines
        self._active_pipelines: dict[str, PipelineState] = {}

    def _initialize_stages(self) -> None:
        """Pipeline aşamalarını başlat"""
        stage_classes: list[type[BasePipelineStage]] = [
            ContentGeneratorAgent,
            DifficultyAgent,
            DistractorAgent,
            ComplianceAgent,
            LanguageQAAgent,
            QualityGateAgent
        ]

        for stage_class in stage_classes:
            stage = stage_class(llm_client=self.llm)
            self.stages[stage.stage_name] = stage

        logger.info(f"Pipeline initialized with {len(self.stages)} stages")

    def get_stage_order(self) -> list[str]:
        """Aşama sırasını döndür"""
        return [
            "content_generator",
            "difficulty_calibration",
            "distractor_generator",
            "osym_compliance",
            "language_qa",
            "quality_gate"
        ]

    async def execute_pipeline(
        self,
        initial_input: dict[str, Any],
        pipeline_id: str | None = None,
        created_by: str | None = None
    ) -> dict[str, Any]:
        """
        Tam pipeline'ı çalıştır

        Args:
            initial_input: Başlangıç verisi (kazanım, ders, konu vb.)
            pipeline_id: Pipeline ID (opsiyonel, otomatik üretilir)
            created_by: Oluşturan kullanıcı

        Returns:
            Dict[str, Any]: Pipeline sonucu
        """
        # Pipeline ID
        pipeline_id = pipeline_id or str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Starting pipeline {pipeline_id}")

        # State oluştur
        state = PipelineState(
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            initial_input=initial_input,
            current_data=initial_input.copy(),
            created_by=created_by,
            started_at=datetime.now(UTC)
        )

        self._active_pipelines[pipeline_id] = state

        # Stage input hazırla
        stage_input = StageInput(
            question_data=initial_input,
            metadata={"pipeline_id": pipeline_id},
            previous_scores={}
        )

        try:
            # Aşamaları sırayla çalıştır
            stage_order = self.get_stage_order()

            for i, stage_name in enumerate(stage_order):
                state.current_stage = stage_name

                # Paralel çalıştırılabilir mi kontrol et
                parallel_group = self._get_parallel_group(stage_name)

                if parallel_group and stage_name == parallel_group[0]:
                    # Paralel çalıştır
                    stage_input, success = await self._execute_parallel_stages(
                        parallel_group, stage_input, state
                    )
                    if not success:
                        break
                    # Paralel gruptaki diğer stage'leri atla
                    continue
                if parallel_group and stage_name in parallel_group[1:]:
                    # Paralel grupta zaten işlendi
                    continue

                # Sequential çalıştır
                output = await self._execute_stage_with_retry(
                    stage_name, stage_input, state
                )

                if not output:
                    # Stage başarısız
                    break

                # Sonraki stage için input hazırla
                stage_input = StageInput(
                    question_data=output.question_data,
                    metadata=stage_input.metadata,
                    previous_scores={
                        **stage_input.previous_scores,
                        stage_name: output.score
                    }
                )

                state.current_data = output.question_data

                # Kritik hata kontrolü
                if not output.passed and output.score < 0.5:
                    logger.warning(f"Pipeline {pipeline_id} stopped at {stage_name} due to low score")
                    break

        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            state.status = PipelineStatus.FAILED
            state.metadata["error"] = str(e)

        # Finalize
        state.completed_at = datetime.now(UTC)
        state.total_duration = time.time() - start_time

        # Final skor ve karar
        if state.stage_results:
            state.final_score = self._calculate_final_score(state.stage_results)
            state.decision = self._make_final_decision(state.final_score)
            state.status = PipelineStatus.COMPLETED
        else:
            state.status = PipelineStatus.FAILED
            state.decision = "rejected"

        # Final output
        state.final_output = {
            "pipeline_id": pipeline_id,
            "question": state.current_data,
            "stage_results": [r.dict() for r in state.stage_results],
            "final_score": state.final_score,
            "decision": state.decision,
            "total_duration": state.total_duration,
            "status": state.status
        }

        logger.info(
            f"Pipeline {pipeline_id} completed: "
            f"score={state.final_score:.2%}, decision={state.decision}, "
            f"duration={state.total_duration:.2f}s"
        )

        return state.final_output

    async def _execute_stage_with_retry(
        self,
        stage_name: str,
        input_data: StageInput,
        state: PipelineState
    ) -> StageOutput | None:
        """
        Stage'i retry logic ile çalıştır

        Args:
            stage_name: Stage adı
            input_data: Stage girişi
            state: Pipeline state

        Returns:
            Optional[StageOutput]: Stage çıkışı veya None
        """
        stage = self.stages.get(stage_name)
        if not stage:
            logger.error(f"Stage not found: {stage_name}")
            return None

        for attempt in range(self.MAX_RETRIES):
            try:
                stage_start = time.time()

                # Stage çalıştır
                output = await stage.process(input_data)

                stage_duration = time.time() - stage_start

                # Result kaydet
                result = StageResult(
                    stage_name=stage_name,
                    score=output.score,
                    passed=output.passed,
                    duration=stage_duration,
                    errors=output.errors,
                    warnings=output.warnings,
                    retry_count=attempt,
                    completed_at=datetime.now(UTC)
                )
                state.add_stage_result(result)

                logger.info(
                    f"Stage {stage_name} completed: "
                    f"score={output.score:.2%}, passed={output.passed}, "
                    f"duration={stage_duration:.2f}s, attempt={attempt + 1}"
                )

                return output

            except Exception as e:
                logger.warning(
                    f"Stage {stage_name} attempt {attempt + 1} failed: {e}"
                )

                if attempt < self.MAX_RETRIES - 1:
                    # Exponential backoff
                    delay = self.RETRY_DELAY_BASE ** attempt
                    await asyncio.sleep(delay)
                else:
                    # Son deneme de başarısız
                    result = StageResult(
                        stage_name=stage_name,
                        score=0.0,
                        passed=False,
                        duration=0.0,
                        errors=[str(e)],
                        warnings=[],
                        retry_count=attempt,
                        completed_at=datetime.now(UTC)
                    )
                    state.add_stage_result(result)
                    logger.error(f"Stage {stage_name} failed after {self.MAX_RETRIES} attempts")

        return None

    async def _execute_parallel_stages(
        self,
        stage_names: list[str],
        input_data: StageInput,
        state: PipelineState
    ) -> tuple:
        """
        Paralel stage'leri çalıştır

        Args:
            stage_names: Paralel çalışacak stage'ler
            input_data: Ortak input
            state: Pipeline state

        Returns:
            tuple: (Güncellenmiş input, başarılı mı)
        """
        logger.info(f"Running parallel stages: {stage_names}")

        # Paralel task'lar oluştur
        tasks = []
        for stage_name in stage_names:
            task = self._execute_stage_with_retry(stage_name, input_data, state)
            tasks.append(task)

        # Paralel çalıştır
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sonuçları birleştir
        merged_data = input_data.question_data.copy()
        merged_scores = input_data.previous_scores.copy()
        all_passed = True

        for stage_name, result in zip(stage_names, results):
            if isinstance(result, Exception):
                logger.error(f"Parallel stage {stage_name} failed: {result}")
                all_passed = False
                continue

            if result:
                # Data'yı birleştir
                merged_data.update(result.question_data)
                merged_scores[stage_name] = result.score
                if not result.passed:
                    all_passed = False
            else:
                all_passed = False

        # Yeni input oluştur
        new_input = StageInput(
            question_data=merged_data,
            metadata=input_data.metadata,
            previous_scores=merged_scores
        )

        return new_input, all_passed

    def _get_parallel_group(self, stage_name: str) -> list[str] | None:
        """Stage'in paralel grubunu bul"""
        for group in self.PARALLEL_GROUPS:
            if stage_name in group:
                return group
        return None

    def _calculate_final_score(self, stage_results: list[StageResult]) -> float:
        """Final skoru hesapla"""
        total_score = 0.0
        total_weight = 0.0

        for result in stage_results:
            stage = self.stages.get(result.stage_name)
            if stage:
                weight = stage.get_stage_weight()
                total_score += result.score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(total_score / total_weight, 4)

    def _make_final_decision(self, score: float) -> str:
        """Final karar ver"""
        if score >= 0.85:
            return "approved"
        if score >= 0.70:
            return "review"
        return "rejected"

    async def get_pipeline_status(self, pipeline_id: str) -> dict | None:
        """Pipeline durumunu getir"""
        state = self._active_pipelines.get(pipeline_id)
        if state:
            return state.to_summary()

        # Redis'ten kontrol et
        if self.redis:
            try:
                data = await self.redis.get(f"pipeline:{pipeline_id}")
                if data:
                    return data
            except Exception:
                pass

        return None

    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Pipeline'ı iptal et"""
        state = self._active_pipelines.get(pipeline_id)
        if state and state.status == PipelineStatus.RUNNING:
            state.status = PipelineStatus.CANCELLED
            logger.info(f"Pipeline {pipeline_id} cancelled")
            return True
        return False

    def get_metrics(self) -> dict[str, Any]:
        """Pipeline metriklerini döndür"""
        total = len(self._active_pipelines)
        completed = sum(
            1 for p in self._active_pipelines.values()
            if p.status == PipelineStatus.COMPLETED
        )
        failed = sum(
            1 for p in self._active_pipelines.values()
            if p.status == PipelineStatus.FAILED
        )

        # Ortalama süre
        durations = [
            p.total_duration for p in self._active_pipelines.values()
            if p.total_duration > 0
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Ortalama skor
        scores = [
            p.final_score for p in self._active_pipelines.values()
            if p.final_score is not None
        ]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "total_pipelines": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "avg_duration": round(avg_duration, 2),
            "avg_score": round(avg_score, 4),
            "stages": list(self.stages.keys())
        }
