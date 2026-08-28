// ============================================================================
// KIRO2 — TEK KAYNAK VERİ MODÜLÜ  (Şafak kanonu prototipi)
// Tüm ekranlar bu modülü okur → tek tutarlı "Hüseyin" hikâyesi.
// ⚠️ Bu dosya DEĞİŞİNCE `kiro-seed.js`'i YENİDEN ÜRET (senkron ikiz → window.__KIRO):
//    ekranlar veriyi kiro-seed.js'ten SENKRON okur; buradaki dinamik import yalnız recovery.
//    (run_script: kiro-data oku → `export ` sil → IIFE'ye sar → window.__KIRO ata. Bkz. DEVIR §22b.)
// Bilimsel çekirdek: CAT/IRT (θ kestirimi) · FSRS (aralıklı tekrar) · BKT (bilgi takibi)
// Model: Qwen3-8B (Türkçe NLP) · Soru bankası: 77.000+ · Roller: öğrenci/veli/öğretmen/admin
// Persona anı: SON DENEME SONRASI — zayıf konular netleşmiş, tekrar kuyruğu dolu.
// ============================================================================

export const engine = {
  model: 'Qwen3-8B',
  bankSize: 77000,
  motorlar: ['CAT/IRT', 'FSRS', 'BKT'],
  roller: ['öğrenci', 'veli', 'öğretmen', 'admin'],
};

export const persona = {
  ad: 'Hüseyin Ateş',
  adKisa: 'Hüseyin',
  bas: 'HA',
  sinif: '12. Sınıf · Sayısal',
  seri: 12,                 // gün — Bugün ekranıyla tutarlı
  seriRekor: 21,
  xp: 2450,
  seviye: 7,
  hedefBolum: 'Bilgisayar Mühendisliği',
  hedefUni: 'ODTÜ / Bilkent',
  hedefSiralama: 15000,
  guncelSiralama: 27400,    // son denemeye göre tahmin
  yksTarihi: '2027-06-20',
  gunlukHedefDk: 45,
  bugunCozulenDk: 30,
};

// θ = IRT yetenek kestirimi (-3..+3) · bkt = BKT p(biliniyor) 0..1 · hakimiyet = birleşik %
export const subjects = [
  { key:'mat', ad:'Matematik', renk:'#5B8DEF', glow:'rgba(91,141,239,0.5)', tur:'AYT+TYT', hakimiyet:78, theta:0.9,  bkt:0.79 },
  { key:'fiz', ad:'Fizik',     renk:'#A77BFF', glow:'rgba(167,123,255,0.5)', tur:'AYT',     hakimiyet:64, theta:0.4,  bkt:0.63 },
  { key:'kim', ad:'Kimya',     renk:'#E25A72', glow:'rgba(226,90,114,0.5)', tur:'AYT',     hakimiyet:52, theta:-0.3, bkt:0.51 },
  { key:'biy', ad:'Biyoloji',  renk:'#2DD4A7', glow:'rgba(45,212,167,0.5)', tur:'AYT',     hakimiyet:71, theta:0.7,  bkt:0.70 },
  { key:'tur', ad:'Türkçe',    renk:'#FFB347', glow:'rgba(255,179,71,0.5)', tur:'TYT',     hakimiyet:83, theta:1.2,  bkt:0.84 },
];

export const subjectMap = subjects.reduce((m, s) => { m[s.key] = s; return m; }, {});

// Konu düzeyi hâkimiyet (BKT) — Öğrenme Yolu / Panel / hedefleme için
export const topics = [
  { ders:'mat', ad:'Türev',              hakimiyet:48, durum:'zayif' },
  { ders:'mat', ad:'Limit ve Süreklilik',hakimiyet:55, durum:'gelisiyor' },
  { ders:'mat', ad:'İntegral',           hakimiyet:62, durum:'gelisiyor' },
  { ders:'mat', ad:'Fonksiyonlar',       hakimiyet:74, durum:'iyi' },
  { ders:'mat', ad:'Trigonometri',       hakimiyet:70, durum:'iyi' },
  { ders:'fiz', ad:'Kuvvet ve Hareket',  hakimiyet:60, durum:'gelisiyor' },
  { ders:'fiz', ad:'Elektrik',           hakimiyet:50, durum:'zayif' },
  { ders:'fiz', ad:'Optik',              hakimiyet:68, durum:'iyi' },
  { ders:'kim', ad:'Mol Kavramı',        hakimiyet:62, durum:'gelisiyor' },
  { ders:'kim', ad:'Gazlar',             hakimiyet:46, durum:'zayif' },
  { ders:'kim', ad:'Asit-Baz',           hakimiyet:58, durum:'gelisiyor' },
  { ders:'kim', ad:'Kimyasal Tepkimeler',hakimiyet:50, durum:'zayif' },
  { ders:'biy', ad:'Genetik',            hakimiyet:72, durum:'iyi' },
  { ders:'biy', ad:'Hücre Bölünmeleri',  hakimiyet:75, durum:'iyi' },
  { ders:'biy', ad:'Sistemler',          hakimiyet:68, durum:'iyi' },
  { ders:'tur', ad:'Paragraf',           hakimiyet:86, durum:'guclu' },
  { ders:'tur', ad:'Sözcükte Anlam',     hakimiyet:84, durum:'guclu' },
  { ders:'tur', ad:'Dil Bilgisi',        hakimiyet:80, durum:'iyi' },
];

// ============================================================================
// ALAN-ÜSTÜ DERS KATALOĞU — üç YKS alanını da kapsar (Alan Kütüphanesi ekranı).
// persona (Sayısal) ekranlarını bozmamak için `subjects`/`topics`'ten AYRI tutulur.
// ============================================================================
export const dersKatalog = {
  tur: { ad:'Türkçe',                 renk:'#F59E0B', tur:'TYT',     konuSayisi:12, ornek:['Paragraf','Sözcükte Anlam','Dil Bilgisi','Anlatım Bozukluğu'] },
  mat: { ad:'Matematik',              renk:'#3B82F6', tur:'TYT+AYT', konuSayisi:16, ornek:['Türev','İntegral','Limit','Fonksiyonlar','Trigonometri'] },
  fiz: { ad:'Fizik',                  renk:'#8B5CF6', tur:'AYT',     konuSayisi:10, ornek:['Kuvvet ve Hareket','Elektrik','Optik','Dalgalar'] },
  kim: { ad:'Kimya',                  renk:'#E0593F', tur:'AYT',     konuSayisi:11, ornek:['Mol Kavramı','Gazlar','Asit-Baz','Tepkimeler'] },
  biy: { ad:'Biyoloji',               renk:'#1FB683', tur:'AYT',     konuSayisi:9,  ornek:['Genetik','Hücre','Sistemler','Ekoloji'] },
  edb: { ad:'Türk Dili ve Edebiyatı', renk:'#D97706', tur:'AYT',     konuSayisi:14, ornek:['Şiir Bilgisi','Edebî Akımlar','Divan Edebiyatı','Roman'] },
  tar: { ad:'Tarih',                  renk:'#B45309', tur:'TYT+AYT', konuSayisi:13, ornek:['İlk Türk Devletleri','Osmanlı','İnkılap Tarihi','Çağdaş Dünya'] },
  cog: { ad:'Coğrafya',               renk:'#0D9488', tur:'TYT+AYT', konuSayisi:12, ornek:['İklim','Nüfus','Ekonomik Coğrafya','Jeopolitik'] },
  fel: { ad:'Felsefe',                renk:'#7C3AED', tur:'TYT+AYT', konuSayisi:8,  ornek:['Bilgi Felsefesi','Ahlak Felsefesi','Mantık','Sanat Felsefesi'] },
  din: { ad:'Din Kültürü',            renk:'#6B7280', tur:'TYT',     konuSayisi:6,  ornek:['İnanç','İbadet','Ahlak','Din ve Hayat'] },
};

