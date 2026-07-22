# KIRO2 — Sprint 6 Port Spec'i: Duygusal çekirdek I (İLK KOYU EKRANLAR)

Kapsam: **3 ekran** (Bugün/Şafak hub · Kutlama · Mola) — Grup 5'in ilk yarısı.
Grup 5'in kalanı (Geri Sayım · Başarımlar · Boss Savaşı) Sprint 7'de.
Piksel referansı her zaman kaynak DC'dir.

## ⚠ Bu sprintte dusk teması İLK KEZ kuruluyor — tema kuralları
- Tema ekran TÜRÜdür (kanon): bu üç ekran **dusk**; kullanıcı toggle'ı YOK.
- `tokens.css → .k-dusk` sınıfı / `tokens.ts → dusk` seti bu sprintte ilk kez gerçek ekrana bağlanır.
- Koyu ekranda **#6B6478 KULLANILMAZ** (kanon-lint uyarısı) — ikincil metin dusk tonları:
  `#B6A6C4` (ikincil) · `#8C8398` (soluk) · `#9B8FB5` (ikon) · `rgba(236,228,240,0.8)` (gövde).
- Şafak gökyüzü gradyanı KANON'dur (README'deki tam durak listesi) — yaklaşıklaştırma yok, birebir.
- Tüm ambient animasyonlar (twinkle, sunPulse, floatUp, cfall, cglow, breatheOrb…) porta
  `prefers-reduced-motion: reduce` guard'ıyla girer (prototipte guard yalnız view-transition'da).

---

## A · Ekran: Bugün — Şafak hub'ı (`KIRO Safak.dc.html`)

**Tema:** DUSK. **Layout:** SideNav YOK — dikey akış, max 840px orta sütun. **Rota:** `/bugun`
(duygusal giriş kapısı; Panel `/panel` işlevsel kapı olarak ayrı yaşar).

