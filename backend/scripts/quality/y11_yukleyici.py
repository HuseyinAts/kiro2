#!/usr/bin/env python
"""Y11 göçünün YAZMA katmanı — `kiro2_temp` → canlı `kiro2`, TEK transaction.

`y11_goc.kaynak_satiri_donustur` saf dönüşümdür ve DB'ye dokunmaz. Bu modül
onun çıktısını dört tabloya yazar. İkisi bilerek ayrı: dönüşüm sentetik girdiyle
242 vakada çivilenebiliyor, yazım ise ancak gerçek Postgres'e karşı ölçülebilir.

#486 — KODEK KAYNAK TARAFINDA ZORUNLU, HEDEF TARAFINDA YASAK
------------------------------------------------------------
asyncpg `json` kolonlarını varsayılan olarak **`str`** döndürür/bekler. Bu iki
ucu ters yönde ısırır ve devir notu bunu "damgasız parti" riski olarak taşıyordu:

* **Okuma (kodek ZORUNLU).** Kodek yoksa `pipeline_metadata` bir `str` gelir ve
  `_damgali_pipeline_metadata` `ValueError` ile durur — gürültülü, iyi. Ama
  "gürültüyü sustur" refleksiyle guard gevşetilirse damga hiç eklenmez ve parti
  **geri alınamaz** (damga geri alma kümesinin TEK taşıyıcısı). Doğru çözüm
  guard'ı gevşetmek değil, **kaynak bağlantısına kodek kaydetmek**.
* **Yazma (kodek YASAK).** Burada değerler `json.dumps` ile AÇIKÇA `str`'e
  çevrilir (`insert_ifadeleri`, saf ve DB'siz test edilebilir). Hedef bağlantıya
  da kodek kaydedilseydi asyncpg o `str`'i BİR KEZ DAHA kodlar; kolon bir JSON
  *string skaları* tutar, `->>'y11_batch'` **NULL** döner ve INSERT patlamaz.
  Sessiz damga kaybı. Bu yüzden hedef bağlantı çıplak bırakılır.

Ölçüldü (20 Ağu, canlı):

    hedefte `json` kolon           : 7  (content 2, metadata 5)  <- 1 DEGIL
    KABUL'de json_typeof='string'  : 0  -> "str geldi = kodek yok" guard'i guvenli
    kaynak `id` / hedef `id`       : character varying  (uuid DEGIL)
    `pipeline_metadata`            : json  (jsonb DEGIL; `->>` ikisinde de calisir)

TABLO SIRASI
------------
`question_bank` İLK. Üç yavru tablonun PK'sı aynı zamanda ebeveyne FK
(`L-s230-yavru-tablonun-pk-si-id`: JOIN anahtarı `qc.id = qb.id`, `question_id`
kolonu YOKTUR). Ters sırada ilk INSERT `ForeignKeyViolationError` verir.

Bekçi: `backend/tests/fast/test_y11_yukleyici.py`
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from collections.abc import Awaitable, Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from y11_goc import kaynak_satiri_donustur

# Yavru tabloların PK'sı ebeveyne FK -> ebeveyn ÖNCE.
TABLO_SIRASI: tuple[str, ...] = (
    "question_bank",
    "question_content",
    "question_metadata",
    "question_statistics",
)

# Hedefte `json` tipli kolonlar (information_schema'dan ölçüldü, 20 Ağu).
# Bu küme eksik olursa asyncpg `dict`/`list` için gürültülü `DataError` verir —
# sessiz kusur değil, ama pilot boşa gider.
JSON_KOLONLARI: dict[str, frozenset[str]] = {
    "question_bank": frozenset(),
    "question_content": frozenset({"alternative_solutions", "structured_explanation"}),
    "question_metadata": frozenset(
        {
            "misconception_tags",
            "pipeline_metadata",
            "secondary_topics",
            "similar_question_ids",
            "solution_steps",
        }
    ),
    "question_statistics": frozenset(),
}

# Kolon adları kod sabitlerinden gelir (kullanıcı girdisi değil), yine de
# SQL'e girmeden önce doğrulanır: bandit S608'in dayanağı budur.
_TANIMLAYICI = re.compile(r"^[a-z_][a-z0-9_]*$")

# Boyut uyuşmazlığı: kaynak vector(768), hedef vector(1536). Dönüşüm bu anahtarı
# hiç üretmiyor; SELECT'e de konmaz ki asyncpg `vector` tipini çözmek zorunda kalmasın.
DISLANAN_KAYNAK_KOLONU = "embedding"


def insert_sql(tablo: str, kolonlar: Sequence[str]) -> str:
    """`INSERT INTO t (a,b) VALUES ($1,$2)` — tanımlayıcılar doğrulanarak."""
    if tablo not in TABLO_SIRASI:
        raise ValueError(f"bilinmeyen hedef tablo: {tablo!r}")
    if not kolonlar:
        raise ValueError(f"{tablo}: kolon listesi bos — INSERT anlamsiz")
    for kolon in kolonlar:
        if not _TANIMLAYICI.match(kolon):
            raise ValueError(f"{tablo}: gecersiz kolon adi {kolon!r}")
    yer_tutucular = ", ".join(f"${i}" for i in range(1, len(kolonlar) + 1))
    # nosec B608 -- tablo adi TABLO_SIRASI'ndan, kolon adlari _TANIMLAYICI
    # regex'inden geciyor (ikisi de yukarida dogrulaniyor). DEGERLERIN hicbiri
    # SQL metnine girmiyor: hepsi $1..$N ile parametreli.
    return f"INSERT INTO {tablo} ({', '.join(kolonlar)}) VALUES ({yer_tutucular})"  # nosec B608


def _json_degeri(tablo: str, kolon: str, deger: Any) -> Any:
    """`json` kolonu için TEK kez serialize et; `None` SQL NULL kalır.

    Gelen değer `str` ise bu, kaynak bağlantısında kodek KAYDEDİLMEDİĞİ anlamına
    gelir (ölçüldü: KABUL kümesinde JSON string skalari 0). Sessizce `dumps`
    uygulamak çift kodlama üretir ve damgayı görünmez kılar -> gürültülü dur.
    """
    if kolon not in JSON_KOLONLARI[tablo]:
        return deger
    if deger is None:
        return None
    if isinstance(deger, str):
        raise ValueError(
            f"{tablo}.{kolon} bir `str` — kaynak baglantisinda json kodegi "
            "KAYITLI DEGIL (#486). Simdi dumps uygulamak CIFT KODLAMA uretir: "
            "kolon bir JSON string skalari tutar, `->>` NULL doner ve parti "
            "damgasiz/geri alinamaz olur. Kodegi kaydet, guard'i gevsetme."
        )
    return json.dumps(deger, ensure_ascii=False)


def insert_ifadeleri(
    hedef: dict[str, dict[str, Any]],
) -> list[tuple[str, tuple[str, ...], tuple[Any, ...]]]:
    """Dönüşüm çıktısını `(tablo, kolonlar, degerler)` üçlülerine çevirir.

    Sıra `TABLO_SIRASI`'na göre SABİT — çağıranın sözlük sırasına bakmaz.
    Kolon kümesi dönüşümün ürettiği anahtarlarla birebirdir: burada bir anahtar
    düşerse ya NOT NULL patlar (gürültülü) ya da `server_default` sürüklemesi
    olur (sessiz; `review_status` bunun ölçülmüş emsali).
    """
    eksik = [t for t in TABLO_SIRASI if t not in hedef]
    if eksik:
        raise ValueError(
            f"donusum ciktisinda {len(eksik)} tablo YOK: {eksik}. Dort sozluk "
            "ATOMIK bir birimdir; yarim INSERT geri alinamaz."
        )
    ifadeler = []
    for tablo in TABLO_SIRASI:
        kolonlar = tuple(hedef[tablo])
        degerler = tuple(
            _json_degeri(tablo, kolon, hedef[tablo][kolon]) for kolon in kolonlar
        )
        ifadeler.append((tablo, kolonlar, degerler))
    return ifadeler


async def parti_yaz(
    baglanti: Any,
    hedefler: Iterable[dict[str, dict[str, Any]]],
    *,
    kalici: bool = False,
    dogrulayici: Callable[[Any, list[str]], Awaitable[Any]] | None = None,
) -> dict[str, Any]:
    """Dört tabloya TEK transaction'da yazar.

    `kalici` varsayılanı **False**: çağrı geri alınır. Yanlış varsayılan, "pilot"
    niyetiyle çalıştırılan bir komutu kalıcı yazıma çevirirdi.

    `dogrulayici` transaction **içinde**, ROLLBACK'ten ÖNCE çağrılır — geri
    alınacak bir yazımı ancak orada okuyabilirsin.
    """
    hedefler = list(hedefler)
    idler = [h["question_bank"]["id"] for h in hedefler]
    rapor: dict[str, Any] = {
        "satir": len(hedefler),
        "kalici": kalici,
        "yazilan": dict.fromkeys(TABLO_SIRASI, 0),
        "dogrulama": None,
    }

    tx = baglanti.transaction()
    await tx.start()
    try:
        for hedef in hedefler:
            for tablo, kolonlar, degerler in insert_ifadeleri(hedef):
                await baglanti.execute(insert_sql(tablo, kolonlar), *degerler)
                rapor["yazilan"][tablo] += 1
        if dogrulayici is not None:
            rapor["dogrulama"] = await dogrulayici(baglanti, idler)
    except BaseException:
        await tx.rollback()
        raise
    if kalici:
        await tx.commit()
    else:
        await tx.rollback()
    return rapor


# ---------------------------------------------------------------------------
# DB yardımcıları (CLI tarafı)
# ---------------------------------------------------------------------------


def dsn_coz(veritabani: str) -> str:
    """`backend/.env` içindeki `DATABASE_URL`'i okuyup DB adını değiştirir.

    Kaynak koda DSN gömmek parolayı git'e sokar ve `detect-secrets` bunu HAKLI
    olarak bloklar (S229). Ortam değişkeni `KIRO2_LIVE_DSN` ile ezilebilir.
    Postgres olmayan DSN REDDEDİLİR: test ortamı `DATABASE_URL`'i sqlite yapıyor
    ve sessizce ona düşmek bu depoda kayıtlı bir kusur sınıfı.
    """
    ham = os.getenv("KIRO2_LIVE_DSN")
    if not ham:
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for satir in env.read_text(encoding="utf-8").splitlines():
                if satir.strip().startswith("DATABASE_URL="):
                    ham = satir.split("=", 1)[1].strip().strip("\"'")
                    break
    if not ham or "postgres" not in ham:
        raise SystemExit(
            "HATA: postgres DSN cozulemedi (backend/.env DATABASE_URL veya "
            "KIRO2_LIVE_DSN). sqlite'a DUSULMEZ."
        )
    for onek in ("postgresql+asyncpg://", "postgresql+psycopg2://", "postgresql://"):
        if ham.startswith(onek):
            ham = "postgresql://" + ham[len(onek) :]
            break
    return ham.rsplit("/", 1)[0] + "/" + veritabani


async def json_kodegi_kaydet(baglanti: Any) -> None:
    """#486 — YALNIZ KAYNAK bağlantısına. Hedefe kaydetmek çift kodlama üretir."""
    for tip in ("json", "jsonb"):
        await baglanti.set_type_codec(
            tip, encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )


