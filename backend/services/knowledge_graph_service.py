"""
Knowledge Graph Service — F4 Granüler Bilgi Haritası

Ön koşul DAG'ı, öğrenci hakimiyet katmanı ve konu önerileri.
Basit Bayesian güncelleme: doğru → mastery += 0.1*(1-mastery),
yanlış → mastery -= 0.1*mastery.
"""
from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger("knowledge_graph_service")

# ---------------------------------------------------------------------------
# Sabit ön koşul yapısı — DB tablosu oluşturulana kadar fallback olarak kullanılır
# ---------------------------------------------------------------------------

def _kp(
    kp_id: str,
    name: str,
    prereqs: list[str],
    dr: list[float],
) -> dict:
    """Bilgi noktası tanım yardımcısı (satır uzunluğunu azaltır)."""
    return {"id": kp_id, "name": name, "prerequisites": prereqs, "difficulty_range": dr}


_PREREQUISITE_DAG: dict[str, list[dict]] = {
    "matematik": [
        _kp("sayilar", "Sayılar", [], [0.0, 0.4]),
        _kp("kumeler", "Kümeler", ["sayilar"], [0.2, 0.5]),
        _kp("fonksiyonlar", "Fonksiyonlar", ["kumeler", "sayilar"], [0.4, 0.7]),
        _kp("limit", "Limit", ["fonksiyonlar"], [0.5, 0.8]),
        _kp("turev", "Türev", ["limit"], [0.6, 0.9]),
        _kp("integral", "İntegral", ["turev"], [0.7, 1.0]),
        _kp("olasilik", "Olasılık", ["sayilar"], [0.3, 0.6]),
        _kp("geometri_temel", "Temel Geometri", [], [0.1, 0.4]),
        _kp("ucgenler", "Üçgenler", ["geometri_temel"], [0.3, 0.6]),
        _kp("donguler", "Dörtgenler ve Çevre", ["ucgenler"], [0.4, 0.7]),
    ],
    "fizik": [
        _kp("vektorler", "Vektörler", [], [0.2, 0.5]),
        _kp("hareket", "Hareket", ["vektorler"], [0.3, 0.6]),
        _kp("kuvvet", "Kuvvet ve Newton Yasaları", ["hareket"], [0.4, 0.7]),
        _kp("enerji", "Enerji ve İş", ["kuvvet"], [0.5, 0.8]),
        _kp("elektrostatik", "Elektrostatik", ["vektorler"], [0.5, 0.8]),
        _kp("elektrik_akimi", "Elektrik Akımı", ["elektrostatik"], [0.6, 0.9]),
    ],
    "kimya": [
        _kp("atom_yapisi", "Atom Yapısı", [], [0.1, 0.4]),
        _kp("periyodik_tablo", "Periyodik Tablo", ["atom_yapisi"], [0.2, 0.5]),
        _kp("kimyasal_bag", "Kimyasal Bağlar", ["periyodik_tablo"], [0.4, 0.7]),
        _kp("mol", "Mol Kavramı", ["atom_yapisi"], [0.3, 0.6]),
        _kp(
            "tepkimeler",
            "Kimyasal Tepkimeler",
            ["mol", "kimyasal_bag"],
            [0.5, 0.8],
        ),
    ],
    "turkce": [
        _kp("ses_bilgisi", "Ses Bilgisi", [], [0.1, 0.3]),
        _kp("kelime_anlami", "Kelime Anlamı", ["ses_bilgisi"], [0.2, 0.5]),
        _kp("cumle_bilgisi", "Cümle Bilgisi", ["kelime_anlami"], [0.3, 0.6]),
        _kp("paragraf", "Paragraf ve Metin", ["cumle_bilgisi"], [0.4, 0.7]),
        _kp("anlatim_bicimleri", "Anlatım Biçimleri", ["paragraf"], [0.5, 0.8]),
    ],
}


def _build_edges(nodes: list[dict]) -> list[dict]:
    """Düğüm listesinden kenar listesi türetir."""
    edges: list[dict] = []
    for node in nodes:
        for prereq_id in node.get("prerequisites", []):
            edges.append({"from": prereq_id, "to": node["id"]})
    return edges


# ---------------------------------------------------------------------------
# Servis fonksiyonları
# ---------------------------------------------------------------------------


