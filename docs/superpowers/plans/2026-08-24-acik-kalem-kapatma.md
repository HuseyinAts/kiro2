# Açık Kalem Kapatma Uygulama Planı (S251)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** S250 sonrası açık kalan, **ölçülerek doğrulanmış** kusurları kapatmak; her biri için
mutasyonla ağırlığı kanıtlanmış bir bekçi bırakmak.

**Architecture:** Beş bağımsız görev. Hiçbiri diğerine bağımlı değil — sıra yalnızca
risk/değer önceliği. Her görev tek başına commit edilebilir ve tek başına geri alınabilir.
Ortak yöntem: kırmızı test → minimal düzeltme → yeşil → mutasyon → commit.

**Tech Stack:** Python 3.13 · FastAPI · pytest (+xdist) · PostgreSQL 18 (port 5434) ·
pre-commit (ruff **0.7.1**, mypy 1.11.2, bandit) · Docker (`kiro2-backend`)

---

## ✅ SONUÇ (24 Ağu 2026 — plan uygulandı)

| Görev | Durum | Ölçülen delta | Commit |
|---|---|---|---|
| **G1** `details` daralması | ✅ | skip **21 → 2** (19 test canlandı) · AST daraltan sınıf **13 → 0** · mypy `exceptions.py` **4 → 0** | `89fe2e417` |
| **G2** RLS göç ankrajı | ✅ | **0 koşuyor → 5 passed** (collection error 1 → 0) | `c4dd5282a` |
| **G3** olmayan modülün testi | ✅ | `tests/integration` collection error **1 → 0** (1962 toplandı) | `c4dd5282a` |
| **G6** koşulsuz susturma (U25) | ✅ | **16 skipped/0 passed → 6 passed/10 skipped** + üretim koruması (7 bekçi) | `c4dd5282a` |
| **G4** `synced_count` | ✅ | 3. sayaç `skipped_count`; **synced+skipped+failed == N** invaryantı test edildi | `ec580070a` |
| **G5** `ServiceError` handler | ❌ **DÜŞÜRÜLDÜ** | Öncülü ÇÜRÜDÜ — aşağı bak | — |

**Mutasyon:** G1 **3/3** · G4 **2/2** — tüm geri alımlar doğrulandı.

### 🔴 G5 neden düşürüldü (planın öncülü yanlıştı)

Plan G5'i *"yetki hataları 500 dönüyor"* varsayımıyla yazmıştı. Ölçüm bunu **çürüttü**:
taze öğrenci hesabıyla **17 yetki-reddi ucu proplandı → 17/17 HTTP 403**, hiçbiri 500 değil.
Canlı yollar `core/authorization.py:12` (`AuthorizationError(HTTPException, 403)`) ve
`auth_dependencies.py:201/223` (`raise HTTPException`) kullanıyor. Gen‑1 `AuthorizationError`'ı
yalnız `enhanced_authentication.py:362/:385` üretiyor ve o metotların üretim çağıranı **0**.

