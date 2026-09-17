#!/usr/bin/env python
"""Bilgi Sarmal TYT Turkce Soru Bankasi -- PASIF ithal.

KAYNAK VE TAVANI
----------------
Kaynak, kitabi gosteren bir okuyucu uygulamasinin 1920x1080 ekran
goruntuleridir (336 sayfa). PDF'te metin katmani YOK: her sayfa tek bir
gomulu JPEG ve o JPEG de 1920x1080 (olculdu). Sayfa karti goruntunun
icinde yalnizca 736x974 piksel yer kaplar; okuma bu cozunurlukte yapildi
(2x buyutulmus kirpim). Bu, kaynagin TAVANIDIR, hattin degil.

OKUYUCU SIMGESI ORTMESI -- BU KITABIN EN ONEMLI KUSURU
------------------------------------------------------
Okuyucu uygulamasi her sorunun soluna bir buyutec ve bir soru isareti
simgesi CIZER. Sag sutunun simgeleri tam olarak SOL sutunun satir
sonlarinin uzerine denk gelir ve oradaki harfleri KAPATIR.

Olcum (simge renkleri kitabin baskisinda hic gecmez; disk 240,238,247 ve
glif 69,39,160):

    1536 simge blogu bulundu
     619 tanesinin sol kenarina 0-3 px mesafede kitap murekkebi var
     451 SORU (1468'in %30.7'si) en az bir bolgesinde bu ortmeden etkileniyor
     12'lik rastgele orneklem yuksek buyutmede incelendi: 11'inde
       gercekten karakter kaybi var

Bu satirlarda okuyucu, ortulen parcayi BAGLAMDAN TAMAMLADI; yani metnin o
bolumu OKUNMUS degil, CIKARILMISTIR. Bu yuzden her satira
`pipeline_metadata.okuyucu_simgesi_ortmesi` yazilir ve bayrak listesine
`okuyucu_simgesi_ortmesi` eklenir. Aktiflestirme kapisi bu bayragi
disarida birakmalidir (urun sahibi karari; ithal PASIF oldugu icin bu
karar ertelenebilir).

Ayni yakalamanin ikinci kopyasi da (screenshots/"Bilgi Sarmal Tyt Turkce
Soru Bankasi 2022 2023") sayfa karti icinde PIKSEL PIKSEL AYNI cikti
(fark 0); kurtarma yolu yoktur.

CEVAP KAYNAGI
-------------
Tek cevap kaynagi kitabin kendi CEVAP ANAHTARIDIR (s332-336). Sorular
COZULMEDI. Anahtar iki bagimsiz okumayla cikarildi (farkli kirpim
geometrisi ve farkli olcek): 114 test blogu, 1468 cevap, FARK 0.

SIFIR SERBESTLIK DERECELI KAPILAR
---------------------------------
  * her testte numaralar 1..N kesintisiz          -> 114 testte 0 kusur
  * anahtardaki `Sayfa:` degerleri kitap boyunca
    kesintisiz artiyor                            -> 0 kusur
  * 114 testin sayfa araliklari 9-331'i tam kapliyor
    (bosluk yok, cakisma yok)                     -> 0 kusur
  * okunan soru sayisi == anahtardaki soru sayisi -> 114/114 test
  * kirmizi soru-numarasi imleci sayimi (metni hic
    gormeyen piksel kanali) ile okunan soru sayisi
    646 sutun yuvasinin 614'unde ayni             -> 32 sapma, hepsi
    aciklanabilir (simge numarayi ortmus ya da sag sutun okuma metni)
  * K1-K12 yapisal dogrulayici                    -> 1468 soruda 0 kusur

KONU AGACI
----------
0029 ile kurulur: 9 bolum (TUR-BS1..TUR-BS9) + 32 konu dugumu
(TUR-BS<n>-NN). Sarmal/OSYM/Simulasyon/Karma/Tarama gibi KARMA testler
konu dugumune degil kendi BOLUM dugumune baglanir; bunlar bir konuyu
degil bolumun tamamini tarar.

Detay: veriseti/zkitap/cikti/BILGI_SARMAL_TURKCE_YONTEM.md
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
VARSAYILAN_VERI = "veriseti/zkitap/cikti/bilgi_sarmal_turkce_sorular.json"
KAYNAK_ADI = "Bilgi Sarmal Tyt Turkce Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
TUR_KOK_KODU = "TUR"
# 0029 kodlari: TUR-BS1..TUR-BS9 ve TUR-BS<n>-NN. Desen 0025'in TUR-D*
# kodlarini KAPSAMAZ (TUR-BS onekini arar).
KOD_ONEKI = "TUR-BS"
SINAV_TURU = "TYT"
DERS_ALANI = "TURKCE"
# Olculdu: exam_type='TYT' satirlarinin cogunlugu grade_level=12; kardes
# kitap (Aktif Ogrenme Dilbilgisi) da 12 ile ithal edildi.
SINIF_DUZEYI = 12
ITHAL_ARACI = "scripts/kitap/bilgi_sarmal_turkce_ithal.py"
TELIF_NOTU = (
    "Bilgi Sarmal Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "Okuyucu uygulamasi ekran goruntusunden okuma hatti. Cevaplar kitabin "
    "kendi cevap anahtarindan (s332-336) IKI BAGIMSIZ okumayla alindi, "
    "fark 0; sorular cozulmedi. Test ici numara surekliligi 114 testte 0 "
    "kusur; anahtardaki sayfa numaralari kesintisiz artiyor; 114 testin "
    "sayfa araliklari 9-331'i tam kapliyor. Okunan soru sayisi anahtarla "
    "114/114 testte ayni. K1-K12 yapisal dogrulayici 1468 soruda 0 kusur. "
    "UYARI: okuyucu uygulamasinin buyutec simgesi sol sutunun satir "
    "sonlarini ortuyor; 451 soruda metnin bir bolumu baglamdan tamamlandi "
    "(okuyucu_simgesi_ortmesi bayragi). "
    "Detay: veriseti/zkitap/cikti/BILGI_SARMAL_TURKCE_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "kitap_sonu_anahtari_cift_okuma_fark_0__numara_surekliligi_114_test_0_kusur"
)


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler."""
    b: list[str] = sik_bayraklari(sec)
    if r.get("okuyucu_simgesi_ortmesi"):
        b.append("okuyucu_simgesi_ortmesi")
    if r.get("sekil_var"):
        b.append("gorsel_yok_sekilli")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_dizgi_kusuru")
    if r.get("konu_eslesme_duzeyi") == "bolum_karma_test":
        b.append("konu_bolum_duzeyinde")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
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
        "osym_year": None,
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
            "pozisyon": r.get("pozisyon"),
            "soru_no": r.get("soru_no"),
            "test_turu": r.get("test_konu"),
            "test_no": r.get("test_index"),
            "test_etiketi": r.get("test_etiketi"),
            "test_soru_sayisi": r.get("test_soru_sayisi"),
            "test_bas_sayfa": r.get("test_bas_sayfa"),
            "test_son_sayfa": r.get("test_son_sayfa"),
            "anahtar_sayfa": r.get("anahtar_sayfa"),
            "basili_test_rozeti": r.get("basili_test_rozeti"),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": "kitap_sonu_cevap_anahtari",
            "anahtar_cift_okuma": True,
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "cikmis_soru": False,
            "sinav_yili": None,
            "sekil_var": bool(r.get("sekil_var")),
            "gorsel_aciklama": r.get("gorsel_aciklama"),
            "gorsel_kaynagi": "yok_soru_kirpimi_uretilmedi",
            "sutun_gorseli": None,
            "numaralanmis_sozcukler": r.get("numaralanmis"),
            "alti_cizili": r.get("alti_cizili"),
            "kaynak_kusuru": r.get("kaynak_kusuru"),
            # Kitabin kusuru DEGIL: okuyucu uygulamasinin simgesi metni
            # ortuyor. Ayri alan, ayri bayrak.
            "okuyucu_simgesi_ortmesi": bool(r.get("okuyucu_simgesi_ortmesi")),
            "ortulen_bolge": int(r.get("ortulen_bolge") or 0),
            "metin_kaynagi": "sayfa_granulerliginde_gorsel_okuma",
            "metin_tavani": "kaynak_1920x1080_sayfa_karti_736x974",
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'TURKCE', %(grade_level)s,
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
            hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos (R5)")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        kod = k["konu_kodu"] or ""
        if not kod.startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {kod!r} {KOD_ONEKI}* degil")
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
        (TUR_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{TUR_KOK_KODU} kok konusu yok"
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
            "0029_bilgi_sarmal_agac kosmadi mi? Kok dugume dusurup sessizce "
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
        "on kontrol: 5 sik + dolu anahtar + dolu metin + TUR-BS konu kodu "
        "+ benzersiz hash -- TEMIZ"
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
