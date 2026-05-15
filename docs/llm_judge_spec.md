# LLM Judge Spec v1

**Tarih:** 15 May 2026 (Session 161, Faz 5.5)
**Plan referansı:** [Quality Pool Plan v1](quality_pool_plan_v1.md) Faz 5-6
**Cost referansı:** [Cost Projection v1](cost_projection_judge_v1.md)
**Status referansı:** [Convention v3](quality_review_status_convention_v3.md) (`bronze_clean` → `auto_judged_high` veya `rejected`)
**Versiyon:** v1.0 (taslak — Faz 5.1 prompt ve Faz 5.3 calibration sonrası v1.1)

---

## 1. Amaç ve Kapsam

### 1.1 Tek cümle

Bronze pool'daki ~80K satırın her biri için Opus 4.7 + Gemini 2.5 Pro bağımsız "**bu soru ve cevap doğru, eksiksiz, çelişkisiz mi?**" yargısı verir; her ikisi de PASS verirse `auto_judged_high` (Gold), değilse `rejected` veya curator queue.

### 1.2 Scope

| Var | Yok |
|---|---|
| `quality_review_status='bronze_clean'` satırlar | `human_verified`, `auto_judged_high`, `rejected`, `archived` |
| Multiple-choice TYT/AYT formatı (5 seçenek A-E) | Açık uçlu, kompozisyon |
| Türkçe içerik | Yabancı dil (YDT henüz dışarıda) |
| Question text + options + book answer | Çözüm adımı / explanation üretimi (Faz 5.8 ayrı) |

### 1.3 Yapmadığı

- **Yeni soru üretmez** — sadece var olanı yargılar
- **Cevap düzeltmez** — sadece "doğru/yanlış/şüpheli" der; düzeltme curator işi
- **Kategori ataması yapmaz** — subject/topic/difficulty mevcut metadata kabul edilir

---

## 2. Input Contract

### 2.1 DB seçimi

```sql
SELECT id::text,
       question_text,
       option_a, option_b, option_c, option_d, option_e,
       correct_answer,           -- A | B | C | D | E
       subject_area,             -- 'MATEMATIK', 'TURKCE', ...
       exam_type,                -- 'TYT' | 'AYT' | 'YDT'
       question_image_url,       -- nullable; spec v1 image-LESS
       pipeline_metadata         -- JSON, audit input only
FROM question_bank
WHERE quality_review_status = 'bronze_clean'
  AND is_active = TRUE
ORDER BY md5(id::text || :run_id);
```

### 2.2 Per-call payload

```python
class JudgeInput(BaseModel):
    id: UUID                     # question_bank.id
    question_text: str           # NFC normalized
    options: dict[str, str]      # {"A": "...", "B": "...", ...}
    book_answer: Literal["A", "B", "C", "D", "E"]
    subject_area: str
    exam_type: Literal["TYT", "AYT", "YDT"]
    image_url: str | None        # spec v1 = always None (text-only)
    metadata_summary: dict       # {"source": "v3.5", "tier": "C"} - curator hint
```

### 2.3 Token budget per call

- Average: 351 input + 150 output tokens (cost_projection v1, n=20)
- p95: ~450 input
- Image: opt-in v2 (extra $0.0048/Opus + $0.0025/Pro per call)

---

## 3. Output Contract

### 3.1 Per-model raw verdict

Her iki model (Opus, Pro) bağımsız olarak şu JSON'u döner:

```json
{
  "model": "claude-opus-4-7" | "gemini-2.5-pro",
  "verdict": "PASS" | "FAIL" | "UNCERTAIN",
  "agreed_answer": "A" | "B" | "C" | "D" | "E" | null,
  "issue": null | "wrong_answer" | "ambiguous_question" | "missing_diagram"
         | "incomplete_options" | "ocr_garbage" | "off_topic" | "other",
  "confidence": 0.0,
  "reasoning": "1-2 sentences in Turkish."
}
```

**Şart:**
- `verdict=PASS` → `agreed_answer == book_answer` ve `issue is None`
- `verdict=FAIL` → en az 1 net hata: yanlış cevap veya yapısal eksiklik
- `verdict=UNCERTAIN` → şüpheli ama net hata yok (ör. seçenekler arası sınır vakası)
- `confidence` reasoning'i kalibre etmek için, threshold v1.1'de kullanılacak

