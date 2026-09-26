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


# ------------------------------------------------- 6. kirpim kutulari (Faz 3)

sys.path.insert(0, str(KOK / "backend" / "scripts" / "kitap"))
from scripts.kitap import fiz345tyt_kutu as ku  # noqa: E402

KUTULAR = json.loads(
    (CIKTI / "345_2025_tyt_fizik_kirpim_kutulari.json").read_text("ascii")
)
ORTME = json.loads((CIKTI / "345_2025_tyt_fizik_ortme_olcumu.json").read_text("ascii"))


def test_kutu_kapilari_temiz() -> None:
    assert ku.kapilar(KUTULAR) == []
    assert KUTULAR["kutu_sayisi"] == 1397 and KUTULAR["kutusuz_soru"] == 0


def test_kutu_ile_cevap_birebir() -> None:
    k = {(x["birim"], x["soru"]): x for x in KUTULAR["kutular"]}
    for c in ANAHTAR["cevaplar"]:
        x = k[(c["birim"], c["soru"])]
        assert (x["dosya"], x["sutun"], x["serit_sira"]) == (
            c["dosya"],
            c["sutun"],
            c["serit_sira"],
        )


def test_capa_kanali_simge_sayisiyla_tutarli() -> None:
    for x in KUTULAR["kutular"]:
        sim = TARAMA["sayfalar"][str(x["dosya"])]["simge"][x["sutun"]]
        if x["capa_kanali"] == "simge":
            assert [x["capa"][0] + 6, x["capa"][1] - 6] in [[m[0], m[0]] for m in sim]
    assert set(KUTULAR["sutun_kanali"]) <= {"numara", "simge"}
    assert sum(KUTULAR["sutun_kanali"].values()) == 714


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


# ------------------------------------------------ 7. transkripsiyon (Faz 4)

from scripts.kitap import fiz345tyt_metin_harness as mh  # noqa: E402

METIN = json.loads((CIKTI / "345_2025_tyt_fizik_metin.json").read_text("ascii"))
IKINCI = json.loads((CIKTI / "345_2025_tyt_fizik_ikinci_okuma.json").read_text("ascii"))
NUMARA_GOZ = json.loads(
    (CIKTI / "345_2025_tyt_fizik_numara_goz.json").read_text("ascii")
)


def test_metin_kapilari_yesil() -> None:
    assert mh.kapi(METIN["sorular"]) == []
    assert METIN["soru_sayisi"] == 1397


def test_metin_kapisi_mutasyonu_yakalar() -> None:
    bozuk = copy.deepcopy(METIN["sorular"])
    bozuk[3]["basili_no"] = 99
    bozuk[5]["sikler"]["C"] = " "
    del bozuk[7]
    hata = mh.kapi(bozuk)
    assert any(h.startswith("KAPI2") for h in hata)
    assert any(h.startswith("KAPI3") for h in hata)
    assert any(h.startswith("KAPI1") for h in hata)
    assert any(h.startswith("KAPI4") for h in hata)


def test_null_numara_yalniz_ortulu_sorularda() -> None:
    """Null basili_no yalniz simge kanali, ortme olcumu ya da gozle listelenen
    tam ortmede; listeden cikan bir soru KAPI2'ye takilir."""
    ortulu = mh.numarasi_ortulu() | mh.ortme_listesi() | mh.numara_goz_listesi()
    nuller = {s["dosya"] for s in METIN["sorular"] if s.get("basili_no") is None}
    assert nuller <= ortulu
    goz = set(NUMARA_GOZ["dosyalar"])
    assert len(goz) == 53 and goz <= nuller
    assert not goz & (mh.numarasi_ortulu() | mh.ortme_listesi())


def test_numara_goz_listesi_disinda_null_durur(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mh, "numara_goz_listesi", set)
    hata = mh.kapi(METIN["sorular"])
    assert len([h for h in hata if h.startswith("KAPI2")]) == 53


def test_metin_kutularla_ayni_dosyalar() -> None:
    k = {f"{x['birim']}_{x['soru']:02d}" for x in KUTULAR["kutular"]}
    assert {s["dosya"] for s in METIN["sorular"]} == k


def test_kivrik_kesme_ve_numara_notu_kalmadi() -> None:
    for s in METIN["sorular"]:
        assert "\u2019" not in s["govde"]
        assert all("\u2019" not in str(v) for v in s["sikler"].values())
        if s.get("kaynak_kusuru"):
            assert not mh.NUMARA_NOTU.search(s["kaynak_kusuru"]), s["dosya"]


