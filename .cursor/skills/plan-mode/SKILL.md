---
name: plan-mode
description: Cursor Plan Mode (Shift+Tab) için dinamik rehber. Kod yazmadan önce implementasyon planı üret, onay al, sonra uygula. KIRO2 değişikliklerinde default yaklaşım.
---

# Plan Mode — Kod Yazmadan Önce Plan

Cursor ekibinin **1 numaralı best practice**'i. Chicago Üniversitesi
çalışmasına göre deneyimli developer'lar kodlamadan önce plan yapıyor.
Agent'a concrete goal vermek, success rate'i dramatik artırıyor.

## Ne Zaman Yüklenmeli

- Kullanıcı karmaşık task açıklıyor (3+ dosya, yeni feature)
- "Nasıl yaparız?" sorusu
- Migration, refactor, mimari karar
- Plan Mode ikonu agent input'unda görünüyor

## Plan Mode Tetikleme

**Klavye:** `Shift+Tab` (agent input alanında)

**Alternatif:** Agent dropdown'ından "Plan" seç

**Otomatik:** Karmaşık task prompt'unda Cursor kendi önerir

## Plan Üretim Süreci

1. **Codebase araştırması** — Agent grep + semantic search ile ilgili dosyaları bulur
2. **Clarifying questions** — "Bu endpoint authenticated mi? Hangi role'ler?"
3. **Markdown plan üretimi** — dosya yolları, kod referansları, adım adım
4. **Senin review'ın** — inline düzenle, fazla adımları sil, eksikleri ekle
5. **Build** — Agent Mode'a geçiş, planı uygular

## KIRO2 Plan Template

Plan'ın şu bölümleri içermesi beklenir:

```markdown
# Plan: [task özeti]

## Araştırma Özeti
- İlgili dosyalar: [path'ler]
- Pattern referansı: [benzer endpoint/component path]
- Etkilenen tablolar: question_bank, users, ...
- Etkilenen endpoint'ler: /api/v1/...

## Uygulama Adımları

### 1. [Adım başlığı] — backend/app/models/X.py
- [ ] Model X'e Y kolonu ekle (nullable=False, default=Z)
- [ ] Unique constraint: (user_id, exam_id)

### 2. Alembic Migration — alembic/versions/XXX_add_y.py
- [ ] `alembic revision --autogenerate -m "add y to X"`
- [ ] CONCURRENTLY index (Session 120 dersi)
- [ ] `alembic upgrade head` dev DB'de test

### 3. API Endpoint — backend/app/api/v1/X.py
- [ ] Depends(get_current_user) + IDOR check
- [ ] Pydantic schema: CreateX, XResponse
- [ ] loader.py'de ROUTER_MAPPING kaydı

### 4. Test — tests/test_X.py
- [ ] Happy path
- [ ] IDOR koruması (başka kullanıcı resource'una erişim)
- [ ] Validation error (invalid payload)

### 5. Frontend — frontend/src/features/X/
- [ ] TanStack Query hook
- [ ] Component (store/authStore pattern)

## Edge Case'ler
- [ ] Kullanıcı yoksa (401)
- [ ] Resource yoksa (404)
- [ ] Rate limit aşımı (429)

## Test Stratejisi
- Unit: backend/tests/
- Integration: end-to-end user flow
- Regression: mevcut 916 test suite

## Rollback Planı
- Migration downgrade: `alembic downgrade -1`
- Feature flag varsa disable

## Tahmini Süre ve Risk
- Süre: ~2 saat
- Risk: düşük (mevcut pattern)
- Bağımlılık: yok
```

## KIRO2 Sağlık Kontrolü — Plan Onaylamadan Önce

Plan'da bunları arama:

| Kontrol | Arama | Neden |
|---|---|---|
| Doğru tablo | "question_bank" (77K) vs "questions" | Dual Table Trap |
| is_active filter | Query'de `.is_active == True` | 13K deprecated soru |
| IDOR | `resource.user_id == current_user.id` | Güvenlik |
| Router kayıt | loader.py'de ROUTER_MAPPING | 404 önleme |
| Migration | Alembic only, no raw DDL | Schema hijyeni |
| Middleware error | JSONResponse (HTTPException değil) | Session 148 |
| Async session | Context mgr vs generator doğru seçim | Session 78 |
| Türkçe string | turkish_upper/lower | I/ı problemi |
| IRT param | [-4, 4] / [0.2, 4] / [0, 0.35] | Algoritma integrity |

## Plan'ı Kaydet — Neden

`.cursor/plans/` altına kaydetmek:

- **Future context**: Sonraki agent session'da `@plan:<adı>` ile referans
- **Team knowledge**: Çalışma arkadaşları ne yaptığını görür
- **Interrupt-recovery**: Yarım kalan işe dönmek kolay
- **Audit**: Neden şu yaklaşım? Alternatifler neydi?

İsimlendirme: `YYYYMMDD_konu.md` (örn. `20260420_add_exam_submit_endpoint.md`)

## Planla Başa Dön — İteration

Agent plan uyguladı ama beğenmedin:

1. **Revert** değişiklikleri (git reset --hard HEAD veya Apply'ı geri al)
2. Plan dosyasını aç
3. Eksik/yanlış detayları düzelt
4. Agent'a "planı güncelledim, tekrar uygula" de

Takip prompt'larıyla düzeltmekten **hızlı ve temiz**.

## Ne Zaman Plan Mode Atlanabilir

- Tek satır bug fix
- Format/lint değişikliği
- Typo/comment düzeltme
- 10+ kez yaptığın mekanik task (örn. yeni test dosyası iskeleti)
- Daha önce approved bir plan'ın uygulanması

## Anti-pattern'lar

- **Plan'ı okumadan Build'e basmak** — agent yanlış varsayım yapmış olabilir
- **Çok genel plan** — "auth ekle" yerine "Depends(get_current_user) + IDOR check + rate limit 5/min"
- **Plan'ı hiç kaydetmemek** — team öğrenemez, future context yok
- **Plan'da clarifying soruları atlamak** — ilk seferde yanlış yön alır
