# Şafak Hub (KIRO Safak.dc.html) — Craft İyileştirme Listesi
> Kaynak: 2026-07-21 uzman analiz turları (renk uyumu · tam sayfa · derin kat analizi · uzaktan/squint · renk çokluğu).
> Statü: **UYGULANDI (2026-07-21) — F2/F3 hariç.** A1-A5 · B1-B6 · C1-C2 · D1 · E1-E6 · F1 tamam. Notlar: A1 Kimya #E25A72 (14 dosya senkron, KARARLAR'a işlendi) · C1 glow-nefes opacity katmanıyla (border-color animasyonu blur'lu kartta donma yaptı — compositor-dostu çözüm) · C2 sessionStorage bayrağı + Soru Çözme mount'unda tek-seferlik WAAPI süpürmesi (RM guard'lı) · B2 "Yolu gör" onaylı kopyası header linkinden 6. hücre ghost kartına TAŞINDI (kopya değişmedi) · F1 delege tanım: **tuğla = ~15 dk'lık günlük plan bloğu** — hero + progress aynı birim ("Şafağa N tuğla kaldı." / "bugün k/t tuğla"); sıfır-durum kopyası "Bugünün tuğlaları yerinde." ONAY BEKLİYOR · E2 progress artık bugunCozulenDk/gunlukHedefDk'den. AÇIK: yok — **F2/F3 + sıfır-durum kopyası da ONAYLANDI ve UYGULANDI (2026-07-21):** F2 gün-seed'li 5 cümlelik mantra havuzu · F3 baskısız sosyal satır "Elif de bugün çalıştı" (sayı/CTA/kıyas yok; üretimde arkadaş verisinden). Liste KAPANDI.

