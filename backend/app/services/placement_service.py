"""
KIRO2 — Placement Test Service
================================
Yeni kullanıcı için hızlı θ kalibrasyonu.

Problem: Yeni kullanıcının θ bilinmiyor.
  - Prior N(0,1) ile başlarsak CAT 12-15 soruda SE<0.35'e ulaşır.
  - Bu kabul edilebilir ama placement test ile 8 soruda ulaşabiliriz.

Neden ayrı bir "placement test" modülü?
  - Standart CAT: epsilon=0.20 (exploration var, çeşitlilik için)
  - Placement CAT: epsilon=0.00, bisection stratejisi (hız için)
  - Kullanıcı UX'i farklı: "Sana uygun seviyeyi buluyoruz" mesajı
  - Tamamlandığında standart CAT oturumlarına geçilir

Bisection stratejisi:
  Sorular [-3, -1.5, 0, +1.5, +3] güçlük basamaklarından seçilir.
  Her yanıt aralığı daraltır:
    Doğru → b_min = mevcut_b
    Yanlış → b_max = mevcut_b
  8 soruda θ ≈ ±0.5 hassasiyete ulaşılır.

Lise türüne göre prior ayarı:
  Anadolu Lisesi  → N(-0.3, 1.0)  (biraz düşük başla)
  Özel Lise       → N(+0.3, 1.0)  (biraz yüksek başla)
  İmam Hatip      → N(-0.2, 1.0)
  Varsayılan      → N(0.0,  1.0)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# ─── Lise türüne göre prior ayarı ────────────────────────────────────────────

SCHOOL_TYPE_PRIOR: dict[str, tuple[float, float]] = {
    "anadolu": (-0.3, 1.0),
    "fen": (0.5, 0.9),
    "ozel": (0.3, 1.0),
    "imam_hatip": (-0.2, 1.0),
    "meslek": (-0.5, 1.0),
    "default": (0.0, 1.0),
}

# Placement test parametreleri
PLACEMENT_MAX_ITEMS = 12
PLACEMENT_SE_STOP = 0.38  # Normal CAT'ten biraz gevşek (hız için)

# Bisection başlangıç güçlük basamakları
DIFFICULTY_STEPS = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]


# ─── Veri yapıları ────────────────────────────────────────────────────────────


def _theta_to_label(theta: float) -> str:
    """θ değerinden seviye etiketi üret."""
    if theta >= 1.5:
        return "İleri"
    if theta >= 0.5:
        return "Orta-İleri"
    if theta >= -0.5:
        return "Orta"
    if theta >= -1.5:
        return "Orta-Temel"
    return "Temel"


@dataclass
class PlacementState:
    """Placement test oturumu durumu (Redis'te cat: prefix ile saklanır)."""

    session_id: str
    user_id: str
    subject_id: str
    school_type: str = "default"
    theta: float = 0.0
    se: float = 1.0
    answered_ids: list[str] = field(default_factory=list)
    responses: list[int] = field(default_factory=list)
    item_params: list[dict] = field(default_factory=list)
    n_questions: int = 0
    b_min: float = -4.0  # bisection alt sınır
    b_max: float = 4.0  # bisection üst sınır
    is_complete: bool = False
    started_at: str = ""

    def to_dict(self) -> dict[str, str]:
        import json

        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "subject_id": self.subject_id,
            "school_type": self.school_type,
            "theta": str(self.theta),
            "se": str(self.se),
            "answered_ids": json.dumps(self.answered_ids),
            "responses": json.dumps(self.responses),
            "item_params": json.dumps(self.item_params),
            "n_questions": str(self.n_questions),
            "b_min": str(self.b_min),
            "b_max": str(self.b_max),
            "is_complete": "1" if self.is_complete else "0",
            "started_at": self.started_at,
        }

    @classmethod
    def from_dict(cls, d: dict[bytes, bytes]) -> PlacementState:
        import json

        s = {k.decode(): v.decode() for k, v in d.items()}
        return cls(
            session_id=s["session_id"],
            user_id=s["user_id"],
            subject_id=s["subject_id"],
            school_type=s.get("school_type", "default"),
            theta=float(s.get("theta", 0.0)),
            se=float(s.get("se", 1.0)),
            answered_ids=json.loads(s.get("answered_ids", "[]")),
            responses=json.loads(s.get("responses", "[]")),
            item_params=json.loads(s.get("item_params", "[]")),
            n_questions=int(s.get("n_questions", 0)),
            b_min=float(s.get("b_min", -4.0)),
            b_max=float(s.get("b_max", 4.0)),
            is_complete=s.get("is_complete", "0") == "1",
            started_at=s.get("started_at", ""),
        )


