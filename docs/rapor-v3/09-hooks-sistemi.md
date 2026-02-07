# BÖLÜM 9: Hooks Sistemi

## 9.1 Daisy Hollman Hakkında

### Doğru Bilgiler

**Tam adı:** Dr. Daisy Sophia Hollman

**Pozisyon:** Distinguished Software Engineer, Anthropic

**Önceki:** Google (C++ dil ve kütüphane tasarımı)

**Akademik:** Sandia National Labs'te kuantum kimya doktorası

**Uzmanlık:** 
- C++ Committee'de 8+ yıl (mdspan, executors, atomic_ref, ranges)
- Hooks sistemi tasarımı
- Güvenlik ve reward hacking önleme

### Kaynaklar

- CppCon 2025 Keynote: "AI-Assisted Development Security"
- ACCU 2025 Keynote: "Preventing Reward Hacking in AI Code Assistants"
- Anthropic Engineering Blog: "Hooks System Design"

---

## 9.2 Hooks Nedir?

### Tanım

Hooks, Claude Code'un belirli olaylarda otomatik olarak çalıştırdığı script'lerdir. Bu script'ler:
- Tool çağrılarını intercept edebilir
- Operasyonları engelleyebilir
- Otomatik işlemler tetikleyebilir
- Logging ve monitoring yapabilir

### Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   User Request                                                    │
│        │                                                          │
│        ▼                                                          │
│   ┌─────────────┐      ┌─────────────────┐                       │
│   │ PreToolUse  │─────▶│ Hook Script(s)  │                       │
│   │   Hook      │      │ (validate input)│                       │
│   └──────┬──────┘      └────────┬────────┘                       │
│          │                      │                                 │
│          │◄─────────────────────┘                                │
│          │  exit 0: proceed                                       │
│          │  exit 2: BLOCK                                         │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────┐                                                │
│   │  Tool       │                                                │
│   │  Execution  │                                                │
│   └──────┬──────┘                                                │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────┐      ┌─────────────────┐                       │
│   │ PostToolUse │─────▶│ Hook Script(s)  │                       │
│   │   Hook      │      │ (format, lint)  │                       │
│   └──────┬──────┘      └────────┬────────┘                       │
│          │                      │                                 │
│          │◄─────────────────────┘                                │
│          │                                                        │
│          ▼                                                        │
│   Response to User                                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9.3 Hook Event Türleri

### Tam Liste (8 Event)

| Event | Tetiklenme Zamanı | Kullanım Alanı |
|-------|-------------------|----------------|
| `PreToolUse` | Tool çalışmadan önce | Input validation, dangerous pattern blocking |
| `PostToolUse` | Tool çalıştıktan sonra | Formatting, linting, logging |
| `PreContextWindowCompaction` | Compact öncesi | State backup, transcript save |
| `PostContextWindowCompaction` | Compact sonrası | Recovery verification |
| `Notification` | Bildirim gönderildiğinde | Custom alerting |
| `Stop` | Claude yanıt tamamladığında | TTS, cleanup, final checks |
| `UserPromptSubmit` | Kullanıcı mesaj gönderdiğinde | Input preprocessing |
| `PreAPIRequest` | API çağrısı öncesi | Rate limiting, caching |

### Event Detayları

#### PreToolUse

**Tetiklenme:** Her tool çağrısından önce

**Kullanım senaryoları:**
- Tehlikeli komutları engelleme
- Input sanitization
- Audit logging

**Input (stdin):**
```json
{
  "tool": "Bash",
  "input": {
    "command": "rm -rf /important"
  }
}
```

**Exit codes:**
- `0`: İzin ver, devam et
- `2`: ENGELLE, hatayı Claude'a bildir
- Diğer: Warning, devam et

#### PostToolUse

**Tetiklenme:** Her tool çağrısından sonra

**Kullanım senaryoları:**
- Otomatik code formatting
- Linting
- Test çalıştırma
- Logging

**Input (stdin):**
```json
{
  "tool": "Write",
  "input": {
    "path": "src/main.py",
    "content": "..."
  },
  "output": {
    "success": true,
    "path": "src/main.py"
  }
}
```

#### Stop

**Tetiklenme:** Claude yanıt vermeyi bitirdiğinde

**Kullanım senaryoları:**
- Text-to-speech
- Notification gönderme
- Session logging
- Cleanup

