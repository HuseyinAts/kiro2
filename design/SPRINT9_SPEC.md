# KIRO2 — Sprint 9 Port Spec'i: AI & Destek (Grup 7)

Kapsam: **4 ekran** (Sokratik AI · AI Sohbet · İnteraktif Çözüm · Kaygı Ölçüm).
Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 8 DoD tamam. Bu sprint **Faz 4.5 (AI proxy)** ile kesişir: iki AI ekranı
prototipte `window.claude.complete` + betik yedeği kullanır — üretimde TÜM model çağrıları
sunucu proxy'sinden geçer (anahtar istemciye sızmaz, oran sınırı + günlük kota sunucuda).

---

## A · Ekran: Sokratik AI (`KIRO2 Sokratik AI.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="ai"`) + sohbet sütunu + 328px sağ ray (≤760px gizli).
**Rota:** `/koc/:soruId` — Soru Çözme çözüm kutusundaki "KIRO Koç ile adım adım" linkinden gelinir.

### Ürün kimliği — BİREBİR korunacak öğeler
- Üst bilgi pili: "Sokratik mod · cevabı vermez" + banner "Bu mod cevabı vermez — birlikte düşünür.
  Öğrenme etkisi korunur."
- Mesaj etiketleri: "yönlendiren soru" · "doğru — devam" · "son adım" · "çözüldü".
- **İpucu merdiveni** (sağ ray): Kavramı hatırlat → Yöntemi yönlendir → İlk adımı birlikte yap
  (kilitli adımlar kilit ikonlu) + "Çözümü göster (son çare)" + "Cevabı görmek yerine ipucu iste —
  getirim etkisi korunur."
- **Sokratik ilerleme**: bar + "Adım: ilişki → terimler → formül → değerler → sonuç." + teşvik kutusu.
- Hızlı chip'ler: "Bir ipucu daha ver" · "Örnek göster"; çözülünce "Çözdün — yeni soruyla baştan".

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- **İndigo #4338CA üç yerde:** banner metni rengi · "yönlendiren soru" etiket rengi · gönder butonu
  hover'ı → sırasıyla #C2452B (dawn) / #C2452B / `filter:brightness(0.94)`.
- "Tam isabet ✓" / "çözüldü ✓" METİN glyph'leri (betik içeriği) → üretim sistem-prompt'una
  "✓✗ karakteri kullanma" kuralı; etiket tiklerine bespoke SVG.
- "Çözümü göster" hover'ı #FEF2F2 → #FFF3EE.

### Port kararları
- `socratic` prop'u (Doğrudan mod karşılaştırması) PROTOTİP ARACIDIR — üretimde mod SABİT Sokratik;
  Doğrudan mod UI'ı taşınmaz. ("Qwen3-8B" model adı da UI'dan kalkar — kullanıcıya model reklamı değil,
  davranış sözü veriyoruz; alt bilgide yalnız "Türkçe öğretmen modeli".)
