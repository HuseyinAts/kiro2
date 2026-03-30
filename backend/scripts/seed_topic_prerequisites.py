"""
YKS Müfredatı — topic_prerequisites Seed Scripti
===================================================
Mevcut 29 prereq'e ~80 YKS önkoşul ilişkisi ekler.
Idempotent: ON CONFLICT DO NOTHING ile tekrar çalıştırılabilir.

Kullanım:
    cd backend
    python scripts/seed_topic_prerequisites.py [--dry-run]
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import NamedTuple

import asyncpg


class Prereq(NamedTuple):
    topic_code: str
    prereq_code: str
    prereq_type: str = "hard"  # 'hard' | 'soft'
    strength: float = 0.8


# YKS müfredatı önkoşul ilişkileri
# (topic → prereq): topic'i öğrenmek için prereq bilinmeli
PREREQUISITES: list[Prereq] = [
    # ── MAT. Detay Zinciri ───────────────────────────────────────────
    Prereq("MAT.USL", "MAT.SAY", "hard", 0.9),  # Üslü ← Sayılar
    Prereq("MAT.MTL", "MAT.SAY", "hard", 0.8),  # Mutlak Değer ← Sayılar
    Prereq("MAT.CRP", "MAT.USL", "hard", 0.85),  # Çarpanlara ← Üslü
    Prereq("MAT.LOG", "MAT.USL", "hard", 0.85),  # Logaritma ← Üslü
    Prereq("MAT.POL", "MAT.CRP", "hard", 0.85),  # Polinomlar ← Çarpanlara
    Prereq("MAT.DNK", "MAT.POL", "hard", 0.9),  # Denklemler ← Polinomlar
    Prereq("MAT.EST", "MAT.DNK", "hard", 0.9),  # Eşitsizlikler ← Denklemler
    Prereq("MAT.FON", "MAT.DNK", "hard", 0.85),  # Fonksiyonlar ← Denklemler
    Prereq("MAT.FON", "MAT.EST", "soft", 0.7),  # Fonksiyonlar ← Eşitsizlikler
    Prereq("MAT.TRG", "MAT.FON", "hard", 0.8),  # Trigonometri ← Fonksiyonlar
    Prereq("MAT.TRG", "MAT.GEO", "soft", 0.6),  # Trigonometri ← Geometri
    Prereq("MAT.IST", "MAT.FON", "soft", 0.7),  # İstatistik ← Fonksiyonlar
    Prereq("MAT.DIZ", "MAT.FON", "hard", 0.8),  # Diziler ← Fonksiyonlar
    Prereq("MAT.LMT", "MAT.TRG", "hard", 0.8),  # Limit ← Trigonometri
    Prereq("MAT.LMT", "MAT.DIZ", "soft", 0.6),  # Limit ← Diziler
    Prereq("MAT.TRV", "MAT.LMT", "hard", 0.95),  # Türev ← Limit
    Prereq("MAT.INT", "MAT.TRV", "hard", 0.95),  # İntegral ← Türev
    Prereq("MAT.PRB", "MAT.SAY", "hard", 0.8),  # Problemler ← Sayılar
    Prereq("MAT.OLS", "MAT.SAY", "hard", 0.75),  # Olasılık ← Sayılar
    Prereq("MAT.KMB", "MAT.OLS", "hard", 0.85),  # Kombinasyon ← Olasılık
    Prereq("MAT.PRM", "MAT.KMB", "hard", 0.85),  # Permütasyon ← Kombinasyon
    # ── TYT-MAT Zinciri ─────────────────────────────────────────────
    Prereq("TYT-MAT-06", "TYT-MAT-01", "hard", 0.8),  # Oran ← Sayılar
    Prereq("TYT-MAT-09", "TYT-MAT-05", "hard", 0.85),  # Fonksiyon ← Denklemler
    Prereq("TYT-MAT-10", "TYT-MAT-01", "soft", 0.7),  # İstatistik ← Sayılar
    Prereq("TYT-MAT-13", "TYT-MAT-12", "hard", 0.85),  # Dörtgenler ← Üçgenler
    Prereq("TYT-MAT-14", "TYT-MAT-13", "hard", 0.8),  # Çember ← Dörtgenler
    Prereq("TYT-MAT-15", "TYT-MAT-01", "hard", 0.75),  # Permütasyon ← Sayılar
    # ── TYT-KIM Zinciri ─────────────────────────────────────────────
    Prereq("TYT-KIM-03", "TYT-KIM-01", "hard", 0.85),  # Bağlar ← Atom
    Prereq("TYT-KIM-04", "TYT-KIM-02", "hard", 0.8),  # Reaksiyonlar ← Periyodik
    Prereq("TYT-KIM-04", "TYT-KIM-03", "hard", 0.8),  # Reaksiyonlar ← Bağlar
    # ── AYT-MAT Zinciri ─────────────────────────────────────────────
    Prereq("AYT-MAT-01", "MAT.TRG", "hard", 0.9),  # AYT Trig ← MAT Trig
    Prereq("AYT-MAT-02", "MAT.GEO", "hard", 0.85),  # Analitik ← Geometri
    Prereq("AYT-MAT-03", "MAT.LOG", "hard", 0.9),  # AYT Log ← MAT Log
    Prereq("AYT-MAT-04", "AYT-MAT-03", "hard", 0.85),  # Limit ← Log
    Prereq("AYT-MAT-04", "MAT.LMT", "hard", 0.8),  # AYT Limit ← MAT Limit
    Prereq("AYT-MAT-05", "AYT-MAT-04", "hard", 0.95),  # Türev ← Limit
    Prereq("AYT-MAT-06", "AYT-MAT-05", "hard", 0.95),  # İntegral ← Türev
    Prereq("AYT-MAT-07", "MAT.OLS", "hard", 0.8),  # AYT Olasılık ← MAT Olasılık
    # ── GEO (Geometri) Zinciri ───────────────────────────────────────
    Prereq("GEO02", "GEO01", "hard", 0.85),  # Üçgenler ← Temel Geometri
    Prereq("GEO03", "GEO02", "hard", 0.8),  # Dörtgenler ← Üçgenler
    Prereq("GEO04", "GEO02", "hard", 0.75),  # Çember ← Üçgenler
    Prereq("GEO05", "GEO01", "hard", 0.8),  # Analitik ← Temel Geometri
    # ── COG (Coğrafya) Zinciri ───────────────────────────────────────
    Prereq("COG02", "COG01", "hard", 0.75),  # İklim ← Harita
    Prereq("COG03", "COG01", "hard", 0.7),  # Nüfus ← Harita
    Prereq("COG04", "COG03", "hard", 0.75),  # Ekonomi ← Nüfus
    Prereq("COG05", "COG02", "soft", 0.65),  # Bölgesel ← İklim
    # ── TYT-COG Zinciri ─────────────────────────────────────────────
    Prereq("TYT-COG-02", "TYT-COG-01", "hard", 0.75),  # Türkiye ← Fiziki
    # ── TAR (Tarih) Zinciri ──────────────────────────────────────────
    Prereq("TAR02", "TAR01", "hard", 0.8),  # Osmanlı Kuruluş ← İlk Çağ
    Prereq("TAR03", "TAR02", "hard", 0.85),  # Yükselme ← Kuruluş
    Prereq("TAR04", "TAR03", "hard", 0.85),  # Kurtuluş ← Yükselme/Duraklama
    Prereq("TAR05", "TAR04", "hard", 0.8),  # Yakın Çağ ← Kurtuluş
    # ── TYT-TAR Zinciri ─────────────────────────────────────────────
    Prereq("TYT-TAR-02", "TYT-TAR-01", "hard", 0.8),  # Yeni Türk ← Osmanlı
    # ── TYT-TR (Türkçe) Zinciri ─────────────────────────────────────
    Prereq("TYT-TR-02", "TYT-TR-01", "soft", 0.65),  # Dil Bilgisi ← Anlama
    Prereq("TYT-TR-03", "TYT-TR-02", "soft", 0.6),  # Paragraf ← Dil Bilgisi
    # ── EDU (Edebiyat) Zinciri ──────────────────────────────────────
    Prereq("EDU02", "EDU01", "hard", 0.8),  # Tanzimat ← Divan
    Prereq("EDU03", "EDU02", "hard", 0.8),  # Milli ← Tanzimat
    Prereq("EDU04", "EDU03", "hard", 0.8),  # Cumhuriyet ← Milli
    Prereq("EDU05", "EDU04", "hard", 0.75),  # Çağdaş ← Cumhuriyet
    # ── SOC (Sosyal) Zinciri ─────────────────────────────────────────
    Prereq("SOC02", "SOC01", "soft", 0.6),  # Tarih ← Vatandaşlık
    Prereq("SOC03", "SOC02", "soft", 0.55),  # Dünya Coğ ← Türk Tarihi
    Prereq("SOC04", "SOC03", "soft", 0.6),  # Ekonomi ← Coğrafya
    Prereq("SOC05", "SOC04", "soft", 0.65),  # Çağdaş Sorunlar ← Ekonomi
    # ── FEN (Fen Bilimleri) Zinciri ─────────────────────────────────
    Prereq("FEN02", "FEN01", "hard", 0.75),  # Hücre ← Madde
    Prereq("FEN03", "FEN01", "hard", 0.7),  # Kuvvet ← Madde
    Prereq("FEN04", "FEN03", "hard", 0.8),  # Enerji ← Kuvvet
    Prereq("FEN05", "FEN04", "soft", 0.65),  # Ekosistem ← Enerji
    # ── TYT-FIZ: Kuvvet → Enerji (eksik olan) ───────────────────────
    Prereq("TYT-BIY-02", "TYT-BIY-01", "hard", 0.9),  # Genetik ← Hücre
]


async def seed(dry_run: bool = False) -> None:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5434/kiro2",
    ).replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)

    # Kod → UUID mapping
    rows = await conn.fetch("SELECT id, code FROM topic_hierarchy")
    code_to_id: dict[str, str] = {r["code"]: str(r["id"]) for r in rows}

    # Mevcut prereq sayısı
    existing = await conn.fetchval("SELECT COUNT(*) FROM topic_prerequisites")
    print(f"Mevcut topic_prerequisites: {existing}")

    inserted = 0
    skipped_missing = 0
    for p in PREREQUISITES:
        topic_id = code_to_id.get(p.topic_code)
        prereq_id = code_to_id.get(p.prereq_code)
        if not topic_id or not prereq_id:
            print(f"  SKIP (kod bulunamadi): {p.topic_code} -> {p.prereq_code}")
            skipped_missing += 1
            continue
        if dry_run:
            print(
                f"  DRY-RUN INSERT: {p.topic_code} -> {p.prereq_code} ({p.prereq_type}, {p.strength})"
            )
            inserted += 1
            continue
        result = await conn.execute(
            """
            INSERT INTO topic_prerequisites (topic_id, prereq_id, prereq_type, strength, is_active)
            VALUES ($1, $2, $3, $4, TRUE)
            ON CONFLICT (topic_id, prereq_id) DO NOTHING
            """,
            topic_id,
            prereq_id,
            p.prereq_type,
            p.strength,
        )
        if result and result.split()[-1] == "1":
            inserted += 1

    await conn.close()

    after = existing if dry_run else await _count(db_url)
    print(
        f"\n{'DRY-RUN' if dry_run else 'DONE'}: {inserted} yeni / {skipped_missing} kod bulunamadi"
    )
    if not dry_run:
        print(f"Toplam topic_prerequisites: {after}")


async def _count(db_url: str) -> int:
    conn = await asyncpg.connect(db_url)
    n = await conn.fetchval("SELECT COUNT(*) FROM topic_prerequisites")
    await conn.close()
    return n


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    asyncio.run(seed(dry_run=dry_run))
