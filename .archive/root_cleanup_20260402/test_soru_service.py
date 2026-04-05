#!/usr/bin/env python3
"""Test Soru model and service directly"""
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test():
    from services.soru_bankasi_service import SoruBankasiServisi

    service = SoruBankasiServisi()

    # Test sorular_listele
    print("Testing sorular_listele with TYT filter...")
    sorular = await service.sorular_listele(sinav_tipi="TYT", limit=5)

    print(f"\nToplam soru: {len(sorular)}")
    print("-" * 80)

    for soru in sorular:
        print(f"Kod: {soru.kod}")
        print(f"Sinav: {soru.sinav_tipi}")
        print(f"Konu: {soru.konu}")
        print(f"Zorluk: {soru.zorluk}")
        print(f"Metin: {soru.metin[:60]}...")
        print()

asyncio.run(test())
