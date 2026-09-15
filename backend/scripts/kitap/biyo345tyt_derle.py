#!/usr/bin/env python
"""345 TYT Biyoloji: OCR ciktisini (ocr_json/) tek veri setine derler.

NEDEN AYRI BIR DERLEME ADIMI
----------------------------
Bu kitabin gorsel hatti sayfa basina bir JSON uretiyor
(`temiz <kitap>/ocr_json/sayfa_XXXX.json`). Ev sozlesmesi ise ithal
araclarinin TEK bir veri setinden okumasi:
`veriseti/zkitap/cikti/<kitap>_sorular.json` (geo345, biyo345, mikro_geo).
Bu betik ikisini birlestirir; ithal araci OCR klasorunun ic yapisini hic
bilmez.

KONU: SAYFANIN KENDI BASLIK BANDINDAN
-------------------------------------
Sayfa JSON'unun `topic_title` alani kitabin sayfa ustundeki KONU BANDIDIR
(ICINDEKILER degil). Olcum (15 Eyl 2026, ocr_json/):
  * 219 soru sayfasinin 112'sinde bant var, 107'sinde yok.
  * Kanonlastirildiginda 14 farkli ad kaliyor
    ("ESEYLI VE ESEYSIZ UREME" ile "ESEYLI ve ESEYSIZ UREME" ayni bant).
  * Bu 14 ad sayfa sirasinda tam 14 KOSU olusturuyor -- hicbir konu ikinci
    kez acilmiyor. Okuyucuya beklenen kosu sayisi soylenmedi; denetimin
    serbestlik derecesi yok.
  * Bantsiz sayfalar bloklarin ARASINDA kaliyor ve "OSYM Tadinda Sorular /
    Orijinal Sorular / Karma Sorular / OSYM Kosesi" bolumleridir. Bir
    ONCEKI bloga ait olduklari 11 ornek sayfada soru metinleri okunarak
    dogrulandi (11/11): orn. s0047 enzim sorulari (onceki blok ENZIMLER),
    s0103 osmoz sorulari (onceki blok HUCRE ZARINDAN MADDE GECISLERI).

Blok sinirlari bu yuzden "bir sonraki blogun basindan onceki sayfa" diye
alinir. Blok metinleri BURAYA ELLE YAZILMAZ: her blogun bandi, o bloktaki
bantli sayfalardan OKUNUR; boylece veri seti kaynaktan turer.

BILINEN SINIR: SORU GORSELI YOK
-------------------------------
Bu hat sayfa ve SUTUN kirpimi uretti, soru kutusu uretmedi; veri setinde
kirpim kutusu YOKTUR. Bu yuzden `question_image_url` ithalde NULL kalir ve
sekil iceren 334 soru `sekil_var` bayragiyla isaretlenir. Sutun kirpiminin
dosya adi her kayitta `sutun_gorseli` olarak tasinir, boylece ileride bir
kutu tespit turu calistirilabilir.

KULLANIM
--------
    python backend/scripts/kitap/biyo345tyt_derle.py [--yaz]
    (--yaz verilmezse yalnizca ozet basilir)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path

KOK = Path("veriseti/zkitap/screenshots")
KITAP = "345 2025 Tyt Biyoloji Soru Bankas\u0131"
VARSAYILAN_CIKTI = "veriseti/zkitap/cikti/biyo345tyt_sorular.json"

# (ilk sayfa, son sayfa, agac kodu) -- 0022_biyo345tyt_konu_agaci ile ayni
# sira. Sinirlar: bantli sayfalarin olusturdugu 14 kosu, her blok bir
# sonraki blogun basindan onceki sayfaya kadar uzatilmis hali.
BLOKLAR: tuple[tuple[int, int, str], ...] = (
    (6, 17, "BIO-T1"),
    (18, 35, "BIO-T2"),
    (36, 49, "BIO-T3"),
    (50, 59, "BIO-T4"),
    (60, 69, "BIO-T5"),
    (70, 87, "BIO-T6"),
    (88, 107, "BIO-T7"),
    (108, 117, "BIO-T8"),
    (118, 141, "BIO-T9"),
    (142, 157, "BIO-T10"),
    (158, 173, "BIO-T11"),
    (174, 191, "BIO-T12"),
    (192, 212, "BIO-T13"),
    (213, 233, "BIO-T14"),
)


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t or "").strip()


def soru_hash(metin: str, secenekler: dict[str, str]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir."""
    payload = "|".join(
        [_nfc(metin).lower()] + [_nfc(secenekler.get(h, "")) for h in "ABCDE"]
    )
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def kanon_bant(ad: str | None) -> str | None:
    """Bant metnini buyuk-kucuk harf farkindan arindirir (TR duyarli)."""
    if not (ad or "").strip():
        return None
    t = unicodedata.normalize("NFC", ad).strip()
    t = t.replace("i", "\u0130").replace("\u0131", "I")
    return t.upper()


def blok_kodu(sayfa: int) -> str | None:
    for bas, son, kod in BLOKLAR:
        if bas <= sayfa <= son:
            return kod
    return None


