---
name: testing-rules
description: KIRO2 test standartlari ve kalite gereksinimleri
trigger: when-testing
priority: high
---

# Testing Rules - KIRO2 Standards

## TEST YAZIM KURALLARI

### Python Tests (pytest)

```python
# DOGRU - Anlamli assertion
def test_user_creation():
    user = create_user(email="test@example.com")
    assert user.email == "test@example.com"
    assert user.id is not None

# YANLIS - Reward hacking
def test_user_creation():
    assert True  # YASAK!
```

### TypeScript Tests (vitest)

```typescript
// DOGRU - Anlamli assertion
test('should create user', () => {
    const user = createUser({ email: 'test@example.com' });
    expect(user.email).toBe('test@example.com');
    expect(user.id).toBeDefined();
});

// YANLIS - Reward hacking
test('should create user', () => {
    expect(true).toBe(true);  // YASAK!
});
```

## YASAK TEST PATTERNLERI

ASLA bu patternleri kullanma:

```python
# Python yasak patternler
assert True
assert 1 == 1
pass  # empty test
...   # ellipsis test

# pytest.skip without reason
@pytest.mark.skip
def test_something():
    pass
```

```typescript
// TypeScript yasak patternler
expect(true).toBe(true);
expect(1).toBe(1);
it.skip('should do something');  // without reason
```

## COVERAGE GEREKSINIMLERI

| Modul | Minimum Coverage |
|-------|------------------|
| backend/services | 80% |
| backend/api | 75% |
| frontend/src/components | 70% |
| frontend/src/services | 80% |
| **Global** | **80%** |

## TEST IZOLASYONU

- Her test bagimsiz olmali
- Testler arasi state paylasilmamali
- Database testleri transaction rollback kullanmali
- Mock'lar test sonunda temizlenmeli

## KIRO2 SPESIFIK TESTLER

### IRT Parametre Validasyonu
```python
@pytest.mark.parametrize("difficulty", [-5.0, 4.1, 10.0])
def test_invalid_difficulty_rejected(difficulty):
    with pytest.raises(ValueError):
        create_question(difficulty=difficulty)
```

### Turkce Karakter Testleri
```python
def test_turkish_upper():
    assert turkish_upper("istanbul") == "ISTANBUL"
    assert turkish_upper("diyarbakir") == "DIYARBAKIR"
```

### ZPD Bolge Kontrolu
```python
def test_zpd_optimal_selection():
    prob = calculate_success_probability(ability=0.0, difficulty=0.0)
    assert 0.15 <= prob <= 0.85, "Soru ZPD disinda"
```

## TEST CALISTIRMA KOMUTLARI

```bash
# Tum testler
pytest -v --tb=short

# Coverage ile
pytest --cov=backend --cov-report=term-missing

# Ilk hatada dur
pytest -x

# Belirli marker
pytest -m "not slow"

# Paralel
pytest -n auto
```

## FLAKY TEST TESPIT

Flaky test tespit edilirse:

1. Test'i `@pytest.mark.flaky(reruns=3)` ile isaretle
2. Root cause analizi yap
3. Duzelt veya skip with reason ekle

## MOCK KULLANIM KURALLARI

- Over-mocking'den kacin
- Sadece external dependencies mock'la
- Database erisimi icin in-memory SQLite kullan
- HTTP istekleri icin httpx mock veya responses kullan

## OGRENILEN DERSLER (Lessons Learned)

### 1. Fixture/Scope Kurali
Buyuk degisiklik yapmadan once bagimlilik ve scope'u anla:

```python
# YANLIS - Fixture'i tamamen kaldirmak
# Conftest'teki fixture baska context'te calismayabilir

# DOGRU - Hibrit yaklasim
# Conftest'te merkezi fonksiyon, dosyada lokal fixture
from tests.conftest import _generate_test_jwt, TEST_JWT_SECRET

@pytest.fixture
def auth_headers(monkeypatch):
    monkeypatch.setattr("core.dependencies.JWT_SECRET", TEST_JWT_SECRET)
    token = _generate_test_jwt("1", "test@example.com", "student")
    return {"Authorization": f"Bearer {token}"}
```

### 2. Hibrit Yaklasim (DRY + Guvenlik)
Merkezi fonksiyon + lokal fixture kombinasyonu en guvenli:

| Yaklasim | DRY | Guvenlik | Tercih |
|----------|-----|----------|--------|
| Tamamen merkezi | 10/10 | 5/10 | Riskli |
| Tamamen lokal | 2/10 | 10/10 | Kod tekrari |
| **Hibrit** | **8/10** | **9/10** | **Onerilen** |

### 3. Adim Adim Ilerleme
Her degisiklikten sonra test calistir:

```bash
# 1. Degisiklik yap
# 2. Hemen test calistir
pytest tests/affected_file.py -v --tb=short

# 3. Basarisiz ise geri al
# 4. Basarili ise devam et
```

### 4. Geri Alma Stratejisi
Her adimda geri donus noktasi olustur:

```python
# DOGRU - Kucuk, geri alinabilir degisiklikler
# Adim 1: Import ekle (test et)
# Adim 2: Fonksiyon cagir (test et)
# Adim 3: Eski kodu kaldir (test et)

# YANLIS - Tek buyuk degisiklik
# Tum dosyayi bir seferde degistir (geri almak zor)
```

### 5. Test Sonrasi Dogrulama Zorunlu
Her kod degisikliginden sonra:

```bash
# Minimum dogrulama
pytest -x --tb=short -q

# Etkilenen dosyalar
pytest tests/changed_module.py -v
```

### 6. Karma Import Stili SQLAlchemy Cakismasi (Session 11)
`from models.base import Base` (absolute) ve `from .base import Base` (relative) ayni projede
karistirildiginda SQLAlchemy iki farkli MetaData nesnesi olusturur ve "Table already defined" hatasi verir.

```python
# YANLIS - Absolute import (models/ dizininden calisirken sorun cikmaz ama
# backend.models uzerinden import edildiginde cift yukleme yapar)
from models.base import Base

# DOGRU - Relative import (her zaman ayni Base nesnesini kullanir)
from .base import Base

# WORKAROUND - Karma import kacinilmazsa
__table_args__ = {"extend_existing": True}
```

### 7. Session-Scoped Fixture Graceful Degradation (Session 11)
Session-scoped fixture'lar (`scope="session"`) external servislere (DB, Redis) baglimliysa,
servis yokken TUM testleri bloke eder. pytest.mark.skipif bile bunu onleyemez cunku
fixture setup skipif'ten once calisir.

```python
# DOGRU - Fixture icinde kontrol
@pytest.fixture(scope="session")
def db_engine():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("Database not available")
    yield engine

# YANLIS - skipif decorator (fixture setup'i engellemez)
@pytest.mark.skipif(not DB_AVAILABLE, reason="No DB")
def test_something(db_engine):  # fixture YINE calisir ve fail olur
    ...
```

### 8. Turkce Enum Adlari (Session 11, KIRO2 Spesifik)
KIRO2'de enum degerleri Turkce: `SubjectType.MATEMATIK` (MATHEMATICS degil),
`DifficultyLevel.COK_KOLAY` (VERY_EASY degil). Test yazarken Ingilizce varsayma.

```python
# YANLIS
subject = SubjectType.MATHEMATICS  # AttributeError!

# DOGRU
subject = SubjectType.MATEMATIK

# KONTROL: Enum degerlerini daima once incele
print(list(SubjectType))  # Gercek degerleri gor
```

### 9. pytestmark MODULE DEGISKENIDIR, Preprocessor Direktifi DEGIL (Session 17)
`pytestmark = pytest.mark.skipif(True, ...)` modulun TAMAMEN yuklenmesini gerektirir.
Import basarisiz olursa veya asilirsa bu satira ASLA ulasilamaz.

```python
# YANLIS - Import hatasi verirse pytestmark'a ulasilamaz
from core.removed_module import RemovedClass  # ModuleNotFoundError!
pytestmark = pytest.mark.skipif(True, reason="skip")  # BURAYA ASLA ULASILMAZ

# YANLIS - Import asilirsa pytestmark'a ulasilamaz
from main import app  # 10+ saniye surebilir, Windows'ta timeout
pytestmark = pytest.mark.skipif(True, reason="skip")  # ASLA ULASILMAZ

# DOGRU - pytest.skip() execution'i ANINDA durdurur
"""Module docstring"""
import pytest
pytest.skip("reason", allow_module_level=True)
# Buradan sonra HICBIR SEY calismaz - import hatalari bile onemli degil
```

