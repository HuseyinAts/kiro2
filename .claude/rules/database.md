# Veritabanı ve Soru Bankası Kuralları

> Bu dosya **her oturumda bağlama yükleniyor** (`paths:` frontmatter'ı yok).
> Kısa tut. Uçucu sayı yazma — **ölçüm komutu** yaz.

## 1. Bağlantı

| | |
|---|---|
| Motor | PostgreSQL **18.1** (`current_setting('server_version')`, 20 Ağu 2026) |
| Port | **5434** (varsayılan 5432 DEĞİL) |
| DB | `kiro2` · uygulama kullanıcısı `kiro2_app` · DDL için `postgres` |
| DSN | **`backend/.env`** — kimlik bilgisi bu dosyaya YAZILMAZ |

Kök `.env.development` legacy SQLite'a bakıyor, **kullanma**.

Salt-okunur ölçüm (Windows, Türkçe SQL için `-f dosya.sql` zorunlu):

```bash
"C:/Program Files/PostgreSQL/18/bin/psql.exe" -U postgres -p 5434 -d kiro2 -t -A -c "<SQL>"
```

## 2. 4 tablolu ayrışma

Legacy tek `questions` tablosu dörde bölündü (1:1, `id` ortak):

| Tablo | İçerik |
|---|---|
| `question_bank` | Çekirdek + durum (`soru_hash`, `primary_topic_id`, `is_active`, `review_status`) |
| `question_content` | `question_text`, `option_a..e`, `correct_answer`, `explanation`, `question_image_url` |
| `question_metadata` | `bloom_level`, `exam_type`, `subject_area`, `grade_level`, `pipeline_metadata` |
| `question_statistics` | `difficulty_level`, `irt_*`, `quality_score`, `quality_review_status` |
| `mv_safe_for_beta` | **Öğrenci/sınav motoru kapısı** (materialized view) |

⚠️ `question_image_url` **`question_content`'te**, `question_bank`'ta DEĞİL (split sonrası taşındı).

### Doğru sorgu kalıbı

```python
from models.question_bank import (
    QuestionBankItem, QuestionContent, QuestionMetadata, QuestionStatistics,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

stmt = (
    select(QuestionBankItem)
    .options(
        selectinload(QuestionBankItem.content),
        selectinload(QuestionBankItem.metadata_info),
        selectinload(QuestionBankItem.statistics),
    )
    .where(QuestionBankItem.is_active.is_(True))
)
```

İlişkiler `lazy='select'` → async oturumda eager-load YOKSA `MissingGreenlet`.
Kolon seçen sorguda (`select(Model.alan, ...)`) eager-load gereksiz — `Row` döner.

## 3. Kanonik değerler (ÖLÇÜLDÜ 20 Ağu 2026)

| Alan | Canlı kanon | Not |
|---|---|---|
| `review_status` | **`'approved'`** (lowercase) | `server_default` `'APPROVED'` diyor — **çelişiyor**, canlı dağılım kazanır |
| `quality_review_status` | `auto_judged_high` \| `pending` | kapıyı besleyen kolon |
| `is_active` | tümü `true` | ORM varsayılanı `False`, açıkça `True` yaz |

Bir alanın kanonu **üç yerden** gelebilir (ORM `default` · `server_default` · canlı
dağılım) ve üçü çelişebilir. Yazmadan önce **canlı dağılımı** sorgula.

## 4. Zorunlu filtreler

- Soru sorgusunda `is_active == True` **ZORUNLU**.
- Öğrenciye servis eden her yol **`mv_safe_for_beta`** kapısından geçmeli
  (`core/quality_gate.py`). `is_active`-only sorgu kaliteyi atlar.

## 5. Hacim ölçümü (sayıyı ezberleme, ÖLÇ)

```sql
SELECT (SELECT count(*) FROM question_bank)      AS bank,
       (SELECT count(*) FROM question_content)   AS content,
       (SELECT count(*) FROM question_metadata)  AS metadata,
       (SELECT count(*) FROM question_statistics) AS stats,
       (SELECT count(*) FROM mv_safe_for_beta)   AS kapi;
```

20 Ağu 2026 anlık değeri: `36967 / 36967 / 36967 / 36967`, kapı `27073`, yetim 0.

## 6. 🔴 KAPIDAKİ İÇERİK GEÇERSİZ — hacim bir VEKİL ÖLÇÜMDÜR

Yukarıdaki invaryantların **hepsi yeşil** ve içerik yine de servis edilemez.
Ölçüldü (19-20 Ağu 2026, iki bağımsız turda):

```
kapidan okunan soru        : 12 + 40  ->  servis edilebilir 0
gorsel URL dolu            : 0 / 27.073
metin sekil/grafik/tabloya atif yapiyor + gorsel yok : 4.584
student_coherent = true    : 36.967 / 36.967   <- tek deger = yargi HIC yapilmamis
difficulty_level = MEDIUM  : 36.967 / 36.967   <- adaptif sinyal YOK
irt_difficulty farkli deger: 1
```

**Gerçek korpus bu veritabanında değil:** aynı sunucuda `kiro2_temp`
(187.835 soru / 420 kitap / %96,7 görsel dolu / 68.022 farklı `irt_difficulty`).
İki havuz arasında **`soru_hash` kesişimi 0** — bugünkü kapı o korpustan türemiyor.
Crop görselleri diskte mevcut: `d-dataset/output/crops` → 528.651 PNG,
container'a `/app/static/crops:ro` mount'lu, DB URL'leri 8/8 dosyaya çözülüyor.

**Sonuç:** havuza dayanan bir işi "değer üretiyor" saymadan önce **örneklemi OKU**.
Satır saymak içerik hakkında sıfır bilgi verir.

## 7. Değiştirmeden önce

- `correct_answer` ve `is_active` **asla otomatik değiştirilmez**.
- >1000 satırlık UPDATE: pilot 30-50 örnek + audit + backup tablo + geri alma yolu.
- Yeni tablo → ÖNCE ORM model, SONRA `alembic revision --autogenerate`.
