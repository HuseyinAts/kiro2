#!/usr/bin/env python
"""ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren FERNUS okuyucusunun 1920x1080 ekran goruntuleridir
(448 sayfa; soru sayfalari s5-s446). Sayfa karti goruntunun icinde
(593, 46)-(1327, 1014) = 734x968 piksel yer kaplar -- BU KITAP ICIN
olculdu; kardes kitaplarda 728x968 ve 748x980 cikmisti, varsayilsaydi her
kirpim kayardi. Basili sayfa no = dosya no (ofset 0), iki bagimsiz yerden
dogrulandi.

CEVAP KAYNAGI: TEST SONU IZGARA KUTUSU
--------------------------------------
Bu kitapta anahtar ne kitabin sonunda ne sayfa altinda: her testin SON
sayfasinin altinda iki satirlik bir IZGARA KUTUSU testin tum sorularinin
cevabini birlikte veriyor (ornek s200: "1.C 2.A ... 13.B"). 138 kutu,
1881 cevap. Sorular COZULMEDI.

Anahtar DORT BAGIMSIZ kanaldan okundu:
  * kanal A : ileri sirali montaj
  * kanal B : ters sirali montaj, farkli olcek
  * kanal C : 4x nokta atisi ornekleme
  * kanal D : test basina okuyucu simgesi sayimi caprazi
Dort kanalda 1881 cevabin tamaminda uyusmazlik YOK.

151 SORU ISLENMEDI -- SAHIP KARARI
----------------------------------
Sag sutunun okuyucu simgesi (opak lila disk) sol sutundaki sorunun SON
SIK SATIRININ uzerine biniyor. Faz 0'in "diskin icinde murekkep var mi"
metrigi bunu yapisal olarak goremezdi -- disk opak oldugu icin altindaki
murekkep goruntude zaten YOK. Dogru metrik "diskin hemen SOLUNDA metin
satiri bitiyor mu": 154 ortme olayi, 151 benzersiz soru.

Bu 151 soru kirpim kutusu dosyasinda `ortulu: true` isaretli; kirpim
uretilmedi, transkripsiyon yapilmadi, bu ithale de GIRMEZ. Kalan 1730
soru ithal edilir. Kararin sahibi: eksik sikli soru servis etmektense
soruyu disarida birakmak.

GORSELLER -- TAM SORU KIRPIMI
-----------------------------
1730 sorunun 1513'u sekil iceriyor ve sekil olmadan soru eksik kalir.
`question_image_url` TAM SORU KIRPIMIDIR; kutu
`pipeline_metadata.kirpim_kutusu`'nda saklanir ve gorseller
`scripts/kitap/acil_geo_kirp.py` ile PNG'lerden yeniden uretilebilir.
Kirpim script'i alti kapidan gecmeden tek dosya yazmaz.

Kutular LLM'e TAHMIN ETTIRILMEDI: okuyucunun her sorunun soluna cizdigi
simge piksel duzeyinde bulundu (glif 69,39,160 + lila disk 240,238,247)
ve kutu simge konumlarindan turetildi. Kirpimlarin alt siniri test sonu
cevap kutusunun USTUNDE tutuldu; kirpimda cevap gorunmez.

17 SORUDA SIKLAR METIN DEGIL
----------------------------
17 soruda A-E siklari grafik/diyagramdir; metin olarak basili degildir.
Bu satirlarda sik alanlarina "(gorsel sik)" yazildi ve `sikler_gorsel`
bayragi kondu -- siklar UYDURULMADI.

KONU AGACI
----------
0034 ile kurulur: GEO kokunun altinda GEO-ACL24 onekiyle 6 bolum +
27 konu + 3 alt konu. Adlar kitabin ICINDEKILER sayfasindan (s3) ve
138 testin ilk sayfasindaki BASLIK BANDINDAN okundu; iki kanal celismedi
ve 138 testin 138'i tek bir konunun sayfa araliginda kaldi. Mevcut
GEO-U* agacina DOKUNULMADI (kitabin konu kumesi onunla ortusmuyor).

BILINEN BORC
------------
  * 151 soru ortme yuzunden ithal edilmedi (yukarida).
  * 36 satirda kitabin KENDI basim kusuru isaretli (biri numara hatasi:
    s0185 sag 2'de basili numara 10, test ici sira 8).
  * 10 satirda okunamayan bir parca isaretli; UYDURULMADI.
  * TAM ikinci transkripsiyon yapilmadi (cevap anahtari icin yapildi).
  * Sinav turu soru duzeyinde OLCULMEDI: kitap TYT ve AYT sorularini
    karisik basiyor, exam_type tek degerli kolon. Kardes geometri
    kitaplariyla tutarli olsun diye 'AYT' yazilir ve durum
    `sinav_turu_kaynagi` ile isaretlenir.

Detay: veriseti/zkitap/cikti/GEO_ACIL_2324_YONTEM.md
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
VARSAYILAN_VERI = f"{CIKTI}/acil_2324_geometri_metin.json"
VARSAYILAN_HARITA = f"{CIKTI}/acil_2324_geometri_konu_haritasi.json"
VARSAYILAN_KUTULAR = f"{CIKTI}/acil_2324_geometri_kirpim_kutulari.json"
KAYNAK_ADI = "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-ACL24"
SINAV_TURU = "AYT"
DERS_ALANI = "GEOMETRI"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/acil_geo_ithal.py"
CROP_ONEK = "ACILGEO_2324"
KART = (593, 46, 1327, 1014)
TELIF_NOTU = (
    "ACIL Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
    "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar KITABIN test "
    "sonu izgara kutusundan alindi; DORT BAGIMSIZ kanal (ileri montaj, ters "
    "montaj, 4x ornekleme, simge sayimi caprazi) 138 testte 1881 cevap verdi "
    "ve hicbirinde uyusmadilar degil -- uyusmazlik yok. Sorular cozulmedi. "
    "Transkripsiyon 37 ayri ajanla yapildi; yedi yapisal kapi (kayit sayisi, "
    "ortme, ad eslesmesi, test basina cevap, basili numara == test ici sira, "
    "cevap eslesmesi, doluluk) gecti. 151 soru okuyucu simgesi ortmesi "
    "yuzunden DISARIDA BIRAKILDI. Detay: "
    "veriseti/zkitap/cikti/GEO_ACIL_2324_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "test_sonu_izgara_kutusu_dort_kanal_1881_1881_uyumlu__"
    "transkripsiyon_basili_numarasi_1729_1730_ayni_1_kitap_basim_hatasi"
)
CEVAP_KAYNAGI = "test_sonu_izgara_kutusu"
KIRPIM_SISTEMI = "sayfa_karti_593_46_1327_1014"


def _bolum_kodu(kod: str) -> str:
    """GEO-ACL24-B01-03-02 -> GEO-ACL24-B01 (kod hiyerarsiyi kendisi tasir)."""
    parca = kod.split("-")
    return "-".join(parca[:3])


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("sekil_var") and not r.get("kirpim_kutusu"):
        b.append("gorsel_yok_sekilli")
    if r.get("sikler_gorsel"):
        b.append("sikler_gorsel")
        if not r.get("kirpim_kutusu"):
            # Siklari gorsel AMA kirpimi da yok: bu satir ogrenciye hicbir
            # bicimde gosterilemez. Silinmiyor, gorunur isaretleniyor.
            b.append("gosterilemez_gorsel_sik_kirpimsiz")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_dizgi_kusuru")
    if r.get("okunamayan"):
        b.append("okunamayan_parca")
    if not (sec.get(r["cevap"]) or "").strip():
        # Anahtar sikkin METNI kaynakta okunamadi (uydurulmadi). Satir
        # silinmiyor: tam soru kirpimi gercek sikki tasiyor.
        b.append("anahtar_sikki_okunamadi")
    if r.get("konu_eslesme_duzeyi") == "alt_konu":
        b.append("konu_alt_konu_duzeyinde")
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
        # GORSEL ADI: kirpim script'inin KENDI urettigi ad (sNNNN_sutun_sira).
        # fiz345'te ad kayit id'siydi; orada veri seti id'yi zaten tasiyordu.
        # Burada kirpim script'i metin hattindan BAGIMSIZ calisiyor (PNG'den
        # uretiyor, hash'i bilmiyor). Ikinci bir adlandirma semasi uydurmak
        # yerine kirpimin kendi deterministik adi kullaniliyor; boylece
        # `acil_geo_kirp.py` yeniden kosunca dosya adlari degismez.
        "question_image_url": (
            f"{os.environ.get('CROP_IMAGE_DIR', 'd-dataset/output/crops')}/"
            f"{CROP_ONEK}/{r['gorsel']}"
            if kutu
            else None
        ),
        # Kitabin soru sayfalarinda cozum YOK; izgara kutusu yalniz harf verir.
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
            "konu_eslesme_duzeyi": r["konu_eslesme_duzeyi"],
            "konu_kaynagi": "icindekiler_ve_test_baslik_bandi",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": int(r["sayfa"]),  # olculdu: ofset 0
            "sutun": r["sutun"],
            "sutun_ici_sira": r["sira"],
            "soru_no_basili": r["soru_no_basili"],
            "test_no": r["test"],
            "test_ici_sira": r["test_ici_sira"],
            "kaynak_gorseli": r["gorsel"],
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": CEVAP_KAYNAGI,
            "anahtar_cift_okuma": True,
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "sekil_var": bool(r.get("sekil_var")),
            "sekil_aciklama": r.get("sekil_aciklama") or None,
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kirpim_kutusu": kutu,
            "kirpim_koordinat_sistemi": KIRPIM_SISTEMI,
            "gorsel_kaynagi": "tam_soru_kirpimi" if kutu else "yok_kutu_uretilemedi",
            "kaynak_kusuru": r.get("kaynak_kusuru") or None,
            "okunamayan": r.get("okunamayan") or None,
            "sinav_turu_kaynagi": "olculmedi_kitap_TYT-AYT_karisik",
            "metin_kaynagi": "soru_granulerliginde_gorsel_okuma",
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


def satirlari_bagla(veri: dict, harita: dict, kutular: dict) -> list[dict[str, Any]]:
    """Metin veri setini konu haritasi ve kirpim kutulariyla birlestirir.

    ORTULU kutular kirpim dosyasindan HIC alinmaz: bu ithalin kapsami
    `acil_2324_geometri_metin.json` icindeki 1730 satirdir.
    """
    kutu = {
        f"s{b['sayfa']:04d}_{b['sutun']}_{b['sira']}.png": b["kirpim_kutusu"]
        for b in kutular["kutular"]
        if not b.get("ortulu")
    }
    alt = {a["kod"] for a in harita["alt_konular"]}
    satir = []
    for s in veri["sorular"]:
        # Eksik sik anahtari `kayit_uret` icinde cig bir KeyError'a donusurdu;
        # kapinin mesaji yerine yigin izi okumak istemiyoruz.
        eksik = [h for h in "ABCDE" if h not in (s.get("sikler") or {})]
        if eksik:
            raise ValueError(f"{s['gorsel']}: sik anahtari eksik {eksik}")
        if str(s["test"]) not in harita["test_konu"]:
            raise ValueError(f"{s['gorsel']}: test {s['test']} haritada yok")
        kod = harita["test_konu"][str(s["test"])]
        satir.append(
            {
                **s,
                "konu_kodu": kod,
                "konu_eslesme_duzeyi": "alt_konu" if kod in alt else "konu",
                "kirpim_kutusu": kutu.get(s["gorsel"]),
            }
        )
    return satir


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
            # TEK ISTISNA: sik metni kaynakta okunamadi VE bu durum
            # `okunamayan` alaninda belgelenmis VE tam soru kirpimi var,
            # yani ogrenci gercek sikki gorselde goruyor. Belgelenmemis
            # bos anahtar hala DURDURUR -- kapinin asil isi o.
            pm_ = k["pipeline_metadata"]
            if not (pm_["okunamayan"] and k["question_image_url"]):
                hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        kod = k["konu_kodu"] or ""
        if not kod.startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {kod!r} {KOD_ONEKI}* degil")
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if bool(pm["kirpim_kutusu"]) != bool(k["question_image_url"]):
            hata.append(f"{k['id']}: kutu ve gorsel yolu tutarsiz")
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
            "0034_acilgeo_agac kosmadi mi? Kok dugume dusurup sessizce yanlis "
            "baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    print("konu dagilimi (ilk 10):")
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
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
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}")


def ithal(yollar: dict[str, Path], dsn: str, yaz: bool) -> int:
    veri = json.loads(yollar["veri"].read_text(encoding="utf-8"))
    harita = json.loads(yollar["harita"].read_text(encoding="utf-8"))
    kutular = json.loads(yollar["kutular"].read_text(encoding="utf-8"))
    satirlar = satirlari_bagla(veri, harita, kutular)
    print(
        f"veri setinde {len(satirlar)} soru "
        f"(ortme yuzunden disarida: {kutular.get('ortulu')})"
    )
    if not satirlar:
        print("DURDU: ithal edilecek satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in satirlar]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print(
        "on kontrol: 5 sik + dolu anahtar + dolu metin + GEO-ACL24 konu kodu "
        "+ test sonu izgara kaynagi + kutu/gorsel tutarliligi "
        "+ benzersiz hash -- TEMIZ"
    )

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
    p.add_argument("--kutular", default=VARSAYILAN_KUTULAR)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    yollar = {
        "veri": Path(args.veri),
        "harita": Path(args.harita),
        "kutular": Path(args.kutular),
    }
    return ithal(yollar, args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
