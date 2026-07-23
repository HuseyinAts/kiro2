// ============================================================================
// KIRO2 — Veri Tipleri (TypeScript)
// Kaynak: kiro-data.js (prototip tek-kaynağı) — şekiller API sözleşmesiyle
// (`KIRO2 API Sozlesmesi.dc.html`) birebir aynıdır: üretimde bu tipler
// `fetch` yanıtlarını doğrular; ekran mantığı değişmez.
//
// Export → Endpoint eşlemesi (özet; tam hâli API Sözleşmesi belgesinde):
//   Persona          GET /me
//   Subject[]        GET /subjects
//   Topic[]          GET /topics
//   Curriculum       GET /curriculum/:ders
//   AtomKirilim      GET /topics/:konu/atoms
//   ReviewItem[]     GET /review/due   (+ POST /review/:id/grade)
//   Question         POST /questions/:id/answer · POST /cat/next
//   LastExam         GET /exams/last
//   SeviyeBilgi      GET /level
//   Engine           GET /engine
// ============================================================================

// ---------- Çekirdek kimlikler ----------

/** Sayısal persona dersleri (subjects/topics/curriculum bu anahtarları kullanır) */
export type SubjectKey = 'mat' | 'fiz' | 'kim' | 'biy' | 'tur';

/** Alan-üstü katalog dersleri (EA/Sözel dahil — dersKatalog) */
export type KatalogKey = SubjectKey | 'edb' | 'tar' | 'cog' | 'fel' | 'din';

export type AlanKey = 'say' | 'ea' | 'soz';

export type TopicDurum = 'zayif' | 'gelisiyor' | 'iyi' | 'guclu';

export type NodeDurum = 'done' | 'current' | 'open' | 'locked';

export type MasteryTierKey = 'tanidik' | 'yetkin' | 'usta' | 'fethedildi';

// ---------- GET /engine ----------

export interface Engine {
  model: string;
  bankSize: number;
  motorlar: string[]; // ['CAT/IRT', 'FSRS', 'BKT']
  roller: string[];
}

// ---------- GET /me ----------

export interface Persona {
  ad: string;
  adKisa: string;
  bas: string; // baş harfler, avatar
  sinif: string;
  seri: number;
  seriRekor: number;
  xp: number;
  seviye: number;
  hedefBolum: string;
  hedefUni: string;
  hedefSiralama: number;
  guncelSiralama: number;
  yksTarihi: string; // ISO 'YYYY-MM-DD'
  gunlukHedefDk: number;
  bugunCozulenDk: number;
}

// ---------- GET /subjects ----------

export interface Subject {
  key: SubjectKey;
  ad: string;
  renk: string; // KOYU-zemin parlak paleti; açık panelde tokens.color.subject.light kullan
  glow: string;
  tur: 'TYT' | 'AYT' | 'AYT+TYT' | 'TYT+AYT';
  hakimiyet: number; // 0-100 birleşik
  theta: number;     // IRT yetenek kestirimi (-3..+3)
  bkt: number;       // BKT p(biliniyor) 0..1
}

export type SubjectMap = Record<SubjectKey, Subject>;

// ---------- GET /topics ----------

export interface Topic {
  ders: SubjectKey;
  ad: string;
  hakimiyet: number; // 0-100 (BKT)
  durum: TopicDurum;
}

// ---------- Alan kütüphanesi ----------

export interface DersKatalogEntry {
  ad: string;
  renk: string;
  tur: string;
  konuSayisi: number;
  ornek: string[];
}

export interface Alan {
  key: AlanKey;
  ad: string;
  renk: string;
  ozet: string;
  ayt: KatalogKey[];
}

/** GET /katalog/:ders/konular — persona-BAĞIMSIZ konu envanteri (EA/Sözel; hakimiyet yok) */
export type KatalogKonular = Partial<Record<KatalogKey, string[]>>;

/** GET /katalog/:ders/uniteler — EA/Sözel ünite ağacı (katalogKonular'ın kırılımı) */
export interface KatalogUnite {
  no: number;
  ad: string;
  konular: string[];
}
export type KatalogUniteler = Partial<Record<KatalogKey, KatalogUnite[]>>;

// ---------- Öğretmen yüzü ----------

/** GET /class/:id/roster — sınıf listesi (öğretmen; risk amber, alarm değil) */
export interface SinifOgrenci {
  no: number;
  ad: string;
  theta: number;      // IRT kestirimi (-3..+3)
  hakimiyet: number;  // genel %
  risk: string | null;
  sonAktif: string;
}