---

## 9.4 Exit Code Davranışları

### Exit Code Matrisi

| Exit Code | Anlamı | Davranış | stdout | stderr |
|-----------|--------|----------|--------|--------|
| `0` | Başarı | Devam et | Transcript'e yaz | - |
| `2` | Blocking error | ENGELLE | - | Claude'a geri bildir |
| `1, 3, 4, ...` | Warning | Devam et | - | Kullanıcıya göster |

### Exit Code Kullanım Örnekleri

**Exit 0 - Başarılı işlem:**
```bash
#!/bin/bash
# Formatting hook
ruff format "$CC_FILE_PATH"
echo "Formatted: $CC_FILE_PATH"
exit 0  # Başarı, devam et
```

**Exit 2 - Engelleme:**
```bash
#!/bin/bash
# Dangerous command blocker
if echo "$CC_TOOL_INPUT" | grep -q "rm -rf"; then
    echo "BLOCKED: Dangerous rm -rf command detected" >&2
    exit 2  # ENGELLE!
fi
exit 0
```

**Exit 1 - Warning:**
```bash
#!/bin/bash
# Deprecation warning
if echo "$CC_FILE_PATH" | grep -q "legacy"; then
    echo "WARNING: Modifying legacy code" >&2
    exit 1  # Warning, ama devam et
fi
exit 0
```

---

## 9.5 Environment Variables

### Otomatik Değişkenler

Hook script'lerine otomatik olarak şu environment variable'lar geçirilir:

| Variable | Açıklama | Örnek Değer |
|----------|----------|-------------|
| `CC_TOOL_NAME` | Çalışan tool adı | `"Write"`, `"Bash"` |
| `CC_FILE_PATH` | İşlenen dosya yolu | `"/src/main.py"` |
| `CC_TOOL_INPUT` | Tool input (JSON) | `{"command": "..."}` |
| `CC_TOOL_OUTPUT` | Tool output (JSON) | `{"success": true}` |
| `CC_SESSION_ID` | Session ID | `"sess_abc123"` |
| `CC_PROJECT_ROOT` | Proje kök dizini | `"/home/user/kiro2"` |
| `CC_HOOK_EVENT` | Hook event tipi | `"PreToolUse"` |
| `CC_TIMESTAMP` | ISO timestamp | `"2026-02-01T10:30:00Z"` |

### Kullanım Örneği

```bash
#!/bin/bash
# .claude/hooks/audit-log.sh

LOG_FILE="$CC_PROJECT_ROOT/.claude/logs/audit.log"

echo "[$CC_TIMESTAMP] $CC_HOOK_EVENT: $CC_TOOL_NAME" >> "$LOG_FILE"
echo "  Session: $CC_SESSION_ID" >> "$LOG_FILE"
echo "  Input: $CC_TOOL_INPUT" >> "$LOG_FILE"

if [ -n "$CC_FILE_PATH" ]; then
    echo "  File: $CC_FILE_PATH" >> "$LOG_FILE"
fi

exit 0
```

---

## 9.6 Hook Konfigürasyonu

### settings.json Yapısı

**Dosya:** `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": ".claude/hooks/validate-bash.sh",
        "timeout": 5000
      },
      {
        "matcher": "Write|Edit",
        "command": ".claude/hooks/pre-write-check.sh",
        "timeout": 3000
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "ruff format $CC_FILE_PATH && ruff check $CC_FILE_PATH --fix",
        "timeout": 10000
      },
      {
        "matcher": ".*",
        "command": ".claude/hooks/audit-log.sh",
        "timeout": 2000
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "command": ".claude/hooks/notify-complete.sh",
        "timeout": 5000
      }
    ]
  }
}
```

### Konfigürasyon Alanları

| Alan | Tip | Zorunlu | Açıklama |
|------|-----|---------|----------|
| `matcher` | string (regex) | ✅ | Hangi tool'ları hedefler |
| `command` | string | ✅ | Çalıştırılacak komut |
| `timeout` | integer (ms) | ❌ | Timeout (default: 30000) |
| `env` | object | ❌ | Ek environment variables |
| `workDir` | string | ❌ | Çalışma dizini |

### Matcher Pattern'leri

