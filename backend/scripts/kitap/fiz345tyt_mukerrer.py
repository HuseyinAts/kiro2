#!/usr/bin/env python
"""345 2025 TYT Fizik: mukerrer olcumu (Faz 5; stm345_mukerrer deseni).

NE OLCULUR
----------
1. Tam carpisma: 1397 sorunun ortak `soru_hash`i (metin_olcum) x tum
   question_bank.soru_hash.
2. Kitap ici tekrar: ayni soru_hash; ve yakin cift (govde 3-gram
   Jaccard >= GUCLU_ESIK ve >= 3 ayni sik).
3. DB yakin aday: FIZIK (OSYM FIZIK satirlari dahil) + bu kaynak adini
   tasiyan satirlar (ithal oncesi: eski hat).

OLCU
----
Formulu koruyan normal bicim (STM345'te matematik icin kuruldu; fizikte de
birim, indis ve us tasiyan govdeler kelime kumesinde kaybolur): NFKC,
kucuk harf, eksi tek '-', bosluk / parantez / LaTeX komutu / dolar / alt
indis '_' / us '^' / vektor oku silinmis govdenin karakter 3-gram Jaccard'i.
Pozitif kontrol: kesirli ve eksili govdelerin LaTeX'e cevrilmis, indisleri
`_{}` ile sarilmis, bosluklari bozulmus hali kendi sorusuna >= GUCLU_ESIK
baglanmak ZORUNDA; baglanmazsa betik durur.

HIZ
---
1397 x ~4800 cift dogrudan Jaccard yerine 3-gram ters indeksi: her satir
icin ortak 3-gram sayisi sayilir, Jaccard = ortak / (|a| + |b| - ortak).
Sonuc dogrudan hesapla ayni (test: rastgele ciftlerde esitlik).

ITHAL ONCESI OLCUM
------------------
Betik ithalden (Faz 6) ONCE kosulur; sonuc dosyasi ithal oncesi durumu
kaydeder.

KULLANIM
--------
    python backend/scripts/kitap/fiz345tyt_mukerrer.py [--dsn ...]
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
ONEK_DOSYA = CIKTI / "345_2025_tyt_fizik"
METIN = Path(f"{ONEK_DOSYA}_metin.json")
ANAHTAR = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
HEDEF = Path(f"{ONEK_DOSYA}_mukerrer_adaylari.json")
KAYNAK_ADI = "345 2025 TYT Fizik Soru Bankasi"
VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
ADAY_ESIK = 0.6
GUCLU_ESIK = 0.9
GUCLU_SIK = 3
KAYIT_ESIK = 0.75
MIN_TRIGRAM = 8
_EKSI = re.compile("[\u2212\u2013\u2014]")
_KESIR = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
_SIL = re.compile(r"[\s$\\{}()\[\]_^\u20d7]")


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
    t = re.sub(r"_(\w)", r"_{\1}", t)
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


def indeks(biz: list[dict[str, Any]]) -> dict[str, list[int]]:
    ind: dict[str, list[int]] = {}
    for i, b in enumerate(biz):
        for g in b["tg"]:
            ind.setdefault(g, []).append(i)
    return ind


def ortaklar(tg: frozenset[str], ind: dict[str, list[int]]) -> dict[int, int]:
    say: dict[int, int] = {}
    for g in tg:
        for i in ind.get(g, ()):
            say[i] = say.get(i, 0) + 1
    return say


def en_yakin(
    tg: frozenset[str], biz: list[dict[str, Any]], ind: dict[str, list[int]]
) -> tuple[float, int]:
    """(en yuksek Jaccard, indeks); ortak 3-gram yoksa (0.0, -1)."""
    en, ei = 0.0, -1
    for i, o in ortaklar(tg, ind).items():
        j = o / (len(tg) + len(biz[i]["tg"]) - o)
        if j > en or (j == en and ei >= 0 and i < ei):
            en, ei = j, i
    return en, ei


def kitap_ici(
    biz: list[dict[str, Any]], ind: dict[str, list[int]]
) -> tuple[list[list[str]], list[dict[str, Any]], float]:
    gruplar: dict[str, list[str]] = {}
    for b in biz:
        gruplar.setdefault(b["hash"], []).append(b["dosya"])
    tekrar = [v for v in gruplar.values() if len(v) > 1]
    yakin, en = [], 0.0
    for i, a in enumerate(biz):
        for k, o in ortaklar(a["tg"], ind).items():
            if k <= i:
                continue
            b = biz[k]
            j = o / (len(a["tg"]) + len(b["tg"]) - o)
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
where m.subject_area = 'FIZIK' or m.source_book = %s
"""


