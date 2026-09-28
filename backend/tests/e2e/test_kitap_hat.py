"""Ortak kitap hatti (scripts/kitap/kitap_hat) -- profil basina veri + migration testleri.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari, profilleri ve
betiklerin saf fonksiyonlarini kullanir. Her profil `SONUC` sozlugunde olculen
sayilarini tasir; yeni kitap = yeni profil (PROFILLER listesine eklenir).

NE KORUR
1. ANAHTAR   -- iki okuma birebir; glif LOO + goz teyidi; glif disi goz; hucre
               sayisi == capa. Mutasyonlar durur.
2. HARITA    -- icindekiler + bant; agac migration'i == harita.
3. CAPA/KUTU -- tarama ve kutu kapilari temiz; kutu anahtarla birebir.
4. METIN     -- harness kapilari; on kayitli TAM ikinci okuma; duzeltmeler.
5. MUKERRER  -- hash degeri yok; eski hat modern karsilik kurali.
6. MIGRATION -- eski hat ciftleri olcumden (modern id); beta dislama; durustluk.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "backend"))

from scripts.kitap.kitap_hat import anahtar as an  # noqa: E402
from scripts.kitap.kitap_hat import harita as ha  # noqa: E402
from scripts.kitap.kitap_hat import kutu as ku  # noqa: E402
from scripts.kitap.kitap_hat import metin as mh  # noqa: E402
from scripts.kitap.kitap_hat import migration_uret as mu  # noqa: E402
from scripts.kitap.kitap_hat import ortak  # noqa: E402
from scripts.kitap.kitap_hat import tarama as ta  # noqa: E402

PROFILLER = ["acl23ag", "acl23kc", "acl24mg"]
VERSIYON = KOK / "backend" / "alembic" / "versions"


class Kitap:
    def __init__(self, kod: str) -> None:
        self.p: ModuleType = ortak.profil(kod)
        self.s = self.p.SONUC
        for ad in (
            "ham_okumalar",
            "cevap_anahtari",
            "capa_taramasi",
            "konu_haritasi",
            "kirpim_kutulari",
            "metin",
            "ikinci_okuma",
            "ortme_olcumu",
        ):
            setattr(self, ad, ortak.oku(self.p, ad))
        self.muk_metni = ortak.yol(self.p, "mukerrer_adaylari").read_text("ascii")
        self.muk = json.loads(self.muk_metni)
        self.adlar = mu.adlar(self.p, self.s["migration_no"])


@pytest.fixture(scope="module", params=PROFILLER)
def k(request: pytest.FixtureRequest) -> Kitap:
    return Kitap(request.param)


def _yukle(ad: str, yol: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _boz(ham: dict, fn) -> dict:  # type: ignore[no-untyped-def]
    h = copy.deepcopy(ham)
    fn(h)
    return h


# ---------------------------------------------------------------- 1. anahtar


def test_anahtar_hamdan_birebir_turer(k: Kitap) -> None:
    assert an.dogrula(k.p, k.ham_okumalar) == []
    assert (
        an.cevaplar_uret(k.p, k.ham_okumalar, k.capa_taramasi)
        == k.cevap_anahtari["cevaplar"]
    )


def test_anahtar_toplamlari(k: Kitap) -> None:
    a = k.cevap_anahtari
    assert (
        a["toplam_cevap"] == k.p.BEKLENEN_SORU and a["test_sayisi"] == k.p.BEKLENEN_TEST
    )
    assert a["harf_dagilimi"] == k.s["harf"]
    g = k.ham_okumalar["glif"]
    assert g["hucre"] == k.s["glif_hucre"] and g["uyum"] == k.s["glif_uyum"]
    assert g["goz_teyit"] == k.s["goz_teyit"]
    assert sorted(g["kapsam_disi_test"]) == k.s["glif_disi"]


def test_ab_farki_durur(k: Kitap) -> None:
    def f(h: dict) -> None:
        c = h["okuma_b"]["testler"][0]["hucreler"][0]
        c[1] = "A" if c[1] != "A" else "B"

    assert any("A != B" in x for x in an.dogrula(k.p, _boz(k.ham_okumalar, f)))


def test_numara_boslugu_ve_harf_disi_durur(k: Kitap) -> None:
    def f(h: dict) -> None:
        for o in ("okuma_a", "okuma_b"):
            h[o]["testler"][1]["hucreler"][1][0] = 9
            h[o]["testler"][2]["hucreler"][0][1] = "F"

    hata = an.dogrula(k.p, _boz(k.ham_okumalar, f))
    assert any("1..N" in x for x in hata) and any("A-E" in x for x in hata)


def test_glif_teyit_ve_goz_c_mutasyonlari_durur(k: Kitap) -> None:
    ilk = next(iter(k.s["goz_teyit"]))
    h = _boz(k.ham_okumalar, lambda h: h["glif"]["goz_teyit"].pop(ilk))
    assert any("glif uyumsuz" in x for x in an.dogrula(k.p, h))
    h = _boz(k.ham_okumalar, lambda h: h["glif"]["goz_teyit"].update({ilk: "Z"}))
    assert any("goz teyidi" in x for x in an.dogrula(k.p, h))
    t = str(k.s["glif_disi"][0])

    def f(h: dict) -> None:
        s = h["goz_c"]["testler"][t]
        h["goz_c"]["testler"][t] = ("A" if s[0] != "A" else "B") + s[1:]

    assert any("goz_c != okuma" in x for x in an.dogrula(k.p, _boz(k.ham_okumalar, f)))


def test_capa_anahtar_farki_durur(k: Kitap) -> None:
    t = copy.deepcopy(k.capa_taramasi)
    t["testler"][0]["capalar"].pop()
    with pytest.raises(ValueError, match="capa"):
        an.cevaplar_uret(k.p, k.ham_okumalar, t)


# ----------------------------------------------------------------- 2. harita


def test_harita_hamdan_birebir_turer(k: Kitap) -> None:
    h = ha.harita_uret(k.p, k.ham_okumalar, k.capa_taramasi, k.cevap_anahtari)
    for alan in ("bolumler", "konular", "testler", "test_sayisi"):
        assert h[alan] == k.konu_haritasi[alan], alan
    assert sum(t["soru_sayisi"] for t in h["testler"]) == k.p.BEKLENEN_SORU


def test_bant_farki_durur(k: Kitap) -> None:
    h = copy.deepcopy(k.ham_okumalar)
    h["okuma_b"]["testler"][0]["konu"] = "BASKA KONU"
    with pytest.raises(ValueError, match="bant A != B"):
        ha.harita_uret(k.p, h, k.capa_taramasi, k.cevap_anahtari)
    for o in ("okuma_a", "okuma_b"):
        h[o]["testler"][0]["konu"] = "BASKA KONU"
    with pytest.raises(ValueError, match="konu"):
        ha.harita_uret(k.p, h, k.capa_taramasi, k.cevap_anahtari)


def test_agac_migration_harita_ile_ayni(k: Kitap) -> None:
    yol = VERSIYON / k.adlar["agac_dosya"]
    m = _yukle("agac", yol)
    assert list(m.BOLUMLER) == [
        (b["kod"], b["ad"]) for b in k.konu_haritasi["bolumler"]
    ]
    assert list(m.KONULAR) == [
        (x["kod"], x["ad"], x["bolum"]) for x in k.konu_haritasi["konular"]
    ]
    assert m.revision == k.adlar["agac_rev"] and m.down_revision == k.s["onceki"]
    assert len(m.revision) <= 32 and all(c < 128 for c in yol.read_bytes())
    assert m.KOK == k.p.KOK_KOD and m.ALAN == k.p.ALAN


# -------------------------------------------------------------- 3. capa/kutu


def test_capa_kapilari_temiz(k: Kitap) -> None:
    assert ta.kapilar(k.p, k.capa_taramasi, k.ham_okumalar) == []
    assert k.capa_taramasi["sayfa_turu"] == k.s["sayfa_turu"]
    assert k.capa_taramasi["capa_toplam"] == k.p.BEKLENEN_SORU


def test_capa_mutasyonu_yakalanir(k: Kitap) -> None:
    t = copy.deepcopy(k.capa_taramasi)
    t["testler"][1]["capalar"].pop()
    assert ta.kapilar(k.p, t, k.ham_okumalar)
    t = copy.deepcopy(k.capa_taramasi)
    c = next(c for c in t["testler"][2]["capalar"] if not c.get("numarasiz"))
    c["x"] += 60
    assert any("x kaymis" in h for h in ta.kapilar(k.p, t, k.ham_okumalar))
    t = copy.deepcopy(k.capa_taramasi)
    c = t["testler"][3]["capalar"][0]
    c["numarasiz"] = True
    assert any("profilde olmayan" in h for h in ta.kapilar(k.p, t, k.ham_okumalar))


def test_kutu_kapilari_ve_anahtar_birebir(k: Kitap) -> None:
    assert ku.kapilar(k.p, k.kirpim_kutulari, k.capa_taramasi) == []
    kutu = {(x["birim"], x["soru"]): x for x in k.kirpim_kutulari["kutular"]}
    assert len(kutu) == k.p.BEKLENEN_SORU
    for c in k.cevap_anahtari["cevaplar"]:
        x = kutu[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["sutun_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["sutun_sira"],
        )


def test_kutu_cakismasi_yakalanir(k: Kitap) -> None:
    v = copy.deepcopy(k.kirpim_kutulari)
    i = next(i for i, x in enumerate(v["kutular"]) if x["sutun_sira"] == 1)
    onceki = next(
        x
        for x in v["kutular"]
        if (x["dosya"], x["sutun"], x["sutun_sira"])
        == (v["kutular"][i]["dosya"], v["kutular"][i]["sutun"], 0)
    )
    v["kutular"][i]["kutu"][1] = onceki["kutu"][1] + 5
    assert ku.kapilar(k.p, v, k.capa_taramasi)


# ------------------------------------------------------------------ 4. metin


def _yazi(s: dict) -> str:
    return s["govde"] + " " + " ".join(map(str, s["sikler"].values()))


def test_metin_kapilari_yesil(k: Kitap) -> None:
    assert mh.kapi(k.p, k.metin["sorular"]) == []
    assert k.metin["soru_sayisi"] == k.p.BEKLENEN_SORU
    assert k.metin["parca_sayisi"] == k.s["metin_parca"]
    assert not [s for s in k.metin["sorular"] if {"cevap", "correct_answer"} & set(s)]


def test_metin_kapisi_mutasyonu_yakalar(k: Kitap) -> None:
    bozuk = copy.deepcopy(k.metin["sorular"])
    bozuk[3]["basili_no"] = 99
    bozuk[5]["sikler"]["C"] = " "
    del bozuk[7]
    hata = mh.kapi(k.p, bozuk)
    for x in ("KAPI1", "KAPI2", "KAPI3", "KAPI4"):
        assert any(h.startswith(x) for h in hata), x


def test_numarasiz_yalniz_profildeki(k: Kitap) -> None:
    null = {s["dosya"] for s in k.metin["sorular"] if s.get("basili_no") is None}
    assert null == mh.numarasiz(k.p)
    assert len(null) == len(getattr(k.p, "NUMARASIZ_CAPA", ()))


def test_ikinci_okuma_on_kayitli_tam(k: Kitap) -> None:
    io = k.ikinci_okuma
    assert "TAM" in io["kural"] and "SONRA" in io["tasarim"]
    s = io["sonuc"]
    assert s["soru"] == k.p.BEKLENEN_SORU
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == k.p.BEKLENEN_SORU
    assert len(io["hukumler"]) == s["farkli_soru"] == k.s["farkli_soru"]
    say: dict[str, int] = {}
    for h in io["hukumler"]:
        say[h["esasli_hata"]] = say.get(h["esasli_hata"], 0) + 1
    assert say == s["hukum_dagilimi"]


def test_duzeltmeler_son_metinde(k: Kitap) -> None:
    m = {s["dosya"]: s for s in k.metin["sorular"]}
    for d in k.ikinci_okuma["duzeltmeler"]:
        s = m[d["dosya"]]
        assert s["okuma"].startswith("duzeltme"), d["dosya"]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for a in ("basili_no", "sekil_var", "sikler_gorsel", "etiket"):
            assert s[a] == d[a], (d["dosya"], a)


def test_okunamaz_sayisi(k: Kitap) -> None:
    q = [s["dosya"] for s in k.metin["sorular"] if "[??]" in _yazi(s)]
    assert len(q) == k.s["okunamaz"]


# ------------------------------------------------------------- 5. mukerrer


def test_mukerrer_hash_yazilmadi_ve_pozitif_kontrol(k: Kitap) -> None:
    assert not re.search(r"[0-9a-f]{32}", k.muk_metni)
    assert k.muk["soru_sayisi"] == k.p.BEKLENEN_SORU
    assert len(k.muk["pozitif_kontrol"]) >= 5
    assert min(x["bozuk_3gram"] for x in k.muk["pozitif_kontrol"]) >= 0.9


def test_eski_hat_kurali(k: Kitap) -> None:
    for e in k.muk["eski_hat"]:
        guclu = e["en_yakin_3gram"] >= 0.9 and e["ayni_sik_sayisi"] >= 3
        assert e["modern_karsilik"] == guclu, e["db_id"]
    assert sum(e["modern_karsilik"] for e in k.muk["eski_hat"]) == k.s["eski_modern"]


# ------------------------------------------------------------ 6. migration


def test_eski_hat_migration_olcumden(k: Kitap) -> None:
    from scripts.kitap.metin_olcum import soru_hash

    yol = VERSIYON / k.adlar["eski_dosya"]
    m = _yukle("eski", yol)
    assert m.revision == k.adlar["eski_rev"] and m.down_revision == k.adlar["agac_rev"]
    assert len(m.revision) <= 32 and all(c < 128 for c in yol.read_bytes())
    assert tuple(k.p.ESKI_KAYNAKLAR) == m.ESKI_KAYNAKLAR
    olcum = {
        (e["db_id"], e["en_yakin_bizim"].removeprefix(f"{k.p.KOD}-"))
        for e in k.muk["eski_hat"]
        if e["modern_karsilik"]
    }
    assert {(a, b) for a, b, _ in m.ESKI_MODERN} == olcum
    metin = {s["dosya"]: s for s in k.metin["sorular"]}
    for _, kirpim, mid in m.ESKI_MODERN:
        s = metin[f"{k.p.KOD}-{kirpim}"]
        h = soru_hash(s["govde"], {x: s["sikler"][x] for x in "ABCDE"})
        assert mid == str(uuid.uuid5(uuid.NAMESPACE_OID, h)), kirpim
    assert m.hedef_idler(set()) == []
    kod = yol.read_text("ascii").split('"""', 2)[2]
    assert "SET is_active = FALSE" in kod
    sql = " ".join(m._ESKI_SQL.split())
    assert "'ithal_araci') IS NULL" in sql and "qb.is_active IS TRUE" in sql


