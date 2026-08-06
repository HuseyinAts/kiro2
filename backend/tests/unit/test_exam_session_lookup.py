"""Sınav oturumu arama sözleşmesi — bilinmeyen ID istisna DEĞİL None döndürür.

NEDEN VAR (gf88, 2 Ağu 2026 ölçümü):
`osym_exam_engine.get_session_data()` üç katmanlı bir arama yapar
(L1 bellek → L2 Redis → L3 DB). Üçü de boş dönerse `session` **None** kalır.
Fonksiyonun `finally:` bloğu ise koşulsuz `session.status` okuyordu
(core/osym_exam_engine.py:1080) → `AttributeError: 'NoneType' object has no
attribute 'status'`.

`finally` içinde fırlayan istisna **normal dönüşün yerine geçer**: fonksiyon
`None` döndüremez, çağıranın `if not session_data: 404` dalına hiç ulaşılamaz.
Ölçülen sonuç: var olmayan her session_id, 28 çağrı yerinin hepsinde
(16'sı `api/sinav.py`) 404 yerine **500** üretiyordu.

Kanıt (canlı, 2 Ağu): POST /api/v1/reports/exam/gf88-probe-sinav-id/generate-pdf
→ 500; konteyner log'u: "Gelişmiş rapor hatası ... 'NoneType' object has no
attribute 'status'".
"""

from __future__ import annotations

import core.exam_session_store
import pytest

from core.osym_exam_engine import ExamStatus, osym_exam_engine

BILINMEYEN_ID = "gf88-olmayan-oturum-kimligi"


@pytest.fixture
def uc_katman_bos(monkeypatch: pytest.MonkeyPatch) -> None:
    """L1/L2/L3'ün üçünü de boşalt — 'oturum yok' senaryosunu üret."""
    # `_session_loading` / `auto_save_tasks` ilk çağrıda tembel kurulur —
    # setattr ile ön-kurmak testin ölçtüğü şeyi değiştirmez, yalnızca
    # fixture'ın AttributeError ile ERROR vermesini önler (ERROR ≠ FAIL).
    osym_exam_engine.active_sessions.pop(BILINMEYEN_ID, None)
    if not hasattr(osym_exam_engine, "_session_loading"):
        osym_exam_engine._session_loading = {}
    osym_exam_engine._session_loading.pop(BILINMEYEN_ID, None)

    async def _bos(_session_id: str):
        return None

    # L2: modül içi `from core.exam_session_store import load_session`
    monkeypatch.setattr(core.exam_session_store, "load_session", _bos)
    # L3: DB yeniden kurulumu
    monkeypatch.setattr(osym_exam_engine, "_reconstruct_session_from_db", _bos)


async def test_bilinmeyen_oturum_none_dondurur(uc_katman_bos: None) -> None:
    """Üç katman da boşken sonuç None olmalı — istisna DEĞİL.

    Bu testin düşme biçimi teşhisi taşır:
      - AttributeError  → `finally` bloğu None'a dokunuyor (asıl kusur)
      - assert hatası   → sessizce yanlış nesne dönüyor
    """
    sonuc = await osym_exam_engine.get_session_data(BILINMEYEN_ID)

    assert sonuc is None, (
        "Var olmayan oturum için None beklenir; aksi hâlde çağıranların "
        "`if not session_data: 404` dalı ölü kalır ve 500 üretilir."
    )


async def test_bilinmeyen_oturum_otomatik_kapanis_gorevi_yaratmaz(
    uc_katman_bos: None,
) -> None:
    """Oturum yokken auto-complete zamanlayıcısı KURULMAMALI.

    `finally` bloğunun asıl işi budur; kapının `session is not None` yerine
    yalnızca istisnayı yutmakla düzeltilmesi bu testi düşürür (mutasyon M2).
    """
    anahtar = f"autoclose:{BILINMEYEN_ID}"
    osym_exam_engine.auto_save_tasks.pop(anahtar, None)

    await osym_exam_engine.get_session_data(BILINMEYEN_ID)

    assert anahtar not in osym_exam_engine.auto_save_tasks, (
        "Var olmayan oturum için otomatik kapanış görevi kurulmuş — "
        "zamanlayıcı sızıntısı."
    )


async def test_yukleme_kaydi_temizlenir(uc_katman_bos: None) -> None:
    """`_session_loading` girdisi her durumda temizlenmeli (stampede koruması).

    `finally` patlarsa `pop` ondan ÖNCE koştuğu için bu bugün de geçer; test
    fix'in bu davranışı bozmadığını çiviler (regresyon koruması).
    """
    await osym_exam_engine.get_session_data(BILINMEYEN_ID)

    assert BILINMEYEN_ID not in osym_exam_engine._session_loading


async def test_alet_dogrulamasi_examstatus_gercek(uc_katman_bos: None) -> None:
    """Kontrol kolu: ölçüm aleti gerçek sembolü kullanıyor mu?

    `ExamStatus.IN_PROGRESS` import edilemezse yukarıdaki testler yanlış
    sebeple yeşil olabilirdi (audit-methodology.md — 'ölçüm aletini doğrula').
    """
    assert ExamStatus.IN_PROGRESS is not None
    assert hasattr(osym_exam_engine, "auto_save_tasks")
