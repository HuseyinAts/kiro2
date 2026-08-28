# Plan: CI/CD Pipeline Paralelleştirme (`pytest-xdist` & Vitest Worker Ayarları)

## Kapsam ve Amaç
Backend (~10.000 test) ve Frontend (300+ Vitest testi) test suitelerinin paralel iş parçacıkları (multi-process workers) ile koşturularak CI/CD boru hattı (GitHub Actions) ve yerel test sürelerinin %70-80 oranında düşürülmesi; Vitest bellek sızıntılarının (`max-old-space-size`) `forks` havuzuyla önlenmesi.

## Uygulama Adımları

1. **Backend `pytest-xdist` Konfigürasyonu:**
   - `backend/pytest.ini` ve `pyproject.toml` içerisindeki `addopts` ayarlarına `-n auto` ve `--dist=loadscope` (test sınıfları ve modül izolasyonu için) eklenmesi.
   - Seri koşması gereken (shared state / DB seed bağımlı) testler için `-m "not serial"` veya `dist=loadscope` mekanizmasının korunması.

2. **Frontend Vitest Worker Pool Yapılandırması (`frontend/vite.config.ts`):**
   - `test` nesnesine `pool: 'forks'` ve `poolOptions.forks` sınırlaması eklenmesi (`maxForks: process.env.CI ? 4 : undefined`).
   - Bellek şişmesini engelleyen izole process temizliği.

3. **CI/CD İş Akışı Güncellemesi (`.github/workflows/ci.yml`):**
   - Backend test adımına `-n auto` parametresinin eklenmesi ve `pytest-xdist` bağımlılığının doğruluk kontrolü.
   - Frontend test adımına `--pool=forks` parametresinin eklenmesi.

4. **Doğrulama ve Testler:**
   - Backend unit testlerini `pytest backend/tests/unit -n auto` ile doğrulama.
   - Frontend testlerini `npm test` ile doğrulama.
