# M3 İskelet — İçerik Pipeline v1.2.1 Akış Tasarımı

**Tarih:** 28 Nisan 2026
**Durum:** TASARIM (henüz uygulanmadı, smoke test bekliyor)
**Tip:** Plan v1.2.1'in alt-seviye akış iskeleti (kod değil, spec)
**Plan referansı:** `.cursor/plans/20260427_icerik_pipeline_v1_2.md`
**Pre-pilot durumu:** PASS (commit `36549f9`, head `prepilot_m2_indexes_20260428`)
- M1 schema-only: `soru_hash`, MRQ, staging tabloları
- S1 backfill: 77.345 satır, 5K batch, ~5.8 dk
- M2 constraint+index: `soru_hash NOT NULL` + partial UNIQUE + lookup index

---

## 0. Pre-Flight

### 0.1 Bu doküman ne yapıyor

Plan v1.2.1 ana pipeline'ı yüksek seviyede tarif ediyor (mimari, conflict policy pseudo-kodu, mapping, risk matrisi). M3 iskeleti **somut akış**ı veriyor: hangi modül ne alır ne döner, conflict policy kodu nasıl yazılır, batch idempotency nasıl çalışır, hangi hata nereye düşer. Pilot script'in (Plan §10 madde 9: `pilot_500p.py`) oturacağı çatı.

### 0.2 M3 ne DEĞİLDİR

- Pilot script'in kendisi değil — bu doküman onun spec'i, kodu değil
- Plan v1.2.1'in revizyonu değil — onu somutlaştırıyor, çelişmiyor
- Yeni schema değişikliği değil — pre-pilot M1+S1+M2 fizik temeli kurdu, M3 onun üstünde davranış
- Çalıştırılabilir kod değil — fonksiyon imzaları + iskelet gövde

### 0.3 Pre-pilot ile bağ — schema → davranış

| Obje (commit `36549f9`) | Tip | M3'te kullanım |
|---|---|---|
| `question_bank.soru_hash` | VARCHAR(32) NOT NULL | Conflict lookup primary key |
| `uq_qb_soru_hash_active` | partial UNIQUE WHERE is_active=TRUE | Active duplicate koruma (Katman 1 INSERT garantisi) |
| `idx_qb_soru_hash` | non-unique | Genel lookup performansı |
| `manual_review_queue` | tablo | Conflict Katman 3 çıktısı |
| `question_bank_staging` | tablo | Pipeline batch staging (her sayfa burada başlar) |


---

## 1. Akış Diyagramı

```
        [PNG: veriseti/zkitap/<kitap>/sayfa_NNNN.png]
                          |
                          v
                 +------------------+
                 |  extract_page()  |  Opus 4.7, 1 PNG/cagri
                 +--------+---------+
                          | ExtractedPage (JSON)
                          v
                 +------------------+
                 |  validate_page() |  schema + anomali tespit
                 +--------+---------+
                          | ValidatedPage + flags
                          v
                 +------------------+
                 |  write_staging() |  question_bank_staging INSERT
                 +--------+---------+
                          | staging_status='pending', staging_batch_id=...
                          v
                 +----------------------+
                 |  resolve_conflict()  |  soru_hash lookup (DB read-only)
                 +----------+-----------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
   Katman 1            Katman 2            Katman 3
   layer=1             layer=2             layer=3
   target=             target=             target=
   'inserted'          'conflict_replaced' 'conflict_kept_old'
   yeni soru           eski kullanilmamis  kalibre/yanitlanmis
        |                   |                   |
        v                   v                   v
   apply_decision      apply_decision      apply_decision
   INSERT into         DELETE old +        INSERT into
   question_bank       INSERT new          manual_review_queue
                                                   |
                                                   v
                                          Huseyin manuel
                                          decision: keep_old / 
                                          replace / merge
                          
                          v
                 +------------------+
                 |  finalize_batch()|  toplama + summary + QA listesi
                 +------------------+
                          |
                          v
                  batch_summary.json
```

