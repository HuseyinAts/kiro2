"""
BKT (Bayesian Knowledge Tracing) + ZPD (Zone of Proximal Development) Servisi

FAZ-1 Gorev 1.4 — Master Plan v2.0
BKTState modeli FAZ-2'de backend/models/gamification.py'de tanimlanir.
Bu servis sadece saf hesaplama yapar (DB islemi yok).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konu parametreleri (KIRO2 YKS spesifik)
# ---------------------------------------------------------------------------

SUBJECT_PARAMS: dict[str, dict[str, float]] = {
    "stem": {
        "p_T": 0.10,  # ogrenme olasiligi
        "p_G": 0.20,  # tahmin olasiligi (guessing)
        "p_S": 0.10,  # kayma olasiligi (slipping)
        "mastery": 0.80,
    },
    "sozel": {
        "p_T": 0.05,
        "p_G": 0.20,
        "p_S": 0.15,
        "mastery": 0.85,
    },
}

SOZEL_SUBJECTS: frozenset[str] = frozenset(
    {"turkce", "tarih", "edebiyat", "felsefe", "din"}
)


def get_params(subject_slug: str) -> dict[str, float]:
    """Konuya gore BKT parametrelerini dondur."""
    if subject_slug.lower() in SOZEL_SUBJECTS:
        return SUBJECT_PARAMS["sozel"]
    return SUBJECT_PARAMS["stem"]


# ---------------------------------------------------------------------------
# ZPD Manager
# ---------------------------------------------------------------------------


class ZPDManager:
    """Zone of Proximal Development hesaplama."""

    MASTERY: float = 0.80
    LOWER: float = 0.40

    @staticmethod
    def zone(p_L: float) -> str:
        """Ogrencinin hangi ZPD bolgesinde oldugunu belirle."""
        if p_L >= ZPDManager.MASTERY:
            return "MASTERED"
        if p_L >= ZPDManager.LOWER:
            return "ZPD_ACTIVE"
        return "FRUSTRATION"

    @staticmethod
    def scaffold_level(p_L: float) -> int:
        """Ipucu seviyesi (0=yok, 5=maksimum)."""
        if p_L >= ZPDManager.MASTERY:
            return 0
        return int(
            5 * (ZPDManager.MASTERY - p_L) / (ZPDManager.MASTERY - ZPDManager.LOWER)
        )

    @staticmethod
    def hints(p_L: float, max_hints: int = 4) -> int:
        """Kullanilabilir ipucu sayisi."""
        if p_L >= ZPDManager.MASTERY:
            return 0
        return max(0, int(max_hints * (1 - p_L / ZPDManager.MASTERY)))

    @staticmethod
    def bilge_mode(p_L: float) -> str:
        """Bilge Alp NPC ogretim modu."""
        if p_L < 0.30:
            return "scaffolding"
        if p_L < 0.50:
            return "guiding"
        if p_L < 0.75:
            return "challenging"
        return "socratic"

    @staticmethod
    def recommended_difficulty(p_L: float) -> str:
        """ZPD'ye gore onerilen zorluk seviyesi."""
        if p_L < 0.30:
            return "kolay"
        if p_L < 0.55:
            return "orta"
        if p_L < 0.75:
            return "zor"
        return "ileri"

    @staticmethod
    def unlock_3d(p_L: float) -> bool:
        """3D simulasyonu acmak icin minimum mastery."""
        return p_L >= 0.45


# ---------------------------------------------------------------------------
# BKT Service — saf fonksiyonlar (DB islemi yok)
# ---------------------------------------------------------------------------


