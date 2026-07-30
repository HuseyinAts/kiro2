"""ES soru index'i — PAYLASILAN sema ve saf mantik.

NEDEN AYRI MODUL (31 Tem 2026'da olculdu)
------------------------------------------
Bu kod once `scripts/es_reindex.py` icindeydi ve `tasks/es_sync_tasks.py`
oradan import ediyordu. Ama `backend/.dockerignore:82` **`scripts/`'i imajdan
eliyor**: konteynerde `/app/scripts` HIC YOK (docker cp bile
"Could not find the file /app/scripts" hatasi verdi).

Yani gecelik celery gorevi her gece ImportError ile cokerdi ve bunu yalniz
log satirindan anlardik. Testler bunu YAKALAMAZ — host'ta `scripts/` var.

Paylasilan mantik artik imaja GIREN bir modulde; hem script hem celery gorevi
buradan okuyor. Tek tanim noktasi: sema iki yerde kopyalanmiyor.
"""

from __future__ import annotations

import os
from typing import Any

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
"""  # noqa: S608  # nosec B608


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