// ---------- Ödevler ----------

/** Geciken teslim yine de 'bekliyor' durumundadır — kaygı-duyarlı sözleşme (alarm dili yok) */
export type OdevDurum = 'acik' | 'bekliyor' | 'tamam';

/** GET /assignments (öğrenci) · POST /assignments (öğretmen) */
export interface Odev {
  id: string;
  baslik: string;
  ders: SubjectKey;
  konu: string;
  atayan: string;
  adet: number;
  yapilan: number;
  dakika: number;
  teslim: string;
  kalan: string | null;
  durum: OdevDurum;
  /** true → set sunucuda θ'ya göre kişiye özel seçilir */
  kisisel: boolean;
}

// ---------- Kimlik (POST /auth/*) ----------

export interface AuthTokens {
  token: string;
  refresh: string;
}

export interface LoginRequest { eposta: string; sifre: string }
export interface RegisterRequest extends LoginRequest { ad: string }

// ---------- GET /review/due (FSRS) ----------

export interface ReviewItem {
  ders: SubjectKey;
  konu: string;
  stabilite: number;         // bellek izi ömrü (gün)
  guclukFSRS: number;        // 0..10
  hatirlanabilirlik: number; // R(t) anlık %
  dueIn: number;             // gün (0 = bugün)
  kart: number;
  gecmisNot: 'kolay' | 'iyi' | 'zor';
}

export interface Flashcard {
  ders: SubjectKey;
  konu: string;
  front: string;
  back: string;
}

// ---------- GET /exams/last ----------

export interface ExamSection {
  ad: string;
  soru: number;
  dogru: number;
  yanlis: number;
  bos: number;
  net: number;
}

export interface LastExam {
  ad: string;
  tarih: string; // ISO
  tip: string;
  tahminiSiralama: number;
  tyt: ExamSection[];
  ayt: ExamSection[];
  /** Prototipte getter — API'de düz sayı döner */
  tytNet: number;
  aytNet: number;
  /** Sınav Sonuç: önceki denemeye net farkı (sunucu; yoksa chip gizlenir) */
  trendNet?: number;
  /** Sınav Sonuç: AI analizi tam metni (sunucu/AI proxy — istemci şablon doldurmaz) */
  aiOzet?: string;
}

// ---------- Soru bankası / CAT ----------

export interface Question {
  id: string;
  /** Sayısal dersleri + EA/Sözel katalog dersleri (edb/tar/cog/fel) */
  ders: KatalogKey;
  konu: string;
  b: number;    // IRT güçlük (-2..+2)
  a: number;    // ayırt edicilik
  sure: number; // ort. çözüm süresi (sn)
  soru: string;
  secenekler: string[];
  dogru: number; // doğru şıkkın indeksi — ÜRETİMDE İSTEMCİYE GÖNDERİLMEZ (sunucu doğrular)
  cozum: string[];
  neden: string;
}

/** CAT yerleştirme maddesi (catBankMat) */
export interface CatItem {
  /** maddeId — idempotent cevap gönderimi (sunucu; mock atar) */
  id?: string;
  b: number;
  konu: string;
  soru: string;
  secenekler: string[];
  dogru: number; // üretimde istemciye gönderilmez
}

// ---------- GET /curriculum/:ders ----------

export interface KonuNode {
  ad: string;
  durum: NodeDurum;
}

export interface CurriculumUnit {
  no: number;
  ad: string;
  durum: NodeDurum;
  progress: string; // 'x/y'
  konular: KonuNode[];
}

export interface CurriculumDers {
  est: string; // '~3 hafta'
  done: number;
  total: number;
  next: { q: number; min: number };
  units: CurriculumUnit[];
}

export type Curriculum = Record<SubjectKey, CurriculumDers>;

// ---------- GET /topics/:konu/atoms ----------

export interface Atom {
  ad: string;
  hakimiyet: number; // 0-100
  /** En zayıf (min hâkimiyet) atom SUNUCU yanıtında işaretlenir — istemci min-hesabı YAPMAZ */
  enZayif?: boolean;
}

export interface AtomKirilim {
  ders: SubjectKey;
  konu: string;
  kavram: string;
  atomlar: Atom[];
}

// ---------- GET /plan/week (Faz 4 sözleşmesi — şimdilik mock katmanı) ----------
// Plan motoru sunucuda kurar (kanon: motorlar sunucuda; istemci blok kaydırmaz).
// Mock kompozisyonu (reviewQueue + topics) YALNIZ mock katmanında yaşar, üretim
// koduna sızmaz — ekran her zaman api-client'tan okur.

