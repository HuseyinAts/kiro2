"""345 2025 TYT Sosyal Bilgiler verisi -- anahtar, harita, kutu, metin.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
betiklerin saf fonksiyonlarini kullanir.

NE KORUR
1. ANAHTAR     -- kitap sonu tablo, iki okuma + goz karari birebir turer;
                  hucre sayisi == okuyucu simgesi (1233); glif LOO tam.
2. MUTASYON    -- A/B farki, gereksiz / yabanci goz karari, bicim disi girdi,
                  hucre-simge farki SystemExit verir.
3. HARITA      -- 300 sayfa bandi A == B; test sayfalari bant (gun, test) ile
                  ayni; 150 test, 69 unite; migration 0065 == harita.
4. KUTULAR     -- 1233 kutu anahtarla birebir; kose etiketi duzeltmesi.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "backend"))
sys.path.insert(0, str(KOK / "backend" / "scripts" / "kitap"))

from scripts.kitap import sos345tyt_anahtar as an  # noqa: E402
from scripts.kitap import sos345tyt_harita as ha  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_sosyal_"
HAM = json.loads((CIKTI / f"{ON}ham_okumalar.json").read_text("ascii"))
ANAHTAR = json.loads((CIKTI / f"{ON}cevap_anahtari.json").read_text("ascii"))
TARAMA = json.loads((CIKTI / f"{ON}capa_taramasi.json").read_text("ascii"))
HARITA = json.loads((CIKTI / f"{ON}konu_haritasi.json").read_text("ascii"))
KUTULAR = json.loads((CIKTI / f"{ON}kirpim_kutulari.json").read_text("ascii"))


def _uret(ham: dict) -> list[dict]:
    ok = an.iki_okuma(ham)
    anahtar = an.birlestir(ok, ham["goz_kararlari"]["farklar"])
    return an.cevaplar_uret(anahtar, an.simge_sirasi(TARAMA))


# ---------------------------------------------------------------- 1. anahtar


def test_anahtar_hamdan_birebir_turer() -> None:
    assert _uret(HAM) == ANAHTAR["cevaplar"]


def test_toplamlar() -> None:
    assert ANAHTAR["toplam_cevap"] == 1233 and ANAHTAR["test_sayisi"] == 150
    assert TARAMA["simge_toplam"] == 1233
    d = ANAHTAR["dogrulama"]
    assert d["a_esittir_b_hucre"] == 1230 and d["goz_karari"] == 3
    assert d["glif_loo_uyum"] == 1233
    assert sum(ANAHTAR["harf_dagilimi"].values()) == 1233


def test_tek_fark_goz_ve_glifle() -> None:
    """A/B yalniz GUN 3 test 6'nin 3-5. hucrelerinde ayrisir; goz A'yi secer."""
    fark = {
        f"G{g:02d}T{t}#{i}"
        for (g, t), (a, b) in an.iki_okuma(HAM).items()
        for i, (x, y) in enumerate(zip(a, b, strict=True), 1)
        if x != y
    }
    assert (
        fark
        == set(HAM["goz_kararlari"]["farklar"])
        == {
            "G03T6#3",
            "G03T6#4",
            "G03T6#5",
        }
    )
    a = {(x["gun"], x["test"]): x["cevaplar"] for x in HAM["anahtar_okumalari"]["A"]}
    assert a[(3, 6)][2:5] == "EBC"
    assert HAM["glif"]["uyumsuz"] == []


# --------------------------------------------------------------- 2. mutasyon


def _boz(fn) -> dict:  # type: ignore[no-untyped-def]
    h = copy.deepcopy(HAM)
    fn(h)
    return h


def test_ab_farki_durur() -> None:
    def f(h: dict) -> None:
        x = h["anahtar_okumalari"]["B"][0]
        x["cevaplar"] = ("A" if x["cevaplar"][0] != "A" else "B") + x["cevaplar"][1:]

    with pytest.raises(SystemExit, match="goz karari yok"):
        _uret(_boz(f))


def test_gereksiz_goz_karari_durur() -> None:
    with pytest.raises(SystemExit, match="gereksiz"):
        _uret(_boz(lambda h: h["goz_kararlari"]["farklar"].update({"G01T1#1": "C"})))


def test_goz_karari_ne_a_ne_b_durur() -> None:
    with pytest.raises(SystemExit, match="ne A ne B"):
        _uret(_boz(lambda h: h["goz_kararlari"]["farklar"].update({"G03T6#3": "A"})))


def test_bicim_disi_girdi_durur() -> None:
    def f(h: dict) -> None:
        h["anahtar_okumalari"]["A"][0]["cevaplar"] = (
            "X" + h["anahtar_okumalari"]["A"][0]["cevaplar"][1:]
        )

    with pytest.raises(SystemExit, match="bicim disi"):
        _uret(_boz(f))


def test_hucre_simge_farki_durur() -> None:
    def f(h: dict) -> None:
        for o in ("A", "B"):
            h["anahtar_okumalari"][o][0]["cevaplar"] += "A"

    with pytest.raises(SystemExit, match="hucre"):
        _uret(_boz(f))


def test_glif_uyumsuzlugu_durur() -> None:
    h = _boz(lambda h: h["glif"].update({"uyum": 1232}))
    with pytest.raises(SystemExit, match="glif"):
        an.glif_dogrula(h, ANAHTAR["cevaplar"])


# ----------------------------------------------------------------- 3. harita


def test_harita_hamdan_birebir_turer() -> None:
    testler, uniteler = ha.harita_uret(ha.bantlar(HAM), ANAHTAR["cevaplar"])
    assert testler == HARITA["testler"] and uniteler == HARITA["uniteler"]


def test_harita_sayilari() -> None:
    assert HARITA["test_sayisi"] == 150 and HARITA["unite_sayisi"] == 69
    assert Counter(t["ders"] for t in HARITA["testler"]) == {
        "TARIH": 50,
        "COGRAFYA": 50,
        "FELSEFE": 25,
        "DIN": 25,
    }
    assert all(len(t["sayfalar"]) == 2 for t in HARITA["testler"])


def test_bant_gun_test_mutasyonu_durur() -> None:
    bant = ha.bantlar(HAM)
    bant[7] = {**bant[7], "test": 2}
    with pytest.raises(SystemExit, match="bant"):
        ha.harita_uret(bant, ANAHTAR["cevaplar"])


def test_bant_ab_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    h["baslik_okumalari"]["B"][0]["konu"] = "BASKA"
    with pytest.raises(SystemExit, match="A/B farkli"):
        ha.bantlar(h)


def test_konu_tabani() -> None:
    assert ha.taban("??KL??M B??LG??S?? - III") == "??KL??M B??LG??S??"
    assert ha.taban("SU - TOPRAK - B??TK?? - II") == "SU - TOPRAK - B??TK??"
    assert ha.taban("G??NCEL D??N?? MESELELER") == "G??NCEL D??N?? MESELELER"


AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0065_sos345_konu_agaci.py"


def _agac():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("agac0065", AGAC_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_migration_uniteleri_harita_ile_ayni() -> None:
    m = _agac()
    kok = {"TARIH": "TAR", "COGRAFYA": "COG", "FELSEFE": "SOS", "DIN": "SOS"}
    assert list(m.UNITELER) == [
        (u["kod"], u["ad"], kok[u["ders"]], u["ders"]) for u in HARITA["uniteler"]
    ]


def test_migration_kimlik_ve_zincir() -> None:
    m = _agac()
    assert m.revision == "0065_sos345_agac"
    assert m.down_revision == "0064_kmt345_beta_onay"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in AGAC_YOLU.read_bytes())
    assert all(
        any(k.startswith(o + "-") for o in m.KOD_ONEKLERI) for k, *_ in m.UNITELER
    )


# ---------------------------------------------------------------- 4. kutular

from scripts.kitap import sos345tyt_kutu as ku  # noqa: E402


def test_kutu_kapilari_temiz() -> None:
    assert ku.kapilar(KUTULAR) == []
    assert KUTULAR["kutu_sayisi"] == 1233 and KUTULAR["kutusuz_soru"] == 0
    assert KUTULAR["sutun_kanali"] == {"simge": 600}


def test_kutu_ile_cevap_birebir() -> None:
    k = {(x["birim"], x["soru"]): x for x in KUTULAR["kutular"]}
    for c in ANAHTAR["cevaplar"]:
        x = k[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["sutun_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["sutun_sira"],
        )


def test_kose_etiketi_duzeltmesi() -> None:
    """'OSYM KOSESI' kutusunun ustu min(etiket, capa) - 1; onceki soru hemen biter."""
    import numpy as np

    a = np.full((300, 100, 3), 255, np.uint8)
    a[200:230, 40:70] = (240, 125, 25)  # etiket dairesi
    sayac: Counter[str] = Counter()
    out = ku._kose_duzelt(
        a, 0, 100, capa=[[10, 22], [203, 215]], ustler=[5, 190], sayac=sayac
    )
    assert out == [5, 199] and sayac["kose_etiketi"] == 1
    # etiket yoksa degismez
    b = np.full((300, 100, 3), 255, np.uint8)
    assert ku._kose_duzelt(
        b, 0, 100, capa=[[10, 22], [203, 215]], ustler=[5, 190], sayac=Counter()
    ) == [5, 190]
    assert KUTULAR["ust_kurali_sayaci"]["kose_etiketi"] == 65
