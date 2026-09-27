"""2019-2020 ACIL TYT Matematik verisi -- anahtar, harita, capa, kutu, metin, mukerrer, migration.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
betiklerin saf fonksiyonlarini kullanir.

NE KORUR
1. ANAHTAR     -- test sonu cevap seridi, iki okuma birebir (1203/1203);
                  glif LOO 1133/1133; glif disi 6 test goz kanaliyla ayni;
                  hucre sayisi == kirmizi numara capasi.
2. MUTASYON    -- A/B farki, numara boslugu, A-E disi harf, glif uyumsuzu,
                  goz_c farki, capa-serit farki durur.
3. HARITA      -- 17 bolum, 32 konu, 95 test; her test tek konu araliginda,
                  bant == konu (basili esdegerlerle); migration 0071 == harita.
4. CAPA/KUTU   -- 1203 capa == serit hucresi; 1203 kutu anahtarla birebir;
                  kutu kapilari; sayfa no lekesi beyazlatmasi yalniz pencerede.
5. METIN       -- harness kapilari; on kayitli TAM ikinci okuma (160 fark);
                  duzeltmeler uygulanmis; `[??]` tahminle doldurulmadi.
6. MUKERRER    -- eski hat 9 satir / 5 modern karsilik; hash degeri yok.
7. 0072 / 0073 -- eski hat ciftleri olcumden; beta dislama kurali; durustluk.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "backend"))
sys.path.insert(0, str(KOK / "backend" / "scripts" / "kitap"))

from scripts.kitap import acil1920tyt_anahtar as an  # noqa: E402
from scripts.kitap import acil1920tyt_harita as ha  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "acil_1920_tyt_matematik_"
HAM = json.loads((CIKTI / f"{ON}ham_okumalar.json").read_text("ascii"))
ANAHTAR = json.loads((CIKTI / f"{ON}cevap_anahtari.json").read_text("ascii"))
TARAMA = json.loads((CIKTI / f"{ON}capa_taramasi.json").read_text("ascii"))
HARITA = json.loads((CIKTI / f"{ON}konu_haritasi.json").read_text("ascii"))
KUTULAR = json.loads((CIKTI / f"{ON}kirpim_kutulari.json").read_text("ascii"))


def _boz(fn) -> dict:  # type: ignore[no-untyped-def]
    h = copy.deepcopy(HAM)
    fn(h)
    return h


# ---------------------------------------------------------------- 1. anahtar


def test_anahtar_hamdan_birebir_turer() -> None:
    assert an.dogrula(HAM) == []
    assert an.cevaplar_uret(HAM, TARAMA) == ANAHTAR["cevaplar"]


def test_toplamlar() -> None:
    assert ANAHTAR["toplam_cevap"] == 1203 and ANAHTAR["test_sayisi"] == 95
    assert ANAHTAR["harf_dagilimi"] == {
        "A": 133,
        "B": 226,
        "C": 349,
        "D": 317,
        "E": 178,
    }
    assert TARAMA["capa_toplam"] == 1203 and TARAMA["test_sayisi"] == 95
    g = HAM["glif"]
    assert g["hucre"] == g["uyum"] == 1133 and g["uyumsuz"] == []
    assert sorted(g["kapsam_disi_test"]) == [20, 25, 31, 40, 67, 82]
    assert {int(k) for k in HAM["goz_c"]["testler"]} == set(g["kapsam_disi_test"])


# --------------------------------------------------------------- 2. mutasyon


def test_ab_farki_durur() -> None:
    def f(h: dict) -> None:
        c = h["okuma_b"]["testler"][0]["hucreler"][0]
        c[1] = "A" if c[1] != "A" else "B"

    assert any("A != B" in x for x in an.dogrula(_boz(f)))


def test_numara_boslugu_durur() -> None:
    def f(h: dict) -> None:
        for o in ("okuma_a", "okuma_b"):
            h[o]["testler"][3]["hucreler"][2][0] = 9

    assert any("1..N" in x for x in an.dogrula(_boz(f)))


def test_harf_disi_durur() -> None:
    def f(h: dict) -> None:
        for o in ("okuma_a", "okuma_b"):
            h[o]["testler"][4]["hucreler"][0][1] = "F"

    assert any("A-E" in x for x in an.dogrula(_boz(f)))


def test_glif_uyumsuzu_durur() -> None:
    h = _boz(lambda h: h["glif"]["uyumsuz"].append(["T001#1", "C", "D"]))
    assert any("glif uyumsuz" in x for x in an.dogrula(h))


def test_goz_c_farki_durur() -> None:
    def f(h: dict) -> None:
        s = h["goz_c"]["testler"]["20"]
        h["goz_c"]["testler"]["20"] = ("A" if s[0] != "A" else "B") + s[1:]

    assert any("goz_c != okuma" in x for x in an.dogrula(_boz(f)))


def test_goz_c_kapsami_durur() -> None:
    h = _boz(lambda h: h["goz_c"]["testler"].pop("82"))
    assert any("goz_c testleri" in x for x in an.dogrula(h))


def test_capa_serit_farki_durur() -> None:
    t = copy.deepcopy(TARAMA)
    t["testler"][0]["capalar"].pop()
    with pytest.raises(ValueError, match="capa"):
        an.cevaplar_uret(HAM, t)


# ----------------------------------------------------------------- 3. harita


def test_harita_hamdan_birebir_turer() -> None:
    h = ha.harita_uret(HAM, TARAMA, ANAHTAR)
    for alan in ("bolumler", "konular", "testler", "test_sayisi"):
        assert h[alan] == HARITA[alan], alan


def test_harita_sayilari() -> None:
    assert len(HARITA["bolumler"]) == 17 and len(HARITA["konular"]) == 32
    assert HARITA["test_sayisi"] == 95
    assert sum(t["soru_sayisi"] for t in HARITA["testler"]) == 1203
    konu = {k["kod"]: k for k in HARITA["konular"]}
    for t in HARITA["testler"]:
        k = konu[t["konu"]]
        assert k["bolum"] == t["bolum"]
        assert all(k["sayfalar"][0] <= p <= k["sayfalar"][1] for p in t["sayfalar"])
    # icindekiler dizgi hatasi 'EBOK-EKOK' adda duzeltildi, kaynagi korundu
    eb = [k for k in HARITA["konular"] if k["icindekiler_adi"] == "EBOK-EKOK"]
    assert len(eb) == 1 and eb[0]["ad"] == "EBOB-EKOK"


def test_bant_ab_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    h["okuma_b"]["testler"][0]["konu"] = "BASKA KONU"
    with pytest.raises(ValueError, match="bant A != B"):
        ha.harita_uret(h, TARAMA, ANAHTAR)


def test_bant_konu_farki_durur() -> None:
    h = copy.deepcopy(HAM)
    for o in ("okuma_a", "okuma_b"):
        h[o]["testler"][10]["konu"] = "OLASILIK"
    with pytest.raises(ValueError, match="konu"):
        ha.harita_uret(h, TARAMA, ANAHTAR)


def test_icindekiler_sayfasi_mutasyonu_durur(monkeypatch: pytest.MonkeyPatch) -> None:
    ic = list(ha.ICINDEKILER)
    b, ad, s = ic[3]
    ic[3] = (b, ad, s + 3)  # 'Bolme' baslangici kaydi: test iki konuya tasar
    monkeypatch.setattr(ha, "ICINDEKILER", tuple(ic))
    with pytest.raises(ValueError):
        ha.harita_uret(HAM, TARAMA, ANAHTAR)


AGAC_YOLU = KOK / "backend" / "alembic" / "versions" / "0071_acl20t_konu_agaci.py"


def _yukle(ad: str, yol: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_migration_agaci_harita_ile_ayni() -> None:
    m = _yukle("agac0071", AGAC_YOLU)
    assert list(m.BOLUMLER) == [(b["kod"], b["ad"]) for b in HARITA["bolumler"]]
    assert list(m.KONULAR) == [
        (k["kod"], k["ad"], k["bolum"]) for k in HARITA["konular"]
    ]
    assert {t["konu"] for t in HARITA["testler"]} == {k for k, _, _ in m.KONULAR}


def test_migration_kimlik_ve_zincir() -> None:
    m = _yukle("agac0071", AGAC_YOLU)
    assert m.revision == "0071_acl20t_agac"
    assert m.down_revision == "0070_trt345_beta_onay"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in AGAC_YOLU.read_bytes())
    assert m.KOK == "MAT" and m.ALAN == "MATEMATIK"
    assert all(k.startswith(m.KOD_ONEKI + "-") for k, *_ in (*m.BOLUMLER, *m.KONULAR))


# -------------------------------------------------------------- 4. capa/kutu

from scripts.kitap import acil1920tyt_kirp as ki  # noqa: E402
from scripts.kitap import acil1920tyt_kutu as ku  # noqa: E402
from scripts.kitap import acil1920tyt_tarama as ta  # noqa: E402


def test_capa_kapilari_temiz() -> None:
    assert ta.kapilar(TARAMA, HAM) == []
    assert TARAMA["sayfa_turu"] == {"test": 265, "acik": 167}


def test_capa_eksigi_yakalanir() -> None:
    t = copy.deepcopy(TARAMA)
    t["testler"][5]["capalar"].pop()
    assert ta.kapilar(t, HAM)


def test_capa_x_kaymasi_yakalanir() -> None:
    t = copy.deepcopy(TARAMA)
    t["testler"][2]["capalar"][0]["x"] += 20
    assert any("x kaymis" in h for h in ta.kapilar(t, HAM))


def test_kutu_kapilari_temiz() -> None:
    assert ku.kapilar(KUTULAR, TARAMA) == []
    assert KUTULAR["kutu_sayisi"] == 1203
    assert ku.SERIT_PAY == 12 and ku.SAYFA_ALTI == 904 and ku.UST_BANT == 76


def test_kutu_ile_cevap_birebir() -> None:
    k = {(x["birim"], x["soru"]): x for x in KUTULAR["kutular"]}
    assert len(k) == 1203
    for c in ANAHTAR["cevaplar"]:
        x = k[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["sutun_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["sutun_sira"],
        )


def test_kutu_cakismasi_yakalanir() -> None:
    v = copy.deepcopy(KUTULAR)
    a = next(i for i, x in enumerate(v["kutular"]) if x["sutun_sira"] == 1)
    onceki = v["kutular"][a - 1]
    v["kutular"][a]["kutu"][1] = onceki["kutu"][1] + 5
    assert ku.kapilar(v, TARAMA)


def test_sayfa_no_lekesi_yalniz_pencerede() -> None:
    a = np.full((979, 742, 3), 255, np.uint8)
    a[890, 350] = (230, 30, 40)  # leke (pencerede, doygun)
    a[890, 360] = (40, 40, 40)  # siyah yazi (doygun degil)
    a[870, 350] = (230, 30, 40)  # pencerenin ustunde
    a[890, 500] = (30, 60, 220)  # pencerenin saginda
    m = ki.sayfa_no_lekesi(a)
    assert m[890, 350] and m.sum() == 1


# ------------------------------------------------ 5. transkripsiyon (Faz 4)

from scripts.kitap import acil1920tyt_metin_harness as mh  # noqa: E402

METIN = json.loads((CIKTI / f"{ON}metin.json").read_text("ascii"))
IKINCI = json.loads((CIKTI / f"{ON}ikinci_okuma.json").read_text("ascii"))
ORTME = json.loads((CIKTI / f"{ON}ortme_olcumu.json").read_text("ascii"))
M = {s["dosya"]: s for s in METIN["sorular"]}


def _yazi(s: dict) -> str:
    return s["govde"] + " " + " ".join(map(str, s["sikler"].values()))


def test_metin_kapilari_yesil() -> None:
    assert mh.kapi(METIN["sorular"]) == []
    assert METIN["soru_sayisi"] == 1203 and METIN["parca_sayisi"] == 29


def test_metin_kapisi_mutasyonu_yakalar() -> None:
    bozuk = copy.deepcopy(METIN["sorular"])
    bozuk[3]["basili_no"] = 99
    bozuk[5]["sikler"]["C"] = " "
    del bozuk[7]
    hata = mh.kapi(bozuk)
    for k in ("KAPI1", "KAPI2", "KAPI3", "KAPI4"):
        assert any(h.startswith(k) for h in hata), k


def test_numara_null_yok_ve_cevap_sizmadi() -> None:
    assert [s["dosya"] for s in METIN["sorular"] if s.get("basili_no") is None] == []
    assert not [s for s in METIN["sorular"] if {"cevap", "correct_answer"} & set(s)]


def test_metin_kutularla_ayni_dosyalar() -> None:
    k = {f"{x['birim']}_{x['soru']:02d}" for x in KUTULAR["kutular"]}
    assert set(M) == k


def test_ikinci_okuma_on_kayitli_tam_okuma() -> None:
    assert "TAM" in IKINCI["kural"]
    assert "SONRA" in IKINCI["tasarim"]
    s = IKINCI["sonuc"]
    assert s["soru"] == 1203
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == 1203
    assert len(IKINCI["hukumler"]) == s["farkli_soru"] == 160
    say = Counter(h["esasli_hata"] for h in IKINCI["hukumler"])
    assert dict(say) == s["hukum_dagilimi"]
    assert s["ilk_okuma_esasli_hata"] == say["okuma_1"] + say["ikisi"] == 59
    assert s["ikinci_okuma_esasli_hata"] == say["okuma_2"] + say["ikisi"] == 59


def test_duzeltmeler_son_metinde_uygulanmis() -> None:
    for d in IKINCI["duzeltmeler"]:
        s = M[d["dosya"]]
        assert s["okuma"].startswith("duzeltme"), d["dosya"]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for h, v in d["sikler"].items():
            assert s["sikler"][h] == str(v).replace("\u2019", "'"), (d["dosya"], h)
        for a in ("basili_no", "sekil_var", "sikler_gorsel", "etiket"):
            assert s[a] == d[a], (d["dosya"], a)
    assert len(IKINCI["duzeltmeler"]) == 160
    assert sum(1 for s in METIN["sorular"] if s["okuma"].startswith("duzeltme")) == 160


def test_okunamaz_isaret_ortmeyle_aciklanir() -> None:
    """`[??]` yalniz diskin ortugu ya da okunamayan yerde; tahmin yazilmadi.

    192 sorunun 188'i ortme olcumunde; kalan 4'u hakemin okunamaz dedigi
    soluk isaret (kok indisi vb.).
    """
    ort = {f"{o['birim']}_{o['soru']:02d}" for o in ORTME["ortme"]}
    q = [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)]
    assert len(q) == 192
    assert len([d for d in q if d not in ort]) == 4


def test_etiket_ve_kivrik_kesme_yok() -> None:
    assert not [s for s in METIN["sorular"] if s.get("etiket")]
    assert not [s for s in METIN["sorular"] if "\u2019" in _yazi(s)]


# ------------------------------------------------ 6. mukerrer (Faz 5)


def _mk():  # type: ignore[no-untyped-def]
    """Gec ice aktarma: betik psycopg ister."""
    from scripts.kitap import acil1920tyt_mukerrer

    return acil1920tyt_mukerrer


MUK_METNI = (CIKTI / f"{ON}mukerrer_adaylari.json").read_text("ascii")
MUK = json.loads(MUK_METNI)
ESKI = "2019-2020-AC\u0130L-TYT-Soru Bankas\u0131"


def test_mukerrer_ozet() -> None:
    assert MUK["soru_sayisi"] == 1203
    assert MUK["db_satiri"] > 5000
    assert MUK["kitap_ici_ayni_hash"] == [] and MUK["kitap_ici_yakin"] == []
    assert MUK["guclu_aday_sayisi"] == 14


def test_eski_hat() -> None:
    assert MUK["eski_hat_ozet"] == {
        ESKI: {"satir": 9, "aktif": 9, "modern_karsilik": 5}
    }
    for e in MUK["eski_hat"]:
        guclu = e["en_yakin_3gram"] >= _mk().GUCLU_ESIK and e["ayni_sik_sayisi"] >= 3
        assert e["modern_karsilik"] == guclu, e["db_id"]
        if guclu:
            assert e["db_cevap"] == e["bizim_cevap"], e["db_id"]


def test_hash_carpismasi() -> None:
    """T093_06 eski hatla, T092_04 ACIL'in 2023-2024 kitabiyla ayni hash."""
    carp = {c["dosya"]: c["db_id"] for c in MUK["db_tam_hash_carpismasi"]}
    assert set(carp) == {"ACL20T-T092_04", "ACL20T-T093_06"}
    eski = {e["db_id"] for e in MUK["eski_hat"]}
    assert carp["ACL20T-T093_06"] in eski and carp["ACL20T-T092_04"] not in eski