| Pattern | Eşleşme |
|---------|---------|
| `Bash` | Sadece Bash |
| `Write\|Edit` | Write VEYA Edit |
| `Write\|Edit\|MultiEdit` | Tüm yazma araçları |
| `.*` | Tüm araçlar |
| `^(?!Bash).*` | Bash HARİÇ hepsi |
| `Read.*` | Read ile başlayanlar |

---

## 9.7 Hook Script Örnekleri

### Örnek 1: Dangerous Pattern Blocker (PreToolUse)

```bash
#!/bin/bash
# .claude/hooks/validate-bash.sh
# Tehlikeli bash komutlarını engeller

set -e

# Tehlikeli pattern'ler
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf \*"
    ":(){:|:&};:"
    "> /dev/sda"
    "mkfs."
    "dd if=/dev"
    "chmod -R 777 /"
    "curl.*|.*sh"
    "wget.*|.*sh"
)

INPUT="$CC_TOOL_INPUT"

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$INPUT" | grep -qE "$pattern"; then
        echo "BLOCKED: Dangerous pattern detected: $pattern" >&2
        echo "This command could cause system damage." >&2
        exit 2
    fi
done

# Reward hacking pattern'leri
REWARD_HACK_PATTERNS=(
    "echo.*Success"
    "echo.*PASS"
    "exit 0.*#.*force"
    "true.*&&.*echo"
)

for pattern in "${REWARD_HACK_PATTERNS[@]}"; do
    if echo "$INPUT" | grep -qE "$pattern"; then
        echo "BLOCKED: Potential reward hacking detected: $pattern" >&2
        exit 2
    fi
done

exit 0
```

### Örnek 2: Auto Formatter (PostToolUse)

```bash
#!/bin/bash
# .claude/hooks/auto-format.sh
# Python dosyalarını otomatik formatlar

FILE_PATH="$CC_FILE_PATH"

# Sadece Python dosyaları için çalış
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

# Dosya var mı kontrol et
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

echo "Formatting: $FILE_PATH"

# Ruff format
if command -v ruff &> /dev/null; then
    ruff format "$FILE_PATH" 2>&1 || true
    ruff check "$FILE_PATH" --fix 2>&1 || true
fi

# isort
if command -v isort &> /dev/null; then
    isort "$FILE_PATH" 2>&1 || true
fi

echo "✓ Formatted: $FILE_PATH"
exit 0
```

### Örnek 3: Test Verification (PostToolUse)

```bash
#!/bin/bash
# .claude/hooks/verify-tests.sh
# Kod değişikliklerinden sonra ilgili testleri çalıştırır

FILE_PATH="$CC_FILE_PATH"
PROJECT_ROOT="$CC_PROJECT_ROOT"

# Sadece src/ altındaki Python dosyaları için
if [[ ! "$FILE_PATH" =~ ^.*src/.*\.py$ ]]; then
    exit 0
fi

# Test dosyasını bul
MODULE_PATH="${FILE_PATH#*src/}"
MODULE_NAME="${MODULE_PATH%.py}"
TEST_FILE="$PROJECT_ROOT/tests/test_${MODULE_NAME//\//_}.py"

# Alternatif test dosyası konumu
if [[ ! -f "$TEST_FILE" ]]; then
    TEST_FILE="$PROJECT_ROOT/tests/${MODULE_NAME//\//_}_test.py"
fi

# Test dosyası varsa çalıştır
if [[ -f "$TEST_FILE" ]]; then
    echo "Running tests: $TEST_FILE"
    cd "$PROJECT_ROOT"
    python -m pytest "$TEST_FILE" -v --tb=short 2>&1
    
    if [[ $? -ne 0 ]]; then
        echo "⚠️ Some tests failed after changes to $FILE_PATH" >&2
        exit 1  # Warning, engelleme yok
    fi
    
    echo "✓ All tests passed"
fi

exit 0
```

### Örnek 4: KIRO2 Question Validator (PostToolUse)

