# KIRO2 — Sprint 5 Port Spec'i: Planlama (Grup 4)

Kapsam: **4 ekran** (Haftalık Plan · Öğrenme Yolu · Bilgi Atomları · Çalışma Modları).
Öğrenme Yolu bu sprintin ağır işi (oyunlaştırılmış patika); diğer üçü hafif.
Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 4 DoD tamam. Bu grupla Soru Çözme'ye giden TÜM giriş kapıları bağlanmış olur
(plan bloğu → çözüm · patika düğümü → çözüm · atom CTA → çözüm · mod kartı → çözüm/tekrar).

---

## A · Ekran: Haftalık Plan (`KIRO2 Haftalik Plan.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="plan"`) + 66px header + 7 sütunlu hafta grid'i
(≤1080px 4 sütun · ≤760px tek sütun). **Rota:** `/plan`.

### Header
"Haftalık Plan" + tarih aralığı ("29 Haz – 5 Tem") · sağda "Günlük hedef {n} dk" (beyaz) +
"Bu hafta ~{n} sa" (coral, virgüllü: "7,5").

### Giriş metni — BİREBİR
"Motor bu haftayı senin için kurdu: bugün **zamanı gelen tekrarlar**, en zayıf konuların ve
hafta sonu bir deneme. Her bloğa dokunup başla."

