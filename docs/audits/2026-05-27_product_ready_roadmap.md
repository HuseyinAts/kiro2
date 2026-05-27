# KIRO2 Product-Ready Roadmap (EdTech Beta Launch)

**Tarih:** 2026-05-27 (S198 sonrası)
**Kaynak:** S179 mega audit + S180 product-readiness audit + S181-S198 progress + EdTech 2026 industry criteria + KVKK research + live spot-verify
**Metod:** 2 paralel Explore subagent sentez + WebSearch (EdTech + KVKK) + canlı DB/git verify

---

## 1. Mevcut Durum Skor Kartı (12 Boyut)

| Boyut | Durum | Skor | Beta-blocker? |
|---|---|---|---|
| **Veri kalitesi** (içerik) | 🟢 İyi | 8/10 | Hayır — gold pool 13,595, %99 image, IRT 100% |
| **Backend fonksiyonel** | 🟢 İyi | 8/10 | Hayır — 1,163 endpoint, mock flag-gated |
| **Frontend build/UX** | 🟡 Orta | 6/10 | Kısmi — build PASS, ama a11y eksik |
| **Test coverage** | 🟡 Orta | 5/10 | Kısmi — %42.75 (hedef %80), pollution |
| **Security (auth/IDOR)** | 🟢 İyi | 7/10 | Hayır — IDOR kapalı, dual auth sağlam |
| **Security (CVE/deps)** | 🔴 Zayıf | 3/10 | **EVET** — ~60 CVE, AGPL risk |
| **Accessibility (WCAG)** | 🔴 Zayıf | 3/10 | **EVET** — provider unmounted, form a11y |
| **DB scalability** | 🔴 Zayıf | 3/10 | **EVET** — PG config 128MB, pool exhaust |
| **Observability** | 🟡 Orta | 5/10 | Hayır — health var, slow-query yok |
| **CI/CD** | 🟢 İyi | 7/10 | Hayır — 11 workflow, quality gate |
| **Compliance (KVKK)** | 🔴 Yok | 1/10 | **EVET** — VERBİS yok, veli rızası yok |
| **Dokümantasyon** | 🟢 İyi | 7/10 | Hayır — MEMORY güncel, README sync |

**Genel: BETA-READY DEĞİL.** 4 kritik blocker boyut (CVE, A11y, DB config, KVKK).

---

## 2. EdTech Product-Ready Kriterleri (2026 Industry Standard)

WebSearch sentezi — EdTech SaaS'ın okula/kuruma satılması için 2026 zorunlulukları:

### Ölçeklenebilirlik
- [ ] Auto-scaling + horizontal scaling (akademik dönem pikleri için predictive)
- [ ] CDN + caching (DB request azaltma)
- [ ] **%99.9+ uptime** (target %99.99 peak)
- [ ] Zero-downtime deployment

### Güvenlik (2026 minimum baseline)
- [ ] MFA tüm internal hesaplarda (GitHub, cloud)
- [ ] Tüm storage private-by-default + audit logging
- [ ] HTTPS/TLS global + security headers (HSTS, CSP, X-Frame-Options)
- [ ] Secrets vault/manager (hardcode YASAK)
- [ ] Otomatik + test edilmiş backup
- [ ] **Multi-tenant data isolation** (okul A ≠ okul B — row-level security)

### Compliance (gatekeeper, afterthought değil)
- [ ] **SOC 2 Type II** (okul districtleri için artık zorunlu)
- [ ] **Türkiye: KVKK + VERBİS kaydı** (FERPA/COPPA US-specific; biz KVKK)
- [ ] Veli açık rızası (reşit olmayan öğrenci verisi)
- [ ] Özel nitelikli veri ek güvenlik tedbiri
- [ ] Veri silme/taşıma hakkı (data subject rights)
- [ ] DPA + sub-processor audit

### Enterprise/EdTech
- [ ] **SSO** (Türkiye: MEB e-okul, e-devlet entegrasyonu — US Clever/ClassLink yerine)
- [ ] WCAG 2.1 AA accessibility
- [ ] Multi-language (TR primary)

### Operasyonel
- [ ] CI/CD otomatik deploy
- [ ] Monitoring + logging + alerting
- [ ] Incident response + escalation
- [ ] Customer support readiness

---

## 3. S181-S198 PROGRESS (Çözülen Blocker'lar) ✅

S180 audit'inin 10 P0'ından **8'i çözüldü** (22 May → 27 May):

