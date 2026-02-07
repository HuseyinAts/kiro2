---
description: Gemini Mimar ile design.md dosyasını analiz et ve mimari önerileri al
---

ADIM 1: Kullanıcıya şunu sor:
"🤔 Gemini 3 Pro'nun **derin düşünme modunu** (thinking mode) aktif etmek ister misiniz?

✅ **Derin Düşünme (Önerilen):** Adım adım mimari analiz, detaylı öneriler, alternatif tasarımlar
⚡ **Hızlı Mod:** Direkt değerlendirme, özet öneriler

(Evet/Hayır veya Derin/Hızlı yazın)"

ADIM 2: Thinking mode'u belirle:
- "Evet", "Derin", "Thinking", "Detaylı" → thinking_mode=True
- "Hayır", "Hızlı", "Fast" → thinking_mode=False
- Belirsizse → thinking_mode=True (tasarım analizi için önerilen)

ADIM 3: Design dokümanını oku ve analiz et:

1. .claude/specs/ veya proje kök dizinindeki design.md dosyasını oku
2. Gemini Mimar'ın 'gemini-design-analysis' veya 'gemini-reasoning-engine' aracını kullan
3. Şu konularda analiz yaptır:
   - Mimari tasarım uygunluğu
   - Mikroservis vs monolitik değerlendirmesi
   - Veritabanı tasarımı
   - API endpoint yapısı
   - Güvenlik önlemleri
   - Performans optimizasyonları

Araç parametreleri:
- design_doc: Okunan design.md içeriği
- thinking_mode: Adım 2'de belirlenen değer

Kullanıcının ek sorusu varsa ona göre analizi derinleştir.
