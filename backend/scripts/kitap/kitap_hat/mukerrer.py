"""Mukerrer olcumu (Faz 5) -- profil gudumlu; acil2021tyt_mukerrer deseni.

NE OLCULUR
----------
1. Tam carpisma: kitabin sorularinin ortak `soru_hash`i x question_bank.
2. Kitap ici tekrar: ayni soru_hash; ve yakin cift (govde 3-gram Jaccard
   >= GUCLU_ESIK ve >= 3 ayni sik).
3. DB yakin aday: p.DERSLER (OSYM dahil) + bu kaynak adini ve eski hat
   adlarini tasiyan satirlar.
4. Eski hat: ayni kitabin eski aktarimi (p.ESKI_KAYNAKLAR). Her eski satir en
   yakin modern soruya baglanir; GUCLU eslesme = modern karsiligi var.

OLCU: govde normal bicimi (NFKC, kucuk, eksi tek '-', kesme/tirnak tek bicim,
<u> yok, bosluk/parantez/LaTeX/dolar/indis/us yok) karakter 3-gram Jaccard;
3-gram ters indeksiyle. Pozitif kontrol: her 50. govdenin bozulmus hali kendi
sorusuna >= GUCLU_ESIK baglanmali; baglanmazsa betik durur.

Betik ithalden ONCE kosulur (ithal oncesi durum kaydi).

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.mukerrer --profil K [--dsn ...]
"""

from __future__ import annotations

import argparse
import os
import re
import unicodedata
from types import ModuleType
from typing import Any

import psycopg

from scripts.kitap.kitap_hat import ortak
from scripts.kitap.metin_olcum import soru_hash

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
_KESME = re.compile("[`\u2019\u2018\u02bc\u00b4]")
_TIRNAK = re.compile("[\u201c\u201d]")


def nm(metin: str | None) -> str:
    """Formulu koruyan normal bicim."""
    t = unicodedata.normalize("NFKC", metin or "").lower().replace("\u0307", "")
    t = re.sub(r"<[^>]+>", "", t)
    t = _TIRNAK.sub('"', _KESME.sub("'", t))
    t = _EKSI.sub("-", t).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    onceki = None
    while onceki != t:
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


def boz(metin: str) -> str:
    t = metin.replace("'", "\u2019").replace('"', "\u201c")
    t = t.replace(" ", "  ")
    k = t.split("  ")
    if len(k) > 4:
        k[2] = f"<u>{k[2]}</u>"
    return "  ".join(k)


def bizim_sorular(p: ModuleType) -> list[dict[str, Any]]:
    anahtar = ortak.oku(p, "cevap_anahtari")["cevaplar"]
    cevap = {ortak.dosya_adi(c["birim"], c["soru"]): c["cevap"] for c in anahtar}
    out = []
    for s in ortak.oku(p, "metin")["sorular"]:
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
    ornek = biz[::50] if len(biz) >= 250 else biz[:: max(1, len(biz) // 5)]
    sonuc = []
    for b in ornek:
        j = jaccard(trigram(nm(boz(b["govde"]))), b["tg"])
        sonuc.append({"dosya": b["dosya"], "bozuk_3gram": round(j, 3)})
    if len(sonuc) < 5 or min(s["bozuk_3gram"] for s in sonuc) < GUCLU_ESIK:
        raise SystemExit(f"Pozitif kontrol basarisiz: {sonuc}")
    return sonuc


_DB_SORGU = """
select m.id, m.source_book, m.source_page, m.subject_area, qb.is_active, q.question_text,
       q.option_a, q.option_b, q.option_c, q.option_d, q.option_e, q.correct_answer
from question_metadata m join question_content q on q.id = m.id
left join question_bank qb on qb.id = m.id
where m.subject_area = any(%s) or m.source_book = any(%s)
"""


def db_adaylari(
    p: ModuleType,
    conn: psycopg.Connection,
    biz: list[dict[str, Any]],
    ind: dict[str, list[int]],
) -> tuple[int, list[dict[str, Any]], float]:
    satirlar = conn.execute(
        _DB_SORGU, (list(p.DERSLER), [p.KAYNAK_ADI, *p.ESKI_KAYNAKLAR])
    ).fetchall()
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
        dogru = sik["ABCDE".index(r[11])] if r[11] in tuple("ABCDE") else None
        bizde = [
            h for h, x in zip("ABCDE", b["sik"], strict=False) if dogru and x == dogru
        ]
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
                "db_dogrusu_bizde": bizde[0] if len(bizde) == 1 else None,
                "sik_sirasi_ayni": sik == b["sik"],
                "etiketli": bool(b["etiket"]),
                "bizim_cevap": b["cevap"],
            }
        )
    adaylar.sort(key=lambda a: (-a["govde_3gram"], a["dosya"], a["db_id"]))
    return len(satirlar), adaylar, round(en, 3)


