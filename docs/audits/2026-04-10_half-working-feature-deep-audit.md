# Half-Working Feature — Deep Audit (Session 136)

**Tarih:** 2026-04-10
**Kaynak:** Golden Flow write-path sweep sonrası kapsamlı pattern analizi
**Scope:** `backend/api/`, `backend/app/api/`, `backend/core/`, `backend/models/`
**Method:** AST grep + runtime probe + OpenAPI diff + Golden Flow suite

---

## TL;DR

Session 136'da Golden Flow suite 5 yarım çalışan feature yakaladı ve tümü
düzeltildi (21/21 → 19 PASS, 2 acceptable SKIP, 0 FAIL). Ama bu sweep
**sinyal degil tarama degil** — problemin **buzdağının ucu** olduğunu
kanıtlar. Aynı kök nedenlerden kaynaklanan **50+ başka bozuk endpoint**
AST audit ile tespit edildi:

| Pattern | Bozuk dosya | Bozuk handler |
|---------|-------------|---------------|
| A — `AsyncSession = Depends(get_db)` + `await db.*` | **7 dosya** | **31 handler** (AST-kanıtlı) |
| B — `TokenPayload.id` AttributeError | **4 dosya** | **60 kullanım** |
| C — VARCHAR overflow riski (≤20) | **6 prod alan** | — |
| D — Silent swallow (`except Exception` + `logger.warning`) | 525 site | (broad, örneklem gerekli) |
| E — Turkish-only endpoint path drift | **32 path** | Frontend guess |

Pattern A ve B birbirinden bağımsız keşfedildi ama **aynı 2 dosya** her
ikisinde de var (`kvkk_privacy_api.py`, `two_factor_auth_api.py`) —
dual-trap: ilk DB çağrısı VE ilk `current_user.id` erişimi ikisi de
500 üretiyor. Bu dosyalar production'da çağırıldığında hangisi önce
tetiklenirse o yüzeye çıkıyor.

---

## Pattern A — sync `get_db` / async handler mismatch

### Kök neden

`backend/` içinde **3 farklı `get_db`** var:

| Import source | Semantik | Doğru kullanım |
|---------------|----------|----------------|
| `from core.database import get_db` | **SYNC** generator, `Session` yield eder | ❌ `AsyncSession` handler ile çakışır |
| `from core.dependencies import get_db` | **ASYNC** wrapper, `AsyncSession` yield eder | ✅ |
| `from app.core.deps import get_db` | **ASYNC** wrapper, `AsyncSession` yield eder | ✅ |

`core/database.py:395` açık açık comment'te "Sync version for compatibility"
diyor. Ama IDE autocomplete hangi sırayla geldiyse developer onu alıyor.
FastAPI DI çözümleyicisi tip annotation'ı **doğrulamaz** — sync `Session`
nesnesini `AsyncSession` parametresine sessizce enjekte eder. İlk
`await db.execute(...)` çağrısında:

```
sqlalchemy.exc.MissingGreenlet:
  greenlet_spawn has not been called; can't call await_only() here.
```

