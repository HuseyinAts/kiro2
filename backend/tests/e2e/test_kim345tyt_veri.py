"""345 2025 TYT Kimya verisi -- cevap anahtari ham okumalardan turer.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
`kim345tyt_anahtar.py`'nin saf fonksiyonlarini kullanir.

NE KORUR
1. TURETME     -- anahtar, ham A/B okumalarindan birebir yeniden uretilir.
2. MUTASYON    -- A/B farki, gereksiz fark karari, bicim disi girdi, numara
                  kopmasi, simge sayisi farki SystemExit verir.
3. KAPSAM      -- soru sayfalari x {L, R}; sutun girdi sayisi == simge sayisi.
4. DURUSTLUK   -- her cevabin kaynagi iki okuma; piksel ya da goz kanali.
"""

from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "backend"))

from scripts.kitap import kim345tyt_anahtar as an  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_kimya_"
HAM = json.loads((CIKTI / f"{ON}ham_okumalar.json").read_text("ascii"))
ANAHTAR = json.loads((CIKTI / f"{ON}cevap_anahtari.json").read_text("ascii"))
TARAMA = json.loads((CIKTI / f"{ON}capa_taramasi.json").read_text("ascii"))


def _uret(ham: dict) -> tuple[list[dict], list[dict]]:
    """Glif kanali ekran goruntusu ister; burada her girdi 'uyum' sayilir."""
    sutunlar = an.iki_okuma(ham)
    glif = {(k, i): "uyum" for k, g in sutunlar.items() for i in range(len(g))}
    unite = an.unite_bulucu(ham)
    goz = ham["goz_kararlari"]
    cev, _, ts = an.cevaplar_uret(
        sutunlar, glif, goz["girdiler"], goz["farklar"], unite
    )
    return cev, an.testler_uret(ts, cev, unite)


# ---------------------------------------------------------------- 1. turetme


def test_anahtar_ham_okumadan_birebir_turer() -> None:
    cev, testler = _uret(HAM)
    alan = ("birim", "soru", "cevap", "dosya", "sutun", "serit_sira", "unite")
    assert [tuple(c[a] for a in alan) for c in cev] == [
        tuple(c[a] for a in alan) for c in ANAHTAR["cevaplar"]
    ]
    assert testler == ANAHTAR["testler"]


def test_toplamlar() -> None:
    assert ANAHTAR["toplam_cevap"] == 1307
    assert ANAHTAR["test_sayisi"] == 138
    assert sum(ANAHTAR["harf_dagilimi"].values()) == 1307
    assert len({(c["birim"], c["soru"]) for c in ANAHTAR["cevaplar"]}) == 1307


def test_iki_okuma_birebir_fark_yok() -> None:
    assert ANAHTAR["dogrulama"]["a_b_farkli_sutun"] == []
    assert HAM["goz_kararlari"]["farklar"] == {}
    a, b = HAM["okumalar"]["A"]["serit"], HAM["okumalar"]["B"]["serit"]
    assert set(a) == set(b) and len(a) == 534
    for k in a:
        assert [e.rstrip("?") for e in a[k].split()] == [
            e.rstrip("?") for e in b[k].split()
        ], k


# ---------------------------------------------------------------- 2. mutasyon


def test_ab_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    h["okumalar"]["B"]["serit"]["7L"] = "6.C 7.A"
    with pytest.raises(SystemExit, match="A/B farki"):
        an.iki_okuma(h)


def test_gereksiz_fark_karari_durur() -> None:
    h = copy.deepcopy(HAM)
    h["goz_kararlari"]["farklar"]["7L"] = {"karar": "6.C 7.E"}
    with pytest.raises(SystemExit, match="fark karari kayitli"):
        an.iki_okuma(h)


def test_bicim_disi_girdi_durur() -> None:
    h = copy.deepcopy(HAM)
    h["okumalar"]["A"]["serit"]["7L"] = "6.C 7.F"
    h["okumalar"]["B"]["serit"]["7L"] = "6.C 7.F"
    with pytest.raises(SystemExit, match="bicim disi"):
        an.iki_okuma(h)


def test_numara_kopmasi_durur() -> None:
    h = copy.deepcopy(HAM)
    for o in "AB":
        h["okumalar"][o]["serit"]["7L"] = "6.C 8.E"
    with pytest.raises(SystemExit, match="numara kopmasi"):
        _uret(h)


