# KIRO2 — İllüstrasyon Kanonu BRIEF (P0-2 hazırlık, 2026-07-05)

> Bu dosya `KIRO Illustrasyon Sistemi.dc.html` üretilmeden önceki gramer kararlarını sabitler.
> DC üretilince bu brief spec'e dönüştürülür (MOTION_KANON_SPEC.md modeli) ve YENI_SOHBET_DEVIR §10 güncellenir.

## Amaç
Spot illüstrasyon grameri: boş durum, kutlama, onboarding, mola/duygusal anlar için
tutarlı, kaygı-duyarlı, emoji-siz sahne dili. SVG placeholder değil — kanonlaşmış çizim kuralları.

## Gramer (öneri — DC'de örneklenecek)
1. **Palet:** yalnız şafak ailesi — mercan/şeftali/altın aksan + zemin türüne göre:
   paper sahnede sıcak kâğıt üstü soluk mürekkep konturlar; dusk sahnede gökyüzü gradyanı üstü
   parlak rim-light. Ders renkleri illüstrasyonda KULLANILMAZ (UI'a ait).
2. **Tek ışık kaynağı:** her sahnede güneş/ufuk tek yönden — gölge ve rim-light hep aynı mantıkla.
   Işık yönü = umut metaforu (alt kenardan doğan ışık, motion kanonuyla aynı imza).
3. **Grenli doku:** düz dolgular üzerine ince grain (SVG turbulence/fractalNoise, düşük opaklık);
   parlak/plastik gradyan yasak.
4. **Figür dili:** insan figürü varsa yüz detayı minimal (göz-nokta, ifade duruşla); yaş kodu
   genç-nötr, cinsiyet-nötr varyantlar. Asla ders çalışan "mutsuz" figür.
5. **Sahne tipleri (DC'de birer örnek):**
   - Boş durum (paper): küçük, sakin, tek nesne + kısa gölge ("Bugün tekrar yok" eğri sahnesi).
   - Kutlama (dusk): doğan güneş + ConfettiDawn ile uyumlu parçacık dili.
   - Onboarding (dusk→paper geçişi): gece→şafak→gündüz ark — kavramsal köprünün görsel anlatımı.
   - Mola (dusk): nefes/gökyüzü, hareketsiz veya çok yavaş (reduced-motion'da statik).
6. **Ölçek/yerleşim:** spot (maks ~240px) — hero illüstrasyon yok; illüstrasyon içeriğin
   yerini almaz, boşluğu yumuşatır.
7. **Yasaklar:** emoji, stok-izometrik stil, indigo/alarm-kırmızısı, insan yüzünde kaygı mimikleri,
   ders renkleriyle illüstrasyon.

## DC yapısı (üretilecek)
`KIRO Illustrasyon Sistemi.dc.html`: üst bölüm gramer kartları (ışık, gren, palet, figür),
alt bölüm 4 sahne tipinin paper+dusk bağlamında canlı örnekleri; her örnekte "yap/yapma" çifti.
Tweaks: zemin (paper/dusk), gren yoğunluğu.

## Kaynaklar
`KIRO Safak Mimari.dc.html` (palet+gökyüzü) · `KIRO Durumlar.dc.html` (boş durum bağlamı) ·
MOTION_KANON_SPEC.md (ışık-süpürmesi imzasıyla hizalama) · kök CLAUDE.md (kanon).
