#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from core.database import db_manager
from sqlalchemy import select
from models.soru_model import Soru

async def test():
    await db_manager.initialize()
    async with db_manager.get_session() as s:
        # Query all questions
        stmt = select(Soru).where((Soru.aktif == True) | (Soru.aktif == None)).limit(5)
        result = await s.execute(stmt)
        sorular = result.scalars().all()

        print(f"Toplam soru sayisi: {len(sorular)}")
        print("-" * 80)
        for soru in sorular:
            print(f"Kod: {soru.kod}")
            print(f"Sinav Tipi: {soru.sinav_tipi}")
            print(f"Konu: {soru.konu}")
            print(f"Zorluk: {soru.zorluk}")
            print(f"Metin: {soru.metin[:50]}...")
            print()

    await db_manager.close()

asyncio.run(test())
