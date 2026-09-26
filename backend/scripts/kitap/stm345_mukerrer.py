#!/usr/bin/env python
"""345 2025 Start Matematik: mukerrer ve eski hat olcumu (Faz 5).

NE OLCULUR
----------
1. Tam carpisma: 371 sorunun ortak `soru_hash`i (metin_olcum) x tum
   question_bank.soru_hash.
2. Kitap ici tekrar: ayni soru_hash; ve yakin cift (govde 3-gram
   Jaccard >= GUCLU_ESIK ve >= 3 ayni sik).
3. DB yakin aday: MATEMATIK + GEOMETRI + bu kitabin eski hat satirlari.

NEDEN KELIME JACCARD DEGIL
--------------------------
Paragraf/TYT deseninin olcusu (kelime kumesi Jaccard >= 0.75 + >= 3 ayni
sik) matematikte bos: govde kelimeleri kalip cumle ('islemin sonucu
kactir?'), formul kelime kumesine girmiyor; sik normalizasyonu eksiyi
bosluga cevirdigi icin '-2' ile '2' ayni sayiliyor ve 1..5 gibi siklar her
yerde ortusuyor. Olculdu: 369 aday / 111 'guclu', gozle hepsi farkli
formul. Bu betik formulu koruyan olcuyu kullanir: bosluksuz, eksi
isaretleri tek '-', LaTeX komutlari/parantez/dolar silinmis govdenin
karakter 3-gram Jaccard'i. Pozitif kontrol (ayni sorunun LaTeX'e
cevrilmis ve bosluklari bozulmus hali) esigin ustunde kalmak ZORUNDA;
kalmazsa betik durur.

ESKI HAT
--------
Bu kitabin adini tasiyan 3 eski satirin sayfalari (basili 194/203/209 =
dosya 195/204/210) gozle incelendi; ESKI_HAT_GOZ sayfada ne oldugunu
kaydeder. Oneri alanidir; pasife alma sahip karari.

ITHAL ONCESI OLCUM
------------------
Betik ithalden (Faz 6) ONCE kosulur: o anda bu kaynak adini tasiyan her
satir eski hattir. Ithalden sonra kosulursa kitabin kendi satirlari kendi
kendine aday olur; sonuc dosyasi ithal oncesi durumu kaydeder.

KULLANIM
--------
    python backend/scripts/kitap/stm345_mukerrer.py [--dsn ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import psycopg

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "backend"))

from scripts.kitap.metin_olcum import soru_hash  # noqa: E402

CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_start_matematik"
METIN = Path(f"{ONEK_DOSYA}_metin.json")
ANAHTAR = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
HEDEF = Path(f"{ONEK_DOSYA}_mukerrer_adaylari.json")
KAYNAK_ADI = "345 2025 Start Matematik"
VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
ADAY_ESIK = 0.6
GUCLU_ESIK = 0.9
GUCLU_SIK = 3
KAYIT_ESIK = 0.75
MIN_TRIGRAM = 8
ESKI_HAT_GOZ = {
    194: (
        "Dosya 195: '0'dan Basla 3 -- Iki Bilinmeyenli Denklemler'; ogretici "
        "ornek + 1-6 denklem sistemi alistirmasi ve bir Isindirma Kosesi "
        "(terazi) sorusu. Dortgen alani / formul sorusu YOK."
    ),
    203: (
        "Dosya 204: '0'dan Basla 1 -- Basit Esitsizlikler'; 9-16 sayi dogrusu "
        "aralik alistirmalari, ogretici ornekler, cevap anahtari. Ortalama / "
        "seri sorusu YOK."
    ),
    209: (
        "Dosya 210: '0'dan Basla 4 -- Basit Esitsizlikler'; 7-11 aralik "
        "alistirmalari, Isindirma Kosesi 12 (ok tablosu), cevap anahtari. "
        "'a + b = 10 ve a - b = 2' sorusu YOK."
    ),
}
_EKSI = re.compile("[\u2212\u2013\u2014]")
_KESIR = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
_SIL = re.compile(r"[\s$\\{}()\[\]]")


def nm(metin: str | None) -> str:
    """Formulu koruyan normal bicim: NFKC, kucuk, eksi tek '-', bosluk/parantez/LaTeX yok."""
    t = unicodedata.normalize("NFKC", metin or "").lower().replace("\u0307", "")
    t = re.sub(r"<[^>]+>", "", t)
    t = _EKSI.sub("-", t).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    onceki = None
    while onceki != t:  # ic ice kesir: en icteki once
        onceki, t = t, _KESIR.sub(r"(\1)/(\2)", t)
    for eski, yeni in (
        ("\\cdot", "\u00b7"),
        ("\\frac", ""),
        ("\\sqrt", "\u221a"),
        ("\\left", ""),
        ("\\right", ""),
    ):
        t = t.replace(eski, yeni)
    return _SIL.sub("", t)


def trigram(metin: str) -> frozenset[str]:
    return frozenset(metin[i : i + 3] for i in range(len(metin) - 2))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def ayni_sik(a: list[str], b: list[str]) -> int:
    return sum(1 for x in a if x and x in b)


def latekse(metin: str) -> str:
    """Pozitif kontrol: 'p/q' -> '$\\frac{p}{q}$', U+2212 -> '-', bosluklar ikiye."""
    t = re.sub(r"(\w+)/(\w+)", r"$\\frac{\1}{\2}$", metin)
    return _EKSI.sub("-", t).replace(" ", "  ")


def bizim_sorular() -> list[dict[str, Any]]:
    anahtar = json.loads(ANAHTAR.read_text("ascii"))["cevaplar"]
    cevap = {f"{c['birim']}_{c['soru']:02d}": c["cevap"] for c in anahtar}
    out = []
    for s in json.loads(METIN.read_text("ascii"))["sorular"]:
        out.append(
            {
                "dosya": s["dosya"],
                "govde": s["govde"],
                "tg": trigram(nm(s["govde"])),
                "sik": [nm(s["sikler"][h]) for h in "ABCDE"],
                "cevap": cevap[s["dosya"]],
                "hash": soru_hash(s["govde"], s["sikler"]),
                "etiket": s["etiket"],
            }
        )
    return out


def kitap_ici(
    biz: list[dict[str, Any]],
) -> tuple[list[list[str]], list[dict[str, Any]], float]:
    gruplar: dict[str, list[str]] = {}
    for b in biz:
        gruplar.setdefault(b["hash"], []).append(b["dosya"])
    tekrar = [v for v in gruplar.values() if len(v) > 1]
    yakin, en = [], 0.0
    for i, a in enumerate(biz):
        for b in biz[i + 1 :]:
            j = jaccard(a["tg"], b["tg"])
            en = max(en, j)
            if j >= GUCLU_ESIK and ayni_sik(a["sik"], b["sik"]) >= GUCLU_SIK:
                yakin.append(
                    {"a": a["dosya"], "b": b["dosya"], "govde_3gram": round(j, 3)}
                )
    return tekrar, yakin, round(en, 3)


def pozitif_kontrol(biz: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Kesirli ve eksili govdelerin LaTeX'lesmis hali kendi sorusuna >= GUCLU_ESIK baglanmali."""
    ornek = [b for b in biz if "/" in b["govde"] and "\u2212" in b["govde"]]
    sonuc = []
    for b in ornek:
        j = jaccard(trigram(nm(latekse(b["govde"]))), b["tg"])
        sonuc.append({"dosya": b["dosya"], "latex_3gram": round(j, 3)})
    if len(sonuc) < 5 or min(s["latex_3gram"] for s in sonuc) < GUCLU_ESIK:
        raise SystemExit(f"Pozitif kontrol basarisiz: {sonuc}")
    return sonuc


