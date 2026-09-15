"""0024_biyo345tyt_gorsel migration'inin koruma testleri.

Canli DB istemez; migration modulunu okur, yani CI'da da kosar.

1. ZINCIR      : revizyon kimligi, onceki revizyon, ad uzunlugu, ASCII.
2. KLASOR ADI  : `i` harfi NOKTASIZ kalmali. ASCII kurali dosya yollarini
                 KAPSAMAZ; klasor adi ASCII'ye duzlenirse her URL sessizce
                 404 olurdu. Bu testin mutasyon karsiligi var.
3. HARITA      : 1022 kayit, 219 sayfa, anahtar/deger bicimleri, ve AYNI
                 kirpimin iki soruya atanmamis olmasi (birebir esleme).
4. ELLE KARAR  : tek tek BAKILARAK verilen kararlar kilitli --
                 s148 sag5 -> q04, s16 sag3 haritada YOK,
                 s92 q04 ve s221 q04 (sahte kutular) hicbir yerde YOK.
5. DURUSTLUK   : human_verified yazilmaz, is_ai_generated atanmaz,
                 sinyal listesi 0023'unkiyle AYNI (yeni iddia eklenmedi).
6. GERI ALMA   : EK_ANAHTARLAR drift kontrolu, downgrade gunlugu dusuruyor,
                 gorsel_kaynagi eski degerine donuyor, bayrak geri ekleniyor.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

GOC_YOLU = KOK / "alembic" / "versions" / "0024_biyo345tyt_gorsel.py"


def _modul():
    spec = importlib.util.spec_from_file_location("goc_0024", GOC_YOLU)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def goc():
    return _modul()


@pytest.fixture(scope="module")
def kaynak_metni() -> str:
    return GOC_YOLU.read_text(encoding="utf-8")


# --- 1. ZINCIR ---------------------------------------------------------


def test_revizyon_zinciri(goc) -> None:
    assert goc.revision == "0024_biyo345tyt_gorsel"
    assert goc.down_revision == "0023_345_beta_onay"
    assert len(goc.revision) <= 32
    assert len(goc.GUNLUK) <= 63


def test_dosya_ascii() -> None:
    ham = GOC_YOLU.read_bytes()
    kusurlu = [i for i, b in enumerate(ham) if b > 127]
    assert not kusurlu, f"ASCII disi bayt: {kusurlu[:5]}"


# --- 2. KLASOR ADI (mutasyon karsiligi) --------------------------------

NOKTASIZ = "\u0131"  # noktasiz i


def test_klasor_adi_noktasiz_i_tasiyor(goc) -> None:
    assert (
        NOKTASIZ in goc.KLASOR
    ), "klasor adindaki noktasiz 'i' ASCII'ye duzlenmis -- her URL 404 olur"
    assert goc.KLASOR.endswith("Bankas" + NOKTASIZ)


def test_mutasyon_ascii_duzlenmis_klasor_yakalanir() -> None:
    bozuk = "345_2025_Tyt_Biyoloji_Soru_Bankasi"
    assert NOKTASIZ not in bozuk


def test_url_bicimi_ev_sozlesmesine_uyuyor(goc) -> None:
    u = goc._url(111, "04")
    assert u.startswith("/static/crops/")
    assert u.endswith("_p0111_q04.png")
    assert u == f"/static/crops/{goc.KLASOR}/{goc.KLASOR}_p0111_q04.png"


def test_sayfa_numarasi_dort_haneli(goc) -> None:
    assert "_p0007_" in goc._url(7, "01")
    assert "_p0221_" in goc._url(221, "03")


# --- 3. HARITA ---------------------------------------------------------


def test_harita_boyutu(goc) -> None:
    assert len(goc.HARITA) == 219
    assert sum(len(v) for v in goc.HARITA.values()) == 1022


def test_harita_anahtar_ve_deger_bicimi(goc) -> None:
    anahtar = re.compile(r"^(sol|sag)\d+$")
    for sayfa, d in goc.HARITA.items():
        assert isinstance(sayfa, int) and sayfa > 0
        for k, v in d.items():
            assert anahtar.match(k), f"bozuk anahtar: {sayfa} {k}"
            assert re.fullmatch(r"\d{2}", v), f"bozuk kirpim indeksi: {sayfa} {k} {v}"


def test_ayni_kirpim_iki_soruya_atanmamis(goc) -> None:
    for sayfa, d in goc.HARITA.items():
        kirpimlar = list(d.values())
        assert len(kirpimlar) == len(
            set(kirpimlar)
        ), f"sayfa {sayfa}: ayni kirpim birden fazla soruya atanmis"


def test_her_sayfada_sol_sag_ayrimi_var(goc) -> None:
    # Okuma sirasi kurali: sol sutun once. En az bir sayfada her iki yan da
    # bulunmali, yoksa harita tek sutunlu uretilmis demektir.
    iki_yanli = [
        s
        for s, d in goc.HARITA.items()
        if any(k.startswith("sol") for k in d) and any(k.startswith("sag") for k in d)
    ]
    assert len(iki_yanli) > 150


# --- 4. ELLE VERILEN KARARLAR (kilitli) --------------------------------


def test_s148_sag5_elle_q04e_baglandi(goc) -> None:
    # s148'de 5 kutu var ama DB'de 4 soru: 2. sag kutu basili no4'tur ve o
    # soru OSYM 2025 TYT'ye ait (dedup). DB'nin tek sag sorusu no5 -> q04.
    assert goc.HARITA[148]["sag5"] == "04"


def test_s16_sag3_haritada_yok(goc) -> None:
    # Dedektor o kutuyu kacirmis; uydurma gorsel baglanmadi.
    assert "sag3" not in goc.HARITA[16]
    assert "sol1" in goc.HARITA[16] and "sol2" in goc.HARITA[16]


def test_sahte_kutular_haritada_hicbir_yerde_yok(goc) -> None:
    # s92 q04: asiri buyuk (5. ve 6. soruyu yutuyor). s221 q04: BOMBOS.
    assert "04" not in goc.HARITA[92].values()
    assert "04" not in goc.HARITA[221].values()


# --- 5. DURUSTLUK ------------------------------------------------------


def test_human_verified_yazilmaz(kaynak_metni: str) -> None:
    kod = kaynak_metni.split('"""', 2)[2]
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_alanina_dokunulmaz(kaynak_metni: str) -> None:
    kod = kaynak_metni.split('"""', 2)[2]
    assert not re.search(r"is_ai_generated\s*=\s*(TRUE|FALSE|true|false)", kod)


