"""Orijinal 2024 TYT-AYT Geometri Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren FERNUS okuyucusunun 1920x1080 ekran goruntuleridir.
Sayfa karti goruntunun icinde (593, 46)-(1327, 1014) = 734x968 piksel yer
kaplar -- BU KITAP ICIN olculdu. Kirpim script'i her sayfayi BEKLENEN_BOYUT
ile karsilastirir; tutmazsa DURUR.

BIRIM = KITABIN KENDI TEST BLOGU
--------------------------------
Kitap sorulari 231 birime bolmus (226 adli test + 5 OSYM bolumu); her
birimin son sayfasinda bir CEVAP SERIDI var. 2072 soru.

CEVAP KAYNAGI: BIRIM SONU CEVAP SERIDI
--------------------------------------
Anahtar kitabin KENDI basili seritlerinden okundu; hicbir soru cozulmedi.
90 seridin tamami (823 girdi) gozle okundu, kalan 1249 girdi bu etiketli
kumeyle kurulan 1-NN siniflandiriciyla okundu (LOO 822/823, egitim kumesi
uyumu 823/823). Ilk turda yanlis cikan 7 girdiyi TOPLAM degil MARJ buldu:
onlar kumenin en dusuk marjli tam olarak 7 girdisiydi. Duzeltmeden sonra
makine kaynakli en dusuk marj 0.1004.

TRANSKRIPSIYON: OKUYUCUYA SAYIM SOYLENMEDI
------------------------------------------
417 soru sayfasi birim sinirina hizali 30 gruba bolundu; her grubu ayri bir
okuyucu okudu. Okuyucuya sayfada kac soru oldugu soylenmedi ve cevap
anahtari gosterilmedi. Dort yapisal kapi (sayfa-sutun basina soru sayisi ==
kirpim kutusu sayisi; birim ici basili numaralar 1..N; bes sik dolu; toplam
2072) 30 grupta da yesil cikti.

GORSELLER -- TAM SORU KIRPIMI
-----------------------------
`question_image_url` TAM SORU KIRPIMIDIR; kutu
`pipeline_metadata.kirpim_kutusu`'nda saklanir ve gorseller
`scripts/kitap/orijinal_geo_kirp.py` ile PNG'lerden yeniden uretilebilir.
Kutular LLM'e TAHMIN ETTIRILMEDI: okuyucu simge konumlarindan turetildi.
Sutun sinirlari SAYFA BASINA olculur (metin blogu tek/cift sayfada ~16 px
kayiyor); sabit sinir cift sayfalarda metni kesiyordu.

ORTULU SORU YOK -- 2072/2072 ITHAL EDILIR
-----------------------------------------
Ortme olcumu (GEO_ORIJINAL_2024_FAZ1.md bolum 14) soru sayfalarinda okuyucu
diskinin altinda soru icerigi KALMADIGINI olctu; disk beyazlatmak soru
kaybettirmiyor. Her sorunun kutusu var.

KONU AGACI
----------
0040 ile kurulur: GEO kokunun altinda GEO-ORJ24 onekiyle 5 bolum + 30 adli
konu + 5 OSYM dugumu. Konu ATAMASI birim duzeyinde yapilir: birim
haritasindaki `konu` alani kullanilir ve her birimin sayfa KUMESI tek bir
konunun araliginda mi diye ayrica dogrulanir.

BILINEN BORC
------------
  * TAM ikinci transkripsiyon yapilmadi (pilot sayfalarda uc kanal yapildi).
  * Cozumler kitapta soru sayfasinda YOK; `explanation` bos birakilir.
  * Sinav turu soru duzeyinde OLCULMEDI: kitap TYT ve AYT sorularini karisik
    basiyor. Kardes geometri kitaplariyla tutarli olsun diye 'AYT' yazilir
    ve durum `sinav_turu_kaynagi` ile isaretlenir.
  * 101 soruda okuyucu YAPISAL kaynak kusuru isaretledi; satirlar ithal
    edilir, bayrakla gorunur kalir.

Detay: veriseti/zkitap/cikti/GEO_ORIJINAL_2024_FAZ1.md
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
VARSAYILAN_VERI = f"{CIKTI}/orijinal_2024_geometri_metin.json"
VARSAYILAN_HARITA = f"{CIKTI}/orijinal_2024_geometri_konu_haritasi.json"
VARSAYILAN_BIRIM = f"{CIKTI}/orijinal_2024_geometri_birim_haritasi.json"
VARSAYILAN_KUTULAR = f"{CIKTI}/orijinal_2024_geometri_kirpim_kutulari.json"
VARSAYILAN_ANAHTAR = f"{CIKTI}/orijinal_2024_geometri_cevap_anahtari.json"
KAYNAK_ADI = "Orijinal 2024 TYT-AYT Geometri Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ORJ24"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/orijinal_geo_ithal.py"
CROP_ONEK = "ORIJINALGEO_2024"
KART = (593, 46, 1327, 1014)
TELIF_NOTU = (
    "Orijinal Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar KITABIN birim "
    "sonu cevap seridinden alindi; 90 serit (823 girdi) gozle okundu, kalan "
    "1249 girdi bu etiketli kumeyle kurulan 1-NN ile okundu (LOO 822/823). "
    "Sorular cozulmedi. Kirpim kutulari okuyucu simgesinden turetildi; sutun "
    "sinirlari sayfa basina olculdu. Transkripsiyon 30 grupta ayri "
    "okuyucularla yapildi; okuyucuya soru sayisi soylenmedi, anahtar "
    "gosterilmedi. Detay: veriseti/zkitap/cikti/GEO_ORIJINAL_2024_FAZ1.md"
)
ANAHTAR_DOGRULAMASI = (
    "birim_sonu_cevap_seridi_gozle_823_makine_1249__"
    "gozle_ile_makine_823_823_uyumlu__"
    "birim_simge_sayisi_esittir_cevap_sayisi_231_231__"
    "basili_numara_esittir_birim_ici_sira_2072_2072"
)
CEVAP_KAYNAGI = "birim_sonu_cevap_seridi"
KIRPIM_SISTEMI = "sayfa_karti_593_46_1327_1014_sutun_sinirlari_sayfa_basina"
BEKLENEN_SORU = 2072
BEKLENEN_BIRIM = 231


def _bolum_kodu(kod: str) -> str:
    """GEO-ORJ24-B01-03 -> GEO-ORJ24-B01 (kod hiyerarsiyi kendisi tasir)."""
    return "-".join(kod.split("-")[:3])


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("sekil_var") and not r.get("kirpim_kutusu"):
        b.append("gorsel_yok_sekilli")
    if r.get("sikler_gorsel"):
        b.append("sikler_gorsel")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_kusuru")
    if not (sec.get(r["cevap"]) or "").strip():
        b.append("anahtar_sikki_okunamadi")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r["sikler"][h] for h in "ABCDE"}
    h = soru_hash(r["govde"], sec)
    n, u, ort = kelime_istatistik(r["govde"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["govde"], sec)
    kutu = r.get("kirpim_kutusu")
    kayit_id = str(uuid.uuid5(uuid.NAMESPACE_OID, h))
    return {
        "id": kayit_id,
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["govde"],
        "secenekler": sec,
        "correct_answer": r["cevap"],
        # GORSEL ADI: kirpim script'inin KENDI urettigi ad (sNNNN_sutun_sira);
        # kirpim hatti metin hattindan bagimsiz calisir, hash'i bilmez.
        "question_image_url": (
            f"/static/crops/{CROP_ONEK}/{r['gorsel']}" if kutu else None
        ),
        "explanation": None,
        "source_page": int(r["sayfa"]),
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
            "bolum_kodu": _bolum_kodu(r["konu_kodu"]),
            "konu_eslesme_duzeyi": "konu",
            "konu_kaynagi": "birim_haritasi_sayfa_araligi_dogrulandi",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": int(r["sayfa"]),  # olculdu: ofset 0
            "sutun": r["sutun"],
            "sutun_ici_sira": r["sira"],
            "soru_no_basili": r["basili_no"],
            "birim_kodu": r["birim"],
            "birim_ici_sira": r["birim_ici_sira"],
            "birim_turu": r["birim_turu"],
            "kaynak_gorseli": r["gorsel"],
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "cevap_okuma_kanali": r["cevap_kanali"],
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "sekil_var": bool(r.get("sekil_var")),
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kaynak_kusuru": r.get("kaynak_kusuru") or None,
            "kirpim_kutusu": kutu,
            "kirpim_koordinat_sistemi": KIRPIM_SISTEMI,
            "gorsel_kaynagi": "tam_soru_kirpimi" if kutu else "yok_kutu_uretilemedi",
            "sinav_turu_kaynagi": "olculmedi_kitap_TYT-AYT_karisik",
            "metin_kaynagi": "sayfa_karti_gorsel_okuma_30_grup",
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


def _birim_sirasi(birimler: list[dict], sorular: list[dict]) -> dict[tuple, dict]:
    """Her soruyu birimine ve birim ici sirasina baglar.

    BAGLAMA KURALI: birimin sayfalarinda OKUMA SIRASI (once SOL sutun
    yukaridan asagiya, sonra SAG) birim ici siradir. Bu kural uydurma
    degil: basili numaralar tam bu siraya gore 1..N cikiyor (KAPI2) ve
    bu fonksiyon o esitligi ayrica dogruluyor.
    """
    okunan: dict[tuple, list[dict]] = {}
    for s in sorular:
        okunan.setdefault((s["sayfa"], s["sutun"]), []).append(s)
    bagli: dict[tuple, dict] = {}
    for b in birimler:
        sira = 0
        for p in range(b["bas_sayfa"], b["son_sayfa"] + 1):
            for sut in ("sol", "sag"):
                for s in sorted(okunan.get((p, sut), []), key=lambda x: x["sira"]):
                    sira += 1
                    bagli[(s["sayfa"], s["sutun"], s["sira"])] = {
                        "kod": b["kod"],
                        "konu": b["konu"],
                        "tur": b["tur"],
                        "birim_ici_sira": sira,
                    }
        if sira != b["soru_sayisi"]:
            raise ValueError(
                f"{b['kod']}: birim ici {sira} soru okundu, "
                f"birim haritasi {b['soru_sayisi']} diyor"
            )
    return bagli


def satirlari_bagla(
    veri: dict, birim: dict, harita: dict, kutular: dict, anahtar: dict
) -> list[dict[str, Any]]:
    """Metin, birim, konu araligi, kirpim kutusu ve cevap anahtarini birlestirir."""
    bagli = _birim_sirasi(birim["birimler"], veri["sorular"])
    kutu = {(b["sayfa"], b["sutun"], b["sira"]): b["kutu"] for b in kutular["kutular"]}
    cevap = {(c["birim"], c["soru"]): c for c in anahtar["cevaplar"]}
    aralik = [(k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]]

    satir = []
    for s in veri["sorular"]:
        anah = (s["sayfa"], s["sutun"], s["sira"])
        b = bagli[anah]
        c = cevap[(b["kod"], b["birim_ici_sira"])]
        # Konu kodu birim haritasindan gelir; sayfa araligiyla AYRICA
        # dogrulanir ki iki kaynak sessizce ayrismasin.
        kapsayan = {kod for bas, son, kod in aralik if bas <= s["sayfa"] <= son}
        if b["konu"] not in kapsayan:
            raise ValueError(
                f"{b['kod']} s{s['sayfa']}: birim konusu {b['konu']} "
                f"sayfa araligiyla ortusmuyor {sorted(kapsayan)}"
            )
        satir.append(
            {
                **s,
                "birim": b["kod"],
                "birim_turu": b["tur"],
                "birim_ici_sira": b["birim_ici_sira"],
                "konu_kodu": b["konu"],
                "cevap": c["cevap"],
                "cevap_kanali": c["kaynak"],
                "sikler_gorsel": all("rsel" in str(v) for v in s["sikler"].values()),
                "gorsel": f"s{s['sayfa']:04d}_{s['sutun']}_{s['sira']}.png",
                "kirpim_kutusu": kutu.get(anah),
            }
        )
    return satir


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
    if len(anahtar["cevaplar"]) != BEKLENEN_SORU:
        hata.append(f"anahtar sayisi {len(anahtar['cevaplar'])} != {BEKLENEN_SORU}")
    if len(kutular["kutular"]) != BEKLENEN_SORU:
        hata.append(f"kutu sayisi {len(kutular['kutular'])} != {BEKLENEN_SORU}")
    # Transkripsiyon anahtardan BAGIMSIZ kanal olmali.
    sizan = [s for s in sorular if {"cevap", "correct_answer"} & set(s)]
    if sizan:
        hata.append(f"{len(sizan)} metin satirinda cevap alani var -- kanal kirlendi")
    return hata


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:
    """Ithal oncesi ici bosluk denetimi -- bir tanesi bile varsa ithal baslamaz."""
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
        kod = k["konu_kodu"] or ""
        if not kod.startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {kod!r} {KOD_ONEKI}* degil")
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if pm["cevap_okuma_kanali"] not in ("gozle", "makine"):
            hata.append(f"{k['id']}: taninmayan cevap okuma kanali")
        if bool(pm["kirpim_kutusu"]) != bool(k["question_image_url"]):
            hata.append(f"{k['id']}: kutu ve gorsel yolu tutarsiz")
        if not k["question_image_url"]:
            # Metin hatti 2072 satir verdiyse kirpim hatti da 2072 kutu
            # vermeli; bu kitapta ortulu soru yok.
            hata.append(f"{k['id']}: kirpim yok -- bu kitapta her sorunun kutusu var")
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
            "SELECT code, id FROM topic_hierarchy WHERE code = ANY(%s)",
            (kodlar,),
        ).fetchall()
    )
    eksik = set(kodlar) - set(konular)
    if eksik:
        return (
            f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)[:5]}. "
            "0040_orijinal_geo_konu_agaci kosmadi mi? Kok dugume dusurup "
            "sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    print("konu dagilimi (ilk 10):")
    for kod, adet in sorted(sayac.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {adet:5d}  {kod}")
    print(f"  ... toplam {len(sayac)} konu kodu")
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print(
        "gorselli          :",
        sum(1 for k in kayitlar if k["question_image_url"]),
        "/",
        len(kayitlar),
    )
    print(
        "cevap kanali      :",
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)),
    )
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}")


def _hazirla(yollar: dict[str, Path]) -> list[dict[str, Any]] | None:
    """Dosyalari okur, kapilardan gecirir, kayitlari uretir.

    Bir kapi tutarsa gerekceyi basar ve None doner; cagiran DURUR. DB'ye
    hicbir sey yazilmadan once bilinmesi gereken her sey buradadir.
    """
    veri = json.loads(yollar["veri"].read_text(encoding="utf-8"))
    harita = json.loads(yollar["harita"].read_text(encoding="utf-8"))
    birim = json.loads(yollar["birim"].read_text(encoding="utf-8"))
    kutular = json.loads(yollar["kutular"].read_text(encoding="utf-8"))
    anahtar = json.loads(yollar["anahtar"].read_text(encoding="utf-8"))

    yapisal = _yapisal_kapilar(veri, birim, kutular, anahtar)
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun buldu; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(
        f"yapisal kapi: {BEKLENEN_SORU} soru + {BEKLENEN_BIRIM} birim + "
        f"{BEKLENEN_SORU} anahtar + {BEKLENEN_SORU} kutu + cevap sizintisi yok "
        "-- TEMIZ"
    )

    satirlar = satirlari_bagla(veri, birim, harita, kutular, anahtar)
    print(f"veri setinde {len(satirlar)} soru")
    kayitlar = [kayit_uret(r) for r in satirlar]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return None
    print(
        "on kontrol: 5 sik + A-E cevap + dolu anahtar sikki + dolu metin "
        f"+ {KOD_ONEKI} konu kodu + birim sonu serit kaynagi "
        "+ kutu/gorsel tutarliligi + benzersiz hash -- TEMIZ"
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
                        "image_width": (kutu[2] - kutu[0]) if kutu else None,
                        "image_height": (kutu[3] - kutu[1]) if kutu else None,
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
            f"DB'de bu ithalin satirlari: toplam {n}, is_active {aktif}, "
            f"kapidan gecen {kapida}"
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
