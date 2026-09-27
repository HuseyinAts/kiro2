"""2020-2021 ACIL TYT Matematik Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri; sayfa karti (589, 43) -
(1331, 1022) = 742x979. 448 PNG; basili sayfa = dosya. 430 test sayfasi +
18 kapak (1-5, 13 bolum kapagi, arka kapak). Acik uclu sayfa yok.

BIRIM = TEST, KONU = ICINDEKILER KONUSU
---------------------------------------
150 test, 2113 soru, 13 bolum, 30 konu (icindekiler s3). Her test tek bir
konu araligina duser; bant adi konu ya da basili alt basligi (BOLME,
EBOB, YAS PROBLEMLERI ...). Tum testler KONU dugumune baglanir (0074;
MAT kokunun altinda MAT-ACL21T-* kodlari). `subject_area` MATEMATIK.

CEVAP KAYNAGI: TEST SONU CEVAP SERIDI
-------------------------------------
Her testin son sayfasindaki sari cevap seridi iki bagimsiz gorsel okumayla
(dort okuyucu) okundu: 2113/2113 hucre ayni. Ucuncu kanal piksel glif LOO
2039/2041 (2 uyumsuz 5x gozle: okuma dogru); bolutlenemeyen 4 test (72
hucre) 5x gozle, hepsi ayni. Hucre sayisi == kirmizi basili numara capasi
(150/150 test). Hicbir soru cozulmedi.

METIN
-----
45 grupta ayri okuyucularla kirpimdan; on kayitli TAM ikinci okuma (45
bagimsiz okuyucu, 249 fark 8 hakemle gozle). Okuyucu diskinin altinda
kalan yazi `[??]`; tahmin yok. null numara yok.

ORTME: ITHAL EDILIR, ISARETLENIR
--------------------------------
Disk halkasinda murekkep olculen sorular `okuyucu_diski_ortme` tasir;
metninde `[??]` kalan sorular `okunamaz_isaret` bayragi tasir (beta
kapisinda disarida kalir).

MUKERRER ADAYLARI ISARETLENIR, SILINMEZ
---------------------------------------
acil_2021_tyt_matematik_mukerrer_adaylari.json: GUCLU aday ->
`mukerrer_aday`. DB ile ayni soru_hash -> ayni id; `ayristir` bunlari
YABANCI sayar, dokunulmaz ve yazilmaz. Baska kaynakta farkli cevap
(GUCLU) iki ayri bilgi: DB'nin dogru sikkinin metni bizde basili
harfteyse `diger_kaynak_sik_sirasi_farkli`, degilse
`diger_kaynak_cevap_farki`. Bizim cevap basili anahtar.

BILINEN BORC
------------
  * Cozumler kitapta soru sayfasinda YOK; `explanation` bos.
  * Sekil icindeki etiketler govdeye yalniz soru onlara dayaniyorsa girer.

Detay: veriseti/zkitap/cikti/MAT_ACIL_2021_TYT_YONTEM.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz
from scripts.kitap.metin_olcum import (
    bloom_belirle,
    kelime_istatistik,
    morfoloji_karmasikligi,
    okunabilirlik,
    sik_bayraklari,
    soru_hash,
)

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
CIKTI = "veriseti/zkitap/cikti"
ONEK_DOSYA = f"{CIKTI}/acil_2021_tyt_matematik"
VARSAYILAN_VERI = f"{ONEK_DOSYA}_metin.json"
VARSAYILAN_HARITA = f"{ONEK_DOSYA}_konu_haritasi.json"
VARSAYILAN_KUTULAR = f"{ONEK_DOSYA}_kirpim_kutulari.json"
VARSAYILAN_ANAHTAR = f"{ONEK_DOSYA}_cevap_anahtari.json"
VARSAYILAN_ORTME = f"{ONEK_DOSYA}_ortme_olcumu.json"
VARSAYILAN_MUKERRER = f"{ONEK_DOSYA}_mukerrer_adaylari.json"
VARSAYILAN_HAM = f"{ONEK_DOSYA}_ham_okumalar.json"
KAYNAK_ADI = "2020-2021 ACIL TYT Matematik Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
KOK_KODLARI = ("MAT",)
KOD_IMI = "MAT-ACL21T-"
DERSLER = ("MATEMATIK",)
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/acil2021tyt_ithal.py"
CROP_ONEK = "ACL21T"
TELIF_NOTU = (
    "ACIL Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
    "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar her testin son "
    "sayfasindaki cevap seridinden iki bagimsiz gorsel okumayla alindi (2113/2113 "
    "hucre ayni; piksel glif LOO ucuncu kanal 2039/2041, 2 uyumsuz 5x goz teyidi; "
    "bolutlenemeyen 4 test 5x goz). Sorular cozulmedi. Kirpim kutulari kirmizi basili "
    "numara capasindan (2113 == serit hucresi). Transkripsiyon 45 grupta ayri "
    "okuyucularla kirpimdan; on kayitli TAM ikinci okuma; anahtar gosterilmedi. "
    "Detay: veriseti/zkitap/cikti/MAT_ACIL_2021_TYT_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "test_sonu_serit_iki_okuma_2113_2113_hucre_ayni__piksel_glif_loo_2039_2041_uyumsuz_goz__"
    "glif_disi_4_test_goz_5x__hucre_sayisi_esittir_kirmizi_numara_capasi_2113"
)
CEVAP_KAYNAGI = "test_sonu_cevap_seridi"
CEVAP_KANALLARI = (
    "iki_okuma+glif",
    "iki_okuma+glif_uyumsuz+goz_teyidi(5x)",
    "iki_okuma+goz(5x)",
)
KIRPIM_SISTEMI = "sayfa_karti_589_43_1331_1022_kirmizi_numara_capasindan"
CAPA_KANALI = "kirmizi_basili_numara"
# Ayni yayinevinin bir onceki baskisi (modern ithal, 0071-0073). Bu kitabin
# sorularinin ~%38'i orada GUCLU eslesir; ayni hash olanlar ayni id tasir ve
# yazilmaz, digerleri `modern_kitap_ikizi` ile isaretlenir (beta kapisi
# ikizi AKTIF olani acmaz -- 0076).
MODERN_IKIZ_KAYNAK = "2019-2020 ACIL TYT Matematik Soru Bankasi"
BEKLENEN_SORU = 2113
BEKLENEN_TEST = 150
BEKLENEN_BOLUM = 13
BEKLENEN_KONU = 30
BEKLENEN_ETIKET = 0
SIK_OKUNAMADI = "[okunamad\u0131]"
GORSEL_SIK = "(g\u00f6rsel \u015f\u0131k)"
OKUNAMAZ = "[??]"
# 'MSU - 2021' / 'TYT - 2023': sinav adi + yil (U+00DC = U-umlaut).
_ETIKET = re.compile(r"(TYT|AYT|YGS|LYS|MS\u00dc|MSU)|((?:19|20)\d\d)")


def etiket_ayristir(etiket: str | None) -> tuple[str | None, int | None]:
    """'MSU - 2021' -> ('MSU', 2021). Etiket yoksa ya da bicim disiysa (None, None)."""
    if not etiket:
        return None, None
    sinav = yil = None
    for ad, sayi in _ETIKET.findall(etiket):
        if ad:
            sinav = "MSU" if ad.startswith("MS") else ad
        if sayi:
            yil = int(sayi)
    if sinav is None or yil is None:
        return None, None
    return sinav, yil


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("sikler_gorsel"):
        b.append("sikler_gorsel")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_kusuru")
    if r.get("ortme"):
        b.append("okuyucu_diski_ortme")
    if r.get("basili_no") is None:
        b.append("numara_ortulu")
    if r.get("modern_ikiz"):
        b.append("modern_kitap_ikizi")
    if r.get("mukerrer"):
        b.append("mukerrer_aday")
    if r.get("hash_carpismasi"):
        b.append("db_hash_carpismasi")
    if r.get("cevap_farki"):
        b.append("diger_kaynak_cevap_farki")
    if r.get("sik_sirasi_farki"):
        b.append("diger_kaynak_sik_sirasi_farkli")
    if r.get("sinav_yili"):
        b.append("cikmis_soru")
    if OKUNAMAZ in r["govde"] + "".join(sec.values()):
        b.append("okunamaz_isaret")
    if any(v == SIK_OKUNAMADI for v in sec.values()):
        b.append("sik_okunamadi")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r["sikler"][h] for h in "ABCDE"}
    h = soru_hash(r["govde"], sec)
    n, u, ort = kelime_istatistik(r["govde"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["govde"], sec)
    kutu = r["kirpim_kutusu"]
    basili_sayfa = int(r["sayfa"])
    cikmis = r.get("sinav_yili") is not None
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "subject_area": r["ders"],
        "question_text": r["govde"],
        "secenekler": sec,
        "correct_answer": r["cevap"],
        # GORSEL ADI: kirpim script'inin urettigi ad (BIRIM_SS.png).
        "question_image_url": f"/static/crops/{CROP_ONEK}/{r['dosya']}.png",
        "explanation": None,
        "source_page": basili_sayfa,
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["govde"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["govde"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": r["sinav_yili"] if cikmis else None,
        "osym_format_compliant": cikmis,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "konu_eslesme_duzeyi": r["duzey"],
            "konu_kaynagi": "sayfa_ust_bandi_konu_ve_icindekiler",
            "ders": r["ders"],
            "test_no": r["test_no"],
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": basili_sayfa,
            "sutun": r["sutun"],
            "sutun_sira": r["sutun_sira"],
            "soru_no_basili": r["basili_no"],
            "soru_no_kaynagi": (
                "basili" if r["basili_no"] is not None else "test_ici_sira"
            ),
            "birim_kodu": r["birim"],
            "birim_ici_sira": r["soru"],
            "bolum_kodu": r["bolum_kodu"],
            "bolum_adi": r["bolum_adi"],
            "konu_adi": r["konu_adi"],
            "kaynak_gorseli": f"{r['dosya']}.png",
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "cevap_okuma_kanali": r["cevap_kanali"],
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "cikmis_soru": cikmis,
            "cikmis_etiketi": r.get("etiket") or None,
            "sinav": r.get("sinav"),
            "sinav_yili": r.get("sinav_yili"),
            "sekil_var": bool(r.get("sekil_var")),
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kaynak_kusuru": r.get("kaynak_kusuru") or None,
            "okuyucu_diski_ortme": r.get("ortme"),
            "mukerrer_aday": r.get("mukerrer"),
            "modern_kitap_ikizi": r.get("modern_ikiz"),
            "db_hash_carpismasi": r.get("hash_carpismasi"),
            "diger_kaynak_cevap_farki": r.get("cevap_farki"),
            "diger_kaynak_sik_sirasi_farkli": r.get("sik_sirasi_farki"),
            "kirpim_kutusu": kutu,
            "gorsel_boyu": [kutu[2] - kutu[0], kutu[3] - kutu[1]] if kutu else None,
            "kirpim_capa_kanali": r["capa_kanali"],
            "kirpim_koordinat_sistemi": KIRPIM_SISTEMI,
            "gorsel_kaynagi": "tam_soru_kirpimi_okuyucu_diski_beyazlatilmis",
            "metin_kaynagi": f"soru_kirpimi_gorsel_okuma_{r['okuma']}_tam_ikinci_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_742x979",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": ITHAL_ARACI,
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(konu_id)s, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
"""
_QC = """
INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, explanation, question_image_url, image_width, image_height)
VALUES (%(id)s, %(question_text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(e)s, %(correct_answer)s,
    NULL, %(question_image_url)s, %(image_width)s, %(image_height)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', %(subject_area)s, %(grade_level)s,
    %(osym_format_compliant)s, %(osym_year)s, %(source_book)s,
    %(source_page)s, %(pipeline_metadata)s::json, %(morphology_complexity)s, %(word_count)s,
    %(unique_word_count)s, %(average_word_length)s, %(readability_score)s, 'PENDING')
"""
_QS = """
INSERT INTO question_statistics (id, difficulty_level, irt_based_difficulty, student_success_rate,
    difficulty_update_count, irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
    is_calibrated, calibration_sample_size, calibration_quality_score, times_asked, times_correct,
    times_wrong, times_skipped, average_response_time, median_response_time, exposure_rate,
    quality_score, quality_review_status)
VALUES (%(id)s, 'MEDIUM', 'medium', 0.5, 0, 1.0, 0.0, 0.2, 1.0, FALSE, 0, 0.0, 0, 0, 0, 0, 0.0, 0.0, 0.0,
    100.0, 'pending')
"""