// YKS alanları — her alanın AYT ders bileşimi (TYT ortak: Türkçe·Mat·Fen·Sosyal)
export const alanlar = [
  { key:'say', ad:'Sayısal',       renk:'#3B82F6', ozet:'Mühendislik · Tıp · Fen bilimleri', ayt:['mat','fiz','kim','biy'] },
  { key:'ea',  ad:'Eşit Ağırlık',  renk:'#1FB683', ozet:'Hukuk · İktisat · Psikoloji',       ayt:['mat','edb','tar','cog'] },
  { key:'soz', ad:'Sözel',         renk:'#F59E0B', ozet:'Öğretmenlik · İlahiyat · Hukuk',    ayt:['edb','tar','cog','fel'] },
];

// EA/SÖZEL konu envanteri — persona-BAĞIMSIZ müfredat referansı (hakimiyet YOK:
// Hüseyin bu dersleri çalışmıyor; dersKatalog.konuSayisi ile birebir sayım).
// Sayısal dersleri zaten `topics`/`curriculum`'da derin — burada tekrarlanmaz.
export const katalogKonular = {
  edb: ['Şiir Bilgisi', 'Söz Sanatları', 'Halk Edebiyatı', 'Divan Edebiyatı', 'Tanzimat Edebiyatı', 'Servet-i Fünun', 'Fecr-i Ati', 'Millî Edebiyat', 'Cumhuriyet Dönemi Şiiri', 'Cumhuriyet Dönemi Romanı', 'Hikâye', 'Tiyatro', 'Edebî Akımlar', 'Dil ve Anlatım'],
  tar: ['İlk Türk Devletleri', 'İslamiyet Öncesi Kültür', 'Türk-İslam Devletleri', 'Anadolu Beylikleri', 'Osmanlı Kuruluş', 'Osmanlı Yükselme', 'Osmanlı Duraklama-Gerileme', '19. Yüzyıl Islahatları', 'I. Dünya Savaşı', 'Millî Mücadele', 'İnkılap Tarihi', 'Atatürk Dönemi Dış Politika', 'Çağdaş Dünya Tarihi'],
  cog: ['Doğa ve İnsan', "Dünya'nın Şekli ve Hareketleri", 'Harita Bilgisi', 'İklim Bilgisi', 'İç ve Dış Kuvvetler', 'Nüfus', 'Göç', 'Yerleşme', 'Ekonomik Faaliyetler', "Türkiye'nin Ekonomik Coğrafyası", 'Bölgeler ve Ülkeler', 'Çevre ve Toplum'],
  fel: ['Felsefeye Giriş', 'Bilgi Felsefesi', 'Varlık Felsefesi', 'Ahlak Felsefesi', 'Sanat Felsefesi', 'Din Felsefesi', 'Siyaset Felsefesi', 'Mantık'],
  din: ['İnanç', 'İbadet', 'Ahlak ve Değerler', 'Din ve Hayat', "Hz. Muhammed'in Hayatı", 'İslam Düşüncesinde Yorumlar'],
};

// EA/Sözel ünite ağacı — katalogKonular'ın ünite kırılımı (MEB kazanım sırası).
// Persona ilerlemesi İÇERMEZ (Hüseyin Sayısal); Alan Kütüphanesi drill'ini gruplar.
export const katalogUniteler = {
  edb: [
    { no:1, ad:'Şiir & Söz Sanatları',      konular:['Şiir Bilgisi','Söz Sanatları'] },
    { no:2, ad:'Eski Türk Edebiyatı',       konular:['Halk Edebiyatı','Divan Edebiyatı'] },
    { no:3, ad:'Yenileşme Dönemi',          konular:['Tanzimat Edebiyatı','Servet-i Fünun','Fecr-i Ati','Millî Edebiyat'] },
    { no:4, ad:'Cumhuriyet Edebiyatı',      konular:['Cumhuriyet Dönemi Şiiri','Cumhuriyet Dönemi Romanı','Hikâye','Tiyatro'] },
    { no:5, ad:'Kuram & Dil',               konular:['Edebî Akımlar','Dil ve Anlatım'] },
  ],
  tar: [
    { no:1, ad:'İlk ve Orta Çağ Türk Tarihi', konular:['İlk Türk Devletleri','İslamiyet Öncesi Kültür','Türk-İslam Devletleri','Anadolu Beylikleri'] },
    { no:2, ad:'Osmanlı Tarihi',              konular:['Osmanlı Kuruluş','Osmanlı Yükselme','Osmanlı Duraklama-Gerileme','19. Yüzyıl Islahatları'] },
    { no:3, ad:'Millî Mücadele & İnkılap',    konular:['I. Dünya Savaşı','Millî Mücadele','İnkılap Tarihi','Atatürk Dönemi Dış Politika'] },
    { no:4, ad:'Çağdaş Dünya',                konular:['Çağdaş Dünya Tarihi'] },
  ],
  cog: [
    { no:1, ad:'Doğal Sistemler',       konular:['Doğa ve İnsan',"Dünya'nın Şekli ve Hareketleri",'Harita Bilgisi','İklim Bilgisi','İç ve Dış Kuvvetler'] },
    { no:2, ad:'Beşerî Sistemler',      konular:['Nüfus','Göç','Yerleşme'] },
    { no:3, ad:'Ekonomik Coğrafya',     konular:['Ekonomik Faaliyetler',"Türkiye'nin Ekonomik Coğrafyası"] },
    { no:4, ad:'Küresel Ortam & Çevre', konular:['Bölgeler ve Ülkeler','Çevre ve Toplum'] },
  ],
  fel: [
    { no:1, ad:'Felsefeyi Tanıma',   konular:['Felsefeye Giriş'] },
    { no:2, ad:'Bilgi & Varlık',     konular:['Bilgi Felsefesi','Varlık Felsefesi'] },
    { no:3, ad:'Değer Felsefesi',    konular:['Ahlak Felsefesi','Sanat Felsefesi','Din Felsefesi'] },
    { no:4, ad:'Toplum & Mantık',    konular:['Siyaset Felsefesi','Mantık'] },
  ],
  din: [
    { no:1, ad:'İnanç & İbadet',            konular:['İnanç','İbadet'] },
    { no:2, ad:'Ahlak & Yaşam',             konular:['Ahlak ve Değerler','Din ve Hayat'] },
    { no:3, ad:'Peygamber & İslam Düşüncesi', konular:["Hz. Muhammed'in Hayatı",'İslam Düşüncesinde Yorumlar'] },
  ],
};

// Öğretmen yüzeyi — 12-A sınıf listesi (Ödev Atama / Öğretmen Paneli).
// theta: IRT kestirimi (-3..+3) · hakimiyet: genel % · risk: etkinlik bayrağı (amber, alarm değil)
export const sinifRoster = [
  { no:1, ad:'Hüseyin Ateş', theta:0.9,  hakimiyet:78, risk:null,                        sonAktif:'bugün' },
  { no:2, ad:'Deniz Arslan', theta:-0.3, hakimiyet:52, risk:'2 ödev teslim edilmedi',    sonAktif:'4 gün önce' },
  { no:3, ad:'Elif Kaya',    theta:1.4,  hakimiyet:86, risk:null,                        sonAktif:'bugün' },
  { no:4, ad:'Mert Yıldız',  theta:0.2,  hakimiyet:64, risk:null,                        sonAktif:'dün' },
  { no:5, ad:'Zeynep Demir', theta:0.6,  hakimiyet:71, risk:null,                        sonAktif:'bugün' },
  { no:6, ad:'Emre Şahin',   theta:-0.7, hakimiyet:44, risk:'9 gündür oturum açmadı',    sonAktif:'9 gün önce' },
  { no:7, ad:'Selin Koç',    theta:0.4,  hakimiyet:68, risk:null,                        sonAktif:'dün' },
  { no:8, ad:'Baran Aydın',  theta:-0.1, hakimiyet:57, risk:null,                        sonAktif:'bugün' },
];

