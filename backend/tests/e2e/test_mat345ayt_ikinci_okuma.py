"""0048: 345 AYT hedefli ikinci okumanin karari ve duzeltmeleri kayda bagli mi.

Canli DB istemez; ikinci okuma kaydini, metin veri setini ve migration'i
DOSYADAN okur -- CI'da koser.

1. KARAR      -- on kayitli kural kayittaki sayimlardan yeniden uretiliyor.
2. KAPSAM     -- orneklem grup basina 7; hedef tabakanin tamami okundu.
3. DUZELTME   -- migration parcasi geri alininca ILK hash'e donuluyor
                 (yani DB'deki metin tam o), ileri alininca veri setine.
4. ESITLIK    -- migration istatistik / kusur / meta degerleri ithalin
                 urettigiyle ayni (taze DB ile duzeltilmis DB ayni satiri tasir).
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
import uuid
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import mat345ayt_ithal as mi  # noqa: E402
from scripts.kitap.metin_olcum import (  # noqa: E402
    kelime_istatistik,
    okunabilirlik,
    soru_hash,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
KAYIT_YOLU = CIKTI / "345_2025_ayt_matematik_ikinci_okuma.json"
METIN_YOLU = CIKTI / "345_2025_ayt_matematik_metin.json"
MIG_YOLU = KOK / "alembic" / "versions" / "0048_mat345ayt_ikinci_okuma.py"

ORNEKLEM, GRUP, GRUP_BASI = 210, 30, 7
OKUNAN, FARKLI = 541, 77
TABAKA, TABAKA_YENI = 362, 331
ESASLI, KUSUR_NOTU = 10, 4
HUKUMLER = {
    "ayni",
    "ilk_okuma_korundu",
    "ilk_okuma_esasli_hata_duzeltildi",
    "kusur_notu_eklendi",
}


@pytest.fixture(scope="module")
def kayit() -> dict:
    return json.loads(KAYIT_YOLU.read_text("ascii"))


@pytest.fixture(scope="module")
def metin() -> dict[str, dict]:
    return {s["dosya"]: s for s in json.loads(METIN_YOLU.read_text("ascii"))["sorular"]}


@pytest.fixture(scope="module")
def mig() -> object:
    spec = importlib.util.spec_from_file_location("ikinci0048", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _h(govde: str, sikler: dict[str, str]) -> str:
    return soru_hash(govde, {k: sikler[k] for k in "ABCDE"})


def _uid(h: str) -> str:
    """Kayit hash'i uuid5 bicimiyle tasir (ithal id'si ile ayni donusum)."""
    return str(uuid.uuid5(uuid.NAMESPACE_OID, h))


def _grup(okuma: str) -> str:
    g = re.search(r"grup_\d\d", okuma)
    assert g, okuma
    return g.group(0)


def _cp_ust(x: int, n: int) -> float:
    """95% Clopper-Pearson ust siniri: P(X <= x; n, p) = 0.025 (ikiye bolme, scipy'siz)."""
    if x == n:
        return 1.0

    def cdf(p: float) -> float:
        return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(x + 1))

    alt, ust = 0.0, 1.0
    for _ in range(80):
        orta = (alt + ust) / 2
        if cdf(orta) > 0.025:
            alt = orta
        else:
            ust = orta
    return (alt + ust) / 2


# ------------------------------------------------------------- 1. karar


