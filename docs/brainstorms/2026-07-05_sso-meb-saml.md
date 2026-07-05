# Brainstorm: SSO (MEB/SAML) entegrasyonu

Tarih: 2026-07-05 | Domain: architecture | Perspektifler: Performans, Bakım, Maliyet

## TL;DR

Kapsam netleşti: MEB e-Okul entegrasyonu mühendislik sorunu değil, iş geliştirme/hukuk sorunu (resmi ortaklık gerektirir, LOI/pilot okul yok) — **dondur**, sadece kurumsal OIDC (Google Workspace/Microsoft Entra/Okta) ile ilerle, SAML2'yi MVP dışı bırak. Araştırma sırasında SSO'dan bağımsız **iki doğrulanmış canlı/potansiyel bug** bulundu: (1) mevcut "Google ile giriş" akışı gerçek JWT üretmiyor — `secrets.token_urlsafe(32)` rastgele string basıyor, kullanıcı login sonrası hiçbir korumalı endpoint'e giremiyor (router kayıtlı/canlı, ACİL fix); (2) `link_or_create_user` organization_id kontrolü yapmadan email'e göre hesap bağlıyor — kurumsal SSO'nun üzerine inşa edilecek zemin şu an cross-tenant hesap ele geçirmeye açık. Her iki bug da SSO kararından önce kapatılmalı.

## Top 5 Aksiyon

1. **enhanced_auth_api.py OAuth2 callback'i gerçek JWT üretecek şekilde düzelt** (`secrets.token_urlsafe` → `jwt_manager`/`create_access_token`) — Etki: 5/5 · Zorluk: kolay · Kaynak: Maliyet (bulgu, doğrulandı: router kayıtlı/canlı). **SSO'dan bağımsız, şimdi yapılmalı.**
2. **Kapsam kararı: MEB e-Okul entegrasyonunu dondur, sadece kurumsal OIDC (Google Workspace/Entra ID/Okta) ile ilerle, SAML2 MVP dışı** — Etki: 5/5 · Zorluk: karar (mühendislik değil) · Kaynak: Bakım+Maliyet konsensüsü.
3. **`link_or_create_user`'a organization_id/tenant kontrolü ekle** (cross-tenant account-takeover guard) — kurumsal SSO kodlanmaya başlamadan önce zemin güvenli olmalı. Etki: 5/5 · Zorluk: orta · Kaynak: Bakım (bulgu, doğrulandı).
4. **Per-tenant IdP config'i DB-backed yap** (`org_sso_configs` tablosu + client_secret encryption — şu an hiçbir yerde secret encryption yok, sadece `os.environ`) — Etki: 4/5 · Zorluk: orta-zor · Kaynak: Bakım.
5. **OAuth state store'u Redis'e taşı** (in-memory tek-process store, multi-worker/replica'da callback farklı worker'a düşünce "invalid_state" üretir) **+ JWT'ye org_id/rol claim'i kısa TTL ile göm** (DB round-trip azaltma, bkz. Çatışmalar) — Etki: 5/4 · Zorluk: kolay/orta · Kaynak: Performans.

## Konsensüs

- **OIDC-only, SAML2 MVP dışı**: Bakım ve Maliyet ayrı ayrı aynı sonuca vardı — üç hedef IdP (Google Workspace, Entra ID, Okta) da OIDC sunuyor; SAML (XML imza, metadata, sertifika) tamamen ayrı kütüphane + operasyonel yük, kod tabanında hiç iz yok.
- **Mevcut `oauth2_service.py` iskeletini genişlet, yeni auth dosyası açma**: Bakım açıkça söyledi (8+ dağınık auth dosyası zaten var); Performans zımnen aynı yönde — mevcut state/timeout desenini iyileştirmeyi öneriyor, sıfırdan yazmayı değil.
- **MEB e-Okul şimdilik dondurulmalı**: Sadece Maliyet dile getirdi ama diğer ikisi de bu kapsamı hiç ele almadı (konu dışı bıraktılar) — fiilen itirazsız.

