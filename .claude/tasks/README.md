# KIRO2 Tasks Sistemi

> Claude Code 2026 Tasks API Entegrasyonu
> Dependency-aware task management with wave-based parallelism

---

## Genel Bakış

Tasks sistemi, TodoWrite'ın yerini alan yeni nesil görev yönetim sistemidir.
Temel farklar:
- **Kalıcı depolama**: `~/.claude/tasks/` dizininde JSON dosyaları
- **Dependency tracking**: `blockedBy` ile bağımlılık yönetimi
- **Multi-session**: Birden fazla terminal aynı task listesini paylaşır
- **Wave parallelism**: Bağımsız görevler otomatik paralel çalışır

---

## Dizin Yapısı

```
~/.claude/tasks/
├── kiro2-master/           # Ana proje task listesi
│   ├── task-001.json
│   ├── task-002.json
│   └── ...
└── README.md
```

---

## Task Schema

```json
{
  "id": "task-001",
  "title": "Görev başlığı",
  "description": "Detaylı açıklama",
  "status": "pending|in_progress|completed|blocked|failed|cancelled",
  "blockedBy": ["task-000"],
  "blocks": ["task-002", "task-003"],
  "owner": "session-abc123",
  "priority": "high|medium|low",
  "tags": ["backend", "api", "sprint-1"],
  "createdAt": "2026-01-26T10:00:00Z",
  "startedAt": null,
  "completedAt": null,
  "metadata": {
    "estimatedHours": 2,
    "actualHours": null,
    "commits": [],
    "notes": ""
  }
}
```

---

## Status Lifecycle

```
PENDING → IN_PROGRESS → COMPLETED
    ↓         ↓
  BLOCKED   FAILED
              ↓
          CANCELLED
```

### Status Kuralları
- `pending`: Başlamamış, dependency'ler tamamlanmış olabilir veya olmayabilir
- `blocked`: `blockedBy` listesindeki task'lar henüz tamamlanmamış
- `in_progress`: Aktif çalışılıyor, `owner` atanmış
- `completed`: Başarıyla tamamlandı
- `failed`: Başarısız oldu, müdahale gerekiyor
- `cancelled`: İptal edildi

---

## Environment Variable

```bash
# Multi-session için ZORUNLU
export CLAUDE_CODE_TASK_LIST_ID="kiro2-master"

# Örnek kullanım
CLAUDE_CODE_TASK_LIST_ID=kiro2-master claude "API endpoint'i tasarla"
```

---

## Wave-Based Parallelism

Bağımsız task'lar aynı wave'de paralel çalışır:

```
Wave 1 (Paralel):
├── task-001: Database Schema Design    (blockedBy: [])
└── task-002: API Documentation         (blockedBy: [])

Wave 2 (Wave 1 tamamlanınca):
├── task-003: API Implementation        (blockedBy: [task-001])
└── task-004: Frontend Mockups          (blockedBy: [task-002])

Wave 3 (Wave 2 tamamlanınca):
└── task-005: Integration Tests         (blockedBy: [task-003, task-004])
```

---

## Kullanım

### Task Oluşturma
```bash
python .claude/scripts/task-manager.py create \
  --title "API endpoint tasarla" \
  --priority high \
  --tags "api,backend"
```

### Task Listeleme
```bash
python .claude/scripts/task-manager.py list --status pending
```

### Task Güncelleme
```bash
python .claude/scripts/task-manager.py update task-001 --status in_progress
```

### Wave Görüntüleme
```bash
python .claude/scripts/task-manager.py waves
```

---

## Broadcasting

Bir session task güncellediğinde, diğer session'lar bilgilendirilir:

```
Terminal 1: Task #3 completed ✓
     │
     ├──> Terminal 2: [Notification] Task #3 completed
     └──> Terminal 3: [Notification] Task #4, #5 now unblocked
```

---

## Entegrasyon

### Claude Code ile
Claude Code otomatik olarak bu sistemi kullanır:
- Task oluşturur ve günceller
- Wave'lere göre paralel çalışır
- Dependency'leri kontrol eder

### Sub-agent'lar ile
Sub-agent'lar da aynı task listesini görür ve güncelleyebilir.

---

## Örnek Task Dosyası

`kiro2-master/task-001.json`:
```json
{
  "id": "task-001",
  "title": "PostgreSQL schema tasarımı",
  "description": "users, questions, exams tablolarını oluştur",
  "status": "completed",
  "blockedBy": [],
  "blocks": ["task-002", "task-003"],
  "owner": "session-abc123",
  "priority": "high",
  "tags": ["database", "backend", "sprint-1"],
  "createdAt": "2026-01-26T10:00:00Z",
  "startedAt": "2026-01-26T10:05:00Z",
  "completedAt": "2026-01-26T11:30:00Z",
  "metadata": {
    "estimatedHours": 2,
    "actualHours": 1.5,
    "commits": ["a1b2c3d"],
    "notes": "IRT parametreleri için ek kolonlar eklendi"
  }
}
```

---

## Best Practices

1. **Dependency Planning**: Task oluşturmadan önce dependency graph çiz
2. **Granular Tasks**: Büyük görevleri küçük parçalara böl
3. **Clear Titles**: Başlıklar açık ve action-oriented olsun
4. **Tag Consistency**: Tutarlı tag'ler kullan (sprint-1, backend, api, vb.)
5. **Regular Updates**: Status'u gerçek zamanlı güncelle

---

## Troubleshooting

### Task stuck in BLOCKED
- `blockedBy` listesindeki task'ların durumunu kontrol et
- Circular dependency var mı kontrol et

### Multiple owners
- Aynı task'a birden fazla session sahip olamaz
- Önce mevcut owner'ı release et

### Sync issues
- `CLAUDE_CODE_TASK_LIST_ID` doğru ayarlanmış mı kontrol et
- File lock sorunları için retry mekanizması var

---

*Claude Code 2026 Tasks API - KIRO2 Entegrasyonu*
