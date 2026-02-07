"""Retrieval Practice Engine - Bjork's Generation Effect + Interleaving.

Bilimsel temel:
- Generation Effect: Bilgiyi hatırlamaya çalışmak, okumaktan daha etkili
- Interleaving: Farklı konuları karıştırarak çalışma
- Testing Effect: Sınav yapmanın kendisi öğrenmeyi güçlendirir
- Successive Relearning: Tekrarlı geri çağırma seansları

Entegrasyonlar:
- FSRS parametreleri ile senkronize (stability, difficulty)
- IRT parametreleri ile zorluk kontrolü
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RetrievalType(str, Enum):
    """Geri çağırma tipi - en zor→en kolay."""

    FREE_RECALL = "free_recall"  # Serbest hatırlama (en zor)
    CUED_RECALL = "cued_recall"  # İpuçlu hatırlama
    RECOGNITION = "recognition"  # Tanıma (çoktan seçmeli)
    REREADING = "rereading"  # Yeniden okuma (en kolay, en az etkili)


class InterleavingStrategy(str, Enum):
    """Konu karıştırma stratejisi."""

    BLOCKED = "blocked"  # Aynı konudan art arda (kolay ama az etkili)
    INTERLEAVED = "interleaved"  # Karışık konular (zor ama çok etkili)
    HYBRID = "hybrid"  # %30 blocked + %70 interleaved


@dataclass
class RetrievalItem:
    """Geri çağırma pratiği için tek item."""

    question_id: str
    topic: str
    subject: str
    difficulty: float  # IRT difficulty (-4 to 4)
    retrieval_type: RetrievalType
    fsrs_stability: float = 1.0
    fsrs_difficulty: float = 5.0
    last_reviewed: Optional[datetime] = None
    success_count: int = 0
    fail_count: int = 0


@dataclass
class RetrievalPlan:
    """Geri çağırma pratik planı."""

    student_id: str
    subject: str
    topics: list[str]
    items: list[RetrievalItem] = field(default_factory=list)
    interleaving_strategy: InterleavingStrategy = InterleavingStrategy.HYBRID
    interleaving_ratio: float = 0.7  # 0=blocked, 1=full interleaved
    session_size: int = 20  # Seans başına soru sayısı
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalSession:
    """Aktif geri çağırma seansı."""

    plan_id: str
    student_id: str
    items: list[RetrievalItem]
    current_index: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed: bool = False


@dataclass
class RetrievalMetrics:
    """Seans performans metrikleri."""

    total_items: int
    correct: int
    incorrect: int
    retrieval_success_rate: float  # 0-1
    avg_difficulty: float
    interleaving_ratio_used: float
    estimated_retention_boost: float  # Tahmini hatırlama artışı
    fsrs_updates: dict = field(default_factory=dict)  # question_id → new_stability


def calculate_retrieval_probability(
    stability: float,
    days_since_review: float,
    difficulty: float = 5.0,
) -> float:
    """FSRS tabanlı geri çağırma olasılığı.

    R(t) = exp(-t / S) where S = stability, t = elapsed days

    Args:
        stability: FSRS stability parameter (days)
        days_since_review: Gözden geçirmeden sonra geçen gün
        difficulty: FSRS difficulty (1-10, optional)

    Returns:
        Geri çağırma olasılığı (0-1)
    """
    if stability <= 0:
        return 0.0
    prob = math.exp(-days_since_review / stability)
    return max(0.0, min(1.0, prob))


def calculate_optimal_retrieval_time(
    stability: float,
    target_retention: float = 0.85,
) -> float:
    """Optimal geri çağırma zamanını hesapla (gün).

    t_opt = -S * ln(R_target)
    Desirable difficulty: Çok kolay değil, çok zor değil

    Args:
        stability: FSRS stability (days)
        target_retention: Hedef hatırlama oranı (0-1)

    Returns:
        Optimal gözden geçirme zamanı (gün)
    """
    if stability <= 0 or target_retention <= 0 or target_retention >= 1:
        return 1.0
    return -stability * math.log(target_retention)


def recommend_interleaving_ratio(
    student_ability: float,
    topic_count: int,
    avg_mastery: float = 0.5,
) -> float:
    """Öğrenci seviyesine göre interleaving oranı.

    Yeni öğrenciler: Daha az karıştırma (blocked tercih)
    İleri öğrenciler: Daha çok karıştırma (interleaved tercih)

    Args:
        student_ability: IRT ability estimate (-4 to 4)
        topic_count: Çalışılacak konu sayısı
        avg_mastery: Ortalama mastery seviyesi (0-1)

    Returns:
        Interleaving ratio (0-1)
    """
    # Base ratio from ability (-4 to 4 → 0.3 to 0.9)
    base_ratio = 0.3 + 0.075 * (student_ability + 4)
    base_ratio = max(0.2, min(0.95, base_ratio))

    # Mastery adjustment: higher mastery → more interleaving
    mastery_bonus = (avg_mastery - 0.5) * 0.2

    # Topic count adjustment: more topics → more interleaving benefit
    topic_bonus = min(0.1, topic_count * 0.02)

    ratio = base_ratio + mastery_bonus + topic_bonus
    return max(0.2, min(0.95, round(ratio, 2)))


def generate_retrieval_schedule(
    student_id: str,
    subject: str,
    topics: list[str],
    available_questions: list[dict],
    student_ability: float = 0.0,
    session_size: int = 20,
) -> RetrievalPlan:
    """Geri çağırma pratik planı oluştur.

    Args:
        student_id: Öğrenci ID
        subject: Ders (matematik, fizik, vb.)
        topics: Çalışılacak konular
        available_questions: Mevcut sorular [{id, topic, difficulty, fsrs_stability, ...}]
        student_ability: IRT ability estimate
        session_size: Seans başına soru sayısı

    Returns:
        RetrievalPlan instance
    """
    interleaving_ratio = recommend_interleaving_ratio(student_ability, len(topics))

    strategy = InterleavingStrategy.HYBRID
    if interleaving_ratio < 0.3:
        strategy = InterleavingStrategy.BLOCKED
    elif interleaving_ratio > 0.8:
        strategy = InterleavingStrategy.INTERLEAVED

    # Select questions with spacing consideration
    items = []
    pool_size = min(len(available_questions), session_size * 2)
    for q in available_questions[:pool_size]:  # Pool larger than needed
        stability = q.get("fsrs_stability", 1.0)
        difficulty = q.get("difficulty", 0.0)

        # Determine retrieval type based on stability
        if stability > 10:
            rtype = RetrievalType.FREE_RECALL  # Well-known: challenge more
        elif stability > 3:
            rtype = RetrievalType.CUED_RECALL
        else:
            rtype = RetrievalType.RECOGNITION  # New: easier retrieval

        items.append(
            RetrievalItem(
                question_id=q.get("id", ""),
                topic=q.get("topic", ""),
                subject=subject,
                difficulty=difficulty,
                retrieval_type=rtype,
                fsrs_stability=stability,
                fsrs_difficulty=q.get("fsrs_difficulty", 5.0),
            )
        )

    # Apply interleaving
    if strategy == InterleavingStrategy.INTERLEAVED:
        random.shuffle(items)
    elif strategy == InterleavingStrategy.HYBRID:
        # Alternate: some blocked, some interleaved
        blocked_count = int(len(items) * (1 - interleaving_ratio))
        blocked = items[:blocked_count]
        interleaved = items[blocked_count:]
        random.shuffle(interleaved)
        items = blocked + interleaved

    # Trim to session size
    items = items[:session_size]

    return RetrievalPlan(
        student_id=student_id,
        subject=subject,
        topics=topics,
        items=items,
        interleaving_strategy=strategy,
        interleaving_ratio=interleaving_ratio,
        session_size=session_size,
    )


def create_retrieval_session(
    plan: RetrievalPlan,
) -> RetrievalSession:
    """Aktif geri çağırma seansı başlat.

    Args:
        plan: RetrievalPlan instance

    Returns:
        RetrievalSession instance
    """
    return RetrievalSession(
        plan_id=f"plan_{plan.student_id}_{plan.created_at.isoformat()[:10]}",
        student_id=plan.student_id,
        items=plan.items,
    )


def evaluate_retrieval_performance(
    session: RetrievalSession,
    responses: list[dict],
) -> RetrievalMetrics:
    """Seans performansını değerlendir.

    Args:
        session: Tamamlanmış seans
        responses: [{question_id, correct: bool, response_time_ms}]

    Returns:
        RetrievalMetrics instance
    """
    if not responses:
        return RetrievalMetrics(
            total_items=0,
            correct=0,
            incorrect=0,
            retrieval_success_rate=0.0,
            avg_difficulty=0.0,
            interleaving_ratio_used=0.0,
            estimated_retention_boost=0.0,
        )

    correct = sum(1 for r in responses if r.get("correct", False))
    incorrect = len(responses) - correct

    # Calculate average difficulty from session items
    diff_map = {item.question_id: item.difficulty for item in session.items}
    difficulties = [diff_map.get(r.get("question_id", ""), 0.0) for r in responses]
    avg_diff = sum(difficulties) / len(difficulties) if difficulties else 0.0

    # Estimate retention boost from retrieval practice
    # Testing effect: ~10-30% retention improvement over re-reading
    success_rate = correct / len(responses) if responses else 0.0

    # Optimal difficulty zone (not too easy, not too hard)
    difficulty_bonus = 1.0 - abs(success_rate - 0.7) * 2  # Peak at 70% success
    difficulty_bonus = max(0.0, difficulty_bonus)

    # Base retention boost: 15% average from testing effect literature
    base_boost = 0.15
    estimated_boost = base_boost * (0.5 + 0.5 * difficulty_bonus)

    # FSRS stability updates
    fsrs_updates = {}
    for r in responses:
        qid = r.get("question_id", "")
        if qid in diff_map:
            item = next((i for i in session.items if i.question_id == qid), None)
            if item:
                old_stability = item.fsrs_stability
                if r.get("correct"):
                    # Successful retrieval → increase stability
                    new_stability = old_stability * (1.0 + 0.1 * (1.0 + item.difficulty))
                else:
                    # Failed retrieval → decrease stability
                    new_stability = old_stability * 0.5
                fsrs_updates[qid] = round(max(0.1, new_stability), 3)

    return RetrievalMetrics(
        total_items=len(responses),
        correct=correct,
        incorrect=incorrect,
        retrieval_success_rate=round(success_rate, 3),
        avg_difficulty=round(avg_diff, 3),
        interleaving_ratio_used=0.7,  # Default hybrid
        estimated_retention_boost=round(estimated_boost, 3),
        fsrs_updates=fsrs_updates,
    )