Bu bir tip hatası değil **runtime hatası**, linter yakalayamaz, mypy
yakalayamaz (her iki tarafın `Session` signature'ı geçerli). Tek koruma
gerçekten endpoint'i çağıran test — Golden Flow bunu yapıyor, ama
mevcut suite sadece 8 + 13 yolu kapsıyor.

### AST audit sonucu

**Kesin bozuk: 7 dosya, 31 handler.**

```
api/eba_routes.py: 3 BROKEN handlers
  :95  get_eba_videos()
  :173 get_eba_video_details()
  :256 get_videos_by_kazanim()

api/khan_routes.py: 9 BROKEN handlers
  :130 khan_oauth_callback()
  :198 get_oauth_status()
  :233 get_khan_content()
  :306 get_khan_content_details()
  :340 sync_user_progress()
  +4 more

api/two_factor_auth_api.py: 7 BROKEN handlers
  :70  setup_2fa()
  :132 enable_2fa()
  :197 disable_2fa()
  :290 verify_backup_code()
  :380 regenerate_backup_codes()
  +2 more

api/osym_questions_api.py: 5 BROKEN handlers
  :23  get_osym_statistics()
  :111 get_available_subjects()
  :150 get_random_questions()
  :238 generate_practice_exam()
  :337 get_questions()

api/kvkk_privacy_api.py: 6 BROKEN handlers
  :190 request_data_export()
  :284 get_export_requests()
  :309 get_export_request()
  :346 request_data_deletion()
  :434 get_deletion_requests()
  +1 more

api/question_crud_api.py: 1 BROKEN handler
  :1032 download_questions()
```

### AST audit'in kaçırdıkları

Bu 31 handler, `await db.execute(...)` pattern'ine tam uyanlar. Audit
**şunları yakalayamadı**:

1. **Farklı parametre adı** (`session`, `async_db`) — ama yine de
   `Depends(get_db)` kullananlar.
2. **İç helper'a `db` geçip helper'ın `await` yapması** — AST tek-seviye
   tarıyor.
3. **Await olmadan sync pattern kullananlar**: `db.query(...)` gibi
   legacy `Session` API'si. Bunlar runtime'da çalışıyor ama:
   - Type annotation yalan söylüyor (`AsyncSession` diyor, `Session` alıyor)
   - `session.execute(select(...))` hiç await olmadan çağrılırsa
     sessizce coroutine return eder (unwarned).

Gerçek mismatch sayısı `grep`'e göre **365 handler × 40 dosya**. AST ile
verified "kesin await-db" ise 31. Aradaki fark (≈330) tip yalanı olan ama
runtime'da ya sync çalışan ya sessizce coroutine döken handler'lar.

### Dual-hit dosyalar

`kvkk_privacy_api.py` ve `two_factor_auth_api.py` Pattern A VE Pattern B
her ikisinde de var:

- `kvkk_privacy_api.py`: 6 handler `AsyncSession = Depends(get_db)` + 22
  kez `current_user.id`
- `two_factor_auth_api.py`: 7 handler `AsyncSession = Depends(get_db)` + 19
  kez `current_user.id`

Her handler çağrısı **ikisinden biri** ile 500 döner — hangisi önce
vurursa. `AuthenticatedUser` dependency'si önce çalıştığı için genelde
`AttributeError` önce tetiklenir. Yani bu dosyalar production'da
çağırıldığında 100% 500 dönüyor.

### Sabit: tek kalıcı çözüm

1. **`core/database.py:395` sync `get_db` sil veya rename** → `get_sync_db_DEPRECATED`
2. **AST-tabanlı lint** `scripts/audit_db_dependency.py` — CI gate
3. **Golden Flow write-path extension** — her düzeltilen dosya için bir GF test

---

## Pattern B — `TokenPayload.id` AttributeError

### Kök neden

`core/jwt_auth.py:get_current_user` bir Pydantic `TokenPayload` döner.
Schema:

```python
class TokenPayload(BaseModel):
    sub: str       # user_id
    email: str
    role: UserRole
    ...
```

`.id` field'ı **yok**. Doğru erişim `.sub`. Ama bazı handler yazarları
`AuthenticatedUser.id` alışkanlığıyla yazıyor:

```python
# BROKEN
current_user: TokenPayload = Depends(get_current_user)
user_id = current_user.id  # AttributeError!

# CORRECT
user_id = current_user.sub
```

Bu da tip-safety'siz: Pydantic v2 `model_config` varsayılan olarak extra
field erişiminde `AttributeError` fırlatır ama static tip kontrolcüsü
(mypy/pyright) bunu ancak `TokenPayload` explicit annotated'se yakalar.
Birçok dosyada annotation yok (`current_user = Depends(...)`), böylece
tip çıkarımı `Any` kalıyor, mypy sessiz kalıyor.

### Bulgu

**4 dosya, 60 toplam kullanım:**

| Dosya | `current_user.id` sayısı | Ayrıca Pattern A? |
|-------|--------------------------|-------------------|
| `api/kvkk_privacy_api.py` | 22 | ✅ EVET (6 handler) |
| `api/two_factor_auth_api.py` | 19 | ✅ EVET (7 handler) |
| `api/enhanced_auth_api.py` | 12 | Ayrı audit — 6 handler Pattern A'da görüldü |
| `api/rate_limit_api.py` | 7 | 1 handler Pattern A'da |

### Sabit

`kvkk_consent_api.py`'de kullanılan hotfix deseni aynen uygulanmalı:

```python
# Önce
from core.database import get_db
from core.jwt_auth import get_current_user
...
db: AsyncSession = Depends(get_db)
current_user: User = Depends(get_current_user)  # yanlış tip
user_id = current_user.id  # AttributeError

# Sonra
from core.database import get_async_session
from core.jwt_auth import TokenPayload, get_current_user
...
db: AsyncSession = Depends(get_async_session)
current_user: TokenPayload = Depends(get_current_user)
user_id = current_user.sub
```

---

## Pattern C — VARCHAR overflow riski

GF2w probe'u `xp_transactions.source VARCHAR(20)` overflow'unu buldu.
Audit benzer riskli alanları listeliyor:

| Dosya | Field | Tip | Risk |
|-------|-------|-----|------|
| `models/gamification.py:168` | `ObaUye.role` | VARCHAR(10) | Enum-like, düşük risk ama `"toycu"` `"noker"` `"bey"`'i aşacak yeni rol eklerse boom |
| `models/gamification.py:192` | `Badge.category` | VARCHAR(20) | "katilim/beceri/basari/sosyal" — güvenli ama yeni kategori eklerken dikkat |
| `models/gamification.py:240` | `Duel.status` | VARCHAR(20) | "pending/active/completed" — güvenli |
| `models/osym_question.py:87, 233` | `status` | VARCHAR(20) | API-driven set edilirse risk |
| `models/student_goal.py:35` | `status` | VARCHAR(20) | API-driven set edilirse risk |

**Aksiyon:** VARCHAR length'leri ≥50 yap **API-driven** (yani istek
gövdesinden string gelen) alanlar için. Salt enum alanlar için native
PostgreSQL ENUM kullan — uzunluk sorunu yok.

