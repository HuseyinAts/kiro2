# KIRO2 — Sprint 3 Port Spec'i: Çekirdek döngü I

Kapsam: **3 ekran** (Soru Çözme · Neden Geri Bildirim · FSRS Tekrar) — Grup 3'ün ilk yarısı.
Bu üçlü ürünün kalbi: soru → sonuç → hafızaya işleme döngüsü. İkinci yarı (Adaptif Test ·
Harmanlanmış Deneme · Sınav Sonuç) Sprint 4'te. Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 2 DoD tamam (SideNav gerçek ekranda çalışıyor; MasteryBadge test edildi —
bu sprintte ikisi de yeniden kullanılıyor).

Kanon hatırlatması (bu üç ekran birincil test alanı): **motorlar SUNUCUDA** — θ/BKT güncellemesi,
FSRS zamanlama ve `dogru` bilgisi yalnız sunucu yanıtından gelir; istemci simülasyonu taşınmaz.

---

## A · Ekran: Soru Çözme (`KIRO2 Soru Cozme.dc.html`)

**Tema:** paper. **Layout:** SideNav YOK — tam ekran odak modu; üstte 62px ince sınav header'ı
+ 4px gradyan ilerleme şeridi (#FF8A5B→#FF6F91). Üst 200px'te yumuşak gün ışığı yıkaması
(radial, rgba(255,158,125,0.07)). **Rota önerisi:** `/cozum/:setId`.

### Header — BİREBİR
- Kapat (X, 38px) → Bugün hub'ı · "Matematik · Günlük Set" + "Türev odağı · {n} soru".
- Sayaç: amber kutu (#FBF0DE/#F2D9AC), saat ikonu, `MM:SS` 18px/800 tabular (geriye sayar; baskı dili YOK — kırmızıya dönme, yanıp sönme yok).
- "Seti Bitir" (beyaz, kenarlıklı) → Sınav Sonuç.

### Soru kartı (radius 20, padding 28/30)
- Meta satırı: "Soru {n} **/ {toplam}**" · konu chip'i (mavi #EAF0FC/#3B6FD4) · zorluk chip'i
  (Kolay #E3F6EE/#0E9E6E · Orta #FBF0DE/#9A5D0D · Zor #FBE8E2/#DD5A3D; eşik: b<0.1 kolay, ≤0.75 orta) ·
  **MasteryBadge** (konu hâkimiyeti, zayıfsa trend down) · sağda "İşaretle/İşaretli" toggle (işaretliyken amber).
- Gövde 17px/1.75. Seçenekler: beyaz + 1.5px #ECE6DD; seçili → #FFF3EE + accent kenar + accent rozet.
- Çözüm modu (cevap sonrası): doğru satır #E9F8F1/#6FD9B0 + "Doğru cevap" · senin (yanlış) satır
  #FCEDE8/#F0A593 + "Senin cevabın" — **terracotta, alarm-kırmızısı değil**. Yeşil çözüm kutusu:
  "Çözüm · adım adım" + numaralı adımlar + "**Neden:** …" + link "Takıldıysan — KIRO Koç ile adım adım" → Sokratik AI.

### Alt gezinme
"Önceki" (ilk soruda %40 soluk + devre dışı) · "Bu soruyu atla" (çıplak metin) · sağda
"Sonraki soru" / son soruda "Seti bitir" — gradyan CTA (#FF8A5B→#FF5E7E, basılınca 2px iner).

### Soru Navigatörü (sağ ray, 296px sticky; ≤820px'te üstte tam genişlik)
- Başlık + "{cevaplanan}/{toplam}" · 5'li grid: şu anki = accent kenarlı boş · cevaplanan = accent dolu ·
  işaretli = amber · boş = #F4F0EA. Altta 4 satırlık lejant (Cevaplanan/Şu anki/İşaretli/Boş) — BİREBİR.
- `showNavigator` prop'u → üretimde ekran ayarı değil; günlük sette AÇIK, deneme modunda ekran-tipine göre.

### Davranış + veri bağlama
- Oturum kalıcılığı: `idx/answers/marked` localStorage'da (`kiro_soru_cozme_v1` deseni) — sekme kapanıp
  açılınca kaldığı yerden. Üretimde de korunur; sunucuya yazım ayrıca.
- Cevap seçimi anında yerel; **soru geçişinde** `POST /questions/{id}/answer` → yanıt `dogru`, çözüm
  adımları, `neden` ve θ/BKT etkisini döner (kanon: `dogru` YALNIZ bu yanıtta). Çözüm modu bu yanıtla açılır.
- Prototipteki `reviewMode` prop'u üretimde durumdur: cevap yanıtı geldi → review.
- "Seti Bitir" → sonuç ekranına set özeti taşınır (Sprint 4'te bağlanır; şimdilik rota geçişi).
- Üç durum: Skeleton ("Sorular hazırlanıyor…" kart iskeleti) · ErrorState (sakin amber; cevap POST'u
  düşerse cevap YEREL kuyrukta bekler — `/sync/events` idempotent deseni) · boş set = plana yönlendirme.

### Ekran DoD notları
- Klavye: 1-5/A-E seçenek seçimi, ←/→ gezinme, M işaretleme — sınav ekranı klavye-birincil.
- 390px: gövde tek sütun, navigatör üstte; hit ≥44px (seçenek satırları 44px+).

---

## B · Ekran: Neden Geri Bildirim (`KIRO2 Neden Geri Bildirim.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="practice"`) + orta sütun (max 720px) + sağ ray 312px
(≤760px gizli). **Rota önerisi:** `/cozum/:setId/neden/:soruId` (Soru Çözme'den çözüm derinleşmesi).

### Sonuç bandı
- Doğru: #F0FDF4/#BBF7D0, yeşil rozet, "Doğru!" + "Güzel iş. Yine de mantığı pekiştirelim."
- Yanlış: "Yanlış — hadi nedenini görelim" + "Hata, öğrenmenin en değerli anı. Aşağıda tam olarak neden."
  — kopya BİREBİR (kaygı-duyarlı çerçeveleme). Sağda süre ("1:12" tabular).
- Header'da Yanlış/Doğru segmenti PROTOTİP ARACIDIR — üretime taşınmaz (durum, cevap yanıtından gelir).

### Soru özeti + "Neden?" bloğu
- Seçenek satırları: doğru = yeşil (#F0FDF4/#86EFAC) + "Doğru cevap"/"Senin cevabın ✓" rozeti;
  seçilen yanlış = kırmızımsı; nötr = beyaz.
- "NEDEN {X} DOĞRU" yeşil kutu + "NEDEN {Y} YANLIŞ" kutusu (yalnız yanlışta) + "ÇÖZÜM · adım adım"
  (#FBF7F1, koyu numara daireleri).
- Aksiyonlar: "Benzer soru çöz →" (coral CTA) · "Kavramı tekrar et" (beyaz) → FSRS.

### Sağ ray
1. **Hafıza motoru kartı** (coral gradyan #C2452B→#FF6F5C): "Yanlış yaptığın için bu kavram
   **tekrar kuyruğuna** eklendi." + "2 gün sonra tekrar göreceksin" — gün değeri üretimde FSRS yanıtından.
2. **Kavram hâkimiyeti etkisi**: konu + **MasteryBadge** (trend down) + amber→terracotta bar +
   "Birkaç doğru çözümle geri yükselir."
3. **İlgili kavramlar** listesi (renk noktaları) — üretimde `/topics/{konu}/atoms` ilişkilerinden.

### ⚠ Kanon düzeltmeleri (prototip hataları — porta TAŞINMAZ, kanon-lint zaten yakalar)
- Yanlış-cevap kırmızıları **yasak listede**: `#991B1B` (metin) ve `#FEE2E2` (rozet zemini).
  Port: Soru Çözme review paletiyle değiştir — zemin `#FCEDE8`, kenar `#F0A593`, rozet `#E8836B`,
  metin `#C2452B`. (#FEF2F2/#FECACA/#FCA5A5 de aynı takasa dahil edilir — tutarlılık.)
- "✓"/"✗" glyph METİN olarak kullanılmış (banner + kutu başlıkları + rozetler) → bespoke SVG tik/çarpı.
- "Benzer soru çöz" hover'ı `#4338CA` (indigo, yasak) → `filter:brightness(0.94)`.

### Veri bağlama
- İçerik tümüyle `POST /questions/{id}/answer` yanıtından (soru özeti, neden, adımlar, FSRS etkisi,
  hâkimiyet değişimi) — ekran salt okur, ikinci istek atmaz.
- Header seri/XP pilleri: `/me`'den (Panel ile aynı kaynak).

### Ekran DoD notları
- "Neden {Y} yanlış" kutusu yalnız yanlış senaryosunda DOM'da; doğruda hiç render edilmez.
- 390px: SideNav 64px; sağ ray gizli — FSRS kartındaki bilgi banner altına kompakt satır olarak inmez, sadece gizlenir (prototip davranışı).

---

## C · Ekran: FSRS Tekrar (`KIRO2 FSRS Tekrar.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="review"`) + içerik (max 1000px). **Rota:** `/tekrar`.
İki katman: sayfa (özet + istatistik) + **tekrar oturumu overlay'i** (modal, rgba(15,23,42,0.55) + blur).

### Sayfa — BİREBİR kopyalar
- Header: "Tekrar · Hafıza Motoru" + "FSRS · ne zaman unutacağını tahmin eder, tam zamanında getirir".
  Sağda "Hedef tutma {n}%" + seri pili.
- Hero sol (coral gradyan #FF7A5B→#FF5E7E): "Bugün tekrar edilecek" + **{n}** 60px/800 + "kart" +
  "Tahmini süre ~{n} dk · tam zamanında, fazlası değil" + beyaz CTA "Tekrara başla" / devam varsa "Tekrara devam et".
- Hero sağ: **Unutma eğrisi** SVG — %85 eşik kesikli çizgisi, turuncu sönüm (Tekrarsız) vs coral testere
  (Tekrarla), ● tekrar noktaları; altta "Her tekrar (●) hatırlamayı tazeler ve aralığı uzatır — tekrarsız bilgi hızla unutulur."
- 3 stat: Tutma oranı %91 yeşil · Bu hafta tekrar {n} · Risk altında {n} (#E0593F) + "konu · eşiğe yaklaşıyor".
- **Konuya göre hafıza gücü**: satır = renk noktası + konu/ders · güç barı (r<84 amber→terracotta gradyan ·
  <92 sarı→yeşil · ≥92 düz yeşil) · vade chip'i (Bugün #FBE8E2/#C2452B · Yarın #FFEDD5/#9A5D0D · n gün yeşil) · %n tabular.
  Alt başlık BİREBİR: "Her konu için \"unutmana kalan süre\" — kırmızılar bugün tekrar istiyor."
- **Önümüzdeki 7 gün · tekrar yükü**: çubuk grafiği (bugün coral, diğerleri #FFD3C4) + "FSRS yükü dengeler — hiçbir gün seni ezmez."

### Tekrar oturumu (overlay)
- Header: "Tekrar oturumu" + "Kart {n} / {toplam}" + ilerleme barı + X.
- Kart: ders chip'i → SORU (20px/700) → "Cevabı göster" (accent CTA, göz ikonu).
- Açılınca: CEVAP yeşil kutu + "Ne kadar kolay hatırladın? — aralığı FSRS belirler" + 4 derece butonu:
  **Tekrar** (<1 dk, terracotta) · **Zor** (3 gün, amber) · **İyi** (6 gün, yeşil) · **Kolay** (12 gün, mavi).
  Aralık etiketleri ("3 gün" vb.) üretimde SUNUCU yanıtından gelir — sabit yazılmaz.
- Bitiş: yeşil kpop rozeti + "Bugünün tekrarı tamam" + "**{n} kart** tam zamanında tekrarlandı — hafıza eğrin
  tazelendi. Serin **{n}. güne** uzadı." + CTA'lar: "Günü kutla" → Kutlama(?type=gunluk) · "Panele dön" · "Soru çözmeye geç".
- Konfeti: **ConfettiDawn** (reduced-motion'da yok) — prototipteki inline burst taşınmaz.

### Veri bağlama
- Sayfa: `GET /review/due` (kartlar + konu kuyruk verisi: hatirlanabilirlik, dueIn) · `/me` (seri, hedef tutma).
- Derecelendirme: `POST /review/{kartId}/grade` → FSRS sunucuda yeniden zamanlar; yanıt sonraki aralığı döner.
  Çevrimdışıysa olay kuyruğa (`/sync/events`, idempotent).
- 7 gün yükü: prototipte sabit — üretimde `/review/due` yanıtına yük projeksiyonu alanı eklenene dek gizlenebilir
  ya da mock'la kalır (Faz 4 kararı; openapi'ye not düşüldü olarak İŞARETLENMEDİ — açık nokta).
- Üç durum: Skeleton · EmptyState ("Bugün tekrar yok — eğrin sağlıklı." tonu; kopya prototipte yok, ErrorState
  standardındaki sakin sesle yazılır ve kullanıcı onayına sunulur) · ErrorState (sakin amber).

### Ekran DoD notları
- Overlay: focus trap + Esc kapatır + `aria-modal`; arka sayfa scroll kilidi.
- Klavye: Boşluk = cevabı göster; 1-4 = derece (Anki alışkanlığı).
- 390px: hero grid tek sütun (`.rstack`); overlay kartı tam genişlik; derece butonları 2×2 grid'e sarabilir — hit ≥44px.

---

## Sprint 3 açık noktaları
1. 7 günlük tekrar yükü verisi openapi'de yok — uç mu genişler, blok mu gizlenir? (Faz 4'te karar.)
2. FSRS boş durumu kopyası prototipte yok — önerilen: "Bugün tekrar yok — eğrin sağlıklı. Yarın {n} kart seni bekliyor." (onay bekliyor).
3. Soru Çözme sayacı sete göre nereden gelir (plan görevi süresi mi sabit 20 dk mı)? — plan verisiyle Sprint 4'te netleşir.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz; Sprint 1-2 kalibrasyonuyla karşılaştır.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Soru Çözme: cevap geri bildirimi `aria-live="assertive"` tek bölgede; şıklar radiogroup + `aria-checked`.
- Soru navigatörü `<nav aria-label="Sorular">`; aktif soru `aria-current="true"`; cevaplanmışlık metinle de ("5. soru, cevaplandı").
- Neden overlay: focus trap + `aria-modal` + Esc (mevcut DoD) + kapanışta tetikleyen öğeye ODAK İADESİ.
- FSRS: derece butonları `aria-keyshortcuts` 1–4; kart çevirme Boşluk + görünür buton eşdeğeri; hatırlanabilirlik % metin olarak da.
