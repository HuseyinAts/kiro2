#!/usr/bin/env python
"""Kitapsız (sentetik) soru havuzunu yedekleyip SİLER — TEK transaction.

NEDEN
-----
`question_bank` iki ayrı evren taşıyor ve ikisi **provenansla** birbirinden
kusursuz ayrılıyor (20 Ağu 2026 ölçümü, canlı `kiro2`):

    source_book IS NULL      36.967 / 36.967 eski parti     <- SENTETIK COP
    source_book IS NOT NULL       0 / 3.616  Y11 KIMYA      <- GERCEK ICERIK

Ayırıcı bir içerik sezgisi DEĞİL, kaynak kaydıdır: yanlış-pozitifi 0, yanlış-
negatifi 0. Ucuz içerik dedektörleri (görsel-atıf / boş şık / tekrar eden şık)
aynı kümenin yalnız **8.696**'sını yakalıyordu — yani tek başlarına kullanılsa
28.271 çöp havuzda kalır ve havuz "temizlenmiş" görünürdü.

Çöp olduğu ÖLÇÜLDÜ, varsayılmadı:

    S231 kapıdan okunan               40 / 40  servis edilemez
    S238 kitapsız havuzdan okunan     12 / 12  servis edilemez
    S238 adversarial (dedektörlerin "temiz" dediği alt küme, 12 ders x 15)
                                     180 / 180 çöp; 6 yargıç, "servis
                                     edilebilir" diyen her karar 3 mercekle
                                     çürütülecekti — hiç karar çıkmadı

TAHRIBAT YOK — ÖLÇÜLDÜ
----------------------
`question_bank.id`'ye FK ile bağlı 11 tablonun 11'i de `ON DELETE CASCADE`,
ve hepsi **BOŞ** (0 satır): `student_answers`, `exam_questions`,
`quiz_questions`, `question_performance_analytics`, `irt_calibration_history`,
`question_tag_associations`, `student_question_flags`, `video_solutions` …
Yani silinen tek şey çöpün kendisi. Canlıda 7 kullanıcı / 4 öğrenci profili var
ve hiçbiri bu sorulardan birini yanıtlamış değil.

GERI ALINABILIRLIK — "silinen küme == yedeklenen küme" YAPISAL OLARAK DOĞRU
---------------------------------------------------------------------------
DELETE, id kümesini predikatı YENIDEN DEĞERLENDIREREK değil **yedek tablodan**
alır. Bu bir assert değil, bir inşa özelliği: yedeklenmemiş bir satır
silinemez. Predikat ince bir biçimde yanlış olsaydı bile yedek ile silinen
küme ayrışamazdı.

Geri alma (dört tablo, ebeveyn ÖNCE — yavruların PK'sı aynı zamanda FK):

    INSERT INTO question_bank       SELECT * FROM question_bank_cop_yedek_<damga>;
    INSERT INTO question_content    SELECT * FROM question_content_cop_yedek_<damga>;
    INSERT INTO question_metadata   SELECT * FROM question_metadata_cop_yedek_<damga>;
    INSERT INTO question_statistics SELECT * FROM question_statistics_cop_yedek_<damga>;
    REFRESH MATERIALIZED VIEW mv_safe_for_beta;

KAPI BOŞALIR — KASITLI
----------------------
`mv_safe_for_beta` bugün 27.073 satır ve **27.073'ü de** bu çöp kümesinden
geliyor (ölçüldü). Silme sonrası kapı 0'a düşer. Bu bir gerileme değil, doğru
sayının ilk kez görünmesi: bugünkü 27.073 zaten 0 servis edilebilir soru
demekti. İkmal ayrı iş — `kiro2_temp` 53.937 TYT MATEMATİK taşıyor (%98,1
görselli).

`--kalici` VARSAYILANI False: çağrı GERİ ALINIR. Yanlış varsayılan "prova"yı
sessizce kalıcı yazıma çevirirdi (`y11_yukleyici.py` ile aynı sözleşme).

Bekçi: `backend/tests/fast/test_y11_cop_sil.py`
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

# Ebeveyn ÖNCE yedeklenir ama SİLME sırasında cascade yavruları kendisi alır.
# Yedek sırası önemsiz; geri YÜKLEME sırası önemli (bkz. docstring).
TABLOLAR: tuple[str, ...] = (
    "question_bank",
    "question_content",
    "question_metadata",
    "question_statistics",
)

# Ayırıcı TEK yerde tanımlı. Kopyalanırsa sürüklenir.
COP_PREDIKATI = "source_book IS NULL"

_DAMGA_DESENI = re.compile(r"^[a-z0-9_]{4,40}$")


def damga_dogrula(damga: str) -> str:
    """Yedek tablo adına gömülecek damgayı doğrular.

    Damga SQL'e dize olarak giriyor (tablo adı parametreleştirilemez), bu yüzden
    beyaz liste zorunlu. Enjeksiyon buradan geçemez.
    """
    if not _DAMGA_DESENI.match(damga):
        raise ValueError(f"gecersiz damga: {damga!r} — yalniz [a-z0-9_], 4-40 karakter")
    return damga


def yedek_tablo_adi(tablo: str, damga: str) -> str:
    if tablo not in TABLOLAR:
        raise ValueError(f"bilinmeyen tablo: {tablo!r}")
    return f"{tablo}_cop_yedek_{damga_dogrula(damga)}"


def yedek_ifadeleri(damga: str) -> list[str]:
    """Dört yedek tablosunu üreten CTAS ifadeleri.

    `question_metadata` İLK: ayırıcı kolon (`source_book`) onda ve diğer üçü
    id kümesini ONDAN türetiyor. Böylece dördü de **aynı** id kümesini taşır;
    predikat dört kez ayrı ayrı değerlendirilmez.
    """
    damga_dogrula(damga)
    meta = yedek_tablo_adi("question_metadata", damga)
    ifadeler = [
        f"CREATE TABLE {meta} AS "  # nosec B608 -- damga beyaz listeden, tablo adi parametrelenmez
        f"SELECT * FROM question_metadata WHERE {COP_PREDIKATI}"
    ]
    for tablo in ("question_bank", "question_content", "question_statistics"):
        ifadeler.append(
            f"CREATE TABLE {yedek_tablo_adi(tablo, damga)} AS "  # nosec B608
            f"SELECT t.* FROM {tablo} t WHERE t.id IN (SELECT id FROM {meta})"
        )
    return ifadeler


def silme_ifadesi(damga: str) -> str:
    """Silme id kümesini YEDEKTEN alır — predikatı yeniden değerlendirmez.

    Yavru tablolar (`content`/`metadata`/`statistics`) ve 11 FK çocuğu
    `ON DELETE CASCADE` ile kendiliğinden gider; hepsi ölçülerek boş bulundu.
    """
    bank_yedek = yedek_tablo_adi("question_bank", damga)
    return (
        "DELETE FROM question_bank "  # nosec B608 -- damga beyaz listeden
        f"WHERE id IN (SELECT id FROM {bank_yedek})"
    )


def dogrulama_sorgulari(damga: str) -> dict[str, str]:
    """Transaction İÇİNDE, geri alımdan ÖNCE koşacak ölçümler."""
    damga_dogrula(damga)
    sorgular = {
        "kalan_bank": "SELECT count(*) FROM question_bank",
        "kalan_content": "SELECT count(*) FROM question_content",
        "kalan_metadata": "SELECT count(*) FROM question_metadata",
        "kalan_statistics": "SELECT count(*) FROM question_statistics",
        # Silme tam olmalı: kitapsız tek satır kalmamalı
        "kalan_kitapsiz": (
            f"SELECT count(*) FROM question_metadata WHERE {COP_PREDIKATI}"  # nosec B608
        ),
        # Y11 partisi DOKUNULMAMIŞ olmalı
        "kalan_y11_damgali": (
            "SELECT count(*) FROM question_metadata "
            "WHERE pipeline_metadata->>'y11_batch' IS NOT NULL"
        ),
        # Yetim: yavru satır ebeveynsiz kalmamalı
        "yetim_content": (
            "SELECT count(*) FROM question_content c "
            "WHERE NOT EXISTS (SELECT 1 FROM question_bank b WHERE b.id=c.id)"
        ),
        "yetim_metadata": (
            "SELECT count(*) FROM question_metadata m "
            "WHERE NOT EXISTS (SELECT 1 FROM question_bank b WHERE b.id=m.id)"
        ),
        "yetim_statistics": (
            "SELECT count(*) FROM question_statistics s "
            "WHERE NOT EXISTS (SELECT 1 FROM question_bank b WHERE b.id=s.id)"
        ),
    }
    for tablo in TABLOLAR:
        sorgular[f"yedek_{tablo}"] = (
            f"SELECT count(*) FROM {yedek_tablo_adi(tablo, damga)}"  # nosec B608
        )
    return sorgular


def beklenti_ihlalleri(
    olcum: dict[str, int], *, beklenen_cop: int, beklenen_kalan: int
) -> list[str]:
    """Ölçümü beklentiyle karşılaştırır; ihlal listesi döndürür (boş = temiz).

    Saf fonksiyon — DB'siz test edilebilir. Kapının kendisi budur: boş liste
    dönmezse çağıran KALICI yazmaz.
    """
    ihlaller: list[str] = []
    for tablo in TABLOLAR:
        anahtar = f"yedek_{tablo}"
        if olcum.get(anahtar) != beklenen_cop:
            ihlaller.append(f"{anahtar}={olcum.get(anahtar)} beklenen {beklenen_cop}")
    for tablo in ("bank", "content", "metadata", "statistics"):
        anahtar = f"kalan_{tablo}"
        if olcum.get(anahtar) != beklenen_kalan:
            ihlaller.append(f"{anahtar}={olcum.get(anahtar)} beklenen {beklenen_kalan}")
    if olcum.get("kalan_kitapsiz") != 0:
        ihlaller.append(f"kalan_kitapsiz={olcum.get('kalan_kitapsiz')} beklenen 0")
    if olcum.get("kalan_y11_damgali") != beklenen_kalan:
        ihlaller.append(
            f"kalan_y11_damgali={olcum.get('kalan_y11_damgali')} "
            f"beklenen {beklenen_kalan}"
        )
    for anahtar in ("yetim_content", "yetim_metadata", "yetim_statistics"):
        if olcum.get(anahtar) != 0:
            ihlaller.append(f"{anahtar}={olcum.get(anahtar)} beklenen 0")
    return ihlaller


async def cop_sil(
    baglanti: Any,
    damga: str,
    *,
    kalici: bool = False,
    dogrulayici: Callable[[Any], Awaitable[dict[str, int]]] | None = None,
) -> dict[str, Any]:
    """Yedekle + sil, TEK transaction. `kalici=False` ise GERİ ALIR."""
    damga_dogrula(damga)
    rapor: dict[str, Any] = {"damga": damga, "kalici": kalici}
    islem = baglanti.transaction()
    await islem.start()
    try:
        for ifade in yedek_ifadeleri(damga):
            await baglanti.execute(ifade)
        silinen = await baglanti.execute(silme_ifadesi(damga))
        rapor["silme_sonucu"] = silinen
        if dogrulayici is not None:
            rapor["olcum"] = await dogrulayici(baglanti)
    except Exception:
        await islem.rollback()
        raise
    if kalici:
        await islem.commit()
    else:
        await islem.rollback()
    return rapor


def dsn_coz(veritabani: str) -> str:
    """DSN'i ortamdan çözer. Parola KODA YAZILMAZ."""
    dsn = os.environ.get("KIRO2_DSN")
    if dsn:
        return dsn
    kullanici = os.environ.get("PGUSER", "postgres")
    parola = os.environ.get("PGPASSWORD", "")
    sunucu = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5434")
    kimlik = f"{kullanici}:{parola}@" if parola else f"{kullanici}@"
    return f"postgresql://{kimlik}{sunucu}:{port}/{veritabani}"


