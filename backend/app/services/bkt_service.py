"""
Bayesian Knowledge Tracing (BKT) Service.

Bu modül KIRO2 öğrenci performans takibi için BKT algoritmasını
uygular. BKT, bir öğrencinin belirli bir konuyu bilme olasılığını
(p_learn) Bayes posterior güncellemesi ile tahmin eder.

Kalıcılık: bkt_states tablosu (UPSERT pattern, raw SQL).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

# -------------------------------------------------------------------
# Constants: Default BKT parametreleri
# -------------------------------------------------------------------

DEFAULT_P_LEARN = 0.05  # Başlangıç öğrenme olasılığı
DEFAULT_P_TRANSIT = 0.10  # Geçiş (transit) olasılığı - her doğru yanıtta öğrenme artışı
DEFAULT_P_GUESS = 0.20  # Yanlış tahmin olasılığı (şansla doğru bilme)
DEFAULT_P_SLIP = 0.10  # Kayma (slip) olasılığı (bilmesine rağmen yanlış cevap)

# -------------------------------------------------------------------
# Mastery durumları
# -------------------------------------------------------------------


class MasteryStatus(str, Enum):
    """BKT mastery durumları - p_learn eşiğine göre belirlenir."""

    FRUSTRATED = "frustrated"  # p_learn < 0.40 - öğrenci zorlanıyor
    LEARNING = "learning"  # 0.40 <= p_learn < 0.80 - öğrenme sürecinde
    MASTERED = "mastered"  # p_learn >= 0.80 - konu hakim


def _compute_mastery(p_learn: float) -> MasteryStatus:
    """p_learn değerine göre mastery status döndür."""
    if p_learn >= 0.80:
        return MasteryStatus.MASTERED
    if p_learn < 0.40:
        return MasteryStatus.FRUSTRATED
    return MasteryStatus.LEARNING


# -------------------------------------------------------------------
# BKTPState dataclass (BKT Persistent State)
# -------------------------------------------------------------------


@dataclass
class BKTPState:
    """
    BKT durumunu temsil eden immutable dataclass.

    DB tablosu bkt_states ile birebir uyumlu. Bu sınıf DB okuma/yazma
    için kullanılır. Field'lar BKTState ORM modeli ile tam uyumludur.

    Notlar:
    - p_learn: Öğrencinin bu konuyu BİLDİĞİ varsayılan posterior olasılık
    - p_transit: Her doğru yanıtta öğrenme artışı oranı (learning rate)
    - p_guess: Şans ile doğru bilme olasılığı (genellikle 1/k = 0.20)
    - p_slip: Bilmesine rağmen yanlış bilme olasılığı (genellikle 0.05-0.10)
    - attempt_count: Toplam deneme sayısı
    - mastery_status: p_learn eşiğine göre türetilmiş durum
    """

    student_id: int
    topic_id: int
    p_learn: float = field(default=DEFAULT_P_LEARN)
    p_transit: float = field(default=DEFAULT_P_TRANSIT)
    p_guess: float = field(default=DEFAULT_P_GUESS)
    p_slip: float = field(default=DEFAULT_P_SLIP)
    attempt_count: int = 0
    mastery_status: MasteryStatus = field(default=MasteryStatus.LEARNING)
    last_attempt: datetime | None = None
    created_at: datetime | None = None


# -------------------------------------------------------------------
# SQL Constants
# -------------------------------------------------------------------

_UPSERT_BKT_SQL = text("""
    INSERT INTO bkt_states (
        student_id,
        topic_id,
        p_learn,
        p_transit,
        p_guess,
        p_slip,
        attempt_count,
        mastery_status,
        last_attempt,
        created_at
    ) VALUES (
        :student_id,
        :topic_id,
        :p_learn,
        :p_transit,
        :p_guess,
        :p_slip,
        :attempt_count,
        :mastery_status,
        :last_attempt,
        NOW()
    )
    ON CONFLICT (student_id, topic_id)
    DO UPDATE SET
        p_learn = EXCLUDED.p_learn,
        p_transit = EXCLUDED.p_transit,
        p_guess = EXCLUDED.p_guess,
        p_slip = EXCLUDED.p_slip,
        attempt_count = EXCLUDED.attempt_count,
        mastery_status = EXCLUDED.mastery_status,
        last_attempt = EXCLUDED.last_attempt
""")

_SELECT_BKT_SQL = text("""
    SELECT
        student_id,
        topic_id,
        p_learn,
        p_transit,
        p_guess,
        p_slip,
        attempt_count,
        mastery_status,
        last_attempt,
        created_at
    FROM bkt_states
    WHERE student_id = :student_id AND topic_id = :topic_id
