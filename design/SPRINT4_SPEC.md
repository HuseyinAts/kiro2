# KIRO2 — Sprint 4 Port Spec'i: Çekirdek döngü II

Kapsam: **3 ekran** (Adaptif Test · Harmanlanmış Deneme · Sınav Sonuç) — Grup 3 biter.
Piksel referansı her zaman kaynak DC'dir; bu spec kopya, durum ve davranışın **kaybolmaması** içindir.

Önkoşul: Sprint 3 DoD tamam (Soru Çözme çekirdeği hazır — Adaptif Test aynı seçenek/soru kartı
desenini yeniden kullanır; kopyala-uyarla, yeni bileşen çıkarma).

Kanon hatırlatması: **θ kestirimi (MLE/EAP), madde seçimi ve SE hesabı SUNUCUDA** — Adaptif Test
DC'sindeki IRT simülasyonu (pickNext, delta hesabı) prototip aracıdır, ASLA porta taşınmaz.

---

## A · Ekran: Adaptif Test (`KIRO2 Adaptif Test.dc.html`)

**Tema:** paper. **Layout:** SideNav YOK (odak modu) — 62px header + soru sütunu + sağda 380px
sticky **motor paneli**. ≤900px'te panel alta iner. **Rota önerisi:** `/adaptif-test`.

