# B2B (Kurumsal/Okul) Satış-Hazırlık — Tasarım & Yol Haritası

*Tarih: 2026-07-03 · Yöntem: 6 boyut × canlı-kod keşfi + mimari tasarım + sentez (13 agent) · Go-to-market: Türkiye kurumsal/okul B2B (dershane/özel okul/MEB)*

## Genel Yargı: **B2B hazırlık ~%25**

B2C temeli sağlam (auth, KVKK veli-onay, yazılı güvenlik kodu) — ama **B2B çekirdeği (kurumsal veri izolasyonu) mimaride HİÇ YOK** ve 5/6 boyutun ön koşulu. Tek büyük yeni-inşa (multi-tenancy) + bir dizi "kod var, aktive et" işi.

## Boyut Olgunluk Karnesi (canlı-kod keşfi)

| Boyut | Olgunluk | İlk-müşteri blocker | Özet |
|---|---|---|---|
| Multi-tenancy | **YOK** | ✅ Evet | Tamamen tek-kiracılı. Organization/Tenant tablosu yok, hiçbir domain tablosunda `organization_id` yok, RLS yok. `school_name` sadece serbest-metin etiket. |
| RBAC / Okul hiyerarşisi | BAŞLANGIÇ | ✅ Evet | 5 düz rol (student/teacher/parent/admin) platform-geneli; okul-admin katmanı + roster/davet akışı yok. |
| SOC2 / Güvenlik | KISMİ | ✅ Evet | Zengin güvenlik kodu VAR ama **devrede değil**: audit logging wire-edilmemiş, CSRF/security middleware comment-out, config_validator enforce etmiyor. |
| KVKK / VERBİS | KISMİ | ✅ Evet | Veli-onay Faz2 var. Ama DSAR export stub (boş), silme/anonimleştirme job yok, RoPA/VERBİS besleyici yok, iki çakışan KVKK model katmanı (şema-drift), okul=sorumlu/KIRO2=işleyen (DPA) modeli yok. |
| Faturalandırma / Lisanslama | BAŞLANGIÇ | ✅ Evet | `is_premium` ikili bayrağı yalnız rate-limit'i etkiliyor; gerçek entitlement/seat/lisans/fatura yok — okula fatura kesip erişim veremiyorsun. |
| SSO / Kimlik (MEB) | BAŞLANGIÇ | ❌ Hayır | SAML servisi yazılı ama unwired + imza doğrulama stub'ı imzasızda `True` dönüyor. MEB e-okul bürokratik (Faz 2). İlk okul password/Google OAuth ile kapatılabilir. |

## En Büyük Riskler

1. **SESSİZ CROSS-TENANT PII SIZINTISI (en yüksek):** `organization_id` retrofit'i ~15-20 tabloya elle uygulanacak; tek sorguda filtre unutulursa A-okulu B-okulunun öğrenci PII'sini görür = anında KVKK ihlali. **Kod tabanının kendi geçmişi bunu kanıtlıyor** (lesson #31/#24 is_active sızıntıları: 55.768 rejected hâlâ is_active=true bulunmuştu — filtre-unutma sınıfı GERÇEK ve tekrarlayan). Mitigasyon: RLS ikinci savunma + zorunlu base-repo filtresi + leak golden flow.
2. **GÜVENLİK TİYATROSU:** "kod var" ≠ "çalışıyor". Audit logging bağlı değil, middleware kapalı, at-rest şifreleme 0 kolona bağlı, SAML imza stub'ı güvensiz. SOC2 wire-edilmiş değişmez audit olmadan imkansız.
3. **KVKK yasal:** DPA (veri sorumlusu/işleyen) modeli yok = B2B sözleşmesinin hukuki temeli eksik.
4. **PROD ŞEMA MİGRASYON:** 178-tablo prod'da VARCHAR-PK + NOT NULL backfill; ORM-first + 3-adımlı nullable→backfill→NOT NULL + backup zorunlu.
5. **SATIŞ ZAMANLAMA:** MEB SSO'yu ilk satışa bağlamak ölümcül gecikme (bürokratik, KIRO2 kontrolü dışı) → Faz 2.

## Yol Haritası

### Faz 0 — İlk-Okul MVP (satılabilir minimum, ~8-12 hafta, XL)
**Load-bearing omurga = multi-tenancy. Şu 5 kalem SIRALI:**
1. `organizations` + `org_memberships` ORM (id VARCHAR PK, users konvansiyonu) + alembic (ORM-first)
2. Tenant-owned ~15-20 tabloya `organization_id` FK: 3-adımlı nullable→`org_legacy_default` backfill→NOT NULL. **`question_bank` HARİÇ** (global salt-okunur katalog)
3. JWT `org_id` claim + `get_current_tenant` dependency + `repositories/base.py`'de **ZORUNLU** org filtresi (endpoint'te unutma riskini kaldırır)
4. `org_admin` rolü + okul-admin akışı (öğretmen davet, sınıfa öğrenci atama, roster)
5. Cross-tenant izolasyon Golden Flow gate: Okul-A→Okul-B 403/404, CI merge-block