def sayfalari_oku(js_dizin: Path) -> dict[int, dict]:
    sayfalar: dict[int, dict] = {}
    for f in sorted(js_dizin.glob("sayfa_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("questions"):
            sayfalar[int(f.stem.split("_")[1])] = d
    return sayfalar


def blok_bantlari(sayfalar: dict[int, dict]) -> dict[str, str]:
    """Her blogun ham bant metni -- ELLE YAZILMAZ, veriden okunur.

    Bir blokta birden cok yazim varsa (buyuk-kucuk harf) en sik goruleni
    alinir; hicbir bant yoksa blok kodu geri dondurulur (olmamali).
    """
    say: dict[str, Counter[str]] = {}
    for no, d in sayfalar.items():
        kod = blok_kodu(no)
        bant = (d.get("topic_title") or "").strip()
        if kod and bant:
            say.setdefault(kod, Counter())[bant] += 1
    out: dict[str, str] = {}
    for _bas, _son, kod in BLOKLAR:
        c = say.get(kod)
        out[kod] = c.most_common(1)[0][0] if c else kod
    return out


def kayitlar_uret(sayfalar: dict[int, dict]) -> list[dict]:
    bantlar = blok_bantlari(sayfalar)
    kayitlar: list[dict] = []
    for no in sorted(sayfalar):
        d = sayfalar[no]
        kod = blok_kodu(no)
        for q in d["questions"]:
            ops = q.get("options") or {}
            sec = {h: _nfc(ops.get(h, "")) for h in "ABCDE"}
            metin = _nfc(q.get("question_text") or "")
            h = soru_hash(metin, sec)
            sutun = q.get("column")
            kayitlar.append(
                {
                    "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
                    "soru_hash": h,
                    "question_text": metin,
                    "a": sec["A"],
                    "b": sec["B"],
                    "c": sec["C"],
                    "d": sec["D"],
                    "e": sec["E"],
                    "correct_answer": q.get("correct_answer"),
                    "sayfa": no,
                    "basili_sayfa": d.get("book_page_from_footer"),
                    "sutun": sutun,
                    "pozisyon": q.get("position_on_page"),
                    "soru_no": q.get("question_number_on_page"),
                    "konu_kodu": kod,
                    "konu_bandi": bantlar.get(kod or ""),
                    "sayfada_bant_var": bool((d.get("topic_title") or "").strip()),
                    "test_turu": d.get("test_category"),
                    "test_no": d.get("test_no"),
                    "sekil_var": bool(q.get("has_diagram")),
                    "cikmis": bool(q.get("is_real_exam_question")),
                    "sinav_yili": q.get("exam_year"),
                    "zorluk_tahmini": q.get("difficulty_estimate"),
                    "cevap_kaynagi": q.get("answer_source"),
                    "sutun_gorseli": (f"sayfa_{no:04d}_{sutun}.png" if sutun else None),
                    "cikarim_guveni": d.get("extraction_confidence"),
                }
            )
    return kayitlar


def _ozet(kayitlar: list[dict]) -> None:
    print("soru:", len(kayitlar))
    print("konu dagilimi:")
    for kod, adet in Counter(k["konu_kodu"] for k in kayitlar).most_common():
        ornek = next(k["konu_bandi"] for k in kayitlar if k["konu_kodu"] == kod)
        print(f"  {adet:5d}  {kod:9s}  {ornek}")
    print("test turu:", dict(Counter(k["test_turu"] for k in kayitlar)))
    print("sekil iceren:", sum(1 for k in kayitlar if k["sekil_var"]))
    print("cikmis:", sum(1 for k in kayitlar if k["cikmis"]))
    print("sinav yili dolu:", sum(1 for k in kayitlar if k["sinav_yili"]))
    print("cevap dagilimi:", dict(Counter(k["correct_answer"] for k in kayitlar)))
    print("benzersiz hash:", len({k["soru_hash"] for k in kayitlar}))
    print("konusuz kayit:", sum(1 for k in kayitlar if not k["konu_kodu"]))


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--kok", default=str(KOK))
    p.add_argument("--cikti", default=VARSAYILAN_CIKTI)
    p.add_argument("--yaz", action="store_true", help="veri setini yaz")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    js = Path(args.kok) / KITAP / f"temiz {KITAP}" / "ocr_json"
    if not js.is_dir():
        print(f"DURDU: OCR klasoru yok -> {js}")
        return 2
    sayfalar = sayfalari_oku(js)
    print(f"soru tasiyan sayfa: {len(sayfalar)}")
    kayitlar = kayitlar_uret(sayfalar)
    _ozet(kayitlar)
    if not args.yaz:
        print("(--yaz verilmedi; dosya yazilmadi)")
        return 0
    hedef = Path(args.cikti)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(".json.tmp")
    gecici.write_text(
        json.dumps(kayitlar, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    gecici.replace(hedef)  # atomik: tuketici yarim dosya gormez
    print(f"YAZILDI: {hedef} ({hedef.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