def test_on_kayitli_kural_kayittaki_sayimlardan_yeniden_uretiliyor(kayit: dict) -> None:
    k = kayit["karar"]
    orn = set(kayit["orneklem_listesi"])
    oku = {o["dosya"]: o for o in kayit["okumalar"]}
    esasli = {
        d for d, o in oku.items() if o["hukum"] == "ilk_okuma_esasli_hata_duzeltildi"
    }
    assert k["orneklem_n"] == len(orn) == ORNEKLEM
    assert sorted(orn & esasli) == k["orneklem_esasli_hata"]
    assert k["orneklem_x"] == len(orn & esasli) == 2
    assert k["cp95_ust"] == pytest.approx(_cp_ust(2, ORNEKLEM), abs=1e-5)
    assert k["cp95_ust"] > k["esik"] == 0.03  # tam-okuma-yok kolu KAPALI
    g11 = {d for d in orn if _grup(oku[d]["ilk_okuma_grubu"]) == "grup_11"}
    assert (k["grup_11"]["n"], k["grup_11"]["x"]) == (len(g11), len(g11 & esasli))
    disi = k["grup_11_disi"]
    assert disi["x"] == len((orn - g11) & esasli) == 0
    assert disi["cp95_ust"] == pytest.approx(_cp_ust(0, disi["n"]), abs=1e-5)
    # hatalar tek tabakada, tabaka disi 0 -> kural HEDEFLI der
    assert k["sonuc"] == "HEDEFLI_IKINCI_OKUMA"
    assert "TAM_IKINCI_OKUMA_YOK" in kayit["protokol"]["karar_kurali"]


# ------------------------------------------------------------ 2. kapsam


def test_orneklem_grup_basina_yedi(kayit: dict) -> None:
    oku = {o["dosya"]: o for o in kayit["okumalar"]}
    g = Counter(_grup(oku[d]["ilk_okuma_grubu"]) for d in kayit["orneklem_listesi"])
    assert len(g) == GRUP and set(g.values()) == {GRUP_BASI}


def test_hedef_tabakanin_tamami_okundu(kayit: dict) -> None:
    oku = {o["dosya"]: o for o in kayit["okumalar"]}
    assert len(oku) == len(kayit["okumalar"]) == OKUNAN
    tabaka = set(kayit["hedef_tabaka"])
    assert len(tabaka) == TABAKA and tabaka <= set(oku)
    assert set(oku) == tabaka | set(kayit["orneklem_listesi"])
    h = kayit["karar"]["hedefli"]
    assert (h["tabaka"], h["yeni_okunan"]) == (TABAKA, TABAKA_YENI)
    assert sum(o["tabaka"] == "hedefli" for o in oku.values()) == TABAKA_YENI
    assert h["esasli_hata"] + kayit["karar"]["orneklem_x"] == ESASLI


def test_her_hukum_bir_farka_dayaniyor(kayit: dict) -> None:
    for o in kayit["okumalar"]:
        assert o["hukum"] in HUKUMLER, o["dosya"]
        assert (o["hukum"] == "ayni") == (not o["farkli_alanlar"]), o["dosya"]
    assert sum(bool(o["farkli_alanlar"]) for o in kayit["okumalar"]) == FARKLI
    c = Counter(o["hukum"] for o in kayit["okumalar"])
    assert c["ilk_okuma_esasli_hata_duzeltildi"] == ESASLI
    assert c["kusur_notu_eklendi"] == KUSUR_NOTU


# ---------------------------------------------------------- 3. duzeltme


def test_kayit_duzeltmeleri_veri_setiyle_uyusuyor(kayit: dict, metin: dict) -> None:
    duz = kayit["duzeltmeler"]
    assert Counter(r["tur"] for r in duz) == {"metin": ESASLI, "kusur_notu": KUSUR_NOTU}
    esasli = {
        o["dosya"]
        for o in kayit["okumalar"]
        if o["hukum"].startswith("ilk_okuma_esasli")
    }
    assert {r["dosya"] for r in duz if r["tur"] == "metin"} == esasli
    for r in duz:
        s = metin[r["dosya"]]
        assert s["okuma"].startswith("duzeltme"), r["dosya"]
        assert s["hakem_notu"] == r["hakem_notu"]
        assert _uid(_h(s["govde"], s["sikler"])) == r["yeni_hash_id"]
        assert (r["id"] != r["yeni_hash_id"]) is (r["tur"] == "metin")
        if r["tur"] == "kusur_notu":
            assert (
                s["kaynak_kusuru"] == r["kaynak_kusuru_yeni"] != r["kaynak_kusuru_ilk"]
            )
    assert kayit["id_sabitleme"] == {
        r["dosya"]: r["id"] for r in duz if r["tur"] == "metin"
    }


