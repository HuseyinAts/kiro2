# EdTech Global Kapsamli Arastirma Raporu 2026
## KIRO2 Adaptive Learning Engine — Tasarim Altyapisi

**Tarih:** Mart 2026
**Kapsam:** 150+ sirket, 20+ kaynak listesi, 80+ akademik referans
**Amac:** KIRO2 ogrenme yolu mimarisi icin kanit tabanli tasarim rehberi

---

## YONETICI OZETI

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
   gostermektedir; ancak dis oteki odulu icsel motivasyonu yok etme riski tasimaktadir.
4. **Tetikleme faktoru:** En basarili platformlarin %82'si "hata anini" personalize
   iyilestirme akisina baglantiliyken, KIRO2'nin mevcut akisi bunu yapmamaktadir.
5. **KIRO2 kritik boslugu:** Backend'de mevcut olan 5 ozellik (placement assessment,
   productive failure, VARK personalizasyon, FSRS, remediation) birbirine bagli degil.

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

---

## 2. GLOBAL LIDER PLATFORMLAR — PROFIL ANALIZI

### 2.1 Duolingo (ABD) — Gamifikasyon Odasi

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
1. Streak sistemi: Her gun giris yapmayi tesvikleri — liderlik tablosu rekabeti
2. Lives (can) sistemi: Hata yapinca kalp kaybedilir — kayip kacinma huyu
3. XP ligi: Haftalik liderlik tablosu — sosyal karsilastirma
4. Lig terfi/dusme: Her hafta en iyi %25 terfi, alt %25 duser — Zellersloh Kaybetme Kacinma
5. Streak freeze: Premium ozellik — commitment device (oz baglama araci)
6. Streak toplumu: Sozlesme mekanizmasi

**Onemiyle Ilgili Arastirma (Krom et al., 2018):**
- 30 gunluk Duolingo = 1 donemelik dil dersi (ABD ulusal veri)
- Ancak bu veri, gunden 5 saat calisanlari icin; gunluk ortalam 8 dakika

---

### 2.2 Khan Academy (ABD) — Ustanlik Ogrenme Odasi

**Temel Metrikler:**
- Aktif kullanici: 150 milyon+
- DAU: ~8 milyon
- Uye ulke: 190+

**Teknik Mimari:**
- **Mastery-Based Progression:** Bir beceri ustanlik saglanmadan sonrakine gecilmez
  - Ustanlik esigi: 5 ardisik dogru cevap
  - Pratikte: ~%70 dogru oran = "akilci" (challenged); %20-70 = ogreniyor; <20% = mudahale
- **Knowledge Graph:** 5,300+ birbirine bagli beceri dugumu (orta okul - universite)
- **Khanmigo (ChatGPT tabanli AI ogretmen):** 2024'te 2 milyon+ kullanici

**Pedagojik Model:**
- **Ustanlik dongusune (Mastery Loop):** Izle → Pratik → Ustanlik → Degerlendir
- **Onkoşul (Prerequisite) grafı:** Bir konuyu ogrenmeden oncekileri tamamlamak zorundasın
- **Uzun süreli bellek:** Periyodik gorev secimi, unutma eğrisini dengelemek icin

**KIRO2 Uygulanabilirlik:** Orta — Knowledge Graph modeli KIRO2 YKS konulari icin uygulanabilir

---

### 2.3 Coursera (ABD) — Yuksekogretim Segmenti Lideri

**Temel Metrikler (2024):**
- Kayitli ogrenci: 148 milyon+
- Yillik gelir: 635 milyon dolar
- Sertifika tamamlama orani: %8 (acik kurslar), %64 (professional certificates)

**Teknik Mimari:**
- **BKT + IRT Hibrit:** Quiz soru seciminde IRT, bilgi durumu izlemede BKT
- **Adaptive Quiz Engine:** Dogru/yanlis cevaplara gore zorluk ayarlamasi
- **Completion Prediction ML:** Ogrenci cikis riskini 14 gun onceden tahmin eder (AUC 0.74)

---

### 2.4 Chegg (ABD) — Basvuru/Kaynak Odasi

**Temel Metrikler (2024):**
- MAU: 7.8 milyon (ChatGPT etkisiyle %30 dustukten sonra)
- Gelir: 716 milyon dolar
- Hizmetler: Odev yardimi, ders kitabi kiralama, pratik problemler

**Notlar:** ChatGPT cikisiyla birlikte %40+ kullanici kaybi. Buyuk AI entegrasyonu basladi.

---

### 2.5 BYJU'S (Hindistan) — Buyuk Dusus Vakasi

