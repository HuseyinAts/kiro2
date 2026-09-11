#!/usr/bin/env python
"""Neofizik AYT Fizik Soru Bankasi 2025 -- OCR ciktisini question_bank'a PASIF ithal eder.

NEDEN PASIF VE is_ai_generated=TRUE (10 Eyl 2026)
------------------------------------------------
Bu satirlarin metni bir OCR/VLM hattindan geldi (kitabin PDF'inde metin katmani
yok; 336 sayfanin tamami 1920x1080 ekran goruntusu). Icerik insan gozuyle
onaylanmadan servis edilmemeli. Bu yuzden her satir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

ile yazilir. Servis kapisi (`v_safe_for_beta`, D9/D10) sozlesmesi geregi
`(is_ai_generated = false OR review_status = 'APPROVED')` ister; iki alan da
bu satirlari kapinin DISINDA tutar -- yani ithal, tek basina hicbir soruyu
ogrenciye ulastirmaz. Aktiflestirme ayri ve bilincli bir adimdir.

VERI NEREDEN GELIYOR
--------------------
`veriseti/zkitap/cikti/neofizik_2025_sorular_v2.json` (git disinda; bkz
.gitignore `veriseti/`). Uretim yontemi ve olcumleri ayni klasordeki
YONTEM.md'de: cift bagimsiz okuma + hakem turu + kitabin basili cevap
anahtariyla capraz dogrulama + cozerek dogrulama.

YALNIZ ONAYA_HAZIR SATIRLAR ITHAL EDILIR
----------------------------------------
Veri setindeki `inceleme_durumu` alani `INSAN_INCELEMESI` olan satirlar
(cevap anahtari basilmayan cikmis sorular, dusuk okuma uyumu olanlar)
BILEREK disarida birakilir -- cevabi olmayan soru ithal etmek, R5
(anahtar dolu bir sikka isaret etmeli) kuralinin ihlaline acik kapi birakir.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu
  (md5(lower(nfc(question_text))|A|B|C|D|E)) -- uq_qb_soru_hash_active uyumlu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: 0013 migration'inin kurdugu FIZ alt agaci
  (FIZ-NEO-B<n>-<KONU>); bulunamazsa FIZ koku.
- question_image_url = /static/crops/NEOFIZIK_2025/<id>.png
- pipeline_metadata: kaynak, bayraklar, gorsel varliklar, uretim kanitlari.

KULLANIM
--------
    python backend/scripts/kitap/neofizik_ithal.py --dsn postgresql://... [--yaz]
    (--yaz verilmezse yalnizca plan basilir)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
VARSAYILAN_VERI = "veriseti/zkitap/cikti/neofizik_2025_sorular_v2.json"
# Kanonik ad tek yerde durur (scripts/kitap/kaynak_sozlesmesi.py).
KAYNAK_ADI = "Neofizik AYT Fizik Soru Bankasi 2025"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
FIZ_KOK_KODU = "FIZ"
TELIF_NOTU = (
    "Neofizik Yayinlari, 2025. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "OCR/VLM hatti: cift bagimsiz okuma + uyusmazlikta hakem turu + kitabin "
    "basili cevap anahtariyla capraz dogrulama. Detay: veriseti/zkitap/cikti/YONTEM.md"
)


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t or "").strip()


def soru_hash(metin: str, secenekler: dict[str, str]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir."""
    payload = "|".join(
        [_nfc(metin).lower()] + [_nfc(secenekler.get(h, "")) for h in "ABCDE"]
    )
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def konu_kodu(bolum_no: int, konu: str) -> str:
    """0013 migration'inin urettigi kodla birebir ayni olmali.

    topic_hierarchy.code varchar(50) -- kesme siniri buradan geliyor.
    """
    slug = "".join(ch if ch.isalnum() else "-" for ch in konu.upper()).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return f"FIZ-NEO-B{bolum_no}-{slug}"[:50].rstrip("-")


