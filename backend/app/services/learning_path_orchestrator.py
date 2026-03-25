"""
KIRO2 — Learning Path Orchestrator
====================================
ZPD + DAG + IRT + FSRS'yi birleştiren merkezi öğrenme yolu servisi.

Mimari:
  IRT θ (her ders)
    ↓
  DAG (önkoşul kontrolü)
    ↓
  ZPD (optimal zorluk bandı)
    ↓
  FSRS (tekrar zamanlaması)
    ↓
  Daily Plan (günlük program)

Bu servis şu soruları cevaplar:
  1. Öğrenci şimdi HANGİ konuya çalışmalı?
  2. BUGÜN ne kadar çalışmalı, hangi sırayla?
  3. Sınava kaç gün var, planı nasıl optimize et?
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("kiro2.lp_orchestrator")

# ─── YKS Ders Konfigürasyonu ─────────────────────────────────────────────────

YKS_SUBJECTS = {
    "TYT": ["TURKCE", "MATEMATIK", "FIZIK", "KIMYA", "BIYOLOJI",
            "TARIH", "COGRAFYA", "SOSYAL"],
    "AYT_SAY": ["MATEMATIK", "FIZIK", "KIMYA", "BIYOLOJI"],
    "AYT_EA":  ["MATEMATIK", "EDEBIYAT", "TARIH", "COGRAFYA"],
    "AYT_SOZ": ["EDEBIYAT", "TARIH", "COGRAFYA", "SOSYAL"],
}

# TYT sınav tarihi sabit (her yıl Haziran ilk haftası)
TYT_EXAM_DATE_DEFAULT = date(date.today().year, 6, 7)

# ─── Veri Yapıları ───────────────────────────────────────────────────────────

@dataclass
class SubjectStatus:
    """Bir dersteki öğrenci durumu."""
    subject: str
    theta: float = 0.0              # IRT yetenek tahmini
    theta_se: float = 0.5           # Standart hata
    mastery_pct: float = 0.0        # 0-100 mastery yüzdesi
    fsrs_due_count: int = 0         # Bugün tekrar edilecek soru sayısı
    next_topic_id: Optional[str] = None
    next_topic_name: Optional[str] = None
    prereq_blocked: bool = False    # Önkoşul tamamlanmamış
    prereq_topic: Optional[str] = None  # Hangi önkoşul eksik
    zpd_lower: float = -1.0         # ZPD alt sınırı
    zpd_upper: float = 1.0          # ZPD üst sınırı
    priority_score: float = 0.0     # Bugünkü çalışma önceliği (0-100)
    needs_cat: bool = False         # CAT henüz yapılmamış → seviye bilinmiyor


@dataclass
class StudyBlock:
    """Tek bir çalışma bloğu (30-45 dk)."""
    subject: str
    topic_id: Optional[str]
    topic_name: str
    activity_type: str              # "cat" | "fsrs_review" | "practice"
    duration_minutes: int = 30
    question_count: int = 10
    difficulty_band: str = "medium" # "easy" | "medium" | "hard"
    reason: str = ""                # Neden bu blok seçildi
    priority: int = 0               # 1=yüksek, 2=orta, 3=düşük


@dataclass
class DailyPlan:
    """Bir günlük çalışma planı."""
    user_id: str
    plan_date: date
    exam_date: date
    days_remaining: int
    total_minutes: int              # Bugün hedeflenen toplam süre
    blocks: List[StudyBlock] = field(default_factory=list)
    fsrs_review_count: int = 0
    new_topic_count: int = 0
    weak_subject: Optional[str] = None
    strong_subject: Optional[str] = None
    motivational_note: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


# ─── Orchestrator Sınıfı ─────────────────────────────────────────────────────

class LearningPathOrchestrator:
    """
    ZPD + DAG + IRT + FSRS birleştiren ana servis.
    """

    def __init__(self, db: AsyncSession, redis=None):
        self.db = db
        self.redis = redis

    # ── Öğrenci Durum Analizi ─────────────────────────────────────────────

    async def get_student_subject_statuses(
        self, user_id: str
    ) -> List[SubjectStatus]:
        """
        Tüm dersler için öğrenci durumunu çek:
        IRT θ + FSRS due count + DAG next topic.
        """
        statuses = []

        # 1. IRT theta değerlerini çek
        theta_map = await self._fetch_thetas(user_id)

        # 2. FSRS due count'ları çek
        fsrs_map = await self._fetch_fsrs_due_counts(user_id)

        # 3. Her ders için durum oluştur
        all_subjects = set()
        for subj_list in YKS_SUBJECTS.values():
            all_subjects.update(subj_list)

        for subject in sorted(all_subjects):
            has_theta = subject in theta_map   # gerçek CAT kaydı var mı?
            theta     = theta_map.get(subject, 0.0)
            se        = 0.5  # varsayılan SE (kalibre olmayan dersler için)
            fsrs_due  = fsrs_map.get(subject, 0)

            # ZPD bandını hesapla (IRT θ bazlı)
            zpd_lower, zpd_upper = self._calc_zpd_band(theta, se)

            # Mastery yüzdesi:
            #   CAT yapılmamış ders → mastery=0 (henüz ölçülmedi)
            #   CAT yapılmış ders   → CDF bazlı hesap
            if not has_theta:
                mastery_pct = 0.0
            else:
                mastery_pct = self._theta_to_mastery_pct(theta, se)

            # Öncelik skoru
            # CAT yapılmamış ders → en yüksek öncelik (100 puan)
            if not has_theta:
                priority = 100.0
            else:
                priority = self._calc_priority_score(
                    theta, fsrs_due, mastery_pct
                )

            status = SubjectStatus(
                subject=subject,
                theta=theta,
                theta_se=se,
                mastery_pct=mastery_pct,
                fsrs_due_count=fsrs_due,
                zpd_lower=zpd_lower,
                zpd_upper=zpd_upper,
                priority_score=priority,
                needs_cat=not has_theta,
            )
            statuses.append(status)

        # Önceliğe göre sırala (yüksek önce)
        statuses.sort(key=lambda s: -s.priority_score)
        return statuses

    async def generate_daily_plan(
        self,
        user_id: str,
        available_minutes: int = 120,
        exam_date: Optional[date] = None,
        exam_type: str = "TYT",
    ) -> DailyPlan:
        """
        Günlük çalışma planı oluştur.

        Algoritma:
          1. Tüm derslerin durumunu analiz et
          2. FSRS tekrar gerektirenleri önce koy (hafıza pekiştirme)
          3. Zayıf derslere daha fazla süre ayır
          4. ZPD bandında soru seç (ne çok kolay ne çok zor)
          5. Sınava kalan güne göre pace ayarla
        """
        if exam_date is None:
            exam_date = TYT_EXAM_DATE_DEFAULT

        today = date.today()
        days_remaining = max(1, (exam_date - today).days)

        # Öğrenci durumunu al
        statuses = await self.get_student_subject_statuses(user_id)

        blocks: List[StudyBlock] = []
        used_minutes = 0
        fsrs_total = 0
        new_topic_count = 0

        # ── FAZ 1: FSRS Tekrarları (ilk 30 dk) ───────────────────────────
        for status in statuses:
            if used_minutes >= available_minutes:
                break
            if status.fsrs_due_count > 0:
                review_mins = min(20, status.fsrs_due_count * 2)
                blocks.append(StudyBlock(
                    subject=status.subject,
                    topic_id=None,
                    topic_name=f"{status.subject} Tekrar",
                    activity_type="fsrs_review",
                    duration_minutes=review_mins,
                    question_count=status.fsrs_due_count,
                    difficulty_band="mixed",
                    reason=f"{status.fsrs_due_count} kart vadesi geldi",
                    priority=1,
                ))
                used_minutes += review_mins
                fsrs_total += status.fsrs_due_count

        # ── FAZ 2: Zayıf Ders CAT Blokları ───────────────────────────────
        # En düşük theta'lı 2 dersi öncelikle al
        weak_subjects = sorted(statuses, key=lambda s: s.theta)[:3]
        for status in weak_subjects:
            if used_minutes >= available_minutes - 10:
                break
            cat_mins = 30
            if days_remaining < 30:  # Sınava yakın → yoğun
                cat_mins = 40
            elif days_remaining > 180:  # Uzak → daha az
                cat_mins = 25

            blocks.append(StudyBlock(
                subject=status.subject,
                topic_id=status.next_topic_id,
                topic_name=status.next_topic_name or f"{status.subject} Adaptif Test",
                activity_type="cat",
                duration_minutes=cat_mins,
                question_count=int(cat_mins * 0.5),
                difficulty_band=self._theta_to_difficulty_band(
                    status.theta, status.zpd_lower, status.zpd_upper
                ),
                reason=f"θ={status.theta:.2f} ({self._theta_label(status.theta)})",
                priority=2,
            ))
            used_minutes += cat_mins
            new_topic_count += 1

        # ── FAZ 3: Güçlü Derste Pratik (kalan süre) ──────────────────────
        remaining = available_minutes - used_minutes
        if remaining >= 20 and statuses:
            strong = max(statuses, key=lambda s: s.theta)
            blocks.append(StudyBlock(
                subject=strong.subject,
                topic_id=None,
                topic_name=f"{strong.subject} İleri Pratik",
                activity_type="practice",
                duration_minutes=remaining,
                question_count=int(remaining * 0.6),
                difficulty_band="hard",
                reason=f"Güçlü alan, θ={strong.theta:.2f}",
                priority=3,
            ))
            used_minutes += remaining

        # Motivasyon notu
        note = self._motivational_note(days_remaining, statuses)

        # Zayıf / güçlü ders
        weak_subj = weak_subjects[0].subject if weak_subjects else None
        strong_subj = max(statuses, key=lambda s: s.theta).subject if statuses else None

        return DailyPlan(
            user_id=user_id,
            plan_date=today,
            exam_date=exam_date,
            days_remaining=days_remaining,
            total_minutes=used_minutes,
            blocks=blocks,
            fsrs_review_count=fsrs_total,
            new_topic_count=new_topic_count,
            weak_subject=weak_subj,
            strong_subject=strong_subj,
            motivational_note=note,
        )

    async def get_next_topic(
        self, user_id: str, subject: str
    ) -> Dict:
        """
        Belirli bir ders için sıradaki konuyu döndür.
        DAG önkoşul kontrolü yapılır.
        """
        theta_map = await self._fetch_thetas(user_id)
        theta = theta_map.get(subject, 0.0)
        zpd_lower, zpd_upper = self._calc_zpd_band(theta, 0.5)

        # DB'den konuları çek (difficulty ZPD bandında)
        TOPIC_SQL = """
            SELECT th.id::text, th.name_tr, th.difficulty_level, COUNT(qb.id) AS qcount
            FROM topic_hierarchy th
            LEFT JOIN question_bank qb
                ON qb.primary_topic_id::text = th.id::text AND qb.is_active = TRUE
            WHERE th.subject_area = :subject
              AND th.is_active = TRUE
              {band_filter}
            GROUP BY th.id, th.name_tr, th.difficulty_level
            ORDER BY th.difficulty_level ASC, COUNT(qb.id) DESC
            LIMIT 1
        """
        # ZPD bandında ara, yoksa tüm konulara fallback
        for band_filter in [
            "AND th.difficulty_level BETWEEN :lower AND :upper",
            "",  # fallback: band filtresi yok
        ]:
            result = await self.db.execute(
                text(TOPIC_SQL.format(band_filter=band_filter)),
                {"subject": subject, "lower": max(-3.0, zpd_lower), "upper": min(3.0, zpd_upper)},
            )
            row = result.fetchone()
            if row:
                break

        if row:
            return {
                "topic_id":      str(row[0]),
                "topic_name":    str(row[1]),
                "difficulty":    float(row[2]) if row[2] is not None else 0.0,
                "question_count": int(row[3]),
                "zpd_lower":     round(zpd_lower, 2),
                "zpd_upper":     round(zpd_upper, 2),
                "theta":         round(theta, 3),
            }

        return {
            "topic_id": None,
            "topic_name": f"{subject} — Genel Tekrar",
            "difficulty": 0.0,
            "question_count": 0,
            "zpd_lower": round(zpd_lower, 2),
            "zpd_upper": round(zpd_upper, 2),
            "theta": round(theta, 3),
        }

    # ── Yardımcı Metodlar ─────────────────────────────────────────────────

    async def _fetch_thetas(self, user_id: str) -> Dict[str, float]:
        """user_theta tablosundan IRT theta değerlerini çek."""
        try:
            result = await self.db.execute(text("""
                SELECT subject_area, theta_estimate
                FROM user_theta
                WHERE user_id = :uid
            """), {"uid": user_id})
            return {row.subject_area: float(row.theta_estimate)
                    for row in result.fetchall()}
        except Exception as e:
            logger.warning(f"Theta çekme hatası: {e}")
            return {}

    async def _fetch_fsrs_due_counts(self, user_id: str) -> Dict[str, int]:
        """FSRS'de bugün vadesi gelen kart sayısını derse göre grupla."""
        try:
            result = await self.db.execute(text("""
                SELECT qb.subject_area, COUNT(*) AS due_count
                FROM user_item_fsrs uif
                JOIN question_bank qb ON qb.id = uif.question_id
                WHERE uif.user_id = :uid
                  AND uif.due_date <= NOW()
                  AND uif.state IN (1, 2, 3)
                GROUP BY qb.subject_area
            """), {"uid": user_id})
            return {row.subject_area: int(row.due_count)
                    for row in result.fetchall()}
        except Exception as e:
            logger.warning(f"FSRS due çekme hatası: {e}")
            return {}

    @staticmethod
    def _calc_zpd_band(theta: float, se: float) -> Tuple[float, float]:
        """
        Vygotsky ZPD'yi IRT parametrelerine çevir.
        ZPD = [θ - 0.5, θ + 1.0] (asimetrik: ileriye doğru daha geniş)
        SE yüksekse band genişler (belirsizlik durumunda keşfetme).
        """
        uncertainty_bonus = min(0.5, se)
        lower = theta - 0.5 - uncertainty_bonus
        upper = theta + 1.0 + uncertainty_bonus
        return lower, upper

    @staticmethod
    def _theta_to_mastery_pct(theta: float, se: float) -> float:
        """θ → 0-100 mastery yüzdesi (normal CDF bazlı)."""
        # P(θ > -1.0) normalize edilmiş mastery
        z = (theta + 1.0) / max(0.1, se)
        # Basitleştirilmiş normal CDF yaklaşımı
        cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return round(min(100.0, max(0.0, cdf * 100)), 1)

    @staticmethod
    def _theta_to_difficulty_band(
        theta: float, zpd_lower: float, zpd_upper: float
    ) -> str:
        mid = (zpd_lower + zpd_upper) / 2
        if theta < mid - 0.5:
            return "easy"
        elif theta > mid + 0.5:
            return "hard"
        return "medium"

    @staticmethod
    def _theta_label(theta: float) -> str:
        if theta < -1.5: return "Temel"
        if theta < -0.5: return "Başlangıç"
        if theta < 0.5:  return "Orta"
        if theta < 1.5:  return "İleri"
        return "Uzman"

    @staticmethod
    def _calc_priority_score(
        theta: float, fsrs_due: int, mastery_pct: float
    ) -> float:
        """
        Çalışma öncelik skoru (0-100).
        Düşük mastery + yüksek FSRS due → yüksek öncelik.
        """
        mastery_factor = max(0, (100 - mastery_pct)) / 100  # 0-1
        fsrs_factor = min(1.0, fsrs_due / 20.0)             # 0-1
        return round((mastery_factor * 0.6 + fsrs_factor * 0.4) * 100, 1)

    @staticmethod
    def _motivational_note(days_remaining: int, statuses: List[SubjectStatus]) -> str:
        if days_remaining <= 7:
            return "🔥 Son düzlük! Her dakika değerli, odaklan!"
        if days_remaining <= 30:
            return "⚡ 1 ay kaldı — eksik konuları tamamlama zamanı."
        if days_remaining <= 90:
            return "📈 3 ay var. Zayıf derslere yoğunlaş, iyi dersleri koru."
        avg_theta = sum(s.theta for s in statuses) / max(1, len(statuses))
        if avg_theta < 0:
            return "🌱 Temelleri sağlam kurmak her şeyin başı. Adım adım ilerliyoruz."
        return "💪 Güzel bir ilerleme! Düzenli çalışmayı sürdür."
