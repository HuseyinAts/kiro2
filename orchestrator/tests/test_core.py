"""
KIRO2 Orchestrator Core - Unit Tests
====================================
Temel modül testleri.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Test imports
from orchestrator.core.state import (
    TaskStatus,
    QualityGateState,
    DiffStats,
    RunState,
)
from orchestrator.core.memory import (
    LessonType,
    ConfidenceLevel,
    Lesson,
    LessonEvidence,
)
from orchestrator.core.quality_gates import (
    GateAction,
    GateOutput,
)
from orchestrator.core.routing import (
    TaskType,
    RiskLevel,
    RoutingEngine,
    TaskAnalyzer,
)
from orchestrator.core.agents import (
    AgentRole,
    AgentOutput,
    AgentFactory,
)


# =============================================================================
# STATE TESTS
# =============================================================================

class TestDiffStats:
    """DiffStats testleri"""

    def test_is_within_limits_default(self):
        """Varsayılan limitlerin içinde olmalı"""
        stats = DiffStats(files_changed=3, lines_added=50, lines_removed=50)
        assert stats.is_within_limits() is True

    def test_exceeds_files_limit(self):
        """Dosya limiti aşılamamalı"""
        stats = DiffStats(files_changed=6, lines_added=10, lines_removed=0)
        assert stats.is_within_limits() is False

    def test_exceeds_lines_limit(self):
        """Satır limiti aşılamamalı"""
        stats = DiffStats(files_changed=2, lines_added=150, lines_removed=60)
        assert stats.is_within_limits() is False

    def test_exceeds_total_limit(self):
        """Toplam satır limiti aşıldığında True dönmeli"""
        stats = DiffStats()
        assert stats.exceeds_total_limit(501) is True

    def test_within_total_limit(self):
        """Toplam satır limiti aşılmadığında False dönmeli"""
        stats = DiffStats()
        assert stats.exceeds_total_limit(400) is False


class TestRunState:
    """RunState testleri"""

    def test_initial_status_is_pending(self):
        """Başlangıç durumu PENDING olmalı"""
        state = RunState(run_id="test-123", task_id="task-456")
        assert state.status == TaskStatus.PENDING

    def test_increment_iteration(self):
        """Iterasyon artırılabilmeli"""
        state = RunState(run_id="test-123", task_id="task-456")
        state.increment_iteration()
        assert state.current_iteration == 1

    def test_cannot_continue_after_max_iterations(self):
        """Max iterasyon sonrası devam edilememeli"""
        state = RunState(run_id="test-123", task_id="task-456")
        state.max_iterations = 3
        state.current_iteration = 3
        assert state.can_continue() is False

    def test_no_progress_detection(self):
        """Aynı hata 4 kez tekrarlanırsa BLOCKED"""
        state = RunState(run_id="test-123", task_id="task-456")
        # Aynı hatayı 4 kez record et
        for _ in range(4):
            state.record_error("lint", "test error message")
        assert state.status == TaskStatus.BLOCKED

    def test_different_errors_no_block(self):
        """Farklı hatalar BLOCKED tetiklememeli"""
        state = RunState(run_id="test-123", task_id="task-456")
        state.record_error("lint", "error 1")
        state.record_error("lint", "error 2")
        state.record_error("lint", "error 3")
        state.record_error("lint", "error 4")
        assert state.can_continue() is True

    def test_quality_gates_initialized(self):
        """Varsayılan kalite kapıları oluşturulmalı"""
        state = RunState(run_id="test-123", task_id="task-456")
        assert "lint" in state.quality_gates
        assert "typecheck" in state.quality_gates
        assert "unit_test" in state.quality_gates

    def test_to_dict_serializable(self):
        """to_dict JSON serializable olmalı"""
        state = RunState(run_id="test-123", task_id="task-456")
        data = state.to_dict()
        json.dumps(data)  # Should not raise


# =============================================================================
# MEMORY TESTS
# =============================================================================

class TestLesson:
    """Lesson testleri"""

    def test_confidence_low_with_few_evidence(self):
        """Az kanıt ile confidence LOW"""
        lesson = Lesson(
            id="test-1",
            lesson_type=LessonType.ERROR_RESOLUTION,
            category="test",
            description="test lesson",
        )
        assert lesson.confidence == ConfidenceLevel.LOW

    def test_confidence_medium_with_more_evidence(self):
        """3-5 kanıt ile confidence MEDIUM"""
        lesson = Lesson(
            id="test-2",
            lesson_type=LessonType.PATTERN_RISK,
            category="test",
            description="test lesson",
        )
        for i in range(5):
            evidence = LessonEvidence(
                run_id=f"run-{i}",
                task_id=f"task-{i}",
                timestamp=datetime.utcnow(),
                gates_passed=["lint", "typecheck"],
                iterations_to_green=2,
                cost=0.01,
            )
            lesson.add_evidence(evidence)
        assert lesson.confidence == ConfidenceLevel.MEDIUM

    def test_confidence_high_with_many_evidence(self):
        """6+ kanıt ile confidence HIGH"""
        lesson = Lesson(
            id="test-3",
            lesson_type=LessonType.STRATEGY_SUCCESS,
            category="test",
            description="test lesson",
        )
        for i in range(8):
            evidence = LessonEvidence(
                run_id=f"run-{i}",
                task_id=f"task-{i}",
                timestamp=datetime.utcnow(),
                gates_passed=["lint", "typecheck", "unit_test"],
                iterations_to_green=1,
                cost=0.01,
            )
            lesson.add_evidence(evidence)
        assert lesson.confidence == ConfidenceLevel.HIGH


# =============================================================================
# ROUTING TESTS
# =============================================================================

class TestRoutingEngine:
    """RoutingEngine / TaskAnalyzer testleri"""

    def test_detect_turkish_nlp_task(self):
        """Turkish NLP task'ı doğru detect etmeli"""
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze("Türkçe sentiment analizi yap")
        assert analysis.task_type == TaskType.TURKISH_NLP

    def test_detect_security_task(self):
        """Security task'ı doğru detect etmeli"""
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze("Fix SQL injection vulnerability in auth")
        assert analysis.task_type == TaskType.SECURITY

    def test_detect_frontend_task(self):
        """Frontend task'ı doğru detect etmeli"""
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze("Create React component for student dashboard")
        assert analysis.task_type == TaskType.FRONTEND

    def test_critical_risk_for_migrations(self):
        """Migration dosyaları CRITICAL risk olmalı"""
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(
            "Update database migration",
            files=["core/alembic/versions/001_init.py"]
        )
        assert analysis.risk_level == RiskLevel.CRITICAL

    def test_high_risk_for_auth_files(self):
        """Auth dosyaları HIGH risk olmalı"""
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(
            "Update authentication logic",
            files=["backend/app/core/auth.py"]
        )
        assert analysis.risk_level == RiskLevel.HIGH