async def build_prerequisite_dag(*, db: AsyncSession, subject: str) -> dict:
    """Bir derse ait ön koşul DAG'ını döndürür.

    Önce DB'den KnowledgePoint tablosunu okumaya çalışır;
    tablo yoksa statik sabit yapıyı kullanır.

    Args:
        db: Veritabanı oturumu.
        subject: Ders adı (küçük harf, örn. 'matematik').

    Returns:
        {nodes: [{id, name, prerequisites, difficulty_range}], edges: [{from, to}]}
    """
    subject_key = subject.lower().strip()

    try:
        from sqlalchemy import select

        from models.knowledge_graph import KnowledgePoint  # lazy import

        result = await db.execute(
            select(KnowledgePoint).where(KnowledgePoint.subject == subject_key)
        )
        rows = result.scalars().all()

        if rows:
            nodes = [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "prerequisites": r.prerequisite_ids or [],
                    "difficulty_range": r.difficulty_range or [0.0, 1.0],
                }
                for r in rows
            ]
            logger.info(
                "DAG loaded from DB",
                extra_data={"subject": subject_key, "node_count": len(nodes)},
            )
            return {"nodes": nodes, "edges": _build_edges(nodes)}

    except Exception as exc:
        logger.debug(
            "DAG DB fallback",
            extra_data={"subject": subject_key, "error": str(exc)},
        )

    # Statik fallback
    nodes = _PREREQUISITE_DAG.get(subject_key, [])
    return {"nodes": nodes, "edges": _build_edges(nodes)}


async def get_student_knowledge_state(
    *, db: AsyncSession, student_id: str, subject: str
) -> list[dict]:
    """Öğrencinin bilgi noktaları başına hakimiyet düzeyini döndürür.

    Bir öğrenci için KB yoksa tüm düğümler 'locked' ya da 'available'
    durumunda, mastery_level=0 ile döner.

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        subject: Ders adı.

    Returns:
        [{knowledge_point_id, name, mastery_level: 0-1, confidence,
          last_assessed, status: locked|available|mastered}]
    """
    subject_key = subject.lower().strip()

    # DAG'dan tüm düğümleri al (DB veya statik)
    dag = await build_prerequisite_dag(db=db, subject=subject_key)
    nodes = dag["nodes"]

    # Hakimiyet verilerini DB'den al
    mastery_map: dict[str, dict] = {}
    try:
        from sqlalchemy import and_, select

        from models.knowledge_graph import StudentKnowledgeState  # lazy import

        result = await db.execute(
            select(StudentKnowledgeState).where(
                and_(
                    StudentKnowledgeState.student_id == student_id,
                    StudentKnowledgeState.subject == subject_key,
                )
            )
        )
        rows = result.scalars().all()
        for r in rows:
            mastery_map[r.knowledge_point_id] = {
                "mastery_level": float(r.mastery_level),
                "confidence": float(r.confidence or 0.5),
                "last_assessed": (
                    r.last_assessed.isoformat() if r.last_assessed else None
                ),
            }

    except Exception as exc:
        logger.debug(
            "Knowledge state DB fallback",
            extra_data={"student_id": student_id, "error": str(exc)},
        )

    # Hangi düğümlerin kilidinin açık olduğunu belirle
    unlocked: set[str] = set()
    for node in nodes:
        prereqs = node.get("prerequisites", [])
        if not prereqs or all(
            mastery_map.get(p, {}).get("mastery_level", 0) >= 0.6 for p in prereqs
        ):
            unlocked.add(node["id"])

    states: list[dict] = []
    for node in nodes:
        kp_id = node["id"]
        data = mastery_map.get(kp_id, {})
        mastery = data.get("mastery_level", 0.0)

        if mastery >= 0.8:
            status = "mastered"
        elif kp_id in unlocked:
            status = "available"
        else:
            status = "locked"

        states.append(
            {
                "knowledge_point_id": kp_id,
                "name": node["name"],
                "mastery_level": mastery,
                "confidence": data.get("confidence", 0.5),
                "last_assessed": data.get("last_assessed"),
                "status": status,
            }
        )

    return states


