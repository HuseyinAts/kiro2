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

# Algoritma pipeline hata sayaclari (observability)
_ALGO_ERRORS: dict[str, int] = {"bkt_read": 0, "bkt_write": 0, "irt": 0, "fsrs": 0}

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

# SubjectArea enum'unda olmayan slug'lari gecerli bir degere esle.
#
# S179 fix (B-P0-32): collapse silinmedi (FSRSCard.subject_area SubjectArea
# enum'unu beklediği için bilinmeyen değer FK violation eder), ancak
# StudentAbility persist artık ayrı slug ID kullanır (`_SUBJECT_ID_MAP`
# içinde tarih=7, cografya=8, edebiyat=9, felsefe=10, din=11) — collapse
# yalnızca FSRSCard storage'a uygulanır, IRT theta'sı KAYBOLMAZ.
_SUBJECT_AREA_MAP: dict[str, str] = {
    "tarih": "sosyal",
    "edebiyat": "turkce",
    "felsefe": "sosyal",
    "din": "sosyal",
    "cografya": "sosyal",
    "geometri": "matematik",
}


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
        # DM-06: p_L < LOWER olduğunda 5'i aşmaması için clamp
        raw = 5 * (ZPDManager.MASTERY - p_L) / (ZPDManager.MASTERY - ZPDManager.LOWER)
        return min(5, int(raw))

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
            denom = p_learn * (1 - p_S) + (1 - p_learn) * p_G
            posterior = (p_learn * (1 - p_S) / denom) if denom > 1e-10 else p_learn
        else:
            # Yanlis cevap
            denom = p_learn * p_S + (1 - p_learn) * (1 - p_G)
            posterior = (p_learn * p_S / denom) if denom > 1e-10 else p_learn

        # Transfer: yeni sey ogrendi mi? (standart BKT: posterior + (1-posterior)*p_T)
        new_p_L = posterior + (1 - posterior) * p_T

        # DM-10: alt ve üst sınır clamp [0.001, 0.999]
        return round(max(0.001, min(new_p_L, 0.999)), 4)

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
        errors: dict[str, str | None] = {
            "bkt": None,
            "irt": None,
            "fsrs": None,
            "zpd": None,
        }

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
        except Exception as e:
            _ALGO_ERRORS["bkt_read"] += 1
            errors["bkt"] = str(e)
            logger.error(
                "BKT state okunamadi student=%s topic=%s: %s",
                student_id,
                topic_id,
                e,
                exc_info=True,
            )
            bkt_state = None

        # DM-09: başlangıç p_L olarak p_T (transit) değil p_L0 (prior) kullan
        p_learn = bkt_state.p_learn if bkt_state else 0.10

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
                    attempt_count=1,
                    last_attempt=datetime.now(UTC),
                    mastery_status="mastered"
                    if new_p_L >= ZPDManager.MASTERY
                    else "learning",
                )
                db.add(bkt_state)
            else:
                bkt_state.p_learn = new_p_L
                bkt_state.attempt_count = (bkt_state.attempt_count or 0) + 1
                bkt_state.last_attempt = datetime.now(UTC)
                if new_p_L >= ZPDManager.MASTERY:
                    bkt_state.mastery_status = "mastered"
        except Exception as e:
            _ALGO_ERRORS["bkt_write"] += 1
            errors["bkt"] = str(e)
            logger.error(
                "BKT DB yazma hatasi student=%s topic=%s: %s",
                student_id,
                topic_id,
                e,
                exc_info=True,
            )

        # --- 2. IRT theta tahmini (BKT-linked) ---
        theta_after = 0.0
        theta_se = 1.0
        try:
            from services.irt_service_3pl import IRTService3PL

            if answered_questions and responses:
                theta_after, theta_se = IRTService3PL.eap_theta(
                    answered_questions, responses
                )
            else:
                # DM-05: BKT→IRT bridge: logit dönüşümü (lineer yerine)
                # p_L [0,1] → theta [-4,4] via ln(p/(1-p)), clamped
                import math as _math

                clamped = max(0.05, min(0.95, new_p_L))
                raw_logit = _math.log(clamped / (1.0 - clamped))
                theta_after = max(-4.0, min(4.0, raw_logit))
                theta_se = max(
                    0.3, 1.0 - new_p_L
                )  # daha yuksek mastery = daha dusuk SE
        except Exception as e:
            _ALGO_ERRORS["irt"] += 1
            errors["irt"] = str(e)
            logger.error(
                "IRT theta basarisiz student=%s: %s", student_id, e, exc_info=True
            )

        # --- 2b. Theta'yi DB'ye persist et (StudentAbility) ---
        try:
            from models.gamification import StudentAbility

            _SUBJECT_ID_MAP = {
                "matematik": 1,
                "geometri": 2,
                "fizik": 3,
                "kimya": 4,
                "biyoloji": 5,
                "turkce": 6,
                "tarih": 7,
                "cografya": 8,
                "edebiyat": 9,
                "felsefe": 10,
                "din": 11,
                "sosyal": 12,
            }
            _slug_lower = subject_slug.lower() if subject_slug else "matematik"
            # S179 fix (B-P0-32): Resolve subject_id from the ORIGINAL slug
            # first so tarih/cografya/edebiyat/felsefe/din each keep their
            # own theta. Fall back to the (lossy) _SUBJECT_AREA_MAP only
            # when the original slug is unknown to _SUBJECT_ID_MAP.
            subj_id = _SUBJECT_ID_MAP.get(_slug_lower)
            if subj_id is None:
                mapped_slug = _SUBJECT_AREA_MAP.get(_slug_lower, _slug_lower)
                subj_id = _SUBJECT_ID_MAP.get(mapped_slug)
            if subj_id is not None:
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                stmt = (
                    pg_insert(StudentAbility)
                    .values(
                        student_id=student_id,
                        subject_id=subj_id,
                        theta=round(theta_after, 4),
                        theta_se=round(theta_se, 4),
                    )
                    .on_conflict_do_update(
                        index_elements=["student_id", "subject_id"],
                        set_={
                            "theta": round(theta_after, 4),
                            "theta_se": round(theta_se, 4),
                        },
                    )
                )
                await db.execute(stmt)
        except Exception as e:
            _ALGO_ERRORS["irt"] += 1
            if errors["irt"] is None:
                errors["irt"] = str(e)
            logger.error(
                "IRT theta persist hatasi student=%s: %s", student_id, e, exc_info=True
            )

        # --- 3. FSRS karti guncelle (state persistent) ---
        fsrs_next_review = None
        try:
            from sqlalchemy import select as sa_select

            from models.fsrs_models import FSRSCard
            from services.fsrs_v6_service import FSRSService

            # Mevcut FSRS karti oku (student_id + topic_id)
            fsrs_stmt = sa_select(FSRSCard).where(
                FSRSCard.student_id == student_id,
                FSRSCard.topic == topic_id,
            )
            fsrs_row = await db.execute(fsrs_stmt)
            fsrs_card = fsrs_row.scalar_one_or_none()

            # Mevcut state'i al veya default
            prev_stability = fsrs_card.stability if fsrs_card else None
            prev_difficulty = fsrs_card.difficulty if fsrs_card else None
            prev_due = fsrs_card.due_date if fsrs_card else None
            prev_reps = fsrs_card.reps if fsrs_card else 0

            fsrs_result = FSRSService.review_card(
                stability=prev_stability,
                difficulty=prev_difficulty,
                due_date=prev_due,
                rating_int=rating,
                reps=prev_reps,
            )
            fsrs_next_review = fsrs_result.get("due_date")

            # State'i DB'ye yaz
            if fsrs_card is None:
                fsrs_card = FSRSCard(
                    student_id=student_id,
                    front_text=f"Topic: {topic_id}",
                    back_text=f"BKT p_L: {new_p_L:.3f}",
                    subject_area=_SUBJECT_AREA_MAP.get(
                        subject_slug.lower(), subject_slug.lower()
                    )
                    if subject_slug
                    else "matematik",
                    topic=topic_id,
                    stability=fsrs_result.get("stability", 0.0),
                    difficulty=fsrs_result.get("difficulty", 0.0),
                    reps=fsrs_result.get("reps", 1),
                    lapses=fsrs_result.get("lapses", 0),
                    state=fsrs_result.get("state", "new"),
                    due_date=fsrs_next_review or datetime.now(UTC),
                    last_review=datetime.now(UTC),
                )
                db.add(fsrs_card)
            else:
                fsrs_card.stability = fsrs_result.get("stability", fsrs_card.stability)
                fsrs_card.difficulty = fsrs_result.get(
                    "difficulty", fsrs_card.difficulty
                )
                fsrs_card.reps = fsrs_result.get("reps") or fsrs_card.reps
                fsrs_card.lapses = fsrs_result.get("lapses", fsrs_card.lapses)
                fsrs_card.state = fsrs_result.get("state", fsrs_card.state)
                fsrs_card.due_date = fsrs_next_review or fsrs_card.due_date
                fsrs_card.last_review = datetime.now(UTC)
        except Exception as e:
            _ALGO_ERRORS["fsrs"] += 1
            errors["fsrs"] = str(e)
            logger.exception(
                "FSRS guncelleme basarisiz student=%s topic=%s: %s",
                student_id,
                topic_id,
                e,
            )

        # --- 4. ZPD + History persist ---
        zpd_zone = ZPDManager.zone(new_p_L)
        scaffold = ZPDManager.scaffold_level(new_p_L)
        try:
            from models.gamification import ZPDHistory

            zpd_row = ZPDHistory(
                student_id=student_id,
                topic_id=topic_id,
                zone=zpd_zone.lower(),
                p_learn=new_p_L,
                theta=theta_after,
                scaffold_level=scaffold,
            )
            db.add(zpd_row)
        except Exception as e:
            errors["zpd"] = str(e)
            logger.exception(
                "ZPD history persist hatasi student=%s topic=%s: %s",
                student_id,
                topic_id,
                e,
            )

        # --- 5. Blackboard publish (fire-and-forget) ---
        try:
            from services.blackboard_service import BlackboardService

            await BlackboardService.get().publish_learning_event(
                student_id=student_id,
                topic_id=topic_id,
                event_data={
                    "new_p_L": new_p_L,
                    "theta": round(theta_after, 4),
                    "theta_se": round(theta_se, 4),
                    "zpd_zone": zpd_zone,
                    "correct": correct,
                },
            )
        except Exception as e:
            logger.debug("Blackboard publish skipped: %s", e)

        return {
            "new_p_L": new_p_L,
            "theta_after": round(theta_after, 4),
            "theta_se": round(theta_se, 4),
            "irt_method": "eap" if (answered_questions and responses) else "bridge",
            "fsrs_next_review": (
                fsrs_next_review.isoformat() if fsrs_next_review else None
            ),
            "zpd_zone": zpd_zone,
            "scaffold_level": scaffold,
            "hints_available": ZPDManager.hints(new_p_L),
            "bilge_mode": ZPDManager.bilge_mode(new_p_L),
            "unlock_3d": ZPDManager.unlock_3d(new_p_L),
            "recommended_difficulty": ZPDManager.recommended_difficulty(new_p_L),
            "errors": errors,
        }
