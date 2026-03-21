# Brainstorm: Learning Path Iyilestirme
Tarih: 2026-03-21 | Domain: feature | Perspektifler: Ogrenci Ahmet, Sistem Mimari, Urun Stratejisti, Egitim Bilimci

## TL;DR
Learning path'in en kritik sorunu **AI-uretilen yolun DB'ye yazilmamasi** — sayfa yenilenince kayboluyor. Mobil UX kullanilamaz (harita gorunumu telefondan eziyet), ve `assess_knowledge` endpoint'inde **auth eksik IDOR acigi** var. ZPD/IRT/FSRS pipeline'i mevcut ama structured_learning_path template engine'den tamamen kopuk.

## Top 5 Aksiyon

| # | Aksiyon | Etki | Zorluk | Kaynak |
|---|---------|------|--------|--------|
| 1 | **create_path sonucunu LearningPath tablosuna persist et** — refresh ile path kaybolmasi critik bug | 5/5 | Orta | Mimar |
| 2 | **assess_knowledge endpoint'ine auth + IDOR fix** — write guvenlik acigi | 5/5 | Kolay | Mimar |
| 3 | **Mobilde varsayilan linear/list gorunum** — tree/harita telefondan kullanilamaz | 5/5 | Kolay | Ahmet |
| 4 | **ZPD-IRT pipeline'ini structured_learning_path'e bagla** — statik difficulty_curve yerine adaptif | 5/5 | Orta | Egitim Bilimci + Mimar |
| 5 | **Quiz basarisizliginda somut aksiyon butonlari** — "Videoyu izle", "Kolay konuya don" | 4/5 | Kolay | Ahmet + Egitim Bilimci |

## Konsensus (2+ perspektif)

1. **ZPD/IRT entegrasyonu kopuk** — Mimar: create_path DB'ye yazmaz; Egitim Bilimci: structured_learning_path BKT->IRT->FSRS pipeline'dan bagimsiz calisiyor. Ayni sorun: template engine statik, adaptif algoritmalardan baglantisiz.
2. **VARK anketini zorunlu yapmayin** — Ahmet: "nedir bu anket, soru cozmek istiyorum"; Egitim Bilimci: "VARK ampirik gecerliligi zayif (Pashler et al., 2008)". Tercih bilgisi olarak kullanilmali, karar mekanizmasinin merkezi olmamali.
3. **Metacognitive geri bildirim eksik** — Egitim Bilimci: Bloom taksonomisi tek yonlu, hangi katmanda takildigina dair bildirim yok; Ahmet: quiz basarisiz olunca ne yapacagini bilmiyor.
4. **Mastery-based skip** — Stratejist: guclu konulari otomatik atlama; Egitim Bilimci: ZPD adaptive difficulty ayni fikri destekliyor.

## Catismalar

| Konu | Taraf A | Taraf B | Onerilen Karar |
|------|---------|---------|----------------|
| Cache stratejisi | Mimar: dual cache'i birlestir (singleton tutarsizligi) | Ahmet: stale-while-revalidate (UX icin eski veriyi goster) | Her ikisi de yapilmali — tek cache instance + SWR pattern |
| Sosyal ozellikler | Stratejist: DuelMode/League 500 DAU'ya kadar gizli tutun | (catisma yok, zamanlama karari) | MVP'de gizle, metrikleri takip et |
| Zorluk atlama | Stratejist: fast-track ile zayif konulara odaklan | Egitim Bilimci: Yerkes-Dodson overfitting riski, az veriyle theta sallanimi | Minimum 10 soru cevabi olmadan skip yapma, threshold kalibre et |

## Perspektif Detaylari

### Ogrenci Ahmet (11. sinif, Ankara, telefondan calisiyor)

**1. Mobilde harita KULLANILAMAZ — linear list gorunumunu varsayilan yap**
Visualizer 600px minHeight + drag/zoom/pan mekanigi var. Telefondan parmakla surukleme eziyet. `viewMode` varsayilani mobilde otomatik "linear" olmali.
- Etki: 5/5 | Zorluk: Kolay | Risk: Linear'da cok fazla konu varsa lazy-load gerekir

**2. Ders degistirince her seferinde full loading spinner**
`changeSubject` her degisimde `setLoading(true)`, cache varken bile. Stale-while-revalidate pattern kullanilmali.
- Etki: 4/5 | Zorluk: Orta | Risk: Stale state gosterimi (completed node "current" gorunmesi)

**3. Quiz basarisiz olunca sadece hata mesaji — yonlendirme yok**
"Bu konu icin soru bulunamadi" yaziyor. "Videoyu izle", "Daha kolay konuya don" gibi aksiyon butonlari gostermeli.
- Etki: 4/5 | Zorluk: Kolay | Risk: Yanlis yonlendirme ogrenciyi yildirabilir

**Kor nokta:** Visualizer'daki "Basla" butonu onClick handler'i YOK — tiklaninca hicbir sey olmuyor. NodeDetailsPanel'deki "Quiz Baslat" calisiyor ama dialog icindeki "Basla" dekoratif.

**Uyari:** VARK anketini ilk giriste ZORUNLU gostermeyin. 11. sinif ogrencisi sayfayi kapatir.

---

### Sistem Mimari (100K esanli kullanici, FastAPI + PostgreSQL + Redis)

**1. update_completion N+1 Query Eliminasyonu**
Her `node_id` icin 2 SELECT + 1 UPDATE — 20 topic icin 60 sorgu. Bulk upsert ile 2 sorguya dusur.
- Etki: 5/5 | Zorluk: Kolay | Risk: TopicProgress'te unique constraint eksik, migration gerekir

