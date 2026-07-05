# Session Handoff — 5 Temmuz 2026 (S200 — Okul onboarding paneli, seçenek A)

**Branch:** feature/self-evolution-optimization · **HEAD:** `c7e87c688` (**PUSHED**, origin senkron)
**DB:** PG18 5434 kiro2 · Alembic head `kvkk_erasure_backup_20260704` — **bu iş MIGRATION İÇERMEZ** (org_memberships mevcut)
**Kapsam kararları (kullanıcı onaylı):** (A) MVP direct-management — e-posta DAVET YOK, mevcut kullanıcıyı yönet · (B) FE gate = platform `'admin'` rolü (FE UserRole enum'unda okul-admin rolü yok)

## Commit 1/2 — Backend TAMAM ✅ (`c7e87c688`, 4 dosya, +755/−6, pushed)

**Yeni endpoint'ler** (`backend/api/org_api.py`, prefix `/api/v1/org`, hepsi `require_org_role("SCHOOL_ADMIN")` + `get_current_tenant`):
- `POST /members` {email, org_role} → mevcut kullanıcıyı email ile ekle/reaktive (201)
- `PATCH /members/{user_id}` {org_role?, is_active?} → rol/aktiflik değiştir
- `DELETE /members/{user_id}` → soft-deaktive (204)
- Hata kodları: 404 email-yok/üye-yok · 409 zaten-üye/başka-kuruma-ait/koltuk-dolu/son-yönetici · 400 geçersiz-rol

**İş mantığı** (`backend/services/org_service.py`, yeni — billing_service deseni, raw async SQL):
- `add_member` / `update_member` / `remove_member` + `OrgMemberError(status_code, detail)` (endpoint HTTPException'a çevirir)
- Guard'lar: koltuk (yalnız STUDENT/TEACHER sayılır, `billing_service.seat_usage`) · son-SCHOOL_ADMIN lockout · cross-tenant claim (`LEGACY_ORG="org_legacy_default"` claim edilebilir, gerçek başka org edilemez)

**Adversarial review (3-lens workflow, 10 bulgu → 8 confirmed) — HEPSİ düzeltildi:**
| Bulgu | Sev | Disposition |
|---|---|---|
| Cross-tenant authz divergence — `get_current_membership` operated-org'a scope DEĞİLdi (LIMIT 1, no ORDER BY, GUC-öncesi) | HIGH | **FIX** `core/dependencies.py`: `Depends(get_current_tenant)` + `WHERE organization_id=:org` + `ORDER BY created_at`. TÜM org endpoint'lerini düzeltir. |
| Dual-membership yaratımı (claim LEGACY üyeliği bırakıyordu) | HIGH | **FIX** `org_service.add_member`: claim'de stale (başka org) aktif üyelikleri deaktive → tek-aktif-üyelik = users.organization_id |
| TOCTOU: seat / son-admin / dup-add | MED/LOW | **FIX** her mutasyonda `pg_advisory_xact_lock(hashtext(org))` (per-org serialize) + `IntegrityError→409` |
| Email case-sensitive lookup (lowercase saklanıyor) | LOW | **FIX** `.strip().lower()` |
| RLS GUC farklı session'da (mutation session'da inert) | MED | **KABUL/DOKÜMANTE**: mutation session'a org-GUC set EDİLMEZ (claim cross-org yazma içerir; GUC olsa RLS bunu görünmez kılar). İzolasyon = her sorguda açık `organization_id` filtresi. |
| "Gerçek org üyesi hijack" / "set_config swallowed" | — | **DISMISSED** (false positive, verify ile) |

**Doğrulama:** 19 TDD test (gerçek PG 5434, self-cleaning temp org) + billing/guard regresyon = **26 PASS**. `ruff` temiz (dependencies.py'deki 9 hata PRE-EXISTING, benim değil). `mypy` scoped temiz.
**Re-run:** `cd backend && python -m pytest tests/unit/test_org_members.py tests/unit/test_billing_dpa.py tests/unit/test_org_role_guard.py -q`

## Commit 2/2 — Frontend BEKLİYOR ⏳ (greenfield, henüz başlanmadı)
Model sayfa: `frontend/src/pages/ModernAdminUsersPage.tsx` (GlassCard + MUI Table + create Dialog + Fab + `apiClient` cookie-auth). Yapılacaklar:
1. `frontend/src/services/organizationService.ts` (yeni) — `apiClient` wrapper + local TS interface: getInfo, getMembers, addMember, updateMember, removeMember, getActivation, getLicense(seat), getDpa, signDpa. (`api.generated.ts` STALE ama GEREKMEZ — apiClient string-path kullanır.)
2. `frontend/src/pages/ModernOrgOnboardingPage.tsx` (yeni) — org bilgi header + DPA durum banner (+"İmzala" → `POST /org/billing/dpa/sign`) + koltuk metre (used/limit `GET /org/billing/license`) + üye roster (MUI Table, rol badge, aksiyon: rol değiştir/deaktive) + "üye ekle" Dialog (email+rol → `POST /org/members`, 409/404 handle)
3. `frontend/src/App.tsx` — lazy import + `<Route path="/admin/organizasyon" element={<ProtectedRoute requiredRoles={['admin']}><OrgOnboardingPage/></ProtectedRoute>}>` admin bloğuna (~577-657 arası)
4. Admin nav link — `frontend/src/components/Navigation/ModernNavigation.tsx` VEYA `RoleBasedNavigation.tsx` (admin bölümü)
5. `organizationService.test.ts` (vitest, apiClient mock)
Backend API kontratı: `/api/v1/org/info`, `/members` (GET/POST/PATCH/DELETE), `/org/billing/{activation,license,dpa}` (+dpa/sign). Auth = httpOnly cookie (apiClient `withCredentials`).

## Deferred (MVP dışı, ayrı iş)
E-posta davet akışı (hesabı olmayan öğrenci) · org oluşturma/operator provisioning · `PUT /org/info` düzenleme · DPA PDF artifact (şu an sadece signer metadata) · plan upgrade/seat_count set · KVKK delete-approve admin UI (backend hazır)

## Revert (gerekirse)
`git revert c7e87c688` (migration yok, temiz revert). Ya da 4 dosyayı 313c0cd6f'e döndür.

---

# Session Handoff — 4 Temmuz 2026

**Branch:** feature/self-evolution-optimization · **HEAD:** `313c0cd6f` (pushed, origin senkron)
**Backend:** durable image (rebuild'li), health 200, `kiro2_app` (non-superuser, RLS aktif)
**Alembic head:** `kvkk_erasure_backup_20260704`
**DB:** PG18 5434 kiro2 · question_bank ~187,835 · v_safe ~25,152

Bu oturum: **Multi-tenancy tamamlama + B2B + KVKK Faz B**. 5 iş akışı, hepsi kanıtlı/canlı/durable.

---

## ✅ Tamamlanan (bu oturum, commit sırası)

### 1. Operator RLS cutover (multi-tenancy artık GERÇEKTEN zorunlu)
- `.env.mvp:5` DATABASE_URL `postgres` → **`kiro2_app`** (non-superuser NOSUPERUSER NOBYPASSRLS) + backend/celery recreate
- Kanıt: app `current_user=kiro2_app super=False bypassrls=False`; RLS izolasyon fsrs_cards GUC=nonexistent→**0**/legacy→120 PASS
- GUC'yi `get_current_tenant` (core/dependencies.py) `set_config('app.current_org_id', org, true)` set ediyor
- Rol scripti: `backend/scripts/rls/create_app_role.sql` · Runbook: `docs/runbooks/rls_activation.md`
- `.env.mvp` gitignore'da (secret, commit edilmez). **Revert:** `.env.mvp:5`→postgres + recreate

### 2. Billing + organizations RLS (commit `5a7113b6a`, migration `faz1_billing_rls_20260704`)
- RLS+FORCE: organizations (scope=`id`), org_memberships, organization_licenses, data_processing_agreements, invoices
- `plans` HARİÇ (global katalog). İzolasyon PASS. Owner-only DDL → migration `postgres` override ile uygulandı
- **Toplam: 78 tablo org_id, 78 RLS** (73 + 5 billing/org)

### 3. B2B endpoint wiring (commit `75de6a3c5`)
- `backend/api/org_billing_api.py` — prefix `/api/v1/org/billing` (B2C `billing_api`=users.is_premium ile AYRI)
- Endpoint'ler: `dpa` (status/sign), `activation`, `license` (+seat/entitlement), `license/start-trial`, `invoices`
- **`require_dpa_signed` aktivasyon gate** (core/dependencies.py): DPA imzasız→403, start-trial bloke
- billing_service: `sign_dpa`/`start_trial`/`list_invoices`. Tenant-scoped (istemci org param YOK)
- E2E ALL PASS: DPA yok→403 / imzalı→200 / tekrar→409

### 4. KVKK Faz B — Md.10 + Md.11 (commit `9b92f7da6`)
- **Md.10 aydınlatma metni:** `backend/api/kvkk_notice_api.py` → `GET /api/v1/kvkk/notice` (+/version), public/rıza-öncesi
- **Md.11 export gerçek:** stub'dı (boş data+sahte URL) → `_collect_user_data` (information_schema'dan user_id'li TÜM tablolar) + private dosya + **AUTH-GATED** `GET /export/{id}/download` (public URL sızması giderildi)
- **2 pre-existing bug düzeldi** (export/delete'in neden "var ama 500" olduğu):
  - Drift: `kvkk_audit_logs` + `kvkk_data_deletion_requests` tabloları DB'de YOKtu → migration `kvkk_missing_tables_20260704` (modelden create + kiro2_app GRANT)
  - `settings.DATABASE_URL` → `settings.database_url` (yanlış attr)

### 5. KVKK Faz B — Md.7 silme executor (commit `313c0cd6f`, migration `kvkk_erasure_backup_20260704`)
- `backend/services/kvkk_erasure_service.py` `anonymize_user` — **anonimleştirme** (hard-delete DEĞİL, KVKK m.28; FK-güvenli)
- users PII (email→`erased_<h8>@anonymized.invalid`, ad/soyad/telefon/2fa/pw, is_active=false) + profil PII (veli_email/school_name/children_ids→NULL)
- Anonimleştirme ÖNCESİ orijinal PII → `kvkk_erasure_backup` (reversible + silme-kanıtı)
- Endpoint: `POST /delete/{id}/approve` (admin, executor dispatch) + `/reject`; `_require_admin` (role case-robust)
- **İnsan-döngüsü:** silme yalnız admin approve'la. Sentetik E2E ALL PASS, **gerçek veriye dokunulmadı**

---

## 🔧 State / Deploy
- Docker: backend + celery healthy, kiro2_app bağlantısı, RLS enforced
- Durable rebuild yapıldı (3 kez): tüm kod + migration image'a bake'li
- GF regresyon: 30 pass / 0 fail (her major değişiklikten sonra)
- MEMORY.md: 468→49 satır (119KB→7.1KB) kompakt edildi bu oturum başında

## ⚠️ Bilinen konular / Follow-up (ertelenen, sıradaki turlar)
1. **Delete executor UI yok** — approve/reject frontend butonu yok; operator şimdilik API'den onaylar. `reviewed_by` gerçek admin user ister (FK)
2. **B2B operator faturalama** — invoice OLUŞTURMA endpoint'i yok (sales-facing havale/PO); şu an sadece list
3. **Okul onboarding paneli** — org admin üye davet/CRUD + koltuk yönetimi frontend eksik (backend kısmen hazır)
4. **SSO (MEB/SAML)** — go-to-market açık şartı, henüz yok (en ağır iş)
5. Eski pending task'lar: #415 A11y/WCAG, #390 gh CLI/Dependabot (operatör)

## 🔁 Revert bilgileri (gerekirse)
- RLS cutover geri: `.env.mvp:5` → `postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2` + `docker compose --env-file .env.mvp up -d --no-deps --force-recreate backend celery-worker celery-beat`
- Migration'lar reversible: `alembic downgrade` (owner=postgres override ile). Erasure backup tablosu orijinal PII'ı tutar (anonimleştirme geri alınabilir)

## 📁 Dokunulan dosyalar (bu oturum)
- `.env.mvp:5` (kiro2_app, gitignore — commit edilmedi)
- `backend/api/`: org_billing_api.py (yeni), kvkk_notice_api.py (yeni), kvkk_privacy_api.py, org_api.py (yok, ref)
- `backend/services/`: billing_service.py, kvkk_erasure_service.py (yeni)
- `backend/core/dependencies.py` (require_dpa_signed)
- `backend/routers/loader.py` (org_billing_api, kvkk_notice_api kayıt)
- `backend/alembic/versions/`: faz1_billing_rls, kvkk_missing_tables, kvkk_erasure_backup (yeni migration'lar)
- Memory: MEMORY.md, project_rls-tenancy-cutover.md, project_kvkk-faz-b.md (yeni)

## ▶️ Sonraki adım (kullanıcı seçecek)
SSO / okul onboarding paneli / operator faturalama / içerik kalitesi (v_safe büyütme) / delete-UI.
Detay ve seçim: bir önceki AskUserQuestion'da 4 seçenek sunuldu (B2B go-to-market odaklı).
