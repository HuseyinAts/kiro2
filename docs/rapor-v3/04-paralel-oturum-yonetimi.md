# BÖLÜM 4: Paralel Oturum Yönetimi

## 4.1 Boris Cherny'nin Çalışma Düzeni

### Orijinal Açıklama

**İngilizce:**
> "I run 5 Claudes in parallel in my terminal. I number my tabs 1-5 and use system notifications to know when Claude wants input. I also run another 5-10 Claudes on claude.ai/code in parallel with my local Claudes."

**Türkçe:**
> "Terminal'de 5 Claude'u paralel çalıştırıyorum. Tab'larımı 1-5 arası numaralandırıyorum ve Claude'un girdi istediğini anlamak için sistem bildirimlerini kullanıyorum. Ayrıca yerel Claude'larımla paralel olarak claude.ai/code'da 5-10 Claude daha çalıştırıyorum."

### Neden Paralel Çalışma?

| Avantaj | Açıklama |
|---------|----------|
| Throughput | 5x daha fazla iş yapılıyor |
| Context isolation | Her görev kendi context'inde |
| Risk dağıtımı | Bir session fail olursa diğerleri devam eder |
| Farklı perspektifler | Aynı soruna farklı yaklaşımlar |
| Bekleme süresini değerlendirme | Claude düşünürken başka görevle ilgilen |

### Örnek İş Akışı

```
Terminal Tab 1: Authentication refactoring
Terminal Tab 2: API endpoint ekleme  
Terminal Tab 3: Unit test yazma
Terminal Tab 4: Documentation güncelleme
Terminal Tab 5: Bug fix

Web Tab 1-5: Code review'lar
Web Tab 6-10: Research ve exploration
```

---

## 4.2 Git Repository İzolasyonu

### Üç Yaklaşım Karşılaştırması

| Yaklaşım | İzolasyon | Disk | Setup | Sync |
|----------|-----------|------|-------|------|
| Git Worktree | Orta | Az | Kolay | Otomatik |
| Git Clone | Tam | Çok | Orta | Manuel |
| Branch + Stash | Düşük | Minimal | Kolay | Riskli |

### Yöntem 1: Git Worktree (Önerilen)

**Avantajlar:**
- Tek .git dizini, çoklu çalışma dizini
- Disk alanı verimli
- Branch tracking otomatik
- Remote ile senkronize

**Kurulum:**
```bash
# Ana repository
cd ~/projects/kiro2

# Worktree'ler oluştur
git worktree add ../kiro2-feature-auth feature/auth
git worktree add ../kiro2-feature-api feature/api
git worktree add ../kiro2-bugfix bugfix/rate-limit
git worktree add ../kiro2-tests tests/integration
git worktree add ../kiro2-docs docs/update

# Sonuç dizin yapısı:
# ~/projects/
# ├── kiro2/              (ana repo)
# ├── kiro2-feature-auth/ (worktree 1)
# ├── kiro2-feature-api/  (worktree 2)
# ├── kiro2-bugfix/       (worktree 3)
# ├── kiro2-tests/        (worktree 4)
# └── kiro2-docs/         (worktree 5)
```

**Worktree yönetimi:**
```bash
# Listele
git worktree list

# Kaldır
git worktree remove ../kiro2-feature-auth

# Prune (silinmiş worktree'leri temizle)
git worktree prune
```

### Yöntem 2: Git Clone (Tam İzolasyon)

Boris'in bahsettiği yöntem bu. Her tab tamamen bağımsız bir clone.

**Avantajlar:**
- Tam izolasyon (ayrı .git)
- Farklı remote'lar mümkün
- Conflict riski sıfır

**Dezavantajlar:**
- Disk alanı: N × repo boyutu
- Manuel senkronizasyon
- Branch tracking yok

