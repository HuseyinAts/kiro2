# ORM Cluster 2 Sample-5 Re-verification — 27 May 2026

**Görev:** S155 baseline "Cluster 2 inverse-rule-of-seven" (41 kolon / 23 tablo) audit'inin sample 5 tablo ile production-risk doğrulaması.
**Tool:** `backend/scripts/audit_orm_schema_drift.py` (re-run, JSON diff vs baseline)
**Baseline:** `docs/audits/2026-04-12_orm-schema-drift-baseline.json` (12 Apr 2026, 41 findings)
**Live DB:** PostgreSQL 18.1 port 5434 `kiro2`

---

## TL;DR — Cluster 2 %100 PHANTOM

| Metric | Baseline (12 Apr) | Now (27 May) | Δ |
|---|---:|---:|---:|
| Cluster 2 (inverse-rule-of-seven) findings | 41 | **0** | **-100%** |
| Cluster 2 affected tables | 23 | **0** | **-100%** |
| Cluster 3 (int-vs-string) findings | 4 | 1 | -75% |
| Cluster 1 (orm-declares-missing-db-col) | 158 | 158 | 0 |
| **Total HIGH** | 203 | **159** | -22% |

**Sonuç:** Cluster 2 backlog ZATEN KAPALI. S155 baseline yazıldıktan sonraki 6 hafta içinde tüm 41 kolon model-level fix edilmiş ama baseline doc güncellenmemiş — klasik S197 meta-audit phantom pattern. Cluster 2 için P0 migration GEREKMİYOR.

**Aksiyon:** S155 baseline doc'a strikethrough + "FIXED 2026-05-27" notu eklenmeli (`docs/audits/2026-04-12_orm-schema-drift-baseline.md` lines 94-116 Cluster 2 bölümü).

---

## Sample-5 Doğrulama (read-only)

Sample seçim kriteri: en yüksek row-count (production-traffic proxy) + cluster 2 listesinden disjoint subject coverage.

| Tablo | DB rows | ORM declares | DB has | Verdict |
|---|---:|---|---|---|
| `kiro2_learning_events` | **254** | id/user_id/session_id **UUID** | uuid/uuid/uuid | ✅ ALIGNED |
| `kiro2_cat_sessions` | 8 | id/user_id **UUID** | uuid/uuid | ✅ ALIGNED |
| `topic_prerequisites` | 106 | id **UUID** (FK'ler Text intentional) | uuid + text/text | ✅ ALIGNED |
| `reasoning_cache` | 0 | id **UUID** | uuid | ✅ ALIGNED |
| `universities` | 0 | id **UUID** | uuid | ✅ ALIGNED |

**Kanıt — `backend/models/cat_models.py:8-12` (S155 fix yorumu):**
> "Session 155 Cluster 2 fix (inverse rule-of-seven): id / user_id / session_id columns declared `Column(String, ...)` but live DB has `uuid` columns. ... Fix is at the model declaration — no migration needed (DB already correct)."

Bu commit Cluster 2'nin S155 sonrası yapıldığını ve fix'in **model-side** (DB değiştirilmedi) olduğunu doğruluyor. Audit script JSON karşılaştırması: baseline'daki 41 finding'in 41'i de NOW=0.

Endpoint kullanımı (P0 risk konfirme):
- `kiro2_*` tablolar: `backend/api/analytics.py`, `backend/api/admin.py`, `backend/services/student_dashboard_service.py` — **production path** (eğer fix edilmemiş olsaydı her INSERT crash olurdu).
- `topic_prerequisites`: DAG service üzerinden okuma yapılıyor.

---

## Triage

| Kategori | Cluster 2 finding | Karar |
|---|---:|---|
| **P0** (production-risk, kolon kullanımda + DB mismatch) | **0** | ✅ Hiç yok, fix tamamlanmış |
| **P1** (latent / orphan) | 0 | — |
| **P2** (mock-only) | 0 | — |

---

## Genel Audit Durumu (bonus)

Cluster 2 sample-5 görevi kapsamı dışında ama re-run ortaya çıkardı:

- **Cluster 1 (university-info backlog): 158/158 hala open** — 15 tablo, en yoğun `dormitory_info` (30), `city_living_costs` (29), `scholarship_programs` (29). Tüm bunlar **cold** (0-traffic) — S155'in dediği gibi tek batch Alembic migration ile kapanır. P1.
- **Cluster 3 (int-vs-string): 1/4 kalmış** — sadece `osym_questions.bloom_level` (orm INTEGER, db varchar). P2 — bloom_level YKS audit'lerinde geçer, kontrol edilmeli.

---

## Migration Önerisi

Cluster 2 için **migration GEREKLİ DEĞİL** (zaten kapalı).

Tek kalan finding (`osym_questions.bloom_level`) için **uygulamayın**, sadece taslak:

```sql
-- DRAFT — NOT FOR EXECUTION
-- Choice A: align ORM to DB (preferred — bloom_level is a string label like "B2-Apply")
-- File: backend/models/osym_question.py
-- Change: bloom_level = Column(Integer) → bloom_level = Column(String(32))

-- Choice B: align DB to ORM (only if bloom levels are numeric 1-6)
-- ALTER TABLE osym_questions
--   ALTER COLUMN bloom_level TYPE INTEGER USING bloom_level::INTEGER;
-- (Will fail if any row has non-numeric value — audit data first.)
```

Karar için önce: `SELECT DISTINCT bloom_level FROM osym_questions LIMIT 20;` — string'se Choice A, sayı'sa Choice B.

---

## Lessons (S197 meta-audit lock için emsal)

1. **Audit doc'lar 6 hafta içinde stale olur.** S155 baseline tüm 41 Cluster 2 finding'i listeledi, S155-S180 arası sessizce hepsi fix edildi, baseline doc güncellenmedi. S197'deki "%87 phantom" pattern Cluster 2'de **%100**.
2. **Re-run her zaman tek source-of-truth.** Bu görev için pertinent action: yeni Cluster 2 dalgası açma → audit script `--fail` CI gate zaten Cluster 2'yi yakalar, manuel triage gereksiz.
3. **Baseline doc'lara strikethrough + tarih ekle** (S197 Mega Audit Lock kuralı): `docs/audits/2026-04-12_orm-schema-drift-baseline.md` Cluster 2 bölümü → ~~strikethrough~~ + "✅ FIXED 2026-05-27".

---

## Kullanılan dosyalar

- Backup script: `backend/scripts/_cluster2_sample_check.sql` (read-only SELECT)
- Re-run JSON: `%TEMP%/cluster2_recheck.json` (geçici, archive değil)
- Source: `backend/models/cat_models.py`, `reasoning_models.py`, `university.py`
