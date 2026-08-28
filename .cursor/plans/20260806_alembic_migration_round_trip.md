# Plan: Alembic Migration Round-Trip & DB Şema Doğrulama Testi

## Kapsam ve Amaç
KIRO2 veritabanı şemasının (PostgreSQL / SQLite) Alembic migration geçmişinin tutarlılığının, geriye dönüklüğünün (downgrade desteği) ve çift yönlü `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` tur testinin doğrulanması.

## Test ve Doğrulama Adımları

1. **Alembic Tekil Head Kontrolü:**
   - `alembic heads` çıktısında birden fazla dal (branch conflict) olmaması (`fa067642bdfe (head)`).

2. **Migration Reversibility (Tersine Çevrilebilirlik) Testi:**
   - Tüm Alembic migration dosyalarının (`alembic/versions/*.py`) hem `upgrade()` hem `downgrade()` fonksiyonlarına sahip olduğunu doğrulayan `test_alembic_migration_roundtrip_reversibility` testinin `backend/tests/db/test_migrations.py` içerisine eklenmesi/güncellenmesi.

3. **Round-Trip İşlem Testi:**
   - `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` komut zincirinin çalıştırılması.

4. **Kod Kalitesi ve Test Koşumu:**
   - `pytest backend/tests/db/test_migrations.py -v` (%100 PASS).
   - `ruff check backend/tests/db/test_migrations.py` (0 Hata).