def test_numara_notu_ayiklama() -> None:
    f = mh.numara_notu_ayikla
    assert f("soru numaras\u0131 beyaz daireyle kesik") is None
    assert f("bas\u0131l\u0131 no k\u0131smen kesik: 8 veya 3") is None
    assert (
        f(
            "g\xf6r\xfcnen k\u0131s\u0131m '3' ya da '8' olabilir; soru k\xf6k\xfcnde ayra\xe7 belirsiz"
        )
        == "soru k\xf6k\xfcnde ayra\xe7 belirsiz"
    )
    # tirnak icindeki ';' bozulmaz, numara disi not aynen kalir
    s = "C \u015f\u0131kk\u0131nda T_L sonras\u0131 ayra\xe7 belirsiz: ';' veya ','"
    assert f(s) == s
    t = "tablo: ortadaki rakam 9 mu 8 mi (9,798 / 9,788)"
    assert f(t) == t


def test_ikinci_okuma_on_kayitli_tam_okuma() -> None:
    assert "TAM ikinci okuma" in IKINCI["kural"]
    assert "SONRA" in IKINCI["tasarim"]
    s = IKINCI["sonuc"]
    assert s["soru"] == 1397
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == 1397
    assert len(IKINCI["hukumler"]) == s["farkli_soru"] == 69
    say = Counter(h["esasli_hata"] for h in IKINCI["hukumler"])
    assert dict(say) == s["hukum_dagilimi"]
    assert s["ilk_okuma_esasli_hata"] == say["okuma_1"] + say["ikisi"] == 14


def test_duzeltmeler_son_metinde_uygulanmis() -> None:
    m = {s["dosya"]: s for s in METIN["sorular"]}
    for d in IKINCI["duzeltmeler"]:
        s = m[d["dosya"]]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for h, v in d["sikler"].items():
            assert s["sikler"][h] == str(v).replace("\u2019", "'"), (d["dosya"], h)
        for a in ("sekil_var", "sikler_gorsel", "etiket"):
            assert s[a] == d[a], (d["dosya"], a)


def test_okunamaz_tahmin_edilmedi() -> None:
    isaretli = [
        s["dosya"]
        for s in METIN["sorular"]
        if "[??]" in s["govde"] + " ".join(map(str, s["sikler"].values()))
    ]
    assert isaretli == ["FZT345-T118_07"]
    s = {x["dosya"]: x for x in METIN["sorular"]}["FZT345-T118_07"]
    assert s["kaynak_kusuru"] and s["govde"].count("[??]") == 3


def test_iki_okumanin_farki_goruntuden_cozuldu() -> None:
    """Ornek hukumler: ilk okumanin esasli hatalari son metinde duzelmis."""
    m = {s["dosya"]: s for s in METIN["sorular"]}
    assert "montelenmesi" in m["FZT345-T074_05"]["govde"]
    assert "\u03b1 > \u03b8" in m["FZT345-T082_07"]["govde"]
    assert "1. rota: 19 km, 26 dk" in m["FZT345-T027_03"]["govde"]
    assert "duyurabilmesi" in m["FZT345-T149_05"]["govde"]
    # kitabin baski hatasi korunur (duzeltme yok)
    assert (
        "kar\u015f\u0131la\u015ft\u0131malar\u0131ndan" in m["FZT345-T011_07"]["govde"]
    )


def test_etiketler_iki_okumada_ayni() -> None:
    et = [s["etiket"] for s in METIN["sorular"] if s.get("etiket")]
    assert len(et) == 40
    assert all(e.split(" - ")[0] in ("TYT", "MS\xdc") for e in et)


def test_soluk_arti_taramasi_kaydi() -> None:
    t = IKINCI["soluk_isaret_taramasi"]
    assert t["aday"] == 11 and "gizli '+' yok" in t["goz_sonucu"]


# ------------------------------------------------ 8. mukerrer (Faz 5)

import re  # noqa: E402


def _mk():  # type: ignore[no-untyped-def]
    """Gec ice aktarma (stm345 deseni): betik psycopg ister."""
    from scripts.kitap import fiz345tyt_mukerrer

    return fiz345tyt_mukerrer


MUK_METNI = (CIKTI / "345_2025_tyt_fizik_mukerrer_adaylari.json").read_text("ascii")
MUK = json.loads(MUK_METNI)


