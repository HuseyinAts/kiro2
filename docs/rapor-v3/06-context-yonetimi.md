# BÖLÜM 6: Context Yönetimi

## 6.1 Context Window Nedir?

Context window, Claude'un bir anda "görebildiği" ve işleyebildiği maksimum metin miktarıdır. Bu, konuşma geçmişi, system prompt, araç tanımları ve CLAUDE.md içeriklerinin toplamını içerir.

### Model Bazlı Context Limitleri

| Model | Context Window | Çıktı Limiti |
|-------|----------------|--------------|
| Claude Opus 4.5 | 200K token | 32K token (max 64K) |
| Claude Sonnet 4.5 | 200K token | 16K token (max 64K) |
| Claude Haiku 4.5 | 200K token | 8K token (max 16K) |

**Not:** Sonnet 4 ve Sonnet 4.5 beta sürümlerinde 1M token extended context desteği mevcut.

### Token Nedir?

Token, modelin metni işleme birimidir. Yaklaşık olarak:
- 1 token ≈ 4 karakter (İngilizce)
- 1 token ≈ 2-3 karakter (Türkçe, özel karakterler nedeniyle)
- 1000 token ≈ 750 kelime (İngilizce)
- 1000 token ≈ 500-600 kelime (Türkçe)

**Örnek token hesabı:**
```
"Merhaba, nasılsın?" 
→ ["Mer", "haba", ",", " nas", "ıl", "sın", "?"]
→ 7 token
```

---

## 6.2 Context Dağılımı

### Tipik 200K Token Dağılımı

```
┌────────────────────────────────────────────────────────┐
│                    200K Context Window                  │
├────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐   │
│ │ System Prompt & Instructions        ~3-5K tokens │   │
│ └──────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────┐   │
│ │ Tool Definitions                    ~3-5K tokens │   │
│ └──────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────┐   │
│ │ CLAUDE.md Files                     ~2-10K tokens│   │
│ └──────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────┐   │
│ │ MCP Server Definitions              ~1-3K tokens │   │
│ └──────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────┐   │
│ │                                                    │   │
│ │           Conversation History                     │   │
│ │                                                    │   │
│ │              ~175-185K tokens                      │   │
│ │                                                    │   │
│ │           (Available for your work)                │   │
│ │                                                    │   │
│ └──────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### Overhead Detayları

| Bileşen | Min | Tipik | Max |
|---------|-----|-------|-----|
| System Prompt | 2K | 3K | 5K |
| Tool Definitions | 2K | 4K | 8K |
| CLAUDE.md (User) | 0K | 1K | 3K |
| CLAUDE.md (Project) | 0K | 2K | 5K |
| CLAUDE.md (Rules) | 0K | 1K | 3K |
| MCP Servers | 0K | 2K | 5K |
| **Toplam Overhead** | **4K** | **13K** | **29K** |
| **Kullanılabilir** | **171K** | **187K** | **196K** |

### Context Kullanımını İzleme

**CLI'da status kontrolü:**
```
> /status

Context Usage: 45,234 / 200,000 tokens (23%)
├── System: 3,120 tokens
├── Tools: 4,567 tokens
├── CLAUDE.md: 2,890 tokens
├── MCP: 1,234 tokens
└── Conversation: 33,423 tokens

