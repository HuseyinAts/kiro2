# KIRO2 — Sprint 10 Port Spec'i: Ticari & Hesap (Grup 8)

Kapsam: **5 ekran** (Abonelik · Plan Yönetimi · Ödeme (+3DS bekleme) · Ayarlar · Bildirim Merkezi).
Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 9 DoD tamam. Bu sprint ADR-002 (Stripe) entegrasyonunun UI yarısı;
gerçek tahsilat Faz 4 backend işiyle birleşir.

Ticari kanon (bu iki satış ekranının ruhu — asla düşürme):
**"Baskı yok"** · deneme önce, kart sonra değil ama "bugün ödeme alınmaz" · "sessizce ücret
alınmaz" sözü · öğrenci fiyat baskısı görmez (veli-ödeyen model) · iptal tek dokunuş.

---

## A · Ekran: Abonelik (`KIRO2 Abonelik.dc.html`)

**Tema:** paper. **Layout:** tek sütun max 840px, geri oku (öğrenci→Ayarlar, veli→Veli Paneli).
**Rota:** `/premium?rol=ogrenci|veli`.

### İki rol — BİREBİR kopyalar
- **Öğrenci:** "Sınava kadar tam erişim" + "Baskı yok. Önce **7 gün ücretsiz** dene — motorun
  tamamı açık. Beğenmezsen tek dokunuşla iptal." Dipnot: "Aboneliği veli hesabından yönetebilirsin.
  Deneme süresi bitmeden hatırlatırız — sessizce ücret alınmaz."
- **Veli:** "{çocuk} için tam erişim" + kanıt şeridi (+{n} net bu ay · %{n} plana uyum · {n} gün seri
  — üretimde çocuğun GERÇEK verisi, `/parent/child/summary`) + "Evde, kendi hızında — yıllıkta ayda
  ₺124…" + dipnot "Fiyat ve satın alma yalnız veli hesabında — {çocuk} fiyat baskısı görmez."

### Bloklar
- Fatura toggle'ı: Aylık / Yıllık (−%38 pili — yalnız yıllık seçiliyken yeşil).
- Plan kartları: Ücretsiz (günde 20 soru · FSRS 5 kart · temel takip · AI günde 5 mesaj) vs
  Premium ("En çok seçilen" rozeti, rol'e göre 6 madde — veli listesinde "Haftalık veli raporu" başta).
- Güven şeridi: {n}+ soru · motorlar · "Kaygı-duyarlı tasarım".

### Port kararları
- **Fiyat ve plan içeriği SUNUCUDAN** (`GET /plans`): ₺199/₺1.490 sabitleri taşınmaz; kampanya/
  fiyat değişikliği deploy istemez. −%38 oranı da hesaplanır (yuvarlama sunucuda).
- **Sprint 9 açık noktası #3 BURADA ÇÖZÜLÜR:** AI kota tanımları plan nesnesinin alanıdır
  (`plan.aiGunlukMesaj`, `plan.gunlukSoru`, `plan.fsrsKart`) — Ücretsiz kart listesi bu alanlardan üretilir.
- "Şu an: Ücretsiz" pili `/me.plan`'dan; premium kullanıcıya `/premium` rotası **Plan Yönetimi
  görünümünü** gösterir — TASARLANDI 2026-07-05: `KIRO2 Plan Yonetimi.dc.html` (aşağıda A2).

### DoD notları
- Fatura toggle'ı `role="radiogroup"`; plan kartları başlık hiyerarşisi h2.
- 390px: `.rplans` tek sütun (premium ÜSTTE — sıra ürün kararı; prototipte free önce, mobilde ters çevir; not düş).

---

## A2 · Ekran: Plan Yönetimi — premium kullanıcı (`KIRO2 Plan Yonetimi.dc.html`)

**Tema:** paper. **Layout:** tek sütun max 680px; geri oku Abonelik'le aynı kural (öğrenci→Ayarlar,
veli→Veli Paneli). **Rota:** `/premium` (plan=premium ise bu görünüm render edilir).

### Bloklar — BİREBİR
- Header: geri oku + KIRO2 Premium logosu + durum pili (Aktif yeşil #E4F7F0/#0B6B4D · Deneme ve
  İptal amber #FBF0DE/#9A5D0D — iptal bile alarm değil).
- Hero: serif italic "Planını yönet." + rol'e göre alt satır (veli: "öğrenci fiyat ya da fatura
  ekranı görmez" · öğrenci: "sürpriz yok, sessiz ücret yok").
- Plan kartı: PREMIUM · Aylık/Yıllık + fiyat + durum chip'i · yenileme satırı ("… e-postayla
  hatırlatırız; sessizce ücret alınmaz") · kart satırı (Visa •••• 4242 + "Kartı değiştir" → Ödeme/
  Stripe kart güncelleme).
