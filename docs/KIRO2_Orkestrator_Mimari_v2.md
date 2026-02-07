# KIRO2 Tam Otonom Orkestratör Mimarisi v2.0

**Tarih:** 11 Ocak 2026  
**Durum:** Uygulama için hazır

---

## 1. Genel Bakış

KIRO2 platformu için tam otonom, kendi kendini geliştiren orkestratör sistemi. Her kullanıcı prompt'u otomatik olarak en uygun ajana (Claude Code veya Codex CLI) yönlendirilir.

### Temel Prensipler

| Prensip | Açıklama |
|---------|----------|
| **Deterministik Yürütme** | Aynı girdi → aynı çıktı |
| **Fail-Fast** | Hata anında dur, düzelt, devam et |
| **Observable** | Her adım trace edilir |
| **Self-Healing** | Hatalardan otomatik kurtarma |
| **Cost-Aware** | Maliyet/fayda optimizasyonu |

---

## 2. Mimari Katmanlar

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGSMITH OBSERVABILITY                      │
│         (Trace, Success Rate, Time-to-Green, Cost)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATION                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Yaratıcı   │→ │    Meta     │→ │      Ajan Fabrikası     │ │
│  │   Zihin     │  │ Orkestratör │  │  (7 uzman ajan tipi)    │ │
│  │ (sadece     │  │(deterministik│  │                         │ │
│  │  plan üretir)│  │  yürütme)   │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      QUALITY GATES LAYER                        │
│     Lint → TypeCheck → UnitTest → Integration → Security       │
│              (zorunlu sıra, fail → fix loop)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    POLICY-DRIVEN ROUTING                        │
│  Görev türü (%30) + Risk (%25) + Diff (%20) + Geçmiş (%25)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────┬─────────────────────────────────────┐
│      LLM LAYER            │       TOOL EXECUTION LAYER          │
│      (LiteLLM)            │         (MCP / Sandbox)             │
│  ┌─────────────────────┐  │  ┌─────────────────────────────┐   │
│  │ Claude Opus/Sonnet  │  │  │ Codex CLI                   │   │
│  │ GPT-4o              │  │  │ Shell (bash/powershell)     │   │
│  │ Qwen3-8B (Turkish)  │  │  │ Git operations              │   │
│  └─────────────────────┘  │  │ Test runners                │   │
│                           │  │ Filesystem                  │   │
│                           │  └─────────────────────────────┘   │
└───────────────────────────┴─────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOOP GUARDRAILS                            │
│  No-progress detector │ Diff/Scope limitleri │ Circuit breaker │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STATE & MEMORY                            │
│  STATE (Redis)              │  MEMORY (PostgreSQL + S3)        │
│  - Kısa ömürlü              │  - Kalıcı                        │
│  - Gerçeklik kaynağı        │  - Sadece öneri verir            │
│  - Kod kararları buradan    │  - Lessons learned               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. LangGraph Rolleri

### 3.1 Yaratıcı Zihin (Creative Mind)

**Görev:** Sadece plan üretir, asla kod yazmaz.

**Giriş:** Kullanıcı prompt'u + bağlam  
**Çıkış:** Yapılandırılmış plan (şema zorunlu)

**Plan Şeması:**
```
{
  "task_id": "uuid",
  "description": "string",
  "steps": [
    {
      "order": 1,
      "action": "create|modify|delete|test",
      "target": "file/path",
      "agent_type": "FrontendBuilder|BackendBuilder|...",
      "estimated_lines": 50,
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
    }
  ],
  "success_criteria": ["test passes", "lint clean"],
  "rollback_plan": "git reset --hard HEAD~1"
}
```

### 3.2 Meta Orkestratör

**Görev:** Planı deterministik olarak yürütür.

**Sorumluluklar:**
- Adım sıralaması
- Ajan atama
- Quality Gate kontrolü
- Hata durumunda karar