---

## Pattern D — Silent swallow

Audit 525 `except Exception + logger.warning` site buldu. Çok broad.
Örnek olarak GF1w probe'u `sinav.py:737-738` fire-and-forget desenini
buldu:

```python
except Exception as e:
    logger.warning(f"BKT pipeline hatası (sınav devam eder): {e}")
```

Bu `logger.warning` traceback'i **kaybediyor**. Doğrusu:

```python
except Exception:
    logger.exception("BKT pipeline hatası (sınav devam eder)")
```

### Sınıflandırma (sample)

Top 15 dosyadaki swallow'lardan örnek aldım:

- **Metrics emission** (prometheus push hatası vb.): legitimate swallow
- **Optional cache write**: legitimate swallow
- **Fire-and-forget algorithm pipeline** (BKT/IRT/FSRS/ZPD): **SILENT
  FEATURE BREAKAGE** — response 200 döner, state güncellenmez
- **Parser fallback**: legitimate ama iç fallback'in yolu logda olmalı

**Aksiyon:** `logger.warning` → `logger.exception` toplu migrasyon
agresif. Önce tam sınıflandırma gerekli. 525 site için 3 dalga:
1. **Dalga 1:** Tüm algoritma pipeline'ları (BKT/IRT/FSRS/ZPD) → `exception`
2. **Dalga 2:** Request handler içindeki swallow → `exception` + raise
3. **Dalga 3:** Optional side-effect (metric, cache) → sakla ama context ekle

---

## Pattern E — TR/EN path drift

`audit_path_drift.py --url http://localhost:8000/openapi.json`:

- **TR/EN Duplicate:** _None — clean_ (Session 135'te 22'ye düştü, şimdi 0)
- **Turkish-Only Paths: 32 hâlâ var**
- **Frontend 404 Risk: ~40** (çoğu `/api/v1/study-rooms/*` — backend
  modülü yok, missing feature)

### Turkish-only paths (32)

```
/api/v1/auth/profil
/api/v1/ogretmen/* (11 path)
/api/v1/veli/* (9 path)
/api/v1/student-dashboard/* (3 path)
/api/v1/zpd-maarif/* (5 path)
/istatistikler, /konular, /soru/{id}, /sorular (4 root-level)
```

**Session 135 path-naming.md** kuralı yeni endpoint'lerde zorunlu —
ama mevcut 32 legacy path duruyor. Aksiyon: her biri için
1. İngilizce canonical ekle (Session 136 `teacher_classroom.py` gibi)
2. TR path'i deprecate et (307 redirect veya silme)
3. Frontend'in doğru path'i kullandığını doğrula

`/istatistikler`, `/konular`, `/soru/*`, `/sorular` — **prefix yok**
— bir router `include_router` çağrısı `prefix=""` ile geçmiş. Silinmesi
gerekir veya doğru prefix ile yeniden bağlanması.

---

## Sistem düzeyinde gözlem

### Neden Golden Flow sweep sadece 5 yarım feature buldu?

**8 okuma-yolu + 13 yazma-yolu = 21 test** covered. Backend'de **1074
endpoint** var. Kapsamım = **%1.95**. Matematiksel olarak aynı oranla
bozukluk genişlerse:
- 5 yarım feature × (1074 / 21) ≈ **255 bozuk feature** olmalı

AST audit **≥31 kesin, ≥60 attribute-error, ≥ kaç-yüz tip-yalan**
bulduğuna göre bu tahmin gerçekçi. **Asıl problem suite kapsamı değil
— kod katmanının pattern hijyeni.**

### İki katman hikayesi

`backend/api/` (eski katman):
- Çoğunluk `from core.database import get_db` kullanıyor (sync shim)
- Çoğunluk `from core.jwt_auth import get_current_user` + `current_user.id`
- Pattern A ve B'deki tüm bozuk dosyalar burada

`backend/app/api/` (yeni katman, Session 112+):
- `from app.core.deps import get_db, User, get_current_user` — doğru
- `User` (AuthenticatedUser) kullanıyor, `.id` valid
- AST audit hiç mismatch bulmadı

