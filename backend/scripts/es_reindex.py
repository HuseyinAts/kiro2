#!/usr/bin/env python
"""Elasticsearch soru index'ini kalite kapısından (mv_safe_for_beta) yeniden kurar.

30-31 TEM 2026 ÖLÇÜMLERİ — bu script neden var
==============================================
* Canlı index 2026-04-01'de **19 saniyede** tek toplu yüklemeyle yazılmış
  (Lucene segment mtime'ları), o günden beri diske tek veri baytı yazılmamış
  (translog 55 bayt = boş). PG ile ES arasında **artımlı senkron yolu YOK**:
  `core/celery_app.py` beat_schedule'ında tek bir ES görevi yok.
* Sonuç: 4 aydır biriken kalite/silme işlemleri ES'e hiç yansımadı.
    - ES: 64.270 doküman, hepsi `is_active: true` diyor
    - PG: bunların yalnız 38.967'si gerçekten aktif → **25.303 dokümanda
      bayat is_active**. "is_active=true" ile filtreleyen her kod yolu
      devre dışı bırakılmış içerik servis eder: kontrol VAR görünür, ÇALIŞMAZ.
    - Kalite kapısı (`mv_safe_for_beta`, 25.127 kayıt) ile kesişim yalnız
      3.665 (%5,7). Yani ES'teki içeriğin %94'ü kapıdan geçmemiş.
* Index'i uygulama içinden yazabilecek TEK yol ölü: `elasticsearch_service.py`
  `create_index(mapping=...)` çağırıyor, gerçek parametre `mappings`
  (`core/elasticsearch_client.py:115`) → TypeError → geniş except → False.

NAİF ONARIM BİR SİLAHTIR (teşhis turunda yakalandı)
--------------------------------------------------
Sadece `mapping=` → `mappings=` düzeltmek YETMEZ, TEHLİKELİDİR:
`elasticsearch_service.index_question` doc_id'yi `str(question.get("id",""))`
ile kuruyor. Ham bir `question_bank` satırı yerine anahtarları uymayan bir
sözlük gelirse doc_id `""` olur; elasticsearch-py boş string'i SKIP_IN_PATH
sayıp **otomatik id** üretir → aynı kayıt her koşuda yeniden yazılır.
Bu script o yola HİÇ girmiyor: doc_id her belgede AÇIKÇA doğrulanıyor
(`_belge_kur` boş/eksik id'de hata fırlatır) ve `elasticsearch_service`
kullanılmıyor.

ŞEMA KARARI (ölçüldü, tahmin değil)
-----------------------------------
Canlı index DB kolon adlarını yansıtıyor (`question_text`, `option_a..e`,
`subject_area`...). `elasticsearch_service.question_mapping` ise TAMAMEN
farklı adlar kullanıyor (`text`, `subject`, `difficulty`) — onunla kurmak
tüketicileri sessizce kırardı. Bu script **canlı şemayı** korur.

CEVAP ALANLARI İNDEKSLENMİYOR
-----------------------------
Canlı index'te `correct_answer` 64.270/64.270 dolu ve `explanation`ın
61.847'si "Doğru cevap: X" yazıyor. API katmanında beyaz liste var
(`STUDENT_SAFE_QUESTION_FIELDS`, 17 alan — ikisi de listede DEĞİL), ama
"alan index'te yok" savunması beyaz liste hatasına da dayanır. Yeni index
bu iki alanı HİÇ taşımıyor. `CONTENT_SAFE_FIELDS` de ikisini istemiyor
(ölçüldü) → tüketici kaybı yok.

KULLANIM
--------
    python scripts/es_reindex.py --dry-run    # ÖLÇER, hiçbir şey yazmaz
    python scripts/es_reindex.py --build      # YENİ index kurar, canlıya dokunmaz
    python scripts/es_reindex.py --cutover --onayla   # yedek + takas

`--cutover` OUTWARD-FACING: arama havuzunu daraltır. `--onayla` olmadan
çalışmaz ve geri alım için önce eski index'i `*_yedek_*` adına kopyalar.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Script `backend/scripts/` içinde olduğu için `sys.path[0]` orasıdır ve
# `core`/`models` görünmez. Ev deseni (bkz. scripts/audit_orm_schema_drift.py:92).
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

logger = logging.getLogger("es_reindex")

CANLI_INDEX = os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")
ES_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")

# Yeni index'e yazılacak alanlar. Canlı şemadan TÜRETİLDİ; `correct_answer` ve
# `explanation` BİLEREK YOK (yukarıdaki nota bakınız). `is_active` de yok:
# index artık yalnız kapıdan geçen kayıtları taşıdığı için "aktif mi" sorusu
# index içinde cevaplanmıyor — bayat bir bayrağın yanlış güven vermesi bu
# kusurun ta kendisiydi.
ALANLAR = (
    "id",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "subject_area",
    "primary_topic_id",
    "exam_type",
    "difficulty_level",
    "irt_difficulty",
    "grade_level",
    "osym_year",
    "source_book",
    "bloom_level",
    "word_count",
    "quality_score",
)

YASAKLI_ALANLAR = frozenset({"correct_answer", "explanation", "is_active"})

# Türkçe analiz zinciri — eski index'ten BİREBİR kopyalandı.
# 31 Tem 2026'da neredeyse kaybediliyordu: ilk kurulan yeni index bu ayarlar
# OLMADAN yazıldı ve fark ancak takas öncesi arama karşılaştırmasıyla görüldü:
#     "hangi"  -> yeni 741 / eski 0    (eski index Türkçe durak kelimesini eliyor)
#     "ister"  -> yeni  61 / eski 270  (eski index gövdeliyor)
# Yani takas sessizce Türkçe arama kalitesini düşürecekti. Doküman sayısı
# tutuyor diye "aynı" sanmak yeterli değil — ARAMA DAVRANIŞI da ölçülmeli.
SETTINGS: dict[str, Any] = {
    "analysis": {
        "filter": {
            "turkish_stemmer": {"type": "stemmer", "language": "turkish"},
            "turkish_stop": {"type": "stop", "stopwords": "_turkish_"},
        },
        "analyzer": {
            "turkish_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "turkish_stop", "turkish_stemmer"],
            },
            "turkish_search_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "turkish_stop"],
            },
        },
    }
}

MAPPING: dict[str, Any] = {
    "properties": {
        "id": {"type": "keyword"},
        "question_text": {
            "type": "text",
            "analyzer": "turkish_analyzer",
            "search_analyzer": "turkish_search_analyzer",
        },
        "option_a": {"type": "text", "analyzer": "turkish_analyzer"},
        "option_b": {"type": "text", "analyzer": "turkish_analyzer"},
        "option_c": {"type": "text", "analyzer": "turkish_analyzer"},
        "option_d": {"type": "text", "analyzer": "turkish_analyzer"},
        "option_e": {"type": "text", "analyzer": "turkish_analyzer"},
        "subject_area": {"type": "keyword"},
        "primary_topic_id": {"type": "keyword"},
        "exam_type": {"type": "keyword"},
        "difficulty_level": {"type": "keyword"},
        "irt_difficulty": {"type": "float"},
        "grade_level": {"type": "integer"},
        "osym_year": {"type": "integer"},
        "source_book": {"type": "keyword"},
        "bloom_level": {"type": "integer"},
        "word_count": {"type": "integer"},
        "quality_score": {"type": "float"},
    }
}

# Kapıdan geçen kayıtları question_bank ile birleştirir. mv_safe_for_beta
# YALNIZCA `id` kolonu taşıyor (ölçüldü) — alanlar buradan geliyor.
# nosec B608 - f-string'e YALNIZCA modul duzeyindeki ALANLAR demetinin sabit
# kolon adlari giriyor; kullanici girdisi HIC yok, parametre de yok.
SORGU = f"""
    SELECT {", ".join("q." + a for a in ALANLAR)}
    FROM mv_safe_for_beta g
    JOIN question_bank q ON q.id = g.id