- Betik yedeği (SOC dizisi) üretimde YOK — model erişilemezse sakin ErrorState ("Koç şu an
  toparlanıyor — birkaç dakika sonra tekrar dene."; kopya onaya).
- +25 XP çözüm ödülü SUNUCUDAN (oturum sonucu yanıtında).

### Veri bağlama — ⚠ uç eksik
- Öneri: `POST /ai/socratic {soruId, messages[]}` → {mesaj, merdivenAdimi, cozuldu, xp?}.
  Merdiven adımı ve "çözüldü" tespiti SUNUCUDA (model çıktısı + kural); istemci sayaç tutmaz.
  Oturum geçmişi sunucuda saklanır (kaldığı yerden devam).
- Bağlam: soru + öğrencinin o konudaki θ'sı prompt'a sunucuda eklenir.

### DoD notları
- Sohbet `aria-live="polite"`; "düşünüyor…" durumu ekran okuyucuya da gider.
- Input Enter ile gönderir; boşken göndermez. 390px: ray gizli, merdiven bilgisi kaybolur (kabul).

---

## B · Ekran: AI Sohbet (`KIRO2 AI Sohbet.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="assistant"`) + sohbet + 320px bağlam paneli.
**Rota:** `/asistan`. Sokratik AI'dan farkı: soruya bağlı koç DEĞİL, genel çalışma asistanı
(konu anlatımı, mini test, tekrar tetikleme). İki ekran bilinçli ayrı — birleştirme kararı ürünün
(açık nokta değil; PORT_DURUM'da ikisi ayrı satır).

### Bloklar — BİREBİR
- Boş durum: "Bugün neyi çözelim, {ad}?" + 4 başlangıç kartı (adım adım açıkla · köklü sayılar ·
  TYT mini test · dünkü yanlışlar) — kart metinleri kullanıcının zayıf konularından kişiselleşir
  (üretimde `/topics` verisiyle; prototipte sabit).
- Composer: fotoğraf butonu + input + 3 chip (Adım adım açıkla · Benzer soru ver · Konuyu özetle).
- Alt uyarı: "KIRO AI hata yapabilir — önemli sonuçları kontrol et." — KORUNUR (güven dili).
- Bağlam paneli: aktif konu chip'i + son soru alıntısı + "Bu konuyu çalış" / "Benzer soru çöz"
  CTA'ları + "Önerilen — zayıf konuların" listesi (%'li, tıklayınca sohbete sorar).

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- Başlangıç kartı ikon zeminleri: #FEF2F2 (kırmızı-50) → #FBE8E2; #F5F3FF (menekşe-50) → #FFF3EE
  (mor yalnız Fizik bağlamında).
- Yerel `reply()` kural-motoru üretimde YOK (proxy düşerse sakin ErrorState; sohbet geçmişi korunur).

### Port kararları + açık nokta
- **Fotoğraf yükleme MVP'de?** Vision maliyeti + moderasyon ister. Öneri: MVP'de buton gizli;
  Faz 4.5'te `POST /ai/vision` ile açılır. (AÇIK NOKTA)
- "TYT mini test" ve "dünkü yanlışlar" chip'leri gerçek eyleme bağlanır: mini test → Soru Çözme
  set oluşturma; tekrar → FSRS kuyruğu (sohbet yanıtı + derin link).

### Veri bağlama — ⚠ uç eksik
- Öneri: `POST /ai/chat {messages[]}` → {mesaj, baglamKonu?, eylem?} (eylem: {tip: 'set'|'tekrar',
  ref}). Sistem prompt'u sunucuda; zayıf konu bağlamı sunucu ekler. Günlük mesaj kotası plana bağlı
  (Abonelik ekranıyla kesişir — Sprint 10).
- Sohbet geçmişi: `GET /ai/chat/history` (son oturum); "Yeni sohbet" sıfırlar.

### DoD notları
- Mesaj listesi `aria-live`; "yazıyor…" balonu duyurulur. 390px: bağlam paneli gizli (prototipte
  media-query YOK — porta eklenir, not düş).

---

## C · Ekran: İnteraktif Çözüm (`KIRO2 Interaktif Cozum.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="interaktif"`) + içerik (max 1000px). **Rota:**
`/interaktif/:id` (MVP pilotu: parabol). İçerik-tabanlı etkileşimli anlatım — formül ezberi yerine
davranış hissi ("Okuma değil — kaydırarak keşfet").

### Bloklar — BİREBİR
- Canlı denklem: y = **a**x² ± **b**x ± **c** (katsayılar renkli: a terracotta · b yeşil · c amber).
- SVG grafik: 300×240, izgara + coral parabol eğrisi + tepe noktası halkası; kaydırınca ANINDA güncellenir.
- 3 slider: a · açılım (−2…2, 0.1) · b · konum (−6…6, 0.5) · c · yükseklik (−6…6, 0.5).
- "Şu an" kartı: kollar yukarı/aşağı (∪/∩ glyph'i — matematiksel sembol, emoji değil; KALIR) ·
  açıklık (dar/orta/geniş/doğru) · tepe noktası (x, y).
- "KEŞFET" kartı: duruma göre 5 içgörü metni (a=0 doğruya dönüşür · |a| büyük daralır · …) — BİREBİR.
- "Mini görev" kartı: "a'yı negatif yap, tepe noktasını (0, 3)'e taşı" + "Kontrol et".

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- **"Kontrol et" hover'ı #4338CA (indigo)** → `filter:brightness(0.94)`.
- **Slider thumb gölgesi rgba(79,70,229,…) (indigo kalıntısı)** → rgba(255,111,92,…).
- KEŞFET kartı menekşe ailesi (#F5F3FF/#DDD6FE/#4C1D95) → dawn: zemin #FFF3EE→#FBF0DE gradyanı,
  kenar #F6D9CB, metin #2A2433.
- Eyebrow "AYT MATEMATİK · PARABOL" rengi #8B5CF6 (mor = Fizik rezervli) → mat mavisi #3B6FD4.
- Tepe noktası ikon zemini #FEF2F2 → #FBE8E2.

### Port kararları
- "Kontrol et" prototipte İŞLEVSİZ — portta çalışır: a<0 VE tepe=(0,3) kontrolü İSTEMCİDE
  (saf matematik, öğrenme motoru değil — kanona aykırı değil); başarıda yeşil onay + küçük XP
  (sunucu `POST /interactive/{id}/complete`).
- Grafik hesabı istemcide kalır (görselleştirme, ölçüm değil).

### Veri bağlama
- İçerik modeli: `GET /interactive/{id}` → {baslik, aciklama, parametreler, gorevler} — MVP'de tek
  pilot (parabol) gömülü de olabilir; uç Faz 4'te karara bağlanır (açık nokta).
- Tamamlama: `POST /interactive/{id}/complete`.

### DoD notları
- Slider'lar `aria-label`'lı (mevcut — koru); değerler `aria-valuetext` ("a = 1,2").
- Denklem satırı `aria-live="polite"` DEĞİL (her kaydırmada konuşmasın); "Şu an" kartı odaklanınca okunur.
- 390px: grid tek sütun (prototipte media-query YOK — porta eklenir, not düş).

---

## D · Ekran: Kaygı Ölçüm (`KIRO2 Kaygi Olcum.dc.html`) — ARAŞTIRMA ARACI

**Tema:** paper. **Rota:** `/arastirma/kaygi?asama=pre|post` — **öğrenci nav'ında YOK**;
kullanılabilirlik oturumu moderatörü açar. Üretim build'inde feature-flag arkasında
(`VITE_RESEARCH=1`) — son kullanıcıya sızmaz.

### ⚠ YASAL ÖN KOŞUL (ekranın kendi dipnotu — BİREBİR korunur)
"6 maddelik STAI-S kısa form uyarlaması … araştırma prototipi — **üretim kullanımı öncesi ölçek
lisansı ve etik kurul onayı gerekir.**" Bu koşul karşılanmadan ekran flag arkasından ÇIKMAZ.
(Veli onayı: 18 yaş altı katılımcı için KVKK + veli izni — Moderatör Kılavuzu'ndaki protokole bağlı.)

### Bloklar — BİREBİR
- Etik satırı: "**Test edilen sensin değil, ürün.** Doğru ya da yanlış cevap yok…" — KORUNUR.
- 6 madde × 4'lü Likert (Hiç/Biraz/Oldukça/Çok fazla; seçili = koyu mürekkep #2A2433) +
  "{n}/6 yanıtlandı" sayacı; hepsi dolmadan gönderilemez.
- Pre/post fazları (URL ya da prop); teşekkür kartları ("Hazırız — birlikte başlayalım." /
  "Teşekkürler — bugünkü katkın ürünü daha nazik yapacak.").
- Moderatör görünümü (katlanır): pre/post skorları + "Kriter · post ≤ pre" değerlendirmesi
  (karşılanmadıysa AMBER, kırmızı değil — zaten doğru) + "Sonraki katılımcı — yanıtları sıfırla".

### Port kararları
- Skorlama istemcide kalabilir (araştırma aracı, öğrenme motoru değil) ama kayıt localStorage
  yerine `POST /research/stai {kod, asama, yanitlar, skor}` — oturum verisi cihazda kalmasın
  (moderatör cihaz değiştirir). AÇIK NOKTA: araştırma verisi backend'i mi ayrı sheet mi.
- "Tura başla" → Canlı Demo linki prototip turuna özel; üretim akışında moderatör yönlendirir
  (link parametrik).

### DoD notları
- Likert butonları ≥44px (mevcut) + `aria-pressed`; madde metni `<label>` ilişkili.
- Skor katılımcıya ASLA gösterilmez (moderatör görünümü ayrı yetki — flag + kod).

---

## Sprint 9 açık noktaları
1. AI uçları openapi'ye eklenecek: `/ai/socratic` · `/ai/chat` (+ kota alanları) — Faz 4.5 sözleşme işi.
2. Fotoğraf/vision MVP'de mi? (öneri: hayır — buton gizli, Faz 4.5'te açılır)
3. AI günlük kota ↔ Abonelik planı eşlemesi (Sprint 10'da Abonelik ekranıyla birlikte).
4. İnteraktif içerik ucu (`/interactive/*`) mi gömülü pilot mu?
5. STAI ölçek lisansı + etik kurul + araştırma verisi backend'i — flag açılmadan önce.
6. AI ErrorState kopyaları onaya: "Koç şu an toparlanıyor — birkaç dakika sonra tekrar dene."

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 7 bitti** → PORT_DURUM'da Grup 7'ye tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Sohbet logu `role="log"` + `aria-live="polite"` (yalnız yeni mesaj); "yazıyor…" aynı bölgede tek satır.
- Giriş alanları `aria-label` (mevcut); hızlı-yanıt çipleri gerçek buton.
- İnteraktif kaydırıcılar `aria-label` + `aria-valuetext` ("a = 1,5"); grafik özeti metinle.
- Kaygı Ölçüm: ölçek satırları `fieldset/legend` + radiogroup; skor katılımcıya OKUNMAZ (SR dahil — yalnız moderatör görünümü).
