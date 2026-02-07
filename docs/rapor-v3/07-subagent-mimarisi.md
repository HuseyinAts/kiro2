# BÖLÜM 7: Subagent Mimarisi

## 7.1 Sid Bidasaria'nın Tasarım Prensipleri

### Sid Bidasaria Hakkında

**Pozisyon:** Anthropic'te Founding Engineer, Claude Code ekibi

**Katkı:** Boris Cherny'nin ardından projeye katılan ikinci mühendis. Subagent sisteminin baş mimarı.

### MLOps Community Röportajından

**İngilizce:**
> "The way we implement it in Claude Code is subagent as tool - agent as tool. Each subagent gets its own isolated 200K context window. With 10 parallel subagents, that's theoretically 2 million tokens of potential capacity."

**Türkçe:**
> "Claude Code'da implementasyon şekli, araç olarak subagent - araç olarak ajan şeklinde. Her subagent kendi izole 200K context window'unu alıyor. 10 paralel subagent ile, teorik olarak 2 milyon token potansiyel kapasite var."

### Temel Tasarım Kararları

| Karar | Gerekçe |
|-------|---------|
| İzole context | Subagent hataları parent'ı etkilemesin |
| Tek seviye depth | Sonsuz iç içe geçme önlenir |
| Dosya tabanlı koordinasyon | Basitlik, debug kolaylığı |
| Özet döndürme | Parent context temiz kalır |
| Maksimum 10 paralel | Kaynak yönetimi, maliyet kontrolü |

---

## 7.2 Parent-Child Mimarisi

### Mimari Diyagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PARENT CLAUDE                             │
│                    (Ana 200K Context)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│   │   Task 1    │  │   Task 2    │  │   Task 3    │   ...      │
│   │  (Spawn)    │  │  (Spawn)    │  │  (Spawn)    │            │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│          │                │                │                     │
└──────────┼────────────────┼────────────────┼─────────────────────┘
           │                │                │
           ▼                ▼                ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   SUBAGENT 1     │ │   SUBAGENT 2     │ │   SUBAGENT 3     │
│  (200K Context)  │ │  (200K Context)  │ │  (200K Context)  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ • Own tools      │ │ • Own tools      │ │ • Own tools      │
│ • Own memory     │ │ • Own memory     │ │ • Own memory     │
│ • Own CLAUDE.md  │ │ • Own CLAUDE.md  │ │ • Own CLAUDE.md  │
│ • Isolated       │ │ • Isolated       │ │ • Isolated       │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌───────────┐        ┌───────────┐        ┌───────────┐
   │  Summary  │        │  Summary  │        │  Summary  │
   │  Result   │        │  Result   │        │  Result   │
   └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  PARENT CLAUDE  │
                    │  (Aggregation)  │
                    └─────────────────┘
```

### Bilgi Akışı

**Parent → Child (Görev aktarımı):**
```python
# Parent'ın gönderdiği
{
    "task": "Review authentication module for security issues",
    "context": {
        "files": ["src/auth/*.py"],
        "focus": "SQL injection, XSS, CSRF",
        "depth": "thorough"
    },
    "output_format": "structured_report"
}
```

**Child → Parent (Sonuç dönüşü):**
```python
# Subagent'ın döndürdüğü (özetlenmiş)
{
    "status": "completed",
    "summary": "Found 3 security issues in auth module",
    "findings": [
        {
            "severity": "high",
            "file": "src/auth/login.py",
            "line": 45,
            "issue": "SQL injection vulnerability",
            "fix": "Use parameterized queries"
        },
        # ... 2 more
    ],
    "files_reviewed": 5,
    "time_taken": "2m 34s"
}
```

**Önemli:** Verbose çıktı (tam dosya içerikleri, debug logları) child'da kalır, parent'a taşınmaz.

---

## 7.3 Kritik Mimari Kısıtlamalar

### Kısıtlama 1: Subagent Depth = 1

**Kural:** Subagent'lar başka subagent oluşturamaz.

**Gerekçe:**
- Sonsuz iç içe geçme önlenir
- Kaynak kullanımı kontrol altında
- Debug ve trace kolaylığı
- Maliyet tahmin edilebilirliği

**Hata durumu:**
```
Subagent trying to spawn another subagent...
ERROR: Subagent depth limit reached (max: 1)
Task will be executed in current context instead.
```

### Kısıtlama 2: Inter-Agent Communication Yok

**Kural:** Subagent'lar birbirleriyle doğrudan iletişim kuramaz.

**Sid Bidasaria:**
> "We decided not to allow agents to talk to each other. Coordination happens through files."

**Dosya tabanlı koordinasyon:**
```
Subagent A                    Subagent B
    │                              │
    │ write output/step1.json      │
    │─────────────────────►       │
    │                              │
    │                    read output/step1.json
    │                    ◄─────────────────────
    │                              │
    │                    write output/step2.json
    │                    ─────────────────────►
    │                              │
    ▼                              ▼