### 3.2 Combined verdict (post-aggregation)

```python
class JudgeVerdict(Enum):
    PASS = "pass"             # both PASS, both agree on book_answer
    FAIL = "fail"             # both FAIL, same issue category preferred
    ESCALATE = "escalate"     # disagreement OR any UNCERTAIN
```

### 3.3 Status mapping

| Combined verdict | quality_review_status | curator queue |
|---|---|---|
| `PASS` | `auto_judged_high` (Gold) | hayır |
| `FAIL` | `rejected` | opsiyonel (spot audit) |
| `ESCALATE` | `bronze_clean` (değişmez) | evet (Faz 7.4) |

---

## 4. Verdict Logic

### 4.1 Aggregation table

| Opus | Pro | Combined | Sebep |
|---|---|---|---|
| PASS | PASS | **PASS** | İkisi de doğru bulup aynı cevabı seçti |
| PASS+answer X | PASS+answer Y | ESCALATE | İkisi de PASS ama farklı cevap (nadir, ~%1) |
| FAIL | FAIL | **FAIL** | İkisi de net hata gördü |
| FAIL | PASS | ESCALATE | Anlaşmazlık → curator |
| PASS | FAIL | ESCALATE | Anlaşmazlık → curator |
| UNCERTAIN | * | ESCALATE | Belirsizlik varsa atla |
| * | UNCERTAIN | ESCALATE | aynı |

**Beklenen dağılım** (cost_projection v1 Faz 5.4 holdout sonrası kalibre edilecek):
- PASS: %65-75
- FAIL: %15-20
- ESCALATE: %5-15

### 4.2 Issue category priority (FAIL durumunda)

İki model farklı `issue` raporlarsa, öncelik (ciddiyetten önemsize):

1. `wrong_answer` (kitap cevabı yanlış)
2. `incomplete_options` (5 seçenek yok veya boş)
3. `missing_diagram` (text "şekildeki" diyor ama image yok)
4. `ocr_garbage` (metin çözülemiyor)
5. `ambiguous_question` (birden fazla cevap savunulabilir)
6. `off_topic` (subject_area ile uyumsuz)
7. `other`

Reject metadata'sına `issue_primary` (en yüksek öncelikli) + `issue_all` (her iki modelden union) yazılır.

### 4.3 Confidence threshold (v1.1'de aktif)

v1: confidence sadece raporlanır, kullanılmaz.
v1.1 (Faz 5.3 calibration sonrası): `confidence < 0.6` → ESCALATE'e zorla.

---

## 5. Pipeline Architecture

### 5.1 Modüller

```
backend/scripts/judge/
├── prompt_v1.py        # Opus + Pro system + user prompts
├── client.py           # API wrappers (anthropic, google.generativeai)
├── aggregator.py       # Aggregation table from §4.1
├── runner.py           # Batch + ThreadPool + checkpoint (tier_i pattern)
├── postprocess.py      # DB UPDATE, audit log write
└── audit.py            # Sample N rows, human review TSV
```

### 5.2 Concurrency

[Tier I ThreadPool pattern](../backend/scripts/tier_i_reocr_apply_threaded.py) referans:
- `ThreadPoolExecutor(max_workers=10)`
- Per-call: 1 Opus call + 1 Pro call **paralel** (asyncio.gather veya 2 thread)
- Locks: stats Counter, checkpoint set, file write
- Checkpoint: `_pilots/judge_checkpoint_<run_id>.json`

### 5.3 Run ID

Her batch için unique ID: `judge_v1_<YYYYMMDD>_<batch_label>` (ör. `judge_v1_20260520_pilot1k`).
Audit trail bu ID üzerinden trace edilir, idempotent re-run için checkpoint key.

### 5.4 Rate limit budget

| Provider | Rate limit (paid) | Worker hedefi | Throughput |
|---|---|---|---|
| Anthropic Opus | 1000 RPM | 10 | ~30/dk safe |
| Gemini Pro | 1000 RPM (paid) | 10 | ~30/dk safe |

