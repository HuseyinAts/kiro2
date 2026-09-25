"""345 2025 Start Matematik Faz 1 verisi -- cevap anahtari ham okumalardan turer.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
`stm345_anahtar.py`'nin saf fonksiyonlarini kullanir.

NE KORUR
1. TURETME     -- anahtar, ham A/B okumalarindan birebir yeniden uretilir.
2. MUTASYON    -- A/B farki, bicim disi girdi SystemExit verir (kapi calisir).
3. SUREKLILIK  -- numara ya +1 ya 1; her test iki ardisik sayfa.
4. BANT        -- bant test no'su unite icinde 1'den; bant adi == icindekiler.
5. KAPSAM      -- yalniz test sayfalari; sutun girdi sayisi == basili numara.
6. DURUSTLUK   -- her cevabin kaynagi iki okuma; piksel ya da goz kanali.
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

from scripts.kitap import stm345_anahtar as an  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
HAM = json.loads(
    (CIKTI / "345_2025_start_matematik_ham_okumalar.json").read_text("ascii")
)
ANAHTAR = json.loads(
    (CIKTI / "345_2025_start_matematik_cevap_anahtari.json").read_text("ascii")
)
TARAMA = json.loads(
    (CIKTI / "345_2025_start_matematik_capa_taramasi.json").read_text("ascii")
)


# ---------------------------------------------------------------- 1. turetme


def test_anahtar_ham_okumadan_birebir_turer() -> None:
    sutunlar = an.iki_okuma(HAM)
    turetilen = [
        (k, i, n, h)
        for k in sorted(sutunlar, key=an._anahtar)
        for i, (n, h, _) in enumerate(sutunlar[k])
    ]
    kayitli = [
        (f"{c['dosya']}{c['sutun']}", c["serit_sira"], c["soru"], c["cevap"])
        for c in ANAHTAR["cevaplar"]
    ]
    assert turetilen == kayitli


def test_toplamlar() -> None:
    assert ANAHTAR["test_sayisi"] == 45
    assert ANAHTAR["toplam_cevap"] == len(ANAHTAR["cevaplar"]) == 371
    assert sum(t["soru_sayisi"] for t in ANAHTAR["testler"]) == 371
    assert sum(ANAHTAR["harf_dagilimi"].values()) == 371


# --------------------------------------------------------------- 2. mutasyon


def test_a_b_farki_durdurur() -> None:
    bozuk = copy.deepcopy(HAM)
    k = next(iter(bozuk["okumalar"]["B"]["serit"]))
    v = bozuk["okumalar"]["B"]["serit"][k]
    son = v[-1]
    yeni = "A" if son != "A" else "B"
    bozuk["okumalar"]["B"]["serit"][k] = v[:-1] + yeni
    with pytest.raises(SystemExit):
        an.iki_okuma(bozuk)


def test_eksik_sutun_durdurur() -> None:
    bozuk = copy.deepcopy(HAM)
    bozuk["okumalar"]["A"]["serit"].pop(next(iter(bozuk["okumalar"]["A"]["serit"])))
    with pytest.raises(SystemExit):
        an.iki_okuma(bozuk)


def test_bicim_disi_girdi_durdurur() -> None:
    with pytest.raises(SystemExit):
        an._girdiler("1.F 2.B")


# ------------------------------------------------------------- 3. sureklilik


def test_numara_surekliligi() -> None:
    onceki = None
    for c in ANAHTAR["cevaplar"]:
        assert c["soru"] == 1 or c["soru"] == onceki + 1
        onceki = c["soru"]


def test_her_test_iki_ardisik_sayfa() -> None:
    for t in ANAHTAR["testler"]:
        a, b = t["sayfalar"]
        assert b == a + 1, t


def test_birim_kodlari_sirali_ve_benzersiz() -> None:
    kodlar = [t["birim"] for t in ANAHTAR["testler"]]
    assert kodlar == [f"STM345-T{i:03d}" for i in range(1, 46)]


# ------------------------------------------------------------------ 4. bant


def test_bant_unite_ve_test_no() -> None:
    uniteler = {u[0]: u[1] for u in HAM["icindekiler"]["uniteler"]}
    bant = HAM["bant_okumasi"]["sayfalar"]
    for t in ANAHTAR["testler"]:
        for s in t["sayfalar"]:
            no, ad = bant[str(s)]
            assert no == t["unite_ici_test"]
            assert ad == uniteler[t["unite"]]


def test_unite_basina_test_sayisi() -> None:
    say = Counter(t["unite"] for t in ANAHTAR["testler"])
    assert sorted(say) == list(range(1, 17))
    assert say == Counter(
        {
            1: 3,
            2: 2,
            3: 2,
            4: 2,
            5: 4,
            6: 4,
            7: 3,
            8: 2,
            9: 2,
            10: 2,
            11: 2,
            12: 3,
            13: 3,
            14: 4,
            15: 4,
            16: 3,
        }
    )


def test_test_sayfasi_kendi_unitesinin_araliginda() -> None:
    bas = sorted((u[2] + 1, u[0]) for u in HAM["icindekiler"]["uniteler"])
    for t in ANAHTAR["testler"]:
        for s in t["sayfalar"]:
            assert [no for d, no in bas if d <= s][-1] == t["unite"]


# ----------------------------------------------------------------- 5. kapsam


def test_yalniz_test_sayfalari() -> None:
    assert len(TARAMA["sayfalar"]) == 90
    assert {c["dosya"] for c in ANAHTAR["cevaplar"]} == {
        int(s) for s in TARAMA["sayfalar"]
    }


def test_sutun_girdi_sayisi_esittir_basili_numara() -> None:
    say = Counter((c["dosya"], c["sutun"]) for c in ANAHTAR["cevaplar"])
    for s, p in TARAMA["sayfalar"].items():
        for t in "LR":
            assert say[(int(s), t)] == len(p["numara"][t]), (s, t)


# -------------------------------------------------------------- 6. durustluk


def test_her_cevap_iki_okuma_ve_ucuncu_kanal() -> None:
    for c in ANAHTAR["cevaplar"]:
        assert c["kaynak"].startswith("iki_okuma+")
        assert "piksel" in c["kaynak"] or "goz" in c["kaynak"]


def test_goz_kararlari_okumayla_ayni() -> None:
    sutunlar = an.iki_okuma(HAM)
    for k, liste in HAM["goz_kararlari"]["girdiler"].items():
        okunan = {f"{n}.{h}" for n, h, _ in sutunlar[k]}
        assert set(liste) <= okunan, k


def test_glif_uyumsuzu_goz_kararinda() -> None:
    goz = HAM["goz_kararlari"]["girdiler"]
    for x in ANAHTAR["dogrulama"]["glif_loo_uyumsuz"]:
        assert x.split("#")[0] in goz, x


def test_ascii() -> None:
    for ad in ("ham_okumalar", "cevap_anahtari", "capa_taramasi"):
        b = (CIKTI / f"345_2025_start_matematik_{ad}.json").read_bytes()
        assert all(c < 128 for c in b), ad


# ------------------------------------------------- 7. unite agaci (Faz 2, 0057)

from scripts.kitap import stm345_harita as ha  # noqa: E402

HARITA = json.loads(
    (CIKTI / "345_2025_start_matematik_konu_haritasi.json").read_text("ascii")
)
AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0057_stm345_konu_agaci.py"


def _agac():
    import importlib.util

    spec = importlib.util.spec_from_file_location("agac0057", AGAC_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_harita_hamdan_birebir_turer() -> None:
    assert ha.harita(HAM, ANAHTAR) == HARITA


def test_migration_uniteleri_harita_ile_ayni() -> None:
    agac = _agac()
    assert list(agac.UNITELER) == [(u["kod"], u["ad"]) for u in HARITA["uniteler"]]
    assert agac.KOD_ONEKI == ha.KOD_ONEKI == "MAT-345S25"
    assert agac.MAT_KOK_KODU == "MAT"


def test_migration_kimlik_ve_zincir() -> None:
    agac = _agac()
    assert agac.revision == "0057_stm345_agac"
    assert agac.down_revision == "0056_prg345_beta_onay"
    assert len(agac.revision) <= 32
    assert "'MATEMATIK'" in AGAC_YOLU.read_text("ascii")


def test_migration_ascii() -> None:
    b = AGAC_YOLU.read_bytes()
    assert all(c < 128 for c in b)


def test_unite_kodlari_ve_sayisi() -> None:
    assert [u["kod"] for u in HARITA["uniteler"]] == [
        f"MAT-345S25-U{i:02d}" for i in range(1, 17)
    ]
    assert HARITA["test_sayisi"] == 45
    assert {t["unite"] for t in HARITA["testler"]} == {
        u["kod"] for u in HARITA["uniteler"]
    }


def test_ayrac_adi_icindekiler_ile_katlanir() -> None:
    for u in HARITA["uniteler"]:
        assert ha.ascii_buyuk(u["ad"]) == u["ad_ascii"]
        assert u["ayrac_sayfasi"] == u["basili_baslangic"] + 1


def test_ayrac_adi_bozulursa_durur() -> None:
    bozuk = copy.deepcopy(HAM)
    k = next(iter(bozuk["ayrac_okumasi"]["sayfalar"]))
    bozuk["ayrac_okumasi"]["sayfalar"][k][1] = "Uydurma Unite"
    with pytest.raises(SystemExit):
        ha.harita(bozuk, ANAHTAR)


def test_ayrac_sayfasi_kayarsa_durur() -> None:
    bozuk = copy.deepcopy(HAM)
    s = bozuk["ayrac_okumasi"]["sayfalar"]
    k = sorted(s, key=int)[3]
    s[str(int(k) + 1)] = s.pop(k)
    with pytest.raises(SystemExit):
        ha.harita(bozuk, ANAHTAR)
