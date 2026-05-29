# KVKK Faz 2 — Veli Email/Token Onay Akışı (Tasarım)

**Tarih:** 2026-05-29
**Durum:** Onaylandı (brainstorming) — implementasyon planı bekliyor
**Bağlam:** Go-to-market = kurumsal/okul (B2B) satışı. KVKK uyumu gatekeeper.
**Önceki faz:** Faz 1 (capture+flag) tamamlandı — `commit 6d30af8a1`.

---

## 1. Amaç ve Kapsam

### Amaç
18 yaşından küçük (reşit olmayan) öğrenci kaydında, veliye email ile gönderilen
tek-kullanımlık token linki üzerinden **açık rıza** (KVKK Madde 5/açık rıza) alınması;
rıza alınana kadar sosyal/PII özelliklerinin kısıtlanması; veliye geri-çekme
(withdraw) hakkı sağlanması.

### Faz 1'den devralınan durum (mevcut, değiştirilmeyecek temel)
- `core/kvkk_compliance.py::is_minor(birth_date)` — 18 yaş eşiği.
- `api/auth.py` register: minor + `veli_email` yoksa → 422.
- Minor hesap: `users.birth_date` saklanır; `student_profiles.veli_onay=False`,
  `student_profiles.veli_email` saklanır. Reşit: `veli_onay=True`, `veli_email=None`.

### Kararlar (brainstorming, 2026-05-29 — kullanıcı onayı)
- **Token süresi:** 7 gün, **DB-kalıcı** (backend restart'ına dayanır).
- **Enforcement:** "Sosyal/PII consent'e bağlı" — çekirdek öğrenme açık;
  sosyal/leaderboard/veri-paylaşımı veli onayı gelene kadar kapalı.
- **Veli kimliği:** Hesapsız tek-tık email linki (veli hesabı/panel YOK).

### Non-goals (YAGNI)
- Veli PARENT hesabı / onay paneli (tek-tık link yeterli).
- Okul/kurum toplu-onay (B2B bulk approval) → Faz D.
- SMS onayı (sadece email).
- Mevcut KVKK breach email kodunun refactor'u (sadece yeni `email_util` eklenir,
  eskisine dokunulmaz — cerrahi müdahale).

---

## 2. Veri Modeli — yeni `veli_consent` tablosu

Ana SQLAlchemy model registry'sinde yeni model (`backend/models/`). Mevcut
`KVKKConsent` reuse EDİLMEZ çünkü: (a) `user_id = Integer` ama `users.id = VARCHAR`
(CLAUDE.md hard rule); (b) `kvkk_compliance.py:276` kendi lokal `declarative_base()`'ini
kullanır → ana registry'de değil, migration'da olmayabilir.

| Kolon | Tip | Not |
|---|---|---|
| `id` | String(36) PK | `str(uuid4())` default — VARCHAR konvansiyonu |
| `child_user_id` | String, indexed, NOT NULL | FK → `users.id` |
| `veli_email` | String, NOT NULL | Faz 1'den |
| `status` | String(20), default `pending` | pending / granted / withdrawn / expired |
| `token_hash` | String(64), indexed, nullable | `sha256(token).hexdigest()`; grant/withdraw'da NULL'lanır (tek-kullanım) |
| `token_expires_at` | DateTime | `requested_at + 7 gün` |
| `requested_at` | DateTime, default now | |
| `granted_at` | DateTime nullable | |
| `withdrawn_at` | DateTime nullable | |
| `consent_text` | Text | Veli neyi onayladı (KVKK aydınlatma metni snapshot) |
| `consent_version` | String(20) | Versiyonlu — örn `"kvkk-veli-1.0"` |
| `ip_address` | String(45) nullable | Onay anı (audit) |
| `user_agent` | String(500) nullable | Onay anı (audit) |
| `created_at / updated_at` | DateTime | |

**Token güvenliği:** Plaintext token sadece email linkinde bulunur. DB'de yalnızca
SHA-256 hash saklanır (DB sızıntısında token kullanılamaz). Doğrulama: gelen
token'ın hash'i hesaplanıp `token_hash` ile lookup edilir.

**Tekillik:** Bir child için aynı anda en fazla 1 aktif (pending) kayıt. `resend`
eski pending'i `expired`/invalidate eder, yeni token üretir.

