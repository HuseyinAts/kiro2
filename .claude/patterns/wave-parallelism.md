# Wave-Based Parallelism Pattern

> "7-10 sub-agent ayni anda calisabiliyor. Bagimsiz task'lar paralel spawn edilir."

## Konsept

```
Wave 1: [Bagimsiz task'lar - paralel calis]
   Task A ─┬
   Task B ─┼─> Wave 2 (bagimlı)
   Task C ─┘

Wave 2: [Wave 1 tamamlaninca basla]
   Task D ─┬
   Task E ─┘─> Wave 3 (bagimlı)

Wave 3: [Wave 2 tamamlaninca basla]
   Task F
```

## KIRO2 Development Waves

### CI/CD Pipeline
```yaml
Wave 1 (Parallel - bagimsiz):
  - ruff check backend/           # Python lint
  - npm run lint                  # TypeScript lint
  - bandit -r backend/            # Security scan

Wave 2 (Parallel - Wave 1'e bagli):
  - mypy backend/                 # Type check
  - npx tsc --noEmit              # TS type check
  - pytest backend/tests/fast/    # Fast tests

Wave 3 (Parallel - Wave 2'ye bagli):
  - pytest backend/tests/integration/  # Integration tests
  - npm test                           # Frontend tests

Wave 4 (Sequential - Wave 3'e bagli):
  - docker-compose build          # Build images
  - docker-compose push           # Push to registry
```

### Task Definition Formati
```json
{
  "tasks": [
    {
      "id": "lint-backend",
      "wave": 1,
      "command": "ruff check backend/",
      "blockedBy": []
    },
    {
      "id": "test-backend",
      "wave": 2,
      "command": "pytest backend/tests/",
      "blockedBy": ["lint-backend"]
    }
  ]
}
```

## Claude Code Kullanimi

```
User: "CI pipeline'i calistir"

Claude:
Wave 1 basliyor (3 task paralel):
@bash: ruff check backend/ &
@bash: npm run lint &
@bash: bandit -r backend/ &

[Wave 1 tamamlandi]

Wave 2 basliyor (2 task paralel):
@bash: pytest -m fast &
@bash: npx tsc --noEmit &

[Wave 2 tamamlandi]

Wave 3 basliyor:
@bash: docker-compose build
```

## Dependency Graph Ornegi

```
         ┌─────────────┐
         │   START     │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐   ┌───────┐   ┌───────┐
│ Lint  │   │ Lint  │   │ Scan  │   Wave 1
│Python │   │  TS   │   │ Sec   │
└───┬───┘   └───┬───┘   └───┬───┘
    │           │           │
    └─────┬─────┴─────┬─────┘
          │           │
    ┌─────▼───┐   ┌───▼─────┐
    │  Type   │   │  Fast   │       Wave 2
    │  Check  │   │  Tests  │
    └────┬────┘   └────┬────┘
         │             │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   Build     │            Wave 3
         │   Docker    │
         └─────────────┘
```

## Performans Kazanimi

| Yaklasim | Sure | Kazanim |
|----------|------|---------|
| Sequential | 10 dakika | - |
| Wave-based | 4 dakika | %60 |
| Max parallel | 3 dakika | %70 |

## Uygulama Notlari

1. **Bagimsizlik kontrol et**: Task A, Task B'nin ciktisina ihtiyac duyuyor mu?
2. **Kaynak limitleri**: Max 7-10 paralel agent
3. **Hata yonetimi**: Bir task fail olursa wave durur
4. **Context izolasyonu**: Her agent kendi 200K token window'una sahip
