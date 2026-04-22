# Cursor 3.x + Nightly — Senin Yapman Gerekenler

Bu dosya, benim yapamadığım (GUI aksiyonu, abonelik, API key gibi)
adımları listeliyor. Cursor'u yeniden başlatmadan önce **hepsini** uygula.

## 1 — Nightly Kanalına Geç (KRİTİK)

**Neden:** [Resmi doc'a göre](https://cursor.com/blog/agent-best-practices)
Agent Skills şu an sadece Nightly release kanalında aktif. `.cursor/skills/`
altındaki 12 skill'in trigger olması için bu gerekli.

**Nasıl:**
1. Cursor aç
2. `Cmd/Ctrl + ,` → Settings
3. Sol menüden **Beta** sekmesi
4. **Update channel** → Nightly seç
5. Restart prompt'una OK
6. Cursor otomatik Nightly build indirir (1-2 dakika)

**Stable'a dönmek istersen:** Aynı menüden Stable seç, sonraki release'de döner.

## 2 — Privacy Mode Enable (KRİTİK — ÖĞRENCİ VERİSİ)

**Neden:** KIRO2 KVKK'ya tabi öğrenci verisi işliyor, TÜBİTAK fonlu algoritma
IP'si var. Privacy Mode olmadan kod model provider'larda cache olabilir.

**Nasıl:**
1. Settings (`Cmd/Ctrl + ,`)
2. **Privacy & Security**
3. **Enforce Privacy Mode** toggle → ON
4. **Privacy Mode Required** — admin override'ı engelle (yalnız kullanımda)

**Doğrulama:** Herhangi bir chat'te model response'un footer'ında "Privacy
Mode: enabled" görmelisin.

## 3 — Default Model: Auto

**Neden:** Auto mode kredi tüketmez, Composer 2 dahil en uygun modeli seçer.
Sadece gerçekten frontier gereken task'larda manuel modele geç.

**Nasıl:**
1. Agent input alanının altındaki model dropdown
2. **Auto** seç (Suggested işaretli olan)
3. Composer 2, GPT-5.4, Opus 4.6, Gemini 3 Pro ihtiyaç bazında değişir

## 4 — Indexing Resync

**Neden:** Yeni `.cursorignore`, `.cursor/rules/` ve skill'ler için index'in
yeniden kurulması lazım.

**Nasıl:**
1. Settings → **Indexing & Codebase**
2. **Resync Index** tıkla
3. 15-30 dakika bekle (KIRO2 77K+ soru içeriğine göre)
4. Status bar'da "Indexing..." kayboldu → tamam

## 5 — MCP Server Doğrulama

**Neden:** 4 MCP server'ın yeşil göstergeye sahip olması lazım:
filesystem, postgres, playwright, sequential-thinking.

**Nasıl:**
1. Settings → **Tools & MCP**
2. Server listesi:
   - ✅ filesystem → yeşil nokta
   - ✅ postgres → yeşil nokta
   - ✅ playwright → yeşil nokta
   - ✅ sequential-thinking → yeşil nokta
3. Kırmızı olan varsa:
   - PowerShell'de `cmd /c npx -y @modelcontextprotocol/server-postgres` manuel test
   - Env var eksikliği olabilir — Windows env: `echo $env:USERPROFILE`

## 6 — GitHub PAT Ekleme

**Neden:** BugBot ve PR otomasyonu için GitHub access gerekli.

**Nasıl:**
1. PowerShell'i yönetici olarak aç:
   ```powershell
   setx GITHUB_PAT "ghp_YOUR_TOKEN_HERE"
   ```
2. PowerShell'i kapat ve aç (env var reload)
3. `.cursor/mcp.json` aç:
4. `"_github_when_ready"` bloğunun ismini `"github"` olarak değiştir ve
   `mcpServers` objesi içine taşı
5. Cursor'ı restart et
6. Settings → Tools & MCP → github yeşil olmalı

## 7 — BugBot Kurulumu (Opsiyonel, $40/ay Ek)

**Not:** BugBot Cursor Pro'ya DAHİL DEĞİL, ayrı abonelik.

**Karar:** İlk ay skip et, Cursor Pro değerini ölçtükten sonra karar ver.

**Eğer karar alırsan:**
1. https://cursor.com/dashboard/bugbot
2. **Connect GitHub** → KIRO2 repo'ya access ver
3. **Enable BugBot** toggle
4. `.cursor/BUGBOT.md` otomatik okunur
5. 14 gün trial başlar

## 8 — Agents Window Aktivasyon

**Neden:** Cursor 3.0 ile gelen ana yenilik — paralel agent'lar, cloud
handoff, Design Mode.

**Nasıl:**
1. `Cmd+Shift+P` (Command Palette)
2. "Agents Window" yaz
3. **Agents Window: Open** seç
4. Yeni pencere açılır — IDE'yi kapatmana gerek yok, ikisi beraber çalışır

**İlk kullanım:** Basit bir task dene:
```
/plan

Task: backend/app/api/v1/health.py endpoint'ini gözden geçir, KIRO2
stack'ine uygun iyileştirme öner.
```

## 9 — Kısayolları Öğren

| Kısayol | İşlev |
|---|---|
| `Shift+Tab` | Plan Mode toggle |
| `Cmd+L` | Chat'e selection ekle |
| `Cmd+K` | Inline edit |
| `Cmd+I` | Composer aç |
| `Cmd+Shift+D` | Design Mode (browser açıkken) |
| `Ctrl+M` (hold) | Voice input |
| `Cmd+Shift+P` → "Agents Window" | Agents Window aç |

## 10 — Kararlar Alman Gereken Konular

### Plan: Pro ($20) vs Pro+ ($60)

**Pro $20 yeter** eğer:
- Günlük 2-3 saat Cursor kullanıyorsan
- Composer 2'yi çoğunlukta kullanıyorsan (cömert havuz)
- Auto mode yeter

**Pro+ $60 geç** eğer:
- Haftalık 3+ gün frontier model (Opus 4.6, GPT-5.4) limit aşıyorsan
- `/best-of-n` düzenli kullanıyorsan (3-4 model paralel)
- Cloud Agents sıkça (laptop kapalı → devam)

**İlk 2 hafta Pro'da kal**, Settings → Usage'tan kredi tüketimini izle.

### Nightly vs Stable

- **Nightly avantajı:** Skills, son özellikler, en güncel Composer
- **Nightly dezavantajı:** Ara sıra bug, crash riski
- **KIRO2 için:** Nightly öner çünkü skills kritik. Crash olursa Stable'a dön.

## 11 — Doğrulama Test Sırası

Hepsini tamamladıktan sonra bu 6 testi sırayla yap:

### Test 1 — Rule trigger
Yeni chat aç, `backend/app/api/v1/auth.py` aç, sor:
> "Yeni endpoint eklersem neleri kontrol etmeliyim?"

Beklenen: 10-backend.mdc'deki IDOR + Dual Table + Router kaydı listesi gelir.

### Test 2 — Skill trigger
Soru: "IRT difficulty parametresinin aralığı nedir?"

Beklenen: education-algorithms veya irt-validation skill'i aktivasyonu
(Nightly'da), `[-4.0, 4.0]` döner.

### Test 3 — Plan Mode
Agent input'unda Shift+Tab bas, task yaz:
> "KIRO2'ye exam submit endpoint'i ekle."

Beklenen: Cursor codebase'i tarar, clarifying soruları sorar, markdown plan
üretir.

### Test 4 — Hook
Bir `.py` dosyası aç, küçük değişiklik yap, kaydet.
Terminal'de `[cursor-format] ruff: ...` log'u çıkmalı.

### Test 5 — Hook block
Composer'da yaz:
> "rm -rf /tmp"

Beklenen: guard-shell hook "DANGEROUS COMMAND BLOCKED" döner.

### Test 6 — @Past Chats
İlk 5 testi yaptıktan sonra yeni chat aç:
> "@Past Chats: rule trigger testi"

Beklenen: İlk test konuşmasına referans, özet döner.

## 12 — Sorun Giderme

### Skills trigger etmiyor
- Nightly'da mısın? Settings → Beta
- `.cursor/skills/<n>/SKILL.md` var mı? YAML frontmatter doğru mu?
- Resync index yaptın mı?

### MCP kırmızı
- PowerShell'de `cmd /c npx -y <paket>` manuel çalışıyor mu?
- `CLAUDE_DESKTOP_CONFIG` vs `.cursor/mcp.json` karışmadı mı?
- Env var'lar set mi? `echo $env:GITHUB_PAT`

### Composer 2 bulunamıyor
- Cursor versiyonu >= 2.0 mi? (Composer 2 gerektirir)
- Model dropdown'da Auto seçili mi?
- Settings → Models altında Composer enabled mi?

### Hook çalışmıyor
- `.cursor/hooks.json` format doğru mu? (JSON validate et)
- Python `python --version` PATH'te mi?
- Script permission'ları var mı? (Windows'ta sorun genelde yok)

## Sonraki Adım

Bu 11 adımı tamamladıktan sonra, 2 hafta boyunca normal çalış. Sonra:

- Kullanım istatistiklerini gözden geçir (Settings → Usage)
- Hangi skill'lerin tetiklendiğini kontrol et
- BugBot'a gerek olup olmadığına karar ver
- Pro+ geçiş kararını ver

Sorularda bana dön, pattern değiştirmek istersen rule/skill güncelleriz.