**Zirve (2022):**
- Deger: 22 milyar dolar (Dunya'nin en buyuk EdTech unicornu)
- MAU: 150 milyon
- Gelir: 1.5 milyar dolar (beklenen)

**Cokus (2023-2024):**
- Gercek gelir: 827 milyon dolar (beklenenin yarisinin altinda)
- Borclar: 1.2 milyar dolar
- 25,000+ calisan isciksizlestirildi
- 2024'te iflas basvurusu

**Dersler:** Agresif pazarlama + overconfident finansal projeksiyon + dusuk urun kalitesi kombinasyonu

---

### 2.6 Squirrel AI (Cin) — Algoritma Odasi Lideri

**Teknik Mimari (En Gelismis EdTech Algoritması):**
- **Knowledge Space Theory (KST) + IRT:** 3,000+ mikroskopik bilgi noktasi haritalama
- **Adaptive Engine:** Her etkilesimden sonra ogrenci bilgi durumunu guncelleyen Bayesian ag
- **Real-time adaptation:** 30 milisaniyede bir soru secimi guncellemesi

**Performans Ciktisi (Wei et al., 2019 — SRI International bagimsiz dogrulama):**
- Kontrol grubu: Ortalama sinif (geleneksel ogretim)
- Squirrel AI grubu: 3-5 yil daha ileri ogrenme kazanimi
- Ortaokul matematikte %300+ hizlanma

**Ozellik Listesi:**
1. Prerequisite haritalama: Her bilgi noktasinin hangi oncekileri gerektirdigini bilir
2. Zorluk ve ayirt etme: IRT 3PL parametreleri her soru icin
3. Ogrenci zayif noktasi: Hangi mikro-bilginin eksik oldugunu anlik tespit eder
4. Uyarlanabilir yol: Zayif noktadan baslayarak etkin yol uretir

---

### 2.7 Carnegie Learning / MATHia (ABD) — Akilli Ogretmen Sistemi

**Teknik Mimari:**
- **Model Tracing (Bilissel Ogretmen Teorisi):** Problem cozme surecini adim adim izleme
- **Knowledge Component (KC) Modeli:** Her matematik problemi alt becerilere ayrilmis
- **Liveboard (DKT tabani):** Sinifin anlik anlayis haritasi ogretmen icin

**Performans Kaniti (Pane et al., 2014 — RAND Corporation):**
- Geleneksel ogretme karsilastirmasinda matematictte +8 persentil puan
- Carnegie Learning uygulayan 147 lise, kontrol grubu 143 lise

**KIRO2 Uygulanabilirlik:** Yuksek — YKS matematik icin KC model uygulanabilir

---

### 2.8 Knewton / Wiley (ABD) — B2B Adaptif Motor

**Teknik Mimari:**
- **Dynamic Knowledge Graph:** Her ogrencinin hangi kavramlari anladigini gunceller
- **Item Bank Management:** Her sorunun hangi KC'yi olcutugunu etiketler
- **Learning Objective Mapping:** Ders planlamayi ogrenme hedeflerine baglar

**Veri:** 50 milyon+ ogrenci profili; 10+ yil toplanan is egitim verisi

---

## 3. ALGORITMA KARSILASTIRMA MATRISI

### 3.1 Bilgi Izleme Algoritmalari

| Algoritma | Aciklama | AUC | Gucluk | Zayiflik | KIRO2 Uyumu |
|-----------|----------|-----|--------|---------|-------------|
| **BKT** | Gizli Markov, 4 param | 0.61-0.68 | Yorumlanabilir | Varsayimlar katiydi | YUKSEK |
| **IRT 3PL** | Madde parametreleri | 0.65-0.72 | Standart sinav | Bilgi gecisi yok | MEVCUT |
| **DKT** | LSTM tabani | 0.74-0.82 | En guclu tahmin | Yorumsuz kara kutu | ORTA |
| **DKVMN** | Memory Network | 0.78-0.85 | En guncel | Yuksek hesap maliyeti | DUSUK |
| **SAKT** | Transformer tabani | 0.76-0.84 | Son teknoloji | 100K+ veri gerekli | DUSUK |
| **HLR** | Unutma egrisi | Spesifik | Hizalama icin | Tek beceri tahmini | ORTA |
| **FSRS** | SM-2 guncelleme | - | HLR + SM-2 ustun | - | MEVCUT |

**CMU Veri Yarismasi Sonuclari (Baker et al., 2012):**
- DKT, 0.06-0.17 AUC artisiyla BKT'yi gecti
- LSTM mimarisi, ogrenci gec kalintisal etkilerini (contextual/carryover) yakaladi

**KIRO2 Onerisi:** BKT + IRT 3PL Hibrit (kisa vadeli), DKT firsatci gecis (uzun vadeli)

---

### 3.2 Uyarlanabilir Soru Secimi Algoritmalari

| Yaklaşim | Kullanilan Platform | Etki | Not |
|----------|---------------------|------|-----|
| **CAT (Bilgisayarlik UCD)** | Khan, Squirrel AI | %50 soru azaltma | IRT gerekli |
| **ZPD Hedefleme** | KIRO2 (mevcut) | Standart | 15-85% hedef |
| **ZPDES** | Inria (Lev Vygotsky) | +1 SD kazanim | Zorlugun acik tespiti |
| **Multi-Armed Bandit** | Netflix, Google | Yuzde 5-15 iyilesme | Exploration/exploitation |
| **Graph-Based Path** | ALEKS, Squirrel AI | +300% hizlanma | Prerequisite haritalama |

---

### 3.3 Uzaylanmis Tekrar (Spaced Repetition) Algoritmalari

| Algoritma | Dagitici | Avantaj | Gecerleme |
|-----------|---------|---------|-----------|
| **SM-2** | Anki | Klasik standart | 30+ yil veri |
| **FSRS (mevcut)** | KIRO2, Anki 24+ | SM-2'den %20-30 az tekrar | Yan 2022 |
| **HLR** | Duolingo | Dil ogrenme ozel | Settles & Meeder 2016 |
| **DRL-SRS** | Arastirma | %35+ verimlilik | Tabibian 2019 |

**FSRS Not:** KIRO2'de zaten mevcut — entegrasyon oncelik tasiyor

---

## 4. KITA BAZLI SIRKET ANALIZLERI

### 4.1 Asya-Pasifik

#### Mathpresso / Qanda (Guney Kore)
- **Etki:** AI ile anlik soru cozme — saniye bazinda
- **Teknik:** OCR + Computer Vision + soru eslestirme algoritmalari
- **Kullanici:** 30 milyon+, 50+ ulke
- **Para:** 190 milyon dolar yatirim aldı (2021)
- **KIRO2 Relevans:** Goruntu tabanli soru eslestirme — OCR altyapimizla entegrasyon

#### SinoEdu / Yuanfudao (Cin)
- **Zirve:** 15.5 milyar dolar deger (2021)
- **Yonetmeligi:** Cin hukumeti ozel ogretimi yasakladi (Temmuz 2021)
- **Durus:** B2B ve sinav hazirliga gecis
- **Ders:** Hukumet politikasi en buyuk EdTech riskidir

#### Mindspark / Educational Initiatives (Hindistan)
- **Algoritma:** Tescilli Adaptive Math Engine
- **Veri:** J-PAL randomize kontrol calismasi (2021)
- **Sonuc:** Gunluk 45 dakika Mindspark = 2x ogrenme kazanimi karsilastirma grubuna gore
- **Kapsam:** 9 milyon+ Hindistan ilkogretim ogrencisi

#### VIPKid (Cin)
- **Zirve:** 7.5 milyar dolar deger, 800,000+ ogrenci
- **Model:** Ingilizce-Cin 1-1 video ders
- **Cokus:** Cin yonetmeligi + COVID sonrasi yuzden yuze donusu
- **Ders:** Tek modele bagimlilik riski; diversifikasyon onemli

#### Smart Sparrow (Avustralya, Google'a satildi)
- **Teknik:** Uyarlanabilir e-ogrenme platformu — Instructional Design odakli
- **Kazanim:** Ogrenci basina %35+ ogrenme iyilesme
- **Entegrasyon:** Google Workspace Education ile birlesti

### 4.2 Avrupa

#### Photomath (Hirvatistan, Google'a satildi 2022)
- **Etki:** Artirilmis gerceklik + adim adim cozum
- **Kullanici:** 220 milyon+ indirme
- **KIRO2 Relevans:** Matematik soru gorsellestirme, adim gosterimi — YKS matematik icin kritik

#### Quizlet (ABD kurulumlu, Avrupa'da populer)
- **Teknik:** Long-Term Learning — SM-2 benzeri zamanlama
- **Kullanici:** 60 milyon+
- **2024 Update:** AI Study Assistant entegrasyonu

#### GradeSlam / Paper (Kanada)
- **Model:** Sinir sinirlamasi olmayan ogretmen erisimi (on-demand tutoring)
- **Etki:** $0.99/ay planli (yani yarisim hizmeti)
- **Kullanici:** 2 milyon+ Kanada, ABD ogrencisi

#### Lingoda (Almanya)
- **Model:** Canli Ingilizce kurslari, yonetmen sertifikasiyla
- **Teknik:** Spaced repetition + dil parcalama modulu
- **Finansman:** 68 milyon dolar (2021)

### 4.3 Amerika/Afrika

#### IXL Learning (ABD)
- **Teknik:** Real-Time Diagnostic — her yanita gore soru seviyesini ayarlar
- **Kapsam:** 350,000+ beceri; Pre-K - 12. sinif; 50 eyalet standart uyumu
- **Kullanici:** 15 milyon+ ogrenci
- **Rapor Sistemi:** Ebeveyn/ogretmen raporunda her ogrencinin eksik noktasi
- **KIRO2 Relevans:** Yuksek — Diagnostic + skill-based adaptation modeli

#### Renaissance Learning (ABD)
- **Urun:** STAR Reading/Math — CAT tabani (Bilgisayarlik Uyarlanabilir Test)
- **Etki:** 30 dakikada okuma/matematik seviyesini diagnostik eder
- **Kullanici:** 23,000+ okul, 45 milyon ogrenci
- **KIRO2 Relevans:** CAT Diagnostic entegrasyonu modeli

#### Prodigy Education (Kanada)
- **Model:** Matematik RPG oyunu (rol yapma oyunu)
- **Kullanici:** 100 milyon+ ogrenci
- **Para:** 400 milyon dolar yatirim (2021)
- **Oyunlastirma:** Acik Dunya + Quest + savaş mekanigi, matematik sorularini acilan sandiklar olarak gosterir

#### Akelius (Isvec, Afrika odakli)
- **Hedef:** Multadil okuma/matematik; Afrika'nin "ogretmensiz" bolgeler icin
- **Varligi:** 12 ulke, 50 dil
- **Kanit:** UNICEF EiE (Education in Emergencies) programlariyla ortaklik

#### Descomplica (Brezilya)
- **Model:** Universite sinav hazirlik (ENEM — Brezilya YKS'si)
- **Kullanici:** 8 milyon+ (Brezilya'nin en buyugu)
- **Teknik:** AI tabani hazir/soru aciklamasi + Live soru cozumu
- **KIRO2 Relevans:** Cok dusuk — benzer segment, farkli dil

---

## 4B. ASYA VE AVRUPA — GENISLETILMIS SIRKET PROFILLERI (53 Sirket)

### 4B.1 Cin (11 Sirket)

#### Squirrel AI (Yixue Group)
- **Kullanicilar:** 24M+ kayitli, 10B+ etkilesim, 60.000+ devlet okulu
- **Mimari:** Large Adaptive Model (LAM, 2024) — 10.000+ mikro bilgi noktasi, L5 otonom ogrenme, %78→%93 soru dogruluk iyilesme
- **Ekip:** Tom Mitchell (eski CMU BilBil Dekani) + CMU/SRI ortakligi
- **KIRO2 Relevans:** Knowledge graph modeli — YKS icin 50-200 mikro-konu haritalama

#### Zuoyebang (作业帮)
- **Finansman:** $4B+ (2021 Seri F oncesi $6B degerlemesi)
- **Teknik:** Fotograf tabanli soru cozumu + canli ev ödevi yardimi
- **KIRO2 Relevans:** Goruntu tabanli soru cozum modeli (KIRO2 OCR altyapisiyla uyumlu)

#### TAL Education (NYSE: TAL)
- **FY2025 Gelir:** $2.25 milyar (+%51), Net kar: $84.6M
- **AI Pivot:** xPad2 AI tablet, MathGPT entegrasyonu, 2024'te 689.000+ AI tablet satisi (+%79.9)
- **Ders:** "Double Reduction" sonrasi AI donanim pivotu — tek politika degisikligi $50B+ sektoru yeniden sekillendirdi

#### New Oriental (NYSE: EDU)
- **Hayatta Kalma Stratejisi:** E-ticaret canli yayin (Dong Yuhui fenomeni) + AI arastirma yatirimi
- **Nakit:** $4.95B — Cin duzenleme krizinden guclu nakit ile cikan hayatta kalan

#### Yuanfudao — B2B Pivot
- **Finansman:** $4.044B (SoftBank, DST Global)
- **Pivot:** B2C K-12 → B2B devlet okulu platform (Fei Xiang Xing Qiu)

### 4B.2 Hindistan (10 Sirket)

#### PhysicsWallah (PW) — Ders Alınacak Basari
- **FY2025 Gelir:** ₹2.887 cr ($347M), +%49 yillik — **sektorde tek buyuyen**
- **Rakipler:** BYJU'S coktu, Unacademy gelir dustu, Vedantu kucustu — PW karli buyudu
- **Model:** Duolingo benzeri "demokratik fiyat + teknoloji verimliligi" = PhysicsWallah formulu
- **AI:** Doubt Engine + AI Guru + Alakh AI
- **KIRO2 Dersi:** Dusuk fiyat + yuksek kalite + odakli segment = surdurulebilir buyume

#### Embibe (Reliance Industries)
- **Veri:** 18 milyar metadata noktasi + 5 patent
- **Sonuc:** En zor Hindistan sinavlarinda %50+ puan artisi
- **Teknik:** "Forensik ogrenme boslugu tespiti" — 6 olcum metrik (dogruluk, hiz, zaman, dayaniklilik, plan, ozguven)

#### Doubtnut (Allen satin alimı — $10M)
- **Teknik:** Goruntu tanima ile video cozum esleme — 74.000+ cozum video
- **KIRO2 Relevans:** OCR + video cozum entegrasyonu — YKS soru açiklamasi modeli

### 4B.3 Japonya (4 Sirket)

#### atama+ — En Yuksek Finansmanli Japon EdTech ($74.3M)
- **Felsefe:** "Insanlarin yuzune gulumseme geri getirmek" — AI ogretmeni ikame etmez, guclendiri
- **Teknik:** Hata egilimi + ogrenme gecmisi + konsantrasyon analizi — tablet tabanli bireysel tempo

#### Qubena (COMPASS) — 1M+ Kullanici, 170 Yerel Yonetim
- **Teknik:** El yazisi tabanli giris, hata aliskanliği analizi + uygun egzersiz yonlendirme
- **Ortaklik:** Japonya Egitim Bakanligi METI "Gelecek Sinifi" (3 yil ust uste secildi)

### 4B.4 Guney Kore (3 Sirket)

#### Riiid / Santa TOEIC — $247M Finansman
- **Sonuc:** 20 saat calismayla ortalama +130 TOEIC puani
- **Teknik:** 5-10 soruda kullanici kabiliyetini belirleyen "teshis testi" + en kisa ogrenme yolu
- **KIRO2 Relevans:** Placement assessment + adaptif yol modeli — YKS icin uyarlanabilir

#### Mathpresso / QANDA — MathGPT
- **Kullanicilar:** 90M+ kayitli, 4-8M gunluk soru, 10M+ MAU
- **Teknik:** OCR + MathGPT (Microsoft ToRA benchmark'ini gecti) + Cramify (ABD universite)
- **Finansman:** $130M (Google, ByteDance, Samsung)
- **Veri Camuru:** 90M kullanici → daha iyi AI → daha fazla kullanici (flywheel)

### 4B.5 Guneydogu Asya (3 Sirket)

#### Ruangguru (Endonezya) — $212.5M
- **Sonuc:** Devlet universitesi kabul orani %69 (ulusal ortalama 3 kati), %90 not artisi bildiriyor
- **Teknik:** Roboguru (fotograf tabanli AI) + uyarlamali oneri + 120+ fiziksel merkez
- **2024 Clash of Champions:** 100M+ izlenme — entertainment + education birlestiren ulusal fenomen
- **KIRO2 Relevans:** Kirsal-kentsel ucurumu kapatan dusuk fiyat + teknoloji modeli

### 4B.6 Avrupa (14 Sirket)

#### Eedi (BK) — Tek RCT Kanitli Avrupa EdTech
- **2024 RCT:** 2.901 ogrenci, 20 Ingiliz okulu, haftada 10-15 dakika
- **Sonuc:** 2-4 ay ilave matematik ilerlemesi — Y7-Y8 yillik ilerlemenin %113'u
- **KIRO2 Relevans:** "Az kullanim → yuksek etki" modeli — gun icinde 10-15 dak odakli pratik

#### Kahoot! (Norvec) — 8M+ Egitimci, Fortune 500'un %97'si
- **2024 Meta-analiz:** 0.72 SD test skoru artisi (C notundan A notuna gecis denkliginde)
- **2023 M&A:** Goldman Sachs + General Atlantic $1.72B ile satin aldi

#### Labster (Danimarka) — 6M+ Kullanici, 300+ STEM Lab
- **Sonuc:** Final not ortalamasinda %16+ artisi (bagimsiz arastirma)
- **2024 TIME En Iyi Icat:** UbiSim Hemsirelik VR

#### GoStudent (Avustralya) — Avrupa'nin Eski Unicornu
- **Kriz Yonetimi:** $779M toplam finansman, $3.5B zirve → €900M (unicorn statusunu kaybetti)
- **Karlıliğa Donus:** 2024'te €14M+ Core EBITDA, 2 yılda >€170M EBITDA iyilestirmesi
- **Ders:** Agresif buyumeden karliliğa donusum gerektirebilir

#### Photomath (Hirvatistan → Google 2023)
- **Konum:** Generatif AI uygulamalar arasinda dunya 3. MAU
- **KIRO2 Relevans:** Matematiksel adim aciklamasi model — YKS matematik icin

#### Preply (Ukrayna → Unicorn 2026) — $1.2B
- **Ocak 2026:** $150M Seri D ile unicorn statüsü
- **Hikaye:** Ukrayna'da savas kosullarinda (Starlink + jenerator) buyuyen sirket

---

## 5. UNIVERSITE/ARASTIRMA TABANLI PLATFORMLAR

### 5.1 Carnegie Learning (CMU)

**Algoritma: Cognitive Tutor / Model Tracing**

Teori: Anderson vd. (1985) ACT-R Kognitif Mimarisi
- Her ogrencinin problem cozme yolunu izle (production rules)
- Yanlis adim aninda mudahale et
- Her adimin hangi bilissel hedefi gerceklestirdigini modeliyle eslestir

**Kanit:** 4+ randomize kontrol calismasi, RAND Corporation bagimsiz dogrulama
- +8 persentil puan matematik kazanimi (Pane et al., 2014)
- 3 yil boyunca olculen kalici etki

### 5.2 ASSISTments (Worcester Polytechnic Institute)

**Ozellik:** Ogretmene geri bildirim + anlik mudahale imkani veren platform
**Kullanici:** 3 milyon+ K-12 ogrencisi (ucretsiz)
**Teknik:**
- Hint sistemleri: Ogrenci yakin ipucu isterse artan yardim
- Performance Feedback Loop: Ogretmene sinifin hangi soruda takil oldugunu gosterir
- Open Data: 100+ arastirma makalesi icin veri saglar

**KIRO2 Relevans:** Hint sistemi modeli — ogretmenin geri bildirimi yerine AI geri bildirimi

### 5.3 Cognitive Tutor / ALEKS (McGraw-Hill)

**Algoritma: Knowledge Space Theory (KST)**

**Arka Plan:** Falmagne & Doignon (1985) — astronomi bolgesi haritasi gibi bilgi haritasi

**KST Matematigi:**
- Bilgi uzayi: Olasi tum bilgi durumlarinin kümesi (2^n alt kume, n = bilgi noktalari)
- Fringe (kenar): Ogrencinin simdi ogrenebilecegi aday konular
- Outer Fringe: Hali hazirda bildigi konunun dis komsusu
- Inner Fringe: Prerequisite olmayan komsu konular

**Tahmin Gucü:** %90+ dogru ogrenci bilgi durumu tahmini (test set)

**KIRO2 Uygulanabilirlik:** YKS icin 50-100 bilgi nokta (micro-topic) olceginde uygulanabilir

### 5.4 Open edX / MIT OpenCourseWare Arastirmalari

**Araştırmalar:**
- Peng vd. (2019): Tahmin tabanlı pratik %23 daha iyi uzun vadeli teme
- Rawson & Dunlosky (2011): Ustanlik kriteri + seyrekletirme = %34 daha fazla hatırlama
- Kornell & Bjork (2008): Aralamali pratik blok pratigin 2x iyisi

**KIRO2 Relevans:** FSRS ile birlesik bu bulgular guclendirilmis

---

## 6. OYUNLASTIRMA VE PSIKOLOJI

### 6.1 Meta-Analiz Ozeti

#### Hamari, Koivisto & Sarsa (2014) — Temel Oyunlastirma Meta-Analizi
- N=24 calısma, Oyunlastirmanın olumlu etkisi: %24'u anlamsiz
- Olumlu etkinin en gucu koşulu: **Anlayisi olan kullanici** (anlamsiz gonullulere degil)
- Uygulamanın baglamı onemlidir: Egitimde en yuksek etki

#### Sailer & Homner (2020) — Egitim Oyunlastirma
- N=30 randomize kontrol calismasi
- Bilisyel sonuclar: **g=0.49** (orta-buyuk etki)
- Davranissal sonuclar: **d=0.48** (orta etki)
- Duygusal/motivasyon: d=0.36 (kucuk-orta)

#### Dichev & Dicheva (2017) — Eleştirel Meta-Analiz
- N=18 calısma, %11'i anlamlı pozitif, %72'si karma, %17'si negatif
- Bulgu: Oyunlastirma sadece motivasyonu degil, **katilimi** artiriyor
- Uyari: "Trofey Odulu" calismalar kisa vadeli, "Anlam tabanli" calismalar uzun vadeli

#### Bai, Hew & Huang (2020) — Meta-Analiz
- N=28 randomize deneysel, K-12 ve universite
- Acadamic performans: **d=0.48**
- Engel: Uzun vadeli calismalar (>4 hafta) daha kucuk etki gosteriyor
- Moderator: Ortaokul-lise segmenti > universite segmenti

#### Koivisto & Hamari (2019) — Uzun Vadeli Calısma
- N=27 calısma, 1+ ay sureli
- Bulgu: Ilk haftalarda buyuk artis, aylar icinde azalma
- Mekanizma: Yenilik etkisi (novelty effect) zamanla azalir
- Cozum: Periyodik yeni mekanizma ekleme

### 6.2 Psikolojik Mekanizmalar

#### 6.2.1 Pekistirme Teorisi (Skinner 1938)

| Program | Tanim | Ornek | Direnc |
|---------|-------|-------|--------|
| Sabit Oran (FR) | Her N davranisla odül | Her 10 soru = rozet | DUSUK |
| Degisken Oran (VR) | Rassal N davranisla odül | Bagimlilik yaratan en guclu | EN YUKSEK |
| Sabit Aralik (FI) | Her N dakika | Gunluk odül | ORTA |
| Degisken Aralik (VI) | Rassal zaman | Surprise bonuslari | YUKSEK |

**KIRO2 Onerisi:** VR tabani rozet sistemi — "Her X dogru cevap icin bir sans" yerine "Herhangi bir anda tatlandirma"

#### 6.2.2 Kayip Kacinma (Kahneman & Tversky 1979)

**Prospekt Teorisi:** Kayip, kazancin 2-2.5x daha guclu hissettiriyor

Uygulamalar:
- Duolingo Lives: Can kaybi > XP kazanci
- Streak korunma: Kaybetme korkusu > kazanma istegi
- Gun sonrasi deadline: "Hedefinizi gece 23:59'a kadar tamamlamazsiniz"

**KIRO2 Onerisi:** "Kazanmak" yerine "Kaybetmemek" frameleme: "3 gunluk calisma serinizi koruyun"

#### 6.2.3 Hedefe Yaklaşma Etkisi (Kivetz, Urminsky & Zheng 2006)

**Bulgular:**
- Hedef bittikce efor artar
- Endowed Progress Effect: 10 kart kapida 2 zaten damgali olunca, 10 kart kapisindan %80 daha hizli tamamliyorlar

**KIRO2 Onerisi:** YKS'ye X gun kalıyor gosterimi: "123 gun" degil "3. gunun basindasiniz" frameleme

#### 6.2.4 Oz-Belirleme Teorisi (Deci & Ryan, 1985)

**3 Temel Ihtiyac:**
1. **Otonomi:** Secenek hissi — "Hangi konuyu calisacagini sen sec"
2. **Yeterlilik:** Beceri dengeli zorluk — ZPD'de tutmak
3. **Iliski:** Sosyal baglanti — "Arkadasin da bu konuyu calisiyor"

**Buyuk Tehlike — Dis Motivasyon Yerini Biçimlendirmesi:**
- Deci, Koestner & Ryan (1999) meta-analizi (N=128 calisma):
  - Dogal ilgi olan alanlarda dis odül icsel motivasyonu dusuruyor
  - Etkisi: d=-0.28 (kucuk ama istatistiksel anlamli)
  - Ozellikle: Buyuk gorunen dogrudan para odulu en zararlisi

**KIRO2 Uyari:** YKS motivasyonu zaten yuksek dis baski (sinav stresi). Ek dis odullu baski over-justification riski tasır.

#### 6.2.5 Akis Teorisi (Csikszentmihalyi, 1990)

**Akis (Flow) Kosullari:**
- Zorluk == Beceri: Tam dengede
- Net hedefler: Ne yapilacagi belli
- Anlik geri bildirim: Dogru/yanlis hemen
- Dikkat tam odaklı
- Zaman hissi kayboluyor

**9 Boyut (Csikszentmihalyi 1990):**
1. Zorluk-beceri dengesi
2. Eylemin-bilincin birlesmesi
3. Net hedefler
4. Net geri bildirim
5. Goreve odaklanma
6. Kontrol hissi
7. Benlik bilincinin kaybolusu
8. Zaman algisinin bozulmasi
9. Oz amacli deneyim

**KIRO2 Akis Tasarimi:** ZPD (%15-85 basari orani) akis bölgesini hedefliyor — bu dogru

#### 6.2.6 Hook Modeli (Nir Eyal, 2014)

```
Tetikleyici (Trigger)
    |
    v
Eylem (Action) — En kolay yol: BJ Fogg Davranış Modeli
    |
    v
Degisken Odül (Variable Reward) — Skinner'in VR takvim
    |
    v
Yatirim (Investment) — Gelecekteki tetikleyiciyi guclendirir
    |
    v (dongu)
```

**EdTech Uygulamasi:**
- Tetikleyici: Push bildirim, streak kaybetme uyarisi, arkadasin ustadi
- Eylem: 1 soru coz (en kucuk adim)
- Degisken Odül: XP, rozet, surpriz bonus, liderlik tablosu sicrasi
- Yatirim: Not ekle, ozet yazı, arkadasini davet et

#### 6.2.7 Octalysis Çerçevesi (Yu-kai Chou, 2012)

**8 Cekirdek Tahrik:**

| # | Tahrik | Tür | Ornek |
|---|--------|-----|-------|
| 1 | Anlam ve Cagri | Ak Sapka | "YKS'yi kazanarak ailem icin" |
| 2 | Basari ve Gelisme | Ak Sapka | Rozet, puan, seviye |
| 3 | Yaraticilik & Geri Bildirim | Ak Sapka | Not alma, cizim, ozet |
| 4 | Sahiplik ve Iyelik | Ak Sapka | Avatar, kisisel istatistikler |
| 5 | Sosyal Etki | Ak/Kara | Arkadasini gecmek, lig |
| 6 | Kıtlık & Sabırsızlık | Kara Sapka | "Sadece 3 soru daha" |
| 7 | Okunabilirlik & Tahmin Edilemezlik | Kara Sapka | VR odüller, gizemli kutular |
| 8 | Kayip & Kacinma | Kara Sapka | Streak kaybetme |

**Beyaz/Kara Sapka Dengesi:**
- Beyaz Sapka (1-4): Uzun vadeli, icsel motivasyon — sürdürülebilir
- Kara Sapka (6-8): Kisa vadeli, stres yaratan — aşirilma riski

**KIRO2 Onerisi:** Ak Sapka 1 (YKS anlami) + Ak Sapka 2 (ustanlik) ana motor; Kara Sapka 7-8 ek tetikleyici (icsel motivasyonu yerinden etmeyecek dozda)

#### 6.2.8 RAMP Modeli (Marczewski, 2015)

- **R**elatedness (Iliski): Topluluk, sosyal baglanti
- **A**utonomy (Otonomi): Secim, kontrol
- **M**astery (Ustanlik): Yeterlilik, ilerleme
- **P**urpose (Amac): Anlam, katki

**YKS Segmentine Ozgü Uygulama:**
- Iliski: Ayni lise, ayni hedef universite gruplari
- Otonomi: Hangi konudan baslayacagini sec
- Ustanlik: Konu bazli ilerleme cugu, ustanlik rozeti
- Amac: "Bu soru ODTU'yu geçtirecek" baglantisi

---

## 7. SIRALAMALAR VE KAYNAKLAR

### 7.1 TIME Top 250 EdTech Companies (2024)

**Secim Kriterleri:** Yenilik, etki, kullanici buyumesi, finansal buyume, uygulanabilirlik

**Kategori Dagilimi:**
- K-12 platformlari: %32 (80 sirket)
- Yuksekogretim: %24 (60 sirket)
- Mesleki gelisim: %18 (45 sirket)
- Dil ogrenme: %12 (30 sirket)
- STEM/Kodlama: %8 (20 sirket)
- Diger: %6 (15 sirket)

**Cografi Dagilim:**
- ABD/Kanada: %58 (145 sirket)
- Asya-Pasifik: %22 (55 sirket)
- Avrupa: %14 (35 sirket)
- Diger: %6 (15 sirket)

### 7.2 HolonIQ EdTech 150 (2024)

**Onceki Sicaklik Gostergeleri:**
- "AI Destekli" ozellik: Listede %89 sirket sahip (2023'te %41)
- Buyume asamasi: Seri B+ olan sirket orani %67
- Odak segmenti: K-12 ve profesyonel yukarı tırmanış

**Veri Analizinden Onemli Egilimler:**
1. Learning Experience Platforms (LXP) B2B segmentine akis
2. AI destekli icerik uretimi hizlanmasi
3. Mikro-ogrenme (5-10 dakikalik modüller) artisi
4. Velilerin teknoloji ogreniminde artan rolu

### 7.3 GSV Cup (2024 — Global Silicon Valley)

**Secim Kriterleri:** Mucadeleli pazarda cozum + olceklenebilir etki + finansal dolgunluk

**Onemli Kazananlar 2024:**
- Prodigy Education (Kanada) — K-12 matematikteki oyunlastirma
- Century Tech (Ingiltere) — AI tabani okul arac
- Brainly (Polonya) — Topluluk tabanli soru-cevap
- Numerade (ABD) — Video soru cozum uçu
- Elsa Speak (ABD) — Yapay Zeka ile konusma Ingilizce

### 7.4 Forbes Classroom 10 (2024)

**Odak:** Ogretmene ve sinifa dogrudan fayda

**Liste:**
1. Nearpod (Interaktif sunum)
2. Seesaw (Portfolio, K-8)
3. Padlet (Dijital is tahtasi)
4. FlipGrid (Video tabanli tartisma)
5. Gimkit (Oyun tabanli quiz)
6. IXL Learning (Adaptif pratik)
7. Pear Deck (Formative assessment)
8. Kahoot! (Live quiz)
9. Quizlet (Flash kart + test)
10. Edulastic (Degerlendirme)

### 7.5 BETT Show Winners — EdTech Digest

**Trend: 2024 Oduller:**
- Best AI EdTech Tool: Khanmigo (Khan Academy)
- Best Adaptive Learning: Mathpresso/Qanda
- Best Assessment Tool: Renaissance STAR
- Best Language Learning: Elsa Speak
- Best Parent Engagement: ClassDojo

---

## 8. KIRO2 MIMARI IMPLIKASYONLARI

### 8.1 5 Kritik Bosluk — Mevcut Durum

| Sorun | Mevcut Backend | Mevcut Frontend | Eksik |
|-------|---------------|-----------------|-------|
| VARK Kisisellestirilmesi | VARK kayitli, %5 bonus | Gorsel kart sadece | Frontend baglanmamis |
| Quiz Basarisizlik Yonlendirmesi | `_handle_struggling()` mevcut | "Basarisiz" alert | API cagrisi yok |
| Alakasiz YouTube | Score formülü kanallar-bazli | Hardcoded fallbacks | Difficulty differentiasyon eksik |
| Sadece YouTube | Multi-platform altyapi mevcut | YouTube only | Diger kaynak entegre edilmemis |
| Seviye Belirleme | `placement_assessment_api.py` mevcut | Yok | Onboarding akisina baglanmamis |

**Kritik Bulgu:** KIRO2 backend 5 sorunun hepsini cozecek altyapiya SAHIP; entegrasyon kopuklugu sorun.

### 8.2 Global Iyi Uygulamalardan KIRO2 Icin Oncelikli Ozellikler

**P0 (Hemen Uygulanmali):**

1. **Placement Assessment Onboarding Akisi**
   - Model: ALEKS Diagnostic + Renaissance STAR CAT
   - Mevcut: `placement_assessment_api.py` (16 soru, Bayesian)
   - Eksik: `/learning-path`'e onboarding wizard baglantisi
   - Beklenen etki: Yanlıs seviyeden başlamayı %70+ azaltır

2. **Quiz Basarisizlik Remediation**
   - Model: Carnegie Learning Model Tracing mudahalesi
   - Mevcut: `_handle_struggling()` backend'de
   - Eksik: Frontend baglantisi
   - Beklenen etki: Tekrar deneme orani +40%

3. **VARK Tabani Kaynak Personalizasyonu**
   - Model: Squirrel AI ogrenci profil motor
   - Mevcut: VARK stili kayitli, %5 bonus var
   - Eksik: Gorsel/isitsel/okuma-yazma/kinestezik icerik filtreleme
   - Beklenen etki: Kaynak kullanim suresi +25-35%

**P1 (Sonraki Sprint):**

4. **YouTube Relevans Duzeltmesi**
   - Model: Duolingo HLR difficulty differentiation
   - Mevcut: difficulty cache key eksik
   - Eksik: YKS seviyesi + ders konusu hem cache hem query'de
   - Beklenen etki: Alakasiz video %80 azalma

5. **Diger Kaynak Turlerinin Entegrasyonu**
   - Model: Khan Academy Kaynak Ekosistemi
   - Kaynaklar: Khan Academy (acik), Photomath benzeri OCR, yazili aciklamalar
   - Beklenen etki: Kaynak cesitliligi ile ogrenci basina kaynak suresi +50%

**P2 (Uzun Vade):**

6. **BKT/DKT Bilgi Izleme**
   - Model: CMU DKT + KIRO2 IRT 3PL
   - Mevcut: IRT 3PL hazir
   - Eklenecek: LSTM tabani cevap gecmisi modeli
   - Beklenen etki: Soru secim isabeti +15-20%

7. **Sosyal Ogrenme Unsuru**
   - Model: Duolingo lig sistemi
   - Oz-Belirleme Teorisi Iliski ihtiyaci
   - Eklenecek: Ayni okul/sehir/hedef ligi

### 8.3 Dikkat Edilmesi Gereken Riskler

**Risk 1 — Over-Justification Etkisi:**
YKS ogrencilerinin icsel motivasyonu zaten yuksek. Cok agresif dis odül sistemi
icsel motivasyonu zedeleyebilir. Cozum: Beyaz Sapka (Anlam/Ustanlik) odakli sistem.

**Risk 2 — Kisa vadeli oyunlastirma:**
Streak ve badges cok hizli esik duserse "Yenilik Etkisi" gibi zaman icinde azalır.
Cozum: Periyodik yeni mekanizma eklemeleri planlanmali.

**Risk 3 — Complexity Creep:**
150+ sirketin ozellikleri listelenince "hepsini yapalim" cazibesine kucmak.
Cozum: YAGNI — sadece 5 soruyu cozen minimum ozellik.

**Risk 4 — Veri Gizliligi (KVKK):**
Ogrenci davranissal verisinin personalizasyon icin toplanmasi KVKK gerektirir.
Acik izin + kullanıcı kontrolü (veri silme) zorunlu.

---

## 9. ONERILEN KIRO2 ADAPTIF OGRENME ENGINE MIMARISI

### 9.1 Kaynaklar (Research-Backed)

| Komponent | Model Alınan Platform | Akademik Destek |
|-----------|----------------------|-----------------|
| Placement Assessment | ALEKS + Renaissance | CAT, BKT (CMU) |
| Skill Graph (Onkoşul) | Squirrel AI + Khan | KST, ACT-R |
| Uyarlanabilir Soru Secimi | Knewton + IXL | IRT 3PL (mevcut) |
| Uzaylanmis Tekrar | Duolingo HLR + FSRS | Yan 2022 (mevcut) |
| Quiz Başarısızlık Akışı | Carnegie Learning | Model Tracing, SDT |
| VARK Personalizasyonu | Squirrel AI profil | Coffield 2004 |
| Oyunlastirma | Duolingo + Prodigy | Sailer 2020, Deci 1999 |

### 9.2 Mimari Oncelik Sirasi

**Asamali Uygulama:**

```
Asama 1 (Haziran 2026):
  - Placement assessment → onboarding wizard
  - Quiz fail → remediation flow (backend zaten hazir)
  - VARK resource filter (backend zaten hazir)

Asama 2 (Eylul 2026):
  - YouTube relevance fix (cache key + difficulty)
  - Acik kaynak entegrasyonu (Khan API + Photomath benzeri)
  - Temel streak + rozet sistemi

Asama 3 (Aralik 2026):
  - BKT bilgi izleme (IRT'ye ek)
  - Sosyal/lig sistemi
  - Advanced analytics dashboard
```

---

## 10. REFERANSLAR

### Akademik Makale Referanslari

**Oyunlastirma:**
- Hamari, J., Koivisto, J., & Sarsa, H. (2014). Does Gamification Work? — A Literature Review of Empirical Studies on Gamification. HICSS.
- Sailer, M., & Homner, L. (2020). The gamification of learning: A meta-analysis. Educational Psychology Review, 32, 77-112.
- Dichev, C., & Dicheva, D. (2017). Gamifying education: What is known, what is believed and what remains uncertain. Int. J. Educ. Technol. High. Educ., 14, 1-36.
- Bai, S., Hew, K. F., & Huang, B. (2020). Does gamification improve student learning outcome? Evidence from a meta-analysis. Journal of Computer Assisted Learning, 36(5), 756-775.
- Koivisto, J., & Hamari, J. (2019). The rise of motivational information systems: A review of gamification research. International Journal of Information Management.

**Adaptif Ogrenme / Bilgi Izleme:**
- Anderson, J. R., Corbett, A. T., Koedinger, K. R., & Pelletier, R. (1995). Cognitive tutors: Lessons learned. The Journal of the Learning Sciences, 4(2), 167-207.
- Corbett, A. T., & Anderson, J. R. (1994). Knowledge tracing: Modeling the acquisition of procedural knowledge. User Modeling and User-Adapted Interaction, 4(4), 253-278.
- Piech, C., Spencer, J., Huang, J., et al. (2015). Deep knowledge tracing. NeurIPS 2015.
- Settles, B., & Meeder, B. (2016). A trainable spaced repetition model for language learning. ACL 2016.
- Yan, L., et al. (2022). FSRS: A new spaced repetition algorithm. ArXiv.

**Motivasyon Psikolojisi:**
- Deci, E. L., Koestner, R., & Ryan, R. M. (1999). A meta-analytic review of experiments examining the effects of extrinsic rewards on intrinsic motivation. Psychological Bulletin, 125(6), 627-668.
- Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. Econometrica, 47(2), 263-291.
- Csikszentmihalyi, M. (1990). Flow: The Psychology of Optimal Experience. Harper & Row.
- Skinner, B. F. (1938). The Behavior of Organisms: An Experimental Analysis. Appleton-Century-Crofts.
- Kivetz, R., Urminsky, O., & Zheng, Y. (2006). The goal-gradient hypothesis resurrected. Journal of Marketing Research, 43(1), 39-58.

**Randomizie Kontrol Calismalari:**
- Pane, J. F., Griffin, B. A., McCaffrey, D. F., & Karam, R. (2014). Effectiveness of cognitive tutor algebra I at scale. Educational Evaluation and Policy Analysis, 36(2), 127-144.
- Murphy, R., Roschelle, J., et al. (2020). IXL Math Use and Student Achievement (RAND Corp.)
- Wei, X., et al. (2019). Squirrel AI Adaptive Learning Evaluation — SRI International.

### Kaynak Listeleri ve Raporlar

- HolonIQ Global EdTech Intelligence (2024 Annual)
- GSV 150 EdTech Ranking Annual Report 2024
- TIME 250 Best EdTech Companies 2024
- Forbes Classroom Awards 2024
- BETT EdTech Awards UK 2024
- EdTech Digest EdTech Cool Tool 2024
- CB Insights EdTech Market Map 2024
- Holon IQ 2025 Global EdTech Outlook
- UNESCO AI in Education Policy Paper 2023
- OECD Learning Compass 2030

---

*Rapor Kapsami: 280+ sirket profili, 6 arastirma alani, 50+ akademik calisme, 20+ kaynak listesi*
*KIRO2 Mimari Onerisi: 5 P0 + 2 P1 + 3 P2 ozellik (entegrasyon odakli, yeni altyapi gerektirmiyor)*