def test_migration_parcasi_geri_alininca_ilk_hash(
    mig: object, kayit: dict, metin: dict
) -> None:
    """Parca ters uygulaninca ILK okumanin hash'i cikar: migration tam DB'deki metni hedefler."""
    duz = {r["dosya"]: r for r in kayit["duzeltmeler"]}
    satirlar = mig.METIN  # type: ignore[attr-defined]
    assert len(satirlar) == ESASLI
    for dosya, sid, eh, yh, sutun, ep, yp, _ist in satirlar:
        r, s = duz[dosya], metin[dosya]
        assert (sid, _uid(eh), _uid(yh)) == (r["id"], r["id"], r["yeni_hash_id"])
        assert ep != yp
        sik = dict(s["sikler"])
        govde = s["govde"]
        if sutun == "question_text":
            assert govde.count(yp) == 1, dosya
            govde = govde.replace(yp, ep)
        else:
            assert sutun == "option_d" and sik["D"] == yp, dosya
            sik["D"] = ep
        assert _h(govde, sik) == eh, dosya
        assert _h(s["govde"], s["sikler"]) == yh, dosya


def test_migration_istatistikleri_ithal_ile_ayni(mig: object, metin: dict) -> None:
    for dosya, *_orta, ist in mig.METIN:  # type: ignore[attr-defined]
        s = metin[dosya]
        n, u, ort = kelime_istatistik(s["govde"])
        sik = {k: s["sikler"][k] for k in "ABCDE"}
        assert ist == (n, u, ort, okunabilirlik(s["govde"], sik)), dosya


def test_migration_kusur_notlari_ve_bayraklari_ithal_ile_ayni(
    mig: object, kayit: dict, metin: dict
) -> None:
    duz = {r["dosya"]: r for r in kayit["duzeltmeler"] if r["tur"] == "kusur_notu"}
    kusur = mig.KUSUR  # type: ignore[attr-defined]
    assert {x[0] for x in kusur} == set(duz)
    for dosya, sid, h, not_, bayrak in kusur:
        s = metin[dosya]
        assert sid == _uid(h) == duz[dosya]["id"] == duz[dosya]["yeni_hash_id"]
        assert not_ == s["kaynak_kusuru"]
        assert "kaynak_kusuru" in bayrak


def test_migration_ve_ithal_ayni_meta(mig: object) -> None:
    meta = mig.ikinci_okuma_meta  # type: ignore[attr-defined]
    for tur in ("metin", "kusur_notu"):
        assert meta(tur) == mi.ikinci_okuma_meta(tur)
    kayit_yolu = str(KAYIT_YOLU.relative_to(KOK.parent)).replace("\\", "/")
    assert kayit_yolu == mig.KAYIT  # type: ignore[attr-defined]
    assert mig.KAYNAK_ADI == mi.KAYNAK_ADI  # type: ignore[attr-defined]


def test_migration_zinciri(mig: object) -> None:
    assert mig.down_revision == "0047_mat345ayt_eski_cevap"  # type: ignore[attr-defined]
    assert len(mig.revision) <= 32  # type: ignore[attr-defined]


def test_cevap_anahtarina_dokunulmadi(mig: object) -> None:
    kaynak = MIG_YOLU.read_text("ascii")
    assert "correct_answer" not in kaynak
    assert "is_active" not in kaynak and "is_public" not in kaynak


@pytest.mark.parametrize("yol", [KAYIT_YOLU, MIG_YOLU], ids=lambda p: p.name)
def test_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name
