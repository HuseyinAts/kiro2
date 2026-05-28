## Session Handoff — 2026-05-28 (A3 a11y + KVKK scoping)
**Branch:** master
**Son commit:** 73cc5614f fix(a2): seed_admin import os
**Uncommitted:** temiz | **3 commit bu session — PUSH EDİLMEDİ**

### Yapılanlar (3 commit)
- `5fc6a7d11` feat(a3): kayıt formu WCAG a11y — ModernRegisterPage per-field error + autoComplete + aria-live + noValidate
- `0619bb070` feat(a3): ChatInput WCAG 4.1.2 — input aria-label + Send butonu aria-label + role=status
- `73cc5614f` fix(a2): seed_admin.py NameError — eksik `import os` (ruff F821 RED→GREEN)

### Verdict / canlı doğrulanan phantom'lar (roadmap 27 May fazla iyimser)
- AGPL paketleri requirements'ta YOK; AccessibilityProvider App.tsx:204'te MOUNT; soru_bankasi 14 endpoint auth TAM; seed_admin env-driven (sadece import os eksikti) → P0-4/P0-5/P1-2/P1-3 phantom
- A3 form a11y GERÇEKTİ → register + chat düzeltildi. Login zaten doğruydu. OSB toggle (useAccessibilitySettings hook + accessibility.css + DOM class) + modal focus trap (AccessibleModal+useFocusTrap, MUI native) ALTYAPI TAM → beta-blocker değil. *Tech-debt: SensoryControl vs useAccessibilitySettings ikisi de `.no-animations` toggle ediyor (acil değil).*
- KVKK backend MEVCUT (roadmap "hiç başlanmadı" = phantom): kvkk_consent_api (/give /withdraw /my-consents /check) + ferpa_coppa_compliance_api + parent_child approval + KVKKConsent/COPPAParentalConsent models. 503 shim S152'de kalktı. `student_profiles.veli_onay` (default FALSE) = minor rıza hook. COPPA `<13` cap → 13-17 için KVKKConsent.

### ⚠️ YENİ KRİTİK LEAD — KVKK Faz 1'i blokladı
**Register contract mismatch (muhtemel beta-blocker, DOĞRULANMADI):**
frontend `RegisterRequest` (`frontend/src/types.ts:187`) = {email, **password**, **ad**, **soyad**, rol, telefon?, okul_id?} → `authService.register` HAM gönderiyor (mapping YOK) → backend `KullaniciOlustur` (`backend/models.py:88`, /kayit + /register alias `api/auth.py:509,627`) = {email, **ad_soyad**, **sifre**, rol, aktif}. `ad_soyad`/`sifre` zorunlu ama frontend göndermiyor → registration muhtemelen 422. İzini süremediğim bir transform olabilir → STACK ile doğrula.

### Engelleyiciler (operatör aksiyonu)
- Dev stack DOWN (Frontend=000 Backend=000) → register mismatch + KVKK e2e doğrulanamıyor: `cd frontend && npm run dev` + backend
- PostgreSQL restart (A1): `Restart-Service postgresql-x64-18` (shared_buffers 4GB)
- GEMINI_API_KEY rotate (chat leak, AUP) | gh CLI yok → A2 CVE/Dependabot bloklu

### Sonraki adımlar
1. **Register mismatch'i stack ile doğrula** → kırıksa authService'te map (ad/soyad→ad_soyad, password→sifre). KVKK Faz 1 ön-koşulu.
2. KVKK Faz 1: dogum_tarihi + veli_email capture → users.birth_date + minor→veli_onay
3. KVKK Faz 2 (email+token; passwordless_auth.py reuse?) + Faz 3 (aydınlatma metni = kullanıcı/hukuk)
4. 3 commit'i push et
