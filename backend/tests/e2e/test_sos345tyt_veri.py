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


# ------------------------------------------------ 5. transkripsiyon (Faz 4)

from scripts.kitap import sos345tyt_metin_harness as mh  # noqa: E402

METIN = json.loads((CIKTI / f"{ON}metin.json").read_text("ascii"))
IKINCI = json.loads((CIKTI / f"{ON}ikinci_okuma.json").read_text("ascii"))
M = {s["dosya"]: s for s in METIN["sorular"]}


def _yazi(s: dict) -> str:
    return s["govde"] + " " + " ".join(map(str, s["sikler"].values()))


def test_metin_kapilari_yesil() -> None:
    assert mh.kapi(METIN["sorular"]) == []
    assert METIN["soru_sayisi"] == 1233 and METIN["parca_sayisi"] == 29


def test_metin_kapisi_mutasyonu_yakalar() -> None:
    bozuk = copy.deepcopy(METIN["sorular"])
    bozuk[3]["basili_no"] = 99
    bozuk[5]["sikler"]["C"] = " "
    del bozuk[7]
    hata = mh.kapi(bozuk)
    for k in ("KAPI1", "KAPI2", "KAPI3", "KAPI4"):
        assert any(h.startswith(k) for h in hata), k


def test_numara_null_yok() -> None:
    assert [s["dosya"] for s in METIN["sorular"] if s.get("basili_no") is None] == []


def test_metin_kutularla_ayni_dosyalar() -> None:
    k = {f"{x['birim']}_{x['soru']:02d}" for x in KUTULAR["kutular"]}
    assert set(M) == k


def test_kivrik_kesme_ve_numara_notu_kalmadi() -> None:
    for s in METIN["sorular"]:
        assert "\u2019" not in _yazi(s), s["dosya"]
        if s.get("kaynak_kusuru"):
            assert not mh.NUMARA_NOTU.search(s["kaynak_kusuru"]), s["dosya"]


def test_ikinci_okuma_on_kayitli_tam_okuma() -> None:
    assert "TAM" in IKINCI["kural"]
    assert "SONRA" in IKINCI["tasarim"]
    s = IKINCI["sonuc"]
    assert s["soru"] == 1233
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == 1233
    assert len(IKINCI["hukumler"]) == s["farkli_soru"] == 194
    say = Counter(h["esasli_hata"] for h in IKINCI["hukumler"])
    assert dict(say) == s["hukum_dagilimi"]
    assert s["ilk_okuma_esasli_hata"] == say["okuma_1"] + say["ikisi"] == 73
    assert s["ikinci_okuma_esasli_hata"] == say["okuma_2"] + say["ikisi"] == 88


def test_duzeltmeler_son_metinde_uygulanmis() -> None:
    for d in IKINCI["duzeltmeler"]:
        s = M[d["dosya"]]
        assert s["okuma"].startswith("duzeltme"), d["dosya"]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for h, v in d["sikler"].items():
            assert s["sikler"][h] == str(v).replace("\u2019", "'"), (d["dosya"], h)
        for a in ("basili_no", "sekil_var", "sikler_gorsel", "etiket"):
            assert s[a] == d[a], (d["dosya"], a)
    assert len(IKINCI["duzeltmeler"]) == 194


def test_okunamaz_tahmin_edilmedi() -> None:
    assert [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)] == []


def test_etiketler() -> None:
    et = [s["etiket"] for s in METIN["sorular"] if s.get("etiket")]
    assert len(et) == 100
    assert Counter(e.split(" - ")[0] for e in et) == {"TYT": 83, "MS\xdc": 14, "AYT": 3}


# ------------------------------------------------ 6. mukerrer (Faz 5)

import re  # noqa: E402


def _mk():  # type: ignore[no-untyped-def]
    """Gec ice aktarma (stm345 deseni): betik psycopg ister."""
    from scripts.kitap import sos345tyt_mukerrer

    return sos345tyt_mukerrer


MUK_METNI = (CIKTI / f"{ON}mukerrer_adaylari.json").read_text("ascii")
MUK = json.loads(MUK_METNI)
ESKI_2025 = "345 2025 Tyt Sosyal Bilgiler Soru Bankas\u0131"
ESKI_2024 = "345 Tyt Sosyal Bilgiler Soru Bankas\u0131"