async def kaynak_kolonlari(baglanti: Any) -> list[str]:
    """Kaynağın kolon listesini `information_schema`'dan çıkar (`embedding` hariç).

    Elle yazılmış bir liste kaynak şeması değişince sessizce bayatlar; buradan
    okumak dönüşümün gürültülü `_zorunlu` kontrolüyle birlikte drift'i görünür tutar.
    """
    satirlar = await baglanti.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='question_bank' "
        "AND column_name <> $1 ORDER BY ordinal_position",
        DISLANAN_KAYNAK_KOLONU,
    )
    return [s["column_name"] for s in satirlar]


async def kaynak_satirlari(
    baglanti: Any, idler: Sequence[str], kolonlar: Sequence[str]
) -> list[dict[str, Any]]:
    """KABUL satırlarını `topic_code` ile birlikte çeker (remap kod üzerinden)."""
    secim = ", ".join(f"q.{k}" for k in kolonlar)
    satirlar = await baglanti.fetch(
        # nosec B608 -- `secim` information_schema.columns'dan gelen kolon
        # adlari; id listesi $1 ile parametreli.
        f"SELECT {secim}, t.code AS topic_code "  # nosec B608
        "FROM question_bank q "
        "JOIN topic_hierarchy t ON t.id = q.primary_topic_id "
        "WHERE q.id = ANY($1::text[])",
        list(idler),
    )
    return [dict(s) for s in satirlar]


