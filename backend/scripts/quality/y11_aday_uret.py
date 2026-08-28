#!/usr/bin/env python
"""MAT/TYT aday seçici — SQL dilimi parametre, KIMYA'ya bağımlı DEĞİL.

KIMYA adayları verdikt TSV'sinden gelir ve `y11_goc_kumesi_uret.py`'de durur;
oraya DOKUNULMAZ. `dict[str, str]` içine `None` koymak tip kirliliği olurdu.

KONU SÜZGECİ ZORUNLU
--------------------
`y11_goc._canli_topic_id()` bilinmeyen kodda `ValueError` fırlatır. 20 Ağu 2026
ölçümü: dilimin 5.420 satırından **871'inin** `primary_topic_id`'si canlı
`topic_hierarchy`'de YOK. Önceden elenmezse yükleyici parti ortasında düşer ve
TEK transaction olduğu için **hiçbir şey** yazılmaz.
⚠️ Eski plan bu sayıyı **386** diyordu — BAYAT. Ölçüm kazanır.

NEDEN KONU TAVANI
-----------------
Canlı dağılımda en büyük konu **975**, en küçüğü 43. Tavansız seçim 600'ün
yarısını tek konudan alırdı; A1 kriteri "konu kırılımını görür" diyor ve bu
tek kovadan karşılanamaz. Tavan konu başına `KONU_BASI_TAVAN`.

NEDEN ~600
----------
Sınır **kör okuma kapasitesi**: T3'te her crop tek tek gözle okunacak (OCR yok,
kullanıcı kararı 20 Ağu: *"ocr yok çok vakit kaybı oluyor"*; OCR'siz istatistiksel
dedektör de kör ölçüldü — KÖTÜ medyan 0,0690 < İYİ 0,0829). MAT-T1 bir turda
354 crop okudu. 600 okunabilir; 5.420 değil. A1 40 soru istiyor → ~14 kat marj.

DETERMİNİZM ZORUNLU
-------------------
`random` KULLANILMAZ ve sıralama `md5(id)` üzerinden yapılır. Nondeterministik
olsaydı PROVA'da ölçülen küme ile KALICI'da yazılan küme ayrışır, prova hiçbir
şey kanıtlamazdı. Postgres `ORDER BY`'sız sorguda satır sırasını garanti etmez,
bu yüzden seçim girdi sırasından da bağımsız olmalı.

Bekçi: `backend/tests/fast/test_y11_aday_uret.py`
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

# 12+ konu × 50 ≈ 600 aday. Sınır kör okuma kapasitesi (yukarıda gerekçeli).
KONU_BASI_TAVAN = 50

DILIMLER: dict[str, str] = {
    "mat_tyt": """
        SELECT id::text AS id, primary_topic_id::text AS konu, soru_hash AS h
        FROM question_bank
        WHERE exam_type = 'TYT' AND subject_area = 'MATEMATIK'
          AND quality_review_status = 'auto_judged_high' AND is_active
          AND question_image_url ~ '_q[0-9]+\\.png$'
          AND correct_answer IN ('A','B','C','D','E')
          AND option_e IS NOT NULL AND btrim(option_e) <> ''
    """,
}
# KIMYA BURAYA EKLENMEZ — bkz. modül docstring'i.


def _sira_anahtari(id_: str) -> str:
    """Deterministik sıralama anahtarı. `random` yerine `md5(id)`."""
    return hashlib.md5(id_.encode()).hexdigest()  # noqa: S324  # nosec B324


def haric_kumesi(set_ici: set[str], capraz: set[str]) -> set[str]:
    """BİRLEŞİM — çıkarma DEĞİL.

    İki küme örtüşebilir. KIMYA'da kesişim 0 ölçüldü ve naif çıkarma TESADÜFEN
    doğru çıktı; MAT'ta aynı şansı varsayma.
    """
    return set_ici | capraz


def konu_dengeli_sec(
    adaylar: Iterable[tuple[str, str]], *, tavan: int = KONU_BASI_TAVAN
) -> list[tuple[str, str]]:
    """Konu başına en fazla `tavan` aday — deterministik, girdi sırasından bağımsız.

    Tavanın ALTINDAKİ konular kırpılmaz; küçük konular da temsil edilsin.
    """
    kovalar: dict[str, list[tuple[str, str]]] = {}
    for id_, konu in adaylar:
        kovalar.setdefault(konu, []).append((id_, konu))
    secilen: list[tuple[str, str]] = []
    for konu in sorted(kovalar):
        sirali = sorted(kovalar[konu], key=lambda x: _sira_anahtari(x[0]))
        secilen.extend(sirali[:tavan])
    return sorted(secilen, key=lambda x: _sira_anahtari(x[0]))


def set_ici_mukerrer(satirlar: Iterable[tuple[str, str | None]]) -> set[str]:
    """Aynı `soru_hash`'i paylaşan satırlardan İLKİ hariç hepsini döndürür.

    İlk = `md5(id)` sırasına göre ilk. Hash'i NULL olan satır elenmez (kimlik
    iddiası yoktur; "yargılanmamışı silme" kuralı).
    """
    gruplar: dict[str, list[str]] = {}
    for id_, h in satirlar:
        if h:
            gruplar.setdefault(h, []).append(id_)
    fazla: set[str] = set()
    for idler in gruplar.values():
        if len(idler) > 1:
            fazla.update(sorted(idler, key=_sira_anahtari)[1:])
    return fazla


def dsn_coz(veritabani: str) -> str:
    """DSN'i ortamdan çözer. Parola KODA YAZILMAZ."""
    ozel = os.environ.get(f"KIRO2_DSN_{veritabani.upper()}")
    if ozel:
        return ozel
    kullanici = os.environ.get("PGUSER", "postgres")
    parola = os.environ.get("PGPASSWORD", "")
    sunucu = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5434")
    kimlik = f"{kullanici}:{parola}@" if parola else f"{kullanici}@"
    return f"postgresql://{kimlik}{sunucu}:{port}/{veritabani}"


