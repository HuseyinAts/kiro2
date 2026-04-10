"""
KIRO2 — FSRS Service
=====================
FSRS state'ini DB'den yönetir ve CAT ile entegre eder.

Önemli tasarım kararı:
  FSRS güncellemeleri CAT oturumu bittiğinde toplu yapılır.
  Her yanıtta ayrı DB yazımı yapılmaz (performans).

Oturum akışı:
  1. CAT başlar → FSRS due items yükle (Redis cache'e)
  2. Her yanıtta → CAT state içinde FSRS güncelleme kuyruğu birikir
  3. Oturum biter → toplu FSRS güncelleme DB'ye yazılır

FSRS+CAT soru seçimi:
  - Vadesi geçmiş FSRS kartları: combined_priority_score hesapla
  - Vadesi gelmemiş kartlar: saf IRT information gain kullan
  - Oturumun ilk N sorusu (warm-up): kolay, vadesi gelen kartlar öncelikli
"""

from __future__ import annotations

import logging
from datetime import UTC

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.fsrs_engine import (
    FSRSResult,
    FSRSState,
    answer_to_fsrs_rating,
    combined_priority_score,
    fsrs_update,
)

logger = logging.getLogger(__name__)

# ─── SQL sorguları ────────────────────────────────────────────────────────────

_FETCH_DUE_SQL = text("""
    SELECT
        f.question_id::text,
        f.stability,
        f.difficulty,
        f.due_date,
        f.last_review,
        f.state,
        f.reps,
        f.lapses,
        f.scheduled_days,
        f.elapsed_days,
        q.irt_discrimination  AS irt_a,
        q.irt_difficulty      AS irt_b,
        q.irt_guessing        AS irt_c,
        q.subject_area        AS subject_id,
        q.primary_topic_id    AS topic_id,
        q.question_text,
        q.option_a,
        q.option_b,
        q.option_c,
        q.option_d
    FROM user_item_fsrs f
    JOIN question_bank q ON q.id = f.question_id
    WHERE f.user_id = :user_id
      AND f.due_date <= NOW() + INTERVAL '4 hours'
      AND f.state IN (1, 2, 3)
      AND q.is_active = TRUE
    ORDER BY f.due_date ASC
    LIMIT :limit
""")

_FETCH_ITEM_SQL = text("""
    SELECT
        f.stability, f.difficulty, f.due_date,
        f.last_review, f.state, f.reps, f.lapses,
        f.scheduled_days, f.elapsed_days
    FROM user_item_fsrs f
    WHERE f.user_id = :uid AND f.question_id = :qid
    FOR UPDATE
""")

_UPSERT_FSRS_SQL = text("""
    INSERT INTO user_item_fsrs (
        user_id, question_id,
        stability, difficulty, due_date,
        last_review, state, reps, lapses,
        scheduled_days, elapsed_days
    ) VALUES (
        :user_id, :question_id,
        :stability, :difficulty, :due_date,
        :last_review, :state, :reps, :lapses,
        :scheduled_days, :elapsed_days
    )
    ON CONFLICT (user_id, question_id) DO UPDATE SET
        stability      = EXCLUDED.stability,
        difficulty     = EXCLUDED.difficulty,
        due_date       = EXCLUDED.due_date,
        last_review    = EXCLUDED.last_review,
        state          = EXCLUDED.state,
        reps           = EXCLUDED.reps,
        lapses         = EXCLUDED.lapses,
        scheduled_days = EXCLUDED.scheduled_days,
        elapsed_days   = EXCLUDED.elapsed_days
""")

_DUE_COUNT_SQL = text("""
    SELECT COUNT(*) AS cnt
    FROM user_item_fsrs
    WHERE user_id = :uid
      AND due_date <= NOW() + INTERVAL '4 hours'
      AND state IN (1, 2, 3)
""")


# ─── FSRSService ──────────────────────────────────────────────────────────────


