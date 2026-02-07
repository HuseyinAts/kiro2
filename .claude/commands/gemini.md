---
description: Gemini Mimar agent'ını çağırır - Sistem mimarisi, kod analizi ve gereksinim incelemesi için Google Gemini 3 Pro kullanır
---

ADIM 1: Kullanıcıya şunu sor:
"🤔 Gemini 3 Pro'nun **derin düşünme modunu** (thinking mode) aktif etmek ister misiniz?

✅ **Derin Düşünme (Önerilen):** Adım adım akıl yürütme, detaylı analiz, alternatif çözümler
⚡ **Hızlı Mod:** Direkt cevap, daha kısa sürede sonuç

(Evet/Hayır veya Derin/Hızlı yazın)"

ADIM 2: Kullanıcının cevabına göre karar ver:
- "Evet", "Derin", "Thinking", "Detaylı", "Evet aktif et" → thinking_mode=True
- "Hayır", "Hızlı", "Fast", "Kısa" → thinking_mode=False
- Belirsizse → thinking_mode=True (varsayılan)

ADIM 3: Gemini Mimar'ı çağır:

Gemini Mimar'ın 'gemini-reasoning-engine' aracını kullanarak kullanıcının sorusunu yanıtla.

Araç parametreleri:
- prompt: Kullanıcının sorusu
- thinking_mode: Adım 2'de belirlenen değer (true/false)
- context: (varsa) Ek bağlam bilgisi

Gemini Mimar şu konularda uzmanlaşmıştır:
- Sistem mimarisi analizi
- Kod incelemesi ve optimizasyon
- Gereksinim analizi
- Best practice önerileri
- Eğitim içeriği üretimi (LGS/YKS soruları)