Per call ~13s (Tier I gözlem) → 10 worker × 4-6 call/dk = **40-60 satır/dk**.
Bronze 80K: ~22-33 saat tek sefer.

---

## 6. Calibration Plan (Faz 5.3 ön-kabul)

### 6.1 200-sample curated set (Faz 4.1)

Stratified:
- 50 exact match (book key + book answer + post-pipeline)
- 50 fuzzy match (substr 0.50-0.70 area)
- 50 fallback (no key, page-level)
- 50 v3.5 residual (legacy_v3_unaudited)

Hüseyin manuel `quality_label`: `correct` / `wrong_answer` / `ambiguous` / `garbage`.

### 6.2 PR curve

Run prototype on 200 set:
- True positive: `quality_label='correct'` AND combined `PASS`
- False positive: `quality_label!='correct'` AND combined `PASS`
- True negative: `quality_label!='correct'` AND combined `FAIL`
- False negative: `quality_label='correct'` AND combined `FAIL`

**F1 hedef:** ≥ 0.80 (ilk), ≥ 0.85 (stretch).

**Threshold tuning:** `confidence` cut-off, ESCALATE genişletme.

### 6.3 Holdout (Faz 5.4)

50 yeni curated set, judge spec v1.1 (calibre edilmiş) ile çalıştır. Hedef metrikler korunmalı.

---

## 7. Audit Trail

### 7.1 pipeline_metadata yazımı

Her judge çağrısı sonrası:

```json
{
  "judge_v1": {
    "run_id": "judge_v1_20260520_pilot1k",
    "ts": "2026-05-20T14:33:21Z",
    "combined_verdict": "PASS",
    "opus": {
      "verdict": "PASS",
      "agreed_answer": "C",
      "issue": null,
      "confidence": 0.92,
      "reasoning": "...",
      "tokens": {"in": 358, "out": 142},
      "latency_ms": 12450
    },
    "pro": {
      "verdict": "PASS",
      "agreed_answer": "C",
      "issue": null,
      "confidence": 0.88,
      "reasoning": "...",
      "tokens": {"in": 351, "out": 130},
      "latency_ms": 11800
    },
    "agreement": "match",         // match | answer_disagree | verdict_disagree | uncertain
    "issue_primary": null,
    "issue_all": []
  }
}
```

### 7.2 RESULT TSV

```
id  run_id  combined  opus_verdict  pro_verdict  agreed_answer  issue  cost_usd
```

Per-batch artifact: `_pilots/judge_<run_id>_RESULT.tsv` (~80K satır).

### 7.3 BACKUP TSV

UPDATE öncesi `quality_review_status` snapshot:

```
id  prev_status  prev_pipeline_metadata
```

Rollback için, Tier I pattern'i ile aynı.

---

## 8. Error Handling

### 8.1 Retry policy

| Error | Action |
|---|---|
| Network timeout / 5xx | 2 retry exponential backoff (1s, 4s) |
| 429 rate limit | Sleep 30s + retry (max 3) |
| Safety filter block (Gemini) | **Don't retry** — flag `gemini_safety_blocked` (Session 160 Geometri pattern) |
| Invalid JSON output | 1 retry with stricter prompt; if fail → ESCALATE with `parse_error` flag |
| API key invalid | Hard fail, exit 1 |

### 8.2 Geometri safety filter mitigation

Session 160 finding: 10/10 Geometri error sistematik (`response.text quick accessor` = `finish_reason != STOP`).

**Spec v1 stratejisi:**
1. İlk pass: standart settings ile çalıştır
2. Gemini safety blocked olanları ayrı pile'a yaz
3. Faz 5.8 (math judge) `safety_settings={HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_NONE}` ile retry
4. Halen blocked olanları curator queue'ya gönder (ESCALATE)

### 8.3 Failure isolation

Bir satırda hata = o satır ESCALATE, batch devam eder. Hata asla apply'a engel olmaz.

### 8.4 Checkpoint discipline