async def topic_haritasi(baglanti: Any) -> dict[str, str]:
    """CANLI `topic_hierarchy`'den `code -> id`. Kaynağın id'si geçirilemez."""
    satirlar = await baglanti.fetch("SELECT code, id FROM topic_hierarchy")
    return {s["code"]: s["id"] for s in satirlar}


async def _main(argv: Sequence[str] | None = None) -> int:
    import asyncpg

    ayristirici = argparse.ArgumentParser(description="Y11 gocu — parti yukleyici")
    ayristirici.add_argument("--idler", required=True, type=Path)
    ayristirici.add_argument("--damga", required=True)
    ayristirici.add_argument("--limit", type=int, default=None)
    ayristirici.add_argument(
        "--kalici",
        action="store_true",
        help="KALICI YAZ. Verilmezse transaction GERI ALINIR (pilot).",
    )
    a = ayristirici.parse_args(argv)

    idler = [
        s.strip() for s in a.idler.read_text(encoding="utf-8").split() if s.strip()
    ]
    if a.limit:
        idler = idler[: a.limit]
    if not idler:
        raise SystemExit("HATA: 0 id — yanlis-sifir, dosyayi kontrol et.")

    kaynak = await asyncpg.connect(dsn_coz("kiro2_temp"))
    hedef = await asyncpg.connect(dsn_coz("kiro2"))
    try:
        await json_kodegi_kaydet(kaynak)  # #486 — yalniz kaynak
        kolonlar = await kaynak_kolonlari(kaynak)
        satirlar = await kaynak_satirlari(kaynak, idler, kolonlar)
        if len(satirlar) != len(idler):
            raise SystemExit(
                f"HATA: {len(idler)} id istendi, {len(satirlar)} satir geldi. "
                "Eksik id sessizce atlanmaz."
            )
        harita = await topic_haritasi(hedef)
        hedefler = [
            kaynak_satiri_donustur(s, topic_kod_haritasi=harita, damga=a.damga)
            for s in satirlar
        ]

        kaynak_ile = {s["id"]: s for s in satirlar}

        async def dogrula(baglanti: Any, yazilan: list[str]) -> dict[str, Any]:
            return await pilot_dogrulama(baglanti, yazilan, a.damga, kaynak_ile)

        rapor = await parti_yaz(hedef, hedefler, kalici=a.kalici, dogrulayici=dogrula)
    finally:
        await kaynak.close()
        await hedef.close()

    print(json.dumps(rapor, ensure_ascii=False, indent=2, default=str))
    return 0