```

### Kısıtlama 3: Maksimum 10 Paralel

**Kural:** Aynı anda maksimum 10 subagent çalışabilir.

**Gerekçe:**
- API rate limit yönetimi
- Maliyet kontrolü
- Sistem kararlılığı

**Batch işleme (10+ görev için):**
```
Batch 1: Subagent 1-10 (paralel)
         ↓ tamamlandı
Batch 2: Subagent 11-20 (paralel)
         ↓ tamamlandı
Batch 3: ...
```

---

## 7.4 Task Tool vs Custom Subagent

### Task Tool (Geçici, Ad-hoc)

**Kullanım:** Tek seferlik, tanımsız görevler

**Syntax:**
```
"Task: Review this file for security issues"
"Task security-check: Audit the authentication module"
```

**Özellikler:**
- Tanım dosyası gerektirmez
- Prompt ile görev tanımlanır
- Default model ve araçlar
- Hızlı, esnek

### Custom Subagent (Kalıcı, Tanımlı)

**Kullanım:** Tekrarlayan, özelleştirilmiş görevler

**Tanım:** `.claude/agents/[name].md` dosyası

**Özellikler:**
- Özel model seçimi
- Tool whitelist/blacklist
- Permission mode
- Timeout ve maxTurns
- Skills inheritance

### Seçim Kriterleri

| Kriter | Task Tool | Custom Subagent |
|--------|-----------|-----------------|
| Kullanım sıklığı | Tek sefer | Tekrarlayan |
| Özelleştirme | Minimal | Detaylı |
| Model seçimi | Default | Özelleştirilebilir |
| Tool kısıtlaması | Yok | Var |
| Setup süresi | 0 | 5-10 dakika |
| Reusability | Yok | Yüksek |

### Karar Ağacı

```
Görev tekrarlayacak mı?
├── Hayır → Task Tool
└── Evet
    └── Özel tool kısıtlaması lazım mı?
        ├── Hayır → Task Tool (ad-hoc pattern)
        └── Evet → Custom Subagent
```

---

## 7.5 Paralel Çalıştırma Stratejileri

### Strateji 1: Fan-Out / Fan-In

```
                    ┌─────────┐
                    │ Parent  │
                    └────┬────┘
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ Agent 1 │   │ Agent 2 │   │ Agent 3 │
      └────┬────┘   └────┬────┘   └────┬────┘
           │             │             │
           └─────────────┼─────────────┘
                         ▼
                    ┌─────────┐
                    │ Parent  │
                    │ (Merge) │
                    └─────────┘
```

**Kullanım:** Bağımsız görevleri paralel işle, sonuçları birleştir.

**Örnek:**
```
"Fan out: Review these 5 modules for security issues
- Task security-1: Review auth/
- Task security-2: Review api/
- Task security-3: Review db/
- Task security-4: Review utils/
- Task security-5: Review config/

