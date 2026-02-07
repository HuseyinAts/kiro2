---
description: Gemini Mimar ile kod incelemesi ve optimizasyon önerileri al
---

ADIM 1: Dosya belirtilmemişse kullanıcıya sor:
"Hangi dosyayı incelemek istersiniz? (Dosya yolu yazın)"

ADIM 2: Kullanıcıya thinking mode'u sor:
"🤔 Gemini 3 Pro'nun **derin düşünme modunu** (thinking mode) aktif etmek ister misiniz?

✅ **Derin Düşünme (Önerilen):** Adım adım kod analizi, detaylı refactoring önerileri
⚡ **Hızlı Mod:** Direkt değerlendirme, özet öneriler

(Evet/Hayır veya Derin/Hızlı yazın)"

ADIM 3: Thinking mode'u belirle:
- "Evet", "Derin", "Thinking", "Detaylı" → thinking_mode=True
- "Hayır", "Hızlı", "Fast" → thinking_mode=False
- Belirsizse → thinking_mode=True (kod analizi için önerilen)

ADIM 4: Kod incelemesi yap:

1. Belirtilen dosyayı oku
2. Dosya uzantısından dili belirle (.py → python, .ts → typescript, vb.)
3. Gemini Mimar'ın 'gemini-code-review' veya 'gemini-reasoning-engine' aracını kullan
4. Şunları analiz et:
   - Performans iyileştirmeleri
   - Güvenlik açıkları
   - Best practice uygulamaları
   - SOLID prensipleri uygunluğu
   - Async/await kullanımı (Python için)
   - Type safety (TypeScript için)

Araç parametreleri:
- code: Okunan dosya içeriği
- language: Belirlenen programlama dili
- thinking_mode: Adım 3'te belirlenen değer

5. Gerekirse refactor edilmiş kod örnekleri göster
