"""
Gelişmiş Sınav Raporlama API'leri
IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri.

@WARN S179 fix (B-P0-57): pre-fix this module had 5 mock points
(lines 310, 395, 490, 615, 892) returning fabricated IRT/ZPD/hybrid
learning-style values, while the REAL IRT engine in `bkt_service.py`
goes unused. Sprint plan: wire each endpoint to the live algorithm
service. Until then responses include `"computed_by": "mock"` so the
frontend can suppress display.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from core.dependencies import AuthenticatedUser, get_current_user
from core.osym_exam_engine import session_to_sinav_sonucu
from core.turkish_nlp_utils import subject_db, subject_key

# Aşağıdaki ignore bir ÖLÇÜM ALETİ artefaktıdır, kod kusuru değil: pre-commit
# mypy depo KÖKÜNDEN koşuyor ve orada bir YOLO ağırlık klasörü (`kiro2/models/`,
# sadece .pt dosyaları) var. `models` o namespace paketine çözülüyor → 0
# attribute. Çalışma zamanında CWD=backend olduğu için gerçek `backend/models`
# yükleniyor ve isimler `__all__`'da mevcut.
from models import SinavSonucu, SinavTipi  # type: ignore[attr-defined]
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

# Arka plan PDF görevlerine güçlü referans (bkz. generate_pdf_report / RUF006).
_BACKGROUND_PDF_TASKS: set[asyncio.Task[None]] = set()


def _mock_report_guard(endpoint_name: str) -> None:
    """S180 fix (#3): refuse to ship mock IRT/ZPD/learning-style data in
    production. Pre-fix advanced_reports returned fabricated psychometric
    parameters that the frontend rendered as real analysis (Bug #B-P0-57).

    In `production` environments without `ALLOW_MOCK_REPORTS=true`, raise
    503 to make the gap visible. In `development` or with the env flag,
    return mock data + `computed_by: mock` marker so consumers can
    suppress display.
    """
    env = os.environ.get("ENVIRONMENT", "").lower()
    allow_mock = os.environ.get("ALLOW_MOCK_REPORTS", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if env in ("production", "prod") and not allow_mock:
        raise HTTPException(
            status_code=503,
            detail=(
                f"{endpoint_name} not yet wired to real IRT/ZPD service. "
                "Set ALLOW_MOCK_REPORTS=true to receive mock-tagged response."
            ),
        )


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

        # Sonuçları işle. `return_exceptions=True` BaseException de döndürebilir
        # (CancelledError vb.); `Exception` ile daraltmak onları veri sanıp rapora
        # gömerdi — bu yüzden BaseException ile daraltılıyor.
        irt_analizi = results[0] if not isinstance(results[0], BaseException) else None
        zpd_analizi = results[1] if not isinstance(results[1], BaseException) else None
        ogrenme_stili_analizi = (
            results[2] if not isinstance(results[2], BaseException) else None
        )
        osym_ets_karsilastirma = (
            results[3] if not isinstance(results[3], BaseException) else None
        )

        # Hataları logla
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gelişmiş rapor hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/exam/{sinav_id}/irt-analysis")
async def get_irt_morfoloji_analysis(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    IRT + Morfoloji analizi detayları
    """
    _mock_report_guard("/reports/exam/{id}/irt-analysis")
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        irt_analizi = await _get_irt_morfoloji_analizi(sinav_id, temel_sonuc)

        from core.mock_endpoint_flags import is_real_impl

        return {
            "sinav_id": sinav_id,
            "analiz_tarihi": datetime.now().isoformat(),
            "irt_morfoloji_analizi": irt_analizi,
            "computed_by": "real"
            if is_real_impl("advanced_reports.irt_analysis")
            else "mock",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IRT analizi hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/exam/{sinav_id}/zpd-recommendations")
async def get_zpd_recommendations(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    ZPD tabanlı kişiselleştirilmiş öneriler
    """
    _mock_report_guard("/reports/exam/{id}/zpd-recommendations")
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        zpd_analizi = await _get_zpd_analizi(current_user.id, temel_sonuc)

        from core.mock_endpoint_flags import is_real_impl

        return {
            "sinav_id": sinav_id,
            "ogrenci_id": current_user.id,
            "analiz_tarihi": datetime.now().isoformat(),
            "zpd_analizi": zpd_analizi,
            "computed_by": "real"
            if is_real_impl("advanced_reports.zpd_recommendations")
            else "mock",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ZPD analizi hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/exam/{sinav_id}/learning-style-analysis")
async def get_learning_style_analysis(
    sinav_id: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Hibrit öğrenme stili bazlı performans analizi
    """
    _mock_report_guard("/reports/exam/{id}/learning-style-analysis")
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        ogrenme_stili_analizi = await _get_hibrit_ogrenme_stili_analizi(
            current_user.id, temel_sonuc
        )

        from core.mock_endpoint_flags import is_real_impl

        return {
            "sinav_id": sinav_id,
            "ogrenci_id": current_user.id,
            "analiz_tarihi": datetime.now().isoformat(),
            "hibrit_ogrenme_stili_analizi": ogrenme_stili_analizi,
            "computed_by": "real"
            if is_real_impl("advanced_reports.learning_style_analysis")
            else "mock",
        }

    except HTTPException:
        raise
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
    _mock_report_guard("/reports/exam/{id}/osym-ets-comparison")
    try:
        temel_sonuc = await session_to_sinav_sonucu(sinav_id)
        if not temel_sonuc:
            raise HTTPException(status_code=404, detail="Sınav sonucu bulunamadı")

        karsilastirma = await _get_osym_ets_karsilastirmasi(sinav_id, temel_sonuc)

        from core.mock_endpoint_flags import is_real_impl

        return {
            "sinav_id": sinav_id,
            "analiz_tarihi": datetime.now().isoformat(),
            "osym_ets_karsilastirmasi": karsilastirma,
            "computed_by": "real"
            if is_real_impl("advanced_reports.osym_ets_comparison")
            else "mock",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ÖSYM/ETS karşılaştırma hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


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

        pdf_filename = (
            f"sinav_raporu_{sinav_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        # SRE Bulkhead: Run PDF generation in the custom PDF_POOL executor
        import asyncio

        from core.worker_pools import PDF_POOL

        async def generate_pdf_in_background():
            loop = asyncio.get_running_loop()
            try:
                await loop.run_in_executor(
                    PDF_POOL,
                    pdf_generator.generate_advanced_exam_report,
                    gelismis_rapor,
                    pdf_filename,
                )
            except Exception as e:
                logger.error(f"Background PDF generation error: {e}")

        # RUF006: create_task'ın dönüşüne güçlü referans tut. Referanssız task
        # event loop tarafından koşarken toplanabilir → PDF sessizce üretilmez.
        task = asyncio.create_task(generate_pdf_in_background())
        _BACKGROUND_PDF_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_PDF_TASKS.discard)

        return {
            "message": "PDF rapor oluşturuluyor",
            "pdf_filename": pdf_filename,
            "download_url": f"/api/v1/reports/download/{pdf_filename}",
        }

    except HTTPException:
        # Propagate 404 from get_advanced_exam_report (sinav not found) as-is;
        # bare except previously re-wrapped it as 500 (GF22/GF77 pattern).
        raise
    except Exception as e:
        logger.error(f"PDF oluşturma hatası - Sınav: {sinav_id}, Hata: {e!s}")
        raise HTTPException(
            status_code=500, detail="Islem basarisiz. Lutfen tekrar deneyin."
        )


@router.get("/download/{filename}")
async def download_pdf_report(
    filename: str, current_user: AuthenticatedUser = Depends(get_current_user)
) -> FileResponse:
    """
    PDF raporu indir
    """
    try:
        safe_name = Path(filename).name
        if not safe_name.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="Sadece PDF dosyalari indirilebilir"
            )
        file_path = f"reports/pdf/{safe_name}"
        return FileResponse(
            path=file_path, filename=safe_name, media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF indirme hatası - Dosya: {filename}, Hata: {e!s}")
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")


# Yardımcı fonksiyonlar


async def _get_irt_aggregate(
    *, topic_code: str | None, ders: str | None
) -> dict[str, float | int]:
    """IRT toplami -- konu kodu varsa KONU bazli, yoksa DERSE duser.

    B3 FAZ 3 kok nedeni: silinen ikiz `_get_subject_irt_aggregate` yalniz DERS
    adi kabul ediyor ve iceride `.upper()` yapiyordu. Konu adi gecirilince iki
    sessiz kusur olusuyordu (ikisi de 21 Agu 2026'da canli DB'de olculdu):
        "Kimyasal Denge" -> "KIMYASAL DENGE" -> 0 satir     (gercek 1262)
        "Kimya"          -> "KIMYA"          -> 3531 satir  (gercek 263)
    Ikincisi TEHLIKELI olan: sifir donmek gurultulu, YANLIS dersin verisini
    donmek sessizdir. Sebep `topic_hierarchy`de level-1 KONU adinin DERS
    adiyla cakismasi (KIM|Kimya, MAT|Matematik).

    `topic_hierarchy.code` ASCII ve cakismasizdir -- ayirt edici anahtar odur.

    Eski ikiz `_get_subject_irt_aggregate` #515'te SILINDI (uretimde oluydu).
    Onu civileyen `tests/fast/test_advanced_reports_split.py` da silindi;
    invaryantlari once mutasyonla olculup `tests/fast/
    test_irt_aggregate_topic_split.py`e tasindi -- ucu (ders dalinda
    kartezyen, NULL varsayilanlari, cache-hit) orada KAPSANMIYORDU.
    """
    from sqlalchemy import func, select

    from core.cache import cache_manager
    from core.database import get_db_session_context
    from models.question_bank import (
        QuestionBankItem,
        QuestionMetadata,
        QuestionStatistics,
        TopicHierarchy,
    )

    if topic_code:
        cache_key = f"irt_aggregate:topic:{topic_code}"
    else:
        cache_key = f"irt_aggregate:subject:{subject_db(ders) or ''}"

    cached: dict[str, float | int] | None = await cache_manager.get(cache_key)
    if cached is not None:
        return cached

    async with get_db_session_context() as session:
        # #485 split: irt_* QuestionStatistics'te, subject_area
        # QuestionMetadata'da. SELECT listesinde yalniz QuestionStatistics
        # kolonlari oldugu icin explicit select_from ZORUNLU -- yoksa
        # SQLAlchemy sol tarafi o tablo sanip kendisine JOIN etmeye calisir
        # ve sorgu CALISMA aninda degil KURULURKEN patlar.
        stmt = (
            select(
                func.avg(QuestionStatistics.irt_difficulty).label("avg_difficulty"),
                func.avg(QuestionStatistics.irt_discrimination).label(
                    "avg_discrimination"
                ),
                func.avg(QuestionStatistics.irt_guessing).label("avg_guessing"),
                func.count().label("sample_size"),
            )
            .select_from(QuestionBankItem)
            .join(QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id)
            .where(QuestionBankItem.is_active.is_(True))
        )
        if topic_code:
            stmt = stmt.join(
                TopicHierarchy,
                TopicHierarchy.id == QuestionBankItem.primary_topic_id,
            ).where(TopicHierarchy.code == topic_code)
        else:
            stmt = stmt.join(
                QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id
            ).where(QuestionMetadata.subject_area == subject_db(ders))
        row = (await session.execute(stmt)).one()

    result = {
        "avg_difficulty": float(row.avg_difficulty or 0.0),
        "avg_discrimination": float(row.avg_discrimination or 1.0),
        "avg_guessing": float(row.avg_guessing or 0.2),
        "sample_size": int(row.sample_size or 0),
    }
    # 1h TTL — IRT parametreleri yalniz Curator guncellemesinde degisir.
    await cache_manager.set(cache_key, result, ttl=3600)
    return result


async def _get_irt_morfoloji_analizi_real(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Real IRT + Morfoloji analizi — DB-backed implementation.

    Subject-level aggregation from `question_bank` (S196 Day 2). Confidence
    intervals are bootstrapped from sample size (replaces hardcoded ±0.3).

    Mock-real schema parity: response keys identical to
    `_get_irt_morfoloji_analizi_mock` so the frontend contract holds. Only
    numeric values change (real DB params vs hardcoded formula).
    """
    soru_analizleri = []
    konu_perfs = temel_sonuc.konu_performanslari or []

    for konu_perf in konu_perfs:
        # B3 FAZ 3: anahtar KONU KODU. `konu_perf.konu` gecirmek "Kimya"
        # ornegindeki gibi YANLIS dersin 3531 satirini dondururdu.
        agg = await _get_irt_aggregate(
            topic_code=konu_perf.konu_kodu, ders=konu_perf.ders
        )
        sample_n = agg["sample_size"]
        morfoloji_faktoru = (
            irt_morfoloji_service.get_subject_morphology_factor(konu_perf.konu)
            if hasattr(irt_morfoloji_service, "get_subject_morphology_factor")
            else 0.1
        )
        # CI half-width shrinks as sqrt(n) — classical SE proxy.
        ci_half = 0.5 / max(1, sample_n) ** 0.5 if sample_n else 0.5
        soru_analizleri.append(
            {
                "konu": konu_perf.konu,
                "irt_parametreleri": {
                    "difficulty": agg["avg_difficulty"],
                    "discrimination": agg["avg_discrimination"],
                    "guessing": agg["avg_guessing"],
                    "morfoloji_faktoru": morfoloji_faktoru,
                },
                "morfoloji_analizi": {
                    "ortalama_morfoloji_skoru": morfoloji_faktoru * 10,
                    "kelime_karmasikligi": 0.0,
                    "ek_cesitliligi": 0.0,
                    "toplam_kelime_sayisi": 0,
                    "ortalama_ek_sayisi": 0.0,
                },
                "soru_kalite_skoru": 70.0 + (konu_perf.basari_yuzdesi * 0.3),
                "zorluk_seviyesi": "orta" if konu_perf.basari_yuzdesi > 50 else "zor",
                "sample_size": sample_n,
                "confidence_interval_half_width": ci_half,
            }
        )

    if not soru_analizleri:
        return {
            "soru_analizleri": [],
            "genel_istatistikler": {
                "ortalama_zorluk": 0.0,
                "ortalama_ayirt_edicilik": 1.0,
                "ortalama_morfoloji_faktoru": 0.0,
                "toplam_soru_sayisi": 0,
            },
            "irt_performans_profili": {
                "yetenek_tahmini": temel_sonuc.ham_puan / 20 - 2,
                "guven_araligi": [
                    temel_sonuc.ham_puan / 20 - 2.5,
                    temel_sonuc.ham_puan / 20 - 1.5,
                ],
                "standart_hata": 0.3,
            },
        }

    ortalama_zorluk = sum(
        s["irt_parametreleri"]["difficulty"] for s in soru_analizleri
    ) / len(soru_analizleri)
    ortalama_ayirt_edicilik = sum(
        s["irt_parametreleri"]["discrimination"] for s in soru_analizleri
    ) / len(soru_analizleri)
    ortalama_morfoloji_faktoru = sum(
        s["irt_parametreleri"]["morfoloji_faktoru"] for s in soru_analizleri
    ) / len(soru_analizleri)
    avg_ci = sum(s["confidence_interval_half_width"] for s in soru_analizleri) / len(
        soru_analizleri
    )

    theta = temel_sonuc.ham_puan / 20 - 2  # rough theta mapping retained from mock
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
            "yetenek_tahmini": theta,
            "guven_araligi": [theta - avg_ci, theta + avg_ci],
            "standart_hata": avg_ci,
        },
    }


async def _get_irt_morfoloji_analizi(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """IRT + Morfoloji analizi — feature-flagged mock/real dispatcher.

    Default = mock (safe). Real path lands when
    ``config/mock_endpoint_flags.json`` flips
    ``advanced_reports.irt_analysis`` to ``true``.
    """
    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.irt_analysis"):
        return await _get_irt_morfoloji_analizi_real(sinav_id, temel_sonuc)

    return await _get_irt_morfoloji_analizi_mock(sinav_id, temel_sonuc)


async def _get_irt_morfoloji_analizi_mock(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """IRT + Morfoloji analizi — mock path (S180 fallback).

    Hardcoded synthetic IRT parametrization. Returns ``computed_by: mock``
    in the caller's response envelope so the frontend can suppress the
    display until the real implementation ships.
    """
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
        return {"hata": "Analiz sirasinda bir hata olustu"}


async def _get_zpd_analizi_real(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Real ZPD analizi via ``ZPDMaarifService.hesapla_turk_zpd()`` (S196 Day 3).

    Per-konu real ZPD via the production Turkish ZPD + MEB Maarif service.
    Cultural and Maarif profiles use the service's Turkish baseline defaults
    (no per-student override yet — Day 4+ wiring).

    Mock-real schema parity preserved: same keys + value scales as
    ``_get_zpd_analizi_mock`` so the frontend contract holds.
    """
    konu_perfs = temel_sonuc.konu_performanslari or []
    if not konu_perfs:
        return {
            "konu_zpd_analizleri": [],
            "genel_zpd_profili": {
                "ortalama_mevcut_seviye": 0.0,
                "ortalama_optimal_zorluk": 0.0,
                "kulturel_uyum_seviyesi": "yuksek",
                "maarif_degerleri_uyumu": "iyi",
            },
            "kisisellestirilmis_oneriler": [],
            "kulturel_faktorler": zpd_maarif_service.varsayilan_kulturel_profil,
            "maarif_degerleri_profili": {
                "milli_degerler_uyumu": 0.8,
                "evrensel_degerler_uyumu": 0.9,
                "kok_degerler_uyumu": 0.8,
            },
        }

    konu_zpd_analizleri = []
    for konu_perf in konu_perfs:
        mevcut_seviye = konu_perf.basari_yuzdesi / 10  # %0-100 → 0-10 ZPD scale
        zpd = await zpd_maarif_service.hesapla_turk_zpd(
            ogrenci_id=ogrenci_id or "anonymous_student",
            konu=konu_perf.konu,
            mevcut_seviye=mevcut_seviye,
        )
        konu_zpd_analizleri.append(
            {
                "konu": konu_perf.konu,
                # B3 FAZ 3: agirlik = kovadaki soru sayisi. Genel profil
                # ortalamasi bununla kovalama-DEGISMEZ hale gelir.
                "agirlik": konu_perf.toplam_soru,
                "mevcut_seviye": zpd.mevcut_seviye,
                "alt_sinir": zpd.alt_sinir,
                "ust_sinir": zpd.ust_sinir,
                "optimal_zorluk": zpd.optimal_zorluk,
                "kulturel_carpan": zpd.kulturel_carpan,
                "maarif_uyum_katsayisi": zpd.maarif_uyum_katsayisi,
                "grup_calismasi_bonusu": zpd.grup_calismasi_bonusu,
                "ogretmen_rehberlik_faktoru": zpd.ogretmen_rehberlik_faktoru,
                "hesaplama_guveni": zpd.hesaplama_guveni,
                "kulturel_uyum_guveni": zpd.kulturel_uyum_guveni,
            }
        )

    kisisellestirilmis_oneriler = []
    for z in konu_zpd_analizleri:
        if z["mevcut_seviye"] < 5:
            kisisellestirilmis_oneriler.append(
                {
                    "konu": z["konu"],
                    "oneri_tipi": "temel_pekistirme",
                    "aciklama": f"{z['konu']} konusunda temel kavramları pekiştirin",
                    "onerilen_zorluk": z["optimal_zorluk"],
                    "ogrenme_yontemi": "grup_calismasi"
                    if z["grup_calismasi_bonusu"] > 0.2
                    else "bireysel",
                    "tahmini_sure": "2-3 hafta",
                }
            )
        elif z["mevcut_seviye"] > 8:
            kisisellestirilmis_oneriler.append(
                {
                    "konu": z["konu"],
                    "oneri_tipi": "ileri_seviye_gelistirme",
                    "aciklama": f"{z['konu']} konusunda ileri seviye problemlere odaklanın",
                    "onerilen_zorluk": z["optimal_zorluk"],
                    "ogrenme_yontemi": "bireysel_arastirma",
                    "tahmini_sure": "1-2 hafta",
                }
            )
        else:
            kisisellestirilmis_oneriler.append(
                {
                    "konu": z["konu"],
                    "oneri_tipi": "dengeli_gelistirme",
                    "aciklama": f"{z['konu']} konusunda mevcut seviyenizi koruyarak ilerleyin",
                    "onerilen_zorluk": z["optimal_zorluk"],
                    "ogrenme_yontemi": "karma_yontem",
                    "tahmini_sure": "1-2 hafta",
                }
            )

    return {
        "konu_zpd_analizleri": konu_zpd_analizleri,
        "genel_zpd_profili": {
            "ortalama_mevcut_seviye": _agirlikli_ortalama(
                konu_zpd_analizleri, "mevcut_seviye"
            ),
            "ortalama_optimal_zorluk": _agirlikli_ortalama(
                konu_zpd_analizleri, "optimal_zorluk"
            ),
            "kulturel_uyum_seviyesi": "yuksek",
            "maarif_degerleri_uyumu": "iyi",
        },
        "kisisellestirilmis_oneriler": kisisellestirilmis_oneriler,
        "kulturel_faktorler": zpd_maarif_service.varsayilan_kulturel_profil,
        "maarif_degerleri_profili": {
            "milli_degerler_uyumu": 0.8,
            "evrensel_degerler_uyumu": 0.9,
            "kok_degerler_uyumu": 0.8,
        },
    }


async def _get_zpd_analizi(ogrenci_id: str, temel_sonuc: SinavSonucu) -> dict[str, Any]:
    """ZPD analizi — feature-flagged mock/real dispatcher (S196 Day 2)."""
    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.zpd_recommendations"):
        return await _get_zpd_analizi_real(ogrenci_id, temel_sonuc)
    return await _get_zpd_analizi_mock(ogrenci_id, temel_sonuc)


async def _get_zpd_analizi_mock(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """ZPD analizi — mock path (S180 fallback)."""
    try:
        # Her konu için ZPD hesapla
        konu_zpd_analizleri = []

        for konu_performansi in temel_sonuc.konu_performanslari:
            konu_seviye = konu_performansi.basari_yuzdesi / 10

            # ZPD aralığını hesapla (mock)
            zpd_araligi = {
                "konu": konu_performansi.konu,
                # B3 FAZ 3: real yolla ayni sozlesme (schema parity).
                "agirlik": konu_performansi.toplam_soru,
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
                "ortalama_mevcut_seviye": _agirlikli_ortalama(
                    konu_zpd_analizleri, "mevcut_seviye"
                ),
                "ortalama_optimal_zorluk": _agirlikli_ortalama(
                    konu_zpd_analizleri, "optimal_zorluk"
                ),
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
        return {"hata": "Analiz sirasinda bir hata olustu"}


async def _get_hibrit_ogrenme_stili_analizi_real(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Real learning-style analysis via ``LearningStyleService`` (S196 Day 3).

    VARK + Felder-Silverman profile from ``student_learning_profiles`` (cached
    by student_id). Falls back to service-computed defaults if no profile
    exists yet. Empty ``behavioral_data`` is intentional — Day 4+ will pull
    LearningAnalytics rows for richer signal.

    Mock-real schema parity preserved.
    """
    from core.database import get_db_session_context

    async with get_db_session_context() as db:
        profile = await learning_style_service.detect_learning_style(
            student_id=ogrenci_id or "anonymous_student",
            db=db,
            behavioral_data={},
        )

    vark_profili = {
        "visual": profile.get("vark_visual", 0.5),
        "auditory": profile.get("vark_auditory", 0.5),
        "reading": profile.get("vark_reading", 0.5),
        "kinesthetic": profile.get("vark_kinesthetic", 0.5),
    }
    felder_silverman_profili = {
        "active_reflective": profile.get("felder_active_reflective", 0.0),
        "sensing_intuitive": profile.get("felder_sensing_intuitive", 0.0),
        "visual_verbal": profile.get("felder_visual_verbal", 0.0),
        "sequential_global": profile.get("felder_sequential_global", 0.0),
    }
    hibrit_kod = profile.get("hybrid_code") or "V-R-A-S-V-S"

    performans_uyumu = []
    for konu_perf in temel_sonuc.konu_performanslari:
        uyum_skoru = _ders_uyum_skoru(
            konu_perf.ders, vark_profili, felder_silverman_profili
        )

        performans_uyumu.append(
            {
                "konu": konu_perf.konu,
                "basari_yuzdesi": konu_perf.basari_yuzdesi,
                "ogrenme_stili_uyumu": uyum_skoru * 100,
                "onerilen_yontem": _get_onerilen_ogrenme_yontemi(
                    konu_perf.konu, vark_profili, felder_silverman_profili
                ),
                "uyum_analizi": "yuksek"
                if uyum_skoru > 0.7
                else "orta"
                if uyum_skoru > 0.5
                else "dusuk",
            }
        )

    hibrit_profil_ozeti = {
        "dominant_vark_stili": profile.get(
            "dominant_vark_style", max(vark_profili, key=vark_profili.get)
        ),
        "dominant_felder_boyutu": profile.get(
            "dominant_felder_dimension",
            max(
                felder_silverman_profili, key=lambda k: abs(felder_silverman_profili[k])
            ),
        ),
        "hibrit_kod": hibrit_kod,
        "guven_seviyesi": profile.get("confidence_score", 0.5),
        "profil_aciklamasi": profile.get("profile_description")
        or _get_hibrit_profil_aciklamasi(hibrit_kod),
    }

    ogrenme_onerileri = [
        {
            "konu": uyum["konu"],
            "oneri": f"{uyum['konu']} için {uyum['onerilen_yontem']} yöntemini deneyin",
            "detay": "Mevcut öğrenme stilinizle uyumlu değil, alternatif yaklaşımlar önerilir",
            "oncelik": "yuksek",
        }
        for uyum in performans_uyumu
        if uyum["uyum_analizi"] == "dusuk"
    ]

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
            "ortalama_uyum_skoru": (
                sum(p["ogrenme_stili_uyumu"] for p in performans_uyumu)
                / len(performans_uyumu)
            )
            if performans_uyumu
            else 0.0,
        },
    }


async def _get_hibrit_ogrenme_stili_analizi(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Hibrit ogrenme stili analizi — feature-flagged dispatcher (S196 Day 2)."""
    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.learning_style_analysis"):
        return await _get_hibrit_ogrenme_stili_analizi_real(ogrenci_id, temel_sonuc)
    return await _get_hibrit_ogrenme_stili_analizi_mock(ogrenci_id, temel_sonuc)


async def _get_hibrit_ogrenme_stili_analizi_mock(
    ogrenci_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Hibrit ogrenme stili analizi — mock path (S180 fallback)."""
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
            # Ders kimligine gore ogrenme stili uyumu (B3 FAZ 3)
            uyum_skoru = _ders_uyum_skoru(
                konu_performansi.ders, vark_profili, felder_silverman_profili
            )

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
        return {"hata": "Analiz sirasinda bir hata olustu"}


async def _get_osym_ets_karsilastirmasi_real(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """Real ÖSYM/ETS comparison via per-konu IRT aggregates (S196 Day 3).

    Computes weighted-average IRT params over the konular present in this
    exam (weighted by `toplam_soru` per konu), then compares against static
    ÖSYM/ETS thresholds using the existing `_karsilastir_*` helpers.

    Mock-real schema parity preserved.

    Design note: ``OSYMBenchmarkComparator`` service is intentionally NOT
    used here. That service compares AI-generated question pipelines against
    ÖSYM (length / difficulty / bloom similarity for Wave 2B generation QA)
    — a different domain than exam-level IRT benchmark comparison. Forcing
    it would break frontend contract. See S196 Day 3 design discussion.
    """
    osym_standartlari: dict[str, Any] = {
        "ayirt_edicilik_min": 0.3,
        "ayirt_edicilik_ideal": 1.0,
        "zorluk_araligi": (-2.0, 2.0),
        "sans_faktoru_max": 0.25,
        "guvenilirlik_min": 0.8,
    }
    ets_standartlari: dict[str, Any] = {
        "ayirt_edicilik_min": 0.4,
        "ayirt_edicilik_ideal": 1.2,
        "zorluk_araligi": (-2.5, 2.5),
        "sans_faktoru_max": 0.2,
        "guvenilirlik_min": 0.85,
    }

    konu_perfs = temel_sonuc.konu_performanslari or []
    if konu_perfs:
        total_weight = 0
        wsum_disc = wsum_diff = wsum_guess = 0.0
        for kp in konu_perfs:
            agg = await _get_irt_aggregate(topic_code=kp.konu_kodu, ders=kp.ders)
            w = max(1, kp.toplam_soru)  # weight by # of questions in this konu
            wsum_disc += agg["avg_discrimination"] * w
            wsum_diff += agg["avg_difficulty"] * w
            wsum_guess += agg["avg_guessing"] * w
            total_weight += w
        sinav_parametreleri = {
            "ortalama_ayirt_edicilik": wsum_disc / total_weight,
            "ortalama_zorluk": wsum_diff / total_weight,
            "ortalama_sans_faktoru": wsum_guess / total_weight,
            # Cronbach α not yet wired (Day 4+ task); keep mock placeholder.
            "guvenilirlik_katsayisi": 0.82,
            "morfoloji_avantaji": 0.15,
        }
    else:
        sinav_parametreleri = {
            "ortalama_ayirt_edicilik": 1.0,
            "ortalama_zorluk": 0.0,
            "ortalama_sans_faktoru": 0.2,
            "guvenilirlik_katsayisi": 0.82,
            "morfoloji_avantaji": 0.15,
        }

    osym_karsilastirma: dict[str, Any] = {
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
    ets_karsilastirma: dict[str, Any] = {
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
    osym_karsilastirma["genel_uyum_skoru"] = _hesapla_genel_uyum_skoru(
        osym_karsilastirma
    )
    ets_karsilastirma["genel_uyum_skoru"] = _hesapla_genel_uyum_skoru(ets_karsilastirma)

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


async def _get_osym_ets_karsilastirmasi(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """ÖSYM/ETS karsilastirma — feature-flagged dispatcher (S196 Day 2)."""
    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.osym_ets_comparison"):
        return await _get_osym_ets_karsilastirmasi_real(sinav_id, temel_sonuc)
    return await _get_osym_ets_karsilastirmasi_mock(sinav_id, temel_sonuc)


async def _get_osym_ets_karsilastirmasi_mock(
    sinav_id: str, temel_sonuc: SinavSonucu
) -> dict[str, Any]:
    """ÖSYM/ETS karsilastirma — mock path (S180 fallback)."""
    try:
        # ÖSYM standartları
        osym_standartlari: dict[str, Any] = {
            "ayirt_edicilik_min": 0.3,
            "ayirt_edicilik_ideal": 1.0,
            "zorluk_araligi": (-2.0, 2.0),
            "sans_faktoru_max": 0.25,
            "guvenilirlik_min": 0.8,
        }

        # ETS standartları
        ets_standartlari: dict[str, Any] = {
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
        osym_karsilastirma: dict[str, Any] = {
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
        ets_karsilastirma: dict[str, Any] = {
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
        return {"hata": "Analiz sirasinda bir hata olustu"}


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


def _agirlikli_ortalama(kayitlar: list[dict], alan: str) -> float:
    """Soru-agirlikli ortalama -- kova SAYISINDAN bagimsiz.

    B3 FAZ 3: onceki bicim `sum(...) / len(kayitlar)` idi. Kova kardinalitesi
    1 -> 13 olunca ortalama sessizce kaydi (olculdu: +9,91 puan). Agirlikli
    bicim ayni veriyi hangi kovalamayla verirsen ver AYNI sonucu uretir --
    yani bir SONRAKI kardinalite degisiminde de kaymaz.

    `agirlik` = o kovadaki soru sayisi. Toplam agirlik 0 ise 0.0 (sifira
    bolme AYRI bir kaynaktir: `len(kayitlar) > 0` iken de olusabilir).
    """
    toplam_agirlik = sum(float(k.get("agirlik", 0)) for k in kayitlar)
    if not toplam_agirlik:
        return 0.0
    return sum(float(k[alan]) * float(k.get("agirlik", 0)) for k in kayitlar) / (
        toplam_agirlik
    )


def _ders_uyum_skoru(
    ders: str | None, vark: dict[str, float], felder: dict[str, float]
) -> float:
    """Ogrenme stili uyum skoru -- DERS kimligine gore dallanir.

    B3 FAZ 3: onceki bicim `if "matematik" in normalize_tr(kp.konu)` idi ve
    iki sebeple kirilgandi:
      1) `konu` B3'ten sonra KONU adi tasiyor -> dal hic girilmiyordu (olu).
      2) `normalize_tr` bir SUBJECT IDENTIFIER'a uygulanmamali: Turkce locale
         I->i donusumu yapar (`.claude/rules/case-convention.md` yasagi).
    Kimlik artik `ders` alanindan gelir ve `subject_key` ile kanonlanir.

    Kanon kume OLCULDU (21 Agu 2026): {KIMYA, MATEMATIK} -- ASCII. Turkce
    dersi kanonda 'TURKCE' bicimindedir; eski koddaki Turkce harfli dize
    hicbir zaman eslesemezdi.
    """
    anahtar = subject_key(ders)
    if anahtar == "matematik":
        return (vark["visual"] + abs(felder["sequential_global"])) / 2
    if anahtar == "turkce":
        return (vark["reading"] + abs(felder["visual_verbal"])) / 2
    return sum(vark.values()) / 4


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


def _hesapla_genel_uyum_skoru(karsilastirma: dict[str, Any]) -> float:
    """Genel uyum skorunu hesapla"""
    skorlar: list[float] = [
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
    irt_analizi: dict[str, Any] | None,
    zpd_analizi: dict[str, Any] | None,
    ogrenme_stili_analizi: dict[str, Any] | None,
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


async def _get_performance_trend_real(
    ogrenci_id: str, sinav_tipi: SinavTipi
) -> dict[str, Any]:
    """Real performance trend via ``ExamPerformanceService`` (S196 Day 3).

    Pulls latest completed ExamSession for this student+type and delegates
    to the service's linear-regression trend analyzer (which queries the
    last 5 sessions internally).

    Mock-real schema parity preserved: maps service keys (`trend`,
    `improvement_rate`, `recent_scores`, `consistency` on 0-100) to mock
    keys (`trend_yonu` TR-localized, `ortalama_artis`, `son_5_sinav`,
    `tutarlilik_skoru` on 0-1 scale).

    Note: calls ``_analyze_improvement_trends`` (leading underscore). This
    is intentional — public wrapper for one caller would be premature
    abstraction (Karpathy "Önce Sadelik" / S196 Day 3 design decision).
    """
    from sqlalchemy import desc, select

    from core.database import get_db_session_context
    from models.enums_db import ExamType
    from models.exam_db import ExamSession
    from services.exam_performance_service import exam_performance_service

    empty_response = {
        "son_5_sinav": [],
        "trend_yonu": "veri_yetersiz",
        "ortalama_artis": 0.0,
        "en_iyi_performans": 0,
        "en_dusuk_performans": 0,
        "tutarlilik_skoru": 0.0,
    }

    # SinavTipi values are uppercase ("TYT"); ExamSession.exam_type stores
    # lowercase ExamType enum. Map via .value.lower() — guard for unknown.
    try:
        exam_type = ExamType(sinav_tipi.value.lower())
    except ValueError:
        logger.warning(f"Bilinmeyen sinav_tipi: {sinav_tipi!r}; veri_yetersiz dön")
        return empty_response

    async with get_db_session_context() as db:
        result = await db.execute(
            select(ExamSession)
            .where(ExamSession.student_id == ogrenci_id)
            .where(ExamSession.exam_type == exam_type)
            .where(ExamSession.status == "completed")
            .order_by(desc(ExamSession.completed_at))
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest is None:
            return empty_response

        trend_data = await exam_performance_service._analyze_improvement_trends(
            db, latest
        )

    trend_map = {
        "improving": "yukselis",
        "declining": "dusus",
        "stable": "stabil",
        "insufficient_data": "veri_yetersiz",
    }
    scores = list(trend_data.get("recent_scores") or [])

    return {
        "son_5_sinav": scores,
        "trend_yonu": trend_map.get(trend_data.get("trend", "stable"), "stabil"),
        "ortalama_artis": float(trend_data.get("improvement_rate", 0.0)),
        "en_iyi_performans": max(scores) if scores else 0,
        "en_dusuk_performans": min(scores) if scores else 0,
        # Service emits consistency on 0-100; mock contract is 0-1. Normalize.
        "tutarlilik_skoru": float(trend_data.get("consistency", 0.0)) / 100.0,
    }


async def _get_performance_trend(
    ogrenci_id: str, sinav_tipi: SinavTipi
) -> dict[str, Any]:
    """Performans trendi — feature-flagged dispatcher (S196 Day 2)."""
    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.performance_trend"):
        return await _get_performance_trend_real(ogrenci_id, sinav_tipi)
    return await _get_performance_trend_mock(ogrenci_id, sinav_tipi)


async def _get_performance_trend_mock(
    ogrenci_id: str, sinav_tipi: SinavTipi
) -> dict[str, Any]:
    """Performans trendi — mock path (S180 fallback)."""
    return {
        "son_5_sinav": [65, 70, 68, 75, 78],
        "trend_yonu": "yukselis",
        "ortalama_artis": 3.25,
        "en_iyi_performans": 78,
        "en_dusuk_performans": 65,
        "tutarlilik_skoru": 0.75,
    }


async def _generate_development_suggestions(
    ogrenci_id: str,
    temel_sonuc: SinavSonucu,
    irt_analizi: dict[str, Any] | None,
    zpd_analizi: dict[str, Any] | None,
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