/** Plan bloğu türü — tag + renk + hedef rota bundan türer */
export type PlanBlokTur = 'calisma' | 'tekrar' | 'deneme' | 'analiz' | 'mola';

export interface PlanBlok {
  tur: PlanBlokTur;
  /** 'calisma' bloğunda ders rengi/adı için (diğer türlerde yok) */
  ders?: SubjectKey;
  baslik: string;    // kart başlığı (konu adı ya da sabit metin)
  meta: string;      // '12 soru · ~30 dk' vb. (birebir kopya)
  dk: number;        // süre (dakika) — sütun toplamı için
  hedefRota: string; // '/soru-cozme' | '/tekrar' | '/mola' vb.
}

export interface PlanGun {
  gun: string;   // 'Pzt'
  tarih: string; // '29 Haz'
  bugun: boolean;
  bloklar: PlanBlok[]; // boş → "Serbest" (doldurulmaz)
}

export interface PlanWeek {
  gunler: PlanGun[];
  aralik: string;       // '29 Haz – 5 Tem'
  gunlukHedefDk: number;
}

// ---------- GET /level ----------

export interface MasteryTier {
  key: MasteryTierKey;
  label: string;
  min: number;
  max: number;
}

export interface SeviyeBilgi {
  seviye: number;
  mevcutEsik: number;
  sonrakiEsik: number;
  span: number;
  ilerleme: number; // 0..1
  kalanXp: number;
}

// ============================================================================
// SPRINT8 · Grup 6 — Oyunlaştırma (Lig · Düello · Arkadaş Serisi · Seri Dondurma)
// Şekiller api-client sözleşmesiyle birebir. Motorlar/otorite SUNUCUDA:
//   - Lig sıralaması + tier eşikleri sunucuda (istemci rank hesaplamaz)
//   - Düello: puan/tur-sonucu/skor/elo SUNUCUDAN (mock'ta bile izole server-sim)
//   - Seri dondurma: freeze mekaniği sunucuda (mock: buildMockStreak)
// ============================================================================

// ---------- Lig (GET /api/v1/leagues/current — snake→camel map) ----------

/** Lig sıralaması satırı — trend/seviye/rank sunucudan (istemci sıralama YAPMAZ) */
export interface LeagueStanding {
  studentId: string;
  ad: string;
  ini: string;               // baş harfler (avatar)
  xp: number;                // haftalık XP
  rank: number;
  seviye: number;
  trend: 'up' | 'down' | 'same';
  benMi: boolean;
}

export interface LeagueData {
  tier: string;              // 'Zümrüt Lig'
  rank: number;              // öğrencinin tier içi sırası
  haftalikXp: number;
  tierToplam: number;        // tier'daki toplam oyuncu
  haftaBitisText: string;    // '2 gün 14 saat'
  /** Yükselme/düşme zon eşikleri (rank) — sunucu (istemci hesaplamaz) */
  zonEsik: { yukselme: number; dusme: number };
  senVsDun: { buHafta: number; gecenHafta: number };
  oduller: string[];
  standings: LeagueStanding[];
}

// ---------- Düello (GERÇEK WIRING — /api/v1/duel/*) ----------

/** Düello sorusu — STRIP'li (doğru şık İSTEMCİYE SIZMAZ; sunucu doğrular) */
export interface DuelQuestion {
  order: number;
  id: string;
  soru: string;
  secenekler: string[];
  sure: number; // saniye
}

export interface DuelMatch {
  sessionId: string;
  durum: 'matched' | 'queued';
  rakip: { ad: string; ini: string; seviye: number };
  mod: string;        // ders/konu
  toplamTur: number;
}

/** Tur kazananı — SUNUCU-OTORİTE (her iki oyuncunun sonucundan türer; ekran HESAPLAMAZ) */
export type DuelTurSonucu = 'me' | 'opp' | 'draw';

/** Cevap sonucu — benDogru/puan/turSonucu SUNUCUDAN (ekran doğruluğu HESAPLAMAZ) */
export interface DuelAnswerResult {
  turTamam: boolean;
  soruOrder: number;
  benPuan: number;
  rakipPuan: number;
  benDogru: boolean;
  /** Bu turun kazananı — sunucu (mock: server-sim izole) hesaplar; ekran yanıttan okur */
  turSonucu: DuelTurSonucu;
}

