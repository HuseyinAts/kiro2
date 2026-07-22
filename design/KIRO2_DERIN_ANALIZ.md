# KIRO2 — Derin Durum Analizi & Kanıt-Temelli Yol Haritası

> İleri düzey araştırma raporu. Bölüm 1 dış kanıt tabanını (pazar · öğrenme bilimi · kaygı-oyunlaştırma) kurar; Bölüm 2 projenin mevcut durumunu bu kanıta karşı ultra-derin analiz eder; Bölüm 3 risk matrisi; Bölüm 4 kanıt-temelli, önceliklendirilmiş "yapabileceklerimiz".

---

## Yönetici Özeti
KIRO2, güçlü kanıt-temelli bir öğrenme omurgası (aralıklı tekrar + adaptif zorluk + getirim pratiği) ile **doğru ama henüz kanıtlanmamış** bir konumlandırmayı (kaygı-duyarlı, akran-baskısız) birleştiriyor. Üç yapısal gerilim var:

1. **Vaad–gerçek açığı:** Bilimsel omurga (CAT/IRT · FSRS · BKT) ve AI tutor **temalı ama çalışmıyor** — ürünün en güçlü, en kanıtlı farkı henüz asıl işlevsel değil.
2. **Kaygı-tezi kendi içinde çelişebiliyor:** Literatür kaygı-duyarlı yaklaşımı desteklerken, üründeki rekabetçi mekanikler (Lig sıralaması, Boss yenilgi çerçevesi) tam da hedef kitleyi (kaygılı/düşük-performanslı öğrenci) riske atan öğeler.
3. **Sunum-gerçek kayması + teknik borç:** Paydaş artefaktları güncel değil; tek-kaynak mimarisi fallback kopyalarıyla seyrelmiş.

Bunlar çözülebilir ve yol haritası nettir (Bölüm 4).

---

## BÖLÜM 1 — Dış Kanıt Tabanı

