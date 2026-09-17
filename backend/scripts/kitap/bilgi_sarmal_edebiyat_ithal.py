#!/usr/bin/env python
"""Bilgi Sarmal AYT Edebiyat Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren bir okuyucu uygulamasinin 1920x1080 ekran
goruntuleridir (416 sayfa). PDF'te metin katmani YOK: orneklenen sayfalar
tek bir gomulu 1920x1080 gorsel tasiyor (olculdu). Sayfa karti goruntunun
icinde yalnizca 728x968 piksel yer kaplar (x 596-1323, y 46-1013; BU KITAP
ICIN olculdu, kardes kitabin 736x974'u VARSAYILMADI). Okuma 2x buyutulmus
kirpimla yapildi. Bu, kaynagin TAVANIDIR.

SAYFA HARITASI (piksel kanallariyla, metin okunmadan)
----------------------------------------------------
    1-9      kapak / kunye / sunu / icindekiler (4 s) / bilgi sayfalari
    10,53,106,257,345   BOLUM ayraci (5 bolum)
    11,54,107,258,346,406,407   SORDUK/SORDULAR (7 sayfa)
    12-405   test soru sayfalari
    408      cevap anahtari kapagi
    409-416  CEVAP ANAHTARI (basili 109-116)

Basili sayfa numarasi govdede dosya numarasiyla BIREBIR ayni (11 sayfada
goruntuden dogrulandi). Anahtar bolumunun kendi numaralandirmasi var.

IKI AYRI CEVAP KAYNAGI -- IKISI DE BASILI
-----------------------------------------
1. Kitap sonu anahtari (s409-416): 130 test blogu, 1572 cevap. IKI
   BAGIMSIZ okuma (farkli kirpim geometrisi + farkli olcek, okuyuculara
   beklenen sayi SOYLENMEDI): tek fark 1 girdi (s243 SARMAL TEST-3 no 12);
   iki hakem yuksek buyutmede 2/2 "D" dedi.
2. SORDUK/SORDULAR sayfalari (7 sayfa, 28 soru): dogru sik sayfanin
   ICINDE KIRMIZI basili. Bu sorular kitap sonu anahtarinda YOK. Kirmizi
   sik IKI BAGIMSIZ okumada 28/28 ayni cikti (ikinci okuyucuya yalnizca
   "hangi sik kirmizi" soruldu, soru metni okutulmadi).

Sorular HICBIR asamada COZULMEDI.

SIFIR SERBESTLIK DERECELI KAPILAR
---------------------------------
  * her testte numaralar 1..N kesintisiz            -> 130 testte 0 kusur
  * anahtardaki `Sayfa:` degerleri kesintisiz artar -> 0 kusur
  * okunan soru sayisi == anahtardaki soru sayisi   -> 130/130 test
  * anahtarin 130 `Sayfa:` degeri, METIN HIC OKUNMADAN olculen
    test-basligi bant kanaliyla (kart y 30-100 notr gri > 8000 px)
    BIREBIR ayni cikti                              -> 130/130
  * okuyucu simgesi GRUBU sayisi >= okunan soru sayisi, 772 sutun
    yuvasinin hicbirinde TERSI degil (565'inde tam esitlik). Fazlalik
    OLCULDU: 16 sayfa 0 soru tasir ama 4-10 simge grubu tasir; cunku
    kitabin ONEMLI/UNUTMA/DIKKAT bilgi kutulari da ayni simgeleri alir.
  * K1-K12 yapisal dogrulayici                      -> 1597 satirda 0 kusur

OKUYUCU SIMGESI ORTMESI -- KURTARILDI
-------------------------------------
Kardes kitapta (BS TYT Turkce) bu okuyucunun buyutec simgesi sol sutunun
satir sonlarini ortuyor ve 1468 sorunun 451'inde metnin bir bolumu
baglamdan tamamlanmak zorunda kalinmisti; ikinci kopya piksel piksel ayni
oldugu icin kurtarma yolu yoktu.

Bu kitapta durum FARKLI ve DAHA IYI:
  * duzeltilmis olcumle (metin murekkebi = koyu VE notr; turuncu ayrac /
    cyan kutu kenari / sari susleme murekkep SAYILMAZ) 1984 simge
    blogunun 133'u metne 0-3 px mesafede -- ust sinir %6.7.
  * ayni kitabin ikinci bir yakalamasi var (screenshots/"Bilgi Sarmal Ayt
    Edebiyat Soru Bankasi", 2023-2024 baskisi) ve simgeleri ~7 px KAYIK:
    ayni sayfada simge maskelerinin yalnizca ~%35'i ortusuyor. Govdedeki
    303 sayfa iki baskida ayni icerikte oldugu icin B'de ortulen bolge
    A'da ACIKTA.
  * Okuyuculara bu ikinci yakalama ("_alt" dosyasi) verildi; ortme
    bayragi kalan satir sayisi 1597'de 2 ve ikisi de yalnizca SORU
    NUMARASININ ortulmesidir (metin degil; numara zaten numara
    surekliligi kapisiyla dogrulandi).

BU KITAP AYRI BIR BASKI, KOPYA DEGIL
------------------------------------
Iki klasorun sayfa karti icindeki tam sayfa piksel farki 416/416 sayfada
sifirdan buyuk. Hizalanmis murekkep maskesi Jaccard'i ile: 318 sayfa ayni
icerik (render gurultusu), 98 sayfa GERCEKTEN farkli (ornek s48'de 11 ve
14 numarali sorular tamamen baska sorular). Bu ithal 2024 baskisini
(daha yeni, orneklerde metni daha tam) kapsar; 2023-2024 baskisinin
farkli 91 govde sayfasi AYRI bir is olarak durur (veri setine girmedi).

DB ORTUSMESI OLCULDU
--------------------
id (= uuid5(soru_hash)) carpismasi: 0/1597. Edebiyat/Turkce alanindaki
3130 mevcut satira karsi kelime kumesi ortusmesi >= 0.75 olan tek aday
(s76 q12, j=0.80) GOZLE incelendi: ortusme yalnizca kalip soru kokunden
geliyor ("Asagidakilerden hangisinde verilen ... ayrac icindeki belirleme
uyumlu degildir?"), icerik tamamen baska. Gercek kopya YOK.

KITABIN KENDI TEKRARI
---------------------
3 soru kitapta IKI KEZ basili: bir kez testte, bir kez SORDUK/SORDULAR
sayfasinda. Iki BAGIMSIZ cevap kaynagi (kitap sonu anahtari / sayfa ici
kirmizi sik) bu 3 soruda da AYNI harfi verdi. id = uuid5(hash) benzersiz
olmak zorunda oldugu icin veri setinde test satiri tutuldu ve
`sorduk_tekrari` ile isaretlendi.

KONU AGACI
----------
0031 ile kurulur: 5 bolum (EDB-BS1..EDB-BS5) + 53 konu dugumu. SARMAL
TEST / OSYM TIPI / Roman Karma gibi KARMA testler ve SORDUK/SORDULAR
sorulari konu dugumune degil kendi BOLUM dugumune baglanir.

BILINEN BORC
------------
  * 64 soru sekil/tablo iceriyor ama soru kirpimi URETILMEDI
    (`gorsel_yok_sekilli`); bunlar ogrenciye sekilsiz gosterilirse
    cozulemez.
  * 8 satirda kitabin KENDI dizgi kusuru isaretli (`kaynak_dizgi_kusuru`).
  * 3 sayfalik bagimsiz teyit okumasi (11 soru): farklarin tamami
    tirnak/tire glif varyantiydi, TEK icerik farki s380 q22'de cikti ve
    goruntuden 4x buyutmede karara baglandi (kitap "evlilik" yaziyor).
    Olculen tek-okuma hata mertebesi ~1 karakter / ~3000 karakter.
    TAM ikinci okuma YAPILMADI; bu borc kayitlidir.

Detay: veriseti/zkitap/cikti/BILGI_SARMAL_EDEBIYAT_YONTEM.md
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
VARSAYILAN_VERI = "veriseti/zkitap/cikti/bilgi_sarmal_edebiyat_sorular.json"
KAYNAK_ADI = "Bilgi Sarmal Ayt Edebiyat Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
EDB_KOK_KODU = "EDB"
# 0031 kodlari: EDB-BS1..EDB-BS5 ve EDB-BS<n>-NN. EDB-OSYM-GENEL'i KAPSAMAZ.
KOD_ONEKI = "EDB-BS"
SINAV_TURU = "AYT"
DERS_ALANI = "EDEBIYAT"
# Olculdu: exam_type='AYT' satirlarinin cogunlugu grade_level=12; kardes
# kitaplar (BS TYT Turkce, Aktif Ogrenme Dilbilgisi) da 12 ile ithal edildi.
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/bilgi_sarmal_edebiyat_ithal.py"
TELIF_NOTU = (
    "Bilgi Sarmal Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "Okuyucu uygulamasi ekran goruntusunden okuma hatti (2024 baskisi). "
    "Cevaplar KITABIN KENDI basili kaynaklarindan alindi: 1572 soru icin "
    "kitap sonu anahtari (dosya s409-416, IKI BAGIMSIZ okuma, tek fark "
    "hakemle 2/2 cozuldu), 25 soru icin sayfa ici KIRMIZI sik (SORDUK/"
    "SORDULAR, iki bagimsiz okuma 28/28 ayni). Sorular COZULMEDI. "
    "Test ici numara surekliligi 130 testte 0 kusur; okunan soru sayisi "
    "anahtarla 130/130 testte ayni; anahtarin 130 sayfa degeri metin hic "
    "okunmadan olculen test-basligi bant kanaliyla 130/130 ortustu. "
    "K1-K12 yapisal dogrulayici 1597 satirda 0 kusur. Okuyucu simgesinin "
    "ortmesi ikinci yakalamadan (2023-2024 baskisi, simgeler ~7 px kayik) "
    "KURTARILDI; kalan ortme 2 satirda ve yalnizca soru numarasinda. "
    "Detay: veriseti/zkitap/cikti/BILGI_SARMAL_EDEBIYAT_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "kitap_sonu_anahtari_cift_okuma_1_fark_hakem_2_2__sayfa_listesi_"
    "piksel_kanaliyla_130_130__numara_surekliligi_130_test_0_kusur"
)
KIRMIZI_DOGRULAMASI = "sayfa_ici_kirmizi_sik_cift_okuma_28_28_fark_0"


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("okuyucu_simgesi_ortmesi"):
        b.append("okuyucu_simgesi_ortmesi")
    if r.get("sekil_var"):
        b.append("gorsel_yok_sekilli")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_dizgi_kusuru")
    if r.get("konu_eslesme_duzeyi") == "bolum":
        b.append("konu_bolum_duzeyinde")
    if r.get("kaynak_bolumu") == "sorduk_sordular":
        b.append("sorduk_sordular_sayfasi")
    if r.get("cikmis_sinav"):
        b.append("cikmis_soru")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    kirmizi = r.get("cevap_kaynagi") == "sayfa_ici_kirmizi_sik"
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        "question_image_url": None,
        # Bu kitabin soru sayfalarinda cozum YOK; anahtar yalnizca harf verir.
        "explanation": None,
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": r.get("sinav_yili"),
        "osym_format_compliant": False,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "bolum_kodu": r["bolum_kodu"],
            "bolum_no": r["bolum_no"],
            "konu_bandi": r["bolum_adi"],
            "konu_eslesme_duzeyi": r["konu_eslesme_duzeyi"],
            "konu_kaynagi": "kitap_sonu_cevap_anahtari_basliklari",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": r.get("basili_sayfa"),
            "sutun": r.get("sutun"),
            "soru_no": r.get("soru_no"),
            "kaynak_bolumu": r.get("kaynak_bolumu"),
            "test_turu": r.get("test_konu"),
            "test_no": r.get("test_index"),
            "test_etiketi": r.get("test_etiketi"),
            "test_soru_sayisi": r.get("test_soru_sayisi"),
            "test_bas_sayfa": r.get("test_bas_sayfa"),
            "test_son_sayfa": r.get("test_son_sayfa"),
            "anahtar_sayfa": r.get("anahtar_sayfa"),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": r.get("cevap_kaynagi"),
            "anahtar_cift_okuma": True,
            "anahtar_dogrulamasi": (
                KIRMIZI_DOGRULAMASI if kirmizi else ANAHTAR_DOGRULAMASI
            ),
            "sorduk_tekrari": bool(r.get("sorduk_tekrari")),
            "sorduk_sayfa": r.get("sorduk_sayfa"),
            "sorduk_etiketi": r.get("sorduk_etiketi") or r.get("etiket"),
            "cikmis_soru": bool(r.get("cikmis_sinav")),
            "sinav_yili": r.get("sinav_yili"),
            "sekil_var": bool(r.get("sekil_var")),
            "gorsel_aciklama": r.get("gorsel_aciklama"),
            "gorsel_kaynagi": "yok_soru_kirpimi_uretilmedi",
            "kaynak_kusuru": r.get("kaynak_kusuru"),
            # Kitabin kusuru DEGIL: okuyucu uygulamasinin simgesi metni
            # ortuyor. Bu kitapta ikinci yakalamadan kurtarildi.
            "okuyucu_simgesi_ortmesi": bool(r.get("okuyucu_simgesi_ortmesi")),
            "ortulen_metin": r.get("ortulen_metin"),
            "ortme_kurtarma_kanali": "ikinci_yakalama_2023_2024_baskisi_simge_7px_kayik",
            "teyit_duzeltmesi": r.get("teyit_duzeltmesi"),
            "metin_kaynagi": "sayfa_granulerliginde_gorsel_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_728x968",
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
    NULL, NULL, NULL, NULL)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'AYT', 'EDEBIYAT', %(grade_level)s,
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


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:
    """Ithal oncesi ici bosluk denetimi -- bir tanesi bile varsa ithal baslamaz."""
    hata = []
    gorulen: set[str] = set()
    for k in kayitlar:
        sec = k["secenekler"]
        if len(sec) != 5 or any(h not in sec for h in "ABCDE"):
            hata.append(f"{k['id']}: 5 sik degil ({sorted(sec)})")
        if not k["correct_answer"]:
            hata.append(f"{k['id']}: cevap anahtari yok")
        elif not (sec.get(k["correct_answer"]) or "").strip():
            hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        kod = k["konu_kodu"] or ""
        if not kod.startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {kod!r} {KOD_ONEKI}* degil")
        kay = k["pipeline_metadata"]["cevap_kaynagi"]
        if kay not in (
            "kitap_sonu_anahtari",
            "sayfa_ici_kirmizi_sik",
            "kitap_sonu_anahtari__sayfa_ici_kirmizi_sik_teyitli",
        ):
            hata.append(f"{k['id']}: taninmayan cevap kaynagi {kay!r}")
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
        (EDB_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{EDB_KOK_KODU} kok konusu yok"
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
            f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)}. "
            "0031_bs_edebiyat_agac kosmadi mi? Kok dugume dusurup sessizce "
            "yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _meta_yenile(conn: psycopg.Connection, eski: list[dict], yaz: bool) -> None:
    """Zaten yazilmis satirlarin turetik alanlarini tazeler."""
    if not yaz:
        print(f"(--meta-guncelle plani: {len(eski)} satirin metadata'si yenilenecek)")
        return
    with conn.transaction():
        for k in eski:
            conn.execute(
                "UPDATE question_metadata SET pipeline_metadata = %(pm)s::json, "
                "readability_score = %(oku)s, morphology_complexity = %(morf)s, "
                "bloom_level = %(bl)s, bloom_category = %(bk)s WHERE id = %(id)s",
                {
                    "id": k["id"],
                    "pm": json.dumps(k["pipeline_metadata"], ensure_ascii=False),
                    "oku": k["readability_score"],
                    "morf": k["morphology_complexity"],
                    "bl": k["bloom_level"],
                    "bk": k["bloom_category"],
                },
            )
            conn.execute(
                "UPDATE question_bank SET primary_topic_id = %(kid)s WHERE id = %(id)s",
                {"id": k["id"], "kid": k["konu_id"]},
            )
    print(f"META GUNCELLENDI: {len(eski)} satir")


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    morf = [k["morphology_complexity"] for k in kayitlar]
    print("konu dagilimi (ilk 12):")
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    for kod, adet in sorted(sayac.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {adet:5d}  {kod}")
    print(f"  ... toplam {len(sayac)} konu kodu")
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print(
        "cevap kaynaklari  :",
        dict(Counter(k["pipeline_metadata"]["cevap_kaynagi"] for k in kayitlar)),
    )
    print(
        "simge ortmesi     :",
        sum(1 for k in kayitlar if k["pipeline_metadata"]["okuyucu_simgesi_ortmesi"]),
    )
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(
            f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}  "
            f"min {min(oku)}  maks {max(oku)}"
        )
        print(
            f"morfoloji         : ort {sum(morf) / len(morf):.3f}  "
            f"min {min(morf)}  maks {max(morf)}"
        )


def ithal(veri_yolu: Path, dsn: str, yaz: bool, meta_guncelle: bool = False) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    print(f"veri setinde {len(veri)} soru")
    if not veri:
        print("DURDU: ithal edilecek satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in veri]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print(
        "on kontrol: 5 sik + dolu anahtar + dolu metin + EDB-BS konu kodu "
        "+ tanidik cevap kaynagi + benzersiz hash -- TEMIZ"
    )

    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2

        yeni, bizim, yabanci = ayristir(conn, kayitlar, KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)

        if meta_guncelle and bizim:
            _meta_yenile(conn, bizim, yaz)
        _ozet(yeni or kayitlar)
        if not yaz:
            print("(--yaz verilmedi; hicbir sey yazilmadi)")
            return 0

        with conn.transaction():
            for k in yeni:
                s = k["secenekler"]
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
            print(
                "HATA: pasif ithal sozlesmesi bozuldu "
                "(aktif ya da kapidan gecen satir var)"
            )
            return 3
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    p.add_argument(
        "--meta-guncelle",
        action="store_true",
        help="var olan satirlarin turetik alanlarini yeniden yaz",
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz, args.meta_guncelle)


if __name__ == "__main__":
    raise SystemExit(main())