def test_mukerrer_ozet() -> None:
    assert MUK["soru_sayisi"] == 1397
    assert MUK["db_satiri"] > 4000
    assert MUK["kitap_ici_ayni_hash"] == [] and MUK["kitap_ici_yakin"] == []
    assert MUK["eski_hat"] == []
    assert MUK["osym_etiketli_soru"] == 40


def test_guclu_adaylar_yalniz_cikmis_sorular() -> None:
    """Baska kitaplarda da basilan OSYM sorulari; etiketsiz guclu aday yok."""
    guclu = [a for a in MUK["adaylar"] if a["guclu"]]
    assert guclu and all(a["etiketli"] for a in guclu)
    assert {a["dosya"] for a in guclu} == set(MUK["osym_etiketli_guclu_aday"])
    carpisan = {c["dosya"] for c in MUK["db_tam_hash_carpismasi"]}
    assert carpisan == {"FZT345-T014_02", "FZT345-T016_04"}
    assert carpisan <= {a["dosya"] for a in guclu}


def test_hash_degeri_yazilmadi() -> None:
    assert not re.search(r"[0-9a-f]{32}", MUK_METNI)
    assert MUK["farkli_soru_hash"] == 1397


def test_cevap_farki_kaydi_basili_anahtari_degistirmez() -> None:
    farklar = {c["dosya"]: c for c in MUK["cevap_farki"]}
    assert farklar["FZT345-T120_09"]["bizim_cevap"] == "D"
    cev = {f"{c['birim']}_{c['soru']:02d}": c["cevap"] for c in ANAHTAR["cevaplar"]}
    assert all(cev[d] == c["bizim_cevap"] for d, c in farklar.items())


def test_pozitif_kontrol_ve_isaret_korunur() -> None:
    mk = _mk()
    assert len(MUK["pozitif_kontrol"]) >= 5
    assert min(k["latex_3gram"] for k in MUK["pozitif_kontrol"]) >= mk.GUCLU_ESIK
    assert mk.nm("F_K \u2212 F_L") == mk.nm("$F_{K} - F_{L}$")
    assert mk.nm("a \u2212 b") != mk.nm("a + b")


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


# ------------------------------------------------- 9. beta onay (0061)

BETA_YOLU = KOK / "backend" / "alembic" / "versions" / "0061_fzt345_beta_onay.py"


def _beta():  # type: ignore[no-untyped-def]
    import importlib.util

    spec = importlib.util.spec_from_file_location("beta0061", BETA_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_0061_kimlik_zincir_ascii() -> None:
    m = _beta()
    assert m.revision == "0061_fzt345_beta_onay"
    assert m.down_revision == "0060_fzt345_agac"
    assert len(m.revision) <= 32
    assert all(c < 128 for c in BETA_YOLU.read_bytes())
    assert m.ITHAL_ARACI == "scripts/kitap/fiz345tyt_ithal.py"
    assert m.KAYNAK == "345 2025 TYT Fizik Soru Bankasi"


def test_0061_dislama_kurali() -> None:
    """Servis disi uc bayrak + gorunen alti alanda [??] + aktif hash ikizi disarida."""
    m = _beta()
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


def test_0061_hedef_olculen_1394() -> None:
    """1397 - 2 (baska kaynakta ayni hash, yazilmadi) - 1 ([??]) = 1394."""
    isaretli = [
        s["dosya"]
        for s in METIN["sorular"]
        if "[??]" in s["govde"] + "".join(map(str, s["sikler"].values()))
    ]
    yazilmayan = {c["dosya"] for c in MUK["db_tam_hash_carpismasi"]}
    assert not yazilmayan & set(isaretli)
    assert len(METIN["sorular"]) - len(yazilmayan) - len(isaretli) == 1394
    assert "1394/1395" in BETA_YOLU.read_text("ascii").splitlines()[0]


def test_0061_durustluk() -> None:
    kaynak = BETA_YOLU.read_text("ascii")
    kod = kaynak.split('"""', 2)[2]
    assert "'human_verified'" not in kod
    assert "is_ai_generated" not in kod and "is_public" not in kod
    assert "'bireysel_denetim_yapildi', false" in kod
    assert "DELETE" not in kod.upper()
    m = _beta()
    assert len(m.SINYALLER) == 5 and len(set(m.SINYALLER)) == 5
