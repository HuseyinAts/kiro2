"""
KIRO2 — Learning Path Orchestrator v2
=======================================
ZPD + DAG + IRT + FSRS birleştiren merkezi öğrenme yolu servisi.

Değişiklikler (v2):
  - DAGService inject edildi; prereq_blocked/prereq_topic artık GERÇEK veri taşıyor
  - theta_se DB'den çekiliyor (sabit 0.5 yerine)
  - days_remaining < 30 → yeni konu AÇILMAZ, FSRS pekiştirme önceliği
  - get_next_topic() önce DAG önkoşul kontrolü yapar, geçilemeyen konuları atlar
  - YKS sınav türüne göre ders ağırlıkları priority_score'a yansıtıldı
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dag_service import DAGService

try:
    from models.gamification import StudentAbility
except ImportError:
    StudentAbility = None  # type: ignore[misc,assignment]

logger = logging.getLogger("kiro2.lp_orchestrator")

# ─── YKS Ders Konfigürasyonu ──────────────────────────────────────────────────

YKS_SUBJECTS = {
    "TYT": [
        "TURKCE",
        "MATEMATIK",
        "FIZIK",
        "KIMYA",
        "BIYOLOJI",
        "TARIH",
        "COGRAFYA",
        "SOSYAL",
    ],
    "AYT_SAY": ["MATEMATIK", "FIZIK", "KIMYA", "BIYOLOJI"],
    "AYT_EA": ["MATEMATIK", "EDEBIYAT", "TARIH", "COGRAFYA"],
    "AYT_SOZ": ["EDEBIYAT", "TARIH", "COGRAFYA", "SOSYAL"],
}

# Sınav türüne göre ders ağırlıkları (ÖSYM soru dağılımı baz alındı)
YKS_SUBJECT_WEIGHTS: dict[str, dict[str, float]] = {
    "TYT": {
        "TURKCE": 1.0,
        "MATEMATIK": 1.0,
        "FIZIK": 0.50,
        "KIMYA": 0.50,
        "BIYOLOJI": 0.50,
        "TARIH": 0.35,
        "COGRAFYA": 0.35,
        "SOSYAL": 0.30,
    },
    "AYT_SAY": {
        "MATEMATIK": 1.0,
        "FIZIK": 0.75,
        "KIMYA": 0.75,
        "BIYOLOJI": 0.75,
    },
    "AYT_EA": {
        "MATEMATIK": 1.0,
        "EDEBIYAT": 1.0,
        "TARIH": 0.50,
        "COGRAFYA": 0.50,
    },
    "AYT_SOZ": {
        "EDEBIYAT": 1.0,
        "TARIH": 0.75,
        "COGRAFYA": 0.50,
        "SOSYAL": 0.50,
    },
}

TYT_EXAM_DATE_DEFAULT = date(date.today().year, 6, 7)

# ─── Veri Yapıları ────────────────────────────────────────────────────────────


@dataclass
class SubjectStatus:
    """Bir dersteki öğrenci durumu."""

    subject: str
    theta: float = 0.0
    theta_se: float = 0.5
    mastery_pct: float = 0.0
    fsrs_due_count: int = 0
    next_topic_id: str | None = None
    next_topic_name: str | None = None
    prereq_blocked: bool = False  # v2: DAG kontrolünden gelen gerçek değer
    prereq_topic: str | None = None  # v2: Hangi önkoşul eksik (topic_id)
    prereq_topic_name: str | None = None  # v2: Okunabilir ismi
    zpd_lower: float = -1.0
    zpd_upper: float = 1.0
    zpd_zone: str = "ZPD_ACTIVE"  # MASTERED | ZPD_ACTIVE | FRUSTRATION
    priority_score: float = 0.0
    needs_cat: bool = False


@dataclass
class StudyBlock:
    """Tek bir çalışma bloğu."""

    subject: str
    topic_id: str | None
    topic_name: str
    activity_type: str  # "cat" | "fsrs_review" | "practice" | "prereq"
    duration_minutes: int = 30
    question_count: int = 10
    difficulty_band: str = "medium"
    reason: str = ""
    priority: int = 0
    prereq_blocked: bool = False  # v2: Bu blok önkoşul gerektiriyor mu


@dataclass
class DailyPlan:
    """Bir günlük çalışma planı."""

    user_id: str
    plan_date: date
    exam_date: date
    days_remaining: int
    total_minutes: int
    blocks: list[StudyBlock] = field(default_factory=list)
    fsrs_review_count: int = 0
    new_topic_count: int = 0
    weak_subject: str | None = None
    strong_subject: str | None = None
    motivational_note: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


# ─── Orchestrator ─────────────────────────────────────────────────────────────


class LearningPathOrchestrator:
    """ZPD + DAG + IRT + FSRS birleştiren ana servis."""

    def __init__(self, db: AsyncSession, redis=None):
        self.db = db
        self.redis = redis
        # v2: DAGService her instance'ta hazır; memory cache sayesinde hızlı
        self._dag_service = DAGService(db=db, redis=redis)

    # ── Öğrenci Durum Analizi ─────────────────────────────────────────────

    async def get_student_subject_statuses(
        self,
        user_id: str,
        exam_type: str = "TYT",
    ) -> list[SubjectStatus]:
        """
        Tüm dersler için öğrenci durumunu çek.
        v2: DAGService üzerinden gerçek önkoşul kontrolü yapılıyor.
        """
        statuses = []

        # 1. IRT theta + SE değerleri
        theta_map, se_map = await self._fetch_thetas_with_se(user_id)

        # 2. FSRS vadesi gelen kart sayısı
        fsrs_map = await self._fetch_fsrs_due_counts(user_id)

        # 3. DAG mastery skorlarını Redis cache'e yükle (sonraki DAG sorgularında kullanılır)
        _ = await self._dag_service.get_user_mastery(user_id)

        # 4. Sınav türü ağırlıkları
        weights = YKS_SUBJECT_WEIGHTS.get(exam_type, YKS_SUBJECT_WEIGHTS["TYT"])

        all_subjects: set = set()
        for subj_list in YKS_SUBJECTS.values():
            all_subjects.update(subj_list)

        for subject in sorted(all_subjects):
            has_theta = subject in theta_map
            theta = theta_map.get(subject, 0.0)
            se = se_map.get(subject, 0.5)  # v2: gerçek SE
            fsrs_due = fsrs_map.get(subject, 0)
            weight = weights.get(subject, 0.5)

            zpd_lower, zpd_upper = self._calc_zpd_band(theta, se)
            mastery_pct = (
                0.0 if not has_theta else self._theta_to_mastery_pct(theta, se)
            )

            # v2: DAGService üzerinden sıradaki konuyu ve önkoşul durumunu al
            prereq_blocked = False
            prereq_topic_id = None
            prereq_topic_name = None
            next_topic_id = None
            next_topic_name = None

            try:
                next_tid = await self._dag_service.get_next_recommended_topic(
                    user_id=user_id,
                    subject_id=subject.lower(),
                )
                if next_tid:
                    # Önerilen konunun önkoşul durumu
                    check = await self._dag_service.check_can_study_topic(
                        user_id=user_id,
                        topic_id=next_tid,
                    )
                    next_topic_id = next_tid
                    # LP-04: DAG'dan gerçek konu adını çek (UUID yerine)
                    dag = await self._dag_service.get_dag()
                    topic_node = dag.get_topic(next_tid)
                    next_topic_name = topic_node.name if topic_node else next_tid

                    if not check.can_proceed and check.blocking_prereqs:
                        prereq_blocked = True
                        prereq_topic_id = check.blocking_prereqs[0]
                        prereq_node = dag.get_topic(prereq_topic_id)
                        prereq_topic_name = (
                            prereq_node.name if prereq_node else prereq_topic_id
                        )
            except Exception as e:
                # K-A3: Hata durumunda güvenli taraf — öğrenci hazır olmadığı konuya gitmesin
                prereq_blocked = True
                logger.warning(f"DAG önkoşul kontrolü başarısız ({subject}): {e}")

            priority = (
                100.0
                if not has_theta
                else self._calc_priority_score(
                    theta=theta,
                    fsrs_due=fsrs_due,
                    mastery_pct=mastery_pct,
                    subject_weight=weight,
                )
            )

            # Compute ZPD zone from mastery_pct
            if mastery_pct >= 80:
                zpd_zone = "MASTERED"
            elif mastery_pct >= 40:
                zpd_zone = "ZPD_ACTIVE"
            else:
                zpd_zone = "FRUSTRATION"

            statuses.append(
                SubjectStatus(
                    subject=subject,
                    theta=theta,
                    theta_se=se,
                    mastery_pct=mastery_pct,
                    fsrs_due_count=fsrs_due,
                    next_topic_id=next_topic_id,
                    next_topic_name=next_topic_name,
                    prereq_blocked=prereq_blocked,
                    prereq_topic=prereq_topic_id,
                    prereq_topic_name=prereq_topic_name,
                    zpd_lower=zpd_lower,
                    zpd_upper=zpd_upper,
                    zpd_zone=zpd_zone,
                    priority_score=priority,
                    needs_cat=not has_theta,
                )
            )

        statuses.sort(key=lambda s: -s.priority_score)
        return statuses

    async def generate_daily_plan(
        self,
        user_id: str,
        available_minutes: int = 120,
        exam_date: date | None = None,
        exam_type: str = "TYT",
    ) -> DailyPlan:
        """
        Günlük çalışma planı.
        v2: Sınava yakın dönemde (< 30 gün) yeni konu açılmaz.
        """
        if exam_date is None:
            exam_date = TYT_EXAM_DATE_DEFAULT

        today = date.today()
        days_remaining = max(1, (exam_date - today).days)

        statuses = await self.get_student_subject_statuses(user_id, exam_type)

        blocks: list[StudyBlock] = []
        used_minutes = 0
        fsrs_total = 0
        new_topic_count = 0

        # Sınava yakın mı? (< 30 gün → sadece tekrar + pekiştirme)
        exam_crunch = days_remaining < 30

        # ── FAZ 1: FSRS Tekrarları ──────────────────────────────────────
        for status in statuses:
            if used_minutes >= available_minutes:
                break
            if status.fsrs_due_count <= 0:
                continue
            review_mins = min(20, status.fsrs_due_count * 2)
            blocks.append(
                StudyBlock(
                    subject=status.subject,
                    topic_id=None,
                    topic_name=f"{status.subject} Tekrar",
                    activity_type="fsrs_review",
                    duration_minutes=review_mins,
                    question_count=status.fsrs_due_count,
                    difficulty_band="mixed",
                    reason=f"{status.fsrs_due_count} kart vadesi geldi",
                    priority=1,
                )
            )
            used_minutes += review_mins
            fsrs_total += status.fsrs_due_count

        # ── FAZ 2: Sınav kıyısında ek FSRS / normal dönemde CAT ─────────
        if exam_crunch:
            # < 30 gün: Tüm kalan süre pekiştirmeye; yeni konu YOK
            remaining = available_minutes - used_minutes
            if remaining >= 20 and statuses:
                weak = sorted(statuses, key=lambda s: s.theta)[0]
                blocks.append(
                    StudyBlock(
                        subject=weak.subject,
                        topic_id=weak.next_topic_id,
                        topic_name=f"{weak.subject} Yoğun Tekrar",
                        activity_type="fsrs_review",
                        duration_minutes=remaining,
                        question_count=int(remaining * 0.8),
                        difficulty_band="medium",
                        reason=f"Sınava {days_remaining} gün kaldı — pekiştirme modu",
                        priority=1,
                    )
                )
                used_minutes += remaining
        else:
            # Normal dönem: Zayıf 3 derste CAT blokları
            weak_subjects = sorted(
                [s for s in statuses if not s.prereq_blocked], key=lambda s: s.theta
            )[:3]

            for status in weak_subjects:
                if used_minutes >= available_minutes - 10:
                    break
                cat_mins = 25 if days_remaining > 180 else 30

                blocks.append(
                    StudyBlock(
                        subject=status.subject,
                        topic_id=status.next_topic_id,
                        topic_name=status.next_topic_name
                        or f"{status.subject} Adaptif Test",
                        activity_type="cat",
                        duration_minutes=cat_mins,
                        question_count=int(cat_mins * 0.5),
                        difficulty_band=self._theta_to_difficulty_band(
                            status.theta, status.zpd_lower, status.zpd_upper
                        ),
                        reason=(
                            f"θ={status.theta:.2f} — {self._theta_label(status.theta)}"
                        ),
                        priority=2,
                        prereq_blocked=False,
                    )
                )
                used_minutes += cat_mins
                new_topic_count += 1

            # Önkoşul engellenmiş dersler için uyarı blokları ekle
            for status in statuses:
                if not status.prereq_blocked:
                    continue
                if used_minutes >= available_minutes:
                    break
                blocks.append(
                    StudyBlock(
                        subject=status.subject,
                        topic_id=status.prereq_topic,
                        topic_name=(
                            f"Önce: {status.prereq_topic_name or status.prereq_topic}"
                        ),
                        activity_type="prereq",
                        duration_minutes=0,
                        question_count=0,
                        difficulty_band="easy",
                        reason=f"{status.subject} için önkoşul tamamlanmadı",
                        priority=2,
                        prereq_blocked=True,
                    )
                )

        # ── FAZ 3: Güçlü Derste Pratik ──────────────────────────────────
        remaining = available_minutes - used_minutes
        if remaining >= 20 and statuses and not exam_crunch:
            strong = max(statuses, key=lambda s: s.theta)
            blocks.append(
                StudyBlock(
                    subject=strong.subject,
                    topic_id=None,
                    topic_name=f"{strong.subject} İleri Pratik",
                    activity_type="practice",
                    duration_minutes=remaining,
                    question_count=int(remaining * 0.6),
                    difficulty_band="hard",
                    reason=f"Güçlü alan, θ={strong.theta:.2f}",
                    priority=3,
                )
            )
            used_minutes += remaining

        note = self._motivational_note(days_remaining, statuses)
        weak_subjects_list = sorted(statuses, key=lambda s: s.theta)
        # TÃ¼m theta'lar eÅŸitse (cold start) weak/strong gÃ¶sterme
        thetas = [s.theta for s in statuses]
        all_equal = len(set(thetas)) <= 1
        _weak = (
            weak_subjects_list[0].subject
            if (weak_subjects_list and not all_equal)
            else None
        )
        _strong_stat = max(statuses, key=lambda s: s.theta) if statuses else None
        _strong = (
            _strong_stat.subject
            if (_strong_stat and not all_equal and _strong_stat.subject != _weak)
            else None
        )
        return DailyPlan(
            user_id=user_id,
            plan_date=today,
            exam_date=exam_date,
            days_remaining=days_remaining,
            total_minutes=used_minutes,
            blocks=blocks,
            fsrs_review_count=fsrs_total,
            new_topic_count=new_topic_count,
            weak_subject=_weak,
            strong_subject=_strong,
            motivational_note=note,
        )

    async def get_next_topic(self, user_id: str, subject: str) -> dict:
        """
        Belirli bir ders için sıradaki konuyu döndür.
        v2: DAG önkoşul kontrolü yapılır; geçilemeyen konu önerilmez.
        """
        theta_map, se_map = await self._fetch_thetas_with_se(user_id)
        theta = theta_map.get(subject, 0.0)
        se = se_map.get(subject, 0.5)
        zpd_lower, zpd_upper = self._calc_zpd_band(theta, se)

        # v2: DAGService'ten önerilen konuyu al
        try:
            next_tid = await self._dag_service.get_next_recommended_topic(
                user_id=user_id,
                subject_id=subject.lower(),
            )
            if next_tid:
                check = await self._dag_service.check_can_study_topic(
                    user_id=user_id, topic_id=next_tid
                )
                blocking_names = check.blocking_prereqs

                # DB'den konu detaylarını çek
                row = await self._fetch_topic_row(next_tid)
                if row:
                    return {
                        "topic_id": str(row["id"]),
                        "topic_name": str(row["name"]),
                        "difficulty": float(row["difficulty"] or 0.0),
                        "question_count": int(row["qcount"] or 0),
                        "zpd_lower": round(zpd_lower, 2),
                        "zpd_upper": round(zpd_upper, 2),
                        "theta": round(theta, 3),
                        "can_proceed": check.can_proceed,
                        "blocking_prereqs": blocking_names,
                        "warning_prereqs": check.warning_prereqs,
                    }
        except Exception as e:
            logger.warning(f"DAG get_next_topic hatası ({subject}): {e}")

        # Fallback: ZPD bandında DB sorgusu (DAG yoksa)
        row = await self._fetch_topic_by_zpd(subject, zpd_lower, zpd_upper)
        if row:
            return {
                "topic_id": str(row["id"]),
                "topic_name": str(row["name"]),
                "difficulty": float(row["difficulty"] or 0.0),
                "question_count": int(row["qcount"] or 0),
                "zpd_lower": round(zpd_lower, 2),
                "zpd_upper": round(zpd_upper, 2),
                "theta": round(theta, 3),
                "can_proceed": True,
                "blocking_prereqs": [],
                "warning_prereqs": [],
            }

        return {
            "topic_id": None,
            "topic_name": f"{subject} — Genel Tekrar",
            "difficulty": 0.0,
            "question_count": 0,
            "zpd_lower": round(zpd_lower, 2),
            "zpd_upper": round(zpd_upper, 2),
            "theta": round(theta, 3),
            "can_proceed": True,
            "blocking_prereqs": [],
            "warning_prereqs": [],
        }

    # ── Yardımcı DB metodları ─────────────────────────────────────────────

    # subject_id → subject_area name reverse mapping (StudentAbility uses int PKs)
    _REVERSE_SUBJECT_MAP: dict[int, str] = {
        1: "MATEMATIK",
        2: "GEOMETRI",
        3: "FIZIK",
        4: "KIMYA",
        5: "BIYOLOJI",
        6: "TURKCE",
        7: "TARIH",
        8: "COGRAFYA",
        9: "EDEBIYAT",
        10: "FELSEFE",
        11: "DIN",
        12: "SOSYAL",
    }

    async def _fetch_thetas_with_se(
        self, user_id: str
    ) -> tuple[dict[str, float], dict[str, float]]:
        """student_abilities tablosundan theta + SE değerleri. v2: SE artık gerçek."""
        theta_map: dict[str, float] = {}
        se_map: dict[str, float] = {}
        try:
            result = await self.db.execute(
                select(StudentAbility).where(StudentAbility.student_id == user_id)
            )
            for row in result.scalars():
                subject_name = self._REVERSE_SUBJECT_MAP.get(row.subject_id, "")
                if subject_name:
                    theta_map[subject_name] = float(row.theta)
                    se_map[subject_name] = float(row.theta_se) if row.theta_se else 0.5
        except Exception as e:
            # K-A6: Hata durumunda boş dict dönmek yerine logla + boş dön
            # (raise yapmak tüm daily API'yi kırar, boş dict güvenli fallback)
            logger.error(f"Theta+SE çekme HATASI — tüm dersler θ=0.0 olacak: {e}")
        return theta_map, se_map

    async def _fetch_fsrs_due_counts(self, user_id: str) -> dict[str, int]:
        """FSRS bugün vadesi gelen kart sayısı (ders bazında).

        LP-03 fix: fsrs_cards tablosu kullan (bkt_service buraya yazar).
        Eski user_item_fsrs tablosu farklı schema — her zaman 0 dönüyordu.
        """
        try:
            result = await self.db.execute(
                text("""
                SELECT subject_area::text, COUNT(*) AS due_count
                FROM fsrs_cards
                WHERE student_id = :uid
                  AND due_date <= NOW()
                  AND state NOT IN ('new')
                GROUP BY subject_area
            """),
                {"uid": user_id},
            )
            return {row.subject_area: int(row.due_count) for row in result.fetchall()}
        except Exception as e:
            logger.warning(f"FSRS due çekme hatası: {e}")
            return {}

    async def _fetch_topic_row(self, topic_id: str) -> dict | None:
        """Tek konu satırı çek (id ile)."""
        try:
            result = await self.db.execute(
                text("""
                SELECT th.id::text AS id, th.name_tr AS name,
                       th.difficulty_level AS difficulty,
                       COUNT(qb.id) AS qcount
                FROM topic_hierarchy th
                LEFT JOIN question_bank qb
                    ON qb.primary_topic_id::text = th.id::text
                    AND qb.is_active = TRUE
                WHERE th.id::text = :tid AND th.is_active = TRUE
                GROUP BY th.id, th.name_tr, th.difficulty_level
            """),
                {"tid": topic_id},
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row.id,
                    "name": row.name,
                    "difficulty": row.difficulty,
                    "qcount": row.qcount,
                }
        except Exception as e:
            logger.debug(f"Konu çekme hatası: {e}")
        return None

    async def _fetch_topic_by_zpd(
        self, subject: str, zpd_lower: float, zpd_upper: float
    ) -> dict | None:
        """ZPD bandında ders bazlı konu çek (DAG fallback)."""
        TOPIC_SQL = """
            SELECT th.id::text AS id, th.name_tr AS name,
                   th.difficulty_level AS difficulty,
                   COUNT(qb.id) AS qcount
            FROM topic_hierarchy th
            LEFT JOIN question_bank qb
                ON qb.primary_topic_id::text = th.id::text AND qb.is_active = TRUE
            WHERE th.subject_area = :subject AND th.is_active = TRUE
              {band_filter}
            GROUP BY th.id, th.name_tr, th.difficulty_level
            ORDER BY th.difficulty_level ASC, COUNT(qb.id) DESC
            LIMIT 1
        """
        for band_filter in [
            "AND th.difficulty_level BETWEEN :lower AND :upper",
            "",
        ]:
            try:
                result = await self.db.execute(
                    text(TOPIC_SQL.format(band_filter=band_filter)),
                    {
                        "subject": subject,
                        "lower": max(-3.0, zpd_lower),
                        "upper": min(3.0, zpd_upper),
                    },
                )
                row = result.fetchone()
                if row:
                    return {
                        "id": row.id,
                        "name": row.name,
                        "difficulty": row.difficulty,
                        "qcount": row.qcount,
                    }
            except Exception as e:
                logger.warning("Konu sorgusu başarısız: %s", e)
        return None

    # ── Hesaplama yardımcıları ────────────────────────────────────────────

    @staticmethod
    def _calc_zpd_band(theta: float, se: float) -> tuple[float, float]:
        """ZPD = [θ−0.5−bonus, θ+1.0+bonus]; SE yüksekse band genişler."""
        bonus = min(0.5, se)
        return theta - 0.5 - bonus, theta + 1.0 + bonus

    @staticmethod
    def _theta_to_mastery_pct(theta: float, se: float) -> float:
        """θ → 0-100 mastery (normal CDF). K-A4: θ=0 → %50 (ortalama)."""
        z = theta / max(0.1, se)
        cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return round(min(100.0, max(0.0, cdf * 100)), 1)

    @staticmethod
    def _theta_to_difficulty_band(
        theta: float, zpd_lower: float, zpd_upper: float
    ) -> str:
        mid = (zpd_lower + zpd_upper) / 2
        if theta < mid - 0.5:
            return "easy"
        if theta > mid + 0.5:
            return "hard"
        return "medium"

    @staticmethod
    def _theta_label(theta: float) -> str:
        if theta < -1.5:
            return "Temel"
        if theta < -0.5:
            return "Başlangıç"
        if theta < 0.5:
            return "Orta"
        if theta < 1.5:
            return "İleri"
        return "Uzman"

    @staticmethod
    def _calc_priority_score(
        theta: float,
        fsrs_due: int,
        mastery_pct: float,
        subject_weight: float = 1.0,
    ) -> float:
        """
        Öncelik skoru (0-100).
        v2: Sınav ağırlığı da hesaba katılıyor.
        """
        mastery_factor = max(0.0, (100 - mastery_pct)) / 100
        fsrs_factor = min(1.0, fsrs_due / 20.0)
        raw = (mastery_factor * 0.6 + fsrs_factor * 0.4) * 100
        return round(raw * subject_weight, 1)

    @staticmethod
    def _motivational_note(days_remaining: int, statuses: list[SubjectStatus]) -> str:
        if days_remaining <= 7:
            return "🔥 Son düzlük! Her dakika değerli, odaklan!"
        if days_remaining <= 30:
            return "⚡ 1 ay kaldı — yeni konu açma, bildiklerini pekiştir."
        if days_remaining <= 90:
            return "📈 3 ay var. Zayıf derslere yoğunlaş, iyi dersleri koru."
        avg_theta = sum(s.theta for s in statuses) / max(1, len(statuses))
        if avg_theta < 0:
            return "🌱 Temelleri sağlam kurmak her şeyin başı. Adım adım ilerle."
        return "💪 Güzel bir ilerleme! Düzenli çalışmayı sürdür."
