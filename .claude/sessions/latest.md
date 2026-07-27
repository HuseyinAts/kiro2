## Session Handoff — 2026-07-27 16:10

**Branch:** feature/self-evolution-optimization (upstream **kuruldu**, push edildi)
**Son commit:** `5f981a557` fix(auth): kayıt student_profiles.id == users.id değişmezini bozuyordu — **PUSH EDİLDİ**
**Uncommitted:** temiz
**Test durumu:** `pytest tests/e2e -m golden_flow` → **32 passed / 148 skipped / 0 failed** (30 baseline + 2 yeni bekçi)

### Yapılanlar

- **Satışa hazırlık yeniden doğrulama** (11 ajan, canlı stack + DB). Sabahki 7 blocker'ın **7'si de AÇIK, 0 fantom**. Üçü iddia edilenden geniş:
  - şema kaybı 1 tablo değil **131 tablo** (kök: `c555a10f4b93` upgrade()'inde 145 DROP TABLE)
  - roster değil **öğretmen modülünün tamamı** servis dışıydı (6/6 uç 500)
  - kalite sızıntısı cat_session'ın ~14 katı: `productive_failure` + `duel_api` + `osym_questions_api` sadece `is_active` → **85.731 soru**
- **Yeni bulgular:** GF paketi %83 skip (login 429 fixture'ları düşürüyor) · `golden-flows.yml` geçersiz YAML → 12 Nis'ten beri hiç koşmamış · `feature/**` hiçbir CI tetiklemiyor · pre-commit hook sır taraması OLMAYAN config'i çağırıyor (11 anahtar sızıntısının kök nedeni) · KVKK açık rıza 0 kayıt/77 kullanıcı · KVKK export'u `password_hash` sızdırıyor · ödeme sağlayıcısı SIFIR · `ENVIRONMENT=production` import anında çöküyor · yedek 2,5 ay eski + DB'nin tek kopyası bu makinede.
- **Kapı 1 / Adım 5 TAMAM (`7291645a7`)**: restore migration (billing_subscriptions, student_question_flags, teacher_classroom_students, teacher_exam_configs, teacher_assignments, teacher_contents) + `env.py include_object` DROP kapısı + `tests/e2e/test_db_schema_parity.py` (RED→GREEN).
  - Canlı: `/api/v1/billing/me` 500→**200**; `/api/v1/teacher/{classes,students,exams,assignments,contents,reports}` 6/6 500→**200**.
  - DDL öncesi tam yedek: `backups/kiro2_pre_schema_restore_20260727.dump` (976 MB, `pg_restore --list` 202 tablo ile doğrulandı).
  - alembic head: `restore_dropped_tables_20260727`.

- **Kapı 1 / Adım 6 TAMAM (`5f981a557`)**: `api/auth.py:631` `str(uuid4())` → `user_id` + 60 satır backfill (yedek tablo `student_profiles_bak_20260727`) + `tests/e2e/test_student_profile_id_invariant.py` (RED 60 → GREEN 0).
  - Canlı E2E: yeni kayıt 201 → profil `id == user_id` → `POST /osym-exam/beta-practice` **HTTP 200** (session oluştu). Test hesabı silindi, sayımlar 77/74/61'e döndü.
  - Bağımlı satır 0, FK'lar `ON UPDATE NO ACTION`, id çakışması 0 → backfill risksizdi.

### Engelleyiciler

- 11 anahtar (10 Google + 1 HF) hâlâ **rotasyona uğramadı** — yalnız Hüseyin yapabilir; geçmiş purge'ü ifşayı geri almaz.
- Force-push (purge klonu `C:\Users\husey\kiro2_purge.git`) kullanıcı tarafından REDDEDİLDİ, bekliyor.

### Sonraki Adımlar (satış planı sırası, maks 5)

1. **Kapı 1 / #7**: kalite kapısını 5 servise yay — `_safe_for_beta_gate()` helper'ı zaten var, benimsenmemiş. En büyük sızıntı `productive_failure_service`/`duel_api`/`osym_questions_api` (sadece `is_active`, 85.731 soru). *~6h*
2. **Kapı 1 / #8**: şifre kurtarma uçtan uca (`email_util.send_email` bağla + SMTP env + `HesapKurtarmaPage` mount + `SMTP_SERVER`/`SMTP_HOST` isim çatalını birleştir). *~8h*
3. **Kapı 1 / #9-10**: roster yazma uçları → 3 panoyu gerçek API'ye bağla (artık tablolar var). *~22h*
4. **Kapı 1 / #11**: `golden-flows.yml` satır 172 YAML fix + `feature/**` tetikleyici + GF skip-oranı bekçisi (%83 skip = yeşil hiçbir şey kanıtlamıyor) + `sympy` pin çakışması (pip-audit bloke). *~15h*
5. **Kapı 0**: anahtar rotasyonu (Hüseyin) + pre-commit hook'unu kök config'e çevir + günlük pg_dump otomasyonu. *~28h*

### Ayrı iş olarak kaydedildi (kapsam dışı bırakıldı)

- `repositories/user_repository.py:66` — `StudentProfile(id default=uuid4)` aynı kusuru taşıyor, hiçbir canlı endpoint çağırmıyor.
- Kalan ~125 kayıp tablo — DORMANT mı NO_WRITE_PATH mı triyajı.
- `coppa_parental_consents` + FERPA/COPPA router'ı — kaldırma kararı bekliyor (KIRO2 Türkiye-only).

### Kararlar (gelecek session tekrar tartışmasın)

- **Restore kapsamı**: yalnızca canlı kod yolu olan 6 tablo. Kalan ~125 kayıp tablo için "DORMANT mı NO_WRITE_PATH mı" triyajı ayrı iş — hepsini geri getirmek gürültü.
- **RLS bu migration'da YOK**: bu 6 tablonun `organization_id` kolonu yok, 79-tablo `tenant_isolation` deseni uygulanamaz. Politika icat etmek yerine kiracı izolasyonu iş emrine (GUC → kapsam → predicate) bırakıldı.
- **`teacher_classrooms` ve `coppa_parental_consents` kapsam dışı**: ilki canlıda mevcut; ikincisi FERPA/COPPA router'ının kaderi ayrı karar (G3 kaldırılmasını öneriyor — KIRO2 Türkiye-only, minor koruması KVKK veli onayı).
- **Sıra bağımlılığı**: RLS'te GUC beslemesi → kapsam → predicate flip. Ters sıra 153 router dosyasını anında boş sonuca düşürür.
