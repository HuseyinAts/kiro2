"""
Zemberek-NLP Türkçe Morfoloji Servisi
Türkçe morfolojik analiz ve karmaşıklık hesaplama sistemi

Bu servis Zemberek-NLP kütüphanesini kullanarak Türkçe kelimelerin
morfolojik analizini yapar ve karmaşıklık faktörlerini hesaplar.
"""

import asyncio
import logging
import math
import re
from datetime import datetime
from functools import lru_cache
from typing import Any

from models.irt_morfoloji import (
    MorfolojiAnalizi,
    MorfolojiKarmasiklikSeviyesi,
    SoruMorfolojiAnalizi,
    TurkceEkTipi,
)

logger = logging.getLogger(__name__)


class ZemberekMorfolojiService:
    """
    Zemberek-NLP tabanlı Türkçe morfoloji analiz servisi

    Bu servis şu özellikleri sunar:
    1. Türkçe kelime morfolojik analizi
    2. Ek tiplerinin belirlenmesi
    3. Karmaşıklık skorlarının hesaplanması
    4. Frekans ve yaygınlık analizleri
    5. Soru metni kapsamlı analizi
    """

    def __init__(self):
        """Zemberek morfoloji servisini başlat"""
        self.zemberek_jar_path = "lib/zemberek-full.jar"  # Zemberek JAR dosyası yolu
        self.kelime_frekanslari = self._load_kelime_frekanslari()
        self.ek_frekanslari = self._load_ek_frekanslari()

        # Türkçe ek tipleri sözlüğü
        self.ek_tipi_sozlugu = {
            # İsim yapım ekleri
            "lık": TurkceEkTipi.ISIM_YAPIM,
            "lik": TurkceEkTipi.ISIM_YAPIM,
            "luk": TurkceEkTipi.ISIM_YAPIM,
            "lük": TurkceEkTipi.ISIM_YAPIM,
            "cı": TurkceEkTipi.ISIM_YAPIM,
            "ci": TurkceEkTipi.ISIM_YAPIM,
            "cu": TurkceEkTipi.ISIM_YAPIM,
            "cü": TurkceEkTipi.ISIM_YAPIM,
            "sız": TurkceEkTipi.ISIM_YAPIM,
            "siz": TurkceEkTipi.ISIM_YAPIM,
            "suz": TurkceEkTipi.ISIM_YAPIM,
            "süz": TurkceEkTipi.ISIM_YAPIM,
            # Fiil yapım ekleri
            "la": TurkceEkTipi.FIIL_YAPIM,
            "le": TurkceEkTipi.FIIL_YAPIM,
            "laş": TurkceEkTipi.FIIL_YAPIM,
            "leş": TurkceEkTipi.FIIL_YAPIM,
            "lan": TurkceEkTipi.FIIL_YAPIM,
            "len": TurkceEkTipi.FIIL_YAPIM,
            # İsim çekim ekleri
            "lar": TurkceEkTipi.ISIM_CEKIM,
            "ler": TurkceEkTipi.ISIM_CEKIM,
            "ın": TurkceEkTipi.ISIM_CEKIM,
            "in": TurkceEkTipi.ISIM_CEKIM,
            "un": TurkceEkTipi.ISIM_CEKIM,
            "ün": TurkceEkTipi.ISIM_CEKIM,
            "a": TurkceEkTipi.ISIM_CEKIM,
            "e": TurkceEkTipi.ISIM_CEKIM,
            "ı": TurkceEkTipi.ISIM_CEKIM,
            "i": TurkceEkTipi.ISIM_CEKIM,
            "u": TurkceEkTipi.ISIM_CEKIM,
            "ü": TurkceEkTipi.ISIM_CEKIM,
            "da": TurkceEkTipi.ISIM_CEKIM,
            "de": TurkceEkTipi.ISIM_CEKIM,
            "ta": TurkceEkTipi.ISIM_CEKIM,
            "te": TurkceEkTipi.ISIM_CEKIM,
            "dan": TurkceEkTipi.ISIM_CEKIM,
            "den": TurkceEkTipi.ISIM_CEKIM,
            "tan": TurkceEkTipi.ISIM_CEKIM,
            "ten": TurkceEkTipi.ISIM_CEKIM,
            # Fiil çekim ekleri
            "yor": TurkceEkTipi.FIIL_CEKIM,
            "dı": TurkceEkTipi.FIIL_CEKIM,
            "di": TurkceEkTipi.FIIL_CEKIM,
            "du": TurkceEkTipi.FIIL_CEKIM,
            "dü": TurkceEkTipi.FIIL_CEKIM,
            "tı": TurkceEkTipi.FIIL_CEKIM,
            "ti": TurkceEkTipi.FIIL_CEKIM,
            "tu": TurkceEkTipi.FIIL_CEKIM,
            "tü": TurkceEkTipi.FIIL_CEKIM,
            "acak": TurkceEkTipi.FIIL_CEKIM,
            "ecek": TurkceEkTipi.FIIL_CEKIM,
            "ır": TurkceEkTipi.FIIL_CEKIM,
            "ir": TurkceEkTipi.FIIL_CEKIM,
            "ur": TurkceEkTipi.FIIL_CEKIM,
            "ür": TurkceEkTipi.FIIL_CEKIM,
            "ar": TurkceEkTipi.FIIL_CEKIM,
            "er": TurkceEkTipi.FIIL_CEKIM,
            # Sıfat yapım ekleri
            "lı": TurkceEkTipi.SIFAT_YAPIM,
            "li": TurkceEkTipi.SIFAT_YAPIM,
            "lu": TurkceEkTipi.SIFAT_YAPIM,
            "lü": TurkceEkTipi.SIFAT_YAPIM,
            "sal": TurkceEkTipi.SIFAT_YAPIM,
            "sel": TurkceEkTipi.SIFAT_YAPIM,
            # Zarf yapım ekleri
            "ca": TurkceEkTipi.ZARF_YAPIM,
            "ce": TurkceEkTipi.ZARF_YAPIM,
            "casına": TurkceEkTipi.ZARF_YAPIM,
            "cesine": TurkceEkTipi.ZARF_YAPIM,
        }

    def _load_kelime_frekanslari(self) -> dict[str, float]:
        """Türkçe kelime frekanslarını yükle"""
        # Gerçek uygulamada büyük frekans veritabanından yüklenecek
        # Şimdilik örnek veriler
        return {
            "ev": 1000.0,
            "okul": 800.0,
            "kitap": 600.0,
            "öğrenci": 500.0,
            "öğretmen": 400.0,
            "ders": 350.0,
            "sınav": 300.0,
            "matematik": 250.0,
            "türkçe": 200.0,
            "bilim": 150.0,
        }

    def _load_ek_frekanslari(self) -> dict[str, float]:
        """Türkçe ek frekanslarını yükle"""
        # Gerçek uygulamada ek kullanım frekansları
        return {
            "lar": 1000.0,
            "ler": 1000.0,
            "ın": 800.0,
            "in": 800.0,
            "un": 800.0,
            "ün": 800.0,
            "da": 600.0,
            "de": 600.0,
            "yor": 500.0,
            "lık": 400.0,
            "lik": 400.0,
            "luk": 400.0,
            "lük": 400.0,
            "dı": 300.0,
            "di": 300.0,
            "du": 300.0,
            "dü": 300.0,
            "cı": 200.0,
            "ci": 200.0,
            "cu": 200.0,
            "cü": 200.0,
        }

    async def analiz_et_kelime(self, kelime: str) -> MorfolojiAnalizi:
        """
        Tek kelime için morfolojik analiz yap

        Args:
            kelime: Analiz edilecek Türkçe kelime

        Returns:
            MorfolojiAnalizi: Detaylı morfoloji analiz sonucu
        """
        try:
            # Zemberek ile morfolojik analiz
            zemberek_sonuc = await self._zemberek_analiz(kelime)

            # Analiz sonucunu parse et
            kok, ekler = self._parse_zemberek_sonuc(zemberek_sonuc)

            # Ek tiplerini belirle
            ek_tipleri = [self._belirle_ek_tipi(ek) for ek in ekler]

            # Frekans bilgilerini al
            kok_frekansi = self.kelime_frekanslari.get(kok.lower(), 1.0)
            ek_frekansi = self._hesapla_ek_frekansi(ekler)
            yaygınlık_skoru = self._hesapla_yaygınlık_skoru(kok, ekler)

            # Morfoloji analizi oluştur
            analiz = MorfolojiAnalizi(
                kelime=kelime,
                kok=kok,
                ekler=ekler,
                ek_tipleri=ek_tipleri,
                ek_sayisi=len(ekler),
                kok_frekansi=kok_frekansi,
                ek_frekansi=ek_frekansi,
                yaygınlık_skoru=yaygınlık_skoru,
                zemberek_analiz=zemberek_sonuc,
            )

            # Morfoloji skorunu hesapla
            analiz.morfoloji_skoru = analiz.hesapla_morfoloji_skoru()
            analiz.karmasiklik_seviyesi = analiz.belirle_karmasiklik_seviyesi()

            logger.debug(
                f"Kelime analizi tamamlandı: {kelime} -> {analiz.karmasiklik_seviyesi.value}"
            )

            return analiz

        except Exception as e:
            logger.error(f"Kelime analiz hatası - Kelime: {kelime}, Hata: {e!s}")

            # Hata durumunda basit analiz döndür
            return MorfolojiAnalizi(
                kelime=kelime,
                kok=kelime,
                ekler=[],
                ek_tipleri=[],
                ek_sayisi=0,
                morfoloji_skoru=1.0,
                karmasiklik_seviyesi=MorfolojiKarmasiklikSeviyesi.BASIT,
            )

    async def analiz_et_soru_metni(
        self, soru_metni: str, soru_id: str
    ) -> SoruMorfolojiAnalizi:
        """
        Soru metni için kapsamlı morfolojik analiz yap

        Args:
            soru_metni: Analiz edilecek soru metni
            soru_id: Soru kimliği

        Returns:
            SoruMorfolojiAnalizi: Kapsamlı soru analiz sonucu
        """
        try:
            baslangic_zamani = datetime.now()

            # Metni kelimelere ayır
            kelimeler = self._temizle_ve_ayir_kelimeler(soru_metni)

            # Her kelime için analiz yap
            kelime_analizleri = []
            for kelime in kelimeler:
                if len(kelime) > 1:  # Tek harfli kelimeleri atla
                    analiz = await self.analiz_et_kelime(kelime)
                    kelime_analizleri.append(analiz)

            # İstatistikleri hesapla
            istatistikler = self._hesapla_soru_istatistikleri(kelime_analizleri)

            # Analiz süresini hesapla
            analiz_suresi = (datetime.now() - baslangic_zamani).total_seconds() * 1000

            # Soru morfoloji analizi oluştur
            soru_analizi = SoruMorfolojiAnalizi(
                soru_id=soru_id,
                soru_metni=soru_metni,
                kelime_analizleri=kelime_analizleri,
                toplam_kelime_sayisi=len(kelimeler),
                benzersiz_kelime_sayisi=len(set(kelimeler)),
                ortalama_morfoloji_skoru=istatistikler["ortalama_morfoloji_skoru"],
                maksimum_morfoloji_skoru=istatistikler["maksimum_morfoloji_skoru"],
                morfoloji_varyansı=istatistikler["morfoloji_varyansı"],
                karmasiklik_dagilimi=istatistikler["karmasiklik_dagilimi"],
                toplam_ek_sayisi=istatistikler["toplam_ek_sayisi"],
                ortalama_ek_sayisi=istatistikler["ortalama_ek_sayisi"],
                ek_tipi_cesitliligi=istatistikler["ek_tipi_cesitliligi"],
                ortalama_kok_frekansi=istatistikler["ortalama_kok_frekansi"],
                ortalama_yaygınlık_skoru=istatistikler["ortalama_yaygınlık_skoru"],
                zemberek_versiyonu="0.17.1",
                analiz_suresi_ms=int(analiz_suresi),
            )

            logger.info(
                f"Soru analizi tamamlandı - ID: {soru_id}, "
                f"Kelime sayısı: {len(kelimeler)}, "
                f"Ortalama morfoloji: {istatistikler['ortalama_morfoloji_skoru']:.2f}"
            )

            return soru_analizi

        except Exception as e:
            logger.error(f"Soru analiz hatası - ID: {soru_id}, Hata: {e!s}")
            raise

    async def _zemberek_analiz(self, kelime: str) -> dict[str, Any]:
        """Zemberek-NLP ile kelime analizi yap"""
        try:
            # Zemberek JAR dosyasını çalıştır
            # Gerçek uygulamada Zemberek Java API'si kullanılacak
            # Şimdilik mock analiz döndür

            # Basit morfolojik analiz simülasyonu
            if kelime.endswith(("lar", "ler")):
                kok = kelime[:-3]
                ekler = ["lar" if kelime.endswith("lar") else "ler"]
            elif kelime.endswith(("lık", "lik", "luk", "lük")):
                kok = kelime[:-3]
                ekler = [kelime[-3:]]
            elif kelime.endswith(("da", "de", "ta", "te")) or kelime.endswith(("ın", "in", "un", "ün")):
                kok = kelime[:-2]
                ekler = [kelime[-2:]]
            else:
                kok = kelime
                ekler = []

            return {
                "kelime": kelime,
                "kok": kok,
                "ekler": ekler,
                "analiz_tipi": "mock",
                "guven": 0.8,
            }

        except Exception as e:
            logger.error(f"Zemberek analiz hatası: {e!s}")
            return {
                "kelime": kelime,
                "kok": kelime,
                "ekler": [],
                "analiz_tipi": "fallback",
                "guven": 0.3,
            }

    def _parse_zemberek_sonuc(
        self, zemberek_sonuc: dict[str, Any]
    ) -> tuple[str, list[str]]:
        """Zemberek analiz sonucunu parse et"""
        kok = zemberek_sonuc.get("kok", zemberek_sonuc.get("kelime", ""))
        ekler = zemberek_sonuc.get("ekler", [])

        return kok, ekler

    def _belirle_ek_tipi(self, ek: str) -> TurkceEkTipi:
        """Ek tipini belirle"""
        # Ek sözlüğünden tip bul
        if ek in self.ek_tipi_sozlugu:
            return self.ek_tipi_sozlugu[ek]

        # Varsayılan olarak isim çekim eki
        return TurkceEkTipi.ISIM_CEKIM

    def _hesapla_ek_frekansi(self, ekler: list[str]) -> float:
        """Eklerin toplam frekansını hesapla"""
        if not ekler:
            return 1.0

        toplam_frekans = 0.0
        for ek in ekler:
            toplam_frekans += self.ek_frekanslari.get(ek, 1.0)

        return toplam_frekans / len(ekler)

    def _hesapla_yaygınlık_skoru(self, kok: str, ekler: list[str]) -> float:
        """Kelime yaygınlık skorunu hesapla"""
        # Kök frekansı faktörü
        kok_frekans = self.kelime_frekanslari.get(kok.lower(), 1.0)
        kok_faktoru = min(1.0, math.log(kok_frekans + 1) / 10.0)

        # Ek frekansı faktörü
        if not ekler:
            ek_faktoru = 1.0
        else:
            ortalama_ek_frekans = self._hesapla_ek_frekansi(ekler)
            ek_faktoru = min(1.0, math.log(ortalama_ek_frekans + 1) / 8.0)

        # Kombinasyon yaygınlığı
        yaygınlık = (kok_faktoru + ek_faktoru) / 2

        return max(0.1, min(1.0, yaygınlık))

    def _temizle_ve_ayir_kelimeler(self, metin: str) -> list[str]:
        """Metni temizle ve kelimelere ayır"""
        # Noktalama işaretlerini kaldır
        temiz_metin = re.sub(r"[^\w\s]", " ", metin)

        # Kelimelere ayır ve küçük harfe çevir
        kelimeler = [kelime.lower().strip() for kelime in temiz_metin.split()]

        # Boş kelimeleri filtrele
        return [kelime for kelime in kelimeler if kelime]

    def _hesapla_soru_istatistikleri(
        self, kelime_analizleri: list[MorfolojiAnalizi]
    ) -> dict[str, Any]:
        """Soru için istatistikleri hesapla"""
        if not kelime_analizleri:
            return {
                "ortalama_morfoloji_skoru": 0.0,
                "maksimum_morfoloji_skoru": 0.0,
                "morfoloji_varyansı": 0.0,
                "karmasiklik_dagilimi": {},
                "toplam_ek_sayisi": 0,
                "ortalama_ek_sayisi": 0.0,
                "ek_tipi_cesitliligi": 0,
                "ortalama_kok_frekansi": 1.0,
                "ortalama_yaygınlık_skoru": 1.0,
            }

        # Morfoloji skorları
        morfoloji_skorlari = [analiz.morfoloji_skoru for analiz in kelime_analizleri]
        ortalama_morfoloji = sum(morfoloji_skorlari) / len(morfoloji_skorlari)
        maksimum_morfoloji = max(morfoloji_skorlari)

        # Varyans hesaplama
        varyans = sum(
            (skor - ortalama_morfoloji) ** 2 for skor in morfoloji_skorlari
        ) / len(morfoloji_skorlari)

        # Karmaşıklık dağılımı
        karmasiklik_dagilimi = {}
        for analiz in kelime_analizleri:
            seviye = analiz.karmasiklik_seviyesi
            karmasiklik_dagilimi[seviye] = karmasiklik_dagilimi.get(seviye, 0) + 1

        # Ek istatistikleri
        toplam_ek_sayisi = sum(analiz.ek_sayisi for analiz in kelime_analizleri)
        ortalama_ek_sayisi = toplam_ek_sayisi / len(kelime_analizleri)

        # Ek tipi çeşitliliği
        tum_ek_tipleri = set()
        for analiz in kelime_analizleri:
            tum_ek_tipleri.update(analiz.ek_tipleri)
        ek_tipi_cesitliligi = len(tum_ek_tipleri)

        # Frekans ortalamaları
        ortalama_kok_frekansi = sum(
            analiz.kok_frekansi for analiz in kelime_analizleri
        ) / len(kelime_analizleri)
        ortalama_yaygınlık = sum(
            analiz.yaygınlık_skoru for analiz in kelime_analizleri
        ) / len(kelime_analizleri)

        return {
            "ortalama_morfoloji_skoru": ortalama_morfoloji,
            "maksimum_morfoloji_skoru": maksimum_morfoloji,
            "morfoloji_varyansı": varyans,
            "karmasiklik_dagilimi": karmasiklik_dagilimi,
            "toplam_ek_sayisi": toplam_ek_sayisi,
            "ortalama_ek_sayisi": ortalama_ek_sayisi,
            "ek_tipi_cesitliligi": ek_tipi_cesitliligi,
            "ortalama_kok_frekansi": ortalama_kok_frekansi,
            "ortalama_yaygınlık_skoru": ortalama_yaygınlık,
        }

    @lru_cache(maxsize=1000)
    async def get_kelime_karmasiklik_cache(self, kelime: str) -> float:
        """Kelime karmaşıklığını cache ile al"""
        analiz = await self.analiz_et_kelime(kelime)
        return analiz.morfoloji_skoru

    async def toplu_kelime_analizi(
        self, kelimeler: list[str]
    ) -> list[MorfolojiAnalizi]:
        """Birden fazla kelime için paralel analiz"""
        tasks = [self.analiz_et_kelime(kelime) for kelime in kelimeler]
        return await asyncio.gather(*tasks)

    def get_morfoloji_istatistikleri(self) -> dict[str, Any]:
        """Servis istatistiklerini döndür"""
        return {
            "kelime_frekanslari_sayisi": len(self.kelime_frekanslari),
            "ek_frekanslari_sayisi": len(self.ek_frekanslari),
            "ek_tipi_sayisi": len(set(self.ek_tipi_sozlugu.values())),
            "cache_boyutu": self.get_kelime_karmasiklik_cache.cache_info().currsize,
            "cache_hit_orani": self.get_kelime_karmasiklik_cache.cache_info().hits
            / max(
                1,
                self.get_kelime_karmasiklik_cache.cache_info().hits
                + self.get_kelime_karmasiklik_cache.cache_info().misses,
            ),
        }