def _kelime_istatistik(metin: str) -> tuple[int, int, float]:
    kelimeler = metin.split()
    if not kelimeler:
        return 0, 0, 0.0
    return (
        len(kelimeler),
        len(set(kelimeler)),
        sum(len(k) for k in kelimeler) / len(kelimeler),
    )


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = r["secenekler"]
    h = soru_hash(r["soru_metni"], sec)
    n, u, ort = _kelime_istatistik(r["soru_metni"])
    # Varlik dosyalari soru kirpimiyla ayni klasore dusuyor; metadata'ya
    # dogrudan servis edilebilir URL yazilir (uygulama /static/crops'u
    # CROP_IMAGE_DIR'e mount ediyor, bkz core/application.py).
    varliklar = []
    for i, v in enumerate(r.get("gorsel_varliklar", []), 1):
        ad = f"{r['id']}-{v['tur']}-{i}.png"
        varliklar.append(
            {"tur": v["tur"], "url": f"/static/crops/{ONEK}/{ad}", "kutu": v["kutu"]}
        )
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": konu_kodu(r["bolum_no"], r["konu"]),
        "question_text": r["soru_metni"],
        "secenekler": sec,
        "correct_answer": r["dogru_cevap"],
        "question_image_url": f"/static/crops/{ONEK}/{r['id']}.png",
        "source_page": r["sayfa"],
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "pipeline_metadata": {
            "kaynak": "neofizik_soru_bankasi",
            "kayit_id": r["id"],
            "bolum_no": r["bolum_no"],
            "bolum_adi": r["bolum_adi"],
            "konu": r["konu"],
            "test_no": r["test_no"],
            "soru_no": r["soru_no"],
            "bayraklar": r["bayraklar"],
            "cevap_kaynagi": r["cevap_kaynagi"],
            "gorsel_varliklar": varliklar,
            "kirpim_kutusu": r.get("kirpim_kutusu"),
            "metin_kaynagi": r["metin_kaynagi"],
            "ikinci_okuma_uyumu": r.get("ikinci_okuma_uyumu"),
            "guven": r["guven"],
            "guven_etiketleri": r["guven_etiketleri"],
            "bagimsiz_cozum_uyumu": (r.get("bagimsiz_cozum") or {}).get(
                "anahtarla_uyum"
            ),
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": "scripts/kitap/neofizik_ithal.py",
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(konu_id)s, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
"""
_QC = """
INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, explanation, question_image_url)
VALUES (%(id)s, %(question_text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(e)s, %(correct_answer)s, NULL, %(question_image_url)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, 2, 'comprehension', 'AYT', 'FIZIK', 12, TRUE, NULL, %(source_book)s,
    %(source_page)s, %(pipeline_metadata)s::json, 0.5, %(word_count)s, %(unique_word_count)s,
    %(average_word_length)s, 50.0, 'PENDING')
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
    return hata


def _meta_yenile(conn: psycopg.Connection, eski: list[dict], yaz: bool) -> None:
    """Zaten yazilmis satirlarin gorsel referanslarini tazeler.

    Kirpim adlandirmasi degistiginde tum tabloyu silip yeniden yazmak yerine
    sadece pipeline_metadata + question_image_url guncellenir.
    """
    if not yaz:
        print(f"(--meta-guncelle plani: {len(eski)} satirin metadata'si yenilenecek)")
        return
    with conn.transaction():
        for k in eski:
            conn.execute(
                "UPDATE question_metadata SET pipeline_metadata = %(pm)s::json "
                "WHERE id = %(id)s",
                {
                    "id": k["id"],
                    "pm": json.dumps(k["pipeline_metadata"], ensure_ascii=False),
                },
            )
            conn.execute(
                "UPDATE question_content SET question_image_url = %(u)s WHERE id = %(id)s",
                {"id": k["id"], "u": k["question_image_url"]},
            )
    print(f"META GUNCELLENDI: {len(eski)} satir")


def ithal(veri_yolu: Path, dsn: str, yaz: bool, meta_guncelle: bool = False) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    hazir = [r for r in veri if r["inceleme_durumu"] == "ONAYA_HAZIR"]
    print(f"veri setinde {len(veri)} soru; ONAYA_HAZIR {len(hazir)}")
    if not hazir:
        print("DURDU: ithal edilecek ONAYA_HAZIR satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in hazir]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print("on kontrol: 5 sik + dolu anahtar + dolu metin -- TEMIZ")

    with psycopg.connect(dsn) as conn:
        kok = conn.execute(
            "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
            (FIZ_KOK_KODU,),
        ).fetchone()
        if not kok:
            print(f"DURDU: {FIZ_KOK_KODU} kok konusu yok")
            return 2
        konular: dict[str, str] = dict(
            conn.execute(
                "SELECT code, id FROM topic_hierarchy WHERE code LIKE 'FIZ-NEO-%'"
            ).fetchall()
        )
        eksik_konu = {k["konu_kodu"] for k in kayitlar} - set(konular)
        if eksik_konu:
            print(
                f"UYARI: {len(eksik_konu)} konu kodu yok (0013 migration kosmadi mi?); "
                f"bunlar FIZ koku ile yazilacak. Ornek: {sorted(eksik_konu)[:3]}"
            )
        for k in kayitlar:
            k["konu_id"] = konular.get(k["konu_kodu"], kok[0])

        # 11 Eyl 2026: burada KAYNAK AYRIMI YOKTU. soru_hash metin+5 sik
        # uzerinden hesaplandigi ve id = uuid5(soru_hash) oldugu icin ayni soru
        # resmi OSYM kitapciginda da varsa ID AYNI olur; ayrim olmadan
        # --meta-guncelle o yabanci satirin metadata'sini eziyordu (mikro geo
        # ithalinde tam olarak bu oldu, 2 OSYM satiri servis kapisindan dustu).
        # Ayrim artik ortak fonksiyonda: scripts/kitap/kaynak_sozlesmesi.py
        yeni, bizim, yabanci = ayristir(conn, kayitlar, KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)

        if meta_guncelle and bizim:
            _meta_yenile(conn, bizim, yaz)
        print(
            "konu dagilimi (ilk 6):",
            dict(Counter(k["pipeline_metadata"]["konu"] for k in yeni).most_common(6)),
        )
        print(
            "gorsel varligi olan:",
            sum(1 for k in yeni if k["pipeline_metadata"]["gorsel_varliklar"]),
        )
        print(
            "sik_bos bayrakli:",
            sum(1 for k in yeni if "sik_bos" in k["pipeline_metadata"]["bayraklar"]),
        )
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
                        "question_image_url": k["question_image_url"],
                    },
                )
                conn.execute(
                    _QM,
                    {
                        **k,
                        "source_book": KAYNAK_ADI,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})

        n, aktif, kapida = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s""",
            (KAYNAK_ADI,),
        ).fetchone()
        print(f"YAZILDI: {len(yeni)} yeni satir")
        print(
            f"DB'de {KAYNAK_ADI}: toplam {n}, is_active {aktif}, kapidan gecen {kapida}"
        )
        if aktif or kapida:
            print(
                "HATA: pasif ithal sozlesmesi bozuldu (aktif ya da kapidan gecen satir var)"
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
        help="var olan satirlarin pipeline_metadata/gorsel URL'sini yeniden yaz",
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz, args.meta_guncelle)


if __name__ == "__main__":
    raise SystemExit(main())