---

## 3. Servis — `VeliOnayService`

`backend/services/veli_onay_service.py` (async, `AsyncSession` ile).

| Metod | İmza | İş |
|---|---|---|
| `request_consent` | `(child_user_id: str, veli_email: str, db) -> str` | pending kayıt + token üret (`secrets.token_urlsafe(32)`) + hash'i sakla, **plaintext token döner** |
| `verify_and_grant` | `(token: str, ip, ua, db) -> VeliOnayResult` | hash → lookup → expiry/used kontrol → `status=granted` + `student_profiles.veli_onay=True` + token_hash NULL |
| `withdraw` | `(token: str, db) -> bool` | `status=withdrawn` + `student_profiles.veli_onay=False` (KVKK geri-çekme) |
| `get_status` | `(child_user_id: str, db) -> VeliOnayStatus` | öğrencinin kendi onay durumu |
| `resend` | `(child_user_id: str, db) -> bool` | eski pending invalidate + yeni token + email |

`VeliOnayResult` / `VeliOnayStatus`: küçük dataclass/Pydantic (success, status, error_code, error_message).

Token deseni `core/passwordless_auth.py`'den ödünç (`secrets.token_urlsafe(32)`,
tek-kullanım, expiry). Servisin kendisi reuse edilmez (in-memory, 15dk, login-amaçlı).

---

## 4. Email — `core/email_util.py`

Mevcut SMTP kodu `kvkk_compliance.py::_send_kvkk_email_notification` içinde gömülü.
Küçük, yeniden-kullanılabilir bir util'e çıkarılır:

```
async def send_email(to: str, subject: str, html_body: str) -> bool
```

- Env: `SMTP_SERVER`, `SMTP_PORT` (default 587), `SMTP_USERNAME`, `SMTP_PASSWORD`.
- Config eksikse: `logger.warning` + `False` döner (registration bloklanmaz).
- Gönderim mevcut pattern gibi thread/async ile non-blocking.

**Veli onay maili içeriği:**
- Onay linki: `{FRONTEND_URL}/veli-onay?token={plaintext_token}`
- Geri-çek linki (footer): `{FRONTEND_URL}/veli-onay?token={plaintext_token}&action=withdraw`
- KVKK aydınlatma özeti + hangi verilerin işlendiği + 7 gün geçerlilik notu.

`FRONTEND_URL` env'den (default `https://kiro2.edu.tr` veya dev `http://localhost:3001`).

---

## 5. Endpoint'ler — `backend/api/auth.py`

| Method | Path | Auth | Açıklama |
|---|---|---|---|
| POST | `/api/v1/auth/veli-onay/verify` | Public (token=auth) | Body `{token}` → onayla |
| POST | `/api/v1/auth/veli-onay/withdraw` | Public (token=auth) | Body `{token}` → geri çek |
| GET | `/api/v1/auth/veli-onay/status` | Öğrenci (Bearer/cookie) | Kendi onay durumu |
| POST | `/api/v1/auth/veli-onay/resend` | Öğrenci | Email tekrar gönder (rate-limit) |

Pydantic schema'lar: `VeliOnayVerifyRequest{token}`, `VeliOnayResponse{status, message}`,
`VeliOnayStatusResponse{status, veli_email_masked, requested_at}`.

`resend` rate-limit: mevcut `_check_rate_limit(request, "register")` deseni reuse.

---

## 6. Enforcement — `require_veli_consent` (`core/dependencies.py`)

```
minor öğrenci (is_minor(users.birth_date)) + student_profiles.veli_onay = False  →  403
reşit VEYA veli_onay = True  →  geçer
```

FastAPI dependency. `student_profiles`'ı sorgular (veli_onay + ilgili user'ın birth_date).

**Gated (veli onayı gelene kadar 403):**
- Leaderboard (`/api/v1/.../leaderboard*`)
- Sosyal/arkadaş özellikleri (social features F0-F6)
- Study rooms
- Chat
- Public profil paylaşımı

**Açık (her zaman, minor dahil):**
- Soru çözme, sınav (osym-exam), çalışma planı (learning-path), çekirdek öğrenme

Kesin endpoint listesi implementasyon planında grep ile çıkarılır; bu tasarım
kategoriyi sabitler. 403 mesajı: "Bu özellik için veli onayı gereklidir."

