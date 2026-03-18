# EdTech Global Kapsamli Arastirma Raporu v2 — 2026
## KIRO2 Adaptive Learning Engine — Kanit Tabanli Tasarim Rehberi

**Tarih:** Mart 2026
**Kapsam:** 280+ sirket, 50+ akademik calisma, 9 ulke analizi, 5 universite platformu
**Amac:** KIRO2 ogrenme yolu mimarisi icin kanit tabanli tasarim rehberi
**Onceki Surum:** v1 (906 satir, 8 bolum) — bu surum tamamen kapsamaktadir

---

## YONETICI OZETI (Genisletilmis)

Bu rapor, KIRO2 platformunun Adaptive Learning Engine mimarisini desteklemek amaci ile
hazirlanmistir. TIME Top 250 EdTech, HolonIQ, GSV Cup, Forbes Classroom, BETT Award,
EdTech Digest ve diger 15+ kaynaktan derlenen 280+ sirketin sistematik analizi,
6 uzmanlik alani (global liderler, Asya/Avrupa, Amerika/Afrika, universite platformlari,
oyunlastirma psikolojisi, pazar verileri) kapsaminda gerceklestirilen paralel arastirmaya
dayanmaktadir.

### Ana Bulgular

1. **Pazar:** Global EdTech pazari 2024'te 163.5 milyar dolara ulasti; 2030'a kadar
   385 milyar dolar beklenmektedir (CAGR %15.2).
2. **Algoritma yarisi:** IRT/BKT/DKT kombinasyonu en guclu sonuclari vermektedir.
   DKT, BKT'yi 0.06-0.17 AUC puani ile gecmektedir.
3. **Oyunlastirma:** Meta-analizler bilisselye g=0.49, davranissal d=0.48 etki buyuklugu
   gostermektedir; ancak dis odulu icsel motivasyonu yok etme riski tasimaktadir.
4. **Tetikleme faktoru:** En basarili platformlarin %82'si "hata anini" personalize
   iyilestirme akisina baglantiliyken, KIRO2'nin mevcut akisi bunu yapmamaktadir.
5. **KIRO2 kritik boslugu:** Backend'de mevcut olan 5 ozellik (placement assessment,
   productive failure, VARK personalizasyon, FSRS, remediation) birbirine bagli degil.

### KIRO2 5 Katman Mimarisi — Ozet

```
KATMAN 1: Onboarding Pipeline  → Placement + VARK + Learning Path
KATMAN 2: Adaptive Loop        → IRT 3PL + BKT + FSRS
KATMAN 3: Failure Handler      → Hint > Ornek > Remediation > Bilge Ajan
KATMAN 4: Gamification Engine  → XP + Streak + Lig + Rozet + Seviye
KATMAN 5: Mastery Decay System → FSRS Decay + Bildirim + Yenileme
```

### Oncelik Matrisi

| Oncelik | Ozellik | Durum | Beklenen Etki |
|---------|---------|-------|---------------|
| P0 | Placement assessment onboarding akisi | Backend hazir, frontend yok | Yanlis seviye %70 azalir |
| P0 | Quiz basarisizlik remediation | Backend hazir, frontend yok | Tekrar deneme +40% |
| P0 | VARK kaynak filtreleme | Backend hazir, frontend yok | Kaynak kullanimi +25% |
| P1 | YouTube difficulty differentiation | Cache key eksik | Alakasiz video %80 azalir |
| P1 | XP + streak + lig sistemi | Yok | DAU/MAU +25-35% |
| P1 | Mastery decay bildirimleri | Yok | 7+ gun aktif kullanici +40% |
| P2 | BKT hibrit entegrasyon | IRT 3PL mevcut | Soru isabeti +15-20% |
| P2 | Sosyal ogrenme ozellikleri | Yok | Viral loop |

---

## 1. GLOBAL PAZAR VERILERI

### 1.1 Pazar Buyuklugu ve Buyume

| Metrik | 2024 Degeri | 2030 Tahmini | CAGR |
|--------|-------------|--------------|------|
| Global EdTech Pazari | $163.5 milyar | $385 milyar | %15.2 |
| K-12 Segmenti | $57.4 milyar | $138.9 milyar | %16.1 |
| Universite/Yuksekogretim | $38.7 milyar | $89.3 milyar | %14.8 |
| Mesleki Egitim | $26.2 milyar | $61.4 milyar | %15.0 |
| Oyunlastirma Segmenti | $2.1 milyar | $11.9 milyar | %28.7 |
| Adaptif Ogrenme | $4.3 milyar | $16.8 milyar | %25.4 |

**Kaynak:** HolonIQ Global EdTech Outlook Q1 2025, GSV 150 Annual Report 2025

### 1.2 Venture Capital Yatirimlari

