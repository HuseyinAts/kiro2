# W2 Cleanup — DEFER Rationale (Session 198)

**Tarih:** 2026-05-27
**Kapsam:** `_deprecated/` purge (W2.1) + Subject tag mismatch (W2.2)
**Status:** ⏸️ DEFER — sprint-level refactor gerek

---

## W2.1 — `_deprecated/` Purge: BLOCKED

### Discovery

| Konum | Dosya | Boyut |
|---|---|---|
| `backend/_deprecated/` | 3 | 11K |
| `backend/api/_deprecated/` | 1 | 5K |
| `backend/api/v1/_deprecated/` | 1 | 1K |
| `backend/core/_deprecated/` | 2 | 53K |
| `backend/models/_deprecated/` | 6 | 90K |
| `backend/services/_deprecated/` | 9 | 194K |
| `frontend/src/pages/_deprecated/` | 2 | 22K |
| `frontend/src/services/_deprecated/` | 1 | 1K |
| **TOPLAM** | **25** | **~377K** |

### Production Import Coupling

`grep -r "_deprecated" backend/ --exclude-dir=_deprecated` 5 dosya buldu:

| Importer | Imports | Pattern |
|---|---|---|
| `backend/core/automated_question_generator.py:3` | `core._deprecated.automated_question_generator` | re-export shim |
| `backend/models/learning_models.py:2` | `_deprecated.learning_models` | re-export shim |
| `backend/models/revolutionary_models.py:2` | `_deprecated.revolutionary_models` | re-export shim |
| `backend/models/__init__.py:204,228` | `_deprecated.learning_models + revolutionary_models` | re-export |
| `backend/api/team_challenges_api.py` (5 yer) | `services._deprecated.team_challenges` | try/import |

Frontend: 0 import (purge-safe).

### Karar — DEFER

Direkt silme = production kırılır. **3 import shim + 1 try/except refactor** gerek:

1. `core/automated_question_generator.py` shim → implementation'ı `core/`'e taşı
2. `models/learning_models.py` shim → impl `models/`'a taşı
3. `models/revolutionary_models.py` shim → impl `models/`'a taşı
4. `models/__init__.py` lines 204, 228 → güncellenen path'ler
5. `api/team_challenges_api.py` 5 yer try/import → tek refactor (TeamChallengeManager kalıcı home)

**Tahmin: 4-8 saatlik refactor sprint.** Şu an cost > benefit.

### Rollback Tag

`v-pre-deprecated-purge-20260527` oluşturuldu (HEAD = 9fe149dff S198 commit). Sprint başlamadan önce safety net.

### Sonraki Adım

- Sprint planlanması (yarım gün)
- Refactor yaparken: her shim için (kod taşı + import güncelle + test PASS) atomic commit
- En sonda `_deprecated/` tam sil + commit

---

## W2.2 — Subject Tag Mismatch: DEFER

### Discovery

Keyword-based heuristic (`auto_judged_high` only, `subject_area` = FIZIK/KIMYA/BIYOLOJI/EDEBIYAT/TURKCE/MATEMATIK):

```
 subject_area | math_kw | bio_kw | chem_kw | phys_kw | total
 BIYOLOJI     |      12 |     29 |      37 |      21 |   399
 EDEBIYAT     |       3 |      0 |       7 |      23 |   641
 FIZIK        |      38 |      2 |      48 |     266 |  1369
 KIMYA        |      41 |      4 |     227 |      60 |  1004
 MATEMATIK    |     443 |      2 |      30 |      75 |  4501
 TURKCE       |       5 |      1 |      33 |     121 |  2009
```

### Pure Mismatch (math-only in FIZIK)

| Subject | Suspicious (math kw + no physics kw) |
|---|---|
| FIZIK | **10** |

### Karar — DEFER

10 soru küçük sayı. Otomatik subject re-classify yüksek false-positive risk:
- "aritmetik" kelimesi fizik soruda da geçebilir (örn. aritmetik ortalama)
- Subject re-classify pipeline test gerektirir (multi_taxonomy_analyzer)

**Önerilen sonraki adım**: 10 FIZIK ID'sini Curator UI'a TSV olarak hazırla, insan pixel-verify yapsın. Sprint yerine 30 dk'lık görev.

### Genel Subject Tag Health

Cross-keyword density düşük (%5-10), büyük çapta mismatch yok. **Aciliyet yok.**

---

## S198 W2 Özet

| W | Konu | Status | Süre tahmini |
|---|---|---|---|
| W2.1 | `_deprecated/` purge | DEFER (5 importer refactor) | 4-8 saat sprint |
| W2.2 | Subject tag mismatch | DEFER (10 q, Curator) | 30 dk |

**Net etki**: Backlog dokümante edildi, rollback tag hazır, false-positive risk açıklandı. Diğer dalgalar (W1, W3, W4) işe yaradı.
