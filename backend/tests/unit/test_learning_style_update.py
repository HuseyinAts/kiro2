"""`LearningStyleService.update_behavioral_data` sozlesmesi (GF-K2 / gf82).

NEDEN VAR (1 Agu 2026 olcumu)
------------------------------
`api/learning_style.py:202` bu metodu cagiriyordu ama metot HIC yazilmamisti:

    AttributeError: 'LearningStyleService' object has no attribute
    'update_behavioral_data'

Golden Flow `gf82` bunu 500 olarak yakaladi. Ayni yolda IKINCI bir kusur daha
vardi: uc `updated_profile.hybrid_code` diye NITELIK okuyordu, oysa servis
`_profile_to_dict` ile **dict** donduruyor — metot yazilsa bile satir yine
patlardi (golden-flows.md "rule-of-four" sozlesme kaymasi sinifi).

ASIL INCELIK: ONBELLEK
-----------------------
`detect_learning_style` ilk is olarak `learning_style:{id}` anahtarini okur.
Onbellek temizlenmezse "guncelleme" ESKI profili geri dondururdu: HTTP 200,
hicbir sey degismez — 500'den daha kotu, cunku sessiz. Asagidaki test tam
olarak bunu civiliyor: `delete` cagrisi kaldirilirsa KIRMIZI doner.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.learning_style_service import LearningStyleService

ORNEK_VERI = {
    "student_id": "ogrenci-1",
    "video_watch_time": 15.0,
    "text_reading_time": 10.0,
}


@pytest.mark.asyncio
async def test_onbellek_once_temizleniyor_sonra_yeniden_hesaplaniyor() -> None:
    """Guncelleme ONCE onbellegi silmeli, SONRA yeniden hesaplamali.

    Sira onemli: once hesaplayip sonra silmek, hesaplamanin bayat onbellekten
    donmesine izin verirdi.
    """
    servis = LearningStyleService()
    cagri_sirasi: list[str] = []

    async def _sil(anahtar: str) -> bool:
        cagri_sirasi.append(f"delete:{anahtar}")
        return True

    async def _tespit(**kwargs) -> dict:
        cagri_sirasi.append("detect")
        return {"hibrit_kod": "VA-AKT", "guven_seviyesi": 0.8}

    with (
        patch(
            "services.learning_style_service.cache_manager.delete",
            new=AsyncMock(side_effect=_sil),
        ),
        patch.object(
            servis, "detect_learning_style", new=AsyncMock(side_effect=_tespit)
        ),
    ):
        sonuc = await servis.update_behavioral_data(
            student_id="ogrenci-1", db=object(), new_data=ORNEK_VERI
        )

    assert cagri_sirasi == ["delete:learning_style:ogrenci-1", "detect"], (
        f"Beklenen sira 'delete -> detect', gorulen: {cagri_sirasi}. "
        "Onbellek temizlenmezse guncelleme ESKI profili doner ve 200 ile "
        "sessizce yalan soyler."
    )
    assert sonuc["hibrit_kod"] == "VA-AKT", "Yeniden hesaplanan profil dondurulmedi"


@pytest.mark.asyncio
async def test_davranissal_veri_hesaplayiciya_aynen_gecirilyor() -> None:
    """Veri kaybi olmamali: gelen dict oldugu gibi `detect_learning_style`'a gitmeli."""
    servis = LearningStyleService()
    yakalanan: dict = {}

    async def _tespit(**kwargs) -> dict:
        yakalanan.update(kwargs)
        return {}

    with (
        patch(
            "services.learning_style_service.cache_manager.delete",
            new=AsyncMock(return_value=True),
        ),
        patch.object(
            servis, "detect_learning_style", new=AsyncMock(side_effect=_tespit)
        ),
    ):
        await servis.update_behavioral_data(
            student_id="ogrenci-1", db="DB", new_data=ORNEK_VERI
        )

    assert (
        yakalanan.get("behavioral_data") == ORNEK_VERI
    ), f"Davranissal veri hesaplayiciya ulasmadi: {yakalanan.get('behavioral_data')}"
    assert yakalanan.get("student_id") == "ogrenci-1", "student_id kayboldu"
    assert yakalanan.get("db") == "DB", "db oturumu gecirilmedi -> uc 500 verir"