export interface DuelResult {
  sessionId: string;
  bitti: boolean;
  benSkor: number;
  rakipSkor: number;
  kazandin: boolean;
  berabere: boolean;
  eloDelta: number;
}

export interface DuelRating {
  elo: number;
  galibiyet: number;
  maglubiyet: number;
  beraberlik: number;
}

/** duelOpponent mock anahtarı (Mert K. / MK / seviye) */
export interface DuelOpponent {
  ad: string;
  ini: string;
  seviye: number;
}

// ---------- Arkadaş Serisi (/birlikte-streak'e yakın + friend-gap) ----------

export interface Friend {
  id: string;
  ad: string;
  sinif: string;
  ini: string;
  avatarGradient: string;
  seri: number;
  xp: number;
  durum: 'calisti' | 'henuz';
  tebrikGonderildi: boolean;
}

export interface CoopQuest {
  baslik: string;
  hedef: number;
  ilerleme: number;
  benPay: number;
  partnerPay: number;
  kalanGun: number;
  odul: string;
}

export interface FriendsData {
  ortakSeri: {
    partner: string;
    sayi: number;
    benBugun: boolean;
    partnerBugun: boolean;
    nudgeDurum: 'idle' | 'sent';
  };
  gorev: CoopQuest;
  arkadaslar: Friend[];
}

// ---------- Seri Dondurma (backend YOK — freeze mekaniği mock) ----------

export interface StreakDay {
  label: string;
  durum: 'done' | 'freeze' | 'today';
}

export interface StreakData {
  seri: number;
  rekor: number;
  dondurmaHak: number;
  hafta: StreakDay[];
}

// ============================================================================
// SPRINT9 · Grup 7-A — Rol panelleri (Veli · Öğretmen · Öğrenci-Özeti · Sınıf)
// Şekiller api-client sözleşmesiyle birebir. Rol-bazlı SALT-OKUR paneller.
// SUNUCU-OTORİTE: öğrenci net/hâkimiyet/risk/theta SUNUCUDA hesaplanır; istemci
// bu türevleri ÜRETMEZ — mock'ta bile veri kiro-data'dan okunur, ekranda değil.
// ============================================================================

/** Haftalık aktivite çubuğu — Veli + Öğretmen + Öğrenci-Özeti paylaşır (WeeklyActivityBars) */
export interface HaftaGun {
  label: string;   // 'Pzt'
  dk: number;      // o günkü çalışma (dakika) — sunucudan
  aktif: boolean;  // çalışma var mı (dk>0) — sunucu türetir; ekran metrik hesaplamaz
}

/** Ders-düzeyi birleşik hâkimiyet (Veli ders ilerleme + Öğretmen sınıf hâkimiyet + Öğrenci-Özeti) */
export interface DersIlerleme {
  ders: string;      // 'Matematik' (görünen ad; renk ekranda ders→palet)
  hakimiyet: number; // 0-100 (sunucu birleşik kestirim)
}

// ---------- Veli Paneli (rol=veli; çocuk verisi SALT-OKUR) ----------

export interface VeliCocuk {
  id: string;
  ad: string;
  sinif: string;
  hedef: string;
  ini: string;            // baş harfler (avatar)
  avatarGradient: string; // CSS gradient string
}

export type VeliUyariTip = 'success' | 'risk' | 'sevinc';
/** Uyarı & öne çıkanlar — risk = amber (alarm değil), sevinç = kutlama tonu */
export interface VeliUyari {
  tip: VeliUyariTip;
  metin: string;
}

/** Son sınav özet satırı (veli görünümü) */
export interface SinavOzet {
  ders: string;
  tarih: string;  // '2 gün önce' / ISO
  net: number;
  tur: string;    // 'TYT' | 'AYT' vb.
}

export interface VeliDashboard {
  cocuklar: VeliCocuk[];
  aktifCocukId: string;
  kpi: {
    cozulenSoru: number;
    cozulenSoruDelta: number;
    cozulenDeneme: number;
    cozulenDenemeDelta: number;
    planUyumu: number;   // %
    netDegisimi: number; // +8.5
  };
  haftalik: HaftaGun[];
  haftaToplamSa: number;  // hafta toplamı (saat)
  haftaTrend: string;     // '+1,1 sa'
  dersIlerleme: DersIlerleme[];
  sonSinavlar: SinavOzet[];
  uyarilar: VeliUyari[];
  /** Premium ROI kanıt bloğu (veli satın-alma yüzeyi) */
  roi: {
    netArtisi: number;
    planUyum: number;
    seri: number;
    haftaOrtDk: number;
  };
  premium: {
    fiyatAy: number;
    indirimYuzde: number;
    maddeler: string[];
  };
}