"""  # nosec B608


def _belge_kur(satir: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Bir DB satırını (doc_id, belge) ikilisine çevirir. SAF fonksiyon.

    İki değişmez ZORUNLU kılınıyor:

    1. `doc_id` boş olamaz. Boş id, elasticsearch-py'de SKIP_IN_PATH'e düşer ve
       ES **otomatik id** üretir; bu da her koşuda kaydın yeniden yazılması
       (çöp doküman birikmesi) demektir. Sessizce geçmek yerine patlıyoruz.
    2. Yasaklı alan (cevap/açıklama/bayat is_active) belgeye SIZAMAZ. Kaynak
       sorgu bugün onları seçmiyor ama sorgu ileride genişletilebilir; kontrol
       veriye bakarak yapılıyor, sorgu metnine güvenerek değil.
    """
    doc_id = str(satir.get("id") or "").strip()
    if not doc_id:
        raise ValueError(f"Bos doc_id — kayit indekslenemez: {satir!r}")

    belge = {a: satir.get(a) for a in ALANLAR if a != "id"}
    sizan = YASAKLI_ALANLAR & set(belge)
    if sizan:
        raise ValueError(f"Yasakli alan belgeye sizdi: {sorted(sizan)}")
    belge["id"] = doc_id
    return doc_id, belge


def _yeni_index_adi(damga: str) -> str:
    """Zaman damgalı yeni index adı. Damga DIŞARIDAN verilir (test edilebilir)."""
    return f"{CANLI_INDEX}_v{damga}"


def esitleme_plani(
    db_kimlikleri: set[str], es_kimlikleri: set[str]
) -> tuple[set[str], set[str]]:
    """Artımlı senkron planı: (eklenecek, silinecek). SAF fonksiyon.

    Watermark (updated_at) yerine KÜME FARKI kullanılıyor çünkü kapıdan
    DÜŞEN kayıtlar watermark'la yakalanamaz — bir soru `rejected` olduğunda
    `mv_safe_for_beta`den çıkar ama ES'te kalır. Tam da bugünkü kusur bu.
    """
    return db_kimlikleri - es_kimlikleri, es_kimlikleri - db_kimlikleri


