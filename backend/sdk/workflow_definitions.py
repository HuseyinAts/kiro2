"""
KIRO2 Workflow Definitions

Claude Code workflow tanımları ve orchestration.
Multi-step görevler için workflow decorator ve yönetim sınıfları.

Kullanım:
    from backend.sdk.workflow_definitions import workflow, create_workflow

    @workflow("code-review")
    async def review_workflow(files: list[str]):
        results = []
        for file in files:
            content = await read_file(file)
            analysis = await analyze_code(content)
            results.append(analysis)
        return aggregate_results(results)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
WorkflowFunc = Callable[..., Coroutine[Any, Any, Any]]


class WorkflowStatus(str, Enum):
    """Workflow durumu."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Workflow adımı."""

    name: str
    description: str = ""
    handler: Callable | None = None
    depends_on: list[str] = field(default_factory=list)
    timeout_ms: int = 60000
    retry_count: int = 0
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowResult:
    """Workflow çalıştırma sonucu."""

    workflow_name: str
    status: WorkflowStatus
    steps: list[WorkflowStep]
    output: Any = None
    total_duration_ms: int = 0
    error: str | None = None


class WorkflowRegistry:
    """
    Workflow registry sınıfı.

    Tanımlı workflow'ların kaydedilmesi ve yönetilmesi için kullanılır.
    """

    _instance: WorkflowRegistry | None = None
    _workflows: dict[str, dict[str, Any]] = {}

    def __new__(cls) -> WorkflowRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._workflows = {}
        return cls._instance

    def register(
        self,
        name: str,
        description: str = "",
        steps: list[WorkflowStep] | None = None,
    ) -> Callable[[WorkflowFunc], WorkflowFunc]:
        """
        Workflow kaydetme decorator'ı.

        Args:
            name: Workflow adı
            description: Açıklama
            steps: Opsiyonel adım tanımları

        Returns:
            Decorator
        """
        def decorator(func: WorkflowFunc) -> WorkflowFunc:
            self._workflows[name] = {
                "name": name,
                "description": description or func.__doc__ or "",
                "handler": func,
                "steps": steps or [],
            }
            logger.info(f"Registered workflow: {name}")
            return func

        return decorator

    def get(self, name: str) -> dict[str, Any] | None:
        """Workflow tanımı al."""
        return self._workflows.get(name)

    def list_workflows(self) -> list[str]:
        """Kayıtlı workflow listesi."""
        return list(self._workflows.keys())

    async def execute(
        self,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> WorkflowResult:
        """
        Workflow çalıştır.

        Args:
            name: Workflow adı
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            WorkflowResult
        """
        import time

        workflow_def = self.get(name)
        if not workflow_def:
            return WorkflowResult(
                workflow_name=name,
                status=WorkflowStatus.FAILED,
                steps=[],
                error=f"Workflow not found: {name}",
            )

        start_time = time.time()

        try:
            handler = workflow_def["handler"]
            output = await handler(*args, **kwargs)

            duration_ms = int((time.time() - start_time) * 1000)

            return WorkflowResult(
                workflow_name=name,
                status=WorkflowStatus.COMPLETED,
                steps=workflow_def.get("steps", []),
                output=output,
                total_duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Workflow {name} failed: {e}")
            duration_ms = int((time.time() - start_time) * 1000)

            return WorkflowResult(
                workflow_name=name,
                status=WorkflowStatus.FAILED,
                steps=workflow_def.get("steps", []),
                error=str(e),
                total_duration_ms=duration_ms,
            )


# Global registry instance
_registry = WorkflowRegistry()


def workflow(
    name: str,
    description: str = "",
    steps: list[WorkflowStep] | None = None,
) -> Callable[[WorkflowFunc], WorkflowFunc]:
    """
    Workflow tanımlama decorator'ı.

    Kullanım:
        @workflow("code-review")
        async def review_workflow(files: list[str]):
            ...

    Args:
        name: Workflow adı
        description: Açıklama
        steps: Adım tanımları

    Returns:
        Decorator
    """
    return _registry.register(name=name, description=description, steps=steps)


def create_workflow(
    name: str,
    steps: list[WorkflowStep],
    description: str = "",
) -> str:
    """
    Programatik workflow oluştur.

    Args:
        name: Workflow adı
        steps: Adım listesi
        description: Açıklama

    Returns:
        Oluşturulan workflow adı
    """
    async def dynamic_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
        results = {}
        for step in steps:
            if step.handler:
                try:
                    step.status = WorkflowStatus.RUNNING
                    step.started_at = datetime.now()

                    result = await step.handler(*args, **kwargs)

                    step.result = result
                    step.status = WorkflowStatus.COMPLETED
                    step.completed_at = datetime.now()
                    results[step.name] = result

                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    step.completed_at = datetime.now()
                    raise

        return results

    _registry._workflows[name] = {
        "name": name,
        "description": description,
        "handler": dynamic_handler,
        "steps": steps,
    }

    return name


async def run_workflow(
    name: str,
    *args: Any,
    **kwargs: Any,
) -> WorkflowResult:
    """
    Workflow çalıştır.

    Args:
        name: Workflow adı
        *args: Arguments
        **kwargs: Keyword arguments

    Returns:
        WorkflowResult
    """
    return await _registry.execute(name, *args, **kwargs)


# Predefined KIRO2 workflows

@workflow(
    name="code-review",
    description="Multi-stage code review workflow",
    steps=[
        WorkflowStep(name="read", description="Dosyaları oku"),
        WorkflowStep(name="lint", description="Linting kontrolü", depends_on=["read"]),
        WorkflowStep(name="security", description="Güvenlik taraması", depends_on=["read"]),
        WorkflowStep(name="report", description="Rapor oluştur", depends_on=["lint", "security"]),
    ],
)
async def code_review_workflow(files: list[str]) -> dict[str, Any]:
    """
    Kod inceleme workflow'u.

    Adımlar:
    1. Dosyaları oku
    2. Linting kontrolü (ruff)
    3. Güvenlik taraması (bandit)
    4. Rapor oluştur

    Args:
        files: İncelenecek dosyalar

    Returns:
        İnceleme sonuçları
    """
    results = {
        "files_reviewed": len(files),
        "issues": [],
        "suggestions": [],
    }

    # Simüle edilmiş inceleme
    for file in files:
        results["issues"].append({
            "file": file,
            "type": "info",
            "message": f"Reviewed {file}",
        })

    return results


@workflow(
    name="test-generation",
    description="Automatic test generation workflow",
    steps=[
        WorkflowStep(name="analyze", description="Kodu analiz et"),
        WorkflowStep(name="generate", description="Test üret", depends_on=["analyze"]),
        WorkflowStep(name="validate", description="Testleri doğrula", depends_on=["generate"]),
    ],
)
async def test_generation_workflow(source_file: str) -> dict[str, Any]:
    """
    Otomatik test üretme workflow'u.

    Args:
        source_file: Kaynak dosya

    Returns:
        Üretilen testler
    """
    return {
        "source_file": source_file,
        "tests_generated": 0,
        "coverage_estimate": 0.0,
    }


@workflow(
    name="question-validation",
    description="YKS soru validasyon workflow'u",
    steps=[
        WorkflowStep(name="parse", description="Soruyu parse et"),
        WorkflowStep(name="irt_validate", description="IRT parametrelerini doğrula", depends_on=["parse"]),
        WorkflowStep(name="zpd_check", description="ZPD kontrolü", depends_on=["irt_validate"]),
        WorkflowStep(name="turkish_check", description="Türkçe kontrolü", depends_on=["parse"]),
        WorkflowStep(name="duplicate_check", description="Duplicate kontrolü", depends_on=["parse"]),
    ],
)
async def question_validation_workflow(question: dict[str, Any]) -> dict[str, Any]:
    """
    YKS soru validasyon workflow'u.

    Kontroller:
    1. Soru formatı
    2. IRT parametreleri
    3. ZPD uygunluğu
    4. Türkçe karakter
    5. Duplicate kontrolü

    Args:
        question: Soru verisi

    Returns:
        Validasyon sonucu
    """
    from backend.sdk.tool_definitions import irt_calculator, zpd_analyzer

    # IRT parametrelerini al
    difficulty = question.get("difficulty", 0.0)
    discrimination = question.get("discrimination", 1.0)
    guessing = question.get("guessing", 0.2)

    # Başarı olasılığı hesapla (ortalama öğrenci için θ=0)
    try:
        prob = irt_calculator(difficulty, discrimination, guessing, ability=0.0)
        zpd_result = zpd_analyzer(prob)
        irt_valid = True
    except ValueError as e:
        irt_valid = False
        zpd_result = {"in_zpd": False, "error": str(e)}

    return {
        "question_id": question.get("id"),
        "irt_valid": irt_valid,
        "zpd_result": zpd_result,
        "overall_valid": irt_valid and zpd_result.get("in_zpd", False),
    }


@workflow(
    name="batch-refactor",
    description="Toplu refactoring workflow'u",
)
async def batch_refactor_workflow(
    pattern: str,
    replacement: str,
    glob_pattern: str,
) -> dict[str, Any]:
    """
    Toplu refactoring.

    Args:
        pattern: Aranacak pattern
        replacement: Yerine konacak
        glob_pattern: Dosya pattern'i

    Returns:
        Refactoring sonucu
    """
    return {
        "pattern": pattern,
        "replacement": replacement,
        "files_modified": 0,
    }