**Paralel ucuz-yüksek-kaldıraç ("kod var, aktive et", çoğu S/M):** audit logging'i auth+veri-erişime wire · güvenlik middleware'lerini aç (HSTS/CSP/CSRF tek tek test) · config_validator fail-fast enforce · iki KVKK model katmanını konsolide et · şifrelemeyi fail-closed yap (base64 fallback sil) · KVKK aydınlatma-metni endpoint'i · DPA modeli + DPA-signed gate · minimum lisanslama (plans + organization_licenses + seat=aktif üye sayımı + havale/PO manuel fatura).

### Faz 1 — Ölçek + Güven (2.-5. okul, XL)
PostgreSQL RLS (yüksek-risk PII) · gerçek DSAR export + silme Celery task + RoPA/VERBİS · EncryptedString PII kolonlar (AES-256-GCM) + at-rest DB şifreleme · RBAC DB-persistence · SSO wiring (SAML imza gerçek XML-DSig, per-org IdP) · seat/feature enforcement + org_audit_logs (SOC2 izi).

### Faz 2 — Kurumsal Olgunluk (MEB, resmi denetim, XL)
MEB e-okul OIDC/SAML (resmi sözleşme bağımlı) · SCIM + Azure AD/Google Workspace · SOC2 Type II + pentest + tamper-evident audit · e-Fatura/GİB · Vault/KMS.

## KISS/YAGNI — KURMA (ilk okulu bloklamaz)
schema-per-tenant · Vault/KMS · metered/proration/dunning · iyzico/PayTR kart · RLS'i Faz 0'a çekmek · nested org · MEB'e bağlamak. Okullar yıllık koltuk bloğunu havale/PO ile alır.

## Tavsiye
Tek load-bearing yeni-inşa = tenancy omurgası (5 sıralı kalem). Diğer HER ŞEY buna asılır — omurga bitmeden başlamak boşa iş. Paralelde ucuz-aktivasyonlarla maturity'yi hızla yükselt. Billing'i minimum tut. SSO/MEB/RLS/SOC2-denetim ertelenebilir. Faz 0 ≈ XL / 8-12 hafta disiplinli **tek-akış** (paralel dev-workflow rate-limit yer — MEMORY dersi).

---

## Faz 1 tenancy ilerleme (2026-07-04)

### Katman A + grup-2: 13 data tablosuna org_id (18 toplam org-scoped)
- Katman A (9): exam_sessions, fsrs_cards/reviews/schedules, student_abilities, bkt_states, student_knowledge_states, performance_history, kvkk_consents.
- Grup-2 (4): learning_paths, topic_progress, user_theta, kiro2_learning_events.
- Desen: nullable org_id FK → backfill (user-join/direct-legacy) → NOT NULL + server_default. Tümü tek-kiracılı→legacy. TDD + canlı-regresyon-yok.

### RLS (Row-Level Security) — kuruldu + kanıtlandı + gate'li
- 13 data tablosuna `tenant_isolation` policy (permissive-when-unset) + FORCE ROW LEVEL SECURITY (migration faz1_rls_20260704).
- **KANIT (geçici non-superuser rol + SET ROLE):** org=A GUC → yalnız A satırı; org=B → yalnız B; GUC-boş → hepsi (permissive). RLS izolasyon mekanizması ÇALIŞIYOR.
- get_current_tenant → `set_config('app.current_org_id')` GUC wiring eklendi.
- **CANLI AKTİVASYON GATE'İ:** App `postgres` (superuser+bypassrls) → RLS şu an BYPASS (no-op, kırmıyor). RLS'i etkin kılmak için: (1) non-superuser DB rolü oluştur + GRANT, (2) DATABASE_URL o role çevir, (3) tam re-test (function/sequence privileges). Bu ayrı infra adımı. App-katman `_scope_tenant` (Faz 0) AKTIF savunma; RLS defense-in-depth.
- identity tablolar (users/profiles/org_memberships) RLS-dışı bırakıldı (özel auth akışları, ayrı değerlendirme).