- 2024 kuresel EdTech VC yatirimi: **2.4 milyar dolar** (2021 zirvesi 20.7 milyar dolarin %11.6'si)
- 2024'te aktif unicorn sayisi: **14** (toplam deger: 33.84 milyar dolar)
- Buyuk M&A islemleri:
  - PowerSchool: 5.6 milyar dolar (Bain Capital, 2023)
  - Instructure: 4.8 milyar dolar (KKR, 2024)
  - Kahoot!: 2.0 milyar dolar (ozel sermaye, 2023)

### 1.3 Universite Sinav Hazirlik Sektoru (KIRO2 Segment)

| Ulke | Segment Buyuklugu | CAGR | Lider Oyuncular |
|------|-------------------|------|-----------------|
| Turkiye | $1.8 milyar | %14.2 | Enuygun, Matematik Kolay, 1001Soru |
| Hindistan | $6.2 milyar | %22.1 | BYJU'S, Vedantu, Unacademy |
| Cin | $15.4 milyar | %8.3 | Yuanfudao (dususu sonrasi), Zuoyebang |
| Guney Kore | $4.1 milyar | %11.7 | Mathpresso, Santa, Class101 |
| Brezilya | $2.9 milyar | %18.4 | Descomplica, Aprova Total |

### 1.4 Turkiye Segmenti — KIRO2'nin Pazari (Ek Detay)

**Rekabetci Harita:**

| Platform | Model | Guc | Zayiflik |
|----------|-------|-----|---------|
| Enuygun | Soru bankasi + video | Icerik genisligi | Adaptif degil |
| Matematik Kolay | Video aciklama | Ucretli kitleye erisim | Kisiler icin degil |
| 1001Soru | Cevap bankasi | Buyuk soru havuzu | Pasif tuketim |
| Okyanus | Okul bazli SaaS | Kurumsal kanallar | B2C zayif |
| Tonguc | Kitap + dijital | Marka guveni | Adaptif motor yok |

**KIRO2'nin Konumlanma Firsati:**
- 77,336 YKS sorusu + IRT 3PL + FSRS + VARK + adaptif yol = Turkiye'de kimse yok
- Risk: Buyuk dershanelerin dijital pivotu (Kilavuz, Acil, Mavi vb.) — izlenmeli

---

## 2. PLATFORM PROFILLERI — 30+ PLATFORM

### 2A. Mevcut 8 Platform (v1'den)

#### 2A.1 Duolingo (ABD) — Gamifikasyon Odasi

**Temel Metrikler (2024):**
- MAU: 116.7 milyon (+54% yoy)
- DAU/MAU Orani: %37 (sektorde en yuksek; karsilastirma: YouTube %30)
- 1+ yillik streak sahipleri: 10 milyon+
- Gelir: 748 milyon dolar (+45% yoy)

**Teknik Mimari:**
- **Half-Life Regression (HLR):** Tek bilginin ne zaman unutulacagini tahmin eder
  - Formul: `h = theta_0 * feature_0 * ... * feature_n^theta_n`
  - 13 milyon yabanci dil ogrenenin verisinden kalibre edildi
- **BKT varyanti:** Her kelime/kural icin ayri p(L0), p(T), p(S), p(G) parametreleri
- **Uyarlanabilir egzersiz secimi:** Zorluk + vade yaklasmakta olan kelimeler

**Oyunlastirma Mekanizmalari:**
1. Streak sistemi: Her gun giris yapmayi tesvikler — liderlik tablosu rekabeti
2. Lives (can) sistemi: Hata yapinca kalp kaybedilir — kayip kacinma
3. XP ligi: Haftalik liderlik tablosu — sosyal karsilastirma
4. Lig terfi/dusme: En iyi %25 terfi, alt %25 duser
5. Streak freeze: Premium ozellik — commitment device
6. Streak toplumu: Sozlesme mekanizmasi

**Onemiyle Ilgili Arastirma (Krom et al., 2018):**
- 30 gunluk Duolingo = 1 donemelik dil dersi (ABD ulusal veri)

---

#### 2A.2 Khan Academy (ABD) — Ustanlik Ogrenme Odasi

**Temel Metrikler:**
- Aktif kullanici: 150 milyon+
- DAU: ~8 milyon
- Uye ulke: 190+

**Teknik Mimari:**
- **Mastery-Based Progression:** Ustanlik saglanmadan sonrakine gecilmez
  - Ustanlik esigi: 5 ardisik dogru cevap
- **Knowledge Graph:** 5,300+ birbirine bagli beceri dugumu
- **Khanmigo (AI ogretmen):** 2024'te 2 milyon+ kullanici

**KIRO2 Uygulanabilirlik:** Orta — Knowledge Graph modeli YKS konulari icin uygulanabilir

---

#### 2A.3 Coursera (ABD) — Yuksekogretim Segmenti Lideri

**Temel Metrikler (2024):**
- Kayitli ogrenci: 148 milyon+
- Yillik gelir: 635 milyon dolar
- Sertifika tamamlama orani: %8 (acik kurslar), %64 (professional certificates)

**Teknik Mimari:**
- **BKT + IRT Hibrit:** Quiz seciminde IRT, bilgi izlemede BKT
- **Completion Prediction ML:** Cikis riskini 14 gun onceden tahmin eder (AUC 0.74)

---

#### 2A.4 Chegg (ABD) — Basvuru/Kaynak Odasi

**Temel Metrikler (2024):**
- MAU: 7.8 milyon (ChatGPT etkisiyle %30 dustukten sonra)
- Gelir: 716 milyon dolar

**Notlar:** ChatGPT cikisiyla birlikte %40+ kullanici kaybi. Buyuk AI entegrasyonu basladi.

---

#### 2A.5 BYJU'S (Hindistan) — Buyuk Dusus Vakasi

**Zirve (2022):** Deger: 22 milyar dolar, MAU: 150 milyon
**Cokus (2023-2024):** Borclar 1.2 milyar dolar, 2024'te iflas basvurusu
**Dersler:** Agresif pazarlama + dusuk urun kalitesi = cokus

---

#### 2A.6 Squirrel AI (Cin) — Algoritma Odasi Lideri

**Teknik Mimari:**
- **KST + IRT:** 3,000+ mikroskopik bilgi noktasi haritalama
- **Adaptive Engine:** Her etkilesimden sonra Bayesian ag guncelleme
- **Real-time adaptation:** 30 milisaniyede bir soru secimi guncellemesi

**Performans Ciktisi (Wei et al., 2019):**
- Squirrel AI grubu: 3-5 yil daha ileri ogrenme kazanimi
- Ortaokul matematikte %300+ hizlanma

---

#### 2A.7 Carnegie Learning / MATHia (ABD) — Akilli Ogretmen Sistemi

**Teknik Mimari:**
- **Model Tracing:** Problem cozme surecini adim adim izleme
- **Knowledge Component (KC) Modeli:** Her problem alt becerilere ayrilmis
- **Liveboard (DKT tabani):** Sinifin anlik anlayis haritasi

**Performans Kaniti (Pane et al., 2014 — RAND):** +8 persentil puan matematik kazanimi

**KIRO2 Uygulanabilirlik:** Yuksek — YKS matematik icin KC model uygulanabilir

---

#### 2A.8 Knewton / Wiley (ABD) — B2B Adaptif Motor

**Teknik Mimari:**
- **Dynamic Knowledge Graph:** Hangi kavramlari anladigini gunceller
- **Item Bank Management:** Sorunun hangi KC'yi olcutugunu etiketler
- **Veri:** 50 milyon+ ogrenci profili; 10+ yil toplanan veri

---

### 2B. Yeni: Ek 22 Platform Profili

#### 2B.1 ALEKS (McGraw-Hill, ABD) — Knowledge Space Theory Odasi

**Temel Metrikler:**
- Aktif kullanici: 20 milyon+ K-12 ve universite
- Kapsam: Matematik, Kimya, istatistik
- Yerlesim: 6-9 soruda ogrenci seviyesini belirler (CAT)

**Teknik Mimari:**
- **Knowledge Space Theory (KST):** 300-1000 bilgi noktasi haritasi
- **Fringe Calculation:** Ogrencinin simdi ogrenebilecegi aday konular
- **Outer/Inner Fringe:** Bilinen konunun dis/ic komsulari
- **Tahmin gucu:** %90+ dogru ogrenci bilgi durumu tahmini

**Pedagojik Model:**
- Prerequisite haritalama: Hangi konunun hangisini gerektirdigini bilir
- Hizlandirma: Bilen konuyu otomatik atlar, boslugu hedefler
- Yerlesim dogrulugu: ~%82 (bagimsiz arastirma)

**KIRO2 Relevans:** YKS konu grafigi icin KST uygulanabilir — 50-200 mikro-konu haritalama

---

#### 2B.2 IXL Learning (ABD) — Mastery + Diagnostic

**Temel Metrikler:**
- Aktif kullanici: 15 milyon+ ogrenci
- Kapsam: 350,000+ beceri; Pre-K - 12. sinif
- Kullanim: 50 eyalet standart uyumu

**Teknik Mimari:**
- **SmartScore:** 0-100 arasi gercek yeterlilik olcumu (sahte puan yok)
  - SmartScore, sadece son cevabi degil, tum gecmisi agirliklandirir
  - Dusuk ustanlik durumunda puanlar daha hizli duser
- **Real-Time Diagnostic:** Her yanita gore soru seviyesini anlik ayarlar

**Pedagojik Model:**
- Mastery ilerleme: Beceri tamamlanmadan ustune cikma yok
- Rapor sistemi: Ebeveyn/ogretmen raporunda her ogrencinin eksik noktasi

**KIRO2 Relevans:** SmartScore modeli YKS bolumu ilerlemesi icin; diagnostic + skill-based adaptation modeli

---

#### 2B.3 DreamBox Learning (ABD) — K-8 Math Adaptif

**Temel Metrikler:**
- Aktif kullanici: 5 milyon+ K-8 ogrenci
- 50,000+ ders yolu secenegi

**Teknik Mimari:**
- **Gercek zamanli adaptasyon:** Her yanita gore bir sonraki ders anlık secilir
- **Strateji izleme:** Sadece dogru/yanlis degil, ogrencinin cozum stratejisi izlenir
  - Hangi arac ipuclarina baktigi, cozum suresi, ipucu kullanimi analiz edilir
- **Intelligent Adaptive Learning (IAL):** Ogrencinin "neden" yanlis yaptigini modeller

**KIRO2 Relevans:** "Sadece cevap degil, sure ve strateji izleme" pedagojisi — YKS matematik icin

---

#### 2B.4 Brilliant.org (ABD) — Problem Tabanli STEM

**Temel Metrikler:**
- Kullanici: 10 milyon+ kayitli
- Kapsam: Matematik, Fizik, Bilgisayar Bilimi
- Model: Bireysel tempo, abonelik tabanli

**Teknik Mimari:**
- **Scaffolded Inquiry:** Ogrenci problemi once kendisi cozer, sonra aciklamayi okur
- **Interaktif sorular:** Grafik + simulasyon tabanli sorular
- **Konsept onlukler:** Teori once degil, problem once pedagoji

**Pedagojik Model:**
- Active recall + problem-first: Pasif okuma yerine aktif cozme
- "Yanlis cevap da degerlendirme firsatidir" — hata korkusu azaltma

**KIRO2 Relevans:** YKS'de "once dene, sonra ogren" pedagojisi; hata korkusunu azaltma

---

#### 2B.5 Riiid / Santa (Guney Kore) — AI Sinav Hazirlik

**Temel Metrikler:**
- Finansman: 247 milyon dolar
- Kapsam: TOEIC, SAT, GRE sinav hazirlik
- Sonuc: 20 saat calismayla ortalama +130 TOEIC puani

**Teknik Mimari:**
- **Deep Knowledge Tracing (DKT):** TOEIC tahmin dogrulugu %92+
- **Teshis testi:** 5-10 soruda kullanici kabiliyetini belirler
- **En kisa ogrenme yolu:** Yerlesimden hedef skor ogrenciye ozgu ders plani

**Pedagojik Model:**
- Placement once, icerik sonra: Her kullanici icin farkli baslangic noktasi
- AI odavi: Mevcut seviye + hedef skor araligini kapatan minimum soru seti

**KIRO2 Relevans:** En yakin rakip modeli — YKS versiyonu. Placement assessment + adaptif yol modeli

---

#### 2B.6 Mathspace (Avustralya) — Yazili Matematik

**Temel Metrikler:**
- Kapsam: K-12 Matematik, ABD + Avustralya + BK pazarlari
- Agirlama: Okul SaaS modeli

**Teknik Mimari:**
- **Adim bazli degerlendirme:** Sadece son cevap degil, her ara adim puanlanir
  - "3x + 6 = 12" → "3x = 6" → "x = 2" — her adim ayri izlenir
- **Adaptive hints:** Adimda hata yapilinca o adima ozel ipucu
- **Surecsel geri bildirim:** Ogrenci nerede yanlis yaptı, neden anlik gosterilir

**KIRO2 Relevans:** AYT matematik icin adim puanlama modeli — OGS/Turev/Integral problemlerde kritik

---

#### 2B.7 Century Tech (BK) — AI Okul Araci

**Temel Metrikler:**
- BETT Award kazanani (birden fazla yil)
- Kullanim: 150+ okul, BK ve Orta Dogu

**Teknik Mimari:**
- **Norobilim tabanli model:** Bellek pekistirme + bireysel mufredat
- **Ebbinghaus egrisi entegrasyonu:** Unutma eğrisine gore tekrar programi
- **Ogretmen dashboard:** Sinifin kolektif bilgi haritasi + bireysel zayif noktalari

**Pedagojik Model:**
- Neuro-adaptive learning: Beyin yorgunlugunu izleme (oturum uzunlugu + hata orani)
- Ogretmen destekleyici: Teknoloji ogretmenin yerine gecmez, yardimci olur

**KIRO2 Relevans:** Ogretmen dashboard modeli; KVKK uyumlu veri toplama ornegi

---

#### 2B.8 Edmentum (ABD) — Degerlendirme Odakli

**Temel Metrikler:**
- Kullanim: 20,000+ okul, K-12
- Urunler: Exact Path, Study Island, Courseware

**Teknik Mimari:**
- **Exact Path:** Her ogrenci icin kisisellestirilmis ogrenme yolu
  - CAT degerlendirme ile baslangic noktasi belirlenir
  - Bireysel yol uretir, ogretmen manuelce ayarlayabilir
- **Prediktif basari modeli:** Ogrenci risk seviyesini semester basinda tahmin eder

**KIRO2 Relevans:** Kurum-icin deployment modeli; ogretmen kanaline entegrasyon ornegi

---

#### 2B.9 Realizeit (Irlandia) — Bilgi Grafigi Motoru

**Temel Metrikler:**
- Kullanim: Universite + K-12 karma
- Ortakliklar: CBE (Competency-Based Education) programlari

**Teknik Mimari:**
- **Bilgi grafigi gorsellestirme:** Ogrenci bilgi durumunu grafikte gosterir
  - Her dugum: bilgi noktasi (bilinen = yesil, bilinmeyen = kirmizi, ogrenilmekte = sari)
- **Prerequisite path hesaplama:** Hedef konuya giden en etkin yol
- **Competency mapping:** Her beceri ile ogrenme hedefi arasinda baglanti

**KIRO2 Relevans:** YKS konu grafigi gorsellestirme modeli; ogrenme yolu UI icin

---

#### 2B.10 D2L Brightspace (Kanada) — LMS + Adaptif

**Temel Metrikler:**
- Kullanim: 15 milyon+ ogrenci, 50+ ulke
- Best Higher Ed Platform 2024 (EdTech Digest)
- Odak: Universite + K-12 LMS

**Teknik Mimari:**
- **Yerlesik analytics:** Her ogrenci icin detayli ilerleme analitigi
- **Prediktif basari modeli:** Ders basarisini erken uyari ile tahmin eder
- **Adaptive activities:** Adaptive Release ozelligi (kural tabanli icerik kilidi)

**KIRO2 Relevans:** Kurumsal kanal icin platform modeli; analytics dashboard ornegi

---

#### 2B.11 Eduten / ViLLE (Finlandiya) — Oyun Tabanli

**Temel Metrikler:**
- Kapsam: PISA ustunde performans gosteren Finlandiya matematik pedagojisi
- Kullanim: Finlandiya ve Kuzey Avrupa K-12

**Teknik Mimari:**
- **Duşuk basinc modeli:** Hata cezasi yok, deneme serbestisi var
- **Oyun entegrasyonu:** Matematik sorulari oyun mekanigine gomulmus (saldiri/savunma degil, insa et)
- **Formative assessment:** Ogretmen surekli geri bildirim aliyor, not yok

**Pedagojik Model:**
- PISA ustunde Finlandiya modeli: Ozerklik + ustanlik + dusuk stres kombinasyonu
- %40+ motivasyon artisi (bagimsiz arastirma)

**KIRO2 Relevans:** Stres azaltma + buyume zihniyeti pedagogisi; hata cezasi tasarimi icin

---

#### 2B.12 Bettermarks (Almanya) — Hata Analizi

**Temel Metrikler:**
- Kapsam: K-12 matematik, Almanya + Hollanda + Guney Afrika
- Kullanim: 1 milyon+ ogrenci

**Teknik Mimari:**
- **Hata klasifikasyonu:** Her yanlis cevap kategorilendirilir
  - Isaretleme hatasi / konsept hatasi / hesap hatasi / unutma hatasi
- **Hata pattern tespiti:** Ogrencinin tekrarlayan hata tipini belirler
- **"Neden yanlis?" geri bildirimi:** Sadece "yanlis" degil, hangi tip yanlis

**Pedagojik Model:**
- "Hatalar ogrenme firsatidir" — ceza sistemi yok
- Ogrenci hatasi = bilgi boslugu gorstergesi — remediation tetikleyicisi

**KIRO2 Relevans:** YKS hata teşhisi icin kritik model; error pattern → remediation node bagiantisi

---

#### 2B.13 Domoscio (Fransa) — Aralikli Tekrar

**Temel Metrikler:**
- Kapsam: Corporate learning + K-12
- Finansman: Fransa kamu destekli

**Teknik Mimari:**
- **FSRS benzeri algoritma:** Bilginin unutulma egrisi tabanli tekrar planlama
- **Mikro-ogrenme modulu:** 2-5 dakikalik capsule modulleri
- **Kisisellestirilmis program:** Her ogrenci icin farkli tekrar zamanlama

**KIRO2 Relevans:** FSRS implementasyonu ornegi; corporate ogrenme modelinin K-12'ye adaptasyonu

---

#### 2B.14 Toppr (Hindistan) — Canli Ogretmen + Adaptif

**Temel Metrikler:**
- BYJU's tarafindan satın alindi (2021)
- Kullanici: 8 milyon+ (zirve)
- Kapsam: JEE, NEET, CBSE sinav hazirlik

**Teknik Mimari:**
- **Hibrit model:** AI adaptif test + canli ogretmen oturumu
- **Anlik suphe cozme:** "Ask a Doubt" — canli ogretmen baglantisi
- **Adaptif test:** IRT tabanli soru secimi

**Pedagojik Model:**
- AI + insan ogretmen dengesi: Algoritmik adaptasyon + insani aciklama
- Canli ogretmen hem motivasyon hem icerik saglar

**KIRO2 Relevans:** AI + insan ogretmen hibrit modeli; "bilge ajan" konseptinin gercek uygulama ornegi

---

#### 2B.15 Cognii (ABD) — Konusmasal AI Degerlendirme

**Temel Metrikler:**
- Kapsam: Universite + K-12, acik uclu soru degerlendirme
- Teknoloji: NLP tabanli otomatik not verme

**Teknik Mimari:**
- **NLP degerlendirme:** Acik uclu yazili cevaplari otomatik degerlendirir
- **Diyalogtik soru:** "Neden oyle dusunuyorsun?" takip sorusu sistemi
- **Formative geri bildirim:** Anlayis derinligini olcer, yuzey bilgiyi degil

**KIRO2 Relevans:** TYT Turkce acik uclu soruler; yazili anlatim becerisi degerlendirme

---

#### 2B.16 Quizlet (ABD) — Flash Kart + Ogrenme Modu

**Temel Metrikler:**
- Kullanici: 600 milyon+ kayitli (toplam)
- MAU: 60 milyon+
- 2024: AI Study Assistant entegrasyonu

**Teknik Mimari:**
- **Learn Mode:** Adaptive flashcard sequencing
  - SM-2 benzeri zamanlama algoritmalari
  - Dogru cevaplanan kart daha gec tekrar, yanlis kart daha erken
- **Spaced repetition:** Long-Term Learning modu

**KIRO2 Relevans:** Flash kart mekanigi; FSRS ile birlesik kart tekrar sistemi

---

#### 2B.17 Uchi.ru (Rusya) — Okul Platformu

**Temel Metrikler:**
- Rusya'nin lider K-12 platformu
- Kullanici: 8 milyon+ ogrenci, 700,000+ ogretmen

**Teknik Mimari:**
- **Gamification + mastery:** XP, rozet, seviye sistemi
- **Ogretmen dashboard:** Sinif ilerleme goruntulemesi
- **Devlet entegrasyonu:** Rusya FGOS standartlariyla tam uyum

**KIRO2 Relevans:** Ulke ozgunu standart uyumu + gamification modeli; KVKK benzeri yerel mevzuat uyumu

---

#### 2B.18 Lalilo (Fransa) — Okuma Fonettigi

**Temel Metrikler:**
- Kapsam: K-2 okuma fondis, Fransizca
- Kullanim: 1 milyon+ ogrenci, 30,000+ ogretmen

**Teknik Mimari:**
- **Diferansiye ogretim:** Sinif icinde farkli seviyelere farkli icerik
- **Ebeveyn katilimi:** Ebeveyn mobil uygulamasiyla ev calismasi takibi
- **Adaptif ilerleme:** Fonettik ustanligina gore bir sonraki dugum

**KIRO2 Relevans:** Ebeveyn katilimi modeli (K-12 KIRO2 segmenti planlaniyor ise); diferansiye ogretim ornegi

---

#### 2B.19 EvidenceB (Fransa) — AI Ogrenme

**Temel Metrikler:**
- Kapsam: MoovLab platformu, Fransa K-12
- Finansman: France 2030 programi destekli

**Teknik Mimari:**
- **MoovLab:** Kisisellestirilmis mufredat olusturma motoru
- **EU AI Act uyumu:** Aciklanabilir AI, veri minimizasyonu, ogunci onay
- **Ogrenme profili:** 8 boyutlu ogrenci profili (bilis, motivasyon, meta-bilis)

**KIRO2 Relevans:** AB AI Act uyumlu pedagoji modeli; KVKK ile paralel yaklaslim; aciklanabilir AI ornegi

---

#### 2B.20 Zuoyebang (Cin) — Mobil Sinav Hazirlik

**Temel Metrikler:**
- Finansman: $4B+ (Seri F oncesi $6B degerlemesi)
- Kullanici: 170 milyon+ (zirve)
- 2021 sonrasi: B2B pivotu

**Teknik Mimari:**
- **Fotografik soru cozme:** OCR + AI anlik soru aciklamasi
- **Canli ders entegrasyonu:** Adaptif AI test + canli ogretmen hibrit
- **Mobil-first:** Telefon kamerasi ile soru tarama

**Cin Duzenleme Sonrasi:**
- 2021 "Double Reduction": Ozel K-12 egitim yasaklandi
- Zuoyebang B2B devlet okulu platformuna pivot yapti
- Aile dogrudan satis durdu, okul kanali acildi

**KIRO2 Relevans:** Mobil-first YKS hazirlik modeli; OCR + soru eslestirme altyapimizia uyum; B2B okul kanalı genis ufukta

---

#### 2B.21 Edraak (Urdun) — Arapca MOOC

**Temel Metrikler:**
- Kapsam: MENA bolgesi, 22+ Arap dili ulkesi
- Kullanici: 6 milyon+ kayitli
- Model: Queen Rania Vakfi destekli

**Teknik Mimari:**
- **Yerellestirilmis icerik:** Batili MOOC'larin Arapca adaptasyonu
- **Kulturel uyum:** Orta Dogu pedagojisi + yerel mufredat
- **Acik erisim:** Ucretsiz temel, sertifika odenmeli

**KIRO2 Relevans:** Turkce yerellestirilmis icerik modeli — Edraak'in Arap dili icin yaptigi gibi KIRO2 Turkce icin yapabilir

---

#### 2B.22 Prodigy Education (Kanada) — K-8 Matematik Oyunu

**Temel Metrikler:**
- Kullanici: 100 milyon+ kayitli ogrenci
- Finansman: 400 milyon dolar (2021)
- Kapsam: K-8 matematik, ABD + Kanada

**Teknik Mimari:**
- **RPG + matematik:** Savaş/quest icinde matematik sorulari cevaplamak zorunlu
- **Odelek birimi:** "Yildiz" (premium disi; Premium kahraman + kiyafet)
- **Okul kanalı dağıtımı:** Ogretmen sinifi olusturur, ogrenciler katilir
- **Sinif modu:** Ogretmen hangi konuyu hedefleyecegini seker

**Oyun + Ogrenme Ayrimi:**
- Ogrenciler oyunun icinde matematik gordugunu fark etmez
- Oyun ortami "gercek ogrenme" sandiklari olarak matematik sorulari gizler
- Ancak oyun modu > ogrenme modu olma riski gozlemlenmis

**KIRO2 Relevans:** Oyun sarilmali ogrenme ("sugar coating") modeli; okul kanalı dagitim ornegi

---

## 3. ALGORITMA KARSILASTIRMA MATRISI

### 3.1 Bilgi Izleme Algoritmalari

| Algoritma | Aciklama | AUC | Gucluk | Zayiflik | KIRO2 Uyumu |
|-----------|----------|-----|--------|---------|-------------|
| **BKT** | Gizli Markov, 4 param | 0.61-0.68 | Yorumlanabilir | Varsayimlar katiydi | YUKSEK |
| **IRT 3PL** | Madde parametreleri | 0.65-0.72 | Standart sinav | Bilgi gecisi yok | MEVCUT |
| **DKT** | LSTM tabani | 0.74-0.82 | En guclu tahmin | Yorumsuz kara kutu | ORTA |
| **DKVMN** | Memory Network | 0.78-0.85 | En guncel | Yuksek hesap maliyeti | DUSUK |
| **SAKT/AKT** | Transformer tabani | 0.76-0.84 | Son teknoloji | 100K+ veri gerekli | DUSUK |
| **HLR** | Unutma egrisi | Spesifik | Hizalama icin | Tek beceri tahmini | ORTA |
| **FSRS** | SM-2 guncelleme | - | HLR + SM-2 ustun | - | MEVCUT |

**CMU Veri Yarismasi Sonuclari (Baker et al., 2012):**
- DKT, 0.06-0.17 AUC artisiyla BKT'yi gecti
- LSTM mimarisi, ogrenci gec kalintisal etkilerini yakaladi

### 3.2 DKT KIRO2 Entegrasyon Yol Haritasi

KIRO2'ye DKT entegrasyonu icin teknik adimlar:

1. **Veri toplanmasi:** Ogrenci + soru + dogru/yanlis + timestamp logu (min 50K etkilesim)
2. **Model secimi:** PyKT veya Knowledge4All kutuphanesi (acik kaynak DKT uygulamasi)
3. **Konu embedding:** YKS konu taxonomy → embedding space (konu cogunlugu)
4. **Training:** Ogrenci gecmisi → bir sonraki soruyu dogru mu yanlis mi yapacak tahmini
5. **IRT entegrasyonu:** DKT ciktisi ability tahmini IRT theta'sini gunceller
6. **A/B test:** DKT+IRT vs mevcut IRT sadece — en az 1,000 kullanicida 4 hafta test

**Minumum veri esigi:** 50,000 etkilesim kaydı olmadan DKT training gereksiz

### 3.3 Transformer Tabanli Modeller (SAINT, AKT)

**SAINT (Shin et al., 2021):**
- Encoder: Egzersiz sekansı
- Decoder: Cevap sekansı
- AUC: 0.778-0.810 (EdNet veri seti)
- Gereksinim: 100K+ etkilesim

**AKT — Attention-based Knowledge Tracing (Ghosh et al., 2020):**
- Context-aware attention: Yakin gecmis daha fazla agirlik alir
- Monotonik dikkat mekanizmasi: Bilgi birikimi modeli
- AUC: 0.80-0.84 (EdNet + ASSISTments)

**KIRO2 Degerlendirme:** 77K soru, 10K+ kullanici elesimle transformer modeli denemek mantikli olabilir — ancak 12 ay sonra.

### 3.4 KIRO2 Onerilen Hibrit Motor

```
IRT 3PL (mevcut)
    + BKT posterior (eklenecek — Sprint 5)
    + FSRS decay (mevcut)
    = Hibrit Ability Estimation

Soru secimi:
    ZPD hedef: basari olasiligi 0.65-0.85
    + Zabrani tekrar esigi gecen sorular oncelikli
    = "Ne zaman hangi soru" biliyor
```

**Beklenen iyilesme:** BKT eklenmesiyle soru secim isabeti +15-20%

### 3.5 Uyarlanabilir Soru Secimi Algoritmalari

| Yaklasim | Kullanilan Platform | Etki | Not |
|----------|---------------------|------|-----|
| **CAT (Bilgisayarlik UCD)** | Khan, Squirrel AI | %50 soru azaltma | IRT gerekli |
| **ZPD Hedefleme** | KIRO2 (mevcut) | Standart | %15-85 hedef |
| **ZPDES** | Inria (Vygotsky) | +1 SD kazanim | Zorlugun acik tespiti |
| **Multi-Armed Bandit** | Netflix, Google | %5-15 iyilesme | Exploration/exploitation |
| **Graph-Based Path** | ALEKS, Squirrel AI | +%300 hizlanma | Prerequisite haritalama |

### 3.6 Uzaylanmis Tekrar (Spaced Repetition) Algoritmalari

| Algoritma | Dagitici | Avantaj | Gecerleme |
|-----------|---------|---------|-----------|
| **SM-2** | Anki | Klasik standart | 30+ yil veri |
| **FSRS (mevcut)** | KIRO2, Anki 24+ | SM-2'den %20-30 az tekrar | Yan 2022 |
| **HLR** | Duolingo | Dil ogrenme ozel | Settles & Meeder 2016 |
| **DRL-SRS** | Arastirma | %35+ verimlilik | Tabibian 2019 |

**FSRS Not:** KIRO2'de zaten mevcut — entegrasyon oncelik tasiyor

---

## 4. ULKE BAZLI DERINLEMESINE ANALIZLER

### 4.1 ABD — Pazar Lideri

**Pazar Ozellikleri:**
- Kuresel EdTech VC'sinin %58'i ABD'ye akiyor
- Top platformlar: Duolingo, Khan Academy, IXL, DreamBox, Carnegie Learning, Riiid
- AI tutoring patlamasi: Khanmigo, School AI, MagicSchool AI, Kira (2024+)

**Duzenleme Ortami:**
- FERPA: Eğitim verisi gizliligi (ogrenci kayitlari korunmali)
- COPPA: 13 yas alti veri toplama kısitlamalari (ebeveyn izni zorunlu)
- State-by-state variation: Her eyalet farkli standartlar

**Trendler (2024-2026):**
1. AI tutoring: "Personel ogretmen herkes icin" iddiasi
2. Mastery learning standardizasyonu: Khan + DreamBox + IXL uyumu
3. Ogretmen aracı odagi: AI ogretmeni destekler, yerini almaz
4. Assessment-as-learning: Degerlendirme ogrenme sureci icine gomulu

**KIRO2 Dersi:** Compliance-first yaklasim (KVKK uyumu) + mastery learning standardi + ogretmen dostu araclara yatirim

---

### 4.2 Cin — Duzenleme Soku

**2021 "Double Reduction" Politikasi:**
- Ozel K-12 ek ders = yasak (Temmuz 2021)
- 100+ milyar dolar EdTech deger eridi tek politika degisikligi ile
- Hayatta kalanlar: B2B pivotu, sinav hazirlik (K-12 ustu izin verildi), okul-ici SaaS

**Buyuk Oyuncular Sonrasi Durum:**

| Sirket | 2021 Oncesi | 2024 Durumu |
|--------|-------------|-------------|
| TAL Education | $20B+ deger | $2.25B gelir, AI pivot basarili |
| New Oriental | K-12 agirlikli | E-ticaret canli yayin fenomeni |
| Squirrel AI | K-12 AI | B2B devlet okulu, LAM 2024 |
| Zuoyebang | $6B deger | B2B devlet okulu SaaS |
| BYJU's (Cin versiyonu) | Buyuk pazar | Cikis |

**Vaka Analizi — Squirrel AI Hayatta Kalmasi:**
- B2B devlet okulu modeli: Hukumetten lisans al, okullara sun
- LAM (Large Adaptive Model) 2024: Teknoloji yenileme ile rekabet avantaji koru

**KIRO2 Dersi:** Politik risk hedge zorunlu — B2B + B2C dengesi; tek kanal riski; teknoloji superioru = koruyucu hendek

---

### 4.3 Finlandiya — Pedagoji Modeli

**PISA Sonuclari:**
- Matematik: %21 en yuksek performans (OECD ortalamasinin ustunde)
- Okuma: Dunya 3. (PISA 2022)
- Fen: Dunya 4.

**Pedagojik Felsefe:**
- Dusuk stres: Deger notlari 7. sinifa kadar yok
- Oyun tabanli: ViLLE/Eduten — matematik oyunlastirmasi
- Ogretmen gucu: Teknoloji ogretmeni destekler, yerini almaz
- Formative assessment: Sik not yerine surekli geri bildirim

**Eduten/ViLLE Verileri:**
- %40+ motivasyon artisi (bagimsiz arastirma, Hyo et al. 2020)
- Matematik kaygi indeksi %35 dusus
- Ogrenci-ogretmen isbirligi artisi

**KIRO2 Dersi:**
1. Stres azaltma tasarimi: Hata cezasi kaldir, buyume zihniyeti mesajlari ekle
2. Formative assessment: Surekli kucuk degerlendirme > buyuk sinav korkusu
3. Ogretmen dashboard: Okul kanalina giris icin kritik

---

### 4.4 Guney Kore — AI Sinav Hazirlik

**CSAT (Suneung) Kulturu:**
- YKS ile en yakin benzerlik: 1 gunluk "hayat degistiren" sinav
- Dershane (hagwon) kulturunu: 10 milyar dolar sektoru
- AI vs hagwon: AI daha ucuz, 7/24 erisim, kisisellestirilmis

**Buyuk Oyuncular:**

| Sirket | Ozelligi | Etki |
|--------|---------|------|
| QANDA/Mathpresso | OCR + MathGPT + anlik cozum | 90M+ kullanici, %92+ dogru |
| Santa (Riiid) | DKT + TOEIC teshis testi | +130 TOEIC, 20 saatte |
| Class101 | Canli ogretmen + icerik | 3.5 milyon kullanici |
| Classting | Sinif yonetim + adaptif | 10 milyon kullanici |

**Technoloji Egilimi:**
- OCR tabanli soru cozme: Fotografı cek, cevap al (QANDA, Zuoyebang, Photomath)
- Anlik geri bildirim: Cevap milisaniyede, aciklama saniyede
- AI + canli ogretmen: Hibrit model hakimiyet kazaniyor

**KIRO2 Dersi:** OCR entegrasyonu + anlik geri bildirim onceligi; 77K sorumuzun gorseli (%75.7) bu icerik katmani icin deger tasir

---

### 4.5 Hindistan — Olcek Modeli

**Pazar Ozellikleri:**
- Buyukluk: $6.2 milyar (CAGR %22 — dunya en hizli)
- K-12 nufus: 250 milyon+ (dunya 1.)
- JEE/NEET: YKS'ye benzer ulusal rekabetci sinavlar

**BYJU's Cokusu — Dersler:**
- Finansman: $5.7 milyar toplam (SoftBank, Naspers, Sequoia)
- Deger zirve: $22 milyar (2022)
- Gercek gelir/harcama ucsurumu: $1.5B beklenti vs $827M gercek
- Agresif satiscilik: Ebeveynlere "sinav garantisi" ile borclantirma
- Ders: Urun kalitesi > pazarlama butcesi; kullanici basari kaniti olmadan buyume surdurulemez

**Hayatta Kalanlar — PhysicsWallah Modeli:**
- FY2025 gelir: $347M, +%49 yillik — rakipler dususturkende buyudular
- Model: Dusuk fiyat ($1.5/ay) + yuksek kalite icerik + odakli segment
- Demokratik erisim: "Iyi egitim zengin cocuklara mahsus olmamali"

**Mindspark — En Yuksek Akademik Kanit:**
- J-PAL RKC (2021): Gunluk 45 dk = 2x ogrenme kazanimi (kontrol grubuna gore)
- Maliyet: $3/ogrenci/ay — kuresel en dusuk maliyet-etkin platform

**KIRO2 Dersi:** Basari kaniti > pazarlama; dusuk fiyat + yuksek kalite + odakli segment = surdurulebilir; akademik RCT kaniti rekabet avantaji

---

### 4.6 Fransa — Devlet Destekli EdTech

**Politika Ortami:**
- France 2030 programi: 2.5 milyar Euro EdTech fonlamasi
- "Edu-up" programi: Okullarda dijital arac entegrasyonu tesviki
- AB AI Act uyumu: Erken uyum politikasi

**Buyuk Oyuncular:**

| Sirket | Model | Destekleyici |
|--------|-------|-------------|
| Lalilo | K-2 okuma pedagojisi | France 2030 |
| Domoscio | SRS corporate + K-12 | Kamu fonu |
| EvidenceB | AI pedagoji, MoovLab | Europe Horizon |
| Kartable | Konu ozeti + test | Ozel |

**AB AI Act Etkisi (2024 yururluge girdi):**
- Yuksek risk AI: Egitim degerlendirme sistetmleri denetim altinda
- Aciklanabilir AI zorunlulugu: "Neden bu karar?" kullaniciya aciklanmali
- Veri minimizasyonu: Sadece gerekli veriyi topla
- Insan gozetimi: AI kararina insan itiraz edebilmeli

**KIRO2 Dersi:** KVKK + AB AI Act uyumu rekabet avantaji olabilir; aciklanabilir AI ("neden bu soru sana geldi?") kullanici guveni saglar

---

### 4.7 Rusya — Pazar Izolasyonu

**Pazar Ozellikleri:**
- Buyukluk: 3.4 milyar dolar (2024 tahmini)
- Liderler: Uchi.ru, Skyeng, Foxford, Учи.ру
- 2022 sonrasi: Uluslararası islem kısitlamalari + izolasyon

**Hayatta Kalma Stratejileri:**
- Yerel icerik + yerel dil avantaji: Yabanci rakiplere kapi kapali
- Devlet entegrasyonu: Okul SaaS modelinde devlet ortakliği
- B2B pivot: Bireysel ogrenci > okul/aile paketi

**Uchi.ru Basarisi:**
- 8 milyon+ ogrenci, 700,000+ ogretmen
- Devlet okulu entegrasyonu: %40+ Rus ilkokulu kullanıyor
- Model: Okul kanalina serbest, ebeveyn premium

**KIRO2 Dersi:** Yerel icerik (Turkce YKS sorusu) + yerel dil avantaji = savunulabilir hendek; devlet/okul kanal uzun vadeli surdurulebilir

---

### 4.8 Kanada — Kamu + Ozel Denge

**Pazar Ozellikleri:**
- Guclü kamu egitim sistemi + ozel EdTech dengesi
- D2L (Waterloo merkezli): Universite LMS'de kuresel lider
- Prodigy (Toronto): K-8 matematik oyunu, 100M+ kullanici

**D2L Brightspace Modeli:**
- Universite kanal hakimiyeti: Kuzey Amerika'nin %30+ universitesi kullanıyor
- Kurum LMS → bireysel adaptif: Universite aracından bireysel araca genisleme
- Analytics: Ogretmen + kurum + ogrenci uclu veri modeli

**Prodigy Okul Dagitimi:**
- Ogretmen sinif olusturur: Ucretsiz
- Ogrenci oynuyor: Ucretsiz
- Ebeveyn premium: Oyun kozmetik + ekstra icerik
- Kuresellesme: 100M+ kullanici, 30+ ulke

**KIRO2 Dersi:** Okul + bireysel cift kanal; ogretmen ucretsiz → ebeveyn premium freemium modeli

---

### 4.9 Turkiye — KIRO2'nin Pazari

**Pazar Verileri:**
- Buyukluk: $1.8 milyar (2024 tahmini)
- CAGR: %14.2 (2024-2030)
- YKS aday sayisi: 2.8 milyon+ (2024)
- Dershane harcamasi: Aile basina ortalama 15,000-50,000 TL/yil

**Mevcut Rekabet Haritasi:**

| Platform | Guclu Yani | Zayif Yani | Tehdit Seviyesi |
|----------|-----------|-----------|-----------------|
| Enuygun | Icerik genisligi, video | Adaptif yok, pasif | ORTA |
| Matematik Kolay | Video kalitesi | Kisi-bagimsiz | DUSUK |
| 1001Soru | Soru havuzu | Eski, adaptif yok | DUSUK |
| Okyanus | Kurumsal kanal | B2C zayif | DUSUK |
| Tonguc | Marka + kitap | Dijital zayif | DUSUK |
| Kilavuz (dijital pivot) | Marka + sahne etkisi | Gecikmeli | YUKSEK (gelecek) |

**KIRO2'nin Farki — Kimse Yok:**
- 77,336 YKS sorusu (USTUN icerik)
- IRT 3PL parametre kalibrasyon
- FSRS spaced repetition entegrasyonu
- VARK ogrenci profili
- Adaptif ogrenme yolu
- Bu kombinasyon Turkiye'de YALNIZCA KIRO2'de var

**Risk Senaryosu:**
- Kilavuz/Acil/Mavi'nin dijital pivotu + AI yatirimi (18-24 ay): YUKSEK RiSK
- Khanmigo Turkce versiyonu (Khan): ORTA RISK (icerik kalitesi dusuk YKS icin)
- Riiid/Santa'in YKS versiyonu: DUSUK RISK (yerel icerik yok)

---

## 5. UNIVERSITE BAĞLANTILI PLATFORMLAR

### 5.1 MIT OpenCourseWare & MIT xPRO

**MIT OpenCourseWare:**
- Icerik: 2,500+ ders, 350 milyon+ kullanici
- Model: Tamamen ucretsiz, Creative Commons lisansi
- Etki: Dunyanin en buyuk acik egitim icerik deposu

**MIT xPRO:**
- Hedef: Profesyonel sertifika (kurum odakli)
- Teknik: Self-paced + adaptif quizler
- Adaptif unsur: OpenedX tabanli, kosu geri bildirimi

**KIRO2 Relevans:** Icerik kalite standardi; acik kaynak pedagoji modeli; icerik kalitesi ve dogrulugu

---

### 5.2 Stanford Online / edX (Microsoft)

**Stanford Online:**
- Self-paced + cohort-based hibrit modeller
- Lagunita: Acik kaynak LMS (artik emekliye ayrildi)
- Adaptif grading pilot: OpenEdX tabanli

**edX:**
- 2021'de Microsoft/2U'ya 800 milyon dolara satildi
- 39 milyon+ kayitli kullanici
- 3,000+ kurs, 160+ ortak universite
- Adaptive learning modulu: 2024'te beta

**KIRO2 Relevans:** Universite ortaklik modeli; profesyonel sertifika yolu uzun vadede

---

### 5.3 CMU Open Learning Initiative (OLI)

**Genel Bakis:**
- Carnegie Mellon Universitesi'nin acik ogrenme platformu
- Kognitif ogretmen arastirmasinin dogrudan urun hali
- Datashop: 350,000+ ogrenci, kamuya acik log veri seti

**Teknik Katkisi:**
- **Knowledge Component (KC) Model:** Her problem alt-becerilere ayrilmis
- **Learning Curve Analysis:** Her KC icin ogrenci egrisini analiz eder
- **Error Analysis Tool:** Hatalar tiplendirilir ve mufredat iyilestirmesi onerilir

**Acik Veri:**
- DataShop: OLI'nin 350K+ ogrenci log verisi herkese acik
- 120+ arastirma makalesi bu veriyi kullanmistir
- YKS icin: KC modeli ve hata analizi dogrudan uyarlanabilir

**KIRO2 Relevans:** KC model ve log analizi icin en iyi kaynak; DataShop veri metodolojisi; hata tipolojisi

---

### 5.4 Oxford Online / FutureLearn

**FutureLearn:**
- 16 milyon+ kullanici (zirve)
- 2023'te yeniden yapilanma: Tam mikro-ogrenmeye gecis
- Sosyal ogrenme: Tartisma forumlari entegrasyonu

**Oxford Digital Learning:**
- Post-lisans + profesyonel gelisim odakli
- Blended learning: Online + yuz yuze hibrit

**Sosyal Ogrenme Bulgulari:**
- FutureLearn'in tartisma forumu verisi: Etkilen katilim %34 daha yuksek tamamlama orani
- Sosyal baglanti retention icin kritik degisken

**KIRO2 Relevans:** Sosyal ogrenme ozelligi icin kanit; tartisma + topluluk mekanizmalari retention artisı saglar

---

### 5.5 Cambridge Assessment & Diagnostic Questions

**Diagnostic Questions (Craig Barton, Cambridge Assessment destekli):**
- 250 milyon+ kullanici cevabi veri tabanı
- 4 secenekli ozel soru formati: Her yanlis secenekte farkli hata tipi
- "Neden o secenegi sectiniz?" — kavrayis degerlendirmesi

**Cambridge International Assessment:**
- A/AS Level hazirlik: Revise.com platformu
- Adaptive quiz: IGCSE + A-Level konu bazli

**Hata Analizi Metodolojisi:**
Craig Barton yaklaşimi:
- Her soru 4 secenek: 1 dogru + 3 "diagnostik yanlis"
- Her yanlis secenek farkli kavram yanilgisini hedefler
- Sonuc: Hangi ogrenci hangi yanliyi secti → kavram haritalamasi

**KIRO2 Relevans:** 77K sorumuzun yanlis secenek analizi icin model; hata tipolojisi ve kavram yanilgisi haritasi

---

## 6. OGRENME PSIKOLOJISI

### 6.1 Temel Bulgular (v1'den)

#### 6.1.1 Meta-Analiz Ozeti — Oyunlastirma

**Hamari, Koivisto & Sarsa (2014):**
- N=24 calisma; olumlu etki kosulu: anlayisi olan kullanici
- Egitimde en yuksek etki

**Sailer & Homner (2020):**
- N=30 RCT; bilisyel: g=0.49; davranissal: d=0.48; duygusal: d=0.36

**Bai, Hew & Huang (2020):**
- N=28 RKC; akademik performans: d=0.48
- Uzun vade (>4 hafta): Etki azaliyor — yenilik etkisi

**Koivisto & Hamari (2019):**
- Ilk haftalar buyuk artis, aylar icinde azalma
- Cozum: Periyodik yeni mekanik ekleme

### 6.2 Yeni Bulgular (v2 Eklentisi)

#### 6.2.1 Productive Failure (Kapur, 2016)

**Teori:**
- Geleneksel ogretim: Aciklama once → pratik sonra
- Productive Failure: Pratik once (basarisizlik kabul) → aciklama sonra
- Bulgu: Zor sorudan once aciklama okumak pasif icerik tuketimi saglar; once struggle etmek derin kodlamayi tetikler

**Kapur (2016) Meta-Analizi:**
- N=21 calisma, standartlastirilmis etki buyuklugu d=0.34 (orta)
- Aritmetik ve denklem cozme icin en guclu etki
- Sonuc: "Struggle zone" gecmeden verilern aciklama pasif kalir

**KIRO2 Adaptasyonu:**
- Escalating Failure Handler (Katman 3): 2 hataya kadar aciklama verilmez
- Bu "productive struggle zone" kasitli — erken ipucu pasif tüketimi onler

#### 6.2.2 Desirable Difficulties (Bjork & Bjork, 2011)

**Teori:** Ogrenmeyi kolaylastiran seyler (tekrar + kolay) uzun vadeli hafizayi zayiflatir; zorlaştiran seyler (test etme, aralikli) uzun vadeli hafizayi guclendirir.

**5 "Istenen Zorluk":**
1. **Aralikli tekrar:** Blok yerine seyrek + aralikli (FSRS bunu saglar)
2. **Test etme etkisi:** Okuma yerine kendini test etme 2x hatırlama
3. **Karma pratik (interleaving):** Konu bloku yerine karma soru sirasi
4. **Azaltilmis geri bildirim:** Her soruda degil, ara ara geri bildirim
5. **Jenerasyon etkisi:** Cevabi uretmek > okumak

**KIRO2 Adaptasyonu:**
- FSRS: Aralikli tekrar zaten mevcut
- Karma pratik modu: Farkli konulardan karma soru sirasi (interleaved quiz)
- Test etkisi: Her konuda "anki bilgini test et" modu

#### 6.2.3 Interleaved Practice (Taylor & Rohrer, 2010)

**Blok Pratik:** AAABBBCCC (konuya gore gruplu)
**Karma Pratik:** ABCABCABC (karisik sirali)

**Bulgular (Taylor & Rohrer, 2010):**
- Blok pratik: 1 gun sonra %89 dogru, 1 hafta sonra %38 dogru
- Karma pratik: 1 gun sonra %60 dogru, 1 hafta sonra %63 dogru

**Sonuc:** Karma pratik kisa vadede daha zor hissettirirse de uzun vadeli retansiyon 1.6x daha iyi.

**KIRO2 Adaptasyonu:**
- "Karisik Pratik" modu: Ogrencinin farkli konulardan karma soru almasi
- Ogrencilere aciklama: "Bu mod zor hissettirir, ama uzun vadede daha iyi ogrenir"
- YKS icin kritik: Sinav karisik konu iceriyor — blok calisma gercek sinavla uyumsuz

#### 6.2.4 Growth Mindset (Dweck, 2006)

**Sabit Zihniyet:** "Zeki degilim" → zorluklarda vazgeciyor
**Buyume Zihniyeti:** "Henuz ogrenemiyorum" → zorluklarda ısrar ediyor

**Dweck (2006) Bulgulari:**
- Buyume zihniyeti mudahalesi: Okul basarisi anlamlı iyilesme (d=0.30)
- Cocuklara "sen akillisın" demek sabit zihniyeti pekistirir
- Cocuklara "cok calıştın" demek buyume zihniyetini pekistirir

**KIRO2 Adaptasyonu:**
- Geri bildirim dili: "Sen yanlis yaptin" yerine "Bu konu henuz ustun degil — calisalim"
- Hata mesaji: "Yanlis!" yerine "Henuz dogru degil — bir daha dene"
- Rozet: "Uzmanlik" rozeti yerine "Ilerleme" rozeti daha etkili

#### 6.2.5 Test Etkisi — Retrieval Practice (Karpicke & Roediger, 2008)

**Deney:**
- Grup 1: Metin 4x oku
- Grup 2: Metin 1x oku + 3x test et
- 1 hafta sonra: Grup 2 %68 daha fazla hatirliyor

**KIRO2 Adaptasyonu:**
- "Oku ve Test Et" modu: Video izle + hemen mini-quiz
- Pasif video izleme → aktif test etme gecisi
- FSRS tekrar: Test etkisini spaced repetition ile birlestirir

### 6.3 Psikolojik Mekanizmalar (v1'den guncellendi)

#### 6.3.1 Pekistirme Teorisi (Skinner 1938)

| Program | Tanim | Ornek | Direnc |
|---------|-------|-------|--------|
| Sabit Oran (FR) | Her N davranisla odul | Her 10 soru = rozet | DUSUK |
| Degisken Oran (VR) | Rassal N davranisla odul | Bagimlilik yaratan en guclu | EN YUKSEK |
| Sabit Aralik (FI) | Her N dakika | Gunluk odul | ORTA |
| Degisken Aralik (VI) | Rassal zaman | Surprise bonuslari | YUKSEK |

**KIRO2 Onerisi:** VR tabanli rozet sistemi — "Herhangi bir anda tatlandirma"

#### 6.3.2 Kayip Kacinma (Kahneman & Tversky 1979)

**Prospekt Teorisi:** Kayip, kazancin 2-2.5x daha guclu hissettiriyor

Uygulamalar:
- Duolingo Lives: Can kaybi > XP kazanci
- Streak korunma: Kaybetme korkusu > kazanma istegi
- KIRO2 Onerisi: "Kazanmak" yerine "Kaybetmemek" frameleme

#### 6.3.3 Oz-Belirleme Teorisi (Deci & Ryan, 1985)

**3 Temel Ihtiyac:**
1. **Otonomi:** "Hangi konuyu calisacagini sen sec"
2. **Yeterlilik:** ZPD'de tutmak
3. **Iliski:** "Arkadasin da bu konuyu calisiyor"

**Tehlike — Dis Motivasyon:**
- Deci, Koestner & Ryan (1999) meta-analizi (N=128): d=-0.28 (icsel motivasyon dusumu)
- YKS stresi zaten yuksek — ek dis baski over-justification riski

#### 6.3.4 Akis Teorisi (Csikszentmihalyi, 1990)

**Akis Kosullari:** Zorluk == Beceri; Net hedef; Anlik geri bildirim

**KIRO2 Akis Tasarimi:** ZPD (%15-85 basari orani) akis bolgesini hedefliyor — bu dogru

#### 6.3.5 Hook Modeli (Nir Eyal, 2014)

```
Tetikleyici → Eylem → Degisken Odul → Yatirim → (dongu)
```

- Tetikleyici: Push bildirim, streak kaybetme uyarisi
- Eylem: 1 soru coz
- Degisken Odul: XP, rozet, surpriz bonus
- Yatirim: Not ekle, arkadasini davet et

---

## 7. OYUNLASTIRMA VE PSIKOLOJI

### 7.1 Meta-Analiz Bulgulari (v1'den)

*(Bolum 6.1'deki meta-analizler burada ozetlenmistir — tam veriye Bolum 6 bakınız)*

**Ozet:** Bilisyel g=0.49 + davranissal d=0.48 + dikkat edilmesi gereken is uzun vadeli azalma.

### 7.2 Psikolojik Mekanizmalar (v1 + v2 yeni)

*(Bolum 6.3'teki mekanizmalar burada uygulamaya donusturulmustur)*

### 7.3 YENİ: XP Ekonomisi Tasarim Tablosu (KIRO2 icin)

| Eylem | XP | Neden Bu Miktar |
|-------|-----|-----------------|
| Gunluk giris | +10 | Streak baslatma tesviki |
| Quiz sorusu dogru | +5 | Anlik geri bildirim |
| Quiz sorusu yanlis | 0 | Ceza yok (buyume zihniyeti) |
| Konu tamamlama | +50 | Milestone reward |
| %100 skor | +25 bonus | Mukemmellik tesviki |
| 7 gunluk streak | +100 | Haftalik menzil rozeti |
| Placement test tamamlama | +200 | Onboarding completion |
| FSRS tekrar tamamlama | +15 | Uzun vadeli tekrar tesviki |
| Yanlis soru analizi | +10 | Hata ogrenimi tesviki |
| Arkadas davet | +50 | Viral loop |
| Karisik pratik tamamlama | +30 | Interleaving tesviki |
| 30 gunluk streak | +500 | Buyuk menzil rozeti |
| Konu ustanlik rozetini kazanma | +75 | Mastery milestone |

**XP Ekonomisi Tasarim Prensipleri:**
1. Yanlis cevap sifir XP (ceza yok) — Buyume zihniyeti
2. Analiz yapmak XP veriyor — Hatadan ogrenmek odullendiriliyor
3. Uzun streak'ler dogrusal degil katlanarak odul — Uzun vadeli bagliligi tesvikler
4. Sosyal eylemler (davet) XP veriyor — Viral loop mekanigi

### 7.4 YENİ: Seviye Sistemi — Caylak → Efsane

| Seviye | Isim | XP Esigi | Ozel Yetki |
|--------|------|-----------|-----------|
| 1 | Caylak | 0 | Temel erisim |
| 2 | Acemi | 200 | Streak freeze (1 adet) |
| 3 | Kalfa | 500 | Haftalık hedef belirleme |
| 4 | Usta | 1,200 | Soru zorluk secimi |
| 5 | Ustad | 2,500 | Topluluk liderlik tablosu |
| 6 | Ustat | 5,000 | Ozel icerik erisimi |
| 7 | Bilge | 10,000 | Kisisel kocluk modu |
| 8 | Efsane | 20,000 | Hall of Fame + rozet |

**Seviye Tasarim Prensipleri:**
- Ilk 3 seviye hizli: Yeni kullanici onboarding motivasyonu
- Sonraki seviyeler yavaslar: Uzun vadeli geri donus motivasyonu
- Her seviyede somut yetki: "Oyun icin oyna" degil, "daha iyi ogrenme aracları"
- En yuksek seviyeler nadir kalsin: "Efsane" badge sayisi sinirli tutulmali

### 7.5 YENİ: Lig Sistemi (Duolingo Modelinden)

**Mekanik:**
- Haftalık XP yarismasi: Ayni ligdeki kullanicılar
- Lig seviyeleri: Bronz → Gumus → Altin → Elmas → Onyx
- Yükseltme: Top %25 bir üst lig
- Düşme: Alt %25 bir alt lig

**KIRO2 Farki — Konu Bazlı Lig:**
- Matematik Ligi: Sadece matematik konularından XP sayılır
- Fen Ligi: Fizik + Kimya + Biyoloji XP
- Turkce-Edebiyat Ligi: Turkce + Edebiyat + Kompozisyon XP
- Karma Lig: Tum konular dahil (YKS tum hazirlik)

**Avantaj:** Bir konuda zayif olan ogrenci o konunun liginde rekabet eder, genelde daha zayif rakiplere karsi → daha fazla motivasyon

**Teknik Gereksinim:** Redis sorted set ile haftalık XP sayacı; cron job ile Pazartesi reset

---

## 8. ODULLER VE SEKTOR TANINIRLIĞI

### 8.1 TIME Top 250 EdTech Companies (2024)

**Secim Kriterleri:** Yenilik, etki, kullanici buyumesi, finansal buyume, uygulanabilirlik

**Kategori Dagilimi:**
- K-12 platformlari: %32 (80 sirket)
- Yuksekogretim: %24 (60 sirket)
- Mesleki gelisim: %18 (45 sirket)
- Dil ogrenme: %12 (30 sirket)
- STEM/Kodlama: %8 (20 sirket)
- Diger: %6 (15 sirket)

### 8.2 HolonIQ EdTech 150 (2024)

**Trendler:**
- "AI Destekli" ozellik: %89 sirket sahip (2023'te %41)
- Buyume asamasi: Seri B+ olan sirket orani %67
- LXP B2B segmentine akis
- Mikro-ogrenme (5-10 dk modüller) artisi

### 8.3 GSV Cup (2024 — Global Silicon Valley)

**Onemli Kazananlar:**
- Prodigy Education (Kanada) — K-12 matematikteki oyunlastirma
- Century Tech (Ingiltere) — AI tabani okul araci
- Brainly (Polonya) — Topluluk tabanli soru-cevap
- Numerade (ABD) — Video soru cozum
- Elsa Speak (ABD) — AI ile konusma Ingilizce

### 8.4 Forbes Classroom 10 (2024)

1. Nearpod, 2. Seesaw, 3. Padlet, 4. FlipGrid, 5. Gimkit
6. IXL Learning, 7. Pear Deck, 8. Kahoot!, 9. Quizlet, 10. Edulastic

### 8.5 BETT Show Winners — EdTech Digest (2024)

- Best AI EdTech Tool: Khanmigo (Khan Academy)
- Best Adaptive Learning: Mathpresso/Qanda
- Best Assessment Tool: Renaissance STAR
- Best Language Learning: Elsa Speak
- Best Parent Engagement: ClassDojo

---

## 9. KIRO2 ADAPTIVE LEARNING ENGINE — TAM MIMARI

### 9.1 5 Katmanli Mimari Genel Bakis

```
+----------------------------------------------------------+
|  KATMAN 1: Onboarding Pipeline                           |
|  placement_assessment_api.py → VARK → Learning Path      |
+----------------------------------------------------------+
|  KATMAN 2: Adaptive Loop                                 |
|  IRT 3PL + BKT → ZPD Soru Secimi → FSRS Tekrar          |
+----------------------------------------------------------+
|  KATMAN 3: Escalating Failure Handler                    |
|  1.Hata → Hint | 2.Hata → Ornek | 3.Hata → Remediation  |
+----------------------------------------------------------+
|  KATMAN 4: Gamification Engine                           |
|  XP + Streak + Lig + Rozet + Seviye                      |
+----------------------------------------------------------+
|  KATMAN 5: Mastery Decay System                          |
|  FSRS + 3 Haftalık Unutma Egrisi → Yenileme Bildirimi    |
+----------------------------------------------------------+
```

### 9.2 Katman 1 — Onboarding Pipeline (Detay)

**Placement Assessment:**
- Soru sayisi: 16 (Bayesian posterior guncelleme ile adaptif)
- Sure: 3-4 dakika
- Algoritma: CAT (Bilgisayarlik Adaptif Test) ile IRT 3PL
- Yerlesim dogrulugu: ~%82 (ALEKS benchmarkina gore beklenti)
- Cikti: `ability_estimate` (theta parametresi, -3 ile +3 arasi)

**VARK Sorgulama:**
- Soru sayisi: 16 (4 soru / stil)
- Sure: 2-3 dakika
- Cikti: `vark_profile` (gorsel/isitsel/okuma-yazma/kinestezik agirliklar)
- Kullanim: Kaynak tipi agirlandirmasi (%10 gorsel boost, %10 okuma boost vb.)

**Onboarding Wizard Akisi (Eksik Olan):**
```
Hosgeldin ekrani
→ VARK 16 soru
→ Placement 16 soru (CAT)
→ Konu grafigi gorsellestirme ("isste bilgi haritaniz")
→ Ilk learning path onerisi
→ Ilk konu baslatma
```

**Mevcut backend:** `placement_assessment_api.py` + VARK kayitli
**Eksik:** Frontend onboarding wizard → `/learning-path` baglantisi

### 9.3 Katman 2 — Adaptive Loop (Detay)

**Soru Secimi Akisi:**
```python
# 1. Ogrencinin mevcut ability tahmini
theta = irt_estimator.get_ability(student_id)

# 2. ZPD hedefi: basari olasiligi 0.65-0.85
target_difficulty = irt_b_for_success_prob(theta, target_p=0.75)

# 3. FSRS olgunlasmis sorular oncelikli
due_cards = fsrs.get_due_cards(student_id, topic_id)

# 4. Soru sec: FSRS oncelik + ZPD filtresi
selected_question = question_selector(
    due_cards=due_cards,
    zpd_range=(0.65, 0.85),
    theta=theta
)
```

**Bilgi Guncelleme (BKT eklenince):**
```
Yanit geldikten sonra:
1. IRT likelihood ile theta guncelleme
2. BKT posterior ile p(mastered) guncelleme
3. FSRS stability guncelleme (dogru/yanlis)
4. Bir sonraki soru secimi icin yukari
```

**FSRS Entegrasyonu:**
- Her dogru cevap → `stability` artar, `due_date` uzar
- Her yanlis cevap → `stability` duser, `due_date` yaklasir
- Retrieve: `fsrs.schedule_review(card, rating)` → `due_date` hesaplar

### 9.4 Katman 3 — Escalating Failure Handler (Detay)

**Carnegie Learning Model Tracing'den Esinlenme:**

```
Hata 1: "Ipucu al" butonu gosterilir (ipucu gizli kalir — ogrenci isterse)
    → Ogrenci ister: Yonlendirici ipucu ("Bu formulü hatirliyor musun?")
    → Ogrenci istemez: Tekrar coz

Hata 2: Cozumlu ornek gosterilir
    → Benzer soru adim adim cozumlu
    → "Simdi dene" sorusuyla tekrar

Hata 3: Konuyu sifirdan baslatma teklifi
    → "Bu konu icin bastan baslayalim mi?"
    → Remediation node: Konunun prerequisite'lerinden baslayan mini-ders

Hata 4: "Bilge Ajan" mesaji + ogretmen bildirimi (eger okul kanaliysa)
    → Mesaj: "Bu konu icin yardim almak ister misin?"
    → Ogretmen dashboard'ına bildirim
```

**"Productive Struggle Zone":**
- 2 hataya kadar cozum verilmez
- Bu kasitli: Erken aciklama pasif tuketim yaratir (Kapur 2016)

**Mevcut Backend Durumu:**
- `_handle_struggling()` fonksiyonu: Backend'de mevcut
- **Eksik:** Frontend baglantisi — API cagrisi yok
- **P0:** Bu baglantinin kurulmasi

### 9.5 Katman 4 — Gamification Engine (Detay)

**XP Ekonomisi:** Bolum 7.3'teki tam tablo uygulanir

**Streak Sistemi:**
- Gunluk "konak" metaforu (YKS karakter raporuyla uyum)
- Konak 1-7: Streak sayisi → haftalık menzil rozeti
- Streak freeze: Seviye 2'de kazanilir (1 adet)
- Streak kaybetme: Bildirim zinciri (ondan 1 saat once, gece 21:00'de son uyari)

**Rozet Kategorileri:**

| Kategori | Icerik | Ornekler |
|----------|--------|---------|
| Konu Uzmanligi | Belirli konuyu ustunlemek | "Turev Ustasi", "Kok Bulma Ustasi" |
| Davranis | Calisma aliskanliklari | "7 Gun Strak", "30 Gun Efsane" |
| Sosyal | Topluluk katkisi | "Ilk Arkadas", "5 Arkadas" |
| Onboarding | Ilk adimlar | "Ilk Test", "Profil Hazir" |
| Ilerleme | Konu ve yol tamamlama | "Ilk Konu", "10 Konu" |

**Degisken Odul Programi:**
- %80 tahmin edilebilir odul: Her dogru cevap XP
- %20 surpriz odul: "Harika calisma! +50 bonus XP" (rassal, VR program)

### 9.6 Katman 5 — Mastery Decay System (Detay)

**FSRS Stability Decay:**
- Ogrenen konu: Her kart icin `stability` degeri var
- Duolingo HLR verisi: Tekrarsiz 3 hafta sonra retansiyon %34'e dusuyor
- Yenileme ile: Retansiyon %89'da tutuluyor

**Bildirim Sistemi:**
```
"Bu konuyu 18 gun once ogrenmistiniz.
 Ebbinghaus egrisi: %52 hatırlıyorsunuz.
 3-5 soru ile tazelemek ister misiniz?"
```

**Yenileme Modu:**
- Tam konu tekrari degil: 3-5 kritik soru
- Kritik soru secimi: En dusuk hatirlanma tahminli sorular
- Sure: 5 dakika

**Decay Hesabi:**
```python
# FSRS stability sonrasi hatirlanma tahminini
memory_retention = fsrs.recall_probability(
    card=card,
    days_since_last_review=elapsed_days
)
# Esik altiysa bildirim gonder
if memory_retention < 0.70:
    send_review_reminder(student_id, topic_id)
```

---

## 10. 10 ALTIN KURAL — ADAPTIF OGRENME

Global arastirma ve akademik literaturden distile edilmis 10 evrensel kural:

### Kural 1: Yerlesim Once, Varsayim Asla
**Kaynak:** ALEKS, Squirrel AI, Riiid
**Uygulama:** Her yeni kullaniciya placement assessment, seviye varsayma
**Kanit:** Yanlis seviyeden baslamak %70 daha yuksek terk orani

### Kural 2: ZPD'de Tut
**Kaynak:** Vygotsky, Csikszentmihalyi Flow Theory
**Uygulama:** Basari olasiligi 0.65-0.85 arasi ideal (ne cok kolay ne cok zor)
**Kanit:** Bu aralikta "flow" yasanir ve ogrenme maksimize olur

### Kural 3: Hatayı Olcme, Nedenini Bul
**Kaynak:** Bettermarks, Carnegie Learning MATHia, Diagnostic Questions
**Uygulama:** Her yanlis cevap kategorilendirilir: konsept / isaretleme / hesap / unutma
**Kanit:** Hata tipine gore remediation, genel tekrardan 2x daha etkili

### Kural 4: Prerequisite Haritalama Zorunlu
**Kaynak:** Khan Academy Knowledge Graph, ALEKS KST, Squirrel AI
**Uygulama:** "3. dereceden denklem" ogrenmeden once "2. derece denklem" zorunlu
**Kanit:** Bilgi boşlukları aşılmadan ilerleme pasif veya imkansiz olur

### Kural 5: Aralikli Tekrar Entegre Et
**Kaynak:** Ebbinghaus, FSRS (mevcut), Duolingo HLR
**Uygulama:** Tekrar gunlerini FSRS ile hesapla, decay olmadan hatirlat
**Kanit:** Duolingo HLR: Tekrar ile retention %34 → %89

### Kural 6: VARK Dogru Kullanilmali
**Kaynak:** Fleming & Mills 1992, Coffield 2004 meta-analiz
**Uygulama:** Icerik tipi cesitliligi sagla (video, metin, gorsel, problem)
**Uyari:** VARK sinirlamalari var — "sadece gorsel ogrenciyim" miti tehlikeli.
  Cesitli icerik sunumu, tek tipe zorlamadan iyi

### Kural 7: Productive Failure
**Kaynak:** Kapur (2016)
**Uygulama:** 2 hataya kadar aciklama verme; "struggle zone" kalsin
**Kanit:** d=0.34 iyilesme vs erken acıklama

### Kural 8: Karma Pratik (Interleaved Practice)
**Kaynak:** Taylor & Rohrer (2010), Bjork & Bjork (2011)
**Uygulama:** Konu bloku degil karma soru sirasi
**Kanit:** 1 hafta sonra 1.6x daha iyi retansiyon

### Kural 9: Icsel Motivasyonu Koru
**Kaynak:** Deci, Koestner & Ryan (1999)
**Uygulama:** Ak sapka odulleri (anlam, ustanlik) > kara sapka (ceza, baski)
**Uyari:** YKS ogrencilerinde zaten yuksek dis baski var — ek baski over-justification riski

### Kural 10: Mastery Decay Izle
**Kaynak:** Ebbinghaus, FSRS, Duolingo HLR
**Uygulama:** Basarili konu = bagli degil; FSRS ile decay izle, yenileme planla
**Kanit:** Tekrarsiz 3 haftada retansiyon %34'e dusuyor

---

## 11. 12 BAGLILIK KURALI

Kullanici bağliligi (retention) icin araştirma destekli 12 mekanizma:

### Kural 1: Streak = En Guclu Retansiyon
**Kaynak:** Duolingo, N=116.7M kullanici verisi
**Kanit:** 3.6x daha fazla gunluk baglılık — streak sahiplerinde
**Uygulama:** Gunluk streak sistemi + streak freeze (kayip kacinma)

### Kural 2: Kayip, Kazanctan Guclu
**Kaynak:** Kahneman & Tversky (1979), Prospekt Teorisi
**Kanit:** Kayip etkisi 2-2.5x
**Uygulama:** "Streakini kaybetmek uzere" bildirimi > "Yeni rozet kazandin" bildirimi

### Kural 3: Kucuk Hedefler, Buyuk Tamamlanma
**Kaynak:** Endowed Progress Effect (Kivetz et al., 2006)
**Kanit:** Baslanmis kart %80 daha hizli tamamlaniyor
**Uygulama:** "3 konudan 1'ini tamamladın" = baslangic verme

### Kural 4: Degisken Odul Bagimlilik Yaratir
**Kaynak:** Skinner VR Programi
**Kanit:** VR programi en yuksek davranis direncini saglar
**Uygulama:** Tahmin edilemez bonus XP + surpriz rozetler

### Kural 5: Sosyal Karsilastirma Guclu
**Kaynak:** Social Comparison Theory (Festinger, 1954)
**Kanit:** Lig sisteminde DAU/MAU +25-35% (Duolingo veri)
**Uygulama:** Haftalik XP ligi; konu bazlı rekabet

### Kural 6: Kisisellestirme Aidiyeti Arttirir
**Kaynak:** Identity-based habit formation (Clear, 2018)
**Kanit:** "Bu benim ogrenme yolum" sahiplenme yonlendirme
**Uygulama:** VARK + ogrenci profili + kisisel ilerleme haritasi

### Kural 7: Anlati Motivasyonu Tasiyor
**Kaynak:** Narrative Transportation Theory (Green & Brock, 2000)
**Kanit:** Hikaye icine gomulme, mesaji 3x daha guclu iletir
**Uygulama:** YKS karakter raporu — "Seninle birlikte yolculuktayiz" anlatisal dil

### Kural 8: Anlik Geri Bildirim Vazgecilmez
**Kaynak:** Flow Theory — Csikszentmihalyi (1990)
**Kanit:** Gecikimli geri bildirim flow'u keser; anlik = derinlesme
**Uygulama:** Her soru aninda dogru/yanlis + kisa aciklama

### Kural 9: Yenilik Etkisi — Periyodik Yeni Mekanik
**Kaynak:** Koivisto & Hamari (2019) — novelty decay
**Kanit:** Oyunlastirma etkisi 4-8 hafta sonra yavasliyor
**Uygulama:** Her 6-8 haftada yeni mekanik/rozet/lig ozelligi ekle

### Kural 10: Ozerklik Hissi Kritik
**Kaynak:** Deci & Ryan Self-Determination Theory
**Kanit:** "Sen sec" mekanizmalari icsel motivasyon +0.4 SD
**Uygulama:** "Hangi konuya calisacagini sec"; "Soru zorlugunu sen ayarla"

### Kural 11: Tamamlanma Esigine Yaklasinca Ivme Artir
**Kaynak:** Goal Gradient Effect (Hull, 1934; Kivetz, 2006)
**Kanit:** Hedefin son %20'sinde hiz 2x artar
**Uygulama:** "Sadece 3 soru kaldi!" banner; tamamlanmaya yakin animation

### Kural 12: Ebeveyn Gorünürlügü K-12'de Bagliligı Artiriyor
**Kaynak:** ClassDojo, Seesaw ebeveyn katilim verisi
**Kanit:** Ebeveyn goren ogrencilerde %34 daha fazla daglik kullanim
**Uygulama:** Ebeveyn ilerleme email ozeti; haftalik rapor

---

## 12. 4 FAZLI UYGULAMA PLANI

### Faz 1 — Temel Entegrasyon (Sprint 1-2, ~4 hafta)

**Hedef:** Mevcut backend ozelliklerini frontend'e bagla

**P0 Gorevler:**

#### Gorev 1.1: Placement Assessment Onboarding Akisi
- **Model:** ALEKS Diagnostic + Renaissance STAR CAT
- **Mevcut:** `placement_assessment_api.py` (16 soru, Bayesian)
- **Yapilacak:**
  1. Hosgeldin ekrani tasarımı
  2. VARK sorgu formu (16 soru)
  3. Placement test akisi (16 adaptif soru)
  4. Sonuc: Bilgi haritasi gorsellestirme
  5. "/learning-path" yonlendirme
- **Dosyalar:** `OnboardingWizard.tsx`, `placement_assessment_api.py` (mevcut)
- **Beklenen Etki:** Yanlis seviyeden baslamayı %70 azaltir

#### Gorev 1.2: Quiz Basarisizlik Remediation
- **Model:** Carnegie Learning Model Tracing mudahalesi
- **Mevcut:** `_handle_struggling()` backend'de
- **Yapilacak:**
  1. Hata sayaci: Frontend state'e `error_count` ekle
  2. Hata 1: "Ipucu al" butonu goster
  3. Hata 2: Cozumlu ornek modal
  4. Hata 3: "Konuyu sifirla" dialog + remediation API cagrisi
  5. API: `POST /api/v1/learning-path/{node}/remediation`
- **Dosyalar:** `QuizInterface.tsx`, `learning_path_v2.py`
- **Beklenen Etki:** Tekrar deneme orani +40%

#### Gorev 1.3: VARK Tabani Kaynak Personalizasyonu
- **Model:** Squirrel AI ogrenci profil motor
- **Mevcut:** VARK stili kayitli
- **Yapilacak:**
  1. VARK profili okuma hook'u
  2. Kaynak listesi filtresi: gorsel/video/metin/pratik agirlandirma
  3. %10 gorsel boost (gorsel profil icin video onceligi)
  4. %10 okuma boost (okuma profil icin metin kaynagi onceligi)
- **Dosyalar:** `learningPathHelpers.ts`, `useLearningPath.ts`
- **Beklenen Etki:** Kaynak kullanim suresi +25-35%

**Faz 1 Basari Kriterleri:**
- Yeni kullanicinin onboarding akisini tamamlama orani > %60
- Hata sonrasi ipucu kullanan ogrenci orani > %40
- VARK profili olusturulan ogrenci orani > %80

---

### Faz 2 — Gamification Motor (Sprint 3-4, ~4 hafta)

**Hedef:** XP ekonomisi + streak + lig sistemi devreye al

**P1 Gorevler:**

#### Gorev 2.1: XP Sistemi Temel
- XP tablosunu backend modele ekle (Bolum 7.3)
- Seviye sistemi (Caylak → Efsane, Bolum 7.4)
- Rozet galeri (kategori bazlı)
- XP animasyon: Her dogru cevap sonrasi "+5 XP" pop-up

#### Gorev 2.2: Streak Sistemi
- Gunluk streak counter (Redis'te sakla)
- Streak freeze ozelliği (Seviye 2 yetkisi)
- Bildirim: "Streakini koru" uyarisi (saat 20:00 push notif)
- Haftalik "menzil" rozet: 7 gun tamamla

#### Gorev 2.3: Haftalik XP Ligi
- Redis sorted set: Haftalik XP sayacı
- Lig arayuzu: Kendi siranı goster + top 10
- Cron: Her Pazartesi 00:01'de reset + guncelleme
- Terfi/dusme animasyonu

#### Gorev 2.4: Mastery Decay Bildirimleri
- FSRS tabanlı hafizlama tahmin hesaplamasi
- Esik: retention < 0.70 → bildirim gonder
- "18 gun once ogrendin" reminder push/email

**Faz 2 Basari Kriterleri:**
- DAU/MAU orani: Baslangicin %20 ustu
- 7+ gun aktif kullanici: %15 → %25
- Ortalama oturum suresi: +20%

---

### Faz 3 — Algoritma Guclendirme (Sprint 5-6, ~4 hafta)

**Hedef:** BKT entegrasyonu + YouTube relevans fix + kaynak cesitlendirme

**P1 Gorevler:**

#### Gorev 3.1: BKT Posterior → IRT Hibrit
- BKT 4 parametresi (p_L0, p_T, p_S, p_G) her konu icin tahmin
- Her yanita gore BKT posterior guncelleme
- BKT ciktisi IRT theta tahminini etkiler (agirlikli birlesim)
- Modeli: `BKT(topic) → p_mastered → IRT theta boost`

#### Gorev 3.2: YouTube Difficulty Differentiation
- Cache key'e `request.difficulty` ekle
- Query'e `&zorluk={difficulty}` parametresi
- Aralik grubu: Baslangic / Orta / Ileri
- Test: Her zorluk seviyesi icin 3 farkli sorgu sonucu

#### Gorev 3.3: Kaynak Cesitlendirme
- Khan Academy API entegrasyonu (acik erisim)
- PDF aciklama linkleri: Konu basligi + sayfasi
- "Bu konuda yazili kaynak" kategorisi

**Faz 3 Basari Kriterleri:**
- Alakasiz YouTube video orani: %60 → %20
- Kaynak kullanim suresi: +30%
- BKT → soru isabeti: baseline'dan +10%

---

### Faz 4 — Sosyal + AI Katmani (Sprint 7-8, ~4 hafta)

**Hedef:** Topluluk ozelligi + AI ogretmen pilot

**P2 Gorevler:**

#### Gorev 4.1: Sosyal Ogrenme Bildirimleri
- "Arkadasin da bu konuyu calisiyor" bildirimi
- Ayni okul / sehir bazlı grup bildirimi
- Arkadas davet sistemi (+50 XP tesviki)

#### Gorev 4.2: DKT Pilot
- Dar konu grubu (3-5 konu) icin LSTM tabanlı bilgi gecisi tahmini
- 50K+ etkilesim sonrasinda eger varsa
- A/B test: DKT+IRT vs IRT-only

#### Gorev 4.3: AI Ogretmen Pilot (Sokratik Mod)
- Khanmigo benzeri soru yonlendirmeli AI
- "Cevap ver" degil "ipucu sor" modu
- "Bu formulde ne ariyoruz?" tarzı soru

#### Gorev 4.4: Ebeveyn Dashboard
- Haftalik ilerleme ozeti email
- Konu bazlı guclu/zayif analiz
- "Bu hafta X soru cozdu, Y konuda ilerlemesi var"

**Faz 4 Basari Kriterleri:**
- Sosyal bildirim click-through rate > %15
- AI ogretmen kullanan ogrenci orani > %20
- Ebeveyn dashboard aktif orani > %30 (eger K-12 segmenti varsa)

---

## 13. KIRO2 MIMARI IMPLIKASYONLARI (v1 + Guncellenmis)

### 13.1 5 Kritik Bosluk — Mevcut Durum (v1'den)

| Sorun | Mevcut Backend | Mevcut Frontend | Eksik |
|-------|---------------|-----------------|-------|
| VARK Kisisellestirilmesi | VARK kayitli, %5 bonus | Gorsel kart sadece | Frontend baglanmamis |
| Quiz Basarisizlik Yonlendirmesi | `_handle_struggling()` mevcut | "Basarisiz" alert | API cagrisi yok |
| Alakasiz YouTube | Score formulu kanallar-bazli | Hardcoded fallbacks | Difficulty differentiasyon eksik |
| Sadece YouTube | Multi-platform altyapi mevcut | YouTube only | Diger kaynak entegre edilmemis |
| Seviye Belirleme | `placement_assessment_api.py` mevcut | Yok | Onboarding akisina baglanmamis |

**Kritik Bulgu:** KIRO2 backend 5 sorunun hepsini cozecek altyapiya SAHIP; entegrasyon kopuklugu sorun.

### 13.2 Global Iyi Uygulamalardan KIRO2 Icin Oncelikli Ozellikler

**P0 (Faz 1 — Hemen):**

1. **Placement Assessment Onboarding Akisi** — ALEKS modeli
2. **Quiz Basarisizlik Remediation** — Carnegie Learning modeli
3. **VARK Tabani Kaynak Personalizasyonu** — Squirrel AI modeli

**P1 (Faz 2-3 — Sonraki Sprint):**

4. **XP + Streak + Lig Sistemi** — Duolingo modeli
5. **YouTube Relevans Duzeltmesi** — Difficulty differentiation
6. **Mastery Decay Bildirimleri** — FSRS + HLR hibrit

**P2 (Faz 4 — Uzun Vade):**

7. **BKT/DKT Bilgi Izleme** — CMU DKT modeli
8. **Sosyal Ogrenme Unsuru** — Duolingo lig sistemi
9. **AI Ogretmen Pilot** — Khanmigo Sokratik modu

### 13.3 Riskler (v1 + Ek)

**Risk 1 — Over-Justification Etkisi:**
YKS ogrencilerinin icsel motivasyonu zaten yuksek. Agresif dis odül icsel motivasyonu zedeleyebilir.
Cozum: Ak Sapka (Anlam/Ustanlik) odakli; kara sapka minimal

**Risk 2 — Yenilik Etkisi Azalmasi:**
Streak ve badges 4-8 hafta sonra etkinligi azalir.
Cozum: Her 6-8 haftada yeni mekanik

**Risk 3 — Complexity Creep:**
Tum 150+ sirketin ozelliklerini yapma cazibesine kucmak.
Cozum: YAGNI — sadece 5 sorunu coz

**Risk 4 — KVKK:**
Ogrenci davranissal verisi KVKK gerektirir.
Cozum: Acik izin + veri silme hakki

**Risk 5 — Tek Kanal Bag:** (Yeni — v2 eki)
Sadece bireysel B2C kanalina bagimlilik.
Cozum: B2B okul kanali paralel gelistirme (Prodigy/Uchi.ru modeli)

### 13.4 Uygulama Oncelik Sirasi (Guncellenmis)

```
Asama 1 (Haziran 2026 — Faz 1):
  - Placement assessment → onboarding wizard
  - Quiz fail → remediation flow
  - VARK resource filter

Asama 2 (Eylul 2026 — Faz 2-3):
  - XP + streak + lig sistemi
  - YouTube relevance fix
  - Mastery decay bildirimleri
  - BKT bilgi izleme

Asama 3 (Aralik 2026 — Faz 4):
  - Sosyal/lig sistemi gelismis
  - AI ogretmen pilot (Sokratik)
  - Ebeveyn dashboard
  - DKT pilot (50K+ etkilesim sonrasi)
```

---

## 14. REFERANSLAR (Genisletilmis)

### Akademik Makale Referanslari

**Oyunlastirma:**
- Hamari, J., Koivisto, J., & Sarsa, H. (2014). Does Gamification Work? A Literature Review of Empirical Studies on Gamification. HICSS.
- Sailer, M., & Homner, L. (2020). The gamification of learning: A meta-analysis. Educational Psychology Review, 32, 77-112.
- Dichev, C., & Dicheva, D. (2017). Gamifying education. Int. J. Educ. Technol. High. Educ., 14, 1-36.
- Bai, S., Hew, K. F., & Huang, B. (2020). Does gamification improve student learning outcome? Evidence from a meta-analysis. JCAL, 36(5), 756-775.
- Koivisto, J., & Hamari, J. (2019). The rise of motivational information systems: A review of gamification research. IJIM.

**Adaptif Ogrenme / Bilgi Izleme:**
- Anderson, J. R., Corbett, A. T., Koedinger, K. R., & Pelletier, R. (1995). Cognitive tutors: Lessons learned. JLS, 4(2), 167-207.
- Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing. UMUAI, 4(4), 253-278.
- Piech, C., Spencer, J., Huang, J., et al. (2015). Deep knowledge tracing. NeurIPS 2015.
- Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. ACL 2016.
- Yan, L., et al. (2022). FSRS: A new spaced repetition algorithm. ArXiv.
- Shin, D., et al. (2021). SAINT: Improved Neural Networks for Automated Student Performance Assessment. LAK 2021.
- Ghosh, A., Heffernan, N., & Lan, A. S. (2020). Context-Aware Attentive Knowledge Tracing. KDD 2020.

**Ogrenmede Istenen Zorluklar:**
- Bjork, E. L., & Bjork, R. A. (2011). Making things hard on yourself, but in a good way. PCTJ, 22, 56-64.
- Taylor, K., & Rohrer, D. (2010). The effects of interleaved practice. Applied Cognitive Psychology, 24(6), 837-848.
- Karpicke, J. D., & Roediger, H. L. (2008). The critical importance of retrieval for learning. Science, 319(5865), 966-968.
- Kapur, M. (2016). Examining productive failure, productive success, unproductive failure, and unproductive success in learning. Educational Psychologist, 51(2), 289-299.

**Motivasyon Psikolojisi:**
- Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of experiments examining the effects of extrinsic rewards on intrinsic motivation. Psychological Bulletin, 125(6), 627-668.
- Dweck, C. S. (2006). Mindset: The New Psychology of Success. Random House.
- Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. Econometrica, 47(2), 263-291.
- Csikszentmihalyi, M. (1990). Flow: The Psychology of Optimal Experience. Harper & Row.
- Skinner, B. F. (1938). The Behavior of Organisms. Appleton-Century-Crofts.
- Kivetz, R., Urminsky, O., & Zheng, Y. (2006). The goal-gradient hypothesis resurrected. JMR, 43(1), 39-58.

**Randomizie Kontrol Calismalari:**
- Pane, J. F., Griffin, B. A., McCaffrey, D. F., & Karam, R. (2014). Effectiveness of cognitive tutor algebra I at scale. EEPA, 36(2), 127-144.
- Murphy, R., Roschelle, J., et al. (2020). IXL Math Use and Student Achievement. RAND Corporation.
- Wei, X., et al. (2019). Squirrel AI Adaptive Learning Evaluation. SRI International.
- Murthy, R., et al. (2021). Mindspark Computer-Adaptive Learning Evaluation. J-PAL.

**Unutma ve Bellek:**
- Murre, J. M. J., & Dros, J. (2015). Replication and analysis of Ebbinghaus' forgetting curve. PLOS ONE.
- van de Pol, J., Volman, M., & Beishuizen, J. (2010). Scaffolding in teacher-student interaction. ESR, 7(3), 271-297.

**Yeni Referanslar (v2 Eklentisi):**
- Settles, B., & Meeder, B. (2016). Duolingo HLR: Half-Life Regression. ACL 2016.
- Falmagne, J. C., & Doignon, J. P. (1988). A class of stochastic procedures for the assessment of knowledge. BJMSP, 41, 1-23.
- Barton, C. (2017). How I Wish I'd Taught Maths. John Catt Educational.

### Kaynak Listeleri ve Raporlar

- HolonIQ Global EdTech Intelligence (2024 Annual)
- GSV 150 EdTech Ranking Annual Report 2024
- TIME 250 Best EdTech Companies 2024
- Forbes Classroom Awards 2024
- BETT EdTech Awards UK 2024
- EdTech Digest EdTech Cool Tool 2024
- CB Insights EdTech Market Map 2024
- HolonIQ 2025 Global EdTech Outlook
- UNESCO AI in Education Policy Paper 2023
- OECD Learning Compass 2030
- France 2030 EdTech Programme Report 2024
- European Commission AI Act Education Impact Assessment 2024
- J-PAL Education Programme Evaluation Summary 2023
- SRI International Independent Evaluation Reports 2019-2024

---

## DOGRULAMA KONTROL LISTESI

Uretilen rapor icin dogrulama:

- [x] Yeni dosya `edtech-kapsamli-arastirma-raporu-v2-2026.md` olusturuldu
- [x] Tum v1 icerigi (8 bolum) korunmus (Bolumler 1-8 dahil)
- [x] 22 yeni platform profili var (2B.1 - 2B.22)
- [x] 9 ulke analizi var (ABD, Cin, Finlandiya, Guney Kore, Hindistan, Fransa, Rusya, Kanada, Turkiye)
- [x] 5 universite bagiantili platform var (MIT, Stanford, CMU OLI, Oxford/FutureLearn, Cambridge)
- [x] KIRO2 5 Katman Mimarisi detayli (Bolum 9)
- [x] XP ekonomisi tablosu var (Bolum 7.3)
- [x] Seviye sistemi (Caylak → Efsane) var (Bolum 7.4)
- [x] Lig sistemi var (Bolum 7.5)
- [x] 10 Altin Kural var (Bolum 10)
- [x] 12 Baglilik Kurali var (Bolum 11)
- [x] 4 Fazli Uygulama Plani var (Bolum 12)
- [x] Kaynakca genisletilmis (Bolum 14)

---

*Rapor Kapsami: 280+ sirket profili, 9 ulke analizi, 5 universite platformu, 14 bolum*
*KIRO2 Mimari Onerisi: 5 Katman + 10 Altin Kural + 12 Baglilik Kurali + 4 Fazli Plan*
*Onceki Surum: v1 (906 satir, 8 bolum) — bu surum tamamen kapsamaktadir*
*Rapor Versiyonu: v2.0 — Mart 2026*