async def _topla(kaynak: Any, hedef: Any, dilim: str) -> dict[str, Any]:
    """Kaynak + hedef okumaları. Ayrı fonksiyon: `_main` saf akış kalsın."""
    ham = [(r["id"], r["konu"], r["h"]) for r in await kaynak.fetch(DILIMLER[dilim])]
    canli_konu = {
        r["id"] for r in await hedef.fetch("SELECT id::text AS id FROM topic_hierarchy")
    }
    canli_hash = {
        r["h"]
        for r in await hedef.fetch(
            "SELECT soru_hash AS h FROM question_bank WHERE soru_hash IS NOT NULL"
        )
    }
    return {"ham": ham, "canli_konu": canli_konu, "canli_hash": canli_hash}


async def _main(argv: Sequence[str] | None = None) -> int:
    import asyncpg  # yerel import: modül DB'siz de import edilebilsin

    ap = argparse.ArgumentParser(description="MAT/TYT aday secici")
    ap.add_argument("--dilim", required=True, choices=sorted(DILIMLER))
    ap.add_argument("--cikti", required=True, type=Path)
    ap.add_argument("--tavan", type=int, default=KONU_BASI_TAVAN)
    a = ap.parse_args(argv)

    kaynak = await asyncpg.connect(dsn_coz("kiro2_temp"))
    hedef = await asyncpg.connect(dsn_coz("kiro2"))
    try:
        veri = await _topla(kaynak, hedef, a.dilim)
    finally:
        await kaynak.close()
        await hedef.close()

    ham = veri["ham"]
    kapsanan = [(i, k, h) for i, k, h in ham if k in veri["canli_konu"]]
    capraz = {i for i, _, h in kapsanan if h and h in veri["canli_hash"]}
    set_ici = set_ici_mukerrer([(i, h) for i, _, h in kapsanan])
    haric = haric_kumesi(set_ici, capraz)
    kalan = [(i, k) for i, k, _ in kapsanan if i not in haric]
    secilen = konu_dengeli_sec(kalan, tavan=a.tavan)

    # Sondaki newline ZORUNLU + newline="\n" ZORUNLU. Aksi halde `fix end of
    # files` ve `mixed line ending` kancalari dosyayi her commit'te duzeltir ve
    # ARAC CIKTISI ile COMMIT'LI ARTEFAKT ayrisir: seciciyi yeniden kosturan
    # herkes agaci kirli bulur, determinizm iddiasi da olculemez hale gelir.
    a.cikti.write_text(
        "".join(f"{i}\n" for i, _ in secilen), encoding="utf-8", newline="\n"
    )

    # SESSİZ ELEME YOK — her düşen sayı yazdırılır.
    print(f"ham aday                  : {len(ham)}")
    print(f"konu kapsami disi elenen  : {len(ham) - len(kapsanan)}")
    print(f"set-ici mukerrer elenen   : {len(set_ici)}")
    print(f"capraz-DB elenen          : {len(capraz)}")
    print(f"haric BIRLESIM            : {len(haric)}")
    print(f"tavan oncesi kalan        : {len(kalan)}")
    print(
        f"SECILEN                   : {len(secilen)}  ({len({k for _, k in secilen})} konu)"
    )
    print(f"cikti                     : {a.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