Estimated remaining: ~154K tokens
```

---

## 6.3 /clear Komutu

### Ne Yapar?

`/clear` tüm konuşma geçmişini siler ve session'ı sıfırlar.

**Silinen:**
- Tüm mesajlar (user + assistant)
- Tool çıktıları
- Ara hesaplamalar
- Hata mesajları

**Korunan:**
- CLAUDE.md dosyaları
- Tool tanımları
- MCP server bağlantıları
- Proje dosyaları (disk'te)

### Ne Zaman Kullanılmalı?

**✅ KULLAN:**

| Senaryo | Neden |
|---------|-------|
| Görev tamamlandı | Yeni görev için temiz başlangıç |
| Context %70+ doldu | Performans düşüşünü önle |
| Claude halüsinasyon yapıyor | Kirli context'ten kurtul |
| Tamamen farklı konuya geçiş | İlgisiz context'i temizle |
| Döngüye girdi | Reset ile çık |

**❌ KULLANMA:**

| Senaryo | Neden |
|---------|-------|
| Görev ortasında | İlerleme kaybı |
| Debugging sırasında | Bağlam kaybı |
| Multi-step workflow | Adımlar arası bağımlılık |

### Kullanım Örnekleri

**Basit kullanım:**
```
> /clear
Context cleared. Starting fresh.
```

**Onay gerektiren mod:**
```json
// .claude/settings.json
{
  "clearConfirmation": true
}
```

```
> /clear
Are you sure you want to clear all context? (y/n): y
Context cleared. Starting fresh.
```

---

## 6.4 /compact Komutu

### Ne Yapar?

`/compact` konuşma geçmişini özetleyerek token kullanımını azaltır.

**Süreç:**
1. Claude mevcut konuşmayı analiz eder
2. Önemli bilgileri çıkarır
3. Özet oluşturur
4. Orijinal mesajları özetle değiştirir

### Otomatik vs Manuel Compact

**Otomatik tetikleme:**
- Context kullanımı %75'e ulaştığında otomatik çalışır
- Kullanıcı müdahalesi gerektirmez

**Manuel tetikleme:**
```
> /compact
Compacting conversation history...
Reduced from 150K to 45K tokens (70% reduction)
```

### Custom Compact Instructions

Özel talimatlarla compact:

```
> /compact Focus on the authentication module changes and ignore documentation discussions

Compacting with custom focus...
Retained: auth module changes, code snippets, decisions
Removed: doc discussions, general chat, exploration
Reduced from 120K to 30K tokens (75% reduction)
```

### Compact Kalite Kontrol

**Potansiyel sorunlar:**
- Önemli detaylar kaybolabilir
- Kod snippet'ları kesilebilir
- Karar bağlamı silinebilir

**Önleme:**
```
> /compact Preserve all code snippets and decision rationales

# Veya settings.json'da:
{
  "compact": {
    "preserveCodeBlocks": true,
    "preserveDecisions": true,
    "preserveErrors": true,
    "minRetention": 0.3
  }
}
```

---

## 6.5 /clear vs /compact Karşılaştırması

### Karar Matrisi

| Durum | /clear | /compact |
|-------|--------|----------|
| Görev tamamlandı | ✅ Önerilen | ❌ Gereksiz |
| Görev ortasında | ❌ İlerleme kaybı | ✅ Önerilen |
| Context %90+ | ✅ Daha güvenli | ⚠️ Yeterli olmayabilir |
| Halüsinasyon | ✅ Kesin çözüm | ⚠️ Sorun kalabilir |
| Debugging | ❌ Bağlam kaybı | ✅ Önerilen |
| Yeni konu | ✅ Önerilen | ❌ Gereksiz |

### Hibrit Strateji

**En iyi yaklaşım:**
```
1. Doğal kesme noktalarında /compact
2. Görev tamamlandığında /clear
3. Problem durumunda /clear
```

**Otomatik strateji:**
```json
// .claude/settings.json
{
  "contextManagement": {
    "autoCompactThreshold": 0.6,
    "compactWarningThreshold": 0.75,
    "forceClearThreshold": 0.95,
    "checkpointInterval": "30m"
  }
}
```

---

## 6.6 Document & Clear Pattern

### Pattern Tanımı

Uzun görevlerde context limitini aşmak için "dışa aktar → temizle → içe aktar" döngüsü.

### Adım Adım Uygulama

**Adım 1: Progress kaydet**
```
"Write our current progress to docs/session-progress.md:
- What we've completed
- Current state of each file
- Decisions made and rationale
- Next steps planned
- Any blockers or open questions"
```

**Adım 2: Context temizle**
```
> /clear
```

**Adım 3: Progress'i yükle ve devam et**
```
"Read docs/session-progress.md and continue from where we left off.
Focus on: [specific next task]"
```

### Progress Dosyası Formatı

```markdown
# Session Progress: [Görev Adı]

## Metadata
- Started: 2026-02-01 10:00 UTC
- Last Updated: 2026-02-01 14:30 UTC
- Estimated Completion: 70%

