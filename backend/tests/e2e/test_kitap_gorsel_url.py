"""TUM kitap ithal araclarinin gorsel URL bicimi -- repo geneli koruma.

NEDEN BU DOSYA VAR
------------------
`core/application.py` sunu yapar:

    crop_dir = os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    app.mount("/static/crops", StaticFiles(directory=crop_dir), name="crops")

`CROP_IMAGE_DIR` bir DOSYA SISTEMI DIZINIDIR; `/static/crops` onun baglandigi
URL yoludur. `question_content.question_image_url` kolonuna URL yazilir.

Bu hata DORT ithal aracinda birden vardi ve IKI turda yakalandi:
  * 0036 -- acil_geo + c1cell_geo (3500 satir), aktiflestirme hazirliginda.
  * 0038 -- fiz345 + mikro_fizik (2542 satir), 0036 sonrasi DB genelinde
    "bozuk URL sifir olmali" taramasi yapilinca.

Ikinci tur, tek tek kitaba bakmanin yetmedigini gosterdi. `test_hicbir_arac_*`
bu yuzden REPO GENELI tarar: `scripts/kitap/` altindaki her arac denetlenir,
yeni bir kitap eklendiginde test kendiliginden onu da kapsar.
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

KITAP_DIZINI = KOK / "scripts" / "kitap"
DOGRU_ONEK = "/static/crops/"

# URL ureten ithal araclari (CROP_ONEK tasiyanlar).
ARAC_ADLARI = [
    "acil_geo_ithal",
    "c1cell_geo_ithal",
    "fiz345_ithal",
    "mikro_fizik_ithal",
]


@pytest.fixture(scope="module")
def araclar() -> dict:
    return {ad: importlib.import_module(f"scripts.kitap.{ad}") for ad in ARAC_ADLARI}


# ------------------------------------------------- repo geneli sweep


def _url_ureten_dosyalar() -> list[Path]:
    """question_image_url deger ATAYAN arac dosyalari."""
    bulunan = []
    for p in sorted(KITAP_DIZINI.glob("*_ithal.py")):
        metin = p.read_text("utf-8")
        if re.search(r'"question_image_url":\s*\(', metin):
            bulunan.append(p)
    return bulunan


def test_sweep_en_az_dort_arac_buluyor() -> None:
    """Tarama bos donerse test kendini kandiriyor demektir."""
    dosyalar = _url_ureten_dosyalar()
    assert len(dosyalar) >= 4, f"yalniz {len(dosyalar)} arac bulundu: {dosyalar}"


def test_hicbir_arac_crop_image_dir_ile_url_kurmuyor() -> None:
    """ASIL KAPI: CROP_IMAGE_DIR bir dizindir, URL'e girmemeli.

    Repo geneli -- yeni bir kitap eklendiginde bu test onu da kapsar.
    """
    suclu = {}
    for p in _url_ureten_dosyalar():
        satirlar = [
            s.strip()
            for s in p.read_text("utf-8").splitlines()
            if "CROP_IMAGE_DIR" in s and not s.lstrip().startswith("#")
        ]
        if satirlar:
            suclu[p.name] = satirlar
    assert not suclu, f"URL uretiminde CROP_IMAGE_DIR izi: {suclu}"


def test_hicbir_arac_d_dataset_yazmiyor() -> None:
    """Eski hatanin imzasi: URL'de dosya sistemi dizini."""
    suclu = {}
    for p in _url_ureten_dosyalar():
        satirlar = [
            s.strip()
            for s in p.read_text("utf-8").splitlines()
            if '"d-dataset' in s or "'d-dataset" in s
            if not s.lstrip().startswith("#")
        ]
        if satirlar:
            suclu[p.name] = satirlar
    assert not suclu, f"kaynakta d-dataset izi: {suclu}"


def test_her_arac_static_crops_yaziyor() -> None:
    for p in _url_ureten_dosyalar():
        metin = p.read_text("utf-8")
        assert f'f"{DOGRU_ONEK}' in metin, f"{p.name}: /static/crops bicimi yok"


# ------------------------------------------------- modul duzeyi


@pytest.mark.parametrize("ad", ARAC_ADLARI)
def test_crop_onek_tanimli_ve_ascii(ad: str, araclar: dict) -> None:
    onek = araclar[ad].CROP_ONEK
    assert onek and onek.isascii()
    assert "/" not in onek, f"{ad}: CROP_ONEK yol icermemeli: {onek!r}"


# ------------------------------------------------- 0038 migration


@pytest.fixture(scope="module")
def mig0038():
    import importlib.util

    yol = KOK / "alembic" / "versions" / "0038_fizik_gorsel_url_onarimi.py"
    spec = importlib.util.spec_from_file_location("mig0038", yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_0038_kimlik_ve_zincir(mig0038) -> None:
    assert mig0038.revision == "0038_fizik_gorsel_url"
    assert mig0038.down_revision == "0037_geo_beta_onay"
    assert len(mig0038.revision) <= 32
    assert mig0038.DOGRU_ONEK == DOGRU_ONEK


def test_0038_onekleri_araclarla_ayni(mig0038, araclar: dict) -> None:
    """Onek uyusmazsa dosya adi dogru olsa bile URL 404 verir."""
    esleme = dict(mig0038.KAYNAKLAR)
    assert esleme[araclar["fiz345_ithal"].KAYNAK_ADI] == (
        araclar["fiz345_ithal"].CROP_ONEK
    )
    assert esleme[araclar["mikro_fizik_ithal"].KAYNAK_ADI] == (
        araclar["mikro_fizik_ithal"].CROP_ONEK
    )


def test_0038_donusum_dosya_adini_koruyor(mig0038) -> None:
    assert (
        mig0038._yeni_url(
            "d-dataset/output/crops/X/501d210a-1172-5eae-8636-3b2c292d9a72.png",
            "FIZ345_AYT",
        )
        == "/static/crops/FIZ345_AYT/501d210a-1172-5eae-8636-3b2c292d9a72.png"
    )


def test_0038_yalniz_kendi_kaynaklarini_hedefler(mig0038) -> None:
    assert "source_book = :kaynak" in mig0038._HEDEF_SQL
    # Zaten dogru olan satirlara dokunmaz (idempotans).
    assert "NOT LIKE :onek" in mig0038._HEDEF_SQL


def test_0036_ve_0038_kaynaklari_cakismiyor(mig0038) -> None:
    """Ayni satiri iki migration onarmasin."""
    import importlib.util

    yol = KOK / "alembic" / "versions" / "0036_geo_gorsel_url_onarimi.py"
    spec = importlib.util.spec_from_file_location("mig0036", yol)
    assert spec and spec.loader
    m36 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m36)
    ortak = {k for k, _ in m36.KAYNAKLAR} & {k for k, _ in mig0038.KAYNAKLAR}
    assert not ortak, f"iki migration ayni kaynagi hedefliyor: {ortak}"
