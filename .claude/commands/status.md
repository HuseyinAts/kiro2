---
allowed-tools: Bash, Read, Glob, Grep
description: Sistem ve servis sağlık kontrolü
---

## Task
KIRO2 sisteminin tam durum raporunu oluştur. Tüm kontrolleri PARALEL çalıştır, sonucu tek tablo formatında sun.

## Kontroller (hepsini paralel çalıştır)

### 1. Servisler
```bash
# Backend
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "DOWN"

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "DOWN"

# Docker containers
docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null | head -10
```

### 2. Git
```bash
cd C:/Users/husey/kiro2
git branch --show-current
git log -1 --oneline
git status --short | head -15
git diff --stat HEAD 2>/dev/null | tail -3
```

### 3. Production Data
```bash
# Soru sayısı (production JSONL)
wc -l < C:/Users/husey/kiro2/d-dataset/eslesmis_sorucevap.jsonl 2>/dev/null || echo "N/A"
```

### 4. Test (sadece toplama, çalıştırma)
```bash
cd C:/Users/husey/kiro2/backend && python -m pytest tests/unit/ --co -q 2>&1 | tail -1
```

### 5. Commit Bekleyen Değişiklikler
```bash
cd C:/Users/husey/kiro2
git diff --cached --stat 2>/dev/null | tail -3
git status --short -- "*.py" | wc -l
```

## Çıktı Formatı

Markdown tablo, kısa ve öz:

| Alan | Durum |
|------|-------|
| Backend | UP/DOWN (HTTP code) |
| Frontend | UP/DOWN (HTTP code) |
| Docker | container listesi |
| Branch | branch adı |
| Son Commit | hash + mesaj |
| Production | X soru |
| Unit Tests | X collected |
| Uncommitted | X dosya |
| Kritik | varsa listele |

KISA TUT. Açıklama yapma, sadece veriyi göster.