## Completed Work

### 1. [Alt görev 1] ✅
- File: `src/module1.py`
- Changes: Added validation function
- Tests: 5 tests passing

### 2. [Alt görev 2] ✅
- File: `src/module2.py`
- Changes: Refactored error handling
- Tests: 3 tests passing

## Current State

### Files Modified
| File | Status | Notes |
|------|--------|-------|
| src/module1.py | Complete | Ready for review |
| src/module2.py | Complete | Ready for review |
| src/module3.py | In Progress | 50% done |
| tests/test_module3.py | Not Started | Blocked by module3 |

### Key Decisions
1. **Decision:** Use async for API calls
   - Rationale: Better performance for concurrent requests
   - Alternative considered: Threading (rejected due to GIL)

2. **Decision:** PostgreSQL over SQLite
   - Rationale: Production-ready, better concurrent access
   - Trade-off: More setup complexity

## Next Steps
1. [ ] Complete module3.py implementation
2. [ ] Write tests for module3
3. [ ] Integration testing
4. [ ] Documentation update

## Blockers
- None currently

## Open Questions
1. Should we add rate limiting at the API gateway level?
2. What's the expected QPS for production?

## Code Snippets to Remember

### Validation Pattern
```python
def validate_question(data: dict) -> tuple[bool, list[str]]:
    errors = []
    # ... validation logic ...
    return len(errors) == 0, errors
```

### Error Handling Pattern
```python
try:
    result = await api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise QuestionGenerationError(str(e)) from e
```
```

### KIRO2 İçin Otomatik Progress Script

```python
# scripts/save_progress.py

import json
from datetime import datetime
from pathlib import Path

def save_session_progress(
    task_name: str,
    completed: list[dict],
    in_progress: list[dict],
    next_steps: list[str],
    decisions: list[dict],
    blockers: list[str] = None,
    questions: list[str] = None
):
    """Session progress'i markdown dosyasına kaydet."""
    
    progress_dir = Path("docs/progress")
    progress_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{task_name.lower().replace(' ', '_')}_{timestamp}.md"
    filepath = progress_dir / filename
    
    content = f"""# Session Progress: {task_name}

## Metadata
- Last Updated: {datetime.now().isoformat()}
- Status: In Progress

## Completed Work
"""
    
    for i, item in enumerate(completed, 1):
        content += f"""
### {i}. {item['title']} ✅
- File: `{item.get('file', 'N/A')}`
- Changes: {item.get('changes', 'N/A')}
- Tests: {item.get('tests', 'N/A')}
"""
    
    content += "\n## In Progress\n"
    for item in in_progress:
        content += f"- {item['title']}: {item.get('progress', '0')}% - {item.get('notes', '')}\n"
    
    content += "\n## Next Steps\n"
    for i, step in enumerate(next_steps, 1):
        content += f"{i}. [ ] {step}\n"
    
    content += "\n## Key Decisions\n"
    for i, decision in enumerate(decisions, 1):
        content += f"""
### {i}. {decision['title']}
- **Decision:** {decision['decision']}
- **Rationale:** {decision['rationale']}
"""
    
    if blockers:
        content += "\n## Blockers\n"
        for blocker in blockers:
            content += f"- {blocker}\n"
    
    if questions:
        content += "\n## Open Questions\n"
        for i, q in enumerate(questions, 1):
            content += f"{i}. {q}\n"
    
    filepath.write_text(content, encoding='utf-8')
    print(f"Progress saved to: {filepath}")
    return filepath

# Kullanım örneği
if __name__ == "__main__":
    save_session_progress(
        task_name="Verification Pipeline",
        completed=[
            {"title": "SyntaxValidator", "file": "orchestrator/validators/syntax_validator.py", "changes": "New file", "tests": "5 passing"},
            {"title": "SchemaValidator", "file": "orchestrator/validators/schema_validator.py", "changes": "New file", "tests": "8 passing"},
        ],
        in_progress=[
            {"title": "PedagogicalValidator", "progress": "70", "notes": "Curriculum mapping done"},
        ],
        next_steps=[
            "Complete PedagogicalValidator",
            "Implement DuplicateDetector",
            "Write integration tests",
        ],
        decisions=[
            {"title": "Embedding Model", "decision": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "rationale": "Good multilingual support for Turkish"},
        ],
        questions=[
            "Optimal similarity threshold for duplicates?",
        ]
    )