_ICERIK_ALANLARI = (
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "correct_answer",
)


async def pilot_dogrulama(
    baglanti: Any,
    idler: Sequence[str],
    damga: str,
    kaynak_ile: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Transaction İÇİNDE koşar: 4 tablo sayımı, yetim, damga, İÇERİK SADAKATİ.

    Damga `->>` ile okunur — çift kodlanmış bir metadata burada NULL döner ve
    yalnız bu kontrol onu yakalar.

    İçerik sadakati ayrı bir kusur sınıfını kapsar: sayım ve damga doğruyken
    kolon/değer **hizası** kaymış olabilir. Tipler uyuştuğu için DB kabul eder ve
    `question_text` ile `explanation`'ı yer değiştirmiş bir satır sessizce servis
    edilir. `correct_answer` şık listesine KONUMSAL referans olduğu için şıkların
    sırası da birebir karşılaştırılır (`L-s232-cevap-harfi-sik-listesi-...`).
    """
    idl = list(idler)
    sayim = {}
    for tablo in TABLO_SIRASI:
        sayim[tablo] = await baglanti.fetchval(
            # nosec B608 -- `tablo` TABLO_SIRASI sabitinden geliyor.
            f"SELECT count(*) FROM {tablo} WHERE id = ANY($1::text[])",  # nosec B608
            idl,
        )
    damgali = await baglanti.fetchval(
        "SELECT count(*) FROM question_metadata "
        "WHERE id = ANY($1::text[]) AND pipeline_metadata->>'y11_batch' = $2",
        idl,
        damga,
    )
    yetim = await baglanti.fetchval(
        "SELECT count(*) FROM question_bank qb "
        "LEFT JOIN question_content   qc ON qc.id = qb.id "
        "LEFT JOIN question_metadata  qm ON qm.id = qb.id "
        "LEFT JOIN question_statistics qs ON qs.id = qb.id "
        "WHERE qb.id = ANY($1::text[]) "
        "AND (qc.id IS NULL OR qm.id IS NULL OR qs.id IS NULL)",
        idl,
    )
    toplam = await baglanti.fetchval("SELECT count(*) FROM question_bank")

    icerik: dict[str, Any] = {"karsilastirilan": 0, "sapma": []}
    kural: dict[str, Any] = {}
    if kaynak_ile is not None:
        geri = await baglanti.fetch(
            "SELECT qb.id, qc.question_text, qc.option_a, qc.option_b, qc.option_c, "
            "qc.option_d, qc.option_e, qc.correct_answer, qc.question_image_url, "
            "qb.is_active, qb.is_public, qb.review_status, "
            "qm.bloom_category, qs.quality_review_status, qs.times_asked "
            "FROM question_bank qb "
            "JOIN question_content    qc ON qc.id = qb.id "
            "JOIN question_metadata   qm ON qm.id = qb.id "
            "JOIN question_statistics qs ON qs.id = qb.id "
            "WHERE qb.id = ANY($1::text[])",
            idl,
        )
        for satir in geri:
            kaynak = kaynak_ile[satir["id"]]
            icerik["karsilastirilan"] += 1
            for alan in _ICERIK_ALANLARI:
                if satir[alan] != kaynak[alan]:
                    icerik["sapma"].append(f"{satir['id']}.{alan}")
        kural = {
            "is_active_true": sum(1 for s in geri if s["is_active"]),
            "is_public_true": sum(1 for s in geri if s["is_public"]),
            "review_status_approved": sum(
                1 for s in geri if s["review_status"] == "approved"
            ),
            "quality_pending": sum(
                1 for s in geri if s["quality_review_status"] == "pending"
            ),
            "times_asked_sifir": sum(1 for s in geri if s["times_asked"] == 0),
            "bloom_lowercase": sum(
                1 for s in geri if (s["bloom_category"] or "").islower()
            ),
            "gorsel_null": sum(1 for s in geri if s["question_image_url"] is None),
        }

    return {
        "tablo_sayimi": sayim,
        "damgali": damgali,
        "yetim": yetim,
        "question_bank_toplam": toplam,
        "icerik_sadakati": icerik,
        "kural_sayimi": kural,
    }


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