def test_simge_sayisi_farki_durur() -> None:
    sut = an.iki_okuma(HAM)
    t = copy.deepcopy(TARAMA["sayfalar"])
    t["7"]["simge"]["L"].append([500, 50])
    with pytest.raises(SystemExit, match="simge"):
        an._kapsam_kapilari(sut, t)


def test_goz_karari_okumayla_celisirse_durur() -> None:
    with pytest.raises(SystemExit, match="celisiyor"):
        an._kanal("7R", 8, "D", "uyum", {"7R": ["8.E", "9.B"]})


# ---------------------------------------------------------------- 3. kapsam


def test_kapsam_kapilari_temiz() -> None:
    an._kapsam_kapilari(an.iki_okuma(HAM), TARAMA["sayfalar"])


def test_soru_sayfalari() -> None:
    assert TARAMA["seritli_sayfa"] == 267
    assert TARAMA["seritsiz_sayfa"] == [3, 4, 5, 35, 71, 109, 139, 155, 195, 231, 263]
    assert TARAMA["seritli_simgesiz_sayfa"] == [1, 2]
    assert TARAMA["simge_toplam"] == 1307


def test_unite_araliklari() -> None:
    u = HAM["icindekiler"]["uniteler"]
    assert len(u) == 9
    assert [x[2] for x in u] == sorted(x[2] for x in u)
    # her unite, onceki unite ayracinin (seritsiz sayfa) hemen arkasindan baslar
    ayrac = set(TARAMA["seritsiz_sayfa"])
    assert all(x[2] - 1 in ayrac for x in u)
    say = Counter(t["unite"] for t in ANAHTAR["testler"])
    assert set(say) == set(range(1, 10))


# ---------------------------------------------------------------- 4. durustluk


def test_kanal_durustlugu() -> None:
    izinli = {
        "iki_okuma+piksel",
        "iki_okuma+goz(5x)",
        "iki_okuma+goz(5x)+tereddut",
    }
    assert set(ANAHTAR["kaynak_dagilimi"]) <= izinli
    uyumsuz = {
        (k.split("#")[0], int(k.split("#")[1]))
        for k in ANAHTAR["dogrulama"]["glif_loo_uyumsuz"]
    }
    for c in ANAHTAR["cevaplar"]:
        if (f"{c['dosya']}{c['sutun']}", c["serit_sira"]) in uyumsuz:
            assert "goz" in c["kaynak"], c


def test_ascii() -> None:
    for ad in ("ham_okumalar", "cevap_anahtari", "capa_taramasi"):
        b = (CIKTI / f"{ON}{ad}.json").read_bytes()
        assert all(x < 128 for x in b), ad
    for p in ("kim345tyt_tarama.py", "kim345tyt_anahtar.py"):
        assert all(
            x < 128 for x in (KOK / "backend" / "scripts" / "kitap" / p).read_bytes()
        )


# ------------------------------------------------- 5. unite agaci (Faz 2, 0062)

from scripts.kitap import kim345tyt_harita as ha  # noqa: E402

HARITA = json.loads((CIKTI / f"{ON}konu_haritasi.json").read_text("ascii"))
AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0062_kmt345_konu_agaci.py"