Then merge all findings into a single report."
```

### Strateji 2: Pipeline

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Agent 1 │──▶│ Agent 2 │──▶│ Agent 3 │──▶│ Agent 4 │
│ (Parse) │   │(Analyze)│   │ (Fix)   │   │ (Test)  │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
```

**Kullanım:** Sıralı, birbirine bağımlı görevler.

**Örnek:**
```
"Pipeline:
1. Task parser: Extract all function signatures from module
2. Task analyzer: Identify functions missing type hints
3. Task fixer: Add type hints to identified functions
4. Task tester: Run mypy to verify fixes"
```

### Strateji 3: Map-Reduce

```
           ┌─────────────────────────┐
           │       Input Data        │
           │   [item1, item2, ...]   │
           └───────────┬─────────────┘
                       │ split
           ┌───────────┼───────────┐
           ▼           ▼           ▼
      ┌─────────┐ ┌─────────┐ ┌─────────┐
      │  Map 1  │ │  Map 2  │ │  Map 3  │
      └────┬────┘ └────┬────┘ └────┬────┘
           │           │           │
           └───────────┼───────────┘
                       ▼
              ┌─────────────┐
              │   Reduce    │
              └─────────────┘
```

**Kullanım:** Büyük veri setlerini parçalara ayır, işle, birleştir.

**KIRO2 örneği:**
```
"Map-Reduce soru analizi:

MAP: 10 subagent, her biri 100 soruyu analiz etsin
- Agent 1: questions[0:100]
- Agent 2: questions[100:200]
- ...

REDUCE: Tüm analizleri birleştir
- Zorluk dağılımı
- Konu coverage
- Kalite metrikleri"
```

---

## 7.6 Subagent Error Handling

### Hata Türleri

| Hata | Açıklama | Varsayılan Davranış |
|------|----------|---------------------|
| Timeout | maxTurns veya süre aşımı | Task cancelled |
| Tool Error | Araç çalıştırma hatası | Retry veya fail |
| Model Error | API hatası | Retry with backoff |
| Logic Error | Yanlış sonuç | Parent'a bildir |

### Parent'ta Hata Yönetimi

```python
# Pseudocode
result = await spawn_subagent("security-reviewer", task)

if result.status == "error":
    if result.error_type == "timeout":
        # Daha küçük görev ver
        smaller_task = split_task(task)
        results = await parallel([
            spawn_subagent("security-reviewer", t) 
            for t in smaller_task
        ])
    elif result.error_type == "tool_error":
        # Farklı araçlarla dene
        result = await spawn_subagent("security-reviewer-fallback", task)
    else:
        # Human intervention gerekli
        notify_human(result.error)
```

### Retry Stratejisi

```yaml
# .claude/agents/resilient-reviewer.md
---
name: resilient-reviewer
retry:
  maxAttempts: 3
  backoffMs: 1000
  backoffMultiplier: 2
onError:
  timeout: split_and_retry
  toolError: fallback_tools
  other: escalate_to_parent
---
```

---

## 7.7 Dosya Tabanlı Koordinasyon

### Koordinasyon Dosyası Yapısı

**Dizin:** `.claude/coordination/`

```
.claude/coordination/
├── tasks/
│   ├── task-001.json      # Pending task
│   ├── task-002.json      # Pending task
│   └── ...
├── results/
│   ├── task-001-result.json
│   └── ...
├── locks/
│   ├── file-src-main.lock
│   └── ...
└── state.json             # Global state
```

### Task Dosyası Formatı

```json
// .claude/coordination/tasks/task-001.json
{
  "id": "task-001",
  "type": "security-review",
  "status": "pending",
  "created": "2026-02-01T10:30:00Z",
  "assigned_to": null,
  "input": {
    "files": ["src/auth/login.py"],
    "scope": "sql_injection"
  },
  "dependencies": [],
  "priority": 1
}
```

### Result Dosyası Formatı

