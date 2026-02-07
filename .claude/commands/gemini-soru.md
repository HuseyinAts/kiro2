---
description: Gemini Mimar ile LGS/YKS soruları üret - Türkçe eğitim içeriği oluşturma
---

ADIM 1: Kullanıcıdan şu bilgileri al (belirtilmemişse):
   - Sınav türü (LGS, YKS-TYT, YKS-AYT)
   - Ders (Matematik, Fizik, Türkçe, vb.)
   - Konu (örn: "Üçgenler", "Newton Yasaları")
   - Soru sayısı

ADIM 2: Kullanıcıya thinking mode'u sor:
"🤔 Gemini 3 Pro'nun **derin düşünme modunu** (thinking mode) aktif etmek ister misiniz?

✅ **Derin Düşünme (Önerilen):** Pedagojik analiz, çoklu soru varyasyonları, detaylı çözüm adımları
⚡ **Hızlı Mod:** Direkt soru üretimi, kısa çözümler

(Evet/Hayır veya Derin/Hızlı yazın)"

ADIM 3: Thinking mode'u belirle:
- "Evet", "Derin", "Thinking", "Detaylı", "Pedagojik" → thinking_mode=True
- "Hayır", "Hızlı", "Fast" → thinking_mode=False
- Belirsizse → thinking_mode=True (kaliteli soru üretimi için önerilen)

ADIM 4: Soru üretimi:

Gemini Mimar'ın 'gemini-reasoning-engine' aracını kullanarak soru üret.

Prompt formatı:
```
Türkçe eğitim sistemi için [Sınav Türü] soruları üret.
Ders: [Ders]
Konu: [Konu]
Soru Sayısı: [Sayı]

Gereksinimler:
- MEB müfredatına uygun
- OSYM soru formatında
- Bloom taksonomisi seviyeleri belirtilmiş
- Detaylı çözüm adımları
- Kazanımlar listelenmiş
- JSON formatında
```

Araç parametreleri:
- prompt: Yukarıdaki format
- thinking_mode: Adım 3'te belirlenen değer
- context: "Türkçe eğitim sistemi, MEB müfredatı"

ADIM 5: JSON formatında sorular oluştur:
```json
{
  "soru_metni": "...",
  "secenekler": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "dogru_cevap": "A",
  "cozum": "...",
  "bloom_seviye": "Uygulama",
  "kazanim": "..."
}
```

ADIM 6: Soruları backend/services/ altında uygun servise kaydetmeyi öner
