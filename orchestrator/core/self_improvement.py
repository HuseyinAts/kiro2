"""
KIRO2 Orchestrator - Self-Improvement Loop
==========================================
Sistem "ajan sayısını artırmadan" daha iyi hale gelir.

Ne üzerinden öğrenir?
- LangSmith metrikleri: success rate, time-to-green, cost-per-success
- Failure pattern'leri: hangi gate'te takılıyor
- Reviewer geri bildirimleri: must-fix türleri

Ne tür iyileştirme yapar?
1. Routing policy güncelleme
2. Prompt/plan şablon iyileştirme
3. Quality gate ayarı

SELF-REPLICATION YOK: Yeni ajan/servis üretmez.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from .state import RunState, TaskStatus, GateResult
from .memory import MemoryStore, Lesson, LessonEvidence, LessonType


class ImprovementType(str, Enum):
    """İyileştirme tipleri"""
    ROUTING_POLICY = "routing_policy"
    PROMPT_TEMPLATE = "prompt_template"
    QUALITY_GATE = "quality_gate"
    PARAMETER = "parameter"


@dataclass
class ImprovementAction:
    """İyileştirme aksiyonu"""
    improvement_type: ImprovementType
    target: str  # Neyi iyileştiriyoruz (routing:task_type, prompt:template_name, etc.)
    change_description: str
    evidence_run_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    applied_at: Optional[datetime] = None


@dataclass
class PerformanceMetrics:
    """Performans metrikleri (LangSmith'ten)"""
    task_type: str
    model: str
    
    # Temel metrikler
    total_runs: int = 0
    successful_runs: int = 0
    blocked_runs: int = 0
    
    # Kalite metrikleri
    avg_iterations_to_green: float = 0.0
    avg_cost: float = 0.0
    
    # Gate başarısızlık dağılımı
    gate_failure_counts: dict[str, int] = field(default_factory=dict)
    
    # Hesaplanan metrikler
    @property
    def success_rate(self) -> float:
        return (self.successful_runs / self.total_runs * 100) if self.total_runs > 0 else 0.0
    
    @property
    def block_rate(self) -> float:
        return (self.blocked_runs / self.total_runs * 100) if self.total_runs > 0 else 0.0


class MetricsCollector:
    """LangSmith'ten metrik toplama (simüle)"""
    
    def __init__(self, langsmith_client=None):
        self.client = langsmith_client
        self._cache: dict[str, PerformanceMetrics] = {}
    
    async def collect_metrics(
        self,
        task_type: str,
        model: str,
        time_window: timedelta = timedelta(days=7)
    ) -> PerformanceMetrics:
        """Son N günlük metrikleri topla"""
        # TODO: Gerçek LangSmith entegrasyonu
        # Şimdilik cache'ten döndür veya varsayılan
        cache_key = f"{task_type}:{model}"
        return self._cache.get(cache_key, PerformanceMetrics(task_type=task_type, model=model))
    
    def record_run_result(self, state: RunState) -> None:
        """Çalışma sonucunu kaydet"""
        cache_key = f"{state.selected_agent}:{state.selected_model}"
        
        if cache_key not in self._cache:
            self._cache[cache_key] = PerformanceMetrics(
                task_type=state.selected_agent or "unknown",
                model=state.selected_model or "unknown"
            )
        
        metrics = self._cache[cache_key]
        metrics.total_runs += 1
        
        if state.status == TaskStatus.COMPLETED:
            metrics.successful_runs += 1
        elif state.status == TaskStatus.BLOCKED:
            metrics.blocked_runs += 1
        
        # Gate başarısızlıklarını kaydet
        for gate_name, gate_state in state.quality_gates.items():
            if gate_state.status == GateResult.FAILED:
                metrics.gate_failure_counts[gate_name] = metrics.gate_failure_counts.get(gate_name, 0) + 1
        
        # Ortalama iterasyon güncelle
        if state.status == TaskStatus.COMPLETED:
            total_success = metrics.successful_runs
            current_avg = metrics.avg_iterations_to_green
            metrics.avg_iterations_to_green = (
                (current_avg * (total_success - 1) + state.current_iteration) / total_success
            )


class SelfImprovementEngine:
    """
    Self-improvement motoru.
    
    Prensipler:
    1. SADECE kanıtlanmış sonuçlardan öğren
    2. İyileştirme kararları ölçüme dayanır
    3. Self-replication YOK - mevcut policy/şablonları optimize et
    """
    
    # Hedef metrikler
    TARGET_SUCCESS_RATE = 90.0  # %90+
    TARGET_ITERATIONS = 3       # ≤3 iterasyon
    TARGET_COST = 0.50          # ≤$0.50
    
    # İyileştirme eşikleri
    MIN_SAMPLE_SIZE = 10  # En az 10 run gerekli
    IMPROVEMENT_THRESHOLD = 0.1  # %10+ iyileşme gerekli
    
    def __init__(self, memory_store: MemoryStore, metrics_collector: MetricsCollector):
        self.memory = memory_store
        self.metrics = metrics_collector
        self.pending_improvements: list[ImprovementAction] = []
    
    async def analyze_and_improve(self) -> list[ImprovementAction]:
        """
        Metrikleri analiz et ve iyileştirme öner.
        
        Returns:
            Önerilen iyileştirme aksiyonları
        """
        improvements = []
        
        # 1. Routing policy analizi
        routing_improvements = await self._analyze_routing_performance()
        improvements.extend(routing_improvements)
        
        # 2. Quality gate analizi
        gate_improvements = await self._analyze_gate_failures()
        improvements.extend(gate_improvements)
        
        # 3. Prompt template analizi (basit)
        # TODO: Prompt performance tracking
        
        self.pending_improvements = improvements
        return improvements
    
    async def _analyze_routing_performance(self) -> list[ImprovementAction]:
        """Routing performansını analiz et"""
        improvements = []
        
        # Her task type için metrikleri kontrol et
        task_types = [
            "turkish_nlp", "security", "refactor", "frontend",
            "backend", "test", "docs", "bugfix"
        ]
        
        for task_type in task_types:
            for model in ["claude-opus-4", "claude-sonnet-4", "codex-cli"]:
                metrics = await self.metrics.collect_metrics(task_type, model)
                
                if metrics.total_runs < self.MIN_SAMPLE_SIZE:
                    continue
                
                # Başarı oranı düşükse
                if metrics.success_rate < self.TARGET_SUCCESS_RATE:
                    # Alternatif model öner
                    improvements.append(ImprovementAction(
                        improvement_type=ImprovementType.ROUTING_POLICY,
                        target=f"routing:{task_type}",
                        change_description=f"{task_type} için {model} başarı oranı düşük "
                                          f"({metrics.success_rate:.1f}%). Alternatif model değerlendir.",
                        confidence=min(metrics.total_runs / 50, 1.0),  # Daha fazla sample = daha yüksek güven
                    ))
                
                # İterasyon sayısı yüksekse
                if metrics.avg_iterations_to_green > self.TARGET_ITERATIONS:
                    improvements.append(ImprovementAction(
                        improvement_type=ImprovementType.PROMPT_TEMPLATE,
                        target=f"prompt:{task_type}",
                        change_description=f"{task_type} için ortalama iterasyon yüksek "
                                          f"({metrics.avg_iterations_to_green:.1f}). Prompt iyileştir.",
                        confidence=min(metrics.total_runs / 50, 1.0),
                    ))
        
        return improvements
    
    async def _analyze_gate_failures(self) -> list[ImprovementAction]:
        """Gate başarısızlıklarını analiz et"""
        improvements = []
        
        # Tüm metrikleri topla
        all_gate_failures: dict[str, int] = {}
        total_runs = 0
        
        for metrics in self.metrics._cache.values():
            total_runs += metrics.total_runs
            for gate, count in metrics.gate_failure_counts.items():
                all_gate_failures[gate] = all_gate_failures.get(gate, 0) + count
        
        if total_runs < self.MIN_SAMPLE_SIZE:
            return improvements
        
        # En çok başarısız olan gate'i bul
        if all_gate_failures:
            worst_gate = max(all_gate_failures, key=all_gate_failures.get)
            failure_rate = all_gate_failures[worst_gate] / total_runs * 100
            
            if failure_rate > 20:  # %20+ başarısızlık
                improvements.append(ImprovementAction(
                    improvement_type=ImprovementType.QUALITY_GATE,
                    target=f"gate:{worst_gate}",
                    change_description=f"{worst_gate} gate'i en çok başarısız oluyor "
                                      f"({failure_rate:.1f}%). Strateji gözden geçir.",
                    confidence=min(total_runs / 100, 1.0),
                ))
        
        return improvements
    
    async def apply_improvement(self, action: ImprovementAction) -> bool:
        """
        İyileştirmeyi uygula.
        
        SADECE policy/parametre değişikliği yapar.
        Yeni ajan/servis OLUŞTURMAZ.
        """
        if action.improvement_type == ImprovementType.ROUTING_POLICY:
            return await self._apply_routing_improvement(action)
        elif action.improvement_type == ImprovementType.PARAMETER:
            return await self._apply_parameter_improvement(action)
        elif action.improvement_type == ImprovementType.QUALITY_GATE:
            return await self._apply_gate_improvement(action)
        elif action.improvement_type == ImprovementType.PROMPT_TEMPLATE:
            # TODO: Prompt template değişikliği
            return False
        
        return False
    
    async def _apply_routing_improvement(self, action: ImprovementAction) -> bool:
        """Routing policy iyileştirmesi uygula"""
        # Parse target: "routing:task_type"
        parts = action.target.split(":")
        if len(parts) != 2:
            return False
        
        task_type = parts[1]
        
        # Memory'ye kaydet (advisory)
        lesson = Lesson(
            id=f"routing_improvement_{task_type}_{datetime.utcnow().timestamp()}",
            lesson_type=LessonType.ROUTING_PREFERENCE,
            category=task_type,
            description=action.change_description,
            suggested_action="Consider alternative model for this task type",
        )
        
        # Evidence olmadan memory'ye yazmıyoruz (proof required)
        # Bu sadece "pending improvement" olarak kalır
        
        action.applied_at = datetime.utcnow()
        return True
    
    async def _apply_parameter_improvement(self, action: ImprovementAction) -> bool:
        """Parametre iyileştirmesi uygula"""
        # TODO: Parametre değişikliği logic
        action.applied_at = datetime.utcnow()
        return True
    
    async def _apply_gate_improvement(self, action: ImprovementAction) -> bool:
        """Quality gate iyileştirmesi uygula"""
        # TODO: Gate configuration değişikliği
        action.applied_at = datetime.utcnow()
        return True
    
    def record_success(self, state: RunState) -> None:
        """
        Başarılı run'ı kaydet ve öğren.
        
        SADECE tüm gate'ler geçtiyse Memory'ye yaz.
        """
        if state.status != TaskStatus.COMPLETED:
            return
        
        if not state.all_gates_passed():
            return
        
        # Metrikleri kaydet
        self.metrics.record_run_result(state)
        
        # Lesson oluştur ve Memory'ye yaz (kanıtlı)
        if state.lesson_learned:
            # TODO: Memory'ye kaydet
            state.lesson_written_to_memory = True


# Singleton
_improvement_engine: Optional[SelfImprovementEngine] = None


def get_improvement_engine(memory_store: MemoryStore = None) -> SelfImprovementEngine:
    """Self-improvement engine singleton'ını al"""
    global _improvement_engine
    if _improvement_engine is None:
        if memory_store is None:
            raise ValueError("memory_store required for first initialization")
        _improvement_engine = SelfImprovementEngine(
            memory_store=memory_store,
            metrics_collector=MetricsCollector()
        )
    return _improvement_engine
