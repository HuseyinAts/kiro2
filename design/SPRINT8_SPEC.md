# KIRO2 — Sprint 8 Port Spec'i: Sosyal & Motivasyon (Grup 6)

Kapsam: **4 ekran** (Lig · 1v1 Düello · Arkadaş Serisi · Seri Dondurma).
Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 7 DoD tamam (Kutlama rotası çalışıyor — Lig ve Seri Dondurma ona bağlanır;
ConfettiDawn hazır).

Bu grupta kaygı-duyarlı tasarımın EN yoğun olduğu yer burası: sıralama gizleme, sakin mod,
insani nudge. Bu mekanizmalar ürünün farklılaştırıcısı — hiçbirini "basitleştirme" adına düşürme.

---

## A · Ekran: Lig (`KIRO2 Lig.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="league"`) + içerik (max 1280px). **Rota:** `/lig`.

### İki kaygı-duyarlı anahtar — ÜRÜN KİMLİĞİ (props → kullanıcı tercihi)
- `sakinMod` (varsayılan AÇIK): kopyalar yumuşar — "Altın Ligi'ndesin — kendi ritminde ilerle,
  sıralama ikincil." · sayaç "Hafta sonu yenilenir" (nötr kutu) · alt bölge "Alt bölge · son 5"
  (amber) · buton "XP kazan". KAPALI: "#{n} sıradasın · ilk 7 Platin'e yükselir" · "Bitişe 3 gün 14 sa" ·
  "Düşme bölgesi · son 5". Üretimde: kullanıcı tercihi (Ayarlar), `/me` profiline yazılır.
- `siralamaGizli` + sayfa içi "Sıralamayı gizle/göster": gizliyken boş-durum kartı
  "Sıralama gizli — odak sende." + "XP'n, serin ve terfi hakkın aynen işliyor. Kıyası istediğin an
  geri açarsın — bu bir ceza değil, bir tercih." (kopya BİREBİR) + koyu ray kartı "Bu haftaki emeğin".
  Tercih kalıcı (`/me`).

### Bloklar
1. **Sen vs dün şeridi** (en üstte, sıralamadan ÖNCE — hiyerarşi bilinçli): serif "Yarıştığın tek
   kişi dünkü sensin." + "+{n} XP · geçen haftaya +%{n}" + dün/bugün mini çubukları.
2. **Lig bandı:** altın kalkan SVG + "Altın Ligi" + sayaç/gizle butonu + 6 kademeli tier şeridi
   (Bronz→Elmas; aktif kademe vurgulu).
3. **Podyum** (ilk 3, altın/gümüş/bronz kaideler) + **sıralama listesi** 3 bölge: Yükselme (ilk 7,
   yeşil) · Güvenli · Alt bölge (amber sakinken). SEN satırı accent kenarlı; trend oku satır başına.
4. **Sağ ray:** koyu "Bu haftaki sıran #{n}" kartı + bölge ilerleme barı · "Terfi ödülleri"
   (Platin + 500 XP + rozet) · seviye ilerleme kartı ("{n} XP kaldı — birkaç oturum daha.") ya da
   seviye atlama kartı → Kutlama?type=seviye.

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- sakinMod KAPALI yolundaki kırmızılar: sayaç kutusu #FEF2F2/#FBD5D5 + "Risk altında ▾" #FB7185 →
  **amber ailesi** (#FBF0DE/#F2D9AC, metin #9A5D0D). Sakin-olmayan mod bile kanona uyar — fark
  kopya netliğinde, renk şiddetinde değil.
- Trend okları ▲/▼/– ve "Güvende ✓" METİN glyph'leri → bespoke SVG üçgen/tik.
- SEN satırı zemini #F5F6FF (indigo-50'ye kayan ton) → #FFF3EE (accent zemin).

### Veri bağlama — ⚠ uç eksik
- **openapi'de lig ucu YOK.** Öneri: `GET /league` → {lig, kademeler, sıralama[], benimSıram,
  haftaBitis, senVsDun{buHafta, gecenHafta}}. XP kazanımı diğer uçlardan doğal akar; **"XP kazan"
  butonu PROTOTİP ARACIDIR — taşınmaz.**