async def _db_satirlari() -> list[dict[str, Any]]:
    from sqlalchemy import text

    from core.database import db_manager

    async with db_manager.get_session() as oturum:
        sonuc = await oturum.execute(text(SORGU))
        return [dict(r) for r in sonuc.mappings().all()]


async def _es_kimlikleri(istemci: Any, index: str) -> set[str]:
    """Index'teki tüm doküman id'lerini çeker.

    `search_after` + `sort: [{"_id": "asc"}]` DENENDI ve ES 8'de 400 verdi
    (`_id` üzerinde sıralama fielddata olmadan yasak). `async_scan` bu iş için
    tasarlanmış yardımcıdır ve sayfalama ayrıntısını kendisi yönetir.
    """
    from elasticsearch.helpers import async_scan

    return {
        vurus["_id"]
        async for vurus in async_scan(
            istemci, index=index, query={"query": {"match_all": {}}}, _source=False
        )
    }


async def calistir(mod: str, onayla: bool, damga: str) -> int:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk

    satirlar = await _db_satirlari()
    print(f"kapidan gecen kayit (mv_safe_for_beta JOIN question_bank): {len(satirlar)}")

    belgeler = [_belge_kur(s) for s in satirlar]
    print(f"belge kuruldu: {len(belgeler)} (bos doc_id / yasakli alan: 0)")

    istemci = AsyncElasticsearch(ES_URL)
    try:
        if await istemci.indices.exists(index=CANLI_INDEX):
            canli = (await istemci.count(index=CANLI_INDEX))["count"]
            canli_kimlikler = await _es_kimlikleri(istemci, CANLI_INDEX)
        else:
            canli, canli_kimlikler = 0, set()
        db_kimlikleri = {d for d, _ in belgeler}
        eklenecek, silinecek = esitleme_plani(db_kimlikleri, canli_kimlikler)

        print(f"canli index dokumani           : {canli}")
        print(f"kapida olup ES'te OLMAYAN      : {len(eklenecek)}")
        print(f"ES'te olup kapidan GECMEYEN    : {len(silinecek)}")
        print(f"yeni index hedef boyutu        : {len(belgeler)}")

        if mod == "dry-run":
            print("\nDRY-RUN: hicbir yazma yapilmadi.")
            return 0

        yeni = _yeni_index_adi(damga)
        if mod == "build":
            await istemci.indices.create(
                index=yeni, body={"mappings": MAPPING, "settings": SETTINGS}
            )
            await async_bulk(
                istemci,
                (
                    {"_index": yeni, "_id": doc_id, "_source": belge}
                    for doc_id, belge in belgeler
                ),
            )
            await istemci.indices.refresh(index=yeni)
            sayi = (await istemci.count(index=yeni))["count"]
            print(f"\nYENI INDEX KURULDU: {yeni} ({sayi} dokuman)")
            print("Canli index'e DOKUNULMADI. Takas icin: --cutover --onayla")
            return 0 if sayi == len(belgeler) else 1

        if mod == "cutover":
            if not onayla:
                print("\nREDDEDILDI: --cutover icin --onayla gerekli.")
                return 2
            yedek = f"{CANLI_INDEX}_yedek_{damga}"
            print(f"1) yedek: {CANLI_INDEX} -> {yedek}")
            await istemci.indices.create(index=yedek)
            await istemci.reindex(
                body={"source": {"index": CANLI_INDEX}, "dest": {"index": yedek}},
                wait_for_completion=True,
            )
            print(f"2) eski index siliniyor: {CANLI_INDEX}")
            await istemci.indices.delete(index=CANLI_INDEX)
            print(f"3) alias: {CANLI_INDEX} -> {yeni}")
            await istemci.indices.put_alias(index=yeni, name=CANLI_INDEX)
            print(f"\nTAKAS TAMAM. Geri alim: alias'i {yedek}'e cevir.")
            return 0
    finally:
        await istemci.close()
    return 1


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    grup = ap.add_mutually_exclusive_group(required=True)
    grup.add_argument("--dry-run", action="store_true", help="Yalniz olc")
    grup.add_argument("--build", action="store_true", help="Yeni index kur")
    grup.add_argument("--cutover", action="store_true", help="Yedekle + takas")
    ap.add_argument("--onayla", action="store_true", help="--cutover icin zorunlu")
    ap.add_argument("--damga", required=True, help="Index adi zaman damgasi")
    a = ap.parse_args()
    mod = "dry-run" if a.dry_run else ("build" if a.build else "cutover")
    return asyncio.run(calistir(mod, a.onayla, a.damga))


if __name__ == "__main__":
    sys.exit(main())
