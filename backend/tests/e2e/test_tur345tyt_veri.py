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


def test_ara_cizgi_kose_cercevesini_almaz() -> None:
    """Kose cercevesi sutun cizgisi sanilmaz: varsayilandan CIZGI_SAPMA'dan uzak aday reddedilir."""
    import numpy as np

    a = np.full((1022, 742, 3), 255, np.uint8)
    a[:, 388] = 150  # varsayilandan uzak dikey cerceve (s104, s138)
    assert ku.ara_cizgi(a, 0) == ku.VARSAYILAN_CIZGI[0] == 372
    b = np.full((1022, 742, 3), 255, np.uint8)
    b[:, 374] = 150  # gercek ayrac: sapma icinde, olculen kullanilir
    assert ku.ara_cizgi(b, 0) == 374
    assert ku.ara_cizgi(b, 1) == 374


# ------------------------------------------------ 5. transkripsiyon (Faz 4)

from scripts.kitap import tur345tyt_metin_harness as mh  # noqa: E402

METIN = json.loads((CIKTI / f"{ON}metin.json").read_text("ascii"))
IKINCI = json.loads((CIKTI / f"{ON}ikinci_okuma.json").read_text("ascii"))
M = {s["dosya"]: s for s in METIN["sorular"]}


def _yazi(s: dict) -> str:
    return s["govde"] + " " + " ".join(map(str, s["sikler"].values()))


def test_metin_kapilari_yesil() -> None:
    assert mh.kapi(METIN["sorular"]) == []
    assert METIN["soru_sayisi"] == 2070 and METIN["parca_sayisi"] == 43


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
    assert s["soru"] == 2070
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == 2070
    assert len(IKINCI["hukumler"]) == s["farkli_soru"] == 164
    say = Counter(h["esasli_hata"] for h in IKINCI["hukumler"])
    assert dict(say) == s["hukum_dagilimi"]
    assert s["ilk_okuma_esasli_hata"] == say["okuma_1"] + say["ikisi"] == 83
    assert s["ikinci_okuma_esasli_hata"] == say["okuma_2"] + say["ikisi"] == 94


def test_duzeltmeler_son_metinde_uygulanmis() -> None:
    for d in IKINCI["duzeltmeler"]:
        s = M[d["dosya"]]
        assert s["okuma"].startswith("duzeltme"), d["dosya"]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for h, v in d["sikler"].items():
            assert s["sikler"][h] == str(v).replace("\u2019", "'"), (d["dosya"], h)
        for a in ("basili_no", "sekil_var", "sikler_gorsel", "etiket", "ortak_baslik"):
            assert s[a] == d[a], (d["dosya"], a)
    assert len(IKINCI["duzeltmeler"]) == 164


def test_okunamaz_tahmin_edilmedi() -> None:
    assert [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)] == []


def test_etiketler() -> None:
    et = [s["etiket"] for s in METIN["sorular"] if s.get("etiket")]
    assert len(et) == 71
    assert Counter(e.split(" - ")[0] for e in et) == {"TYT": 56, "MS\xdc": 15}


def test_ortak_baslik_kutularla_ayni() -> None:
    """Okuyucunun gordugu ortak baslik, kutu asamasindaki ortak parca gruplariyla birebir."""
    ob = {d for d, s in M.items() if s.get("ortak_baslik")}
    assert len(ob) == 20
    takip = {
        f"{k['birim']}_{k['soru']:02d}"
        for k in KUTULAR["kutular"]
        if k.get("ortak_parca")
    }
    assert takip <= ob
    for d in ob:
        a, b = (int(x) for x in M[d]["ortak_baslik"].split(" - "))
        assert M[d]["basili_no"] in (a, b), d


# ------------------------------------------------ 6. mukerrer (Faz 5)

import re  # noqa: E402


def _mk():  # type: ignore[no-untyped-def]
    """Gec ice aktarma (stm345 deseni): betik psycopg ister."""
    from scripts.kitap import tur345tyt_mukerrer

    return tur345tyt_mukerrer


MUK_METNI = (CIKTI / f"{ON}mukerrer_adaylari.json").read_text("ascii")
MUK = json.loads(MUK_METNI)
ESKI_2025 = "345 2025 Tyt T\u00fcrk\u00e7e Soru Bankas\u0131"
ESKI_2024 = "345 Tyt T\u00fcrk\u00e7e Soru Bankas\u0131"
ESKI_YAYINEVI = "345 Yayinevi TYT Turkce Soru Bankasi 2025"
PARAGRAF = "345 2025 Paragraf Sifir Risk Soru Bankasi"


