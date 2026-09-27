"""345 2025 TYT Turkce verisi -- anahtar, harita, kutu, metin.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
betiklerin saf fonksiyonlarini kullanir.

NE KORUR
1. ANAHTAR     -- kitap sonu tablo, iki okuma + goz karari birebir turer;
                  hucre sayisi == basili numara (2070); glif uyumsuzlari goz
                  karari ya da goz teyidi tasir.
2. MUTASYON    -- A/B farki, gereksiz / yabanci goz karari, bicim disi girdi,
                  hucre-numara farki, teyitsiz glif uyumsuzu SystemExit verir.
3. HARITA      -- 420 sayfa bandi A == B; test sayfalari bant (tur, no, konu)
                  ile ayni; konu ilk sayfasi == icindekiler; 207 test, 8
                  unite, 27 konu; migration 0068 == harita.
4. KUTULAR     -- 2070 kutu anahtarla birebir; numara capasi; blok ustu;
                  kose etiketi; ortak parca.
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

from scripts.kitap import tur345tyt_anahtar as an  # noqa: E402
from scripts.kitap import tur345tyt_harita as ha  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_turkce_"
HAM = json.loads((CIKTI / f"{ON}ham_okumalar.json").read_text("ascii"))
ANAHTAR = json.loads((CIKTI / f"{ON}cevap_anahtari.json").read_text("ascii"))
TARAMA = json.loads((CIKTI / f"{ON}capa_taramasi.json").read_text("ascii"))
HARITA = json.loads((CIKTI / f"{ON}konu_haritasi.json").read_text("ascii"))
KUTULAR = json.loads((CIKTI / f"{ON}kirpim_kutulari.json").read_text("ascii"))


def _uret(ham: dict) -> list[dict]:
    ok = an.iki_okuma(ham)
    anahtar = an.birlestir(ok, ham["goz_kararlari"]["farklar"])
    return an.cevaplar_uret(ok, anahtar, an.numara_sirasi(TARAMA))


# ---------------------------------------------------------------- 1. anahtar


def test_anahtar_hamdan_birebir_turer() -> None:
    cev = _uret(HAM)
    assert cev == ANAHTAR["cevaplar"]
    an.glif_dogrula(HAM, cev)


def test_toplamlar() -> None:
    assert ANAHTAR["toplam_cevap"] == 2070 and ANAHTAR["test_sayisi"] == 207
    assert TARAMA["numara_toplam"] == 2070 and TARAMA["simge_toplam"] == 2067
    d = ANAHTAR["dogrulama"]
    assert d["a_esittir_b_hucre"] == 2067 and d["goz_karari"] == 3
    assert d["glif_loo_uyum"] == 2066 and d["glif_goz_teyit"] == 3
    assert sum(ANAHTAR["harf_dagilimi"].values()) == 2070


def test_farklar_goz_ve_glifle() -> None:
    """A/B uc hucrede ayrisir (ikisi '?'); goz karari her birini kapatir."""
    fark = {
        f"T{t['sira']:03d}#{i}"
        for t in an.iki_okuma(HAM)
        for i, (x, y) in enumerate(zip(t["a"], t["b"], strict=True), 1)
        if x != y or x == "?"
    }
    assert (
        fark == set(HAM["goz_kararlari"]["farklar"]) == {"T071#4", "T086#7", "T173#4"}
    )
    assert HAM["goz_kararlari"]["farklar"] == {
        "T071#4": "B",
        "T086#7": "D",
        "T173#4": "C",
    }
    uyumsuz = {u[0] for u in HAM["glif"]["uyumsuz"]}
    assert uyumsuz == {"T120#3", "T143#10", "T173#4", "T180#8"}
    assert set(HAM["glif"]["goz_teyit"]) == uyumsuz - set(
        HAM["goz_kararlari"]["farklar"]
    )


def test_test_sirasi_ve_turler() -> None:
    ok = an.iki_okuma(HAM)
    assert Counter(t["tur"] for t in ok) == {"KO": 51, "OT": 98, "OR": 17, "KA": 41}
    assert [t["sayfa"] for t in ok] == sorted(t["sayfa"] for t in ok)


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
        _uret(_boz(lambda h: h["goz_kararlari"]["farklar"].update({"T001#1": "C"})))


def test_goz_karari_ne_a_ne_b_durur() -> None:
    with pytest.raises(SystemExit, match="ne A ne B"):
        _uret(_boz(lambda h: h["goz_kararlari"]["farklar"].update({"T071#4": "A"})))


def test_goz_karari_soru_isareti_olamaz() -> None:
    with pytest.raises(SystemExit, match="ne A ne B"):
        _uret(_boz(lambda h: h["goz_kararlari"]["farklar"].update({"T086#7": "?"})))


def test_bicim_disi_girdi_durur() -> None:
    def f(h: dict) -> None:
        h["anahtar_okumalari"]["A"][0]["cevaplar"] = (
            "X" + h["anahtar_okumalari"]["A"][0]["cevaplar"][1:]
        )

    with pytest.raises(SystemExit, match="bicim disi"):
        _uret(_boz(f))


def test_test_kimligi_farki_durur() -> None:
    with pytest.raises(SystemExit, match="kimligi"):
        _uret(_boz(lambda h: h["anahtar_okumalari"]["B"][5].update({"no": 9})))


def test_hucre_numara_farki_durur() -> None:
    def f(h: dict) -> None:
        for o in ("A", "B"):
            h["anahtar_okumalari"][o][0]["cevaplar"] += "A"

    with pytest.raises(SystemExit, match="hucre"):
        _uret(_boz(f))


def test_teyitsiz_glif_uyumsuzu_durur() -> None:
    h = _boz(lambda h: h["glif"]["goz_teyit"].pop("T120#3"))
    with pytest.raises(SystemExit, match="glif"):
        an.glif_dogrula(h, ANAHTAR["cevaplar"])


# ----------------------------------------------------------------- 3. harita


def test_harita_hamdan_birebir_turer() -> None:
    testler, uniteler, konular = ha.harita_uret(
        ha.bantlar(HAM), ANAHTAR["cevaplar"], HAM["anahtar_okumalari"]["A"]
    )
    assert testler == HARITA["testler"]
    assert uniteler == HARITA["uniteler"] and konular == HARITA["konular"]
    ha.kapak_dogrula(TARAMA)


def test_harita_sayilari() -> None:
    assert HARITA["test_sayisi"] == 207 and HARITA["unite_sayisi"] == 8
    assert HARITA["konu_sayisi"] == 27
    assert Counter(t["duzey"] for t in HARITA["testler"]) == {"konu": 166, "unite": 41}
    assert Counter(len(t["sayfalar"]) for t in HARITA["testler"]) == {2: 201, 3: 6}
    ka = {t["karma_konu"] for t in HARITA["testler"] if t["tur"] == "KA"}
    assert len(ka) == 8 and None not in ka


def test_bant_tur_no_mutasyonu_durur() -> None:
    bant = ha.bantlar(HAM)
    bant[7] = {**bant[7], "no": 3}
    with pytest.raises(SystemExit, match="bant"):
        ha.harita_uret(bant, ANAHTAR["cevaplar"], HAM["anahtar_okumalari"]["A"])


def test_bant_konu_mutasyonu_durur() -> None:
    bant = ha.bantlar(HAM)
    bant[6] = {**bant[6], "konu": "BASKA KONU"}
    with pytest.raises(SystemExit, match="konu"):
        ha.harita_uret(bant, ANAHTAR["cevaplar"], HAM["anahtar_okumalari"]["A"])


def test_icindekiler_sayfasi_mutasyonu_durur(monkeypatch: pytest.MonkeyPatch) -> None:
    konu = dict(ha.KONU_SAYFASI)
    konu["DEY\u0130M VE ATAS\u00d6Z\u00dc"] = 30
    monkeypatch.setattr(ha, "KONU_SAYFASI", konu)
    with pytest.raises(SystemExit, match="icindekiler"):
        ha.harita_uret(
            ha.bantlar(HAM), ANAHTAR["cevaplar"], HAM["anahtar_okumalari"]["A"]
        )


def test_bant_ab_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    h["baslik_okumalari"]["B"][0]["konu"] = "BASKA"
    with pytest.raises(SystemExit, match="A/B farkli"):
        ha.bantlar(h)


AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0068_trt345_konu_agaci.py"


def _agac():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("agac0068", AGAC_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_migration_agaci_harita_ile_ayni() -> None:
    m = _agac()
    assert list(m.UNITELER) == [(u["kod"], u["ad"]) for u in HARITA["uniteler"]]
    assert list(m.KONULAR) == [
        (k["kod"], k["ad"], k["unite"]) for k in HARITA["konular"]
    ]
    dugum = {k for k, _ in m.UNITELER} | {k for k, _, _ in m.KONULAR}
    assert {t["dugum"] for t in HARITA["testler"]} <= dugum


def test_migration_kimlik_ve_zincir() -> None:
    m = _agac()
    assert m.revision == "0068_trt345_agac"
    assert m.down_revision == "0067_sos345_beta_onay"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in AGAC_YOLU.read_bytes())
    assert m.KOK == "TUR" and m.ALAN == "TURKCE"
    assert all(k.startswith(m.KOD_ONEKI + "-") for k, *_ in (*m.UNITELER, *m.KONULAR))


# ---------------------------------------------------------------- 4. kutular

from scripts.kitap import tur345tyt_kutu as ku  # noqa: E402


def test_kutu_kapilari_temiz() -> None:
    assert ku.kapilar(KUTULAR) == []
    assert KUTULAR["kutu_sayisi"] == 2070 and KUTULAR["kutusuz_soru"] == 0
    assert KUTULAR["sutun_kanali"] == {"numara": 840}
    assert KUTULAR["ust_kurali_sayaci"]["blok_simgesi"] == 128


def test_kutu_ile_cevap_birebir() -> None:
    k = {(x["birim"], x["soru"]): x for x in KUTULAR["kutular"]}
    for c in ANAHTAR["cevaplar"]:
        x = k[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["sutun_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["sutun_sira"],
        )


def test_blok_ustleri() -> None:
    """Simge en yakin (ustteki) numaraya aittir; blok simgesi kutu ustunu yukari tasir."""
    capa = [[148, 156], [400, 407], [650, 657]]
    # 157: ilk numaranin yaninda (ayni satir); 300: ikinci sorunun blogu
    assert ku.blok_ustleri(capa, [[157, 45], [300, 45]]) == [148, 293, 650]
    assert ku.blok_ustleri(capa, []) == [148, 400, 650]


def test_kose_etiketi_yan_satir() -> None:
    """Onceki sorunun son satiri etiketin yaninda bitiyorsa kutu ustu o satirin altina iner."""
    import numpy as np

    a = np.full((300, 200, 3), 255, np.uint8)
    a[200:230, 150:180] = (242, 132, 36)  # etiket dairesi
    a[196:204, 10:60] = 40  # onceki sorunun son satiri (etiketle ayni yukseklikte)
    out = ku._kose_duzelt(
        a, 0, 200, capa=[[10, 22], [240, 247]], ustler=[5, 190], sayac=Counter()
    )
    assert out == [5, 204]


def test_ortak_parca() -> None:
    ortak = {
        (k["birim"], k["soru"]): k["ortak_parca"]
        for k in KUTULAR["kutular"]
        if k.get("ortak_parca")
    }
    assert len(ortak) == KUTULAR["ortak_parca_eklenen_soru"] == 10
    ad = {(k["birim"], k["soru"]): k for k in KUTULAR["kutular"]}
    for (b, _s), o in ortak.items():
        ilk = ad[(b, o["ilk_soru"])]
        assert o["kutu"][1] == ilk["kutu"][1] and o["kutu"][3] < ilk["capa"][0]
        assert o["kutu"][3] - o["kutu"][1] >= ku.ORTAK_EN_AZ


def test_tavan_ust_bant() -> None:
    assert min(k["kutu"][1] for k in KUTULAR["kutular"]) >= ku.TAVAN == 112
