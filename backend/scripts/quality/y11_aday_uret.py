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
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

# 12+ konu × 50 ≈ 600 aday. Sınır kör okuma kapasitesi (yukarıda gerekçeli).
KONU_BASI_TAVAN = 50

# AYT KONULARI (R2, 7 Eyl 2026). S239'da ICERIK OKUNARAK olculdu -- yargi
# `primary_topic_id`'de, metin regex'inde DEGIL (o katman 0 verip yaniltti).
# `exam_type='TYT'` etiketli dilimde bu kodlardan 179 soru cikti (26 metin +
# 96 konu kodu + 57 TRG/DIZ) ve canlidan geri silindi. Secici bunlari artik
# HIC secmez; silinenler geri gelmesin diye `--haric-dosya` da var.
AYT_KONU_KODLARI: frozenset[str] = frozenset(
    {"MAT.TRV", "MAT.INT", "MAT.LMT", "MAT.LOG", "MAT.TRG", "MAT.DIZ"}
)

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
    # TURKCE/TYT (7 Eyl 2026). Ayni kalite suzgeci + KONU KAPSAMI SUZGECI:
    # olculdu, `subject_area='TURKCE'` etiketli temiz dilimde 28 soru MAT.PRB /
    # KIM / GEN / COG konularina bagli (etiket hatasi). Konu kodu canlida da
    # var oldugu icin yukleyici bunlari SESSIZCE matematik konusu altina
    # yazardi; dilim TUR / TUR.* / TYT-TR-* ile sinirlandi.
    "tur_tyt": """
        SELECT qb.id::text AS id, qb.primary_topic_id::text AS konu, qb.soru_hash AS h
        FROM question_bank qb
        JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
        WHERE qb.exam_type = 'TYT' AND qb.subject_area = 'TURKCE'
          AND qb.quality_review_status = 'auto_judged_high' AND qb.is_active
          AND qb.question_image_url ~ '_q[0-9]+\\.png$'
          AND qb.correct_answer IN ('A','B','C','D','E')
          AND qb.option_e IS NOT NULL AND btrim(qb.option_e) <> ''
          AND (th.code = 'TUR' OR th.code LIKE 'TUR.%' OR th.code LIKE 'TYT-TR-%')
    """,
    # SOS/TYT (7 Eyl 2026). DIKKAT: bu dilim tek bir `subject_area` DEGIL, TYT
    # denemesinin "SOS" BOLUMU. Blueprint bolumu uc dersi birden kapsiyor
    # (TARIH 3474 + SOSYAL 958 + COGRAFYA 854 aktif) ve `generate-mock` de
    # bransi konu tablosunun subject_area'sindan {sosyal,tarih,cografya,...}
    # kumesiyle esliyor. Ders basina ayri dilim acmak bolumu yapay boler.
    # Konu kapsami suzgeci TUR'daki ile ayni gerekce: olculdu, temiz dilimde 10
    # soru FIZ/KIM/TUR/GEN konularina bagli (etiket hatasi) -- kapsam disi.
    "sos_tyt": """
        SELECT qb.id::text AS id, qb.primary_topic_id::text AS konu, qb.soru_hash AS h
        FROM question_bank qb
        JOIN topic_hierarchy th ON th.id = qb.primary_topic_id
        WHERE qb.exam_type = 'TYT'
          AND qb.subject_area IN ('TARIH', 'SOSYAL', 'COGRAFYA')
          AND qb.quality_review_status = 'auto_judged_high' AND qb.is_active
          AND qb.question_image_url ~ '_q[0-9]+\\.png$'
          AND qb.correct_answer IN ('A','B','C','D','E')
          AND qb.option_e IS NOT NULL AND btrim(qb.option_e) <> ''
          AND (th.code IN ('TAR', 'COG', 'SOS')
               OR th.code LIKE 'TAR0%' OR th.code LIKE 'TYT-TAR-%'
               OR th.code LIKE 'COG0%' OR th.code LIKE 'TYT-COG-%'
               OR th.code LIKE 'SOC0%')
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


def kirmizi_liste_oku(dosyalar: Iterable[Path]) -> set[str]:
    """Daha once REDDEDILMIS id'lerin birlesimi (sizdiran, AYT, silinen).

    Capraz-DB elemesi yalniz CANLIDA olani eler; kor okumada sizdirdigi icin
    hic yazilmayan ya da AYT diye geri silinen id canlida YOKTUR ve secici
    onu ikinci turda yeniden secerdi. Kirmizi liste o kapiyi kapatir.
    """
    idler: set[str] = set()
    for dosya in dosyalar:
        idler.update(
            s.strip() for s in dosya.read_text(encoding="utf-8").split() if s.strip()
        )
    return idler


def ayt_konu_idleri(
    konu_kodu: Mapping[str, str], kodlar: frozenset[str] = AYT_KONU_KODLARI
) -> set[str]:
    """Konu haritasi (id -> code) icinden AYT kodlu konu id'leri."""
    return {tid for tid, kod in konu_kodu.items() if kod in kodlar}