**Session 112 refactor eski katmanı bırakıp yenisini yazdı ama
eski katmanı temizlemedi.** Böylece Pattern A + B tek katmana
toplandı. Fix stratejisi: eski katmanı **tamamen** yeni katmana
taşımak mı, yoksa yerinde fix mi? Bu stratejik karar.

### Neden mevcut linting yakalamadı?

- **ruff**: `F` (undefined/unused), `E` (style) kuralları tutar. Type
  mismatch `E`'de değil. No config flag this.
- **mypy**: `strict` mode bile Pydantic attribute erişimini çıkarımla
  yakalayamıyor — `TokenPayload` annotation'ı olmayan dosya `Any`
  kalıyor.
- **Tests**: `backend/api/` test coverage %18 (Session 127 öncesi), şimdi
  %53. Ama coverage "line executed" demek — endpoint'in **semantik**
  doğru çalıştığını teyit etmez. Çok test muhtemelen mock session
  kullanıyor, production `get_db` SYNC shim'ine hiç dokunmuyor.

---

## Öneri: 4-aşamalı düzeltme planı

### Aşama 1 — Hemen (1-2 commit)

1. **`core/database.py:395 get_db` rename** → `_get_sync_db_LEGACY`,
   `from core.database import get_db` import'u **CI hard-fail** yap
   (sadece `from core.database import get_async_session` izinli).
2. **AST linter ekle:** `backend/scripts/audit_db_dependency.py` — CI gate
3. **Golden Flow sweep çalıştır**, her fix sonrası commit.

### Aşama 2 — Pattern A toplu fix (3-5 commit)

Her dosya için TDD loop:
1. GF write test yaz (GF8wA pattern)
2. Test FAIL
3. Import swap + signature fix
4. Test PASS
5. Commit

Sıralama (user impact):
- `khan_routes.py` (9 handler, Khan Academy entegrasyonu kritik)
- `osym_questions_api.py` (5 handler, ÖSYM soru listesi)
- `two_factor_auth_api.py` (7 handler, 2FA güvenlik)
- `eba_routes.py` (3 handler, EBA video)
- `kvkk_privacy_api.py` (6 handler, KVKK veri taşıma)
- `question_crud_api.py` (1 handler, toplu indirme)

### Aşama 3 — Pattern B dual-trap fix (2 commit)

1. `enhanced_auth_api.py` (12 `.id` kullanımı, ayrıca ~6 handler Pattern A)
2. `rate_limit_api.py` (7 `.id` kullanımı, 1 handler Pattern A)

### Aşama 4 — Pattern D algorithm pipeline fix (1 commit)

Tüm BKT/IRT/FSRS/ZPD fire-and-forget blocklarında:
- `logger.warning(f"... {e}")` → `logger.exception("...")`
- `sinav.py:737-738` başta olmak üzere tüm pipeline hataları **structured
  log + metric counter** ile surface edilsin

### Aşama 5 — Path drift (opsiyonel, ayrı sprint)

32 Turkish-only path'in her biri için canonical İngilizce endpoint ekle
+ legacy deprecation.

---

## Toplam etki tahmini

| Aşama | Düzelttiği endpoint | Prevented 500 |
|-------|---------------------|---------------|
| Session 136 sweep (bitmiş) | 8 | ~8 |
| Aşama 1-3 (Pattern A+B) | 31 broken + 60 attribute-error sites | **~85 endpoint** |
| Aşama 4 (Pattern D) | silent feature rot | sessiz bozulmayı yüzeye çıkarır |
| Aşama 5 (Path drift) | ~40 frontend 404 | frontend navigasyon |

Toplam **~125 endpoint** production'da 500 veya yanlış davranıştan
düzelir. Bu **%12 endpoint kapsamı** demek.

---

## Altında yatan meta-ders

**Kod inceleme + lint + test üçgeni bu sınıfta bug'ları yakalamıyor.**
Yakalayan tek şey **canlı backend'e HTTP isteği atan entegrasyon testi**.
Golden Flow doğru yaklaşım ama suite **endpoint başına** genişletilmeli:
her yeni route eklendiğinde otomatik bir smoke probe oluşturulmalı.

Alternatif: Schemathesis ile **OpenAPI-derived property test** — her
endpoint için otomatik auth + temel payload ile 500 aramak. Çoğu GF
test'in yerini alabilir. Mevcut `schemathesis` paketi zaten requirements'ta
mevcut, ama koşulmuyor.

---

*Audit author:* Session 136 Golden Flow sweep → Pattern extraction → AST
deep dive. Takip: `docs/audits/2026-04-10_half-working-feature-deep-audit.md`
ve `.claude/rules/golden-flows.md`.
