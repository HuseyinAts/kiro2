# 🤖 Gemini 3 Pro MCP Entegrasyonu

## ✅ Yapılandırma Tamamlandı

Gemini 3 Pro modeli MCP (Model Context Protocol) üzerinden Kiro IDE'ye entegre edildi.

---

## 📋 Yapılan Değişiklikler

### 1. MCP Sunucu Yapılandırması

**Dosya:** `C:\Users\husey\.kiro\settings\mcp.json`

```json
{
  "mcpServers": {
    "google-gemini": {
      "command": "uvx",
      "args": ["mcp-server-google-gemini"],
      "env": {
        "GOOGLE_API_KEY": "${GOOGLE_API_KEY}",
        "GEMINI_MODEL": "gemini-3-pro"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## 🔑 Sonraki Adımlar

### 1. Google API Key Alın

1. https://aistudio.google.com/ adresine gidin
2. "Get API Key" butonuna tıklayın
3. API key'i kopyalayın

### 2. API Key'i .env Dosyasına Ekleyin

`.env` dosyasını açın ve şu satırı bulun:

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

Gerçek API key'inizi buraya yapıştırın:

```bash
GOOGLE_API_KEY=AIzaSyC...your_actual_key
```

### 3. Kiro IDE'yi Yeniden Başlatın

veya Command Palette'te (Ctrl+Shift+P):
- **"MCP: Reconnect All Servers"** komutunu çalıştırın

---

## 🎯 Kullanım

MCP sunucusu başladıktan sonra, Gemini 3 Pro otomatik olarak Kiro IDE içinden kullanılabilir olacak.

**Not:** Gemini 3 Pro henüz beta aşamasındaysa, model adını `gemini-2.0-flash-exp` olarak değiştirebilirsiniz.

---

**Tarih:** 17 Kasım 2025  
**Platform:** Teknofest 2025 Eğitim Eylemci Platformu