```json
// .claude/coordination/results/task-001-result.json
{
  "task_id": "task-001",
  "status": "completed",
  "completed_at": "2026-02-01T10:32:15Z",
  "agent": "security-reviewer",
  "output": {
    "findings": [...],
    "summary": "...",
    "recommendations": [...]
  },
  "metrics": {
    "duration_ms": 135000,
    "tokens_used": 15234
  }
}
```

### Lock Mekanizması

**File locking (race condition önleme):**

```python
# orchestrator/coordination/file_lock.py

import fcntl
import os
from pathlib import Path

class FileLock:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lock_path = Path(f".claude/coordination/locks/{filepath.replace('/', '-')}.lock")
        self.lock_file = None
    
    def acquire(self) -> bool:
        """Lock dosyasını al."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = open(self.lock_path, 'w')
        try:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(f"{os.getpid()}\n")
            self.lock_file.flush()
            return True
        except BlockingIOError:
            self.lock_file.close()
            return False
    
    def release(self):
        """Lock dosyasını bırak."""
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_path.unlink(missing_ok=True)
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for {self.filepath}")
        return self
    
    def __exit__(self, *args):
        self.release()
```

**Kullanım:**
```python
with FileLock("src/auth/login.py") as lock:
    # Bu dosyayı güvenle düzenle
    edit_file("src/auth/login.py", changes)
```

---

## 7.8 KIRO2 Subagent Örnekleri

### Matematik Soru Üretici

```yaml
# .claude/agents/matematik-generator.md
---
name: matematik-generator
description: "YKS matematik soruları üretir. Use PROACTIVELY for TYT/AYT matematik içeriği."
model: opus
tools:
  - Read
  - Write
  - Bash
  - Glob
allowedTools:
  - Read
  - Write
disallowedTools:
  - WebSearch  # Harici kaynak kullanmasın
permissionMode: acceptEdits
maxTurns: 50
timeout: 600
---

# Matematik Soru Üretici Agent

## Rol
TYT ve AYT matematik müfredatına uygun, pedagojik açıdan kaliteli sorular üret.

## Müfredat Kapsamı

### TYT Matematik
- Temel Kavramlar
- Sayı Basamakları
- Bölme-Bölünebilme
- EBOB-EKOK
- Rasyonel Sayılar
- Basit Eşitsizlikler
- Mutlak Değer
- Üslü Sayılar
- Köklü Sayılar
- Çarpanlara Ayırma
- Oran-Orantı
- Problemler (Yaş, İşçi, Havuz, vb.)
- Kümeler
- Fonksiyonlar (Temel)
- Permütasyon-Kombinasyon
- Olasılık
- İstatistik (Temel)

### AYT Matematik
- Fonksiyonlar (İleri)
- Polinomlar
- İkinci Dereceden Denklemler
- Trigonometri
- Logaritma
- Diziler
- Limit
- Türev
- İntegral

## Soru Formatı

```json
{
  "question_id": "MAT-TYT-001",
  "question_text": "...",
  "options": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "...",
    "E": "..."
  },
  "correct_answer": "C",
  "difficulty_level": 3,
  "topic_tags": ["limit", "süreklilik"],
  "subtopic": "limit",
  "exam_type": "AYT",
  "explanation": "...",
  "solution_steps": ["Adım 1: ...", "Adım 2: ..."],
  "estimated_time_seconds": 120,
  "bloom_level": 3
}
```

## Kurallar

### Zorunlu
- Her soru UTF-8 encoding ile Türkçe karakterleri desteklemeli
- Matematiksel ifadeler LaTeX formatında: $...$ veya $$...$$
- Zorluk seviyesi 1-5 arası (1=çok kolay, 5=çok zor)
- Çeldiriciler mantıklı ve yaygın hatalardan türetilmeli

### Yasak
- Kopya veya çok benzer soru üretme
- Cevabı soru metninde ima etme
- Çok uzun veya karmaşık soru metni (max 200 kelime)
```

