# KIRO2 — Sprint 11 Port Spec'i: Öğretmen & Veli (Grup 9)

Kapsam: **6 ekran** (Öğretmen Paneli · Öğrenci Özeti (öğretmen, A2) · Veli Paneli · Veli Bağlama
(KVKK — spec: YENI_SOHBET_DEVIR §6 + `KIRO2 Veli Baglama.dc.html`) · Ödev Atama · Sınıf Kurulumu — A3, 2026-07-22). Öğrenci tarafı
(Ödevlerim) Sprint 1'de portlandı — bu sprint halkayı kapatır. Piksel referansı her zaman kaynak DC'dir.

Rol kanonu: öğretmen/veli SİZ-dili; öğrenciye dair risk sinyalleri YALNIZ yetişkine gösterilir
(öğrenciye bayrak yok); sınıf sıralaması hiçbir yüzeyde yayınlanmaz.

---

## A · Ekran: Öğretmen Paneli (`KIRO2 Ogretmen Paneli.dc.html`)

**Tema:** paper. **Layout:** SideNav öğretmen preset'i (`ui-starter/SideNav` — Sprint 2'de test
edildi) + içerik (max 1280px). **Rota:** `/ogretmen` (rol=öğretmen varsayılan giriş rotası).

### Bloklar — BİREBİR
- Topbar: sınıf chip'leri (12-A · Sayısal aktif / 11-B · EA) + "Ödev oluştur" CTA.
  **⚠ Prototip hatası:** CTA `Soru Cozme`'ye linkli — port: `/ogretmen/odev/yeni` (Ödev Atama).
- KPI ×4: Sınıf ortalama net 72,4 (+3,1) · Aktif öğrenci 28/32 (7g) · Teslim bekleyen ödev 6
  ("2 gecikmiş" amber) · Bu hafta çözülen soru 4.210 (+12%).