**Karar Ağacı:**
```
Plan al
  ↓
Her adım için:
  ├── Routing kararı (Policy Matrix)
  ├── Ajan spawn et
  ├── Sonucu bekle
  ├── Quality Gate kontrolü
  │     ├── PASS → Sonraki adım
  │     └── FAIL → Fix loop (max 3)
  │           ├── Deneme 1: Otomatik düzelt
  │           ├── Deneme 2: Strateji değiştir
  │           └── Deneme 3: BLOCKED → İnsan
  └── Tamamlandı → MEMORY'ye kaydet
```

### 3.3 Ajan Fabrikası

**Görev:** Uzman ajanları spawn/terminate eder.

**7 Ajan Tipi:**

| Ajan | Uzmanlık | Varsayılan Model |
|------|----------|------------------|
| **OCRMatcher** | Soru-cevap eşleştirme | Claude Opus |
| **Validator** | Veri doğrulama | Claude Sonnet |
| **FrontendBuilder** | React/TypeScript | Codex CLI |
| **BackendBuilder** | FastAPI/Python | Codex CLI |
| **TestWriter** | pytest/jest | Codex CLI |
| **SecurityAuditor** | Güvenlik taraması | Claude Opus |
| **Refactorer** | Kod iyileştirme | Claude Opus |

**Spawn Kuralları:**
- Tek iş per ajan (Single Responsibility)
- İş bitince terminate
- Max 5 paralel ajan
- Kaynak limitleri zorunlu

---

## 4. Quality Gates Layer

### Gate Sırası (Zorunlu)

```
┌──────────┐   ┌───────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
│   LINT   │ → │ TYPECHECK │ → │ UNITTEST │ → │ INTEGRATION │ → │ SECURITY │
│  ruff/   │   │  mypy/    │   │ pytest/  │   │   API/DB    │   │  bandit/ │
│  eslint  │   │  tsc      │   │  jest    │   │   tests     │   │  semgrep │
└──────────┘   └───────────┘   └──────────┘   └─────────────┘   └──────────┘
```

### Her Gate için Kurallar

| Durum | Aksiyon |
|-------|---------|
| **PASS** | Sonraki gate'e geç |
| **FAIL (1. deneme)** | Otomatik düzeltme dene |
| **FAIL (2. deneme)** | Strateji değiştir (minimal scope) |
| **FAIL (3. deneme)** | **BLOCKED** - İnsan müdahalesi |

### Gate Konfigürasyonu

```
quality_gates:
  lint:
    tools: ["ruff", "eslint"]
    auto_fix: true
    max_retries: 3
    
  typecheck:
    tools: ["mypy --strict", "tsc --noEmit"]
    auto_fix: false
    max_retries: 3
    
  unittest:
    tools: ["pytest -x", "jest --bail"]
    coverage_threshold: 80
    max_retries: 3
    
  integration:
    tools: ["pytest tests/integration/"]
    timeout: 300
    max_retries: 2
    
  security:
    tools: ["bandit", "semgrep", "npm audit"]
    severity_threshold: "medium"
    max_retries: 1
```

---

## 5. Policy-Driven Routing

### Routing Matrisi

| Faktör | Ağırlık | Açıklama |
|--------|---------|----------|
| **Görev Türü** | %30 | Frontend, Backend, NLP, Security |
| **Risk Seviyesi** | %25 | LOW, MEDIUM, HIGH, CRITICAL |
| **Diff Tahmini** | %20 | Satır sayısı, dosya sayısı |
| **Geçmiş Başarı** | %25 | Bu tip görevdeki success rate |

### Görev Türü → Model Eşleştirme

| Görev Türü | Birincil | Yedek | Sebep |
|------------|----------|-------|-------|
| Türkçe NLP | Claude Opus | Qwen3-8B | Türkçe anlama |
| Security | Claude Opus | GPT-4o | Kritik analiz |
| Kompleks Refactor | Claude Opus | Claude Sonnet | Bağlam koruma |
| React Component | Codex CLI | Claude Sonnet | Hız + maliyet |
| API Endpoint (CRUD) | Codex CLI | Claude Sonnet | Şablon bazlı |
| Unit Test | Codex CLI | GPT-4o | Pattern matching |
| Dokümantasyon | Codex CLI | Claude Sonnet | Hız |

