# Debug Mode Başlat

**Cursor native özelliği**: Agent dropdown'ından "Debug Mode" seç. Bu komut
workflow hatırlatıcısı olarak çalışır.

## Ne Zaman Kullanılmalı

Debug Mode standart agent interaksiyonundan farklıdır. Kullan:

- **Reproduce edebildiğin ama sebebini bulamadığın bug'lar** — özellikle
  race condition, timing issue
- **Performance problemleri** — memory leak, slow query, blocking I/O şüphesi
- **Regression** — önceden çalışıyordu, artık çalışmıyor
- **Sessiz başarısızlık** — 200 dönüyor ama data yanlış/boş

Standart agent yeter:
- Basit hata mesajı ile test failure
- Stack trace zaten root cause'u gösteriyor
- `.claude/rules/debugging-first.md`'deki bilinen pattern

## Debug Mode'un Çalışma Şekli

Standart agent'tan farkı:

1. **Hipotez üretir** — ne yanlış olabilir, birden fazla olasılık
2. **Kodu logging ile instrument eder** — geçici print/log statement'lar ekler
3. **Reproduce etmeni ister** — sen bug'ı tetikle
4. **Runtime data topla** — gerçek davranışı ölç
5. **Evidence-based fix** — tahmin değil, veriye dayalı düzeltme

## KIRO2 Debug Workflow

### Adım 1 — INFRA-FIRST (30 saniye)

Debug Mode'a dalmadan ÖNCE:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
pg_isready -p 5434
redis-cli ping
curl -s http://localhost:8000/api/v1/health
```

Herhangi biri fail → altyapı önce, Debug Mode'a gerek yok.

### Adım 2 — Reproduce Komutu Ver

Agent'a nasıl tetikleneceğini **spesifik** söyle:

```
Debug Mode:
Bug: /api/v1/exams/start endpoint'i 200 dönüyor ama questions listesi boş.

Reproduce:
1. Browser'da http://localhost:3001'e git
2. Login: test@kiro2.local / Test1234!
3. Dashboard → "TYT Matematik" seç → Start Exam
4. Request: POST /api/v1/exams/start  body: {"exam_type": "TYT", "subject": "matematik"}
5. Response body: {"questions": [], "exam_id": "..."}  ← boş!

Beklenen: 40 soruluk question array
```

### Adım 3 — Instrument'a İzin Ver

Debug Mode geçici logging ekleyecek:
- `logger.debug(f"Query params: {params}")`
- `logger.debug(f"DB result: len={len(result)}, is_active_count=...")`
- `logger.debug(f"Filter chain: {query.statement}")`

**Commit etme** bu logging'leri — fix sonrası revert et.

### Adım 4 — Root Cause Tablosunu Gör

Debug Mode mutlaka şöyle bir tablo üretmeli:

| Hipotez | Veri | Sonuç |
|---|---|---|
| Dual Table: `questions` query'leniyor | DB log: `SELECT FROM questions WHERE ...` 0 row | ✅ DOĞRULANDI |
| is_active filtresi eksik | Query: `WHERE exam_type='TYT'` (is_active yok) | ✅ İKİNCİL NEDEN |
| Enum case uyumsuzluğu | Query param: "tyt", DB column: "TYT" | ✅ ÜÇÜNCÜL NEDEN |

### Adım 5 — Fix + Regression Check

- Minimal fix uygula
- Instrumentation revert et
- Pytest: `cd backend && pytest tests/ -x --tb=short -q`
- Manual reproduce: 200 + dolu questions array

## Kullanım Örnekleri

```
# Performance
Debug Mode: /api/v1/questions endpoint'i p95 1200ms. Hedef <500ms.
Reproduce: ab -n 100 -c 10 http://localhost:8000/api/v1/questions

# Race condition
Debug Mode: Concurrent exam submit'te 2 users aynı exam_id'yi paylaşıyor.
Reproduce: [script]

# Regression
Debug Mode: Commit a1b2c3 öncesi auth/login çalışıyordu, sonra 401.
Reproduce: curl -X POST .../auth/login -d '{...}'
```

## Anti-pattern'lar

- "Debug Mode, neden çalışmıyor?" — spesifik reproduce adımı YOK → başarısız olur
- Debug Mode'u tek satır fix için kullanma — overkill
- Instrumentation'ı commit etme — production'da çöp log olur

## Referans

- `.cursor/skills/debug-bug/SKILL.md` — INFRA-FIRST protokolü
- `.claude/rules/debugging-first.md` — root cause analiz template'i
- `.claude/rules/systematic-debugging.md` — phantom filter (%30-70 rapor yanlış)