## Çatışmalar

| Konu | Taraf A | Taraf B | Önerilen karar |
|---|---|---|---|
| Tenant/rol bilgisi nerede tutulsun | **Performans**: JWT claim'ine göm (org_id+rol), kısa TTL ile staleness'i kabul et — her istekte DB round-trip'i azaltır | **Mevcut mimari** (RLS + `get_current_tenant`): her istekte taze DB kontrolü, anlık-iptal/güvenlik önceliği | Şimdi **premature optimization** olabilir — 100K eşzamanlı yüke gerçekten yaklaşılmadan DB round-trip'in darboğaz olduğu ölçülsün; ölçülürse kısa TTL (5-15dk) + rol-değişikliğinde refresh-token invalidation ile hibrit uygulanabilir. |

## Perspektif Detayları

### Performans Mühendisi
- OAuth state store (`oauth2_service.py` satır ~917-935) tek-process in-memory dict — multi-worker/replica'da callback farklı worker'a düşünce state bulunamaz → login-storm'da retry fırtınası. **Öneri**: Redis'e taşı (TTL 10dk korunur). Etki 5, zorluk kolay, risk: Redis login path'inde hard dependency olur.
- `get_current_tenant`/`get_current_membership` her tenant-scoped istekte 2-3 ekstra DB round-trip yapıyor — 100K eşzamanlıda Postgres'e ağır yük biner. **Öneri**: SSO token mint anında org_id+org_role'u JWT claim'ine göm, kısa TTL ile sınırla (bkz. Çatışmalar). Etki 5, zorluk orta, risk: rol/org değişikliği TTL kadar gecikmeli yansır.
- Token-exchange `httpx.Timeout(30.0)` — kurumsal IdP dönem-başı login fırtınasında yavaşlarsa worker/event-loop bloke olur. **Öneri**: agresif timeout (connect 2-3sn/total 5sn) + circuit breaker. Etki 4, zorluk kolay, risk: yanlış-pozitif circuit-open tüm okulu aynı anda kilitler.
- **Kör nokta**: Okul-bazlı IdP metadata/JWKS process-local cache'lenirse, deploy/restart sonrası fleet genelinde eşzamanlı cache-miss stampede IdP'ye toplu istek atar → shared Redis-cached JWKS + background refresh gerekir.
- **Uyarı**: Her API isteğinde yetkiyi canlı IdP'ye introspect etme — local JWT mint + kısa TTL kullan, aksi halde IdP outage = platform outage.

### Bakım (Maintainability) Mühendisi
- Protokol kapsamını sadece OIDC'ye kilitle (bkz. Konsensüs). Etki 5, zorluk kolay, risk: SAML-only bir okul IdP'si gelecek borç olur.
- Per-tenant IdP config'i DB-backed yap (`org_sso_configs` + secret encryption). Etki 4, zorluk orta-zor, risk: yanlış tenant config'i sessiz login failure üretir — tenant-bazlı debug şart.
- Yeni servisi `oauth2_service.py` içine provider-tipi olarak ekle, yeni dosya açma (`OAuth2Provider` enum + `PROVIDER_CONFIGS` zaten genişletilebilir). Etki 5, zorluk orta, risk: dosya mega-dosyaya dönebilir.
- **Kör nokta (doğrulandı)**: `link_or_create_user` sadece email-eşleşmesiyle bağlıyor, organization_id kontrolü YOK — B2B SSO'da bir IdP başka kurumdan aynı email'i döndürürse cross-tenant hesap ele geçirme riski oluşur.
- **Uyarı**: SAML2 + OIDC'yi aynı sprint'te "genel destek" adına implement etmeye çalışma — iki kütüphane + per-tenant config + account-linking güvenliği + 8 mevcut auth dosyasıyla entegrasyon birlikte başlarsa test edilebilirlik çöker.