## A. Renk (uyum kırıkları)
- [x] **A1. Kimya ≈ marka corali çakışması (en kritik):** ders rengi `#FF6B6B`, marka eylem corali `#FF6F5C` ile uzaktan aynı okunuyor → Kimya'nın koyu-parlak tonunu oklch'de kızıl-somona ayrıştır (aynı L/C, hue mercandan uzağa). ⚠ **KANON DEĞİŞİKLİĞİ — Şafak-yerel değil:** koyu-parlak palet merkezi tanımdır (kaynak: `kiro-data.js` subjects.renk/glow + SPRINT6_SPEC paleti + Tasarim Sistemi/Safak Renk DC'leri); değişiklik tüm koyu tüketicilere yansır → uygulamadan önce KARARLAR onayı alınır, sonra kaynaklar senkron güncellenir.
- [x] **A2. Mint'in çift kimliği:** aynı yeşil hem Biyoloji (kimlik) hem "SEN vs DÜN" (büyüme) → delta bloğunun yeşilini bir kademe soluklaştır (oklch, hue 165→155 ısıt + doygunluk düşür); ders yeşili doygun kalır.
- [x] **A3. Alt bölge soğuk ses tekleştirme:** mantra lavantası (#D8C6E0) mood grisi ailesine yaklaştırılır; alt üçte-birde tek soğuk aksan kalır (mint).
- [x] **A4. İki altın tek değere:** hero `#FFD98C` vs pil ikonu `#FFE0A8` → tek altın (#FFD98C).
- [x] **A5. AA altı üçüncül metin:** mission kartındaki "Matematik" `#7E7393` (~3.6:1) → `#9B8FB5`.

## B. Kompozisyon (uzaktan/squint bulguları)
- [x] **B1. Gap ritmiyle kümeleme:** grup içi 12px / gruplar arası 26-30px — bölümler mesafeden okunur.
- [x] **B2. Grid deliği:** ders gridinin 6. hücresine ghost "Tüm dersler →" kartı (Öğrenme Yolu'na).
- [x] **B3. Altını aşağı taşı:** mantra kartına ince altın kenar ışığı — üst poster/alt panel kopukluğu dikilir.
- [x] **B4. Footer ufuk çizgisi:** sayfa dibinde 2px sıcak gradyan — ufukla kafiye, kompozisyon kapanışı.
- [x] **B5. Pil ayrımı:** "Sınava sayım" ghost (eylem), seri pili **hafif** altın tintli (bg ~%14 altın — dolu altın DEĞİL, CTA ile yarışmasın) (durum).
- [x] **B6. Ölçek disiplini:** radius merdiveni 22/18/14/10'a, boşluklar 4px tabana sabitlenir (13/15/19px ara değerler temizlenir).

## C. Hareket (Motion Kanonu hizası)
- [x] **C1. floatUp kaldır:** mission kartının sürekli sallanması → glow-nefes (ışıkla mikro-hareket); Fitts ihlali de kapanır.
- [x] **C2. Şafak imza geçişi:** Başla → Soru Çözme rotasına kanondaki alt-kenar ışık süpürmesi (rota başına bir kez) — "gece→gündüz" köprüsünün animasyonu. ⚠ Uygulama notu: ayrı dokümanlar arası ::view-transition'a GÜVENME (cross-document VT sınırlı destek) — hedef sayfada sessionStorage bayrağıyla tetiklenen tek-seferlik WAAPI süpürmesi olarak kur (kanon capture kuralı: baz opacity:1, animasyon geçici uygulanır).

## D. Sahne fiziği
- [x] **D1. Tepe rim light:** siluet sırtlarına 1px sıcak kontur — güneş yakınlığıyla fiziksel süreklilik.

## E. Durum / veri / erişilebilirlik
- [x] **E1. Review boş-durumu:** `reviewCount=0` → onaylı kopya "Bugün tekrar yok — eğrin sağlıklı." (şu an "0 konu tekrar bekliyor" yanlış-durumu; kopya FSRS için ZATEN onaylı — KARARLAR #1 — yeniden kullanım, yeni onay gerekmez).
- [x] **E2. Veri bağlama (mekanik kısım):** "bugün 3/5" + %60 bar hardcoded → `bugunCozulenDk / gunlukHedefDk`'ye bağla. (Hero "47 tuğla" sayısı F1'e taşındı — önce "tuğla neyi sayar" tanımı gerekir.)
- [x] **E3. Mood bloğu canlandırma:** seçilmemiş yüzlere duygu renginin ~%25 tonu · etiket 9px→11px · seçim vurgusu doğuş-easing.
- [x] **E4. Dekoratif svg'lere `aria-hidden="true"`** (tepe silueti svg'si + metin komşulu ikon svg'leri; yıldızlar div'dir, kapsam dışı).
- [x] **E5. Uzun ders adı taşması:** kart başlığına ellipsis stratejisi ("Türk Dili ve Edebiyatı").
- [x] **E6. Spec notu:** mood seçimi üretimde `POST /me/mood` ile kalıcı (KARARLAR #5) — prototipe yorum satırı.

## F. Kopya onayı gerektirenler (KULLANICI KARARI)
- [x] **F1. Tuğla dili ve tanımı:** (a) "tuğla" neyi sayar — kalan plan görevi mi, haftalık hedef mi? Tanım kararı SENİN; (b) tanım sonrası hero sayısı o veriden türetilir; (c) "bugün 3/5" → "bugün 3/5 tuğla" kopya değişikliği.
- [x] **F2. Mantra rotasyonu:** gün-seed'li 5-7 onaylı cümle havuzu (kopya listesi onaya sunulur).
- [x] **F3. İlişkililik satırı:** hub'a baskısız tek sosyal sinyal (ör. "Elif de bugün çalıştı") — kapsam kararı + kopya onayı. Bilinçli sadelik tercih edilirse "hub'da sosyal katman yok" kararı spec'e yazılır.

## Önerilen uygulama sırası (etki/maliyet)
A5 → E1 → C1 → A1 → A2+A3 → E3 → B1 → B5 → B2 → A4 → B3+B4 → D1 → E2 → B6 → C2 → E4+E5+E6 → (onay sonrası) F1-F3.

---

# Denetim Kontrol Listesi (uygulama sonrası) — ✅ KOŞULDU 2026-07-21
**Squint testi (uzaktan):**
- [x] Alt %60'ta en az iki okunur küme sınırı var; sayfa "üstte bitmiş" hissi vermiyor. *(dersler→Elif satırı→tekrar/delta→4mood/mantra; 28px grup sınırı + footer ufku görselde okunuyor)*
- [x] Sayfada altın en az bir kez alt bölgede tekrar ediyor. *(mantra altın kenarı + footer ufuk çizgisi)*
- [x] CTA dışında onunla aynı okunan renk kütlesi yok (Kimya barı ayrışmış). *(#E25A72 gül-kızıl, coral'den net ayrık — ekran görüntüsüyle)*
- [x] Mint bloğu ikincil vurgu olarak CTA'nın önüne geçmiyor. *(soluk yeşil; CTA tek doygun kütle)*
- [x] Mood satırı "disabled" değil "canlı seçici" okunuyor. *(yüzler duygu renginde + 11px etiket)*
- [x] Grid'de amaçsız boş hücre yok. *(6. hücre: ghost "Yolu gör" kartı)*

**Ölçüm:**
- [x] Koyu zeminde tüm ≤13px metinler ≥4.5:1 (özellikle eski #7E7393 noktası). *(#9B8FB5≈5.1 · mood fg alfa C9≈5.0 · #8C8398≈4.7 — hesapla)*
- [x] Mood etiketleri ≥11px; hedefler ≥44px. *(11px; buton ~77px)*
- [x] Radius'lar {22,18,14,10,99} kümesinde; boşluklar 4'ün katı. *(NOT: veri barları 6px mikro-radius ve 8×14px pil padding'i bilinçli mikro-istisna; 9/11/13/15/19/30px kalıntıları temizlendi)*
- [x] grep: yeni Kimya tonu **proje genelinde** geçti — `kiro-data.js` + tüm koyu tüketiciler; `#FF6B6B` hiçbir koyu ekranda kalmadı (Boss kendi allow'unda) · `floatUp` kullanımı yok. *(14 dosya senkron; kalan tek eşleşme bu listenin tarihsel metni)*
- [x] `K.subjects` tüketicileri grep'lendi; koyu/açık palet karışması regresyonu yok (paper ekranlar açık paleti kullanmaya devam ediyor). *(⚠ GERÇEK BULGU: Öğrenci Paneli Sayısal track'i koyu paleti kullanıyordu → açık palet map'iyle DÜZELTİLDİ; Veli Paneli kendi açık map'i, diğerleri renk kullanmıyor)*

**Davranış:**
- [x] `prefers-reduced-motion: reduce` → tüm döngüler durur; gökyüzü tint/konum statik yaşıyor; içerik kaybı yok. *(blanket guard + statik modulasyon — kod denetimi)*
- [x] Tweaks: `gokyuzu` 4 faz + `ufukIsigi` 4 seviye görsel olarak ayrışıyor. *(kod + faz değerleri; panelden gezilebilir)*
- [x] `reviewCount=0` simülasyonunda onaylı boş kopya görünüyor. *(reviewTitle/reviewSub dalları — kod denetimi)*
- [x] Akış testi: sayfa stream sırasında baz gökyüzü + kartlar deliksiz boyanıyor (holes yalnız modülasyon ekliyor). *(baz stiller inline; delikler ek-stil deseni)*
- [x] Klavye: mood butonları focus-visible halka alıyor; okuma sırası selamlama→başlık→CTA. *(global :focus-visible + DOM sırası)*
- [x] bugun.png + handoff kopyası tazelendi; YENI_SOHBET_DEVIR.md güncellendi.