_DB_SORGU = """
select m.id, m.source_book, m.source_page, m.subject_area, qb.is_active, q.question_text,
       q.option_a, q.option_b, q.option_c, q.option_d, q.option_e, q.correct_answer
from question_metadata m join question_content q on q.id = m.id
left join question_bank qb on qb.id = m.id
where m.subject_area in ('MATEMATIK', 'GEOMETRI') or m.source_book = %s
"""


def db_adaylari(
    conn: psycopg.Connection, biz: list[dict[str, Any]]
) -> tuple[int, list[dict[str, Any]], float]:
    satirlar = conn.execute(_DB_SORGU, (KAYNAK_ADI,)).fetchall()
    adaylar, en = [], 0.0
    for r in satirlar:
        tg = trigram(nm(r[5]))
        if len(tg) < MIN_TRIGRAM:
            continue
        j, b = max(((jaccard(tg, x["tg"]), x) for x in biz), key=lambda p: p[0])
        en = max(en, j)
        if j < KAYIT_ESIK:
            continue
        sik = [nm(x) for x in r[6:11]]
        ayni = ayni_sik(sik, b["sik"])
        adaylar.append(
            {
                "dosya": b["dosya"],
                "govde_3gram": round(j, 3),
                "ayni_sik_sayisi": ayni,
                "guclu": j >= GUCLU_ESIK and ayni >= GUCLU_SIK,
                "db_id": str(r[0]),
                "db_kaynak": r[1],
                "db_ders": r[3],
                "db_cevap": r[11],
                "bizim_cevap": b["cevap"],
            }
        )
    adaylar.sort(key=lambda a: (-a["govde_3gram"], a["dosya"], a["db_id"]))
    return len(satirlar), adaylar, round(en, 3)


