"""
TDD: Policy validator stub'larının gerçek logic ile değiştirilmesi testleri.

Bu testler ÖNCE FAIL etmeli (stub'lar her zaman True döndürüyor),
fix sonrası PASS etmeli.
"""

import threading

import pytest

from orchestrator.core.policy_engine import PolicyEngine, get_policy_engine


@pytest.fixture
def engine():
    return PolicyEngine()


# --- Quality Validator ---


def test_quality_validator_fails_on_low_coverage(engine):
    result = engine.evaluate({"test_coverage": 40}, policy_ids=["P22_TEST_COVERAGE"])
    assert len(result) == 1
    assert result[0].passed is False, "Düşük test coverage (40%) reject edilmeli"


def test_quality_validator_passes_on_high_coverage(engine):
    result = engine.evaluate({"test_coverage": 80}, policy_ids=["P22_TEST_COVERAGE"])
    assert result[0].passed is True


def test_quality_validator_fails_on_high_complexity(engine):
    result = engine.evaluate({"complexity_score": 20}, policy_ids=["P21_CODE_STYLE"])
    assert result[0].passed is False, "Yüksek complexity (>15) reject edilmeli"


def test_quality_validator_passes_on_low_complexity(engine):
    result = engine.evaluate({"complexity_score": 5}, policy_ids=["P21_CODE_STYLE"])
    assert result[0].passed is True


# --- Resource Validator ---


def test_resource_validator_fails_on_high_cpu(engine):
    result = engine.evaluate({"cpu_usage_pct": 95}, policy_ids=["P31_CPU_LIMITS"])
    assert result[0].passed is False, "Yüksek CPU (%95) reject edilmeli"


def test_resource_validator_passes_on_normal_cpu(engine):
    result = engine.evaluate({"cpu_usage_pct": 50}, policy_ids=["P31_CPU_LIMITS"])
    assert result[0].passed is True


def test_resource_validator_fails_on_memory_exceeded(engine):
    result = engine.evaluate(
        {"memory_mb": 9000, "memory_limit_mb": 8192},
        policy_ids=["P32_MEMORY_LIMITS"],
    )
    assert result[0].passed is False, "Memory limit aşımı reject edilmeli"


# --- Learning Validator ---


def test_learning_validator_fails_on_regression(engine):
    result = engine.evaluate(
        {"regression_detected": True}, policy_ids=["P41_REGRESSION_PREVENTION"]
    )
    assert result[0].passed is False, "Regresyon tespiti reject edilmeli"


def test_learning_validator_passes_without_regression(engine):
    result = engine.evaluate(
        {"regression_detected": False}, policy_ids=["P41_REGRESSION_PREVENTION"]
    )
    assert result[0].passed is True


def test_learning_validator_fails_on_large_parameter_delta(engine):
    result = engine.evaluate({"parameter_delta": 0.8}, policy_ids=["P39_PARAMETER_BOUNDS"])
    assert result[0].passed is False, "Büyük parametre değişimi (>0.5) reject edilmeli"


# --- Workflow Integrity ---


def test_workflow_integrity_fails_on_empty_steps(engine):
    result = engine.evaluate({"workflow": {"steps": []}}, policy_ids=["P3_WORKFLOW_INTEGRITY"])
    assert result[0].passed is False, "Boş workflow steps reject edilmeli"


def test_workflow_integrity_passes_with_steps(engine):
    result = engine.evaluate(
        {"workflow": {"steps": ["step1", "step2"]}}, policy_ids=["P3_WORKFLOW_INTEGRITY"]
    )
    assert result[0].passed is True


# --- Backward Compatibility: boş context her zaman True ---


def test_empty_context_always_passes(engine):
    """Boş context gönderildiğinde mevcut davranış korunmalı (backward compat)."""
    for policy_id in ["P22_TEST_COVERAGE", "P31_CPU_LIMITS", "P41_REGRESSION_PREVENTION"]:
        results = engine.evaluate({}, policy_ids=[policy_id])
        assert results[0].passed is True, f"{policy_id} boş ctx'te True olmalı"


# --- Singleton Thread Safety ---


def test_singleton_thread_safety():
    ids = []

    def get():
        ids.append(id(get_policy_engine()))

    threads = [threading.Thread(target=get) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(set(ids)) == 1, "Tüm thread'ler aynı singleton instance'ı almalı"
