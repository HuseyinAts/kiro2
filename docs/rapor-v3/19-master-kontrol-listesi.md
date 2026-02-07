# BÖLÜM 19: Master Kontrol Listesi (v2 - Düzeltilmiş)

> Bu bölüm, 18 bölümlük rapordan çıkarılan tüm aksiyonları tek bir kontrol listesinde toplar.
> Claude Code'da her görev için bu listeyi referans al.

---

## 📋 GENEL WORKFLOW KONTROL LİSTESİ

### Her Oturum Başlangıcında
- [ ] CLAUDE.md dosyasını oku (proje root'ta varsa)
- [ ] `.claude/settings.json` yapılandırmasını kontrol et
- [ ] Proje context'ini anla (dizin yapısı, tech stack)
- [ ] Mevcut durumu değerlendir (son commit, açık PR'lar)
- [ ] Görev kapsamını netleştir (ne yapılacak, ne YAPILMAYACAK)
- [ ] `/doctor` ile sistem sağlığını kontrol et

### Her Görev Başlangıcında
- [ ] Görevi tam olarak anla (belirsizlik varsa sor)
- [ ] Kompleks mi değerlendir:
  - 3+ dosya değişikliği → Plan Mode
  - Yeni feature → Plan Mode
  - Refactoring → Plan Mode
  - Debugging (kök neden belirsiz) → Plan Mode
- [ ] İlgili dosyaları oku (ÖNCE oku, SONRA değiştir)
- [ ] Mevcut testleri kontrol et (varsa)
- [ ] Bağımlılıkları anla (import'lar, config'ler)

### Her Görev Sonunda
- [ ] Değişiklikleri doğrula (syntax, logic)
- [ ] Testleri çalıştır: `pytest -v`
- [ ] Lint kontrolü: `ruff check . --fix`
- [ ] Format kontrolü: `ruff format .`
- [ ] Type check (varsa): `mypy .`
- [ ] Gereksiz değişiklik var mı kontrol et
- [ ] Commit mesajı hazırla (conventional format)

---

## 🔵 BÖLÜM 1-2: Verification & Feedback Loops

### 3 Katmanlı Doğrulama Protokolü

**Layer 1 - Syntax Validation:**
- [ ] JSON geçerli mi? (`python -m json.tool file.json`)
- [ ] YAML geçerli mi? (yamllint)
- [ ] Python syntax doğru mu? (`python -m py_compile file.py`)
- [ ] Import'lar çözülebiliyor mu?

**Layer 2 - Semantic Validation:**
- [ ] Mantıksal tutarlılık var mı?
- [ ] İş kurallarına uygun mu?
- [ ] Edge case'ler düşünüldü mü?
- [ ] Null/None/empty kontrolleri var mı?

**Layer 3 - Independent Review:**
- [ ] Farklı perspektiften değerlendir
- [ ] "Bu gerçekten doğru mu?" sor
- [ ] Alternatif çözümleri düşün
- [ ] Testleri bağımsız çalıştır

### Her Kod Değişikliğinde
- [ ] Syntax hatası yok
- [ ] Import'lar çalışıyor
- [ ] Fonksiyon imzaları doğru (type hints)
- [ ] Return type'lar uyumlu
- [ ] Exception handling var
- [ ] Docstring yazıldı

### Her Soru Üretiminde (KIRO2)
- [ ] JSON schema geçerli
- [ ] Tüm zorunlu alanlar mevcut:
  - `question_id`, `question_text`, `options`, `correct_answer`, `difficulty_level`
- [ ] 5 seçenek var (A, B, C, D, E)
- [ ] Doğru cevap seçeneklerde var
- [ ] Zorluk seviyesi (1-5) içerikle uyumlu
- [ ] Türkçe karakterler doğru (ğ, ü, ş, ı, ö, ç)
- [ ] LaTeX syntax doğru ($...$ veya $$...$$)
- [ ] Duplicate kontrolü yapıldı

---

## 🔵 BÖLÜM 3: Plan Mode

### Ne Zaman Plan Mode Kullan?
- [ ] 3+ dosya değişikliği gerekiyorsa ✓
- [ ] Yeni feature implementasyonu ✓
- [ ] Refactoring işlemi ✓
- [ ] Debugging (kök neden belirsiz) ✓
- [ ] Mimari değişiklik ✓
- [ ] Kompleks görev (belirsiz adımlar) ✓

### Ne Zaman Plan Mode KULLANMA?
- [ ] Tek dosya, basit değişiklik ✗
- [ ] Typo düzeltme ✗
- [ ] Basit soru-cevap ✗
- [ ] Dokümantasyon okuma ✗

### Plan Mode Süreci
- [ ] `Shift+Tab x2` ile Plan Mode'a geç
- [ ] Mevcut dosyaları analiz et (read-only)
- [ ] Adım adım plan oluştur (numbered list)
- [ ] Her adım için:
  - [ ] Tek bir iş yapıyor (atomic)
  - [ ] Expected output belirli
  - [ ] Bağımlılıklar net
- [ ] Risk noktalarını işaretle
- [ ] Kullanıcı onayı al
- [ ] Plan onaylandıktan sonra execute et

### Plan Kalite Kontrolü
- [ ] Her adım atomic (tek iş yapıyor)
- [ ] Bağımlılıklar doğru sıralanmış
- [ ] Rollback noktaları belirlenmiş
- [ ] Test stratejisi dahil edilmiş
- [ ] Tahmini süre/effort belirtilmiş

---

## 🔵 BÖLÜM 4: Paralel Oturum Yönetimi

### Git Worktree Kurulumu
```bash
# Komutlar
git worktree add ../kiro2-feature-x feature-x
git worktree add ../kiro2-bugfix-y bugfix-y
git worktree list
git worktree remove ../kiro2-feature-x
```

- [ ] Ana branch temiz mi? (uncommitted changes yok)
- [ ] Worktree dizini oluşturuldu mu?
- [ ] Her worktree farklı branch'te mi?
- [ ] Dosya çakışması riski değerlendirildi mi?
- [ ] Aynı dosyayı iki worktree'de değiştirmiyorum

### Paralel Çalışma Kuralları
- [ ] Her oturum farklı modülde çalışıyor
- [ ] Shared resource yok (aynı dosya değişmiyor)
- [ ] Database lock riski yok (farklı tablolar/kayıtlar)
- [ ] Merge stratejisi belirlenmiş (rebase vs merge)
- [ ] Maksimum 5 paralel oturum

### Senkronizasyon
- [ ] Düzenli commit yapılıyor (her mantıksal değişiklik)
- [ ] Branch'ler güncel tutuluyor (`git pull --rebase`)
- [ ] Conflict'ler hemen çözülüyor
- [ ] Ana branch'e merge öncesi:
  - [ ] Tüm testler geçiyor
  - [ ] Code review yapıldı
  - [ ] Conflict yok

---

## 🔵 BÖLÜM 5: CLAUDE.md ve Memory

### CLAUDE.md Zorunlu Bölümler
- [ ] **Proje Bilgisi:** İsim, konum, tech stack
- [ ] **Kritik Kurallar:** ASLA yapma listesi
- [ ] **Dizin Yapısı:** Ana klasörler ve amaçları
- [ ] **Hızlı Komutlar:** Build, test, lint komutları
- [ ] **Veritabanı:** Connection string, port, credentials (referans)

### CLAUDE.md Yapısı Kontrolü
- [ ] Proje bilgisi güncel mi?
- [ ] Kritik kurallar tanımlı mı? (PostgreSQL port 5434!)
- [ ] Dizin yapısı doğru mu?
- [ ] Hızlı komutlar çalışıyor mu?
- [ ] Son güncelleme tarihi var mı?

### Memory Yönetimi
- [ ] Önemli kararlar kaydedildi mi?
- [ ] Session arası bilgi aktarımı var mı?
- [ ] Progress dosyası güncel mi? (`docs/session-progress.md`)
- [ ] Tekrar eden hatalar not edildi mi?
- [ ] Çözülen sorunlar belgelendi mi?

### CLAUDE.md Güncelleme Zamanları
- [ ] Yeni modül eklendiğinde
- [ ] Kritik kural değiştiğinde
- [ ] Proje yapısı değiştiğinde
- [ ] Yeni pattern keşfedildiğinde
- [ ] Tech stack değiştiğinde
- [ ] Environment değişikliğinde

---

## 🔵 BÖLÜM 6: Context Yönetimi

### Context Durumu Takibi
- [ ] `/status` ile context durumunu kontrol et
- [ ] %60 dolulukta: Uyarı (settings.json warningThreshold)
- [ ] %70 dolulukta: Aksiyon al - /compact veya /clear (settings.json clearThreshold)
- [ ] %85+ dolulukta: ACİL clear gerekli
- [ ] Gereksiz dosya yükleME (sadece gerekeni oku)
- [ ] Büyük dosyalarda `grep` veya `head/tail` kullan

### /clear Kullanım Zamanları
- [ ] Yeni, tamamen farklı görev başlarken
- [ ] Hata döngüsüne girildiğinde (aynı hata 3+ kez)
- [ ] Konu tamamen değiştiğinde
- [ ] Context %80+ dolduğunda
- [ ] Model "unutkanlık" gösterdiğinde

### /compact Kullanım Zamanları
- [ ] Uzun görev devam ederken
- [ ] Önceki context'in bir kısmı hala gerekli
- [ ] Otomatik tetiklendiğinde (onayla)
- [ ] Custom özet ile: `/compact [özet talimatı]`

### Document & Clear Pattern
```
1. Progress dosyası oluştur: docs/session-progress.md
2. İçeriğe ekle:
   - Tamamlanan işler
   - Mevcut durum (hangi dosya, hangi satır)
   - Sonraki adımlar
   - Açık sorular/blocker'lar
3. /clear yap
4. Progress dosyasını oku ve devam et
```

- [ ] Progress dosyası oluşturuldu
- [ ] Mevcut durum tam kaydedildi
- [ ] Sonraki adımlar listelendi
- [ ] Açık sorular not edildi
- [ ] `/clear` yapıldı
- [ ] Progress dosyası okunarak devam edildi

---

## 🔵 BÖLÜM 7-8: Subagent Mimarisi

### Subagent Kullanım Kararı
Ne zaman KULLAN:
- [ ] Görev bağımsız mı? (izole çalışabilir) ✓
- [ ] Verbose output var mı? (context kirletir) ✓
- [ ] Farklı uzmanlık gerekiyor mu? ✓
- [ ] Paralel çalışma mümkün mü? ✓

Ne zaman KULLANMA:
- [ ] Ana context gerekli ✗
- [ ] Sık iletişim lazım ✗
- [ ] Basit/kısa görev ✗

### Subagent Çağırma Syntax
```
Task: [görev açıklaması]
Task [agent-name]: [görev açıklaması]
```

### Subagent Görev Tanımı
- [ ] Net ve spesifik görev tanımı
- [ ] Beklenen output formatı belirli
- [ ] Scope sınırları çizilmiş (ne YAPILMAYACAK)
- [ ] Timeout değeri uygun (default: 300s)
- [ ] Hangi dosyalara erişeceği belirli

### Mevcut Subagent'lar (KIRO2) — 19 aktif + 10 archive
| Agent | Kullanım | Model |
|-------|----------|-------|
| **Code Quality (4)** | | |
| `verification-agent` | Boris Cherny doğrulama | Haiku (PROACTIVE) |
| `test-runner` | Test çalıştırma & coverage | Sonnet (PROACTIVE) |
| `code-reviewer` | PR review & güvenlik | Sonnet (PROACTIVE) |
| `debugger` | Hata ayıklama, root cause | Opus |
| **Specialists (3)** | | |
| `python-pro` | Python 3.11+ uzmanlığı | Opus (PROACTIVE) |
| `turkish-nlp-specialist` | Türkçe NLP, IRT/FSRS/ZPD | Opus |
| `claude-md-improvement` | Auto feedback loop | Sonnet |
| **KIRO2 Core (4)** | | |
| `kiro2-backend-api` | FastAPI, SQLAlchemy | inherit |
| `kiro2-frontend-specialist` | React, TypeScript | inherit |
| `kiro2-devops-engineer` | CI/CD, deployment | inherit |
| `kiro2-content-manager` | Soru üretimi, validation | inherit |
| **Orchestration (1)** | | |
| `master-orchestrator` | Ana koordinatör | Opus |
| **KFC Spec Workflow (7)** | | |
| `spec-*` (7 adet) | Requirements→Design→Tasks→Impl→Test→Judge | inherit |

> 10 agent archive'da: worker-*, backend/frontend-coordinator, ai-ml-coordinator, devops-coordinator, steering docs

### Subagent Sonuç Kontrolü
- [ ] Görev tamamlandı mı?
- [ ] Output beklenen formatta mı?
- [ ] Hata oluştu mu? (error handling)
- [ ] Ana context'e entegre edildi mi?
- [ ] Sonuç doğrulandı mı?

### Koordinasyon Dosyaları
```
.claude/coordination/
├── tasks/          # Görev tanımları
├── results/        # Sonuçlar
├── locks/          # File locks
└── state.json      # Genel durum
```

- [ ] Tasks dizini: Görev JSON'ları
- [ ] Results dizini: Sonuç JSON'ları
- [ ] State.json: Aktif görevler, tamamlananlar
- [ ] Lock mekanizması: Race condition önleme

---

## 🔵 BÖLÜM 9: Hooks Sistemi

### Hook Yapılandırma Kontrolü
**Dosya:** `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "./hooks/validate-bash.sh",
        "timeout": 5000
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "./hooks/auto-format.sh",
        "timeout": 10000
      }
    ]
  }
}
```

- [ ] `.claude/settings.json` mevcut
- [ ] Matcher pattern'ları doğru (regex)
- [ ] Timeout değerleri uygun (ms cinsinden)
- [ ] Hook script'leri çalıştırılabilir (`chmod +x`)
- [ ] Windows'ta: `.ps1` veya `.cmd` uzantısı

### PreToolUse Hook'ları (pre-tool-use.ps1)
- [ ] Tehlikeli komut bloklama aktif:
  - `rm -rf /`, `DROP DATABASE`, `format C:`
  - `git push --force origin main/master`
  - `cat .env`, `echo $API_KEY`
  - `curl | bash`, `eval()`, `exec()`
- [ ] Dosya path validasyonu var
- [ ] Reward hacking tespiti (echo "Success", exit 0 #, true)
- [ ] Korunan path'ler engelleniyor (~/.ssh, ~/.aws, .env)

### PostToolUse Hook'ları (post-tool-use.ps1)
- [ ] Edit/Write sonrası otomatik doğrulama:
  - Python: `ruff check` (E,F,W hataları)
  - Python: `mypy` type check
  - Reward hacking pattern tespiti
- [ ] Test dosyası bütünlük kontrolü (boş test, skipped test)
- [ ] Exit Code 2 ile bloklama çalışıyor

### PreCompact Hook (pre-compact.ps1)
- [ ] Compaction öncesi progress.md yedekleniyor
- [ ] Git status ve son commit'ler kaydediliyor
- [ ] Backup dizini: `~/.claude/session-backups/`
- [ ] Compaction log'u tutuluyor

### Stop Hook (stop.ps1)
- [ ] Claude yanıt tamamlandığında final kontrol
- [ ] Uncommitted changes uyarısı
- [ ] TODO listesi hatırlatması
- [ ] Build status kontrolü
- [ ] Informational only (exit 0, bloklamaz)

### Hook Exit Code'ları (KRİTİK)
| Code | Anlam | Aksiyon |
|------|-------|---------|
| `0` | Başarı | Devam et |
| `2` | BLOCK | İşlemi ENGELLE |
| `1,3,4...` | Warning | Log'la, devam et |

### Platform Farkları
| Platform | Script | Shebang |
|----------|--------|---------|
| Linux/Mac | `.sh` | `#!/bin/bash` |
| Windows | `.ps1` veya `.cmd` | - |

---

## 🔵 BÖLÜM 10: Reward Hacking Önleme

### 🚨 ASLA YAPMA - Kod Yazarken
- [ ] ❌ Test'i "geçmesi için" değiştirme
- [ ] ❌ `assert True` kullanma
- [ ] ❌ `echo Success` fake output yazma
- [ ] ❌ `exit 0` ile zorla başarı döndürme
- [ ] ❌ Boş test yazarak coverage şişirme
- [ ] ❌ Hata mesajlarını `/dev/null`'a yönlendirme
- [ ] ❌ Test output'unu manipüle etme
- [ ] ❌ `try: ... except: pass` ile hataları yutma

### 🚨 ASLA YAPMA - Soru Üretirken
- [ ] ❌ Kolay soru üretip yüksek zorluk verme
- [ ] ❌ Cevabı soru metnine gizleme
- [ ] ❌ Anlamsız/kolay çeldiriciler yazma
- [ ] ❌ Mevcut soruyu kopyalayıp değiştirme
- [ ] ❌ Validation'ı atlatacak formatta üretme

### ✅ Bağımsız Doğrulama
- [ ] Farklı yöntemle sonucu kontrol et
- [ ] Testleri izole ortamda çalıştır
- [ ] Output'u manuel incele
- [ ] "Bu gerçekten doğru mu?" sor
- [ ] Başka birinin (veya subagent) review etmesini sağla

### Reward Hacking Tespit İşaretleri
- [ ] Test aniden geçmeye başladı (şüpheli)
- [ ] Coverage %100'e çıktı (şüpheli)
- [ ] Çok hızlı "tamamlandı" (şüpheli)
- [ ] Zorluk dağılımı bozuk (şüpheli)
- [ ] Duplicate oranı yüksek (şüpheli)

---

## 🔵 BÖLÜM 11: Prompt Engineering

### XML Tag Kullanımı
```xml
<instructions>Ana talimatlar buraya</instructions>
<context>Bağlam bilgisi buraya</context>
<example>
  <input>Örnek girdi</input>
  <output>Örnek çıktı</output>
</example>
<constraints>Kısıtlamalar buraya</constraints>
<format>Beklenen çıktı formatı</format>
```

- [ ] `<instructions>` - Ana talimatlar (ne yapılacak)
- [ ] `<context>` - Bağlam bilgisi (neden yapılacak)
- [ ] `<example>` - Örnekler (nasıl yapılacak)
- [ ] `<constraints>` - Kısıtlamalar (ne YAPILMAYACAK)
- [ ] `<format>` - Çıktı formatı (nasıl dönecek)

### Few-Shot Örnekleri
- [ ] 3-5 örnek (optimal sayı)
- [ ] Örnekler çeşitli (farklı case'ler)
- [ ] Edge case dahil (sınır durumlar)
- [ ] Zorluk artan sırada (kolay → zor)
- [ ] Hatalı örnek + düzeltme (ne YAPILMAMALI)

### Chain-of-Thought (CoT)
Ne zaman kullan:
- [ ] Matematik problemlerinde ✓
- [ ] Mantıksal çıkarımlarda ✓
- [ ] Multi-step görevlerde ✓
- [ ] Debugging'de ✓

Ne zaman KULLANMA:
- [ ] Basit fact soruları ✗
- [ ] Format dönüşümü ✗
- [ ] Direkt lookup ✗

Format:
```xml
<thinking>Düşünce süreci buraya</thinking>
<answer>Final cevap buraya</answer>
```

### Prompt Kalite Kontrolü
- [ ] Net ve spesifik (belirsizlik yok)
- [ ] Pozitif talimatlar ("X yap" vs "X yapMA")
- [ ] Gereksiz tekrar yok
- [ ] Beklenen format belirtilmiş
- [ ] Kısıtlamalar açık
- [ ] Örnek verilmiş (kompleks görevlerde)

---

## 🔵 BÖLÜM 12: MCP Entegrasyonları

### MCP Server Kontrolü
**Dosya:** `.mcp.json` (proje) veya `~/.claude/mcp.json` (global)

| Server | Amaç | Durum |
|--------|------|-------|
| kiro2-orchestrator | İç orchestration MCP | Aktif |
| gemini-mcp | Google Gemini entegrasyonu | Aktif |
| gemini-reasoning-mcp | Advanced reasoning | Aktif |
| zemberek-mcp | Türkçe NLP (morfoloji, heceleme) | Aktif |
| chromadb-mcp | Vector DB (semantic search) | Aktif |
| claude-md-improvement | CLAUDE.md otomatik iyileştirme | Aktif |

- [ ] MCP server'lar çalışıyor mu? (`.mcp.json` kontrol)
- [ ] Zemberek bağlantısı aktif mi? (host:8081)
- [ ] ChromaDB persist dizini doğru mu? (`backend/vector_db`)
- [ ] Gemini API key tanımlı mı? (GOOGLE_API_KEY)

### MCP Kullanım Kararı
- [ ] Harici veri gerekli mi? → Context7, Web Search
- [ ] Kalıcı depolama lazım mı? → Memory
- [ ] Dosya işlemi gerekli mi? → Filesystem
- [ ] Veritabanı sorgusu var mı? → PostgreSQL

### MCP Güvenlik
- [ ] Read-only user kullanılıyor (DB için)
- [ ] Allowed directories kısıtlı (Filesystem için)
- [ ] Environment variables güvenli (.env'de)
- [ ] Hassas veri loglanmıyor
- [ ] Rate limiting var

---

## 🔵 BÖLÜM 13: Claude Agent SDK

### API Çağrısı Öncesi
- [ ] Model seçimi uygun mu?
  - `claude-opus-4-5-20251101` - Kompleks analiz
  - `claude-sonnet-4-5-20250929` - Genel amaçlı
  - `claude-haiku-4-5-20251001` - Hızlı/ucuz
- [ ] `max_tokens` yeterli mi? (output için)
- [ ] System prompt hazır mı?
- [ ] Tools tanımlandı mı? (JSON Schema)

### API Çağrısı Sırası
- [ ] Rate limiting aktif (50 req/min önerilen)
- [ ] Error handling var:
  - `RateLimitError` → Exponential backoff
  - `APIConnectionError` → Retry
  - `APIError` → Log ve fail
- [ ] Retry logic implementeli (max 3)
- [ ] Timeout ayarlanmış

### API Çağrısı Sonrası
- [ ] Response parse edildi
- [ ] Tool calls işlendi (varsa)
- [ ] Maliyet kaydedildi (token tracking)
- [ ] Başarı/hata loglandı
- [ ] Cache güncellendi (varsa)

### Maliyet Takibi
| Model | Input (1M) | Output (1M) |
|-------|------------|-------------|
| Opus | $15 | $75 |
| Sonnet | $3 | $15 |
| Haiku | $0.25 | $1.25 |

- [ ] Daily limit ayarlandı
- [ ] Monthly limit ayarlandı
- [ ] Alert threshold var

---

## 🔵 BÖLÜM 14: GitHub Actions

### Workflow Dosyası Kontrolü
**Dosya:** `.github/workflows/claude-code.yml`

- [ ] Trigger doğru tanımlı:
  - `pull_request: [opened, synchronize]`
  - `issue_comment: [created]`
- [ ] Permissions yeterli:
  - `contents: read`
  - `pull-requests: write`
  - `issues: write`
- [ ] Secrets tanımlı: `ANTHROPIC_API_KEY`
- [ ] Timeout ayarlanmış (10-15 dk)

### PR Review Workflow
- [ ] Otomatik review aktif
- [ ] Security scan dahil
- [ ] Test çalıştırma var
- [ ] Maliyet limiti ayarlı (conditional execution)
- [ ] `@claude` mention desteği

### CI/CD Best Practices
- [ ] Matrix build (modüller için)
- [ ] Artifact kaydetme (review raporları)
- [ ] Coverage raporu üretme
- [ ] Conditional execution (maliyet kontrolü)
- [ ] Caching (dependencies)

---

## 🔵 BÖLÜM 15: LangGraph Entegrasyonu

### StateGraph Kontrolü
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(KIROState)
graph.add_node("node_name", node_function)
graph.add_edge("from", "to")
graph.set_entry_point("start")
app = graph.compile(checkpointer=checkpointer)
```

- [ ] State tipi tanımlı (TypedDict)
- [ ] Tüm node'lar eklenmiş
- [ ] Edge'ler doğru bağlanmış
- [ ] Conditional edge'ler tanımlı
- [ ] Entry point belirlenmiş

### Node Implementasyonu
- [ ] Her node tek iş yapıyor (single responsibility)
- [ ] State güncellemesi doğru (immutable update)
- [ ] Error handling var
- [ ] Logging aktif
- [ ] Timeout var (uzun işlemler için)

### Checkpointing
- [ ] Checkpoint storage seçildi:
  - Development: `SqliteSaver`
  - Production: `PostgresSaver`
- [ ] Thread ID stratejisi var
- [ ] Recovery mekanizması test edildi
- [ ] State consistency sağlanıyor

### Human-in-the-Loop
- [ ] Interrupt noktaları belirlendi (`interrupt_before`)
- [ ] Review UI/CLI mevcut
- [ ] Timeout ayarlandı (human response için)
- [ ] Devam mekanizması çalışıyor (`app.invoke(None, config)`)

### Orchestrator Ek Modüller (v2.6.0)
| Modül | Amaç | Durum |
|-------|-------|-------|
| `loop_guardrail.py` | Sonsuz döngü koruması (max iter, timeout, repeated error, no-progress) | ✅ Aktif |
| `risk_map_generator.py` | Görev risk analizi (security, scope, complexity, data integrity) | ✅ Aktif |
| `regression_tracker.py` | Test/metrik regresyon tespiti (coverage, failures, duration, error rate) | ✅ Aktif |
| `cost_tracker.py` | LLM maliyet takibi (daily/weekly/monthly budget, model bazlı) | ✅ Aktif |

> Bu modüller `orchestrator/core/__init__.py` v2.6.0'da export edilmektedir.

---

## 🔵 BÖLÜM 16: Test ve Kalite

### Test Yazarken
- [ ] Test izole (bağımsız çalışabilir, sıra bağımsız)
- [ ] Tek bir şeyi test ediyor (single assertion focus)
- [ ] Assertions anlamlı (clear failure message)
- [ ] Edge case'ler dahil (boundary conditions)
- [ ] Happy path + error path
- [ ] Mock'lar minimal (sadece external dependencies)

### Test Çalıştırırken
```bash
pytest -v                    # Verbose
pytest -x                    # İlk hatada dur
pytest --lf                  # Son başarısızları tekrarla
pytest --cov=orchestrator    # Coverage ile
pytest -m unit               # Sadece unit testler
pytest -m "not slow"         # Yavaş testleri atla
```

- [ ] Unit testler geçiyor
- [ ] Integration testler geçiyor
- [ ] Coverage %80+ (hedef)
- [ ] Performans testleri (gerekirse)
- [ ] E2E testler (kritik flow'lar)

### Fixture Kullanımı
- [ ] Mock'lar doğru yapılandırılmış
- [ ] Database fixture izole (her test temiz DB)
- [ ] API mock'ları güncel
- [ ] Cleanup yapılıyor (teardown)
- [ ] Fixture scope uygun (function/class/module)

### CI'da Test
- [ ] Her PR'da test çalışıyor
- [ ] Coverage raporu üretiliyor
- [ ] Başarısız test merge'i engelliyor
- [ ] Test süresi kabul edilebilir (<5 dk)
- [ ] Flaky test yok (veya retry var)

---

## 🔵 BÖLÜM 17: Risk Yönetimi

### Teknik Risk Kontrolleri
| Risk | Kontrol |
|------|---------|
| API Rate Limit | Rate limiter aktif |
| Context Overflow | /compact, /clear stratejisi |
| DB Connection Loss | Connection pool, retry |
| Timeout | Timeout değerleri ayarlı |

- [ ] Rate limiting aktif
- [ ] Context overflow koruması var
- [ ] Database connection pool var
- [ ] Retry logic implementeli
- [ ] Circuit breaker (opsiyonel)

### Güvenlik Risk Kontrolleri
- [ ] API key `.env`'de (hardcode yok)
- [ ] `.env` gitignore'da
- [ ] SQL injection koruması (parametrized query)
- [ ] RBAC implementeli (role-based access)
- [ ] Sensitive data loglanmıyor
- [ ] Secrets rotation planı var

### Kalite Risk Kontrolleri
- [ ] Quality gates aktif (lint, test, type check)
- [ ] Duplicate detection çalışıyor
- [ ] Human review queue var (kritik içerik için)
- [ ] Anomaly detection aktif (unusual patterns)

### Operasyonel Risk Kontrolleri
- [ ] Maliyet takibi yapılıyor (daily/monthly)
- [ ] Budget limitleri var ve alert veriyor
- [ ] Health check çalışıyor
- [ ] Alerting konfigüre edilmiş (PagerDuty/Slack)
- [ ] Backup stratejisi var
- [ ] Disaster recovery planı var

---

## 🔵 BÖLÜM 18: Yol Haritası Takibi

### Haftalık Kontrol
- [ ] Bu hafta tamamlanması gereken görevler net
- [ ] Blocker'lar belirlendi ve escalate edildi
- [ ] Öncelikler güncel (değişiklik varsa)
- [ ] Progress kaydedildi (docs/progress.md)
- [ ] Retrospektif notları alındı

### Modül Durumu Takibi
- [ ] Tamamlanan modüller işaretlendi ✅
- [ ] Devam eden modüllerin %'si güncel
- [ ] Eksik modüller planlandı
- [ ] Bağımlılıklar gözetildi
- [ ] Technical debt takip ediliyor

### Metrik Takibi
| Metrik | Hedef | Mevcut |
|--------|-------|--------|
| Test coverage | >80% | ? |
| Error rate | <5% | ? |
| API success | >99% | ? |
| Response time | <2s | ? |

- [ ] Test coverage kontrol edildi
- [ ] Error rate izleniyor
- [ ] Maliyet takibi yapılıyor
- [ ] Performance metrikleri ölçülüyor

---

## 🎯 KIRO2'YE ÖZEL KONTROL LİSTESİ

### ⚠️ PostgreSQL Kuralları (KRİTİK!)
- [ ] **Port: 5434** (5432 DEĞİL! Bu çok önemli!)
- [ ] Connection string: `postgresql://kiro2_user:password@localhost:5434/kiro2`
- [ ] Connection pool kullanılıyor (min=2, max=10)
- [ ] Parametrized query (SQL injection yok)
- [ ] Transaction yönetimi var

### Türkçe İçerik Kuralları
- [ ] UTF-8 encoding (`# -*- coding: utf-8 -*-`)
- [ ] Türkçe karakterler doğru: ğ, ü, ş, ı, ö, ç, Ğ, Ü, Ş, İ, Ö, Ç
- [ ] Büyük İ = İ (dotted), küçük ı = ı (dotless)
- [ ] LaTeX inline: `$...$`
- [ ] LaTeX display: `$$...$$`
- [ ] JSON'da unicode escape değil, direkt karakter

### Soru Üretimi Kuralları
- [ ] `question_id` formatı: `[DERS]-[SINAV]-[KONU]-[NO]`
  - Örnek: `MAT-AYT-LIMIT-001`
- [ ] 5 seçenek zorunlu (A, B, C, D, E)
- [ ] `difficulty_level`: 1-5 arası integer
- [ ] Zorluk dağılımı: %10/%20/%40/%20/%10 (1/2/3/4/5)
- [ ] Duplicate rate: <%1 (semantic similarity check)
- [ ] Human review pass rate: >%95

### Orchestrator Kuralları
- [ ] LangGraph StateGraph kullanılıyor
- [ ] Redis için run-scoped operations
- [ ] LangSmith tracing aktif
- [ ] Quality gates pipeline çalışıyor:
  1. Schema validation
  2. Content validation
  3. Pedagogical validation
  4. Duplicate detection

---

## 📊 HIZLI REFERANS TABLOSU

### Komutlar
| Komut | Kullanım | Ne Zaman |
|-------|----------|----------|
| `Shift+Tab x2` | Plan Mode toggle | Kompleks görev |
| `/clear` | Context temizle | Yeni görev, %80+ dolu |
| `/compact` | Context özetle | Devam eden uzun görev |
| `/status` | Durum göster | Context kontrolü |
| `/doctor` | Sistem sağlığı | Sorun şüphesi |
| `# [not]` | Anlık not | Önemli bilgi |

### Model Seçimi
| Görev | Model | Neden |
|-------|-------|-------|
| Derin analiz, mimari | claude-opus-4-5 | En yetenekli |
| Genel amaçlı, kod | claude-sonnet-4-5 | Denge |
| Hızlı görevler, basit | claude-haiku-4-5 | Hızlı/ucuz |

### Hook Exit Codes
| Code | Anlam | Aksiyon |
|------|-------|---------|
| 0 | Başarı | Devam et |
| 2 | BLOCK | İşlemi ENGELLE |
| 1,3,4... | Warning | Log'la, devam et |

### Dosya Konumları
| Dosya | Konum | Amaç |
|-------|-------|------|
| CLAUDE.md | Proje root | Ana kılavuz |
| Subagents | `.claude/agents/` | Agent tanımları |
| Hooks | `.claude/settings.json` | Hook config |
| Progress | `docs/session-progress.md` | Durum takibi |
| Rapor | `docs/rapor-v3/` | Detaylı dokümantasyon |

---

## ✅ GÜNLÜK KONTROL (Daily Checklist)

### 🌅 Sabah (Oturum Başı)
- [ ] CLAUDE.md güncel mi?
- [ ] `/doctor` ile sistem sağlığı OK
- [ ] Dünkü progress kontrol edildi
- [ ] Bugünkü görevler netleştirildi
- [ ] Context temiz başlıyor (`/clear`)

### 🌞 Öğle (Ara Kontrol)
- [ ] Context durumu iyi mi? (`/status`)
- [ ] Beklenmedik hata var mı?
- [ ] Progress kaydedildi mi?
- [ ] Blocker var mı? (escalate et)

### 🌙 Akşam (Oturum Sonu)
- [ ] Günün çalışmaları commit edildi
- [ ] Progress dosyası güncellendi
- [ ] Yarın için notlar alındı
- [ ] Testler geçiyor mu kontrol edildi
- [ ] Açık PR'lar review edildi

---

## 🏁 RELEASE CHECKLIST (Major Release Öncesi)

### Kod Kalitesi
- [ ] Test coverage > %80
- [ ] Lint errors: 0 (`ruff check .`)
- [ ] Type errors: 0 (`mypy .`)
- [ ] Tüm public fonksiyonlarda docstring
- [ ] Dead code temizlendi
- [ ] TODO/FIXME'ler çözüldü

### Güvenlik
- [ ] Security audit yapıldı
- [ ] Secrets güvenli (.env, not hardcoded)
- [ ] SQL injection yok (parametrized query)
- [ ] XSS koruması var (frontend)
- [ ] Dependency vulnerabilities tarandı (`pip-audit`)

### Performans
- [ ] Response time < 2s (P95)
- [ ] Memory usage normal (leak yok)
- [ ] Database queries optimize (N+1 yok)
- [ ] Rate limiting çalışıyor
- [ ] Caching stratejisi var

### Dokümantasyon
- [ ] README güncel
- [ ] API docs güncel
- [ ] CHANGELOG yazıldı
- [ ] Migration notları hazır
- [ ] Deploy notları hazır

### Operasyonel
- [ ] Monitoring konfigüre
- [ ] Alerting aktif
- [ ] Backup stratejisi test edildi
- [ ] Rollback planı hazır
- [ ] Runbook güncellendi

---

## 📈 METRİK HEDEF TABLOSU

| Kategori | Metrik | Hedef | Kritik |
|----------|--------|-------|--------|
| **Kod** | Test coverage | >80% | >60% |
| **Kod** | Lint errors | 0 | <10 |
| **Kod** | Type errors | 0 | <5 |
| **Performans** | API response | <2s | <5s |
| **Performans** | Build time | <60s | <120s |
| **Güvenilirlik** | Uptime | >99.9% | >99% |
| **Güvenilirlik** | Error rate | <1% | <5% |
| **Maliyet** | Daily API cost | <$10 | <$50 |
| **İçerik** | Question quality | >95% | >90% |
| **İçerik** | Duplicate rate | <1% | <5% |

---

---

## 🔵 SKILLS SİSTEMİ (.claude/skills/)

### Mevcut Skill Dosyaları
| Skill | Amaç | Kullanım |
|-------|------|----------|
| `code-review` | Kod inceleme standartları | Agent'lara yüklenebilir |
| `deep-research` | Derin araştırma protokolü | Araştırma görevleri |
| `deploy` | Deployment prosedürleri | DevOps agent |
| `education-algorithms` | IRT, ZPD, FSRS algoritmaları | Content agent |
| `irt-validation` | IRT parametre doğrulama | Soru validasyonu |
| `kiro2-specific` | KIRO2 proje kuralları | Tüm agent'lar |
| `owasp-guide` | OWASP güvenlik rehberi | Security review |
| `perf-analysis` | Performans analiz protokolü | Optimization |
| `save-memory` | Session hafıza kaydetme | Context yönetimi |
| `security-checklist` | Güvenlik kontrol listesi | Her PR'da |
| `turkish-nlp` | Türkçe NLP kuralları | İçerik üretimi |
| `yks-generator` | YKS soru üretim standartları | Soru üretimi |

### Skills Kullanımı
```yaml
# Agent tanımında skills referansı
---
name: my-agent
skills:
  - security-checklist
  - kiro2-specific
---
```

- [ ] İlgili agent'lara doğru skill'ler atanmış mı?
- [ ] Skill dosyaları güncel mi?
- [ ] Yeni görev türü için skill gerekiyor mu?

---

**Bu kontrol listesi, 18 bölümlük raporun tüm kritik noktalarını özetler.**
**Her görevde ilgili bölümlerin checklistini kullan.**

*Son güncelleme: 1 Şubat 2026 - v3 (Gerçek durumla senkronize edilmiş)*
*Düzeltmeler: Context threshold %60/%70, MCP listesi güncellenmiş, Hooks detaylandırılmış, Skills eklendi*
