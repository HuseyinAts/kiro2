"""
Performance Monitor - Agent Performans Izleme ve Analizi

Agent'larin performansini surekli izler, metrikler toplar ve iyilestirme onerileri sunar.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from .agent_genome import AgentGenome, PerformanceMetrics


class MetricType(Enum):
    """Metrik tipleri"""
    TASK_SUCCESS = "task_success"
    RESPONSE_TIME = "response_time"
    TOKEN_USAGE = "token_usage"
    ERROR_RATE = "error_rate"
    QUALITY_SCORE = "quality_score"
    USER_SATISFACTION = "user_satisfaction"


@dataclass
class TaskExecution:
    """Gorev calistirma kaydi"""
    agent_id: str
    task_id: str
    task_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    response_time_ms: float = 0
    token_count: int = 0
    quality_score: float = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "task_type": self.task_type,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "success": self.success,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "token_count": self.token_count,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
        }


@dataclass
class WeakPoint:
    """Zayif nokta analizi"""
    agent_id: str
    area: str
    severity: float  # 0-1
    description: str
    suggested_improvement: str


@dataclass
class Improvement:
    """Iyilestirme onerisi"""
    agent_id: str
    improvement_type: str
    priority: int  # 1-5, 1 en yuksek
    description: str
    expected_impact: float  # 0-1
    implementation_hint: str


class PerformanceMonitor:
    """
    Agent Performans Izleyici

    Gorevler:
    - Gorev calistirma metriklerini topla
    - Fitness skorlari hesapla
    - Zayif noktalari tespit et
    - Iyilestirme onerileri sun
    """

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.metrics_dir = self.base_path / "orchestration" / "metrics"

        # In-memory caches
        self._executions: dict[str, list[TaskExecution]] = defaultdict(list)
        self._aggregated_metrics: dict[str, PerformanceMetrics] = {}

        # Configuration
        self.max_history_days = 30
        self.min_tasks_for_analysis = 5

    async def initialize(self) -> None:
        """Monitor'u baslat"""
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        await self._load_historical_data()

    async def _load_historical_data(self) -> None:
        """Gecmis verileri yukle"""
        metrics_file = self.metrics_dir / "executions.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for agent_id, executions in data.items():
                        for ex in executions:
                            self._executions[agent_id].append(
                                TaskExecution(
                                    agent_id=ex["agent_id"],
                                    task_id=ex["task_id"],
                                    task_type=ex["task_type"],
                                    started_at=datetime.fromisoformat(ex["started_at"]),
                                    completed_at=datetime.fromisoformat(ex["completed_at"]) if ex.get("completed_at") else None,
                                    success=ex["success"],
                                    error_message=ex.get("error_message"),
                                    response_time_ms=ex["response_time_ms"],
                                    token_count=ex.get("token_count", 0),
                                    quality_score=ex.get("quality_score", 0),
                                    metadata=ex.get("metadata", {}),
                                )
                            )
            except Exception:
                pass  # Start fresh if file is corrupted

    async def _save_data(self) -> None:
        """Verileri kaydet"""
        metrics_file = self.metrics_dir / "executions.json"
        data = {
            agent_id: [ex.to_dict() for ex in executions]
            for agent_id, executions in self._executions.items()
        }
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    async def track_execution(
        self,
        agent_id: str,
        task_id: str,
        task_type: str,
        started_at: datetime,
        completed_at: datetime,
        success: bool,
        error_message: Optional[str] = None,
        token_count: int = 0,
        quality_score: float = 0,
        metadata: Optional[dict] = None,
    ) -> TaskExecution:
        """
        Gorev calistirma kaydi ekle

        Args:
            agent_id: Agent ID
            task_id: Gorev ID
            task_type: Gorev tipi
            started_at: Baslama zamani
            completed_at: Bitis zamani
            success: Basarili mi
            error_message: Hata mesaji
            token_count: Kullanilan token sayisi
            quality_score: Kalite skoru (0-1)
            metadata: Ek veriler

        Returns:
            TaskExecution kaydi
        """
        response_time_ms = (completed_at - started_at).total_seconds() * 1000

        execution = TaskExecution(
            agent_id=agent_id,
            task_id=task_id,
            task_type=task_type,
            started_at=started_at,
            completed_at=completed_at,
            success=success,
            error_message=error_message,
            response_time_ms=response_time_ms,
            token_count=token_count,
            quality_score=quality_score,
            metadata=metadata or {},
        )

        self._executions[agent_id].append(execution)

        # Clean old data
        await self._cleanup_old_data(agent_id)

        # Save periodically
        if len(self._executions[agent_id]) % 10 == 0:
            await self._save_data()

        return execution

    async def _cleanup_old_data(self, agent_id: str) -> None:
        """Eski verileri temizle"""
        cutoff = datetime.now() - timedelta(days=self.max_history_days)
        self._executions[agent_id] = [
            ex for ex in self._executions[agent_id]
            if ex.started_at > cutoff
        ]

    async def calculate_fitness(self, agent_id: str) -> float:
        """
        Agent fitness skorunu hesapla

        Args:
            agent_id: Agent ID

        Returns:
            Fitness skoru (0-1)
        """
        executions = self._executions.get(agent_id, [])

        if len(executions) < self.min_tasks_for_analysis:
            return 0.5  # Default score

        # Calculate components
        success_rate = sum(1 for e in executions if e.success) / len(executions)

        # Response time score (inverse, faster is better)
        avg_response = sum(e.response_time_ms for e in executions) / len(executions)
        response_score = max(0, 1 - (avg_response / 10000))  # 10s = 0 score

        # Quality score
        quality_scores = [e.quality_score for e in executions if e.quality_score > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

        # Weighted fitness
        fitness = (
            success_rate * 0.4 +
            response_score * 0.3 +
            avg_quality * 0.3
        )

        return min(1.0, max(0.0, fitness))

    async def get_metrics(self, agent_id: str) -> PerformanceMetrics:
        """
        Agent icin toplam metrikleri getir

        Args:
            agent_id: Agent ID

        Returns:
            PerformanceMetrics
        """
        executions = self._executions.get(agent_id, [])

        if not executions:
            return PerformanceMetrics()

        successful = [e for e in executions if e.success]

        return PerformanceMetrics(
            total_tasks=len(executions),
            successful_tasks=len(successful),
            failed_tasks=len(executions) - len(successful),
            avg_response_time_ms=sum(e.response_time_ms for e in executions) / len(executions),
            total_tokens_used=sum(e.token_count for e in executions),
        )

    async def identify_weak_points(self, agent_id: str) -> list[WeakPoint]:
        """
        Agent zayif noktalarini tespit et

        Args:
            agent_id: Agent ID

        Returns:
            WeakPoint listesi
        """
        executions = self._executions.get(agent_id, [])
        weak_points = []

        if len(executions) < self.min_tasks_for_analysis:
            return weak_points

        # Check success rate
        success_rate = sum(1 for e in executions if e.success) / len(executions)
        if success_rate < 0.7:
            weak_points.append(WeakPoint(
                agent_id=agent_id,
                area="success_rate",
                severity=1 - success_rate,
                description=f"Dusuk basari orani: {success_rate:.0%}",
                suggested_improvement="Hata pattern'lerini analiz et ve prompt'u iyilestir",
            ))

        # Check response time
        avg_response = sum(e.response_time_ms for e in executions) / len(executions)
        if avg_response > 5000:  # 5 seconds
            weak_points.append(WeakPoint(
                agent_id=agent_id,
                area="response_time",
                severity=min(1.0, avg_response / 10000),
                description=f"Yuksek yanit suresi: {avg_response:.0f}ms",
                suggested_improvement="Model degistir veya prompt'u kisalt",
            ))

        # Check error patterns by task type
        task_types = defaultdict(list)
        for e in executions:
            task_types[e.task_type].append(e)

        for task_type, type_executions in task_types.items():
            type_success = sum(1 for e in type_executions if e.success) / len(type_executions)
            if type_success < 0.5:
                weak_points.append(WeakPoint(
                    agent_id=agent_id,
                    area=f"task_type:{task_type}",
                    severity=1 - type_success,
                    description=f"'{task_type}' gorevlerinde dusuk basari: {type_success:.0%}",
                    suggested_improvement=f"'{task_type}' icin ozel yetenek ekle",
                ))

        # Check quality scores
        quality_scores = [e.quality_score for e in executions if e.quality_score > 0]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            if avg_quality < 0.6:
                weak_points.append(WeakPoint(
                    agent_id=agent_id,
                    area="quality",
                    severity=1 - avg_quality,
                    description=f"Dusuk kalite skoru: {avg_quality:.0%}",
                    suggested_improvement="Validation adimi ekle veya temperature dusur",
                ))

        return sorted(weak_points, key=lambda w: w.severity, reverse=True)

    async def suggest_improvements(self, agent_id: str) -> list[Improvement]:
        """
        Iyilestirme onerileri sun

        Args:
            agent_id: Agent ID

        Returns:
            Improvement listesi
        """
        weak_points = await self.identify_weak_points(agent_id)
        improvements = []

        for wp in weak_points:
            priority = 1 if wp.severity > 0.5 else 2 if wp.severity > 0.3 else 3

            if "success_rate" in wp.area:
                improvements.append(Improvement(
                    agent_id=agent_id,
                    improvement_type="prompt_optimization",
                    priority=priority,
                    description="System prompt'u iyilestir",
                    expected_impact=0.2,
                    implementation_hint="Hata yapilan gorevlerdeki ortak pattern'leri bul ve prompt'a ekle",
                ))

            elif "response_time" in wp.area:
                improvements.append(Improvement(
                    agent_id=agent_id,
                    improvement_type="model_change",
                    priority=priority,
                    description="Daha hizli model kullan",
                    expected_impact=0.3,
                    implementation_hint="Opus -> Sonnet veya Sonnet -> Haiku",
                ))

            elif "task_type:" in wp.area:
                task_type = wp.area.split(":")[1]
                improvements.append(Improvement(
                    agent_id=agent_id,
                    improvement_type="capability_add",
                    priority=priority,
                    description=f"'{task_type}' icin ozel yetenek ekle",
                    expected_impact=0.25,
                    implementation_hint=f"Capability(name='{task_type}_expert', proficiency=0.8)",
                ))

            elif "quality" in wp.area:
                improvements.append(Improvement(
                    agent_id=agent_id,
                    improvement_type="validation_add",
                    priority=priority,
                    description="Kalite kontrol adimi ekle",
                    expected_impact=0.15,
                    implementation_hint="Ciktiyi validator agent'a gonder",
                ))

        return sorted(improvements, key=lambda i: i.priority)

    async def get_comparative_report(self, agent_ids: list[str]) -> dict:
        """
        Birden fazla agent'i karsilastir

        Args:
            agent_ids: Agent ID listesi

        Returns:
            Karsilastirma raporu
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "agents": {},
            "rankings": {
                "success_rate": [],
                "response_time": [],
                "fitness": [],
            },
        }

        for agent_id in agent_ids:
            metrics = await self.get_metrics(agent_id)
            fitness = await self.calculate_fitness(agent_id)

            report["agents"][agent_id] = {
                "metrics": {
                    "total_tasks": metrics.total_tasks,
                    "success_rate": metrics.success_rate,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                },
                "fitness": fitness,
            }

            report["rankings"]["success_rate"].append((agent_id, metrics.success_rate))
            report["rankings"]["response_time"].append((agent_id, metrics.avg_response_time_ms))
            report["rankings"]["fitness"].append((agent_id, fitness))

        # Sort rankings
        report["rankings"]["success_rate"].sort(key=lambda x: x[1], reverse=True)
        report["rankings"]["response_time"].sort(key=lambda x: x[1])  # Lower is better
        report["rankings"]["fitness"].sort(key=lambda x: x[1], reverse=True)

        return report

    async def generate_report(self, agent_id: str) -> str:
        """
        Agent icin detayli rapor olustur

        Args:
            agent_id: Agent ID

        Returns:
            Markdown formatinda rapor
        """
        metrics = await self.get_metrics(agent_id)
        fitness = await self.calculate_fitness(agent_id)
        weak_points = await self.identify_weak_points(agent_id)
        improvements = await self.suggest_improvements(agent_id)

        report = f"""# Performance Report: {agent_id}

Generated: {datetime.now().isoformat()}

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | {metrics.total_tasks} |
| Success Rate | {metrics.success_rate:.1%} |
| Avg Response Time | {metrics.avg_response_time_ms:.0f}ms |
| Fitness Score | {fitness:.2f} |

## Weak Points

"""
        if weak_points:
            for wp in weak_points:
                report += f"### {wp.area}\n"
                report += f"- Severity: {wp.severity:.0%}\n"
                report += f"- Issue: {wp.description}\n"
                report += f"- Suggestion: {wp.suggested_improvement}\n\n"
        else:
            report += "No significant weak points identified.\n\n"

        report += "## Improvement Suggestions\n\n"

        if improvements:
            for imp in improvements:
                report += f"### [{imp.priority}] {imp.improvement_type}\n"
                report += f"- Description: {imp.description}\n"
                report += f"- Expected Impact: +{imp.expected_impact:.0%}\n"
                report += f"- How: {imp.implementation_hint}\n\n"
        else:
            report += "No improvements suggested at this time.\n"

        return report