- Fatura geçmişi: tarih · açıklama · tutar · "Ödendi" yeşil chip + "Makbuz" linki (Stripe hosted
  invoice). Deneme durumunda boş durum: "Henüz fatura yok — deneme sürüyor, bugün ödeme alınmadı."
- **İptal — TEK adım, dark pattern yok:** sakin beyaz kart, onay diyaloğu/suçluluk kopyası/indirim
  tuzağı YOK; tıkla → iptal + üstte amber bilgi bandı ("İptal edildi — {dönem sonu} gününe kadar
  her şey açık.") + **"Geri aç"** butonu (geri-al modeli; onay yerine geri-alınabilirlik).
  Deneme iptali kopyası: "Deneme sırasında iptal edersen hiç ücret alınmaz."

### Veri bağlama
- `GET /billing/subscription` (openapi'ye eklendi) — tüm tarih/tutar/kart sunucudan; prototipteki
  sabitler taşınmaz. İptal `DELETE /billing/subscription`; geri açma `POST /billing/subscription/reactivate`.
- Prototip tweaks: `durum` (aktif/deneme/iptal) + `fatura` (yillik/aylik) + `rol` tüm durumları gezer.

### DoD notları
- Kart değiştirme Stripe üzerinden (SetupIntent) — ham kart formu bu ekranda da yasak.
- 560px: fatura satırı açıklama sütununu gizler (`.rfathide`).

---

## B · Ekran: Ödeme (`KIRO2 Odeme.dc.html`)

**Tema:** paper-nötr (radial #FFF3EE→#F1F2F6). **Rota:** `/odeme?rol=&fatura=`.
**⚠ Zemin düzeltmesi:** #F1F2F6 (soğuk gri) → paper ailesi (#F4F1EC türevi) — checkout bile marka sıcaklığında.

### ⚠ PCI MİMARİSİ — prototip formu OLDUĞU GİBİ TAŞINMAZ
Prototip ham kart alanları çizer (isim/no/SKT/CVC). Üretimde kart verisi DOM'umuza ASLA girmez
(ADR-002): **Stripe Elements** hosted alanları kullanılır; prototipteki görünüm Elements
`appearance` API'siyle birebir taklit edilir (radius 12, zemin #FBF8F3, kenar #E6DFD4, Hanken
Grotesk, tabular rakam). İsim alanı bizde kalabilir (PCI dışı). Hint'ler:
- İstemci-doğrulama hint'leri BİREBİR ("Kart numarası 16 haneli olmalı — acele yok." vb.) —
  Elements validasyon olaylarına bağlanır; amber kutu, ASLA kırmızı.
- Sağlayıcı reddi de aynı tonda: "Kart bu sefer onaylanmadı — bankan engellemiş olabilir; başka
  kartla dene ya da bize yaz." (kopya onaya).
- **3D Secure:** TR kartlarında zorunlu challenge akışı → "Bankan doğrulama istiyor" bekleme
  durumu **TASARLANDI (2026-07-05, `KIRO2 Odeme.dc.html` faz=3ds)**: dawn-aksan spinner halkası +
  kalkan ikonu · başlık "Bankan doğrulama istiyor." · açıklama (bildirim/SMS onayı; "onay gelince
  burası kendiliğinden ilerler") · 3 adımlı ilerleme (Kart bilgisi alındı ✓ → Banka onayı ● →
  Deneme başlar) · not "Genelde bir dakikadan kısa sürer — bu sayfa açık kalsın." · 5 sn sonra
  fallback: "Bildirim gelmedi mi?" → "Doğrulama penceresini yeniden aç" / "Farklı kartla dene" ·
  alt satır "Doğrulama bankanın kendi güvenli sayfasında (3-D Secure) yapılır; şifren bize
  ulaşmaz." Ret dönüşü → form + amber kutuda onaylı ret kopyası. Spinner reduced-motion guard'lı.
  Prototipteki zamanlayıcılar simülasyondur; üretimde Stripe challenge dönüşü beklenir
  (`/billing/trial` yanıtı `dogrulama_gerekli` + clientSecret).

### Bloklar — BİREBİR
- Başlık: öğrenci "Son bir adım." / veli "Denemeyi birlikte başlatalım." + rol'e göre alt metin.
- Özet paneli: Plan · Deneme (7 gün ücretsiz, yeşil) · İlk ödeme tarihi (bugün+7 — SUNUCUDAN gelir,
  saat dilimi sunucu) · Sonra {fiyat}. Güvence kutusu 3 madde ("✓" METİN glyph'i → bespoke SVG tik).
- "**Bugün ödeme alınmaz.**" CTA altı satırı + kilit satırı "256-bit şifreli bağlantı · kart bilgisi
  bizde tutulmaz" — KORUNUR.
- Başarı kartı: "Deneme başladı." + "7 gün boyunca her şey açık… Bitmeden hatırlatırız."
  **CTA düzeltmesi:** prototip "Devam edelim" → Kutlama?type=gunluk (yanlış tören) — port:
  öğrenci → Bugün (`/bugun`), veli → Veli Paneli. Kutlama'ya gitmez.
- Alt destek satırı: "Takıldıysan destek ekibine yaz — gerçek bir insan…" (Hesap Kurtarma ile aynı söz).

### Veri bağlama
- `POST /billing/checkout {planId, fatura}` → Stripe client secret; onay → `POST /billing/confirm`.
  openapi'deki `kartToken` alanı Stripe akışına göre güncellenir (Faz 4 sözleşme işi).
- Deneme hatırlatması: sunucu işi (e-posta, bitişten 2 gün önce) — "hatırlatırız" sözünün altyapısı;
  backlog'a not.

### DoD notları
- Form alanları `<label for>` ilişkili (mevcut — koru); hata hint'i `aria-live="polite"` + ilgili alana `aria-describedby`.
- 390px: `.ogrid` tek sütun; özet paneli formun ALTINA iner (önce iş, sonra özet).

---

## C · Ekran: Ayarlar (`KIRO2 Ayarlar.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="panel"`) + içerik (max 900px). **Rota:** `/ayarlar`.

### Bloklar — BİREBİR
1. Profil hero'su (coral gradyan): baş harf + ad/sınıf + seviye·XP·seri + "Düzenle".
2. Premium upsell kartı (koyu) → Abonelik. **Premium kullanıcıda gizlenir/plan-yönetimine döner.**
3. **Hedefin:** hedef bölüm/üni · hedef sıralama (+ "şu an ~{n}" + ilerleme barı) · "2027 YKS'ye {n} gün" ·
   günlük hedef dk (± butonlar; 15-180, 15'lik adım — sunucuya `PATCH /me/settings`).
4. **Bildirim tercihleri** (5 toggle; "Sakin varsayılan: az ve zamanında. Baskı yok."): tekrar ·
   seri · deneme · arkadaş · haftalık rapor (varsayılan KAPALI — sakin varsayılan bilinçli).
5. Hesap satırları: e-posta (+"doğrulandı") · şifre değiştir → Hesap Kurtarma akışı · Gizlilik & veri
  (KVKK metinleri; Faz 4'te sayfa) · Çıkış yap (terracotta).
6. "Kaydedildi" pili (başlıkta, 1.6 sn) — `aria-live="polite"`.

### ⚠ İKİ KANON ÇATIŞMASI (karar ister — porta girmeden)
1. **Tema seçici (Açık/Koyu/Sistem):** kanon "tema ekran TÜRÜdür, kullanıcı toggle'ı YOK" der;
   prototipteki satır çelişir (alt metni bile "çalışma ekranları hep aydınlık kalır" diyor).
   **Öneri: seçici KALDIRILIR**; yerine bilgi satırı "Çalışma ekranları göz konforu için aydınlık,
   duygusal anlar şafak — otomatik." (Koyu tercih ihtiyacı doğarsa yalnız hub/duygusal ekranlar
   kapsamında yeniden tasarlanır.)
2. **Vurgu rengi seçici (4 renk, teal dahil):** dawn aksanı marka İPLİĞİdir; kullanıcı accent'i
   değiştirirse marka dili bozulur. **Öneri: MVP'de KALDIRILIR** (ya da şafak ailesiyle sınırlı
   3 ton: Mercan/Kiremit/Amber — teal çıkar). Karar gelene dek portlanmaz.

### PORT EKLERİ — önceki sprintlerin "Ayarlar'a bağlanır" sözleri (prototipte YOK, portta VAR)
Mevcut toggle satır deseniyle (aynı anatomi) şu satırlar eklenir:
- **Sakin mod** (Lig kopyaları yumuşak — Sprint 8) — varsayılan AÇIK.
- **Sıralamayı gizle** (Lig listesi çekilmez — Sprint 8) — varsayılan KAPALI.
- **Geri sayım tercihi** (Kaygı-nötr / Geri sayım — Sprint 7) — varsayılan Kaygı-nötr; segment kontrol.
- **Yoğunluk** (Rahat/Kompakt — Sprint 2 Panel prop'u) — Görünüm bölümüne segment.
Hepsi `PATCH /me/settings` (sunucu) — sakinMod/sıralama cihazlar arası taşınmalı; yalnız yoğunluk
localStorage kalabilir (görsel tercih).

### Veri bağlama
- `GET /me` + `GET/PATCH /me/settings`. E-posta/şifre akışları `/auth/*`. Bildirim tercihi push
  aboneliğiyle senkron (ADR-004 web fazı: yalnız uygulama içi).

### DoD notları
- Toggle'lar gerçek `<button role="switch" aria-checked>`; satırın tamamı tıklanabilir (mevcut — koru).
- 390px: `.rtwo` tek sütun; hero sarar.

---

## D · Ekran: Bildirim Merkezi (`KIRO2 Bildirim Merkezi.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="panel"`) + içerik (max 760px). **Rota:** `/bildirimler`.
Panel topbar'ındaki zil buradan beslenir (rozet sayısı ortak kaynak).

### Bloklar — BİREBİR
- Başlık + "{n} yeni" pili (#E0593F) + "Tümünü okundu işaretle" + temizle (çöp) butonu.
- Gruplar: **Bugün / Bu hafta**; satır = renkli ikon karesi + başlık (okunmamış 800 + krem zemin
  #FFFBF9 + turuncu nokta) + açıklama + görece zaman + derin link (tekrar→FSRS · zayıf konu→Yol ·
  düello→Düello · seri→Seri · deneme→Sonuç · arkadaş→Arkadaşlar · rozet→Yol).
- Boş durum: yeşil zil + "Her şey sakin." + "Sıfır bildirim. Dikkatin dağılmadan, sakin kafayla
  çalışmaya dönebilirsin." + Panele dön — KORUNUR (boş durum ödül gibi hissettirir).
- Alt not: "Bildirimleri Ayarlar'dan kısabilirsin — sakin varsayılan, baskı yok."

### ⚠ Kanon düzeltmesi (porta taşınmaz)
- Düello bildirimi ikon rengi #8B5CF6/#F5F3FF (mor = Fizik/boss rezervli) → coral (#E0593F/#FFF3EE)
  ya da amber; sosyal davet morları kanona aykırı.

### Veri bağlama
- `GET /notifications` (ADR-003: 15 sn poll — zil rozeti de aynı poll'dan) · `POST /notifications/
  {id}/read` · `POST /notifications/read-all` · `DELETE /notifications` (temizle).
  openapi'de bildirim ucu var mı Faz 4'te doğrulanır; yoksa eklenir (açık nokta).
- Bildirim ÜRETİMİ sunucuda; içerik kopyaları (nazik ton) sunucu şablonlarında — şablon metinleri
  bu DC'den birebir alınır (ör. "~{n} dk yeter, fazlası değil.").
- Zaman etiketleri görece ("Şimdi/Bu sabah/2 gün önce") — `Intl.RelativeTimeFormat('tr')`.

### DoD notları
- Liste `<nav aria-label="Bildirimler">` + okunmamışlar `aria-label`'da belirtilir; "Tümünü okundu"
  sonrası odak korunur.
- Temizle butonu onay ister (prototipte anında — portta küçük onay; yanlış dokunuş 7 bildirimi silmesin).
- 390px: satırlar sarar; zaman etiketi başlığın altına.

---

## Sprint 10 açık noktaları
1. **Ayarlar tema seçici + vurgu rengi seçici kaldırılsın mı?** (öneri: ikisi de MVP'den çıkar — kanon)
2. ~~Premium kullanıcının Abonelik sayfası~~ — TASARLANDI 2026-07-05 (`KIRO2 Plan Yonetimi.dc.html`, bölüm A2).
3. ~~3D Secure bekleme durumu~~ — TASARLANDI 2026-07-05 (Odeme DC, faz=3ds; yukarıda).
4. Ödeme reddi kopyası onaya: "Kart bu sefer onaylanmadı — bankan engellemiş olabilir…"
5. Bildirim uçları openapi doğrulaması; bildirim şablon metinleri sunucuya taşınırken birebir korunacak.
6. Mobilde plan kartı sırası (premium üstte?) — ürün kararı.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 8 bitti** → PORT_DURUM'da Grup 8'e tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Fatura segmenti radiogroup; fiyat değişimi `aria-live="polite"`.
- Ödeme (Stripe Elements): iframe'lere erişilebilir ad; hata kopyası `aria-live="polite"` + `aria-describedby`; 3DS bekleme adımları `role="status"`.
- Ayarlar toggle'ları `role="switch"` + `aria-checked`; stepper butonlarına eylem etiketi ("Günlük hedefi 15 dk artır").
- Bildirim Merkezi: okunmamış sayısı başlıkta metin; "tümünü okundu" sonucu `polite`; liste semantiği.