### Risk Seviyeleri

| Seviye | Dosya Pattern'leri | Gereklilik |
|--------|-------------------|------------|
| **CRITICAL** | `/backend/app/core/security/*`, `/backend/alembic/*`, `*.env*`, `*migration*` | İnsan onayı |
| **HIGH** | `/backend/app/core/config.py`, `docker-compose.yml` | Ekstra review |
| **MEDIUM** | `/backend/app/api/*`, `/backend/app/services/*` | Normal flow |
| **LOW** | `/frontend/src/components/*`, `/tests/*`, `*.md` | Hızlı işlem |

### Routing Karar Akışı

```
Yeni görev geldi
      │
      ▼
┌─────────────────┐
│ Görev analizi   │
│ - Tür belirleme │
│ - Risk tahmini  │
│ - Diff tahmini  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Geçmiş kontrol  │
│ - Bu tip görev  │
│ - Başarı oranı  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Skor hesapla    │
│ Σ(faktör×ağırlık)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Model/Tool seç  │
│ - En yüksek skor│
│ - Yedek belirle │
└─────────────────┘
```

---

## 6. Loop Guardrails

### 6.1 No-Progress Detector

**Error Fingerprint Hesaplama:**
```
fingerprint = hash(test_name + error_line + error_type)
```

**Tekrar Sayısına Göre Aksiyon:**

| Tekrar | Aksiyon |
|--------|---------|
| 1 | Fingerprint kaydet, normal düzeltme |
| 2 | **UYARI**, strateji değiştirmeyi düşün |
| 3 | **Strateji değiştir**: minimal patch, scope küçült, farklı model |
| 4 | **BLOCKED**, insan müdahalesi gerekli |

### 6.2 Diff/Scope Limitleri

| Limit | Değer | Aşım Durumunda |
|-------|-------|----------------|
| **Tek iterasyonda max dosya** | 5 | Otomatik parçalama |
| **Tek iterasyonda max satır** | 200 | Plan revizyonu |
| **Toplam görevde max satır** | 500 | Alt görevlere böl |

### 6.3 Circuit Breaker

**Tetikleyiciler:**
- 3 ardışık BLOCKED
- Error rate > %50 (son 10 görev)
- Timeout > 5 dakika

**Aksiyon:**
- Tüm aktif görevleri duraklat
- Alert gönder
- Manuel reset bekle

### Loop Guardrails Akış

```
Görev başladı
      │
      ▼
┌─────────────────┐
│ İterasyon #N    │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Sonuç?  │
    └────┬────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
  PASS  FAIL  TIMEOUT
    │    │      │
    │    ▼      ▼
    │  ┌──────────────┐
    │  │ Fingerprint  │
    │  │ kontrol      │
    │  └──────┬───────┘
    │         │
    │    ┌────┴────┐
    │    │ Kaçıncı?│
    │    └────┬────┘
    │    ┌─┬──┴──┬─┐
    │    ▼ ▼    ▼ ▼
    │   1-2  3   4+
    │    │   │   │
    │    ▼   ▼   ▼
    │  Retry Strateji BLOCKED
    │         değiş
    │           │
    │      ┌────┴────┐
    │      │Diff/Scope│
    │      │ kontrol  │
    │      └────┬────┘
    │           │
    │      ┌────┴────┐
    │      │ Limit   │
    │      │ aşıldı? │
    │      └────┬────┘
    │      NO   │  YES
    │       │   │   │
    │       ▼   │   ▼
    │    Devam  │  Parçala
    │       │   │   │
    └───────┴───┴───┘
            │
            ▼
      Sonraki adım
```

---

## 7. State & Memory Ayrımı

