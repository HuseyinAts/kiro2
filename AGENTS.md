# AGENTS.md — KIRO2 Agent Talimatları

Bu dosya background agent'lar ve cloud agent'lar için proje kurulumunu
tanımlar. Cursor cloud agent özelliği açıldığında otomatik okunur.

## Proje Özeti

KIRO2 — YKS/TYT/AYT hazırlık platformu.
Stack: FastAPI + PostgreSQL (port 5434) + Redis + React/TypeScript + LiteLLM
Algoritmalar: IRT 3PL, FSRS-6, BKT
NLP: Qwen3-8B fine-tuned, Turkish tokenizer

## Cloud Agent Kurulum Komutları

VM başlangıcında sırasıyla çalıştırılır:

```bash
# 1. Python ortamı
python -m venv .venv
source .venv/bin/activate  # Linux/cloud
pip install -r requirements.txt
pip install -r requirements_hybrid.txt  # ek NLP bağımlılıkları

# 2. Frontend
cd frontend && npm ci && cd ..

# 3. Servisler (Docker)
docker compose up -d postgres redis

# 4. DB hazırla
cd backend && alembic upgrade head && cd ..

# 5. Smoke test
pg_isready -p 5434 || exit 1
redis-cli ping || exit 1
```

## Test Komutları

```bash
# Backend
pytest tests/ -x --tb=short --cov=backend

# Frontend
cd frontend && npm test -- --run

# Migration round-trip
cd backend && alembic upgrade head && alembic downgrade -1 && alembic upgrade head
```

## Cursor 3.x Cloud ↔ Local Handoff (Nisan 2026)

Cursor 3.0 ile cloud agent handoff pattern'ı:

### Local → Cloud (laptop kapatılacak)

Agents Window'da aktif session:
1. Sağ tık session → "Move to Cloud"
2. Cloud'da devam eder, laptop kapatılabilir
3. Mobile app'ten progress izle
4. Tamamlanınca notification

### Cloud → Local (edit + test etmek için)

Cloud session'ı görüp:
1. Sağ tık → "Move to Local"
2. Composer 2 ile hızlı iterate
3. Sonra tekrar Cloud'a pushlayabilirsin

**KIRO2 için uygun task'lar:**
- ✅ OCR pipeline (uzun sürer, laptop'a bağımlılık yok)
- ✅ Dataset processing (120K question batch)
- ✅ Golden dataset regression test
- ✅ Alembic migration round-trip test
- ❌ Production DB migration (cloud'dan prod access YASAK)
- ❌ Secret içeren iş (cloud sandbox'ta env kısıtlı)

## Agent'ın Uyması Gereken Kurallar

### İzinler

- `.env`, `.env.*` dosyalarına DOKUNMAZ
- `secrets/`, `*.pem`, `*.key` dosyalarına DOKUNMAZ
- Production DB'ye (`.env.production` credentials) BAĞLANMAZ
- `git push --force` YAPMAZ
- `main` / `master` branch'ine doğrudan push YAPMAZ

### Yetki Sınırları

Agent yalnızca:
- Feature branch'lerde çalışır (`feature/*`, `fix/*`)
- PR açar, doğrudan merge YAPMAZ
- CHANGELOG.md güncellenir
- Conventional commit formatı: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`

### Kod Kalite Zorunlulukları

Her PR için:
- `pytest -x` tam pass
- Test coverage %80 altına düşmez
- `ruff check` 0 hata
- `mypy backend/` 0 hata (mevcut baseline üstüne çıkmaz)
- Yeni endpoint'te AuthGuard + IDOR check var
- Yeni migration reversible

### Cursor 3.x Özel Kurallar

- **3+ dosya değiştiren task** → Plan Mode zorunlu, `.cursor/plans/` kaydet
- **Belirsiz karar** → `/best-of-n` ile paralel model karşılaştır
- **Risky experiment** → `/worktree` ile izole et
- **UI iteration** → Integrated Browser + Design Mode
- **Bug fix** → `/debug-mode` pattern (INFRA-FIRST)

## Proje Özel Notları

### Dual Table Trap (kritik)

`Question` için iki model var. Doğru olan:
```python
from models.question_bank import QuestionBankItem as Question
# is_active == True filtresi ZORUNLU
```

### Docker İmaj Staleness

Container'da 404/ImportError → önce image rebuild:
```bash
docker compose build --no-cache backend && docker compose up -d
```

### Host-Docker Ağ

Container içinden host servislerine `host.docker.internal` ile ulaş
(localhost container'ı kendisi).

### Cloud Agent DB Erişimi

Cloud sandbox'tan:
- ✅ Docker PostgreSQL (container içi) — OK
- ❌ Host PostgreSQL (port 5434 localhost) — VPN/SSH tunnel gerekir
- ❌ Production DB — YASAK

## Agent Hata Davranışı

- 2+ iterasyonda aynı hatayla karşılaşırsa: dur, rapor ver, insan onayı iste
- Plan-before-execute: 3+ dosya değişikliğinde önce plan sun
- 3 iterasyonda çözülemeyen bug → `/debug-mode` devreye al (hipotez + instrument)
- `.claude/rules/plan-before-execute.md` referans

## Bildirim Kanalları

Cursor cloud agent tamamlandığında:
- **Slack integration**: @cursor mention ile task başlat, DM ile sonuç
- **GitHub**: PR otomatik açılır, reviewer atanır
- **Mobile**: Cursor mobile app notification
- **Web**: cursor.com/agents dashboard

## Detaylı Referanslar

- `CLAUDE.md` — session management, pre-flight checks, test requirements
- `.cursor/README.md` — Cursor yapılandırma özeti
- `.cursor/MIGRATION-NIGHTLY.md` — GUI kurulum adımları
- `.cursor/rules/10-backend.mdc` — backend pattern'ları
- `.cursor/rules/30-migrations.mdc` — migration güvenliği
- `.cursor/rules/40-algorithms.mdc` — IRT/FSRS/BKT koruması
- `.claude/rules/security.md` — detaylı güvenlik kuralları
- `.claude/rules/testing.md` — 30 öğrenilen ders (Session 6-148)
- `REPO_MAP.md` — dizin yapısı