def kapsam_suz(
    ham: Iterable[tuple[str, str, str | None]],
    kaynak_kodu: Mapping[str, str],
    canli_kodlar: set[str],
) -> list[tuple[str, str, str | None]]:
    """Konusu canlida KODLA var olan adaylari birak (yukleyiciyle ayni olcut).

    Id ile olcmek UUID drift'inde yanlis-negatif verir: temp `TUR` ile canli
    `TUR` ayni kod, farkli id. Yukleyici kodla esledigi icin secici de kodla
    olcmeli; aksi halde alet, yukleyicinin kabul edecegi soruyu "kapsam disi"
    diye atar (TURKCE'de 673 soru, 7 Eyl 2026).
    """
    return [(i, k, h) for i, k, h in ham if kaynak_kodu.get(k) in canli_kodlar]


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
    # KAPSAM KODLA OLCULUR, ID ILE DEGIL (7 Eyl 2026, TURKCE olcumu).
    # Yukleyici konuyu KODLA esler (`y11_goc._canli_topic_id`); level-1 kokler
    # (MAT, TUR) canli ile temp'te AYNI KODU tasir ama FARKLI id'ye sahiptir
    # (UUID drift, y11_konu_seed.py docstring'i). Secici id ile olcunce TUR
    # kokundeki 673 soru "kapsam disi" cikti; oysa yukleyici hepsini kabul
    # ederdi. Olcum aleti yukleyiciyle AYNI dili konusmali.
    kaynak_kodu = {
        r["id"]: r["code"]
        for r in await kaynak.fetch("SELECT id::text AS id, code FROM topic_hierarchy")
    }
    canli_kodlar = {
        r["code"] for r in await hedef.fetch("SELECT code FROM topic_hierarchy")
    }
    canli_hash = {
        r["h"]
        for r in await hedef.fetch(
            "SELECT soru_hash AS h FROM question_bank WHERE soru_hash IS NOT NULL"
        )
    }
    return {
        "ham": ham,
        "kaynak_kodu": kaynak_kodu,
        "canli_kodlar": canli_kodlar,
        "canli_hash": canli_hash,
    }


async def _main(argv: Sequence[str] | None = None) -> int:
    import asyncpg  # yerel import: modül DB'siz de import edilebilsin

    ap = argparse.ArgumentParser(description="MAT/TYT aday secici")
    ap.add_argument("--dilim", required=True, choices=sorted(DILIMLER))
    ap.add_argument("--cikti", required=True, type=Path)
    ap.add_argument("--tavan", type=int, default=KONU_BASI_TAVAN)
    ap.add_argument(
        "--haric-dosya",
        action="append",
        type=Path,
        default=[],
        help="Daha once reddedilmis id listesi (tekrarlanabilir). R2+ icin ZORUNLU "
        "sayilmali: canlida olmayan ama reddedilmis id aksi halde geri gelir.",
    )
    a = ap.parse_args(argv)

    kaynak = await asyncpg.connect(dsn_coz("kiro2_temp"))
    hedef = await asyncpg.connect(dsn_coz("kiro2"))
    try:
        veri = await _topla(kaynak, hedef, a.dilim)
    finally:
        await kaynak.close()
        await hedef.close()

    ham = veri["ham"]
    kaynak_kodu: dict[str, str] = veri["kaynak_kodu"]
    kapsanan = kapsam_suz(ham, kaynak_kodu, veri["canli_kodlar"])
    ayt_idler = ayt_konu_idleri(kaynak_kodu)
    ayt_elenen = sum(1 for _, k, _ in kapsanan if k in ayt_idler)
    kapsanan = [(i, k, h) for i, k, h in kapsanan if k not in ayt_idler]
    capraz = {i for i, _, h in kapsanan if h and h in veri["canli_hash"]}
    set_ici = set_ici_mukerrer([(i, h) for i, _, h in kapsanan])
    kirmizi = kirmizi_liste_oku(a.haric_dosya)
    kirmizi_elenen = {i for i, _, _ in kapsanan if i in kirmizi}
    haric = haric_kumesi(set_ici, capraz) | kirmizi_elenen
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
    print(f"konu kapsami disi elenen  : {len(ham) - len(kapsanan) - ayt_elenen}")
    print(f"AYT konusu elenen         : {ayt_elenen}")
    print(f"set-ici mukerrer elenen   : {len(set_ici)}")
    print(f"capraz-DB elenen          : {len(capraz)}")
    print(f"kirmizi liste elenen      : {len(kirmizi_elenen)}  (liste: {len(kirmizi)})")
    print(f"haric BIRLESIM            : {len(haric)}")
    print(f"tavan oncesi kalan        : {len(kalan)}")
    print(
        f"SECILEN                   : {len(secilen)}  ({len({k for _, k in secilen})} konu)"
    )
    print(f"cikti                     : {a.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