def test_sinyal_listesi_0023_ile_ayni(goc) -> None:
    # Kutu dogrulamasi GORSEL eslemesini dogrular, transkripsiyonu ya da
    # cevabi degil -- bu yuzden sinyal listesine yeni madde EKLENMEMELI.
    yol = KOK / "alembic" / "versions" / "0023_345_beta_onay.py"
    spec = importlib.util.spec_from_file_location("goc_0023", yol)
    m23 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m23)
    (tyt,) = (s for k, s in m23.KAYNAKLAR if k == "345 2025 TYT Biyoloji Soru Bankasi")
    assert tuple(goc.SINYALLER) == tuple(tyt)


def test_gorsel_kaynagi_degeri_durust(goc) -> None:
    assert goc.ESKI_GORSEL_KAYNAGI == "yok_soru_kirpimi_uretilmedi"
    assert "dogrulanmis" in goc.YENI_GORSEL_KAYNAGI
    assert goc.YENI_GORSEL_KAYNAGI != goc.ESKI_GORSEL_KAYNAGI


# --- 6. GERI ALMA ------------------------------------------------------


def test_ek_anahtarlar_yazilanlarla_ortusuyor(goc, kaynak_metni: str) -> None:
    kod = kaynak_metni.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    yazilan = set(re.findall(r"'([a-z_0-9]+)',\s*(?:true|false|CAST)", kod))
    eksik = yazilan - set(goc.EK_ANAHTARLAR) - {"gorsel_kaynagi"}
    assert not eksik, f"downgrade'in silmedigi anahtar: {eksik}"


def test_downgrade_her_seyi_geri_aliyor(kaynak_metni: str) -> None:
    alt = kaynak_metni.split("def downgrade", 1)[1]
    assert "op.drop_table(GUNLUK)" in alt
    assert "question_image_url = :u" in alt
    assert "ESKI_GORSEL_KAYNAGI" in alt
    assert "gorsel_yok_sekilli" in alt  # bayrak geri ekleniyor
    assert "onceki_quality_review_status" in alt


def test_gunluk_onceki_degerleri_sakliyor(kaynak_metni: str) -> None:
    ust = kaynak_metni.split("def upgrade", 1)[1].split("def downgrade", 1)[0]
    for alan in (
        "onceki_url",
        "onceki_is_active",
        "onceki_review_status",
        "onceki_quality_review_status",
        "aktiflestirildi",
    ):
        assert alan in ust, f"gunlukte {alan} yok"
