"""PASIF ithal -- profil gudumlu (acil2021tyt_ithal deseni).

BIRIM = TEST, KONU = ICINDEKILER KONUSU
---------------------------------------
Her test tek bir konu araligina duser (konu haritasi); sorular konu
dugumune baglanir (kitabin kendi agaci, <KOD_ONEKI>-*; agac migration'i).

CEVAP KAYNAGI: TESTIN BASILI CEVAP ANAHTARI
------------------------------------------
Iki bagimsiz gorsel okuma (A == B), piksel glif LOO ucuncu kanal (uyumsuz
hucre 5x goz teyidi), glifin bolutleyemedigi testler 5x gozle; hucre sayisi
== okuyucu simgesi + kirmizi numara capasi. Hicbir soru cozulmedi.

METIN
-----
Ayri okuyucularla kirpimdan; on kayitli TAM ikinci okuma, farklar hakemle
gozle (metin_iki_okuma). Okuyucu diskinin altinda kalan yazi `[??]`.

BAYRAKLAR (silinmez, isaretlenir)
---------------------------------
okuyucu_diski_ortme, okunamaz_isaret, numara_basilmamis, mukerrer_aday,
modern_kitap_ikizi, db_hash_carpismasi, diger_kaynak_cevap_farki,
diger_kaynak_sik_sirasi_farkli, sik_okunamadi, kaynak_kusuru. DB ile ayni
soru_hash -> ayni id; `ayristir` bunlari YABANCI sayar, yazilmaz.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.ithal --profil K [--kuru | --yaz]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from collections import Counter
from types import ModuleType
from typing import Any

import psycopg

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz
from scripts.kitap.kitap_hat import ortak
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
ITHAL_ARACI = "scripts/kitap/kitap_hat/ithal.py"
CEVAP_KAYNAGI = "testin_basili_cevap_anahtari"
CEVAP_KANALLARI = (
    "iki_okuma+glif",
    "iki_okuma+glif_uyumsuz+goz_teyidi(5x)",
    "iki_okuma+goz(5x)",
)
CAPA_KANALI = "okuyucu_simgesi+kirmizi_basili_numara"
SIK_OKUNAMADI = "[okunamad\u0131]"
GORSEL_SIK = "(g\u00f6rsel \u015f\u0131k)"
OKUNAMAZ = "[??]"
_ETIKET = re.compile(r"(TYT|AYT|YGS|LYS|MS\u00dc|MSU)|((?:19|20)\d\d)")


def etiket_ayristir(etiket: str | None) -> tuple[str | None, int | None]:
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


def telif_notu(p: ModuleType) -> str:
    return (
        f"{p.YAYINEVI}. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
        "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
    )


def anahtar_dogrulamasi(p: ModuleType, ham: dict) -> str:
    n = sum(len(t["hucreler"]) for t in ham["okuma_a"]["testler"])
    g = ham["glif"]
    return (
        f"basili_anahtar_iki_okuma_{n}_{n}_hucre_ayni__piksel_glif_loo_{g['uyum']}_{g['hucre']}"
        f"_uyumsuz_goz__glif_disi_{len(g['kapsam_disi_test'])}_test_goz_5x__"
        f"hucre_sayisi_esittir_numara_capasi_{n}"
    )


def uretim_notu(p: ModuleType, ham: dict) -> str:
    n = sum(len(t["hucreler"]) for t in ham["okuma_a"]["testler"])
    g = ham["glif"]
    return (
        "FERNUS okuyucu ekran goruntusunden okuma hatti (kitap_hat). Cevaplar testin basili "
        f"cevap anahtarindan iki bagimsiz gorsel okumayla alindi ({n}/{n} hucre ayni; piksel glif "
        f"LOO ucuncu kanal {g['uyum']}/{g['hucre']}, {len(g.get('goz_teyit', {}))} uyumsuz 5x goz "
        f"teyidi; bolutlenemeyen {len(g['kapsam_disi_test'])} test 5x goz). Sorular cozulmedi. "
        "Kirpim kutulari okuyucu simgesi + kirmizi basili numara capasindan. Transkripsiyon ayri "
        "okuyucularla kirpimdan; on kayitli TAM ikinci okuma; anahtar gosterilmedi. Detay: "
        f"veriseti/zkitap/cikti/{p.YONTEM_BELGESI}"
    )


_KAYIT_BAYRAKLARI = (
    ("sikler_gorsel", "sikler_gorsel"),
    ("kaynak_kusuru", "kaynak_kusuru"),
    ("ortme", "okuyucu_diski_ortme"),
    ("basili_no", "numara_basilmamis"),
    ("numara_baski_hatasi", "numara_baski_hatasi"),
    ("modern_ikiz", "modern_kitap_ikizi"),
    ("mukerrer", "mukerrer_aday"),
    ("hash_carpismasi", "db_hash_carpismasi"),
    ("cevap_farki", "diger_kaynak_cevap_farki"),
    ("sik_sirasi_farki", "diger_kaynak_sik_sirasi_farkli"),
    ("sinav_yili", "cikmis_soru"),
)


def _bayraklar(
    r: dict[str, Any], sec: dict[str, str], oncul_yok: tuple[str, ...] = ()
) -> list[str]:
    b: list[str] = sik_bayraklari(sec)
    if r["dosya"] in oncul_yok:
        # Soru, kirpimi DISINDA kalan numarasiz ortak grafige / sekle dayanir
        # (profilde ORTAK_ONCUL_YOK, gozle): ogrenciye gosterilemez.
        b.append("ortak_oncul_kirpimda_yok")
    for alan, bayrak in _KAYIT_BAYRAKLARI:
        # basili_no: bayrak numara YOKSA (None); digerleri alan doluysa.
        var = r.get(alan) is None if alan == "basili_no" else bool(r.get(alan))
        if var:
            b.append(bayrak)
    if OKUNAMAZ in r["govde"] + "".join(sec.values()):
        b.append("okunamaz_isaret")
    if any(v == SIK_OKUNAMADI for v in sec.values()):
        b.append("sik_okunamadi")
    return b


def kayit_uret(p: ModuleType, r: dict[str, Any], ham: dict) -> dict[str, Any]:
    sec = {h: r["sikler"][h] for h in "ABCDE"}
    h = soru_hash(r["govde"], sec)
    n, u, ort = kelime_istatistik(r["govde"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["govde"], sec)
    kutu = r["kirpim_kutusu"]
    basili_sayfa = int(r["sayfa"]) + int(getattr(p, "SAYFA_OFSETI", 0))
    cikmis = r.get("sinav_yili") is not None
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "subject_area": p.ALAN,
        "exam_type": p.SINAV,
        "question_text": r["govde"],
        "secenekler": sec,
        "correct_answer": r["cevap"],
        "question_image_url": f"/static/crops/{p.KOD}/{r['dosya']}.png",
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
            "kaynak": p.KOD.lower(),
            "profil": p.KOD,
            "konu_kodu": r["konu_kodu"],
            "konu_eslesme_duzeyi": "konu",
            "konu_kaynagi": "icindekiler_ve_test_ust_bandi",
            "ders": p.ALAN,
            "test_no": r["test_no"],
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": basili_sayfa,
            "sutun": r["sutun"],
            "sutun_sira": r["sutun_sira"],
            "soru_no_basili": r["basili_no"],
            "soru_no_kaynagi": "basili"
            if r["basili_no"] is not None
            else "test_ici_sira",
            "birim_kodu": r["birim"],
            "birim_ici_sira": r["soru"],
            "bolum_kodu": r["bolum_kodu"],
            "bolum_adi": r["bolum_adi"],
            "konu_adi": r["konu_adi"],
            "test_bandi": r["bant"],
            "kaynak_gorseli": f"{r['dosya']}.png",
            "bayraklar": _bayraklar(r, sec, tuple(getattr(p, "ORTAK_ONCUL_YOK", ()))),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "cevap_okuma_kanali": r["cevap_kanali"],
            "anahtar_dogrulamasi": anahtar_dogrulamasi(p, ham),
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
            "gorsel_boyu": [kutu[2] - kutu[0], kutu[3] - kutu[1]],
            "kirpim_capa_kanali": CAPA_KANALI,
            "kirpim_koordinat_sistemi": "sayfa_karti_{}_{}_{}_{}_numara_capasindan".format(
                *p.KART
            ),
            "gorsel_kaynagi": "tam_soru_kirpimi_okuyucu_diski_beyazlatilmis",
            "metin_kaynagi": f"soru_kirpimi_gorsel_okuma_{r['okuma']}_tam_ikinci_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": telif_notu(p),
            "uretim": uretim_notu(p, ham),
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, %(exam_type)s, %(subject_area)s, %(grade_level)s,
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


def goz_hucreleri(p: ModuleType, ham: dict, harita: dict) -> dict[tuple[str, int], str]:
    """Glif kanalinin bolutleyemedigi testlerin hucreleri + goz teyitli uyumsuzlar."""
    birimler = {t["birim"]: t for t in harita["testler"]}
    out: dict[tuple[str, int], str] = {}
    for no, dizi in ham["goz_c"]["testler"].items():
        birim = ortak.birim_kodu(p, int(no))
        if birim not in birimler:
            raise ValueError(f"goz testi {no}: {birim} haritada yok")
        if len(dizi) != birimler[birim]["soru_sayisi"]:
            raise ValueError(f"goz testi {no}: {len(dizi)} hucre != soru sayisi")
        for i in range(1, len(dizi) + 1):
            out[(birim, i)] = "iki_okuma+goz(5x)"
    for anahtar in ham["glif"].get("goz_teyit", {}):
        t, soru = anahtar.split("#")
        birim = f"{p.KOD}-{t}"
        if birim not in birimler:
            raise ValueError(f"goz teyidi {anahtar}: {birim} haritada yok")
        out[(birim, int(soru))] = "iki_okuma+glif_uyumsuz+goz_teyidi(5x)"
    return out


def _mukerrer_esleri(
    p: ModuleType, mukerrer: dict[str, Any]
) -> tuple[dict, dict, dict, dict, dict]:
    """GUCLU aday, hash carpismasi, modern kitap ikizi, cevap / sik sirasi farki."""
    guclu = {
        a["dosya"]: {
            k: a[k] for k in ("db_id", "db_kaynak", "govde_3gram", "ayni_sik_sayisi")
        }
        for a in mukerrer["adaylar"]
        if a["guclu"]
    }
    carpisan = {c["dosya"]: c["db_id"] for c in mukerrer["db_tam_hash_carpismasi"]}
    ikiz: dict[str, list[str]] = {}
    modern = getattr(p, "MODERN_IKIZ_KAYNAK", None)
    for a in mukerrer["adaylar"]:
        if modern and a["guclu"] and a["db_kaynak"] == modern:
            ikiz.setdefault(a["dosya"], []).append(a["db_id"])
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
    return guclu, carpisan, ikiz, cevap_farki, sik_sirasi


def satirlari_bagla(p: ModuleType, oku: dict[str, Any]) -> list[dict[str, Any]]:
    veri, harita, kutular, anahtar = (
        oku["veri"],
        oku["harita"],
        oku["kutular"],
        oku["anahtar"],
    )
    mukerrer, ortme = oku["mukerrer"], oku["ortme"]
    test = {t["birim"]: t for t in harita["testler"]}
    bolum = {b["kod"]: b for b in harita["bolumler"]}
    konu = {k["kod"]: k for k in harita["konular"]}
    kutu = {(k["birim"], k["soru"]): k for k in kutular["kutular"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    ortulen: dict[tuple[str, int], list] = {}
    for o in ortme["ortme"]:
        ortulen.setdefault((o["birim"], o["soru"]), []).append(o["simge"])
    guclu, carpisan, ikiz, cevap_farki, sik_sirasi = _mukerrer_esleri(p, mukerrer)
    goz = goz_hucreleri(p, oku["ham"], harita)
    numarasiz = {
        ortak.dosya_adi(ortak.birim_kodu(p, t["test"]), i)
        for t in oku["tarama"]["testler"]
        for i, c in enumerate(t["capalar"], 1)
        if c.get("numarasiz")
    }
    satir = []
    hatali = getattr(p, "BASKI_NUMARA_HATASI", {})
    for s0 in veri["sorular"]:
        # Kitapta yanlis numara basilmis (gozle, profilde listeli): sira cevap
        # seridinden, basili numara oldugu gibi saklanir.
        baski_hatasi = (
            hatali.get(s0["dosya"]) is not None
            and s0["basili_no"] == hatali[s0["dosya"]]
        )
        s = {**s0, "numara_baski_hatasi": True} if baski_hatasi else s0
        kod, sira = s["dosya"].rsplit("_", 1)
        sira_i = int(sira)
        k = kutu[(kod, sira_i)]
        if (
            not baski_hatasi
            and s["basili_no"] != sira_i
            and not (s["basili_no"] is None and s["dosya"] in numarasiz)
        ):
            raise ValueError(f"{s['dosya']}: basili {s['basili_no']} != sira {sira_i}")
        t = test[kod]
        if t["bolum"] not in bolum:
            raise ValueError(f"{kod}: bolum {t['bolum']} haritada yok")
        dugum = str(t["konu"])
        if dugum not in konu or konu[dugum]["bolum"] != t["bolum"]:
            raise ValueError(f"{kod}: konu {dugum} bolumu {t['bolum']} degil")
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
                "bant": t["bant"],
                "test_no": t["test"],
                "konu_kodu": dugum,
                "cevap": c["cevap"],
                "cevap_kanali": goz.get((kod, sira_i), "iki_okuma+glif"),
                "sikler_gorsel": bool(s.get("sikler_gorsel"))
                or all(v == GORSEL_SIK for v in s["sikler"].values()),
                "kirpim_kutusu": k["kutu"],
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


def sekil_ikizleri(kayitlar: list[dict[str, Any]]) -> int:
    """Ayni metin + ayni bes sik, FARKLI sekil: id = uuid5(hash | sekil | kirpim adi)."""
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


def yapisal_kapilar(p: ModuleType, oku: dict[str, Any]) -> list[str]:
    veri, harita, kutular, anahtar = (
        oku["veri"],
        oku["harita"],
        oku["kutular"],
        oku["anahtar"],
    )
    hata = []
    n = p.BEKLENEN_SORU
    sorular = veri["sorular"]
    if len(sorular) != n:
        hata.append(f"soru sayisi {len(sorular)} != {n}")
    if len(harita["testler"]) != p.BEKLENEN_TEST:
        hata.append(f"test sayisi {len(harita['testler'])} != {p.BEKLENEN_TEST}")
    if len(harita["bolumler"]) != len(p.BOLUMLER):
        hata.append("bolum sayisi profille ayni degil")
    if len(harita["konular"]) != len(p.ICINDEKILER):
        hata.append("konu sayisi profille ayni degil")
    if sum(t["soru_sayisi"] for t in harita["testler"]) != n:
        hata.append(f"harita soru toplami {n} degil")
    if len(anahtar["cevaplar"]) != n:
        hata.append(f"anahtar sayisi {len(anahtar['cevaplar'])} != {n}")
    if len(kutular["kutular"]) != n:
        hata.append(f"kutu sayisi {len(kutular['kutular'])} != {n}")
    if len({s["dosya"] for s in sorular}) != len(sorular):
        hata.append("ayni kirpim iki kez okunmus")
    sizan = [s for s in sorular if {"cevap", "correct_answer"} & set(s)]
    if sizan:
        hata.append(f"{len(sizan)} metin satirinda cevap alani var -- kanal kirlendi")
    etiketli = [s for s in sorular if s.get("etiket")]
    if len(etiketli) != p.BEKLENEN_ETIKET:
        hata.append(f"etiketli soru {len(etiketli)} != {p.BEKLENEN_ETIKET}")
    for s in etiketli:
        if etiket_ayristir(s["etiket"]) == (None, None):
            hata.append(f"{s['dosya']}: etiket {s['etiket']!r} ayrismadi")
    return hata


def on_kontrol(p: ModuleType, kayitlar: list[dict[str, Any]]) -> list[str]:
    hata = []
    gorulen: set[str] = set()
    kod_imi = f"{p.KOD_ONEKI}-"
    ofset = int(getattr(p, "SAYFA_OFSETI", 0))
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
        if not (k["konu_kodu"] or "").startswith(kod_imi):
            hata.append(f"{k['id']}: konu kodu {k['konu_kodu']!r} {kod_imi}* degil")
        pm = k["pipeline_metadata"]
        if pm["cevap_okuma_kanali"] not in CEVAP_KANALLARI:
            hata.append(
                f"{k['id']}: taninmayan cevap okuma kanali {pm['cevap_okuma_kanali']!r}"
            )
        if not pm["kirpim_kutusu"] or not k["question_image_url"]:
            hata.append(f"{k['id']}: kirpim yok")
        if (
            pm["soru_no_basili"] != pm["birim_ici_sira"]
            and not (
                pm["soru_no_basili"] is None and "numara_basilmamis" in pm["bayraklar"]
            )
            and "numara_baski_hatasi" not in pm["bayraklar"]
        ):
            hata.append(f"{k['id']}: basili numara test ici siraya esit degil")
        if pm["basili_sayfa"] != pm["sayfa_dosya_no"] + ofset:
            hata.append(f"{k['id']}: basili sayfa != dosya + ofset {ofset}")
        if pm["cikmis_soru"] != (k["osym_year"] is not None):
            hata.append(f"{k['id']}: cikmis bayragi ile osym_year tutarsiz")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def hazirla(p: ModuleType) -> list[dict[str, Any]] | None:
    oku = {
        "veri": ortak.oku(p, "metin"),
        "harita": ortak.oku(p, "konu_haritasi"),
        "kutular": ortak.oku(p, "kirpim_kutulari"),
        "anahtar": ortak.oku(p, "cevap_anahtari"),
        "ortme": ortak.oku(p, "ortme_olcumu"),
        "mukerrer": ortak.oku(p, "mukerrer_adaylari"),
        "ham": ortak.oku(p, "ham_okumalar"),
        "tarama": ortak.oku(p, "capa_taramasi"),
    }
    yapisal = yapisal_kapilar(p, oku)
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(f"yapisal kapi: {p.BEKLENEN_SORU} soru / {p.BEKLENEN_TEST} test -- TEMIZ")
    satirlar = satirlari_bagla(p, oku)
    kayitlar = [kayit_uret(p, r, oku["ham"]) for r in satirlar]
    ikiz = sekil_ikizleri(kayitlar)
    if ikiz:
        print(f"sekil ikizi: {ikiz} grup")
    hata = on_kontrol(p, kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return None
    print("on kontrol TEMIZ")
    return kayitlar


def _konu_id_ata(
    p: ModuleType, conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    kok = conn.execute(
        "SELECT 1 FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (p.KOK_KOD,),
    ).fetchone()
    if not kok:
        return f"kok konu {p.KOK_KOD} yok"
    kodlar = sorted({k["konu_kodu"] for k in kayitlar})
    konular: dict[str, str] = dict(
        conn.execute(
            "SELECT code, id FROM topic_hierarchy WHERE code = ANY(%s)", (kodlar,)
        ).fetchall()
    )
    eksik = set(kodlar) - set(konular)
    if eksik:
        return f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)[:5]} (agac migration'i kosmadi mi?)"
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def ozet(kayitlar: list[dict[str, Any]]) -> None:
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    print("konu dagilimi:", dict(sorted(sayac.items())))
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar:", dict(bayrak) or "(yok)")
    print(
        "cevap kanali:",
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)),
    )


def ithal(p: ModuleType, dsn: str, yaz: bool) -> int:
    if KAYNAK_KAYITLARI.get(p.KAYNAK_ADI, {}).get("onek") != p.KOD:
        print(f"DURDU: kaynak_sozlesmesi'nde {p.KAYNAK_ADI!r} -> {p.KOD} kaydi yok")
        return 2
    kayitlar = hazirla(p)
    if kayitlar is None:
        return 2
    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(p, conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2
        yeni, _bizim, yabanci = ayristir(conn, kayitlar, p.KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)
        ozet(yeni or kayitlar)
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
                        "grade_level": p.SINIF,
                        "source_book": p.KAYNAK_ADI,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})
        satir = conn.execute(
            """SELECT count(*), count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s AND m.pipeline_metadata->>'ithal_araci' = %s""",
            (p.KAYNAK_ADI, ITHAL_ARACI),
        ).fetchone()
        if satir is None:  # pragma: no cover
            raise RuntimeError("dogrulama sorgusu satir dondurmedi")
        n, aktif, kapida = satir
        print(
            f"YAZILDI: {len(yeni)} yeni satir; DB'de bu ithal: {n}, aktif {aktif}, kapidan {kapida}"
        )
        if aktif or kapida:
            print("HATA: pasif ithal sozlesmesi bozuldu")
            return 3
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--profil", required=True)
    ap.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    ap.add_argument("--yaz", action="store_true")
    ap.add_argument("--kuru", action="store_true")
    a = ap.parse_args()
    getattr(sys.stdout, "reconfigure", lambda **_: None)(encoding="utf-8")
    p = ortak.profil(a.profil)
    if a.kuru:
        k = hazirla(p)
        if k is None:
            return 2
        ozet(k)
        return 0
    return ithal(p, a.dsn, a.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
