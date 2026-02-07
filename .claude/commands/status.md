---
allowed-tools: Bash, Read, Glob
description: Sistem ve servis sağlık kontrolü
---

## Task
KIRO2 sisteminin sağlık durumunu kontrol et.

## Kontroller

### 1. Backend Servisleri
```bash
# FastAPI health check
curl -s http://localhost:8000/health || echo "Backend DOWN"

# Redis bağlantısı
redis-cli ping || echo "Redis DOWN"

# PostgreSQL bağlantısı (dev'de SQLite)
cd backend && python -c "from app.core.database import engine; print('DB OK')" || echo "DB DOWN"
```

### 2. Frontend
```bash
# Next.js dev server
curl -s http://localhost:3000 > /dev/null && echo "Frontend OK" || echo "Frontend DOWN"
```

### 3. Git Durumu
```bash
git status --short
git log -1 --oneline
```

### 4. Test Durumu
```bash
# Son test sonuçları
cd backend && pytest --collect-only -q 2>/dev/null | tail -5
```

### 5. Disk/Memory
```bash
# Windows
wmic logicaldisk get size,freespace,caption 2>/dev/null || df -h 2>/dev/null
```

## Çıktı Formatı

```
╔════════════════════════════════════╗
║        KIRO2 DURUM RAPORU          ║
╠════════════════════════════════════╣
║ Backend API    : ✅ OK / ❌ DOWN   ║
║ Frontend       : ✅ OK / ❌ DOWN   ║
║ PostgreSQL/SQLite: ✅ OK / ❌ DOWN ║
║ Redis          : ✅ OK / ❌ DOWN   ║
║ Git Branch     : [branch-name]     ║
║ Son Commit     : [commit-msg]      ║
╚════════════════════════════════════╝
```