- Sıralama gizliyken istemci listeyi İSTEMEZ (gizlilik = veri de çekilmez; yalnız kendi özetin).
- Üç durum: Skeleton · ErrorState · lig yoksa (ilk hafta) "Ligin Pazartesi başlıyor" boş durumu (kopya onaya).

### DoD notları
- Sıralama listesi `<ol>` semantiği; SEN satırı `aria-current="true"`.
- 390px: podyum sığar (max-width'ler); ray alta.

---

## B · Ekran: 1v1 Düello (`KIRO2 Duello.dc.html`)

**Tema:** koyu gece-mavisi arena (#16203B→#0A0E1B) — Boss gibi oyun sahnesi istisnası (çalışma
ekranı değil). **Layout:** SideNav YOK; 58px bar (X → Lig · "Matematik · Hızlı" · tur sayacı).
**Rota:** `/duello/:macId`.

### Sahne — BİREBİR
- **VS bandı:** sen (accent kenarlı avatar + puan) — orta (skor {n}—{n} + 96px halka sayaç +
  7 tur noktası) — rakip (terracotta kenarlı + kfRing nabzı beklerken).
- Sayaç: 10 sn, son 3 sn'de halka terracotta'ya döner (baskı değil oyun temposu — süre COŞKU
  rengi, alarm değil).
- Soru kartı: 2×2 seçenek; kilitlenince "Cevabın kilitlendi" + rakip durumu pili
  ("Mert ✓ doğru · 4 sn").
- Tur sonucu bandı: "Turu kazandın!" / "Rakip turu aldı" / "Berabere" + alt metin
  (ör. "Doğruydun ama Mert daha hızlıydı.") + "Sonraki tur" CTA.
- **Güçler:** 50:50 ×1 · Süre Dondur ×2 — prototipte GÖRSEL; üretim davranışı tanımsız (açık nokta:
  MVP'de güçler pasif gösterilir mi hiç mi? Öneri: MVP'de kaldır, veri modeli hazır olunca ekle).
- Bitiş overlay'i: Kazandın / Berabere / "Bu sefer olmadı" ("Mert bu turu aldı. Rövanşta sen
  kazanırsın." — yenilgi kopyası nazik, BİREBİR) + skor + "+{n} XP" + "Tekrar oyna" / "Lige dön".
- Kazanınca konfeti → ConfettiDawn.

### ⚠ MİMARİ AÇIK NOKTA — ADR-003 çatışması (karar ister)
Prototip rakibi Math.random ile simüle eder. Gerçek 1v1 canlı akış ister; **ADR-003 (15 sn polling,
WS yok)** bununla çelişir. Seçenekler:
1. **MVP: asenkron düello** — rakip turlarını kendi hızında oynar, sonuçlar poll ile gelir
   ("Yazışmalı satranç" modeli; UI'da "Rakip cevaplıyor…" yerine "Sıra sende — Mert'in sonucu gelince
   görürsün"). ADR-003'e uyar. (ÖNERİLEN)
2. Düello sırasında kısa-poll (2-3 sn) istisnası — ADR-003'e ek not gerekir.
3. Düelloyu post-MVP'ye ertele (PORT_DURUM'da işaretle).
Karar gelene dek ekran PORTLANIR ama eşleşme akışı mock kalır.

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- Ekran accent'i prototipte **#0D9488 teal varsayılan** — marka ipliği coral'dır; port varsayılanı
  `#FF6F5C` (teal bir keşifti).
- Rakip durum/sonuç kırmızıları #FB7185 → terracotta (#E8836B/#C2452B).
- "✓ doğru / ✗ yanlış" ve sayaçtaki "✓" METİN glyph'leri → bespoke SVG.
- İnline konfeti → ConfettiDawn.

### Veri bağlama — ⚠ uç eksik
- **openapi'de düello ucu YOK.** Öneri: `POST /duel/match {ders, mod}` → mac; `POST /duel/{id}/answer`
  → {dogru, sürem, rakipDurum?, turSonucu?, macSonucu?}; rakip sonuçları poll (`GET /duel/{id}`).
  Puan formülü (100 + kalan sn × 5) SUNUCUDA. XP ödülü sunucudan.
- Soru havuzu sunucudan (kolay/hızlı set) — istemci `catBankMat` filtresi taşınmaz.

### DoD notları
- Sayaç `role="timer"` + kalan süre görsel-dışı da erişilir; 10 sn'lik tur için reduced-motion'da
  halka animasyonu yerine sayı yeterli.
- 390px: `.rvs` sıkışır (avatar 48px), tur noktaları gizli (prototip davranışı).

---

## C · Ekran: Arkadaş Serisi (`KIRO2 Arkadas Serisi.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="arkadas"`) + içerik (max 1000px). **Rota:** `/arkadaslar`.

### Bloklar — BİREBİR
1. **Ortak seri hero'su** (coral gradyan): "Ortak seri · Elif ile" + iki avatar arasında alev +
   ortak seri sayısı + durum satırı "Sen bugün ✓ · Elif henüz çalışmadı" + "Elif'i dürt" butonu →
   basılınca "Gönderildi ✓" + metin "…nazik bir dürtme gönderildi" (buton devre dışı kalır — günde 1).
2. **Birlikte görev kartı:** "Birlikte 100 soru çözün" + "Ödül: ikinize de 2× XP boost + ortak rozet." +
   çift renkli ilerleme barı (Sen coral · Elif pembe) + "⏳ 2 gün kaldı" rozetı.
3. **Arkadaş listesi:** Seri/XP sıralama toggle'ı; satır = avatar + ad/sınıf + seri + durum chip'i
   ("çalıştı ✓" yeşil / "henüz değil" amber) + XP + tebrik butonu (basılınca yeşil tik + "+1" float).
   İlk satır altın vurgulu. Alt bilgi kutusu: "Ortak seriler, bireysel seriden daha dayanıklıdır:
   kimse arkadaşını bırakmak istemez."

### ⚠ Kanon düzeltmeleri (porta taşınmaz — kanon-lint yakalar)
- **"Arkadaş ekle" hover'ı `#4338CA` (indigo, yasak)** → `filter:brightness(0.94)`.
- **"⏳" EMOJİ** (görev kartı) → bespoke SVG kum saati/saat.
- "çalıştı ✓" / "Gönderildi ✓" / "Tebrik gönderildi ✓" METİN glyph'leri → bespoke SVG tik.
- "BİRLİKTE GÖREV" rozet zemini #F5F3FF (menekşe-50) → #FFF3EE.

### Veri bağlama — ⚠ uç eksik
- **openapi'de arkadaş ucu YOK.** Öneri: `GET /friends` (liste + ortak seri + görev durumu) ·
  `POST /friends/{id}/nudge` (günde 1 sınırı SUNUCUDA) · `POST /friends/{id}/congrats` ·
  `POST /friends/invite`. Birlikte görev: sunucu tanımlı (`/friends/quest`).
- Dürtme alıcıda push/bildirim üretir (ADR-004: web fazında bildirim merkezi üzerinden).
- Üç durum: Skeleton · ErrorState · arkadaş yoksa davet boş-durumu ("Birlikte çalışmak seriyi
  dayanıklı kılar — ilk arkadaşını davet et" tonu, kopya onaya).

### DoD notları
- Dürtme/tebrik butonları `aria-pressed` + durum değişimi `aria-live="polite"`.
- 390px: hero grid tek sütun; arkadaş satırı XP sütunu gizlenebilir (prototipte yok — taşma testi).

---

## D · Ekran: Seri Dondurma (`KIRO2 Seri Dondurma.dc.html`)

**Tema:** paper. **Layout:** SideNav (`active="seri"`) + içerik (max 980px). **Rota:** `/seri`.

### Bloklar — BİREBİR
1. **Seri hero'su** (amber gradyan #7C2D12→#C77A1E): alev + {n} + "günlük seri" + "En uzun · {n} gün" +
   "Seriyi kutla" → Kutlama?type=seri.
2. **Bu hafta şeridi:** 7 gün karosu — tamamlanan (alev, amber zemin) · dondurma (buz kristali SVG,
   buz-mavisi zemin #DBEAFE) · bugün (coral kontur) + lejant + başlıkta "Per günü dondurma kurtardı".
3. **Seri Dondurma kartı:** buz ikonu + "{n} hakkın" + "Bir gün kaçırırsan serin **sıfırlanmaz** —
   dondurma otomatik devreye girer. Kötü bir gün, ayların emeğini silmesin." + istatistik kutusu
   ("Dondurma kullananlar 7 günden sonra ortalama %48 daha uzun seri sürdürüyor.").
4. **Nudge önizleme kartı:** İNSANİ ton — "Bugün son bir adım kaldı — serini koru. Acelesi yok,
   sana uygun bir saatte hallederiz." + "Günde en fazla 1 nazik hatırlatma. İstediğin an kapatabilirsin."
5. **Kilometre taşları:** 7 gün Alev → şu an → rekor → 30 gün taç (bağlayıcı çizgiler).
6. **CTA bandı:** "Bugünü tamamla, seriyi {n}'e taşı" + "Sadece 1 ders veya 10 soru yeterli —
   acelesi yok." → Soru Çözme.

### ⚠ Port kararları
- **"AGRESİF (anti-örnek)" nudge tonu ÜRETİME TAŞINMAZ** — prototipteki toggle pedagojik gösterimdir
  (kırmızılar + emoji bilinçli anti-örnek). Portta yalnız insani ton; anti-örnek tasarım
  dokümantasyonunda yaşar. (Bu karar #FEE2E2/#FECACA/#991B1B/⚠️ ihlallerini kökten çözer.)
- Buz-mavisi (#DBEAFE/#2563EB) dondurmanın SEMANTİK rengi — kalır. Ancak istatistik kutusundaki
  **#1E40AF (yasak indigo listesinde)** → #2563EB'ye çekilir.
- "%48 daha uzun" iddiası: kaynak doğrulanana dek yayın kopyasından çıkar ya da "içeride ölçülen"
  ifadesine yumuşatılır (açık nokta — ürün/hukuk).

### Veri bağlama
- `/me` (seri, rekor) · `/streak/checkin` (mevcut) · **eksik:** dondurma hakları + hafta durumu →
  öneri: `GET /streak` {seri, rekor, dondurmaHak, hafta[]} + dondurma OTOMATİK (sunucu uygular,
  istemci yalnız gösterir — buton yok, kanon: affedicilik zahmetsiz olmalı).
- Nudge tercihi: `/me` bildirim ayarı (kapatılabilir — Ayarlar Sprint 9).

### DoD notları
- Hafta karoları `role="img"` + gün-durum etiketi; dondurma karosu "Perşembe — dondurma kullanıldı".
- 390px: `.rstack` tek sütun; kilometre taşları yatay scroll yerine sarar (taşma testi).

---

## Sprint 8 açık noktaları
1. **Düello mimarisi:** asenkron model (ADR-003 uyumlu, önerilen) / kısa-poll istisnası / erteleme?
2. Düello güçleri (50:50, Süre Dondur) MVP'de var mı? (öneri: yok)
3. Sosyal uçlar openapi'ye eklenecek: `/league` · `/duel/*` · `/friends/*` · `/streak` (Faz 4 sözleşme işi).
4. "%48" istatistiğinin kaynağı — yayın kopyası kararı.
5. Lig "ilk hafta" ve arkadaş "davet" boş-durum kopyaları onaya sunuldu.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 6 bitti** → PORT_DURUM'da Grup 6'ya tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Lig: liste `<ol>` semantiği; SEN satırı `aria-current="true"`; "Sıralamayı gizle" `aria-pressed` + değişim `aria-live="polite"`.
- Düello: skor güncellemeleri tek `polite` bölge; asenkron sonuç poll'la gelince `polite` duyuru + başlık odağı.
- Arkadaş Serisi: ortak seri `role="progressbar"`; davet butonları net erişilebilir ad.
- Seri Dondurma: hak sayısı metinle; onay akışı tek adım, odak sırası korunur.
