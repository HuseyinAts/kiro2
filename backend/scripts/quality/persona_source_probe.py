"""Persona alanlarinin canli DB'de gercekten dolu olup olmadigini olcer (#447 A1).

Bu probe, /api/v1/me servisinin SQL'ini yazmadan ONCE kosar. Iki sorusu var:

1. Varsayilan kolon adlari GERCEKTEN var mi? (users.is_active,
   student_profiles.user_id, streaks.user_id ...) — yoksa servis SQL'i
   calisma zamaninda patlar ve bunu testte degil UYGULAMADA gorurduk.
2. Alanlar DOLU mu? Bir kolonun var olmasi veri oldugu anlamina gelmez.
   Bos kolon = uc `None` doner; bu kabul edilebilir ama BILEREK secilmeli,
   sonradan sasirilarak degil.

Kullanim (backend/ dizininden):
    python scripts/quality/persona_source_probe.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

from sqlalchemy import text  # noqa: E402

from core.database import get_db_session_context  # noqa: E402

# Once SEMA: kolon gercekten var mi? information_schema yalan soylemez.
SEMA_SORGUSU = text(
    """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE (table_name = 'users'
             AND column_name IN ('id','first_name','last_name','total_xp','level','is_active'))
       OR (table_name = 'streaks'
             AND column_name IN ('user_id','current_streak','largest_streak'))
       OR (table_name = 'student_profiles'
             AND column_name IN ('user_id','grade_level','target_department',
                                 'target_university','study_hours_per_day'))
    ORDER BY table_name, column_name
    """
)

# Sonra VERI: kolon var ama dolu mu?
VERI_SORGUSU = text(
    """
    SELECT
      (SELECT count(*) FROM users)                                    AS kullanici,
      (SELECT count(*) FROM users WHERE total_xp > 0)                 AS xp_dolu,
      (SELECT count(*) FROM users WHERE level > 1)                    AS seviye_dolu,
      (SELECT count(*) FROM streaks)                                  AS streak_satiri,
      (SELECT count(*) FROM student_profiles)                         AS profil_satiri,
      (SELECT count(*) FROM student_profiles
         WHERE target_university IS NOT NULL)                         AS hedef_uni_dolu,
      (SELECT count(*) FROM student_profiles
         WHERE study_hours_per_day IS NOT NULL)                       AS gunluk_saat_dolu
    """
)

BEKLENEN = (
    {
        ("users", c)
        for c in ("id", "first_name", "last_name", "total_xp", "level", "is_active")
    }
    | {("streaks", c) for c in ("user_id", "current_streak", "largest_streak")}
    | {
        ("student_profiles", c)
        for c in (
            "user_id",
            "grade_level",
            "target_department",
            "target_university",
            "study_hours_per_day",
        )
    }
)


async def main() -> int:
    async with get_db_session_context() as oturum:
        bulunan = {
            (s["table_name"], s["column_name"])
            for s in (await oturum.execute(SEMA_SORGUSU)).mappings()
        }
        sayilar = (await oturum.execute(VERI_SORGUSU)).mappings().one()

    eksik = sorted(BEKLENEN - bulunan)
    print("=== SEMA ===")
    print(f"  beklenen kolon: {len(BEKLENEN)}  bulunan: {len(bulunan)}")
    if eksik:
        print("  EKSIK KOLONLAR (servis SQL'i BUNA GORE duzeltilmeli):")
        for tablo, kolon in eksik:
            print(f"    {tablo}.{kolon}")
    else:
        print("  eksik yok — A3'teki SQL varsayimlari gecerli")

    print("\n=== VERI DOLULUGU ===")
    for ad, deger in sayilar.items():
        print(f"  {ad:20s}: {deger}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