class BKTService:
    """
    Bayesian Knowledge Tracing implementasyonu.

    NOT: BKTState modeli FAZ-2'de backend/models/gamification.py'de tanimlanir.
    record_answer() async olup DB'yi bu modelden kullanir.
    """

    @staticmethod
    def update(
        p_learn: float,
        correct: bool,
        p_T: float = 0.10,
        p_G: float = 0.20,
        p_S: float = 0.10,
    ) -> float:
        """
        Saf BKT guncelleme — DB islemi yok.

        Args:
            p_learn: Mevcut ogrenme olasiligi
            correct: Dogru cevap verildi mi?
            p_T: Ogrenme transfer olasiligi
            p_G: Tahmin olasiligi (guessing)
            p_S: Kayma olasiligi (slipping)

        Returns:
            Guncellenmis ogrenme olasiligi [0, 1]
        """
        if correct:
            # Dogru cevap verildiyse: Bayes posterior
            posterior = (
                p_learn * (1 - p_S) / (p_learn * (1 - p_S) + (1 - p_learn) * p_G)
            )
        else:
            # Yanlis cevap
            posterior = p_learn * p_S / (p_learn * p_S + (1 - p_learn) * (1 - p_G))

        # Transfer: yeni sey ogrendi mi?
        new_p_L = posterior + (1 - posterior) * p_T

        return round(min(new_p_L * (1 - p_T), 0.999), 4)

    @classmethod
    async def record_answer(
        cls,
        student_id: str,
        topic_id: str,
        subject_slug: str,
        correct: bool,
        rating: int,
        db: AsyncSession,
        answered_questions: list | None = None,
        responses: list | None = None,
    ) -> dict[str, Any]:
        """
        4 algoritma birlesik pipeline:
        1. BKT guncelle
        2. IRT theta guncelle
        3. FSRS karti guncelle
        4. ZPD belirle

        Returns:
            {
                new_p_L, theta_after, theta_se,
                fsrs_next_review, zpd_zone,
                scaffold_level, hints_available,
                bilge_mode, unlock_3d,
                recommended_difficulty
            }
        """
        params = get_params(subject_slug)

        # --- 1. BKT: mevcut durumu oku ---
        try:
            from sqlalchemy import select

            from models.gamification import BKTState

            stmt = select(BKTState).where(
                BKTState.student_id == student_id,
                BKTState.topic_id == topic_id,
            )
            result = await db.execute(stmt)
            bkt_state = result.scalar_one_or_none()
        except Exception:
            bkt_state = None

        p_learn = bkt_state.p_learn if bkt_state else params.get("p_T", 0.10)

        new_p_L = cls.update(
            p_learn,
            correct,
            p_T=params["p_T"],
            p_G=params["p_G"],
            p_S=params["p_S"],
        )

        # DB'ye yaz
        try:
            if bkt_state is None:
                from models.gamification import BKTState

                bkt_state = BKTState(
                    student_id=student_id,
                    topic_id=topic_id,
                    p_learn=new_p_L,
                    mastery_status="learning",
                )
                db.add(bkt_state)
            else:
                bkt_state.p_learn = new_p_L
                bkt_state.attempt_count = (bkt_state.attempt_count or 0) + 1
                bkt_state.last_attempt = datetime.now(UTC)
                if new_p_L >= ZPDManager.MASTERY:
                    bkt_state.mastery_status = "mastered"
            await db.flush()
        except Exception as e:
            logger.warning("BKT DB yazma hatasi: %s", e)

        # --- 2. IRT theta tahmini (basit EAP) ---
        theta_after = 0.0
        theta_se = 1.0
        try:
            from services.irt_service_3pl import IRTService3PL

            if answered_questions and responses:
                theta_after, theta_se = IRTService3PL.eap_theta(
                    answered_questions, responses
                )
        except Exception as e:
            logger.debug("IRT theta guncelleme atildi: %s", e)

        # --- 3. FSRS karti guncelle ---
        fsrs_next_review = None
        try:
            from services.fsrs_v6_service import FSRSService

            fsrs_result = FSRSService.review_card(
                stability=None,
                difficulty=None,
                due_date=None,
                rating_int=rating,
                reps=0,
            )
            fsrs_next_review = fsrs_result.get("due_date")
        except Exception as e:
            logger.debug("FSRS guncelleme atildi: %s", e)

        # --- 4. ZPD ---
        return {
            "new_p_L": new_p_L,
            "theta_after": round(theta_after, 4),
            "theta_se": round(theta_se, 4),
            "fsrs_next_review": (
                fsrs_next_review.isoformat() if fsrs_next_review else None
            ),
            "zpd_zone": ZPDManager.zone(new_p_L),
            "scaffold_level": ZPDManager.scaffold_level(new_p_L),
            "hints_available": ZPDManager.hints(new_p_L),
            "bilge_mode": ZPDManager.bilge_mode(new_p_L),
            "unlock_3d": ZPDManager.unlock_3d(new_p_L),
            "recommended_difficulty": ZPDManager.recommended_difficulty(new_p_L),
        }