def db_adaylari(
    conn: psycopg.Connection, biz: list[dict[str, Any]], ind: dict[str, list[int]]
) -> tuple[int, list[dict[str, Any]], float]:
    satirlar = conn.execute(_DB_SORGU, (KAYNAK_ADI,)).fetchall()
    adaylar, en = [], 0.0
    for r in satirlar:
        tg = trigram(nm(r[5]))
        if len(tg) < MIN_TRIGRAM:
            continue
        j, bi = en_yakin(tg, biz, ind)
        en = max(en, j)
        if j < KAYIT_ESIK:
            continue
        b = biz[bi]
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
                "db_aktif": r[4],
                "db_cevap": r[11],
                "etiketli": bool(b["etiket"]),
                "bizim_cevap": b["cevap"],
            }
        )
    adaylar.sort(key=lambda a: (-a["govde_3gram"], a["dosya"], a["db_id"]))
    return len(satirlar), adaylar, round(en, 3)


def eski_hat(
    conn: psycopg.Connection, biz: list[dict[str, Any]], ind: dict[str, list[int]]
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
        j, bi = en_yakin(tg, biz, ind)
        b = biz[bi] if bi >= 0 else {"dosya": None}
        out.append(
            {
                "db_id": str(r[0]),
                "basili_sayfa": r[1],
                "db_ders": r[2],
                "db_aktif": r[3],
                "db_cevap": r[5],
                "db_govde": r[4],
                "sayfada_goz": "SAYFA INCELENMEDI",
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
    ind = indeks(biz)
    tekrar, yakin, ic_en = kitap_ici(biz, ind)
    with psycopg.connect(args.dsn) as conn:
        hashler = [b["hash"] for b in biz]
        hash_dosya = {b["hash"]: b["dosya"] for b in biz}
        tam = conn.execute(
            "select soru_hash, id::text from question_bank where soru_hash = any(%s) order by 1, 2",
            (hashler,),
        ).fetchall()
        db_satiri, adaylar, db_en = db_adaylari(conn, biz, ind)
        eski = eski_hat(conn, biz, ind)
    guclu = [a for a in adaylar if a["guclu"]]
    veri = {
        "kaynak": KAYNAK_ADI,
        "arac": "backend/scripts/kitap/fiz345tyt_mukerrer.py",
        "olcu": (
            f"govde normal bicimi (bosluksuz, eksi tek '-', LaTeX/parantez/dolar/indis/us/vektor oku yok) karakter 3-gram "
            f"Jaccard; GUCLU = 3-gram >= {GUCLU_ESIK} VE bes sikkin >= {GUCLU_SIK}'u normal bicimde "
            f"birebir; kayitta 3-gram >= {KAYIT_ESIK}. DB: FIZIK (OSYM dahil) + bu kaynak adini "
            "tasiyan satirlar. 3-gram ters indeksiyle (docstring)."
        ),
        "soru_sayisi": len(biz),
        "osym_etiketli_soru": sum(1 for b in biz if b["etiket"]),
        "osym_etiketli_guclu_aday": sorted(
            {a["dosya"] for a in adaylar if a["guclu"] and a["etiketli"]}
        ),
        "pozitif_kontrol": kontrol,
        # Hash degeri yazilmaz (detect-secrets); carpisan sorumuz + DB id.
        "db_tam_hash_carpismasi": [
            {"dosya": hash_dosya[t[0]], "db_id": t[1]} for t in tam
        ],
        "kitap_ici_ayni_hash": tekrar,
        "kitap_ici_yakin": yakin,
        "kitap_ici_en_yuksek_3gram": ic_en,
        "db_satiri": db_satiri,
        "db_en_yuksek_3gram": db_en,
        "aday_sayisi": len(adaylar),
        "guclu_aday_sayisi": len(guclu),
        "adaylar": adaylar,
        # Ayni (ya da cok yakin) soru baska kaynakta farkli cevapla: bilgi
        # kaydi. Bizim cevap kitabin BASILI anahtaridir; degistirilmez.
        "cevap_farki": [
            {
                k: a[k]
                for k in (
                    "dosya",
                    "db_id",
                    "db_kaynak",
                    "db_cevap",
                    "bizim_cevap",
                    "govde_3gram",
                    "guclu",
                )
            }
            for a in adaylar
            if a["db_cevap"] != a["bizim_cevap"]
        ],
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