class FSRSService:
    """FSRS state yönetimi — DB operasyonları."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Okuma ────────────────────────────────────────────────────

    async def get_due_items(
        self,
        user_id: str,
        subject_id: str | None = None,
        limit: int = 50,
    ) -> list[tuple[FSRSState, dict]]:
        """
        Vadesi gelen FSRS kartlarını IRT parametreleriyle birlikte getir.
        Döndürür: [(FSRSState, {irt_a, irt_b, irt_c, subject_id, topic_id}), ...]
        """
        result = await self.db.execute(
            _FETCH_DUE_SQL, {"user_id": user_id, "limit": limit}
        )
        rows = result.fetchall()

        items = []
        for row in rows:
            if subject_id and row.subject_id != subject_id:
                continue

            state = FSRSState(
                user_id=user_id,
                question_id=row.question_id,
                stability=float(row.stability),
                difficulty=float(row.difficulty),
                due_date=row.due_date.replace(tzinfo=UTC)
                if row.due_date.tzinfo is None
                else row.due_date,
                last_review=row.last_review,
                state=row.state,
                reps=row.reps,
                lapses=row.lapses,
                scheduled_days=row.scheduled_days,
                elapsed_days=float(row.elapsed_days),
            )
            irt = {
                "a": float(row.irt_a),
                "b": float(row.irt_b),
                "c": float(row.irt_c),
                "subject_id": row.subject_id,
                "topic_id": row.topic_id,
                "question_text": row.question_text or "",
                "option_a": row.option_a or "",
                "option_b": row.option_b or "",
                "option_c": row.option_c or "",
                "option_d": row.option_d or "",
            }
            items.append((state, irt))

        return items

    async def get_item_state(self, user_id: str, question_id: str) -> FSRSState | None:
        """Tek bir user-item çiftinin FSRS state'ini getir."""
        result = await self.db.execute(
            _FETCH_ITEM_SQL, {"uid": user_id, "qid": question_id}
        )
        row = result.fetchone()
        if not row:
            return None

        return FSRSState(
            user_id=user_id,
            question_id=question_id,
            stability=float(row.stability),
            difficulty=float(row.difficulty),
            due_date=row.due_date,
            last_review=row.last_review,
            state=row.state,
            reps=row.reps,
            lapses=row.lapses,
            scheduled_days=row.scheduled_days,
            elapsed_days=float(row.elapsed_days),
        )

    async def get_due_count(self, user_id: str) -> int:
        """Vadesi gelen kart sayısı (Redis cache key: due_count:{user_id})."""
        result = await self.db.execute(_DUE_COUNT_SQL, {"uid": user_id})
        row = result.fetchone()
        return int(row.cnt) if row else 0

    # ── Yazma ────────────────────────────────────────────────────

    async def apply_review(
        self,
        user_id: str,
        question_id: str,
        is_correct: bool,
        response_ms: int | None = None,
        item_b: float | None = None,
    ) -> FSRSResult:
        """
        Tek yanıt için FSRS güncelleme — anlık DB yazımı.
        CAT oturumu dışı (standalone review) için kullanılır.
        """
        state = await self.get_item_state(user_id, question_id)

        if state is None:
            # İlk kez görülen soru
            state = FSRSState(user_id=user_id, question_id=question_id)

        puan = answer_to_fsrs_rating(is_correct, response_ms, item_b=item_b)
        result = fsrs_update(state, puan)

        await self._write_state(result.new_state)
        await self.db.commit()
        return result

    async def apply_batch_reviews(
        self,
        reviews: list[
            dict
        ],  # [{user_id, question_id, is_correct, response_ms, item_b}]
    ) -> int:
        """
        Toplu FSRS güncelleme — CAT oturumu bitişinde çağrılır.
        Her review için ayrı DB call yapmak yerine pipeline.

        Döndürür: başarıyla güncellenen kayıt sayısı
        """
        written = 0
        skipped_ids: list[str] = []
        for r in reviews:
            try:
                state = await self.get_item_state(r["user_id"], r["question_id"])
                if state is None:
                    state = FSRSState(
                        user_id=r["user_id"], question_id=r["question_id"]
                    )
                puan = answer_to_fsrs_rating(
                    r["is_correct"],
                    r.get("response_ms"),
                    item_b=r.get("item_b"),
                )
                result = fsrs_update(state, puan)
                await self._write_state(result.new_state)
                written += 1
            except Exception as exc:
                # Tek hata tüm batch'i durdurmasın
                skipped_ids.append(str(r.get("question_id", "?")))
                logger.error(
                    "FSRS yazım hatası q=%s: %s", r.get("question_id", "?"), exc
                )

        if skipped_ids:
            logger.error(
                "FSRS batch: %d soru atlandı: %s", len(skipped_ids), skipped_ids
            )
        if written:
            await self.db.commit()
        return written

    async def _write_state(self, state: FSRSState) -> None:
        """FSRSState'i DB'ye yaz (UPSERT)."""
        await self.db.execute(
            _UPSERT_FSRS_SQL,
            {
                "user_id": state.user_id,
                "question_id": state.question_id,
                "stability": round(state.stability, 4),
                "difficulty": round(state.difficulty, 2),
                "due_date": state.due_date,
                "last_review": state.last_review,
                "state": state.state,
                "reps": state.reps,
                "lapses": state.lapses,
                "scheduled_days": state.scheduled_days,
                "elapsed_days": round(state.elapsed_days, 2),
            },
        )