### STATE (Redis)

**Özellikler:**
- Kısa ömürlü (TTL: 24 saat)
- **Gerçeklik kaynağı** - Kod kararları buradan
- Mutable

**İçerik:**
```
state:{task_id}:
  status: "running|completed|blocked|failed"
  current_step: 3
  files_modified: ["src/App.tsx", "src/api.ts"]
  error_fingerprints: {"abc123": 2, "def456": 1}
  iteration_count: 2
  last_checkpoint: "commit_sha"
```

### MEMORY (PostgreSQL + S3)

**Özellikler:**
- Kalıcı
- **Sadece öneri verir** - Kod asla MEMORY'den karar almaz
- Append-only (geçmiş silinmez)

**İçerik:**
```
lessons_learned:
  - task_type: "react_component"
    pattern: "useState hook for forms"
    success_rate: 0.95
    avg_iterations: 1.2
    
  - task_type: "turkish_nlp"
    pattern: "zemberek for morphology"
    success_rate: 0.88
    avg_iterations: 2.1
    
strategy_history:
  - strategy_id: "minimal_patch_v2"
    win_rate: 0.82
    use_count: 150
```

### Kritik Kural

```
                    ┌─────────────┐
                    │   MEMORY    │
                    │ (PostgreSQL)│
                    └──────┬──────┘
                           │
                     "Bu tip görevde
                      şu strateji iyi
                      çalışmış" (öneri)
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│                META ORKESTRATÖR                  │
│                                                  │
│  Kararlar STATE'e dayanır:                       │
│  - Mevcut durum nedir?                           │
│  - Kaç iterasyon oldu?                           │
│  - Hangi dosyalar değişti?                       │
│                                                  │
│  MEMORY sadece öneri:                            │
│  - Geçmişte ne işe yaradı?                       │
│  - Hangi patternler başarılı?                    │
│                                                  │
└──────────────────────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    STATE    │
                    │   (Redis)   │
                    └─────────────┘
```

---

## 8. LangSmith Observability

### Zorunlu Metrikler

| Metrik | Açıklama | Hedef |
|--------|----------|-------|
| **Success Rate** | Başarılı görev / Toplam görev | >90% |
| **Time-to-Green** | İlk deneme → Tüm testler geçti | <3 iterasyon |
| **Cost-per-Success** | Başarılı görev başına maliyet | <$0.50 |
| **Loop Rate** | 3+ iterasyon gereken görevler | <5% |
| **Rollback Rate** | Geri alınan değişiklikler | <10% |

### Trace Yapısı

```
trace:
  run_id: "uuid"
  task_id: "uuid"
  user_prompt: "string"
  
  steps:
    - step: 1
      agent: "FrontendBuilder"
      model: "codex-cli"
      input: {...}
      output: {...}
      duration_ms: 1234
      tokens_used: 500
      cost: 0.02
      
    - step: 2
      agent: "TestWriter"
      ...
      
  quality_gates:
    lint: {status: "pass", duration_ms: 200}
    typecheck: {status: "pass", duration_ms: 500}
    unittest: {status: "fail", attempts: 2, final: "pass"}
    
  final_status: "completed"
  total_cost: 0.15
  total_duration_ms: 45000
```

### Dashboard Görünümü