def test_hash_degeri_yazilmadi() -> None:
    assert not re.search(r"[0-9a-f]{32}", MUK_METNI)
    assert MUK["farkli_soru_hash"] == 1203


def test_pozitif_kontrol_ve_ders() -> None:
    mk = _mk()
    assert len(MUK["pozitif_kontrol"]) >= 5
    assert min(k["bozuk_3gram"] for k in MUK["pozitif_kontrol"]) >= mk.GUCLU_ESIK
    assert mk.DERSLER == ("MATEMATIK", "GEOMETRI")
    assert mk.ESKI_KAYNAKLAR == (ESKI,)
    assert mk.nm("x \u2212 1") == mk.nm("x-1")


# ------------------------------- 7. eski hat pasif (0072) + beta onay (0073)

VERSIYON = KOK / "backend" / "alembic" / "versions"
ESKI_YOLU = VERSIYON / "0072_acl20t_eski_hat_pasif.py"
BETA_YOLU = VERSIYON / "0073_acl20t_beta_onay.py"


def test_0072_kimlik_zincir_ascii() -> None:
    m = _yukle("eski0072", ESKI_YOLU)
    assert m.revision == "0072_acl20t_eski_hat_pasif"
    assert m.down_revision == "0071_acl20t_agac"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in ESKI_YOLU.read_bytes())
    assert m.ESKI_KAYNAKLAR == (ESKI,)
    assert m.ITHAL_ARACI == "scripts/kitap/acil1920tyt_ithal.py"


