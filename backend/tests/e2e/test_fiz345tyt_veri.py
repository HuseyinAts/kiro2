"""345 2025 TYT Fizik verisi -- cevap anahtari ham okumalardan turer.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
`fiz345tyt_anahtar.py`'nin saf fonksiyonlarini kullanir.

NE KORUR
1. TURETME     -- anahtar, ham A/B okumalarindan birebir yeniden uretilir.
2. MUTASYON    -- A/B farki, gecersiz goz karari, bicim disi girdi, numara
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

from scripts.kitap import fiz345tyt_anahtar as an  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
HAM = json.loads((CIKTI / "345_2025_tyt_fizik_ham_okumalar.json").read_text("ascii"))
ANAHTAR = json.loads(
    (CIKTI / "345_2025_tyt_fizik_cevap_anahtari.json").read_text("ascii")
)
TARAMA = json.loads(
    (CIKTI / "345_2025_tyt_fizik_capa_taramasi.json").read_text("ascii")
)


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
    assert ANAHTAR["toplam_cevap"] == 1397
    assert ANAHTAR["test_sayisi"] == 176
    assert sum(ANAHTAR["harf_dagilimi"].values()) == 1397
    assert len({(c["birim"], c["soru"]) for c in ANAHTAR["cevaplar"]}) == 1397


def test_tek_fark_goz_ve_sureklilikle() -> None:
    assert ANAHTAR["dogrulama"]["a_b_farkli_sutun"] == ["277R"]
    f = HAM["goz_kararlari"]["farklar"]["277R"]
    assert f["karar"] == HAM["okumalar"]["A"]["serit"]["277R"]
    sol = HAM["okumalar"]["A"]["serit"]["277L"].split()
    assert sol[-1].startswith("5.") and f["karar"].startswith("6.")


# ---------------------------------------------------------------- 2. mutasyon


def test_ab_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    h["okumalar"]["B"]["serit"]["7L"] = "7.C 8.C 9.A"
    with pytest.raises(SystemExit, match="A/B farki"):
        an.iki_okuma(h)


def test_goz_karari_ne_a_ne_b_durur() -> None:
    h = copy.deepcopy(HAM)
    h["goz_kararlari"]["farklar"]["277R"]["karar"] = "6.E"
    with pytest.raises(SystemExit, match="ne A ne B"):
        an.iki_okuma(h)


def test_bicim_disi_girdi_durur() -> None:
    h = copy.deepcopy(HAM)
    h["okumalar"]["A"]["serit"]["7L"] = "7.C 8.C 9.F"
    h["okumalar"]["B"]["serit"]["7L"] = "7.C 8.C 9.F"
    with pytest.raises(SystemExit, match="bicim disi"):
        an.iki_okuma(h)


def test_numara_kopmasi_durur() -> None:
    h = copy.deepcopy(HAM)
    for o in "AB":
        h["okumalar"][o]["serit"]["7L"] = "7.C 9.C 9.E"
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
        an._kanal("7R", 10, "D", "uyum", {"7R": ["10.E", "11.E"]})


# ---------------------------------------------------------------- 3. kapsam


def test_kapsam_kapilari_temiz() -> None:
    an._kapsam_kapilari(an.iki_okuma(HAM), TARAMA["sayfalar"])


def test_soru_sayfalari() -> None:
    assert TARAMA["seritli_sayfa"] == 357
    assert TARAMA["seritsiz_sayfa"] == [3, 4, 5, 43, 99, 161, 225, 273, 315]
    assert TARAMA["seritli_simgesiz_sayfa"] == [1, 2]
    assert TARAMA["simge_toplam"] == 1397


def test_unite_araliklari() -> None:
    u = HAM["icindekiler"]["uniteler"]
    assert len(u) == 19
    assert [x[2] for x in u] == sorted(x[2] for x in u)
    say = Counter(t["unite"] for t in ANAHTAR["testler"])
    assert set(say) == set(range(1, 20))


# ---------------------------------------------------------------- 4. durustluk


def test_kanal_durustlugu() -> None:
    izinli = {
        "iki_okuma+piksel",
        "iki_okuma+goz(10x)",
        "iki_okuma+goz(10x)+tereddut",
        "iki_okuma_farkli+goz(10x)+numara_surekliligi",
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
        b = (CIKTI / f"345_2025_tyt_fizik_{ad}.json").read_bytes()
        assert all(x < 128 for x in b), ad
    for p in ("fiz345tyt_tarama.py", "fiz345tyt_anahtar.py"):
        assert all(
            x < 128 for x in (KOK / "backend" / "scripts" / "kitap" / p).read_bytes()
        )


# ------------------------------------------------- 5. unite agaci (Faz 2, 0060)

from scripts.kitap import fiz345tyt_harita as ha  # noqa: E402

HARITA = json.loads(
    (CIKTI / "345_2025_tyt_fizik_konu_haritasi.json").read_text("ascii")
)
AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0060_fzt345_konu_agaci.py"


def _agac():
    import importlib.util

    spec = importlib.util.spec_from_file_location("agac0060", AGAC_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_harita_hamdan_birebir_turer() -> None:
    assert ha.harita(HAM, ANAHTAR) == HARITA


def test_migration_uniteleri_harita_ile_ayni() -> None:
    agac = _agac()
    assert list(agac.UNITELER) == [(u["kod"], u["ad"]) for u in HARITA["uniteler"]]
    assert agac.KOD_ONEKI == ha.KOD_ONEKI == "FIZ-345T25"
    assert agac.FIZ_KOK_KODU == "FIZ"


def test_migration_kimlik_ve_zincir() -> None:
    agac = _agac()
    assert agac.revision == "0060_fzt345_agac"
    assert agac.down_revision == "0059_stm345_beta_onay"
    assert len(agac.revision) <= 32
    assert "'FIZIK'" in AGAC_YOLU.read_text("ascii")
    assert all(c < 128 for c in AGAC_YOLU.read_bytes())


def test_unite_kodlari_ve_test_baglantisi() -> None:
    kod = [u["kod"] for u in HARITA["uniteler"]]
    assert kod == [f"FIZ-345T25-U{i:02d}" for i in range(1, 20)]
    assert {t["unite"] for t in HARITA["testler"]} == set(kod)
    assert sum(t["soru_sayisi"] for t in HARITA["testler"]) == 1397


def test_bant_adi_mutasyonu_durur() -> None:
    h = copy.deepcopy(HAM)
    h["bant_okumasi"]["baslangic"]["100"]["unite_adi"] = "KUVVET"
    with pytest.raises(SystemExit, match="U5: bant"):
        ha.harita(h, ANAHTAR)


def test_rozet_mutasyonu_durur() -> None:
    h = copy.deepcopy(HAM)
    h["bant_okumasi"]["baslangic"]["44"]["rozet"] = "2. bolum"
    with pytest.raises(SystemExit, match="rozet"):
        ha.harita(h, ANAHTAR)


def test_ve_baglaci_yalniz_bantta_atlanir() -> None:
    assert ha.bant_uyar(
        "ISIK AKISI VE AYDINLANMA",
        "I\u015f\u0131k Ak\u0131s\u0131 - Ayd\u0131nlanma - G\u00f6lge",
    )
    assert not ha.bant_uyar(
        "ISIK AKISI VE GOLGE X", "I\u015f\u0131k Ak\u0131s\u0131 - G\u00f6lge"
    )