### İçerik Doğrulayıcı

```yaml
# .claude/agents/content-validator.md
---
name: content-validator
description: "Üretilen içeriği pedagojik açıdan doğrular. MUST BE USED after any question generation."
model: sonnet
tools:
  - Read
  - Grep
permissionMode: plan
maxTurns: 30
timeout: 300
---

# İçerik Doğrulayıcı Agent

## Rol
Üretilen soruları pedagojik ve teknik açıdan doğrula.

## Kontrol Listesi

### 1. Format Kontrolü
- [ ] JSON schema'ya uygun mu?
- [ ] Tüm zorunlu alanlar var mı?
- [ ] UTF-8 encoding doğru mu?
- [ ] LaTeX syntax geçerli mi?

### 2. İçerik Kontrolü
- [ ] Soru metni anlaşılır mı?
- [ ] Matematiksel notation doğru mu?
- [ ] Türkçe dilbilgisi doğru mu?
- [ ] Seçenekler mantıklı mı?

### 3. Pedagojik Kontrol
- [ ] Zorluk seviyesi tutarlı mı?
- [ ] Müfredata uygun mu?
- [ ] Çeldirici kalitesi yeterli mi?
- [ ] Bloom taksonomisi uygun mu?

### 4. Duplicate Kontrolü
- [ ] Soru bankasında benzer soru var mı?
- [ ] Aynı sorunun farklı formatı mı?

## Çıktı Formatı

```json
{
  "validation_id": "VAL-001",
  "question_id": "MAT-TYT-001",
  "status": "PASS" | "FAIL" | "WARNING",
  "timestamp": "2026-02-01T10:30:00Z",
  "checks": {
    "format": {"status": "PASS", "details": null},
    "content": {"status": "PASS", "details": null},
    "pedagogy": {"status": "WARNING", "details": "Zorluk seviyesi düşürülebilir"},
    "duplicate": {"status": "PASS", "details": null}
  },
  "overall_score": 85,
  "recommendations": [
    "Zorluk seviyesini 3'ten 2'ye düşürün"
  ]
}
```

## Scoring

| Kontrol | Ağırlık | PASS | WARNING | FAIL |
|---------|---------|------|---------|------|
| Format | 25% | 25 | 15 | 0 |
| Content | 30% | 30 | 20 | 0 |
| Pedagogy | 30% | 30 | 20 | 0 |
| Duplicate | 15% | 15 | 10 | 0 |

**Geçme kriteri:** overall_score >= 70
```

---

## 7.9 Özet

### Checklist

- [ ] Subagent mimarisini anladım (izolasyon, depth=1)
- [ ] Task Tool vs Custom Subagent farkını biliyorum
- [ ] Paralel çalıştırma stratejilerini (fan-out, pipeline, map-reduce) seçebiliyorum
- [ ] Error handling stratejisi belirledim
- [ ] Dosya tabanlı koordinasyon implementasyonu planladım
- [ ] KIRO2 için özel subagent'lar tanımladım

### Quick Reference

| Komut/Kavram | Açıklama |
|--------------|----------|
| `Task: [prompt]` | Ad-hoc subagent |
| `.claude/agents/*.md` | Custom subagent tanımı |
| `maxTurns` | Maksimum iterasyon |
| `timeout` | Saniye cinsinden süre limiti |
| `permissionMode: plan` | Sadece okuma |
| `PROACTIVELY` | Otomatik delegasyon tetikleyici |

### Metrikler

| Metrik | İdeal |
|--------|-------|
| Subagent başarı oranı | > 95% |
| Ortalama subagent süresi | < 5 dakika |
| Context transfer overhead | < 5K token |
| Paralel efficiency | > 80% |

---

**Önceki Bölüm:** [06 - Context Yönetimi](./06-context-yonetimi.md)  
**Sonraki Bölüm:** [08 - Subagent Tanımlama Formatı](./08-subagent-tanimlama-formati.md)