def test_mukerrer_ozet() -> None:
    assert MUK["soru_sayisi"] == 2070
    assert MUK["db_satiri"] > 5000
    assert MUK["kitap_ici_ayni_hash"] == []
    # ortak parcali ciftler ayni govdeyi tasir ama siklari farkli: yakin cift degil
    assert MUK["kitap_ici_yakin"] == []
    assert MUK["osym_etiketli_soru"] == 71


def test_eski_hat_uc_aktarim() -> None:
    oz = MUK["eski_hat_ozet"]
    assert oz[ESKI_2025] == {"satir": 18, "aktif": 18, "modern_karsilik": 10}
    assert oz[ESKI_2024] == {"satir": 11, "aktif": 11, "modern_karsilik": 5}
    assert oz[ESKI_YAYINEVI] == {"satir": 2, "aktif": 2, "modern_karsilik": 2}
    for e in MUK["eski_hat"]:
        guclu = e["en_yakin_3gram"] >= _mk().GUCLU_ESIK and e["ayni_sik_sayisi"] >= 3
        assert e["modern_karsilik"] == guclu, e["db_id"]


def test_hash_carpismasi_paragraf_kitabi() -> None:
    """Ayni yayinevinin Paragraf kitabi ayni 4 cikmis soruyu basmis (ayni hash)."""
    assert sorted(c["dosya"] for c in MUK["db_tam_hash_carpismasi"]) == [
        "TRT345-T041_07",
        "TRT345-T044_07",
        "TRT345-T045_08",
        "TRT345-T069_06",
    ]
    eski = {e["db_id"] for e in MUK["eski_hat"]}
    assert not {c["db_id"] for c in MUK["db_tam_hash_carpismasi"]} & eski
    guclu = {a["db_id"]: a["db_kaynak"] for a in MUK["adaylar"] if a["guclu"]}
    for c in MUK["db_tam_hash_carpismasi"]:
        assert guclu[c["db_id"]] == PARAGRAF


def test_hash_degeri_yazilmadi() -> None:
    assert not re.search(r"[0-9a-f]{32}", MUK_METNI)
    assert MUK["farkli_soru_hash"] == 2070


def test_cevap_farki_sik_sirasi_ve_icerik() -> None:
    cev = {f"{c['birim']}_{c['soru']:02d}": c["cevap"] for c in ANAHTAR["cevaplar"]}
    assert len(MUK["cevap_farki"]) == 95
    assert all(cev[c["dosya"]] == c["bizim_cevap"] for c in MUK["cevap_farki"])
    # GUCLU OSYM satirlarinda kitap siklari yeniden siralamis; dogru sikkin
    # METNI basili anahtarin harfinde.
    osym = [
        c
        for c in MUK["cevap_farki"]
        if c["db_kaynak"] == "OSYM 2025 TYT" and c["guclu"]
    ]
    assert len(osym) == 3
    for c in osym:
        assert not c["sik_sirasi_ayni"] and c["db_dogrusu_bizde"] == c["bizim_cevap"]
    assert MUK["cevap_farki_sik_sirasi"] == 6
    kaynak = {c["db_id"]: c for c in MUK["cevap_farki"]}
    guclu_icerik = [i for _, i in MUK["cevap_farki_icerik"] if kaynak[i]["guclu"]]
    assert len(guclu_icerik) == 4
    assert all(kaynak[i]["db_kaynak"] in (ESKI_2025, ESKI_2024) for i in guclu_icerik)


def test_pozitif_kontrol_ve_normal_bicim() -> None:
    mk = _mk()
    assert len(MUK["pozitif_kontrol"]) >= 5
    assert min(k["bozuk_3gram"] for k in MUK["pozitif_kontrol"]) >= mk.GUCLU_ESIK
    assert mk.nm("Yunus\u2019un \u201cs\u00f6z\u00fc\u201d") == mk.nm(
        'Yunus\'un "s\u00f6z\u00fc"'
    )
    assert mk.nm("<u>kitap</u>") == mk.nm("kitap")
    assert mk.nm("edeb\u00ee") != mk.nm("edebi")
    assert mk.DERSLER == ("TURKCE", "EDEBIYAT")


def test_indeksli_jaccard_dogrudanla_ayni() -> None:
    mk = _mk()
    biz = mk.bizim_sorular()
    ind = mk.indeks(biz)
    for a in biz[::60]:
        j, i = mk.en_yakin(a["tg"], biz, ind)
        dogrudan = max(mk.jaccard(a["tg"], b["tg"]) for b in biz)
        assert j == pytest.approx(dogrudan)
        assert j == pytest.approx(1.0) and biz[i]["tg"] == a["tg"]
    tg = mk.trigram(mk.nm("tamamen alakasiz bir metin parcasi xyzq"))
    j, _ = mk.en_yakin(tg, biz, ind)
    assert j == pytest.approx(max(mk.jaccard(tg, b["tg"]) for b in biz))