// Öğrenci yüzü — Hüseyin'e atanmış ödevler (Ödevlerim ekranı; Odev Atama'nın öğrenci ucu).
// durum: 'acik' | 'bekliyor' (geciken — "eksik" DEĞİL, kaygı-duyarlı) | 'tamam'
// kisisel: θ-tabanlı kişiye özel set · dakika: tahmini süre (adet × ~1.6)
export const odevler = [
  { id:'odv-24', baslik:'Türev soru paketi',        ders:'mat', konu:'Türev',               atayan:'Mehmet Öztürk', adet:10, yapilan:4,  dakika:16, teslim:'Cuma 23:59',  kalan:'2 gün', durum:'acik',     kisisel:true },
  { id:'odv-23', baslik:'İntegral mini set',        ders:'mat', konu:'İntegral',            atayan:'Mehmet Öztürk', adet:8,  yapilan:3,  dakika:13, teslim:'dün 23:59',   kalan:null,    durum:'bekliyor', kisisel:true },
  { id:'odv-22', baslik:'Limit tekrar seti',        ders:'mat', konu:'Limit ve Süreklilik', atayan:'Mehmet Öztürk', adet:12, yapilan:12, dakika:19, teslim:'Salı 23:59',  kalan:null,    durum:'tamam',    kisisel:true },
];

// FSRS aralıklı tekrar kuyruğu — SON DENEME sonrası bugün bekleyenler
// stabilite: bellek izi ömrü (gün) · guclukFSRS: 0..10 · hatirlanabilirlik: R(t) anlık %
export const reviewQueue = [
  { ders:'mat', konu:'Türev',               stabilite:3.8, guclukFSRS:7.2, hatirlanabilirlik:82, dueIn:0, kart:6, gecmisNot:'zor' },
  { ders:'mat', konu:'Limit ve Süreklilik', stabilite:5.0, guclukFSRS:6.5, hatirlanabilirlik:88, dueIn:0, kart:4, gecmisNot:'iyi' },
  { ders:'kim', konu:'Kimyasal Tepkimeler', stabilite:2.1, guclukFSRS:8.0, hatirlanabilirlik:79, dueIn:0, kart:5, gecmisNot:'zor' },
  { ders:'fiz', konu:'Elektrik',            stabilite:6.2, guclukFSRS:7.0, hatirlanabilirlik:91, dueIn:1, kart:4, gecmisNot:'iyi' },
  { ders:'biy', konu:'Genetik',             stabilite:9.4, guclukFSRS:5.2, hatirlanabilirlik:94, dueIn:2, kart:3, gecmisNot:'kolay' },
];

// Son deneme — Sınav Sonuç / Panel / "neden bu konu tekrar kuyruğunda" için
export const lastExam = {
  ad: 'KIRO Genel Deneme #7',
  tarih: '2026-06-29',
  tip: 'TYT + AYT (Sayısal)',
  tahminiSiralama: 27400,
  tyt: [
    { ad:'Türkçe',           soru:40, dogru:34, yanlis:4,  bos:2, net:33.0 },
    { ad:'Sosyal Bilimler',  soru:20, dogru:15, yanlis:3,  bos:2, net:14.25 },
    { ad:'Temel Matematik',  soru:40, dogru:24, yanlis:10, bos:6, net:21.5 },
    { ad:'Fen Bilimleri',    soru:20, dogru:15, yanlis:3,  bos:2, net:14.25 },
  ],
  ayt: [
    { ad:'Matematik', soru:40, dogru:20, yanlis:12, bos:8, net:17.0 },
    { ad:'Fizik',     soru:14, dogru:8,  yanlis:4,  bos:2, net:7.0 },
    { ad:'Kimya',     soru:13, dogru:6,  yanlis:5,  bos:2, net:4.75 },
    { ad:'Biyoloji',  soru:13, dogru:9,  yanlis:2,  bos:2, net:8.5 },
  ],
  get tytNet() { return this.tyt.reduce((a, s) => a + s.net, 0); },
  get aytNet() { return this.ayt.reduce((a, s) => a + s.net, 0); },
};