def test_0072_ciftler_olcumden_turer() -> None:
    m = _yukle("eski0072", ESKI_YOLU)
    olcum = {
        (e["db_id"], e["en_yakin_bizim"].removeprefix("ACL20T-"))
        for e in MUK["eski_hat"]
        if e["modern_karsilik"]
    }
    assert set(m.ESKI_MODERN) == olcum and len(m.ESKI_MODERN) == 5


def test_0072_guard_modern_yoksa_dokunmaz() -> None:
    m = _yukle("eski0072", ESKI_YOLU)
    assert m.hedef_idler(set()) == []
    tum = {f"ACL20T-{d}.png" for _, d in m.ESKI_MODERN}
    assert len(m.hedef_idler(tum)) == 5
    assert len(m.hedef_idler(tum - {"ACL20T-T093_06.png"})) == 4


def test_0072_durustluk() -> None:
    kod = ESKI_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "DELETE" not in kod.upper()
    assert "SET is_active = FALSE" in kod
    sql = " ".join(_yukle("eski0072", ESKI_YOLU)._ESKI_SQL.split())
    assert "'ithal_araci') IS NULL" in sql and "qb.is_active IS TRUE" in sql


def test_0073_kimlik_zincir_ascii() -> None:
    m = _yukle("beta0073", BETA_YOLU)
    assert m.revision == "0073_acl20t_beta_onay"
    assert m.down_revision == "0072_acl20t_eski_hat_pasif"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in BETA_YOLU.read_bytes())
    assert m.ITHAL_ARACI == "scripts/kitap/acil1920tyt_ithal.py"
    assert m.KAYNAK == "2019-2020 ACIL TYT Matematik Soru Bankasi"