**2. Cache Instance Tutarsizligi**
`learning_path_v2.py` kendi `_get_cache()` fonksiyonunu kullaniyor, `LearningPathCache` singleton ile hicbir baglantisi yok. Iki ayri Redis connection, iki ayri L1 cache.
- Etki: 4/5 | Zorluk: Orta | Risk: TTL farklari (300s vs 900s) birlestirilirken regression

**3. create_path Sonucunu DB'ye Persist Et**
AI path uretir ama LearningPath tablosuna hicbir sey yazmaz — sadece JSON doner. Kullanici sayfa yenileyince path kaybolur.
- Etki: 5/5 | Zorluk: Orta | Risk: modules JSON kolonuna buyuk payload, partitioning gerekir

**Kor nokta:** `assess_knowledge` endpoint'inde auth YOK — herhangi bir student_id ile baska ogrencinin bilgi seviyesini sorgulayip guncelleyebilir. IDOR + write guvenlik acigi.

**Uyari:** `structured_learning_path.py`'deki hardcoded template'leri 100K olcek icin kullanmayin. Tum rule'lar hafizada, DB destegi yok.

---

### Urun Stratejisti

**1. Haftalik Ilerleme Raporu — Veli/Ogrenci Paylasimi**
Veli WhatsApp/PDF raporu (haftalik mastery, zayif konular, onerilen calisma suresi). Rakipler (Doping Hafiza, Testinium) bunu sunmuyor.
- Etki: 5/5 | Zorluk: Orta | Risk: Veli baskisi ogrenciyi yildirabilir

**2. Anonim Kohorta Benchmark — Akran Karsilastirma**
Konu bazli performansi ayni hedef siralamasindaki anonim kohort ile karsilastirma. Premium-only.
- Etki: 4/5 | Zorluk: Kolay | Risk: Alt performansta motivasyon dusurme

**3. Adaptif Konu Atlama — Mastery-Based Fast Track**
Guclu konulari otomatik skip edip zayif konulara odaklanma. TUBITAK "kisiye ozel ogrenme" kriterine katkisi var.
- Etki: 4/5 | Zorluk: Orta | Risk: Yanlis skip — kolay gorunden guclu sanip sinav surprizi

**Kor nokta:** Sistem calisma suresi verisi toplamIyor. `available_time` var ama gercek oturum suresi olculmuyor. Verimlilik metrigi olusturulamaz.

**Uyari:** MVP'de DuelMode ve LeaguePanel'i ACMAYIN. Yeterli kullanici tabanI olmadan sosyal ozellikler bos gorunur.

---

### Egitim Bilimci (SR, ZPD, IRT, Bloom, Yerkes-Dodson)

**1. ZPD Adaptif Zorluk Ayari Eksik**
`difficulty_curve` sabit. Gercek ZPD, ogrencinin anlik performansina gore zorluk bantini daraltmali. IRT theta degeri her quiz sonrasi guncellenmeli. BKT->IRT->FSRS pipeline var ama structured_learning_path bundan bagimsiz.
- Etki: 5/5 | Zorluk: Orta | Risk: Over-fitting — az veriyle theta sallanimi (Yerkes-Dodson)

**2. Bloom Taksonomisi Tek Yonlu**
6 Bloom katmani tanimli ama hangi katmanda takildigina dair metacognitive geri bildirim yok. "Uygulama"da %40 basari varken "Analiz"e gecmek pedagojik olarak yanlis.
- Etki: 4/5 | Zorluk: Kolay | Risk: Ilerleme hissi kaybi

**3. Sinav Kaygisi Yonetimi Tamamen Yok**
`FINAL_ASSESSMENT` + `required_score` var ama basarisizlikta desensitizasyon stratejisi yok. Yerkes-Dodson'a gore yuksek stakes motivasyon dusurur.
- Etki: 4/5 | Zorluk: Kolay | Risk: "Kolaylastirma" algisi

**Kor nokta:** `LearningPathAgent` `weak_topics` cikariyor ama NEDEN zayif oldugunu analiz etmiyor. Bilgi eksikligi mi, kavram yanilgisi mi, dikkat hatasi mi? Hata siniflandirmasi olmadan kisisellestirilmis yol yuzeysel kalir.

**Uyari:** VARK modelini karar mekanizmasinin merkezi yapMAyin. Ampirik gecerliligi zayif (Pashler et al., 2008). Tercih bilgisi olarak kullanilmali.

## Kor Noktalar & Uyarilar (Birlesik)

### Kor Noktalar
1. **Broken "Basla" butonu** — Visualizer'daki onClick handler yok, dekoratif (Ahmet)
2. **assess_knowledge IDOR** — auth eksik, write guvenlik acigi (Mimar)
3. **Calisma suresi olculmuyor** — verimlilik metrikleri olusturulamaz (Stratejist)
4. **Hata siniflandirmasi yok** — neden zayif bilgi analize edilmiyor (Egitim Bilimci)
5. **Path DB'ye yazilmiyor** — refresh ile kaybolur (Mimar)
6. **Dual cache tutarsizligi** — iki ayri Redis connection, invalidation kopuk (Mimar)

### Uyarilar
1. VARK anketini zorunlu yapMAyin (Ahmet + Egitim Bilimci)
2. DuelMode/LeaguePanel'i 500 DAU oncesi acMAyin (Stratejist)
3. Hardcoded template engine'i 100K olcekte kullanMAyin (Mimar)
4. Az veriyle aggressive zorluk atlama yapMAyin — min 10 soru (Egitim Bilimci)
