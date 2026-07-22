# KIRO2 — Sprint 1 (Kalibrasyon) Port Spec'i

Kapsam: **3 bileşen** (Button · Card · StatusChip) + **2 ekran** (Giriş & Kayıt · Ödevlerim).
Amaç: DoD'siyle bitir, ekran-başı/bileşen-başı gerçek süreyi ölç → PORT_DURUM.md kalibrasyon bölümüne yaz.
Piksel referansı her zaman kaynak DC'dir; bu spec kopya, durum ve davranışın **kaybolmaması** içindir.

---

## A · Bileşenler

### A1 · Button (`ui-starter/Button.tsx` temel)
- Varyantlar: primary (coral dolgu, beyaz metin) · ghost · disabled. Yükseklik ≥44px hedef.
- Piksel referansı: `KIRO Bilesenler.dc.html`. Storybook + RTL + axe + görsel diff.

### A2 · Card (`ui-starter/Card.tsx` temel)
- Açık yüzey: `#fff`, border `#ECE6DD`, radius 18-20, gölge `shadow.cardSoft`.

### A3 · StatusChip (`ui-starter/StatusChip.tsx` — hazır, test edilecek)
- `acik` #FFF3EE/#C2452B · `bekliyor` #FBF0DE/#9A5D0D · `tamam` #E4F7F0/#17936B.
- Test: "eksik" kelimesi HİÇBİR çıktıda yok; `acik + kalan` → "AÇIK · 2 GÜN".

---

## B · Ekran: Giriş & Kayıt (`KIRO2 Giris.dc.html`)

**Tema:** paper (açık). Arka plan: `radial-gradient(1200px 500px at 50% -10%, #FFF3EE 0%, #F1F2F6 60%)`.
**Rota önerisi:** `/giris` (sekme state'i URL'e yansıyabilir: `?mod=kayit`).

### Durum makinesi
`giris | kayit | tamam(giriş-sonrası) | tamam(kayıt-sonrası)` + `hint` (tek satır amber uyarı) + `goster` (şifre görünürlüğü).

### Kopya — BİREBİR (değiştirme)
| Yer | Metin |
|---|---|
| Üst sağ link | İlk kez mi? Önce değerini gör → Onboarding |
| Giriş başlık (serif italik 30px) | Tekrar hoş geldin. |
| Giriş alt metin | Serin ve ilerlemen seni bekliyor — kaldığın yerden devam. |
| Şifre linki | Şifreni mi unuttun? → Hesap Kurtarma |
| Giriş CTA | Devam edelim |
| Giriş dipnot | Girişte sıralama yok, alarm yok — sadece bugünkü planın. |
| Kayıt başlık | Başlayalım. |
| Kayıt alt metin | Hesap açmak 1 dakika. İstersen önce 6 soruluk seviye ölçümünü dene — kayıt sonrası da yapabilirsin. |
| Kayıt CTA | Hesabımı aç |
| Kayıt dipnot | Verilerin sende kalır; sınıf arkadaşlarına hiçbir şey yayınlanmaz. |
| Tamam (giriş) | İçerdesin. / Serin ve ilerlemen aynen yerinde. Bugünkü planın hazır. / CTA: Panele geç |
| Tamam (kayıt) | Hesabın hazır. / Şimdi 6 soruluk seviye ölçümüyle sana özel planını çıkaralım — 2 dakika. / CTA: Seviyeni ölçelim → Onboarding |
| Sayfa altı | Takıldıysan destek ekibine yaz — gerçek bir insan, okul saatlerinde ~10 dk içinde döner. |

### Doğrulama hint'leri — BİREBİR (amber kutu, #FBF0DE/#F2D9AC, metin #9A5D0D; ASLA kırmızı)
- E-posta geçersiz: "Bu adres eksik görünüyor — bir kez daha bakar mısın?"
- Şifre boş (giriş): "Şifreni yazmayı unuttun gibi — acele yok."
- Ad <2 karakter (kayıt): "Adını da alalım — sana adınla seslenelim."
- Şifre zayıf (kayıt): "Şifre en az 8 karakter, harf + rakam bir arada olsun."
- Kural: şifre ≥8 + rakam + harf (Türkçe karakterler dahil: `/[a-zA-ZçğıöşüÇĞİÖŞÜ]/`).

