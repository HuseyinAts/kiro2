## Session Handoff — 2026-05-29
**Branch:** master | **Son commit:** 3013f273f docs(kvkk) Faz 2 tasarım spec (+ bu handoff'ta plan commit'lenir)
**Uncommitted:** docs/superpowers/plans/2026-05-29-kvkk-faz2-veli-onay.md (handoff commit'ine dahil)
**Stratejik yön:** Kurumsal/okul (B2B) satışı — tam roadmap A+B+C+D (auto-memory: project_go-to-market.md)

### Yapilanlar (bu session)
- **Durum analizi:** git + `docs/audits/2026-05-27_product_ready_roadmap.md` ile 28 May işleri (KVKK Faz 1, A2 CVE, A3 a11y, A1 DB) MEMORY drift'i tespit edildi (hook 77K stale)
- **Brainstorming (superpowers):** KVKK Faz 2 veli onay akışı → onaylı tasarım
- **Spec yazıldı + commit:** `docs/superpowers/specs/2026-05-29-kvkk-faz2-veli-onay-design.md` (3013f273f)
- **Plan yazıldı:** `docs/superpowers/plans/2026-05-29-kvkk-faz2-veli-onay.md` — 11 task TDD, placeholder'sız
- **Kod keşfi (doğrulanmış):** register=`api/auth.py:509` `kullanici_kayit` raw-SQL minor handling :528; `StudentProfile` → `models/database.py` (user_models DEĞİL); `passwordless_auth` reuse REDDEDİLDİ (in-memory/15dk/login-amaçlı)

### Fail Eden Testler
- YOK — bu session kod yazılmadı (tasarım+plan fazı). Plan'daki testler henüz implement edilmedi.

### Engelleyiciler
- `GEMINI_API_KEY` rotate ZORUNLU (AUP leak, önceki session) — operatör
- A1 PostgreSQL restart (shared_buffers 4GB) — operatör
- Integration testleri `USE_POSTGRES_TESTS=true` + dev DB (port 5434) gerektirir

### Sonraki Adimlar (maks 5)
1. **KVKK Faz 2 implementasyonu** — plan'ı yürüt (subagent-driven önerildi, kullanıcı seçimi bekleniyor)
2. Faz 2 Task 1'den başla: `veli_consent` model + migration (TDD)
3. Gated endpoint listesi grep ile netleştir (Task 8)
4. Operatör: GEMINI key rotate + PG restart + gh CLI install
5. KVKK B1 devamı (aydınlatma metni, veri silme/taşıma hakkı) — roadmap Faz B

### Kararlar (gelecek session tekrar tartismasin)
- Yaklaşım A seçildi: amaca-özel `veli_consent` tablosu (KVKKConsent Integer/orphaned-Base tuzaklarından kaçınır)
- Token: 7 gün DB-kalıcı, SHA-256 hash (plaintext sadece email); granted'da hash KORUNUR (idempotency + withdraw-by-token)
- Enforcement: sosyal/PII consent-gated, çekirdek öğrenme açık; veli hesabı YOK (tek-tık link)
- veli_onay UPDATE raw `text()` (register stiliyle tutarlı, StudentProfile ORM bağımlılığı yok)