def test_beta_migration(k: Kitap) -> None:
    yol = VERSIYON / k.adlar["beta_dosya"]
    m = _yukle("beta", yol)
    assert m.revision == k.adlar["beta_rev"] and m.down_revision == k.adlar["eski_rev"]
    assert len(m.revision) <= 32 and all(c < 128 for c in yol.read_bytes())
    assert m.KAYNAK == k.p.KAYNAK_ADI
    assert m.ITHAL_ARACI == "scripts/kitap/kitap_hat/ithal.py"
    assert f"({k.s['beta']})" in yol.read_text("ascii").splitlines()[0]
    sql = " ".join(m._HEDEF_SQL.split())
    for bayrak in m.SERVIS_DISI_BAYRAKLAR:
        assert f"? '{bayrak}')" in sql, bayrak
    for alan in (
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
    ):
        assert f"qc.{alan} NOT LIKE :isaret" in sql, alan
    assert "o.soru_hash = qb.soru_hash AND o.is_active IS TRUE" in sql
    assert "'modern_kitap_ikizi'" in sql
    kod = yol.read_text("ascii").split('"""', 2)[2]
    assert "'human_verified'" not in kod
    assert "is_ai_generated" not in kod and "is_public" not in kod
    assert "'bireysel_denetim_yapildi', false" in kod
    assert "DELETE" not in kod.upper()
    assert len(set(m.SINYALLER)) == 5
