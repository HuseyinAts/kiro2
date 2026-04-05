# -*- coding: utf-8 -*-
"""
question_bank -> Elasticsearch indexer
Turkish analyzer ile soru metinlerini index'le
"""
import asyncio, os, sys, json
sys.path.insert(0, '/app')

import psycopg2
from elasticsearch import AsyncElasticsearch

ES_URL   = os.environ.get('ELASTICSEARCH_URL', 'http://turkiye_sinav_elasticsearch:9200')
ES_INDEX = os.environ.get('ELASTICSEARCH_INDEX', 'turkiye_sinav_platform')
BATCH    = 500

# Turkish analyzer mapping
INDEX_MAPPING = {
    "settings": {
        "analysis": {
            "analyzer": {
                "turkish_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "turkish_stop", "turkish_stemmer"]
                },
                "turkish_search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "turkish_stop"]
                }
            },
            "filter": {
                "turkish_stop": {
                    "type": "stop",
                    "stopwords": "_turkish_"
                },
                "turkish_stemmer": {
                    "type": "stemmer",
                    "language": "turkish"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id":              {"type": "keyword"},
            "question_text":   {"type": "text", "analyzer": "turkish_analyzer",
                                "search_analyzer": "turkish_search_analyzer"},
            "option_a":        {"type": "text", "analyzer": "turkish_analyzer"},
            "option_b":        {"type": "text", "analyzer": "turkish_analyzer"},
            "option_c":        {"type": "text", "analyzer": "turkish_analyzer"},
            "option_d":        {"type": "text", "analyzer": "turkish_analyzer"},
            "option_e":        {"type": "text", "analyzer": "turkish_analyzer"},
            "correct_answer":  {"type": "keyword"},
            "explanation":     {"type": "text", "analyzer": "turkish_analyzer"},
            "exam_type":       {"type": "keyword"},
            "subject_area":    {"type": "keyword"},
            "primary_topic_id":{"type": "keyword"},
            "difficulty_level":{"type": "keyword"},
            "irt_difficulty":  {"type": "float"},
            "bloom_level":     {"type": "integer"},
            "is_calibrated":   {"type": "boolean"},
            "is_calib_pool":   {"type": "boolean"},
            "is_active":       {"type": "boolean"},
            "quality_score":   {"type": "float"},
            "source_book":     {"type": "keyword"},
            "osym_year":       {"type": "integer"},
            "grade_level":     {"type": "integer"},
            "word_count":      {"type": "integer"}
        }
    }
}

async def main():
    es = AsyncElasticsearch([ES_URL])
    
    # Index oluştur (varsa sil, yeniden oluştur)
    if await es.indices.exists(index=ES_INDEX):
        print(f"Index '{ES_INDEX}' mevcut — siliniyor...")
        await es.indices.delete(index=ES_INDEX)
    
    await es.indices.create(index=ES_INDEX, body=INDEX_MAPPING)
    print(f"Index '{ES_INDEX}' oluşturuldu (Turkish analyzer)")
    
    # DB bağlantısı
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'host.docker.internal'),
        port=5434, dbname='kiro2', user='postgres', password='postgres'
    )
    cur = conn.cursor()
    
    # Aktif soruları çek (is_active=TRUE)
    cur.execute("""
        SELECT id, question_text, option_a, option_b, option_c, option_d, option_e,
               correct_answer, explanation, exam_type, subject_area, primary_topic_id,
               difficulty_level, irt_difficulty, bloom_level,
               is_calibrated, is_calib_pool, is_active, quality_score,
               source_book, osym_year, grade_level, word_count
        FROM question_bank
        WHERE is_active = TRUE
        ORDER BY id
    """)
    
    total = 0
    errors = 0
    batch_ops = []
    
    while True:
        rows = cur.fetchmany(BATCH)
        if not rows:
            break
        
        for row in rows:
            (qid, qtext, oa, ob, oc, od, oe, ca, expl,
             exam, subj, topic_id, dlevel, irt_diff, bloom,
             is_calib, is_pool, is_active, qscore,
             src_book, osym_yr, grade, wc) = row
            
            doc = {
                "id": qid,
                "question_text": qtext or "",
                "option_a": oa or "",
                "option_b": ob or "",
                "option_c": oc or "",
                "option_d": od or "",
                "option_e": oe or "",
                "correct_answer": ca or "",
                "explanation": expl or "",
                "exam_type": exam or "",
                "subject_area": subj or "",
                "primary_topic_id": topic_id or "",
                "difficulty_level": str(dlevel) if dlevel else "",
                "irt_difficulty": float(irt_diff) if irt_diff else 0.0,
                "bloom_level": int(bloom) if bloom else 1,
                "is_calibrated": bool(is_calib),
                "is_calib_pool": bool(is_pool),
                "is_active": bool(is_active),
                "quality_score": float(qscore) if qscore else 0.0,
                "source_book": src_book or "",
                "osym_year": int(osym_yr) if osym_yr else None,
                "grade_level": int(grade) if grade else 12,
                "word_count": int(wc) if wc else 0,
            }
            batch_ops.append({"index": {"_index": ES_INDEX, "_id": qid}})
            batch_ops.append(doc)
        
        if batch_ops:
            resp = await es.bulk(operations=batch_ops, refresh=False)
            if resp.get('errors'):
                err_items = [i for i in resp['items'] if i.get('index', {}).get('error')]
                errors += len(err_items)
                if err_items:
                    print(f"  Hata örneği: {err_items[0]['index']['error']}")
            total += len(rows)
            batch_ops = []
            print(f"  {total:,} soru indexlendi...", end='\r')
    
    await es.indices.refresh(index=ES_INDEX)
    stats = await es.indices.stats(index=ES_INDEX)
    doc_count = stats['indices'][ES_INDEX]['primaries']['docs']['count']
    
    print(f"\nTAMAM: {total:,} soru işlendi, {doc_count:,} ES'te, {errors} hata")
    cur.close(); conn.close()
    await es.close()

asyncio.run(main())