### Gün sütunu
- Bugün: #FFF3EE zemin + accent kenar + "BUGÜN" rozeti; diğer günler #FBF8F3/#ECE6DD.
- Blok kartı (sol 3px ders/tür rengi): üstte TAG (uppercase 9.5px) · başlık · meta. Türler:
  **Çalışma** (ders rengi; "12 soru · ~30 dk") · **FSRS Tekrar** (amber #9A5D0D; "{n} kart · ~{n} dk") ·
  **Deneme** (accent; "TYT + AYT · ~135 dk") · **Analiz** (gri; "net + zayıf konu · ~25 dk") ·
  **Mola** (yeşil #1FB683; "sakinleş · ~10 dk" → Mola ekranı).
- Boş gün: kesikli çerçeve, "Serbest" — doldurulmaz (dinlenme meşru; kaygı-duyarlılık).
- Sütun altı: "Toplam · {n} dk" (tabular).

### Props → üretim
- `denemeGunu` (Cmt/Paz) + `molaGoster` → kullanıcı plan tercihleri; Ayarlar'a bağlanır (plan
  motoruna parametre olarak gider, istemcide blok kaydırma YAPILMAZ).

### Veri bağlama — ⚠ AÇIK NOKTA
- **openapi'de plan ucu YOK.** Plan kurulumu motor işidir (kanon: motorlar sunucuda) — öneri:
  `GET /plan/week` → { gunler[]: { tarih, bloklar[]: { tur, konu, meta, dk, hedefRota } } }.
  Faz 4'te sözleşmeye eklenene dek ekran mock'la çalışır (prototipteki reviewQueue+topics bileşimi
  yalnız mock katmanında yaşar, üretim koduna sızmaz).
- Üç durum: Skeleton (7 sütun iskeleti) · EmptyState (plan henüz kurulmadıysa → Onboarding'e CTA) · ErrorState.

### DoD notları
- Blok kartları gerçek `<a>`; gün başlıkları `<h2>` + grid `role="list"` değil — doğal akış yeter.
- 390px: tek sütun; bugün en üstte görünür olmalı (sıra korunur, scroll bugüne).

---

## B · Ekran: Öğrenme Yolu (`KIRO2 Ogrenme Yolu.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="path"`) + header (seri + XP pilleri, Panel'dekiyle aynı) +
sol patika / sağ 320px sticky ray (≤1024px tek sütun). **Rota:** `/yol`.

### Ders değiştirici
Pill satırı (5 ders; aktif = accent dolgu + alt gölge "ledge") + sağda "**{n}/{n}** konu ·
hâkimiyet **%{n}**". Ders değişimi patikayı yeniden çizer (istemci state).

### Patika (ekranın kimliği — oyunlaştırılmış dikey yol)
- **Ünite bandı:** ünite-renkli gradyan (sıra: #3B6FD4 · #0E9E9E · #8B5CF6 · #1FB683 · #E0593F ·
  #D98A2B) + alt "ledge" gölgesi; "N. ÜNİTE" + ad + ilerleme "{a}/{b}" + beyaz bar.
- **Düğümler:** 72px daire, merkez çizgi (kesikli) üstünde yatay ofsetlerle zikzak
  (0/40/52/40/0/−40/−52/−40 px). Durumlar (lejant kartı BİREBİR):
  - **Tamam** = yeşil #1FB683 + tik + #17936B ledge
  - **Şu an** = accent + play + pulsayan halka (kring) + üstte zıplayan "BAŞLA" balonu (kbounce) +
    yanda maskot (46px gradyan daire, kfloat) — maskot şu-an düğümünün ofsetine göre sol/sağ.
  - **Hazır** = beyaz + yıldız + ince kenar
  - **Kilitli** = #ECE6DD + kilit; `href` yok (tıklanamaz).
- Basma efekti: `style-active` ile 5px aşağı iner, ledge kaybolur (fiziksel düğme hissi) — patika
  düğmelerinin imzası, KORUNUR.
- **Checkpoint** (ünite sonu, 86px kare): Tamam = altın gradyan "ÜNİTE FETHEDİLDİ" · Şu an =
  terracotta gradyan "ÜNİTE TESTİ · BOSS" → Boss Savaşı · Kilitli = gri "KİLİTLİ".
- Patika sonu: bayrak + "{ders} bitiş".

### Sağ ray
1. **Sıradaki adım:** "Sıradaki adım" rozeti + **MasteryBadge** + konu başlığı + açıklama
   ("Bu derste en düşük hâkimiyetli konun (%{n}). En çok kazanımı burada elde edersin.") +
   "{n} soru · ~{n} dk" + "Konuya başla" (ledge'li accent CTA) + ikincil link
   "Atomlara in · en zayıf: {atom}" → Bilgi Atomları(?konu=).
2. **Ders hâkimiyeti halkası:** 100px halka %{n} + "{n}/{n} konu tamam · Tahmini bitiş: **{ay}**".
3. **Lejant kartı** (4 durum).

### ⚠ Port notları
- kbounce/kring/kfloat animasyonları `prefers-reduced-motion: reduce`'ta KAPANIR (prototipte
  guard yok — porta eklenir; view-transition guard'ı zaten desen).
- Zikzak ofsetleri 390px'te 0/±28px'e daralır (taşma testi).

### Veri bağlama
- `GET /curriculum/{ders}` (ünite ağacı + durumlar + next) · `GET /subjects` (hâkimiyet) ·
  `GET /topics` (en zayıf konu) · atom bağı: `GET /topics/{konu}/atoms` (varlığı ikincil CTA'yı açar).
- Düğüm durum geçişleri sunucudan gelir; istemci "tamamlandı" işaretlemez (çözüm ekranı yazar, yol okur).
- Üç durum: Skeleton (bant + 4 düğüm iskeleti) · ErrorState · yeni kullanıcıda tüm patika "hazır/kilitli" doğal boş hâldir.

---

## C · Ekran: Bilgi Atomları (`KIRO Bilgi Atomlari.dc.html`)

**Tema:** paper. **Layout:** SideNav YOK — tek sütun makale düzeni (max 820px). **Rota:** `/atomlar?konu=`.
(Öğrenme Yolu ve Panel'den drill-down hedefi.)

### Kopya — BİREBİR (bu ekran değer-önerisi anlatısıdır)
| Yer | Metin |
|---|---|
| Kicker | KONU DEĞİL · TAM ADIM (terracotta, letterspaced) |
| Başlık (Instrument Serif 38px — bu ekranda serif MEŞRU: his/mantra anlatısı) | Bilgi Atomları |
| Giriş | Motor "Türev'de zayıfsın" demez — konuyu ince atomlara böler ve **tam başarısız adımı** gösterir. Böylece 12 soru boşa değil, doğru yere gider. |
| İçgörü kutusu | **Sorun {konu} değil** — sadece **{atom} adımında** zayıfsın. Motor bugünkü 12 soruyu tam bu atoma ayırdı; diğer {n} atomun sağlam, onlarla vakit harcamıyoruz. |
| CTA | {atom} atomunu çöz (12 soru) → Soru Çözme |

### Bloklar
- Odak konu chip'leri (zayıf konular; aktif = terracotta #E0593F + ledge). `?konu=` URL paramı
  başlangıç seçimi (route state; paylaşılabilir link).
- Breadcrumb: {konu} → {kavram} → **{zayıf atom}** (amber vurgu).
- Atom listesi: zayıf atom = amber zemin + ünlem + pulseA animasyonu (reduced-motion'da kapalı);
  sağlamlar = yeşil tik. Her satırda **MasteryBadge** (zayıf trend=down).
- İçgörü kutusu: #FFF3EE→beyaz gradyan + sol 3px #C77A1E (amber dolgu kanonu).

### Veri bağlama
- `GET /topics/{konu}/atoms` → kavram + atomlar[{ad, hakimiyet}]; en zayıf atom SUNUCU yanıtında
  işaretli gelir (öneri: `enZayif: true` alanı — prototipteki min-pct istemci hesabı taşınmaz).
- Üç durum: Skeleton · ErrorState · atom kırılımı olmayan konu → bu rotaya link zaten üretilmez.

### DoD notları
- pulseA yalnız dekoratif; zayıf atom bilgisi metin + ikonla da mevcut (renge bağımlı değil).
- 390px: breadcrumb sarar; chip satırı yatay scroll değil wrap.

---

## D · Ekran: Çalışma Modları (`KIRO Calisma Modlari.dc.html`)

**Tema:** paper. **Layout:** SideNav YOK — tek sütun (max 880px), 2×2 mod grid'i (≤760px tek sütun).
**Rota:** `/modlar`.

### Kopya — BİREBİR
| Yer | Metin |
|---|---|
| Kicker | TEK HAVUZ · ÇOK YOL |
| Başlık (serif 38px) | Çalışma Modları |
| Giriş | Aynı kart havuzundan farklı getirim biçimleri — motor senin verinden üretir, ekstra içerik yok. Çeşitlilik hafızayı güçlendirir. |
| Havuz kartı | Türev · zincir kuralı havuzu · {n} kart · zayıf atomundan otomatik derlendi · sağda {tier} %{n} |
| Alt not | Not: Dört mod da aynı {n} kartı farklı getirim yüküyle test eder — tanıma (kart), hatırlama (test), eşleme (eşleştirme), hız altında geri getirme (hız). Motor hangi modun hangi kartta en çok işe yaradığını öğrenir. |

### Mod kartları (renk + ikon + sayaç + açıklama + CTA)
1. **Kart** (terracotta) "{n} kart" → FSRS Tekrar — "Klasik çevir-göster…"
2. **Test** (mavi #3B6FD4) "{n} soru" → Soru Çözme — "Çoktan seçmeli sınav biçimi…"
3. **Eşleştirme** (yeşil) "{n} çift" → FSRS Tekrar — "Kavram ↔ tanım eşle…"
4. **Hız** (amber) "60 sn" → Düello — "Zaman baskısı altında geri getirme…"
Eşleştirme ve Hız'ın KENDİ oturum UI'ları prototipte YOK — rotaları en yakın deneyime gider
(prototip kararı; ayrı mod ekranları kapsam dışı, ileride ürün kararı).

### Veri bağlama
- Havuz: `GET /topics` (en zayıf mat konusu) + `GET /review/due` (kart sayısı) — hafif ekran,
  ayrı uç gerektirmez.
- Üç durum: Skeleton · ErrorState · havuz boşsa EmptyState (FSRS boş-durum kopyasıyla aynı ton).

---

## Sprint 5 açık noktaları
1. **`GET /plan/week` ucu openapi'de yok** — en kritik eksik; plan motoru sözleşmeye eklenmeli (öneri yukarıda).
2. Atom yanıtına `enZayif` işareti eklenmesi (istemci min-hesabı yerine).
3. Eşleştirme + Hız modlarının gerçek oturum UI'ları: kapsam dışı mı, Faz 6 backlog'u mu? (ürün kararı)

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz; Grup 4 bitince tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Haftalık Plan: blok listeleri `<ul>/<li>`; gün kolonları `aria-label` ("Pazartesi · 3 blok · 85 dk").
- Öğrenme Yolu düğümleri: buton + `aria-label` (mevcut) + kilitli `aria-disabled="true"`; klavye sırası = curriculum sırası.
- Bilgi Atomları chip seçici radiogroup + `aria-checked`; drill linki bağlam taşır ("Türev atomlarına in").
- Çalışma Modları: kart = tek buton tek eylem; süre/kart sayısı metinle.