| S180 P0 | Çözüm | Session |
|---|---|---|
| MEMORY stale (77K vs 167K) | Sürekli güncelleme + drift fix | S180-S198 |
| Phase 7 gold pool %0 rationale | %99.95 coverage | S181 |
| 35 mock endpoint live | Impl hazır + flag-gated (operator açar) | S196 Day 1-4 |
| Frontend TS build FAIL (5 err) | `npm run build` PASS | S180 (1be9262b8) |
| Study Rooms API missing (404) | CRUD + frontend wire + backend gap | S197+S198 W4.1/W4.1b |
| Rate limiter unactivated | Redis rate limiter wired to auth | S180 sprint0 |
| `.env` git tracked | Temiz (verify: 0 tracked) | S180 sprint2 ✅ |
| Subject enum collapse | Fixed | S180 sprint0 |
| Fire-forget exceptions swallowed | _ALGO_ERRORS counter | S180 sprint3 |
| Test coverage %16 | %42.75 (+%157) | S178-S198 |

**Bonus (S198):** ORM Cluster 2 phantom temizlik (HIGH 203→159), Curator 285 gold pool, Study Rooms tam kapatma.

---

## 4. HÂLÂ AÇIK Blocker'lar (Live-Verified)

### 🔴 P0 — Beta Blocker (verify edildi, phantom DEĞİL)

