# Kiro Özel Ajanlar

Bu dizin, Kiro IDE'de kullanılacak özel ajanları içerir.

## Gemini Mimar Ajanı

**Dosya:** `gemini-mimar.json`

### Özellikler

- **Model:** Google Gemini 3 Pro (fallback: Gemini 2.0 Flash)
- **Uzmanlık:** Sistem mimarisi, kod analizi, gereksinim analizi
- **Araçlar:** `gemini-reasoning-engine` (MCP üzerinden)

### Kullanım

1. **Kiro IDE'de Ajan Seçimi**
   - Sol panelde "Agents" bölümünü açın
   - "Gemini Mimar" ajanını seçin

2. **Örnek Sorular**
   ```
   - "Bu projenin design.md dosyasını analiz et ve iyileştirme önerileri sun"
   - "Requirements.md dosyasındaki gereksinimleri incele ve eksiklikleri belirt"
   - "Bu kod parçasını optimize et ve best practice'lere uygun hale getir"
   ```

3. **Thinking Mode**
   - Gemini Mimar, varsayılan olarak "thinking mode" kullanır
   - Bu mod, adım adım akıl yürütme süreci gösterir
   - Karmaşık problemler için idealdir

### MCP Sunucu Yapılandırması

**Dosya:** `C:\Users\husey\.kiro\settings\mcp.json`

```json
{
  "mcpServers": {
    "gemini-reasoning-engine": {
      "command": "python",
      "args": ["-m", "backend.mcp_servers.gemini_reasoning_mcp"],
      "env": {
        "GOOGLE_API_KEY": "${GOOGLE_API_KEY}"
      },
      "disabled": false
    }
  }
}
```

### Gereksinimler

- Python 3.11+
- `google-generativeai` paketi
- `mcp` paketi
- Google API Key (`.env` dosyasında)

### Kurulum

1. **Paketleri Kur**
   ```bash
   pip install google-generativeai mcp
   ```

2. **API Key Ayarla**
   `.env` dosyasına ekleyin:
   ```bash
   GOOGLE_API_KEY=your_api_key_here
   ```

3. **MCP Sunucusunu Başlat**
   - Kiro IDE'yi yeniden başlatın
   - veya Command Palette'te "MCP: Reconnect All Servers"

### Sorun Giderme

**MCP sunucusu başlamıyor:**
```bash
# Manuel test
python -m backend.mcp_servers.gemini_reasoning_mcp
```

**API Key hatası:**
- `.env` dosyasında `GOOGLE_API_KEY` değişkenini kontrol edin
- API key'in geçerli olduğundan emin olun

**Model bulunamadı:**
- Gemini 3 Pro henüz kullanıma açılmadıysa, otomatik olarak Gemini 2.0 Flash kullanılır

### Kaynaklar

- **Steering Files:**
  - `.kiro/steering/product.md` - Ürün gereksinimleri
  - `.kiro/steering/tech.md` - Teknik standartlar

- **MCP Sunucu:**
  - `backend/mcp_servers/gemini_reasoning_mcp.py`

### Özelleştirme

Ajan davranışını özelleştirmek için `gemini-mimar.json` dosyasını düzenleyin:

```json
{
  "name": "Gemini Mimar",
  "prompt": "Özel prompt buraya...",
  "allowedTools": ["gemini-reasoning-engine"],
  "model": "claude-sonnet-4.5",
  "resources": [
    "file://.kiro/steering/custom.md"
  ]
}
```

---

**Tarih:** 22 Kasım 2025  
**Platform:** Teknofest 2025 Eğitim Eylemci Platformu
