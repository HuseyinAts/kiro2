# Case Convention — Subject Area & Exam Type

Bu kural Session 133 kapsamlı audit sonucu oluşturuldu.
**Root cause:** BKT sessiz skip, DAG 0 eşleşme, prereq_blocked bypass — tümü case mismatch.

---

## Katmanlar ve Beklenen Case

| Katman | Örnek | Beklenen |
|--------|-------|----------|
| `question_bank.subject_area` (DB) | "MATEMATIK", "TURKCE" | **UPPERCASE** (plain str) |
| `topic_hierarchy.subject_area` (DB) | "MATEMATIK", "FIZIK" | **UPPERCASE** |
| `question_bank.exam_type` (DB) | "TYT", "AYT" | **UPPERCASE** |
| Frontend → Backend API | exam_type, subject | **UPPERCASE** (toUpperCase()) |
| BKT/IRT algoritma iç slug | subject_slug | **lowercase** ("matematik") |
| `SubjectArea` enum değerleri | SubjectArea.MATEMATIK | **lowercase** (.value = "matematik") |
| `FSRSCard.subject_area` (DB) | SubjectArea enum | **lowercase** enum değeri |
| DAG `get_subject_topics(subject_id)` | "MATEMATIK" | **UPPERCASE** (exact match) |

---

## Kurallar

### ✅ DOĞRU Kullanımlar

```python
# DB query — UPPERCASE
qb.subject_area = :subject  # {"subject": subject.upper()}

# DAG query — UPPERCASE (dag_service.py:243 defansif .upper() var)
dag.get_subject_topics(subject_id.upper() if subject_id else subject_id)

# BKT slug — lowercase (algoritma iç)
subject_slug = (row.subject_area or "matematik").lower()  # sinav.py
BKTService.record_answer(subject_slug="matematik")

# FSRSCard — SubjectArea enum (lowercase değer)
FSRSCard(subject_area=_SUBJECT_AREA_MAP.get(slug.lower(), slug.lower()))

# Fallback dict — UPPERCASE DB için, lowercase algo için
db_subject = subject_map.get(subject.lower(), subject.upper())  # doğru pattern
```

### ❌ YANLIŞ Kullanımlar

```python
# DB sorgusunda lowercase — KRITIK BUG
LOWER(qb.subject_area) = :subject  # ❌ YAPMA
qb.subject_area == "matematik"    # ❌ subject_map'siz

# DAG'a lowercase göndermek (artık defansif var ama yine de yapma)
dag.get_subject_topics(subject.lower())  # ❌

# q_meta["subject"] BKT'ye UPPERCASE gitmeli → bkt_service .lower() yapıyor
# Ama yine de BKT konvansiyonu gereği lowercase gönder
q_meta["subject"] = subject_area.upper()  # ❌ BKT expects lowercase slug
q_meta["subject"] = subject_area.lower()  # ✅ BKT pipeline lowercase
```

---

## Bilinen Wrapper Zincirleri

```
question_bank.subject_area (UPPERCASE)
    ↓ sinav.py:669 .lower()
    → BKTService.record_answer(subject_slug="matematik")
        ↓ bkt_service.py _slug_lower = slug.lower() (defensive)
        → _SUBJECT_AREA_MAP.get(_slug_lower)  # lowercase keys
        → SubjectArea enum lookup
        → FSRSCard.subject_area = "matematik"  # lowercase enum value

question_bank.subject_area (UPPERCASE)
    ↓ learning_path_v2.py:1267 .lower()
    → q_meta["subject"] = "matematik"
        → BKTService.record_answer(subject_slug="matematik")

topic_hierarchy.subject_area (UPPERCASE)
    → dag_service.get_subject_topics("MATEMATIK")
        ↓ dag.get_subject_topics(subject_id.upper())  # defensive
        → DAG node lookup UPPERCASE
```

---

## Hızlı Doğrulama Checklist

Yeni endpoint/service yazarken:

- [ ] DB'den gelen `subject_area` → DB query'de UPPERCASE, BKT'ye lowercase
- [ ] `topic_hierarchy.subject_area` → DAG query'de UPPERCASE
- [ ] Frontend'den gelen subject → `.toUpperCase()` ile DB query
- [ ] BKT `subject_slug` → her zaman lowercase
- [ ] `FSRSCard.subject_area` → SubjectArea enum değeri (lowercase "matematik")
- [ ] DAG `get_subject_topics()` → UPPERCASE veya dag_service defansif .upper() güvencesi

---

## Defansif Guard'lar (Mevcut)

| Dosya | Satır | Guard |
|-------|-------|-------|
| `dag_service.py` | 243 | `subject_id.upper() if subject_id else subject_id` |
| `bkt_service.py` | 316 | `_slug_lower = subject_slug.lower() if subject_slug else "matematik"` |
| `cat_session.py` | 68 | `_normalize_subject()` Turkish char + lowercase |
| `mastery_confidence_service.py` | 208 | `subject.upper()` |

---

*Oluşturulma: 2026-04-10 Session 133/134*
*Root cause commit: a4ef60f (bkt defensive), f6187cb (case fixes)*
