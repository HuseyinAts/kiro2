# Kiro IDE + Claude Code 2026 Entegrasyon Rehberi

> **Tarih:** 26 Ocak 2026
> **Versiyon:** 1.0.0
> **Uyumluluk:** %95 (4 kritik iyileştirme ile %100)

---

## Genel Bakis

KIRO2 projesi hem Kiro IDE hem de Claude Code 2026 altyapilarini kullanmaktadir. Bu belge, iki sistemin birlikte nasil calistigini ve potansiyel cakismalarin nasil yonetilecegini aciklar.

---

## Dizin Yapisi

```
kiro2/
├── .kiro/                    # Kiro IDE yapilandirmasi
│   ├── settings/
│   │   ├── mcp.json          # 20 MCP server tanimlamasi
│   │   └── project.json      # Proje ayarlari
│   ├── hooks/                # 11 Kiro hook dosyasi
│   ├── specs/                # MASTER_SPEC (47 REQ)
│   └── steering/             # Agent yonlendirme
│
└── .claude/                  # Claude Code 2026 yapilandirmasi
    ├── settings.json         # Ana ayarlar
    ├── settings.local.json   # Yerel ayarlar
    ├── agents/               # 22 agent tanimi
    ├── skills/               # 12 skill tanimi
    ├── commands/             # 21 slash command
    ├── hooks/                # 4 hook tipi (PS scripts)
    ├── tasks/                # Task yonetim sistemi
    ├── patterns/             # 7 orkestrasyon pattern
    └── evals/                # 5 kod kalite degerlendirmesi
```

---

## Hook Oncelik Sirasi

Her iki sistem de hook'lara sahiptir. Asagidaki oncelik sirasi uygulanir:

### Yuksekten Dusuge Oncelik

| Oncelik | Sistem | Hook | Tetikleyici |
|---------|--------|------|-------------|
| 1 | Claude | `PreToolUse` | Bash komutlari oncesi |
| 2 | Kiro | `05-kvkk-compliance` | Kisisel veri islemleri |
| 3 | Kiro | `06-security-hardening` | Guvenlik dosyalari |
| 4 | Claude | `PostToolUse` | Edit/Write sonrasi |
| 5 | Kiro | `01-revolutionary-ai` | AI agent dosyalari |
| 6 | Kiro | `02-video-quality` | Video servisleri |
| 7 | Kiro | `03-health-audit` | Genel saglik kontrolu |
| 8 | Kiro | `04-osym-exam` | Sinav format kontrolu |
| 9 | Claude | `PreCompact` | Context yedekleme |
| 10 | Claude | `Stop` | Tamamlanma dogrulama |

### Hook Cakisma Kurallari

1. **Guvenlik Oncelikli:** KVKK ve OWASP hook'lari her zaman once calisir
2. **Claude Dogrulama:** PostToolUse her dosya degisikliginde tetiklenir
3. **Kiro Kalite:** AI/Video/Exam hook'lari ilgili dosyalarda tetiklenir
4. **Cifte Dogrulama:** Hem Claude hem Kiro dogrulama yaparsa, ikisi de gecmelidir

---

## MCP Sunucu Yonetimi

### Baslatma Sirasi (Kritik)

MCP sunuculari asagidaki sirada baslatilmalidir:

```
1. zemberek-nlp (port 8081)     # Turkce NLP - temel
   ↓
2. chromadb-mcp                  # Vektor DB - embedding gerektirir
   ↓
3. kiro2-orchestrator            # Ana orkestrator
   ↓
4. gemini-mcp                    # Icerik uretimi
   ↓
5. youtube-education-api         # Video arama
   ↓
6. [Diger MCP sunuculari]        # Paralel baslayabilir
```

### Baslatma Scripti

```powershell
# .kiro/scripts/startup-mcp-servers.ps1 dosyasini kullanin
.\\.kiro\\scripts\\startup-mcp-servers.ps1
```

### Port Listesi

| Sunucu | Port | Durum |
|--------|------|-------|
| Zemberek NLP | 8081 | Kritik |
| Blackboard | 8765 | Kritik |
| Prometheus Exporter | 9090 | Opsiyonel |
| Backend API | 8000 | Uygulama |
| Frontend Dev | 3000 | Gelistirme |

---

## Model Secimi

### Claude Code 2026 Model Stratejisi

| Gorev Tipi | Model | Maliyet |
|------------|-------|---------|
| Arastirma | Sonnet | $0.10-0.50 |
| Kod yazma | Sonnet | $0.10-0.50 |
| Kritik kararlar | Opus | $0.50-2.00 |
| Code review | Opus | $0.50-2.00 |
| Test yazma | Sonnet | $0.10-0.50 |

### Kiro Hook'lari icin Model

Kiro hook'lari icin varsayilan model: **claude-opus-4.5**

Hook'larda model belirtilmediyse, `.claude/settings.json` deki model kullanilir.

---

## Exit Code Kurallari

### Claude Code Standardi

| Exit Code | Anlam | Aksiyon |
|-----------|-------|---------|
| 0 | Basari | Devam et |
| 2 | Engelleyici Hata | DUR, duzelt, tekrar dene |
| Diger | Uyari | Kullaniciya goster, devam et |

### Kiro Hook'larinda Exit Code (YENI)

Kiro hook'larinda exit code destegi eklenmeli:

```json
{
  "type": "askAgent",
  "exitCodes": {
    "blocking": [2],
    "warning": [1],
    "success": [0]
  }
}
```

---

## Uyumluluk Kontrol Listesi

### Gunluk Kullanim

- [x] MCP sunuculari dogru sirada baslat
- [x] Claude Code 2026 hook'lari aktif
- [x] Kiro hook'lari aktif
- [x] KVKK/Guvenlik hook'lari oncelikli

### Haftalik Bakim

- [ ] Hook cakisma logu kontrol et
- [ ] MCP sunucu saglik kontrolu
- [ ] Token tuketimi izle
- [ ] Eval sonuclarini incele

### Aylik Gozden Gecirme

- [ ] Yeni Claude Code ozellikleri entegre et
- [ ] Kiro hook'larini guncelle
- [ ] Model maliyet analizi yap
- [ ] Performans metrikleri raporla

---

## Sorun Giderme

### Hook Cifte Calisma

**Belirti:** Ayni dosya icin iki kez dogrulama mesaji
**Cozum:** Bu beklenen davranistir. Her iki sistem de dogrulama yapar.

### MCP Port Cakismasi

**Belirti:** "Port already in use" hatasi
**Cozum:**
```powershell
netstat -ano | findstr :8081
taskkill /PID <PID> /F
```

### Context Erken Doluyor

**Belirti:** Claude %60 uyarisi cok erken tetikleniyor
**Cozum:** Kiro hook'larinin AI prompt'larini kisalt veya `context: fork` kullan

### Model Belirsizligi

**Belirti:** Hangi modelin calistigini bilemiyorum
**Cozum:** `.claude/settings.json` deki `"model": "opus"` ayarini kontrol et

---

## Referanslar

- [Claude Code 2026 Entegrasyon Plani](../.claude/plans/fizzy-leaping-muffin.md)
- [CLAUDE.md Proje Kurallari](../CLAUDE.md)
- [MASTER_SPEC Gereksinimler](.kiro/specs/MASTER_SPEC/requirements.md)
- [MCP Sunucu Dokumantasyonu](.kiro/settings/MCP_SERVER_README.md)

---

## Degisiklik Gecmisi

| Tarih | Versiyon | Degisiklik |
|-------|----------|------------|
| 2026-01-26 | 1.0.0 | Ilk surum - entegrasyon rehberi |
