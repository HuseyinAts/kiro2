# 🤖 Gemini Mimar Ajanı - Kullanım Kılavuzu

## ✅ Durum

- ✅ **Ajan Dosyası:** `.kiro/agents/gemini-mimar.json` MEVCUT
- ✅ **MCP Sunucusu:** Çalışıyor
- ✅ **Gemini Model:** Yüklü (Gemini Experimental 1206)

---

## 🔍 Kiro IDE'de Gemini Mimar'ı Bulma

### Yöntem 1: Command Palette

1. **Ctrl+Shift+P** tuşlarına basın
2. **"agent"** veya **"select agent"** yazın
3. **"Gemini Mimar"** seçeneğini arayın

### Yöntem 2: Chat Paneli

1. Kiro IDE'de **Chat** panelini açın (genellikle sağ tarafta)
2. Chat input alanının üstünde veya yanında **ajan seçici** olabilir
3. Dropdown menüden **"Gemini Mimar"** seçin

### Yöntem 3: Settings/Preferences

1. **File → Preferences → Settings** (veya Ctrl+,)
2. **"agents"** arayın
3. Mevcut ajanları görün

---

## ⚠️ Eğer Gemini Mimar Görünmüyorsa

### Çözüm 1: Kiro IDE'yi Yeniden Başlatın

```
1. Kiro IDE'yi tamamen kapatın
2. Tekrar açın
3. Agents bölümünü kontrol edin
```

### Çözüm 2: Window Reload

```
1. Command Palette açın (Ctrl+Shift+P)
2. "Reload Window" yazın ve Enter'a basın
3. IDE yeniden yüklenecek
```

### Çözüm 3: Ajan Dosyasını Kontrol Edin

Dosyanın doğru formatta olduğundan emin olun:

```bash
# PowerShell'de kontrol edin
Get-Content .kiro/agents/gemini-mimar.json | ConvertFrom-Json
```

Hata alırsanız, JSON formatı bozuk olabilir.

---

## 🎯 Alternatif: Doğrudan MCP Kullanımı

Eğer Kiro IDE'de "Agents" özelliği yoksa veya Gemini Mimar görünmüyorsa, **doğrudan MCP araçlarını kullanabilirsiniz:**

### Python Script ile Kullanım

```bash
# Terminal'de çalıştırın
py test_gemini_direct.py
```

Seçim: **2** (İnteraktif Mod)

Artık Gemini ile sohbet edebilirsiniz!

---

## 💡 Gemini Mimar Ne Yapar?

Gemini Mimar ajanı şunları yapabilir:

### 1. Sistem Tasarımı Analizi
```
"Design.md dosyasını analiz et ve mimari iyileştirmeler öner"
```

### 2. Kod İncelemesi
```
"Bu Python kodunu incele ve best practice'lere uygun hale getir"
```

### 3. Gereksinim Analizi
```
"Requirements.md dosyasını kontrol et ve eksiklikleri belirt"
```

### 4. Eğitim İçeriği Üretimi
```
"8. sınıf matematik için LGS soruları üret"
```

---

## 🔧 Kiro IDE Ajan Sistemi Hakkında

Kiro IDE'nin ajan sistemi şu şekilde çalışır:

### Ajan Tanımı Formatı

```json
{
  "name": "Ajan Adı",
  "description": "Ajan açıklaması",
  "prompt": "Ajan system prompt'u",
  "allowedTools": ["araç-1", "araç-2"],
  "model": "kullanılacak-model",
  "resources": ["file://dosya1.md", "file://dosya2.md"]
}
```

### Ajan Dosya Konumu

```
.kiro/agents/ajan-adi.json
```

### MCP Araçları

Ajanlar, MCP (Model Context Protocol) araçlarını kullanır:

```
MCP Sunucusu → Araçlar → Ajan → Kullanıcı
```

---

## 📊 Gemini Mimar Yapılandırması

### Mevcut Yapılandırma

```json
{
  "name": "Gemini Mimar",
  "description": "Google Gemini 3 Pro ile sistem mimarisi ve kod analizi",
  "allowedTools": ["gemini-reasoning-engine"],
  "model": "claude-sonnet-4.5",
  "resources": [
    "file://.kiro/steering/product.md",
    "file://.kiro/steering/tech.md"
  ]
}
```

### Kullanılan MCP Aracı

**gemini-reasoning-engine:**
- Gemini Experimental 1206 modeli
- Thinking mode (akıl yürütme)
- 4 alt araç:
  - `gemini_reasoning_engine`
  - `gemini_code_review`
  - `gemini_design_analysis`
  - `gemini_requirements_analysis`

---

## 🚀 Hızlı Başlangıç

### Seçenek A: Kiro IDE'de Ajan Kullanımı

```
1. Kiro IDE'yi yeniden başlatın
2. Command Palette → "Select Agent" → "Gemini Mimar"
3. Chat panelinde soru sorun
```

### Seçenek B: Python Script ile Kullanım

```bash
# Terminal'de
py test_gemini_direct.py

# Seçim: 2 (İnteraktif Mod)

💬 Siz: Merhaba Gemini!
```

---

## 📞 Destek

### Ajan Görünmüyor?

1. `.kiro/agents/gemini-mimar.json` dosyasının var olduğunu kontrol edin
2. Kiro IDE'yi yeniden başlatın
3. Command Palette → "Reload Window"
4. Hala görünmüyorsa, Python scriptini kullanın

### MCP Sunucusu Çalışmıyor?

```bash
# MCP sunucusunu test edin
py -c "from backend.mcp_servers.gemini_reasoning_mcp import mcp; print('OK')"
```

### API Key Hatası?

```bash
# .env dosyasını kontrol edin
GOOGLE_API_KEY=AIzaSyB7KSM64qj3DIeTLsWnWVTHDrHU41NzUvA
```

---

## ✅ Özet

| Özellik | Durum |
|---------|-------|
| Ajan Dosyası | ✅ Mevcut |
| MCP Sunucusu | ✅ Çalışıyor |
| Gemini Model | ✅ Yüklü |
| Python Script | ✅ Hazır |

**Gemini Mimar kullanıma hazır!**

Kiro IDE'de görünmüyorsa, `py test_gemini_direct.py` ile doğrudan kullanabilirsiniz.

---

**Tarih:** 22 Kasım 2025  
**Platform:** Teknofest 2025 Eğitim Eylemci Platformu