# ─── CAT+FSRS Birleşik Soru Seçici ───────────────────────────────────────────


def build_combined_candidate_list(
    due_items: list[tuple[FSRSState, dict]],
    new_candidates: list[dict],  # IRT parametreleri olan sorular
    current_theta: float,
    answered_ids: set,
    max_due_per_session: int = 5,
) -> list[tuple[str, float]]:
    """
    CAT + FSRS öncelik listesi oluştur.

    Sıralama mantığı:
      1. Vadesi geçmiş kartlar (urgency > 0): combined_priority_score ile
      2. Yeni/vadesi gelmemiş sorular: IRT information gain ile

    Argümanlar:
      due_items:           FSRS.get_due_items() sonucu
      new_candidates:      DB'den gelen yeni soru havuzu
      current_theta:       öğrencinin mevcut θ tahmini
      answered_ids:        bu oturumda yanıtlananlar
      max_due_per_session: oturum başına max kaç FSRS tekrar

    Döndürür: [(question_id, priority_score), ...] azalan sırada
    """
    from .irt_engine import fisher_information  # app/services/ içinde aynı dizin

    scored: list[tuple[str, float]] = []

    # 1. FSRS due kartları (oturum limiti ile)
    due_count = 0
    for fsrs_state, irt in due_items:
        qid = fsrs_state.question_id
        if qid in answered_ids:
            continue
        if due_count >= max_due_per_session:
            break

        info = float(fisher_information(current_theta, irt["a"], irt["b"], irt["c"]))
        score = combined_priority_score(fsrs_state, info)
        scored.append((qid, score))
        due_count += 1

    # 2. Yeni sorular (IRT information gain)
    for cand in new_candidates:
        qid = str(cand.get("question_id") or cand.get("id", ""))
        if not qid or qid in answered_ids:
            continue
        if any(q == qid for q, _ in scored):
            continue

        a = float(cand.get("a", cand.get("discrimination", 1.0)))
        b = float(cand.get("b", cand.get("difficulty", 0.0)))
        c = float(cand.get("c", cand.get("guessing", 0.25)))
        info = float(fisher_information(current_theta, a, b, c))
        scored.append((qid, info * 0.40))  # w_irt ağırlığı

    # Azalan önceliğe göre sırala
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
