"""Kirpim gorsellerinin servis edildigi mount'un bekcisi.

NEDEN VAR (11 Eyl 2026)
----------------------
Ithal edilen kitaplarin sorularinda `question_image_url` her zaman
`/static/crops/<ONEK>/<kayit_id>.png` bicimindedir ve bu URL'yi gercekten
servis eden tek yer core/application.py'deki tek bir mount satiridir.

Depoda bu gercege dair birden fazla test var (test_curator_api.py,
tests/fast/test_y11_goc.py, tests/e2e/test_mikro_geo_ithal.py) -- ama hepsi
URL'nin BICIMINI dogruluyor; mount'un var oldugunu dogrulayan yoktu.
Sonuc olarak dokumanlar ve devir notlari gercegi "core/application.py:441"
gibi SATIR NUMARASIYLA anlatiyordu. Satir numarasi ilk refactor'de bayatlar
ve bayat bir referans, dogrulanmis bir gercek gibi gorunur.

Bu bekci ayni gercegi ICERIKTEN dogrular: artik dokumanin satir numarasi
vermesine gerek yok, bu testin adini vermesi yeter.

NE DOGRULAR
-----------
- mount yolu tam olarak "/static/crops" (ithal scriptlerinin yazdigi onek),
- dizin ortam degiskeninden okunur (CROP_IMAGE_DIR) -- yani CI/uretim
  kirpimlari baska bir diskten servis edebilir,
- dizin yoksa uygulama mount ETMEZ (StaticFiles var olmayan dizinde
  aciliste patlar; koruma bilerek orada).

Kod okur, uygulama baslatmaz -- bu yuzden tests/fast altinda.
"""

from __future__ import annotations

from pathlib import Path

_UYGULAMA = Path(__file__).resolve().parents[2] / "core" / "application.py"
_KAYNAK = _UYGULAMA.read_text(encoding="utf-8")


def test_kirpim_mount_yolu_degismemis():
    """Ithal scriptleri /static/crops yaziyor; uygulama ayni yolu mount etmeli."""
    assert '"/static/crops"' in _KAYNAK, (
        "core/application.py artik /static/crops mount etmiyor -- ithal edilen "
        "tum kitaplarin question_image_url'leri 404 olur"
    )


def test_kirpim_dizini_ortamdan_okunuyor():
    """Dizin sabit degil, CROP_IMAGE_DIR ile degistirilebilir olmali."""
    assert "CROP_IMAGE_DIR" in _KAYNAK, (
        "kirpim dizini artik ortam degiskeninden okunmuyor -- CI ve uretim "
        "kirpimlari farkli diskten servis edemez"
    )


def test_dizin_yoksa_mount_edilmiyor():
    """Var olmayan dizinde StaticFiles aciliste patlar; koruma yerinde kalmali."""
    assert "is_dir()" in _KAYNAK, (
        "mount artik dizin varligini kontrol etmiyor -- kirpim klasoru olmayan "
        "ortamlarda uygulama acilista patlar"
    )
