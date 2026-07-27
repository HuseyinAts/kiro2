## Session Handoff — 2026-07-27 06:20
**Branch:** feature/self-evolution-optimization (upstream takibi YOK — filter-repo `origin`'i kaldırdı, geri eklendi ama `-u` set edilmedi)
**Son commit:** 68a2aa6b3 fix(security): HEAD'deki iki sır izini kaldır + .archive'ı gitignore'a al — **PUSH EDİLMEDİ**
**Uncommitted:** temiz

### Yapilanlar
- **Satışa hazırlık denetimi** (canlı sistem + 19-ajan kod denetimi). Karar: **iki kapı da NO-GO** — B2B pilot ~6-9 hafta, genel satış ~4-6 ay.
- `backend/api/auth.py:1459` — `# TODO: Send email with reset link`. Token Redis'e yazılıyor, e-posta GİTMİYOR, kullanıcıya "gönderildi" deniyor. Konteynerde SMTP env yok. `/hesap-kurtarma` kayıtlı rota değil (`kiro/screens/GirisPage.tsx:337` sadece `<a href>`).
- `exam_sessions.student_id` → FK `student_profiles.id`, kod `users.id` yolluyor. DB: 74 profilin 60'ında `id <> user_id` → `/osym-exam/beta-practice` yeni kullanıcıda **500 ForeignKeyViolation** (canlı üretildi).
- `backend/api/billing_api.py:62` — `billing_subscriptions` tablosu DB'de YOK, migration zincirde ve `alembic_version` head'de → `/api/v1/billing/me` **500**. `alembic_version` gerçek şemanın güvenilir kaydı değil (aynı sınıf: `.claude/rules/windows-hnsw-build.md`).
- `backend/app/services/cat_session.py:263,299` — status-only filtre, `v_safe_for_beta` kullanmıyor → **9.855 soru kapıyı atlıyor** (34.982 vs 25.127). `/cat/next` canlıda kendi kendini cevaplayan bozuk soru döndürdü.
- **RLS fiilen KAPALI** (önceki oturumların "güçlü yan" kaydı YANLIŞ): politika `current_setting(...) IS NULL OR ...='' OR ...` → GUC yokken tüm satırlar geçer. Canlı: `SET ROLE kiro2_app` + GUC yok → `users` 77/77 görünür. `get_current_tenant` **153 router dosyasının 2'sinde**.
- 3 pano %100 mock / 0 API çağrısı: `ModernTeacherDashboard.tsx`, `ModernParentDashboard.tsx`, `ModernAdminDashboard.tsx` — üçü de giriş sonrası varsayılan iniş ekranı.
- `backend/app/api/teacher_classroom.py` — `POST /students` YOK → öğretmen sınıfına öğrenci ekleyemiyor (B2B çekirdek fiili).
- **Sır envanteri**: geçmişte 12 gerçek kimlik bilgisi (11 Google `AIzaSy…`, 1 HF `hf_…`) + `backend/.env (1)` içinde OpenAI/Anthropic. Hepsi GitHub'a push edilmiş.
- `68a2aa6b3` — `.archive/root_cleanup_20260402/question_gen_output.txt` silindi; `.gitignore` `archive/` deseni `.archive/`'i kaçırıyordu (KÖK NEDEN) → eklendi; `tests/fast/test_core_config_comprehensive.py` fixture'ı `AIza` önekinden arındırıldı (41/41 PASS).
- **Geçmiş purge HAZIR, PUSH EDİLMEDİ**: `C:\Users\husey\kiro2_purge.git` (209 MB). Doğrulandı: 21.904 blob **0 sır**, commit 1166=1166, kayıp yok, 6,0 GB→209 MB. Yedek: `C:\Users\husey\kiro2_backup_prepurge.git`.

### Fail Eden Testler
- Tam paket 15 dk'da BİTMİYOR (timeout %46'da). Kısmi: **5.023 pass / 109 fail / 2.719 skip (%35)**.
- Kırmızılar: `fast/test_webb_dok_classifier.py` (20F), `integration/health/test_health_api.py` (11F), `slow/test_phase1_berturk_comprehensive.py` (13F), `smoke/test_smoke_database.py`, `smoke/test_smoke_startup.py`, `test_api_contract.py` (5F).
- CLAUDE.md'deki "1.223 passed / 1 fail" tablosu gerçeği YANSITMIYOR.

### Engelleyiciler
- Force-push kullanıcı tarafından REDDEDİLDİ — purge klonu gönderilmeyi bekliyor.
- 12 anahtarın sağlayıcı konsollarından iptali SADECE Hüseyin yapabilir; purge ifşayı geri almaz.

### Sonraki Adimlar (maks 5)
1. **Anahtar rotasyonu** (Google×11, HF×1, OpenAI, Anthropic) — purge'den bağımsız, ertelenemez.
2. **Pre-commit sır tarayıcısı** (gitleaks/detect-secrets) — 12 anahtarın hepsini commit anında yakalardı.
3. Kiracı izolasyonu: `get_current_tenant` yayılımı ÖNCE, RLS fail-closed SONRA (ters sıra tüm sorguları 0 satıra düşürür).
4. `student_profiles.id` FK uyuşmazlığı — TDD, en ucuz görünür kazanç.
5. `cat_session.py` havuzunu `v_safe_for_beta`'ya çevir + regresyon testi.

### Kararlar (gelecek session tekrar tartismasin)
- **Purge kapsamı**: sırlar + build artefaktları BİRLİKTE. Tek başına sır purge'ü repoyu 6 GB bırakırdı, push düşerdi.
- **İki geçişli filter-repo ZORUNLU**: `--replace-text` tüm blob'ları akıtır → Windows `fast-import` "cannot truncate pack: Permission denied" ile düşer (84 MB nvidia wheel'de). Önce `--invert-paths` (4 sn), sonra `--replace-text` (15 sn).
- **`--mirror` KULLANMA**: yayımlanmamış 14 yerel WIP dalını (`claude/*`, `recovered-stash-*`, `archive/*`) GitHub'a açar. Sadece ortak 3 dal: `feature/self-evolution-optimization`, `master`, `recover/clean-main-wip-1261`. Uzaktaki 20 dependabot dalı eski sırlı geçmişi taşıdığı için silinmeli (Dependabot yeniden üretir).
- **Entropi ile sır sınıflandırma ATILDI**: gerçek OpenAI anahtarını "sentetik", sentetik test anahtarını "gerçek" saydı. Ölçüt = köken (gerçek .env/shell çıktısı mı, fixture mı).
- Push sonrası bu çalışma reposu yeniden klonlanmalı (hash'ler değişecek); `git push -u` ile upstream geri kurulmalı.