**QA örnekleme** (Plan §1.2: %1 random + %100 flagged):
- `%100 flagged`: `validate_page` `flags.needs_manual_review=True` işaretler
- `%1 random`: `finalize_batch` staging'den stratifiye sample seçer
- Manuel inceleme **akış dışı** (Hüseyin offline)


---

## 2. Modül Sınırları + Veri Sözleşmeleri

### 2.1 Modül listesi

| Modül | Çağrıldığı yer | Yan etki | Saf? |
|---|---|---|---|
| `extract_page(png)` | Pilot script ana döngü | Opus API call | Hayır |
| `validate_page(extracted)` | extract sonrası | Yok | Evet |
| `write_staging(validated, batch_id, conn)` | validate sonrası | DB INSERT (staging) | Hayır |
| `resolve_conflict(staging_id, conn)` | write_staging sonrası | DB SELECT | Hayır (read) |
| `apply_decision(decision, conn)` | resolve sonrası | DB INSERT/DELETE+INSERT/MRQ | Hayır |
| `finalize_batch(batch_id, conn)` | batch sonu | DB SELECT + dosya yazımı (summary) | Hayır |

### 2.2 Veri sözleşmeleri

```python
from typing import TypedDict, Literal


class ExtractedQuestion(TypedDict):
    position_on_page: int
    question_number_on_page: int
    question_text: str
    options: dict[str, str]                # {"A": ..., "B": ..., "C": ..., "D": ..., "E": ... | None}
    correct_answer: Literal["A", "B", "C", "D", "E"]
    has_diagram: bool
    is_real_exam_question: bool
    exam_year: int | None
    bloom_level_estimate: int              # 1-6
    difficulty_estimate: Literal["VERY_EASY", "EASY", "MEDIUM", "HARD", "VERY_HARD"]


class ExtractedPage(TypedDict):
    file_page: str                         # "0015"
    book_page_from_footer: int | None
    page_type: Literal["questions", "lecture", "chapter_cover", "unit_cover", "mixed"]
    test_no: int | None
    test_category: str | None
    subject_area: str                      # büyük harf, MATEMATIK/GEOMETRI/...
    primary_topic_code: str                # topic_hierarchy.code
    exam_type: Literal["AYT", "TYT"]
    questions: list[ExtractedQuestion]
    extraction_confidence: float           # 0.0-1.0
    page_notes: str


class ValidationFlags(TypedDict):
    schema_ok: bool                        # JSON şeması doğru
    has_anomaly: bool                      # extraction_confidence<0.7 vb.
    anomaly_reasons: list[str]             # ["low_confidence", "subject_area_invalid", ...]
    needs_manual_review: bool              # %100 flagged sample (QA)


class ValidatedPage(TypedDict):
    extracted: ExtractedPage
    flags: ValidationFlags


class ConflictDecision(TypedDict):
    staging_id: str
    soru_hash: str
    layer: Literal[1, 2, 3]                # 1=INSERT, 2=REPLACE, 3=KEEP_OLD
    target_status: Literal[
        "inserted",
        "conflict_replaced",
        "conflict_kept_old",
        "failed",
    ]
    existing_question_id: str | None       # Katman 2 ve 3 için
    keep_old_reason: str | None            # Katman 3 için
```

### 2.3 Modül imzaları (taslak)