```

---

## 6.7 Subagent Context İzolasyonu

### Her Subagent Ayrı Context'e Sahip

Subagent başlatıldığında:
- Kendi 200K token context window'u
- Parent'tan bağımsız
- Sadece verilen görev bilgisi

```
┌─────────────────────────────────────────────────────────┐
│                    Parent Context (200K)                 │
│  ┌─────────────────────────────────────────────────────┐│
│  │ System + Tools + CLAUDE.md + Conversation           ││
│  │ [150K used]                                          ││
│  └─────────────────────────────────────────────────────┘│
│                          │                               │
│                    [Task spawn]                          │
│                          ↓                               │
│  ┌──────────────────┐  ┌──────────────────┐             │
│  │ Subagent 1 (200K)│  │ Subagent 2 (200K)│             │
│  │ [20K used]       │  │ [25K used]       │             │
│  │ - Task context   │  │ - Task context   │             │
│  │ - Isolated work  │  │ - Isolated work  │             │
│  └──────────────────┘  └──────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Subagent'a Geçirilen Bilgi

| Bilgi | Geçirilir mi? |
|-------|---------------|
| Görev tanımı | ✅ Evet |
| İlgili dosya yolları | ✅ Evet |
| Parent context özeti | ✅ Evet (kısa) |
| Tüm konuşma geçmişi | ❌ Hayır |
| Diğer tool çıktıları | ❌ Hayır |
| Diğer subagent sonuçları | ❌ Hayır |

### Subagent Overhead

Her subagent başlangıç overhead'i:

| Bileşen | Token |
|---------|-------|
| Subagent system prompt | ~2K |
| Görev tanımı | ~1-3K |
| İlgili context özeti | ~2-5K |
| Miras alınan kurallar | ~1-2K |
| **Toplam başlangıç** | **~6-12K** |

**10 paralel subagent teorik kapasitesi:**
```
10 × (200K - 12K overhead) = 10 × 188K = 1.88M token
```

### Subagent Sonuç Dönüşü

Subagent tamamlandığında parent'a dönen:

```json
{
  "status": "success",
  "summary": "3 paragraphs max summary",
  "files_created": ["path/to/file1.py"],
  "files_modified": ["path/to/file2.py"],
  "errors": [],
  "metrics": {
    "tokens_used": 45234,
    "turns": 12,
    "duration_seconds": 180
  }
}
```

**Verbose çıktı nereye gider?**
- Subagent'ın context'inde kalır
- Parent'a geçmez
- Log dosyasına yazılabilir

---

## 6.8 Agresif Context Yönetimi Stratejisi

### Boris Cherny'nin 5 Kuralı

**Kural 1: %50 Kuralı**
> "Önceki context'in %50'sinden azı ilgiliyse /clear kullan"

Örnek:
- Authentication görevi tamamlandı
- Şimdi tamamen farklı bir modüle geçiyorsun
- Önceki context'in çoğu artık ilgisiz
- `/clear` ve yeni başlangıç

**Kural 2: Skills'e Taşı**
> "Kuralları kesin başlıklarla Skills'e taşı - context kirliliğini azaltır"

CLAUDE.md'de her şeyi tutma. Koşullu kuralları `.claude/rules/`'a taşı:
```
# ÖNCE (tek CLAUDE.md)
Tüm Python kuralları...
Tüm JavaScript kuralları...
Tüm güvenlik kuralları...
= 5000 token her zaman yüklü

# SONRA (rules dizini)
.claude/rules/python-rules.md (Python dosyaları için)
.claude/rules/js-rules.md (JS dosyaları için)
.claude/rules/security-rules.md (güvenlik için)
= İlgili olanlar yüklenir
```

**Kural 3: Verbose Çıktıları Subagent'a Hapset**
> "Gürültülü araç çıktılarını subagent'lara hapset - ana context temiz kalır"

