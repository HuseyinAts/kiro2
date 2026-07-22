# KIRO2 — Sprint 2 Port Spec'i: Auth hunisini tamamla + kabuk

Kapsam: **2 bileşen bağlama/test** (SideNav · MasteryBadge) + **3 ekran**
(Hesap Kurtarma · Onboarding · Öğrenci Paneli). Sprint 1'in devamı: Grup 1 (auth)
biter, Grup 2 (kabuk + panel) açılır. Piksel referansı her zaman kaynak DC'dir;
bu spec kopya, durum ve davranışın **kaybolmaması** içindir.

Önkoşul: Sprint 1 DoD tamam (Button · Card · StatusChip · Giriş · Ödevlerim) +
kalibrasyon süreleri PORT_DURUM.md'ye yazılmış.

---

## A · Bileşenler

### A1 · SideNav (`ui-starter/SideNav.tsx` — hazır, bağlanacak + test)
- Bu sprintte ilk kez gerçek ekranda kullanılıyor (Öğrenci Paneli, `active="panel"`).
- 250px sabit; ≤760px'te 64px ikon-only (`collapsed`) — panel DC'sindeki `.rnav` media-query davranışı birebir.
- `renderLink` router entegrasyonu: react-router `Link`'e bağla; sayfa yenilenmez.
- Test: preset başına (öğrenci/veli/öğretmen) nav öğeleri + aria-current; axe temiz.

### A2 · MasteryBadge (`ui-starter/MasteryBadge.tsx` — hazır, bağlanacak + test)
- Panelde ders satırında `badge pct trend="up"` olarak kullanılıyor (≤760px gizli, `.rsec`).
- Test: tier sınırları (39→Tanıdık · 40→Yetkin · 64→Yetkin · 65→Usta · 85→Fethedildi), açık palet.

---

## B · Ekran: Hesap Kurtarma (`KIRO2 Hesap Kurtarma.dc.html`)

**Tema:** paper. Arka plan + kart Giriş ekranıyla AYNI (`max-width:460px`, radius 20, aynı gölge).
**Rota önerisi:** `/hesap-kurtarma`.

### Durum makinesi
`eposta → kod → sifre → tamam` + `hint` (amber) + `goster` (şifre görünürlüğü) + `yeniden` (kod tekrar gönderildi bayrağı). "Adresi değiştir" → `eposta`'ya döner, kod sıfırlanır.