### Maliyet Analisti
- Sadece Google Workspace/Entra ID/Okta için genel OIDC — mevcut `oauth2_service.py` Authorization Code Grant iskelesini genişletmek ucuz; asıl maliyet domain→org_id JIT provisioning'in `org_memberships`/`get_current_tenant` üzerine yazılması. Etki 4, zorluk orta, risk (doğrulandı): OAuth2 callback şu an gerçek JWT üretmiyor — üstüne inşa edilirse SSO kullanıcıları hiçbir korumalı endpoint'e giremez.
- SAML2'yi kapsam dışı bırak — python3-saml gibi ayrı kütüphane + operasyonel yük, kod tabanında hiç iz yok. Etki 2 (talep varsayımsal), zorluk zor, risk: LOI/pilot okul talebi olmadan 2-3 haftalık iş.
- MEB e-Okul entegrasyonunu dondur — bu mühendislik değil iş geliştirme/hukuk sorusu, kamu API'sine özel şirket erişimi genelde kapalı. Etki/zorluk bilinmiyor (dış blocker), risk: spekülatif kod yazımı, sonuçsuz kalma ihtimali yüksek.
- **Kör nokta (doğrulandı)**: `unified_auth_service.py` (`os.getenv("JWT_SECRET", ...)` zayıf fallback) ile `core/dependencies.py` (`settings.jwt_secret_key`, farklı env var adı: `JWT_SECRET` vs `JWT_SECRET_KEY`) iki ayrı JWT secret kaynağı — doğrulama: `unified_auth_service.py` hiçbir router'a bağlı DEĞİL (dead code), bu yüzden şu an aktif değil ama ileride yanlışlıkla kullanılırsa "login başarılı, sonraki istek 401" sınıfı gizli hata üretir.
- **Uyarı**: Pilot okul/LOI yokken SAML/OIDC+JIT'i "genel platform özelliği" diye inşa etme — `org_api.py` zaten manuel email-ile-üye-ekleme sunuyor, faturalama/KVKK backlog'una göre fırsat maliyeti yüksek.

## Kör Noktalar & Uyarılar (birleşik + doğrulama durumu)

| Bulgu | Kaynak | Doğrulama |
|---|---|---|
| OAuth2 callback (`enhanced_auth_api.py`) gerçek JWT üretmiyor, `secrets.token_urlsafe(32)` basıyor | Maliyet | **CONFIRMED** — kod okundu, `jwt_manager` fetch edilip hiç kullanılmıyor. Router (`api.enhanced_auth_api`) `routers/loader.py`'de kayıtlı → canlı/erişilebilir. |
| `link_or_create_user` organization_id kontrolü yapmadan email'e göre bağlıyor | Bakım | **CONFIRMED** — kod okundu, sadece `User.email` eşleşmesi var. |
| `unified_auth_service.py` vs `core/dependencies.py` farklı JWT secret env var'ı okuyor | Maliyet | **CONFIRMED ama DORMANT** — `unified_auth_service.py` hiçbir api/router dosyasında import edilmiyor (grep 0 sonuç), şu an aktif zarar vermiyor. |
| OAuth state store in-memory, multi-worker'da kaybolur | Performans | Kod okundu (`_states: dict`), mantık doğru — canlıda kaç worker/replica koştuğu ayrıca doğrulanmalı. |
| IdP JWKS process-local cache stampede riski | Performans (kör nokta) | Henüz kod yok (gelecek tasarım riski), doğrulama N/A. |

**Genel uyarı**: SSO kararı MEB'e değil kurumsal OIDC'ye kilitlensin; SAML2 ve MEB entegrasyonu talep (LOI/pilot okul) olmadan başlatılmasın; SSO kodlaması başlamadan önce Top 5'teki 1 ve 3 numaralı fix'ler (fake token + cross-tenant account-linking) kapatılmalı.
