# Analyze — Tek Dosya Deep Analysis

Belirtilen dosyayı okur, yapısını anlatır, risk/iyileştirme noktalarını listeler.
`deep-audit` skill'inin hafif versiyonu — tek dosya için.

## Ne Zaman Kullanılmalı

- **Yeni codebase onboarding** — "Bu dosya ne yapıyor?"
- **Legacy dosya** — eski kod, commit hash'i kimse hatırlamıyor
- **Refactor öncesi** — mevcut yapıyı anlama
- **Code review öncesi** — PR'daki bir dosyayı detaylı kavrama
- **Debug başlangıcı** — bug ilgili dosyada mı?

## Ne Zaman KULLANMA

- Dosya zaten basit + iyi komentli
- 5+ dosyayı analiz etmek istiyorsan → `/review` veya deep-audit skill
- Specific soru varsa → direkt sor, analiz overkill

## Kullanım

```
/analyze backend/app/services/irt/calibration.py
/analyze frontend/src/features/exam/ExamPlayer.tsx
/analyze backend/alembic/versions/004_add_slug.py
```

## Agent Protokolü

Dosya path'i verildiğinde:

### 1. Dosyayı oku

Tam içerik, LSP tool'ları ile symbol listesi

### 2. Yapı özeti çıkar

```markdown
## Yapı Özeti

**Dosya:** backend/app/services/irt/calibration.py
**Satır:** 324
**Purpose:** IRT 3PL parametrelerinin MLE ile kestirimi

**Export'lar:**
- `estimate_ability(responses, items)` — MLE ability estimation
- `calibrate_items(responses_df)` — Joint item parameter estimation
- `IRTParameters` — Pydantic model

**Import'lar:**
- scipy.optimize (minimize)
- backend.app.models.question_bank
- backend.app.schemas.irt (IRTParameters)
```

### 3. KIRO2 Sağlık Kontrolü

Bu dosyanın bu alanındaki KIRO2 pattern'larına uyumu:

| Kontrol | Durum | Not |
|---|---|---|
| Dual Table (question_bank) | ✅ / ❌ | `from models.question_bank` var mı |
| is_active filtresi | ✅ / ❌ | Query'lerde `.is_active == True` var mı |
| IDOR koruması | ✅ / ❌ / N/A | Endpoint değil, N/A |
| Async session pattern | ✅ / ❌ | Doğru kullanım |
| Type hints | ✅ / ⚠️ | Coverage % |
| Docstring | ✅ / ⚠️ | Coverage % |
| Error handling | ✅ / ⚠️ | try/except + logging |
| Test coverage | ✅ / ⚠️ / ❌ | İlgili test dosyası var mı |

### 4. Risk ve İyileştirme Noktaları

```markdown
## Riskler (P0 → P2)

### P0 — Acil
- Satır 42: N+1 query pattern `for item in items: db.query(...)`
- Satır 89: NaN kontrolü eksik, IRT formülde math domain error

### P1 — Sprint İçinde
- Satır 120-145: Duplicate logic (calibrate_v1 + calibrate_v2 benzer)
- Tüm dosya: Error messages İngilizce (KIRO2 Türkçe standart)

### P2 — Teknik Borç
- Fonksiyon `_internal_solver` 85 satır — bölünebilir
- `# TODO: remove after v2` (commit a1b2c3 tarihi Session 50)
```

### 5. İyileştirme Önerileri

```markdown
## Öneriler

1. **Performance**: N+1 → batch query
   ```python
   # Mevcut (yavaş)
   results = [db.query(Q).filter(Q.id == i).first() for i in ids]
   # Önerilen
   results = db.query(Q).filter(Q.id.in_(ids)).all()
   ```

2. **Robustness**: NaN guard
   ```python
   if math.isnan(ability) or math.isinf(ability):
       raise ValueError("Invalid ability value")
   ```

3. **Türkçe error**: `"Parameter out of range"` → `"Parametre geçersiz aralıkta"`
```

### 6. İlgili Dosyalar

```markdown
## Related Files

- `backend/app/schemas/irt.py` — Pydantic tanımları
- `backend/app/models/question_bank.py` — Question modeli
- `tests/irt/test_calibration.py` — Test coverage
- `tests/irt/test_calibration_golden.py` — Golden dataset
- `.claude/skills/irt-validation/SKILL.md` — detaylı rehber
```

## KIRO2 Kategorileri

Dosyanın türüne göre farklı checklist uygulanır:

### Backend API endpoint (`backend/app/api/v1/*.py`)
- Depends(get_current_user)
- IDOR ownership check
- Pydantic request/response schema
- Rate limit decorator
- Router kaydı loader.py'de

### Backend Service (`backend/app/services/**/*.py`)
- Business logic izolasyonu
- DB session pattern (context mgr vs generator)
- Error handling + logging
- Unit test coverage

### Backend Model (`backend/app/models/**/*.py`)
- SQLAlchemy 2.0 pattern
- Relationship lazy loading strategy
- `__tablename__`, `__table_args__`
- Dual Table uyarısı (question_bank vs questions)

### Algorithm (`backend/app/services/{irt,fsrs,bkt}/**/*.py`)
- Parametrik sınırlar
- NaN/Inf koruması
- Test golden dataset referansı
- Benchmark + literature refs

### Frontend Component (`frontend/src/**/*.tsx`)
- Props interface + default export
- State management (store/ tekil)
- TanStack Query (API çağrısı varsa)
- Accessibility (aria-*, semantic HTML)
- Tailwind + dark mode

### Migration (`alembic/versions/*.py`)
- Reversible (downgrade dolu)
- CONCURRENTLY index (production tablolar)
- revision chain doğru
- Test: upgrade → downgrade → upgrade round-trip

## Örnek

```
/analyze backend/app/services/exam/scoring.py
```

Beklenen output: Yukarıdaki 6 bölüm + KIRO2 kategorisine (Backend Service)
göre özel checklist.

## Referans

- `.claude/skills/deep-research/SKILL.md` — multi-file araştırma
- `.cursor/skills/code-review/SKILL.md` — PR review protokolü
- `/review` komutu — değişiklik-bazlı review
