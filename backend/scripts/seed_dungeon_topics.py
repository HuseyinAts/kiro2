"""
Dungeon Topic Seed Script
=========================
1. Fix subject_area=NULL on MAT.xxx topics (-> MATEMATIK)
2. Add ~19 new subtopics for underrepresented subjects
3. Add ~25 new prerequisite edges

Idempotent: ON CONFLICT DO UPDATE / DO NOTHING.

Usage:
    cd backend
    python scripts/seed_dungeon_topics.py [--dry-run]
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import NamedTuple

import asyncpg

DB_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5434/kiro2",
)


class NewTopic(NamedTuple):
    code: str
    name_tr: str
    name_en: str
    subject_area: str
    level: int = 2
    description: str = ""


class Prereq(NamedTuple):
    topic_code: str
    prereq_code: str
    prereq_type: str = "hard"
    strength: float = 0.8


# ── Step 1: subject_area UPDATE for NULL-subject subtopics ──────────
SUBJECT_AREA_FIXES = {
    "MAT.": "MATEMATIK",
}

# ── Step 2: New subtopics for underrepresented subjects ─────────────
NEW_TOPICS: list[NewTopic] = [
    # Turkce (mevcut: 3 topic, +5 yeni)
    NewTopic("TUR.PAR", "Paragraf", "Paragraph", "TURKCE"),
    NewTopic("TUR.ANL", "Anlam Bilgisi", "Semantics", "TURKCE"),
    NewTopic("TUR.YAZ", "Yazim Kurallari", "Spelling Rules", "TURKCE"),
    NewTopic("TUR.DIL", "Dil Bilgisi", "Grammar", "TURKCE"),
    NewTopic("TUR.SOZ", "Soz Varigi", "Vocabulary", "TURKCE"),
    # Biyoloji (mevcut: 2 topic, +6 yeni)
    NewTopic("BIY.HUC", "Hucre Biyolojisi", "Cell Biology", "BIYOLOJI"),
    NewTopic("BIY.GEN", "Genetik", "Genetics", "BIYOLOJI"),
    NewTopic("BIY.EKO", "Ekoloji", "Ecology", "BIYOLOJI"),
    NewTopic("BIY.SIS", "Sistemler", "Body Systems", "BIYOLOJI"),
    NewTopic("BIY.EVR", "Evrim", "Evolution", "BIYOLOJI"),
    NewTopic("BIY.BIT", "Bitki Biyolojisi", "Plant Biology", "BIYOLOJI"),
    # Fizik (mevcut: 4 TYT topic, +4 yeni AYT)
    NewTopic("FIZ.OPT", "Optik", "Optics", "FIZIK"),
    NewTopic("FIZ.ELE", "Elektrik", "Electricity", "FIZIK"),
    NewTopic("FIZ.MAG", "Manyetizma", "Magnetism", "FIZIK"),
    NewTopic("FIZ.MOD", "Modern Fizik", "Modern Physics", "FIZIK"),
    # Kimya (mevcut: 4 TYT topic, +4 yeni AYT)
    NewTopic("KIM.ORG", "Organik Kimya", "Organic Chemistry", "KIMYA"),
    NewTopic("KIM.ASI", "Asitler ve Bazlar", "Acids and Bases", "KIMYA"),
    NewTopic("KIM.DEN", "Kimyasal Denge", "Chemical Equilibrium", "KIMYA"),
    NewTopic("KIM.TER", "Termokimya", "Thermochemistry", "KIMYA"),
]

# ── Step 3: New prerequisite edges ──────────────────────────────────
NEW_PREREQS: list[Prereq] = [
    # Turkce
    Prereq("TUR.ANL", "TUR.PAR", "hard", 0.8),
    Prereq("TUR.YAZ", "TUR.DIL", "hard", 0.8),
    Prereq("TUR.SOZ", "TUR.PAR", "soft", 0.6),
    # Biyoloji
    Prereq("BIY.GEN", "BIY.HUC", "hard", 0.9),
    Prereq("BIY.SIS", "BIY.HUC", "hard", 0.8),
    Prereq("BIY.EVR", "BIY.GEN", "hard", 0.8),
    Prereq("BIY.BIT", "BIY.HUC", "soft", 0.6),
    Prereq("BIY.EKO", "BIY.SIS", "soft", 0.6),
    # Fizik
    Prereq("FIZ.ELE", "TYT-FIZ-03", "hard", 0.8),  # Enerji -> Elektrik
    Prereq("FIZ.MAG", "FIZ.ELE", "hard", 0.9),
    Prereq("FIZ.OPT", "TYT-FIZ-04", "hard", 0.8),  # Dalgalar -> Optik
    Prereq("FIZ.MOD", "FIZ.ELE", "soft", 0.7),
    # Kimya
    Prereq("KIM.ORG", "TYT-KIM-03", "hard", 0.8),  # Kim Baglar -> Organik
    Prereq("KIM.ASI", "TYT-KIM-04", "hard", 0.8),  # Reaksiyonlar -> Asit/Baz
    Prereq("KIM.DEN", "KIM.ASI", "hard", 0.8),
    Prereq("KIM.TER", "TYT-KIM-04", "hard", 0.7),  # Reaksiyonlar -> Termokimya
]


async def main(dry_run: bool = False) -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        # ── Step 1: Fix subject_area ──
        for prefix, subject in SUBJECT_AREA_FIXES.items():
            if dry_run:
                rows = await conn.fetch(
                    "SELECT code FROM topic_hierarchy WHERE code LIKE $1 AND subject_area IS NULL",
                    f"{prefix}%",
                )
                print(
                    f"[DRY-RUN] Would UPDATE {len(rows)} topics: {prefix}* -> {subject}"
                )
            else:
                result = await conn.execute(
                    "UPDATE topic_hierarchy SET subject_area = $1 WHERE code LIKE $2 AND subject_area IS NULL",
                    subject,
                    f"{prefix}%",
                )
                print(f"[UPDATE] {prefix}* -> {subject}: {result}")

        # ── Step 2: Insert new topics ──
        for t in NEW_TOPICS:
            if dry_run:
                print(f"[DRY-RUN] Would INSERT topic: {t.code} ({t.name_tr})")
            else:
                await conn.execute(
                    """
                    INSERT INTO topic_hierarchy
                        (id, code, name_tr, name_en, subject_area, level, description,
                         meb_code, meb_kazanim, osym_relevance, osym_frequency,
                         total_questions, average_difficulty, is_active)
                    VALUES
                        (gen_random_uuid(), $1, $2, $3, $4, $5, $6,
                         '', '[]'::json, 0.5, 0.5, 0, 0.5, true)
                    ON CONFLICT (code) DO UPDATE SET
                        name_tr = EXCLUDED.name_tr,
                        subject_area = EXCLUDED.subject_area
                    """,
                    t.code,
                    t.name_tr,
                    t.name_en,
                    t.subject_area,
                    t.level,
                    t.description,
                )
                print(f"[INSERT] {t.code}: {t.name_tr}")

        # ── Step 3: Insert new prerequisites ──
        for p in NEW_PREREQS:
            if dry_run:
                print(
                    f"[DRY-RUN] Would INSERT prereq: {p.topic_code} -> {p.prereq_code} ({p.prereq_type})"
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO topic_prerequisites (id, topic_id, prereq_id, prereq_type, strength, is_active)
                    SELECT gen_random_uuid(), t.id, p.id, $3, $4, true
                    FROM topic_hierarchy t, topic_hierarchy p
                    WHERE t.code = $1 AND p.code = $2
                    ON CONFLICT DO NOTHING
                    """,
                    p.topic_code,
                    p.prereq_code,
                    p.prereq_type,
                    p.strength,
                )
                print(f"[PREREQ] {p.topic_code} -> {p.prereq_code} ({p.prereq_type})")

        # ── Summary ──
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM topic_hierarchy WHERE subject_area IS NOT NULL"
        )
        prereq_count = await conn.fetchval("SELECT COUNT(*) FROM topic_prerequisites")
        print(
            f"\n[DONE] Topics with subject_area: {count}, Prerequisites: {prereq_count}"
        )

    finally:
        await conn.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry_run))