Tier I lesson ([smoke-test-checkpoint-trap memory](../C--Users-husey-kiro2/memory/feedback_smoke_test_checkpoint_trap.md)):
- Smoke test SADECE `--resume` ile (checkpoint overwrite riski)
- Pre-run: `cp checkpoint backup` zorunlu

---

## 9. Cost & Performance Budget

[Cost Projection v1](cost_projection_judge_v1.md) referans.

**Bronze 80K text-only:** $1,477 (Opus + Pro double, image hariç)
**Bronze 80K with image:** $2,061 (+%40 — v2 opsiyonu)

**Latency budget per call:** ≤ 15s p95 (Opus dominant, Pro daha hızlı)
**Throughput:** 40-60 satır/dk (10 worker, paralel Opus+Pro)
**Total runtime:** Bronze 80K = ~22-33 saat (rate limit izin verirse paralel 20 worker = 11-17 saat)

---

## 10. Acceptance Criteria

### 10.1 Pre-deploy (Faz 5.4 holdout sonrası)

- [ ] F1 ≥ 0.80 on 50-sample holdout
- [ ] False positive rate (kötü soru'ya PASS deme) ≤ %5
- [ ] Latency p95 ≤ 15s/call
- [ ] Cost projection sapması ≤ %10 (50 sample dry-run)
- [ ] Geometri error pile ≤ %5 (post-mitigation)

### 10.2 Post-deploy (Faz 6.4 audit sonrası)

- [ ] Random 100 sample post-judge audit hata oranı ≤ %8 (ilk), ≤ %5 (3 ay sonra)
- [ ] ESCALATE oranı %5-15 aralığında (curator yükü makul)
- [ ] False negative (judge fail ama doğru) ≤ %2 (Faz 6.6 reject pile audit)

### 10.3 Drift gates (Faz 7.5)

Her 1000 yeni Sapphire eklendiğinde re-calibration:
- F1 düşerse > 0.05 → prompt revize
- Issue dağılımı %30+ kayarsa → calibration set genişlet

---

## 11. Versioning

Spec semver:
- **v1.0** — bu dosya, taslak
- **v1.1** — Faz 5.3 calibration sonrası confidence threshold aktif
- **v1.2** — Faz 5.4 holdout sonrası prompt revize
- **v2.0** — image input opt-in, Faz 5.8 math hybrid entegre

Spec değişiklikleri `pipeline_metadata.judge_v1.spec_version` alanında trace edilir.

---

## 12. Open Questions / Future Work

| # | Soru | Karar tarihi |
|---|---|---|
| Q1 | Image input opt-in default mi olmalı? Cost +%40 ama recall artabilir | Faz 5.4 holdout sonrası |
| Q2 | "Aynı subject, farklı model" pattern var mı? Subject-stratified prompt? | Faz 5.3 PR curve sonrası |
| Q3 | Math judge (Faz 5.8) bu spec'ten bağımsız mı, integrated mi? | Faz 5.8 prototype sonrası |
| Q4 | ESCALATE pile için curator UI ayrı mı, mevcut queue'ya entegre mi? | Faz 3.x (curator UI) ile birleştir |
| Q5 | Gemini safety_settings BLOCK_NONE etik/güvenlik review gerekiyor mu? | EduTech context'te low risk, kararı doc'a yaz |
| Q6 | "Both UNCERTAIN" durumu rare olur mu, frequent mi? | Pilot 1K (Faz 6.1) gözlem |

---

## 13. References

- [Quality Pool Plan v1](quality_pool_plan_v1.md) — Faz 5-6 detayı
- [Cost Projection v1](cost_projection_judge_v1.md) — token + dollar budget
- [Convention v3](quality_review_status_convention_v3.md) — `bronze_clean` → `auto_judged_high`/`rejected`
- [Tier I ThreadPool pattern](../backend/scripts/tier_i_reocr_apply_threaded.py) — concurrency reference
- [Audit harness](../backend/scripts/audit_harness.py) — weekly 30-sample baseline
- [SymPy verifier](../backend/scripts/sympy_verifier.py) — math symbolic check (Faz 5.8 add-on)

---

*Faz 5.5 spec v1.0. Faz 5.1 prompt design + Faz 5.2 prototype + Faz 5.3 calibration sonrası v1.1 revize.*
