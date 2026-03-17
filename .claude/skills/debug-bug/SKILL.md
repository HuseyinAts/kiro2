# Debug Bug — Root Cause + TDD

Bug aciklamasi veya failing test path alir, root cause analizi + fix uygular.

## Kullanim
/debug-bug "health endpoint 503 donuyor"
/debug-bug backend/tests/test_auth.py::test_login

## Adimlar

1. **INFRA-FIRST** (30 saniye):
   - `docker ps --format "table {{.Names}}\t{{.Status}}"`
   - `pg_isready -p 5434` (veya docker exec)
   - `redis-cli ping`
   - `curl -s http://localhost:8000/api/v1/health`
   Herhangi biri fail → ONCE altyapiyi duzelt, SONRA bug'a bak.

2. **Reproduce** (hatayi tekrarla):
   - Endpoint hatasi: `curl -s http://localhost:8000/api/v1/ENDPOINT | head -20`
   - Test hatasi: `cd backend && pytest TEST_PATH -x --tb=short`
   - Sessiz basarisizlik: 200 donup bos data mi kontrol et

3. **Root Cause Analysis tablosunu GOSTER** (debugging-first.md formati)

4. **TDD Fix** (max 3 iterasyon):
   - Fail eden test yoksa → ONCE test yaz
   - Minimal fix (max 3 dosya)
   - pytest ile dogrula
   - Regression check: ilgili test suite

5. **Raporla:**
   Fix/Skip: X dosya fix, Y dosya skip
   Etkilenen testler: [test sonuclari]
