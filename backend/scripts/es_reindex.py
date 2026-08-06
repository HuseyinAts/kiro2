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
import sys
from pathlib import Path
from typing import Any

# Script `backend/scripts/` içinde olduğu için `sys.path[0]` orasıdır ve
# `core`/`models` görünmez. Ev deseni (bkz. scripts/audit_orm_schema_drift.py:92).
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

logger = logging.getLogger("es_reindex")

# Paylasilan sema ve saf mantik core/ icinde: `scripts/` .dockerignore ile
# imajdan ELENIYOR (satir 82), dolayisiyla celery gorevi oradan import EDEMEZ.
from core.es_index_schema import (  # noqa: E402
    ALANLAR,
    CANLI_INDEX,
    MAPPING,
    SETTINGS,
    SORGU,
    YASAKLI_ALANLAR,
    _belge_kur,
    _es_kimlikleri,
    _yeni_index_adi,
    esitleme_plani,
)

__all__ = [
    "ALANLAR",
    "MAPPING",
    "SETTINGS",
    "SORGU",
    "YASAKLI_ALANLAR",
    "_belge_kur",
    "_yeni_index_adi",
    "esitleme_plani",
]


async def _db_satirlari() -> list[dict[str, Any]]:
    from sqlalchemy import text

    from core.database import db_manager

    async with db_manager.get_session() as oturum:
        sonuc = await oturum.execute(text(SORGU))
        return [dict(r) for r in sonuc.mappings().all()]


async def calistir(mod: str, onayla: bool, damga: str) -> int:
    from elasticsearch.helpers import async_bulk

    from core.elasticsearch_client import get_elasticsearch_client

    satirlar = await _db_satirlari()
    print(f"kapidan gecen kayit (mv_safe_for_beta JOIN question_bank): {len(satirlar)}")

    belgeler = [_belge_kur(s) for s in satirlar]
    print(f"belge kuruldu: {len(belgeler)} (bos doc_id / yasakli alan: 0)")

    es_wrapper = get_elasticsearch_client()
    await es_wrapper._ensure_connected()
    istemci = es_wrapper._client

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