### Veri bağlama (Faz 4)
- Giriş: `POST /auth/login` · Kayıt: `POST /auth/register` (+ varsa misafir yerleştirme θ'sı gövdede).
- Sunucu hatası → aynı amber hint kutusu, `ErrorState` kopya standardı ("sorun sende değil" tonu). Alarm-kırmızısı YOK.
- Mock modda: `login()/register()` sahte token döner; `tamam` durumuna geçilir.

### Ekran DoD notları
- Sekme role="tablist"/"tab"; şifre göster/gizle `aria-label` mevcut — koru.
- 390px: kart `max-width:460px; padding:0 24px` zaten akışkan; taşma testi yap.

---

## C · Ekran: Ödevlerim (`KIRO2 Odevlerim.dc.html`)

**Tema:** paper (açık, #F7F4EF). **Layout:** SideNav (250px, `active="odev"`) + içerik (max-width 820px, ortalanmış).
**Rota önerisi:** `/odevlerim`.

### Header
- 66px sticky, `rgba(250,247,242,0.86)` + `backdrop-filter:blur(8px)`, alt çizgi #ECE6DD.
- Sol: "Ödevlerim" (16px/800) + alt satır "12-A · {öğretmen adı}" → mock'ta `sinifRoster`/persona'dan.
- Sağ özet (tabular-nums): `"{açıkSayı} açık ödev · ~{kalanDk} dk"`; kalanDk = Σ (adet−yapilan)×1.6 (yalnız tamam olmayanlar).

### Ödev kartı (border-radius 18, padding 20/22)
- Kenar rengi: durum `bekliyor` → `#F2D9AC`, diğer → `#ECE6DD`.
- Sol ikon kutusu 40px: ders rengi %10 dolgu (`renk+'1A'`) + ders-renkli pano ikonu. Ders renkleri (AÇIK palet): mat #3B82F6 · fiz #8B5CF6 · kim #E0593F · biy #1FB683 · tur #F59E0B.
- Başlık satırı: başlık (15px/800) + **StatusChip** (`chipLabel`: acik+kalan → "Açık · 2 gün").
- Alt satır: `"{dersAdı} · {konu} · {atayan}"` (12.5px, #6B6478).
- Sağ blok: `"{yapilan} / {adet} soru"` (tabular) + alt `"~{dk} dk"` ya da `"bitti"` (dk = (adet−yapilan)×1.6, min 1).
- İlerleme barı 7px: zemin #F0EAE1; dolgu ders rengi, tamam → #1FB683. `aria-label="{başlık} — ilerleme yüzde {pct}"`.
- Alt şerit: `kisisel` ise hedef ikonlu "Sorular seviyene göre seçildi" · "Teslim: {tarih}" · sağda CTA:
  tamam → "Çözümlere bak" (beyaz, #ECE6DD kenar) · yapilan>0 → "Devam et" · yoksa "Başlayalım" (coral dolgu). CTA → Soru Çözme rotası.
- `bekliyor` kartında amber not kutusu (saat ikonu): **"Teslim geçti ama kapanmadı — çözdüğün her soru hâlâ sayılır."**

### Boş durum — BİREBİR
- Serif italik 22px: "Şu an ödevin yok."
- "Plan sende — istersen bugünkü tekrar kartlarına bak ya da zayıf konunda birkaç soru çöz."
- CTA: "Haftalık plana git" → Haftalık Plan rotası.

### Liste dipnotu — BİREBİR
"Geciken ödev \"eksik\" değil, **bekliyor** — kaldığın yerden devam etmen yeter. Sınıf sıralaması yayınlanmaz."

### Veri bağlama
- Mock: `getAssignments()` ← `kiro-data.json → odevler`. Live: `GET /assignments`.
- İlerleme yazımı: `POST /assignments/:id/progress` (Soru Çözme ekranından; bu ekran salt okur).
- Üç durum: Skeleton (kart iskeleti ×3, zıplamayan) · EmptyState (yukarıdaki boş durum) · ErrorState (sakin amber, "sorun sende değil").

### Ekran DoD notları
- 390px: kartın başlık/chip satırı `flex-wrap` — koru; SideNav telefonda 64px ikon-only ya da gizli (KIRO2 Mobil.dc.html referans).
- "eksik" kelimesi kanon lint'te zaten yasak — bu ekran birincil test alanı.

---

## Ölçüm
Bitince PORT_DURUM.md'ye yaz: bileşen-başı ve ekran-başı süre → kalan iş tahmini formülüne koy.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Giriş/Kayıt: her input `label[for]`+`id` eşleşmeli; hata/hint `aria-describedby` ile inputa bağlı, gösterimde `aria-live="polite"`; şifre-göster `aria-pressed` + aria-label; sekme sırası: sekmeler → form → birincil CTA → ikincil linkler.
- Giriş/Kayıt sekme anahtarı: basit radiogroup kabul — seçili durum `aria-checked`.
- Ödevlerim: kart listesi `<ul>/<li>`; durum çipi renk+METİN birlikte (yalnız renk değil); ilerleme `role="progressbar"` + `aria-valuenow/max`.
- StatusChip bileşen sözleşmesi: `label` prop zorunlu — durum asla yalnız renkle kodlanmaz.
