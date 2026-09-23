"""ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri; sayfa karti (593, 46) -
(1327, 1014) = 734x968 (Faz 0'da 11 ornekte 0 px sapma). 400 PNG, 392 soru
sayfasi (dosya 7-398), basili sayfa = dosya - 4 (dosya 3-4-5 ayni kapak).

BIRIM = SERIT NUMARASININ 1'DEN BASLADIGI DIZI
----------------------------------------------
Her soru sayfasinin altinda sutun basina yarim cevap seridi var; numara
kitap boyunca 429 kez 1'e donuyor. Her donus bir birim: 318'i 'Konu
Ogrenme' sayfalarindaki sari alt baslik kutusuyla, 111'i buyuk basliktaki
bir 'Konu Uygulama' testiyle basliyor (iki kanal birebir, bkz. birim
haritasi). 1948 soru.

CEVAP KAYNAGI: SAYFA ALTI CEVAP SERIDI
--------------------------------------
Anahtar kitabin KENDI basili seritlerinden uc bagimsiz gorsel okumayla
okundu; hicbir soru cozulmedi. 1915 girdi uc okumada ayni; 31 B/D girdisi
piksel olcumu (orta cubuk) + goz ile; 2 girdi goz ile.

KONU AGACI
----------
Icindekiler sayfasi yakalamada yok; agac sayfa basliklarindan kuruldu
(0041): GEO kokunun altinda GEO-ACL25 onekiyle 33 konu + 315 alt konu.
Konu Ogrenme birimleri ALT KONU dugumune, test birimleri KONU dugumune
baglanir.

ORTME: ITHAL EDILIR, ISARETLENIR
--------------------------------
Sahip karari (yeniden yakalama yok): okuyucu diski beyazlatildi; diskin
kenar halkasinda kitap murekkebi olculen sorular `okuyucu_diski_ortme`
bayragi tasir (acil_2025_geometri_ortme_olcumu.json). Okuyucunun kaynak
kusuru notlari da `kaynak_kusuru` bayragiyla gorunur kalir.

BILINEN BORC
------------
  * TAM ikinci transkripsiyon yapilmadi.
  * Cozumler kitapta soru sayfasinda YOK; `explanation` bos.
  * Sinav turu soru duzeyinde OLCULMEDI (kitap TYT-AYT karisik); kardes
    geometri kitaplariyla tutarli 'AYT' yazilir, `sinav_turu_kaynagi` ile
    isaretlenir.

Detay: veriseti/zkitap/cikti/GEO_ACIL_2025_FAZ1.md
"""

from __future__ import annotations

