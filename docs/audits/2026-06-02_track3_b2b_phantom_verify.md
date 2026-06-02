# Track 3 (B2B Ürün-Hazırlık) — Phantom-Verify + Açık-Liste

**Tarih:** 2 Haziran 2026
**Amaç:** `2026-05-27_product_ready_roadmap.md` P0 listesi (27 May, stale olabilir)
canlı koda karşı doğrulandı — gerçek açık iş ile phantom ayrıldı.
**Yöntem:** 1 verify-ajanı + manuel grep, her iddia `dosya:satır` ile.

## PHANTOM (zaten yapılmış — aksiyon GEREKSİZ)

| İddia | Gerçek | Kanıt |
|-------|--------|-------|
| Retention push sadece log, beat'te yok | TAM wired | `push_tasks.py:59` gerçek INSERT + `celery_app.py:186` beat `crontab(20:00)` |
| AccessibilityProvider dead-code | Mount'lu | `App.tsx:205` (S179 F-P0-3) |
| KVKK veri silme/taşıma endpoint yok | VAR | `kvkk_privacy_api.py` `/export` + `/delete` + loader kayıtlı |
| Form raw-input label'sız (67 eksik) | 0 raw-input | Tüm formlar MUI TextField (otomatik label) |
| AGPL risk (ultralytics/PyMuPDF) | Hiçbir req'de yok | lazy import graceful-degrade |
| Kritik CVE'ler | Güncel pinli | aiohttp/cryptography/requests/urllib3/pillow/idna; python-jose kullanılmıyor |

→ product_ready_roadmap'in ~%75'i phantom (S197 meta-audit %87 bulgusunun tekrarı).

## GERÇEKTEN AÇIK

| # | Açık | Efor | Durum |
|---|------|------|-------|
| 1 | **Multi-tenant izolasyon** — tenant_id/org_id/RLS hiç yok | **L** | DESIGN gerek |
| 2 | **SSO (MEB/e-okul/SAML/OAuth)** — kod yok, authlib wire değil | **L** | DESIGN gerek |
| 3 | KVKK aydınlatma + gizlilik METNİ — sadece düz metin link | M | içerik + sayfa |
| 4 | ~~seed_database hardcoded admin123~~ | S | ✅ **FIXED** (`a8d318ec1`) |
| 5 | passlib 1.7.4 (dormant) + nltk 3.8.1 eski pin | S-M | bump/migrate |
| 6 | Login field-level validation (error/helperText) | S | UX/a11y |
| 7 | requirements-security-updates.txt stale/çelişkili | S | sil/güncelle |

## #4 FIXED (bu oturum)

`seed_database.py`: admin123/superadmin123 → `_resolve_admin_password()`
(env `SEED_ADMIN_PASSWORD`/`SEED_SUPERADMIN_PASSWORD` veya `secrets.token_urlsafe`
random fallback) + `main()` production guard (ENVIRONMENT=production'da demo seed
engellendi). Runtime test PASS, ruff temiz. `production_seed.py` zaten doğruydu.

## Karar gerektiren (Hüseyin)

**En kritik 2 B2B blocker (#1 multi-tenant + #2 SSO) L-efor + mimari karar gerektirir:**
- Multi-tenant: tenant model tasarımı (organization tablosu, tenant_id FK'lar, RLS
  vs app-level filtreleme), migrasyon stratejisi (167K soru + mevcut kullanıcılar)
- SSO: hangi sağlayıcı (MEB e-okul mu, genel SAML mı, e-devlet mi), kimlik eşleme

Bunlar `/brainstorm` + design doc + plan ister — körlemesine kod YAZILMAZ.
Küçük item'lar (#5/#6/#7) hızlı kapatılabilir ara işler.