### Kopya — BİREBİR (değiştirme)
| Yer | Metin |
|---|---|
| Üst sağ link | Girişe dön |
| Adım etiketi | Adım 1 / 3 · Adım 2 / 3 · Adım 3 / 3 (uppercase, #9A93A5) |
| 1 başlık (serif italik 30px) | Hesabını birlikte açalım. |
| 1 alt metin | Şifre unutmak da çalışmanın bir parçası. E-postanı yaz, sana 6 haneli bir kod gönderelim. |
| 1 CTA | Kod gönder |
| 1 dipnot | Adresini hatırlamıyorsan okul e-postanı da deneyebilirsin. |
| 2 başlık | Kod yolda. |
| 2 alt metin | **{maskeliAdres}** adresine 6 haneli bir kod gönderdik. Gelmesi bir dakikayı bulabilir. |
| 2 CTA | Doğrula |
| 2 linkler | Adresi değiştir · Kodu yeniden gönder → tıklanınca "Gönderildi — gelen kutuna bak" |
| 2 dipnot | Kod gelmediyse spam klasörüne bakmak genelde yeter. |
| 3 başlık | Yeni şifreni seç. |
| 3 alt metin | Hatırlaması kolay, tahmin etmesi zor bir şey iyi gider. |
| 3 CTA | Şifreyi güncelle |
| 4 başlık | Hazırsın. |
| 4 alt metin | Şifren güncellendi. Serin ve ilerlemen aynen yerinde — kaldığın yerden devam. |
| 4 CTA | Panele dön → Panel rotası |
| Sayfa altı | Takıldıysan destek ekibine yaz — gerçek bir insan, okul saatlerinde ~10 dk içinde döner. |

### Hint'ler — BİREBİR (amber kutu #FBF0DE/#F2D9AC, metin #9A5D0D; ASLA kırmızı)
- E-posta geçersiz: "Bu adres eksik görünüyor — bir kez daha bakar mısın?"
- Kod ≠6 hane: "Kod 6 haneli olmalı — acele yok."
- (Yanlış kod, sunucudan — aynı ton, ör. "Bu kod tutmadı — yenisini gönderebiliriz." → ErrorState kopya standardı.)

### Ayrıntılar
- E-posta maskesi: ilk 2 karakter + `•••` + `@domain` (i<2 ise maskesiz).
- Kod input: `inputMode="numeric"`, yalnız rakam, max 6; 24px/800, `letter-spacing:0.42em`, ortalı, tabular-nums.
- Şifre kural listesi CANLI (yazarken renklenir): "En az 8 karakter" · "Harf ve rakam bir arada" (Türkçe harfler dahil) · "Tahmini zor" (12345678/password/sifre123 önekleri reddedilir). ok → daire #1FB683 + metin #17936B; değil → #D9D2C7/#9A93A5.
- Başarı adımında yeşil onay dairesi (#E4F7F0 zemin, #17936B tik, 58px).

### Veri bağlama (Faz 4)
- 1: `POST /auth/recover` · 2: `POST /auth/recover/verify` → `{ resetToken }` · 3: `POST /auth/recover/reset`.
- "Kodu yeniden gönder" → `POST /auth/recover` tekrar; buton etiketi değişir, yeni istek atılana kadar disabled kalabilir.
- Mock modda adımlar istemcide ilerler (prototipteki gibi).

### Ekran DoD notları
- Adım etiketi `aria-live="polite"` bölgesinde; her adım değişiminde başlığa focus.
- 390px: kart zaten akışkan; kod input'unda letter-spacing taşması test edilecek.

---

## C · Ekran: Onboarding — misafir yerleştirme (`KIRO2 Onboarding.dc.html`)

**Tema:** paper (Giriş ile aynı gradyan). **Rota önerisi:** `/onboarding` — **auth GEREKMEZ** (misafir hunisi; route guard bunu istisna tutar).

### Durum makinesi
`calib (soru 1-6) → hazir`. Stepper 3 adım: "Hoş geldin" (hep tamam ✓) → "Seviye tespiti" (calib'de aktif) → "Planın hazır" (hazir'da aktif). Tamam = #1FB683 dolu ✓; aktif = #FFF3EE zemin + 2px #FF6F5C kenar; bekleyen = #ECE6DD. Bağlayıcı çizgi tamamsa yeşil, değilse #E2E5EB.

### Kopya — BİREBİR
| Yer | Metin |
|---|---|
| Üst bar | Adım {2|3} / 3 · Hesabın var mı? Giriş yap · Atla → Panel |
| Calib başlık (Hanken 26px/800 — serif DEĞİL) | Seviyeni öğreniyoruz |
| Calib alt metin | Sadece **6 soru · ~2 dakika**. Her cevap sonrakini seçer — tahmin değil, ölçüm. |
| Soru kartı üstü | TYT Matematik (mavi chip) · Soru {n} / 6 |
| Tahmin kutusu | Seviye tahmini netleşiyor · {ölçülüyor|temel|orta|orta-üst} · Temel / Orta / İleri |
| Calib dipnot | Hesap oluşturmaya gerek yok — önce değerini gör, sonra kaydet. |
| Hazir başlık | Planın hazır! |
| Hazir alt metin | 6 soruda seviyeni ölçtük — **{n}/6 doğru**. Sana özel 30 günlük yol haritasını kurduk; zayıf konuların öncelikli. |
| 3 stat kutusu | Tahmini seviye {Temel|Orta|Orta-üst|İleri} · Net potansiyeli ~{n} · Odak konu {konu} |
| İlk hafta şeridi | İLK HAFTAN · Gün 1 · {odak} temel · Gün 2 · Paragraf · Gün 3 · Deneme |
| CTA'lar | Çalışmaya başla → · Hesabını oluştur ve ilerlemeni kaydet · Testi yeniden çöz |

### Davranış
- Cevap tıklanır tıklanmaz sonraki soru (doğru/yanlış GÖSTERİLMEZ — yerleştirme, ceza yok).
- Canlı tahmin barı: gradyan #FCA5A5→#FCD34D→#86EFAC, beyaz/coral toplu iğne, `left = 12 + oran×76 %`, 0.35s geçiş.
- Bitişte konfeti — **ConfettiDawn bileşeni kullan** (`useReducedMotion`: azaltılmış harekette yok). Prototipteki inline burst taşınmaz.
- Skor eşlemesi: ≤2 Temel · 3 Orta · 4 Orta-üst · ≥5 İleri; net ~`225 + doğru×13` (180-360 kıskaç); odak konu: ≥4 doğru → en zayıf mat konusu, 2-3 → Problemler, <2 → Temel İşlemler.

### ⚠ Kanon düzeltmeleri (prototip hataları — porta TAŞINMAZ)
- "Çalışmaya başla" hover'ı prototipte `#4338CA` (indigo) — **YASAK**. Port: `filter:brightness(0.94)` (diğer coral CTA'larla aynı).
- Stepper ✓ işareti metin "✓" değil, Button/StatusChip'teki bespoke tik SVG'si olsun.

### Veri bağlama (Faz 4)
- Sorular İSTEMCİDE SEÇİLMEZ (prototip `catBankMat`'ten seçiyordu — motorlar sunucuda): yerleştirme `POST /cat/next` ile madde-madde ilerler (6 madde, yerleştirme modu); θ kestirimi sunucudan gelir, tahmin barı onu gösterir.
- Misafir sonucu: θ yerelde tutulur; "Hesabını oluştur" → Kayıt'a gider, `POST /auth/register` gövdesinde taşınır (ADR-001, sözleşmede hazır).
- Mock modda: `kiro-data.js → catBankMat` merdiveni (prototipteki 6 konu sırası) aynen.

### Ekran DoD notları
- Seçenek kutuları buton semantiği (`role="button"` değil gerçek `<button>`), hit ≥44px.
- 390px: seçenek grid'i `1fr`'a düşer; 3 stat kutusu alt alta.

---

## D · Ekran: Öğrenci Paneli (`KIRO2 Ogrenci Paneli.dc.html`)

**Tema:** paper (#F7F4EF). **Layout:** SideNav (250px, `active="panel"`) + içerik (max-width 1280px). **Rota önerisi:** `/panel` (girişte varsayılan rota, rol=öğrenci).

### Topbar (66px sticky, `rgba(250,247,242,0.86)` + blur(8), alt çizgi #ECE6DD)
- Arama: beyaz kutu, "Konu, soru veya deneme ara…" + ⌘K rozeti (≤760px gizli). Sprint 2'de görsel kabuk; davranış sonraki sprint.
- Seri pili: amber (#FBF0DE/#F2D9AC), alev ikonu, `{seri}` tabular + "gün".
- XP pili: beyaz, coral seviye karesi `{seviye}` + `{xp}` (tr-TR binlik) + "XP".
- Ayarlar + Bildirim ikon butonları (38px, aria-label var — koru); bildirim noktası #E0593F.

### İçerik blokları (sıra korunur)
1. **Selamlama:** "Merhaba, {ad}" (29px/800) + "Bugün **2 görevin** kaldı — serini **{seri+1}. güne** taşımana 1 çalışma kaldı." + sağda uzun tarih.
2. **Hero — Bugünün planı:** 1fr/300px grid. Sol: coral rozet "Bugünün planı", görev başlığı + "{ders} · {n} soru · ~{dk} dk · zayıf konun olarak işaretlendi", ilerleme barı + "3/5 görev", CTA'lar "Çalışmaya devam et" (coral, play ikonu) → Soru Çözme · "Deneme başlat" (beyaz) → Adaptif Test. Sağ (#FBF8F3): günlük hedef halkası (SVG, 128px, dasharray 351.9) "%60 · günlük hedef" + "45 dk çalıştın · hedef 75 dk".
3. **KPI ×4:** Ortalama başarı %72 (+4) · Çözülen soru 1.248 (+186) · Tamamlanan sınav 14 (+2) · Çalışma süresi 47 sa (bu ay). Yeşil trend oku #17936B; sayılar 30px/800 tabular.
4. **Ders Bazında Hâkimiyet** (sol sütun): başlık + "IRT yetenek (θ) tahminine göre · son 30 gün" + track chip'i. Ders satırı: renk noktası · ad · θ chip'i (≤760px gizli) · **MasteryBadge** · trend · %n · ders-renkli bar. Ders renkleri açık palet (Sprint 1 ile aynı).
5. **Haftalık İlerleme** (görünürlük prop'u): sparkline (accent, %10 dolgu alan) + "+8,4 net / bu hafta" + Pzt…Paz.
6. **Günlük Görevler** (sağ sütun): 3/5 rozeti; tamamlar #FBF7F1 zemin + yeşil tik + üstü çizili; bekleyenler kenarlıklı, XP değeri coral ("FSRS tekrarını bitir +50" → FSRS · "1 deneme çöz +80" → Soru Çözme).
7. **Son Sınavlar:** "Tümü →"; satır: TYT/AYT karesi · ad · "{n} gün önce · D Y B / net meta" · yeşil skor chip'i (#ECFDF5/#047857).

### Props → üretim karşılığı
- `yogunluk` (Rahat/Kompakt) → kullanıcı tercihi, Ayarlar'a bağlanacak yerel tercih (localStorage); Kompakt = padding/gap sıkılaşması (prototipteki `.yogun-kompakt` değerleri).
- `examTrack` → `/me` persona alanından gelir; Sayısal dışı track'lerde ders seti değişir (EA/Sözel/Dil satır setleri prototipte).
- `showWeeklyTrend` → veri yoksa (yeni kullanıcı) blok gizlenir.

### Veri bağlama (Faz 4)
- `GET /me` (ad, seri, xp, seviye, track) · `GET /subjects` (hâkimiyet+θ) · `GET /exams/last` (son sınavlar + net meta) · `GET /level` (XP eşiği) · `GET /review/due` (görev "FSRS tekrarını bitir" durumu).
- Bugünün planı: plan görevi kaynağı Haftalık Plan ekranıyla ortak (sonraki sprint); şimdilik mock görev.
- Üç durum: Skeleton (hero + KPI + liste iskeletleri, zıplamayan) · EmptyState (yeni kullanıcı: KPI'lar "—", hâkimiyet "İlk soruların bekliyor" kopyası) · ErrorState (sakin amber).

### Ekran DoD notları
- 390px: `.rnav` 64px ikon-only; `.rhero`/`.rtwo` tek sütun; `.rkpi` 2→1 sütun; arama gizli — prototip media-query'leri birebir.
- Tüm sayılar tabular-nums (seri, XP, KPI, %n, skor) — kanon lint kapsamında görsel kontrol.
- Selamlamadaki "2 görevin" mock'ta sabit; canlıda görev sayacına bağlanır.

### Açık soru (kullanıcıya)
- Günlük görev kopyası "Streak'i koru" — anglicism. Seri pili "gün" diyor; "Seriyi koru" mu yazılsın, prototip birebir mi kalsın? (Karar gelene dek birebir port.)

---

## Ölçüm
Sprint 1 kalibrasyonuyla karşılaştır: ekran-başı süre beklenen aralıkta mı?
Sapma >%40 ise PORT_DURUM.md tahmin formülünün katsayısını güncelle.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Hesap Kurtarma: adım değişiminde `h1` programatik odak alır (SR akışı); kod inputu `inputmode="numeric"` + `autocomplete="one-time-code"`; şifre-kural checklist'i `aria-live="polite"`.
- Onboarding Adım 1 (ton): `role="radiogroup"` + `aria-labelledby`; seçenekler `role="radio"` + `aria-checked`; yanıt kutusu `aria-live="polite"`; "Bu soruyu geç" gerçek buton.
- Onboarding yerleştirme: şıklar BUTON (tek dokunuş ilerletir — radiogroup değil); seviye çubuğu dekoratif `aria-hidden` + metin eşdeğeri ("Seviye tahmini: orta").
- Öğrenci Paneli: KPI kartlarında başlık→değer okuma sırası DOM'da; grafikler tek cümlelik `aria-label` özetle (Veri-Viz kanonu); nav rayında `aria-current="page"`.