Örnek:
```
# KÖTÜ - Ana context'te
> npm install
[10000 satır çıktı...]

# İYİ - Subagent'ta
> Task: "Run npm install and report any errors"
Subagent: "Installation complete. No errors."
```

**Kural 4: 30 Dakika Checkpoint**
> "Her 30 dakikada bir progress checkpoint al"

Timer kur:
```bash
# 30 dakikada bir hatırlat
watch -n 1800 'notify-send "Claude" "Time for a checkpoint!"'
```

**Kural 5: Büyük Dosyaları Özetle**
> "Büyük dosya okumalarını summarize et, tam içeriği context'te tutma"

```
# KÖTÜ
"Read the entire codebase and understand it"
→ 50K token tüketir

# İYİ
"List all Python files and summarize what each module does in one sentence"
→ 2K token
```

---

## 6.9 Context Monitoring Dashboard

### CLI Status Command

```
> /status --detailed

╔══════════════════════════════════════════════════════════╗
║                   CONTEXT STATUS                          ║
╠══════════════════════════════════════════════════════════╣
║ Total:        200,000 tokens                              ║
║ Used:          89,234 tokens (45%)                        ║
║ Available:    110,766 tokens (55%)                        ║
╠══════════════════════════════════════════════════════════╣
║ BREAKDOWN                                                 ║
║ ├── System Prompt:     3,120 tokens  (2%)                ║
║ ├── Tool Definitions:  4,567 tokens  (2%)                ║
║ ├── CLAUDE.md:         2,890 tokens  (1%)                ║
║ ├── MCP Servers:       1,234 tokens  (1%)                ║
║ └── Conversation:     77,423 tokens (39%)                ║
╠══════════════════════════════════════════════════════════╣
║ SESSION INFO                                              ║
║ ├── Duration:          2h 34m                            ║
║ ├── Turns:             47                                ║
║ ├── Files Read:        12                                ║
║ ├── Files Modified:    5                                 ║
║ └── Tools Called:      89                                ║
╠══════════════════════════════════════════════════════════╣
║ RECOMMENDATIONS                                           ║
║ ⚠️  Consider /compact at 60% (currently 45%)              ║
║ ✓  Context usage healthy                                  ║
╚══════════════════════════════════════════════════════════╝
```

### Settings.json Konfigürasyonu

```json
{
  "contextMonitoring": {
    "showStatusBar": true,
    "warningThreshold": 0.6,
    "criticalThreshold": 0.8,
    "autoCompactThreshold": 0.75,
    "notifications": {
      "onWarning": true,
      "onCritical": true,
      "onAutoCompact": true
    },
    "logging": {
      "enabled": true,
      "logFile": ".claude/context-usage.log",
      "logInterval": "5m"
    }
  }
}
```

---

## 6.10 Özet

### Checklist

- [ ] Context dağılımını anla (overhead vs kullanılabilir)
- [ ] /clear ve /compact farkını bil
- [ ] Document & Clear pattern'ı uygula
- [ ] Subagent izolasyonunu kullan
- [ ] 5 agresif yönetim kuralını takip et
- [ ] Status monitoring'i aktifleştir

### Quick Reference

| Komut | Etki | Ne Zaman |
|-------|------|----------|
| `/clear` | Tam reset | Görev tamamlandı, yeni konu |
| `/compact` | Özet + temizle | Görev ortasında, %60+ doluluk |
| `/status` | Durum göster | Her zaman |
| `/compact [focus]` | Özel odaklı özet | Belirli context koruma |

### Metrikler

| Metrik | Sağlıklı | Uyarı | Kritik |
|--------|----------|-------|--------|
| Context kullanımı | < 50% | 50-75% | > 75% |
| Conversation token | < 100K | 100-150K | > 150K |
| Session süresi | < 1h | 1-2h | > 2h |
| Turns | < 30 | 30-50 | > 50 |

---

**Önceki Bölüm:** [05 - CLAUDE.md ve Memory Sistemi](./05-claude-md-ve-memory.md)  
**Sonraki Bölüm:** [07 - Subagent Mimarisi](./07-subagent-mimarisi.md)
