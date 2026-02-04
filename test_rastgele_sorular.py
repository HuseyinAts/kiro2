#!/usr/bin/env python3
"""Test rastgele_sorular_sec directly"""
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test():
    from services.soru_bankasi_service import SoruBankasiServisi

    service = SoruBankasiServisi()

    # Test rastgele_sorular_sec
    print("Testing rastgele_sorular_sec with TYT...")
    sorular = await service.rastgele_sorular_sec(
        sinav_tipi="TYT",
        soru_sayisi=2
    )

    print(f"\nSeçilen soru sayısı: {len(sorular)}")
    print("-" * 80)

    for soru in sorular:
        print(f"Kod: {soru.kod}")
        print(f"Konu: {soru.konu}")
        print(f"Zorluk: {soru.zorluk}")
        print()

asyncio.run(test())