async def _main(argv: Sequence[str] | None = None) -> int:
    import asyncpg  # yerel import: modül DB'siz de import edilebilsin

    ayristirici = argparse.ArgumentParser(
        description="Kitapsiz (sentetik) soru havuzunu yedekle + sil"
    )
    ayristirici.add_argument("--damga", required=True, help="orn: 20260820")
    ayristirici.add_argument("--beklenen-cop", type=int, required=True)
    ayristirici.add_argument("--beklenen-kalan", type=int, required=True)
    ayristirici.add_argument(
        "--kalici",
        action="store_true",
        help="VERILMEZSE geri alinir (prova). Kalici yazim icin ACIKCA ver.",
    )
    a = ayristirici.parse_args(argv)

    baglanti = await asyncpg.connect(dsn_coz("kiro2"))
    try:

        async def dogrula(b: Any) -> dict[str, int]:
            return {
                ad: await b.fetchval(sql)
                for ad, sql in dogrulama_sorgulari(a.damga).items()
            }

        rapor = await cop_sil(baglanti, a.damga, kalici=a.kalici, dogrulayici=dogrula)
    finally:
        await baglanti.close()

    olcum = rapor.get("olcum", {})
    for ad, deger in sorted(olcum.items()):
        print(f"  {ad:24s} = {deger}")
    ihlaller = beklenti_ihlalleri(
        olcum, beklenen_cop=a.beklenen_cop, beklenen_kalan=a.beklenen_kalan
    )
    print(f"\nkalici={rapor['kalici']}  silme={rapor.get('silme_sonucu')}")
    if ihlaller:
        print("IHLAL:")
        for i in ihlaller:
            print(f"  - {i}")
        return 1
    print("Tum beklentiler karsilandi.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