// ============================================================================
// SORU BANKASI — 26 tam YKS-tarzı soru + adım adım çözüm (18 Sayısal + 8 EA/Sözel)
// b = IRT güçlük (-2..+2) · a = ayırt edicilik · sure = ort. çözüm süresi (sn)
// ============================================================================
export const questionBank = [
  // ---- MATEMATİK ----
  { id:'mat-turev-1', ders:'mat', konu:'Türev', b:0.4, a:1.2, sure:75,
    soru:'f(x) = x³ − 3x² + 2 fonksiyonunun x = 2 noktasındaki teğetinin eğimi kaçtır?',
    secenekler:['−4', '0', '4', '8', '12'], dogru:1,
    cozum:[
      'Bir noktadaki teğet eğimi = o noktadaki türev: f′(2).',
      'Türevi al: f′(x) = 3x² − 6x.',
      'x = 2 yaz: f′(2) = 3·(2²) − 6·2 = 12 − 12.',
      'f′(2) = 0 → teğet yatay (x=2 yerel ekstremum).',
    ],
    neden:'Türev, bir noktadaki anlık değişim hızıdır; grafikte teğetin eğimine eşittir.' },

  { id:'mat-turev-2', ders:'mat', konu:'Türev', b:1.1, a:1.3, sure:90,
    soru:'f(x) = x·eˣ fonksiyonunun türevi f′(x) aşağıdakilerden hangisidir?',
    secenekler:['eˣ', 'x·eˣ', 'eˣ·(1 + x)', 'eˣ·(x − 1)', '1 + x'], dogru:2,
    cozum:[
      'İki fonksiyonun çarpımı → çarpım kuralı: (u·v)′ = u′v + uv′.',
      'u = x → u′ = 1 ;  v = eˣ → v′ = eˣ.',
      'f′(x) = 1·eˣ + x·eˣ.',
      'Ortak çarpan eˣ parantezine al: f′(x) = eˣ·(1 + x).',
    ],
    neden:'Çarpım kuralı, iki değişen büyüklüğün ortak değişimini ayrıştırır.' },

  { id:'mat-limit-1', ders:'mat', konu:'Limit ve Süreklilik', b:0.2, a:1.1, sure:70,
    soru:'lim (x→2)  (x² − 4)/(x − 2)  limitinin değeri kaçtır?',
    secenekler:['0', '2', '4', '8', 'Limit yok'], dogru:2,
    cozum:[
      'x = 2 koyunca 0/0 belirsizliği çıkar → çarpanlara ayır.',
      'Pay: x² − 4 = (x − 2)(x + 2).',
      '(x − 2) sadeleşir: ifade x + 2 olur.',
      'x → 2 için: 2 + 2 = 4.',
    ],
    neden:'0/0 belirsizliğinde ortak çarpanı sadeleştirip sürekli hale getiririz.' },

  { id:'mat-integral-1', ders:'mat', konu:'İntegral', b:0.6, a:1.2, sure:80,
    soru:'∫₀¹ (3x² + 2x) dx  integralinin değeri kaçtır?',
    secenekler:['1', '2', '3', '4', '5'], dogru:1,
    cozum:[
      'Terim terim ilkel al: ∫3x² dx = x³, ∫2x dx = x².',
      'F(x) = x³ + x².',
      'Newton-Leibniz: F(1) − F(0).',
      '(1 + 1) − (0 + 0) = 2.',
    ],
    neden:'Belirli integral, eğri altında kalan net alanı verir (ilkelin uç değerleri farkı).' },

  { id:'mat-fonk-1', ders:'mat', konu:'Fonksiyonlar', b:-0.2, a:1.0, sure:55,
    soru:'f(x) = 2x − 3 ve g(x) = x² ise (f∘g)(2) kaçtır?',
    secenekler:['1', '3', '5', '8', '13'], dogru:2,
    cozum:[
      'Bileşke içten dışa çalışır: (f∘g)(2) = f( g(2) ).',
      'Önce g(2) = 2² = 4.',
      'Sonra f(4) = 2·4 − 3 = 8 − 3.',
      '= 5.',
    ],
    neden:'Bileşke fonksiyonda bir fonksiyonun çıktısı diğerinin girdisi olur.' },

  { id:'mat-trig-1', ders:'mat', konu:'Trigonometri', b:0.5, a:1.1, sure:60,
    soru:'sin30° + cos60° toplamı kaçtır?',
    secenekler:['0', '1/2', '1', '√3/2', '√3'], dogru:2,
    cozum:[
      'Özel açı değerleri: sin30° = 1/2.',
      'cos60° = 1/2.',
      '1/2 + 1/2 = 1.',
    ],
    neden:'30° ve 60° tümler açılardır: sin30° = cos60°.' },

  // ---- FİZİK ----
  { id:'fiz-hareket-1', ders:'fiz', konu:'Kuvvet ve Hareket', b:0.3, a:1.2, sure:65,
    soru:'Sürtünmesiz yatay düzlemde 2 kg kütleye 10 N kuvvet uygulanıyor. Cismin ivmesi kaç m/s² olur?',
    secenekler:['2', '5', '10', '20', '0,2'], dogru:1,
    cozum:[
      'Newton’un 2. yasası: F = m·a.',
      'İvme çekilir: a = F / m.',
      'a = 10 N / 2 kg.',
      '= 5 m/s².',
    ],
    neden:'Net kuvvet, kütle ile ivmenin çarpımına eşittir; sürtünme yoksa tüm kuvvet ivmeye gider.' },

  { id:'fiz-hareket-2', ders:'fiz', konu:'Kuvvet ve Hareket', b:0.8, a:1.1, sure:70,
    soru:'Yerden serbest bırakılan bir cisim 3 s sonra kaç m/s hıza ulaşır? (g = 10 m/s², hava sürtünmesi yok)',
    secenekler:['3', '10', '13', '30', '45'], dogru:3,
    cozum:[
      'Serbest düşmede ilk hız sıfır: v = g·t.',
      'v = 10 · 3.',
      '= 30 m/s.',
    ],
    neden:'Serbest düşmede hız, yerçekimi ivmesiyle zamanın çarpımı kadar artar.' },

  { id:'fiz-elektrik-1', ders:'fiz', konu:'Elektrik', b:0.9, a:1.2, sure:65,
    soru:'12 V’luk bir pile 4 Ω’luk direnç bağlanıyor. Devreden geçen akım kaç A olur? (iç direnç yok)',
    secenekler:['0,33', '3', '8', '16', '48'], dogru:1,
    cozum:[
      'Ohm yasası: V = I·R.',
      'Akım çekilir: I = V / R.',
      'I = 12 V / 4 Ω.',
      '= 3 A.',
    ],
    neden:'Gerilim, akım ile direncin çarpımına eşittir (Ohm yasası).' },

  { id:'fiz-optik-1', ders:'fiz', konu:'Optik', b:0.7, a:1.0, sure:95,
    soru:'Odak uzaklığı 20 cm olan çukur aynada cisim aynadan 30 cm uzakta. Görüntünün aynaya uzaklığı kaç cm’dir? (1/f = 1/dᵢ + 1/dₒ)',
    secenekler:['12', '15', '50', '60', '10'], dogru:3,
    cozum:[
      'Ayna denklemi: 1/f = 1/dᵢ + 1/dₒ.',
      '1/dᵢ = 1/f − 1/dₒ = 1/20 − 1/30.',
      'Ortak payda 60: (3 − 2)/60 = 1/60.',
      'dᵢ = 60 cm.',
    ],
    neden:'Ayna denklemi odak, cisim ve görüntü uzaklıklarını birbirine bağlar.' },

  // ---- KİMYA ----
  { id:'kim-mol-1', ders:'kim', konu:'Mol Kavramı', b:0.2, a:1.1, sure:55,
    soru:'1 mol su (H₂O) kaç tane su molekülü içerir? (Nₐ = 6·10²³)',
    secenekler:['3·10²³', '6·10²³', '12·10²³', '18', '1'], dogru:1,
    cozum:[
      '1 mol, Avogadro sayısı kadar tanecik demektir.',
      'Nₐ = 6·10²³.',
      'Dolayısıyla 1 mol H₂O = 6·10²³ molekül.',
    ],
    neden:'Mol, tanecik sayısını sayılabilir ölçeğe taşıyan köprü birimidir.' },

  { id:'kim-gaz-1', ders:'kim', konu:'Gazlar', b:0.7, a:1.2, sure:70,
    soru:'Sabit sıcaklıkta 2 L’lik bir gazın basıncı 3 atm’dir. Hacim 6 L’ye çıkarılırsa basınç kaç atm olur?',
    secenekler:['0,5', '1', '3', '6', '9'], dogru:1,
    cozum:[
      'Sabit sıcaklık → Boyle yasası: P₁·V₁ = P₂·V₂.',
      '3 · 2 = P₂ · 6.',
      '6 = 6·P₂.',
      'P₂ = 1 atm.',
    ],
    neden:'Sabit sıcaklıkta basınç ile hacim ters orantılıdır (Boyle).' },

  { id:'kim-asit-1', ders:'kim', konu:'Asit-Baz', b:0.5, a:1.1, sure:60,
    soru:'[H⁺] = 10⁻³ mol/L olan bir çözeltinin pH değeri kaçtır?',
    secenekler:['3', '−3', '11', '7', '10'], dogru:0,
    cozum:[
      'Tanım: pH = −log[H⁺].',
      '[H⁺] = 10⁻³.',
      'pH = −log(10⁻³) = −(−3) = 3.',
    ],
    neden:'pH, hidrojen iyonu derişiminin negatif logaritmasıdır; küçük pH = asidik.' },

  // ---- BİYOLOJİ ----
  { id:'biy-genetik-1', ders:'biy', konu:'Genetik', b:0.6, a:1.2, sure:70,
    soru:'Aa × Aa çaprazlamasından oluşan bireylerin genotip oranı nedir?',
    secenekler:['3 : 1', '1 : 2 : 1', '1 : 1', '9 : 3 : 3 : 1', 'Tümü Aa'], dogru:1,
    cozum:[
      'Her ebeveynin gametleri: A ve a.',
      'Punnett karesi: AA, Aa, Aa, aa.',
      'Genotip oranı 1 AA : 2 Aa : 1 aa.',
      '(Fenotip oranı ise 3 baskın : 1 çekinik olurdu.)',
    ],
    neden:'Monohibrit çaprazlamada gametlerin bağımsız birleşimi 1:2:1 genotip verir.' },

  { id:'biy-hucre-1', ders:'biy', konu:'Hücre Bölünmeleri', b:0.4, a:1.0, sure:60,
    soru:'Mitoz bölünme sonucu bir hücreden kaç hücre oluşur ve kromozom sayısı nasıl değişir?',
    secenekler:['2 hücre, yarıya iner', '4 hücre, yarıya iner', '2 hücre, değişmez', '4 hücre, değişmez', '1 hücre, iki katına çıkar'], dogru:2,
    cozum:[
      'Mitozda DNA önce eşlenir, sonra eşit paylaşılır.',
      '1 ana hücre → 2 yavru hücre oluşur.',
      'Her yavru hücrede kromozom sayısı korunur: 2n → 2n.',
    ],
    neden:'Mitoz, büyüme ve onarım için genetik olarak özdeş hücreler üretir.' },

  { id:'biy-sistem-1', ders:'biy', konu:'Sistemler', b:0.3, a:1.0, sure:50,
    soru:'İnsanda oksijeni dokulara taşıyan kan hücresi hangisidir?',
    secenekler:['Akyuvar', 'Alyuvar', 'Kan pulcuğu', 'Plazma', 'Lenfosit'], dogru:1,
    cozum:[
      'Oksijeni bağlayan protein hemoglobindir.',
      'Hemoglobin alyuvarların (eritrosit) içinde bulunur.',
      'Dolayısıyla oksijeni alyuvarlar taşır.',
    ],
    neden:'Alyuvarlardaki hemoglobin, oksijenle geri dönüşümlü bağ kurarak taşır.' },

  // ---- TÜRKÇE ----
  { id:'tur-sozcuk-1', ders:'tur', konu:'Sözcükte Anlam', b:0.4, a:1.1, sure:80,
    soru:'“Ağır” sözcüğü aşağıdaki cümlelerin hangisinde mecaz anlamda kullanılmıştır?',
    secenekler:[
      'Çantası çok ağır olduğu için zor taşıdı.',
      'Bu kayayı ağır olduğu için kaldıramadı.',
      'Söylediklerinin altında ağır bir anlam gizliydi.',
      'Valizi ağır gelince yardım istedi.',
      'Yük ağır olunca kamyon yavaşladı.',
    ], dogru:2,
    cozum:[
      'Mecaz anlam: sözcüğün gerçek (fiziksel) anlamından uzaklaşıp yeni anlam kazanması.',
      'A, B, D, E: hepsinde “ağır” = fiziksel ağırlık → gerçek anlam.',
      'C: “ağır bir anlam” = derin, etkileyici → mecaz anlam.',
    ],
    neden:'Bir sözcüğün mecaz kullanımı, gerçek anlamının bağlamda çözülüp yerini soyut anlama bırakmasıdır.' },

  { id:'tur-cumle-1', ders:'tur', konu:'Cümlede Anlam', b:0.5, a:1.1, sure:75,
    soru:'“Sınava az çalıştı ama yine de başardı.” cümlesindeki anlam ilişkisi aşağıdakilerden hangisidir?',
    secenekler:['Neden-sonuç', 'Karşıtlık (zıtlık)', 'Koşul', 'Amaç-sonuç', 'Eşitlik'], dogru:1,
    cozum:[
      '“ama, yine de” bağlaçları beklenmedik bir durumu işaret eder.',
      'Az çalışınca normalde başarısızlık beklenir; oysa başardı.',
      'Beklenen ile gerçekleşen çelişiyor → karşıtlık (zıtlık) ilişkisi.',
    ],
    neden:'Karşıtlık ilişkisinde iki yargı birbiriyle beklenti düzeyinde çelişir.' },

  // ---- EDEBİYAT (EA/Sözel) ----
  { id:'edb-divan-1', ders:'edb', konu:'Divan Edebiyatı', b:0.3, a:1.1, sure:60,
    soru:'Aşağıdakilerden hangisi Divan edebiyatı nazım biçimidir?',
    secenekler:['Koşma', 'Mani', 'Gazel', 'Semai', 'Varsağı'], dogru:2,
    cozum:[
      'Koşma, semai ve varsağı Âşık (Halk) edebiyatı nazım biçimleridir.',
      'Mani, Anonim Halk edebiyatı ürünüdür.',
      'Gazel; beyitlerle yazılan, aruz ölçülü Divan nazım biçimidir.',
    ],
    neden:'Nazım biçimleri gelenekle sınıflandırılır: aruz+beyit düzeni Divan geleneğinin imzasıdır.' },

  { id:'edb-akim-1', ders:'edb', konu:'Edebî Akımlar', b:0.7, a:1.2, sure:70,
    soru:'“Mai ve Siyah” romanıyla Türk edebiyatında realist romanın öncülerinden sayılan Servet-i Fünun yazarı kimdir?',
    secenekler:['Namık Kemal', 'Halit Ziya Uşaklıgil', 'Ahmet Mithat Efendi', 'Recaizade Mahmut Ekrem', 'Yakup Kadri Karaosmanoğlu'], dogru:1,
    cozum:[
      'Servet-i Fünun (Edebiyat-ı Cedide) dönemi 1896-1901 arasıdır.',
      'Dönemin roman ustası Halit Ziya Uşaklıgil’dir.',
      '“Mai ve Siyah” ile “Aşk-ı Memnu” onun batılı teknikli realist romanlarıdır.',
    ],
    neden:'Dönem-yazar-eser üçlüsü birlikte kodlanır: Servet-i Fünun romanı = Halit Ziya.' },

  // ---- TARİH (EA/Sözel) ----
  { id:'tar-islahat-1', ders:'tar', konu:'19. Yüzyıl Islahatları', b:0.8, a:1.2, sure:75,
    soru:'Osmanlı Devleti’nde padişahın yetkilerini ilk kez sınırlandıran belge aşağıdakilerden hangisidir?',
    secenekler:['Tanzimat Fermanı', 'Sened-i İttifak', 'Islahat Fermanı', 'Kanun-i Esasi', 'Hatt-ı Hümayun'], dogru:1,
    cozum:[
      'Sened-i İttifak 1808’de II. Mahmut ile âyanlar arasında imzalandı.',
      'Belge, âyanların haklarını tanıyarak padişahın otoritesini İLK kez sınırladı.',
      'Tanzimat (1839) ve Islahat (1856) fermanları daha sonradır; Kanun-i Esasi (1876) ilk anayasadır.',
    ],
    neden:'“İlk kez sınırlama” vurgusu kronolojiyle çözülür: 1808 hepsinden öncedir.' },

  { id:'tar-milli-1', ders:'tar', konu:'Millî Mücadele', b:-0.2, a:1.0, sure:50,
    soru:'Türkiye Büyük Millet Meclisi hangi tarihte açılmıştır?',
    secenekler:['19 Mayıs 1919', '23 Nisan 1920', '1 Kasım 1922', '29 Ekim 1923', '3 Mart 1924'], dogru:1,
    cozum:[
      '19 Mayıs 1919 Samsun’a çıkış, Millî Mücadele’nin başlangıcıdır.',
      'TBMM, Ankara’da 23 Nisan 1920’de açıldı.',
      '1 Kasım 1922 saltanatın kaldırılması, 29 Ekim 1923 Cumhuriyet’in ilanıdır.',
    ],
    neden:'Millî Mücadele kronolojisi beş kilit tarihle omurgalanır; TBMM = 23 Nisan 1920.' },

  // ---- COĞRAFYA (EA/Sözel) ----
  { id:'cog-iklim-1', ders:'cog', konu:'İklim Bilgisi', b:0.1, a:1.1, sure:55,
    soru:'Türkiye’de karasal ikliminin en sert yaşandığı bölge aşağıdakilerden hangisidir?',
    secenekler:['Akdeniz', 'Karadeniz', 'Doğu Anadolu', 'Ege', 'Marmara'], dogru:2,
    cozum:[
      'Karasallık; denize uzaklık ve yükseltiyle artar.',
      'Doğu Anadolu hem denizden uzak hem ortalama yükseltisi en fazla bölgedir (Erzurum-Kars).',
      'Kışlar çok soğuk-karlı, yaz-kış sıcaklık farkı en büyüktür.',
    ],
    neden:'İklim sertliği iki değişkenle okunur: denize uzaklık + yükselti.' },

  { id:'cog-nufus-1', ders:'cog', konu:'Nüfus', b:0.4, a:1.1, sure:60,
    soru:'Bir ülkenin nüfus piramidinin tabanının geniş olması aşağıdakilerden hangisini gösterir?',
    secenekler:['Yaşlı nüfusun fazlalığını', 'Doğum oranının yüksekliğini', 'Ortalama yaşam süresinin uzunluğunu', 'Göç verildiğini', 'Nüfusun azaldığını'], dogru:1,
    cozum:[
      'Piramidin tabanı = en genç yaş grupları (0-14).',
      'Taban genişse genç nüfus kalabalıktır.',
      'Bu da doğum oranının yüksek olduğunu gösterir.',
    ],
    neden:'Nüfus piramidi yaş yapısının fotoğrafıdır; taban doğurganlığı okur.' },

  // ---- FELSEFE (Sözel) ----
  { id:'fel-bilgi-1', ders:'fel', konu:'Bilgi Felsefesi', b:0.3, a:1.1, sure:60,
    soru:'“Doğru bilginin kaynağı yalnızca akıldır” görüşünü savunan felsefi akım aşağıdakilerden hangisidir?',
    secenekler:['Empirizm', 'Rasyonalizm', 'Kritisizm', 'Pozitivizm', 'Pragmatizm'], dogru:1,
    cozum:[
      'Empirizm bilginin kaynağını deneyime dayandırır.',
      'Rasyonalizm (akılcılık) kaynağı YALNIZ akıl olarak görür (Descartes, Platon).',
      'Kritisizm ikisini sentezler; pozitivizm olgulara, pragmatizm faydaya bakar.',
    ],
    neden:'Akımlar “bilginin kaynağı” sorusuna verdikleri cevapla ayrışır.' },

  { id:'fel-mantik-1', ders:'fel', konu:'Mantık', b:0.2, a:1.0, sure:55,
    soru:'“Tüm insanlar ölümlüdür. Sokrates insandır. O hâlde Sokrates ölümlüdür.” çıkarımı hangi akıl yürütme türüne örnektir?',
    secenekler:['Tümevarım', 'Analoji', 'Tümdengelim', 'Diyalektik', 'Sezgi'], dogru:2,
    cozum:[
      'Genel bir öncülden (tüm insanlar) yola çıkılıyor.',
      'Tekil bir sonuca (Sokrates) iniliyor.',
      'Genelden özele akıl yürütme = tümdengelim (dedüksiyon); öncüller doğruysa sonuç zorunludur.',
    ],
    neden:'Tümdengelimde sonuç, öncüllerin içinde zaten saklıdır — zorunlu geçerlilik buradan gelir.' },
];