**Kurulum:**
```bash
# 5 ayrı clone
cd ~/projects

git clone git@github.com:user/kiro2.git kiro2-1
git clone git@github.com:user/kiro2.git kiro2-2
git clone git@github.com:user/kiro2.git kiro2-3
git clone git@github.com:user/kiro2.git kiro2-4
git clone git@github.com:user/kiro2.git kiro2-5

# Her birinde farklı branch
cd kiro2-1 && git checkout -b feature/auth
cd ../kiro2-2 && git checkout -b feature/api
cd ../kiro2-3 && git checkout -b bugfix/rate-limit
cd ../kiro2-4 && git checkout -b tests/integration
cd ../kiro2-5 && git checkout -b docs/update
```

**Senkronizasyon:**
```bash
# Değişiklikleri main'e merge
cd ~/projects/kiro2-1
git push origin feature/auth

# Ana repo'da merge
cd ~/projects/kiro2
git fetch origin
git merge origin/feature/auth
```

### KIRO2 İçin Önerilen Yapı

```
C:\Users\husey\
├── kiro2\                    # Ana development
├── kiro2-orchestrator\       # Orchestrator geliştirme
├── kiro2-frontend\           # Frontend geliştirme
├── kiro2-content\            # İçerik üretimi
├── kiro2-tests\              # Test yazımı
└── kiro2-experiments\        # Deneysel özellikler
```

---

## 4.3 Terminal Konfigürasyonu

### Windows Terminal (Windows 11)

**Profil ayarları (`settings.json`):**
```json
{
  "profiles": {
    "list": [
      {
        "name": "KIRO2-1 (Orchestrator)",
        "commandline": "powershell.exe -NoExit -Command \"cd C:\\Users\\husey\\kiro2-orchestrator\"",
        "startingDirectory": "C:\\Users\\husey\\kiro2-orchestrator",
        "tabTitle": "1-ORCH",
        "icon": "🔧"
      },
      {
        "name": "KIRO2-2 (Frontend)",
        "commandline": "powershell.exe -NoExit -Command \"cd C:\\Users\\husey\\kiro2-frontend\"",
        "startingDirectory": "C:\\Users\\husey\\kiro2-frontend",
        "tabTitle": "2-FRONT",
        "icon": "🎨"
      },
      {
        "name": "KIRO2-3 (Content)",
        "commandline": "powershell.exe -NoExit -Command \"cd C:\\Users\\husey\\kiro2-content\"",
        "startingDirectory": "C:\\Users\\husey\\kiro2-content",
        "tabTitle": "3-CONT",
        "icon": "📚"
      },
      {
        "name": "KIRO2-4 (Tests)",
        "commandline": "powershell.exe -NoExit -Command \"cd C:\\Users\\husey\\kiro2-tests\"",
        "startingDirectory": "C:\\Users\\husey\\kiro2-tests",
        "tabTitle": "4-TEST",
        "icon": "🧪"
      },
      {
        "name": "KIRO2-5 (Experiments)",
        "commandline": "powershell.exe -NoExit -Command \"cd C:\\Users\\husey\\kiro2-experiments\"",
        "startingDirectory": "C:\\Users\\husey\\kiro2-experiments",
        "tabTitle": "5-EXP",
        "icon": "🔬"
      }
    ]
  }
}
```

### iTerm2 (macOS)

**Profil konfigürasyonu:**
```
iTerm2 → Preferences → Profiles

Profile 1: KIRO2-Orchestrator
  - Working Directory: ~/projects/kiro2-orchestrator
  - Badge: 1-ORCH
  - Tab Color: Blue
  
Profile 2: KIRO2-Frontend
  - Working Directory: ~/projects/kiro2-frontend
  - Badge: 2-FRONT
  - Tab Color: Green
  
...
```

**Bildirim ayarları:**
```
iTerm2 → Preferences → Profiles → [Profile] → Advanced

Triggers:
  Regex: "Claude is waiting for input"
  Action: Post Notification
  
  Regex: "Error:"
  Action: Post Notification + Highlight
```

### tmux (Linux/macOS)

