#!/usr/bin/env python
"""345 2025 AYT Fizik Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren bir okuyucu uygulamasinin 1920x1080 ekran
goruntuleridir (392 sayfa). PDF'te metin katmani YOK. Sayfa karti
goruntunun icinde (584, 42)-(1332, 1022) = 748x980 piksel yer kaplar
(BU KITAP ICIN olculdu; kardes Mikro Orijinal TYT Fizik'te 728x968 idi,
varsayilsaydi her kirpim kayardi). Okuma 2x buyutulmus kirpimla yapildi.

CEVAP KAYNAGI: HER SAYFANIN ALTINDA, SUTUN BASINA SATIR
-------------------------------------------------------
Bu kitapta anahtar kitabin sonunda ya da test sonunda DEGIL, her soru
sayfasinin altinda sutun basina ayri basili (ornek s87: solda "5.C 6.D",
sagda "7.D 8.E"). Kart koordinatinda y 892-897, kucuk gri punto.
Sorular COZULMEDI.

Satirlar IKI BAGIMSIZ okumayla cikarildi:

  * okuma A : 5x olcek, 12'serli montaj, sayfa sirasinda
  * okuma B : 7x olcek,  9'arli montaj, TERS sirada
  * okuyuculara hicbir sayfada kac girdi bekledigi SOYLENMEDI
  * ikisi de 382 sayfa / 1308 girdi buldu
  * harf duzeyinde uyusmazlik 5 sutun (hepsi B/E karismasi); besi de
    12x buyutmede gozle karara baglandi (B'nin alt kasesi kapali).

SIFIR SERBESTLIK DERECELI KAPILAR
---------------------------------
  * sayfa ici numara surekliligi (sol sutun bitince sag devam)  -> 382/382 sayfa, 0 kusur
  * sayfalar arasi gecis: ya "devam" ya "yeni test 1'den"       -> 379 gecisin hepsi, ucuncu durum yok
  * transkripsiyonun urettigi numaralar == cevap satiri         -> 686 sayfa/sutun, 0 fark
  * her testin iki sayfasi ayni bolumde                         -> 190/190 test
  * benzersiz soru_hash                                         -> 1308/1308

Yani soru sayisi (1308) ve test sayisi (190) BIRBIRINDEN BAGIMSIZ uc
kanaldan ayni cikti: iki cevap satiri okumasi + 32 ayri alt ajanin
yaptigi soru transkripsiyonu.

GORSELLER -- TAM SORU KIRPIMI
-----------------------------
Sorularin %77'si (1007) sekil/grafik/devre semasi iceriyor ve sekil
olmadan soru eksik kalir. `question_image_url` TAM SORU KIRPIMIDIR;
kutu `pipeline_metadata.kirpim_kutusu`'nda saklanir ve gorseller
`scripts/kitap/fiz345_kirp.py` ile PDF'ten yeniden uretilebilir.

Kutular LLM'e TAHMIN ETTIRILMEDI: okuyucunun her sorunun soluna cizdigi
buyutec simgesi piksel duzeyinde bulundu (glif 69,39,160 + lila disk
240,238,247; sayfa ustu susleme y<120 ve olcu disi bloklar elendi) ve
kutu [simge ust - 6, sonraki simge ust - 9] olarak turetildi. Bir
sutunda simge sayisi o sutunun cevap satiri girdisine ESIT DEGILSE o
sutunun sorulari kirpimsiz birakildi: 1295 kutu uretildi, 13 soruda
uretilemedi (7 sutun).

Kirpimlarin alt siniri cevap satirinin USTUNDE tutuldu; kirpimda cevap
gorunmez.

19 SORUDA SIKLAR METIN DEGIL
----------------------------
19 soruda A-E siklari grafik/diyagramdir; metin olarak basili degildir.
Bu satirlarda sik alanlarina `(gorsel sik)` yazildi ve `sikler_gorsel`
bayragi kondu -- siklar UYDURULMADI. Bu sorular ancak kirpim gorseliyle
birlikte gosterilebilir; 19'un 18'inde kirpim var. Kalan 1 satirda
(s27 sag 5) ne sik metni ne de kirpim var: satir SILINMEDI, ayrica
`gosterilemez_gorsel_sik_kirpimsiz` bayragiyla isaretlendi.

MUKERRER ADAYLARI ISARETLENDI, SILINMEDI
----------------------------------------
DB'deki FIZIK satirlarina karsi kelime kumesi ortusmesi >= 0.75 olan 11
soru bulundu (9'u `OSYM 2025 AYT` -- kitap zaten cikmis soru basiyor,
2'si `Neofizik AYT Fizik Soru Bankasi 2025`). 11'in 10'unda DB'deki
cevap bizim okumamizla AYNI. Tek catisma (s49 soru 3) gozle incelendi:
iki soru da "konum-zaman grafigine gore hiz-zaman grafigi" kalibinda,
govdeler farkli ve iki tarafta da siklar grafik -- ayni soru degil,
ayni kalip. Hash duzeyinde DB ile carpisma 0.

KONU AGACI
----------
0033 ile kurulur: 20 bolum (FIZ-345-B01..B20) + 40 konu dugumu.
Bolum adlari ve sayfa araliklari kitabin ICINDEKILER sayfasindan
(f3-f4), konu adlari her testin sayfa ustundeki BASLIK BANDINDAN
(190 testin 190'i okundu). Bandin adi bolum adiyla ayniysa ya da birden
cok bolumu kapsiyorsa (ornek "BIR ve IKI BOYUTTA HAREKET") soru BOLUM
dugumune baglanir: 1037 satir bolum, 271 satir konu duzeyinde.

BILINEN BORC
------------
  * 13 soruda kirpim kutusu uretilemedi (11'i sekilli).
  * 16 satirda okuyucu simgesi metni ortuyor; bu kitabin 2024 baskisi
    kurtarma kanali olarak KULLANILABILIR ama bu ithalde kullanilmadi.
  * 25 satirda kitabin KENDI basim kusuru isaretli.
  * TAM ikinci transkripsiyon yapilmadi (cevap satiri icin yapildi).
  * Kitap CIKMIS SORU kutularinda sinav yilini basiyor; yil alani
    sistematik cikarilmadi, `osym_year` NULL birakildi.

Detay: veriseti/zkitap/cikti/FIZ_345_AYT_YONTEM.md
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
VARSAYILAN_VERI = "veriseti/zkitap/cikti/345_ayt_fizik_sorular.json"
KAYNAK_ADI = "345 2025 AYT Fizik Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
FIZ_KOK_KODU = "FIZ"
KOD_ONEKI = "FIZ-345"
SINAV_TURU = "AYT"
DERS_ALANI = "FIZIK"
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/fiz345_ithal.py"
CROP_ONEK = "FIZ345_AYT"
TELIF_NOTU = (
    "345 Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni olmadan "
    "servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "Okuyucu uygulamasi ekran goruntusunden okuma hatti. Cevaplar KITABIN "
    "her sayfasinin altindaki, sutun basina basili CEVAP SATIRINDAN alindi; "
    "IKI BAGIMSIZ okuma (farkli olcek + farkli gruplama + ters sira) 382 "
    "sayfada 1308 girdi verdi, uyusmazlik 5 sutun ve hepsi gozle karara "
    "baglandi; sorular cozulmedi. Transkripsiyonun urettigi soru numaralari "
    "686 sayfa/sutunda cevap satiriyla BIREBIR ayni cikti. Sayfa ici numara "
    "surekliligi 382 sayfada 0 kusur. Gorseller TAM SORU KIRPIMIDIR; kutular "
    "simge konumundan turetildi, 1295/1308 soruda uretilebildi. Detay: "
    "veriseti/zkitap/cikti/FIZ_345_AYT_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "sayfa_alti_cevap_satiri_cift_okuma_fark_5_sutun_gozle_cozuldu__"
    "transkripsiyon_numaralariyla_686_686_ayni__sayfa_ici_sureklilik_0_kusur"
)


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("okuyucu_simgesi_ortmesi"):
        b.append("okuyucu_simgesi_ortmesi")
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
        # Kitabin soru sayfalarinda cozum YOK; satir yalnizca harf verir.
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
            "test_son_sayfa": r.get("test_son_sayfa"),
            "anahtar_sayfa": int(r["sayfa"]),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": "sayfa_alti_cevap_satiri",
            "anahtar_cift_okuma": True,
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "sekil_var": bool(r.get("sekil_var")),
            "sekil_aciklama": r.get("sekil_aciklama"),
            "sikler_gorsel": bool(r.get("sikler_gorsel")),
            "kirpim_kutusu": kutu,
            "kirpim_gerekcesi": r.get("kirpim_gerekcesi"),
            "kirpim_koordinat_sistemi": "sayfa_karti_584_42_1332_1022",
            "gorsel_kaynagi": "tam_soru_kirpimi" if kutu else "yok_kutu_uretilemedi",
            "kaynak_kusuru": r.get("kaynak_kusuru"),
            "okuyucu_simgesi_ortmesi": bool(r.get("okuyucu_simgesi_ortmesi")),
            "ortulen_metin": r.get("ortulen_metin"),
            "mukerrer_aday": r.get("mukerrer_aday"),
            "metin_kaynagi": "sayfa_granulerliginde_gorsel_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_748x980",
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'AYT', 'FIZIK', %(grade_level)s,
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
        if pm["cevap_kaynagi"] != "sayfa_alti_cevap_satiri":
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
            "0033_fiz345_agac kosmadi mi? Kok dugume dusurup sessizce yanlis "
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
        "on kontrol: 5 sik + dolu anahtar + dolu metin + FIZ-345 konu kodu "
        "+ sayfa alti satir kaynagi + kutu/gorsel tutarliligi "
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
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
