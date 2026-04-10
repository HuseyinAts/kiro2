"""
KIRO2 — DAG Service
====================
DB'den önkoşul grafiğini yükler, Redis'te önbelleğe alır,
CAT motoru ile entegre çalışır.

Kritik tasarım kararları:
  1. DAG uygulama başlangıcında memory'ye yüklenir (startup cache)
     → Her istekte DB sorgusu yapılmaz
  2. Konu güncellendiğinde Redis cache temizlenir
  3. CAT soru seçiminden ÖNCE mastery kontrolü yapılır
     → Önkoşul yok → CAT'e geç
     → HARD önkoşul var → öğrenciyi önkoşul konusuna yönlendir
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dag_engine import (
    LearningPath,
    MasteryCheck,
    PrereqType,
    PrerequisiteDAG,
    build_yks_dag,
    compute_mastery_from_theta,
)

logger = logging.getLogger("kiro2.dag")

# Redis cache key — 6 saat TTL (DAG nadiren değişir)
DAG_CACHE_TTL = 21600
MASTERY_CACHE_TTL = 300  # 5 dakika


class DAGService:
    """
    DAG yükleme, mastery hesaplama, CAT entegrasyon servisi.
    """

    def __init__(self, db: AsyncSession, redis=None):
        self.db = db
        self.redis = redis
        self._dag: PrerequisiteDAG | None = None

    # ── DAG Yükleme ───────────────────────────────────────────────

    async def get_dag(self) -> PrerequisiteDAG:
        """
        DAG'ı döndür. Sırasıyla:
          1. Memory cache (en hızlı)
          2. Redis cache
          3. DB'den yükle
          4. YKS built-in fallback (DB boşsa)
        """
        if self._dag is not None:
            return self._dag

        # Redis cache
        if self.redis:
            cached = await self.redis.get("dag:yks")
            if cached:
                self._dag = self._deserialize_dag(cached)
                return self._dag

        # DB'den yükle
        dag = await self._load_from_db()
        if dag and dag.node_count > 0:
            self._dag = dag
        else:
            # Fallback: built-in YKS DAG
            logger.warning("DB'de DAG verisi yok — built-in YKS DAG kullanılıyor")
            self._dag = build_yks_dag()

        # Redis'e yaz
        if self.redis:
            await self.redis.setex(
                "dag:yks",
                DAG_CACHE_TTL,
                self._serialize_dag(self._dag),
            )

        return self._dag

    async def _load_from_db(self) -> PrerequisiteDAG:
        """topic_prerequisites tablosundan DAG yükle."""
        dag = PrerequisiteDAG()

        # Konuları yükle
        topics_result = await self.db.execute(
            text("""
            SELECT id::text, name_tr AS name, COALESCE(subject_area, '') AS subject_id
            FROM topic_hierarchy
            WHERE is_active = TRUE
            ORDER BY name_tr
        """)
        )
        topic_rows = topics_result.fetchall()
        if len(topic_rows) > 5000:
            logger.warning(
                "topic_hierarchy %d satır — beklenenden fazla", len(topic_rows)
            )
        for row in topic_rows:
            dag.add_topic(str(row.id), row.name, str(row.subject_id))

        if dag.node_count == 0:
            return dag

        # Önkoşulları yükle
        prereqs_result = await self.db.execute(
            text("""
            SELECT
                topic_id,
                prereq_id,
                prereq_type,
                strength
            FROM topic_prerequisites
            WHERE is_active = TRUE
            ORDER BY topic_id, prereq_id
        """)
        )
        for row in prereqs_result.fetchall():
            try:
                ptype = PrereqType(row.prereq_type or "hard")
                dag.add_prereq(
                    str(row.topic_id),
                    str(row.prereq_id),
                    ptype,
                    float(row.strength or 1.0),
                )
            except (ValueError, KeyError) as e:
                logger.warning(f"Önkoşul yüklenemedi: {e}")

        ok, errors = dag.build()
        if not ok:
            logger.error(f"DAG döngüsü tespit edildi: {errors}")
            raise RuntimeError(f"DAG döngüsü tespit edildi: {errors}")

        return dag

    # ── Mastery ───────────────────────────────────────────────────

    async def get_user_mastery(
        self,
        user_id: str,
        subject_id: str | None = None,
    ) -> dict[str, float]:
        """
        Kullanıcının tüm konulardaki mastery skorlarını getir.
        Redis cache → DB sorgusu.

        Mastery skoru: P(θ > 0) — IRT θ tahmininden hesaplanır.
        """
        cache_key = f"mastery:{user_id}"
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        # cat_sessions tablosundan son θ değerlerini çek
        # Her oturum subject_id'ye bağlı; mastery topic_id bazında döner
        # subject_id → topics tablosu üzerinden topic_id'ye ulaşırız
        result = await self.db.execute(
            text("""
            SELECT DISTINCT ON (q.primary_topic_id)
                q.primary_topic_id AS topic_id,
                cs.theta_final,
                cs.se_final
            FROM kiro2_cat_sessions cs
            JOIN question_bank q ON q.subject_area = cs.subject_id
            WHERE cs.user_id = :uid
              AND cs.state = 'completed'
              AND q.primary_topic_id IS NOT NULL
              AND q.is_active = TRUE
            ORDER BY q.primary_topic_id, cs.completed_at DESC
        """),
            {"uid": user_id},
        )

        # Konu başına en yüksek mastery al
        mastery: dict[str, float] = {}
        for row in result.fetchall():
            tid = row.topic_id
            score = compute_mastery_from_theta(
                float(row.theta_final),
                float(row.se_final or 0.5),
            )
            if tid not in mastery or mastery[tid] < score:
                mastery[tid] = score

        if self.redis:
            await self.redis.setex(
                cache_key,
                MASTERY_CACHE_TTL,
                json.dumps(mastery),
            )

        return mastery

    # ── CAT Entegrasyon ───────────────────────────────────────────

    async def check_can_study_topic(
        self,
        user_id: str,
        topic_id: str,
    ) -> MasteryCheck:
        """
        Kullanıcının bir konuya çalışmaya hazır olup olmadığını kontrol et.
        CAT soru seçiminden ÖNCE çağrılmalı.

        Döndürür:
          MasteryCheck.can_proceed=True  → CAT başlatılabilir
          MasteryCheck.can_proceed=False → blocking_prereqs listesini göster
        """
        dag = await self.get_dag()
        mastery = await self.get_user_mastery(user_id)
        return dag.check_mastery(topic_id, mastery)

    async def get_next_recommended_topic(
        self,
        user_id: str,
        subject_id: str,
    ) -> str | None:
        """
        Kullanıcının şu an çalışabileceği en uygun konuyu öner.

        Mantık:
          1. Konuları topological sırayla tara
          2. Mastery < 0.70 olan ilk konuyu seç
          3. Önkoşulları tamamlanmış olmalı (can_proceed=True)
        """
        dag = await self.get_dag()
        mastery = await self.get_user_mastery(user_id)
        topics = dag.get_subject_topics(subject_id)

        for node in topics:
            score = mastery.get(node.topic_id, 0.0)
            if score >= 0.70:
                continue  # zaten ustalaştı

            check = dag.check_mastery(node.topic_id, mastery)
            if check.can_proceed:
                return node.topic_id

        return None  # tüm konular tamamlandı

    async def get_learning_path_for_user(
        self,
        user_id: str,
        target_topic_id: str,
    ) -> LearningPath:
        """Kullanıcıya özel öğrenme yolu — ustalaşılanları atlar."""
        dag = await self.get_dag()
        mastery = await self.get_user_mastery(user_id)
        return dag.get_learning_path(target_topic_id, mastery, skip_mastered=True)

    # ── Seri/Deserialize ──────────────────────────────────────────

    def _serialize_dag(self, dag: PrerequisiteDAG) -> str:
        """DAG'ı Redis için JSON string'e çevir."""
        data = {
            "nodes": [
                {
                    "topic_id": n.topic_id,
                    "name": n.name,
                    "subject_id": n.subject_id,
                    "level": n.level,
                }
                for n in dag.get_all_topics()
            ],
            "edges": [
                {
                    "topic_id": e.topic_id,
                    "prereq_id": e.prereq_id,
                    "ptype": e.ptype.value,
                    "strength": e.strength,
                }
                for e in dag._edges
            ],
        }
        return json.dumps(data, ensure_ascii=False)

    def _deserialize_dag(self, raw: bytes) -> PrerequisiteDAG:
        """Redis'ten okunan JSON'dan DAG oluştur."""
        data = json.loads(raw)
        dag = PrerequisiteDAG()

        for n in data["nodes"]:
            dag.add_topic(n["topic_id"], n["name"], n["subject_id"])

        for e in data["edges"]:
            try:
                dag.add_prereq(
                    e["topic_id"],
                    e["prereq_id"],
                    PrereqType(e["ptype"]),
                    float(e["strength"]),
                )
            except (ValueError, KeyError):
                pass

        ok, errors = dag.build()
        if not ok:
            logger.warning(f"Cached DAG döngüsü: {errors}")
        return dag

    async def invalidate_cache(self) -> None:
        """DAG ve mastery cache'lerini temizle (konu güncellendiğinde)."""
        self._dag = None
        if self.redis:
            await self.redis.delete("dag:yks")