def dugum_dogrula(kod: str, t: dict, konu: dict) -> str:
    """Her test konu dugumune baglanir; konunun bolumu testin bolumu olmali."""
    dugum = str(t["konu"])
    if dugum not in konu or konu[dugum]["bolum"] != t["bolum"]:
        raise ValueError(f"{kod}: konu {dugum} bolumu {t['bolum']} degil")
    return dugum


def satirlari_bagla(
    veri: dict,
    harita: dict,
    kutular: dict,
    anahtar: dict,
    *,
    ortme: dict,
    mukerrer: dict,
    goz_hucreleri: dict[tuple[str, int], str] | None = None,
) -> list[dict[str, Any]]:
    """Metin, konu haritasi, kirpim kutusu, cevap anahtari, ortme ve mukerrer adaylarini birlestirir.

    Birlestirme anahtari (test kodu, test ici sira). BASILI numaranin test ici
    siraya esitligi AYRICA dogrulanir (bu kitapta null numara yok).
    """
    test = {t["birim"]: t for t in harita["testler"]}
    bolum = {b["kod"]: b for b in harita["bolumler"]}
    konu = {k["kod"]: k for k in harita["konular"]}
    kutu = {(k["birim"], k["soru"]): k for k in kutular["kutular"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    ortulen: dict[tuple[str, int], list] = {}
    for o in ortme["ortme"]:
        ortulen.setdefault((o["birim"], o["soru"]), []).append(o["simge"])
    guclu = {
        a["dosya"]: {
            k: a[k] for k in ("db_id", "db_kaynak", "govde_3gram", "ayni_sik_sayisi")
        }
        for a in mukerrer["adaylar"]
        if a["guclu"]
    }
    carpisan = {c["dosya"]: c["db_id"] for c in mukerrer["db_tam_hash_carpismasi"]}
    ikiz: dict[str, list[str]] = {}
    for a in mukerrer["adaylar"]:
        if a["guclu"] and a["db_kaynak"] == MODERN_IKIZ_KAYNAK:
            ikiz.setdefault(a["dosya"], []).append(a["db_id"])
    goz_hucreleri = goz_hucreleri or {}
    cevap_farki: dict[str, dict] = {}
    sik_sirasi: dict[str, dict] = {}
    for c in mukerrer["cevap_farki"]:
        if not c["guclu"]:
            continue
        kayit = {k: c[k] for k in ("db_id", "db_kaynak", "db_cevap", "govde_3gram")}
        if c["db_dogrusu_bizde"] == c["bizim_cevap"]:
            sik_sirasi[c["dosya"]] = kayit
        else:
            cevap_farki[c["dosya"]] = kayit
    satir = []
    for s in veri["sorular"]:
        kod, sira = s["dosya"].rsplit("_", 1)
        sira_i = int(sira)
        k = kutu[(kod, sira_i)]
        if s["basili_no"] != sira_i:
            raise ValueError(f"{s['dosya']}: basili {s['basili_no']} != sira {sira_i}")
        t = test[kod]
        if t["bolum"] not in bolum:
            raise ValueError(f"{kod}: bolum {t['bolum']} haritada yok")
        dugum = dugum_dogrula(kod, t, konu)
        c = cevap[(kod, sira_i)]
        if (k["dosya"], k["sutun"], k["sutun_sira"]) != (
            c["dosya"],
            c["sutun"],
            c["sutun_sira"],
        ):
            raise ValueError(
                f"{s['dosya']}: kutu ile cevap anahtari ayni soruyu gostermiyor"
            )
        if k["dosya"] not in t["sayfalar"]:
            raise ValueError(
                f"{s['dosya']}: sayfa {k['dosya']} testin sayfalarinda degil"
            )
        sinav, yil = etiket_ayristir(s.get("etiket"))
        satir.append(
            {
                **s,
                "birim": kod,
                "soru": sira_i,
                "sayfa": k["dosya"],
                "sutun": k["sutun"],
                "sutun_sira": k["sutun_sira"],
                "bolum_kodu": t["bolum"],
                "bolum_adi": bolum[t["bolum"]]["ad"],
                "konu_adi": konu[dugum]["ad"],
                "ders": DERSLER[0],
                "test_no": t["test"],
                "duzey": "konu",
                "konu_kodu": dugum,
                "cevap": c["cevap"],
                "cevap_kanali": goz_hucreleri.get((kod, sira_i), "iki_okuma+glif"),
                "sikler_gorsel": bool(s.get("sikler_gorsel"))
                or all(v == GORSEL_SIK for v in s["sikler"].values()),
                "kirpim_kutusu": k["kutu"],
                "capa_kanali": CAPA_KANALI,
                "ortme": ortulen.get((kod, sira_i)),
                "mukerrer": guclu.get(s["dosya"]),
                "modern_ikiz": sorted(ikiz[s["dosya"]]) if s["dosya"] in ikiz else None,
                "hash_carpismasi": carpisan.get(s["dosya"]),
                "cevap_farki": cevap_farki.get(s["dosya"]),
                "sik_sirasi_farki": sik_sirasi.get(s["dosya"]),
                "sinav": sinav,
                "sinav_yili": yil,
            }
        )
    return satir


def goz_hucreleri(ham: dict, harita: dict) -> dict[tuple[str, int], str]:
    """Glif kanalinin bolutleyemedigi testlerin hucreleri -> goz kanali.

    ham['goz_c']['testler'] = {'20': 'BAAB...'}; testin her hucresi
    (ACL21T-T016, 1..N) 'iki_okuma+goz(5x)' kanalindan gelir. Glif uyumsuzu
    olup 5x goz teyidi tasiyan hucreler ('T042#10') ayri kanaldir.
    """
    birimler = {t["birim"]: t for t in harita["testler"]}
    out: dict[tuple[str, int], str] = {}
    for no, dizi in ham["goz_c"]["testler"].items():
        birim = f"{ONEK}-T{int(no):03d}"
        if birim not in birimler:
            raise ValueError(f"goz testi {no}: {birim} haritada yok")
        if len(dizi) != birimler[birim]["soru_sayisi"]:
            raise ValueError(f"goz testi {no}: {len(dizi)} hucre != soru sayisi")
        for i in range(1, len(dizi) + 1):
            out[(birim, i)] = "iki_okuma+goz(5x)"
    for anahtar in ham["glif"].get("goz_teyit", {}):
        t, soru = anahtar.split("#")
        birim = f"{ONEK}-{t}"
        if birim not in birimler:
            raise ValueError(f"goz teyidi {anahtar}: {birim} haritada yok")
        out[(birim, int(soru))] = "iki_okuma+glif_uyumsuz+goz_teyidi(5x)"
    return out


def sekil_ikizleri(kayitlar: list[dict[str, Any]]) -> int:
    """Ayni metin + ayni bes sik, FARKLI sekil: kimligi kirpimla ayristirir.

    soru_hash formulu (metin + sikler) ortak altyapi oldugu icin DEGISTIRILMEZ;
    yalniz bu grupta id = uuid5(hash | sekil | kirpim adi) olur (mat345tyt /
    acil25_geo_ithal ile ayni kural). Grup uyelerinden biri sekilsizse
    ayristirma YAPILMAZ; on kontrol 'ayni hash iki kez' ile durur.
    """
    grup: dict[str, list[dict[str, Any]]] = {}
    for k in kayitlar:
        grup.setdefault(k["soru_hash"], []).append(k)
    n = 0
    for h, g in grup.items():
        if len(g) < 2 or not all(k["pipeline_metadata"]["sekil_var"] for k in g):
            continue
        n += 1
        adlar = [k["pipeline_metadata"]["kaynak_gorseli"] for k in g]
        for k in g:
            ad = k["pipeline_metadata"]["kaynak_gorseli"]
            k["id"] = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{h}|sekil|{ad}"))
            k["pipeline_metadata"]["sekil_ikizi_ile"] = [a for a in adlar if a != ad]
            k["pipeline_metadata"]["bayraklar"].append("sekil_ikizi")
    return n


def _yapisal_kapilar(
    veri: dict, harita: dict, kutular: dict, anahtar: dict
) -> list[str]:
    """Bu kitabin tasiyici sayimlari -- sessizce kayan bir satir olmasin."""
    hata = []
    sorular = veri["sorular"]
    if len(sorular) != BEKLENEN_SORU:
        hata.append(f"soru sayisi {len(sorular)} != {BEKLENEN_SORU}")
    if len(harita["testler"]) != BEKLENEN_TEST:
        hata.append(f"test sayisi {len(harita['testler'])} != {BEKLENEN_TEST}")
    if len(harita["bolumler"]) != BEKLENEN_BOLUM:
        hata.append(f"bolum sayisi {len(harita['bolumler'])} != {BEKLENEN_BOLUM}")
    if len(harita["konular"]) != BEKLENEN_KONU:
        hata.append(f"konu sayisi {len(harita['konular'])} != {BEKLENEN_KONU}")
    if sum(t["soru_sayisi"] for t in harita["testler"]) != BEKLENEN_SORU:
        hata.append(f"harita soru toplami {BEKLENEN_SORU} degil")
    if len(anahtar["cevaplar"]) != BEKLENEN_SORU:
        hata.append(f"anahtar sayisi {len(anahtar['cevaplar'])} != {BEKLENEN_SORU}")
    if len(kutular["kutular"]) != BEKLENEN_SORU:
        hata.append(f"kutu sayisi {len(kutular['kutular'])} != {BEKLENEN_SORU}")
    if len({s["dosya"] for s in sorular}) != len(sorular):
        hata.append("ayni kirpim iki kez okunmus")
    # Transkripsiyon anahtardan BAGIMSIZ kanal olmali.
    sizan = [s for s in sorular if {"cevap", "correct_answer"} & set(s)]
    if sizan:
        hata.append(f"{len(sizan)} metin satirinda cevap alani var -- kanal kirlendi")
    # Cikmis soru etiketi: sayi ve bicim (sinav + yil) -- ayrismayan etiket durur.
    etiketli = [s for s in sorular if s.get("etiket")]
    if len(etiketli) != BEKLENEN_ETIKET:
        hata.append(f"etiketli soru {len(etiketli)} != {BEKLENEN_ETIKET}")
    for s in etiketli:
        if etiket_ayristir(s["etiket"]) == (None, None):
            hata.append(f"{s['dosya']}: etiket {s['etiket']!r} ayrismadi")
    return hata


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:  # noqa: PLR0912
    """Ithal oncesi ic tutarlilik -- bir tanesi bile varsa ithal baslamaz."""
    hata = []
    gorulen: set[str] = set()
    for k in kayitlar:
        sec = k["secenekler"]
        if len(sec) != 5 or any(h not in sec for h in "ABCDE"):
            hata.append(f"{k['id']}: 5 sik degil ({sorted(sec)})")
        if k["correct_answer"] not in set("ABCDE"):
            hata.append(f"{k['id']}: cevap {k['correct_answer']!r} A-E degil")
        elif not (sec.get(k["correct_answer"]) or "").strip():
            hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        if KOD_IMI not in (k["konu_kodu"] or ""):
            hata.append(f"{k['id']}: konu kodu {k['konu_kodu']!r} *{KOD_IMI}* degil")
        if k["subject_area"] not in DERSLER:
            hata.append(f"{k['id']}: ders {k['subject_area']!r} taninmiyor")
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if pm["cevap_okuma_kanali"] not in CEVAP_KANALLARI:
            hata.append(
                f"{k['id']}: taninmayan cevap okuma kanali {pm['cevap_okuma_kanali']!r}"
            )
        if not pm["kirpim_kutusu"] or not k["question_image_url"]:
            hata.append(f"{k['id']}: kirpim yok -- bu kitapta her sorunun kutusu var")
        if pm["soru_no_basili"] != pm["birim_ici_sira"] and not (
            pm["soru_no_basili"] is None and "numara_ortulu" in pm["bayraklar"]
        ):
            hata.append(f"{k['id']}: basili numara test ici siraya esit degil")
        if pm["basili_sayfa"] != pm["sayfa_dosya_no"]:
            hata.append(f"{k['id']}: basili sayfa != dosya")
        if pm["cikmis_soru"] != (k["osym_year"] is not None):
            hata.append(f"{k['id']}: cikmis bayragi ile osym_year tutarsiz")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur."""
    kokler = {
        r[0]
        for r in conn.execute(
            "SELECT code FROM topic_hierarchy WHERE code = ANY(%s) AND parent_id IS NULL",
            (list(KOK_KODLARI),),
        ).fetchall()
    }
    if kokler != set(KOK_KODLARI):
        return f"kok konu eksik: {sorted(set(KOK_KODLARI) - kokler)}"
    kodlar = sorted({k["konu_kodu"] for k in kayitlar})
    konular: dict[str, str] = dict(
        conn.execute(
            "SELECT code, id FROM topic_hierarchy WHERE code = ANY(%s)", (kodlar,)
        ).fetchall()
    )
    eksik = set(kodlar) - set(konular)
    if eksik:
        return (
            f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)[:5]}. "
            "0071_acl20t_konu_agaci kosmadi mi? Kok dugume dusurup "
            "sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    print("konu dagilimi:")
    for kod, adet in sorted(sayac.items()):
        print(f"  {adet:5d}  {kod}")
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print(
        "cevap kanali      :",
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)),
    )
    print("cikmis (yil dolu) :", sum(1 for k in kayitlar if k["osym_year"]))
    print("ders dagilimi     :", dict(Counter(k["subject_area"] for k in kayitlar)))
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}")


def _hazirla(yollar: dict[str, Path]) -> list[dict[str, Any]] | None:
    """Dosyalari okur, kapilardan gecirir, kayitlari uretir (None = DURDU)."""
    oku = {ad: json.loads(p.read_text(encoding="utf-8")) for ad, p in yollar.items()}
    yapisal = _yapisal_kapilar(
        oku["veri"], oku["harita"], oku["kutular"], oku["anahtar"]
    )
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun buldu; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(
        f"yapisal kapi: {BEKLENEN_SORU} soru + {BEKLENEN_TEST} test + {BEKLENEN_BOLUM} bolum + {BEKLENEN_KONU} konu + "
        f"{BEKLENEN_SORU} anahtar + {BEKLENEN_SORU} kutu + {BEKLENEN_ETIKET} etiket + "
        "cevap sizintisi yok -- TEMIZ"
    )
    satirlar = satirlari_bagla(
        oku["veri"],
        oku["harita"],
        oku["kutular"],
        oku["anahtar"],
        ortme=oku["ortme"],
        mukerrer=oku["mukerrer"],
        goz_hucreleri=goz_hucreleri(oku["ham"], oku["harita"]),
    )
    print(f"veri setinde {len(satirlar)} soru")
    kayitlar = [kayit_uret(r) for r in satirlar]
    ikiz = sekil_ikizleri(kayitlar)
    if ikiz:
        print(f"sekil ikizi: {ikiz} grup (ayni metin + ayni sikler, farkli sekil)")
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return None
    print(
        "on kontrol: 5 sik + A-E cevap + dolu anahtar sikki + dolu metin "
        f"+ *{KOD_IMI}* konu kodu + ders + tablo kaynagi + kutu/gorsel + basili no "
        "+ basili sayfa + cikmis/yil + benzersiz hash -- TEMIZ"
    )
    return kayitlar


def ithal(yollar: dict[str, Path], dsn: str, yaz: bool) -> int:
    kayitlar = _hazirla(yollar)
    if kayitlar is None:
        return 2
    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2
        yeni, _bizim, yabanci = ayristir(conn, kayitlar, KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)
        _ozet(yeni or kayitlar)
        if not yaz:
            print("(--yaz verilmedi; hicbir sey yazilmadi)")
            return 0
        with conn.transaction():
            for k in yeni:
                s = k["secenekler"]
                gen, boy = k["pipeline_metadata"]["gorsel_boyu"]
                conn.execute(_QB, k)
                conn.execute(
                    _QC,
                    {
                        "id": k["id"],
                        "question_text": k["question_text"],
                        "a": s["A"],
                        "b": s["B"],
                        "c": s["C"],
                        "d": s["D"],
                        "e": s["E"],
                        "correct_answer": k["correct_answer"],
                        "question_image_url": k["question_image_url"],
                        "image_width": gen,
                        "image_height": boy,
                    },
                )
                conn.execute(
                    _QM,
                    {
                        **k,
                        "grade_level": SINIF_DUZEYI,
                        "source_book": KAYNAK_ADI,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})
        satir = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s AND m.pipeline_metadata->>'ithal_araci' = %s""",
            (KAYNAK_ADI, ITHAL_ARACI),
        ).fetchone()
        if satir is None:  # pragma: no cover  # count(*) hep satir dondurur
            raise RuntimeError("dogrulama sorgusu satir dondurmedi")
        n, aktif, kapida = satir
        print(f"YAZILDI: {len(yeni)} yeni satir")
        print(
            f"DB'de bu ithalin satirlari: toplam {n}, is_active {aktif}, kapidan gecen {kapida}"
        )
        if aktif or kapida:
            print("HATA: pasif ithal sozlesmesi bozuldu")
            return 3
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument("--harita", default=VARSAYILAN_HARITA)
    p.add_argument("--kutular", default=VARSAYILAN_KUTULAR)
    p.add_argument("--anahtar", default=VARSAYILAN_ANAHTAR)
    p.add_argument("--ortme", default=VARSAYILAN_ORTME)
    p.add_argument("--mukerrer", default=VARSAYILAN_MUKERRER)
    p.add_argument("--ham", default=VARSAYILAN_HAM)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    p.add_argument(
        "--kuru", action="store_true", help="DB'ye hic baglanma, yalniz kapilari kos"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    yollar = {
        "veri": Path(args.veri),
        "harita": Path(args.harita),
        "kutular": Path(args.kutular),
        "anahtar": Path(args.anahtar),
        "ortme": Path(args.ortme),
        "mukerrer": Path(args.mukerrer),
        "ham": Path(args.ham),
    }
    if args.kuru:
        kayitlar = _hazirla(yollar)
        if kayitlar is None:
            return 2
        _ozet(kayitlar)
        print("(--kuru: DB'ye baglanilmadi)")
        return 0
    return ithal(yollar, args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