// FSRS aralıklı tekrar — kavram kartları (getirim pratiği). Bugün bekleyen konulara bağlı.
export const flashcards = [
  { ders:'mat', konu:'Türev',               front:'Zincir kuralı: [f(g(x))]′ ifadesi neye eşittir?', back:'f′(g(x)) · g′(x) — dışın türevi çarpı için türevi.' },
  { ders:'mat', konu:'Türev',               front:'Çarpım kuralı: (u·v)′ neye eşittir?',              back:'u′·v + u·v′' },
  { ders:'mat', konu:'Limit ve Süreklilik', front:'0/0 belirsizliğinde ilk yapılacak şey nedir?',     back:'Pay ve paydayı çarpanlara ayırıp ortak çarpanı sadeleştirmek.' },
  { ders:'kim', konu:'Kimyasal Tepkimeler', front:'Bir tepkime denklemi neden denkleştirilir?',       back:'Kütlenin korunumu: her elementin atom sayısı iki tarafta eşit olmalıdır.' },
  { ders:'kim', konu:'Mol Kavramı',         front:'Mol sayısı (n) hangi formülle bulunur?',           back:'n = m / M  (kütle / molar kütle)' },
  { ders:'fiz', konu:'Elektrik',            front:'Ohm yasası nedir?',                                back:'V = I · R  (gerilim = akım × direnç)' },
  { ders:'biy', konu:'Genetik',             front:'Aa × Aa çaprazlamasında fenotip oranı nedir?',     back:'3 baskın : 1 çekinik' },
  { ders:'fiz', konu:'Kuvvet ve Hareket',   front:'Newton’un 2. yasası nasıl ifade edilir?',          back:'F = m · a  (net kuvvet = kütle × ivme)' },
];