```python
from pathlib import Path
from asyncpg import Connection


async def extract_page(png_path: Path, model: str = "claude-opus-4-7") -> ExtractedPage:
    """
    Tek PNG'den Opus okuması.
    JSON parse fail'de 1 retry farklı prompt; 2. fail RuntimeError.
    API timeout/5xx'de 3 retry exponential backoff (2s, 4s, 8s).
    """
    ...


def validate_page(extracted: ExtractedPage) -> ValidatedPage:
    """
    Saf fonksiyon — DB yok, API yok.
    Schema doğrulama + anomali kuralları:
      - extraction_confidence < 0.7 → needs_manual_review
      - subject_area enum dışı → has_anomaly + needs_manual_review
      - questions=[] ama page_type='questions' → has_anomaly
      - correct_answer şıkkı options'ta yok → has_anomaly
    """
    ...


async def write_staging(
    validated: ValidatedPage,
    batch_id: str,
    conn: Connection,
) -> list[str]:
    """
    question_bank_staging'e INSERT. Sayfadaki her soru için ayrı satır.
    Hash burada hesaplanıp staging.soru_hash kolonuna yazılır.
    Dönüş: oluşturulan staging_id listesi (UUID).
    staging_status='pending' başlar.
    """
    ...


async def resolve_conflict(
    staging_id: str,
    conn: Connection,
) -> ConflictDecision:
    """
    soru_hash lookup + 3 katman karar ağacı. DB-readonly bu adımda.
    Bölüm 3'teki tam kod buradan çağrılır.
    """
    ...


async def apply_decision(
    decision: ConflictDecision,
    conn: Connection,
) -> None:
    """
    Karara göre question_bank INSERT / DELETE+INSERT / MRQ INSERT.
    staging_status alanını da günceller.
    Her çağrı kendi transaction'ında (async with conn.transaction()).
    """
    ...


async def finalize_batch(
    batch_id: str,
    conn: Connection,
) -> dict:
    """
    Batch sonu özet üretir:
      - kaç inserted / conflict_replaced / conflict_kept_old / failed
      - QA örnekleme listesi (%1 random staging'den + %100 needs_manual_review)
      - failed sayfalar listesi (staging_status='failed' + failed_pages.csv birleşimi)
    Çıktı: batch_summary.json + qa_sample.csv
    """
    ...
```


---

## 3. Conflict Policy — Somut Python Taslağı

```python
async def resolve_conflict(
    staging_id: str,
    conn: Connection,
) -> ConflictDecision:
    """
    Karar ağacı (Plan v1.2.1 §5.4):
      - Hash yoksa              → Katman 1 (INSERT)
      - Hash var, kullanılmamış → Katman 2 (DELETE + INSERT)
      - Hash var, korunacak     → Katman 3 (KEEP_OLD → MRQ)

    "Korunacak" tanımı:
      is_calibrated=TRUE OR irt_calibrated=TRUE
      OR is_calib_pool=TRUE OR has_answers=TRUE
    """
    # 1. Staging kaydını çek (hash zaten yazılı)
    staging = await conn.fetchrow(
        """
        SELECT staging_id, soru_hash
        FROM question_bank_staging
        WHERE staging_id = $1
        """,
        staging_id,
    )
    if staging is None:
        raise ValueError(f"Staging row not found: {staging_id}")

    # 2. Tek SQL ile lookup — has_answers EXISTS subquery'siyle birlikte
    existing = await conn.fetchrow(
        """
        SELECT
            q.id,
            q.is_calibrated,
            q.irt_calibrated,
            q.is_calib_pool,
            EXISTS(
                SELECT 1 FROM student_answers sa
                WHERE sa.question_id = q.id
            ) AS has_answers
        FROM question_bank q
        WHERE q.soru_hash = $1 AND q.is_active = TRUE
        LIMIT 1
        """,
        staging["soru_hash"],
    )


    # 3. Karar ağacı
    if existing is None:
        return {
            "staging_id": staging_id,
            "soru_hash": staging["soru_hash"],
            "layer": 1,
            "target_status": "inserted",
            "existing_question_id": None,
            "keep_old_reason": None,
        }

    is_protected = (
        existing["is_calibrated"]
        or existing["irt_calibrated"]
        or existing["is_calib_pool"]
        or existing["has_answers"]
    )

    if not is_protected:
        return {
            "staging_id": staging_id,
            "soru_hash": staging["soru_hash"],
            "layer": 2,
            "target_status": "conflict_replaced",
            "existing_question_id": existing["id"],
            "keep_old_reason": None,
        }

    # Katman 3: korunacak — sebep stringini üret
    reasons = []
    if existing["is_calibrated"]:
        reasons.append("is_calibrated")
    if existing["irt_calibrated"]:
        reasons.append("irt_calibrated")
    if existing["is_calib_pool"]:
        reasons.append("is_calib_pool")
    if existing["has_answers"]:
        reasons.append("has_answers")

    return {
        "staging_id": staging_id,
        "soru_hash": staging["soru_hash"],
        "layer": 3,
        "target_status": "conflict_kept_old",
        "existing_question_id": existing["id"],
        "keep_old_reason": "kept_old: " + ",".join(reasons),
    }
```

