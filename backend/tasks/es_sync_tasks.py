"""Elasticsearch ↔ kalite kapısı artımlı senkronu.

NEDEN VAR — 30-31 TEM 2026 ÖLÇÜMLERİ
====================================
PG ile ES arasında **hiçbir artımlı senkron yolu yoktu**: `core/celery_app.py`
beat_schedule'ında tek bir ES görevi bulunmuyordu. Sonuç, canlı sistemden
ölçüldü:

    canlı index dokümanı            : 64.270
    ES'te olup kapıdan GEÇMEYEN     : 60.605
    kapıda olup ES'te OLMAYAN       : 21.462
    kapı (mv_safe_for_beta)         : 25.127

Index 2026-04-01'de 19 saniyede tek toplu yüklemeyle yazılmış ve o günden beri
diske tek veri baytı yazılmamış (translog 55 bayt = boş). Yani 4 aylık kalite
ve silme işlemlerinin HİÇBİRİ arama yüzeyine yansımadı.

`quality_gate_tasks` bunu ÇÖZMEZ: o yalnız `mv_safe_for_beta`yı tazeliyor.
Kapı tazelense bile ES ayrı bir depo olduğu için oradaki bayat kayıt servis
edilmeye devam eder — Ders #31'in ("status yargısı != servis dışı") ikinci
deposu.

NEDEN WATERMARK DEĞİL KÜME FARKI
--------------------------------
`updated_at` watermark'ı yalnız DEĞİŞEN kaydı yakalar. Oysa asıl tehlike
kapıdan DÜŞEN kayıt: bir soru `rejected` olduğunda `mv_safe_for_beta`den
çıkar, ama ES'te satırı DURUR ve watermark onu asla göstermez. Bu yüzden
plan küme farkıyla kuruluyor (`core.es_index_schema.esitleme_plani`).

NEDEN AYRI ADVISORY LOCK ANAHTARI
---------------------------------
`quality_gate_tasks._REFRESH_LOCK_KEY = 727_20260727` matview yenilemesini
serileştiriyor. Aynı anahtarı kullanmak iki FARKLI işi birbirine bloke
ettirirdi (senkron koşarken matview yenilemesi sessizce atlanır). Ayrı anahtar.

BEAT SIRASI KRİTİK
------------------
03:30 matview yenilemesi → 04:00 ES senkronu. Ters sıra bir gün ESKİ havuzu
indeksler; yani senkron her zaman taze kapıyı okumalı.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Paylasilan mantik core/ icinde. ONCE `scripts/`ten import ediliyordu ve bu
# KONTEYNERDE COKERDI: backend/.dockerignore:82 `scripts/`i imajdan eliyor,
# /app/scripts HIC YOK. Host'ta test yesil, uretimde her gece ImportError.

# quality_gate_tasks._REFRESH_LOCK_KEY (727_20260727) ile ÇAKIŞMAMALI.
_SENKRON_LOCK_KEY = 731_20260731

ES_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX = os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")


async def _senkronla() -> dict[str, Any]:
    from elasticsearch.helpers import async_bulk
    from sqlalchemy import text

    from core.database import db_manager
    from core.elasticsearch_client import get_elasticsearch_client
    from core.es_index_schema import (
        SORGU,
        _belge_kur,
        _es_kimlikleri,
        esitleme_plani,
    )

    async with db_manager.get_session() as oturum:
        kilit = await oturum.execute(
            text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": _SENKRON_LOCK_KEY}
        )
        if not kilit.scalar():
            logger.info("ES senkronu zaten kosuyor, atlandi")
            return {"atlandi": True}

        satirlar = [dict(r) for r in (await oturum.execute(text(SORGU))).mappings()]

    belgeler = dict(_belge_kur(s) for s in satirlar)

    es_wrapper = get_elasticsearch_client()
    await es_wrapper._ensure_connected()
    istemci = es_wrapper._client

    try:
        if not await istemci.indices.exists(index=INDEX):
            logger.warning("Index yok, senkron atlandi: %s", INDEX)
            return {"atlandi": True, "sebep": "index yok"}

        mevcut = await _es_kimlikleri(istemci, INDEX)
        eklenecek, silinecek = esitleme_plani(set(belgeler), mevcut)

        if eklenecek:
            await async_bulk(
                istemci,
                (
                    {"_index": INDEX, "_id": k, "_source": belgeler[k]}
                    for k in eklenecek
                ),
            )
        if silinecek:
            await async_bulk(
                istemci,
                ({"_op_type": "delete", "_index": INDEX, "_id": k} for k in silinecek),
                raise_on_error=False,  # zaten silinmiş belge hata sayılmaz
            )
        await istemci.indices.refresh(index=INDEX)
        sonuc = {
            "eklenen": len(eklenecek),
            "silinen": len(silinecek),
            "kapi": len(belgeler),
        }
        logger.info("ES senkronu tamam: %s", sonuc)
        return sonuc
    finally:
        await istemci.close()


try:
    from core.celery_app import celery_app

    @celery_app.task(name="tasks.es_sync_tasks.sync_search_index", bind=True)
    def sync_search_index(self: Any) -> dict[str, Any]:
        """Arama index'ini kalite kapısıyla eşitler (ekle + SİL)."""
        return asyncio.run(_senkronla())

except Exception:  # pragma: no cover - celery yoksa modül yine import edilebilir
    logger.debug("celery_app yok; es_sync_tasks yalniz kutuphane olarak yuklendi")