**Session script (`~/.local/bin/kiro2-tmux.sh`):**
```bash
#!/bin/bash

SESSION="kiro2"

# Session varsa bağlan
tmux has-session -t $SESSION 2>/dev/null
if [ $? -eq 0 ]; then
    tmux attach -t $SESSION
    exit 0
fi

# Yeni session oluştur
tmux new-session -d -s $SESSION -n "orchestrator"
tmux send-keys -t $SESSION:orchestrator "cd ~/projects/kiro2-orchestrator && claude" Enter

tmux new-window -t $SESSION -n "frontend"
tmux send-keys -t $SESSION:frontend "cd ~/projects/kiro2-frontend && claude" Enter

tmux new-window -t $SESSION -n "content"
tmux send-keys -t $SESSION:content "cd ~/projects/kiro2-content && claude" Enter

tmux new-window -t $SESSION -n "tests"
tmux send-keys -t $SESSION:tests "cd ~/projects/kiro2-tests && claude" Enter

tmux new-window -t $SESSION -n "experiments"
tmux send-keys -t $SESSION:experiments "cd ~/projects/kiro2-experiments && claude" Enter

# İlk pencereye dön
tmux select-window -t $SESSION:orchestrator

# Bağlan
tmux attach -t $SESSION
```

---

## 4.4 Session Transfer

### /share Komutu

**Kullanım:**
```
> /share
Session shared! Access at: https://claude.ai/share/abc123xyz
```

**Ne paylaşılır:**
- Tüm konuşma geçmişi
- Dosya değişiklikleri (diff)
- Tool çıktıları

**Ne paylaşılmaz:**
- Yerel dosya içerikleri
- API key'ler
- Environment variables

### --resume Flag

**Önceki session'ı devam ettir:**
```bash
# Session ID ile
claude --resume sess_abc123xyz

# Son session'ı
claude --resume last

# Listele
claude --list-sessions
```

### --teleport Flag

**Session'ı cihazlar arası taşı:**
```bash
# Mobilde başlat
# iOS/Android Claude app'te çalış

# Masaüstünde devam et
claude --teleport [session-url]
```

### Session Yönetimi Best Practices

**Adlandırma convention'ı:**
```
[proje]-[modül]-[tarih]-[kısa-açıklama]

Örnekler:
kiro2-auth-20260201-rate-limiting
kiro2-frontend-20260201-dashboard-redesign
kiro2-tests-20260201-integration-coverage
```

**Session metadata:**
```json
// .claude/sessions/kiro2-auth-20260201.json
{
  "id": "sess_abc123",
  "name": "kiro2-auth-20260201-rate-limiting",
  "created": "2026-02-01T10:30:00Z",
  "lastActive": "2026-02-01T14:45:00Z",
  "status": "completed",
  "summary": "Rate limiting threshold 5→10 düzeltildi",
  "files_changed": [
    "src/auth/rate_limiter.py",
    "tests/test_rate_limiter.py"
  ],
  "commits": ["a1b2c3d"]
}
```

---

## 4.5 Çakışma Yönetimi

### Senaryo 1: Aynı Dosyayı Düzenleme

**Problem:**
- Tab 1'deki Claude `src/main.py` düzenliyor
- Tab 2'deki Claude da `src/main.py` düzenliyor
- Git merge conflict!

**Önleme:**
```bash
# Her session başında dosya "kilitle"
echo "src/main.py" >> .claude/locked-files.txt

# Diğer session'larda kontrol
if grep -q "src/main.py" .claude/locked-files.txt; then
    echo "⚠️ Bu dosya başka session'da düzenleniyor!"
fi
```

**Çözüm (conflict oluşursa):**
```bash
# Merge conflict çöz
git checkout --ours src/main.py   # Kendi değişikliklerini al
# veya
git checkout --theirs src/main.py # Diğer değişiklikleri al
# veya
git mergetool                     # Manual merge
```

### Senaryo 2: Dependency Çakışması

**Problem:**
- Tab 1: `pip install numpy==1.24`
- Tab 2: `pip install numpy==1.26`
- Hangi versiyon aktif?

