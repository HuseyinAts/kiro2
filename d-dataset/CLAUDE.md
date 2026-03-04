# KIRO2 d-dataset - Soru-Cevap Eslestirme Pipeline

## Proje Durumu (Mart 2026)
**Production:** `eslesmis_sorucevap.jsonl` = **77,336 soru (v3.5)**
- 405 kitap, 100% validation PASS, 0 critical
- db_v7=0, rematch=0, LOW confidence=0

## Kritik Yollar
```
SCREENSHOTS  = C:\Users\husey\kiro2\veriseti\zkitap\screenshots\
ANSWERS_DB   = C:\Users\husey\kiro2\d-dataset\output\answer_keys_v8\answers_v8.db
OUTPUT       = C:\Users\husey\kiro2\d-dataset\output\extracted_answers\
SCRIPTS      = C:\Users\husey\kiro2\d-dataset\scripts\        # NOT git-tracked!
PROCESSED    = C:\Users\husey\kiro2\d-dataset\processed\      # NOT git-tracked!
```

## Veritabani Semasi (answers_v8.db)
```sql
-- answers tablosu YOK (v7'deki %39 dogruluk tablosu silindi)

CREATE TABLE answers_page_inline (  -- 78,720 satir, ~%85 dogruluk
    id INTEGER PRIMARY KEY,
    book_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    answer TEXT NOT NULL,
    confidence REAL DEFAULT 0.85,
    source TEXT,
    created_at TIMESTAMP
);

CREATE TABLE page_test_map (        -- 50,557 satir, extraction verisi
    book_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    test_no INTEGER DEFAULT 0,
    raw TEXT,
    PRIMARY KEY (book_name, page_number)
);

CREATE TABLE test_groups (          -- 21,505 grup
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_name TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    chapter_local_test_no INTEGER,
    chapter_index INTEGER DEFAULT 0,
    first_page INTEGER,
    last_page INTEGER,
    page_count INTEGER,
    UNIQUE(book_name, group_id)
);
```

## Cevap Kaynaklari (v3.5)
| Kaynak | Sayi | Oran |
|--------|------|------|
| Kitap eslestirme (Tier A-D) | 58,942 | %76.2 |
| AI crossval/bayes | 17,585 | %22.7 |
| AI crop solve (yeni kitaplar) | 809 | %1.0 |

## Version History
- v1.0: 36,967 -> v2.4: 86,249 -> v3.0-v3.4: 76,527 -> **v3.5: 77,336**
- v3.4->v3.5: +809 eklendi (4 yeni kitap, AI crop solve ile)

## Onemli Kurallar
- Eslestirme dogruysa kitap cevabi ground truth — AI dogrulama gereksiz
- db_v7 (%39) ve rematch (%25) kaynakli cevaplar SILINDI
- Chi-square 4,226 = Edebiyat kitaplarinin dogal yapisi, veri hatasi degil
- Turkce metin: HER ZAMAN NFC normalize + Turkish case mapping