""")


# -------------------------------------------------------------------
# BKTService
# -------------------------------------------------------------------


class BKTService:
    """
    Bayesian Knowledge Tracing servisi.

    Kullanım örneği:
        service = BKTService(db)
        state = await service.get_bkt_state(student_id=1, topic_id=5)

        # Doğru cevap
        await service.update_bkt_state(student_id=1, topic_id=5, is_correct=True)

        # Yanlış cevap
        await service.update_bkt_state(student_id=1, topic_id=5, is_correct=False)

    Mevcut durum yoksa (first touch), varsayılan değerlerle yeni kayıt oluşturulur.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Args:
            db: SQLAlchemy AsyncSession. Genellikle Depends(get_db) ile enjekte edilir.
        """
        self._db = db

    async def get_bkt_state(self, student_id: int, topic_id: int) -> BKTPState:
        """
        Öğrencinin belirli bir konudaki BKT durumunu oku.

        Kayıt yoksa varsayılan değerlerle yeni BKTPState döndürür
        (upsert'ten önce çağrıldığında first-touch için kullanılabilir).

        Args:
            student_id: Öğrenci ID
            topic_id: Konu ID

        Returns:
            BKTPState: Mevcut durum veya yeni başlangıç durumu
        """
        result = await self._db.execute(
            _SELECT_BKT_SQL,
            {"student_id": student_id, "topic_id": topic_id},
        )
        row = result.fetchone()

        if row is None:
            # First touch - varsayılan başlangıç durumu
            return BKTPState(
                student_id=student_id,
                topic_id=topic_id,
                p_learn=DEFAULT_P_LEARN,
                p_transit=DEFAULT_P_TRANSIT,
                p_guess=DEFAULT_P_GUESS,
                p_slip=DEFAULT_P_SLIP,
                attempt_count=0,
                mastery_status=MasteryStatus.LEARNING,
                last_attempt=None,
                created_at=None,
            )

        return BKTPState(
            student_id=row.student_id,
            topic_id=row.topic_id,
            p_learn=float(row.p_learn),
            p_transit=float(row.p_transit),
            p_guess=float(row.p_guess),
            p_slip=float(row.p_slip),
            attempt_count=row.attempt_count,
            mastery_status=MasteryStatus(row.mastery_status),
            last_attempt=row.last_attempt,
            created_at=row.created_at,
        )

    async def update_bkt_state(
        self, student_id: int, topic_id: int, is_correct: bool
    ) -> BKTPState:
        """
        BKT durumunu güncelle ve veritabanına UPSERT et.

        Standard BKT posterior güncelleme formülü:
        - Doğru cevap:  p_L_new = p_L + (1 - p_L) * p_T
          (Mevcut bilgi + yeni öğrenme kazanımı)
        - Yanlış cevap: p_L_new = p_L * (1 - p_T)
          (Mevcut bilginin bir kısmı kaybolur/silinir)

        NOT: Bu, BKT'nin orijinal Cormier & Corbett formülüdür.
        Alternatif Bayes posterior formülasyonu için fsrs_service.py'ye bakılabilir.

        Args:
            student_id: Öğrenci ID
            topic_id: Konu ID
            is_correct: Yanıtın doğru olup olmadığı

        Returns:
            BKTPState: Güncellenmiş yeni durum
        """
        # 1. Mevcut durumu oku (yoksa varsayılan)
        current = await self.get_bkt_state(student_id=student_id, topic_id=topic_id)

        # 2. Standart BKT posterior güncellemesi
        p_L = current.p_learn
        p_T = current.p_transit

        if is_correct:
            # Doğru cevap: bilgi öğrenme artışı
            # p_L_new = p_L + (1 - p_L) * p_T
            p_learn_new = p_L + (1.0 - p_L) * p_T
        else:
            # Yanlış cevap: bilgi kaybı (slip/slip without learning)
            # p_L_new = p_L * (1 - p_T)
            p_learn_new = p_L * (1.0 - p_T)

        # 3. Clamp: olasılık sınırları içinde tut
        p_learn_new = max(0.0, min(1.0, p_learn_new))

        # 4. attempt_count artır
        new_attempt_count = current.attempt_count + 1

        # 5. Mastery status güncelle
        mastery_status = _compute_mastery(p_learn_new)

        # 6. New state oluştur
        now = datetime.now(UTC)
        new_state = BKTPState(
            student_id=student_id,
            topic_id=topic_id,
            p_learn=round(p_learn_new, 6),
            p_transit=current.p_transit,
            p_guess=current.p_guess,
            p_slip=current.p_slip,
            attempt_count=new_attempt_count,
            mastery_status=mastery_status,
            last_attempt=now,
            created_at=current.created_at,
        )

        # 7. UPSERT
        await self._write_state(new_state)

        return new_state

    async def _write_state(self, state: BKTPState) -> None:
        """
        BKT durumunu bkt_states tablosuna UPSERT et.

        Args:
            state: Yazılacak BKTPState
        """
        await self._db.execute(
            _UPSERT_BKT_SQL,
            {
                "student_id": state.student_id,
                "topic_id": state.topic_id,
                "p_learn": state.p_learn,
                "p_transit": state.p_transit,
                "p_guess": state.p_guess,
                "p_slip": state.p_slip,
                "attempt_count": state.attempt_count,
                "mastery_status": state.mastery_status.value,
                "last_attempt": state.last_attempt,
            },
        )
        await self._db.commit()