import argparse
import json
import os
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
VARSAYILAN_VERI = f"{CIKTI}/acil_2025_geometri_metin.json"
VARSAYILAN_HARITA = f"{CIKTI}/acil_2025_geometri_konu_haritasi.json"
VARSAYILAN_BIRIM = f"{CIKTI}/acil_2025_geometri_birim_haritasi.json"
VARSAYILAN_KUTULAR = f"{CIKTI}/acil_2025_geometri_kirpim_kutulari.json"
VARSAYILAN_ANAHTAR = f"{CIKTI}/acil_2025_geometri_cevap_anahtari.json"
VARSAYILAN_ORTME = f"{CIKTI}/acil_2025_geometri_ortme_olcumu.json"
KAYNAK_ADI = "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ACL25"
SINIF_DUZEYI = 12
SAYFA_OFSETI = 4
ITHAL_ARACI = "scripts/kitap/acil25_geo_ithal.py"
CROP_ONEK = "ACILGEO_2025"
TELIF_NOTU = (
    "Acil Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
    "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar KITABIN sayfa "
    "alti cevap seridinden uc bagimsiz gorsel okumayla alindi (1915 uc okuma "
    "ayni, 31 B/D piksel olcumu + goz, 2 goz). Sorular cozulmedi. Kirpim "
    "kutulari basili soru numarasindan turetildi. Transkripsiyon 32 grupta "
    "ayri okuyucularla kirpimdan yapildi; anahtar gosterilmedi. Detay: "
    "veriseti/zkitap/cikti/GEO_ACIL_2025_FAZ1.md"
)
ANAHTAR_DOGRULAMASI = (
    "sayfa_alti_serit_uc_okuma_1915_bd_piksel_31_goz_2__"
    "sutun_basina_serit_girdisi_esittir_numara_capasi_784_784__"
    "serit_numarasi_1_ya_da_onceki_arti_1_kopma_yok__"
    "basili_numara_esittir_birim_ici_sira_1948_1948"
)
CEVAP_KAYNAGI = "sayfa_alti_cevap_seridi"
CEVAP_KANALLARI = ("uc_okuma", "iki_okuma+piksel_BD", "goz_zoom")
KIRPIM_SISTEMI = "sayfa_karti_593_46_1327_1014_sutun_sinirlari_tek_cift"
BEKLENEN_SORU = 1948
BEKLENEN_BIRIM = 429
# Okuyucu diski altinda kalip hic okunamayan sik (acil25_geo_metin_harness.py
# ile ayni isaret): "[okunamadi]" -- noktasiz i.
SIK_OKUNAMADI = "[okunamad\u0131]"


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("sikler_gorsel"):
        b.append("sikler_gorsel")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_kusuru")
    if r.get("ortme"):
        b.append("okuyucu_diski_ortme")
    if any(v == SIK_OKUNAMADI for v in sec.values()):
        b.append("sik_okunamadi")
    if not (sec.get(r["cevap"]) or "").strip() or sec.get(r["cevap"]) == SIK_OKUNAMADI:
        b.append("anahtar_sikki_okunamadi")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r["sikler"][h] for h in "ABCDE"}
    h = soru_hash(r["govde"], sec)
    n, u, ort = kelime_istatistik(r["govde"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["govde"], sec)
    kutu = r["kirpim_kutusu"]
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["govde"],
        "secenekler": sec,
        "correct_answer": r["cevap"],
        # GORSEL ADI: kirpim script'inin urettigi ad (BIRIM_SS.png).
        "question_image_url": f"/static/crops/{CROP_ONEK}/{r['dosya']}.png",
        "explanation": None,
        "source_page": int(r["sayfa"]) - SAYFA_OFSETI,
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["govde"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["govde"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": None,
        "osym_format_compliant": False,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "ana_konu_kodu": r["ana_konu"],
            "konu_eslesme_duzeyi": "alt_konu" if r["alt_konu"] else "konu",
            "konu_kaynagi": "birim_haritasi_sayfa_basligi_ve_sari_kutu",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": int(r["sayfa"]) - SAYFA_OFSETI,
            "sutun": r["sutun"],
            "serit_sira": r["serit_sira"],
            "soru_no_basili": r["basili_no"],
            "birim_kodu": r["birim"],
            "birim_ici_sira": r["soru"],
            "birim_turu": r["birim_turu"],
            "birim_adi": r["birim_adi"],
            "kaynak_gorseli": f"{r['dosya']}.png",
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "cevap_okuma_kanali": r["cevap_kanali"],
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "sekil_var": bool(r.get("sekil_var")),
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kaynak_kusuru": r.get("kaynak_kusuru") or None,
            "okuyucu_diski_ortme": r.get("ortme"),
            "kirpim_kutusu": kutu,
            "kirpim_koordinat_sistemi": KIRPIM_SISTEMI,
            "gorsel_kaynagi": "tam_soru_kirpimi",
            "sinav_turu_kaynagi": "olculmedi_kitap_TYT-AYT_karisik",
            "metin_kaynagi": "soru_kirpimi_gorsel_okuma_32_grup",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_734x968",
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'AYT', 'GEOMETRI', %(grade_level)s,
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


def satirlari_bagla(
    veri: dict, birim: dict, harita: dict, kutular: dict, anahtar: dict, *, ortme: dict
) -> list[dict[str, Any]]:
    """Metin, birim, konu, kirpim kutusu, cevap anahtari ve ortme olcumunu birlestirir.

    Birlestirme anahtari (birim kodu, birim ici sira). Metin satiri bu cifti
    dosya adindan tasir; BASILI numaranin birim ici siraya esitligi burada
    AYRICA dogrulanir ki kutu-capa hatasi sessizce kaymasin.
    """
    bir = {b["kod"]: b for b in birim["birimler"]}
    konu = {k["kod"] for k in harita["konular"]}
    alt = {a["kod"]: a["ust"] for a in harita["alt_konular"]}
    kutu = {(k["birim"], k["soru"]): k for k in kutular["kutular"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    ortulen: dict[tuple[str, int], list] = {}
    for o in ortme["ortme"]:
        ortulen.setdefault((o["birim"], o["soru"]), []).append(o["simge"])
    satir = []
    for s in veri["sorular"]:
        kod, sira = s["dosya"].rsplit("_", 1)
        sira_i = int(sira)
        if s["basili_no"] != sira_i:
            raise ValueError(f"{s['dosya']}: basili {s['basili_no']} != sira {sira_i}")
        b = bir[kod]
        if b["konu"] not in konu:
            raise ValueError(f"{kod}: konu {b['konu']} haritada yok")
        if b["alt_konu"] and alt.get(b["alt_konu"]) != b["konu"]:
            raise ValueError(
                f"{kod}: alt konu {b['alt_konu']} {b['konu']} altinda degil"
            )
        q = b["sorular"][sira_i - 1]
        k = kutu[(kod, sira_i)]
        if (k["dosya"], k["sutun"], k["serit_sira"]) != (
            q["dosya"],
            q["sutun"],
            q["serit_sira"],
        ):
            raise ValueError(
                f"{s['dosya']}: kutu ile birim haritasi ayni soruyu gostermiyor"
            )
        c = cevap[(kod, sira_i)]
        satir.append(
            {
                **s,
                "birim": kod,
                "soru": sira_i,
                "sayfa": q["dosya"],
                "sutun": q["sutun"],
                "serit_sira": q["serit_sira"],
                "birim_turu": b["tur"],
                "birim_adi": b["ad"],
                "ana_konu": b["konu"],
                "alt_konu": b["alt_konu"],
                "konu_kodu": b["alt_konu"] or b["konu"],
                "cevap": c["cevap"],
                "cevap_kanali": c["kaynak"],
                "sikler_gorsel": all("rsel" in str(v) for v in s["sikler"].values()),
                "kirpim_kutusu": k["kutu"],
                "ortme": ortulen.get((kod, sira_i)),
            }
        )
    return satir


def sekil_ikizleri(kayitlar: list[dict[str, Any]]) -> int:
    """Ayni metin + ayni bes sik, FARKLI sekil: kimligi kirpimla ayristirir.

    Olculdu: d8'de sol #2 ve sag #5 ayni govdeyi ve ayni siklari tasiyor ama
    sekilleri farkli ve kitabin anahtari farkli (C / D). soru_hash formulu
    (metin + sikler) ortak altyapi oldugu icin DEGISTIRILMEZ; bunun yerine
    yalniz bu grupta id = uuid5(hash | sekil | kirpim adi) olur ve iki kayit
    birbirini `sekil_ikizi_ile` alaninda gosterir. Grup uyelerinden biri
    sekilsizse ayristirma YAPILMAZ: o gercek bir cift okumadir ve on kontrol
    'ayni hash iki kez' ile durur.

    Bilinen sinir: uq_qb_soru_hash_active (is_active iken tekil) yuzunden
    ikizlerden yalniz biri ayni anda aktif olabilir; ithal zaten pasif.
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
    veri: dict, birim: dict, kutular: dict, anahtar: dict
) -> list[str]:
    """Bu kitabin tasiyici sayimlari -- sessizce kayan bir satir olmasin."""
    hata = []
    sorular = veri["sorular"]
    if len(sorular) != BEKLENEN_SORU:
        hata.append(f"soru sayisi {len(sorular)} != {BEKLENEN_SORU}")
    if len(birim["birimler"]) != BEKLENEN_BIRIM:
        hata.append(f"birim sayisi {len(birim['birimler'])} != {BEKLENEN_BIRIM}")
    if sum(b["soru_sayisi"] for b in birim["birimler"]) != BEKLENEN_SORU:
        hata.append("birim haritasi soru toplami 1948 degil")
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
    return hata


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:
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
        if not (k["konu_kodu"] or "").startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {k['konu_kodu']!r} {KOD_ONEKI}* degil")
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if pm["cevap_okuma_kanali"] not in CEVAP_KANALLARI:
            hata.append(
                f"{k['id']}: taninmayan cevap okuma kanali {pm['cevap_okuma_kanali']!r}"
            )
        if not pm["kirpim_kutusu"] or not k["question_image_url"]:
            hata.append(f"{k['id']}: kirpim yok -- bu kitapta her sorunun kutusu var")
        if pm["soru_no_basili"] != pm["birim_ici_sira"]:
            hata.append(f"{k['id']}: basili numara birim ici siraya esit degil")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur."""
    kok = conn.execute(
        "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (GEO_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{GEO_KOK_KODU} kok konusu yok"
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
            "0041_acil25_geo_konu_agaci kosmadi mi? Kok dugume dusurup "
            "sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    sayac = Counter(k["pipeline_metadata"]["ana_konu_kodu"] for k in kayitlar)
    print("konu dagilimi (ilk 10):")
    for kod, adet in sorted(sayac.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {adet:5d}  {kod}")
    print(
        f"  ... toplam {len(sayac)} ana konu, "
        f"{len({k['konu_kodu'] for k in kayitlar})} baglanan dugum"
    )
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print(
        "cevap kanali      :",
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)),
    )
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}")


def _hazirla(yollar: dict[str, Path]) -> list[dict[str, Any]] | None:
    """Dosyalari okur, kapilardan gecirir, kayitlari uretir (None = DURDU)."""
    oku = {ad: json.loads(p.read_text(encoding="utf-8")) for ad, p in yollar.items()}
    yapisal = _yapisal_kapilar(
        oku["veri"], oku["birim"], oku["kutular"], oku["anahtar"]
    )
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun buldu; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(
        f"yapisal kapi: {BEKLENEN_SORU} soru + {BEKLENEN_BIRIM} birim + "
        f"{BEKLENEN_SORU} anahtar + {BEKLENEN_SORU} kutu + cevap sizintisi yok -- TEMIZ"
    )
    satirlar = satirlari_bagla(
        oku["veri"],
        oku["birim"],
        oku["harita"],
        oku["kutular"],
        oku["anahtar"],
        ortme=oku["ortme"],
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
        f"+ {KOD_ONEKI} konu kodu + serit kaynagi + kutu/gorsel + basili no "
        "+ benzersiz hash -- TEMIZ"
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
                kutu = k["pipeline_metadata"]["kirpim_kutusu"]
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
                        "image_width": kutu[2] - kutu[0],
                        "image_height": kutu[3] - kutu[1],
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
    p.add_argument("--birim", default=VARSAYILAN_BIRIM)
    p.add_argument("--kutular", default=VARSAYILAN_KUTULAR)
    p.add_argument("--anahtar", default=VARSAYILAN_ANAHTAR)
    p.add_argument("--ortme", default=VARSAYILAN_ORTME)
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
        "birim": Path(args.birim),
        "kutular": Path(args.kutular),
        "anahtar": Path(args.anahtar),
        "ortme": Path(args.ortme),
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
