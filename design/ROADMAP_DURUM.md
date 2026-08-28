# KIRO2 — Roadmap Durum & Kalan İşler

Bu belge `KIRO2_DERIN_ANALIZ.md` yol haritasının **uygulanan** kısımlarını ve tasarım-aracı dışında kalan (gerçek kod tabanı / araştırma / backend gerektiren) **kalan** işleri kaydeder. Referans: derin analiz raporu Bölüm 4.

## ✅ Uygulandı (bu prototipte)

### P0 — Dürüstlük & tutarlılık
- **P0.1 Tek "bugün" modeli** — `kiro-data.js`'e `bugunBilgi()` + `buHafta()` eklendi. Öğrenci Paneli tarih etiketi ve Haftalık Plan (7 gün + haftaRange) artık **canlı** tek referanstan; Geri Sayım zaten `Date.now()`. (Sınav Sonuç'taki tarih = geçmiş deneme, bilinçli sabit.)
- **Backend-öncesi boşluklar — ✅ YAPILDI (bu tur)** — Giriş & Kayıt (№30), Ödevlerim (№31, öğretmen Ödev Atama'nın öğrenci ucu), Ödeme (№32); API sözleşmesine auth/assignments/sync/notifications/billing/league+duel uçları; types.ts + api-client.ts eşitlendi. Bkz. DEVIR §22s.
- **Mobil uyarlama — ✅ ilk teslim (bu tur)** — `KIRO2 Mobil.dc.html` (№33): 8 telefon-çerçeveli kritik ekran (Bugün · Soru Çözme · FSRS · Ödevlerim · Kutlama · Lig · Sokratik · Çevrimdışı), 390pt + safe-area. Bkz. DEVIR §22u.
- **P0.2 Sunum güncel** — Canlı Demo turu 8 → **12 sahne**; sunum 11 → **12 slayt** ("Günün ötesi", §22t) + PPTX/PDF yeniden export (Geri Sayım · Haftalık Plan · Başarımlar · Abonelik yeni ekran görüntüleriyle eklendi; `screenshots/flow/`).
- **Bonus** — View Transitions "skipped transition" konsol hatası 50 dosyada giderildi (`navigation:auto` kaldırıldı; micro-interaction + `:focus-visible` + reduced-motion korundu).

### P1 — Vaadi gerçeğe yaklaştır
- **P1.4 Gerçek AI** — **AI Sohbet** ve **Sokratik AI** artık gerçek `window.claude.complete` çağırıyor. Sistem-prompt'lar en zayıf konulara (`topics`) dayalı, kaygı-duyarlı, Sokratik (cevabı vermeden yönlendiren). "yazıyor…" göstergesi + API hatasında scripted fallback. Sokratik'te merdiven/ilerleme hissi korundu (hibrit).
- **P1.5 Kaygı-mekaniği yumuşatıldı** — Boss yenilgisi "Ejderha seni yendi" → **"Henüz değil · kaybeden yok, sadece 'henüz' olan var"**; retry "Hazırlan, geri dön". (Literatür: rekabet/yenilgi çerçevesi kaygılı öğrenciyi caydırır.)
- **P1.6 Paywall paradoksu** — En kanıtlı araç (FSRS) artık **ücretsiz katmanda tadımlık** (günlük 5 kart) + temel hâkimiyet takibi; Premium'da sınırsız.

## ⏳ Kalan — bu araç dışında (gerçek kod / araştırma / backend)

### P1 (kalan)
- **Rekabeti opsiyonel yap — ✅ YAPILDI (bu tur, prototipte)** — Lig'e "Sıralamayı gizle/göster" düğmesi + `siralamaGizli` tweak (varsayılan görünür → ürün kararı zorlanmadı); "sen vs dün" hero zaten birincil. `sakinMod`'da düşme bölgesi amber + rekabet kopyaları yumuşatıldı; `sakinMod=false` eski hâli A/B için verir. Bkz. DEVIR §22g.
- **Geri Sayım A/B** — kaygı-nötr "hazırlık ilerlemesi" alternatif görünümü; hangisinin kaygıyı düşürdüğü **kullanıcı testiyle** belirlenmeli.

### P2 — Sağlamlaştır & doğrula
- **Kaygıyı ölç** — `USER_TESTING.md` planını çalıştır (pre/post durumluk kaygı + kavrama). Ürünün 1 numaralı doğrulanmamış iddiası. **İnsan + gerçek katılımcı gerektirir.** Saha yüzü hazır: STAI-S anketi (`KIRO2 Kaygi Olcum`) + **moderatör kılavuzu (`KIRO2 Moderator Kilavuzu.dc.html`, bu tur)** — 60 dk oturum akışı, akran-dili script'leri, etik/onam kontrol listesi. Kalan: ölçek lisansı + etik kurul onayı + gerçek katılımcılar.
- **Kapsam: EA/Sözel — ✅ çekirdek + ünite ağacı (bu tur) / tam havuz üretimde** — `katalogKonular` (53 persona-bağımsız konu) + 8 çözümlü soru + **`katalogUniteler` (edb/tar/cog ünite ağacı; Alan Kütüphanesi drill'i ünite başlıklı, DEVIR §22p)**. Kalan: fel/din ağacı, tam soru havuzu, EA/Sözel persona — **ürün kapsamı kararı + içerik ekibi işi.** Bkz. DEVIR §22l+§22p.
- **Veli satın-alma yüzeyi — ✅ YAPILDI (bu tur)** — Veli Paneli ROI bölümü + `KIRO2 Abonelik.dc.html?rol=veli` veli-yüzü paywall (siz-dili, kanıt şeridi, "öğrenci fiyat baskısı görmez" ilkesi). Bkz. DEVIR §22h.
- **Erişilebilirlik sıkı-AA — ✅ YAPILDI (bu tur, prototipte)** — `ACCESSIBILITY.md`'deki 6 öneri uygulandı: gri→`#6B6478`, amber→`#9A5D0D`, sabit coral metin→`#C2452B` (yalnız aydınlık ekranlar), tüm ikon düğmeleri + form alanlarına `aria-label`. Runtime denetimi: adsız öğe 0, koyu regresyon 0. Bkz. DEVIR §22c. (Üretim kod tabanında da aynı token'larla sürdürülebilir.)

### P3 — Ölçek & gerçek ürün
- **Fallback borcunu azalt — ✅ YAPILDI (bu tur)** — `kiro-seed.js` senkron ikizi (`window.__KIRO`, <head>'de klasik script, support.js'ten önce) → 32 ekran K'yı ilk render'da SENKRON okur; inline literal fallback'ler silindi (`const K = this.state.K || window.__KIRO; if(!K) return {}`). Tek eşitleme noktası: kiro-data.js değişince kiro-seed.js'i yeniden üret. Bkz. DEVIR §22b.
- **Sistematik durum yönetimi — ✅ standart tasarlandı (bu tur)** — `KIRO Durumlar.dc.html` spec ekranı: yükleniyor/boş/hata üçlüsünün kanonik örnekleri (açık+koyu) + kaygı-duyarlı kopya formülleri; üretimde Skeleton/EmptyState/ErrorState bileşenlerine gömülür (BILESEN_ENVANTER §B). Bkz. DEVIR §22k.
- **Gerçek backend** — `KIRO2 API Sozlesmesi.dc.html` sözleşmesini uygula; gerçek IRT kalibrasyonu + madde havuzu + FSRS zamanlayıcı (genişleyen aralık). `import('./kiro-data.js')` → `fetch`.
- **Gerçek kod tabanı** — `design_handoff_kiro2/` paketiyle React/RN/SwiftUI'da uygula.
- **Cihaz/ekran-okuyucu testi** — `ACCESSIBILITY.md` manuel test listesi (VoiceOver/TalkBack, font %200, güneş ışığı, renk körlüğü). **Gerçek cihaz gerektirir.**

## Özet
Raporun **inşa edilebilir** P0/P1 maddeleri bu prototipte tamam — en kritik ikisi dâhil: **gerçek AI** (bilim-vaadini gerçeğe yaklaştırır) ve **kaygı-mekaniği + paywall** düzeltmeleri (kaygı-tezi çelişkisini azaltır). Kalanlar doğaları gereği **gerçek katılımcı, gerçek cihaz ya da üretim kod tabanı** gerektirir ve handoff paketiyle o ortama taşınır. Ürünün iki temel iddiasından biri (kanıt-temelli) artık kısmen **çalışıyor**; diğeri (kaygı-duyarlı) artık **ölçülmeye hazır**.