`apply_decision` taslağı (kısaltılmış — gerçek kod 41 NOT NULL kolon mapping yapar, Plan §5.5):

```python
async def apply_decision(decision: ConflictDecision, conn: Connection) -> None:
    """Tek transaction içinde DB değişikliği + staging_status update."""
    async with conn.transaction():
        if decision["layer"] == 1:
            await _insert_to_question_bank(decision, conn)
            await _update_staging_status(decision["staging_id"], "inserted", conn)

        elif decision["layer"] == 2:
            await conn.execute(
                "DELETE FROM question_bank WHERE id = $1",
                decision["existing_question_id"],
            )
            await _insert_to_question_bank(decision, conn)
            await _update_staging_status(decision["staging_id"], "conflict_replaced", conn)

        else:  # Katman 3
            await _insert_to_mrq(
                old_question_id=decision["existing_question_id"],
                new_payload=await _staging_to_payload(decision["staging_id"], conn),
                reason=decision["keep_old_reason"],
                conn=conn,
            )
            await _update_staging_status(decision["staging_id"], "conflict_kept_old", conn)
```

`_insert_to_question_bank`, `_staging_to_payload`, `_insert_to_mrq`, `_update_staging_status` Plan §5.5'in 41 NOT NULL kolon mapping'ini kullanır — bu doküman onların kodunu içermiyor, pilot script işi.


---

## 4. Idempotency / Recoverability

### 4.1 staging_batch_id format

```
pilot_<kitap_slug>_<YYYYMMDD_HHMMSS>
örn: pilot_345_2025_ayt_matematik_20260429_143022
```

Bir kitap × bir başlatma zamanı = bir batch. Aynı kitabı yeniden başlatmak yeni batch_id üretir (zaman damgası farklı). **Resume** = aynı batch_id ile script'i tekrar çağırmak.

### 4.2 Resume mantığı

Pilot script crash veya manuel iptalden sonra `--resume <batch_id>` ile çağrıldığında:

```python
async def resumable_pages(batch_id: str, conn: Connection) -> set[int]:
    """
    Bu batch'te tamamlanmamış sayfaları döndürür.
    Tamamlanmış: staging_status IN ('inserted','conflict_replaced','conflict_kept_old')
    Tamamlanmamış (resume edilecek): 'pending', 'failed'
    """
    rows = await conn.fetch(
        """
        SELECT DISTINCT source_page
        FROM question_bank_staging
        WHERE staging_batch_id = $1
          AND staging_status IN ('pending', 'failed')
        """,
        batch_id,
    )
    return {r["source_page"] for r in rows}
```

Pilot başlangıç akışı:
```
if batch_id_already_exists(batch_id, conn):
    pages_to_process = all_pages - completed_pages
    log("Resume: {len} pages remaining")
else:
    pages_to_process = all_pages
    log("New batch: {len} pages")
```

### 4.3 Aynı batch içinde aynı hash 2+ kez

Aynı sayfa iki kere extract edilirse (resume sırasında) aynı `soru_hash` üretilir. `write_staging` aynı hash'i staging'e iki kez yazabilir — staging tablosu hash UNIQUE değil, kabul edilebilir. Sonra:

