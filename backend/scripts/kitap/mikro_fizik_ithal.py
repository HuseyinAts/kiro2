#!/usr/bin/env python
"""Mikro Orijinal TYT Fizik Soru Bankasi 2025 -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren bir okuyucu uygulamasinin 1920x1080 ekran
goruntuleridir (400 sayfa). PDF'te metin katmani YOK. Sayfa karti
goruntunun icinde (596, 46)-(1324, 1014) = 728x968 piksel yer kaplar
(BU KITAP ICIN olculdu). Okuma 2x buyutulmus kirpimla yapildi.

CEVAP KAYNAGI: SAYFA ALTI CEVAP SERIDI
--------------------------------------
Bu kitapta anahtar her testin IKINCI (son) sayfasinin altinda duz basili;
serit o testin tum cevaplarini tasir. Sorular COZULMEDI.

Serit, metin hic okunmadan piksel duzeyinde bulundu: kutunun alt cerceve
cizgisi kart y=896'da, x 50-730 araliginda kesintisiz koyu kosu.

  * serit bulunan sayfa                              : 186
  * kitabin ICINDEKILER sayfasindan turetilen test    : 186
  * beklenen serit sayfasinda serit bulunmayan        : 0
  * beklenmeyen sayfada serit bulunan                 : 0
  * seritlerdeki magenta numara kumesi (girdi sayisi)  : 1326

Serit IKI BAGIMSIZ okumayla cikarildi (A: 4x olcek, 8'erli montaj, sayfa
sirasinda; B: 5x olcek, 6'sarli montaj, TERS sirada; okuyuculara girdi
sayisi SOYLENMEDI): iki okuma da 186 serit / 1326 cevap verdi ve
harf duzeyinde FARK 0. Okunan cevap sayisi piksel kanalinin girdi
sayisiyla da birebir ayni.

Her serit kirpimi sayfanin BASILI NUMARASINI da tasidigi icin sayfa
numarasi denetimi ayni okumadan geldi.

SIFIR SERBESTLIK DERECELI KAPILAR
---------------------------------
  * her seritte numaralar 1..N kesintisiz            -> 186 seritte 0 kusur
  * cevap harfleri A-E                               -> 0 kusur
  * okunan soru sayisi == serit girdisi              -> 186/186 test
  * K1-K12 yapisal dogrulayici                       -> 1326 satirda 0 kusur

GORSELLER -- TAM SORU KIRPIMI
-----------------------------
Sorularin %77'si sekil/grafik/tablo iceriyor ve sekil olmadan soru eksik
kalir. `question_image_url` TAM SORU KIRPIMIDIR (metin + sekil birlikte);
kirpim kutusu `pipeline_metadata.kirpim_kutusu`'nda saklanir ve gorseller
`scripts/kitap/mikro_fizik_kirp.py` ile PDF'ten yeniden uretilebilir.

KUTULAR LLM'E TAHMIN ETTIRILMEDI: okuyucu uygulamasinin her sorunun
soluna cizdigi buyutec simgesi piksel duzeyinde bulundu ve kutu
[simge ust - 6, sonraki simge ust - 9] olarak turetildi. Bir sutunda
simge sayisi o sutunda okunan soru sayisina ESIT DEGILSE o sutunun
sorulari kirpimsiz birakildi ve `gorsel_yok_sekilli` ile isaretlendi:
1326 sorunun 1247'sinde kutu uretildi, 79'unda uretilemedi (46 sutun
yuvasi). Sutun sinirlari sayfa basina sag sutun simgesinin x konumundan
turetilir; sabit sinir hem kirpiyor hem komsu sutundan harf sizdiriyordu
(goz kontrolu ile goruldu ve duzeltildi).

MUKERRER ADAYLARI ISARETLENDI, SILINMEDI
----------------------------------------
DB'deki FIZIK satirlarina karsi kelime kumesi ortusmesi >= 0.75 olan 34
soru bulundu (30'u `Neofizik TYT Fizik Soru Bankasi`, 4'u `OSYM 2025 TYT`).
Iki ornek gozle karsilastirildi: metin kelimesi kelimesine ayni, yani bu
sorular iki farkli yayinevinin kitabinda ayni sekilde basili. Bunlar
SILINMEDI; `pipeline_metadata.mukerrer_aday` ile hedef satirin id'si,
kitabi ve ortusme degeri yazildi -- birlestirme/eleme urun sahibinin
karari.

YAN BULGU: bu 34 sorunun 34'unde de DB'deki satirin cevabi bizim serit
okumamizla AYNI cikti; yani bagimsiz uretilmis iki kitap (ve 4 soruda
OSYM'nin kendi kitapciki) anahtari dogruladi.

KONU AGACI
----------
0032 ile kurulur: 11 bolum (FIZ-MO1..FIZ-MO11) + 49 konu dugumu. Bolumler
ve sayfa araliklari kitabin ICINDEKILER sayfasindan, konu adlari her
testin BASLIK BANDINDAN alindi. OSYM TARZI / OSYM TARZI ORIJINAL testleri
bir konuyu degil bolumun tamamini tarar; onlar bolum dugumune baglanir.

BILINEN BORC
------------
  * 79 soruda kirpim kutusu uretilemedi (`gorsel_yok_sekilli`).
  * 16 satirda kitabin KENDI dizgi kusuru isaretli.
  * 16 satirda okuyucu simgesi metni ortuyor; bu kitabin ikinci bir
    yakalamasi YOK, kurtarma kanali yok.
  * TAM ikinci transkripsiyon yapilmadi (cevap seridi icin yapildi).

Detay: veriseti/zkitap/cikti/MIKRO_FIZIK_TYT_YONTEM.md
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
VARSAYILAN_VERI = "veriseti/zkitap/cikti/mikro_fizik_tyt_sorular.json"
KAYNAK_ADI = "Mikro Orijinal TYT Fizik Soru Bankasi 2025"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-MO"
SINAV_TURU = "TYT"
DERS_ALANI = "FIZIK"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/mikro_fizik_ithal.py"
CROP_ONEK = "MIKRO_FIZIK_TYT"
TELIF_NOTU = (
    "Mikro Orijinal Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "Okuyucu uygulamasi ekran goruntusunden okuma hatti. Cevaplar KITABIN "
    "sayfa alti CEVAP SERIDINDEN alindi (her testin son sayfasinda), IKI "
    "BAGIMSIZ okuma (farkli olcek + farkli gruplama + ters sira) FARK 0; "
    "sorular cozulmedi. Serit sayisi (186) ve girdi sayisi (1326) metin hic "
    "okunmadan piksel kanaliyla da ayni cikti. Test ici numara surekliligi "
    "186 seritte 0 kusur; okunan soru sayisi 186/186 testte anahtarla ayni. "
    "K1-K12 yapisal dogrulayici 1326 satirda 0 kusur. Gorseller TAM SORU "
    "KIRPIMIDIR; kutular simge konumundan turetildi, 1247/1326 soruda "
    "uretilebildi. Detay: veriseti/zkitap/cikti/MIKRO_FIZIK_TYT_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "sayfa_alti_serit_cift_okuma_fark_0__serit_186_186_piksel_kanaliyla_"
    "ayni__numara_surekliligi_186_test_0_kusur"
)


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("okuyucu_simgesi_ortmesi"):
        b.append("okuyucu_simgesi_ortmesi")
    if r.get("sekil_var") and not r.get("kirpim_kutusu"):
        b.append("gorsel_yok_sekilli")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_dizgi_kusuru")
    if r.get("konu_eslesme_duzeyi") == "bolum":
        b.append("konu_bolum_duzeyinde")
    if r.get("mukerrer_aday"):
        b.append("mukerrer_aday")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    kutu = r.get("kirpim_kutusu")
    kayit_id = str(uuid.uuid5(uuid.NAMESPACE_OID, h))
    return {
        "id": kayit_id,
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        "question_image_url": (
            f"{os.environ.get('CROP_IMAGE_DIR', 'd-dataset/output/crops')}/"
            f"{CROP_ONEK}/{kayit_id}.png"
            if kutu
            else None
        ),
        # Kitabin soru sayfalarinda cozum YOK; serit yalnizca harf verir.
        "explanation": None,
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": None,
        "osym_format_compliant": False,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "bolum_kodu": r["bolum_kodu"],
            "bolum_no": r["bolum_no"],
            "konu_bandi": r["bolum_adi"],
            "konu": r.get("konu"),
            "konu_eslesme_duzeyi": r["konu_eslesme_duzeyi"],
            "konu_kaynagi": "icindekiler_ve_test_baslik_bandi",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": r.get("basili_sayfa"),
            "sutun": r.get("sutun"),
            "soru_no": r.get("soru_no"),
            "test_no": r.get("test_no"),
            "test_basligi": r.get("test_basligi"),
            "test_turu": r.get("test_turu"),
            "test_bas_sayfa": r.get("test_bas_sayfa"),
            "test_soru_sayisi": r.get("test_soru_sayisi"),
            "anahtar_sayfa": r.get("serit_sayfa"),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": "sayfa_alti_cevap_seridi",
            "anahtar_cift_okuma": True,
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "sekil_var": bool(r.get("sekil_var")),
            "sekil_aciklama": r.get("sekil_aciklama"),
            "kirpim_kutusu": kutu,
            "kirpim_gerekcesi": r.get("kirpim_gerekcesi"),
            "kirpim_koordinat_sistemi": "sayfa_karti_596_46_1324_1014",
            "gorsel_kaynagi": "tam_soru_kirpimi" if kutu else "yok_kutu_uretilemedi",
            "kaynak_kusuru": r.get("kaynak_kusuru"),
            "okuyucu_simgesi_ortmesi": bool(r.get("okuyucu_simgesi_ortmesi")),
            "ortulen_metin": r.get("ortulen_metin"),
            "mukerrer_aday": r.get("mukerrer_aday"),
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
    NULL, %(question_image_url)s, %(image_width)s, %(image_height)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'FIZIK', %(grade_level)s,
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
        pm = k["pipeline_metadata"]
        if pm["cevap_kaynagi"] != "sayfa_alti_cevap_seridi":
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
        (FIZ_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{FIZ_KOK_KODU} kok konusu yok"
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
            "0032_mikro_fizik_agac kosmadi mi? Kok dugume dusurup sessizce "
            "yanlis baglamaktansa duruyorum."
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


def ithal(veri_yolu: Path, dsn: str, yaz: bool) -> int:
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
        "on kontrol: 5 sik + dolu anahtar + dolu metin + FIZ-MO konu kodu "
        "+ serit kaynagi + kutu/gorsel tutarliligi + benzersiz hash -- TEMIZ"
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
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
