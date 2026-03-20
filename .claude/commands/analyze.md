---
allowed-tools: Read, Grep, Glob, Task, Write
argument-hint: [dosya yolu]
description: Bir dosyayı 3 paralel mühendis gözüyle analiz et — satır bazlı somut bulgular. Stratejik kararlar için /brainstorm kullan.
---

## Ne zaman KULLANMA

- Stratejik karar ("bu özelliği ekleyelim mi?") → `/brainstorm`
- Plan sorgulama ("bu yaklaşım doğru mu?") → `/challenge`
- Birden fazla dosya → Her biri için ayrı `/analyze` çalıştır

## Bağlam (ön-işleme)

- Dosya: !`cat $ARGUMENTS 2>/dev/null | head -300 || echo "DOSYA BULUNAMADI: $ARGUMENTS"`
- Son değişiklikler: !`git log --oneline -5 -- $ARGUMENTS 2>/dev/null || echo "Git bilgisi yok"`
- İlgili dosyalar: !`grep -l "$(basename $ARGUMENTS .py)" $(dirname $ARGUMENTS)/*.py 2>/dev/null | head -5 || echo "Yok"`

## Adım 1: Dosya kontrolü

Eğer ön-işleme "DOSYA BULUNAMADI" döndüyse → Kullanıcıya bildir, dur.

Dosya yolunu not et: $ARGUMENTS

## Adım 2: 3 paralel subagent

**3 Task çağrısını aynı yanıtında** yap. Her birine dosya **yolunu** ver.

**Task 1 — Performans:**
```
$ARGUMENTS dosyasını Read tool ile oku. Performans açısından analiz et.

Kontrol listesi:
- N+1 query (döngü içinde DB çağrısı)
- list() gereksiz kullanımı (generator yeterli mi?)
- Async/await yanlış kullanımı (sync çağrı async fonksiyonda)
- Cache fırsatı (aynı veri tekrar hesaplanıyor mu?)
- Hot path'te gereksiz iş (her request'te çalışan ağır hesaplama)

ZORUNLU FORMAT — her bulgu için:
[Satır X] {sorun} → {önerilen değişiklik} → {beklenen iyileşme}

Bulgu yoksa sadece "Temiz" yaz. Max 200 kelime.
YASAK: Dosyayı okumadan varsayımla konuşmak. Read tool KULLAN.
```

**Task 2 — Kod kalitesi:**
```
$ARGUMENTS dosyasını Read tool ile oku. Kod kalitesi açısından analiz et.

Kontrol listesi:
- SRP ihlali (fonksiyon 2+ iş yapıyor)
- Kötü isimlendirme (x, tmp, data gibi belirsiz isimler)
- Eksik type hint
- Magic number/string (açıklamasız sabit değer)
- Bare except veya Exception yakalama
- Yüksek cyclomatic complexity (5+ if/elif/for iç içe)

ZORUNLU FORMAT:
[Satır X] {sorun} → {öneri}

Bulgu yoksa "Temiz". Max 200 kelime.
YASAK: Dosyayı okumadan varsayımla konuşmak. Read tool KULLAN.
```

**Task 3 — Güvenilirlik:**
```
$ARGUMENTS dosyasını Read tool ile oku. Güvenilirlik açısından analiz et.

Kontrol listesi:
- Tight coupling (test için mock gerektirecek doğrudan bağımlılık)
- Handle edilmeyen edge case (None, boş liste, Türkçe karakter: ş,ğ,ü,ö,ç,ı,İ)
- Race condition (shared mutable state, concurrent access)
- Input validation eksikliği (kullanıcı girdisi kontrol edilmeden kullanılıyor)
- Fail-safe tanımsız (DB/Redis bağlantısı koparsa ne olur?)
- Yetersiz logging (hata durumunda debug edilebilir mi?)

ZORUNLU FORMAT:
[Satır X] {senaryo} → {önerilen test veya değişiklik}

Bulgu yoksa "Temiz". Max 200 kelime.
YASAK: Dosyayı okumadan varsayımla konuşmak. Read tool KULLAN.
```

## Adım 3: Doğrulama (max 1 retry)

Her subagent çıktısını kontrol et:
- [Satır X] formatı var mı? Yoksa → 1 kez yeniden fırlat: "Satır numarası zorunlu, dosyayı Read ile oku"
- "Genel olarak iyi" gibi boş mu? → 1 kez yeniden fırlat
- "Temiz" → Kabul et
- İkinci başarısızlıkta devam et, sentezde "(satır numarası verilemedi)" olarak belirt

## Adım 4: Sentez

Tüm bulguları birleştir, çakışmaları (aynı satırda 2 perspektif) vurgula:

```
📊 {dosya_adı} — {satır_sayısı} satır

🔴 KRİTİK (hemen):
1. [Satır X] {sorun} → {çözüm} ({perspektif})

🟡 ÖNEMLİ (yakın):
1. [Satır X] {sorun} → {çözüm}

🟢 İYİLEŞTİRME (uygun zamanda):
1. [Satır X] {sorun} → {çözüm}

📈 Performans: X/10 | Kalite: X/10 | Güvenilirlik: X/10
```

3+ kritik bulgu varsa → `Write` ile tam raporu `docs/brainstorms/code_{DOSYA_ADI}_{TARIH}.md`'ye kaydet.