def test_mukerrer_ozet() -> None:
    assert MUK["soru_sayisi"] == 1233
    assert MUK["db_satiri"] > 500
    assert MUK["kitap_ici_ayni_hash"] == []
    # kitap kendi sorusunu 30. gunde tekrar basmis (C sikki bir kelime farkli)
    assert MUK["kitap_ici_yakin"] == [
        {"a": "SOS345-T010_02", "b": "SOS345-T148_01", "govde_3gram": 1.0}
    ]
    assert MUK["osym_etiketli_soru"] == 100


def test_eski_hat_iki_baski() -> None:
    oz = MUK["eski_hat_ozet"]
    assert oz[ESKI_2025] == {"satir": 26, "aktif": 26, "modern_karsilik": 25}
    assert oz[ESKI_2024] == {"satir": 12, "aktif": 12, "modern_karsilik": 8}
    for e in MUK["eski_hat"]:
        guclu = e["en_yakin_3gram"] >= _mk().GUCLU_ESIK and e["ayni_sik_sayisi"] >= 3
        assert e["modern_karsilik"] == guclu, e["db_id"]


def test_hash_carpismasi_eski_hat() -> None:
    assert [c["dosya"] for c in MUK["db_tam_hash_carpismasi"]] == ["SOS345-T095_06"]
    eski = {e["db_id"] for e in MUK["eski_hat"]}
    assert MUK["db_tam_hash_carpismasi"][0]["db_id"] in eski


def test_hash_degeri_yazilmadi() -> None:
    assert not re.search(r"[0-9a-f]{32}", MUK_METNI)
    assert MUK["farkli_soru_hash"] == 1233


def test_cevap_farki_sik_sirasi_ve_icerik() -> None:
    cev = {f"{c['birim']}_{c['soru']:02d}": c["cevap"] for c in ANAHTAR["cevaplar"]}
    assert len(MUK["cevap_farki"]) == 20
    assert all(cev[c["dosya"]] == c["bizim_cevap"] for c in MUK["cevap_farki"])
    # OSYM satirlarinin hepsinde kitap siklari yeniden siralamis; dogru sikkin
    # METNI basili anahtarin harfinde.
    for c in MUK["cevap_farki"]:
        if c["db_kaynak"] == "OSYM 2025 TYT":
            assert (
                not c["sik_sirasi_ayni"] and c["db_dogrusu_bizde"] == c["bizim_cevap"]
            )
    assert MUK["cevap_farki_sik_sirasi"] == 14
    icerik = MUK["cevap_farki_icerik"]
    assert len(icerik) == 6
    kaynak = {c["db_id"]: c["db_kaynak"] for c in MUK["cevap_farki"]}
    assert sum(kaynak[i] in (ESKI_2025, ESKI_2024) for _, i in icerik) == 5


def test_pozitif_kontrol_ve_normal_bicim() -> None:
    mk = _mk()
    assert len(MUK["pozitif_kontrol"]) >= 5
    assert min(k["bozuk_3gram"] for k in MUK["pozitif_kontrol"]) >= mk.GUCLU_ESIK
    assert mk.nm("Atat\u00fcrk\u2019\u00fcn \u201cs\u00f6z\u00fc\u201d") == mk.nm(
        'Atat\u00fcrk\'\u00fcn "s\u00f6z\u00fc"'
    )
    assert mk.nm("<u>millet</u>") == mk.nm("millet")
    assert mk.nm("mill\u00ee") != mk.nm("milli")


def test_indeksli_jaccard_dogrudanla_ayni() -> None:
    mk = _mk()
    biz = mk.bizim_sorular()
    ind = mk.indeks(biz)
    for a in biz[::35]:
        j, i = mk.en_yakin(a["tg"], biz, ind)
        dogrudan = max(mk.jaccard(a["tg"], b["tg"]) for b in biz)
        assert j == pytest.approx(dogrudan)
        assert j == pytest.approx(1.0) and biz[i]["tg"] == a["tg"]
    tg = mk.trigram(mk.nm("tamamen alakasiz bir metin parcasi xyzq"))
    j, _ = mk.en_yakin(tg, biz, ind)
    assert j == pytest.approx(max(mk.jaccard(tg, b["tg"]) for b in biz))