| # | Konu | Kanıt | Etki |
|---|---|---|---|
| P0-1 | **DB config tuning** | Live: shared_buffers=128MB, work_mem=4MB, max_conn=100, random_page_cost=4.0 (SSD'de yanlış) | Cache hit %56, pool exhaust @100 concurrent |
| P0-2 | **PgBouncer yok** | MEMORY: "planned for 100K+ users" | Connection pool exhaustion 100 öğrenci'de |
| P0-3 | **~60 CVE** (S179'da 111→60) | aiohttp/transformers/pillow/pyjwt CRITICAL | Supply-chain risk |
| P0-4 | **AGPL license risk** | ultralytics + PyMuPDF AGPL-3.0 | Ticari kullanımda source disclosure zorunlu |
| P0-5 | **A11y dead code** | AccessibilityProvider/AccessibleLayout unmounted | WCAG claim-but-broken |
| P0-6 | **Form a11y** | 3 aria-invalid / 150+ input, 67 label eksik | Screen reader registration imkansız |
| P0-7 | **KVKK/VERBİS** | Hiç başlanmadı | Yasal — ceza 272K-13.6M TL |
| P0-8 | **Veli açık rızası** | Reşit olmayan öğrenci verisi | KVKK zorunlu, akış yok |

### 🟡 P1 — Important

| # | Konu | Kaynak |
|---|---|---|
| P1-1 | Hot-path indexes apply (migration hazır, `alembic upgrade head` yapılmadı) | S179 |
| P1-2 | 3 endpoint auth gap (soru_bankasi.py) | S179 B-P0-1 |
| P1-3 | seed_admin.py hardcoded password | S179 B-P0-3 |
| P1-4 | Dependabot 200+ PR backlog (merge blocked) | S179 |
| P1-5 | Test pollution bisect (427 fail full-sweep) | S197/S198 |
| P1-6 | Login latency doğrulama (1.3s → ? after bcrypt 12→10) | S180 |
| P1-7 | Auth modules %0 coverage (csrf, unified_auth) | S179/S198 |
| P1-8 | Observability: slow-query tracking (pg_stat_statements preload) | S179 |
| P1-9 | A11y: modal focus trap, contrast, aria-busy | S179 |
| P1-10 | SSO (MEB e-okul / e-devlet entegrasyonu) | Enterprise |

### 🟢 P2 — Nice-to-have
- 76 low_conf + 78 unsolvable pending (Curator manuel)
- `_deprecated/` purge (5 importer refactor)
- ORM Cluster 1 migration (~140 col, cold tables)
- 33 Turkish-only endpoint (English alias)
- SOC 2 Type II (uzun vade, kurumsal satış için)

---

## 5. Faz-Bazlı Roadmap

### FAZ A — Beta-Blocker Burndown (1-2 hafta) 🔴

**A1. DB Scalability (2-3 gün)**
- `postgresql.conf` tuning: shared_buffers 128MB→2GB, work_mem 4MB→32MB, max_connections 100→200, random_page_cost 4.0→1.1
- Hot-path index migration apply (`alembic upgrade head` — S179 hazır)
- PgBouncer kurulum (transaction pooling, 100K hedef)
- Verify: cache hit %56→%92, curator queue 156ms→<5ms

**A2. Security CVE Sweep (2-3 gün)**
- Dependabot backlog merge (200+ PR triage)
- No-fix paket kararı: nltk/ollama/python-jose migrate
- AGPL: ultralytics/PyMuPDF production-path audit → commercial veya replace
- 3 auth-gap endpoint fix + seed_admin password env-driven

**A3. Accessibility (3-4 gün)**
- AccessibilityProvider + AccessibleLayout mount (dead code aktive)
- Form a11y: aria-invalid + label pairing (registration/booking forms)
- OSB toggle frontend wire (no_animations/no_shadows)
- Modal focus trap + contrast fix

### FAZ B — Compliance (2-3 hafta, paralel başlayabilir) 🔴

**B1. KVKK Temel (1 hafta)**
- VERBİS kayıt değerlendirmesi (eşik: 50+ çalışan veya 25M TL bilanço; özel nitelikli veri istisna kontrol)
- Veli açık rıza akışı (reşit olmayan öğrenci kayıt)
- Aydınlatma metni + gizlilik politikası
- Veri silme/taşıma hakkı endpoint

**B2. Data Governance (1 hafta)**
- Özel nitelikli veri ek güvenlik (encryption at rest)
- Sub-processor audit (Gemini/Qwen/3rd party)
- Veri saklama politikası + retention

**B3. SOC 2 hazırlık (uzun vade, kurumsal için)**
- Security-only Type 1 (pragmatik başlangıç)
- Audit logging + access control formalize

### FAZ C — Operasyonel Olgunluk (1-2 hafta) 🟡

**C1. Observability**
- pg_stat_statements preload (slow query tracking)
- Sentry wire (error tracking)
- Algorithm perf structured logging (BKT/IRT/FSRS)
- Frontend RUM

**C2. Test Coverage Push (%42→%70)**
- Test pollution bisect → fail-free sweep
- Auth modules coverage (csrf, unified_auth %0→%50)
- %0 dosyalar smoke tests

**C3. Performance**
- Login latency verify + optimize (pool wait)
- Frontend bundle optimization

### FAZ D — Enterprise (4+ hafta, satış-driven) 🟢
- SSO (MEB e-okul / e-devlet)
- Multi-tenant isolation (okul bazlı)
- SOC 2 Type II

---

## 6. Bundan Sonra Ne Yapmalı (Öncelik Sırası)

**Bu hafta (kritik path):**
1. **DB config tuning + index apply** (A1) — en yüksek ROI, 2-3 gün, ölçülebilir (cache hit, latency)
2. **CVE sweep** (A2) — supply-chain risk, Dependabot backlog
3. **KVKK temel başlat** (B1) — yasal risk, ceza 13.6M TL'ye kadar

**Gelecek hafta:**
4. **Accessibility** (A3) — okula satış için WCAG zorunlu
5. **Test coverage + pollution** (C2)
6. **Observability** (C1)

**Karar gereken stratejik sorular (kullanıcıya):**
- Beta hedef kitle: **kontrollü beta** (100 curator + 1K öğrenci) mı, **kamuya açık** mı? (Kontrollü beta için mevcut state warning'lerle kabul edilebilir — S180 verdict)
- KVKK: kurum büyüklüğü VERBİS eşiğini aşıyor mu? (özel nitelikli veri istisna olabilir)
- SSO öncelik: doğrudan tüketici (B2C öğrenci) mi, kurum/okul (B2B) satışı mı?

---

## 7. Tahmini Timeline

| Senaryo | Süre | Kapsam |
|---|---|---|
| **Kontrollü beta** (1K öğrenci) | **1-2 hafta** | Faz A (DB+CVE+A11y core) |
| **Kamuya açık beta** | **3-4 hafta** | Faz A + B1 (KVKK temel) |
| **Kurumsal/okul satışı** | **2-3 ay** | Faz A+B+C+D (SOC2, SSO) |

S180 verdict ("3-4 hafta concurrent") hâlâ geçerli — ama S181-S198 ile **8 P0 zaten kapandı**, kalan blocker'lar daha dar (DB config + CVE + A11y + KVKK).

---

## Kaynaklar
- S179 mega audit: `docs/audits/2026-05-21_full_audit/`
- S180 product readiness: `docs/audits/2026-05-22_product_ready_audit/`
- EdTech 2026 criteria: WebSearch (SaaS readiness, COPPA/SOC2, SETDA)
- KVKK/VERBİS: kvkk.gov.tr, verbis.kvkk.gov.tr
- Live verify: PG config (port 5434), git ls-files, frontend build state