def test_0073_dislama_kurali() -> None:
    """Servis disi uc bayrak + gorunen alti alanda [??] + aktif hash ikizi disarida."""
    m = _yukle("beta0073", BETA_YOLU)
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
    assert m.ORTME_ISARETI == "%[??]%"
    assert "qb.is_active IS NOT TRUE" in sql
    assert "o.soru_hash = qb.soru_hash AND o.is_active IS TRUE" in sql


def test_0073_hedef_olculen_1010() -> None:
    """1203 - 192 gorunen [??] - 1 aktif ikiz (T092_04; [??] yok) = 1010."""
    isaretli = {s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)}
    assert len(isaretli) == 192 and "ACL20T-T092_04" not in isaretli
    assert 1203 - len(isaretli) - 1 == 1010
    assert "(1010/1203)" in BETA_YOLU.read_text("ascii").splitlines()[0]


def test_0073_durustluk() -> None:
    kod = BETA_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "'human_verified'" not in kod
    assert "is_ai_generated" not in kod and "is_public" not in kod
    assert "'bireysel_denetim_yapildi', false" in kod
    assert "DELETE" not in kod.upper()
    m = _yukle("beta0073", BETA_YOLU)
    assert len(m.SINYALLER) == 5 and len(set(m.SINYALLER)) == 5
    assert "anahtar_iki_bagimsiz_okuma_1203_1203_hucre" in m.SINYALLER
