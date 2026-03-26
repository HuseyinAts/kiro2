"""
Gelişmiş Sınav Raporlama API'leri
IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from core.dependencies import AuthenticatedUser, get_current_user
from core.osym_exam_engine import session_to_sinav_sonucu
from models import SinavSonucu, SinavTipi
from services.irt_morfoloji_service import IRTMorfolojiService
from services.learning_style_service import LearningStyleService
from services.zpd_maarif_service import ZPDMaarifService
from utils.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["Gelişmiş Raporlar"])

# Servis instance'ları
irt_morfoloji_service = IRTMorfolojiService()
zpd_maarif_service = ZPDMaarifService()
learning_style_service = LearningStyleService()
pdf_generator = PDFReportGenerator()


@router.get("/exam/{sinav_id}/advanced")
async def get_advanced_exam_report(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Gelişmiş sınav raporu getir
    IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri dahil
    """
    try:
        logger.info(
            f"Gelişmiş sınav raporu istendi - Sınav: {sinav_id}, Kullanıcı: {current_user.id}"
        )

        # Temel sınav sonucunu al
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        # Paralel olarak gelişmiş analizleri yap
        tasks = [
            _get_irt_morfoloji_analizi(sinav_id, temel_sonuc),
            _get_zpd_analizi(current_user.id, temel_sonuc),
            _get_hibrit_ogrenme_stili_analizi(current_user.id, temel_sonuc),
            _get_osym_ets_karsilastirmasi(sinav_id, temel_sonuc),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Sonuçları işle
        irt_analizi = results[0] if not isinstance(results[0], Exception) else None
        zpd_analizi = results[1] if not isinstance(results[1], Exception) else None
        ogrenme_stili_analizi = (
            results[2] if not isinstance(results[2], Exception) else None
        )
        osym_ets_karsilastirma = (
            results[3] if not isinstance(results[3], Exception) else None
        )

        # Hataları logla
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Gelişmiş analiz hatası {i}: {result!s}")

        # Kapsamlı rapor oluştur
        gelismis_rapor = {
            "sinav_id": sinav_id,
            "ogrenci_id": current_user.id,
            "rapor_tarihi": datetime.now().isoformat(),
            "temel_sonuc": _serialize_temel_sonuc(temel_sonuc),
            "irt_morfoloji_analizi": irt_analizi,
            "zpd_analizi": zpd_analizi,
            "hibrit_ogrenme_stili_analizi": ogrenme_stili_analizi,
            "osym_ets_karsilastirmasi": osym_ets_karsilastirma,
            "kisisellestirilmis_oneriler": await _generate_personalized_recommendations(
                current_user.id,
                temel_sonuc,
                irt_analizi,
                zpd_analizi,
                ogrenme_stili_analizi,
            ),
            "performans_trendi": await _get_performance_trend(
                current_user.id, temel_sonuc.sinav_tipi
            ),
            "gelisim_onerileri": await _generate_development_suggestions(
                current_user.id, temel_sonuc, irt_analizi, zpd_analizi
            ),
        }

        logger.info(f"Gelişmiş sınav raporu oluşturuldu - Sınav: {sinav_id}")
        return gelismis_rapor

    except Exception as e:
        logger.error(f"Gelişmiş rapor hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/exam/{sinav_id}/irt-analysis")
async def get_irt_morfoloji_analysis(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    IRT + Morfoloji analizi detayları
    """
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        irt_analizi = await _get_irt_morfoloji_analizi(sinav_id, temel_sonuc)

        return {
            "sinav_id": sinav_id,
            "analiz_tarihi": datetime.now().isoformat(),
            "irt_morfoloji_analizi": irt_analizi,
        }

    except Exception as e:
        logger.error(f"IRT analizi hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/exam/{sinav_id}/zpd-recommendations")
async def get_zpd_recommendations(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    ZPD tabanlı kişiselleştirilmiş öneriler
    """
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        zpd_analizi = await _get_zpd_analizi(current_user.id, temel_sonuc)

        return {
            "sinav_id": sinav_id,
            "ogrenci_id": current_user.id,
            "analiz_tarihi": datetime.now().isoformat(),
            "zpd_analizi": zpd_analizi,
        }

    except Exception as e:
        logger.error(f"ZPD analizi hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/exam/{sinav_id}/learning-style-analysis")
async def get_learning_style_analysis(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Hibrit öğrenme stili bazlı performans analizi
    """
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        ogrenme_stili_analizi = await _get_hibrit_ogrenme_stili_analizi(
            current_user.id, temel_sonuc
        )

        return {
            "sinav_id": sinav_id,
            "ogrenci_id": current_user.id,
            "analiz_tarihi": datetime.now().isoformat(),
            "hibrit_ogrenme_stili_analizi": ogrenme_stili_analizi,
        }

    except Exception as e:
        logger.error(f"Öğrenme stili analizi hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/exam/{sinav_id}/osym-ets-comparison")
async def get_osym_ets_comparison(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    ÖSYM/ETS standartları ile karşılaştırma raporu
    """
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        karsilastirma = await _get_osym_ets_karsilastirmasi(sinav_id, temel_sonuc)

        return {
            "sinav_id": sinav_id,
            "analiz_tarihi": datetime.now().isoformat(),
            "osym_ets_karsilastirmasi": karsilastirma,
        }

    except Exception as e:
        logger.error(f"ÖSYM/ETS karşılaştırma hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.post("/exam/{sinav_id}/generate-pdf")
async def generate_pdf_report(
    sinav_id: str,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    """
    PDF rapor oluştur ve indirme linki döndür
    """
    try:
        # Gelişmiş raporu al
        gelismis_rapor = await get_advanced_exam_report(sinav_id, current_user)

        # PDF oluşturma task'ını background'a ekle
        pdf_filename = (
            f"sinav_raporu_{sinav_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        background_tasks.add_task(
            pdf_generator.generate_advanced_exam_report, gelismis_rapor, pdf_filename
        )

        return {
            "message": "PDF rapor oluşturuluyor",
            "pdf_filename": pdf_filename,
            "download_url": f"/api/v1/reports/download/{pdf_filename}",
        }

    except Exception as e:
        logger.error(f"PDF oluşturma hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin.")


@router.get("/download/{filename}")
async def download_pdf_report(
    filename: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> FileResponse:
    """
    PDF raporu indir
    """
    try:
        file_path = f"reports/pdf/{filename}"
        return FileResponse(
            path=file_path, filename=filename, media_type="application/pdf"
        )

    except Exception as e:
        logger.error(f"PDF indirme hatası - Dosya: {filename}, Hata: {e!s}")
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")


# Yardımcı fonksiyonlar


async def _get_irt_morfoloji_analizi(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """IRT + Morfoloji analizi yap"""
    try:
        # Sınav sorularını al ve analiz et
        soru_analizleri = []

        # Mock IRT analizi (gerçek implementasyonda soru bankasından alınır)
        for i, konu_performansi in enumerate(temel_sonuc.konu_performanslari):
            soru_analizi = {
                "konu": konu_performansi.konu,
                "irt_parametreleri": {
                    "difficulty": -0.5
                    + (konu_performansi.basari_yuzdesi / 100) * 2,  # -0.5 ile 1.5 arası
                    "discrimination": 0.8
                    + (konu_performansi.basari_yuzdesi / 100)
                    * 0.7,  # 0.8 ile 1.5 arası
                    "guessing": 0.2,
                    "morfoloji_faktoru": 0.1
                    + (i * 0.05),  # Konu bazlı morfoloji faktörü
                },
                "morfoloji_analizi": {
                    "ortalama_morfoloji_skoru": 5.0 + (i * 0.5),
                    "kelime_karmasikligi": 6.0 + (i * 0.3),
                    "ek_cesitliligi": 4.0 + (i * 0.2),
                    "toplam_kelime_sayisi": 25 + (i * 5),
                    "ortalama_ek_sayisi": 2.0 + (i * 0.1),
                },
                "soru_kalite_skoru": 70.0 + (konu_performansi.basari_yuzdesi * 0.3),
                "zorluk_seviyesi": "orta"
                if konu_performansi.basari_yuzdesi > 50
                else "zor",
            }
            soru_analizleri.append(soru_analizi)

        # Genel IRT istatistikleri
        ortalama_zorluk = sum(
            s["irt_parametreleri"]["difficulty"] for s in soru_analizleri
        ) / len(soru_analizleri)
        ortalama_ayirt_edicilik = sum(
            s["irt_parametreleri"]["discrimination"] for s in soru_analizleri
        ) / len(soru_analizleri)
        ortalama_morfoloji_faktoru = sum(
            s["irt_parametreleri"]["morfoloji_faktoru"] for s in soru_analizleri
        ) / len(soru_analizleri)

        return {
            "soru_analizleri": soru_analizleri,
            "genel_istatistikler": {
                "ortalama_zorluk": ortalama_zorluk,
                "ortalama_ayirt_edicilik": ortalama_ayirt_edicilik,
                "ortalama_morfoloji_faktoru": ortalama_morfoloji_faktoru,
                "toplam_soru_sayisi": len(soru_analizleri),
            },
            "morfoloji_farkindaliği": {
                "genel_seviye": "orta",
                "guclu_alanlar": ["temel_kelime_yapisi", "ek_tanima"],
                "gelisim_alanlari": ["karmasik_turetim", "anlam_degisimi"],
                "oneri_skorlari": {
                    "kelime_haznesi_gelistirme": 75,
                    "morfoloji_egzersizleri": 80,
                    "kok_ek_analizi": 70,
                },
            },
            "irt_performans_profili": {
                "yetenek_tahmini": temel_sonuc.ham_puan / 20
                - 2,  # -2 ile +3 arası theta
                "guven_araligi": [
                    temel_sonuc.ham_puan / 20 - 2.5,
                    temel_sonuc.ham_puan / 20 - 1.5,
                ],
                "standart_hata": 0.3,
            },
        }

    except Exception as e:
        logger.error(f"IRT morfoloji analizi hatası: {e!s}")
        return {"hata": str(e)}


async def _get_zpd_analizi(ogrenci_id: str, temel_sonuc: SinavSonucu) -> dict[str, Any]:
    """ZPD analizi yap"""
    try:
        # Mevcut seviyeyi hesapla
        mevcut_seviye = temel_sonuc.ham_puan / 10  # 0-10 arası normalize et

        # Her konu için ZPD hesapla
        konu_zpd_analizleri = []

        for konu_performansi in temel_sonuc.konu_performanslari:
            konu_seviye = konu_performansi.basari_yuzdesi / 10

            # ZPD aralığını hesapla (mock)
            zpd_araligi = {
                "konu": konu_performansi.konu,
                "mevcut_seviye": konu_seviye,
                "alt_sinir": max(0, konu_seviye - 0.5),
                "ust_sinir": min(10, konu_seviye + 1.5),
                "optimal_zorluk": konu_seviye + 1.0,
                "kulturel_carpan": 1.2,  # Türk kültürü faktörü
                "maarif_uyum_katsayisi": 0.8,
                "grup_calismasi_bonusu": 0.3,
                "ogretmen_rehberlik_faktoru": 0.2,
                "hesaplama_guveni": 0.85,
                "kulturel_uyum_guveni": 0.78,
            }

            konu_zpd_analizleri.append(zpd_araligi)

        # Kişiselleştirilmiş öneriler
        kisisellestirilmis_oneriler = []

        for zpd in konu_zpd_analizleri:
            if zpd["mevcut_seviye"] < 5:
                kisisellestirilmis_oneriler.append(
                    {
                        "konu": zpd["konu"],
                        "oneri_tipi": "temel_pekistirme",
                        "aciklama": f"{zpd['konu']} konusunda temel kavramları pekiştirin",
                        "onerilen_zorluk": zpd["optimal_zorluk"],
                        "ogrenme_yontemi": "grup_calismasi"
                        if zpd["grup_calismasi_bonusu"] > 0.2
                        else "bireysel",
                        "tahmini_sure": "2-3 hafta",
                    }
                )
            elif zpd["mevcut_seviye"] > 8:
                kisisellestirilmis_oneriler.append(
                    {
                        "konu": zpd["konu"],
                        "oneri_tipi": "ileri_seviye_gelistirme",
                        "aciklama": f"{zpd['konu']} konusunda ileri seviye problemlere odaklanın",
                        "onerilen_zorluk": zpd["optimal_zorluk"],
                        "ogrenme_yontemi": "bireysel_arastirma",
                        "tahmini_sure": "1-2 hafta",
                    }
                )
            else:
                kisisellestirilmis_oneriler.append(
                    {
                        "konu": zpd["konu"],
                        "oneri_tipi": "dengeli_gelistirme",
                        "aciklama": f"{zpd['konu']} konusunda mevcut seviyenizi koruyarak ilerleyin",
                        "onerilen_zorluk": zpd["optimal_zorluk"],
                        "ogrenme_yontemi": "karma_yontem",
                        "tahmini_sure": "1-2 hafta",
                    }
                )

        return {
            "konu_zpd_analizleri": konu_zpd_analizleri,
            "genel_zpd_profili": {
                "ortalama_mevcut_seviye": sum(
                    z["mevcut_seviye"] for z in konu_zpd_analizleri
                )
                / len(konu_zpd_analizleri),
                "ortalama_optimal_zorluk": sum(
                    z["optimal_zorluk"] for z in konu_zpd_analizleri
                )
                / len(konu_zpd_analizleri),
                "kulturel_uyum_seviyesi": "yuksek",
                "maarif_degerleri_uyumu": "iyi",
            },
            "kisisellestirilmis_oneriler": kisisellestirilmis_oneriler,
            "kulturel_faktorler": {
                "grup_calismasi_tercihi": 0.8,
                "ogretmene_saygi_seviyesi": 0.9,
                "aile_katilim_derecesi": 0.7,
                "akran_rekabet_egilimi": 0.6,
            },
            "maarif_degerleri_profili": {
                "milli_degerler_uyumu": 0.8,
                "evrensel_degerler_uyumu": 0.9,
                "kok_degerler_uyumu": 0.8,
            },
        }

    except Exception as e:
        logger.error(f"ZPD analizi hatası: {e!s}")
        return {"hata": str(e)}


async def _get_hibrit_ogrenme_stili_analizi(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Hibrit öğrenme stili analizi yap"""
    try:
        # Mock hibrit öğrenme stili profili
        vark_profili = {
            "visual": 0.7,  # Görsel
            "auditory": 0.5,  # İşitsel
            "reading": 0.8,  # Okuma/Yazma
            "kinesthetic": 0.4,  # Kinestetik
        }

        felder_silverman_profili = {
            "active_reflective": 0.3,  # Aktif ↔ Yansıtıcı (-1 ile +1 arası)
            "sensing_intuitive": -0.2,  # Algısal ↔ Sezgisel
            "visual_verbal": 0.6,  # Görsel ↔ Sözel
            "sequential_global": -0.4,  # Sıralı ↔ Bütünsel
        }

        # 64 kombinasyondan hibrit kod oluştur
        hibrit_kod = "V-R-A-S-V-S"  # Visual-Reading-Active-Sensing-Visual-Sequential

        # Performans uyumu analizi
        performans_uyumu = []

        for konu_performansi in temel_sonuc.konu_performanslari:
            # Konu tipine göre öğrenme stili uyumu hesapla
            if "matematik" in konu_performansi.konu.lower():
                uyum_skoru = (
                    vark_profili["visual"]
                    + abs(felder_silverman_profili["sequential_global"])
                ) / 2
            elif "türkçe" in konu_performansi.konu.lower():
                uyum_skoru = (
                    vark_profili["reading"]
                    + abs(felder_silverman_profili["visual_verbal"])
                ) / 2
            else:
                uyum_skoru = sum(vark_profili.values()) / 4

            performans_uyumu.append(
                {
                    "konu": konu_performansi.konu,
                    "basari_yuzdesi": konu_performansi.basari_yuzdesi,
                    "ogrenme_stili_uyumu": uyum_skoru * 100,
                    "onerilen_yontem": _get_onerilen_ogrenme_yontemi(
                        konu_performansi.konu, vark_profili, felder_silverman_profili
                    ),
                    "uyum_analizi": "yuksek"
                    if uyum_skoru > 0.7
                    else "orta"
                    if uyum_skoru > 0.5
                    else "dusuk",
                }
            )

        # Genel hibrit profil özeti
        hibrit_profil_ozeti = {
            "dominant_vark_stili": max(vark_profili, key=vark_profili.get),
            "dominant_felder_boyutu": max(
                felder_silverman_profili, key=lambda k: abs(felder_silverman_profili[k])
            ),
            "hibrit_kod": hibrit_kod,
            "guven_seviyesi": 0.82,
            "profil_aciklamasi": _get_hibrit_profil_aciklamasi(hibrit_kod),
        }

        # Kişiselleştirilmiş öğrenme önerileri
        ogrenme_onerileri = []

        for uyum in performans_uyumu:
            if uyum["uyum_analizi"] == "dusuk":
                ogrenme_onerileri.append(
                    {
                        "konu": uyum["konu"],
                        "oneri": f"{uyum['konu']} için {uyum['onerilen_yontem']} yöntemini deneyin",
                        "detay": "Mevcut öğrenme stilinizle uyumlu değil, alternatif yaklaşımlar önerilir",
                        "oncelik": "yuksek",
                    }
                )

        return {
            "vark_profili": vark_profili,
            "felder_silverman_profili": felder_silverman_profili,
            "hibrit_profil_ozeti": hibrit_profil_ozeti,
            "performans_uyumu": performans_uyumu,
            "ogrenme_onerileri": ogrenme_onerileri,
            "stil_bazli_performans_analizi": {
                "en_uyumlu_konular": [
                    p["konu"] for p in performans_uyumu if p["uyum_analizi"] == "yuksek"
                ],
                "gelisim_gerektiren_konular": [
                    p["konu"] for p in performans_uyumu if p["uyum_analizi"] == "dusuk"
                ],
                "ortalama_uyum_skoru": sum(
                    p["ogrenme_stili_uyumu"] for p in performans_uyumu
                )
                / len(performans_uyumu),
            },
        }

    except Exception as e:
        logger.error(f"Hibrit öğrenme stili analizi hatası: {e!s}")
        return {"hata": str(e)}


async def _get_osym_ets_karsilastirmasi(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """ÖSYM/ETS standartları ile karşılaştırma yap"""
    try:
        # ÖSYM standartları
        osym_standartlari = {
            "ayirt_edicilik_min": 0.3,
            "ayirt_edicilik_ideal": 1.0,
            "zorluk_araligi": (-2.0, 2.0),
            "sans_faktoru_max": 0.25,
            "guvenilirlik_min": 0.8,
        }

        # ETS standartları
        ets_standartlari = {
            "ayirt_edicilik_min": 0.4,
            "ayirt_edicilik_ideal": 1.2,
            "zorluk_araligi": (-2.5, 2.5),
            "sans_faktoru_max": 0.2,
            "guvenilirlik_min": 0.85,
        }

        # Mock sınav parametreleri
        sinav_parametreleri = {
            "ortalama_ayirt_edicilik": 0.85,
            "ortalama_zorluk": 0.2,
            "ortalama_sans_faktoru": 0.22,
            "guvenilirlik_katsayisi": 0.82,
            "morfoloji_avantaji": 0.15,
        }

        # ÖSYM karşılaştırması
        osym_karsilastirma = {
            "ayirt_edicilik_durumu": _karsilastir_parametre(
                sinav_parametreleri["ortalama_ayirt_edicilik"],
                osym_standartlari["ayirt_edicilik_min"],
                osym_standartlari["ayirt_edicilik_ideal"],
            ),
            "zorluk_durumu": _karsilastir_zorluk(
                sinav_parametreleri["ortalama_zorluk"],
                osym_standartlari["zorluk_araligi"],
            ),
            "sans_faktoru_durumu": _karsilastir_sans_faktoru(
                sinav_parametreleri["ortalama_sans_faktoru"],
                osym_standartlari["sans_faktoru_max"],
            ),
            "genel_uyum_skoru": 0.0,
        }

        # ETS karşılaştırması
        ets_karsilastirma = {
            "ayirt_edicilik_durumu": _karsilastir_parametre(
                sinav_parametreleri["ortalama_ayirt_edicilik"],
                ets_standartlari["ayirt_edicilik_min"],
                ets_standartlari["ayirt_edicilik_ideal"],
            ),
            "zorluk_durumu": _karsilastir_zorluk(
                sinav_parametreleri["ortalama_zorluk"],
                ets_standartlari["zorluk_araligi"],
            ),
            "sans_faktoru_durumu": _karsilastir_sans_faktoru(
                sinav_parametreleri["ortalama_sans_faktoru"],
                ets_standartlari["sans_faktoru_max"],
            ),
            "genel_uyum_skoru": 0.0,
        }

        # Genel uyum skorlarını hesapla
        osym_karsilastirma["genel_uyum_skoru"] = _hesapla_genel_uyum_skoru(
            osym_karsilastirma
        )
        ets_karsilastirma["genel_uyum_skoru"] = _hesapla_genel_uyum_skoru(
            ets_karsilastirma
        )

        # Türkçe morfoloji avantajı
        morfoloji_avantaji = {
            "morfoloji_faktoru_etkisi": sinav_parametreleri["morfoloji_avantaji"],
            "dil_analizi_derinligi": "yuksek",
            "osym_ets_uzerindeki_avantaj": "Türkçe morfolojik analiz ile ÖSYM/ETS'nin sunmadığı detaylı dil analizi",
            "ek_bilgi_boyutlari": [
                "Kelime kökü analizi",
                "Ek türetim karmaşıklığı",
                "Morfolojik belirsizlik çözümü",
                "Türkçe'ye özel dil yapısı analizi",
            ],
        }

        # Sonuç değerlendirmesi
        sonuc_degerlendirmesi = _belirle_karsilastirma_sonucu(
            osym_karsilastirma["genel_uyum_skoru"],
            ets_karsilastirma["genel_uyum_skoru"],
        )

        return {
            "sinav_parametreleri": sinav_parametreleri,
            "osym_karsilastirma": osym_karsilastirma,
            "ets_karsilastirma": ets_karsilastirma,
            "morfoloji_avantaji": morfoloji_avantaji,
            "sonuc_degerlendirmesi": sonuc_degerlendirmesi,
            "iyilestirme_onerileri": _generate_improvement_suggestions(
                osym_karsilastirma, ets_karsilastirma, sinav_parametreleri
            ),
        }

    except Exception as e:
        logger.error(f"ÖSYM/ETS karşılaştırma hatası: {e!s}")
        return {"hata": str(e)}


# Yardımcı fonksiyonlar


def _serialize_temel_sonuc(sonuc: SinavSonucu) -> dict[str, Any]:
    """Temel sonucu serialize et"""
    return {
        "sinav_id": sonuc.sinav_id,
        "sinav_tipi": sonuc.sinav_tipi.value,
        "toplam_soru": sonuc.toplam_soru,
        "dogru_sayisi": sonuc.dogru_sayisi,
        "yanlis_sayisi": sonuc.yanlis_sayisi,
        "bos_sayisi": sonuc.bos_sayisi,
        "net_sayisi": sonuc.net_sayisi,
        "ham_puan": sonuc.ham_puan,
        "konu_performanslari": [
            {
                "konu": kp.konu,
                "toplam_soru": kp.toplam_soru,
                "dogru_sayisi": kp.dogru_sayisi,
                "yanlis_sayisi": kp.yanlis_sayisi,
                "bos_sayisi": kp.bos_sayisi,
                "basari_yuzdesi": kp.basari_yuzdesi,
            }
            for kp in sonuc.konu_performanslari
        ],
        "zayif_konular": sonuc.zayif_konular,
        "guclu_konular": sonuc.guclu_konular,
    }


def _get_onerilen_ogrenme_yontemi(konu: str, vark: dict, felder: dict) -> str:
    """Konu ve öğrenme stiline göre önerilen yöntem"""
    if vark["visual"] > 0.7:
        return "görsel_materyaller"
    if vark["auditory"] > 0.7:
        return "sesli_anlatim"
    if vark["reading"] > 0.7:
        return "metin_tabanli_calisma"
    if vark["kinesthetic"] > 0.7:
        return "uygulamali_egzersizler"
    return "karma_yontem"


def _get_hibrit_profil_aciklamasi(hibrit_kod: str) -> str:
    """Hibrit profil kodu açıklaması"""
    return f"Hibrit öğrenme profili {hibrit_kod}: Görsel ve okuma ağırlıklı, aktif öğrenme tarzı"


def _karsilastir_parametre(
    deger: float, minimum: float, ideal: float
) -> dict[str, Any]:
    """Parametre karşılaştırması"""
    if deger >= ideal:
        durum = "ideal"
        skor = 100.0
    elif deger >= minimum:
        durum = "kabul_edilebilir"
        skor = 70.0
    else:
        durum = "yetersiz"
        skor = 30.0

    return {"durum": durum, "skor": skor, "deger": deger}


def _karsilastir_zorluk(deger: float, aralik: tuple) -> dict[str, Any]:
    """Zorluk karşılaştırması"""
    min_z, max_z = aralik

    if min_z <= deger <= max_z:
        durum = "uygun"
        skor = 100.0
    elif min_z - 0.5 <= deger <= max_z + 0.5:
        durum = "kabul_edilebilir"
        skor = 70.0
    else:
        durum = "uygun_degil"
        skor = 30.0

    return {"durum": durum, "skor": skor, "deger": deger}


def _karsilastir_sans_faktoru(deger: float, maksimum: float) -> dict[str, Any]:
    """Şans faktörü karşılaştırması"""
    if deger <= maksimum:
        durum = "uygun"
        skor = 100.0
    elif deger <= maksimum + 0.1:
        durum = "kabul_edilebilir"
        skor = 70.0
    else:
        durum = "yuksek"
        skor = 30.0

    return {"durum": durum, "skor": skor, "deger": deger}


def _hesapla_genel_uyum_skoru(karsilastirma: dict) -> float:
    """Genel uyum skorunu hesapla"""
    skorlar = [
        karsilastirma["ayirt_edicilik_durumu"]["skor"],
        karsilastirma["zorluk_durumu"]["skor"],
        karsilastirma["sans_faktoru_durumu"]["skor"],
    ]
    return sum(skorlar) / len(skorlar)


def _belirle_karsilastirma_sonucu(osym_skor: float, ets_skor: float) -> str:
    """Karşılaştırma sonucunu belirle"""
    if osym_skor >= 90 and ets_skor >= 90:
        return "Her iki standardı da aşıyor"
    if osym_skor >= 70 and ets_skor >= 70:
        return "Her iki standarda da uygun"
    if osym_skor >= 70 or ets_skor >= 70:
        return "Bir standarda uygun"
    return "Standartların altında"


def _generate_improvement_suggestions(osym: dict, _: dict, params: dict) -> list[str]:
    """İyileştirme önerileri oluştur"""
    oneriler = []

    if osym["ayirt_edicilik_durumu"]["skor"] < 70:
        oneriler.append(
            "Soru ayırt ediciliğini artırmak için daha net seçenekler kullanın"
        )

    if osym["zorluk_durumu"]["skor"] < 70:
        oneriler.append("Soru zorluğunu hedef öğrenci seviyesine göre ayarlayın")

    if osym["sans_faktoru_durumu"]["skor"] < 70:
        oneriler.append(
            "Şans faktörünü azaltmak için çeldirici seçenekleri güçlendirin"
        )

    oneriler.append("Türkçe morfoloji analizi avantajını koruyun ve geliştirin")

    return oneriler


async def _generate_personalized_recommendations(
    ogrenci_id: str,
    temel_sonuc: SinavSonucu,
    irt_analizi: dict,
    zpd_analizi: dict,
    ogrenme_stili_analizi: dict,
) -> list[dict[str, Any]]:
    """Kişiselleştirilmiş öneriler oluştur"""
    oneriler = []

    # Zayıf konular için öneriler
    for zayif_konu in temel_sonuc.zayif_konular:
        oneri = {
            "konu": zayif_konu,
            "oneri_tipi": "konu_pekistirme",
            "aciklama": f"{zayif_konu} konusunda temel kavramları pekiştirin",
            "oncelik": "yuksek",
            "tahmini_sure": "2-3 hafta",
            "kaynak_onerileri": [
                "video_dersler",
                "interaktif_egzersizler",
                "konu_anlatimi",
            ],
        }
        oneriler.append(oneri)

    # Güçlü konular için öneriler
    for guclu_konu in temel_sonuc.guclu_konular:
        oneri = {
            "konu": guclu_konu,
            "oneri_tipi": "ileri_seviye_gelistirme",
            "aciklama": f"{guclu_konu} konusunda ileri seviye problemlere odaklanın",
            "oncelik": "orta",
            "tahmini_sure": "1-2 hafta",
            "kaynak_onerileri": [
                "zor_problemler",
                "olimpiyat_sorulari",
                "arastirma_projeleri",
            ],
        }
        oneriler.append(oneri)

    return oneriler


async def _get_performance_trend(
    ogrenci_id: str, sinav_tipi: SinavTipi
) -> dict[str, Any]:
    """Performans trendini getir"""
    # Mock trend verisi
    return {
        "son_5_sinav": [65, 70, 68, 75, 78],
        "trend_yonu": "yukselis",
        "ortalama_artis": 3.25,
        "en_iyi_performans": 78,
        "en_dusuk_performans": 65,
        "tutarlilik_skoru": 0.75,
    }


async def _generate_development_suggestions(
    ogrenci_id: str, temel_sonuc: SinavSonucu, irt_analizi: dict, zpd_analizi: dict
) -> list[str]:
    """Gelişim önerileri oluştur"""
    oneriler = []

    if temel_sonuc.ham_puan < 60:
        oneriler.append("Temel kavramlara odaklanın ve düzenli tekrar yapın")
        oneriler.append("Günlük çalışma programı oluşturun")
    elif temel_sonuc.ham_puan < 80:
        oneriler.append("Orta seviye problemleri çözmeye odaklanın")
        oneriler.append("Zayıf konularınızı belirleyip özel çalışma yapın")
    else:
        oneriler.append("İleri seviye problemlerle kendinizi zorlayın")
        oneriler.append("Farklı soru tiplerini deneyimleyin")

    oneriler.append("Türkçe morfoloji farkındalığınızı geliştirin")
    oneriler.append("Öğrenme stilinize uygun materyaller kullanın")

    return oneriler