def eski_hat(
    conn: psycopg.Connection, biz: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    satirlar = conn.execute(
        """select m.id, m.source_page, m.subject_area, qb.is_active, q.question_text, q.correct_answer
           from question_metadata m join question_content q on q.id = m.id
           left join question_bank qb on qb.id = m.id
           where m.source_book = %s
           order by m.source_page""",
        (KAYNAK_ADI,),
    ).fetchall()
    out = []
    for r in satirlar:
        tg = trigram(nm(r[4]))
        j, b = max(((jaccard(tg, x["tg"]), x) for x in biz), key=lambda p: p[0])
        out.append(
            {
                "db_id": str(r[0]),
                "basili_sayfa": r[1],
                "db_ders": r[2],
                "db_aktif": r[3],
                "db_cevap": r[5],
                "db_govde": r[4],
                "sayfada_goz": ESKI_HAT_GOZ.get(r[1], "SAYFA INCELENMEDI"),
                "kitapta_var": False,
                "en_yakin_bizim": b["dosya"],
                "en_yakin_3gram": round(j, 3),
                "oneri": "pasif (sahip karari)",
            }
        )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    args = p.parse_args()
    biz = bizim_sorular()
    kontrol = pozitif_kontrol(biz)
    tekrar, yakin, ic_en = kitap_ici(biz)
    with psycopg.connect(args.dsn) as conn:
        hashler = [b["hash"] for b in biz]
        tam = conn.execute(
            "select soru_hash, id::text from question_bank where soru_hash = any(%s) order by 1, 2",
            (hashler,),
        ).fetchall()
        db_satiri, adaylar, db_en = db_adaylari(conn, biz)
        eski = eski_hat(conn, biz)
    guclu = [a for a in adaylar if a["guclu"]]
    veri = {
        "kaynak": KAYNAK_ADI,
        "arac": "backend/scripts/kitap/stm345_mukerrer.py",
        "olcu": (
            f"govde normal bicimi (bosluksuz, eksi tek '-', LaTeX/parantez/dolar yok) karakter 3-gram "
            f"Jaccard; GUCLU = 3-gram >= {GUCLU_ESIK} VE bes sikkin >= {GUCLU_SIK}'u normal bicimde "
            f"birebir; kayitta 3-gram >= {KAYIT_ESIK}. DB: MATEMATIK + GEOMETRI + bu kitabin eski hat "
            "satirlari. Kelime Jaccard olcusu matematikte bos oldugu icin kullanilmadi (docstring)."
        ),
        "soru_sayisi": len(biz),
        "osym_etiketli_soru": sum(1 for b in biz if b["etiket"]),
        "pozitif_kontrol": kontrol,
        "db_tam_hash_carpismasi": [list(t) for t in tam],
        "kitap_ici_ayni_hash": tekrar,
        "kitap_ici_yakin": yakin,
        "kitap_ici_en_yuksek_3gram": ic_en,
        "db_satiri": db_satiri,
        "db_en_yuksek_3gram": db_en,
        "aday_sayisi": len(adaylar),
        "guclu_aday_sayisi": len(guclu),
        "adaylar": adaylar,
        "eski_hat": eski,
        # Hash degerleri yazilmaz (detect-secrets hex entropi); ithal yeniden hesaplar.
        "farkli_soru_hash": len({b["hash"] for b in biz}),
    }
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(
        f"hash carpismasi {len(tam)}, kitap ici {len(tekrar)}/{len(yakin)} (en {ic_en}), "
        f"db {db_satiri} satir, aday {len(adaylar)}, guclu {len(guclu)} (en {db_en}), eski hat {len(eski)}"
    )
    print("pozitif kontrol", kontrol)


if __name__ == "__main__":
    main()