// CAT/IRT yerleştirme havuzu — TYT Matematik (b: IRT güçlük, geniş yayılım). Adaptif Test bunu kullanır.
export const catBankMat = [
  { b:-1.2, konu:'İşlem Önceliği', soru:'12 + 8 × 2 işleminin sonucu kaçtır?', secenekler:['40','28','20','32'], dogru:1 },
  { b:-0.8, konu:'Geometri',        soru:'Düzgün bir altıgenin iç açıları toplamı kaç derecedir?', secenekler:['360°','540°','720°','1080°'], dogru:2 },
  { b:-0.5, konu:'Denklem',         soru:'3x = 21 ise x kaçtır?', secenekler:['6','7','8','9'], dogru:1 },
  { b:-0.2, konu:'Kesirler',        soru:'0,25 ondalık sayısının kesir karşılığı aşağıdakilerden hangisidir?', secenekler:['1/2','1/3','1/4','2/5'], dogru:2 },
  { b:0.0,  konu:'Üslü Sayılar',     soru:'2⁴ ifadesinin değeri kaçtır?', secenekler:['8','16','12','32'], dogru:1 },
  { b:0.3,  konu:'Geometri',        soru:'Bir üçgenin iç açıları 2 : 3 : 4 oranındadır. En büyük açı kaç derecedir?', secenekler:['40°','60°','80°','90°'], dogru:2 },
  { b:0.5,  konu:'Fonksiyonlar',    soru:'f(x) = 2x + 1 ise f(3) değeri kaçtır?', secenekler:['5','6','7','9'], dogru:2 },
  { b:0.6,  konu:'Yüzde',           soru:'Bir sayının %15’i 45 ise, bu sayı kaçtır?', secenekler:['200','250','300','450'], dogru:2 },
  { b:0.8,  konu:'Diziler',         soru:'İlk terimi 3, ortak çarpanı 2 olan geometrik dizinin ilk 5 teriminin toplamı kaçtır?', secenekler:['93','96','90','45','189'], dogru:0 },
  { b:1.0,  konu:'Logaritma',       soru:'log₂ 32 değeri kaçtır?', secenekler:['4','5','6','16'], dogru:1 },
  { b:1.3,  konu:'Köklü Sayılar',    soru:'√50 + √18 ifadesinin en sade hâli aşağıdakilerden hangisidir?', secenekler:['8√2','√68','5√2','13√2'], dogru:0 },
  { b:1.5,  konu:'İkinci Derece',    soru:'x² − 5x + 6 = 0 denkleminin köklerinin toplamı kaçtır?', secenekler:['5','6','−5','1'], dogru:0 },
  { b:1.8,  konu:'Trigonometri',    soru:'sin30° + cos60° işleminin sonucu kaçtır?', secenekler:['1/2','1','√3/2','0'], dogru:1 },
  { b:2.0,  konu:'Türev',           soru:'Türevi f′(x) = 6x olan f(x) aşağıdakilerden hangisi olabilir?', secenekler:['3x²','6','2x³','x²'], dogru:0 },
];