### Header — BİREBİR
- X → Panel · "Adaptif Yerleştirme Testi" + "TYT Matematik · seviyene göre uyarlanıyor".
- "CAT · IRT" rozeti (#FFF3EE, coral, hedef ikonu). Sağda "Uygulanan madde" + sayı.

### Soru kartı
- Üst: "Madde {n}" · Matematik chip'i · sağda "Zorluk: **{Kolay|Orta|Zor}**" + 5'li dikey bar
  (dolu sayısı b'den; Kolay yeşil #1FB683 · Orta amber #F59E0B · Zor terracotta #E8836B).
- Gövde + seçenekler Soru Çözme ile aynı desen (seçili = #FFF3EE + accent). Doğru/yanlış geri
  bildirimi GÖSTERİLMEZ (yerleştirme — ceza yok, Onboarding ile aynı ilke).
- Altta: "Emin değilim" (beyaz, sol) · "Cevapla →" (accent; seçim yokken %45 soluk + devre dışı).
- Bitiş kartı: yeşil rozet + "Yerleştirme tamamlandı" + "{n} maddede seviyeni ölçtük — tahmin
  yeterince kararlı (SE {n})." + 3 stat (Yetenek θ · Seviye · Net potansiyeli ~{n}) +
  CTA "Panele git →" · "Öğrenme yolunu aç".

### Uygulanan maddeler şeridi (soru kartının altı)
- Başlık "Uygulanan maddeler — zorluk adaptasyonu" + sağda "{n} doğru · {n} yanlış".
- Madde başına çubuk: yükseklik = zorluk; renk doğru #1FB683 / yanlış #E8836B. Boşken:
  "İlk cevabınla dolmaya başlar…". Lejant BİREBİR: "Doğru → zorluk arttı" · "Yanlış → zorluk azaldı".

### Motor paneli (sağ ray — bu ekranın kimliği; şeffaf motor = güven inşası)
1. **Yetenek tahmini (θ):** 42px tabular değer ± SE · seviye rozeti (Zayıf terracotta · Orta amber ·
   Güçlü yeşil) · "≈ üst **%{n}** · tahmini **{n} net** (TYT Mat)" · −3…+3 bandı üzerinde
   işaretçi + SE genişliğinde %20 coral bant (0.3s geçişli).
2. **θ Yakınsaması:** çizgi + güven bandı SVG'si; "Tahmin her maddeyle kararlı hâle geliyor;
   güven aralığı daralıyor." Eksen: Madde 1 · 6 · 12.
3. **Standart hata (SE):** değer + ilerleme barı (hedef çizgisi yeşil) + "Hedef: SE < 0,30
   (yeşil çizgi)" + "~{n} soru kaldı" · altta Güvenilirlik / Madde / Doğruluk üçlüsü.

### Sayı biçimi
Tüm θ/SE değerleri virgüllü Türkçe ondalık ("0,42" · "−1,05"), tabular-nums; eksi işareti U+2212 (−).

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- "tamamlandı ✓" metin glyph'i → bespoke SVG tik (ya da yalnız "tamamlandı").
- Matematik chip'i burada #EFF6FF/#2563EB — Soru Çözme'de #EAF0FC/#3B6FD4. Port'ta TEK konu-chip
  stili kullanılır (Soru Çözme'deki); ekranlar arası tutarlılık.

### Veri bağlama (Faz 4)
- Akış tümüyle `POST /cat/next`: cevap gönderilir → yanıt {sonrakiMadde, θ, SE, seviye, netTahmini,
  uygulananlar[]} döner. İstemci HİÇBİR IRT hesabı yapmaz; motor paneli sunucu değerleriyle çizilir.
- "Emin değilim" = cevapsız gönderim (`secim: null`) — sunucu düşük bilgi olarak işler; prototipteki
  "yanlış say" davranışı SİMÜLASYONDUR, taşınmaz.
- Durdurma kuralı sunucuda (SE<0.30 veya 12 madde); istemci `bitti: true` bayrağına tepki verir.
- Üç durum: Skeleton ("Test hazırlanıyor…") · ErrorState (sakin amber; cevap kuyruğu idempotent) ·
  oturum yarıda kalırsa kaldığı maddeden devam (sunucu oturum kimliğiyle).

### Ekran DoD notları
- Motor paneli `aria-live="polite"` değil — her maddede konuşmasın; yalnız bitişte duyuru.
- Klavye: Soru Çözme ile aynı (1-5/A-E, Enter=Cevapla).
- 390px: panel alta; grafikler tam genişlik; hit ≥44px.

---

## B · Ekran: Harmanlanmış Deneme (`KIRO2 Harmanlanmis Deneme.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="deneme"`) + içerik (max 980px). **Rota:** `/deneme/harman`.
Bu ekran bir ÖN SAYFA (oturum lobisi): yöntemi açıklar, bileşimi gösterir, Soru Çözme'ye gönderir.

### Kopya — BİREBİR (yöntem-güven ekranı; kopya pedagojik varlıktır)
| Yer | Metin |
|---|---|
| Header | Harmanlanmış Deneme · Karışık konu pratiği · interleaving |
| Rozet | KANITLI YÖNTEM · d≈0,35 (amber) |
| Başlık | Konuları karıştır, daha iyi öğren |
| Gövde | Tek konu üst üste çalışmak (bloklu) kolay *hisseder* ama zayıf kalır. Konuları **harmanlamak** beyni her soruda "hangi yöntem?" diye seçim yapmaya zorlar — ayırt etme ve gerçek sınav transferi güçlenir. |
| Oturum kartı (coral gradyan) | Bu oturum · **{n}** soru · {n} konu · ~{n} dk · karışık sıra · CTA "Denemeyi başlat →" |
| Sıra notu (harmanlı) | Konular bilinçli karıştırıldı — her soruda yöntem seçimi yeniden tetiklenir. |
| Sıra notu (bloklu) | Aynı konu üst üste gruplanmış — akıcı ama zayıf transfer. (Karşılaştırma için) |
| Bileşim alt başlığı | FSRS + zayıf konularına göre seçildi — en çok tekrar isteyenler ağırlıkta. |

### Bloklar
1. **Soru sırası görselleştirmesi:** 42px renkli sayı chip'leri; konu lejantı. Header'daki
   Harmanlanmış/Bloklu pili sırayı canlı değiştirir (abc abc abc ↔ aaa bbb ccc) — bu toggle
   ÜRETİMDE KALIR (pedagojik gösterim; deneme her zaman harmanlı başlar, bloklu yalnız karşılaştırma görünümü).
2. **Karşılaştırma kartları:** BLOKLU (gri; + Kolay hisseder, akıcı · − Zayıf uzun-vade transfer ·
   − "Hangi yöntem?" seçimini öğretmez) vs HARMANLANMIŞ (coral zemin; + Güçlü transfer + ayırt etme ·
   + Gerçek sınav koşuluna yakın · ! Zor hisseder — bu "istenen zorluk"). İşaretler +/−/! METİN olarak
   kalabilir (glyph değil, tipografik işaret) ama renkleri: + yeşil · − terracotta #E0593F · ! amber #9A5D0D.
3. **Oturum bileşimi:** 4 konu kartı (renk noktası + ad + soru sayısı + "TYT/AYT · durum").

### Veri bağlama
- Bileşim: `GET /review/due` kuyruğu + `GET /topics` zayıf/durum bilgisi (prototipteki formül:
  reviewQueue ilk 4 konu, kart sayıları) — üretimde sunucu hazır bileşim dönebilir (Faz 4'te
  `/review/due` yanıtına `harmanBilesim` eklenmesi değerlendirilir; eklenmezse istemci aynı formülü uygular).
- "Denemeyi başlat" → Soru Çözme rotasına set parametresiyle (`/cozum/harman-{id}`).
- Üç durum: Skeleton · EmptyState (tekrar kuyruğu boşsa: FSRS boş-durum kopyasıyla aynı ton,
  Sprint 3 açık noktası #2'ye bağlı) · ErrorState.

### Ekran DoD notları
- Sıra chip'leri dekoratiftir: `aria-hidden`, lejant metni yeterli.
- 390px: hero + karşılaştırma tek sütun; bileşim 2×2.

---

## C · Ekran: Sınav Sonuç (`KIRO2 Sinav Sonuc.dc.html`)

**Tema:** paper. **Layout:** SideNav YOK — 62px header (geri oku → Panel) + içerik (max 1100px).
**Rota:** `/sinav/:id/sonuc`. **Net-birincil hiyerarşi** (kanon): büyük sayılar net'tir, sıralama küçük ve çerçevelenmiş.

### Hero (300px sol + sağ)
- Sol (#FBF8F3): 148px doğru-oranı halkası (%{n} + "doğru oranı") + yeşil trend chip'i
  "+8,5 net · son denemeye göre" (değer sunucudan).
- Sağ: "Güzel iş, {ad}!" + "**{TYT Deneme}** · {n} soru tamamlandı" + 3 sayı:
  TYT neti · **Toplam net** (accent, vurgu) · Tahmini sıralama — etiketi BİREBİR:
  "Tahmini sıralama · **yalnız yön göstergesi**" (kaygı çerçevelemesi; asla kaldırma).

### Stat satırı ×4
Doğru (yeşil) · Yanlış (terracotta) · Boş (gri) · Net (accent, vurgulu). 24px/800 tabular.

### İki sütun
1. **Ders Bazında Net Dökümü:** satır = renk noktası · TYT/AYT etiketi (TYT #EEF3F8/#5A6B82 ·
   AYT #FBF0DE/#9A5D0D) · ders adı · "D{n} · Y{n} · B{n}" · sağda "{net} / {toplam}" · ders-renkli bar.
   Net biçimi: virgüllü ("42,5").
2. **AI Analizi:** logo karesi + "Toplam netin **{n}** — en güçlü dersin **{X}**. En çok gelişim
   alanın **{Y}**; zayıf konularını tekrar listene ekledim." (üretimde bu metin sunucudan/AI proxy'den
   gelir — istemci şablon doldurmaz; Faz 4.5'e not).
3. **Geliştirilecek konular:** ≤4 satır; %hâkimiyet <50 terracotta, değilse amber.

### CTA satırı
"{n} yanlışı tekrar et (FSRS)" (accent, döngü ikonu) → FSRS · "Zayıf konuları öğrenme yoluna ekle" (beyaz) → Öğrenme Yolu.

### ⚠ Kanon düzeltmesi (porta taşınmaz)
- Yanlış stat ikonunun zemini `#FEF2F2` (kırmızı ailesi) → `#FBE8E2` (terracotta zemin, diğer
  ekranlarla tutarlı). İkon rengi #E0593F zaten doğru.

### Veri bağlama
- `GET /exams/last` (ya da `/exams/:id`) — ad, tip, tarih, ders dökümü (D/Y/B/net/soru),
  tahminiSiralama, trend. Zayıf konular: `GET /topics` (durum=zayif, en düşük 4).
- Üç durum: Skeleton · ErrorState · henüz deneme yoksa bu rotaya gelinmez (Panel "Son Sınavlar" boşsa link yok).

### Ekran DoD notları
- Halka SVG'sine `role="img"` + `aria-label="Doğru oranı yüzde {n}"`.
- 390px: hero tek sütun; stat 2×2→1; CTA'lar alt alta (flex-wrap zaten var).

---

## Sprint 4 açık noktaları
1. Harman bileşimi sunucu mu istemci mi hesaplar? (öneri: sunucu — `/review/due` yanıtına alan; Faz 4 kararı)
2. AI Analizi metni: Faz 4.5 AI proxy'den mi, deneme yanıtına gömülü mü? (öneri: `/exams/:id` yanıtında hazır metin — proxy çağrısı gerektirmez)
3. Sınav Sonuç trend değeri ("+8,5 net") openapi ExamResult şemasında yok — alan eklenecek.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. Grup 3 bitti → PORT_DURUM'da Grup 3'e tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Süre göstergesi `role="timer"` + `aria-live="off"` — sürekli duyuru YOK (kaygı); yalnız son 1 dk'da tek `polite` duyuru.
- "Emin değilim" ayrı, net etiketli buton (secim:null anlamı SR'a da aynı dille).
- Sınav Sonuç tabloları `<caption>` + `th scope`; net-birincil hiyerarşi DOM sırasında da (görselle aynı).
- θ/SE animasyonu dekoratif `aria-hidden`; sonuç özeti tek `aria-live="polite"` bölge.
