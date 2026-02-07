"""
Pipeline Orchestrator Tests
Pipeline koordinatör testleri

Property Tests (design.md):
- Property 5: Stage Execution Order
- Property 6: Retry Logic
"""

import pytest
from unittest.mock import AsyncMock

# Note: conftest.py adds backend dir to sys.path

from pipeline.orchestrator import PipelineOrchestrator
from pipeline.stage_base import StageInput, StageOutput
from pipeline.pipeline_state import PipelineStatus


class TestPipelineOrchestrator:
    """Pipeline Orchestrator test sınıfı"""

    @pytest.fixture
    def orchestrator(self):
        """Orchestrator fixture"""
        return PipelineOrchestrator()

    # ============== Unit Tests ==============

    def test_stage_initialization(self, orchestrator):
        """Stage başlatma testi"""
        assert len(orchestrator.stages) == 6
        assert "content_generator" in orchestrator.stages
        assert "difficulty_calibration" in orchestrator.stages
        assert "distractor_generator" in orchestrator.stages
        assert "osym_compliance" in orchestrator.stages
        assert "language_qa" in orchestrator.stages
        assert "quality_gate" in orchestrator.stages

    def test_stage_order(self, orchestrator):
        """Stage sırası testi"""
        order = orchestrator.get_stage_order()

        expected_order = [
            "content_generator",
            "difficulty_calibration",
            "distractor_generator",
            "osym_compliance",
            "language_qa",
            "quality_gate"
        ]

        assert order == expected_order

    def test_parallel_group_detection(self, orchestrator):
        """Paralel grup tespiti"""
        # osym_compliance ve language_qa paralel çalışabilmeli
        group1 = orchestrator._get_parallel_group("osym_compliance")
        group2 = orchestrator._get_parallel_group("language_qa")

        assert group1 is not None
        assert group2 is not None
        assert "osym_compliance" in group1
        assert "language_qa" in group1

    def test_final_score_calculation(self, orchestrator):
        """Final skor hesaplama testi"""
        from pipeline.pipeline_state import StageResult
        from datetime import datetime, timezone

        results = [
            StageResult(
                stage_name="content_generator",
                score=0.9,
                passed=True,
                duration=10.0,
                completed_at=datetime.now(timezone.utc)
            ),
            StageResult(
                stage_name="difficulty_calibration",
                score=0.8,
                passed=True,
                duration=5.0,
                completed_at=datetime.now(timezone.utc)
            )
        ]

        score = orchestrator._calculate_final_score(results)

        # (0.9 * 0.25 + 0.8 * 0.20) / (0.25 + 0.20) = 0.385 / 0.45 = 0.855...
        assert 0.8 <= score <= 0.9

    def test_final_decision(self, orchestrator):
        """Final karar testi"""
        assert orchestrator._make_final_decision(0.90) == "approved"
        assert orchestrator._make_final_decision(0.75) == "review"
        assert orchestrator._make_final_decision(0.60) == "rejected"

    @pytest.mark.asyncio
    async def test_execute_pipeline_success(self, orchestrator):
        """Başarılı pipeline çalıştırma testi"""
        # Mock stages
        for stage_name, stage in orchestrator.stages.items():
            mock_output = StageOutput(
                question_data={"question_text": "Test"},
                score=0.85,
                passed=True,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"stage": stage_name},
                execution_time=1.0
            )
            stage.process = AsyncMock(return_value=mock_output)

        result = await orchestrator.execute_pipeline({
            "kazanim": "Test kazanımı",
            "subject": "matematik",
            "topic": "Test konu"
        })

        assert result["status"] == PipelineStatus.COMPLETED
        assert "final_score" in result
        assert "decision" in result
        assert len(result["stage_results"]) > 0

    @pytest.mark.asyncio
    async def test_get_pipeline_status(self, orchestrator):
        """Pipeline durumu sorgulama testi"""
        # Var olmayan pipeline
        status = await orchestrator.get_pipeline_status("non-existent-id")
        assert status is None

    def test_get_metrics(self, orchestrator):
        """Metrik alma testi"""
        metrics = orchestrator.get_metrics()

        assert "total_pipelines" in metrics
        assert "completed" in metrics
        assert "failed" in metrics
        assert "success_rate" in metrics
        assert "stages" in metrics
        assert len(metrics["stages"]) == 6

    # ============== Property Tests ==============

    def test_property_stage_execution_order(self, orchestrator):
        """
        Property 5 (design.md): Stage Execution Order

        Stages must execute in order:
        Content → Difficulty → Distractor → Compliance → Language → Quality Gate
        """
        order = orchestrator.get_stage_order()

        # Sıra kontrolü
        assert order.index("content_generator") < order.index("difficulty_calibration")
        assert order.index("difficulty_calibration") < order.index("distractor_generator")
        assert order.index("distractor_generator") < order.index("osym_compliance")
        # osym_compliance ve language_qa paralel olabilir
        assert order.index("osym_compliance") < order.index("quality_gate")
        assert order.index("language_qa") < order.index("quality_gate")

    def test_property_max_retries(self, orchestrator):
        """
        Property 6 (design.md): Retry Logic

        Max 3 retries per stage
        """
        assert orchestrator.MAX_RETRIES == 3

    @pytest.mark.asyncio
    async def test_property_retry_logic_execution(self, orchestrator):
        """Retry logic çalışma testi"""
        # İlk 2 denemede fail, 3. denemede başarılı
        attempt_count = 0

        async def mock_process(input_data):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("Simulated failure")
            return StageOutput(
                question_data=input_data.question_data,
                score=0.8,
                passed=True,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={},
                execution_time=1.0
            )

        orchestrator.stages["content_generator"].process = mock_process

        from pipeline.pipeline_state import PipelineState

        state = PipelineState(
            pipeline_id="test",
            status=PipelineStatus.RUNNING,
            initial_input={}
        )

        input_data = StageInput(
            question_data={},
            metadata={},
            previous_scores={}
        )

        result = await orchestrator._execute_stage_with_retry(
            "content_generator",
            input_data,
            state
        )

        assert result is not None
        assert attempt_count == 3  # 3. denemede başarılı