// ============================================================================
// CURRICULUM — ders → ünite → konu ağacı (Öğrenme Yolu tek kaynağı)
// durum: done (fethedildi) · current (şu an) · open (hazır) · locked (kilitli)
// progress = ünitenin gerçek konu sayacı (temsili konu listesinden bağımsız)
// ============================================================================
export const curriculum = {
  mat: { est:'~3 hafta', done:12, total:25, next:{ q:12, min:18 }, units:[
    { no:1, ad:'Temel Kavramlar', durum:'done', progress:'4/4', konular:[
      {ad:'Sayı kümeleri',durum:'done'},{ad:'İşlem önceliği',durum:'done'},{ad:'Tek-çift',durum:'done'},{ad:'Ardışık sayılar',durum:'done'}] },
    { no:2, ad:'Bölme & Bölünebilme', durum:'done', progress:'5/5', konular:[
      {ad:'Bölme',durum:'done'},{ad:'Bölünebilme',durum:'done'},{ad:'EBOB-EKOK',durum:'done'},{ad:'Asal çarpan',durum:'done'}] },
    { no:3, ad:'Üslü & Köklü Sayılar', durum:'current', progress:'2/4', konular:[
      {ad:'Üslü sayılar',durum:'done'},{ad:'Üs kuralları',durum:'done'},{ad:'Köklü sayılar',durum:'current'},{ad:'Köklü işlemler',durum:'open'}] },
    { no:4, ad:'Çarpanlara Ayırma', durum:'open', progress:'0/3', konular:[
      {ad:'Ortak çarpan',durum:'open'},{ad:'Özdeşlikler',durum:'open'},{ad:'Rasyonel ifade',durum:'open'}] },
    { no:5, ad:'Oran-Orantı & Problemler', durum:'locked', progress:'0/4', konular:[
      {ad:'Oran-orantı',durum:'locked'},{ad:'Yüzde',durum:'locked'},{ad:'Hız problemleri',durum:'locked'},{ad:'İşçi-havuz',durum:'locked'}] },
  ] },
  fiz: { est:'~5 hafta', done:6, total:18, next:{ q:14, min:22 }, units:[
    { no:1, ad:'Fizik Bilimine Giriş', durum:'done', progress:'3/3', konular:[
      {ad:'Büyüklükler',durum:'done'},{ad:'Birim sistemleri',durum:'done'},{ad:'Vektörler',durum:'done'}] },
    { no:2, ad:'Kuvvet & Hareket', durum:'current', progress:'3/5', konular:[
      {ad:'Denge',durum:'done'},{ad:'Sürtünme',durum:'done'},{ad:'Newton yasaları',durum:'current'},{ad:'İtme-momentum',durum:'open'}] },
    { no:3, ad:'Enerji & İş', durum:'open', progress:'0/4', konular:[
      {ad:'İş',durum:'open'},{ad:'Kinetik enerji',durum:'open'},{ad:'Güç',durum:'open'},{ad:'Korunum',durum:'open'}] },
    { no:4, ad:'Elektrik & Manyetizma', durum:'locked', progress:'0/4', konular:[
      {ad:'Yük',durum:'locked'},{ad:'Akım',durum:'locked'},{ad:'Direnç',durum:'locked'},{ad:'Alan',durum:'locked'}] },
  ] },
  kim: { est:'~4 hafta', done:8, total:20, next:{ q:10, min:16 }, units:[
    { no:1, ad:'Atomun Yapısı', durum:'done', progress:'4/4', konular:[
      {ad:'Atom modelleri',durum:'done'},{ad:'Tanecikler',durum:'done'},{ad:'İzotop',durum:'done'},{ad:'Katmanlar',durum:'done'}] },
    { no:2, ad:'Periyodik Sistem', durum:'done', progress:'4/4', konular:[
      {ad:'Gruplar',durum:'done'},{ad:'Periyotlar',durum:'done'},{ad:'Özellikler',durum:'done'},{ad:'Eğilimler',durum:'done'}] },
    { no:3, ad:'Mol & Stokiyometri', durum:'current', progress:'0/4', konular:[
      {ad:'Mol kavramı',durum:'current'},{ad:'Mol hesapları',durum:'open'},{ad:'Tepkime denklemi',durum:'open'},{ad:'Verim',durum:'open'}] },
    { no:4, ad:'Asit-Baz & Organik', durum:'locked', progress:'0/4', konular:[
      {ad:'pH',durum:'locked'},{ad:'Tampon',durum:'locked'},{ad:'Hidrokarbon',durum:'locked'},{ad:'Fonksiyonel grup',durum:'locked'}] },
  ] },
  biy: { est:'~5 hafta', done:5, total:16, next:{ q:12, min:20 }, units:[
    { no:1, ad:'Hücre & Organeller', durum:'done', progress:'4/4', konular:[
      {ad:'Zar',durum:'done'},{ad:'Çekirdek',durum:'done'},{ad:'Organeller',durum:'done'},{ad:'Taşıma',durum:'done'}] },
    { no:2, ad:'Hücre Bölünmesi', durum:'current', progress:'1/4', konular:[
      {ad:'Hücre döngüsü',durum:'done'},{ad:'Mitoz',durum:'current'},{ad:'Mayoz',durum:'open'},{ad:'Eşeyli üreme',durum:'open'}] },
    { no:3, ad:'Kalıtım', durum:'open', progress:'0/4', konular:[
      {ad:'Mendel',durum:'open'},{ad:'Çaprazlama',durum:'open'},{ad:'Bağlı genler',durum:'open'},{ad:'Mutasyon',durum:'open'}] },
    { no:4, ad:'Ekosistem', durum:'locked', progress:'0/4', konular:[
      {ad:'Besin zinciri',durum:'locked'},{ad:'Madde döngüsü',durum:'locked'},{ad:'Popülasyon',durum:'locked'},{ad:'Komünite',durum:'locked'}] },
  ] },
  tur: { est:'~2 hafta', done:14, total:22, next:{ q:15, min:20 }, units:[
    { no:1, ad:'Sözcükte Anlam', durum:'done', progress:'5/5', konular:[
      {ad:'Gerçek-mecaz',durum:'done'},{ad:'Deyim',durum:'done'},{ad:'Atasözü',durum:'done'},{ad:'Eş-zıt anlam',durum:'done'}] },
    { no:2, ad:'Cümlede Anlam', durum:'done', progress:'4/4', konular:[
      {ad:'Öznel-nesnel',durum:'done'},{ad:'Neden-sonuç',durum:'done'},{ad:'Koşul',durum:'done'},{ad:'Karşılaştırma',durum:'done'}] },
    { no:3, ad:'Paragraf', durum:'current', progress:'5/8', konular:[
      {ad:'Ana düşünce',durum:'current'},{ad:'Yardımcı düşünce',durum:'done'},{ad:'Anlatım biçimi',durum:'done'},{ad:'Akış',durum:'open'}] },
    { no:4, ad:'Dil Bilgisi', durum:'open', progress:'0/5', konular:[
      {ad:'Ses bilgisi',durum:'open'},{ad:'Sözcük türleri',durum:'open'},{ad:'Cümle ögeleri',durum:'open'},{ad:'Yazım',durum:'open'}] },
  ] },
};

