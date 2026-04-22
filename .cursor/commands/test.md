# Test Çalıştır

KIRO2 testlerini pattern-based veya komple çalıştır. Kullanıcı pattern/scope'u
komut sonrası belirtecek.

## Karar Matrisi

Kullanıcının verdiği argumana göre:

| Argüman | Komut |
|---|---|
| (boş) | `cd backend && pytest tests/unit -v --tb=short` |
| `unit` | `cd backend && pytest tests/unit -v --tb=short` |
| `integration` | `cd backend && pytest tests/integration -v --tb=short` |
| `coverage` | `cd backend && pytest --cov=backend --cov-report=term-missing` |
| `fast` | `cd backend && pytest --lf -v` (last failed) |
| `frontend` | `cd frontend && npm test -- --run` |
| `e2e` | `cd frontend && npx playwright test` |
| `all` | Backend + frontend + e2e sırayla |
| (pattern) | `cd backend && pytest -k "<pattern>" -v --tb=short` |

## Gereksinimler

- Her test koşumunda `-v --tb=short` (verbose + kısa traceback)
- İlk hatada dur için `-x` ekle (debug modda)
- Failure'lar varsa liste halinde özet ver, ilk 3'ünün traceback'ini göster

## Pre-flight (Session 120 dersi)

Backend test öncesi:
```bash
pg_isready -p 5434 || echo "PG DOWN"
redis-cli ping || echo "REDIS DOWN"
```

Servisler down ise testler skip olur (fixture'lar graceful degradation yapıyor).

## Rapor Formatı

```
## Test Sonuçları
- Passed: N
- Failed: M
- Skipped: K
- Baseline: 916 (Session 120 referansı)

### Failures (varsa ilk 3)
1. tests/X::test_Y — sebep özeti
2. ...

### Öneriler
- ...
```

## İlgili Kurallar

- Test yazma/düzeltme için `.claude/rules/testing.md` referans
- Reward hacking pattern'ları (`assert True`) yasak — `.cursor/rules/10-backend.mdc`
- Flaky test → `@pytest.mark.flaky(reruns=3)` ile işaretle