---

## 7. Kayıt Entegrasyonu — `api/auth.py` register

Faz 1 minor dalı (`api/auth.py:528-619`) korunur. Hesap + `student_profiles` (veli_onay=False)
oluşturulduktan **sonra** eklenir:

```
if minor:
    token = await VeliOnayService.request_consent(child_user_id=user_id,
                                                   veli_email=..., db=db)
    # fire-and-forget — registration'ı bloklamaz
    await send_email(to=veli_email, subject=..., html_body=link içeren)
```

Email hatası registration'ı **bozmaz** (log + resend mevcut). Faz 1'in 422
("veli_email zorunlu") davranışı değişmez.

---

## 8. Hata Yönetimi

| Senaryo | Davranış |
|---|---|
| Geçersiz token | 400 + "Geçersiz veya süresi dolmuş onay bağlantısı" |
| Süresi dolmuş token | 400 + "Bağlantı süresi dolmuş. Öğrenci yeniden gönderebilir." + status=expired |
| Zaten kullanılmış/granted token tekrar | 200 + "Onay zaten alınmış" (idempotent, hata değil) |
| Email gönderim hatası (kayıt) | Registration başarılı kalır; log + resend mevcut |
| Withdraw sonrası tekrar withdraw | 200 idempotent |

Tüm hatalar **route handler içinde** `HTTPException` (middleware değil — 500'e dönüşmez,
`.claude/rules/middleware.md` uyumlu).

---

## 9. Test Stratejisi (TDD — fail-first)

**Unit (`tests/unit/test_veli_onay_service.py`):**
- request → pending kayıt + token döner
- verify_and_grant → granted + veli_onay=True
- expired token → reddet
- kullanılmış token → reddet (tek-kullanım)
- withdraw → withdrawn + veli_onay=False
- token hashing (plaintext DB'de saklanmaz)

**Integration (`tests/integration/test_veli_onay_flow.py`):**
- register minor → consent pending → verify → veli_onay=True
- enforcement: pending iken gated endpoint 403, granted sonrası 200
- resend → yeni token, eski invalidate

**Golden Flow (`tests/e2e/test_golden_flows.py`):**
- Yeni GF (golden-flows.md kuralı: yeni user-facing journey = yeni GF testi).
  Status < 500 + semantik kontrol. GF list yorumu + history tablosu güncellenir.

**Migration verify:**
- `information_schema.columns` ile `veli_consent` doğrula (CLAUDE.md migration kuralı).

---

## 10. Migration

1. ORM model **önce** (`backend/models/veli_consent.py` veya uygun mevcut modül).
2. `alembic revision --autogenerate -m "veli_consent table (kvkk faz2)"`.
3. `op.create_table()` + `sa.Column()` (raw SQL değil — CLAUDE.md kuralı).
4. `alembic upgrade head` → `information_schema` doğrulama.

---

## 11. Dosya Etki Listesi (implementasyon planı için ön-harita)

| # | Dosya | Değişiklik | Risk |
|---|---|---|---|
| 1 | `backend/models/veli_consent.py` (yeni) | ORM model | LOW |
| 2 | `backend/alembic/versions/*_veli_consent.py` (yeni) | migration | MED |
| 3 | `backend/services/veli_onay_service.py` (yeni) | servis | MED |
| 4 | `backend/core/email_util.py` (yeni) | SMTP util | LOW |
| 5 | `backend/api/auth.py` | 4 endpoint + register entegrasyonu | MED |
| 6 | `backend/core/dependencies.py` | `require_veli_consent` dep | MED |
| 7 | Sosyal/PII router'ları (grep ile) | `Depends(require_veli_consent)` ekle | MED |
| 8 | `frontend/src/pages/VeliOnayPage.tsx` (yeni) | onay/red sayfası | LOW |
| 9 | `frontend/src/services/authService.ts` | veli-onay verify/withdraw/status çağrıları | LOW |
| 10 | Testler (unit + integration + GF) | yeni | LOW |

---

## 12. Açık Sorular (plan aşamasında netleşir)
- Gated endpoint'lerin kesin listesi (grep `leaderboard|social|study-room|chat`).
- `FRONTEND_URL` env'i prod/dev için ayarlı mı (yoksa eklenecek).
- `consent_version` / aydınlatma metni içeriği final.
