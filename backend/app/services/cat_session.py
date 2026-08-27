"""
KIRO2 — CAT Session Service
============================
Redis üzerinde stateful CAT oturum yönetimi.

Neden Redis Hash?
  - Tek atomic HGETALL ile tüm state okunur (~1ms)
  - HSET ile tek alan güncellenebilir (partial update)
  - TTL ile otomatik temizlik (1 saat)
  - 500 eş zamanlı oturum × 2KB = sadece 1MB bellek

Key yapısı:
  cat:{session_id}  →  Hash
    user_id          : str (UUID)
    subject_id       : str (UUID)
    theta            : str (float, 4 decimal)
    se               : str (float, 4 decimal)
    answered_ids     : str (JSON list of UUIDs)
    responses        : str (JSON list of 0/1)
    item_params      : str (JSON list of {a,b,c,question_id})
    n_questions      : str (int)
    started_at       : str (ISO datetime)
    state            : str ("active"|"completed"|"abandoned")
    termination_reason: str

Akış:
  start_session()
    → Redis'e yeni state yaz
    → İlk soruyu seç (prior θ=0, SE=1)
    → Soruyu döndür

  submit_answer(session_id, question_id, is_correct)
    → Redis'ten state oku
    → EAP ile θ güncelle
    → Bitiş kontrolü yap
    → Bitmiyorsa: sonraki soruyu seç
    → Redis'e güncellenmiş state yaz
    → Sonucu döndür

  Neden "submit_answer DB'den geçmez"?
    Tüm hesaplama Redis'ten okunan cache'de yapılır.
    Sadece oturum bittiğinde toplu DB yazımı yapılır.
    Bu 150ms → ~20ms latency iyileştirmesi sağlar.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis

from app.services.irt_engine import (
    MAX_ITEMS,
    SE_STOP,
    IRTResult,
    ItemParams,
    eap_update,
    select_next_question,
    should_terminate,
)
from core.quality_gate import safe_for_beta_sql

logger = logging.getLogger(__name__)


def _normalize_subject(s: str) -> str:
    """Normalize Turkish subject name to ASCII-lowercase map key."""
    return (
        s.lower()
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ı", "i")
    )


# ------------------------------------------------------------------
# Session TTL
# ------------------------------------------------------------------

CAT_SESSION_TTL = 3600  # 1 saat (saniye)
THETA_CACHE_TTL = 300  # 5 dakika


# ------------------------------------------------------------------
# State dataclass
# ------------------------------------------------------------------


@dataclass
class CATState:
    """
    Bir CAT oturumunun tam durumu.
    Redis Hash'te JSON olarak saklanır.
    """

    session_id: str
    user_id: str
    subject_id: str
    theta: float = 0.0
    se: float = 1.0
    answered_ids: list[str] = field(default_factory=list)
    responses: list[int] = field(default_factory=list)  # 0|1
    item_params: list[dict] = field(default_factory=list)  # {a,b,c,question_id}
    n_questions: int = 0
    started_at: str = ""
    state: str = "active"  # active|completed|abandoned
    termination_reason: str = ""
    warm_up_done: bool = False  # ilk 3 kolay soru bitti mi
    # Misafir (auth'suz) yerleştirme: user_id gerçek bir users satırı DEĞİL
    # ("guest:<uuid>"). Bu oturumun hiçbir kalıcı tabloya yazılmaması gerekir —
    # FK ihlali ve RLS'li tablolara sahipsiz satır yazımı önlenir.
    is_guest: bool = False
    # SUNUCUNUN SERVİS ETTİĞİ madde. Yanıtın gerçekten bu maddeye ait olduğu
    # doğrulanmazsa istemci hangi sorunun puanlanacağını seçebilir; yanıt
    # doğru/yanlış bilgisini geri verdiği için bu, soru bankasının cevap
    # anahtarını sızdıran bir oracle'a dönüşür.
    pending_question_id: str = ""
    # "Emin değilim" ile atlanan maddeler. θ'ya GİRMEZ (uygulanmamış sayılır)
    # ama madde bütçesinden düşer ve tekrar sunulmaz.
    skipped_ids: list[str] = field(default_factory=list)

    # ------- Yardımcı metodlar -------

    def get_item_params_objects(self) -> list[ItemParams]:
        return [
            ItemParams(
                question_id=p["question_id"],
                a=p.get("a", 1.0),
                b=p.get("b", 0.0),
                c=p.get("c", 0.25),
            )
            for p in self.item_params
        ]

    def is_active(self) -> bool:
        return self.state == "active"

    def to_redis_dict(self) -> dict[str, str]:
        """Redis HSET için string değerleri."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "subject_id": self.subject_id,
            "theta": str(self.theta),
            "se": str(self.se),
            "answered_ids": json.dumps(self.answered_ids),
            "responses": json.dumps(self.responses),
            "item_params": json.dumps(self.item_params),
            "n_questions": str(self.n_questions),
            "started_at": self.started_at,
            "state": self.state,
            "termination_reason": self.termination_reason,
            "warm_up_done": "1" if self.warm_up_done else "0",
            "is_guest": "1" if self.is_guest else "0",
            "pending_question_id": self.pending_question_id,
            "skipped_ids": json.dumps(self.skipped_ids),
        }

    @classmethod
    def from_redis_dict(cls, data: dict[bytes, bytes]) -> CATState:
        """Redis HGETALL çıktısından CATState oluştur."""
        d = {k.decode(): v.decode() for k, v in data.items()}
        return cls(
            session_id=d["session_id"],
            user_id=d["user_id"],
            subject_id=d["subject_id"],
            theta=float(d.get("theta", 0.0)),
            se=float(d.get("se", 1.0)),
            answered_ids=json.loads(d.get("answered_ids", "[]")),
            responses=json.loads(d.get("responses", "[]")),
            item_params=json.loads(d.get("item_params", "[]")),
            n_questions=int(d.get("n_questions", 0)),
            started_at=d.get("started_at", ""),
            state=d.get("state", "active"),
            termination_reason=d.get("termination_reason", ""),
            warm_up_done=d.get("warm_up_done", "0") == "1",
            is_guest=d.get("is_guest", "0") == "1",
            pending_question_id=d.get("pending_question_id", ""),
            skipped_ids=json.loads(d.get("skipped_ids", "[]")),
        )