# ------------------------------- 7. eski hat pasif (0069) + beta onay (0070)

VERSIYON = KOK / "backend" / "alembic" / "versions"
ESKI_YOLU = VERSIYON / "0069_trt345_eski_hat_pasif.py"
BETA_YOLU = VERSIYON / "0070_trt345_beta_onay.py"


def _yukle(ad: str, yol: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_0069_kimlik_zincir_ascii() -> None:
    m = _yukle("eski0069", ESKI_YOLU)
    assert m.revision == "0069_trt345_eski_hat_pasif"
    assert m.down_revision == "0068_trt345_agac"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in ESKI_YOLU.read_bytes())
    assert m.ESKI_KAYNAKLAR == (ESKI_2025, ESKI_2024, ESKI_YAYINEVI)
    assert m.ITHAL_ARACI == "scripts/kitap/tur345tyt_ithal.py"


def test_0069_ciftler_olcumden_turer() -> None:
    """Liste == mukerrer olcumunde modern_karsilik=true olan eski satirlar."""
    m = _yukle("eski0069", ESKI_YOLU)
    olcum = {
        (e["db_id"], e["en_yakin_bizim"].removeprefix("TRT345-"))
        for e in MUK["eski_hat"]
        if e["modern_karsilik"]
    }
    assert set(m.ESKI_MODERN) == olcum and len(m.ESKI_MODERN) == 17
    assert len({e for e, _ in m.ESKI_MODERN}) == 17
    # bu kitapta eski hatla ayni hash yok (carpisma Paragraf kitabiyla)
    carp = {c["db_id"] for c in MUK["db_tam_hash_carpismasi"]}
    assert not carp & {e for e, _ in m.ESKI_MODERN}


def test_0069_guard_modern_yoksa_dokunmaz() -> None:
    m = _yukle("eski0069", ESKI_YOLU)
    assert m.hedef_idler(set()) == []
    tum = {f"TRT345-{d}.png" for _, d in m.ESKI_MODERN}
    assert len(m.hedef_idler(tum)) == 17
    # ayni moderne iki eski satir baglanabilir: ikisi de duser
    ikili = Counter(d for _, d in m.ESKI_MODERN)
    d, n = ikili.most_common(1)[0]
    assert len(m.hedef_idler(tum - {f"TRT345-{d}.png"})) == 17 - n


def test_0069_durustluk() -> None:
    kod = ESKI_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "DELETE" not in kod.upper()
    assert "SET is_active = FALSE" in kod
    sql = " ".join(_yukle("eski0069", ESKI_YOLU)._ESKI_SQL.split())
    assert "'ithal_araci') IS NULL" in sql and "qb.is_active IS TRUE" in sql


def test_0070_kimlik_zincir_ascii() -> None:
    m = _yukle("beta0070", BETA_YOLU)
    assert m.revision == "0070_trt345_beta_onay"
    assert m.down_revision == "0069_trt345_eski_hat_pasif"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in BETA_YOLU.read_bytes())
    assert m.ITHAL_ARACI == "scripts/kitap/tur345tyt_ithal.py"
    assert m.KAYNAK == "345 2025 TYT Turkce Soru Bankasi"


def test_0070_dislama_kurali() -> None:
    """Servis disi uc bayrak + gorunen alti alanda [??] + aktif hash ikizi disarida."""
    m = _yukle("beta0070", BETA_YOLU)
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


def test_0070_hedef_olculen_2066() -> None:
    isaretli = [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)]
    assert isaretli == []
    # 2070 - Paragraf kitabinda ayni hash ile duran 4 soru
    assert len(MUK["db_tam_hash_carpismasi"]) == 4
    assert "2066/2066" in BETA_YOLU.read_text("ascii").splitlines()[0]


def test_0070_durustluk() -> None:
    kod = BETA_YOLU.read_text("ascii").split('"""', 2)[2]
    assert "'human_verified'" not in kod
    assert "is_ai_generated" not in kod and "is_public" not in kod
    assert "'bireysel_denetim_yapildi', false" in kod
    assert "DELETE" not in kod.upper()
    m = _yukle("beta0070", BETA_YOLU)
    assert len(m.SINYALLER) == 5 and len(set(m.SINYALLER)) == 5
    assert "anahtar_iki_bagimsiz_okuma_2067_2070_hucre" in m.SINYALLER