// Konu-altı ATOM kırılımı — Bilgi Atomları (motor "tam başarısız adımı" gösterir)
export const atomKirilim = [
  // ---- MATEMATİK ----
  { ders:'mat', konu:'Türev', kavram:'Zincir kuralı', atomlar:[
    { ad:'Dış fonksiyonun türevi',        hakimiyet:84 },
    { ad:'İç-fonksiyon türevi',           hakimiyet:38 },
    { ad:'Çarpım kuralıyla birleştirme',  hakimiyet:71 },
    { ad:'Zincirin zincire uygulanması',  hakimiyet:66 },
  ] },
  { ders:'mat', konu:'Limit ve Süreklilik', kavram:'Belirsizlik ve süreklilik', atomlar:[
    { ad:'Soldan–sağdan limit',            hakimiyet:64 },
    { ad:'Belirsizlik türleri (0/0, ∞/∞)', hakimiyet:52 },
    { ad:'Çarpanlara ayırarak limit',      hakimiyet:58 },
    { ad:'Süreklilik koşulu',              hakimiyet:46 },
  ] },
  { ders:'mat', konu:'İntegral', kavram:'Belirli integral', atomlar:[
    { ad:'İlkel (antitürev) alma',         hakimiyet:70 },
    { ad:'Değişken değiştirme',            hakimiyet:58 },
    { ad:'Newton–Leibniz uygulaması',      hakimiyet:66 },
    { ad:'Alan olarak yorumlama',          hakimiyet:54 },
  ] },
  // ---- FİZİK ----
  { ders:'fiz', konu:'Kuvvet ve Hareket', kavram:'Newton yasaları', atomlar:[
    { ad:'Serbest cisim diyagramı',        hakimiyet:68 },
    { ad:'Newton 2. yasa (F = m·a)',       hakimiyet:64 },
    { ad:'Sürtünme kuvveti',               hakimiyet:55 },
    { ad:'Eğik düzlem çözümü',            hakimiyet:48 },
  ] },
  { ders:'fiz', konu:'Elektrik', kavram:'Ohm yasası ve devreler', atomlar:[
    { ad:'Gerilim–akım–direnç ilişkisi',  hakimiyet:74 },
    { ad:'Seri devrede eşdeğer direnç',   hakimiyet:58 },
    { ad:'Paralel devrede eşdeğer direnç',hakimiyet:41 },
    { ad:'Elektriksel güç ve enerji',     hakimiyet:52 },
  ] },
  // ---- KİMYA ----
  { ders:'kim', konu:'Mol Kavramı', kavram:'Mol ve stokiyometri temeli', atomlar:[
    { ad:'Mol–tanecik (Avogadro)',        hakimiyet:74 },
    { ad:'Mol–kütle (n = m/M)',           hakimiyet:66 },
    { ad:'Mol–hacim (NŞA)',               hakimiyet:58 },
    { ad:'Derişim (molarite)',            hakimiyet:50 },
  ] },
  { ders:'kim', konu:'Gazlar', kavram:'Gaz yasaları', atomlar:[
    { ad:'Boyle yasası (P–V)',        hakimiyet:63 },
    { ad:'Charles yasası (V–T)',      hakimiyet:55 },
    { ad:'İdeal gaz denklemi',        hakimiyet:44 },
    { ad:'Kısmi basınçlar (Dalton)',  hakimiyet:36 },
  ] },
  { ders:'kim', konu:'Asit-Baz', kavram:'pH ve denge', atomlar:[
    { ad:'Asit–baz tanımları',            hakimiyet:68 },
    { ad:'pH–pOH hesabı',                 hakimiyet:60 },
    { ad:'Kuvvetli/zayıf ayrımı',         hakimiyet:54 },
    { ad:'Tampon çözeltiler',            hakimiyet:44 },
  ] },
  { ders:'kim', konu:'Kimyasal Tepkimeler', kavram:'Denkleştirme & stokiyometri', atomlar:[
    { ad:'Tepkime türlerini tanıma',  hakimiyet:64 },
    { ad:'Denklem denkleştirme',      hakimiyet:57 },
    { ad:'Mol–kütle ilişkisi',        hakimiyet:49 },
    { ad:'Sınırlayıcı bileşen',       hakimiyet:39 },
  ] },
];

// Bir kırılımın en zayıf atomu (motorun hedeflediği adım)
export function enZayifAtom(kirilim) {
  return kirilim.atomlar.slice().sort((a, b) => a.hakimiyet - b.hakimiyet)[0];
}

// Bir konunun atom kırılımı (yoksa null) — Öğrenme Yolu / Bilgi Atomları paylaşır
export function atomlarByKonu(konu) {
  return atomKirilim.find((x) => x.konu === konu) || null;
}

// ---------------------------------------------------------------------------
// YARDIMCILAR
// ---------------------------------------------------------------------------

// Birleşik hâkimiyet kademesi (KIRO Mastery Rozet ile birebir eşik)
export function masteryTier(pct) {
  if (pct < 40) return { key:'tanidik',    label:'Tanıdık',    min:0,  max:40 };
  if (pct < 65) return { key:'yetkin',     label:'Yetkin',     min:40, max:65 };
  if (pct < 85) return { key:'usta',       label:'Usta',       min:65, max:85 };
  return              { key:'fethedildi', label:'Fethedildi', min:85, max:100 };
}

// IRT 2-parametreli: bir öğrencinin (θ) bir soruyu (a,b) doğru yapma olasılığı
export function irtProb(theta, a, b) {
  return 1 / (1 + Math.exp(-a * (theta - b)));
}

// Belirli ders/konudan n soru seç (yoksa tüm dersten)
export function seciliSet(dersKey, n, konu) {
  let q = questionBank.filter((x) => x.ders === dersKey);
  if (konu) q = q.filter((x) => x.konu === konu);
  return (n ? q.slice(0, n) : q);
}

export function konularByDers(dersKey) {
  return topics.filter((t) => t.ders === dersKey);
}

// Türkçe sayı: 12.5 → "12,5"
export function trNum(n) {
  return String(n).replace('.', ',');
}

// Seviye XP eşikleri — kümülatif XP (indeks = seviye). persona.xp=2450 → seviye 7.
export const seviyeEsik = [0, 0, 200, 450, 760, 1140, 1580, 2080, 2680, 3380, 4180, 5080, 6080];

// Bir XP değerinin seviye bilgisi: seviye + sonraki seviyeye ilerleme (Lig level-up için)
export function seviyeBilgi(xp) {
  let sev = 1;
  for (let L = 1; L < seviyeEsik.length; L++) { if (xp >= seviyeEsik[L]) sev = L; }
  const mevcutEsik = seviyeEsik[sev] || 0;
  const sonrakiEsik = seviyeEsik[sev + 1] || (mevcutEsik + 900);
  const span = Math.max(1, sonrakiEsik - mevcutEsik);
  const ilerleme = Math.min(1, Math.max(0, (xp - mevcutEsik) / span));
  return { seviye: sev, mevcutEsik, sonrakiEsik, span, ilerleme, kalanXp: Math.max(0, sonrakiEsik - xp) };
}

const _gunAdlari = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
const _gunKisa = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'];
const _aylar3 = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
const _aylarTam = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];

// Tek "bugün" kaynağı — Panel / Haftalık Plan / Geri Sayım aynı canlı referanstan
export function bugunBilgi(d = new Date()) {
  return { gunAdi: _gunAdlari[d.getDay()], gun: d.getDate(), ayAdi: _aylarTam[d.getMonth()],
    tarihUzun: _gunAdlari[d.getDay()] + ', ' + d.getDate() + ' ' + _aylarTam[d.getMonth()] };
}
// Bu haftanın 7 günü (Pzt→Paz) — Haftalık Plan için
export function buHafta(d = new Date()) {
  const pzt = new Date(d); pzt.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  const out = [];
  for (let i = 0; i < 7; i++) { const x = new Date(pzt); x.setDate(pzt.getDate() + i);
    out.push({ gun: _gunKisa[x.getDay()], tarih: x.getDate() + ' ' + _aylar3[x.getMonth()], bugun: x.toDateString() === d.toDateString() }); }
  return out;
}

export default { engine, persona, subjects, subjectMap, topics, dersKatalog, alanlar, katalogKonular, curriculum, atomKirilim, enZayifAtom, atomlarByKonu, reviewQueue, lastExam, questionBank, flashcards, catBankMat, masteryTier, irtProb, seciliSet, konularByDers, trNum, seviyeEsik, seviyeBilgi, bugunBilgi, buHafta };