def eski_hat(
    p: ModuleType,
    conn: psycopg.Connection,
    biz: list[dict[str, Any]],
    ind: dict[str, list[int]],
) -> list[dict[str, Any]]:
    satirlar = conn.execute(
        """select m.id, m.source_page, m.subject_area, qb.is_active, q.question_text, q.correct_answer,
                  m.source_book, q.option_a, q.option_b, q.option_c, q.option_d, q.option_e
           from question_metadata m join question_content q on q.id = m.id
           left join question_bank qb on qb.id = m.id
           where m.source_book = any(%s)
           order by m.source_book, m.source_page, m.id""",
        (list(p.ESKI_KAYNAKLAR),),
    ).fetchall()
    out = []
    for r in satirlar:
        tg = trigram(nm(r[4]))
        j, bi = en_yakin(tg, biz, ind) if len(tg) >= MIN_TRIGRAM else (0.0, -1)
        b = biz[bi] if bi >= 0 else {"dosya": None, "sik": [], "cevap": None}
        ayni = ayni_sik([nm(x) for x in r[7:12]], b["sik"])
        karsilik = j >= GUCLU_ESIK and ayni >= GUCLU_SIK
        out.append(
            {
                "db_id": str(r[0]),
                "db_kaynak": r[6],
                "basili_sayfa": r[1],
                "db_ders": r[2],
                "db_aktif": r[3],
                "db_cevap": r[5],
                "en_yakin_bizim": b["dosya"],
                "en_yakin_3gram": round(j, 3),
                "ayni_sik_sayisi": ayni,
                "modern_karsilik": karsilik,
                "bizim_cevap": b["cevap"],
            }
        )
    return out


def olc(p: ModuleType, dsn: str) -> dict[str, Any]:
    biz = bizim_sorular(p)
    kontrol = pozitif_kontrol(biz)
    ind = indeks(biz)
    tekrar, yakin, ic_en = kitap_ici(biz, ind)
    with psycopg.connect(dsn) as conn:
        hashler = [b["hash"] for b in biz]
        hash_dosya = {b["hash"]: b["dosya"] for b in biz}
        tam = conn.execute(
            "select soru_hash, id::text from question_bank where soru_hash = any(%s) order by 1, 2",
            (hashler,),
        ).fetchall()
        db_satiri, adaylar, db_en = db_adaylari(p, conn, biz, ind)
        eski = eski_hat(p, conn, biz, ind)
    guclu = [a for a in adaylar if a["guclu"]]
    return {
        "kaynak": p.KAYNAK_ADI,
        "arac": "backend/scripts/kitap/kitap_hat/mukerrer.py",
        "olcu": (
            f"govde normal bicimi karakter 3-gram Jaccard; GUCLU = 3-gram >= {GUCLU_ESIK} VE bes "
            f"sikkin >= {GUCLU_SIK}'u normal bicimde birebir; kayitta 3-gram >= {KAYIT_ESIK}. DB: "
            f"{'/'.join(p.DERSLER)} (OSYM dahil) + bu kaynak ve eski hat adlarini tasiyan satirlar."
        ),
        "soru_sayisi": len(biz),
        "osym_etiketli_soru": sum(1 for b in biz if b["etiket"]),
        "osym_etiketli_guclu_aday": sorted(
            {a["dosya"] for a in adaylar if a["guclu"] and a["etiketli"]}
        ),
        "pozitif_kontrol": kontrol,
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
                    "db_dogrusu_bizde",
                    "sik_sirasi_ayni",
                )
            }
            for a in adaylar
            if a["db_cevap"] != a["bizim_cevap"]
        ],
        "cevap_farki_sik_sirasi": sum(
            1
            for a in adaylar
            if a["db_cevap"] != a["bizim_cevap"]
            and a["db_dogrusu_bizde"] == a["bizim_cevap"]
        ),
        "cevap_farki_icerik": sorted(
            {
                (a["dosya"], a["db_id"])
                for a in adaylar
                if a["db_cevap"] != a["bizim_cevap"]
                and a["db_dogrusu_bizde"] != a["bizim_cevap"]
            }
        ),
        "eski_hat_ozet": {
            k: {
                "satir": sum(1 for e in eski if e["db_kaynak"] == k),
                "aktif": sum(1 for e in eski if e["db_kaynak"] == k and e["db_aktif"]),
                "modern_karsilik": sum(
                    1 for e in eski if e["db_kaynak"] == k and e["modern_karsilik"]
                ),
            }
            for k in p.ESKI_KAYNAKLAR
        },
        "eski_hat": eski,
        "farkli_soru_hash": len({b["hash"] for b in biz}),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profil", required=True)
    ap.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    veri = olc(p, args.dsn)
    ortak.yaz(p, "mukerrer_adaylari", veri, girinti=1)
    print(
        f"hash carpismasi {len(veri['db_tam_hash_carpismasi'])}, kitap ici "
        f"{len(veri['kitap_ici_ayni_hash'])}/{len(veri['kitap_ici_yakin'])} "
        f"(en {veri['kitap_ici_en_yuksek_3gram']}), db {veri['db_satiri']} satir, aday "
        f"{veri['aday_sayisi']}, guclu {veri['guclu_aday_sayisi']} (en {veri['db_en_yuksek_3gram']}), "
        f"eski hat {len(veri['eski_hat'])}"
    )
    print("eski hat ozet", veri["eski_hat_ozet"])
    print("cevap farki icerik", veri["cevap_farki_icerik"])


if __name__ == "__main__":
    main()