# ------------------------------- 7. eski hat pasif (0066) + beta onay (0067)

VERSIYON = KOK / "backend" / "alembic" / "versions"
ESKI_YOLU = VERSIYON / "0066_sos345_eski_hat_pasif.py"
BETA_YOLU = VERSIYON / "0067_sos345_beta_onay.py"


def _yukle(ad: str, yol: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_0066_kimlik_zincir_ascii() -> None:
    m = _yukle("eski0066", ESKI_YOLU)
    assert m.revision == "0066_sos345_eski_hat_pasif"
    assert m.down_revision == "0065_sos345_agac"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in ESKI_YOLU.read_bytes())
    assert m.ESKI_KAYNAKLAR == (ESKI_2025, ESKI_2024)
    assert m.ITHAL_ARACI == "scripts/kitap/sos345tyt_ithal.py"


def test_0066_ciftler_olcumden_turer() -> None:
    """Liste == mukerrer olcumunde modern_karsilik=true olan eski satirlar."""
    m = _yukle("eski0066", ESKI_YOLU)
    olcum = {
        (e["db_id"], e["en_yakin_bizim"].removeprefix("SOS345-"))
        for e in MUK["eski_hat"]
        if e["modern_karsilik"]
    }
    assert set(m.ESKI_MODERN) == olcum and len(m.ESKI_MODERN) == 33
    assert len({e for e, _ in m.ESKI_MODERN}) == 33
    # ayni hash'li eski satir listede (aktiflestirme icin sart)
    carp = {c["db_id"] for c in MUK["db_tam_hash_carpismasi"]}
    assert carp <= {e for e, _ in m.ESKI_MODERN} and len(carp) == 1


def test_0066_guard_modern_yoksa_dokunmaz() -> None:
    m = _yukle("eski0066", ESKI_YOLU)
    assert m.hedef_idler(set()) == []
    tum = {f"SOS345-{d}.png" for _, d in m.ESKI_MODERN}
    assert len(m.hedef_idler(tum)) == 33
    # ayni moderne iki eski satir (iki baski) baglanabilir: ikisi de duser
    assert len(m.hedef_idler(tum - {"SOS345-T010_05.png"})) == 31


def test_0066_durustluk() -> None:
    kod = ESKI_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "DELETE" not in kod.upper()
    assert "SET is_active = FALSE" in kod
    sql = " ".join(_yukle("eski0066", ESKI_YOLU)._ESKI_SQL.split())
    assert "'ithal_araci') IS NULL" in sql and "qb.is_active IS TRUE" in sql


def test_0067_kimlik_zincir_ascii() -> None:
    m = _yukle("beta0067", BETA_YOLU)
    assert m.revision == "0067_sos345_beta_onay"
    assert m.down_revision == "0066_sos345_eski_hat_pasif"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in BETA_YOLU.read_bytes())
    assert m.ITHAL_ARACI == "scripts/kitap/sos345tyt_ithal.py"
    assert m.KAYNAK == "345 2025 TYT Sosyal Bilgiler Soru Bankasi"


def test_0067_dislama_kurali() -> None:
    """Servis disi uc bayrak + gorunen alti alanda [??] + aktif hash ikizi disarida."""
    m = _yukle("beta0067", BETA_YOLU)
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


def test_0067_hedef_olculen_1233() -> None:
    isaretli = [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)]
    assert isaretli == []
    assert "1233/1233" in BETA_YOLU.read_text("ascii").splitlines()[0]


def test_0067_durustluk() -> None:
    kod = BETA_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "'human_verified'" not in kod
    assert "is_ai_generated" not in kod and "is_public" not in kod
    assert "'bireysel_denetim_yapildi', false" in kod
    assert "DELETE" not in kod.upper()
    m = _yukle("beta0067", BETA_YOLU)
    assert len(m.SINYALLER) == 5 and len(set(m.SINYALLER)) == 5
    assert "anahtar_iki_bagimsiz_okuma_1230_1233_hucre" in m.SINYALLER
