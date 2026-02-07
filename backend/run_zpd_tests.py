#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ZPD Maarif Service - Test Runner
Comprehensive testing for Turkish cultural ZPD calculation service
"""

import asyncio
import sys

from services.zpd_maarif_service import ZPDMaarifService
from models.zpd_maarif import KulturelBaglamProfili, MaarifDegerleriProfili


class ZPDTestRunner:
    """Test runner for ZPD Maarif Service"""

    def __init__(self):
        self.service = ZPDMaarifService()
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        print(f"[{status}]: {test_name}")
        if message:
            print(f"   {message}")

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

        self.test_results.append(
            {"test": test_name, "passed": passed, "message": message}
        )

    async def test_01_temel_zpd_hesaplama(self):
        """Test 1: Temel ZPD hesaplama"""
        try:
            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_001", konu="matematik", mevcut_seviye=6.0
            )

            # Dogrulamalar
            assert sonuc is not None, "Sonuc None olmamali"
            assert hasattr(sonuc, "alt_sinir"), "alt_sinir olmali"
            assert hasattr(sonuc, "ust_sinir"), "ust_sinir olmali"
            assert hasattr(sonuc, "optimal_zorluk"), "optimal_zorluk olmali"

            # ZPD sinirlari mantikli olmali
            assert (
                sonuc.alt_sinir < 6.0
            ), f"Alt sinir ({sonuc.alt_sinir}) < mevcut seviye (6.0)"
            assert (
                sonuc.ust_sinir > 6.0
            ), f"Ust sinir ({sonuc.ust_sinir}) > mevcut seviye (6.0)"
            assert (
                sonuc.alt_sinir < sonuc.optimal_zorluk < sonuc.ust_sinir
            ), "Alt < Optimal < Ust"

            self.log_test(
                "test_01_temel_zpd_hesaplama",
                True,
                f"ZPD: [{sonuc.alt_sinir:.2f}, {sonuc.ust_sinir:.2f}], Optimal: {sonuc.optimal_zorluk:.2f}",
            )
        except Exception as e:
            self.log_test("test_01_temel_zpd_hesaplama", False, str(e))

    async def test_02_dusuk_seviye_zpd(self):
        """Test 2: Dusuk seviye (1.0) icin ZPD"""
        try:
            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_002", konu="matematik", mevcut_seviye=1.0
            )

            # Alt sinir negatif olmamali
            assert sonuc.alt_sinir >= 0.0, f"Alt sinir ({sonuc.alt_sinir}) >= 0"
            assert sonuc.ust_sinir <= 4.0, f"Ust sinir ({sonuc.ust_sinir}) makul"

            self.log_test(
                "test_02_dusuk_seviye_zpd",
                True,
                f"Dusuk seviye ZPD: [{sonuc.alt_sinir:.2f}, {sonuc.ust_sinir:.2f}]",
            )
        except Exception as e:
            self.log_test("test_02_dusuk_seviye_zpd", False, str(e))

    async def test_03_yuksek_seviye_zpd(self):
        """Test 3: Yuksek seviye (9.5) icin ZPD"""
        try:
            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_003", konu="matematik", mevcut_seviye=9.5
            )

            # Ust sinir 10'u gecmemeli
            assert sonuc.ust_sinir <= 10.0, f"Ust sinir ({sonuc.ust_sinir}) <= 10"
            assert sonuc.alt_sinir >= 7.0, f"Alt sinir ({sonuc.alt_sinir}) makul"

            self.log_test(
                "test_03_yuksek_seviye_zpd",
                True,
                f"Yuksek seviye ZPD: [{sonuc.alt_sinir:.2f}, {sonuc.ust_sinir:.2f}]",
            )
        except Exception as e:
            self.log_test("test_03_yuksek_seviye_zpd", False, str(e))

    async def test_04_kulturel_profil_yuksek_grup(self):
        """Test 4: Yuksek grup calismasi profili"""
        try:
            kulturel_profil = KulturelBaglamProfili(
                ogrenci_id="test_004",
                grup_calismasi_tercihi=0.9,
                ogretmene_saygi_seviyesi=0.85,
                aile_katilim_derecesi=0.8,
                akran_rekabet_egilimi=0.7,
                otorite_kabul_seviyesi=0.85,
                toplumsal_onay_ihtiyaci=0.8,
                basari_odaklilik=0.9,
                kolektif_kimlik_gucu=0.85,
            )

            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_004",
                konu="matematik",
                mevcut_seviye=6.0,
                kulturel_profil=kulturel_profil,
            )

            assert sonuc is not None, "Sonuc None olmamali"
            # Yuksek grup calismasi = genis ZPD (grup destegi ile daha zor konular)
            zpd_genisligi = sonuc.ust_sinir - sonuc.alt_sinir
            assert (
                zpd_genisligi > 1.5
            ), f"Grup profili ile ZPD genisligi ({zpd_genisligi:.2f}) > 1.5"

            self.log_test(
                "test_04_kulturel_profil_yuksek_grup",
                True,
                f"Grup profili ZPD genisligi: {zpd_genisligi:.2f}",
            )
        except Exception as e:
            self.log_test("test_04_kulturel_profil_yuksek_grup", False, str(e))

    async def test_05_kulturel_profil_dusuk(self):
        """Test 5: Dusuk kulturel faktorler"""
        try:
            kulturel_profil = KulturelBaglamProfili(
                ogrenci_id="test_005",
                grup_calismasi_tercihi=0.2,
                ogretmene_saygi_seviyesi=0.3,
                aile_katilim_derecesi=0.2,
                akran_rekabet_egilimi=0.3,
                otorite_kabul_seviyesi=0.3,
                toplumsal_onay_ihtiyaci=0.2,
                basari_odaklilik=0.4,
                kolektif_kimlik_gucu=0.3,
            )

            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_005",
                konu="tarih",
                mevcut_seviye=5.0,
                kulturel_profil=kulturel_profil,
            )

            assert sonuc is not None, "Sonuc None olmamali"
            # Dusuk faktorler = dar ZPD (bireysel ogrenme)
            zpd_genisligi = sonuc.ust_sinir - sonuc.alt_sinir

            self.log_test(
                "test_05_kulturel_profil_dusuk",
                True,
                f"Bireysel profil ZPD genisligi: {zpd_genisligi:.2f}",
            )
        except Exception as e:
            self.log_test("test_05_kulturel_profil_dusuk", False, str(e))

    async def test_06_maarif_profili_yuksek_milli(self):
        """Test 6: Yuksek milli degerler profili"""
        try:
            maarif_profili = MaarifDegerleriProfili(
                ogrenci_id="test_006",
                vatan_sevgisi=0.9,
                millet_bilinci=0.85,
                aile_birligi=0.9,
                bayrak_sevgisi=0.9,
                istiklal_ruhu=0.85,
                adalet=0.8,
                dostluk=0.8,
                durustluk=0.8,
                ozgurluk=0.7,
                esitlik=0.8,
                baris=0.8,
                sabir=0.8,
                saygi=0.9,
                sevgi=0.8,
                sorumluluk=0.9,
                duyarlilik=0.8,
                hosgoru=0.8,
            )

            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_006",
                konu="tarih",  # Tarih konusu milli degerlerle uyumlu
                mevcut_seviye=7.0,
                maarif_profili=maarif_profili,
            )

            assert sonuc is not None, "Sonuc None olmamali"

            self.log_test(
                "test_06_maarif_profili_yuksek_milli",
                True,
                f"Milli degerler profili - ZPD: [{sonuc.alt_sinir:.2f}, {sonuc.ust_sinir:.2f}]",
            )
        except Exception as e:
            self.log_test("test_06_maarif_profili_yuksek_milli", False, str(e))

    async def test_07_farkli_konular(self):
        """Test 7: Farkli konularda ZPD"""
        try:
            konular = ["matematik", "fizik", "tarih", "edebiyat", "biyoloji"]
            sonuclar = {}

            for konu in konular:
                sonuc = await self.service.hesapla_turk_zpd(
                    ogrenci_id="test_007", konu=konu, mevcut_seviye=6.0
                )
                sonuclar[konu] = sonuc

            # Tum konular icin ZPD hesaplanmis olmali
            assert len(sonuclar) == len(konular), "Tum konular hesaplanmali"

            for konu, sonuc in sonuclar.items():
                assert sonuc is not None, f"{konu} icin sonuc None olmamali"
                assert sonuc.alt_sinir < sonuc.ust_sinir, f"{konu} icin ZPD mantikli"

            self.log_test(
                "test_07_farkli_konular",
                True,
                f"{len(konular)} farkli konu icin ZPD hesaplandi",
            )
        except Exception as e:
            self.log_test("test_07_farkli_konular", False, str(e))

    async def test_08_negatif_seviye_duzeltme(self):
        """Test 8: Negatif seviye otomatik duzeltme"""
        try:
            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_008", konu="matematik", mevcut_seviye=-2.0  # Negatif
            )

            # Negatif seviye 0'a duzeltilmeli
            assert sonuc.alt_sinir >= 0.0, "Alt sinir negatif olmamali"

            self.log_test(
                "test_08_negatif_seviye_duzeltme", True, "Negatif seviye duzeltildi"
            )
        except Exception as e:
            self.log_test("test_08_negatif_seviye_duzeltme", False, str(e))

    async def test_09_cok_yuksek_seviye_duzeltme(self):
        """Test 9: Cok yuksek seviye otomatik duzeltme"""
        try:
            sonuc = await self.service.hesapla_turk_zpd(
                ogrenci_id="test_009",
                konu="matematik",
                mevcut_seviye=15.0,  # Cok yuksek
            )

            # Ust sinir 10'u gecmemeli
            assert sonuc.ust_sinir <= 10.0, "Ust sinir 10'u gecmemeli"

            self.log_test(
                "test_09_cok_yuksek_seviye_duzeltme",
                True,
                "Cok yuksek seviye duzeltildi",
            )
        except Exception as e:
            self.log_test("test_09_cok_yuksek_seviye_duzeltme", False, str(e))

    async def test_10_performans_hiz(self):
        """Test 10: Performans - 10 hesaplama hizi"""
        try:
            import time

            start = time.time()
            for i in range(10):
                await self.service.hesapla_turk_zpd(
                    ogrenci_id=f"perf_test_{i}",
                    konu="matematik",
                    mevcut_seviye=5.0 + i * 0.5,
                )
            elapsed = time.time() - start

            # 10 hesaplama < 1 saniye olmali
            assert elapsed < 1.0, f"10 hesaplama {elapsed:.3f}s < 1.0s"

            self.log_test(
                "test_10_performans_hiz",
                True,
                f"10 hesaplama {elapsed:.3f} saniyede tamamlandi",
            )
        except Exception as e:
            self.log_test("test_10_performans_hiz", False, str(e))

    async def run_all_tests(self):
        """Tum testleri calistir"""
        print("=" * 60)
        print("ZPD Maarif Service - Test Runner")
        print("=" * 60)
        print()

        tests = [
            self.test_01_temel_zpd_hesaplama,
            self.test_02_dusuk_seviye_zpd,
            self.test_03_yuksek_seviye_zpd,
            self.test_04_kulturel_profil_yuksek_grup,
            self.test_05_kulturel_profil_dusuk,
            self.test_06_maarif_profili_yuksek_milli,
            self.test_07_farkli_konular,
            self.test_08_negatif_seviye_duzeltme,
            self.test_09_cok_yuksek_seviye_duzeltme,
            self.test_10_performans_hiz,
        ]

        for test in tests:
            await test()

        print()
        print("=" * 60)
        print("Test Sonuclari")
        print("=" * 60)
        print(f"Basarili: {self.tests_passed}")
        print(f"Basarisiz: {self.tests_failed}")
        print(f"Toplam: {self.tests_passed + self.tests_failed}")
        if (self.tests_passed + self.tests_failed) > 0:
            print(
                f"Basari Orani: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%"
            )
        print("=" * 60)

        return self.tests_failed == 0


async def main():
    """Ana fonksiyon"""
    runner = ZPDTestRunner()
    success = await runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