### 10. Toplu Dosya Modifikasyonunda IDEMPOTENT Script Kullan (Session 17)
Birden fazla script ayni dosyalari hedeflediginde veri bozulmasi olusur.
3 script 107+ dosyayi modifiye etti, cakisan dosyalarda syntax hatalari olustu.

```python
# YANLIS - Birden fazla script ayni dosyalari degistirir
# Script 1: pytestmark ekler (21 dosya)
# Script 2: pytestmark ekler (76 dosya)
# Script 3: pytest.skip ekler (31 dosya)
# Sonuc: Cakisan dosyalarda syntax bozulmasi!

# DOGRU - TEK idempotent script, sentinel marker ile
SENTINEL = "# UNIVERSAL_SKIP_APPLIED"

def fix_file(filepath):
    content = read(filepath)
    if SENTINEL in content:
        return "already_done"  # Idempotent!

    # Docstring'den sonra, TUM importlardan ONCE ekle
    insert_skip_after_docstring(content, SENTINEL)
```

### 11. Metin Isleme Python Blok Yapisini Anlayamaz (Session 17)
Satir-bazli metin isleme (startswith, strip) try/except blok yapisini goremez.
`pytestmark` blogu `except:` govdesinin icine yerlestirildi → IndentationError.

```python
# YANLIS - Script try/except'i anlayamaz:
# Script "from X import Y" gorur → sonrasina pytestmark ekler
# Ama bu satir except blogunun icindeydi!
try:
    from tests.conftest import _generate_test_jwt
except ImportError:
    import jwt
    pytestmark = pytest.mark.skipif(True, ...)  # <-- BURAYA EKLENDI (HATALI!)
    TEST_JWT_SECRET = "..."  # <-- IndentationError!

# DOGRU - EN BASA ekle (blok yapisi onemli degil)
import pytest
pytest.skip("reason", allow_module_level=True)
# Artik try/except bloklari bile onemli degil - asla calismazlar
```

### 12. Toplu Islemden Once 2-3 Dosyada Sample Dogrulama Yap (Session 17)
76 dosyayi toplu modifiye eden script calistirildi ama ciktisi dogrulanmadi.
4 dosyada syntax bozulmasi ancak tum dizin test edildiginde kesfedildi.

```bash
# YANLIS - Scripti calistir, sonucu kontrol etme
python skip_failing_tests.py  # 76 dosya modifiye etti
# ... saatler sonra: 22 collection error!

# DOGRU - Once 2-3 dosyada test et
python skip_failing_tests.py --dry-run  # Ne yapacagini goster
python skip_failing_tests.py --only tests/slow/test_api_auth_comprehensive.py  # Tek dosya
python -m pytest tests/slow/test_api_auth_comprehensive.py --co  # Collection test
# Basarili? → Tum dosyalari calistir
```

### 13. Fix/Skip Oranini Takip Et (Session 6-19 Analizi)
Her session sonunda fix/skip oranini hesapla. %50+ skip = teknik borc alarm.

```python
# Her session sonunda hesapla:
fix_count = 6   # Gercekten duzeltilen test dosya sayisi
skip_count = 19  # Module/class skip edilen dosya sayisi
ratio = fix_count / (fix_count + skip_count)  # 0.24 = %24 fix

# HEDEF: ratio >= 0.50 (en az %50 gercek fix)
# ALARM: ratio < 0.30 (cok fazla skip, teknik borc birikiyor)
```

### 14. Tekrarlayan Sorunlari ROOT CAUSE'dan Coz (Session 6-19 Analizi)
Ayni sorun 2+ session'da gorulurse PATCH yapma, root cause coz.
Ornekler:
- Health endpoint 503: Session 7, 12, 19'da 3 kez patch yapildi
- SQLAlchemy import cakismasi: Session 11'de ders cikarildi, Session 19'da tekrarladi
- httpx AsyncClient deprecated: Session 8, 12'de skip edildi

