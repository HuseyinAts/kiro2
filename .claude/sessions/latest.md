# Session — 3 Temmuz 2026: Satış-hazırlık + İçerik Uzman Paneli

**Branch:** feature/self-evolution-optimization · **Soru:** "proje satışa hazır mı + içerik kalitesi (disiplin uzmanları + ÖSYM)"

## ✅ Yapıldı (canlı doğrulandı)
1. **P0 DB (kritik blocker):** `postgresql-x64-18` STOPPED idi → boş docker pg15 5434'ü kapmıştı → platform HİÇ soru servis etmiyordu ("healthy/200" yanıltıcı). Fix: `docker stop turkiye_sinav_postgres_dev` + admin `Start-Service postgresql-x64-18` → question_bank=**187.835** (CLAUDE.md'deki 77K/192K yanlış), v_safe=25.165, backend reconnect.
2. **P1 Redis/celery:** kiro2-redis çalışmıyordu (turkiye_sinav_redis_dev 6379'u işgal). Fix: eski durdur → `docker compose up -d redis` → backend/celery restart → **celery healthy** (önce unhealthy), gaierror gitti.
3. **İçerik uzman paneli** (Workflow wf_dcd9146d, 24 agent, 12 branş+ÖSYM+adversaryal): verdict **KOŞULLU, ~%90.8 servis kalite / ~%9.2 ağırlıklı kusur.** Temiz EDEBIYAT(A-)/COGRAFYA(B+), kötü GENEL(F,%62)/TURKCE(D,OCR58)/GEOMETRI(D+). Rapor: `docs/audits/2026-07-03_content_quality_expert_panel.md`.
4. **İçerik P0/P1 uygulandı (reversible):** 13 doğrulanmış anahtar-hatası + 25 GENEL/FEN → is_active=false. Backuplar: `question_bank_content_panel_deact_backup_20260703` (13), `question_bank_content_panel_genelfen_backup_20260703` (25). v_safe 25.165→**25.127**. correct_answer DOKUNULMADI.
5. **GF canlı doğrulama** (161 endpoint curl sweep): yalnız **1 gerçek 500** = `GET /api/v1/reviews/` (student_reviews tablosu yok, üniversite-değerlendirme alt-sistemi hiç yaratılmamış, ikincil özellik). Diğer hepsi <500.

## ⏳ Kalan backlog (sonraki oturum — workflow-shaped)
- **P1:** student_reviews alt-sistemi → 503-shim veya universities/departments/... migration. GF pytest harness bug: `query_monitor_config.py:24` bare Histogram çift-import → idempotent guard ekle.
- **P2 içerik (Workflow):** TYT/AYT etiket denetimi (MATEMATIK/KIMYA) + tam-havuz garble taraması (char-trigram LM). TURKCE/GEOMETRI re-OCR. re-curate 23 ID: `backend/scripts/quality/_content_panel/recurate_ids.json`.
- **P2 B2B (design Workflow):** okul SSO/MEB, multi-tenant, SOC2/VERBİS — büyük ölçüde eksik, go-to-market blocker.

## 🔧 State
- Stack: PG18(5434, 187835 soru)+kiro2-redis+backend+celery(worker/beat)+frontend HEPSİ healthy. Health 200.
- **DİKKAT:** kiro2 compose 4-dosya merge drift'i (dev.yml turkiye_sinav_* duplike servisleri). Temiz çözüm: turkiye_sinav_* kaldır + tek `down`+`up`.
- Git: değişiklikler commit EDİLMEDİ (scriptler + audit doc untracked). DB değişiklikleri backup'lı uygulandı.
- Scriptler: `backend/scripts/quality/_content_panel/` (export/apply/branches).

## Sonraki tek adım
Kullanıcı seçsin: (a) P2 içerik remediasyon workflow'u (TYT/AYT relabel + garble scan), (b) B2B design workflow, (c) student_reviews shim+GF harness fix. Rate-limit: tek workflow.

## GÜNCELLEME (aynı oturum, P2 içerik "a" tamamlandı)
- **TYT/AYT relabel:** Workflow wf_83250ded (30 uzman) → 748 soru TYT→AYT (MATEMATIK 484+KIMYA 264, conf≥0.8), 67 keyword-FP TYT'de bırakıldı, 5 halüsinasyon-id guard'landı. Backup `question_bank_tytayt_relabel_backup_20260703`. v_safe exam_type 22918/2209→22170/2957. exam_type-only, reversible.
- **Garble taraması:** garble_char_lm.py tüm-aktif (110858) — ≥4.0 sadece 41 aday, servis(v_safe)=1 borderline → AKSIYON YOK (char-garble≈0; panelin "garble"si semantik/re-OCR işi). Garble efsanesi tekrar doğrulandı.
- Scriptler: `backend/scripts/quality/_content_panel/` (tytayt/, apply_tytayt_relabel.py, garble_served_ids.json) + `_garble_tmp/qb_full.tsv`.
- **Kalan sıradaki:** (b) B2B design workflow VEYA (c) student_reviews shim+GF harness fix VEYA TURKCE/GEOMETRI re-OCR (23 recurate_ids).

## GÜNCELLEME 2 (b tamamlandı — B2B design)
- Workflow wq7tmlsni (13 agent): B2B hazırlık **%25**. multi-tenancy=YOK (load-bearing, tüm B2B ön koşulu), RBAC/billing/SSO=BAŞLANGIÇ, SOC2/KVKK=KISMİ. Rapor: docs/audits/2026-07-03_b2b_readiness_design.md.
- Faz 0 (ilk-okul MVP, ~8-12hf XL): 5 sıralı tenancy kalemi (organizations+org_memberships → organization_id FK ~15-20 tablo [question_bank hariç] → JWT org_id+get_current_tenant+zorunlu repo filtre → org_admin rolü → cross-tenant leak GF gate) + ucuz-aktivasyonlar (audit-log wire, security middleware aç, KVKK konsolide, DPA modeli, min lisanslama havale/PO).
- En büyük risk: sessiz cross-tenant PII sızıntısı (kod tabanının is_active-sızıntı geçmişi bu sınıfı kanıtlıyor). Ertele: MEB SSO/RLS/SOC2-denetim/e-Fatura.

## GÜNCELLEME 3 (Faz 0 tenancy başladı — Step 1 + 2a)
- **Step 1** (commit 7a400b17d): organizations + org_memberships ORM + migration b1a2c3d4e5f6. VARCHAR PK, String enum-değil, FK CASCADE. TDD 3/3, information_schema doğrulandı. Additive (mevcut tabloya sıfır dokunuş).
- **Step 2a** (commit 8d1225f96): nullable organization_id FK kimlik çekirdeğine (users 76 + student_profiles 73 + teacher_profiles 0 + parent_profiles 1) + org_legacy_default backfill (0 NULL). Migration c2d3e4f5a6b7. FK RESTRICT. TDD 4/4. Regresyon yok (canlı health 200/login 401/reviews 404).
- **Alembic head:** c2d3e4f5a6b7. Geri alma: alembic downgrade (reversible, kayıpsız).
- **Kalan Faz 0 (ayrı turlar, sıralı):**
  - Step 2b: NOT NULL flip (kimlik çekirdeği, backfill %100 teyitli)
  - Step 2c: diğer ~76 tenant-owned tabloya org_id (user_id join'li backfill, tur tur, backup'lı) — VEYA org'u user_id join ile türet (RLS Faz 1)
  - Step 3: JWT org_id claim + get_current_tenant dependency + repositories/base.py ZORUNLU org filtresi + 4 ORM modele org_id kolonu
  - Step 4: org_admin rolü + okul-admin akışı (org_memberships.org_role)
  - Step 5: cross-tenant leak Golden Flow gate (Okul-A→Okul-B 403/404, CI merge-block)
- **80 tenant-owned aday tablo** tespit edildi (user_id/student_id/teacher_id kolonlu). En dolu: image_uploads 70K, chat_sessions 10K, refresh_tokens 4.8K.

## GÜNCELLEME 4 (Faz 0 Step 2b/3a — commit e81a1ed90)
- NOT NULL flip (faz0_notnull_20260703): 4 kimlik tablosu org_id NOT NULL (backfill-guard'lı).
- server_default='org_legacy_default' (faz0_orgdefault_20260703): CANLI 500 fix. NOT NULL sonrası eski register kodu org_id set etmiyordu → NotNullViolation (register 500, logdan teyit). Default ile eski INSERT'ler legacy-org alır → register 201.
- get_current_tenant dependency (core/dependencies.py): users.organization_id resolver, tenant'sız 403.
- TDD 10/10. Canlı: register 201/health 200/login 401. Alembic head: faz0_orgdefault_20260703.
- DERS: uydurma revision-id (d3e4f5a6b7c8) mevcut migration ile çakıştı → alembic cycle → benzersiz id kullan (faz0_*_20260703). NOT NULL + eski-kod = kırılma → server_default ZORUNLU.
- **Kalan Faz 0:** Step 3-enforce (repositories/base.py ZORUNLU org filtresi + 4 ORM org_id kolonu + JWT org_id claim) → Step 4 org_admin rolü (org_memberships.org_role) → Step 5 cross-tenant leak GF gate.

## GÜNCELLEME 5 (Faz 0 Step 3 — commit 2e96d6c7b)
- BaseRepository tenant scoping: __init__ organization_id opsiyonel + _scope_tenant helper → get_by_id/get_by_field/get_all ZORUNLU org filtresi (org_id None=backward-compat, global tablo muaf). hasattr(is_active) deseninin ikizi.
- 4 kimlik modeline ORM organization_id kolonu (DB Step 2 ile senkron).
- KRON MÜCEVHERİ: test_tenant_scoping_isolation 3/3 — org_A repo'su org_B'yi görmüyor (get_all+get_by_id), unscoped hepsini. Cross-tenant sızıntı savunması KANITLANDI. Tüm org testleri: 13/13.
- Canlı: health 200/login 401. ruff temiz. Ders: test-seed şema zorunlulukları (userrole UPPERCASE 'STUDENT', first_name/last_name NOT NULL) DB'den doğrulanmalı.
- **Kalan Faz 0:** Step 4 org_admin rolü (org_memberships.org_role + require_org_role) + okul-admin akışı (öğretmen davet/roster) → Step 5 cross-tenant leak Golden Flow gate (canlı endpoint 403/404 + CI) + JWT org_id claim + endpoint wiring (get_current_tenant'ı repo'lara bağla). Enforcement primitifi HAZIR, wiring kaldı.

## GÜNCELLEME 6 (Faz 0 Step 4 — commit 1372286b0)
- Backfill migration faz0_memberships_20260703: 76 user → 76 org_membership (0 orphan). users.role→org_role: ADMIN→SCHOOL_ADMIN vb. Dağılım 72 STUDENT/2 PARENT/1 TEACHER/1 SCHOOL_ADMIN.
- get_current_membership resolver + require_org_role(*roles) guard factory (SCHOOL_ADMIN süper-yetkili, yetkisiz/üyeliksiz 403). core/dependencies.py.
- TDD 4/4 role guard. Tüm Faz 0: 17/17. Canlı health 200/login 401. ruff temiz. Alembic head: faz0_memberships_20260703.
- **Kalan Faz 0 (Step 5, SON):** cross-tenant leak Golden Flow gate (canlı endpoint 403/404 + CI merge-block) + JWT org_id claim + get_current_tenant/require_org_role'u GERÇEK endpoint'lere wire (okul-admin CRUD: öğretmen davet/roster). Tüm primitifler HAZIR (get_current_tenant + repo _scope_tenant + require_org_role), kalan iş = endpoint wiring + leak GF + deploy.
- **Deploy notu:** Bu 6 commit'in kodu container'a HENÜZ deploy edilmedi (host+DB'de canlı, container eski kod çalışıyor — org_id kolonları nullable-default sayesinde eski kod kırılmadı). Step 5 sonrası clean rebuild + GF gate gerekli.

## GÜNCELLEME 7 (Faz 0 Step 5 — TAMAMLANDI, commit 646325966 pushed)
- api/org_api.py: GET /org/members + /org/info (referans wiring). org_id get_current_tenant'tan (istemci param YOK=yapısal cross-tenant güvence) + require_org_role + tenant-scoped sorgu. loader.py kaydı.
- Golden Flow gate: test_gf_org_members_tenant_scoped + _role_gated (CI merge-block).
- DEPLOY: 9 backend dosyası container'a (docker cp+restart).
- DEPLOY BUG yakalandı+düzeltildi: container ORM organizations FK çözemedi (NoReferencedTableError) → models/organization.py app-startup import yok → user_models.py'ye import eklendi. Host testleri kaçırdı (explicit import), yalnız canlı login 500 gösterdi.
- CANLI TEYİT: admin org/members 200 (kendi kurumu), org/info 200, student 403 (rol guard), login 200, health 200. Faz 0 unit 17/17.
- **FAZ 0 TAMAM (5/5):** Step1 tablolar→Step2 org_id retrofit→Step3 repo izolasyon(kanıtlı)→Step4 org_admin→Step5 wiring+leak GF+deploy. correct_answer/içerik dokunulmadı. 6 tenancy commit + push.
- **Kalan (Faz 1, ayrı):** diğer ~76 tabloya org_id, PostgreSQL RLS, JWT org_id claim (perf), gerçek okul-admin CRUD (öğretmen davet/roster), SSO wiring. Enforcement primitifleri hazır+deploy'lu.

## GÜNCELLEME 8 (#1 durable deploy ÇÖZÜLDÜ + latent register bug fix)
- FINAL rebuild (3 build: cache'li) → backend image 01:07 (tüm session kodu + auth.py fix baked). Backend + celery --force-recreate (docker cp YOK).
- KESİN durabilite testi: fresh-image recreate → login 200/admin org-members 200/student 403/register 201/reviews 404. Ephemeral risk GİTTİ.
- LATENT BUG: api/auth.py:584 register 'kullanicilar' (yok) sorguluyordu → 500. Oturum-öncesi commit a2da1dae4, hiç deploy edilmemiş (4-gün bayat container gizledi). rebuild açığa çıkardı. Fix kullanicilar→users. commit d549f3bd6.
- #2 DONE: GF harness in-process→canlı httpx (golden-flows.md). commit d549f3bd6.
- Kalan: #3 (76-tablo retrofit tasarımı) + #4 (tüm-havuz içerik tarama) — workflow ile.

## GÜNCELLEME 9 (#3 + #4 çözüldü — 4 açık madde TAMAM)
- #4 tüm-havuz içerik: 25.127 servis sorusu DETERMİNİSTİK tarandı (örneklem değil). ~%0 yapısal kusur (11 flag=false-positive: figure_orphan regex Türkçe şekilde/şekillenen/tablo-deyim substring yakaladı + 1 borderline garble). Deaktivasyon YOK (körü körüne silmedim). Panelin ~%9.2'si SEMANTİK (cevap-anahtarı/çeldirici) = blind-solve backlog, deterministik yakalanamaz. Script _content_fullscan/deterministic_scan.py.
- #3 76-tablo retrofit: staged tasarım (Katman A yüksek-PII→B analytics→C büyük/düşük-hassas + RLS Faz1). Tek seferde 80-tablo YASAK (=#1 risk). Backfill deseni user_id join.
- Rapor: docs/audits/2026-07-04_content_fullscan_and_retrofit_design.md.
- **4 AÇIK MADDE TAMAM:** #1 durable✅ #2 GF harness✅ #3 tasarım✅ #4 tarama✅.

## GÜNCELLEME 10 (semantik cevap-anahtarı ÖLÇÜLDÜ — kanıt-tabanlı)
- Blind-solve workflow wmwwzt222 (54 agent, 1330 stratified, key AYRI=kör): 1309 tahmin.
- ÖLÇÜLMÜŞ AGREE %96.8 (1250/1302). Branş: KIMYA/SOSYAL/MAT %97-99, EDEBIYAT %91 en düşük.
- 2. sinyal (17 hiConf disagree): 8 STORED_WRONG + 7 STORED_CORRECT + 2 AMBIGUOUS. A-bias dersi: tek-model disagree'nin %47'si gerçek.
- ÖLÇÜLMÜŞ anahtar-hatası %0.77 (2-sinyal) — panelin %9.2'sinin ~1/12'si. Panel ŞİŞİKMİŞ; servis anahtar-kalitesi ~%97-99.
- 8 STORED_WRONG + 2 AMBIGUOUS flag'li (pipeline_metadata.keyverify_*, backup question_bank_keyverify_flag_backup_20260704). correct_answer/is_active DOKUNULMADI (curator/3.-sinyal işi).
- Rapor docs/audits/2026-07-04_keyverify_blindsolve_evidence.md. Scriptler _keyverify/.
- **3 iz durumu:** semantik=ölçüldü(%97 sağlam, hedefli-dalga backlog) · Faz1 tenancy=tasarım hazır(Katman A sonraki) · B2B=%25 tasarım(DPA/billing sonraki).

## GÜNCELLEME 11 (EDEBIYAT hedefli tam-havuz dalgası)
- EDEBIYAT tam 1144 havuz kör-çözüldü (workflow w479x6edk, 46 agent). AGREE %98.0 (1099/1121) — 56-örnek %91.1 KÜÇÜK-ÖRNEKLEM GÜRÜLTÜSÜYMÜŞ, EDEBIYAT aslında ~%98.
- 2. sinyal (8 hiConf): 5 STORED_WRONG + 3 model-hatası. Doğrulanmış hata 5/1121=%0.45.
- Kümülatif 13 anahtar-hatası curator-flag'li (backup ×2), correct_answer DOKUNULMADI.
- KANIT: en kötü branş bile ~%98 anahtar-doğru → servis havuzu satış için sağlam.
- Scriptler _keyverify_edebiyat/. HEAD sonraki commit.

## GÜNCELLEME 12 (Faz 1 Katman A tenancy — yüksek-PII tablolar)
- 9 yüksek-PII tabloya organization_id retrofit (migration faz1_katmanA_20260704): fsrs_cards(120)/student_abilities(631)/bkt_states(28)/performance_history(15)/exam_sessions(27) + 4 boş (fsrs_reviews/schedules, student_knowledge_states, kvkk_consents).
- Desen: nullable→user-join+COALESCE-legacy backfill→NOT NULL→server_default. Tüm mevcut veri tek-kiracılı→legacy. FK→organizations RESTRICT.
- TDD 4/4 (NOT NULL + 0 NULL + FK + server_default). Canlı: health 200, NotNull ihlali YOK.
- NOT: /fsrs/flashcards/due 500 = ÖNCEDEN VAR OLAN bug (services/_deprecated/fsrs_service.py:253 db.query on AsyncSession, sync/async karışması testing.md#25), migration'la İLGİSİZ, _deprecated'te — cerrahi disiplinle dokunulmadı.
- Alembic head: faz1_katmanA_20260704. Reversible (downgrade).
- **Kalan Faz 1:** Katman A grup-2 (exam_sessions zaten yapıldı; learning_paths→lp_student_profiles, topic_progress, user_theta/kiro2_learning_events FK'siz) + Katman B analytics + Katman C büyük(image_uploads 70K) + RLS + ORM org_id kolonları(bu 9 tablo) + repo-scoping wiring.

## GÜNCELLEME 13 (Faz 1 RLS — kuruldu + kanıtlandı + gate'li)
- 13 data tablosuna RLS tenant_isolation policy (permissive-when-unset) + FORCE (faz1_rls_20260704).
- KANIT: geçici non-superuser rol + SET ROLE → org=A GUC yalnız A satırı, org=B yalnız B, GUC-boş hepsi. RLS izolasyon ÇALIŞIYOR.
- get_current_tenant → set_config('app.current_org_id') GUC wiring.
- GATE: app postgres=superuser+bypassrls → RLS şu an NO-OP (kırmıyor). Aktivasyon = non-superuser rol + DATABASE_URL değişikliği + re-test (ayrı infra). _scope_tenant (Faz 0) aktif savunma.
- Canlı: health/login 200. get_current_tenant değişikliği inert (superuser'da GUC no-op), sonraki rebuild'de gömülür.
- **Kalan Faz 1:** non-superuser rol infra (RLS aktivasyon) + Katman B analytics + Katman C image_uploads(70K) + bu 13 tabloya ORM org_id + repo-scoping wiring.

## GÜNCELLEME 14 (RLS aktivasyon infra — non-superuser rol KANITLANDI)
- kiro2_app rolü (NOSUPERUSER NOBYPASSRLS) + kapsamlı grant'lar (200 tablo SELECT + INSERT/UPDATE/DELETE + sequences + functions + default-privilege). Script backend/scripts/rls/create_app_role.sql (idempotent, committed).
- KANIT-1: kiro2_app olarak bağlanıp app sorguları (login/join/SELECT/INSERT-DELETE) çalıştı + RLS aktif (GUC=nonexistent→0 satır izolasyon, GUC-boş→hepsi permissive).
- KANIT-2 (CANLI): geçici override ile backend kiro2_app recreate → health/login 200 + GF sweep 162 endpoint 0 permission-500. App non-superuser'da kusursuz. Sonra postgres'e geri alındı (canonical), override silindi.
- Runbook: docs/runbooks/rls_activation.md (adımlar + revert + canlı-kanıt).
- **GATE:** durable aktivasyon = operatör .env.mvp:5 DATABASE_URL→kiro2_app flip + GUC-wiring rebuild (asistan .env* değiştirmez, guardrail). Cutover GÜVENLİ+kanıtlı.
- RLS artık: policy'ler kurulu + rol hazır+kanıtlı + GUC wiring commit'li. Tek eksik = operatörün 1-satır .env flip'i.

## GÜNCELLEME 15 (Faz 1 Katman B/C — kalan 60 tablo org_id)
- 60 tenant-owned tabloya org_id (migration faz1_katmanBC_20260704, programatik üretildi). topic_hierarchy HARİÇ (global taksonomi). Büyükler image_uploads 70K/chat_sessions 10K/refresh_tokens 4.8K + 30+ boş.
- Direct-legacy backfill → NOT NULL → server_default. 78/80 tenant-owned tablo org-scoped.
- Canlı regresyon YOK: login 200 (refresh_tokens server_default aldı), register 201, GF 0 yeni 500.
- **Kalan Faz 1:** RLS'i 60 Katman B/C tablosuna genişlet + 73 tabloya ORM org_id + repo-scoping wiring + operatör RLS-cutover (.env flip).