class TestPipelineStateManagement:
    """Pipeline state yönetimi testleri"""

    @pytest.fixture
    def orchestrator(self):
        return PipelineOrchestrator()

    @pytest.mark.asyncio
    async def test_cancel_running_pipeline(self, orchestrator):
        """Çalışan pipeline'ı iptal etme"""
        from pipeline.pipeline_state import PipelineState

        # Active pipeline ekle
        state = PipelineState(
            pipeline_id="test-cancel",
            status=PipelineStatus.RUNNING,
            initial_input={}
        )
        orchestrator._active_pipelines["test-cancel"] = state

        result = await orchestrator.cancel_pipeline("test-cancel")

        assert result is True
        assert state.status == PipelineStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_pipeline(self, orchestrator):
        """Var olmayan pipeline'ı iptal etme"""
        result = await orchestrator.cancel_pipeline("nonexistent")
        assert result is False


class TestParallelExecution:
    """Paralel çalıştırma testleri"""

    @pytest.fixture
    def orchestrator(self):
        return PipelineOrchestrator()

    def test_parallel_groups_defined(self, orchestrator):
        """Paralel gruplar tanımlı mı"""
        assert len(orchestrator.PARALLEL_GROUPS) > 0
        assert ["osym_compliance", "language_qa"] in orchestrator.PARALLEL_GROUPS

    @pytest.mark.asyncio
    async def test_parallel_stages_execution(self, orchestrator):
        """Paralel aşamaların çalışması"""
        from pipeline.pipeline_state import PipelineState

        # Mock stages
        for stage_name in ["osym_compliance", "language_qa"]:
            mock_output = StageOutput(
                question_data={"test": True},
                score=0.9,
                passed=True,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={"stage": stage_name},
                execution_time=0.5
            )
            orchestrator.stages[stage_name].process = AsyncMock(return_value=mock_output)

        state = PipelineState(
            pipeline_id="test",
            status=PipelineStatus.RUNNING,
            initial_input={}
        )

        input_data = StageInput(
            question_data={},
            metadata={},
            previous_scores={}
        )

        new_input, success = await orchestrator._execute_parallel_stages(
            ["osym_compliance", "language_qa"],
            input_data,
            state
        )

        assert success is True
        assert "osym_compliance" in new_input.previous_scores
        assert "language_qa" in new_input.previous_scores


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
