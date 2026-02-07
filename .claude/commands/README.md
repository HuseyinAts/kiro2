# Gemini Mimar Slash Commands

Bu dizin, Gemini Mimar agent'ını kolayca çağırmak için slash command'ları içerir.

## 🎯 Kullanılabilir Komutlar

### `/gemini`
**Genel kullanım** - Gemini Mimar'ı herhangi bir soru için çağırır

```
/gemini Bu projenin mimarisini analiz et
```

**Özellik:** Derin düşünme modu seçeneği (thinking mode)

### `/gemini-design`
**Tasarım analizi** - design.md dosyasını otomatik analiz eder

```
/gemini-design
```

**Özellik:** Adım adım mimari analiz veya hızlı değerlendirme seçeneği

### `/gemini-code`
**Kod incelemesi** - Belirtilen kod dosyasını inceler

```
/gemini-code backend/api/questions_api.py
```

**Özellik:** Detaylı refactoring önerileri veya hızlı kod analizi seçeneği

### `/gemini-soru`
**Soru üretimi** - LGS/YKS soruları üretir

```
/gemini-soru 8. sınıf matematik üçgenler 5 soru
```

**Özellik:** Pedagojik derin analiz veya hızlı soru üretimi seçeneği

## 🤔 Derin Düşünme Modu (Thinking Mode)

Tüm komutlar kullanıcıya **derin düşünme modu** seçeneği sunar:

### ✅ Derin Düşünme (Önerilen)
- Adım adım akıl yürütme
- Detaylı analiz ve açıklamalar
- Alternatif çözümler
- Best practice önerileri
- Daha uzun süre (~10-30 saniye)

### ⚡ Hızlı Mod
- Direkt cevap
- Özet değerlendirme
- Kısa öneriler
- Daha kısa süre (~2-5 saniye)

**Kullanım sırasında sistem size soracak:**
```
🤔 Gemini 3 Pro'nun derin düşünme modunu aktif etmek ister misiniz?
✅ Derin Düşünme (Önerilen): Adım adım analiz...
⚡ Hızlı Mod: Direkt cevap...
(Evet/Hayır veya Derin/Hızlı yazın)
```

## 📋 Kullanım Adımları

1. **Chat'te `/` yazın** - Komut listesi görünür
2. **Komut seçin** - İstediğiniz komutu tıklayın
3. **Thinking mode seçin** - "Evet/Derin" veya "Hayır/Hızlı"
4. **Sonucu bekleyin** - Gemini 3 Pro analiz yapar

## 💡 Pratik Örnekler

### Örnek 1: Kod İncelemesi (Derin Mod)
```
/gemini-code backend/services/veli_service.py
→ Sistem: Derin düşünme modu aktif edilsin mi?
→ Siz: Evet
→ Gemini: 🤖 [Adım adım kod analizi başlar...]
```

### Örnek 2: Hızlı Tasarım Analizi
```
/gemini-design
→ Sistem: Derin düşünme modu aktif edilsin mi?
→ Siz: Hayır, hızlı
→ Gemini: 🤖 [Özet mimari değerlendirme]
```

### Örnek 3: Pedagojik Soru Üretimi
```
/gemini-soru YKS-AYT Fizik "Newton Yasaları" 3 soru
→ Sistem: Derin düşünme modu aktif edilsin mi?
→ Siz: Derin
→ Gemini: 🤖 [Pedagojik analiz + detaylı sorular]
```

## ⚙️ Teknik Detaylar

### MCP Araç Parametreleri

Tüm komutlar `gemini-reasoning-engine` MCP aracını kullanır:

```python
{
  "prompt": "Kullanıcının sorusu",
  "thinking_mode": True,  # veya False
  "context": "Ek bağlam bilgisi"
}
```

### Thinking Mode Davranışı

**thinking_mode=True** olduğunda:
```
Prompt = "Lütfen adım adım düşünerek ve akıl yürütme
sürecini göstererek yanıtla.\n\n" + Kullanıcı Sorusu
```

**thinking_mode=False** olduğunda:
```
Prompt = Kullanıcı Sorusu (direkt)
```

## 🎓 Hangi Modu Seçmeliyim?

### Derin Düşünme Modu Önerilir:
- ✅ Sistem mimarisi tasarımı
- ✅ Kod refactoring
- ✅ Eğitim içeriği üretimi
- ✅ Karmaşık problem çözme
- ✅ Öğrenme amaçlı analiz

### Hızlı Mod Önerilir:
- ⚡ Basit sorular
- ⚡ Hızlı değerlendirme
- ⚡ Özet bilgi
- ⚡ Zaman kısıtlı durumlar

## 🔗 İlgili Dosyalar

- **MCP Sunucusu:** `backend/mcp_servers/gemini_reasoning_mcp.py`
- **Agent Tanımı:** `.kiro/agents/gemini-mimar.json`
- **Komut Dosyaları:** `.claude/commands/gemini*.md`

## 📞 Sorun Giderme

**Komutlar görünmüyor:**
```bash
# Claude Code'u yeniden başlatın
# veya
Ctrl+Shift+P → "Reload Window"
```

**Thinking mode çalışmıyor:**
- MCP sunucusunun çalıştığından emin olun
- `.env` dosyasında `GOOGLE_API_KEY` kontrol edin

---

**Not:** Tüm komutlar Gemini Mimar agent'ını kullanır ve Google Gemini 3 Pro (veya fallback: Gemini 2.0 Flash) modeliyle çalışır.