async def suggest_next_topics(
    *, db: AsyncSession, student_id: str, subject: str, limit: int = 5
) -> list[dict]:
    """Kilidini açık, düşük hakimiyetli bilgi noktalarını önerir.

    'available' durumundaki ve mastery_level < 0.8 olan noktaları
    mastery artan sırada döndürür (en zayıf önce).

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        subject: Ders adı.
        limit: Maksimum öneri sayısı.

    Returns:
        [{knowledge_point_id, name, mastery_level, reason}]
    """
    states = await get_student_knowledge_state(
        db=db, student_id=student_id, subject=subject
    )

    candidates = [
        s for s in states
        if s["status"] == "available" and s["mastery_level"] < 0.8
    ]
    # En düşük hakimiyet önce
    candidates.sort(key=lambda s: s["mastery_level"])

    suggestions: list[dict] = []
    for c in candidates[:limit]:
        mastery = c["mastery_level"]
        if mastery == 0.0:
            reason = "Henüz çalışılmamış konu — başlangıç için iyi bir seçim."
        elif mastery < 0.4:
            reason = (
                f"Hakimiyet düşük (%{mastery * 100:.0f})."
                " Temel alıştırmalara odaklan."
            )
        else:
            reason = f"Hakimiyet orta (%{mastery * 100:.0f}). Pratik yaparak pekiştir."

        suggestions.append(
            {
                "knowledge_point_id": c["knowledge_point_id"],
                "name": c["name"],
                "mastery_level": c["mastery_level"],
                "reason": reason,
            }
        )

    logger.info(
        "Next topic suggestions generated",
        extra_data={
            "student_id": student_id,
            "subject": subject,
            "count": len(suggestions),
        },
    )

    return suggestions


async def update_knowledge_state(
    *, db: AsyncSession, student_id: str, knowledge_point_id: str, is_correct: bool
) -> dict:
    """Soruya verilen cevap sonrası hakimiyet düzeyini günceller.

    Bayesian güncelleme:
      doğru → mastery += 0.1 * (1 - mastery)
      yanlış → mastery -= 0.1 * mastery

    Args:
        db: Veritabanı oturumu.
        student_id: Öğrenci kimliği.
        knowledge_point_id: Bilgi noktası kimliği.
        is_correct: Cevap doğru mu?

    Returns:
        {knowledge_point_id, student_id, old_mastery, new_mastery, delta, is_correct}
    """
    try:
        from datetime import datetime

        from sqlalchemy import and_, select

        from models.knowledge_graph import StudentKnowledgeState  # lazy import

        result = await db.execute(
            select(StudentKnowledgeState).where(
                and_(
                    StudentKnowledgeState.student_id == student_id,
                    StudentKnowledgeState.knowledge_point_id == knowledge_point_id,
                )
            )
        )
        state = result.scalars().first()

        if state:
            old_mastery = float(state.mastery_level)
        else:
            # Konu için kısa subject bilgisi — prefix çıkar
            subject = (
                knowledge_point_id.split("_")[0]
                if "_" in knowledge_point_id
                else "unknown"
            )
            state = StudentKnowledgeState(
                student_id=student_id,
                knowledge_point_id=knowledge_point_id,
                subject=subject,
                mastery_level=0.0,
                confidence=0.5,
            )
            old_mastery = 0.0
            db.add(state)

        # Bayesian güncelleme
        if is_correct:
            delta = 0.1 * (1.0 - old_mastery)
        else:
            delta = -0.1 * old_mastery

        new_mastery = max(0.0, min(1.0, old_mastery + delta))
        state.mastery_level = new_mastery
        state.last_assessed = datetime.now(UTC)

        # Güven artışı: cevap verilince biraz daha emin olunur
        old_confidence = float(state.confidence or 0.5)
        state.confidence = min(1.0, old_confidence + 0.05)

        db.add(state)
        await db.commit()
        await db.refresh(state)

        logger.info(
            "Knowledge state updated",
            extra_data={
                "student_id": student_id,
                "kp_id": knowledge_point_id,
                "old_mastery": round(old_mastery, 3),
                "new_mastery": round(new_mastery, 3),
                "is_correct": is_correct,
            },
        )

        return {
            "knowledge_point_id": knowledge_point_id,
            "student_id": student_id,
            "old_mastery": round(old_mastery, 3),
            "new_mastery": round(new_mastery, 3),
            "delta": round(delta, 3),
            "is_correct": is_correct,
        }

    except Exception as exc:
        logger.warning(
            "Knowledge state update fallback",
            extra_data={
                "student_id": student_id,
                "kp_id": knowledge_point_id,
                "error": str(exc),
            },
        )
        return {
            "knowledge_point_id": knowledge_point_id,
            "student_id": student_id,
            "old_mastery": 0.0,
            "new_mastery": 0.1 if is_correct else 0.0,
            "delta": 0.1 if is_correct else 0.0,
            "is_correct": is_correct,
        }