- **Öğrenci Performansı tablosu:** avatar+ad+durum · ort. net (virgüllü) · hâkimiyet bar+% ·
  son aktivite+trend. Satır → öğrenci-özet sayfası (`/ogretmen/ogrenci/:id` salt-okur —
  **TASARLANDI 2026-07-05: `KIRO2 Ogretmen Ogrenci Ozet.dc.html`**, aşağıda A2; prototip
  linkleri de bu DC'ye güncellendi — tablo satırları artık tıklanır).
- **Dikkat gerektiren öğrenciler** (sağ ray): 3 kart — giriş yok / net düşüşte / ödev teslim edilmedi.
- **Sınıf konu hâkimiyeti:** 4 konu barı (≥75 yeşil · ≥60 amber · altı terracotta).

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- "Dikkat gerektiren" ilk kartı KIRMIZI ailede (#FEF2F2/#FBD5D5) — kanon: risk AMBER.
  Port: en yüksek öncelik = koyu amber (#FBF0DE/#F2D9AC, metin #9A5D0D), orta = açık amber
  (#FFFBEB/#FDE9B8). Şiddet farkı renk tonuyla, kırmızıyla değil.
- Sınıf chip'leri gerçek `<button>` değil `<span cursor:pointer>` — portta buton + `aria-pressed`.

### Veri bağlama — ⚠ uç eksik
- **openapi'de öğretmen uçları YOK.** Öneri: `GET /teacher/classes` · `GET /teacher/class/{id}/summary`
  (KPI + konu hâkimiyeti) · `GET /teacher/class/{id}/students` (tablo + dikkat listesi — dikkat
  kuralları SUNUCUDA: girişsiz gün ≥5, net düşüşü ≤−3, teslimsiz ödev ≥2).
- Sınıf arkadaşı verileri prototipte authored — üretimde gerçek roster.
- Üç durum: Skeleton · ErrorState · sınıf yoksa "İlk sınıfını kur" boş durumu (kopya onaya).

### DoD notları
- Tablo gerçek `<table>` ya da `role="table"`; başlıklar `<th scope="col">`.
- 390px: `.rstud` 3 sütuna düşer (son aktivite gizli — prototip davranışı).

---

## A2 · Ekran: Öğrenci Özeti — öğretmen görünümü (`KIRO2 Ogretmen Ogrenci Ozet.dc.html`)

**Tema:** paper. **Layout:** SideNav öğretmen (`active="students"`) + içerik (max 1220px).
**Rota:** `/ogretmen/ogrenci/:id` — SALT-OKUR (tek aksiyon: "Bu öğrenciye ödev ata" → Ödev Atama).

### Bloklar — BİREBİR
- Topbar: "← Panel" geri linki · "Öğrenci özeti" · sınıf chip'i · sağda "Salt-okur görünüm" pili.
- Kimlik bandı: avatar + ad + sınıf + son aktivite + CTA "Bu öğrenciye ödev ata".
- Durum kartı (tek): risk varsa AMBER (#FBF0DE/#F2D9AC, metin #9A5D0D) — alt satırı BİREBİR:
  "Bu sinyal yalnız size görünür — öğrenciye bayrak gösterilmez. Nazik bir başlangıç: küçük,
  kişiye özel bir set atamak." · risk yoksa yeşil sakin kart ("Ritmi sağlıklı — …").
- KPI ×4: Son deneme TYT net (+trend) · Genel hâkimiyet % · Çalışma serisi (gün) · Ödev durumu
  (tamam/toplam + "n bekliyor" amber — "eksik" YOK).
- Sol: Ders hâkimiyeti (AÇIK palet; alt not: "tekil cevaplar bu görünüme inmez") · "Desteğe hazır
  konular" amber chip'leri (motor önerisi; %'li) · Atanan ödevler (StatusChip: Tamam yeşil /
  Bekliyor amber / Açık nötr + ilerleme n/adet) · Son deneme (TYT/AYT etiketleri Sınav Sonuç
  standardı #EEF3F8/#5A6B82 · #FBF0DE/#9A5D0D; dipnot: "Net, yalnız yön göstergesidir — sınıf içi
  sıralama hiçbir yüzeyde yayınlanmaz.").
- Sağ ray: Haftalık aktivite (7 çubuk dk; pasif #FFD3C4, aktif accent — Veli Paneli düzeltmesiyle
  aynı dil) · **Öğrenci gizliliği kutusu** (kanonu öğreten yüzey — asla kaldırma): sohbet+duygu
  verisi inmez · tekil cevap görünmez, yalnız konu-düzeyi · risk sinyali yalnız yetişkine.

### Veri bağlama
- `GET /teacher/student/{id}/summary` (openapi'ye eklendi) — risk kuralları ve hâkimiyet SUNUCUDA;
  sohbet/mood/tekil cevap bu uca ASLA dahil edilmez.
- Prototip tweaks: `ogrenci` (saglikli/riskli) tüm durumları gezer; `?ogrenci=riskli` URL'den de çalışır.
- Üç durum: Skeleton · ErrorState · ödev listesi boşsa satırlar yerine sakin boş satır (kopya onaya).

### DoD notları
- Salt-okur: sayfada form/veri-yazan etkileşim YOK; tek CTA Ödev Atama'ya gider (öğrenci ön-seçili).
- 760px: `.rtwo` tek sütun, KPI 2×2; 440px KPI tek sütun.

---

## B · Ekran: Veli Paneli (`KIRO2 Veli Paneli.dc.html`)

**Tema:** paper. **Layout:** SideNav veli preset'i + içerik (max 1240px). **Rota:** `/veli`
(rol=veli varsayılan giriş). Çoklu çocuk: topbar'da çocuk chip'leri (Hüseyin/Elif).

### Bloklar — BİREBİR
- Çocuk özet bandı: avatar + ad/sınıf/hedef + bu hafta çalışma (sa) + son deneme neti + seri pili.
- KPI ×4: Çözülen soru 312 (+48) · Çözülen deneme 3 (+1) · Plan uyumu %86 · Net değişimi +8,5 (bu ay).
- **Haftalık Aktivite:** 7 çubuk (dk) + hafta toplamı + trend.
- **Ders Bazında İlerleme:** açık palet ders barları.
- **Son Sınavlar:** satırlar → Sınav Sonuç (veli salt-okur görünümü).
- **Uyarılar & Öne Çıkanlar:** yeşil (ivme) · amber (kimya az çalışıldı) · coral (rozet) —
  ton dengesi bilinçli: 1 kutlama + 1 nazik uyarı + 1 sevinç; ASLA yığılmış kırmızı liste olmaz.
- **Premium ROI bölümü** (veli satın-alma yüzeyi): "Yöntem işe yarıyor" kanıt bloğu (+8,5 net ·
  %86 uyum · seri — çocuğun GERÇEK verisi) + koyu Premium kartı (4 madde + ₺124/ay + −%38 +
  "7 gün ücretsiz deneyin" → Abonelik?rol=veli + "sessiz ücret yok").

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- Haftalık aktivite pasif çubuk rengi **#C9D2FB (menekşe-mavi, indigo ailesine kayar)** →
  şafak soluk tonu #FFD3C4 (FSRS 7-gün grafiğiyle aynı dil; aktif gün accent kalır).
- TYT/AYT etiket renkleri Sınav Sonuç'takinden FARKLI (#EFF6FF/#3B82F6 · #ECFDF5/#1FB683) —
  port: TEK stil, Sınav Sonuç standardı (TYT #EEF3F8/#5A6B82 · AYT #FBF0DE/#9A5D0D).
- ₺124 ve −%38 sabitleri → `GET /plans` (Sprint 10 kararıyla aynı).

### Veri bağlama — ⚠ uç + akış eksik
- Öneri: `GET /parent/children` · `GET /parent/child/{id}/summary` (KPI + aktivite + dersler +
  sınavlar + uyarılar — uyarı üretimi SUNUCUDA, nazik şablonlarla).
- **AÇIK NOKTA — hesap bağlama:** veli↔çocuk bağlantı akışı (davet kodu? e-posta onayı?) prototipte
  YOK; KVKK gereği açık rıza akışı tasarlanmalı (Faz 4 öncesi ürün kararı + mini tasarım işi).
- Veli hesabında öğrenci gizliliği: sohbet içerikleri ve mood verisi veliye GÖSTERİLMEZ (kanon;
  yalnız çalışma metrikleri).

### DoD notları
- Çocuk chip'leri `role="tablist"`; bildirim zili Bildirim Merkezi'nin veli sürümüne (Faz 4'te ayrı
  bildirim seti) bağlanır.
- 390px: özet bandı sarar; ROI bölümü `.rroi` tek sütun.

---

## C · Ekran: Ödev Atama (`KIRO2 Odev Atama.dc.html`)

**Tema:** paper. **Layout:** SideNav öğretmen (`active="assignments"`) + form (1.5fr) + sticky
özet (1fr). **Rota:** `/ogretmen/odev/yeni`.

### 3 adım — BİREBİR
1. **Konu:** radyo kartları, zayıf konular önde ("Sınıfın son deneme verisine göre zayıf konular
   önde.") + kademe etiketi (Zayıf amber · Gelişiyor mavi · Sağlam yeşil) + "Sınıf hâkimiyeti ~%{n} ·
   soru havuzunda hazır".
2. **Kapsam & teslim:** soru sayısı segmenti (10/15/20) · teslim segmenti (Yarın/Cuma/Pazar) ·
   **Kişiye özel zorluk toggle'ı (varsayılan AÇIK — ürün farklılaştırıcısı):** "Her öğrenci aynı
   konudan kendi θ seviyesine göre soru alır — kimse boğulmaz, kimse sıkılmaz. Sınıf ortalaması
   öğrencilere gösterilmez." BİREBİR.
3. **Öğrenciler:** tümü seçili başlar; checkbox satırları (risk notu amber, hâkimiyet bar) +
   "Tümünü seç/bırak".
- **Özet** (sticky): konu · soru+~dk · teslim 23:59 · kişi · zorluk + motor notu ("Motor, her
  öğrencinin θ kestirimine göre {n} soruluk ayrı bir set kurar; zayıf atomlara ağırlık verir.").
- **Kaygı-duyarlı varsayılanlar kutusu** — ÜÇ MADDE BİREBİR (sıralama yayınlanmaz · "eksik" değil
  "bekliyor" · risk amber, öğrenciye bayrak yok). Bu kutu öğretmene kanonu ÖĞRETIR — asla kaldırma.
- Başarı: "Ödev atandı — öğrencilere sakin bir bildirim gitti." (`role="status"` mevcut — koru).

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- Varsayılanlar kutusu + "Atandı ✓" buton etiketindeki "✓" METİN glyph'leri → bespoke SVG tik.
- Öğrenci hâkimiyet barı kademe renkleri DUSK paletinde (#7FB0FF/#FF9E7D/#FCD34D) — açık zemin;
  port: MasteryBadge'in AÇIK kademe renkleri (Sprint 2 standardı) — iki palet karışmaz.

### Port kararları
- Teslim hızlı seçimleri kalır + **özel tarih alanı eklenir** (Yarın/Cuma/Pazar her haftaya uymaz;
  `<input type="date">` + 23:59 sabit saat; öneri).
- "Taslak kaydet" prototipte işlevsiz → MVP: yerel taslak (localStorage, sınıf+form anahtarı);
  sunucu taslağı Faz 4 sonrası.
- Kişiye özel set kurulumu SUNUCUDA (`POST /teacher/assignments {konuId, adet, teslimTarihi,
  kisisel, ogrenciIds}` → motor set'i kurar); istemci yalnız formu gönderir.

### Veri bağlama
- Konu listesi: `GET /teacher/class/{id}/topics` (zayıflık sırasıyla) · roster: `/teacher/class/
  {id}/students`. Ödev ataması öğrenci tarafında Ödevlerim'e (Sprint 1) ve sakin bildirime düşer.
- Üç durum: Skeleton · ErrorState (form verisi kaybolmaz — yerel taslak) · roster boşsa sınıf kurulumuna yönlendirme.

### DoD notları
- Radyo/checkbox satırları gerçek semantik (`role="radio"`/`checkbox` + `aria-checked`); klavye ok tuşları.
- 1120px altı: `.rtwo` tek sütun, özet alta iner (sticky kalkar).
- Soru sayısı/teslim segmentleri ≥44px (40px — porta 44'e çıkar; kanon hit-alan).

---

---

## A3 · Ekran: Sınıf Kurulumu — "İlk sınıfını kur" (`KIRO2 Sinif Kurulum.dc.html`, 2026-07-22)

**Tema:** paper (Hesap Kurtarma/Veli Bağlama aile dili — radial şafak yıkaması + tek kart 560px). **Rota:** `/ogretmen/sinif/yeni`. **Karar:** MVP'ye girer (KARARLAR 2026-07-21) — kod-temelli minimal kurulum; öğrenci listesi/CSV içe aktarma YOK.
- **Durum makinesi:** bilgi → davet → hazir (`baslangicAdim` tweak; adım eyebrow'u sağ üstte `aria-live`).
- **Adım 1:** sınıf adı input + Düzey segmenti (11/12/Mezun) + Alan segmenti (Sayısal/EA/Sözel). ⚠ Prototipte segment dolgusu `background:#fff` + `box-shadow:inset 0 0 0 999px <zemin>` deseniyle (runtime gotcha çözümü) — üretimde normal state'li stil kullanılır, desen TAŞINMAZ.
- **Adım 2:** 6 haneli süresiz katılım kodu (38px tabular, kesikli kart) + "Kodu kopyala" (kopyalandı geri bildirimi) + "Davet linkini paylaş" + kaygı-duyarlı sınıf varsayılanları kartı (sıralama yayınlanmaz · "bekliyor" dili · risk bayrağı öğrenciye inmez) — Ödev Atama'daki kartla aynı dil.
- **Adım 3:** yeşil onay; boş-liste kopyası "boş liste bir eksik değil, başlangıçtır"; CTA "Panele git" + ikincil "İlk ödevi hazırla".
- **Veri:** `POST /teacher/classes {ad, duzey, alan}` → `{id, katilimKodu}`; öğrenci ucu `POST /me/class/join {kod}` (Ayarlar → Sınıfa katıl); kod yenileme sunucuda.
- **Giriş noktaları:** Öğretmen Paneli topbar kesikli "+" (aria-label "Yeni sınıf kur"); boş öğretmen hesabında panel boş-durumu bu akışa yönlendirir (üretim kuralı).
- **DoD:** üç adım klavyeyle gezilir; segmentler radiogroup + `aria-checked`; kopyalama başarısı görsel + kod alanı `aria-live`; alt gizlilik kilit satırı her adımda görünür.

## Sprint 11 açık noktaları
1. ~~Öğretmenin öğrenci-özet sayfası~~ — TASARLANDI 2026-07-05 (`KIRO2 Ogretmen Ogrenci Ozet.dc.html`, bölüm A2).
2. Veli↔çocuk hesap bağlama + KVKK rıza akışı — ürün kararı + tasarım (Faz 4 öncesi).
3. Öğretmen/veli uçları openapi'ye eklenecek (`/teacher/*` · `/parent/*`).
4. Öğretmen boş durumu ("İlk sınıfını kur") + sınıf oluşturma akışı MVP'de var mı?
5. Veli bildirim seti (zil) — öğrenci bildirimlerinden ayrı şablonlar.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 9 bitti** → PORT_DURUM'da Grup 9'a tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Öğretmen tablosu `th scope` + satır linkinin erişilebilir adı = öğrenci adı; risk çipi renk+metin.
- Öğrenci Özeti: "Salt-okur görünüm" pili `role="status"`; haftalık aktivite çubukları değer metniyle.
- Veli Bağlama: kod inputu tek `aria-label`; adım değişiminde başlık odağı; "Onay bekleniyor" `role="status"`.
- Ödev Atama: roster checkbox'ları `label` ile; özet çubuğu seçim değiştikçe `aria-live="polite"`; θ switch'i `role="switch"`.
