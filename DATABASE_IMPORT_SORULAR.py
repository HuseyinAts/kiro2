#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATABASE IMPORT - JSON'dan PostgreSQL'e soru yükleme
"""

import sys
import os
import json
import asyncio
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def log(msg):
    print(msg, flush=True)

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def import_questions():
    """JSON dosyasından soruları database'e aktar"""
    log("="*80)
    log("DATABASE IMPORT - SORULAR")
    log("="*80)
    log("")

    # JSON dosyasını oku
    json_file = "URETILEN_20_SORU.json"
    if not os.path.exists(json_file):
        log(f"[HATA] {json_file} bulunamadı!")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        sorular = json.load(f)

    log(f"[✓] {len(sorular)} soru yüklendi")
    log("")

    try:
        # Database bağlantısı
        from core.database import db_manager

        await db_manager.initialize()
        log(f"[✓] Database bağlantısı OK")
        log("")

        # Her soruyu kaydet
        imported = 0
        skipped = 0
        errors = []

        async with db_manager.get_session() as session:
            for idx, soru in enumerate(sorular, 1):
                try:
                    meta = soru['_metadata']

                    log(f"[{idx}/{len(sorular)}] {meta['id']} - {meta['ders']}")

                    # Check if exists
                    from sqlalchemy import text
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM sorular WHERE kod = :kod"),
                        {"kod": meta['id']}
                    )
                    exists = result.scalar() > 0

                    if exists:
                        log(f"  [ATLA] Zaten var")
                        skipped += 1
                        continue

                    # Insert - matching actual table schema
                    # Convert secenekler to proper JSON string format
                    secenekler_json = json.dumps(soru['secenekler'], ensure_ascii=False)

                    # Generate UUID for id column (required, NOT NULL)
                    import uuid
                    soru_uuid = str(uuid.uuid4())

                    await session.execute(
                        text("""
                            INSERT INTO sorular (
                                id, kod, metin, secenekler, dogru_cevap,
                                sinav_tipi, konu, alt_konu, kazanim, zorluk,
                                irt_difficulty, bloom_level,
                                aktif, olusturma_tarihi, status
                            ) VALUES (
                                CAST(:id AS uuid), :kod, :metin, CAST(:secenekler AS jsonb), :dogru_cevap,
                                :sinav_tipi, :konu, :alt_konu, :kazanim, :zorluk,
                                :irt_difficulty, :bloom_level,
                                true, NOW(), 'approved'
                            )
                        """),
                        {
                            "id": soru_uuid,
                            "kod": meta['id'],
                            "metin": soru['soru_metni'],
                            "secenekler": secenekler_json,
                            "dogru_cevap": soru['dogru_cevap'],
                            "sinav_tipi": "TYT",
                            "konu": f"{meta['ders']} - {meta['konu']}",
                            "alt_konu": meta['alt_konu'],
                            "kazanim": soru.get('kazanim', ''),
                            "zorluk": meta['zorluk'],
                            "irt_difficulty": meta.get('irt_difficulty', 0.0),
                            "bloom_level": meta.get('bloom_level', 'apply')
                        }
                    )

                    await session.commit()
                    imported += 1
                    log(f"  [✓] Kaydedildi")

                except Exception as e:
                    error_msg = f"Soru {idx} hata: {str(e)[:100]}"
                    log(f"  [HATA] {error_msg}")
                    errors.append(error_msg)
                    await session.rollback()

        log("")
        log("="*80)
        log("SONUÇ")
        log("="*80)
        log(f"\nToplam Soru:    {len(sorular)}")
        log(f"Import Edilen:  {imported}")
        log(f"Atlandı:        {skipped}")
        log(f"Hatalar:        {len(errors)}")
        log("")

        if errors:
            log("HATALAR:")
            for err in errors[:5]:
                log(f"  - {err}")
            log("")

        if imported > 0:
            log(f"[✓✓✓] {imported} soru database'e aktarıldı!")
        elif skipped > 0:
            log(f"[✓] Tüm sorular zaten database'de mevcut")

        log("="*80)

        await db_manager.close()

    except Exception as e:
        log(f"[HATA] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(import_questions())
