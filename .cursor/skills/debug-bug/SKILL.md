---
name: debug-bug
description: Bug veya failing test için root cause analizi + TDD fix. INFRA-FIRST yaklaşımı, max 3 iterasyon.
---

# Debug Bug — Root Cause + TDD

Bug açıklaması veya failing test verildiğinde:
1. Altyapıyı kontrol et
2. Reproduce et
3. Root cause'u belirle
4. TDD döngüsüyle fix (max 3 iterasyon)

## Ne Zaman Yüklenmeli

- "bug var" / "hata alıyorum" / "X çalışmıyor" raporu
- Failing test path verildiğinde
- 500/503/404 hatası raporunda
- Sessiz başarısızlık (200 ama boş data)

## Adım 1 — INFRA-FIRST (30 saniye)

Bug'a dalmadan önce altyapı canlı mı:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
pg_isready -p 5434      # PostgreSQL
redis-cli ping           # Redis
curl -s http://localhost:8000/api/v1/health
```

Herhangi biri fail → ÖNCE altyapı, sonra bug.

## Adım 2 — Reproduce

**Endpoint hatası:**
```bash
curl -s http://localhost:8000/api/v1/ENDPOINT | head -20
```

**Test hatası:**
```bash
cd backend && pytest TEST_PATH -x --tb=short
```

**Sessiz başarısızlık:**
- 200 dönüyor ama boş data → Dual Table Trap şüphesi
- `is_active` filtresi eksik mi?
- `question_bank` vs `questions` tablo adı doğru mu?

## Adım 3 — Root Cause Tablosu

`.claude/rules/debugging-first.md` formatında sun:

```markdown
| Semptom | Olası Kök | Doğrulama | Fix |
|---|---|---|---|
| 503 | Docker down | docker ps | compose up -d |
| 503 | PG unreachable | pg_isready | restart service |
| 200 boş | Dual Table | SELECT COUNT question_bank | model değiştir |
| 404 | Router kayıtsız | loader.py check | ROUTER_MAPPING'e ekle |
| 500 | Middleware HTTPException | logs | JSONResponse yap |
```

## Adım 4 — TDD Fix (max 3 iter)

- Fail eden test yoksa → önce test yaz
- Minimal fix (max 3 dosya)
- Pytest ile doğrula
- Regression check: ilgili suite

## Adım 5 — Raporla

```
Fix Sonucu
- Iterasyon: N
- Fix/Skip: X dosya fix, Y skip
- Etkilenen test: [sonuç]
- Root cause: [1 cümle]
- Fix: [dosya:satır]
- Regression: PASS/FAIL
```

## Phantom Sorun Filtresi (Session 121)

Rapordaki her "eksik/bozuk" iddiasını DOĞRULA önce:

- "Tablo X eksik" → `grep 'CREATE TABLE X'` + `information_schema`
- "Kolon Y yok" → `grep 's.Y' app/api/` (kod kullanıyor mu?)
- "Endpoint 404" → `grep ROUTER_MAPPING` + Docker image güncel mi?
- "Modül import edilmiyor" → `python -c "from X import Y"`

%30-70 phantom çıkıyor. 30 saniye doğrulama, saatlerce yanlış fix'i önler.

## Detaylı Rehber

- `.claude/skills/debug-bug/SKILL.md`
- `.claude/rules/debugging-first.md`
- `.claude/rules/systematic-debugging.md`
- `.cursor/skills/tdd-loop/SKILL.md` — iterasyon detayı