### 1.1 Pazar & bağlam (Türkiye YKS)
- YKS, Türkiye'de üniversiteye girişin **neredeyse tek belirleyicisi**; sonuç akademik performansa dayalı, bu da yoğun bir baskı/rekabet kültürü yaratıyor (TutorChase, 2024).
- Özel ders/**dershane** derinden yerleşik: bir taşra araştırmasında öğrencilerin **~yarısı** son bir yılda özel ders almış; en popüler dersler matematik, fen, Türkçe; **yönlendiren çoğunlukla veli** (Şanlıurfa anketi, n=1329, 2021). Yani **ödeyen = veli**, karar sürecinde veli merkezde.
- Küresel özel-ders pazarı **2025'te ~133,8 milyar $, 2034'te ~248,4 milyar $ (%7,12 CAGR)**; Asya-Pasifik lider (%35,5). Belirgin trend: **AI-güdümlü adaptif platformlar, gerçek-zaman ilerleme takibi, kişiselleştirilmiş çalışma planları, abonelik modelleri** (IMARC/Futurism, 2025-26).
- AI-tutor etkisi ölçülüyor: FEV Tutor–Stanford çalışması AI CoPilot'un K-12 matematik sonuçlarını ortalama **+9 puan** iyileştirdiğini raporladı (2024).

**Çıkarım:** KIRO2 gerçek, büyük ve büyüyen bir pazarın **doğru trendinde** (AI-adaptif + kişisel plan). Ama iki gerçekle yüzleşmeli: (a) köklü, veli-güvenli dershaneye karşı net bir fark; (b) veli-ödeyen dinamiği (ürün öğrenciye tasarlanmış, kararı veli veriyor). **Kaygı-duyarlılık burada gerçek bir beyaz-alan**: kültür yüksek-baskı; sakin, kanıt-temelli bir alternatif farklılaştırıcı.

### 1.2 Öğrenme bilimi — omurga güçlü kanıtlı
- **Aralıklı tekrar (FSRS'in temeli):** Tıp eğitimi meta-analizinde 21.415 öğrenci, standart çalışmaya karşı **SMD = 0,78 (güçlü etki)** (Systematic Review & Meta-Analysis, PubMed 41601436, 2025). Bağımsız RCT'ler etki büyüklüğü ~0,8 doğruluyor (Karachi, n=115).
- **Getirim pratiği + dağıtık pratik en üstün teknikler:** Donoghue & Hattie (2021) 242 çalışma / ~169.000 katılımcı — dağıtık pratik ve pratik-test 10 teknik içinde **en etkili ikili**; ironik biçimde öğrencilerin en çok kullandığı **vurgulama/tekrar-okuma/özetleme en etkisizler arasında**.
- **Aralık tasarımı önemli:** genişleyen aralıklar (ör. 2-7-17-40 gün) sabit/daralan aralıklardan daha iyi tutulum sağlıyor (French survey, 2024).

**Çıkarım:** KIRO2'nin çekirdek mekaniği (FSRS aralıklı tekrar + getirim + adaptif zorluk) **eğitim biliminin en kanıtlı araçlarıdır** ve öğrencilerin doğal olarak yapmadığı şeydir. Bu, ürünün **en savunulabilir farkı**. Sorun: şu an temalı/illüstratif — asıl motor devrede değil, ve paywall arkasında.

### 1.3 Oyunlaştırma & kaygı — çift kenarlı bıçak
- Oyunlaştırma "çift-kenarlı": olumlu duygu ve başarı hissini güçlendirebilir, ama ödül yapıları **kaygı duyarlılığını yükseltebilir** (Cheng; PMC12913498).
- Ergenlerde **performans-odaklı liderlik tabloları stres/hayal kırıklığı yaratır; içsel motivasyonu düşürür, sosyal kıyası ve baskıyı artırır; kontrol-edici algılanan ödüller ve sürekli görünür başarısızlıklar özerkliği/öz-yeterliği baltalar — özellikle düşük-performanslı öğrencileri caydırır** (arXiv 2512.15630).
- Rekabetçi öğeler kaygıyı **sürdürebilir**: yüksek motivasyona rağmen kaygıda yalnız mütevazı düşüş (Tayland CALL çalışması, 2024).
- Ama iyi tasarlanınca **tersi de mümkün**: işbirlikçi/gerilimsiz gamification (Kahoot RCT, Ürdün) stres ve kaygıyı anlamlı düşürüp öz-yeterliği artırdı; İspanya'da 12-haftalık gamified program çocuklarda kaygıyı azalttı (RCT, n=120).

**Çıkarım (kritik):** Literatür KIRO2'nin **tezini doğruluyor** — akran-baskısız, "sen vs dün", işbirlikçi, sakin oyunlaştırma kaygıyı düşürebilir. Ama **aynı literatür KIRO2'nin bazı mekaniklerini uyarıyor**: Lig sıralaması, 1v1 Düello ve Boss'taki **yenilgi çerçevesi** ("Ejderha seni yendi", sürekli görünür can/HP kaybı) tam da düşük-performanslı, kaygılı öğrenciyi caydıran öğeler. Ürün, kaçındığını iddia ettiği baskı mekaniğini kısmen içe almış.

---

## BÖLÜM 2 — Ultra-Derin Mevcut-Durum Analizi

### 2.1 Mimari & teknik borç
**Güçlü:** Tek-kaynak `kiro-data.js` + `§2` bağlama deseni; 25+ ekran tutarlı Hüseyin hikâyesine bağlı; her ekran Design Component; ışık/koyu kanonu tutarlı; API sözleşmesi (§20) üretim geçişini `import → fetch`e indirger.

**Borç:**
- **Fallback kopyalama:** Her ekran kiro-data değerlerini authored fallback olarak inline taşıyor → aynı gerçeğin 25+ kopyası. `kiro-data` düzenlenince fallback bayatlar; tek-kaynak "tek" olmaktan kısmen çıkar. (Bilinçli seçim — stream-flaşını önler — ama ölçekte bakım borcu.)
- **Zaman tutarsızlığı:** Üç farklı "bugün" — Panel sabit ("Pzt 29 Haziran"), Geri Sayım gerçek `Date.now()` (353 gün), Haftalık Plan sabit "29 Haz–5 Tem". Üretimde tek sunucu-`now` şart.
- **View Transitions Chromium'a bağlı:** preview'da şık, diğer tarayıcılarda anlık-nav'a düşer (kırılma yok ama tutarsız deneyim).
- **Curriculum granülerlik uyumsuzluğu:** `topics` (AYT: Türev/İntegral) ile `curriculum` konuları (TYT: Üslü/Köklü) farklı katman; "sıradaki adım" en zayıf AYT konusunu gösterirken yolculuk TYT ünitelerini gösteriyor → ince kavramsal çatlak.

### 2.2 Ürün tezi — kanıta karşı (en kritik bölüm)
KIRO2'nin çekirdek tezi: *"kaygı-duyarlı + kanıt-temelli."* Kanıta göre:
- **Kanıt-temelli kısım DOĞRU ama İNŞA EDİLMEMİŞ.** FSRS/CAT/BKT en kanıtlı araçlar (Bölüm 1.2) — ama temalı. AI Sohbet/Sokratik senaryolu. Ürünün en savunulabilir değeri henüz asıl çalışmıyor.
- **Kaygı-duyarlı kısım YÖNELIM DOĞRU ama ÖLÇÜLMEMİŞ ve KISMEN ÇELİŞİK.** "Sen vs dün", davet dili, risk=amber, ölçülü kutlama → literatürle uyumlu. Ama Lig/Düello/Boss-yenilgi → literatürün uyardığı baskı mekaniği (2.1.3). **Geri sayım** özellikle riskli: her geri-sayım özünde kaygı-tetikleyici; "gündoğumu" çerçevesi hipotez, kanıt değil — **kullanıcı testiyle pre/post kaygı ölçülmeli** (test planı §, tam bunu hedefliyor).

**Sonuç:** Ürünün iki iddiası da henüz **doğrulanmamış** — biri (bilim) inşa edilmediği için, diğeri (kaygı) ölçülmediği için. Bu, projenin **bir numaralı boşluğu**.

### 2.3 İş modeli & pazar konumu
- **Fiyat:** ₺124-199/ay authored, pazar-doğrulaması yok. Dershane maliyetine göre konumlanmalı (dershane çok daha pahalı → app ucuz alternatif olarak güçlü).
- **Paywall paradoksu:** Değer-önermesinin **merkezi** özellikler (adaptif test, FSRS) paywall arkasında. Kanıt der ki bunlar asıl farklılaştırıcı — ama ödeyemeyen kaygılı öğrenci tam da bunlardan mahrum. Ücretsiz katman "tadımlık FSRS" sunmalı (dönüşüm + etik).
- **Veli-ödeyen dinamiği:** Ürün öğrenciye tasarlı; kararı veli veriyor (Bölüm 1.1). Veli Paneli var ama **satın-alma ikna yüzeyi** (ilerleme kanıtı → ROI) zayıf. Paywall'ın veli-yüzü güçlendirilmeli.

### 2.4 Veri & kapsam gerçekliği
- **Sadece Sayısal:** Persona ve tüm veri Sayısal; ürün "genel YKS" diyor ama EA/Sözel **yok**. Adreslenebilir pazarın büyük kısmı kapsam dışı.
- **Veri inceliği:** ~20 soru, 4 konuda atom, curriculum konuları "temsili" (progress "5/5" ama 4 konu listeli — bilinçli fudge). Demo için yeter; gerçek kullanımda hemen tükenirdi.
- **Motor gerçekliği:** θ/BKT/CAT değerleri illüstratif; gerçek IRT kalibrasyonu, madde havuzu, FSRS zamanlaması yok.

### 2.5 Erişilebilirlik & tutarlılık
- Kontrast: koyu ekranlar tam AA; açık ekranlarda birincil/ikincil AA, en soluk griler FAIL (dekoratif) — belgelendi (§ACCESSIBILITY), düzeltilmedi.
- Sunum kayması: Canlı Demo (8 sahne), paydaş destesi (8 slayt), flow görüntüleri → 4 yeni ekranı içermiyor. Paydaşa ürünü **eksik temsil ediyor**.
- Galeri sayaçları güncel değil (yeni kartlar eklendi, rozet sayıları eski).

---

## BÖLÜM 3 — Risk & Fırsat Matrisi

| Alan | Güç | Risk | Kanıt |
|---|---|---|---|
| Öğrenme bilimi | En kanıtlı mekanik (SMD 0.78) | Henüz inşa edilmemiş | 1.2 |
| Kaygı-duyarlılık | Gerçek beyaz-alan | Rekabet mekaniği tezi çürütebilir + ölçülmemiş | 1.3, 2.2 |
| Pazar | Doğru trend (AI-adaptif), büyük | Dershane + veli-ödeyen | 1.1 |
| Mimari | Tek-kaynak + API sözleşmesi | Fallback borcu, zaman tutarsızlığı | 2.1 |
| İş modeli | Ucuz alternatif potansiyeli | Paywall paradoksu, fiyat doğrulanmamış | 2.3 |
| Kapsam | Derin Sayısal hikâye | EA/Sözel yok, veri ince | 2.4 |

---

## BÖLÜM 4 — Yapabileceklerimiz (kanıt-temelli, önceliklendirilmiş)

### P0 — Dürüstlük & tutarlılık (hızlı; gerçek hatalar)
1. **Tek "bugün" modeli** — Geri Sayım · Haftalık Plan · Panel tek referansa (`kiro-data`'ya `bugun` alanı). *Gerekçe: 2.1 zaman tutarsızlığı.*
2. **Sunumu güncelle** — Canlı Demo turuna + paydaş destesine 4 yeni ekranı ekle; flow görüntülerini yenile. *Gerekçe: 2.5 sunum kayması.*
3. **Galeri sayaçları + giriş noktaları** temizliği.

### P1 — Vaadi gerçeğe yaklaştır (en yüksek etki)
4. **AI'ı gerçekten canlandır** — AI Sohbet + Sokratik AI'ı gerçek Claude API ile (senaryo → gerçek Sokratik diyalog). *Gerekçe: 2.2 — en savunulabilir değer henüz sahte; AI-tutor pazarın trendi (1.1, FEV +9pp).*
5. **Kaygı-tezini mekaniğe göm** — literatürün uyardığı öğeleri yumuşat:
   - Boss: "Ejderha seni yendi" → "henüz değil, birlikte tekrar"; kayıp yerine ilerleme çerçevesi.
   - Lig: sıralama-görünürlüğünü kıs, "sen vs dün"ü birincil yap; opsiyonel/kapatılabilir rekabet.
   - Geri Sayım: kaygı-nötr çerçeveyi test et; alternatif "hazırlık ilerlemesi" görünümü.
   *Gerekçe: 1.3 — rekabet mekaniği hedef kitleyi caydırıyor.*
6. **FSRS'i ücretsiz katmana taşı (tadımlık)** — paywall paradoksunu çöz: en kanıtlı araç herkese biraz açık. *Gerekçe: 2.3 + 1.2.*

### P2 — Sağlamlaştır & doğrula
7. **Kaygıyı ölç** — kullanıcı testi planını (§) çalıştır; pre/post durumluk kaygı + kavrama. *Ürünün 1 numaralı doğrulanmamış iddiası (2.2).*
8. **Kapsamı genişlet** — EA/Sözel persona + veri; soru/atom havuzunu büyüt. *Gerekçe: 2.4 — adreslenebilir pazar.*
9. **Veli satın-alma yüzeyi** — Veli Paneli'nde ROI/ilerleme-kanıtı → paywall veli-yüzü. *Gerekçe: 1.1 veli-ödeyen.*
10. **Fallback borcunu azalt** — ortak fallback modülü / tek-kaynak sadeleştirme; erişilebilirlik düzeltmelerini uygula.

### P3 — Ölçek & gerçek ürün
11. Sistematik durum yönetimi (hata/boş/yükleniyor); zaman/lokalizasyon.
12. Handoff paketiyle (§) gerçek kod tabanında (React/RN) uygulama; gerçek IRT kalibrasyonu + FSRS zamanlayıcı (genişleyen aralık, 1.2).

**Önerilen sıra:** P0 (2-3 hızlı düzeltme) → **P1/4-5 (gerçek AI + kaygı-mekaniği)** en yüksek stratejik etki → P2/7 (kaygıyı ölç: tezi kanıtla ya da çürüt). Bu üçü ürünü "prototip"ten "kanıtlanmış ürün"e taşıyan omurga.

---

### Kaynaklar (dış kanıt)
- Aralıklı tekrar meta-analizi (21.415 öğrenci, SMD 0.78): PubMed 41601436 (2025). Donoghue & Hattie (2021), 242 çalışma. Genişleyen aralık: French survey (2024).
- Oyunlaştırma & kaygı: Cheng (PMC12913498); "Age-Aware Gamification" (arXiv 2512.15630); Kahoot RCT Ürdün (ScienceDirect, 2024); İspanya çocuk RCT (PMC11942101).
- Pazar: IMARC/Futurism özel-ders pazarı (2025-26); Türkiye özel ders (Şanlıurfa anketi 2021; TutorChase 2024); FEV Tutor–Stanford (2024).

*Not: Dış kaynaklar bağlam ve kanıt içindir; proje/kişi hakkında olgu değildir. Etki büyüklükleri farklı bağlamlardan (çoğu tıp/dil eğitimi) genellenirken dikkatli olunmalı.*