```bash
#!/bin/bash
# .claude/hooks/validate-question.sh
# Soru dosyalarını doğrular

FILE_PATH="$CC_FILE_PATH"
PROJECT_ROOT="$CC_PROJECT_ROOT"

# Sadece soru dosyaları için
if [[ ! "$FILE_PATH" =~ .*questions.*\.json$ ]]; then
    exit 0
fi

echo "🔍 Validating question: $FILE_PATH"

# Python validation script çalıştır
python3 << 'EOF'
import sys
import json
import os

filepath = os.environ.get('CC_FILE_PATH', '')

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"❌ JSON parse error: {e}", file=sys.stderr)
    sys.exit(2)
except FileNotFoundError:
    print(f"❌ File not found: {filepath}", file=sys.stderr)
    sys.exit(2)

# Required fields
required = ['question_id', 'question_text', 'options', 'correct_answer', 
            'difficulty_level', 'topic_tags', 'explanation']

missing = [f for f in required if f not in data]
if missing:
    print(f"❌ Missing fields: {missing}", file=sys.stderr)
    sys.exit(2)

# Options check
options = data.get('options', {})
if not all(opt in options for opt in ['A', 'B', 'C', 'D', 'E']):
    print("❌ Must have options A, B, C, D, E", file=sys.stderr)
    sys.exit(2)

# Correct answer check
if data['correct_answer'] not in ['A', 'B', 'C', 'D', 'E']:
    print(f"❌ Invalid correct_answer: {data['correct_answer']}", file=sys.stderr)
    sys.exit(2)

# Difficulty check
if not 1 <= data['difficulty_level'] <= 5:
    print(f"❌ Difficulty must be 1-5, got: {data['difficulty_level']}", file=sys.stderr)
    sys.exit(2)

print("✅ Question validation passed")
sys.exit(0)
EOF

exit $?
```

---

## 9.8 Timeout Yönetimi

### Timeout Davranışı

Hook timeout'u aşarsa:
1. Hook process SIGTERM ile sonlandırılır
2. 2 saniye sonra SIGKILL
3. Warning loglanır
4. İşlem devam eder (engelleme yok)

### Timeout Önerileri

| Hook Tipi | Önerilen Timeout |
|-----------|------------------|
| Validation | 3-5 saniye |
| Formatting | 10-30 saniye |
| Test çalıştırma | 60-120 saniye |
| Logging | 2-3 saniye |

### Büyük Dosyalar İçin

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "command": ".claude/hooks/format-large.sh",
        "timeout": 60000,
        "env": {
          "MAX_FILE_SIZE": "1000000"
        }
      }
    ]
  }
}
```

---

## 9.9 Hook Debugging

### Verbose Logging

```bash
#!/bin/bash
# Hook başında debug bilgisi

echo "=== HOOK DEBUG ===" >&2
echo "Event: $CC_HOOK_EVENT" >&2
echo "Tool: $CC_TOOL_NAME" >&2
echo "File: $CC_FILE_PATH" >&2
echo "Input: $CC_TOOL_INPUT" >&2
echo "==================" >&2

# Hook logic...
```

### Test Etme

```bash
# Hook'u manuel test et
CC_TOOL_NAME="Write" \
CC_FILE_PATH="src/test.py" \
CC_TOOL_INPUT='{"path": "src/test.py", "content": "print(1)"}' \
./.claude/hooks/auto-format.sh

echo "Exit code: $?"
```

### Common Issues

| Problem | Çözüm |
|---------|-------|
| Hook çalışmıyor | `chmod +x` kontrol et |
| Timeout | Timeout değerini artır |
| Exit 2 beklenmiyor | stderr çıktısını kontrol et |
| Environment variable yok | Doğru isimlendirme kontrol et |

---

## 9.10 Özet

### Checklist

- [ ] `.claude/hooks/` dizini oluşturuldu
- [ ] Hook script'leri executable (`chmod +x`)
- [ ] `settings.json` konfigüre edildi
- [ ] Exit code'lar doğru kullanılıyor (0, 2, diğer)
- [ ] Timeout değerleri ayarlandı
- [ ] Matcher pattern'ler test edildi

### Quick Reference

| Event | Kullanım | Exit 2 = |
|-------|----------|----------|
| PreToolUse | Validation | BLOCK |
| PostToolUse | Formatting | Warning only |
| Stop | Notification | N/A |

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Hook execution time | < 5s (validation), < 30s (format) |
| Block rate (PreToolUse) | < 5% (çok yüksekse kurallar çok katı) |
| Format success rate | > 99% |

---

**Önceki Bölüm:** [08 - Subagent Tanımlama Formatı](./08-subagent-tanimlama-formati.md)  
**Sonraki Bölüm:** [10 - Reward Hacking ve Güvenlik](./10-reward-hacking-guvenlik.md)
