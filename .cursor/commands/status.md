# Sistem Durumu

KIRO2 servislerinin ve proje durumunun tam sağlık raporu. Paralel kontrol et,
tek tablo formatında sun.

## Kontroller

### 1. Servisler

```bash
# Backend (FastAPI)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health

# Frontend (Vite dev server)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000

# Docker container'lar
docker ps --format "{{.Names}}: {{.Status}}" | head -10
```

### 2. Veritabanları

```bash
# PostgreSQL (port 5434)
pg_isready -p 5434 && echo "PG UP" || echo "PG DOWN"

# Redis (port 6379)
redis-cli ping

# Elasticsearch (opsiyonel, dev'de)
curl -s http://localhost:9200/_cluster/health | jq -r '.status'
```

### 3. Git

```bash
git branch --show-current
git log -1 --oneline
git status --short | head -15
git diff --stat HEAD | tail -3
```

### 4. Production Data

```bash
# Production soru bankası
wc -l < d-dataset/eslesmis_sorucevap.jsonl 2>/dev/null || echo "N/A"

# question_bank tablosu (Dual Table Trap referansı)
psql -p 5434 -d kiro2 -U postgres -t -c \
  "SELECT COUNT(*) FROM question_bank WHERE is_active = true;" 2>/dev/null || echo "N/A"
```

### 5. Test Sağlığı

```bash
# Collection test (çalıştırmadan sayar)
cd backend && python -m pytest tests/unit/ --co -q 2>&1 | tail -1

# Son çalıştırma sonucu (pytest cache'den)
cat backend/.pytest_cache/v/cache/lastfailed 2>/dev/null | wc -l
```

### 6. Commit Bekleyenler

```bash
# Staged değişiklikler
git diff --cached --stat | tail -3

# Uncommitted Python dosyaları
git status --short -- "*.py" | wc -l
```

## Çıktı Formatı

Markdown tablo, **kısa ve öz**:

```markdown
# KIRO2 Status — [TARIH HH:MM]

| Alan | Durum |
|---|---|
| Backend | UP/DOWN (HTTP code) |
| Frontend | UP/DOWN (HTTP code) |
| PostgreSQL (5434) | UP/DOWN |
| Redis | UP/DOWN |
| Docker | N container çalışıyor |
| Branch | [adı] |
| Son Commit | `hash` [mesaj] |
| Uncommitted | N dosya (X .py, Y .ts) |
| Production Sorular | N soru |
| question_bank aktif | N kayıt |
| Unit Tests | N collected |

## Kritik Uyarılar
- [varsa liste, yoksa "yok"]
```

**KISA TUT** — açıklama yapma, sadece veriyi göster. Tablo yeterli.