Ayakta kalan kısım: üç handler modülü gerçekten kayıtsız ölü kod. Ama kaydetmenin
bugünkü değeri **+0** (o ailenin `api/`+`services/` içinde **1** `raise`'i var) →
`audit-methodology.md`: *"Fix'in değeri: +0 ise fix yapılmaz."* Ölü kod temizliği
X06 (d) ile birlikte ele alınmalı, ayrı kalem.

---

## Ölçüm temeli (bu plan tahmine dayanmıyor)

| Kalem | Ölçüm | Komut/ankraj |
|---|---|---|
| G1 | `core/exceptions.py`'de **13 sınıf** ebeveyni `ServiceError`'un `details`'ini daraltmış | AST taraması; sağlam kalan yalnız `ValidationError` + `DatabaseError` |
| G1 | Bu yüzden **19 test susturulmuş**, hepsi aynı gerekçe: *"API changed: no details parameter"* | `tests/slow/test_core_exceptions_comprehensive.py`, 21 skip'in 19'u |
| G2 | RLS testi **toplanamıyor**: göç dosyası `versions/` yerine `versions_archive/`'de | `alembic/versions_archive/ad6ba3bbe485_fix_rls_fail_closed_policy.py` mevcut |
| G3 | `services/ocr_sanitizer_service` **git geçmişinde hiç var olmamış**; testi `tests/integration` toplanmasını kırıyor | `git log --all -- backend/services/ocr_sanitizer_service.py` → boş |
| G4 | `synced_count`, FSRS kartı bulunmasa da artıyor → öğrenciye **fazla-raporlama** | `services/offline_sync_service.py:358` |
| G5 | `ServiceError` ailesi için kayıtlı handler **yok**; 403 döndüren üç modülün üçü de ölü | canlı `app.exception_handlers` = 5 anahtar |
| G5 | Ama canlı `api/`+`services/` içinde bu aileden **yalnız 1** `raise` var → blast radius küçük | `grep -rn "raise <Sinif>(" api/ services/` |

**Ertelenenler (kullanıcı onayı gerektirir, bu planda YOK):** X06 (c) 3 rol kapısının
birleştirilmesi (**32 uç** etkilenir) · X06 (d) 16 ölü tanımın silinmesi · beş ölü modülün
silinmesi · SMTP #441 (operatör).

---

## File Structure

| Dosya | Sorumluluk | Görev |
|---|---|---|
| `backend/core/exceptions.py` | Değişiklik: 13 sınıfın `__init__`'ine `details` geri konur | G1 |
| `backend/tests/slow/test_core_exceptions_comprehensive.py` | Değişiklik: 19 `@pytest.mark.skip` kaldırılır | G1 |
| `backend/tests/integration/test_rls_fail_closed_with_check.py` | Değişiklik: göç çözücüsü iki dizini de arar | G2 |
| `backend/tests/integration/test_ocr_sanitizer_rag_guardrails.py` | Değişiklik: modül düzeyi skip + görünür gerekçe | G3 |
| `backend/services/offline_sync_service.py` | Değişiklik: sayaç anlamı düzeltilir | G4 |
| `backend/tests/unit/test_offline_sync_sayac_dogrulugu.py` | **Yeni**: sayaç bekçisi | G4 |
| `backend/core/application.py` | Değişiklik: `ServiceError` handler'ı kaydedilir | G5 |
| `backend/tests/unit/test_service_error_http_kodu.py` | **Yeni**: 403/404/503 eşleme bekçisi | G5 |

---

## Görev G1: `details` daralması — 13 sınıf, 19 susturulmuş test

**Neden önce bu:** Kırmızı testler **zaten yazılmış ve commit'lenmiş**, sadece susturulmuş.
Susturmayı kaldırmak = kırmızı testi yazmak. TDD'nin en temiz hâli. Ayrıca S250'de
`DatabaseError` için aynı düzeltme kanıtlandı; desen doğrulanmış.

**Files:**
- Modify: `backend/core/exceptions.py` (13 sınıf)
- Modify: `backend/tests/slow/test_core_exceptions_comprehensive.py` (19 skip)

- [ ] **Adım 1: Susturmaları kaldır (= kırmızı testi yaz)**

`details` gerekçeli 19 skip satırını sil. Şu iki gerekçe **KALSIN** (farklı kusur, bu görevin kapsamı değil):
`"JSON serialization escapes Turkish characters with unicode"` ve
`"ContentError now uses EnhancedServiceError format with error code prefix"`.

```bash
cd C:/Users/husey/kiro2/backend
python - <<'PY'
from pathlib import Path
p = Path("tests/slow/test_core_exceptions_comprehensive.py")
veri = p.read_bytes()
se = b"\r\n" if b"\r\n" in veri else b"\n"
satirlar = veri.split(se)
tut, silinen = [], 0
for s in satirlar:
    metin = s.decode("utf-8", "replace")
    if "pytest.mark.skip" in metin and "no details parameter" in metin:
        silinen += 1
        continue
    if "pytest.mark.skip" in metin and "details is now {} not None" in metin:
        silinen += 1
        continue
    tut.append(s)
p.write_bytes(se.join(tut))
print(f"kaldirilan skip: {silinen}  (19 beklenir)")
PY
```

Beklenen çıktı: `kaldirilan skip: 19  (19 beklenir)`

- [ ] **Adım 2: Kırmızıyı gör**

```bash
python -m pytest tests/slow/test_core_exceptions_comprehensive.py -q --no-header -p no:cacheprovider
```

Beklenen: **19 failed**, hepsi `TypeError: ... unexpected keyword argument 'details'`.
Skip sayısı 21 → **2**.

> Kırmızı sayısı 19 değilse DUR. 19'dan az ise bazı testler başka sebeple zaten geçiyordur
> (o sınıf `details`'i daraltmamış olabilir) — listeyi yeniden ölç, planı düzelt.

- [ ] **Adım 3: 13 sınıfa `details` geri koy**

Desen S250'de `DatabaseError` için commit edilenle **birebir aynı**: yerel değişkeni
`detay` yap, parametreyi `details` olarak ekle, açıkça verilen `details` üste yazsın.

`backend/core/exceptions.py` içinde şu 13 sınıfı değiştir:

```python
class NotFoundError(ServiceError):
    """Resource not found exception"""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {}
        if resource_type:
            detay["resource_type"] = resource_type
        if resource_id:
            detay["resource_id"] = resource_id
        if details:
            detay.update(details)
        super().__init__(message, "NOT_FOUND", detay)


class AuthorizationError(ServiceError):
    """Authorization error exception"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, "AUTHORIZATION_ERROR", dict(details) if details else {})


class ExternalServiceError(ServiceError):
    """External service error exception"""

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {}
        if service_name:
            detay["service_name"] = service_name
        if status_code is not None:
            detay["status_code"] = status_code
        if details:
            detay.update(details)
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", detay)


class ConfigurationError(ServiceError):
    """Configuration error exception"""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {"config_key": config_key} if config_key else {}
        if details:
            detay.update(details)
        super().__init__(message, "CONFIGURATION_ERROR", detay)


class BusinessLogicError(ServiceError):
    """Business logic error exception"""

    def __init__(
        self,
        message: str,
        rule: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {"rule": rule} if rule else {}
        if details:
            detay.update(details)
        super().__init__(message, "BUSINESS_LOGIC_ERROR", detay)


class AuthenticationError(ServiceError):
    """Authentication error exception"""

    def __init__(
        self,
        message: str = "Authentication failed",
        token_type: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {"token_type": token_type} if token_type else {}
        if details:
            detay.update(details)
        super().__init__(message, "AUTHENTICATION_ERROR", detay)


class RateLimitError(ServiceError):
    """Rate limit exceeded exception"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: int | None = None,
        reset_time: datetime | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {}
        if limit:
            detay["limit"] = limit
        if reset_time:
            detay["reset_time"] = reset_time.isoformat()
        if details:
            detay.update(details)
        super().__init__(message, "RATE_LIMIT_ERROR", detay)


class TimeoutError(ServiceError):
    """Operation timeout exception"""

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = (
            {"timeout_seconds": timeout_seconds} if timeout_seconds else {}
        )
        if details:
            detay.update(details)
        super().__init__(message, "TIMEOUT_ERROR", detay)


class ConcurrencyError(ServiceError):
    """Concurrency/locking error exception"""

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {"resource": resource} if resource else {}
        if details:
            detay.update(details)
        super().__init__(message, "CONCURRENCY_ERROR", detay)


class IntegrationError(ServiceError):
    """System integration error exception"""

    def __init__(
        self,
        message: str,
        system_name: str | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {}
        if system_name:
            detay["system_name"] = system_name
        if error_code:
            detay["integration_error_code"] = error_code
        if details:
            detay.update(details)
        super().__init__(message, "INTEGRATION_ERROR", detay)


class MaintenanceError(ServiceError):
    """Service under maintenance exception"""

    def __init__(
        self,
        message: str = "Service is under maintenance",
        estimated_duration: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = (
            {"estimated_duration": estimated_duration} if estimated_duration else {}
        )
        if details:
            detay.update(details)
        super().__init__(message, "MAINTENANCE_ERROR", detay)


class QuotaExceededError(ServiceError):
    """Resource quota exceeded exception"""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        current_usage: int | None = None,
        limit: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        detay: dict[str, Any] = {}
        if resource_type:
            detay["resource_type"] = resource_type
        if current_usage is not None:
            detay["current_usage"] = current_usage
        if limit is not None:
            detay["limit"] = limit
        if details:
            detay.update(details)
        super().__init__(message, "QUOTA_EXCEEDED_ERROR", detay)
```

`SecurityError` (satır 211) için de aynı desen: `details` parametresi eklenir, yerel
sözlük `detay` olur, sonda `detay.update(details)`.

> **Dikkat:** `detay` yerel değişkenini `dict[str, Any]` olarak **açıkça tiple**. Aksi halde
> mypy `details["limit"] = limit` (int) satırında `Incompatible types in assignment` verir —
> `exceptions.py`'deki mevcut 4 mypy hatasının kaynağı tam olarak budur ve bu görev onları
> **da** kapatır.

- [ ] **Adım 4: Yeşili gör**

```bash
python -m pytest tests/slow/test_core_exceptions_comprehensive.py -q --no-header -p no:cacheprovider
```

Beklenen: **0 failed**, skip **2**.

- [ ] **Adım 5: Bekçi hâlâ yeşil mi + kwarg sözleşmesi bozulmadı mı**

```bash
python -m pytest tests/unit/test_exception_kwarg_sozlesmesi.py tests/unit/test_core_exceptions_coverage.py tests/unit/test_core_utils.py -q --no-header -p no:cacheprovider
```

Beklenen: hepsi passed, 0 failed.

- [ ] **Adım 6: mypy deltasını ölç (kapı borcu azalıyor mu?)**

```bash
cd C:/Users/husey/kiro2
pre-commit run mypy --files backend/core/exceptions.py 2>&1 | tail -8
```

Beklenen: `exceptions.py`'deki **4 `[assignment]` hatası kaybolmuş** olmalı.
Kaybolmadıysa `detay` tipini açıkça yazmayı atlamışsındır.

- [ ] **Adım 7: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/core/exceptions.py backend/tests/slow/test_core_exceptions_comprehensive.py
git commit -F - <<'MSG'
fix(exceptions): 13 sinif ebeveynin details'ini daraltmisti -- 19 susturulmus test acildi

S250 DatabaseError icin ayni daralmayi duzeltmisti. AST olcumu daralmanin
13 sinifta oldugunu gosterdi (saglam kalan: ValidationError, DatabaseError).

Testler zaten YAZILMISTI, sadece susturulmustu: 19 skip'in hepsi ayni cumleyi
tasiyordu -- "API changed: no details parameter". Susturmayi kaldirmak kirmizi
testi yazmak oldu; sonra 13 imza onarildi.

Olculen: skip 21 -> 2 · 19 test PASS · exceptions.py mypy [assignment] 4 -> 0.
Davranis: taban sinif DEGISMEDI, __str__ korundu.
MSG
```

- [ ] **Adım 8: Mutasyon — testler yük taşıyor mu?**

`AuthenticationError.__init__`'ten `details` parametresini geçici olarak çıkar, koş, geri al:

```bash
cd C:/Users/husey/kiro2/backend
python - <<'PY'
import subprocess, sys
from pathlib import Path
p = Path("core/exceptions.py"); veri = p.read_bytes()
se = b"\r\n" if b"\r\n" in veri else b"\n"
ankraj = se.join([b'        token_type: str | None = None,', b'        details: dict[str, Any] | None = None,', b'    ):'])
assert veri.count(ankraj) == 1, f"ankraj tekil degil: {veri.count(ankraj)}"
p.write_bytes(veri.replace(ankraj, se.join([b'        token_type: str | None = None,', b'    ):'])))
r = subprocess.run([sys.executable, "-m", "pytest", "tests/slow/test_core_exceptions_comprehensive.py", "-q", "--tb=no", "-p", "no:cacheprovider"], capture_output=True, text=True)
print([l for l in r.stdout.splitlines() if "passed" in l or "failed" in l][-1:])
subprocess.run(["git", "checkout", "HEAD", "--", "backend/core/exceptions.py"], cwd="..", check=True)
print("geri alim:", subprocess.run(["git","status","--short","--untracked-files=no","backend/core/exceptions.py"], cwd="..", capture_output=True, text=True).stdout.strip() == "")
PY
```

Beklenen: en az **2 failed** (AuthenticationError testleri) ve `geri alim: True`.
`0 failed` çıkarsa testler yük taşımıyor demektir — **DUR**.

---

## Görev G2: RLS testinin göç ankrajı arşive taşınmış

**Files:**
- Modify: `backend/tests/integration/test_rls_fail_closed_with_check.py:66-77`

- [ ] **Adım 1: Kırmızıyı gör (zaten kırmızı)**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/integration/test_rls_fail_closed_with_check.py --collect-only -q 2>&1 | tail -5
```

Beklenen: `Failed: Migration bulunamadi: ...\alembic\versions\ad6ba3bbe485_fix_rls_fail_closed_policy.py`

- [ ] **Adım 2: Çözücüyü iki dizinde arar hâle getir**

> Depo dersi: *"Bekçi SABİT değer beklememeli"*. Tek yol çivilemek yerine **ara**;
> bulunamazsa hangi dizinlere baktığını söyleyerek düş.

`_migration_modulu()` fonksiyonunu şununla değiştir:

```python
def _migration_modulu():
    """Migration'i dosya yolundan yukler (alembic/versions paket degil).

    Squash turlerinde dosya ``versions/`` -> ``versions_archive/`` tasinabiliyor.
    Tek yolu civilemek bu testi SESSIZCE olduruyordu; iki dizin de aranir.
    """
    ad = "ad6ba3bbe485_fix_rls_fail_closed_policy.py"
    kok = Path(__file__).resolve().parents[2] / "alembic"
    adaylar = [kok / "versions" / ad, kok / "versions_archive" / ad]
    yol = next((a for a in adaylar if a.exists()), None)
    if yol is None:  # pragma: no cover - dosya tamamen silinirse haber ver
        pytest.fail(
            "Migration hicbir dizinde bulunamadi. Bakilan yollar: "
            + " | ".join(str(a) for a in adaylar)
        )
    spec = importlib.util.spec_from_file_location(yol.stem, yol)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul
```

- [ ] **Adım 3: Toplama düzeldi mi**

```bash
python -m pytest tests/integration/test_rls_fail_closed_with_check.py --collect-only -q 2>&1 | tail -4
```

Beklenen: toplama hatası YOK, **8 test toplandı**.

- [ ] **Adım 4: Testleri gerçekten koş (canlı PG gerekir)**

```bash
"C:/Program Files/PostgreSQL/18/bin/pg_isready.exe" -p 5434
python -m pytest tests/integration/test_rls_fail_closed_with_check.py -q --no-header -p no:cacheprovider 2>&1 | tail -6
```

Beklenen: passed veya **gerekçeli** skip. **Hata (error) OLMAMALI.**
Skip çıkarsa gerekçeyi devir notuna yaz — "toplanıyor" ile "koşuyor" ayrı şeylerdir.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/tests/integration/test_rls_fail_closed_with_check.py
git commit -m "fix(test): RLS bekcisinin goc ankraji arsivde -- iki dizin de aranir

e002f550b squash'i ad6ba3bbe485'i versions/ -> versions_archive/ tasimis.
Test tek yolu civilediginden 8 test collection error veriyordu (S249'da tespit,
gorev no atanmamisti). Cozucu artik iki dizini de ariyor ve bulamazsa hangi
yollara baktigini soyleyerek dusuyor.

Olculen: tests/integration toplama hatasi 2 -> 1 (kalan: G3)."
```

---

## Görev G3: Hiç var olmamış servisin testi toplanmayı kırıyor

**Files:**
- Modify: `backend/tests/integration/test_ocr_sanitizer_rag_guardrails.py`

**Ölçüm:** `git log --all -- backend/services/ocr_sanitizer_service.py` → **boş**.
Servis hiç yazılmamış; test ona rağmen commit'lenmiş.

- [ ] **Adım 1: Kırmızıyı gör**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/integration/test_ocr_sanitizer_rag_guardrails.py --collect-only -q 2>&1 | tail -3
```

Beklenen: `ModuleNotFoundError: No module named 'services.ocr_sanitizer_service'`

- [ ] **Adım 2: Modül düzeyinde görünür skip koy**

> `pytestmark` **çalışmaz** — import hatası ona ulaşmadan patlar (testing.md ders #9).
> Tek doğru mekanizma dosyanın en başında `pytest.skip(..., allow_module_level=True)`.

Dosyanın docstring'inden hemen sonra, **tüm importlardan önce**:

```python
import pytest

pytest.skip(
    "AÇIK BORÇ: services/ocr_sanitizer_service HİÇ YAZILMADI "
    "(git log --all -> 0 commit). Bu test var olmayan bir modüle karşı yazılmış ve "
    "tests/integration toplanmasını kırıyordu. Servis yazılınca bu satır KALDIRILACAK.",
    allow_module_level=True,
)
```

- [ ] **Adım 3: Toplama düzeldi mi**

```bash
python -m pytest tests/integration/ --collect-only -q 2>&1 | tail -4
```

Beklenen: **0 collection error** (G2 de yapıldıysa), toplanan test sayısı > 0.

- [ ] **Adım 4: Borcu görünür yere yaz**

`.claude/lessons/ders_kaydi.yaml` veya `docs/audits/2026-08-12_25uzman/iddialar.yaml`'a
yeni kalem: *"ocr_sanitizer_service yazılmadı, testi skip'li"* + bu commit hash'i.
**Sessiz skip bırakma** — skip bir muafiyet değil, ölçülmüş bir ertelemedir.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/tests/integration/test_ocr_sanitizer_rag_guardrails.py
git commit -m "fix(test): var olmayan modulun testi toplanmayi kiriyordu -- gorunur skip

services/ocr_sanitizer_service git gecmisinde HIC yok (git log --all -> 0 commit).
Test ona ragmen commit'lenmis ve tests/integration toplanmasini kiriyordu.
pytestmark kullanilmadi: import hatasi ona ulasmadan patlar (testing.md #9).

Olculen: tests/integration collection error 1 -> 0. Borc kutuge yazildi."
```

---

## Görev G4: `synced_count` fazla-raporluyor — **KULLANICI KARARI GEREKLİ**

**Files:**
- Modify: `backend/services/offline_sync_service.py:350-359`
- Create: `backend/tests/unit/test_offline_sync_sayac_dogrulugu.py`

**Kusur (ölçüldü):** `services/offline_sync_service.py:358`

```python
card = next((c for c in cards if question_id in c.front_text), None)
if card is not None:
    _apply_fsrs_grade(card=card, is_correct=is_correct, time_seconds=time_seconds)
    db.add(card)

synced += 1   # <-- kart YOKSA hicbir sey kalici olmadi ama yine de "senkronlandi" sayiliyor
```

Öğrenci çevrimdışı 40 soru çözüp senkronlarsa, hiçbirinin FSRS kartı yoksa
API **`synced_count: 40`** döner — hiçbir şey kaydedilmemiştir.

### ⚠️ Burada senin kararın gerekiyor

Üç geçerli yaklaşım var ve seçim **ürün davranışını** belirliyor:

| Seçenek | Davranış | Bedel |
|---|---|---|
| **A** | `synced` yalnız kart güncellendiğinde artar; kalanı `failed` | `failed` "öğrenci hatası" çağrışımı yapar; kart yokluğu öğrencinin suçu değil |
| **B** | Yanıt şemasına 3. alan: `skipped_count` | Frontend sözleşmesi değişir (tüketiciyi de güncellemek gerekir) |
| **C** | Kart yoksa **oluştur**, sonra `synced++` | En doğru davranış ama en büyük iş; FSRS kart üretim kuralını bilmek gerekir |

**Senden istenen (5-10 satır):** `backend/services/offline_sync_service.py` içinde,
`for item in results:` döngüsünün sonundaki sayaç bloğunu seçtiğin davranışa göre yaz.
Karar verirken düşün: öğrenci "40 senkronlandı" görüp ertesi gün hiçbirini tekrar
listesinde bulamazsa ne hisseder? Sessiz kayıp mı, dürüst kısmi başarı mı?

- [ ] **Adım 1: Kararı al** (yukarıdaki A/B/C)

- [ ] **Adım 2: Kırmızı testi yaz** — `backend/tests/unit/test_offline_sync_sayac_dogrulugu.py`

Seçenek **A** için (diğerleri seçilirse assert'i ona göre yaz):

```python
"""Bekci: synced_count GERCEKTEN kalici olan yanit sayisini sayar.

Kusur (S251 olcumu): offline_sync_service.py:358 'synced += 1' FSRS karti
bulunamadiginda da calisiyordu -- ogrenciye hicbir sey kaydedilmeden
"senkronlandi" deniyordu.
"""

import pytest

from services import offline_sync_service


@pytest.mark.asyncio
async def test_karti_olmayan_yanit_synced_sayilmaz(monkeypatch):
    # kart listesi BOS -> hicbir yanit kalici olmaz -> synced_count 0 olmali
    sonuc = await _sync_calistir(kartlar=[], yanit_sayisi=3, monkeypatch=monkeypatch)
    assert sonuc["synced_count"] == 0, "kart yokken synced_count artmamali"
    assert sonuc["failed_count"] == 3
```

`_sync_calistir` yardımcısını gerçek servise karşı yaz — `db`'yi sahte bir
`AsyncSession` ile değil, mevcut test altyapısındaki oturum fixture'ıyla kur.
**Mock'a karşı test yazma:** bu depoda `isinstance(..., AsyncMock)` dallanması
yüzünden 50 test aylarca yalnız mock dalını koşmuştu (S226-S228).

- [ ] **Adım 3: Kırmızıyı gör**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_offline_sync_sayac_dogrulugu.py -q --no-header -p no:cacheprovider
```

Beklenen: FAIL — `assert 3 == 0`

- [ ] **Adım 4: Düzeltmeyi uygula** (senin kararın)

- [ ] **Adım 5: Yeşili gör + mevcut offline-sync bekçileri bozulmadı mı**

```bash
python -m pytest tests/unit/test_offline_sync_sayac_dogrulugu.py tests/unit/test_offline_sync_docstring_tutarliligi.py -q --no-header -p no:cacheprovider
grep -rn "synced_count" ../frontend/src --include=*.ts --include=*.tsx | head
```

İkinci komut boş değilse **frontend tüketicisi var** — B seçildiyse onu da güncelle.

- [ ] **Adım 6: Commit + mutasyon** (G1 Adım 8 kalıbıyla)

---

## Görev G5: `ServiceError` ailesi için HTTP eşlemesi kayıtlı değil

**Files:**
- Modify: `backend/core/application.py` (`_rate_limit_exceeded_handler` kaydının yanına)
- Create: `backend/tests/unit/test_service_error_http_kodu.py`

**Ölçüm ve dürüst uyarı:** Bu kalemin **bugünkü kullanıcı-görünür etkisi yok**.
Canlı `api/` + `services/` içinde bu aileden yalnız **1** `raise` var; canlı yetki kapısı
zaten `HTTPException(403)` fırlatıyor ve doğru çalışıyor (kimliksiz istek → **401** ölçüldü).
Değeri **ileriye dönük**: X06 (c) kapı birleştirmesi bu aileyi canlandırırsa, hazır olur.

> **Toptan `setup_exception_handlers(app)` ÇAĞIRMA.** O fonksiyon
> `core/exception_handlers.py:545`'te `Exception` catch-all'ını da kaydediyor ve
> `core/application.py:354`'teki mevcut catch-all'ı devirir. Blast radius uygulama geneli.
> Yalnız `ServiceError` kaydedilecek.

- [ ] **Adım 1: Kırmızı testi yaz** — `backend/tests/unit/test_service_error_http_kodu.py`

```python
"""Bekci: ServiceError ailesi dogru HTTP koduna eslenmeli (403/404/503), 500'e DEGIL.

Kusur (S251 olcumu): canli uygulamada bu aile icin KAYITLI HANDLER YOK; uc ayri
403-donduren handler modulu yazilmis ama ucu de olu kod. Sonuc: dogru kurulmus
bir AuthorizationError dahi istemciye 500 doner.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.exceptions import AuthorizationError, NotFoundError


def _uygulama() -> FastAPI:
    from core.application import _servis_hatasi_handleri_kaydet

    app = FastAPI()
    _servis_hatasi_handleri_kaydet(app)

    @app.get("/yetkisiz")
    async def yetkisiz():
        raise AuthorizationError("Bu isleme yetkiniz yok")

    @app.get("/yok")
    async def yok():
        raise NotFoundError("Soru bulunamadi", resource_type="question")

    return app


def test_authorization_error_403_doner():
    with TestClient(_uygulama(), raise_server_exceptions=False) as istemci:
        assert istemci.get("/yetkisiz").status_code == 403


def test_not_found_error_404_doner():
    with TestClient(_uygulama(), raise_server_exceptions=False) as istemci:
        assert istemci.get("/yok").status_code == 404


def test_kontrol_kolu_handler_kayitsizken_500_donerdi():
    """Kontrol kolu: kayit YAPILMAZSA 500 doner -- yani yukaridaki yesiller anlamli."""
    app = FastAPI()

    @app.get("/yetkisiz")
    async def yetkisiz():
        raise AuthorizationError("x")

    with TestClient(app, raise_server_exceptions=False) as istemci:
        assert istemci.get("/yetkisiz").status_code == 500
```

- [ ] **Adım 2: Kırmızıyı gör**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit/test_service_error_http_kodu.py -q --no-header -p no:cacheprovider
```

Beklenen: `ImportError: cannot import name '_servis_hatasi_handleri_kaydet'`

- [ ] **Adım 3: Minimal kaydı yaz**

`backend/core/application.py` içinde, `app.add_exception_handler(RateLimitExceeded, ...)`
satırının (≈316) hemen ardına gelecek şekilde:

```python
def _servis_hatasi_handleri_kaydet(app: FastAPI) -> None:
    """ServiceError ailesini HTTP kodlarina esler.

    YALNIZ ServiceError kaydedilir. core/exception_handlers.py:518'deki toptan
    setup_exception_handlers(), :545'te ``Exception`` catch-all'ini da kaydedip
    bu dosyadaki :354 catch-all'ini devirirdi -- blast radius uygulama geneli.
    """
    from core.exception_handlers import ExceptionHandlers

    handlers = ExceptionHandlers(turkish_messages=True)
    app.add_exception_handler(ServiceError, handlers.service_exception_handler)
```

ve uygulama kurulumunda (RateLimitExceeded kaydının hemen altında) çağır:

```python
    _servis_hatasi_handleri_kaydet(app)
```

`ServiceError` importunu dosyanın import bloğuna ekle:

```python
from core.exceptions import ServiceError
```

> Starlette handler'ı MRO üzerinden bulur → `AuthorizationError`, `NotFoundError` gibi
> **tüm alt sınıflar** bu tek kayıtla kapsanır. Eşleme
> `core/exception_handlers.py:162-169`'daki `status_mapping`'ten gelir.

- [ ] **Adım 4: Yeşili gör**

```bash
python -m pytest tests/unit/test_service_error_http_kodu.py -q --no-header -p no:cacheprovider
```

Beklenen: **3 passed**.

- [ ] **Adım 5: Mevcut hata davranışı bozulmadı mı (regresyon)**

```bash
python -m pytest tests/core/test_error_handler.py tests/integration/test_error_handling_system.py tests/fast/test_exception_handling_execution.py -q --no-header -p no:cacheprovider 2>&1 | tail -4
```

Beklenen: G1 öncesindeki sayılarla aynı; **yeni failed YOK**.

- [ ] **Adım 6: Canlıda doğrula (konteyner)**

```bash
cd C:/Users/husey/kiro2/backend
MSYS_NO_PATHCONV=1 docker cp core/application.py kiro2-backend:/app/core/application.py
MSYS_NO_PATHCONV=1 docker exec kiro2-backend find /app/core -name "*.pyc" -delete
docker restart kiro2-backend && sleep 90
curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 http://localhost:8000/health
MSYS_NO_PATHCONV=1 docker exec -e PYTHONPATH=/app -w /app kiro2-backend \
  python -c "from main import app; print(len(app.exception_handlers), 'handler kayitli')"
```

Beklenen: `/health` → **200**, handler sayısı **5 → 6**.
`Start-Sleep 90` **kısaltma** — bu backend 150 router yüklüyor, açılış 60-85 sn.

- [ ] **Adım 7: Commit + mutasyon**

Mutasyon: `_servis_hatasi_handleri_kaydet(app)` çağrısını yorum satırı yap →
3 testten en az 2'si düşmeli. Sonra `git checkout HEAD -- backend/core/application.py`
ve `git status --short` **boş** olduğunu doğrula.

---

## Görev G6: Göç güvenlik testleri **koşulsuz** susturulmuş (U25)

**Files:**
- Modify: `backend/tests/test_migrations.py:37-40`

**Ölçüm:** `pytestmark = pytest.mark.skipif(True, reason="Migration tests require real
PostgreSQL, 1F + 10E")` — **16 test**, hepsi koşulsuz atlanıyor. Gerekçe "gerçek PostgreSQL
gerekir" diyor ama koşul `True`; PG **çalışıyor** (`pg_isready -p 5434` → kabul ediyor).
Gerçek sebep gerekçenin kuyruğunda saklı: *1F + 10E* — testler **bozuktu** ve düzeltmek
yerine susturuldu. Bu dosyada `test_no_manual_table_drops_without_backup` var: bu deponun
5 Ağu içerik kaybı tam o sınıftı ve bekçisi o gün de ölüydü.

> Bu görev **keşif içerir**: susturma kalkınca 1F+10E geri gelebilir. Amaç hepsini yeşile
> boyamak değil, **gerçek durumu görünür kılmak**. Yanlış-SIFIR bir ilerleme sayacında tek
> kabul edilemez hata türüdür.

- [ ] **Adım 1: Gerçek durumu ölç (susturmayı GEÇİCİ kaldır, commit ETME)**

```bash
cd C:/Users/husey/kiro2/backend
"C:/Program Files/PostgreSQL/18/bin/pg_isready.exe" -p 5434
python -c "from pathlib import Path; p=Path('tests/test_migrations.py'); v=p.read_bytes(); assert v.count(b'pytest.mark.skipif(')==1; p.write_bytes(v.replace(b'skipif(
    True,', b'skipif(
    False,'))"
python -m pytest tests/test_migrations.py -q --tb=line -p no:cacheprovider 2>&1 | tail -12
cd .. && git checkout HEAD -- backend/tests/test_migrations.py && git status --short --untracked-files=no backend/tests/test_migrations.py
```

Son komutun çıktısı **BOŞ** olmalı (geri alım doğrulandı). Kaç passed/failed/error
gördüğünü **yaz** — sonraki adım buna bağlı.

- [ ] **Adım 2: Susturmayı koşullu yap (sabit `True` yerine ÖLÇÜLEN koşul)**

```python
import os

import pytest
from sqlalchemy import create_engine, text


def _postgres_erisilebilir() -> bool:
    """Gocler gercek PostgreSQL ister; sqlite'a SESSIZCE dusmek yanlis-yesil uretir."""
    dsn = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or ""
    if "postgresql" not in dsn:
        return False
    try:
        with create_engine(dsn).connect() as baglanti:
            baglanti.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _postgres_erisilebilir(),
    reason=(
        "Gercek PostgreSQL yok (TEST_DATABASE_URL/DATABASE_URL postgresql degil veya "
        "baglanti kurulamiyor). SABIT True DEGIL: PG varsa bu testler KOSAR."
    ),
)
```

- [ ] **Adım 3: Kalan gerçek kırıkları TEK TEK işaretle**

Adım 1'de failed/error veren testleri tek tek `@pytest.mark.xfail(strict=True,
reason="<gercek sebep>")` ile işaretle. Modül düzeyi toptan susturma **geri konmayacak**.
`strict=True` kritik: test beklenmedik şekilde geçmeye başlarsa kapı düşer ve haber verir.

- [ ] **Adım 4: Yeni durumu ölç ve YAZ**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/test_migrations.py -q --no-header -p no:cacheprovider 2>&1 | tail -4
```

Beklenen: "16 skipped" yerine gerçek dağılım (ör. `9 passed, 7 xfailed`).
Sayıyı devir notuna yaz — *16 skipped* ile *9 passed + 7 xfailed* aynı şey değildir.

- [ ] **Adım 5: Commit**

```bash
cd C:/Users/husey/kiro2
git add backend/tests/test_migrations.py
git commit -m "fix(test): goc guvenlik testleri KOSULSUZ susturulmustu (U25)"
```

---

## Kapanış (tüm görevler bittikten sonra)

- [ ] **Tam regresyon**

```bash
cd C:/Users/husey/kiro2/backend
python -m pytest tests/unit tests/core tests/fast -q --no-header -p no:cacheprovider 2>&1 | tail -6
```

- [ ] **Kapı borcu deltasını ölç** (S250 taban çizgisi: mypy 14 / ruff 12 / bandit 1)

```bash
cd C:/Users/husey/kiro2
pre-commit run mypy --files backend/core/exceptions.py backend/core/enhanced_authentication.py 2>&1 | tail -3
```

- [ ] **`.claude/sessions/latest.md`** güncelle: kapanan kalemler + ölçülen deltalar +
      açık kalanlar + E3 gerekçesi (G4/G5 `backend/services` ve `backend/api` sınırında).

- [ ] **`docs/audits/2026-08-12_25uzman/iddialar.yaml`** — kapanan kalemlerin
      `zorlayici_test` ve `commit` alanlarını doldur.

---

## Bu planda BİLEREK olmayanlar (kullanıcı onayı gerekir)

| Kalem | Neden ertelendi |
|---|---|
| X06 (c) 3 rol kapısının birleştirilmesi | **32 canlı uç** etkileniyor (`require_role` 19 · `require_org_role` 7 · `require_admin` 6). Kendi turunu ve kendi E2E'sini hak ediyor |
| X06 (d) 16 ölü tanımın silinmesi | CLAUDE.md: *"önceden var olan dead code'a istenmedikçe dokunma"* — açık istek gerekir |
| Beş ölü modülün silinmesi | Borcu 24→0 indirir ama geri alınamaz; `query_builder`/`transaction_manager`/`enhanced_database`/`migration_framework`/`connection_pool_optimizer` |
| `enhanced_authentication.py`'deki 6 mypy hatası | Ölü `authenticate_user` alt ağacında; yukarıdaki silme kararı bunları zaten götürebilir |
| SMTP #441 | Operatör işi, kod değil |