- 1. satır `apply_decision` Katman 1 olur, `INSERT` başarılı.
- 2. satır `apply_decision` Katman 2/3 olur (artık hash question_bank'ta var). Ama bu kayıt da bu batch'in kendi yarattığı kayıt — Katman 2'de DELETE+INSERT kendi kendini bozar.

**Önlem:** `resolve_conflict` lookup'ında `WHERE q.is_active = TRUE` zaten var; Katman 1 INSERT sonrası q.is_active=TRUE olur. 2. satır geldiğinde Katman 2 olur ve **az önce INSERT ettiği kaydı DELETE eder, sonra tekrar INSERT eder**. Sonuç: idempotent ama gereksiz IO.

**Pilot için kabul edilen davranış:** Resume oranı düşük olacağından (%5 altı tahmin) gereksiz IO ihmal edilebilir. Eğer pilot RESULT'ta yüksek resume görünürse, `write_staging` öncesi `staging_batch_id+source_page` ile dedup eklenir (ek SELECT).

---

## 5. Hata Kurtarma — Modül × Hata Türü Matrisi

| Modül | Hata Türü | Davranış | Çıktı |
|---|---|---|---|
| `extract_page` | API timeout / rate limit | 3 retry exp backoff (2s,4s,8s) | Hala fail → `failed_pages.csv` |
| `extract_page` | JSON parse fail | 1 retry farklı prompt | Hala fail → `failed_pages.csv` |
| `extract_page` | API 5xx | 3 retry | Hala fail → `failed_pages.csv` |
| `extract_page` | API 4xx (auth/quota) | Retry yok | Pilot durur (kritik) |
| `validate_page` | Schema mismatch (eksik alan) | flag + devam | `flags.has_anomaly=True` |
| `validate_page` | `extraction_confidence < 0.7` | flag + devam | `flags.needs_manual_review=True` |
| `validate_page` | `subject_area` enum dışı | flag + devam | `flags.anomaly_reasons += [enum_invalid]` |
| `validate_page` | `correct_answer` options'ta yok | flag + devam | `flags.anomaly_reasons += [answer_mismatch]` |
| `write_staging` | DB connection lost | 3 retry, sonra batch durur | Resume gerekir |
| `write_staging` | Constraint violation | Log + staging_status='failed' | Sayfa atlanır, devam |
| `resolve_conflict` | DB query fail | 1 retry, sonra status='failed' | Sayfa atlanır, devam |
| `apply_decision` | Katman 2 DELETE fail | Tx rollback, status='failed' | Sayfa atlanır, devam |
| `apply_decision` | INSERT fail (FK eksik vb.) | Tx rollback, status='failed' | Sayfa atlanır, devam |
| `apply_decision` | MRQ INSERT fail | Tx rollback, status='failed' | Sayfa atlanır, devam |
| `finalize_batch` | Hatalı sayım | Log uyarı, summary üret | Bilgi notu |

**Genel kural:** modül seviyesinde hata = sayfa atlanır, batch devam. Yalnız iki istisna:
- `extract_page` 4xx (auth/quota) → kritik, pilot durur
- `write_staging` DB connection lost → resume zorunlu

İki kayıt yeri vardır:
- `failed_pages.csv` → extract aşamasında düşenler (DB'ye hiç gelmedi)
- `staging_status='failed'` → staging sonrası düşenler (DB'de iz var)


---

## 6. M3 Kabul Kriterleri (Smoke Test)

M3 iskeleti **uygulandığında** aşağıdaki smoke test ile doğrulanır.
**Kapsam:** 5-10 sayfa Matematik kitabı, gerçek Opus + gerçek DB.

### 6.1 PASS kriterleri

| # | Kriter | Doğrulama yöntemi |
|---|---|---|
| 1 | İskelet imzaları çalışır koda dönüştürülebildi | Pilot script bu iskelet üzerine inşa edildi, runtime hata yok |
| 2 | Conflict policy 3 katmanın üçünü de gerçek veride üretti | `SELECT staging_status, COUNT(*) FROM question_bank_staging WHERE staging_batch_id=$1 GROUP BY 1` |
| 3 | Idempotency: aynı batch_id ile 2. çalıştırma no-op | Aynı `staging_batch_id` ile pilot 2. kez çalıştırılır → 0 yeni question_bank yazımı, 0 yeni MRQ |
| 4 | Hata kurtarma: API kesilirse pilot devam eder | Manuel test (network drop simülasyonu); `failed_pages.csv` doluyor, batch tamamlanıyor |
| 5 | İki kayıt yeri ayrımı çalışıyor | Smoke sonu `failed_pages.csv` ve `staging_status='failed'` ayrı kontrol |
| 6 | Backend regression yok | `/health` 5/5 + `/api/v1/osym/statistics` aynı `total` |

### 6.2 FAIL durumları → aksiyon

| Kriter | Olası sebep | Aksiyon |
|---|---|---|
| 1 | İskelet imzaları yetersiz | M3 v2 gerekli |
| 2 | Katman 2 veya 3 üretilmedi (5 sayfa hep Katman 1) | Smoke kapsamı 50 sayfaya genişlet |
| 3 | Resume logic eksik veya bozuk | Resume akışı + UNIQUE INDEX davranışı gözden geçir |
| 4-5 | Hata matrisi eksik | Modül × hata türü genişlet, retry sayıları kalibre |
| 6 | Schema migration kalıntısı | Rollback gerekebilir |

---

## 7. Açık Kararlar / Borçlar

| ID | Karar | Önerim | Bağlı |
|---|---|---|---|
| K-M3-1 | Pilot script konumu | `backend/scripts/pipeline/pilot_500p.py` (S1 backfill_soru_hash.py orada) | Pilot script yazımı |
| K-M3-2 | `extract_page` async mı sync mı? | Async (Opus API zaten async, paralel çağrı için kapı açık) | Throughput |
| K-M3-3 | DB connection: per-batch tek mi, modül başı yeni mi? | Per-batch tek + her `apply_decision` kendi `async with conn.transaction()` | Performans |
| K-M3-4 | QA örnekleme (%1 random + %100 flagged) hangi modülde? | `validate_page` flagged işaretler, `finalize_batch` random sample seçer | Plan §1.2 |
| K-M3-5 | Batch çalışırken backend canlı mı? | Evet — staging tablosu izole, production okumaları etkilenmez | Plan v1.2.1 R8 |
| K-M3-6 | Smoke test'te kullanılacak Opus modeli | `claude-opus-4-7` (60 sayfa baseline ile aynı) | Reproducibility |
| K-M3-7 | Pilot script çalışma yeri (CLI / sohbet / Claude Code) | İlk smoke bu sohbette MCP üzerinden, sonra Claude Code CLI | Plan §5.1 |

---

## 8. Sıradaki Adımlar

1. ✅ Hüseyin: M3 iskelet onayı (K2/K3/K4 — bu sohbette tamamlandı)
2. ✅ Claude: M3 iskelet dokümanı (`.cursor/plans/20260428_pipeline_M3_iskelet.md`)
3. ⏳ Hüseyin: M3 dokümanı gözden geçirmesi, K-M3-1...7 cevaplaması
4. ⏳ Claude (yeni sohbet veya bu): Pilot script yazımı (`pilot_500p.py`)
5. ⏳ Hüseyin: Smoke test (5-10 sayfa, M3 §6 kabul kriterleri)
6. ⏳ Claude: Smoke RESULT raporu (`.cursor/plans/<tarih>_pipeline_M3_smoke_RESULT.md`)
7. ⏳ Karar: PASS → 500 sayfa pilot başlat (Plan §10) / FAIL → M3 v2 revize

---

## 9. M3 Ne DEĞİLDİR (özet)

- ❌ Çalışır kod değil — pilot script onun ürünü, ayrı iş
- ❌ Plan v1.2.1'in revizyonu değil — onu somutlaştırıyor
- ❌ Yeni schema migration değil — pre-pilot M1+S1+M2 kapandı
- ❌ Smoke test sonucu değil — bu doküman tasarım, smoke ayrı RESULT
- ❌ 500 sayfa ana pilot değil — bu sadece akış iskeleti, ana pilot Plan §10
- ❌ QA workflow detayı değil — manuel inceleme akış dışı (Hüseyin offline)

---

## 10. Versiyon

**v1 (28.04.2026):** İlk yazım. Plan v1.2.1'in §3.1, §5.4, §5.5 bölümlerinin somut akış iskeleti. Pre-pilot M1+S1+M2 (commit `36549f9`) zemini üzerine kuruldu. İçerik: 6 modül × veri sözleşmeleri + conflict policy Python taslağı + idempotency mantığı + 15 satırlık hata kurtarma matrisi + 6 maddelik smoke kabul kriterleri + 7 açık karar.
