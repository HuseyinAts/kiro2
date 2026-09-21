"""Geometri ithal araclarinin gorsel URL bicimi -- regresyon koruma.

NEDEN BU TEST VAR
-----------------
`core/application.py` sunu yapar:

    crop_dir = os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    app.mount("/static/crops", StaticFiles(directory=crop_dir), name="crops")

Yani `CROP_IMAGE_DIR` bir DOSYA SISTEMI DIZINIDIR; `/static/crops` ise onun
baglandigi URL yoludur. `question_content.question_image_url` kolonuna URL
yazilir.

`acil_geo_ithal.py` ve `c1cell_geo_ithal.py` bir sure DIZINI url kolonuna
yazdi; DB'ye tarayicinin cozemedigi goreli bir yol girdi (3500 satir).
Satirlar PASIF oldugu icin gorunmedi ve ancak aktiflestirme oncesi olcumde
yakalandi -- 3032'si sekle bagimli sorulardi. Migration 0036 mevcut
satirlari onardi; bu test araclarin bir daha ayni hatayi yazmasini engeller.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import acil_geo_ithal as ag  # noqa: E402
from scripts.kitap import c1cell_geo_ithal as cg  # noqa: E402

DOGRU_ONEK = "/static/crops/"
ARACLAR = [("acil", ag), ("c1cell", cg)]
YOLLAR = {
    "acil": KOK / "scripts" / "kitap" / "acil_geo_ithal.py",
    "c1cell": KOK / "scripts" / "kitap" / "c1cell_geo_ithal.py",
}


def _ornek_kayit(modul) -> dict:
    """Kirpim kutusu OLAN asgari bir kayit -- URL uretimini tetikler."""
    ortak = {
        "gorsel": "s0123_sol_2.png",
        "sayfa": 123,
        "sutun": "sol",
        "sira": 2,
        "cevap": "A",
        "govde": "Ornek soru govdesi.",
        "sikler": dict.fromkeys("ABCDE", "sik"),
        "sekil_var": False,
        "sekil_aciklama": None,
        "sikler_gorsel": False,
        "kirpim_kutusu": [10, 20, 300, 400],
        "soru_no_basili": 2,
        "konu_kodu": f"{modul.KOD_ONEKI}-B01-01",
    }
    if modul is ag:
        ortak |= {
            "test": 1,
            "test_ici_sira": 2,
            "konu_eslesme_duzeyi": "konu",
            "kaynak_kusuru": None,
            "okunamayan": None,
        }
    else:
        ortak |= {"birim": 1, "birim_ici_sira": 2}
    return ortak


@pytest.mark.parametrize(("ad", "modul"), ARACLAR, ids=[a for a, _ in ARACLAR])
def test_url_static_crops_onekiyle_baslar(ad: str, modul) -> None:
    kayit = modul.kayit_uret(_ornek_kayit(modul))
    url = kayit["question_image_url"]
    assert url is not None
    assert url.startswith(DOGRU_ONEK), f"{ad}: URL {url!r} {DOGRU_ONEK} ile baslamiyor"
    assert url == f"{DOGRU_ONEK}{modul.CROP_ONEK}/s0123_sol_2.png"


@pytest.mark.parametrize(("ad", "modul"), ARACLAR, ids=[a for a, _ in ARACLAR])
def test_url_dosya_sistemi_yolu_icermez(ad: str, modul) -> None:
    """Eski hata tam olarak buydu: dizin adi URL'e sizmisti."""
    url = modul.kayit_uret(_ornek_kayit(modul))["question_image_url"]
    assert "d-dataset" not in url, f"{ad}: URL'de dosya sistemi dizini var: {url!r}"
    assert not url.startswith("."), f"{ad}: URL goreli yol: {url!r}"


@pytest.mark.parametrize(("ad", "modul"), ARACLAR, ids=[a for a, _ in ARACLAR])
def test_crop_image_dir_url_uretiminde_kullanilmiyor(
    ad: str, modul, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CROP_IMAGE_DIR degisse bile URL DEGISMEMELI (o bir dizin, URL degil)."""
    monkeypatch.setenv("CROP_IMAGE_DIR", "/bambaska/bir/dizin")
    url = modul.kayit_uret(_ornek_kayit(modul))["question_image_url"]
    assert "bambaska" not in url, f"{ad}: CROP_IMAGE_DIR hala URL'e siziyor: {url!r}"
    assert url.startswith(DOGRU_ONEK)


@pytest.mark.parametrize(("ad", "modul"), ARACLAR, ids=[a for a, _ in ARACLAR])
def test_kutusuz_kayitta_url_yok(ad: str, modul) -> None:
    kayit_girdi = _ornek_kayit(modul) | {"kirpim_kutusu": None}
    assert modul.kayit_uret(kayit_girdi)["question_image_url"] is None


def test_migration_0036_iki_kitabi_hedefler() -> None:
    """0036 yalniz bu iki kaynagi onarir ve dogru oneki yazar."""
    import importlib.util

    yol = KOK / "alembic" / "versions" / "0036_geo_gorsel_url_onarimi.py"
    spec = importlib.util.spec_from_file_location("mig0036", yol)
    assert spec and spec.loader
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)

    assert mig.revision == "0036_geo_gorsel_url"
    assert mig.down_revision == "0035_c1cellgeo_agac"
    assert len(mig.revision) <= 32
    assert mig.DOGRU_ONEK == DOGRU_ONEK
    assert {k for k, _ in mig.KAYNAKLAR} == {ag.KAYNAK_ADI, cg.KAYNAK_ADI}
    # crop onekleri ithal araclariyla ayni olmali, yoksa dosya adi 404 verir
    onekler = dict(mig.KAYNAKLAR)
    assert onekler[ag.KAYNAK_ADI] == ag.CROP_ONEK
    assert onekler[cg.KAYNAK_ADI] == cg.CROP_ONEK
    # donusum: dosya adi korunur, onek degisir
    assert (
        mig._yeni_url("d-dataset/output/crops/X/s0005_sol_1.png", "ACILGEO_2324")
        == "/static/crops/ACILGEO_2324/s0005_sol_1.png"
    )


def test_araclarda_eski_desen_kalmadi() -> None:
    """Kaynak metinde CROP_IMAGE_DIR ile URL kurma deseni bir daha olmasin."""
    for ad, yol in YOLLAR.items():
        metin = yol.read_text("utf-8")
        satirlar = [
            s
            for s in metin.splitlines()
            if "CROP_IMAGE_DIR" in s and not s.lstrip().startswith("#")
        ]
        assert not satirlar, f"{ad}: URL uretiminde CROP_IMAGE_DIR izi: {satirlar}"