# ------------------------------------------------------------------
# CATSessionService
# ------------------------------------------------------------------


class CATSessionService:
    """
    CAT oturumlarını Redis üzerinde yöneten servis.

    Kullanım:
      service = CATSessionService(redis_client, db_session)
      result  = await service.start_session(user_id, subject_id)
      result  = await service.submit_answer(session_id, question_id, is_correct=True)
    """

    REDIS_PREFIX = "cat"

    def __init__(self, redis: aioredis.Redis, db):
        self.redis = redis
        self.db = db

    def _key(self, session_id: str) -> str:
        return f"{self.REDIS_PREFIX}:{session_id}"

    # ---- Redis okuma/yazma ----

    async def _read_state(self, session_id: str) -> CATState | None:
        """Redis'ten CATState oku. Yoksa None."""
        data = await self.redis.hgetall(self._key(session_id))
        if not data:
            return None
        return CATState.from_redis_dict(data)

    async def _write_state(self, state: CATState) -> None:
        """CATState'i Redis'e yaz, TTL'yi yenile."""
        key = self._key(state.session_id)
        pipe = self.redis.pipeline()
        pipe.hset(key, mapping=state.to_redis_dict())
        pipe.expire(key, CAT_SESSION_TTL)
        await pipe.execute()

    async def _delete_state(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))

    # ---- Soru havuzu ----

    async def _get_candidate_questions(
        self, subject_id: str, theta: float, warm_up: bool
    ) -> list[ItemParams]:
        """
        Veritabanından uygun soruları çek.

        warm_up=True ise: b < -0.5 olan kolay sorular (P>0.80)
        Aksi halde: ZPD bölgesindeki sorular (b ≈ theta ± 1.5)

        Not: Bu sorgu sonucu kısa süreli önbelleğe alınabilir,
             ama 5K ölçeğinde her seferinde DB'ye gitmek de kabul edilebilir.
        """
        from sqlalchemy import text
        # Question model gerekmez — raw SQL kullanıyoruz

        if warm_up:
            # [KALIBRASYON HAVUZU] Pilot sorulardan sec - daha fazla yanit biriksin
            # Oncelik sirasi:
            #   1. is_calib_pool=TRUE ve kolay (b < 0) → zorunlu ilk temas
            #   2. is_calib_pool=TRUE tumu → havuz doluysa genisle
            #   3. Normal kolay sorular (fallback)
            stmt = text(
                r"""
                SELECT qb.id::text,
                       qs.irt_discrimination AS a,
                       qs.irt_difficulty AS b,
                       qs.irt_guessing AS c
                FROM question_bank qb
                LEFT JOIN question_content qc ON qc.id = qb.id
                LEFT JOIN question_metadata qm ON qm.id = qb.id
                LEFT JOIN question_statistics qs ON qs.id = qb.id
                WHERE LOWER(qm.subject_area) = LOWER(:subject_id)
                  AND qb.is_active = TRUE
                  -- 15 May 2026: Convention v2 — bkz: docs/quality_review_status_convention.md
                  AND qs.quality_review_status IN ('human_verified', 'auto_judged_high')
                  -- Kalite kapısı (core/quality_gate.py) — status-only filtre 34.982 satır
                  -- görüyor, kapı 25.127; aradaki 9.855 demoted/tek-sinyal/bozuk soru
                  -- öğrenciye servis ediliyordu. Status satırı savunma katmanı olarak kalır.
                  AND """  # noqa: S608 (kapı sabiti, kullanıcı girdisi değil)
                + safe_for_beta_sql("qb.id")
                + r"""
                  -- 18 May 2026: Bug #11 fix — IMAGE-REQUIRED soruları HARIÇ
                  -- Vision audit: tüm image'lar options leak içeriyor, text-self-contained dar
                  -- Bug #11 v3: PostgreSQL C locale fix — [şŞ] char class her Türkçe ilk-harf için
                  AND qc.question_text !~* '[şŞ]ekil|[yY]ukarıda|[aA]şağıda|verilen graf|verilen tablo|[tT]abloda|[gG]rafikte|[şŞ]emada|[hH]aritada|[vV]erilenler|aşağıdaki şek|[gG]örsel|[kK]avram harita|[dD]eney düzene|numaraland.* özelli|şekildeki kap|[cC]am boru|[pP]aralelkenar|şek\.|şek |[dD]ik üçgen|[eE]şkenar üçgen|[iI]kizkenar üçgen'
                  AND (
                      -- Oncelik 1: Gercek IRT kalibrasyonu olan calib_pool sorulari
                      (qs.is_calib_pool = TRUE AND qs.is_calibrated = TRUE AND qs.irt_difficulty BETWEEN -1.0 AND 1.0)
                      OR
                      -- Oncelik 2: Kalibreli ama b araligi disinda
                      (qs.is_calib_pool = TRUE AND qs.is_calibrated = TRUE)
                      OR
                      -- Oncelik 3: Kalibrasyon havuzunda ama is_calibrated=FALSE (default parametreler)
                      (qs.is_calib_pool = TRUE)
                      OR
                      -- Son care: kolay normal sorular
                      (qs.irt_difficulty < :b_max)
                  )
                ORDER BY
                    -- is_calibrated=TRUE olanlar her zaman once gelir
                    CASE WHEN qs.is_calibrated = TRUE AND qs.is_calib_pool = TRUE THEN 0
                         WHEN qs.is_calib_pool = TRUE THEN 1
                         ELSE 2 END ASC,
                    RANDOM()
                LIMIT 30
            """
            )
        else:
            # ZPD bolgesi: theta - 1.5 < b < theta + 1.5
            # Kalibrasyon havuzundaki sorulari tercih et
            stmt = text(
                r"""
                SELECT qb.id::text,
                       qs.irt_discrimination AS a,
                       qs.irt_difficulty AS b,
                       qs.irt_guessing AS c
                FROM question_bank qb
                LEFT JOIN question_content qc ON qc.id = qb.id
                LEFT JOIN question_metadata qm ON qm.id = qb.id
                LEFT JOIN question_statistics qs ON qs.id = qb.id
                WHERE LOWER(qm.subject_area) = LOWER(:subject_id)
                  AND qs.irt_difficulty BETWEEN :b_min AND :b_max
                  AND qb.is_active = TRUE
                  -- 15 May 2026: Convention v2 — bkz: docs/quality_review_status_convention.md
                  AND qs.quality_review_status IN ('human_verified', 'auto_judged_high')
                  -- Kalite kapısı (core/quality_gate.py) — status-only filtre 34.982 satır
                  -- görüyor, kapı 25.127; aradaki 9.855 demoted/tek-sinyal/bozuk soru
                  -- öğrenciye servis ediliyordu. Status satırı savunma katmanı olarak kalır.
                  AND """  # noqa: S608 (kapı sabiti, kullanıcı girdisi değil)
                + safe_for_beta_sql("qb.id")
                + r"""
                  -- 18 May 2026: Bug #11 fix — IMAGE-REQUIRED soruları HARIÇ
                  -- Vision audit: tüm image'lar options leak içeriyor, text-self-contained dar
                  -- Bug #11 v3: PostgreSQL C locale fix — [şŞ] char class her Türkçe ilk-harf için
                  AND qc.question_text !~* '[şŞ]ekil|[yY]ukarıda|[aA]şağıda|verilen graf|verilen tablo|[tT]abloda|[gG]rafikte|[şŞ]emada|[hH]aritada|[vV]erilenler|aşağıdaki şek|[gG]örsel|[kK]avram harita|[dD]eney düzene|numaraland.* özelli|şekildeki kap|[cC]am boru|[pP]aralelkenar|şek\.|şek |[dD]ik üçgen|[eE]şkenar üçgen|[iI]kizkenar üçgen'
                ORDER BY
                    -- is_calibrated=TRUE olanlar ZPD icinde de one alinir
                    CASE WHEN qs.is_calibrated = TRUE AND qs.is_calib_pool = TRUE THEN 0
                         WHEN qs.is_calib_pool = TRUE THEN 1
                         ELSE 2 END ASC,
                    RANDOM()
                LIMIT 100
            """
            )

        params = (
            {"subject_id": subject_id, "b_max": max(theta - 1.0, -0.5)}
            if warm_up
            else {
                "subject_id": subject_id,
                "b_min": theta - 1.5,
                "b_max": theta + 1.5,
            }
        )

        result = await self.db.execute(stmt, params)
        rows = result.fetchall()

        return [
            ItemParams(
                question_id=str(row.id),
                a=float(row.a),
                b=float(row.b),
                c=float(row.c),
            )
            for row in rows
        ]

    async def _fetch_question_detail(self, question_id: str) -> dict | None:
        """Soru içeriğini DB'den çek."""
        from sqlalchemy import text

        stmt = text("""
            SELECT qb.id::text,
                   qc.question_text AS stem,
                   CASE
                       WHEN qc.option_e IS NOT NULL AND qc.option_e != ''
                       THEN json_build_object('A', qc.option_a, 'B', qc.option_b,
                                             'C', qc.option_c, 'D', qc.option_d, 'E', qc.option_e)
                       ELSE json_build_object('A', qc.option_a, 'B', qc.option_b,
                                             'C', qc.option_c, 'D', qc.option_d)
                   END AS options,
                   qc.correct_answer AS correct_option,
                   -- COALESCE: cocuk satiri yoksa LEFT JOIN NULL dondurur; asagidaki
                   -- float() cagrilari patlar. Varsayilanlar ORM ile ayni
                   -- (models/question_bank.py:371-373).
                   COALESCE(qs.irt_difficulty, 0.0) AS difficulty,
                   COALESCE(qs.irt_discrimination, 1.0) AS discrimination,
                   COALESCE(qs.irt_guessing, 0.25) AS guessing,
                   qb.primary_topic_id::text AS topic_id,
                   th.name_tr AS konu,
                   qm.subject_area AS subject_id,
                   qc.question_image_url,
                   qc.image_width,
                   qc.image_height,
                   qc.image_ocr_text
            FROM question_bank qb
            LEFT JOIN question_content qc ON qc.id = qb.id
            LEFT JOIN question_metadata qm ON qm.id = qb.id
            LEFT JOIN question_statistics qs ON qs.id = qb.id
            LEFT JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
            WHERE qb.id = :qid AND qb.is_active = TRUE
        """)
        result = await self.db.execute(stmt, {"qid": question_id})
        row = result.fetchone()
        if not row:
            return None
        return {
            "question_id": row.id,
            "stem": row.stem,
            "options": row.options,
            "correct_option": row.correct_option,
            "topic_id": row.topic_id,
            "konu": row.konu,
            "subject_id": row.subject_id,
            "irt": {
                "difficulty": round(float(row.difficulty), 4),
                "discrimination": round(float(row.discrimination), 4),
                "guessing": round(float(row.guessing), 4),
            },
            "question_image_url": row.question_image_url,
            "image_alt_text": row.image_ocr_text[:200] if row.image_ocr_text else None,
            "image_width": row.image_width,
            "image_height": row.image_height,
        }

    # ---- Ana API ----

    async def fetch_question_detail(self, question_id: str) -> dict | None:
        """Soru içeriğinin dışarıya açık okuyucusu (adaptörler için)."""
        return await self._fetch_question_detail(question_id)

    async def start_session(
        self,
        user_id: str,
        subject_id: str,
        placement_theta: float = 0.0,
        *,
        is_guest: bool = False,
    ) -> dict[str, Any]:
        """
        Yeni CAT oturumu başlat.

        1. Önceki aktif oturumu iptal et (aynı kullanıcı + konu)
        2. Yeni CATState oluştur
        3. İlk soruyu seç (warm-up: kolay soru)
        4. Redis'e yaz
        5. Soru + session_id döndür

        Döndürür:
          {
            session_id: str,
            question:   {question_id, stem, options, ...},
            theta:      float,
            se:         float,
            n_questions: 0,
            phase:      "warm_up"
          }
        """
        session_id = str(uuid.uuid4())
        now_iso = datetime.now(UTC).isoformat()

        # KOD GERÇEĞİ FIX (seanslar arası hafıza): kalıcı θ'yı geri oku.
        # _update_theta_cache her cevapta theta:{user}:{subject_id} anahtarına
        # yazıyordu ama okuyanı yoktu -> her yeni seans θ=0'dan başlıyordu.
        # Guest hariç, çağıran varsayılanı (0.0) bıraktıysa son θ'yı prior yap;
        # cache miss / parse hatası -> soğuk başlangıç (bugünküyle aynı).
        if not is_guest and placement_theta == 0.0:
            try:
                _cached_theta = await self.redis.get(f"theta:{user_id}:{subject_id}")
                if _cached_theta is not None:
                    _tv = float(
                        _cached_theta.decode()
                        if isinstance(_cached_theta, bytes)
                        else _cached_theta
                    )
                    if -4.0 <= _tv <= 4.0:
                        placement_theta = _tv
            except Exception:
                placement_theta = 0.0

        # BUG-6 FIX: Önceki aktif oturumu Redis'ten temizle
        prev_key = f"cat:active:{user_id}:{subject_id}"
        prev_session_id = await self.redis.get(prev_key)
        if prev_session_id:
            prev_id = (
                prev_session_id.decode()
                if isinstance(prev_session_id, bytes)
                else prev_session_id
            )
            prev_state = await self._read_state(prev_id)
            if prev_state and prev_state.is_active():
                prev_state.state = "abandoned"
                prev_state.termination_reason = "new_session_started"
                await self._write_state(prev_state)

        state = CATState(
            session_id=session_id,
            user_id=user_id,
            subject_id=subject_id,
            theta=placement_theta,
            se=1.0,
            started_at=now_iso,
            is_guest=is_guest,
        )

        # İlk soru: warm-up (kolay)
        candidates = await self._get_candidate_questions(
            subject_id, placement_theta, warm_up=True
        )

        if not candidates:
            # Warm-up sorusu yoksa normal havuza geç.
            #
            # 19 Agu 2026 (Y4) — BU DAL SESSIZ OLMAMALI. Olculdu: warm_up
            # havuzunun DORT dalinin DORDU de bu veride bos donuyor
            #   - Oncelik 1/2/3 -> `is_calib_pool = TRUE` sarti; canli DB'de
            #     is_calib_pool TRUE=0 / FALSE=36.967
            #   - Son care -> `irt_difficulty < max(theta-1.0, -0.5)`; tum
            #     satirlarda irt_difficulty=0.0 oldugu icin theta=0'da
            #     `0.0 < -0.5` FALSE -> 0 satir
            # Yani "kolay ilk soru" tasarim niyeti fiilen OLU: ogrencinin ilk
            # sorusu rastgele bir ZPD maddesi oluyor. Fallback dogru davranis
            # (oturum yine baslar) ama SESSIZ olmasi kusuru gorunmez kiliyordu.
            # Bu uyari, prior'lar yazilana kadar (Y4 Adim 3) tek sinyaldir.
            logger.warning(
                "CAT warm-up havuzu BOS (ders=%s, theta=%.2f) -> core havuzuna "
                "dusuluyor; 'kolay ilk soru' garantisi YOK. Beklenen sebep: "
                "is_calib_pool=FALSE ve irt_difficulty kalibre edilmemis.",
                subject_id,
                placement_theta,
            )
            candidates = await self._get_candidate_questions(
                subject_id, placement_theta, warm_up=False
            )

        if not candidates:
            raise ValueError(f"Konu {subject_id} için soru bulunamadı")

        first_item = select_next_question(
            theta=state.theta,
            candidates=candidates,
            answered_ids=set(),
            epsilon=0.0,  # ilk soruda exploration yok, en kolay olanı ver
        )

        # BUG-7 FIX: first_item None kontrolü
        if first_item is None:
            raise ValueError(f"Konu {subject_id} için uygun soru seçilemedi")

        question_detail = await self._fetch_question_detail(first_item.question_id)

        # Sunulan maddeyi state'e yaz: yanıtın bu maddeye ait olduğu
        # doğrulanabilsin (cevap-anahtarı oracle'ı önleme).
        state.pending_question_id = first_item.question_id

        await self._write_state(state)
        # Aktif oturum kaydını Redis'e yaz (önceki iptal için)
        await self.redis.setex(prev_key, CAT_SESSION_TTL, session_id)

        return {
            "session_id": session_id,
            "question": question_detail,
            "theta": state.theta,
            "se": state.se,
            "n_questions": 0,
            "phase": "warm_up",
            "is_complete": False,
        }

    async def submit_answer(
        self,
        session_id: str,
        question_id: str,
        is_correct: bool,
        response_ms: int | None = None,
        *,
        max_items: int = MAX_ITEMS,
        se_threshold: float = SE_STOP,
    ) -> dict[str, Any]:
        """
        Yanıtı işle ve bir sonraki soruyu getir.

        TEMEL AKIŞ:
          1. Redis'ten state oku                     (~1ms)
          2. Yanıtı state'e ekle
          3. EAP ile θ ve SE güncelle               (~5ms)
          4. Bitiş kontrolü yap
          5a. Bitmişse: DB'ye oturum yaz, state'i kapat
          5b. Bitmemişse: sonraki soruyu seç        (~10ms)
          6. State'i Redis'e geri yaz               (~1ms)
          7. Sonucu döndür

        Toplam: ~20ms (DB round-trip YOK, sadece Redis)

        Döndürür:
          {
            is_complete:       bool,
            theta:             float,
            se:                float,
            n_questions:       int,
            termination_reason: str | None,
            next_question:     dict | None,
            phase:             str,
            feedback:          dict   # doğru mu, açıklama
          }
        """
        # 1. Redis'ten oku
        state = await self._read_state(session_id)
        if state is None:
            raise ValueError(f"Oturum bulunamadı veya süresi dolmuş: {session_id}")
        if not state.is_active():
            raise ValueError(f"Oturum zaten tamamlanmış: {session_id} ({state.state})")

        # 2. Yanıtı ekle (replay guard — aynı soru iki kez cevaplanamaz)
        if question_id in state.answered_ids:
            raise ValueError(f"Bu soru zaten cevaplanmış: {question_id}")
        state.answered_ids.append(question_id)
        state.responses.append(1 if is_correct else 0)
        state.n_questions += 1

        # Soru parametrelerini item_params'a ekle (EAP için şart)
        q_detail = await self._fetch_question_detail(question_id)
        if q_detail:
            state.item_params.append(
                {
                    "question_id": question_id,
                    "a": q_detail["irt"]["discrimination"],
                    "b": q_detail["irt"]["difficulty"],
                    "c": q_detail["irt"]["guessing"],
                }
            )
        else:
            # Soru bulunamazsa varsayılan IRT parametreleri kullan
            # responses ile item_params eşit uzunlukta kalmalı
            state.item_params.append(
                {
                    "question_id": question_id,
                    "a": 1.0,
                    "b": 0.0,
                    "c": 0.25,
                }
            )

        # 3. EAP güncelle
        irt_result: IRTResult = eap_update(
            responses=state.responses,
            item_params=state.get_item_params_objects(),
        )
        state.theta = irt_result.theta
        state.se = irt_result.se

        # Warm-up tamamlandı mı? (ilk 3 soru)
        if state.n_questions >= 3:
            state.warm_up_done = True

        # 3b/3c. PROGRESSIVE PERSIST — misafir oturumunda TAMAMEN atlanır.
        # Misafirin user_id'si ("guest:<uuid>") gerçek bir users satırı değildir:
        # student_abilities/xp_transactions FK'yı ihlal eder, üstelik bu tablolar
        # FORCE RLS altında olduğu için sahipsiz satır yazımı zaten reddedilir.
        if not state.is_guest:
            # Her cevaptan sonra theta'yı DB'ye yaz — öğrenci oturumu
            # tamamlamasa bile son theta kaydedilir.
            try:
                _SUBJ_MAP = {
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
                _sid = _SUBJ_MAP.get(_normalize_subject(state.subject_id))
                if _sid is not None:
                    from sqlalchemy import text as _txt

                    await self.db.execute(
                        _txt("""
                        INSERT INTO student_abilities (student_id, subject_id, theta, theta_se, updated_at)
                        VALUES (:uid, :sid, :theta, :se, NOW())
                        ON CONFLICT (student_id, subject_id)
                        DO UPDATE SET theta = :theta, theta_se = :se, updated_at = NOW()
                        """),
                        {
                            "uid": state.user_id,
                            "sid": _sid,
                            "theta": round(state.theta, 4),
                            "se": round(state.se, 4),
                        },
                    )
                    await self.db.commit()
            except Exception as e:
                logger.error("CAT theta persist HATASI — theta kaybı riski: %s", e)

            # XP: Doğru 10XP, Yanlış 3XP (katılım ödülü)
            try:
                from sqlalchemy import text as _txt2

                _xp = 10 if is_correct else 3
                # 1) xp_transactions INSERT (gamification endpoint bunu okur)
                await self.db.execute(
                    _txt2("""INSERT INTO xp_transactions (student_id, amount, source, created_at)
                             VALUES (:uid, :xp, 'cat', NOW())"""),
                    {"uid": state.user_id, "xp": _xp},
                )
                # 2) users.total_xp UPDATE (dashboard bunu okur)
                await self.db.execute(
                    _txt2("UPDATE users SET total_xp = total_xp + :xp WHERE id = :uid"),
                    {"uid": state.user_id, "xp": _xp},
                )
                await self.db.commit()
            except Exception as e:
                logger.warning("CAT XP persist hatası: %s", e)

        # 4. Bitiş kontrolü
        # Bütçe = cevaplanan + atlanan (omit de madde sunumudur).
        terminate, reason = should_terminate(
            state.se,
            state.n_questions + len(state.skipped_ids),
            se_threshold=se_threshold,
            max_items=max_items,
        )

        if terminate:
            # 5a. Oturumu kapat
            state.state = "completed"
            state.termination_reason = reason
            state.pending_question_id = ""
            await self._write_state(state)

            # DB'ye toplu kayıt (async, non-blocking tercih edilir)
            await self._persist_session_to_db(state)

            # θ cache'ini güncelle
            await self._update_theta_cache(state)

            return {
                "is_complete": True,
                "theta": state.theta,
                "se": state.se,
                "n_questions": state.n_questions,
                "termination_reason": reason,
                "next_question": None,
                "phase": "completed",
                "feedback": {
                    "is_correct": is_correct,
                    "correct_option": q_detail.get("correct_option")
                    if q_detail
                    else None,
                },
                "plan_refresh_needed": True,  # Frontend bunu gorünce /daily-plan yeniler
            }

        # 5b. Sonraki soruyu seç
        phase = "warm_up" if not state.warm_up_done else "core"
        candidates = await self._get_candidate_questions(
            state.subject_id,
            state.theta,
            warm_up=(not state.warm_up_done),
        )

        next_item = select_next_question(
            theta=state.theta,
            candidates=candidates,
            answered_ids=set(state.answered_ids),
            epsilon=0.20,
        )

        if next_item is None:
            # Havuz tükendi → oturumu bitir
            state.state = "completed"
            state.termination_reason = "pool_exhausted"
            state.pending_question_id = ""
            await self._write_state(state)
            await self._persist_session_to_db(state)
            return {
                "is_complete": True,
                "theta": state.theta,
                "se": state.se,
                "n_questions": state.n_questions,
                "termination_reason": "pool_exhausted",
                "next_question": None,
                "phase": "completed",
                "feedback": {
                    "is_correct": is_correct,
                    "correct_option": q_detail.get("correct_option")
                    if q_detail
                    else None,
                },
            }

        next_question_detail = await self._fetch_question_detail(next_item.question_id)
        state.pending_question_id = next_item.question_id

        # 6. State'i Redis'e geri yaz
        await self._write_state(state)

        return {
            "is_complete": False,
            "theta": state.theta,
            "se": state.se,
            "n_questions": state.n_questions,
            "termination_reason": None,
            "next_question": next_question_detail,
            "phase": phase,
            "feedback": {
                "is_correct": is_correct,
                "correct_option": q_detail.get("correct_option") if q_detail else None,
            },
        }

    async def skip_question(
        self,
        session_id: str,
        question_id: str,
        *,
        max_items: int = MAX_ITEMS,
    ) -> dict[str, Any]:
        """
        Maddeyi ATLA ("Emin değilim") — omit UYGULANMAMIŞ sayılır.

        Omit'i yanlış (0) kodlamak dürüst belirsizliği kör tahminden ağır
        cezalandırır: θ_true=+1.0 olan öğrenci 12 maddenin 6'sında omit derse
        θ̂=-1.04 çıkar, kör tahmin etseydi -0.56 olurdu. IRT'de omit'in doğru
        muamelesi "bu madde uygulanmadı"dır; YKS'de de boş bırakmanın maliyeti
        sıfırdır.

        Bu yüzden madde:
          - responses/item_params'a GİRMEZ (θ ve SE değişmez),
          - answered_ids'e girer (tekrar sunulmaz),
          - skipped_ids'e girer ve madde BÜTÇESİNDEN düşer (test sonsuza gitmez).
        """
        state = await self._read_state(session_id)
        if state is None:
            raise ValueError(f"Oturum bulunamadı veya süresi dolmuş: {session_id}")
        if not state.is_active():
            raise ValueError(f"Oturum zaten tamamlanmış: {session_id} ({state.state})")
        if question_id in state.answered_ids:
            raise ValueError(f"Bu soru zaten işlendi: {question_id}")

        state.answered_ids.append(question_id)
        state.skipped_ids.append(question_id)

        sunulan = state.n_questions + len(state.skipped_ids)
        if sunulan >= max_items:
            state.state = "completed"
            state.termination_reason = "max_questions"
            state.pending_question_id = ""
            await self._write_state(state)
            await self._persist_session_to_db(state)
            return {
                "is_complete": True,
                "theta": state.theta,
                "se": state.se,
                "n_questions": state.n_questions,
                "termination_reason": "max_questions",
                "next_question": None,
                "phase": "completed",
            }

        candidates = await self._get_candidate_questions(
            state.subject_id, state.theta, warm_up=(not state.warm_up_done)
        )
        next_item = select_next_question(
            theta=state.theta,
            candidates=candidates,
            answered_ids=set(state.answered_ids),
            epsilon=0.20,
        )
        if next_item is None:
            state.state = "completed"
            state.termination_reason = "pool_exhausted"
            state.pending_question_id = ""
            await self._write_state(state)
            await self._persist_session_to_db(state)
            return {
                "is_complete": True,
                "theta": state.theta,
                "se": state.se,
                "n_questions": state.n_questions,
                "termination_reason": "pool_exhausted",
                "next_question": None,
                "phase": "completed",
            }

        next_detail = await self._fetch_question_detail(next_item.question_id)
        state.pending_question_id = next_item.question_id
        await self._write_state(state)

        return {
            "is_complete": False,
            "theta": state.theta,
            "se": state.se,
            "n_questions": state.n_questions,
            "termination_reason": None,
            "next_question": next_detail,
            "phase": "warm_up" if not state.warm_up_done else "core",
        }

    async def get_session_state(self, session_id: str) -> CATState | None:
        """Mevcut oturum durumunu getir."""
        return await self._read_state(session_id)

    async def abandon_session(self, session_id: str) -> None:
        """Oturumu iptal et."""
        state = await self._read_state(session_id)
        if state and state.is_active():
            state.state = "abandoned"
            state.termination_reason = "user_abandoned"
            await self._write_state(state)
            await self._persist_session_to_db(state)

    # ---- DB Kalıcılık ----

    async def _persist_session_to_db(self, state: CATState) -> None:
        """
        Tamamlanan oturumu PostgreSQL'e yaz.

        Bu fonksiyon sadece oturum bittiğinde çağrılır.
        Her yanıtta DB yazımı yapmak yerine,
        sadece son durumu toplu olarak kaydediyoruz.

        Misafir oturumu hiçbir tabloya yazılmaz — sahibi olmayan bir user_id ile
        kiro2_cat_sessions/learning_events/user_theta satırı üretmek FK ve RLS
        ihlalidir; yerleştirme sonucu yalnız Redis'te (TTL'li) yaşar.
        """
        if state.is_guest:
            logger.debug(
                "Misafir CAT oturumu — DB persist atlandı: %s", state.session_id
            )
            return

        from sqlalchemy import text

        stmt = text("""
            INSERT INTO kiro2_cat_sessions (
                id, user_id, subject_id,
                theta_final, se_final,
                n_questions, started_at, completed_at,
                termination_reason, state
            ) VALUES (
                :session_id, :user_id, :subject_id,
                :theta, :se,
                :n_questions, :started_at, NOW(),
                :termination_reason, :state
            )
            ON CONFLICT (id) DO UPDATE SET
                theta_final   = EXCLUDED.theta_final,
                se_final      = EXCLUDED.se_final,
                n_questions   = EXCLUDED.n_questions,
                completed_at  = NOW(),
                state         = EXCLUDED.state
        """)
        from datetime import datetime

        started_dt = (
            datetime.fromisoformat(state.started_at)
            if isinstance(state.started_at, str) and state.started_at
            else datetime.now(UTC)
        )
        await self.db.execute(
            stmt,
            {
                "session_id": state.session_id,
                "user_id": state.user_id,
                "subject_id": state.subject_id,
                "theta": state.theta,
                "se": state.se,
                "n_questions": state.n_questions,
                "started_at": started_dt,
                "termination_reason": state.termination_reason,
                "state": state.state,
            },
        )

        # Her yanıtı learning_events'e yaz
        for i, (q_id, resp) in enumerate(
            zip([_q for _q in state.answered_ids if _q not in set(state.skipped_ids)], state.responses, strict=False)
        ):
            _params_raw = state.item_params[i] if i < len(state.item_params) else {}
            event_stmt = text("""
                INSERT INTO kiro2_learning_events (
                    occurred_at, user_id, question_id,
                    event_type, is_correct, session_id
                ) VALUES (
                    NOW(), :user_id, :question_id,
                    'cat_answer', :is_correct, :session_id
                )
            """)
            await self.db.execute(
                event_stmt,
                {
                    "user_id": state.user_id,
                    "question_id": q_id,
                    "is_correct": bool(resp),
                    "session_id": state.session_id,
                },
            )

        # ── student_abilities UPSERT ──────────────────────────────────
        # CAT biter bitmez IRT θ tahminini student_abilities tablosuna yaz.
        # LearningPathOrchestrator bu tabloyu okur — eksik olursa ZPD hesaplanamaz.
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
        subj_id = _SUBJECT_ID_MAP.get(_normalize_subject(state.subject_id))
        if subj_id is not None:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            from models.gamification import StudentAbility

            stmt = (
                pg_insert(StudentAbility)
                .values(
                    student_id=state.user_id,
                    subject_id=subj_id,
                    theta=round(state.theta, 4),
                    theta_se=round(state.se, 4),
                )
                .on_conflict_do_update(
                    index_elements=["student_id", "subject_id"],
                    set_={
                        "theta": round(state.theta, 4),
                        "theta_se": round(state.se, 4),
                    },
                )
            )
            await self.db.execute(stmt)
        else:
            import logging

            logging.getLogger("kiro2.cat").warning(
                f"CAT UPSERT: bilinmeyen subject_id '{state.subject_id}'"
            )

        # ── user_theta UPSERT (IRT θ global store) ───────────────────
        # DAGService ve ZPD bu tablodan okur. subject_area string key.
        await self.db.execute(
            text("""
                INSERT INTO user_theta
                    (user_id, subject_area, theta_estimate, theta_se, response_count)
                VALUES (:uid, :subj, :theta, :se, :resp)
                ON CONFLICT (user_id, subject_area) DO UPDATE SET
                    theta_estimate = EXCLUDED.theta_estimate,
                    theta_se       = EXCLUDED.theta_se,
                    response_count = EXCLUDED.response_count,
                    last_updated   = NOW()
            """),
            {
                "uid": state.user_id,
                "subj": state.subject_id,
                "theta": round(state.theta, 4),
                "se": round(state.se, 4),
                "resp": len(getattr(state, "responses", [])),
            },
        )

        await self.db.commit()

        # BUG-12 FIX: FSRS user_item_fsrs tablosunu güncelle
        # learning_events yazıldıktan sonra toplu FSRS güncellemesi yap
        try:
            from app.services.fsrs_service import FSRSService

            fsrs_svc = FSRSService(self.db)
            reviews = [
                {
                    "user_id": state.user_id,
                    "question_id": q_id,
                    "is_correct": bool(resp),
                    "response_ms": None,
                    "item_b": state.item_params[i].get("b")
                    if i < len(state.item_params)
                    else None,
                }
                for i, (q_id, resp) in enumerate(
                    zip([_q for _q in state.answered_ids if _q not in set(state.skipped_ids)], state.responses, strict=False)
                )
            ]
            await fsrs_svc.apply_batch_reviews(reviews)
        except Exception as exc:
            import logging

            logging.getLogger("kiro2.cat").warning(
                f"FSRS batch update başarısız (non-critical): {exc}"
            )

        # Dashboard cache invalidation — CAT tamamlandığında eski cache'i sil
        try:
            await self.redis.delete(f"student_dashboard:summary:{state.user_id}")
        except Exception as e:
            logger.warning("Dashboard cache invalidation hatası: %s", e)

        # Streak güncelleme — CAT tamamlandığında bugünü aktif say
        try:
            from sqlalchemy import text as _stxt

            await self.db.execute(
                _stxt("""
                INSERT INTO streaks (user_id, current_streak, largest_streak, last_activity, total_days_active)
                VALUES (:uid, 1, 1, CURRENT_DATE, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    current_streak = CASE
                        WHEN streaks.last_activity = CURRENT_DATE THEN streaks.current_streak
                        WHEN streaks.last_activity = CURRENT_DATE - 1 THEN streaks.current_streak + 1
                        ELSE 1
                    END,
                    largest_streak = GREATEST(streaks.largest_streak, CASE
                        WHEN streaks.last_activity = CURRENT_DATE - 1 THEN streaks.current_streak + 1
                        ELSE streaks.current_streak
                    END),
                    last_activity = CURRENT_DATE,
                    total_days_active = CASE
                        WHEN streaks.last_activity = CURRENT_DATE THEN streaks.total_days_active
                        ELSE streaks.total_days_active + 1
                    END
                """),
                {"uid": state.user_id},
            )

            # Weekly progress güncelleme
            _iso = datetime.now(UTC).isocalendar()
            await self.db.execute(
                _stxt("""
                INSERT INTO weekly_progress (user_id, year, week_number, total_activities, total_time_seconds, streak_days, created_at, updated_at)
                VALUES (:uid, :yr, :wk, 1, :secs, 0, NOW(), NOW())
                ON CONFLICT ON CONSTRAINT uq_weekly_progress DO UPDATE SET
                    total_activities = weekly_progress.total_activities + 1,
                    total_time_seconds = weekly_progress.total_time_seconds + :secs,
                    updated_at = NOW()
                """),
                {
                    "uid": state.user_id,
                    "yr": _iso.year,
                    "wk": _iso.week,
                    "secs": state.n_questions * 15,
                },  # ~15s per question estimate
            )
            await self.db.commit()
        except Exception as e:
            logger.warning("CAT streak/weekly persist hatası: %s", e)

    async def _update_theta_cache(self, state: CATState) -> None:
        """Kullanıcının θ tahminini Redis'e cache'le."""
        key = f"theta:{state.user_id}:{state.subject_id}"
        await self.redis.setex(
            key,
            THETA_CACHE_TTL,
            str(state.theta),
        )
