"""345 2025 TYT Kimya verisi -- cevap anahtari ham okumalardan turer.

Ekran goruntusu istemez (CI'da yok); yalniz depodaki JSON'lari ve
`kim345tyt_anahtar.py`'nin saf fonksiyonlarini kullanir.

NE KORUR
1. TURETME     -- anahtar, ham A/B okumalarindan birebir yeniden uretilir.
2. MUTASYON    -- A/B farki, gereksiz fark karari, bicim disi girdi, numara
                  kopmasi, simge sayisi farki SystemExit verir.
3. KAPSAM      -- soru sayfalari x {L, R}; sutun girdi sayisi == simge sayisi.
4. DURUSTLUK   -- her cevabin kaynagi iki okuma; piksel ya da goz kanali.
5. UNITE AGACI -- 0062 migration'i harita ile ayni.
6. KUTULAR     -- 1307 kirpim kutusu anahtarla birebir.
7. METIN       -- kapilar yesil; on kayitli tam ikinci okuma, 192 fark hakemle
                  cozuldu; soluk isaretler pikselden; Lewis cizimi metne dokulmez.
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


# ------------------------------------------------ 7. transkripsiyon (Faz 4)

from scripts.kitap import kim345tyt_metin_harness as mh  # noqa: E402

METIN = json.loads((CIKTI / f"{ON}metin.json").read_text("ascii"))
IKINCI = json.loads((CIKTI / f"{ON}ikinci_okuma.json").read_text("ascii"))
M = {s["dosya"]: s for s in METIN["sorular"]}


def _yazi(s: dict) -> str:
    return s["govde"] + " " + " ".join(map(str, s["sikler"].values()))


def test_metin_kapilari_yesil() -> None:
    assert mh.kapi(METIN["sorular"]) == []
    assert METIN["soru_sayisi"] == 1307 and METIN["parca_sayisi"] == 30


def test_metin_kapisi_mutasyonu_yakalar() -> None:
    bozuk = copy.deepcopy(METIN["sorular"])
    bozuk[3]["basili_no"] = 99
    bozuk[5]["sikler"]["C"] = " "
    del bozuk[7]
    hata = mh.kapi(bozuk)
    for k in ("KAPI1", "KAPI2", "KAPI3", "KAPI4"):
        assert any(h.startswith(k) for h in hata), k


def test_null_numara_yalniz_ortulu_sorularda() -> None:
    nuller = {s["dosya"] for s in METIN["sorular"] if s.get("basili_no") is None}
    assert nuller == {"KMT345-T073_09", "KMT345-T094_04"}
    assert nuller <= mh.numarasi_ortulu() | mh.ortme_listesi()
    assert mh.numara_goz_listesi() == set()


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
    assert s["soru"] == 1307
    assert s["ayni_soru_normalize"] + s["farkli_soru"] == 1307
    assert len(IKINCI["hukumler"]) == s["farkli_soru"] == 192
    say = Counter(h["esasli_hata"] for h in IKINCI["hukumler"])
    assert dict(say) == s["hukum_dagilimi"]
    assert s["ilk_okuma_esasli_hata"] == say["okuma_1"] + say["ikisi"] == 62
    assert s["ikinci_okuma_esasli_hata"] == say["okuma_2"] + say["ikisi"] == 46


def test_duzeltmeler_son_metinde_uygulanmis() -> None:
    for d in IKINCI["duzeltmeler"]:
        s = M[d["dosya"]]
        assert s["govde"] == d["govde"].replace("\u2019", "'"), d["dosya"]
        for h, v in d["sikler"].items():
            assert s["sikler"][h] == str(v).replace("\u2019", "'"), (d["dosya"], h)
        for a in ("sekil_var", "sikler_gorsel", "etiket"):
            assert s[a] == d[a], (d["dosya"], a)
    assert len(IKINCI["duzeltmeler"]) == 195  # 192 hukum + 3 Lewis sozlesmesi


def test_okunamaz_tahmin_edilmedi() -> None:
    assert [s["dosya"] for s in METIN["sorular"] if "[??]" in _yazi(s)] == []


def test_lewis_cizimi_metne_dokulmedi() -> None:
    for s in METIN["sorular"]:
        t = _yazi(s)
        assert "[Lewis" not in t and "O::C::O" not in t and "[:" not in t, s["dosya"]
    assert "(\u015fekil)" in M["KMT345-T048_09"]["govde"]


def test_soluk_isaret_pikselden_karara_baglandi() -> None:
    """Soluk '+' (dikey cubugu silik) pikselde varsa '+', yoksa basildigi gibi '-'."""
    assert "NH_4^+" in M["KMT345-T039_01"]["sikler"]["D"]
    assert "_(11)Na^+" in M["KMT345-T018_07"]["govde"]
    # dikey iz olmayan eksi basildigi gibi korunur (cozum yapilmaz)
    assert "Na^\u2212" in M["KMT345-T034_05"]["govde"]
    assert "Mg^(2\u2212) ile" in M["KMT345-T042_04"]["govde"]
    t = IKINCI["soluk_isaret_taramasi"]
    assert t["aday"] == 41 and t["katyon_eksi"]["liste"] == 9


def test_etiketler_iki_okumada_ayni() -> None:
    et = [s["etiket"] for s in METIN["sorular"] if s.get("etiket")]
    assert len(et) == 100
    assert Counter(e.split(" - ")[0] for e in et) == {"TYT": 51, "MS\xdc": 49}


# ------------------------------------------------ 8. mukerrer (Faz 5)

import re  # noqa: E402


def _mk():  # type: ignore[no-untyped-def]
    """Gec ice aktarma (stm345 deseni): betik psycopg ister."""
    from scripts.kitap import kim345tyt_mukerrer

    return kim345tyt_mukerrer


MUK_METNI = (CIKTI / f"{ON}mukerrer_adaylari.json").read_text("ascii")
MUK = json.loads(MUK_METNI)
ESKI_2025 = "345 2025 Tyt Kimya Soru Bankas\u0131"
ESKI_2024 = "345 Tyt Kimya Soru Bankas\u0131"


def test_mukerrer_ozet() -> None:
    assert MUK["soru_sayisi"] == 1307
    assert MUK["db_satiri"] > 4000
    # ayni genel govde ("Asagidakilerden hangisi yanlistir?") kitap icinde
    # tekrar eder ama siklar farkli: ne ayni hash ne yakin cift
    assert MUK["kitap_ici_ayni_hash"] == [] and MUK["kitap_ici_yakin"] == []
    assert MUK["osym_etiketli_soru"] == 100


def test_eski_hat_iki_baski() -> None:
    oz = MUK["eski_hat_ozet"]
    assert oz[ESKI_2025] == {"satir": 294, "aktif": 294, "modern_karsilik": 211}
    assert oz[ESKI_2024] == {"satir": 213, "aktif": 213, "modern_karsilik": 119}
    for e in MUK["eski_hat"]:
        guclu = e["en_yakin_3gram"] >= _mk().GUCLU_ESIK and e["ayni_sik_sayisi"] >= 3
        assert e["modern_karsilik"] == guclu, e["db_id"]


def test_hash_carpismasi_eski_hat_ve_ayt() -> None:
    carp = {c["dosya"] for c in MUK["db_tam_hash_carpismasi"]}
    assert len(MUK["db_tam_hash_carpismasi"]) == len(carp) == 36
    assert "KMT345-T073_09" in carp and "KMT345-T136_07" in carp


def test_hash_degeri_yazilmadi() -> None:
    assert not re.search(r"[0-9a-f]{32}", MUK_METNI)
    assert MUK["farkli_soru_hash"] == 1307


def test_cevap_farki_kaydi_basili_anahtari_degistirmez() -> None:
    cev = {f"{c['birim']}_{c['soru']:02d}": c["cevap"] for c in ANAHTAR["cevaplar"]}
    assert len(MUK["cevap_farki"]) == 59
    assert all(cev[c["dosya"]] == c["bizim_cevap"] for c in MUK["cevap_farki"])


def test_pozitif_kontrol_ve_isaret_korunur() -> None:
    mk = _mk()
    assert len(MUK["pozitif_kontrol"]) >= 5
    assert min(k["latex_3gram"] for k in MUK["pozitif_kontrol"]) >= mk.GUCLU_ESIK
    assert mk.nm("SO_4^(2\u2212)") == mk.nm("$SO_{4}^{2-}$")
    assert mk.nm("Na^+") != mk.nm("Na^\u2212")


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