@dataclass
class PlacementResult:
    """Placement test sonucu."""

    theta: float
    se: float
    n_questions: int
    school_type: str
    subject_id: str
    confidence: str  # "high" | "medium" | "low"

    @property
    def level_label(self) -> str:
        """Öğrenciye gösterilen seviye etiketi."""
        if self.theta >= 1.5:
            return "İleri"
        if self.theta >= 0.5:
            return "Orta-İleri"
        if self.theta >= -0.5:
            return "Orta"
        if self.theta >= -1.5:
            return "Orta-Temel"
        return "Temel"

    @property
    def suggested_start_difficulty(self) -> float:
        """CAT için başlangıç güçlük önerisi."""
        return round(self.theta, 1)


# ─── Bisection Soru Seçici ────────────────────────────────────────────────────


def _bisection_target_b(b_min: float, b_max: float) -> float:
    """Bisection ortası — bir sonraki sorunun hedef güçlüğü."""
    return (b_min + b_max) / 2.0


def select_placement_question(
    state: PlacementState,
    candidates: list[dict],  # {question_id, a, b, c}
) -> dict | None:
    """
    Placement için soru seç: bisection + maximum Fisher Information.

    1. Hedef güçlük = (b_min + b_max) / 2
    2. Hedef güçlüğe en yakın soruları bul (±0.5 pencere)
    3. Bu pencerede en yüksek Fisher Information'lı soruyu döndür
    4. Pencerede soru yoksa pencereyi genişlet
    """
    from app.services.irt_engine import fisher_information

    answered = set(state.answered_ids)
    pool = [c for c in candidates if c.get("question_id", c.get("id")) not in answered]
    if not pool:
        return None

    target_b = _bisection_target_b(state.b_min, state.b_max)

    # Pencere içindeki sorular
    for window in [0.5, 1.0, 1.5, 4.0]:  # dardan genişe
        window_pool = [
            q
            for q in pool
            if abs(float(q.get("b", q.get("difficulty", 0.0))) - target_b) <= window
        ]
        if window_pool:
            break
    else:
        window_pool = pool

    # En yüksek Fisher Information
    best = max(
        window_pool,
        key=lambda q: float(
            fisher_information(
                state.theta,
                float(q.get("a", q.get("discrimination", 1.0))),
                float(q.get("b", q.get("difficulty", 0.0))),
                float(q.get("c", q.get("guessing", 0.25))),
            )
        ),
    )
    return best


def update_bisection_bounds(state: PlacementState, is_correct: bool) -> None:
    """Yanıt sonucu bisection sınırlarını güncelle."""
    if not state.item_params:
        return
    last_b = float(state.item_params[-1].get("b", 0.0))
    if is_correct:
        state.b_min = max(state.b_min, last_b)
    else:
        state.b_max = min(state.b_max, last_b)


# ─── Placement Test Service ───────────────────────────────────────────────────


