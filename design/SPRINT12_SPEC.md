# KIRO2 — Sprint 12 Port Spec'i: Platform (Grup 10 — SON üretim grubu)

Kapsam: **2 ekran + 2 karar kalemi** — Çevrimdışı · Alan Kütüphanesi · Çözüm Paylaş (kapsam
kararı) · Mobil Uyarlama (referans, port edilmez). Piksel referansı her zaman kaynak DC'dir.

---

## A · Ekran: Çevrimdışı (`KIRO2 Cevrimdisi.dc.html`)

**Tema:** paper. **Layout:** SideNav + içerik (max 1060px). Bu ekran İKİ ürün parçasıdır:
1. **Global bağlantı bandı** (app-shell deseni — her ekranın üstünde belirir):
   Çevrimdışı (amber #FBF0DE · "Çevrimdışısın — sorun değil, çalışman cihazında sürüyor.") ·
   Yeniden bağlanıyor (şafak #FFF3EE) · Bağlandı (yeşil, "her şey eşitlendi" — birkaç sn sonra kaybolur).
   Kopyalar BİREBİR; `role="status"` korunur. Prototipteki `durum` prop'u üretimde gerçek
   bağlantı+eşitleme durumudur (navigator.onLine + kuyruk durumu).
2. **Tam sayfa** (`/cevrimdisi`): bağlantı yokken çalışılabilecekleri gösterir.

### Bloklar — BİREBİR
- Hero: "İnternet gitti. Çalışman gitmedi." (bağlanınca: "Hoş geldin — kaldığın yerdeyiz.") +
  "Çözdüğün her soru kaydedilir, bağlantı gelince kendiliğinden eşitlenir. Hiçbir şey kaybolmaz."
- **Cihazında hazır:** indirilen paketler (soru paketi · bugünkü FSRS kartları · deneme yanlışları)
  + "Başla" → ilgili ekran; dipnot "Paketler sen çevrimiçiyken kendiliğinden indirilir…".
- **Eşitleme kuyruğu:** bekleyen kayıtlar + "Bağlantı gelince bu liste kendiliğinden boşalır —
  senin bir şey yapman gerekmez." (suçlamayan, iş yüklemeyen dil — KORUNUR).
- **Bağlantı bekliyor:** canlı özellikler soluk listede (AI koç · Lig & Düello · yeni paket) —
  "kapalı" değil "bekliyor" çerçevesi.

### Port kararları — ⚠ KAPSAM KARARI GEREKLİ
- Altyapı: service worker + IndexedDB önbellek + `/sync/events` idempotent kuyruk (kanonda var).
  **Öneri — MVP çevrimdışı kapsamı iki katman:**
  K1 (MVP): global bant + cevap kuyruğu (çözüm sırasında kopan bağlantı veri kaybetmez) +
  bugünkü FSRS kartları önbelleği. K2 (sonra): proaktif soru paketi indirme + bu tam sayfa.
  Tam sayfa K2 ile gelir; K1'de yalnız bant + kuyruk rozeti. ONAY BEKLİYOR.
- Sayfa altındaki "Bu ekran KIRO Durumlar standardının… Tweaks panelinden…" paragrafı PROTOTİP
  NOTUDUR — taşınmaz.
- "Son eşitleme: bugün 14:32" sabit → gerçek zaman damgası (görece biçim).

### DoD notları
- Bant durum değişimi `aria-live="polite"`; bağlandı bandı otomatik kaybolurken odak çalınmaz.
- 1060px altı `.rtwo` tek sütun.

---

## B · Ekran: Alan Kütüphanesi (`KIRO2 Alan Kutuphanesi.dc.html`)

**Tema:** paper. **Layout:** tek sütun max 1080px. **Rota önerisi:** `/kutuphane`
(geri → Panel; prototipteki Tasarım Sistemi linki prototip hub'ıdır, taşınmaz).

### Bloklar — BİREBİR
- Başlık: "Alan Kütüphanesi" + "KIRO2 yalnız Sayısal değil — Sayısal, Eşit Ağırlık ve Sözel…".
- **3 alan kartı:** Sayısal · EA · Sözel; kullanıcının alanı "SENİN ALANIN" rozeti + renkli
  kenar + gölge; AYT ders listeleri (konu sayılarıyla) + "TYT ortak: …" dipnotu.
- **Tüm dersler · içerik derinliği:** 10 ders kartı (harf karesi + tür + konu sayısı + örnek
  chip'leri) — "konuların tamamını gör" akordiyonu: ünite başlıkları (amber eyebrow) + numaralı
  konu listesi + "{n} örnek soru çözümüyle havuzda" şeridi.

### Port kararları
- Bu ekran hem **kapsam vitrini** (misafir/yeni kullanıcı görebilir) hem **alan/ders gezgini**.
  Konu satırları üretimde TIKLANIR → Bilgi Atomları (`/atomlar?konu=`) ya da Öğrenme Yolu
  (ders bağlamına göre); prototipte statik (not düş).
- Ders renk paleti genişliyor (edebiyat/tarih/coğrafya/felsefe/din) — genişletilmiş ders
  renkleri `tokens.ts` ders paletine EKLENİR (tek kaynak; tintOf haritası token'a taşınır).
  Mor burada Fizik dışına da değiyor (edb #7C3AED) — ders rengi olarak İSTİSNA kabul edilir
  (kanon moru "semantik" kısıtlar, ders kimliği serbest) ama Fizik morundan ayrışsın diye edb
  tonu koyulaştırılmış kalır. Not düş.
- Veri: `GET /catalog` (alanlar + dersler + üniteler + konular + örnek soru sayıları) —
  openapi'de YOK, eklenecek. Kullanıcının alanı `/me.track`.

### DoD notları
- Akordiyon butonu `aria-expanded`; konu listeleri gerçek `<ol>`.
- 900px: 3 alan kartı tek sütun; 680px: katalog tek sütun (mevcut media query'ler).

---

## C · KAPSAM KARARI: Çözüm Paylaş (`KIRO Cozum Paylas.dc.html`)

Tek kartlık konsept ekranı (nav'sız, 760px): açık-uçlu soruda öğrenci çözümü + akran yorumu +
ÖĞRETMEN yorumu ("öğretmen dokunuşu + akran öğrenmesi") + "faydalı buldu" sayacı +
"Sen de bir çözüm paylaş — açıklamak, en güçlü öğrenmedir."

### ⚠ Öneri: MVP'ye GİRMEZ — Faz sonrası, öğretmen-merkezli pilotla
Gerekçe: reşit olmayan kullanıcıların ürettiği içerik (UGC) — moderasyon altyapısı, KVKK,
zorbalık riski (kaygı-duyarlı kanonla doğrudan çelişebilir). Girecekse ilk sürüm **öğretmen-onaylı**
akış olmalı: yorum yalnız öğretmen + öğretmenin onayladığı akran yanıtlarıyla yayınlanır;
serbest akran yorumu sonrası. PORT_DURUM'da "ertelendi" işaretlenir; DC referans olarak kalır.
Uçlar (girerse): `/solutions/*` + moderasyon kuyruğu. ONAY BEKLİYOR.

---

## D · REFERANS: Mobil Uyarlama (`KIRO2 Mobil.dc.html`) — port edilmez

8 iOS çerçevesinde kritik ekranların 390pt uyarlaması (Bugün koyu hub · Soru Çözme · FSRS ·
Ödevlerim · Kutlama · Lig · Sokratik AI · Çevrimdışı). Bu bir ÜRETİM EKRANI DEĞİL, tasarım
referansıdır:
- **Web portu için:** her sprintteki 390px DoD kontrollerinin görsel kabul referansı — responsive
  QA bu DC'ye bakarak yapılır (özellikle: hit ≥44pt, koyu/açık kuralının mobilde korunması).
- **Gelecek native uygulama için** (ADR-000 notu: Expo ihtiyacı doğunca): alt tab bar deseni
  (Bugün/Plan/Çöz/Profil), mobil Kutlama kopyası ("Bugünü ördün."), kompakt kart anatomileri
  buradan başlar. Web responsive'de alt tab bar KULLANILMAZ (web deseni: 64px ikon-nav) — iki
  platform deseni karıştırılmaz.
- PORT_DURUM'da "referans — port edilmez" işaretlenir.

---

## Sprint 12 açık noktaları
1. **Çevrimdışı kapsamı:** K1/K2 katmanlaması onayı (MVP = bant + cevap kuyruğu + FSRS önbelleği).
2. **Çözüm Paylaş:** MVP dışı + öğretmen-onaylı pilot önerisi onayı.
3. `GET /catalog` ucu openapi'ye eklenecek.
4. Alan Kütüphanesi konu satırlarının tıklama hedefi: Bilgi Atomları mı Öğrenme Yolu mu? (ürün kararı)
5. Genişletilmiş ders renkleri (edb/tar/cog/fel/din) tokens.ts'e taşınacak.

## Ölçüm + KAPANIŞ
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 10 bitti = tüm üretim ekranlarının spec'i TAMAM**
(2026-07-05 itibarıyla 42 ekran — sonradan eklenen Veli Bağlama / Öğrenci Özeti / Plan Yönetimi
spec'leri SPRINT10-11 A2/§6 bölümlerinde).
Kalan spec-dışı işler: (1) openapi'ye tüm sprintlerde önerilen uçların toplu eklenmesi (Faz 4
sözleşme güncellemesi — ayrı iş kalemi), (2) araştırma/dokümantasyon DC'leri (Canlı Demo, Moderatör
Kılavuzu, Sunum…) port edilmez — referans olarak kalır, (3) bekleyen kullanıcı onayları listesi
YENI_SOHBET_DEVIR'de.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Çevrimdışı bant `role="status"` (bağlantı değişince `polite`); kuyruk listesi `<ul>`; "bağlantı bekliyor" durumu METİNLE (yalnız dim değil).
- Alan Kütüphanesi drill: `aria-expanded` + `aria-controls`; konu listesi `<ol>`.
- 390px QA: hit ≥44 + odak halkası iki zeminde görünür (BREAKPOINT_SPEC QA matrisiyle birlikte koşulur).
