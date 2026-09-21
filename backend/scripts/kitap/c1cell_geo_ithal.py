#!/usr/bin/env python
"""C1CELL 2024 TYT-AYT Geometri Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren FERNUS okuyucusunun 1920x1080 ekran goruntuleridir.
Sayfa karti goruntunun icinde (591, 46)-(1329, 1014) = 738x968 piksel yer
kaplar -- BU KITAP ICIN olculdu; kardes kitaplarda 734x968, 728x968 ve
748x980 cikmisti, varsayilsaydi her kirpim kayardi. Kirpim script'i her
sayfayi BEKLENEN_BOYUT ile karsilastirir; tutmazsa DURUR.

BIRIM = KITABIN KENDI TEST BLOGU
--------------------------------
Kitap sorulari 163 birime bolmus; her birimin sonunda bir CEVAP SERIDI var.
Birim numarasi kitapta basili degil, yapisal olarak turetildi (bkz. KAPI).

CEVAP KAYNAGI: BIRIM SONU CEVAP SERIDI
--------------------------------------
Anahtar ne kitabin sonunda ne sayfa altinda: her birimin son sayfasinin
altinda acik mavi hucreli bir SERIT birimin tum sorularinin cevabini
birlikte veriyor. 163 serit, 1770 cevap. Sorular COZULMEDI.

Anahtar UC BAGIMSIZ kanaldan okundu (ben + iki ayri ajan), ardindan
uyusmayan hucreler yuksek buyutmede tek tek hakem okumasiyla karara
baglandi; hakem 5 hatayi benim okumamda buldu (ilk gecis %99.72).
Son durum: 1770 cevabin tamaminda uc kanal uyumlu.

YAPISAL GARANTI: BIRIM SIMGE-SAYISI == CEVAP-SAYISI (163/163)
-------------------------------------------------------------
Bu ithalin tasiyici kapisi. Okuyucu her sorunun soluna bir simge cizer;
simgeler piksel duzeyinde bulundu (lila disk 240,238,247 / glif 69,39,160).
Birim sinirlari "N'e geri topla" ile cizildi: seritten geriye dogru simge
toplanir, toplam serit'in cevap sayisina esitlenince birim kapanir.
163 birimin 163'unde simge sayisi cevap sayisina esit cikti -- yani
hicbir soru kaymadi, hicbir cevap sahipsiz kalmadi.

Bes sayfada okuyucu-disi sekil/konu-kutusu isaretleri simge sanilmisti;
bunlar `..._simge_duzeltme.json` overlay'i ile dusuruldu, ham Faz 0
ciktisina DOKUNULMADI (olcum izi korunur).

ORTULU SORU YOK -- 1770/1770 ITHAL EDILIR
-----------------------------------------
ACIL 2023-2024'te sag sutunun opak okuyucu diski sol sutunun son sik
satirini ortuyordu ve 151 soru disarida birakilmisti. C1CELL'de kutular
dort kapidan (sayi, serit sizintisi, ortusme/kisa kutu, murekkep) gecti
ve ortme yok; 1770 sorunun tamami ithal edilir.

GORSELLER -- TAM SORU KIRPIMI
-----------------------------
1770 sorunun 1519'u sekil iceriyor ve sekil olmadan soru eksik kalir.
`question_image_url` TAM SORU KIRPIMIDIR; kutu
`pipeline_metadata.kirpim_kutusu`'nda saklanir ve gorseller
`scripts/kitap/c1cell_geo_kirp.py` ile PNG'lerden yeniden uretilebilir.
Kutular LLM'e TAHMIN ETTIRILMEDI: simge konumlarindan turetildi.

1 SORUDA SIKLAR METIN DEGIL
---------------------------
s0397 sol 2'de A-E siklari donusum geometrisi sekilleridir; metin olarak
basili degildir. O satirda sik alanlarina "(gorsel sik)" yazildi ve
`sikler_gorsel` bayragi kondu -- siklar UYDURULMADI. Tam soru kirpimi
gercek sikleri tasiyor.

KONU AGACI
----------
0035 ile kurulur: GEO kokunun altinda GEO-C1C24 onekiyle 5 bolum +
21 konu. Adlar ve sayfa araliklari kitabin ICINDEKILER sayfasindan
okundu. Konu ATAMASI birim duzeyinde yapilir: 163 birimin 163'u tek bir
konunun sayfa araliginin ICINDE kaldi (olculdu), yani bir birimin
sorulari asla iki konuya bolunmez. Mevcut GEO-U* ve GEO-ACL24 agaclarina
DOKUNULMADI.

BILINEN BORC
------------
  * TAM ikinci transkripsiyon yapilmadi (cevap anahtari icin yapildi).
  * Cozumler kitapta soru sayfasinda YOK; `explanation` bos birakildi.
  * Sinav turu soru duzeyinde OLCULMEDI: kitap TYT ve AYT sorularini
    karisik basiyor, exam_type tek degerli kolon. Kardes geometri
    kitaplariyla tutarli olsun diye 'AYT' yazilir ve durum
    `sinav_turu_kaynagi` ile isaretlenir.

Detay: veriseti/zkitap/cikti/GEO_C1CELL_2024_KESIF.md
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
VARSAYILAN_VERI = f"{CIKTI}/c1cell_2024_geometri_metin.json"
VARSAYILAN_HARITA = f"{CIKTI}/c1cell_2024_geometri_konu_haritasi.json"
VARSAYILAN_KUTULAR = f"{CIKTI}/c1cell_2024_geometri_kirpim_kutulari.json"
VARSAYILAN_ANAHTAR = f"{CIKTI}/c1cell_2024_geometri_cevap_anahtari.json"
KAYNAK_ADI = "C1CELL 2024 TYT-AYT Geometri Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
GEO_KOK_KODU = "GEO"
KOD_ONEKI = "GEO-C1C24"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/c1cell_geo_ithal.py"
CROP_ONEK = "C1CELLGEO_2024"
KART = (591, 46, 1329, 1014)
TELIF_NOTU = (
    "C1CELL Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
    "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "FERNUS okuyucu ekran goruntusunden okuma hatti. Cevaplar KITABIN birim "
    "sonu cevap seridinden alindi; UC BAGIMSIZ kanal (ben + iki ajan) 163 "
    "seritte 1770 cevap okudu, uyusmayan hucreler yuksek buyutmede hakem "
    "okumasiyla karara baglandi ve son durumda uyusmazlik kalmadi. Sorular "
    "cozulmedi. Kirpim kutulari okuyucu simgesinden turetildi ve dort "
    "yapisal kapidan (sayi, serit sizintisi, ortusme/kisa kutu, murekkep) "
    "gecti. Tasiyici kapi: her birimde simge sayisi cevap sayisina esit "
    "(163/163). Transkripsiyon 12 ajanla soru-granulerliginde yapildi. "
    "Detay: veriseti/zkitap/cikti/GEO_C1CELL_2024_KESIF.md"
)
ANAHTAR_DOGRULAMASI = (
    "birim_sonu_cevap_seridi_uc_kanal_1770_1770_uyumlu__"
    "birim_simge_sayisi_esittir_cevap_sayisi_163_163__"
    "basili_numara_esittir_birim_ici_sira_1770_1770"
)
CEVAP_KAYNAGI = "birim_sonu_cevap_seridi"
KIRPIM_SISTEMI = "sayfa_karti_591_46_1329_1014"
BEKLENEN_SORU = 1770
BEKLENEN_BIRIM = 163


def _bolum_kodu(kod: str) -> str:
    """GEO-C1C24-B01-03 -> GEO-C1C24-B01 (kod hiyerarsiyi kendisi tasir)."""
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
    if not (sec.get(r["cevap"]) or "").strip():
        # Anahtar sikkin METNI kaynakta okunamadi (uydurulmadi). Satir
        # silinmiyor: tam soru kirpimi gercek sikki tasiyor.
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
        # acil_geo_ithal.py ile ayni gerekce -- kirpim hatti metin hattindan
        # bagimsiz calisir, hash'i bilmez.
        "question_image_url": (
            f"{os.environ.get('CROP_IMAGE_DIR', 'd-dataset/output/crops')}/"
            f"{CROP_ONEK}/{r['gorsel']}"
            if kutu
            else None
        ),
        # Kitabin soru sayfalarinda cozum YOK; serit yalniz harf verir.
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
            "konu_kaynagi": "icindekiler_sayfa_araligi_birim_duzeyinde",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": int(r["sayfa"]),  # olculdu: ofset 0
            "sutun": r["sutun"],
            "sutun_ici_sira": r["sira"],
            "soru_no_basili": r["soru_no_basili"],
            "birim_no": r["birim"],
            "birim_ici_sira": r["birim_ici_sira"],
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
            "sinav_turu_kaynagi": "olculmedi_kitap_TYT-AYT_karisik",
            "metin_kaynagi": "soru_granulerliginde_gorsel_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_738x968",
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


def birim_konu_haritasi(veri: dict, harita: dict) -> dict[int, str]:
    """Her birime TEK konu kodu atar; birim iki konuya yayiliyorsa DURDURUR.

    NEDEN BIRIM DUZEYINDE: kitabin konu sinirlari sayfa araligi olarak
    basili; soru duzeyinde atama yapilsaydi bir birimin sorulari konu
    sinirinda ikiye bolunebilirdi (ayni testin sorulari farkli konularda).
    Olculdu ki 163 birimin 163'u tek bir konunun araliginda kaliyor --
    atama bu yuzden birimin sayfa KUMESI uzerinden dogrulanarak yapilir.
    """
    araliklar = [(k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]]
    birim_sayfa: dict[int, set[int]] = {}
    for s in veri["sorular"]:
        birim_sayfa.setdefault(int(s["birim"]), set()).add(int(s["sayfa"]))

    esleme: dict[int, str] = {}
    for birim in sorted(birim_sayfa):
        kodlar = set()
        for sayfa in birim_sayfa[birim]:
            bulunan = [kod for bas, son, kod in araliklar if bas <= sayfa <= son]
            if not bulunan:
                raise ValueError(
                    f"birim {birim}: sayfa {sayfa} hicbir konu araliginda degil"
                )
            kodlar.update(bulunan)
        if len(kodlar) != 1:
            raise ValueError(
                f"birim {birim}: sayfalari {len(kodlar)} konuya yayiliyor "
                f"{sorted(kodlar)} -- konu atamasi belirsiz, duruyorum"
            )
        esleme[birim] = kodlar.pop()
    return esleme


def satirlari_bagla(veri: dict, harita: dict, kutular: dict) -> list[dict[str, Any]]:
    """Metin veri setini konu haritasi ve kirpim kutulariyla birlestirir."""
    kutu = {
        f"s{b['sayfa']:04d}_{b['sutun']}_{b['sira']}.png": b["kirpim_kutusu"]
        for b in kutular["kutular"]
        if not b.get("ortulu")
    }
    birim_konu = birim_konu_haritasi(veri, harita)
    satir = []
    for s in veri["sorular"]:
        # Eksik sik anahtari `kayit_uret` icinde cig bir KeyError'a donusurdu;
        # kapinin mesaji yerine yigin izi okumak istemiyoruz.
        eksik = [h for h in "ABCDE" if h not in (s.get("sikler") or {})]
        if eksik:
            raise ValueError(f"{s['gorsel']}: sik anahtari eksik {eksik}")
        satir.append(
            {
                **s,
                "konu_kodu": birim_konu[int(s["birim"])],
                "kirpim_kutusu": kutu.get(s["gorsel"]),
            }
        )
    return satir


def _anahtar_caprazi(veri: dict, anahtar: dict) -> list[str]:
    """Metin satirlarinin cevabi ile ayri anahtar dosyasi celisiyor mu.

    Metin hatti (12 ajan) ile anahtar hatti (uc kanal + hakem) BAGIMSIZ
    yurudu. Ikisi celisirse hangisinin dogru oldugunu bu script bilemez;
    ithali durdurmak tek dogru davranis.
    """
    amap = {
        (int(a["birim"]), int(a["soru_no"])): a["cevap"] for a in anahtar["anahtar"]
    }
    hata = []
    for s in veri["sorular"]:
        anah = (int(s["birim"]), int(s["birim_ici_sira"]))
        if anah not in amap:
            hata.append(f"{s['gorsel']}: birim {anah[0]} soru {anah[1]} anahtarda yok")
        elif amap[anah] != s["cevap"]:
            hata.append(f"{s['gorsel']}: metin {s['cevap']} != anahtar {amap[anah]}")
    return hata


def _yapisal_kapilar(veri: dict, anahtar: dict, kutular: dict) -> list[str]:
    """Bu kitabin tasiyici sayimlari -- sessizce kayan bir satir olmasin."""
    hata = []
    sorular = veri["sorular"]
    if len(sorular) != BEKLENEN_SORU:
        hata.append(f"soru sayisi {len(sorular)} != {BEKLENEN_SORU}")
    birimler = {int(s["birim"]) for s in sorular}
    if len(birimler) != BEKLENEN_BIRIM:
        hata.append(f"birim sayisi {len(birimler)} != {BEKLENEN_BIRIM}")
    if len(anahtar["anahtar"]) != BEKLENEN_SORU:
        hata.append(f"anahtar sayisi {len(anahtar['anahtar'])} != {BEKLENEN_SORU}")
    kayan = [
        s["gorsel"]
        for s in sorular
        if int(s["soru_no_basili"]) != int(s["birim_ici_sira"])
    ]
    if kayan:
        hata.append(
            f"{len(kayan)} satirda basili numara birim ici siradan farkli: {kayan[:5]}"
        )
    # ORTULU YOK: bu kitabin ayirt edici garantisi. Bir kutu `ortulu`
    # isaretlenirse `satirlari_bagla` onu sessizce dusurur ve satir
    # gorselsiz ithal edilir -- 1519 soru sekilsiz anlamsiz oldugu icin
    # bu sessiz kayip kabul edilemez. Mutasyon testinde kacan tek delik
    # buydu; kapi buraya kondu.
    ortulu = [b for b in kutular["kutular"] if b.get("ortulu")]
    if ortulu:
        hata.append(f"{len(ortulu)} kutu ortulu isaretli; C1CELL'de ortulu soru YOK")
    if len(kutular["kutular"]) != BEKLENEN_SORU:
        hata.append(f"kutu sayisi {len(kutular['kutular'])} != {BEKLENEN_SORU}")
    hata.extend(_anahtar_caprazi(veri, anahtar))
    return hata


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
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != CEVAP_KAYNAGI:
            hata.append(f"{k['id']}: taninmayan cevap kaynagi")
        if bool(pm["kirpim_kutusu"]) != bool(k["question_image_url"]):
            hata.append(f"{k['id']}: kutu ve gorsel yolu tutarsiz")
        if not k["question_image_url"]:
            # acil_geo_ithal.py'de kirpimsiz satir mesruydu (151 ortulu soru
            # veri setinden zaten cikarilmisti). Burada degil: metin hatti
            # 1770 satir verdiyse kirpim hatti da 1770 kutu vermeli.
            hata.append(f"{k['id']}: kirpim yok -- C1CELL'de her sorunun kutusu var")
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
            "0035_c1cellgeo_agac kosmadi mi? Kok dugume dusurup sessizce yanlis "
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


def _hazirla(yollar: dict[str, Path]) -> list[dict[str, Any]] | None:
    """Dosyalari okur, kapilardan gecirir, kayitlari uretir.

    Bir kapi tutarsa gerekceyi basar ve None doner; cagiran DURUR. DB'ye
    hicbir sey yazilmadan once bilinmesi gereken her sey buradadir.
    """
    veri = json.loads(yollar["veri"].read_text(encoding="utf-8"))
    harita = json.loads(yollar["harita"].read_text(encoding="utf-8"))
    kutular = json.loads(yollar["kutular"].read_text(encoding="utf-8"))
    anahtar = json.loads(yollar["anahtar"].read_text(encoding="utf-8"))

    yapisal = _yapisal_kapilar(veri, anahtar, kutular)
    if yapisal:
        print(f"DURDU: yapisal kapi {len(yapisal)} sorun buldu; ilk 10:")
        for h in yapisal[:10]:
            print("   ", h)
        return None
    print(
        f"yapisal kapi: {BEKLENEN_SORU} soru + {BEKLENEN_BIRIM} birim + "
        f"{BEKLENEN_SORU} anahtar + {BEKLENEN_SORU} kutu (ortulu 0) "
        "+ basili numara == birim ici sira + metin/anahtar caprazi -- TEMIZ"
    )

    satirlar = satirlari_bagla(veri, harita, kutular)
    print(f"veri setinde {len(satirlar)} soru (ortulu: {kutular.get('ortulu')})")
    if not satirlar:
        print("DURDU: ithal edilecek satir yok")
        return None

    kayitlar = [kayit_uret(r) for r in satirlar]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return None
    print(
        "on kontrol: 5 sik + dolu anahtar + dolu metin + GEO-C1C24 konu kodu "
        "+ birim sonu serit kaynagi + kutu/gorsel tutarliligi "
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
    p.add_argument("--anahtar", default=VARSAYILAN_ANAHTAR)
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
        "anahtar": Path(args.anahtar),
    }
    return ithal(yollar, args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