def _agac():  # type: ignore[no-untyped-def]
    import importlib.util

    spec = importlib.util.spec_from_file_location("agac0062", AGAC_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_harita_hamdan_birebir_turer() -> None:
    assert ha.harita(HAM, ANAHTAR) == HARITA


def test_migration_uniteleri_harita_ile_ayni() -> None:
    agac = _agac()
    assert list(agac.UNITELER) == [(u["kod"], u["ad"]) for u in HARITA["uniteler"]]
    assert agac.KOD_ONEKI == ha.KOD_ONEKI == "KIM-345T25"
    assert agac.KIM_KOK_KODU == "KIM"


def test_migration_kimlik_ve_zincir() -> None:
    agac = _agac()
    assert agac.revision == "0062_kmt345_agac"
    assert agac.down_revision == "0061_fzt345_beta_onay"
    assert len(agac.revision) <= 32
    assert "'KIMYA'" in AGAC_YOLU.read_text("ascii")
    assert all(c < 128 for c in AGAC_YOLU.read_bytes())


def test_unite_kodlari_ve_test_baglantisi() -> None:
    kod = [u["kod"] for u in HARITA["uniteler"]]
    assert kod == [f"KIM-345T25-U{i:02d}" for i in range(1, 10)]
    assert {t["unite"] for t in HARITA["testler"]} == set(kod)
    assert sum(t["soru_sayisi"] for t in HARITA["testler"]) == 1307
    assert sum(len(u["konular"]) for u in HARITA["uniteler"]) == 35


def test_bant_adi_mutasyonu_durur() -> None:
    h = copy.deepcopy(HAM)
    h["bant_okumasi"]["baslangic"]["110"]["konu_adi"] = "KATILAR"
    with pytest.raises(SystemExit, match="U4: bant"):
        ha.harita(h, ANAHTAR)


def test_rozet_mutasyonu_durur() -> None:
    h = copy.deepcopy(HAM)
    h["bant_okumasi"]["baslangic"]["36"]["rozet"] = "2. TEST"
    with pytest.raises(SystemExit, match="rozet"):
        ha.harita(h, ANAHTAR)


def test_ascii_buyuk_sapka() -> None:
    assert ha.ascii_buyuk("Maddenin Fiziksel H\xe2lleri") == "MADDENIN FIZIKSEL HALLERI"


# ------------------------------------------------- 6. kirpim kutulari (Faz 3)

sys.path.insert(0, str(KOK / "backend" / "scripts" / "kitap"))
from scripts.kitap import kim345tyt_kutu as ku  # noqa: E402

KUTULAR = json.loads((CIKTI / f"{ON}kirpim_kutulari.json").read_text("ascii"))
ORTME = json.loads((CIKTI / f"{ON}ortme_olcumu.json").read_text("ascii"))


def test_kutu_kapilari_temiz() -> None:
    assert ku.kapilar(KUTULAR) == []
    assert KUTULAR["kutu_sayisi"] == 1307 and KUTULAR["kutusuz_soru"] == 0


def test_kutu_ile_cevap_birebir() -> None:
    k = {(x["birim"], x["soru"]): x for x in KUTULAR["kutular"]}
    for c in ANAHTAR["cevaplar"]:
        x = k[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["serit_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["serit_sira"],
        )


def test_capa_kanali_simge_birincil() -> None:
    for x in KUTULAR["kutular"]:
        sim = TARAMA["sayfalar"][str(x["dosya"])]["simge"][x["sutun"]]
        if x["capa_kanali"] == "simge":
            assert [x["capa"][0] + 6, x["capa"][1] - 6] in [[m[0], m[0]] for m in sim]
        else:
            # yalniz simgesi ust bantta duran 3 sutun numara capali
            assert (x["dosya"], x["sutun"]) in {(28, "R"), (226, "R"), (228, "R")}
        assert x["capa"][0] >= ku.UST_BANT_ALTI
    assert KUTULAR["sutun_kanali"] == {"simge": 531, "numara": 3}


def test_capa_secimi_ust_bant_simgesini_reddeder() -> None:
    s = {
        "simge": {"R": [[83, 368], [583, 370]]},
        "numara": {"R": [[148, 156, 386, 391], [582, 589, 386, 391]]},
    }
    capa, kanal = ku._capa_sec(s, "R", 2)
    assert kanal == "numara" and capa[0] == [148, 156]
    s["numara"]["R"] = s["numara"]["R"][:1]
    assert ku._capa_sec(s, "R", 2) is None


def test_kutu_kapisi_mutasyonu() -> None:
    v = copy.deepcopy(KUTULAR)
    v["kutular"][0]["kutu"][3] = 900
    assert any("sizinti" in h for h in ku.kapilar(v))
    v = copy.deepcopy(KUTULAR)
    a = [x for x in v["kutular"] if (x["dosya"], x["sutun"]) == (7, "L")]
    a[0]["kutu"][3] = a[1]["kutu"][1] + 5
    assert any("cakisma" in h for h in ku.kapilar(v))


def test_ortme_raporu() -> None:
    assert ORTME["tam_kitap"] is True
    assert ORTME["kenar_kapisi_ihlali"] == 0
    assert ORTME["ortme_suphesi_soru"] == len(
        {(o["birim"], o["soru"]) for o in ORTME["ortme"]}
    )
