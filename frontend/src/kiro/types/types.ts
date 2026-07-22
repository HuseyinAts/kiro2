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
}
