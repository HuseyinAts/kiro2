"""Cognitive Profiler - SOLO ve Marzano bazlı bilişsel profil.

Öğrenci yanıtlarını taksonomi seviyeleriyle analiz ederek bilişsel profil oluşturur:
- Ders bazlı SOLO/Marzano performans takibi
- Bilişsel tavan ve taban tespiti (ceiling/floor)
- Güçlü ve zayıf yönler (Türkçe açıklamalar)
- Üstbilişsel ve öz-sistem skorları (davranış bazlı)
- Sonraki soru için taksonomi düzeyi önerisi
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .taxonomy_classifier import (
    MARZANO_COGNITIVE_NAMES,
    MARZANO_SYSTEM_NAMES,
    SOLO_LEVEL_NAMES,
    MARZANO_SUBJECTS,
    SOLO_SUBJECTS,
    TaxonomyType,
)


@dataclass
class TaggedResponse:
    """Taksonomi etiketli öğrenci yanıtı."""

    question_id: str
    subject: str
    topic: str = ""
    is_correct: bool = False
    difficulty: float = 0.0

    # Taksonomi etiketleri (TaxonomyClassifier'dan gelir)
    solo_level: int = 0                  # 1-5, 0 = etiketlenmemiş
    marzano_system: int = 0              # 1-3, 0 = etiketlenmemiş
    marzano_cognitive_level: int = 0     # 1-4, 0 = etiketlenmemiş

    # Davranış verileri (metacognitive/self-system için)
    time_spent_seconds: float = 0.0
    skipped: bool = False


@dataclass
class TaxonomyPerformance:
    """Bir taksonomi seviyesindeki performans."""

    level: int
    level_name: str
    total_questions: int = 0
    correct_count: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return self.correct_count / self.total_questions

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "level_name": self.level_name,
            "total_questions": self.total_questions,
            "correct_count": self.correct_count,
            "success_rate": round(self.success_rate, 3),
        }


@dataclass
class SubjectCognitiveProfile:
    """Bir dersteki bilişsel profil."""

    subject: str
    primary_taxonomy: TaxonomyType = TaxonomyType.SOLO

    # SOLO seviye performansları (key: level 1-5)
    solo_performance: dict[int, TaxonomyPerformance] = field(default_factory=dict)
    # Marzano bilişsel seviye performansları (key: cognitive_level 1-4)
    marzano_performance: dict[int, TaxonomyPerformance] = field(default_factory=dict)

    # Tavan ve taban
    cognitive_ceiling: int = 0           # En yüksek başarılı seviye
    cognitive_floor: int = 0             # En düşük başarısız seviye
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        perf_key = "solo" if self.primary_taxonomy == TaxonomyType.SOLO else "marzano"
        perf_data = (
            self.solo_performance
            if self.primary_taxonomy == TaxonomyType.SOLO
            else self.marzano_performance
        )
        return {
            "subject": self.subject,
            "primary_taxonomy": self.primary_taxonomy.value,
            perf_key: {k: v.to_dict() for k, v in perf_data.items()},
            "cognitive_ceiling": self.cognitive_ceiling,
            "cognitive_floor": self.cognitive_floor,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class CognitiveProfile:
    """Tüm derslerdeki bilişsel profil."""

    student_id: str
    subject_profiles: dict[str, SubjectCognitiveProfile] = field(default_factory=dict)

    # Çapraz-ders özet
    metacognitive_score: float = 0.0     # 0-1 (davranış bazlı)
    self_system_score: float = 0.0       # 0-1 (davranış bazlı)
    recommendations: list[str] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "subject_profiles": {k: v.to_dict() for k, v in self.subject_profiles.items()},
            "metacognitive_score": round(self.metacognitive_score, 3),
            "self_system_score": round(self.self_system_score, 3),
            "recommendations": self.recommendations,
        }


@dataclass
class CognitiveProfilerConfig:
    """Profiler konfigürasyonu."""

    min_questions_per_level: int = 3     # Seviye değerlendirmesi için minimum soru
    ceiling_threshold: float = 0.6       # Bu üstü = başarılı
    floor_threshold: float = 0.4         # Bu altı = zorlanıyor
    max_recommendations: int = 5

    # Davranış bazlı eşikler
    fast_response_ratio: float = 0.5     # Beklenen sürenin bu altı = hızlı
    skip_rate_threshold: float = 0.15    # Bu üstü = düşük motivasyon


@dataclass
class CognitiveProfiler:
    """SOLO ve Marzano bazlı bilişsel profil motoru.

    Öğrenci yanıtlarını taksonomi seviyeleriyle analiz eder,
    bilişsel tavan/taban tespit eder ve Türkçe öneriler üretir.

    Example:
        >>> profiler = CognitiveProfiler()
        >>> responses = [TaggedResponse(question_id="Q1", subject="Türkçe",
        ...     is_correct=True, solo_level=4), ...]
        >>> profile = profiler.process("S001", responses)
        >>> print(profile.subject_profiles["Türkçe"].cognitive_ceiling)
    """

    config: CognitiveProfilerConfig = field(default_factory=CognitiveProfilerConfig)

    def process(
        self, student_id: str, responses: list[TaggedResponse],
    ) -> CognitiveProfile:
        """Yanıtlardan bilişsel profil oluştur.

        Args:
            student_id: Öğrenci ID.
            responses: Taksonomi etiketli yanıtlar.

        Returns:
            CognitiveProfile.
        """
        profile = CognitiveProfile(student_id=student_id)

        if not responses:
            return profile

        # 1. Ders bazlı grupla
        by_subject: dict[str, list[TaggedResponse]] = {}
        for r in responses:
            by_subject.setdefault(r.subject, []).append(r)

        # 2. Her ders için profil oluştur
        for subject, subject_responses in by_subject.items():
            sp = self._build_subject_profile(subject, subject_responses)
            self._compute_ceiling_floor(sp)
            self._identify_strengths_weaknesses(sp)
            profile.subject_profiles[subject] = sp

        # 3. Davranış bazlı skorlar
        self._compute_behavioral_scores(profile, responses)

        # 4. Öneriler
        self._generate_recommendations(profile)

        profile.last_updated = datetime.now(timezone.utc).isoformat()
        return profile

    def get_next_question_params(
        self, profile: CognitiveProfile, subject: str,
    ) -> dict[str, Any]:
        """Sonraki soru için önerilen taksonomi parametreleri.

        Öğrencinin ZPD'sine yakın seviyede soru önerir.

        Args:
            profile: Bilişsel profil.
            subject: Ders.

        Returns:
            {"solo_level": int, "marzano_cognitive_level": int, "primary": str}
        """
        sp = profile.subject_profiles.get(subject)
        if not sp:
            return {"solo_level": 2, "marzano_cognitive_level": 2, "primary": "solo"}

        # Tavan varsa tavan seviyesinde, yoksa ortada hedefle
        ceiling = sp.cognitive_ceiling
        if ceiling > 0:
            target = min(ceiling + 1, 5)  # Tavan + 1 (ZPD)
        else:
            target = 2  # Başlangıç

        if sp.primary_taxonomy == TaxonomyType.SOLO:
            return {"solo_level": target, "marzano_cognitive_level": 0, "primary": "solo"}
        return {"solo_level": 0, "marzano_cognitive_level": min(target, 4), "primary": "marzano"}

    def _build_subject_profile(
        self, subject: str, responses: list[TaggedResponse],
    ) -> SubjectCognitiveProfile:
        """Bir ders için taksonomi performansını hesapla."""
        primary = TaxonomyType.SOLO if subject in SOLO_SUBJECTS else TaxonomyType.MARZANO
        if subject not in SOLO_SUBJECTS and subject not in MARZANO_SUBJECTS:
            # Fallback
            primary = TaxonomyType.SOLO

        sp = SubjectCognitiveProfile(subject=subject, primary_taxonomy=primary)

        for r in responses:
            # SOLO performans
            if r.solo_level > 0:
                if r.solo_level not in sp.solo_performance:
                    sp.solo_performance[r.solo_level] = TaxonomyPerformance(
                        level=r.solo_level,
                        level_name=SOLO_LEVEL_NAMES.get(r.solo_level, ""),
                    )
                perf = sp.solo_performance[r.solo_level]
                perf.total_questions += 1
                if r.is_correct:
                    perf.correct_count += 1

            # Marzano bilişsel performans
            if r.marzano_cognitive_level > 0:
                lvl = r.marzano_cognitive_level
                if lvl not in sp.marzano_performance:
                    sp.marzano_performance[lvl] = TaxonomyPerformance(
                        level=lvl,
                        level_name=MARZANO_COGNITIVE_NAMES.get(lvl, ""),
                    )
                perf = sp.marzano_performance[lvl]
                perf.total_questions += 1
                if r.is_correct:
                    perf.correct_count += 1

        return sp

    def _compute_ceiling_floor(self, sp: SubjectCognitiveProfile) -> None:
        """Bilişsel tavan ve tabanı hesapla."""
        performance = (
            sp.solo_performance
            if sp.primary_taxonomy == TaxonomyType.SOLO
            else sp.marzano_performance
        )

        ceiling = 0
        floor = 0

        for level in sorted(performance.keys()):
            perf = performance[level]
            if perf.total_questions < self.config.min_questions_per_level:
                continue
            if perf.success_rate >= self.config.ceiling_threshold:
                ceiling = max(ceiling, level)
            if perf.success_rate < self.config.floor_threshold and floor == 0:
                floor = level

        sp.cognitive_ceiling = ceiling
        sp.cognitive_floor = floor

    def _identify_strengths_weaknesses(self, sp: SubjectCognitiveProfile) -> None:
        """Güçlü ve zayıf yönleri tespit et."""
        performance = (
            sp.solo_performance
            if sp.primary_taxonomy == TaxonomyType.SOLO
            else sp.marzano_performance
        )
        names = (
            SOLO_LEVEL_NAMES
            if sp.primary_taxonomy == TaxonomyType.SOLO
            else MARZANO_COGNITIVE_NAMES
        )

        sp.strengths = []
        sp.weaknesses = []

        for level in sorted(performance.keys()):
            perf = performance[level]
            if perf.total_questions < self.config.min_questions_per_level:
                continue
            name = names.get(level, f"Seviye {level}")
            if perf.success_rate >= 0.7:
                sp.strengths.append(f"{name} ({perf.success_rate:.0%})")
            elif perf.success_rate < self.config.floor_threshold:
                sp.weaknesses.append(f"{name} ({perf.success_rate:.0%})")

    def _compute_behavioral_scores(
        self, profile: CognitiveProfile, responses: list[TaggedResponse],
    ) -> None:
        """Davranış bazlı üstbilişsel ve öz-sistem skorlarını hesapla."""
        if not responses:
            return

        total = len(responses)
        skipped = sum(1 for r in responses if r.skipped)
        timed = [r for r in responses if r.time_spent_seconds > 0]

        # Öz-sistem: boş bırakma oranı düşük = yüksek skor
        skip_rate = skipped / total
        if skip_rate <= self.config.skip_rate_threshold:
            profile.self_system_score = min(1.0, 1.0 - skip_rate * 3)
        else:
            profile.self_system_score = max(0.0, 0.5 - skip_rate)

        # Üstbilişsel: tutarlı cevaplama hızı = yüksek skor
        if len(timed) >= 5:
            times = [r.time_spent_seconds for r in timed]
            avg = sum(times) / len(times)
            if avg > 0:
                variance = sum((t - avg) ** 2 for t in times) / len(times)
                cv = (variance ** 0.5) / avg  # Coefficient of variation
                # Düşük CV = tutarlı = yüksek üstbiliş
                profile.metacognitive_score = max(0.0, min(1.0, 1.0 - cv))
            else:
                profile.metacognitive_score = 0.5
        else:
            profile.metacognitive_score = 0.5  # Yetersiz veri

    def _generate_recommendations(self, profile: CognitiveProfile) -> None:
        """Türkçe bilişsel gelişim önerileri üret."""
        profile.recommendations = []

        for subject, sp in profile.subject_profiles.items():
            # Zayıf yönler için öneriler
            for weakness in sp.weaknesses[:2]:
                taxonomy_name = "SOLO" if sp.primary_taxonomy == TaxonomyType.SOLO else "Marzano"
                profile.recommendations.append(
                    f"{subject}: {weakness} seviyesinde pratik yapın ({taxonomy_name})"
                )

            # Tavan geliştirme
            if sp.cognitive_ceiling > 0:
                max_level = 5 if sp.primary_taxonomy == TaxonomyType.SOLO else 4
                if sp.cognitive_ceiling < max_level:
                    names = (
                        SOLO_LEVEL_NAMES
                        if sp.primary_taxonomy == TaxonomyType.SOLO
                        else MARZANO_COGNITIVE_NAMES
                    )
                    next_name = names.get(sp.cognitive_ceiling + 1, "")
                    if next_name:
                        profile.recommendations.append(
                            f"{subject}: '{next_name}' düzeyine geçiş için çalışın"
                        )

        # Davranış bazlı öneriler
        if profile.metacognitive_score < 0.4:
            profile.recommendations.append(
                "Üstbilişsel strateji: Problem çözmeden önce plan yapma alışkanlığı geliştirin"
            )
        if profile.self_system_score < 0.4:
            profile.recommendations.append(
                "Motivasyon: Zor soruları boş bırakmak yerine eleme yöntemiyle deneyin"
            )

        profile.recommendations = profile.recommendations[: self.config.max_recommendations]