```python
# YANLIS - Her testte ayri patch
def test_health(mock_checker):
    mock_checker.return_value = {"status": "ok"}  # Patch

# DOGRU - Root cause: Health check neden 503 donuyor?
# conftest.py'de test ortami icin health check konfigurasyonu
@pytest.fixture(autouse=True)
def mock_health_dependencies(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    # Health check icin gerekli tum bagimliliklar
```

### 15. Ogrenilen Dersleri ENFORCE Et (Session 6-19 Analizi)
Ders cikarilmasi YETMEZ. 3 adim gerekli:
1. testing.md'ye yaz (YAPILIYOR)
2. Pre-commit hook veya lint rule ekle (YAPILMIYOR)
3. CI/CD'de kontrol et (YAPILMIYOR)

```bash
# Ornek: SQLAlchemy absolute import yasagi
# .pre-commit-config.yaml'a ekle:
- repo: local
  hooks:
  - id: no-absolute-model-import
    name: No absolute model imports
    entry: 'from models\.'
    language: pygrep
    files: 'backend/models/.*\.py$'
    # "from models.xxx" yerine "from .xxx" kullanilmali
```

### 16. Model/ORM Degisiklikleri En Yuksek Oncelik (Session 19)
Model dosyalarindaki sorunlar (import, relationship, duplicate class)
BINLERCE testi etkiler. Session 19'da 7 model fix ile 7973 test acildi.

```
# Test failure triage sirasi:
1. ONCE: models/ dizinindeki sorunlari kontrol et
   - Import cakismasi (absolute vs relative)
   - Duplicate class tanimi
   - Relationship path hatalari
2. SONRA: Test dosyalarindaki sorunlari fix et
3. EN SON: Test'i skip et (sadece external dependency yoksa)
```

### 17. Yeni Service/Agent Olusturdugunda Test ZORUNLU (Session 9)
Session 9'da 5 agent + 1 service olusturuldu, HICBIRININ testi yok.

```python
# YANLIS - Service olusturduktan sonra baska ise gec
class CognitiveLoadCalculator:
    def calculate(self, ...): ...
# "Test sonra yazilir" → ASLA yazilmaz

# DOGRU - Ayni session'da en az 3 test
def test_cognitive_load_happy_path():
    calc = CognitiveLoadCalculator()
    result = calc.calculate(valid_input)
    assert result.score > 0

def test_cognitive_load_edge_case():
    ...

def test_cognitive_load_error():
    ...
```

### 18. Session Notu Standart Formati (Session 6-19 Analizi)
Eksik/tutarsiz session notlari context kaybi yapar.

```markdown
## Session X (Tarih)
**Giris:** [passed] passed, [skipped] skipped, [failed] failed
**Cikis:** [passed] passed, [skipped] skipped, [failed] failed
**Commit:** [hash]
**Branch:** [branch]
**Fix/Skip:** [X] fix, [Y] skip (oran: Z%)
**Yapilan:** (tablo)
**Tekrarlayan:** (varsa onceki session referansi)
**Sonraki:** (1 cumle)
```

### 19. Toplu Script Dry-Run ZORUNLU (Session 17)
10+ dosyayi etkileyen script icin dry-run + sample dogrulama zorunlu.
Session 17'de 3 script 107 dosya bozdu cunku dry-run yapilmadi.

```bash
# YANLIS - Hemen calistir
python fix_all_tests.py  # 107 dosya bozuldu!

# DOGRU - 4 adimli guvenli islem
python fix_all_tests.py --dry-run          # 1. Ne yapacagini goster
python fix_all_tests.py --only file1.py    # 2. Tek dosyada dene
pytest file1.py --co                        # 3. Collection dogrula
python fix_all_tests.py                     # 4. Basariliysa tamamini calistir
```

### 20. httpx ASGITransport Toplu Migration (Session 8, 12)
httpx 0.27+ icin AsyncClient(app=...) deprecated. 6+ dosya skip edildi.
Tek tek skip yerine toplu migration yapilmali.

```python
# ESKI (deprecated, 6+ test dosyasinda skip sebebi)
async with AsyncClient(app=app, base_url="http://test") as client:
    response = await client.get("/api/health")

# YENI (httpx 0.27+ uyumlu)
from httpx import ASGITransport
transport = ASGITransport(app=app)
async with AsyncClient(transport=transport, base_url="http://test") as client:
    response = await client.get("/api/health")
```