```
┌─────────────────────────────────────────────────────────────────┐
│                   KIRO2 ORCHESTRATOR DASHBOARD                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SUCCESS RATE        TIME-TO-GREEN       COST-PER-SUCCESS      │
│  ┌─────────────┐    ┌─────────────┐     ┌─────────────┐        │
│  │    92%      │    │    1.8      │     │   $0.32     │        │
│  │    ▲ +3%    │    │  iterations │     │    ▼ -15%   │        │
│  └─────────────┘    └─────────────┘     └─────────────┘        │
│                                                                 │
│  LOOP RATE           BLOCKED             ACTIVE TASKS          │
│  ┌─────────────┐    ┌─────────────┐     ┌─────────────┐        │
│  │    4.2%     │    │      1      │     │      3      │        │
│  │    ▼ -1%    │    │   pending   │     │   running   │        │
│  └─────────────┘    └─────────────┘     └─────────────┘        │
│                                                                 │
│  RECENT TASKS                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✓ Create QuestionCard component    1 iter   $0.12  2min │   │
│  │ ✓ Add /api/progress endpoint       2 iter   $0.28  4min │   │
│  │ ⚠ Fix OCR matching logic           3 iter   $0.45  8min │   │
│  │ ✗ Migrate auth to Zustand          BLOCKED  $0.60  ---  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Regression Test Seti

20 KIRO2-spesifik benchmark görev:

| # | Görev | Beklenen |
|---|-------|----------|
| 1 | Basit React component | 1 iter, <$0.15 |
| 2 | CRUD API endpoint | 1 iter, <$0.20 |
| 3 | Unit test yazma | 1 iter, <$0.10 |
| 4 | Türkçe NLP işleme | 2 iter, <$0.50 |
| 5 | Security fix | 2 iter, <$0.40 |
| ... | ... | ... |

---

## 9. Güvenlik Modeli

### 9.1 Tool Allowlist

**İZİN VERİLEN:**
```
git: [add, commit, push, pull, checkout, branch, merge, status, diff, log]
npm: [install, run, test, build]
pytest: [*]
ruff: [check, format, --fix]
eslint: [*, --fix]
docker: [build, run, stop, ps, logs]
```

**YASAKLI:**
```
rm: [-rf, -r (system dirs)]
curl: [* (dış URL'ler)]
wget: [*]
git: [push --force, reset --hard (without backup)]
sql: [DROP, TRUNCATE, DELETE without WHERE]
```

### 9.2 İnceleme Gerektiren Durumlar

| Durum | Gereklilik |
|-------|------------|
| `/backend/app/core/security/*` değişikliği | İnsan onayı |
| `/backend/alembic/*` değişikliği | İnsan + Test |
| `*.env*` okuma/yazma | **YASAK** |
| >500 satır değişiklik | Plan revizyonu |
| Yeni dependency ekleme | Güvenlik taraması |

### 9.3 Secret Filtering

**Maskelenen Patternler:**
```
API_KEY=sk-xxx... → API_KEY=***MASKED***
password: "123" → password: "***MASKED***"
JWT: eyJhbG... → JWT: ***MASKED***
```

**Asla Loglama:**
- `.env` dosya içerikleri
- API anahtarları
- Şifreler
- Token'lar

### 9.4 Merge Policy

| Değişiklik Boyutu | Merge Şekli |
|-------------------|-------------|
| <50 satır | Otomatik merge |
| 50-200 satır | Ajan review sonrası |
| >200 satır | İnsan review zorunlu |
| CRITICAL dosya | Her zaman insan onayı |

---

## 10. Tam Akış Örneği

### Senaryo: "React ile soru kartı komponenti oluştur"

```
KULLANICI: "React ile soru kartı komponenti oluştur"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ YARATICI ZİHİN                                                  │
│                                                                 │
│ Plan üretir:                                                    │
│ {                                                               │
│   "steps": [                                                    │
│     {"order": 1, "action": "create",                           │
│      "target": "src/components/QuestionCard/types.ts",         │
│      "agent": "FrontendBuilder", "lines": 15},                 │
│     {"order": 2, "action": "create",                           │
│      "target": "src/components/QuestionCard/index.tsx",        │
│      "agent": "FrontendBuilder", "lines": 45},                 │
│     {"order": 3, "action": "create",                           │
│      "target": "src/components/QuestionCard/styles.ts",        │
│      "agent": "FrontendBuilder", "lines": 20},                 │
│     {"order": 4, "action": "create",                           │
│      "target": "src/components/QuestionCard/QuestionCard.test.tsx",│
│      "agent": "TestWriter", "lines": 30}                       │
│   ],                                                            │
│   "success_criteria": ["lint pass", "typecheck pass", "test pass"]│
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ META ORKESTRATÖR                                                │
│                                                                 │
│ Routing kararı:                                                 │
│ - Görev türü: Frontend (%30)                                    │
│ - Risk seviyesi: LOW (%25)                                      │
│ - Diff tahmini: <100 satır (%20)                               │
│ - Geçmiş başarı: %92 (%25)                                     │
│                                                                 │
│ Sonuç: CODEX CLI seçildi                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ AJAN FABRİKASI                                                  │
│                                                                 │
│ FrontendBuilder spawn edildi                                    │
│ - Model: Codex CLI                                              │
│ - Timeout: 60s                                                  │
│ - Memory limit: 512MB                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ FrontendBuilder ÇALIŞIYOR                                       │
│                                                                 │
│ İterasyon 1:                                                    │
│ - types.ts oluşturuldu (15 satır)                              │
│ - index.tsx oluşturuldu (45 satır)                             │
│ - styles.ts oluşturuldu (20 satır)                             │
│                                                                 │
│ Toplam: 80 satır, 3 dosya                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ QUALITY GATES                                                   │
│                                                                 │
│ [✓] Lint (ruff/eslint)     - 0.3s - PASS                       │
│ [✓] TypeCheck (tsc)        - 1.2s - PASS                       │
│ [✓] Security (semgrep)     - 0.5s - PASS                       │
│                                                                 │
│ Tüm gate'ler geçti!                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ TestWriter ÇALIŞIYOR                                            │
│                                                                 │
│ QuestionCard.test.tsx oluşturuldu (30 satır)                   │
│ pytest çalıştırıldı: 4 test PASS                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ SONUÇ                                                           │
│                                                                 │
│ Status: COMPLETED                                               │
│ İterasyon: 2                                                    │
│ Maliyet: $0.12                                                  │
│ Süre: 45 saniye                                                 │
│                                                                 │
│ MEMORY'ye kaydedildi:                                           │
│ - Pattern: "QuestionCard component structure"                   │
│ - Success: true                                                 │
│ - Lesson: "Codex CLI for simple React components"              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Hata Senaryosu Örneği

### Senaryo: test_matching.py sürekli fail

```
İTERASYON 1:
├── FIX: OCRMatcher match_threshold değiştirildi
├── TEST: pytest tests/test_matching.py
├── SONUÇ: FAIL - AssertionError at line 45
├── FINGERPRINT: hash("test_matching.py" + "45" + "AssertionError") = "abc123"
└── AKSİYON: Fingerprint kaydedildi, retry

İTERASYON 2:
├── FIX: fuzzy_ratio threshold artırıldı
├── TEST: pytest tests/test_matching.py
├── SONUÇ: FAIL - AssertionError at line 45 (AYNI HATA!)
├── FINGERPRINT: "abc123" (2. kez görüldü)
└── AKSİYON: ⚠️ UYARI - Strateji değiştir

İTERASYON 3:
├── STRATEJİ DEĞİŞİKLİĞİ: Minimal patch, scope küçült
├── FIX: Sadece match_threshold değiştirildi (tek satır)
├── TEST: pytest tests/test_matching.py
├── SONUÇ: FAIL - AssertionError at line 45 (AYNI HATA!)
├── FINGERPRINT: "abc123" (3. kez görüldü)
└── AKSİYON: Farklı model dene (Claude Opus → GPT-4o)

İTERASYON 4:
├── MODEL: GPT-4o
├── FIX: Farklı yaklaşım denendi
├── TEST: pytest tests/test_matching.py
├── SONUÇ: FAIL - AssertionError at line 45 (AYNI HATA!)
├── FINGERPRINT: "abc123" (4. kez görüldü)
└── AKSİYON: 🛑 BLOCKED - İnsan müdahalesi gerekli

FINAL STATUS: BLOCKED
├── Sebep: No-progress detected (4 identical failures)
├── Son fingerprint: "abc123"
├── Denenen modeller: [Codex CLI, Claude Opus, GPT-4o]
├── Denenen stratejiler: [normal, minimal_patch, different_model]
└── Bekleyen: İnsan müdahalesi
```

---

## 12. Uygulama Yol Haritası

### Faz 1: Temel Altyapı (Hafta 1-2)

| Görev | Çıktı |
|-------|-------|
| LangGraph kurulumu | Temel graph yapısı |
| LangSmith entegrasyonu | Trace aktif |
| LiteLLM konfigürasyonu | Model routing |
| Redis + PostgreSQL | State/Memory ayrımı |

**Başarı Kriterleri:**
- [x] Basit görev tamamlama: %70+
- [x] Tüm adımlar trace ediliyor: %100
- [x] Yanıt süresi: <30 saniye

### Faz 2: Quality Gates (Hafta 3)

| Görev | Çıktı |
|-------|-------|
| Lint gate | ruff + eslint entegrasyonu |
| TypeCheck gate | mypy + tsc entegrasyonu |
| Test gate | pytest + jest entegrasyonu |
| Security gate | bandit + semgrep |

**Başarı Kriterleri:**
- [x] Gate'ler sıralı çalışıyor
- [x] Auto-fix aktif
- [x] Max 3 retry kuralı

### Faz 3: Loop Guardrails (Hafta 4)

| Görev | Çıktı |
|-------|-------|
| Error fingerprinting | Hash tabanlı tespit |
| No-progress detector | 4. tekrarda BLOCKED |
| Diff/Scope limitleri | Max 5 dosya, 200 satır |
| Circuit breaker | Cascade failure koruması |

**Başarı Kriterleri:**
- [x] Quality Gates geçiş: %80+
- [x] Loop rate: <%10
- [x] BLOCKED rate: <%5

### Faz 4: Ajan Fabrikası (Hafta 5-6)

| Görev | Çıktı |
|-------|-------|
| 7 ajan şablonu | Template library |
| Spawn/terminate mantığı | Lifecycle manager |
| Routing matrisi | Policy engine |
| Paralel execution | Max 5 ajan |

**Başarı Kriterleri:**
- [x] Doğru ajan seçimi: %90+
- [x] Kaynak limitleri çalışıyor
- [x] Paralel görevler stabil

### Faz 5: Yaratıcı Zihin (Hafta 7-8)

| Görev | Çıktı |
|-------|-------|
| Plan üretme | Şema zorunlu |
| Strateji öğrenme | MEMORY entegrasyonu |
| Öz-evrim | Parametre optimizasyonu |
| Yeni ajan üretimi | Genetik operatörler |

**Başarı Kriterleri:**
- [x] Success rate: %90+
- [x] Time-to-Green: <3 iterasyon
- [x] Cost-per-Success: <$0.50
- [x] İnsan müdahalesi: <1/gün
- [x] Otonom çalışma: >4 saat

---

## 13. Sonuç

Bu mimari dokümanı, KIRO2 platformu için tam otonom orkestratör sisteminin tüm bileşenlerini tanımlar:

✅ **LangGraph Rolleri:** Yaratıcı Zihin (plan), Meta Orkestratör (yürütme), Ajan Fabrikası (uzmanlar)

✅ **Quality Gates:** Zorunlu sıralı kontroller, auto-fix, max 3 retry

✅ **Loop Guardrails:** Error fingerprinting, no-progress detection, diff limitleri

✅ **Policy-Driven Routing:** Görev türü + risk + diff + geçmiş başarı

✅ **State vs Memory:** Redis (gerçeklik kaynağı) ≠ PostgreSQL (öneri)

✅ **Güvenlik:** Tool allowlist, secret filtering, merge policy

✅ **Observability:** LangSmith trace, success rate, cost tracking

---

**Sonraki Adım:** Faz 1 uygulamasına başla.