### Gökyüzü hero'su (430px)
- Kanon gradyan (176deg, #141029→…→#FFC76F) + 6 yıldız (twinkle, farklı faz/süre) +
  güneş (radyal glow 520px sunPulse + 128px çekirdek) + 2 katmanlı tepe silüeti SVG (#1C1330/#140E22).
- Üst bar: KIRO şafak logosu · "Sınava sayım" cam pili → Geri Sayım · seri pili ("{n} gün seri").
- Kopya: "{selamlama}, {ad}" — saat bazlı: 5-12 Günaydın · 12-18 İyi günler · 18-23 İyi akşamlar ·
  23-5 "Geç oldu" (gece çalışana yumuşak dokunuş — KORUNUR).
- Başlık: "Şafağa **{n} tuğla** kaldı." (altın vurgu) + "Bugünkü tuğlanı koyalım — acelesi yok,
  sakin adım adım." — {n} = sınava kalan gün (Geri Sayım ile AYNI kaynak).

### Görev kartı (ufka oturan, -62px overlap; floatUp)
- Cam-koyu gradyan kart: "BUGÜNKÜ İLK TUĞLA" (şeftali eyebrow) + görev başlığı + "~30 dk ·
  ● zayıf konun · Matematik" + ilerleme barı (coral gradyan) + "bugün 3/5".
- Sağda 104px kare "Başla" düğmesi (coral gradyan, basınca scale 0.96) → Soru Çözme.
- Veri: Haftalık Plan'ın bugünkü ilk açık bloğu (plan motoru — Sprint 5 açık noktası `/plan/week`).

### Ders kartları ("Derslerin · hâkimiyet · son 30 gün" + "Yolu gör →")
3 sütun (≤800px 2'li): koyu kart #19131F/#2A2236, köşede ders-renkli glow, nokta + ad + %n +
bar. **KOYU-parlak ders paleti** kullanılır (mat #5B8DEF · fiz #A77BFF · kim #E25A72 · biy #2DD4A7 ·
tur #FFB347) — Panel'in açık paletiyle KARIŞTIRMA (iki palet tablosu README'de).

### Alt kartlar
- **FSRS kartı:** "{n} konu tekrar bekliyor" + "{konu} sevgi istiyor — ~{n} dk yeter." → FSRS.
- **SEN vs DÜN kartı** (yeşil ton): "+{n} dk" + iki çubuk (dün/bugün) + "Sadece dünkü seninle
  yarışıyorsun." — sıralama-baskısı yerine öz-kıyas; kopya BİREBİR.
- **Bugün nasılsın?** ("KIRO tonunu ayarlar"): 5 bespoke SVG yüz (bitkin/gergin/idare/iyi/harika —
  ağız path'i değişir; emoji DEĞİL). Seçim mesajı amber-şeftali kutuda; 5 mesaj BİREBİR
  (ör. bitkin: "Tükendiysen bugün 10 dakika yeter — gerçekten. Dinlenmek de hazırlığın parçası.").
- **Mantra kartı** (serif italik): "Sınav bir günü ölçer. Sen çok daha fazlasısın."

### Veri bağlama
- `/me` (ad, seri, bugünDk) · `/subjects` (koyu palet renkleriyle) · `/review/due` (FSRS kartı) ·
  görev: plan motorundan · tuğla sayısı: sınav tarihi (`/me` ya da Geri Sayım kaynağı).
- **AÇIK NOKTA — ruh hâli:** openapi'de mood ucu yok. "KIRO tonunu ayarlar" sözü ton kişiselleştirmesi
  ima ediyor → öneri: `POST /me/mood {gun, deger}` (AI proxy tonu + kopya seçimine girdi). Karar
  gelene dek seçim YERELDE tutulur (localStorage, gün anahtarlı) ve mesaj istemciden gelir.
- Üç durum: Skeleton (hero statik degrade + kart iskeleti) · ErrorState (görev kartı yerine sakin
  amber kart; gökyüzü her zaman çizilir — boş his yok) · yeni kullanıcı: görev yoksa CTA Onboarding'e.

### DoD notları
- Hero metinleri gradyan üstünde: kontrast noktası en açık bölge (alt-sağ) — başlık sola sabit, test et.
- Mood butonları gerçek `<button>` + `aria-pressed`; yüz SVG'leri `aria-hidden`, etiket metin.
- 390px: başlık 30px'e iner (`.rh1`), kart grid'leri tek sütun; güneş konumu %67 sabit kalır.

---

## B · Ekran: Kutlama (`KIRO2 Kutlama.dc.html`)

**Tema:** DUSK. **Layout:** tam ekran merkezli tören sahnesi. **Rota:** `/kutlama?type=&xp=&seri=`
(gunluk · seviye · seri · boss). Diğer ekranlar bu rotaya parametreyle gelir (FSRS "Günü kutla" → ?type=gunluk).

### Sahne
- Zemin: radyal gece degrade (#3E1F4E→#110C18) + 4 yıldız.
- Konfeti: 20 deterministik parça, şafak paleti (#FF6F5C #FF9E7D #FFD98C #C9A8E0 #2DD4A7),
  cfall sonsuz döngü — **reduced-motion'da konfeti hiç render edilmez** (ConfettiDawn davranışıyla aynı;
  isterse ConfettiDawn bileşeni kullanılır, prototipteki inline liste taşınmaz).
- Merkez: 104px gradyan rozet (tür ikonu: tik/yıldız/alev/kalkan — bespoke SVG) + cglow halo + cpop girişi.
- Sıralı cup girişleri (0.15s kademeli): eyebrow → başlık (serif 58px) → alt metin → ödül chip'leri →
  mantra → CTA.

### Tür içerikleri — BİREBİR (kopya tablosu)
| Tür | Eyebrow | Başlık | Alt metin | Ödül | Mantra | CTA |
|---|---|---|---|---|---|---|
| gunluk | Günlük hedef | Bugünkü tuğlanı koydun. | {n} dakika çalıştın — şafağa bir tuğla daha yakınsın. Yarın da buradayız. | +40 XP · bugünkü kazanç | Büyük duvarlar tek tuğlayla yükselir. | Devam et |
| seviye | Seviye atladın | Seviye {n}! | Toplam {xp} XP topladın. Her seviye, dünkü senden bir adım ileride. | +120 XP + "Seviye {n} · yeni rütbe" | Kıyasladığın tek kişi, dünkü sensin. | Yoluna devam et |
| seri | Seri kilometre taşı | {n} günlük seri! | Rekoruna {n} gün kaldı. İstikrar, hızdan daha güçlüdür — sakin devam. | {n} gün üst üste | Her gün küçük bir söz, kendine tutulmuş. | Seriyi sürdür |
| boss | Boss zaferi | Ejderha yenildi! | {konu} ejderhasını alt ettin — en zayıf konun artık senin gücün oluyor. | +120 XP + "{konu} · ustalık rozeti" | Korktuğun konu, en çok büyüdüğün yerdir. | Zaferi kutla |

Tür renk kimlikleri: gunluk coral/pembe · seviye altın · seri şeftali/amber · boss mor (#C9A8E0/#8B5CF6 —
mor yalnız Fizik + boss mistiği; kanon istisnası zaten Boss ekranında tanımlı).

### Port notları
- Alt kısımdaki "önizle:" tür değiştirici PROTOTİP ARACIDIR — üretime taşınmaz.
- CTA hedefi tür bağlamına göre: gunluk → Bugün · seviye/seri → Bugün · boss → Başarımlar (ürün
  kararı; prototipte hepsi Bugün'e döner — şimdilik aynen).
- XP/ödül değerleri sunucudan gelir (`/streak/checkin`, `/questions/*/answer` yanıtlarındaki xp
  alanları); ekran salt gösterir.

### DoD notları
- `role="status"` + başlığa focus (tören ekranı ekran okuyucuda da duyulur).
- 390px: başlık 40px (`.rhl`); chip'ler sarar.

---

## C · Ekran: Mola (`KIRO2 Mola.dc.html`)

**Tema:** DUSK (en koyu zemin: #0F0B16 — gece-şafak sakinliği). **Layout:** tek sütun max 720px,
tam yükseklik. **Rota:** `/mola`. Haftalık Plan "Nefes molası" bloğu + çalışma ekranlarından gelinir.

### Kopya — BİREBİR
| Yer | Metin |
|---|---|
| Kicker | NEFESLEN (lavanta #C9A8E0) |
| Başlık (serif 33px) | Mola da hazırlığın bir parçası. |
| Orb altı | 4 · 4 · 4 · 4 KUTU NEFESİ · ORBLA BİRLİKTE |
| Alt | Bugün **{n dk / n sa n dk}** çalıştın — bu molayı hak ettin. |
| Mantra (serif italik) | "Dinlenen zihin daha iyi öğrenir." |
| CTA | Hazır hissediyorum → Bugün · üst sağ "Çalışmaya dön" |

### Nefes orbu (ekranın kalbi)
- 260px sahne: dış halka (breatheRing) + degrade orb (breatheOrb) — **16s döngü, 4 faz** (4-4-4-4
  kutu nefesi): büyü (al) → dur (tut) → küçül (bırak) → dur (tut).
- Faz yönergeleri ("Nefes al · Tut · Yavaşça bırak · Tut") CSS opacity zamanlamasıyla (c1-c4)
  orb'la senkron — port'ta aynı 16s zamanlama korunur (JS timer da olur; animasyon tercih edilir).
- **reduced-motion:** orb sabit orta boyda; yönergeler statik liste olarak alt alta ("4 sn nefes al ·
  4 sn tut · 4 sn bırak · 4 sn tut") — egzersiz erişilebilir kalır.

### Dinlenme seçenekleri (4 chip: 2 dk nefes · Göz dinlendir · Su iç · Kısa yürüyüş)
Prototipte tıklanmaz görsel öneriler — porta AYNEN (aksiyon yok; öneri kartı). Renkleri:
lavanta/şeftali/mavi/yeşil %14 dolgu + bespoke ikon.

### Veri bağlama
- Yalnız `/me` (bugünkü çalışma dakikası). Ekran başka istek atmaz — mola ekranı ağ trafiğiyle
  meşgul edilmez; veri yoksa alt satır gizlenir (hata kutusu ASLA gösterilmez — sakinlik bozulmaz).

### DoD notları
- Orb `aria-hidden`; egzersiz talimatı metinle mevcut. Sayfa başlığına focus.
- 390px: chip'ler 2×2 sarar (`.rchips`); orb 260px sığar (padding daralır).

---

## Sprint 6 açık noktaları
1. **Mood ucu yok** — `POST /me/mood` önerisi (ton kişiselleştirme sözünün altyapısı). Karar gelene dek yerel.
2. Kutlama CTA hedefleri tür bazında farklılaşsın mı? (şimdilik hepsi Bugün'e)
3. "Şafağa {n} tuğla" sayacının kesin tanımı: sınava kalan gün mü, plan görev sayısı mı? (prototipte 47 sabit — Geri Sayım ekranıyla senkron olmalı; Sprint 7'de netleşir)

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. Dusk tema kurulum maliyetini AYRI satır olarak not et
(sonraki koyu ekranlar için kalibrasyon).

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Gökyüzü/yıldız/konfeti dekoratif katmanlar `aria-hidden="true"`; içerik DOM'da önde.
- Mood butonları radiogroup + `aria-checked`; mood mesajı `aria-live="polite"`.
- Mola nefes metinleri İÇERİKTİR: reduce'ta da görünür (hedefli guard); faz değişimi tek `aria-live="polite"` bölgeden.
- Kutlama: başlık programatik odak; CTA sırası DOM'da birincil önce.