// ---------- Öğretmen Paneli (rol=öğretmen; öğrenci metrik SALT-OKUR) ----------

export interface OgretmenSinif {
  id: string;
  ad: string;      // '12-A'
  seviye: string;  // '12. Sınıf'
  ders: string;    // 'Sayısal'
  ogrenciSayisi: number;
}

export type OgrenciRisk = 'yok' | 'dikkat';
export interface OgretmenOgrenci {
  id: string;
  ad: string;
  ini: string;
  ortNet: number;
  hakimiyet: number;  // 0-100
  sonAktif: string;
  risk: OgrenciRisk;  // sunucu türetir; öğrenciye bayrak gösterilmez
  odevDurum: string;
}

/** Dikkat gerektiren öğrenci kartı (yalnız yetişkine görünür) */
export interface DikkatKarti {
  tip: string;   // risk türü etiketi
  ad: string;
  metin: string;
}

export interface OgretmenPanel {
  siniflar: OgretmenSinif[];
  aktifSinifId: string;
  kpi: {
    ogrenci: number;
    ogrenciDelta: number;
    gecikmisOdev: number;
    ortNet: number;
    ortNetDelta: number;
  };
  ogrenciler: OgretmenOgrenci[];
  dikkat: DikkatKarti[];
  sinifHakimiyet: DersIlerleme[];
}

// ---------- Öğrenci Özeti (rol=öğretmen; TEK öğrenci SALT-OKUR) ----------

export type OgrenciDurum = 'saglikli' | 'dikkat';
export interface OgrenciOzeti {
  id: string;
  ad: string;
  ini: string;
  sinif: string;
  ders: string;
  sonAktivite: string;
  durum: OgrenciDurum;
  kpi: {
    net: number;
    hakimiyet: number;
    seri: number;
    cozulen: number;
  };
  haftalik: HaftaGun[];
  dersHakimiyet: DersIlerleme[];
  /** Yalnız risk durumunda dolu (amber şerit metni) */
  riskMetni?: string;
}

// ---------- Sınıf Kurulumu (rol=öğretmen; katılım-kodu backend YOK → mock) ----------

export interface YeniSinif {
  ad: string;
  seviye: string;
  ders: string;
}
export interface KurulanSinif {
  id: string;
  ad: string;
  seviye: string;
  ders: string;
  katilimKodu: string;  // 6-haneli (server-sim; deterministik)
  katilimLink: string;
}

// ============================================================================
// SPRINT9-B · Grup 7-B — Veli Bağlama (KVKK) + Ödev Atama
// Şekiller api-client sözleşmesiyle birebir. SUNUCU-OTORİTE: bağlantı kodunun
// üretimi/doğrulaması, KVKK rıza kaydı ve θ-set kurulumu SUNUCUDA yapılır —
// istemci (mock'ta bile) kod üretmez, rızayı hesaplamaz, soru setini seçmez.
// ============================================================================

// ---------- Veli Bağlama (KVKK; kod-akışı mock — backend e-posta tabanlı) ----------

/** 6-hane bağlantı kodu doğrulama sonucu — SUNUCU doğrular (istemci kod üretmez).
 *  gecerli=false ise diğer alanlar boş bırakılır. */
export interface LinkCodeSonuc {
  gecerli: boolean;
  cocukAd?: string;
  cocukBas?: string;   // baş harfler (avatar)
  relationId?: string; // sonraki adım (rıza/poll) bu id ile ilerler (sunucudan)
}

/** Öğrenci tarafı bekleyen veli isteği — scope iki yönlü şeffaflık (görür/görmez) */
export interface PendingVeliIstek {
  relationId: string;
  veliAd: string;
  veliBas: string;     // baş harfler (avatar)
  scope: { gorur: string[]; gormez: string[] };
}

/** KVKK aydınlatma metni sürümü — rıza kaydında sunucu bu sürümü mühürler */
export interface KvkkNotice {
  version: string;
}