# =============================================================================
# AGENTS TESTS
# =============================================================================

class TestAgentFactory:
    """AgentFactory testleri"""

    def test_create_all_agent_types(self):
        """Tüm ajan tipleri oluşturulabilmeli"""
        for role in AgentRole:
            agent = AgentFactory.create(role)
            assert agent.role == role

    def test_planner_has_correct_system_prompt(self):
        """Planner doğru system prompt'a sahip olmalı"""
        agent = AgentFactory.create(AgentRole.PLANNER)
        assert "SMART" in agent.system_prompt
        assert "plan" in agent.system_prompt.lower()

    def test_security_auditor_has_correct_system_prompt(self):
        """Security Auditor doğru system prompt'a sahip olmalı"""
        agent = AgentFactory.create(AgentRole.SECURITY_AUDITOR)
        assert "SQL injection" in agent.system_prompt
        assert "XSS" in agent.system_prompt


class TestAgentOutput:
    """AgentOutput testleri"""

    def test_agent_output_serializable(self):
        """AgentOutput JSON serializable olmalı"""
        output = AgentOutput(
            role=AgentRole.PLANNER,
            success=True,
            content={"plan": []},
            reasoning="Test reasoning",
            confidence=0.9,
            files_affected=["test.py"],
            metadata={"cost": 0.01}
        )
        # Should not raise
        json.dumps({
            "role": output.role.value,
            "success": output.success,
            "content": output.content,
            "confidence": output.confidence,
        })


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