class PlacementTestService:
    """
    Placement test yönetimi.
    CATSessionService'in sadeleştirilmiş versiyonu —
    placement tamamlandığında CATSessionService'e aktarım yapılır.
    """

    REDIS_PREFIX = "placement"
    TTL = 7200  # 2 saat

    def __init__(self, db, redis):
        self.db = db
        self.redis = redis
        # Redis None ise direkt bağlantı kur (fallback)
        if self.redis is None:
            try:
                import os

                import redis.asyncio as _aioredis

                _url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.redis = _aioredis.from_url(_url, decode_responses=False)
            except Exception as e:
                logger.warning("Redis bağlantısı başarısız (placement): %s", e)

    def _key(self, sid: str) -> str:
        return f"{self.REDIS_PREFIX}:{sid}"

    async def _read(self, sid: str) -> PlacementState | None:
        data = await self.redis.hgetall(self._key(sid))
        if not data:
            return None
        return PlacementState.from_dict(data)

    async def _write(self, state: PlacementState) -> None:
        pipe = self.redis.pipeline()
        pipe.hset(self._key(state.session_id), mapping=state.to_dict())
        pipe.expire(self._key(state.session_id), self.TTL)
        await pipe.execute()

    async def _get_candidates(self, subject_id: str, b_center: float) -> list[dict]:
        """Tüm güçlük seviyelerinden örnek sorular getir (placement için geniş havuz). v2-case-fix"""
        from sqlalchemy import text

        result = await self.db.execute(
            text("""
            SELECT
                id::text                AS question_id,
                question_text,
                option_a,
                option_b,
                option_c,
                option_d,
                irt_discrimination      AS a,
                irt_difficulty          AS b,
                irt_guessing            AS c,
                subject_area            AS subject_id,
                primary_topic_id        AS topic_id
            FROM question_bank
            WHERE LOWER(subject_area) = LOWER(:sid)
              AND is_active = TRUE
              -- 15 May 2026: Convention v2 — eski 'approved' (hardcoded literal,
              -- %87 hatalı) yasak. Sadece gerçek manuel onay (human_verified)
              -- veya LLM-as-judge yüksek güven (auto_judged_high) kabul.
              -- Bkz: docs/quality_review_status_convention.md
              AND quality_review_status IN ('human_verified', 'auto_judged_high')
              -- 18 May 2026: Bug #11 fix — IMAGE-REQUIRED soruları HARIÇ.
              -- Vision audit (10/10 sample) tüm question_image_url'lerin
              -- options leak içerdiğini ortaya koydu. Geçici çözüm: text-self-contained
              -- sorulara dar (image olmadan çözülebilen).
              AND question_text !~* 'şekil|yukarıda|aşağıda|verilen graf|verilen tablo|tabloda|grafikte|şemada|haritada|verilenler|aşağıdaki şek'
            ORDER BY RANDOM()
            LIMIT 80
        """),
            {"sid": subject_id},
        )
        return [dict(r._mapping) for r in result.fetchall()]

    async def start(
        self,
        user_id: str,
        subject_id: str,
        school_type: str = "default",
    ) -> dict[str, Any]:
        """
        Placement test başlat.

        1. Okul türüne göre prior ayarla
        2. Orta güçlükte ilk soruyu seç (b ≈ 0)
        3. Redis'e state yaz
        4. İlk soru + session_id döndür
        """
        # subject_id normalize: DB büyük harf kullanıyor (MATEMATIK, TURKCE...)
        subject_id = subject_id.upper()

        prior_mean, prior_sd = SCHOOL_TYPE_PRIOR.get(
            school_type.lower(), SCHOOL_TYPE_PRIOR["default"]
        )

        session_id = str(uuid.uuid4())
        state = PlacementState(
            session_id=session_id,
            user_id=user_id,
            subject_id=subject_id,
            school_type=school_type,
            theta=prior_mean,
            se=prior_sd,
            started_at=datetime.now(UTC).isoformat(),
        )

        candidates = await self._get_candidates(subject_id, b_center=prior_mean)
        if not candidates:
            raise ValueError(f"Konu {subject_id} için placement sorusu bulunamadı")

        first_q = select_placement_question(state, candidates)
        if first_q is None:
            raise ValueError("İlk placement sorusu seçilemedi")

        await self._write(state)

        # correct_answer sızdırma — CAT ile aynı format (stem/options)
        question_safe = {
            "question_id": first_q.get("question_id"),
            "stem": first_q.get("question_text", ""),
            "options": {
                "A": first_q.get("option_a", ""),
                "B": first_q.get("option_b", ""),
                "C": first_q.get("option_c", ""),
                "D": first_q.get("option_d", ""),
            },
            "topic_id": first_q.get("topic_id", ""),
            "subject_id": first_q.get("subject_id", ""),
        }

        return {
            "session_id": session_id,
            "question": question_safe,
            "progress": {"current": 0, "max": PLACEMENT_MAX_ITEMS},
            "level_hint": _theta_to_label(state.theta),
            "is_complete": False,
        }

    async def answer(
        self,
        session_id: str,
        question_id: str,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Yanıtı işle:
          1. state oku
          2. bisection sınırlarını güncelle
          3. EAP θ güncelle
          4. Bitiş kontrolü
          5. Bitmemişse sonraki soruyu seç
          6. State kaydet
        """
        state = await self._read(session_id)
        if state is None:
            raise ValueError("Placement oturumu bulunamadı")
        if state.is_complete:
            raise ValueError("Placement oturumu tamamlanmış")

        # Soru parametrelerini al
        from sqlalchemy import text

        row = await self.db.execute(
            text("""
            SELECT irt_discrimination AS a, irt_difficulty AS b, irt_guessing AS c
            FROM question_bank WHERE id = :qid
        """),
            {"qid": question_id},
        )
        q_row = row.fetchone()
        item_b = float(q_row.b) if q_row else 0.0
        item_a = float(q_row.a) if q_row else 1.0
        item_c = float(q_row.c) if q_row else 0.25

        # State güncelle
        state.answered_ids.append(question_id)
        state.responses.append(1 if is_correct else 0)
        state.item_params.append(
            {"question_id": question_id, "a": item_a, "b": item_b, "c": item_c}
        )
        state.n_questions += 1

        # Bisection sınırlarını güncelle
        update_bisection_bounds(state, is_correct)

        # EAP θ güncelle
        from app.services.irt_engine import ItemParams, eap_update

        prior_mean, prior_sd = SCHOOL_TYPE_PRIOR.get(
            state.school_type.lower(), SCHOOL_TYPE_PRIOR["default"]
        )
        item_params_objs = [
            ItemParams(p["question_id"], p["a"], p["b"], p["c"])
            for p in state.item_params
        ]
        irt_result = eap_update(
            state.responses, item_params_objs, prior_mean=prior_mean, prior_sd=prior_sd
        )
        state.theta = irt_result.theta
        state.se = irt_result.se

        # Bitiş kontrolü
        done = state.se <= PLACEMENT_SE_STOP or state.n_questions >= PLACEMENT_MAX_ITEMS

        if done:
            state.is_complete = True
            await self._write(state)
            result = self._build_result(state)
            # θ'yı CAT için cache'e yaz
            await self.redis.setex(
                f"theta:{state.user_id}:{state.subject_id}", 300, str(state.theta)
            )
            return {
                "is_complete": True,
                "result": result.__dict__,
                "next_question": None,
                "progress": {"current": state.n_questions, "max": PLACEMENT_MAX_ITEMS},
            }

        # Sonraki soruyu seç
        candidates = await self._get_candidates(state.subject_id, b_center=state.theta)
        next_q = select_placement_question(state, candidates)
        if next_q is None:
            state.is_complete = True

        await self._write(state)

        next_q_safe = None
        if next_q:
            next_q_safe = {
                "question_id": next_q.get("question_id"),
                "stem": next_q.get("question_text", ""),
                "options": {
                    "A": next_q.get("option_a", ""),
                    "B": next_q.get("option_b", ""),
                    "C": next_q.get("option_c", ""),
                    "D": next_q.get("option_d", ""),
                },
                "topic_id": next_q.get("topic_id", ""),
                "subject_id": next_q.get("subject_id", ""),
            }

        return {
            "is_complete": state.is_complete,
            "result": self._build_result(state).__dict__ if state.is_complete else None,
            "next_question": next_q_safe,
            "progress": {"current": state.n_questions, "max": PLACEMENT_MAX_ITEMS},
            "theta": state.theta,
            "se": state.se,
        }

    def _build_result(self, state: PlacementState) -> PlacementResult:
        confidence = (
            "high" if state.se <= 0.30 else "medium" if state.se <= 0.38 else "low"
        )
        return PlacementResult(
            theta=state.theta,
            se=state.se,
            n_questions=state.n_questions,
            school_type=state.school_type,
            subject_id=state.subject_id,
            confidence=confidence,
        )

    async def get_state(self, session_id: str) -> PlacementState | None:
        return await self._read(session_id)