/** kiro-data.veliBaglama mock anahtarı (server-sim doğrulama + iki-taraf şeffaflık) */
export interface VeliBaglamaData {
  /** Geçerli 6-hane kod (server-sim; verifyLinkCode bununla deterministik karşılaştırır) */
  veliBaglamaKodu: string;
  cocukAd: string;
  cocukBas: string;
  veliAd: string;
  veliBas: string;
  /** Öğrenci tarafı bekleyen istek (getPendingParentRequest mock kaynağı) */
  pending: PendingVeliIstek;
  /** Veli tarafı rıza ekranı kapsam listeleri */
  scope: { gorur: string[]; gormez: string[] };
}

// ---------- Ödev Atama (Ödevlerim/SPRINT1 döngüsü; zengin-atama backend YOK → mock) ----------

/** Atama için konu atomu — zayıflık sıralı (sunucu sıralar; istemci sıralama YAPMAZ) */
export interface KonuAtom {
  id: string;
  ad: string;
  hakimiyet: number;                     // 0-100 (sınıf birleşik kestirim)
  durum: 'zayif' | 'gelisiyor' | 'iyi';
  soruHavuzuHazir: boolean;              // set kurulabilir mi (sunucu türetir)
}

/** Atama ekranı öğrenci satırı — SinifOgrenci + id + ini (avatar).
 *  net/hâkimiyet/theta/risk SUNUCUDAN; istemci türev üretmez. */
export interface AtamaOgrenci extends SinifOgrenci {
  id: string;
  ini: string;
}

/** Ödev atama formu — istemci YALNIZ formu gönderir; θ-set kurulumu SUNUCUDA
 *  (kisisel=true → her öğrencinin seti sunucuda θ'sına göre seçilir). */
export interface AtamaForm {
  konuId: string;
  adet: number;
  teslimTarihi: string;
  kisisel: boolean;
  ogrenciIds: string[];
}

/** kiro-data.odevAtama mock anahtarı (zayıflık-sıralı konular + zengin roster) */
export interface OdevAtamaData {
  konular: KonuAtom[];
  roster: AtamaOgrenci[];
}

// ---------- Canlı "bugün" yardımcıları ----------

export interface BugunBilgi {
  gunAdi: string;
  gun: number;
  ayAdi: string;
  tarihUzun: string;
}

export interface HaftaGunu {
  gun: string;   // 'Pzt'
  tarih: string; // '3 Tem'
  bugun: boolean;
}

// ---------- Yardımcı imzalar (kiro-data.js ile birebir) ----------

export interface KiroHelpers {
  masteryTier(pct: number): MasteryTier;
  irtProb(theta: number, a: number, b: number): number;
  seviyeBilgi(xp: number): SeviyeBilgi;
  enZayifAtom(kirilim: AtomKirilim): Atom;
  atomlarByKonu(konu: string): AtomKirilim | null;
  konularByDers(dersKey: SubjectKey): Topic[];
  seciliSet(dersKey: SubjectKey, n?: number, konu?: string): Question[];
  trNum(n: number): string;
  bugunBilgi(d?: Date): BugunBilgi;
  buHafta(d?: Date): HaftaGunu[];
}

/** Prototipteki window.__KIRO / kiro-data default export'un tam şekli */
export interface KiroData extends KiroHelpers {
  engine: Engine;
  persona: Persona;
  subjects: Subject[];
  subjectMap: SubjectMap;
  topics: Topic[];
  dersKatalog: Record<KatalogKey, DersKatalogEntry>;
  alanlar: Alan[];
  katalogKonular: KatalogKonular;
  curriculum: Curriculum;
  atomKirilim: AtomKirilim[];
  reviewQueue: ReviewItem[];
  lastExam: LastExam;
  questionBank: Question[];
  flashcards: Flashcard[];
  catBankMat: CatItem[];
  seviyeEsik: number[];
  katalogUniteler: KatalogUniteler;
  sinifRoster: SinifOgrenci[];
  odevler: Odev[];
  // --- SPRINT8 · Grup 6 mock anahtarları ---
  league: LeagueData;
  duelOpponent: DuelOpponent;
  friends: FriendsData;
  streak: StreakData;
  // --- SPRINT9 · Grup 7-A mock anahtarları ---
  veliDashboard: VeliDashboard;
  ogretmenPanel: OgretmenPanel;
  /** id → tek öğrenci özeti (öğretmen salt-okur görünümü) */
  ogrenciOzetleri: Record<string, OgrenciOzeti>;
  siniflar: OgretmenSinif[];
  // --- SPRINT9-B · Grup 7-B mock anahtarları ---
  veliBaglama: VeliBaglamaData;
  odevAtama: OdevAtamaData;
}
