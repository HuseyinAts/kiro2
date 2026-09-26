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