**Önleme:**
```bash
# Her worktree için ayrı virtualenv
python -m venv ~/projects/kiro2-1/.venv
python -m venv ~/projects/kiro2-2/.venv

# Session başında aktifleştir
source ~/projects/kiro2-1/.venv/bin/activate
```

**KIRO2 için setup script:**
```bash
#!/bin/bash
# setup-workspaces.sh

WORKSPACES=("orchestrator" "frontend" "content" "tests" "experiments")
BASE_DIR="C:/Users/husey"

for ws in "${WORKSPACES[@]}"; do
    WS_DIR="$BASE_DIR/kiro2-$ws"
    
    # Dizin yoksa oluştur
    if [ ! -d "$WS_DIR" ]; then
        git clone https://github.com/user/kiro2.git "$WS_DIR"
    fi
    
    # Virtualenv oluştur
    if [ ! -d "$WS_DIR/.venv" ]; then
        python -m venv "$WS_DIR/.venv"
    fi
    
    # Dependencies yükle
    source "$WS_DIR/.venv/Scripts/activate"
    pip install -r "$WS_DIR/requirements.txt"
    deactivate
    
    echo "✓ $ws workspace hazır"
done
```

### Senaryo 3: Port Çakışması

**Problem:**
- Tab 1: `python -m pytest` (port 5000'de test server)
- Tab 3: `python -m pytest` (port 5000 zaten kullanımda!)

**Önleme:**
```python
# conftest.py
import os

# Workspace'e göre port range
workspace_id = int(os.environ.get("WORKSPACE_ID", "0"))
BASE_PORT = 5000 + (workspace_id * 100)

@pytest.fixture
def test_server_port():
    return BASE_PORT
```

**Environment variable ile:**
```bash
# Tab 1
export WORKSPACE_ID=1
claude

# Tab 2
export WORKSPACE_ID=2
claude
```

---

## 4.6 Paralel Claude Stratejileri

### Strateji 1: Görev Bazlı Ayrım

```
Tab 1: Backend development
Tab 2: Frontend development
Tab 3: Testing
Tab 4: Documentation
Tab 5: DevOps / Infrastructure
```

**Avantaj:** Net sorumluluk alanları
**Dezavantaj:** Cross-cutting concern'lerde koordinasyon gerekli

### Strateji 2: Modül Bazlı Ayrım

```
Tab 1: Authentication modülü
Tab 2: Question generation modülü
Tab 3: User management modülü
Tab 4: Analytics modülü
Tab 5: API gateway modülü
```

**Avantaj:** Derin context, az conflict
**Dezavantaj:** Modüller arası entegrasyon zorlaşır

### Strateji 3: Workflow Bazlı Ayrım

```
Tab 1: Planning (Plan Mode)
Tab 2: Implementation
Tab 3: Code Review
Tab 4: Testing
Tab 5: Deployment prep
```

**Avantaj:** CI/CD benzeri akış
**Dezavantaj:** Sequential bottleneck oluşabilir

### KIRO2 İçin Önerilen Strateji

**Hibrit yaklaşım:**
```
Tab 1: Orchestrator core (ana geliştirme)
Tab 2: Subagent development (paralel agent yazımı)
Tab 3: Content pipeline (soru üretimi)
Tab 4: Quality assurance (test + review)
Tab 5: Research & experiments (yeni fikirler)
```

---

## 4.7 Maliyet Yönetimi

### Paralel Session Maliyeti

**Hesaplama:**
```
5 paralel session × 50K token/session = 250K token/cycle

Sonnet 4.5 fiyatı:
- Input: $3/1M token
- Output: $15/1M token

Tipik dağılım (80% input, 20% output):
- Input: 200K × $3/1M = $0.60
- Output: 50K × $15/1M = $0.75
- Toplam: $1.35/cycle

Günde 10 cycle: $13.50/gün
Aylık: ~$400
```

### Maliyet Optimizasyonu

**1. Model seçimi:**
```
Basit görevler: Haiku ($0.25/1M input, $1.25/1M output)
Orta görevler: Sonnet
Kompleks görevler: Opus (sadece gerektiğinde)
```

**2. Context yönetimi:**
```bash
# Her 30 dakikada /clear
# Veya otomatik:
claude --auto-clear-interval 30m
```

**3. Caching:**
```json
// .claude/settings.json
{
  "caching": {
    "enabled": true,
    "promptCache": true,
    "ttl": 3600
  }
}
```

### Bütçe Limitleri

```json
// .claude/settings.json
{
  "budget": {
    "daily": 50,
    "weekly": 250,
    "monthly": 800,
    "alertThreshold": 0.8,
    "hardLimit": true
  }
}
```

**Alert davranışı:**
- %80'e ulaşınca: Warning notification
- %100'e ulaşınca: Session blocked (hardLimit: true ise)

---

## 4.8 Monitoring ve Alerting

### Session Status Dashboard

**Terminal-based (tmux statusbar):**
```bash
# ~/.tmux.conf
set -g status-right '#(~/.local/bin/claude-status.sh)'
```

**claude-status.sh:**
```bash
#!/bin/bash

# Her tab için status
for i in {1..5}; do
    status_file="$HOME/.claude/status-$i.json"
    if [ -f "$status_file" ]; then
        state=$(jq -r '.state' "$status_file")
        case $state in
            "thinking") echo -n "🤔" ;;
            "waiting")  echo -n "⏳" ;;
            "error")    echo -n "❌" ;;
            "done")     echo -n "✅" ;;
        esac
    else
        echo -n "⚫"
    fi
done
```

### Notification System

**macOS:**
```bash
# osascript ile notification
osascript -e 'display notification "Claude needs input" with title "Tab 3"'
```

**Windows (PowerShell):**
```powershell
# BurntToast module
Install-Module -Name BurntToast
New-BurntToastNotification -Text "Claude needs input", "Tab 3"
```

**Linux:**
```bash
# notify-send
notify-send "Claude" "Tab 3 needs input"
```

### Centralized Logging

```python
# orchestrator/monitoring/session_logger.py

import json
from datetime import datetime
from pathlib import Path

class SessionLogger:
    def __init__(self, log_dir: str = "~/.claude/logs"):
        self.log_dir = Path(log_dir).expanduser()
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_event(self, session_id: str, event_type: str, data: dict):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "data": data
        }
        
        log_file = self.log_dir / f"{datetime.now():%Y-%m-%d}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_active_sessions(self) -> list:
        """Aktif session'ları listele."""
        status_files = self.log_dir.glob("status-*.json")
        active = []
        
        for sf in status_files:
            with open(sf) as f:
                status = json.load(f)
                if status.get("state") != "closed":
                    active.append(status)
        
        return active
```

---

## 4.9 Özet

### Checklist

- [ ] Git worktree veya clone ile workspace izolasyonu
- [ ] Terminal profilleri konfigüre edildi
- [ ] Notification sistemi aktif
- [ ] Port/dependency conflict önleme
- [ ] Bütçe limitleri ayarlandı
- [ ] Session logging aktif

### Quick Reference

| Komut | Açıklama |
|-------|----------|
| `git worktree add ../dir branch` | Yeni worktree |
| `git worktree list` | Worktree listesi |
| `/share` | Session paylaş |
| `claude --resume last` | Son session'ı devam ettir |
| `claude --teleport [url]` | Session transfer |

### Metrikler

| Metrik | Tek Session | 5 Paralel Session |
|--------|-------------|-------------------|
| Günlük throughput | 5-8 görev | 20-30 görev |
| Context overflow riski | Yüksek | Düşük (izole) |
| Coordination overhead | Yok | Orta |
| Maliyet | $3-5/gün | $10-15/gün |

---

**Önceki Bölüm:** [03 - Plan Mode](./03-plan-mode.md)  
**Sonraki Bölüm:** [05 - CLAUDE.md ve Memory Sistemi](./05-claude-md-ve-memory.md)
