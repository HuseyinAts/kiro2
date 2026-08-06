// ============================================================================
// KIRO2 — API Client (üretim başlangıcı)
// Sözleşme: KIRO2 API Sozlesmesi.dc.html — uçlar ve JSON şekilleri oradan;
// tipler ./types.ts'ten. İki mod:
//   'mock' — kiro-data.json'ı servisler (backend hazır olmadan ekran portu)
//   'live' — gerçek REST tabanı (baseUrl)
// Ekran kodu YALNIZ bu client'ı çağırır; mock→live geçişi tek konfigürasyon.
//
// [DIKKAT] Sunucu-otoriter kurallar (mock'ta simüle edilir, live'da sunucu yapar):
// - Soru doğrulama: `dogru` şıkkı ve çözümler istemciye YANIT SONRASI iner.
// - CAT madde seçimi + θ güncelleme, FSRS zamanlama, BKT güncelleme sunucuda.
// ============================================================================

import type {
  Engine, Persona, Subject, Topic, Curriculum, CurriculumDers, AtomKirilim,
  PlanWeek, PlanBlok, PlanGun,
  ReviewItem, LastExam, CatItem, SeviyeBilgi, SubjectKey, KiroData,
  KatalogKey,
  Question,
  Odev,
  SinifOgrenci,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  LeagueData,
  DuelQuestion, DuelMatch, DuelAnswerResult, DuelTurSonucu, DuelResult, DuelRating,
  FriendsData, StreakData,
  VeliDashboard, VeliCocuk, VeliUyari, SinavOzet, DersIlerleme, HaftaGun,
  OgretmenPanel, OgretmenSinif, OgretmenOgrenci, DikkatKarti,
  OgrenciOzeti, YeniSinif, KurulanSinif,
  LinkCodeSonuc, PendingVeliIstek, KvkkNotice,
  KonuAtom, AtamaOgrenci, AtamaForm,
  BildirimYanit, AlanKutuphaneData, SyncStatus,
  PlanTier, FaturaDonem, AbonelikData, OdemeOzeti, ThreeDSDurum, AbonelikYonetim,
  SohbetRol, SohbetMesaj, SohbetOturum, SohbetTeachingMode, SohbetStreamArgs, SohbetStreamHandlers,
  KiroRol, IlkHaftaResponse,
} from '../types';

// SPRINT8 · Grup 6 tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  LeagueStanding, LeagueData,
  DuelQuestion, DuelMatch, DuelAnswerResult, DuelTurSonucu, DuelResult, DuelRating, DuelOpponent,
  Friend, CoopQuest, FriendsData,
  StreakDay, StreakData,
} from '../types';

// SPRINT9 · Grup 7-A panel tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  HaftaGun, DersIlerleme,
  VeliDashboard, VeliCocuk, VeliUyari, VeliUyariTip, SinavOzet,
  OgretmenPanel, OgretmenSinif, OgretmenOgrenci, OgrenciRisk, DikkatKarti,
  OgrenciOzeti, OgrenciDurum, YeniSinif, KurulanSinif,
} from '../types';

// SPRINT9-B · Grup 7-B tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  LinkCodeSonuc, PendingVeliIstek, KvkkNotice, VeliBaglamaData,
  KonuAtom, AtamaOgrenci, AtamaForm, OdevAtamaData,
} from '../types';

// SPRINT10-A · Grup 8 (paylaşılan infra) tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  BildirimTon, Bildirim, BildirimGrup, BildirimYanit,
  ConnectivityState, CachedPack, SyncQueueItem, SyncStatus,
  AlanKutuphaneDers, AlanKutuphaneAlan, AlanKutuphaneData,
} from '../types';

// SPRINT10-B · Grup 8 (billing infra) tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  PlanTier, FaturaDonem, AbonelikPlan, AbonelikData,
  OdemeFaz, OdemeOzeti, KartFormState, ThreeDSDurum, OdemeYontem, Fatura, AbonelikYonetim,
} from '../types';

// SPRINT11 · AI Sohbet + Sokratik AI tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  SohbetRol, SohbetMesaj, SohbetOturum, SohbetTeachingMode,
  SohbetStreamArgs, SohbetStreamHandlers, SokratikSenaryo,
} from '../types';

// FAZ 3 KAPANIŞ · İlk Hafta + Rol tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  KiroRol, IlkHaftaGun, IlkHaftaKart, IlkHaftaOzet, IlkHaftaResponse,
} from '../types';

// ---------------------------------------------------------------------------
// Konfigürasyon
// ---------------------------------------------------------------------------

export interface KiroApiConfig {
  mode: 'mock' | 'live';
  /** live modda zorunlu, ör. 'https://api.kiro2.app/v1' */
  baseUrl?: string;
  /** mock modda veri kaynağı: import edilmiş kiro-data.json ya da fetch edilecek URL */
  mockData?: MockData | string;
  fetchImpl?: typeof fetch;
}

/** kiro-data.json'ın şekli (KiroData'nın salt-veri alt kümesi — fonksiyonlar hariç) */
export type MockData = Pick<KiroData,
  'engine' | 'persona' | 'subjects' | 'topics' | 'dersKatalog' | 'alanlar' | 'katalogKonular' |
  'katalogUniteler' | 'sinifRoster' | 'odevler' |
  'reviewQueue' | 'lastExam' | 'questionBank' | 'flashcards' | 'catBankMat' |
  'curriculum' | 'atomKirilim' | 'seviyeEsik' |
  'league' | 'duelOpponent' | 'friends' | 'streak' |
  'veliDashboard' | 'ogretmenPanel' | 'ogrenciOzetleri' | 'siniflar' |
  'veliBaglama' | 'odevAtama' |
  'bildirimler' | 'alanKutuphane' | 'cevrimdisi' |
  'abonelik' | 'abonelikYonetim' |
  'sohbet' | 'sokratik' |
  'ilkHafta' | 'rol'>;

let cfg: KiroApiConfig = { mode: 'mock' };
let mockCache: MockData | null = null;

export function configureKiroApi(next: KiroApiConfig): void {
  cfg = next;
  // Mock verisi KLONLANIR: her config çağrısı özel, değiştirilebilir bir oturum-store'u
  // verir (mutasyonlar paylaşılan import'u kirletmez + testler arası izolasyon). Bu,
  // postAtama gibi server-sim mutasyonların (odevler'e yazma) getAssignments'a
  // yansımasını sağlayan Ödev Atama↔Ödevlerim döngüsünün temelidir.
  mockCache = typeof next.mockData === 'object' && next.mockData
    ? (structuredClone(next.mockData) as MockData)
    : null;
}

async function mock(): Promise<MockData> {
  if (mockCache) return mockCache;
  const src = cfg.mockData;
  if (typeof src === 'string') {
    const f = cfg.fetchImpl ?? fetch;
    mockCache = (await (await f(src)).json()) as MockData;
    return mockCache;
  }
  throw new Error('KiroApi: mock modda mockData verilmedi (kiro-data.json import edin ya da URL geçin).');
}

// B2 (Faz 4): tek konvansiyon — her istek yolu '/api/v1' ile başlar. Zaten prefixli
// (duel/league/kvkk/teacher) yollar idempotent geçer; çıplak yollar (/me,/subjects…)
// normalize edilir. baseUrl = origin (VITE_API_URL DEĞİL — same-origin cookie zorunlu).
function apiPath(path: string): string {
  return path.startsWith('/api/v1') ? path : '/api/v1' + path;
}

// B1 (Faz 4): 401 → gerçek app'in /login akışına yönlendir (apiHelpers ile aynı sözleşme).
function redirectToLogin(): void {
  if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

async function live<T>(path: string, init?: RequestInit): Promise<T> {
  if (cfg.baseUrl == null) throw new Error('KiroApi: live modda baseUrl zorunlu.');
  const f = cfg.fetchImpl ?? fetch;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  // Auth = httpOnly COOKIE (Bearer/getToken düştü). credentials:'include' → cookie gider.
  const res = await f(cfg.baseUrl + apiPath(path), {
    ...init,
    credentials: 'include',
    headers: { ...headers, ...(init?.headers as object) },
  });
  if (res.status === 401) { redirectToLogin(); throw new KiroApiError(401, path); }
  if (!res.ok) throw new KiroApiError(res.status, path);
  // Zarf çöz (merkezi): {success,data}|{data}|ham → gövde. Zaten çözen uçlar idempotent.
  return unwrapData(await res.json()) as T;
}

export class KiroApiError extends Error {
  constructor(public status: number, public path: string) {
    super('KiroApi ' + status + ' — ' + path);
  }
}

// ---------------------------------------------------------------------------
// GET uçları
// ---------------------------------------------------------------------------

export async function getEngine(): Promise<Engine> {
  return cfg.mode === 'mock' ? (await mock()).engine : live<Engine>('/engine');
}

export async function getMe(): Promise<Persona> {
  return cfg.mode === 'mock' ? (await mock()).persona : live<Persona>('/me');
}

export async function getSubjects(): Promise<Subject[]> {
  return cfg.mode === 'mock' ? (await mock()).subjects : live<Subject[]>('/subjects');
}

export async function getTopics(ders?: SubjectKey): Promise<Topic[]> {
  if (cfg.mode === 'mock') {
    const t = (await mock()).topics;
    return ders ? t.filter((x) => x.ders === ders) : t;
  }
  return live<Topic[]>('/topics' + (ders ? '?ders=' + ders : ''));
}

export async function getCurriculum(ders: SubjectKey): Promise<CurriculumDers> {
  if (cfg.mode === 'mock') return (await mock()).curriculum[ders];
  return live<CurriculumDers>('/curriculum/' + ders);
}

export async function getAllCurriculum(): Promise<Curriculum> {
  if (cfg.mode === 'mock') return (await mock()).curriculum;
  return live<Curriculum>('/curriculum');
}

export async function getTopicAtoms(konu: string): Promise<AtomKirilim | null> {
  if (cfg.mode === 'mock') {
    const found = (await mock()).atomKirilim.find((x) => x.konu === konu);
    return found ? markEnZayif(found) : null;
  }
  return live<AtomKirilim | null>('/topics/' + encodeURIComponent(konu) + '/atoms');
}

/** Sunucu-otoriter simülasyon: en zayıf (min hâkimiyet) atomu işaretle.
 *  İstemci min-hesabı YAPMAZ — SPRINT5 açık-nokta 2 (enZayif sunucudan gelir). */
export function markEnZayif(k: AtomKirilim): AtomKirilim {
  if (k.atomlar.length === 0) return k;
  const min = Math.min(...k.atomlar.map((a) => a.hakimiyet));
  let marked = false;
  return {
    ...k,
    atomlar: k.atomlar.map((a) => {
      const enZayif = !marked && a.hakimiyet === min;
      if (enZayif) marked = true;
      return { ...a, enZayif };
    }),
  };
}

// ---------------------------------------------------------------------------
// Haftalık Plan — GET /plan/week (openapi'de YOK; plan motoru Faz 4 sözleşmesi)
// Mock: reviewQueue (due) + topics (zayıf) + sabit iskelet kompozisyonu.
// Bu kompozisyon YALNIZ mock katmanında yaşar — üretim koduna sızmaz.
// ---------------------------------------------------------------------------

/** Deterministik mock hafta (DC ile birebir: Pzt 29 Haz bugün → Paz 5 Tem). */
export function buildMockPlanWeek(d: MockData): PlanWeek {
  const due = (d.reviewQueue ?? []).filter((r) => r.dueIn === 0);
  const tekrar = (r: ReviewItem): PlanBlok => ({
    tur: 'tekrar', ders: r.ders, baslik: `${r.konu} tekrarı`,
    meta: `${r.kart} kart · ~${r.kart * 4} dk`, dk: r.kart * 4, hedefRota: '/tekrar',
  });
  const calisma = (ders: SubjectKey, konu: string): PlanBlok => ({
    tur: 'calisma', ders, baslik: konu, meta: '12 soru · ~30 dk', dk: 30, hedefRota: '/soru-cozme',
  });
  const deneme: PlanBlok = { tur: 'deneme', baslik: 'Harmanlanmış Deneme', meta: 'TYT + AYT · ~135 dk', dk: 135, hedefRota: '/deneme' };
  const analiz: PlanBlok = { tur: 'analiz', baslik: 'Deneme analizi', meta: 'net + zayıf konu · ~25 dk', dk: 25, hedefRota: '/sinav-sonuc' };
  const mola: PlanBlok = { tur: 'mola', baslik: 'Nefes molası', meta: 'sakinleş · ~10 dk', dk: 10, hedefRota: '/mola' };
  const gunler: PlanGun[] = [
    { gun: 'Pzt', tarih: '29 Haz', bugun: true, bloklar: [calisma('mat', 'Türev'), ...(due[0] ? [tekrar(due[0])] : [])] },
    { gun: 'Sal', tarih: '30 Haz', bugun: false, bloklar: [calisma('kim', 'Gazlar'), ...(due[1] ? [tekrar(due[1])] : [])] },
    { gun: 'Çar', tarih: '1 Tem', bugun: false, bloklar: [calisma('fiz', 'Elektrik'), ...(due[2] ? [tekrar(due[2])] : [])] },
    { gun: 'Per', tarih: '2 Tem', bugun: false, bloklar: [calisma('kim', 'Kimyasal Tepkimeler')] },
    { gun: 'Cum', tarih: '3 Tem', bugun: false, bloklar: [calisma('mat', 'Limit ve Süreklilik')] },
    { gun: 'Cmt', tarih: '4 Tem', bugun: false, bloklar: [deneme] },
    { gun: 'Paz', tarih: '5 Tem', bugun: false, bloklar: [analiz, mola] },
  ];
  return { gunler, aralik: '29 Haz – 5 Tem', gunlukHedefDk: d.persona.gunlukHedefDk ?? 0 };
}

export async function getPlanWeek(): Promise<PlanWeek> {
  if (cfg.mode === 'mock') return buildMockPlanWeek(await mock());
  return live<PlanWeek>('/api/v1/plan/week');
}

export async function getReviewDue(): Promise<ReviewItem[]> {
  if (cfg.mode === 'mock') return (await mock()).reviewQueue.filter((r) => r.dueIn === 0);
  return live<ReviewItem[]>('/review/due');
}

/** EA/Sözel dahil persona-bağımsız konu envanteri */
export async function getKatalogKonular(ders: KatalogKey): Promise<string[]> {
  if (cfg.mode === 'mock') return (await mock()).katalogKonular?.[ders] ?? [];
  return live<string[]>('/katalog/' + ders + '/konular');
}

export async function getLastExam(): Promise<LastExam> {
  return cfg.mode === 'mock' ? (await mock()).lastExam : live<LastExam>('/exams/last');
}

export async function getLevel(): Promise<SeviyeBilgi> {
  if (cfg.mode === 'mock') {
    const d = await mock();
    // mock persona xp'yi DOLU tutar; ?? yalniz tip kapatici (uretim yolu degil).
    return seviyeBilgiFrom(d.seviyeEsik, d.persona.xp ?? 0);
  }
  return live<SeviyeBilgi>('/level');
}

/** Soru seti maddesi — sunucu-otoriter: dogru/cozum/neden İÇERMEZ (postAnswer'da iner). */
export type SoruSetItem = Pick<Question, 'id' | 'ders' | 'konu' | 'b' | 'soru' | 'secenekler'>;

/** Günlük/konu seti (Soru Çözme). Mock: questionBank filtre + STRIP; live: GET /questions/set. */
export async function getQuestionSet(ders: KatalogKey = 'mat', konu?: string): Promise<SoruSetItem[]> {
  if (cfg.mode === 'mock') {
    const bank = (await mock()).questionBank.filter((q) => q.ders === ders);
    const sirali = konu ? [...bank].sort((a, b) => Number(b.konu === konu) - Number(a.konu === konu)) : bank;
    // Açık pick → dogru/cozum/neden asla kopyalanmaz (istemciye sızmaz).
    return sirali.map(({ id, ders: d, konu: k, b, soru, secenekler }) => ({ id, ders: d, konu: k, b, soru, secenekler }));
  }
  const q = konu ? '?ders=' + ders + '&konu=' + encodeURIComponent(konu) : '?ders=' + ders;
  return live<SoruSetItem[]>('/questions/set' + q);
}

// ---------------------------------------------------------------------------
// POST uçları — sunucu-otoriter; mock yalnız ekran geliştirmeye yetecek kadar
// ---------------------------------------------------------------------------

export interface AnswerResult {
  correct: boolean;
  /** Doğru şıkkın indeksi — yalnız YANITTAN SONRA gelir */
  dogru: number;
  cozum: string[];
  neden: string;
  /** Sunucunun güncellediği kestirimler */
  theta?: number;
  bkt?: number;
  xpKazanilan?: number;
  // --- Neden Geri Bildirim sağ ray (sunucudan; ekran salt-okur) ---
  /** "{n} gün sonra tekrar göreceksin" — FSRS zamanlaması sunucuda */
  fsrsNextDays?: number;
  /** Kavram hâkimiyeti etkisi (yanlışta trend down) */
  mastery?: { konu: string; pct: number; trend: 'up' | 'stable' | 'down' };
  /** İlgili kavramlar (renk noktalı) — /topics/{konu}/atoms ilişkilerinden */
  relatedConcepts?: { ad: string; renk: string }[];
  /** Yanlış senaryoda "NEDEN {Y} YANLIŞ" gövdesi (sunucu şablonu; doğruda gelmez) */
  nedenYanlis?: string;
}

export async function postAnswer(questionId: string, secilen: number): Promise<AnswerResult> {
  if (cfg.mode === 'mock') {
    const q = (await mock()).questionBank.find((x) => x.id === questionId);
    if (!q) throw new KiroApiError(404, '/questions/' + questionId + '/answer');
    const dogru = secilen === q.dogru;
    return {
      correct: dogru, dogru: q.dogru, cozum: q.cozum, neden: q.neden, xpKazanilan: dogru ? 10 : 2,
      fsrsNextDays: dogru ? 5 : 2,
      mastery: { konu: q.konu, pct: dogru ? 72 : 58, trend: dogru ? 'up' : 'down' },
      relatedConcepts: [
        { ad: 'Bileşke fonksiyon türevi', renk: color_subject_mor },
        { ad: 'Üstel fonksiyon türevi', renk: color_subject_mavi },
        { ad: 'Çarpım kuralı', renk: color_subject_yesil },
      ],
      nedenYanlis: dogru ? undefined : `${q.secenekler[secilen] ?? '—'} işaretledin — doğrusu ${q.secenekler[q.dogru] ?? '—'}. Aşağıdaki adımlar nerede saptığını tam olarak gösteriyor.`,
    };
  }
  return live<AnswerResult>('/questions/' + questionId + '/answer', { method: 'POST', body: JSON.stringify({ secilen }) });
}

// İlgili-kavram nokta renkleri (mock; üretimde /topics/{konu}/atoms'tan)
const color_subject_mor = '#8B5CF6';
const color_subject_mavi = '#3B82F6';
const color_subject_yesil = '#1FB683';

/** Uygulanan madde (motor paneli + θ yakınsaması) */
export interface CatUygulanan { b: number; ok: boolean; theta: number; se: number }
export interface CatNextArgs { oturumId?: string; maddeId?: string; secim?: number | null; madde?: number }
export interface CatNextResult {
  item: Omit<CatItem, 'dogru'>;
  theta: number; se: number; done: boolean;
  seviye: 'zayif' | 'orta' | 'guclu';
  topPct: number; netTahmini: number; madde: number;
  /** Motor paneli değerleri — SUNUCUDAN (istemci IRT/eşik hesaplamaz) */
  kalanTahmini: number; guvenilirlik: number;
  uygulananlar: CatUygulanan[];
}

/** Adaptif yerleştirme — θ/SE/madde-seçimi/durdurma SUNUCUDA (istemci IRT HESAPLAMAZ).
 *  args.madde = istemcinin cevapladığı madde sayısı; sunucu yanıtı motor panelini çizer. */
export async function postCatNext(args: CatNextArgs = {}): Promise<CatNextResult> {
  if (cfg.mode === 'mock') {
    const bank = (await mock()).catBankMat;
    const n = Math.min(12, Math.max(0, args.madde ?? 0)); // uygulanan madde sayısı
    // Sunucu-simülasyon: yakınsayan θ/SE (deterministik; istemci hesaplamaz)
    const uygulananlar: CatUygulanan[] = Array.from({ length: n }, (_, i) => ({
      b: bank[i % bank.length]!.b,
      ok: i % 3 !== 2,
      theta: Math.min(0.62, 0.08 + (i + 1) * 0.045),
      se: Math.max(0.24, 0.72 - (i + 1) * 0.04),
    }));
    const theta = n === 0 ? 0 : uygulananlar[n - 1]!.theta;
    const se = n === 0 ? 0.72 : uygulananlar[n - 1]!.se;
    const done = (n >= 1 && se < 0.30) || n >= 12;
    const { dogru: _g, ...ham } = bank[n % bank.length]!;
    const seviye = theta < -0.3 ? 'zayif' : theta < 0.5 ? 'orta' : 'guclu';
    return {
      item: { ...ham, id: 'mad-' + (n + 1) }, theta, se, done, seviye,
      topPct: Math.max(1, Math.round(30 - theta * 14)),
      netTahmini: Math.round(28 + theta * 8),
      kalanTahmini: done ? 0 : Math.max(0, Math.ceil((se - 0.30) / 0.04)),
      guvenilirlik: Math.round((1 - se * se) * 100),
      madde: n, uygulananlar,
    };
  }
  return live<CatNextResult>('/cat/next', { method: 'POST', body: JSON.stringify(args) });
}

/** Sınav Sonuç — GET /exams/:id; mock trend/AI-özeti ekler (sunucu-otoriter alanlar). */
export async function getExamResult(id?: string): Promise<LastExam> {
  if (cfg.mode === 'mock') {
    const e = (await mock()).lastExam;
    const secs = [...e.tyt, ...e.ayt];
    const strong = secs.reduce((a, b) => (b.net > a.net ? b : a), secs[0]!);
    const weak = secs.reduce((a, b) => (b.net / Math.max(1, b.soru) < a.net / Math.max(1, a.soru) ? b : a), secs[0]!);
    const netStr = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 }).format(e.tytNet + e.aytNet);
    return { ...e, trendNet: 8.5, aiOzet: `Toplam netin ${netStr} — en güçlü dersin ${strong.ad}. En çok gelişim alanın ${weak.ad}; zayıf konularını tekrar listene ekledim.` };
  }
  return live<LastExam>('/exams/' + (id ?? 'last'));
}

/** FSRS 4 derece (Anki): tekrar=again · zor=hard · iyi=good · kolay=easy */
export type ReviewGrade = 'tekrar' | 'zor' | 'iyi' | 'kolay';

/** Kart-bazlı derecelendirme — kanon: POST /review/{kartId}/grade (konu değil; aynı konudan çok kart) */
export async function postReviewGrade(kartId: string, grade: ReviewGrade): Promise<{ nextDueIn: number }> {
  if (cfg.mode === 'mock') {
    // FSRS aralığı SUNUCUDA hesaplanır; mock kaba bir aralık döner (istemci hesaplamaz)
    const next = grade === 'kolay' ? 12 : grade === 'iyi' ? 6 : grade === 'zor' ? 3 : 0;
    return { nextDueIn: next };
  }
  return live<{ nextDueIn: number }>('/review/' + encodeURIComponent(kartId) + '/grade', { method: 'POST', body: JSON.stringify({ grade }) });
}

/** Tekrar oturumu kartı — aralık önizlemeleri SUNUCUDAN (FSRS projeksiyonu; istemci hesaplamaz) */
export interface ReviewCard {
  id: string;
  ders: SubjectKey;
  konu: string;
  front: string;
  back: string;
  previews: { tekrar: string; zor: string; iyi: string; kolay: string };
}

export async function getReviewSession(): Promise<ReviewCard[]> {
  if (cfg.mode === 'mock') {
    const cards = (await mock()).flashcards;
    // id per-kart (aynı konudan çok kart olabilir); previews sunucu FSRS projeksiyonu (mock: tipik)
    return cards.map((c, i) => ({ id: 'fsrs-' + i, ...c, previews: { tekrar: '<1 dk', zor: '3 gün', iyi: '6 gün', kolay: '12 gün' } }));
  }
  return live<ReviewCard[]>('/review/session');
}

/** Konuya göre hafıza gücü (tüm kuyruk — due dahil) */
export async function getReviewTopics(): Promise<ReviewItem[]> {
  if (cfg.mode === 'mock') return (await mock()).reviewQueue;
  return live<ReviewItem[]>('/review/topics');
}

// ---------------------------------------------------------------------------
// Yardımcı — seviyeBilgi (kiro-data.js ile birebir; mock getLevel kullanır)
// ---------------------------------------------------------------------------

export function seviyeBilgiFrom(seviyeEsik: number[], xp: number): SeviyeBilgi {
  let sev = 1;
  for (let L = 1; L < seviyeEsik.length; L++) if (xp >= seviyeEsik[L]) sev = L;
  const mevcutEsik = seviyeEsik[sev] ?? 0;
  const sonrakiEsik = seviyeEsik[sev + 1] ?? mevcutEsik + 900;
  const span = Math.max(1, sonrakiEsik - mevcutEsik);
  const ilerleme = Math.min(1, Math.max(0, (xp - mevcutEsik) / span));
  return { seviye: sev, mevcutEsik, sonrakiEsik, span, ilerleme, kalanXp: Math.max(0, sonrakiEsik - xp) };
}

// ---------------------------------------------------------------------------
// Boss Savaşı — POST /boss/session + /boss/answer (openapi'de YOK; Faz 4 sözleşmesi)
// Sunucu-otorite: dogru + hasar/HP/kombo/can SUNUCUDA (mock server-sim; istemci HESAPLAMAZ).
// Boss teması = en zayıf mat konu + o konunun en zayıf atomu. Sorular getQuestionSet STRIP'li.
// ---------------------------------------------------------------------------

export interface BossSession {
  oturumId: string;
  bossAd: string;         // "{konu} Ejderhası"
  konu: string;
  zayifAtom: string;
  bossSeviye: number;     // mock sabit 9; üretimde sunucu (açık-nokta 5)
  maxHP: number;          // 2000
  maxCan: number;         // 5
  sorular: SoruSetItem[]; // dogru/cozum/neden STRIP'li (istemciye sızmaz)
  odulXp: number;         // 800 (mock sabit; üretimde sunucu — Kutlama'daki +120 ile çakışır, açık-nokta 5)
  odulRozet: string;      // "Efsanevi rozet"
}

export async function postBossSession(): Promise<BossSession> {
  if (cfg.mode === 'mock') {
    const d = await mock();
    const matTopics = d.topics.filter((t) => t.ders === 'mat');
    const zayif = matTopics.reduce<{ ad: string; hakimiyet: number }>(
      (a, b) => (b.hakimiyet < a.hakimiyet ? b : a),
      matTopics[0] ?? { ad: 'Türev', hakimiyet: 48 },
    );
    const kir = d.atomKirilim.find((x) => x.konu === zayif.ad);
    const atom = kir ? (markEnZayif(kir).atomlar.find((a) => a.enZayif)?.ad ?? kir.atomlar[0]?.ad ?? '—') : 'İç-fonksiyon türevi';
    const sorular = await getQuestionSet('mat', zayif.ad);
    return {
      oturumId: 'boss-' + zayif.ad, bossAd: zayif.ad + ' Ejderhası', konu: zayif.ad, zayifAtom: atom,
      bossSeviye: 9, maxHP: 2000, maxCan: 5, sorular, odulXp: 800, odulRozet: 'Efsanevi rozet',
    };
  }
  return live<BossSession>('/boss/session', { method: 'POST', body: JSON.stringify({}) });
}

export interface BossDurum { hp: number; kombo: number; can: number }
export interface BossAnswerResult extends BossDurum {
  correct: boolean;
  dogru: number;          // doğru şık — YANITTAN SONRA (sunucu)
  hasar: number;          // 280 + (kombo-1)*70 — mock server-sim (istemci hesaplamaz)
  sonuc?: 'won' | 'lost';
}

/** Boss saldırı: correct + hasar/HP/kombo/can SUNUCUDA (mock: dogru bank'tan, hasar formülü mock-izole).
 *  durum = istemcinin son bilinen HP/kombo/can'ı; sunucu (mock) sonrakini döner (postCatNext deseni). */
export async function postBossAnswer(questionId: string, secim: number | null, durum: BossDurum): Promise<BossAnswerResult> {
  if (cfg.mode === 'mock') {
    const q = (await mock()).questionBank.find((x) => x.id === questionId);
    const correct = q != null && secim === q.dogru;
    let { hp, kombo, can } = durum;
    let hasar = 0;
    if (correct) { hasar = 280 + (kombo - 1) * 70; hp = Math.max(0, hp - hasar); kombo += 1; }
    else { can -= 1; kombo = 1; }
    const sonuc: 'won' | 'lost' | undefined = hp <= 0 ? 'won' : can <= 0 ? 'lost' : undefined;
    return { correct, dogru: q?.dogru ?? 0, hasar, hp, kombo, can, sonuc };
  }
  return live<BossAnswerResult>('/boss/answer', { method: 'POST', body: JSON.stringify({ questionId, secim, durum }) });
}

// ---------------------------------------------------------------------------
// Kimlik — POST /auth/* (mock: sahte token; gerçek doğrulama sunucuda)
// ---------------------------------------------------------------------------

export async function login(req: LoginRequest): Promise<AuthTokens> {
  if (cfg.mode === 'mock') return { token: 'mock-jwt', refresh: 'mock-refresh' };
  return live<AuthTokens>('/auth/login', { method: 'POST', body: JSON.stringify(req) });
}

export async function register(req: RegisterRequest): Promise<AuthTokens> {
  if (cfg.mode === 'mock') return { token: 'mock-jwt', refresh: 'mock-refresh' };
  return live<AuthTokens>('/auth/register', { method: 'POST', body: JSON.stringify(req) });
}

// 3 adımlı kurtarma: recover → verifyResetCode → resetPassword.
// F4: `/auth/recover` backend'de HİÇ YOKTU (0 eşleşme) — ekran mock modda
// sessizce ilerlediği için fark edilmemişti; live modda 404 alırdı. Gerçek
// uçlar `/auth/forgot-password`, `/auth/verify-reset-code`, `/auth/reset-password`.

/** 1/3 — kod iste. Sunucu adresin kayıtlı olup olmadığından BAĞIMSIZ olarak
 *  aynı yanıtı verir (numaralandırma önleme), bu yüzden dönüş hep `ok:true`. */
export async function recover(eposta: string): Promise<{ ok: boolean }> {
  if (cfg.mode === 'mock') { return { ok: true }; }
  await live<{ success: boolean; message: string }>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email: eposta }),
  });
  return { ok: true };
}

/** 2/3 — 6 haneli kodu doğrula; başarılıysa sıfırlama token'ı döner. */
export async function verifyResetCode(
  eposta: string,
  kod: string,
): Promise<{ ok: boolean; token: string | null }> {
  if (cfg.mode === 'mock') {
    const gecerli = /^\d{6}$/.test(kod);
    return { ok: gecerli, token: gecerli ? 'mock-reset-token' : null };
  }
  const r = await live<{ success: boolean; token: string | null }>('/auth/verify-reset-code', {
    method: 'POST',
    body: JSON.stringify({ email: eposta, code: kod }),
  });
  return { ok: r?.success === true, token: r?.token ?? null };
}

/** 3/3 — token ile yeni şifreyi yaz. Politika sunucuda; mesaj kullanıcıya gösterilir. */
export async function resetPassword(
  token: string,
  yeniSifre: string,
): Promise<{ ok: boolean; mesaj: string }> {
  if (cfg.mode === 'mock') { return { ok: true, mesaj: 'Şifre güncellendi' }; }
  const r = await live<{ success: boolean; message: string }>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, newPassword: yeniSifre }),
  });
  return { ok: r?.success === true, mesaj: r?.message ?? '' };
}

// ---------------------------------------------------------------------------
// Ödevler — GET /assignments (öğrenci) · POST /assignments (öğretmen)
// durum: 'bekliyor' geciken teslim demektir — kaygı-duyarlı sözleşme (alarm dili yok)
// ---------------------------------------------------------------------------

export async function getAssignments(): Promise<Odev[]> {
  if (cfg.mode === 'mock') return (await mock()).odevler ?? [];
  return live<Odev[]>('/assignments');
}

export interface AssignmentRequest {
  konu: string;
  adet: number;
  teslim: string;
  /** true → her öğrencinin seti sunucuda θ'ya göre seçilir */
  kisisel: boolean;
  ogrenciler: string[];
}

export async function postAssignment(req: AssignmentRequest): Promise<{ id: string }> {
  if (cfg.mode === 'mock') return { id: 'odv-mock' };
  return live<{ id: string }>('/assignments', { method: 'POST', body: JSON.stringify(req) });
}

export async function postAssignmentProgress(id: string, soruId: string, cevap: number): Promise<{ yapilan: number; durum: Odev['durum'] }> {
  if (cfg.mode === 'mock') return { yapilan: 1, durum: 'acik' };
  return live('/assignments/' + id + '/progress', { method: 'POST', body: JSON.stringify({ soruId, cevap }) });
}

// ---------------------------------------------------------------------------
// Öğretmen — GET /class/:id/roster
// ---------------------------------------------------------------------------

export async function getClassRoster(sinifId: string): Promise<SinifOgrenci[]> {
  if (cfg.mode === 'mock') return (await mock()).sinifRoster ?? [];
  return live<SinifOgrenci[]>('/class/' + sinifId + '/roster');
}

// ===========================================================================
// SPRINT8 · Grup 6 — Oyunlaştırma (Lig · Düello · Arkadaş Serisi · Seri Dondurma)
// İki kollu: mock (jsdom/Storybook/ekran portu) · live (gerçek REST/SSE).
// Sunucu-otorite: puan/tur-sonucu/skor/elo mock'ta bile İZOLE server-sim'de
// hesaplanır — ekran ASLA doğruluk/skor hesaplamaz. Sorular STRIP'li (doğru sızmaz).
// ===========================================================================

/** EventSource/live taban URL — live()/cfg ile aynı kaynak. */
function esBase(): string {
  return cfg.baseUrl ?? '';
}

// --- Lig — GET /api/v1/leagues/current (+ /me + /level) snake→camel map ------

interface StandingsEntryDTO {
  student_id: string;
  display_name: string;
  xp: number;
  rank: number;
  is_self: boolean;
}
interface LeagueCurrentDTO {
  tier: string;
  rank: number;
  weekly_xp: number;
  total_in_tier: number;
  week_start: string;
  standings: StandingsEntryDTO[];
}

/** Ad → baş harfler (avatar). Sunucu display_name'i genel olabilir; self için /me. */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toLocaleUpperCase('tr-TR');
  return (parts[0][0] + parts[parts.length - 1][0]).toLocaleUpperCase('tr-TR');
}

function mapLeague(cur: LeagueCurrentDTO, me: Persona, lvl: SeviyeBilgi): LeagueData {
  const end = new Date(cur.week_start);
  end.setDate(end.getDate() + 7);
  const ms = end.getTime() - Date.now();
  const gun = Math.max(0, Math.floor(ms / 86_400_000));
  const saat = Math.max(0, Math.floor((ms % 86_400_000) / 3_600_000));
  // Not: seviye/trend + zonEsik/oduller/senVsDun backend DTO'da YOK. Self için
  // /level; diğerleri için istekçi seviyesi placeholder (mock zengin; live best-effort).
  return {
    tier: cur.tier,
    rank: cur.rank,
    haftalikXp: cur.weekly_xp,
    tierToplam: cur.total_in_tier,
    haftaBitisText: ms > 0 ? `${gun} gün ${saat} saat` : 'Hafta bitti',
    zonEsik: { yukselme: 10, dusme: Math.max(1, cur.total_in_tier - 4) },
    senVsDun: { buHafta: cur.weekly_xp, gecenHafta: 0 },
    oduller: [],
    standings: cur.standings.map((e) => ({
      studentId: e.student_id,
      ad: e.is_self ? me.ad : e.display_name,
      ini: e.is_self ? me.bas : initials(e.display_name),
      xp: e.xp,
      rank: e.rank,
      seviye: lvl.seviye,
      trend: 'same' as const,
      benMi: e.is_self,
    })),
  };
}

/** Lig durumu. mock: kiro-data.league; live: /api/v1/leagues/current + /me + /level (map).
 *  Ekran gizli-modda standings'i ÇEKMEZ (gizlilik) — bu karar ekranda, client'ta değil. */
export async function getLeague(): Promise<LeagueData> {
  if (cfg.mode === 'mock') return (await mock()).league;
  const [cur, me, lvl] = await Promise.all([
    live<LeagueCurrentDTO>('/api/v1/leagues/current'),
    getMe(),
    getLevel(),
  ]);
  return mapLeague(cur, me, lvl);
}

// --- Düello — GERÇEK WIRING (/api/v1/duel/*) --------------------------------
// Mock kolu EventSource KULLANMAZ (jsdom'da yok): setTimeout ile SCRIPTED
// deterministik rakip cevapları (server-sim izole). Skor/tur-sonucu/elo burada
// hesaplanır — ekran değil. Doğru şık STRIP'li sorularda İSTEMCİYE SIZMAZ.

interface DuelSimRound { rakipDogru: boolean; rakipSure: number }
interface DuelUserRound { benDogru: boolean; benSure: number }
interface DuelSimState {
  toplamTur: number;
  script: DuelSimRound[];
  full: Question[];                       // doğru şık burada kalır (server-sim); sızmaz
  userRounds: (DuelUserRound | undefined)[];
  benCevaplanan: number;
}

/** Mock düello oturum durumu (sunucu-oturum eşdeğeri; sadece mock kolunda yaşar). */
const duelSim = new Map<string, DuelSimState>();

const HARF = ['A', 'B', 'C', 'D', 'E'];
const RAKIP_DOGRU_SCRIPT = [true, true, false, true, false];
const RAKIP_SURE_SCRIPT = [4200, 3100, 5800, 2600, 5000];

function rakipSkorKismi(st: DuelSimState, orderDahil: number): number {
  return st.script.slice(0, orderDahil + 1).filter((s) => s.rakipDogru).length;
}
function rakipSkorToplam(st: DuelSimState): number {
  return st.script.filter((s) => s.rakipDogru).length;
}
function benSkorHesap(st: DuelSimState): number {
  return st.userRounds.filter((u) => u?.benDogru).length;
}
/** Tur sonucu SUNUCU-OTORİTE: her iki oyuncunun sonucundan türer (ekran değil). */
function turSonucuHesap(u: DuelUserRound | undefined, r: DuelSimRound): 'me' | 'opp' | 'draw' {
  const bd = u?.benDogru ?? false;
  if (bd && r.rakipDogru) return (u?.benSure ?? Infinity) <= r.rakipSure ? 'me' : 'opp';
  if (bd) return 'me';
  if (r.rakipDogru) return 'opp';
  return 'draw';
}

/** Eşleşme kuyruğuna gir. live: POST /api/v1/duel/matchmake {subject}. */
export async function postDuelMatchmake(ders: string): Promise<DuelMatch> {
  if (cfg.mode === 'mock') {
    const d = await mock();
    const bank = d.questionBank.filter((q) => q.ders === ders);
    const pool = bank.length ? bank : d.questionBank;
    const full = pool.slice(0, 5);
    const toplamTur = full.length;
    const sessionId = 'duel-' + ders;
    duelSim.set(sessionId, {
      toplamTur,
      script: full.map((_, i) => ({
        rakipDogru: RAKIP_DOGRU_SCRIPT[i % RAKIP_DOGRU_SCRIPT.length],
        rakipSure: RAKIP_SURE_SCRIPT[i % RAKIP_SURE_SCRIPT.length],
      })),
      full,
      userRounds: [],
      benCevaplanan: 0,
    });
    return { sessionId, durum: 'matched', rakip: d.duelOpponent, mod: ders, toplamTur };
  }
  const r = await live<{ status: string; session_id: string | null; message: string }>(
    '/api/v1/duel/matchmake', { method: 'POST', body: JSON.stringify({ subject: ders }) },
  );
  return {
    sessionId: r.session_id ?? '',
    durum: r.status === 'matched' ? 'matched' : 'queued',
    // Not: matchmake yanıtı rakip kimliği/tur sayısı DÖNMEZ — best-effort placeholder.
    rakip: { ad: 'Rakip', ini: '?', seviye: 0 },
    mod: ders,
    toplamTur: 5,
  };
}

interface DuelCurrentQuestionDTO {
  session_id: string;
  status: string;
  question_order: number | null;
  question_id: string | null;
  question_text: string | null;
  options: Record<string, string> | null;
  time_per_question_sec: number;
  total_questions: number;
  answered: boolean;
}

/** Sıradaki cevaplanmamış soru (STRIP'li). live: GET /api/v1/duel/{id}/current-question. */
export async function getDuelCurrentQuestion(sessionId: string): Promise<DuelQuestion | null> {
  if (cfg.mode === 'mock') {
    const st = duelSim.get(sessionId);
    if (!st || st.benCevaplanan >= st.toplamTur) return null;
    const q = st.full[st.benCevaplanan];
    if (!q) return null;
    // Açık pick → dogru/cozum/neden asla kopyalanmaz.
    return { order: st.benCevaplanan, id: q.id, soru: q.soru, secenekler: q.secenekler, sure: q.sure };
  }
  const r = await live<DuelCurrentQuestionDTO>('/api/v1/duel/' + sessionId + '/current-question');
  if (r.question_order == null || !r.question_id || !r.question_text || !r.options) return null;
  const opts = r.options;
  const secenekler = HARF.filter((k) => opts[k] != null).map((k) => opts[k]);
  return {
    order: r.question_order, id: r.question_id, soru: r.question_text,
    secenekler, sure: r.time_per_question_sec,
  };
}

interface DuelAnswerDTO {
  round_complete: boolean;
  question_order: number;
  player1_score: number;
  player2_score: number;
  is_correct: boolean;
}

/** Cevap gönder — correct/puan SUNUCUDA. live: POST /api/v1/duel/{id}/answer.
 *  secimHarfi 'A'-'E'; mock'ta doğru şık indeksten türer, ekran doğruluğu HESAPLAMAZ. */
export async function postDuelAnswer(
  sessionId: string, order: number, secimHarfi: string, timeMs: number,
): Promise<DuelAnswerResult> {
  if (cfg.mode === 'mock') {
    const st = duelSim.get(sessionId);
    if (!st) throw new KiroApiError(404, '/api/v1/duel/' + sessionId + '/answer');
    const q = st.full[order];
    const secimIndex = HARF.indexOf(secimHarfi.toUpperCase());
    const benDogru = q != null && secimIndex === q.dogru;
    st.userRounds[order] = { benDogru, benSure: timeMs };
    st.benCevaplanan = Math.max(st.benCevaplanan, order + 1);
    // Tur kazananı SUNUCU-OTORİTE: bu turun userRound'u + RAKİP script'inden (izole);
    // ekran hesaplamaz, yanıttan okur. (Stream timer'ı DEĞİL — MAJOR-1 yeniden-tahsis.)
    const rr = st.script[order];
    const turSonucu: DuelTurSonucu = rr ? turSonucuHesap(st.userRounds[order], rr) : 'draw';
    return {
      turTamam: true, soruOrder: order,
      benPuan: benSkorHesap(st), rakipPuan: rakipSkorKismi(st, order), benDogru, turSonucu,
    };
  }
  const r = await live<DuelAnswerDTO>('/api/v1/duel/' + sessionId + '/answer', {
    method: 'POST',
    body: JSON.stringify({ question_order: order, answer: secimHarfi.toUpperCase(), time_ms: timeMs }),
  });
  // Not: answer yanıtı istekçinin rolünü döndürmez — p1=ben best-effort (kesin sonuç getDuelResult'ta).
  // turSonucu best-effort: backend tur-kazananını DÖNDÜRMEZ; round_complete + kümülatif skor
  // yönünden türetiyoruz. Rakip henüz cevaplamadıysa (round_complete=false) yön geçici —
  // kesin tur/maç sonucu getDuelResult'ta. (Mock kolu izole server-sim ile kesin hesaplar.)
  const turSonucu: DuelTurSonucu = !r.round_complete
    ? (r.is_correct ? 'me' : 'opp')
    : r.player1_score === r.player2_score ? 'draw'
    : r.player1_score > r.player2_score ? 'me' : 'opp';
  return {
    turTamam: r.round_complete, soruOrder: r.question_order,
    benPuan: r.player1_score, rakipPuan: r.player2_score, benDogru: r.is_correct, turSonucu,
  };
}

interface DuelResultDTO {
  session_id: string;
  finished: boolean;
  my_score: number;
  opponent_score: number;
  won: boolean;
  draw: boolean;
  elo_change: number;
}

/** Düello sonucu. live: GET /api/v1/duel/{id}/result. */
export async function getDuelResult(sessionId: string): Promise<DuelResult> {
  if (cfg.mode === 'mock') {
    const st = duelSim.get(sessionId);
    if (!st) {
      return { sessionId, bitti: false, benSkor: 0, rakipSkor: 0, kazandin: false, berabere: false, eloDelta: 0 };
    }
    const bitti = st.benCevaplanan >= st.toplamTur;
    const benSkor = benSkorHesap(st);
    const rakipSkor = rakipSkorToplam(st);
    const kazandin = bitti && benSkor > rakipSkor;
    const berabere = bitti && benSkor === rakipSkor;
    const eloDelta = bitti ? (kazandin ? 18 : berabere ? 0 : -12) : 0;
    return { sessionId, bitti, benSkor, rakipSkor, kazandin, berabere, eloDelta };
  }
  const r = await live<DuelResultDTO>('/api/v1/duel/' + sessionId + '/result');
  return {
    sessionId: r.session_id, bitti: r.finished, benSkor: r.my_score, rakipSkor: r.opponent_score,
    kazandin: r.won, berabere: r.draw, eloDelta: r.elo_change,
  };
}

interface DuelRatingDTO {
  elo_rating: number;
  wins: number;
  losses: number;
  draws: number;
}

/** Düello ELO. live: GET /api/v1/duel/rating. */
export async function getDuelRating(): Promise<DuelRating> {
  if (cfg.mode === 'mock') return { elo: 1240, galibiyet: 14, maglubiyet: 6, beraberlik: 2 };
  const r = await live<DuelRatingDTO>('/api/v1/duel/rating');
  return { elo: r.elo_rating, galibiyet: r.wins, maglubiyet: r.losses, beraberlik: r.draws };
}

export interface DuelStreamHandlers {
  onConnected?: () => void;
  /** YALNIZ rakip durum-pili (rakipDogru/rakipSure). Tur kazananı stream'den GELMEZ —
   *  turSonucu postDuelAnswer yanıtındadır (sunucu-otorite; MAJOR-1 yeniden-tahsis). */
  onAnswer?: (d: { rakipDogru: boolean; rakipSure: number }) => void;
  onFinished?: (r: DuelResult) => void;
  onError?: () => void;
}

/** Canlı düello akışı. live: EventSource(<base>/api/v1/duel/stream/<id>) — {type} parse eder,
 *  unsubscribe (es.close) DÖNER. mock: setTimeout SCRIPTED rakip cevapları + finished (server-sim
 *  izole); unsubscribe = clearTimeout temizleyici. jsdom'da EventSource yok → mock kolu KULLANMAZ. */
export function duelStream(sessionId: string, h: DuelStreamHandlers): () => void {
  if (cfg.mode === 'mock') {
    const st = duelSim.get(sessionId);
    const timers: ReturnType<typeof setTimeout>[] = [];
    timers.push(setTimeout(() => h.onConnected?.(), 0));
    if (st) {
      st.script.forEach((r, i) => {
        timers.push(setTimeout(() => {
          // Rakip bu turu cevapladı — YALNIZ durum-pili sinyali. Tur kazananı
          // postDuelAnswer(turSonucu) ile döner (userRound + script'ten; ekran değil).
          h.onAnswer?.({ rakipDogru: r.rakipDogru, rakipSure: r.rakipSure });
        }, (i + 1) * 900));
      });
      timers.push(setTimeout(() => {
        const benSkor = benSkorHesap(st);
        const rakipSkor = rakipSkorToplam(st);
        const kazandin = benSkor > rakipSkor;
        const berabere = benSkor === rakipSkor;
        h.onFinished?.({
          sessionId, bitti: true, benSkor, rakipSkor, kazandin, berabere,
          eloDelta: kazandin ? 18 : berabere ? 0 : -12,
        });
      }, (st.script.length + 1) * 900));
    }
    return () => timers.forEach((t) => clearTimeout(t));
  }

  // live — gerçek SSE. EventSource cookie-auth için withCredentials.
  const es = new EventSource(esBase() + '/api/v1/duel/stream/' + sessionId, { withCredentials: true });
  es.onmessage = (ev: MessageEvent) => {
    let d: Record<string, unknown>;
    try { d = JSON.parse(ev.data as string) as Record<string, unknown>; }
    catch { return; }
    const t = d.type;
    if (t === 'connected') h.onConnected?.();
    else if (t === 'answer') {
      // Stream YALNIZ rakip durum-pili besler; tur kazananı postDuelAnswer'da.
      h.onAnswer?.({
        rakipDogru: Boolean(d.is_correct),
        rakipSure: Number(d.time_ms ?? 0),
      });
    } else if (t === 'finished') {
      h.onFinished?.({
        sessionId,
        bitti: true,
        benSkor: Number(d.my_score ?? d.player1_score ?? 0),
        rakipSkor: Number(d.opponent_score ?? d.player2_score ?? 0),
        kazandin: Boolean(d.won),
        berabere: Boolean(d.draw),
        eloDelta: Number(d.elo_change ?? 0),
      });
    } else if (t === 'error') h.onError?.();
  };
  es.onerror = () => h.onError?.();
  return () => es.close();
}

// --- Arkadaş Serisi — mock-katmanı (backend YOK; live yolu ileri sözleşme) ---

/** Arkadaş serisi + ortak görev. mock: kiro-data.friends. */
export async function getFriends(): Promise<FriendsData> {
  if (cfg.mode === 'mock') return (await mock()).friends;
  return live<FriendsData>('/friends');
}

/** Dürtme gönder (server-sim; günde 1 sunucuda enforce, mock her zaman 'sent'). */
export async function postFriendNudge(id: string): Promise<{ durum: 'sent' }> {
  if (cfg.mode === 'mock') return { durum: 'sent' };
  return live<{ durum: 'sent' }>('/friends/' + id + '/nudge', { method: 'POST', body: JSON.stringify({}) });
}

/** Tebrik gönder (server-sim). */
export async function postFriendCongrats(id: string): Promise<{ gonderildi: boolean }> {
  if (cfg.mode === 'mock') return { gonderildi: true };
  return live<{ gonderildi: boolean }>('/friends/' + id + '/congrats', { method: 'POST', body: JSON.stringify({}) });
}

// --- Seri Dondurma — mock (backend YOK; freeze mekaniği mock) ----------------

/** Deterministik hafta: Pzt→Çar done · Per freeze · Cum-Cmt done · Bugün today; dondurmaHak=2.
 *  seri/rekor persona'dan (sunucu; mock persona ile birebir). */
export function buildMockStreak(p: Persona): StreakData {
  return {
    // Mock kurucu: persona bu iki alani DOLU tutar. `?? 0` yalniz Persona
    // tipi nullable oldugu icin var; uretimde bu yol kullanilmiyor.
    seri: p.seri ?? 0,
    rekor: p.seriRekor ?? 0,
    dondurmaHak: 2,
    hafta: [
      { label: 'Pzt', durum: 'done' },
      { label: 'Sal', durum: 'done' },
      { label: 'Çar', durum: 'done' },
      { label: 'Per', durum: 'freeze' },
      { label: 'Cum', durum: 'done' },
      { label: 'Cmt', durum: 'done' },
      { label: 'Bugün', durum: 'today' },
    ],
  };
}

/** Seri + dondurma hakkı. mock: buildMockStreak(persona) deterministik. */
export async function getStreak(): Promise<StreakData> {
  if (cfg.mode === 'mock') return buildMockStreak((await mock()).persona);
  return live<StreakData>('/streak');
}

// ---------------------------------------------------------------------------
// Diğer sözleşme uçları (şekil: KIRO2 API Sozlesmesi §bildirim/§senkron/§fatura)
// GET /notifications · POST /sync/events · POST /billing/trial — ekran portu
// sırasında bu kalıpla eklenir (mock kısa devre + live fetch).
// ---------------------------------------------------------------------------

// ===========================================================================
// SPRINT9 · Grup 7-A — Rol panelleri (Veli · Öğretmen · Öğrenci-Özeti · Sınıf)
// İki kollu: mock (kiro-data) · live (gerçek /parent + /teacher; snake→camel).
// Zarf karışık ({success,data} | {data} | ham Pydantic) → unwrapData ile normalize.
// SUNUCU-OTORİTE: öğrenci net/hâkimiyet/risk/theta SUNUCUDA hesaplanır; istemci
// bu türevleri ÜRETMEZ — mock'ta bile veri kiro-data'dan OKUNUR, ekranda değil.
// ===========================================================================

type Rec = Record<string, unknown>;
const asRec = (v: unknown): Rec => (v != null && typeof v === 'object' ? (v as Rec) : {});
/** Zarf çöz: {success,data} | {data} | ham gövde — hepsinden gövdeyi çıkar. */
const unwrapData = (raw: unknown): unknown => {
  const o = asRec(raw);
  return 'data' in o && o.data != null ? o.data : raw;
};
const asArr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const nnum = (v: unknown, def = 0): number => (typeof v === 'number' && Number.isFinite(v) ? v : def);
const nstr = (v: unknown, def = ''): string => (typeof v === 'string' ? v : def);
/** İlk dolu anahtar (snake VEYA camel) — best-effort normalize. */
const pick = (o: Rec, ...keys: string[]): unknown => {
  for (const k of keys) if (o[k] != null) return o[k];
  return undefined;
};

// --- snake→camel eşleyiciler (live; şekil belirsiz → esnek okuma + neutral fallback) ---

function mapHaftaGun(v: unknown): HaftaGun {
  const o = asRec(v);
  const dk = nnum(pick(o, 'dk', 'minutes', 'dakika'));
  const aktifRaw = pick(o, 'aktif', 'active');
  return { label: nstr(pick(o, 'label', 'gun', 'day')), dk, aktif: typeof aktifRaw === 'boolean' ? aktifRaw : dk > 0 };
}
function mapDersIlerleme(v: unknown): DersIlerleme {
  const o = asRec(v);
  return { ders: nstr(pick(o, 'ders', 'subject', 'ad', 'name')), hakimiyet: nnum(pick(o, 'hakimiyet', 'mastery', 'pct')) };
}
function mapVeliCocuk(v: unknown): VeliCocuk {
  const o = asRec(v);
  // Backend ParentChildRelationResponse 'child_name'/'child_id' döner (backend/models/parent.py) —
  // ÖNCELİKLİ dene: 'id' relation'ın kendi id'si (int), 'child_id' DEĞİL — pick() ilk-dolu
  // seçtiği için sıralama kritik (aksi halde relation-id, öğrenci id'si sanılıp sonraki
  // /parent/children/{id}/performance çağrısına yanlış id gider).
  const ad = nstr(pick(o, 'child_name', 'ad', 'name', 'display_name'));
  return {
    id: nstr(pick(o, 'child_id', 'id', 'student_id')),
    ad,
    sinif: nstr(pick(o, 'sinif', 'class_name', 'grade')),
    hedef: nstr(pick(o, 'hedef', 'target', 'goal')),
    ini: nstr(pick(o, 'ini', 'initials')) || initials(ad),
    avatarGradient: nstr(pick(o, 'avatarGradient', 'avatar_gradient'), 'linear-gradient(135deg,#2A2433,#4A4456)'),
  };
}
function mapSinavOzet(v: unknown): SinavOzet {
  const o = asRec(v);
  return {
    ders: nstr(pick(o, 'ders', 'subject', 'name', 'ad')),
    tarih: nstr(pick(o, 'tarih', 'date')),
    net: nnum(pick(o, 'net', 'score')),
    tur: nstr(pick(o, 'tur', 'type', 'tip')),
  };
}
function mapVeliUyari(v: unknown): VeliUyari {
  const o = asRec(v);
  const t = nstr(pick(o, 'tip', 'type'), 'success');
  const tip: VeliUyari['tip'] = t === 'risk' || t === 'sevinc' ? t : 'success';
  return { tip, metin: nstr(pick(o, 'metin', 'message', 'text')) };
}
function mapOgretmenSinif(v: unknown): OgretmenSinif {
  const o = asRec(v);
  return {
    id: nstr(pick(o, 'id', 'class_id')),
    ad: nstr(pick(o, 'ad', 'name')),
    seviye: nstr(pick(o, 'seviye', 'grade_level', 'level')),
    ders: nstr(pick(o, 'ders', 'subject_area', 'subject')),
    ogrenciSayisi: nnum(pick(o, 'ogrenciSayisi', 'ogrenci', 'student_count', 'students')),
  };
}
function toRisk(v: unknown): OgretmenOgrenci['risk'] {
  if (v === true) return 'dikkat';
  if (typeof v === 'string' && v !== '' && v !== 'yok' && v !== 'none') return 'dikkat';
  return 'yok';
}
function mapOgretmenOgrenci(v: unknown): OgretmenOgrenci {
  const o = asRec(v);
  const ad = nstr(pick(o, 'ad', 'name', 'display_name'));
  return {
    id: nstr(pick(o, 'id', 'student_id')),
    ad,
    ini: nstr(pick(o, 'ini', 'initials')) || initials(ad),
    ortNet: nnum(pick(o, 'ortNet', 'avg_net', 'net')),
    hakimiyet: nnum(pick(o, 'hakimiyet', 'mastery')),
    sonAktif: nstr(pick(o, 'sonAktif', 'last_active', 'last_seen')),
    risk: toRisk(pick(o, 'risk', 'risk_level', 'at_risk')),
    odevDurum: nstr(pick(o, 'odevDurum', 'assignment_status')),
  };
}
function mapDikkatKarti(v: unknown): DikkatKarti {
  const o = asRec(v);
  return {
    tip: nstr(pick(o, 'tip', 'type')),
    ad: nstr(pick(o, 'ad', 'name')),
    metin: nstr(pick(o, 'metin', 'message', 'reason')),
  };
}

/** Veli paneli. mock: kiro-data.veliDashboard (cocukId → aktif çocuk).
 *  live: GET /parent/dashboard + /parent/children + /parent/children/{id}/performance kompoze. */
export async function getVeliDashboard(cocukId?: string): Promise<VeliDashboard> {
  if (cfg.mode === 'mock') {
    const base = (await mock()).veliDashboard;
    // SALT-OKUR: aktif çocuk değişse de net/hâkimiyet sunucudan gelir (mock tek çocuk verisi).
    return cocukId && base.cocuklar.some((c) => c.id === cocukId) ? { ...base, aktifCocukId: cocukId } : base;
  }
  const [dashRaw, childrenRaw] = await Promise.all([
    live<unknown>('/parent/dashboard'),
    live<unknown>('/parent/children'),
  ]);
  const dash = asRec(unwrapData(dashRaw));
  const cocuklar = asArr(unwrapData(childrenRaw)).map(mapVeliCocuk);
  const aktifCocukId = cocukId || nstr(pick(dash, 'aktifCocukId', 'active_child_id')) || cocuklar[0]?.id || '';
  const perf = aktifCocukId
    ? asRec(unwrapData(await live<unknown>('/parent/children/' + encodeURIComponent(aktifCocukId) + '/performance')))
    : {};
  // Zarf içindeki `kpi` bloğunu da düz oku (Pydantic karışık şekil).
  const src: Rec = { ...dash, ...asRec(pick(dash, 'kpi')), ...perf, ...asRec(pick(perf, 'kpi')) };
  const kpi = {
    cozulenSoru: nnum(pick(src, 'cozulenSoru', 'solved_questions')),
    cozulenSoruDelta: nnum(pick(src, 'cozulenSoruDelta', 'solved_questions_delta')),
    cozulenDeneme: nnum(pick(src, 'cozulenDeneme', 'exams_taken', 'solved_exams')),
    cozulenDenemeDelta: nnum(pick(src, 'cozulenDenemeDelta', 'exams_taken_delta')),
    planUyumu: nnum(pick(src, 'planUyumu', 'plan_adherence')),
    netDegisimi: nnum(pick(src, 'netDegisimi', 'net_change')),
  };
  const roiSrc = asRec(pick(src, 'roi'));
  const premSrc = asRec(pick(src, 'premium'));
  return {
    cocuklar,
    aktifCocukId,
    kpi,
    haftalik: asArr(pick(src, 'haftalik', 'weekly', 'week', 'weekly_activity')).map(mapHaftaGun),
    haftaToplamSa: nnum(pick(src, 'haftaToplamSa', 'week_total_hours')),
    haftaTrend: nstr(pick(src, 'haftaTrend', 'week_trend')),
    dersIlerleme: asArr(pick(src, 'dersIlerleme', 'subject_progress')).map(mapDersIlerleme),
    sonSinavlar: asArr(pick(src, 'sonSinavlar', 'recent_exams')).map(mapSinavOzet),
    uyarilar: asArr(pick(src, 'uyarilar', 'alerts')).map(mapVeliUyari),
    roi: {
      netArtisi: nnum(pick(roiSrc, 'netArtisi', 'net_gain'), kpi.netDegisimi),
      planUyum: nnum(pick(roiSrc, 'planUyum', 'plan_adherence'), kpi.planUyumu),
      seri: nnum(pick(roiSrc, 'seri', 'streak'), nnum(pick(src, 'current_streak'))),
      haftaOrtDk: nnum(pick(roiSrc, 'haftaOrtDk', 'avg_daily_minutes')),
    },
    premium: {
      fiyatAy: nnum(pick(premSrc, 'fiyatAy', 'price_month'), 124),
      indirimYuzde: nnum(pick(premSrc, 'indirimYuzde', 'discount_pct'), 38),
      maddeler: asArr(pick(premSrc, 'maddeler', 'items')).map((x) => nstr(x)).filter(Boolean),
    },
  };
}

/** Öğretmen paneli. mock: kiro-data.ogretmenPanel (sinifId → aktif sınıf).
 *  live: GET /teacher/classes + /teacher/students + /teacher/reports kompoze. */
export async function getOgretmenPanel(sinifId?: string): Promise<OgretmenPanel> {
  if (cfg.mode === 'mock') {
    const base = (await mock()).ogretmenPanel;
    return sinifId && base.siniflar.some((s) => s.id === sinifId) ? { ...base, aktifSinifId: sinifId } : base;
  }
  const [classesRaw, studentsRaw, reportsRaw] = await Promise.all([
    live<unknown>('/teacher/classes'),
    live<unknown>('/teacher/students'),
    live<unknown>('/teacher/reports'),
  ]);
  const siniflar = asArr(unwrapData(classesRaw)).map(mapOgretmenSinif);
  const ogrenciler = asArr(unwrapData(studentsRaw)).map(mapOgretmenOgrenci);
  const rep = asRec(unwrapData(reportsRaw));
  const src: Rec = { ...rep, ...asRec(pick(rep, 'kpi')) };
  return {
    siniflar,
    aktifSinifId: sinifId || siniflar[0]?.id || '',
    kpi: {
      ogrenci: nnum(pick(src, 'ogrenci', 'student_count', 'students')),
      ogrenciDelta: nnum(pick(src, 'ogrenciDelta', 'active_students', 'student_delta')),
      gecikmisOdev: nnum(pick(src, 'gecikmisOdev', 'overdue_assignments', 'pending_assignments')),
      ortNet: nnum(pick(src, 'ortNet', 'avg_net')),
      ortNetDelta: nnum(pick(src, 'ortNetDelta', 'avg_net_delta')),
    },
    ogrenciler,
    dikkat: asArr(pick(src, 'dikkat', 'attention', 'at_risk')).map(mapDikkatKarti),
    sinifHakimiyet: asArr(pick(src, 'sinifHakimiyet', 'class_mastery', 'topic_mastery')).map(mapDersIlerleme),
  };
}

/** Tek öğrenci özeti (öğretmen salt-okur). mock: kiro-data.ogrenciOzetleri[id].
 *  live: GET /teacher/students/{id} (özet /teacher/reports'a düşebilir). */
export async function getOgrenciOzeti(ogrenciId: string): Promise<OgrenciOzeti> {
  if (cfg.mode === 'mock') {
    const map = (await mock()).ogrenciOzetleri;
    const found = map[ogrenciId] ?? Object.values(map)[0];
    if (!found) throw new KiroApiError(404, '/teacher/students/' + ogrenciId);
    return found;
  }
  const o = asRec(unwrapData(await live<unknown>('/teacher/students/' + encodeURIComponent(ogrenciId))));
  const src: Rec = { ...o, ...asRec(pick(o, 'kpi')) };
  const durumRaw = pick(o, 'durum', 'status');
  const durum: OgrenciOzeti['durum'] = durumRaw === 'dikkat' || durumRaw === 'risk' ? 'dikkat' : 'saglikli';
  const ad = nstr(pick(o, 'ad', 'name'));
  const riskMetni = nstr(pick(o, 'riskMetni', 'risk_message'));
  return {
    id: nstr(pick(o, 'id', 'student_id')) || ogrenciId,
    ad,
    ini: nstr(pick(o, 'ini', 'initials')) || initials(ad),
    sinif: nstr(pick(o, 'sinif', 'class_name')),
    ders: nstr(pick(o, 'ders', 'subject')),
    sonAktivite: nstr(pick(o, 'sonAktivite', 'last_active', 'sonAktif')),
    durum,
    kpi: {
      net: nnum(pick(src, 'net', 'avg_net', 'tytNet')),
      hakimiyet: nnum(pick(src, 'hakimiyet', 'mastery', 'genelHakimiyet')),
      seri: nnum(pick(src, 'seri', 'streak')),
      cozulen: nnum(pick(src, 'cozulen', 'solved', 'solved_questions')),
    },
    haftalik: asArr(pick(src, 'haftalik', 'weekly')).map(mapHaftaGun),
    dersHakimiyet: asArr(pick(src, 'dersHakimiyet', 'subject_mastery', 'dersler')).map(mapDersIlerleme),
    ...(riskMetni ? { riskMetni } : {}),
  };
}

// --- Sınıf kurulumu — katılım kodu SERVER-SIM (backend YOK; deterministik 6-hane) ---

/** Deterministik 6-haneli katılım kodu (server-sim; aynı seed → aynı kod). */
function katilimKodUret(seed: string): string {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return String(100000 + ((h >>> 0) % 900000)); // 6 hane, baştaki sıfır yok
}
const katilimLink = (kod: string): string => 'https://kiro2.app/katil/' + kod;

/** Sınıf oluştur. live: POST /api/v1/teacher/classes {name,grade_level,subject_area}.
 *  mock: server-sim — id + deterministik 6-hane kod + davet linki üret. */
export async function postSinif(s: YeniSinif): Promise<KurulanSinif> {
  if (cfg.mode === 'mock') {
    const kod = katilimKodUret(s.ad + '|' + s.seviye + '|' + s.ders);
    return { id: 'sinif-' + kod, ad: s.ad, seviye: s.seviye, ders: s.ders, katilimKodu: kod, katilimLink: katilimLink(kod) };
  }
  const o = asRec(unwrapData(await live<unknown>('/api/v1/teacher/classes', {
    method: 'POST',
    body: JSON.stringify({ name: s.ad, grade_level: s.seviye, subject_area: s.ders }),
  })));
  const kod = nstr(pick(o, 'katilimKodu', 'join_code', 'code')) || katilimKodUret(s.ad + '|' + s.seviye + '|' + s.ders);
  return {
    id: nstr(pick(o, 'id', 'class_id')),
    ad: nstr(pick(o, 'ad', 'name'), s.ad),
    seviye: nstr(pick(o, 'seviye', 'grade_level'), s.seviye),
    ders: nstr(pick(o, 'ders', 'subject_area'), s.ders),
    katilimKodu: kod,
    katilimLink: nstr(pick(o, 'katilimLink', 'join_link')) || katilimLink(kod),
  };
}

/** Katılım kodu yenile — BACKEND YOK → mock server-sim (her çağrıda yeni kod).
 *  live yolu ileri sözleşme (POST .../rotate-code); backend 501 dönerse mock-flag'e düşülür. */
let _kodNonce = 0;
export async function rotateKatilimKodu(sinifId: string): Promise<{ katilimKodu: string; katilimLink: string }> {
  if (cfg.mode === 'mock') {
    _kodNonce += 1;
    const kod = katilimKodUret(sinifId + '#' + _kodNonce);
    return { katilimKodu: kod, katilimLink: katilimLink(kod) };
  }
  const o = asRec(unwrapData(await live<unknown>('/api/v1/teacher/classes/' + encodeURIComponent(sinifId) + '/rotate-code', {
    method: 'POST', body: JSON.stringify({}),
  })));
  const kod = nstr(pick(o, 'katilimKodu', 'join_code', 'code'));
  return { katilimKodu: kod, katilimLink: nstr(pick(o, 'katilimLink', 'join_link')) || katilimLink(kod) };
}

// ===========================================================================
// SPRINT9-B · Grup 7-B — Veli Bağlama (KVKK) + Ödev Atama
// İki kollu: mock (kiro-data/server-sim) · live (gerçek /kvkk + /parent + /teacher).
// SUNUCU-OTORİTE: bağlantı kodunun üretimi/doğrulaması, KVKK rıza kaydı ve θ-set
// kurulumu SUNUCUDA yapılır — istemci (mock'ta bile) kod üretmez, rızayı
// hesaplamaz, soru setini seçmez. Kod doğrulama + relationId üretimi server-sim
// İZOLE fonksiyonlarda yaşar; ekran bunları çağırmaz/hesaplamaz.
// ===========================================================================

// --- Veli Bağlama (KVKK) ---

/** Kod → relationId (server-sim; deterministik). İstemci bu id'yi ÜRETMEZ — sunucu döndürür. */
function relationIdUret(kod: string): string {
  return 'rel-' + kod;
}

/** 6-hane bağlantı kodu doğrulama — SUNUCU-OTORİTE. mock: kiro-data.veliBaglama.veliBaglamaKodu
 *  ile deterministik karşılaştırma (istemci kod üretmez/doğrulamaz; yalnız eşitlik sonucunu alır).
 *  live: backend e-posta tabanlı — kod ucu YOK → NEW forward sözleşme (POST verify-code). */
export async function verifyLinkCode(kod: string): Promise<LinkCodeSonuc> {
  const temiz = kod.replace(/\D/g, '').slice(0, 6);
  if (cfg.mode === 'mock') {
    const vb = (await mock()).veliBaglama;
    if (temiz.length === 6 && temiz === vb.veliBaglamaKodu) {
      return { gecerli: true, cocukAd: vb.cocukAd, cocukBas: vb.cocukBas, relationId: relationIdUret(temiz) };
    }
    return { gecerli: false };
  }
  const o = asRec(unwrapData(await live<unknown>('/api/v1/parent/verify-code', {
    method: 'POST', body: JSON.stringify({ code: temiz }),
  })));
  const gecerli = pick(o, 'gecerli', 'valid') === true;
  return gecerli
    ? {
        gecerli: true,
        cocukAd: nstr(pick(o, 'cocukAd', 'child_name')),
        cocukBas: nstr(pick(o, 'cocukBas', 'child_initials')),
        relationId: nstr(pick(o, 'relationId', 'relation_id', 'id')),
      }
    : { gecerli: false };
}

/** Öğrenci: veli bağlama için 6-hane kısa-ömürlü kod üret — SUNUCU-OTORİTE.
 *  mock: kiro-data.veliBaglama.veliBaglamaKodu (istemci kod üretmez).
 *  live: POST /api/v1/parent/link-code → {code, expires_at} (10 dk geçerli). */
export async function generateLinkCode(): Promise<{ kod: string; gecerlilikSonu: string }> {
  if (cfg.mode === 'mock') {
    const vb = (await mock()).veliBaglama;
    return { kod: vb.veliBaglamaKodu, gecerlilikSonu: '' };
  }
  const o = asRec(unwrapData(await live<unknown>('/api/v1/parent/link-code', { method: 'POST' })));
  return { kod: nstr(pick(o, 'kod', 'code')), gecerlilikSonu: nstr(pick(o, 'gecerlilikSonu', 'expires_at')) };
}

/** KVKK aydınlatma metni sürümü. live: GET /api/v1/kvkk/notice; mock: {version:'v3'}. */
export async function getKvkkNotice(): Promise<KvkkNotice> {
  if (cfg.mode === 'mock') return { version: 'v3', text: 'KVKK aydınlatma metni (mock).' };
  const o = asRec(unwrapData(await live<unknown>('/api/v1/kvkk/notice')));
  return {
    version: nstr(pick(o, 'version', 'notice_version'), 'v3'),
    text: nstr(pick(o, 'text', 'notice_text')) || undefined,
  };
}

/** KVKK açık rıza ver — rıza kaydı SUNUCUDA tutulur (consentId sunucudan).
 *  Backend ConsentGiveRequest 3 zorunlu alan ister (purpose enum, consent_text,
 *  privacy_policy_version) — purpose bu akış için sabit 'account_management'
 *  (veli-çocuk hesap bağlama; backend/models/kvkk_models.py DataProcessingPurpose).
 *  live: POST /api/v1/kvkk/consent/give; mock: server-sim (deterministik consentId). */
export async function giveConsent(
  args: { consentText: string; policyVersion: string },
): Promise<{ ok: boolean; consentId: string }> {
  if (cfg.mode === 'mock') return { ok: true, consentId: 'consent-' + args.policyVersion };
  const o = asRec(unwrapData(await live<unknown>('/api/v1/kvkk/consent/give', {
    method: 'POST',
    body: JSON.stringify({
      purpose: 'account_management',
      consent_text: args.consentText,
      privacy_policy_version: args.policyVersion,
    }),
  })));
  return {
    ok: pick(o, 'ok', 'success') !== false,
    consentId: nstr(pick(o, 'consentId', 'consent_id', 'id')),
  };
}

/** Bağlantı durumu yoklama (veli tarafı). mock: server-sim — ilk yoklama 'bekliyor',
 *  sonraki 'onaylandi' (çocuk onayı simülasyonu; istemci karar vermez).
 *  live: GET /parent/children polling — relation çocuk listesine düştüyse 'onaylandi'. */
const _pollSeen = new Set<string>();
export async function pollLinkStatus(relationId: string): Promise<{ durum: 'bekliyor' | 'onaylandi' }> {
  if (cfg.mode === 'mock') {
    if (_pollSeen.has(relationId)) return { durum: 'onaylandi' };
    _pollSeen.add(relationId);
    return { durum: 'bekliyor' };
  }
  const children = asArr(unwrapData(await live<unknown>('/parent/children')));
  const onayli = children.some((c) => {
    const o = asRec(c);
    return nstr(pick(o, 'relationId', 'relation_id', 'id', 'child_id')) === relationId;
  });
  return { durum: onayli ? 'onaylandi' : 'bekliyor' };
}

/** Öğrenci tarafı bekleyen veli isteği. mock: kiro-data.veliBaglama.pending.
 *  live: öğrenci-tarafı bekleyen-istek GET ucu backend'de YOK → istemci beslemez (null). */
export async function getPendingParentRequest(): Promise<PendingVeliIstek | null> {
  if (cfg.mode === 'mock') return (await mock()).veliBaglama.pending;
  return null;
}

/** İlişki onayı/reddi (öğrenci tarafı). live: PUT /api/v1/parent/approval/{id}?approved.
 *  mock: server-sim (onay/ret SUNUCUDA işlenir; mock her zaman ok). */
export async function approveRelation(relationId: string, approved: boolean): Promise<{ ok: boolean }> {
  if (cfg.mode === 'mock') return { ok: true };
  const o = asRec(unwrapData(await live<unknown>(
    '/api/v1/parent/approval/' + encodeURIComponent(relationId) + '?approved=' + (approved ? 'true' : 'false'),
    { method: 'PUT', body: JSON.stringify({ approved }) },
  )));
  return { ok: pick(o, 'ok', 'success') !== false };
}

// --- Ödev Atama (zengin-atama backend YOK → mock; live yolları forward sözleşme) ---

function mapKonuAtom(v: unknown): KonuAtom {
  const o = asRec(v);
  const durumRaw = nstr(pick(o, 'durum', 'status'), 'gelisiyor');
  const durum: KonuAtom['durum'] = durumRaw === 'zayif' || durumRaw === 'iyi' ? durumRaw : 'gelisiyor';
  const havuzRaw = pick(o, 'soruHavuzuHazir', 'pool_ready', 'has_pool');
  return {
    id: nstr(pick(o, 'id', 'topic_id', 'konuId')),
    ad: nstr(pick(o, 'ad', 'name', 'topic')),
    hakimiyet: nnum(pick(o, 'hakimiyet', 'mastery')),
    durum,
    // FAIL-CLOSED (27 Tem 2026). Eskiden default `true` idi ve backend bu alanı
    // HİÇBİR yerde üretmiyor (pool_ready/has_pool grep = 0) → alan hep undefined
    // → her konu "soru havuzunda hazır" görünüyordu. Kalite kapısı yayılınca 26
    // konu ile GENEL/FEN dersleri sıfır soruya düşüyor; bilinmeyeni "hazır"
    // saymak öğretmene olmayan havuz için ödev kurdurur. Bilinmiyorsa hazır değil.
    soruHavuzuHazir: typeof havuzRaw === 'boolean' ? havuzRaw : false,
  };
}

function mapAtamaOgrenci(v: unknown): AtamaOgrenci {
  const o = asRec(v);
  const ad = nstr(pick(o, 'ad', 'name', 'display_name'));
  const riskRaw = pick(o, 'risk', 'risk_note', 'at_risk');
  return {
    id: nstr(pick(o, 'id', 'student_id')),
    no: nnum(pick(o, 'no', 'number')),
    ad,
    ini: nstr(pick(o, 'ini', 'initials')) || initials(ad),
    theta: nnum(pick(o, 'theta', 'ability')),
    hakimiyet: nnum(pick(o, 'hakimiyet', 'mastery')),
    risk: typeof riskRaw === 'string' && riskRaw !== '' ? riskRaw : null,
    sonAktif: nstr(pick(o, 'sonAktif', 'last_active', 'last_seen')),
  };
}

/** Atama konu atomları — zayıflık sıralı (SUNUCU sıralar; istemci sıralama YAPMAZ).
 *  mock: kiro-data.odevAtama.konular; live: GET /teacher/class/{id}/topics (NEW). */
export async function getAtamaKonular(sinifId: string): Promise<KonuAtom[]> {
  if (cfg.mode === 'mock') return (await mock()).odevAtama.konular;
  return asArr(unwrapData(await live<unknown>('/teacher/class/' + encodeURIComponent(sinifId) + '/topics'))).map(mapKonuAtom);
}

/** Atama öğrenci listesi (θ/hâkimiyet/risk SUNUCUDAN). mock: kiro-data.odevAtama.roster;
 *  live: GET /teacher/students (class_id filtreli). */
export async function getAtamaRoster(sinifId: string): Promise<AtamaOgrenci[]> {
  if (cfg.mode === 'mock') return (await mock()).odevAtama.roster;
  return asArr(unwrapData(await live<unknown>('/teacher/students?class_id=' + encodeURIComponent(sinifId)))).map(mapAtamaOgrenci);
}

/** Ödev ata — istemci YALNIZ formu gönderir; θ-set kurulumu SUNUCUDA (kisisel=true ise
 *  her öğrencinin seti sunucuda θ'ya göre seçilir). mock: server-sim id + atananSayı.
 *  live: POST /teacher/assignments (genişletilmiş alanlar). */
export async function postAtama(form: AtamaForm): Promise<{ id: string; atananSayi: number }> {
  if (cfg.mode === 'mock') {
    const seed = form.konuId + '|' + form.teslimTarihi + '|' + form.ogrenciIds.join(',');
    const id = 'atama-' + katilimKodUret(seed);
    // Server-sim: atama, ortak mock-store'daki `odevler`'e yeni bir Odev olarak yazılır →
    // öğrencinin Ödevlerim (getAssignments) listesinde görünür (tam döngü). Gerçek backend
    // Faz 4'te bu Odev'i sunucu üretir; burada mock konuId→konu adı eşlemesiyle türetir.
    const c = await mock();
    const konu = (c.odevAtama?.konular ?? []).find((k) => k.id === form.konuId);
    const yeni: Odev = {
      id,
      baslik: (konu?.ad ?? 'Yeni ödev') + ' · ' + form.adet + ' soru',
      ders: 'mat',
      konu: konu?.ad ?? form.konuId,
      atayan: 'Öğretmenin',
      adet: form.adet,
      yapilan: 0,
      dakika: Math.max(10, form.adet * 2),
      teslim: form.teslimTarihi,
      kalan: null,
      durum: 'acik',
      kisisel: form.kisisel,
    };
    c.odevler = [yeni, ...(c.odevler ?? [])];
    return { id, atananSayi: form.ogrenciIds.length };
  }
  const o = asRec(unwrapData(await live<unknown>('/teacher/assignments', {
    method: 'POST',
    body: JSON.stringify({
      topic_id: form.konuId,
      count: form.adet,
      due_date: form.teslimTarihi,
      personalized: form.kisisel,
      student_ids: form.ogrenciIds,
    }),
  })));
  return {
    id: nstr(pick(o, 'id', 'assignment_id')),
    atananSayi: nnum(pick(o, 'atananSayi', 'assigned_count', 'count'), form.ogrenciIds.length),
  };
}

// ===========================================================================
// SPRINT10-A · Grup 8 (paylaşılan infra) — Bildirim Merkezi · Alan Kütüphanesi · Çevrimdışı
// İki kollu: mock (kiro-data) · live (gerçek REST). SUNUCU-OTORİTE: okunmamış
// sayacı, senkron kuyruğu ve önbellek paketleri SUNUCUDA belirlenir. Mutation
// metodları server-sim (ok döner) — ekran optimistik günceller; istemci sayaç
// veya kuyruk türetmez (bağlantı durumu ekran-yerel, veri değil).
// ===========================================================================

// --- Bildirim Merkezi — GET /notifications (+ read / read-all / clear) ---

/** Bildirim listesi (zaman-gruplu + okunmamış sayısı SUNUCUDAN). mock: kiro-data.bildirimler. */
export async function getBildirimler(): Promise<BildirimYanit> {
  if (cfg.mode === 'mock') return (await mock()).bildirimler;
  return live<BildirimYanit>('/notifications');
}

/** Tek bildirimi okundu işaretle — server-sim (mock her zaman ok; ekran optimistik günceller). */
export async function markBildirimOkundu(id: string): Promise<{ okundu: true }> {
  if (cfg.mode === 'mock') return { okundu: true };
  await live('/notifications/' + encodeURIComponent(id) + '/read', { method: 'POST', body: JSON.stringify({}) });
  return { okundu: true };
}

/** Tümünü okundu işaretle — okunmamış sayısı SUNUCUDAN (mock: 0). */
export async function markTumBildirimOkundu(): Promise<{ okunmamis: number }> {
  if (cfg.mode === 'mock') return { okunmamis: 0 };
  const o = asRec(unwrapData(await live<unknown>('/notifications/read-all', { method: 'POST', body: JSON.stringify({}) })));
  return { okunmamis: nnum(pick(o, 'okunmamis', 'unread', 'unread_count')) };
}

/** Bildirimleri temizle — server-sim (mock her zaman temizlendi). */
export async function clearBildirimler(): Promise<{ temizlendi: true }> {
  if (cfg.mode === 'mock') return { temizlendi: true };
  await live('/notifications/clear', { method: 'POST', body: JSON.stringify({}) });
  return { temizlendi: true };
}

// --- Alan Kütüphanesi — GET /alan-kutuphane ---

/** Alan kütüphanesi (senin alanın + 3 alan + dersler). mock: kiro-data.alanKutuphane. */
export async function getAlanKutuphane(): Promise<AlanKutuphaneData> {
  if (cfg.mode === 'mock') return (await mock()).alanKutuphane;
  return live<AlanKutuphaneData>('/alan-kutuphane');
}

// --- Çevrimdışı / Senkron — GET /offline/durum ---

/** Çevrimdışı senkron durumu (son eşitleme + kuyruk + paketler SUNUCUDAN). mock: kiro-data.cevrimdisi. */
export async function getCevrimdisiDurum(): Promise<SyncStatus> {
  if (cfg.mode === 'mock') return (await mock()).cevrimdisi;
  // Gerçek yol '/offline/sync-status' (backend SyncStatusResponse: last_sync_at,
  // pending_results_count, offline_package_version — F4-S2 keşif). 'kuyruk' (senkron-
  // olmamış öğeler tanım gereği CİHAZ-YEREL, sunucu bilemez) ve 'paketler' (adlandırılmış
  // plan/tekrar/soru/video paketleri) kavramları backend'de hiç yok — uydurma YAPILMAZ,
  // dürüst boş liste döner (ekranın kendi EmptyState'i zarif gösterir).
  const o = asRec(await live<unknown>('/offline/sync-status'));
  const lastSync = nstr(pick(o, 'last_sync_at'));
  const sonEsitleme = lastSync
    ? new Date(lastSync).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
    : 'Henüz eşitlenmedi';
  return { sonEsitleme, kuyruk: [], paketler: [] };
}

// ===========================================================================
// SPRINT10-B · Grup 8 (billing infra) — Abonelik · Ödeme (3DS sim) · Plan Yönetimi
// İki kollu: mock (kiro-data/server-sim) · live (forward REST sözleşmesi).
// SAF-MOCK: gerçek PSP (iyzico/PayTR/Stripe) YOK — 3DS timer-sim; kart verisi PCI
// UI-only, backend'e GİTMEZ. SUNUCU-OTORİTE: fiyat/tier/durum/3DS-sonucu/fatura
// SUNUCUDA belirlenir — istemci (mock'ta bile) fiyat hesaplamaz, 3DS sonucu ÜRETMEZ.
// Fiyat/ROI modeli veliDashboard.premium+roi ile HİZALIDIR (çelişen 2. model yok).
// ÖĞRENCİ FİYAT GİZLİ: getAbonelik('ogrenci') planları dönebilir ama ekran GÖSTERMEZ
// (childFirst=true → VeliYonlendirmeKarti). Satın-alma/kart/iptal yalnız veli.
// ===========================================================================

// --- Abonelik + Plan Yönetimi (rol'e göre) ---

/** Abonelik verisi (rol param). mock: kiro-data.abonelik; öğrenci bağlamında childFirst=true
 *  (ekran fiyat GÖSTERMEZ → VeliYonlendirmeKarti). live: GET /billing/abonelik?rol. */
export async function getAbonelik(rol: 'ogrenci' | 'veli'): Promise<AbonelikData> {
  if (cfg.mode === 'mock') {
    const base = (await mock()).abonelik;
    return { ...base, rol, childFirst: rol === 'ogrenci' };
  }
  return live<AbonelikData>('/billing/abonelik?rol=' + rol);
}

/** İlk ödeme tarihi (deneme bitişi) — sunucu-otorite; mock deterministik türetir (istemci fiyat değil). */
function ilkOdemeTarihHesap(gun: number): string {
  const d = new Date();
  d.setDate(d.getDate() + gun);
  return new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }).format(d);
}

/** Ödeme özeti (tutar/tarih SUNUCUDAN; istemci fiyat HESAPLAMAZ). mock: abonelik planından türer.
 *  live: GET /odeme/ozet?tier&fatura. */
export async function getOdemeOzeti(tier: PlanTier, fatura: FaturaDonem): Promise<OdemeOzeti> {
  if (cfg.mode === 'mock') {
    const ab = (await mock()).abonelik;
    const plan = ab.planlar.find((p) => p.tier === tier) ?? ab.planlar[ab.planlar.length - 1]!;
    const denemeGunu = ab.denemeGunu ?? 7;
    return {
      planAd: plan.ad,
      tier,
      fatura,
      tutar: fatura === 'yillik' ? plan.fiyatYil : plan.fiyatAy,
      ilkOdemeTarih: ilkOdemeTarihHesap(denemeGunu),
      denemeGunu,
    };
  }
  return live<OdemeOzeti>('/odeme/ozet?tier=' + tier + '&fatura=' + fatura);
}

/** Ödeme denemesi başlat — intentId SUNUCUDAN (mock: server-sim). live: POST /odeme/deneme-baslat. */
export async function postOdemeDeneme(): Promise<{ intentId: string }> {
  if (cfg.mode === 'mock') return { intentId: 'intent-mock' };
  const o = asRec(unwrapData(await live<unknown>('/odeme/deneme-baslat', { method: 'POST', body: JSON.stringify({}) })));
  return { intentId: nstr(pick(o, 'intentId', 'intent_id', 'id')) };
}

/** 3DS sonucu — MOCK TİMER-SİM: kısa gecikme sonra 'onaylandi' (SAF-MOCK; gerçek PSP YOK).
 *  SUNUCU-OTORİTE: istemci 3DS sonucunu ÜRETMEZ — çözülebilir Promise döner (test-deterministik).
 *  live: GET /odeme/3ds/{intentId} (backend 3DS callback durumu). */
export async function getOdeme3dsSonuc(intentId: string): Promise<ThreeDSDurum> {
  if (cfg.mode === 'mock') {
    return new Promise<ThreeDSDurum>((resolve) => setTimeout(() => resolve('onaylandi'), 400));
  }
  const o = asRec(unwrapData(await live<unknown>('/odeme/3ds/' + encodeURIComponent(intentId))));
  const d = nstr(pick(o, 'durum', 'status'), 'onaylandi');
  return d === 'reddedildi' || d === 'bekliyor' ? d : 'onaylandi';
}

/** Plan Yönetimi verisi (rol param). mock: kiro-data.abonelikYonetim. live: GET /abonelik/yonetim?rol. */
export async function getAbonelikYonetim(rol: 'ogrenci' | 'veli'): Promise<AbonelikYonetim> {
  if (cfg.mode === 'mock') {
    const base = (await mock()).abonelikYonetim;
    return { ...base, rol };
  }
  return live<AbonelikYonetim>('/abonelik/yonetim?rol=' + rol);
}

/** Aboneliği iptal et — iptalTarih SUNUCUDAN (yenileme tarihinde sona erer; iptal RED değil → coral).
 *  live: POST /abonelik/iptal. mock: server-sim (yenilemeTarih'i iptal-bitiş olarak döner). */
export async function postAbonelikIptal(): Promise<{ durum: 'iptal'; iptalTarih: string }> {
  if (cfg.mode === 'mock') {
    const y = (await mock()).abonelikYonetim;
    return { durum: 'iptal', iptalTarih: y.yenilemeTarih };
  }
  const o = asRec(unwrapData(await live<unknown>('/abonelik/iptal', { method: 'POST', body: JSON.stringify({}) })));
  return { durum: 'iptal', iptalTarih: nstr(pick(o, 'iptalTarih', 'cancel_date', 'ends_at')) };
}

/** İptali geri al — abonelik aktifleşir. live: POST /abonelik/geri-ac. mock: server-sim. */
export async function postAbonelikGeriAc(): Promise<{ durum: 'aktif' }> {
  if (cfg.mode === 'mock') return { durum: 'aktif' };
  await live('/abonelik/geri-ac', { method: 'POST', body: JSON.stringify({}) });
  return { durum: 'aktif' };
}

/** Fatura makbuzu bağlantısı — href SUNUCUDAN. mock: fatura kaydından. live: GET /abonelik/fatura/{id}/makbuz. */
export async function getFaturaMakbuz(id: string): Promise<{ href: string }> {
  if (cfg.mode === 'mock') {
    const y = (await mock()).abonelikYonetim;
    const f = y.faturalar.find((x) => x.id === id);
    return { href: f?.makbuzHref ?? '/makbuz/' + id };
  }
  const o = asRec(unwrapData(await live<unknown>('/abonelik/fatura/' + encodeURIComponent(id) + '/makbuz')));
  return { href: nstr(pick(o, 'href', 'url', 'makbuzHref')) || '/makbuz/' + id };
}

// ===========================================================================
// SPRINT11 · AI Sohbet + Sokratik AI — çift-kollu streaming (duelStream deseni)
// İki kollu: mock (jsdom/Storybook/ekran portu; EventSource/ReadableStream YOK →
// setTimeout scripted token akışı) · live (POST /enhanced-chat/stream; fetch +
// ReadableStream reader — EventSource GET-only olduğundan POST-SSE elle ayrıştırılır).
// SUNUCU-OTORİTE: AI yanıtı/çözümü SUNUCUDAN gelir — mock katmanı bunun deterministik
// server-sim eşdeğeridir; istemci CEVAP UYDURMAZ. Sokratik ton cevabı VERMEZ —
// yönlendirir (kiro-data.sokratik senaryolu sorular). İnteraktif Çözüm bunu KULLANMAZ.
// ===========================================================================

/** Token akış gecikmesi (ms) — kısa/deterministik (fake-timer testinde runAllTimers). */
const SOHBET_TOKEN_MS = 24;

/** Sohbet mesajı snake→camel eşleyici (live; şekil belirsiz → esnek okuma). */
function mapSohbetMesaj(v: unknown, i: number): SohbetMesaj {
  const o = asRec(v);
  const rolRaw = nstr(pick(o, 'rol', 'role', 'sender'));
  const rol: SohbetRol = rolRaw === 'ben' || rolRaw === 'user' || rolRaw === 'student' ? 'ben' : 'ai';
  const tag = pick(o, 'tag', 'label');
  return {
    id: nstr(pick(o, 'id', 'message_id')) || 'm-' + i,
    rol,
    metin: nstr(pick(o, 'metin', 'content', 'text', 'message')),
    ...(tag != null ? { tag: nstr(tag) } : {}),
  };
}

/** Sohbet server-sim yanıtı — mock LLM yerine senaryolu metin (istemci CEVAP UYDURMAZ;
 *  bu mock katmanı sunucu-otorite yanıtın deterministik eşdeğeridir).
 *  socratic: cevabı VERMEZ, yönlendirici sorular sorar (kiro-data.sokratik).
 *  direct: yöntemi sakin dille doğrudan anlatır (somut sayısal sonuç uydurmaz — yöntem verir). */
function sohbetScriptedYanit(d: MockData, teaching: SohbetTeachingMode): string {
  if (teaching === 'socratic') {
    const s = d.sokratik;
    return [s.acilis, ...s.adimlar].join(' ');
  }
  return 'Tabii, birlikte bakalım. Önce soruda verilenleri ve neyi bulman istendiğini ayrı ayrı yazalım; '
    + 'sonra uygun kuralı seçip adımları sırayla uygularız. Takıldığın adımı bana söyle, oradan devam edelim.';
}

/** Açılış oturumu. mock: kiro-data.sohbet (direct) / kiro-data.sokratik.acilis (socratic; SEN, kaygı-duyarlı).
 *  live: GET /enhanced-chat/sessions → son oturum + mesajları (snake→camel). */
export async function getSohbet(teaching: SohbetTeachingMode = 'direct'): Promise<SohbetOturum> {
  if (cfg.mode === 'mock') {
    const d = await mock();
    if (teaching === 'socratic') {
      return {
        id: d.sohbet.id,
        ...(d.sohbet.baslik != null ? { baslik: d.sohbet.baslik } : {}),
        mesajlar: [{ id: 'sok-acilis', rol: 'ai', metin: d.sokratik.acilis, tag: 'Sokratik' }],
      };
    }
    return d.sohbet;
  }
  // Zarf {success, sessions:[...]} — merkezi unwrapData 'data' anahtarını arar, burada
  // YOK; 'sessions' anahtarını AÇIKÇA çöz. En güncel oturum sessions[0] (backend
  // updated_at DESC sıralar) — mesajlar backend'de İNLİNE dönmez, AYRI uçtan çekilir.
  const sessionsEnvelope = asRec(await live<unknown>('/enhanced-chat/sessions'));
  const sessions = asArr(pick(sessionsEnvelope, 'sessions', 'data'));
  const last = asRec(sessions[0]);
  const sessionId = nstr(pick(last, 'id', 'session_id'));
  const baslik = nstr(pick(last, 'baslik', 'title', 'name'));
  let mesajlar: SohbetMesaj[] = [];
  if (sessionId) {
    const msgEnvelope = asRec(
      await live<unknown>('/enhanced-chat/sessions/' + encodeURIComponent(sessionId) + '/messages'),
    );
    mesajlar = asArr(pick(msgEnvelope, 'messages', 'data')).map(mapSohbetMesaj);
  }
  return {
    id: sessionId || 'oturum',
    ...(baslik ? { baslik } : {}),
    mesajlar,
  };
}

/** Stream'siz fallback — tek atımda AI yanıtı. mock: server-sim senaryolu metin;
 *  live: POST /enhanced-chat/message (teaching→teaching_mode gövde alanı). */
export async function postSohbetMesaj(args: SohbetStreamArgs): Promise<SohbetMesaj> {
  const teaching: SohbetTeachingMode = args.teaching ?? 'direct';
  if (cfg.mode === 'mock') {
    const d = await mock();
    return {
      id: 'msg-' + (args.oturumId ?? d.sohbet.id),
      rol: 'ai',
      metin: sohbetScriptedYanit(d, teaching),
      ...(teaching === 'socratic' ? { tag: 'Sokratik' } : {}),
    };
  }
  const o = asRec(await live<unknown>('/enhanced-chat/message', {
    method: 'POST',
    body: JSON.stringify({
      session_id: args.oturumId, message: args.metin, teaching_mode: teaching, student_id: args.studentId,
    }),
  }));
  return mapSohbetMesaj(o, 0);
}

/** Canlı sohbet akışı — ÇİFT-KOLLU (duelStream deseni). unsubscribe DÖNER.
 *  mock: setTimeout scripted token akışı (onConnected → onToken×N → onFinished); jsdom'da
 *   EventSource/ReadableStream YOK → mock kolu KULLANMAZ. Senkron seam: mockCache varsa
 *   timer'lar SENKRON kurulur (test-deterministik; fake-timer runAllTimers ile sürer).
 *  live: POST /enhanced-chat/stream — fetch + response.body ReadableStream reader; 'data: {content}'
 *   → onToken, 'data: [DONE]' → onFinished, ilk event session_id → onConnected. AbortController ile
 *   unsubscribe. teaching → teaching_mode gövde alanı. */
export function streamSohbet(args: SohbetStreamArgs, h: SohbetStreamHandlers): () => void {
  const teaching: SohbetTeachingMode = args.teaching ?? 'direct';

  if (cfg.mode === 'mock') {
    const timers: ReturnType<typeof setTimeout>[] = [];
    let cancelled = false;
    const basla = (d: MockData): void => {
      if (cancelled) return;
      const oturumId = args.oturumId ?? d.sohbet.id;
      const tam = sohbetScriptedYanit(d, teaching);
      // Kelime + boşluk token'ları — join('') tam metni birebir yeniden kurar (reconstruction).
      const tokenlar = tam.split(/(\s+)/).filter((t) => t.length > 0);
      timers.push(setTimeout(() => { if (!cancelled) h.onConnected?.(oturumId); }, 0));
      tokenlar.forEach((tok, i) => {
        timers.push(setTimeout(() => { if (!cancelled) h.onToken?.(tok); }, (i + 1) * SOHBET_TOKEN_MS));
      });
      timers.push(setTimeout(() => {
        if (cancelled) return;
        h.onFinished?.({
          id: 'msg-' + oturumId + '-' + tokenlar.length,
          rol: 'ai',
          metin: tam,
          ...(teaching === 'socratic' ? { tag: 'Sokratik' } : {}),
        });
      }, (tokenlar.length + 1) * SOHBET_TOKEN_MS));
    };
    // mockCache SENKRON hazırsa hemen kur (test-deterministik seam); yoksa async yükle.
    if (mockCache) basla(mockCache);
    else void mock().then(basla).catch((e) => { if (!cancelled) h.onError?.(e); });
    return () => { cancelled = true; timers.forEach((t) => clearTimeout(t)); };
  }

  // live — POST-SSE (EventSource GET-only): fetch + ReadableStream reader.
  const controller = new AbortController();
  let acc = '';
  let connectedSent = false;

  void (async () => {
    const f = cfg.fetchImpl ?? fetch;

    if (args.file) {
      // File upload uses message-with-attachment (non-streaming, simulated stream for UI)
      const formData = new FormData();
      formData.append('file', args.file);
      formData.append('message', args.metin);
      formData.append('teaching_mode', teaching);
      if (args.oturumId) formData.append('session_id', args.oturumId);
      if (args.studentId) formData.append('student_id', args.studentId);

      const res = await f(esBase() + apiPath('/enhanced-chat/message-with-attachment'), {
        method: 'POST',
        credentials: 'include',
        body: formData,
        signal: controller.signal,
      });

      if (!res.ok) { h.onError?.(new KiroApiError(res.status, '/enhanced-chat/message-with-attachment')); return; }
      const data = await res.json();
      if (!data.success) { h.onError?.(new Error(data.error || 'Upload failed')); return; }

      const session_id = data.data?.session_id;
      const message = data.data?.message || '';

      if (session_id) h.onConnected?.(session_id);

      // Simulate token streaming for the UI
      const tokens = message.split(/(\s+)/);
      for (const token of tokens) {
        if (controller.signal.aborted) break;
        h.onToken?.(token);
        await new Promise(r => setTimeout(r, 10)); // tiny delay for visual effect
      }

      if (!controller.signal.aborted) {
        h.onFinished?.({
          id: 'msg-live-' + Date.now(),
          rol: 'ai',
          metin: message,
          ...(teaching === 'socratic' ? { tag: 'Sokratik' } : {}),
        });
      }
      return;
    }

    // Normal text message (streaming)
    const headers: Record<string, string> = { 'Content-Type': 'application/json', Accept: 'text/event-stream' };
    const res = await f(esBase() + apiPath('/enhanced-chat/stream'), {
      method: 'POST',
      credentials: 'include',
      headers,
      body: JSON.stringify({
        session_id: args.oturumId, message: args.metin, teaching_mode: teaching, student_id: args.studentId,
      }),
      signal: controller.signal,
    });
    if (!res.ok || !res.body) { h.onError?.(new KiroApiError(res.status, '/enhanced-chat/stream')); return; }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n');
      buf = parts.pop() ?? '';
      for (const line of parts) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (payload === '[DONE]') {
          h.onFinished?.({
            id: 'msg-live-' + acc.length,
            rol: 'ai',
            metin: acc,
            ...(teaching === 'socratic' ? { tag: 'Sokratik' } : {}),
          });
          return;
        }
        let content = payload;
        try {
          const j = JSON.parse(payload) as Record<string, unknown>;
          if (!connectedSent && typeof j.session_id === 'string') { h.onConnected?.(j.session_id); connectedSent = true; }
          content = typeof j.content === 'string' ? j.content : '';
        } catch { /* düz metin token (JSON değil) */ }
        if (content) { acc += content; h.onToken?.(content); }
      }
    }
  })().catch((e) => { if (!controller.signal.aborted) h.onError?.(e); });
  return () => controller.abort();
}

// ===========================================================================
// FAZ 3 KAPANIŞ · İlk Hafta (onboarding momentum) + Rol (route guard kaynağı)
// İki kollu: mock (kiro-data) · live (gerçek REST). SUNUCU-OTORİTE: İlk Hafta'nın
// currentDay/yüzde/odakKonu (mastery-sıralı)/tier/zayifAtom + gün durumları
// SUNUCUDA belirlenir — istemci (mock'ta bile) bunları TÜRETMEZ, veri kiro-data'dan
// OKUNUR. Rol AYRI kaynak: Persona'ya rol EKLENMEZ (API sözleşmesi birebir korunur).
// ===========================================================================

/** İlk Hafta momentum yayı + kilometre-taşı kartları (öğrenci → SEN).
 *  mock: kiro-data.ilkHafta; live: GET /onboarding/ilk-hafta. */
export async function getIlkHafta(): Promise<IlkHaftaResponse> {
  if (cfg.mode === 'mock') return (await mock()).ilkHafta;
  return live<IlkHaftaResponse>('/onboarding/ilk-hafta');
}

/** Kullanıcı rolü — route guard landing kaynağı (Persona'dan AYRI; rol Persona'ya EKLENMEZ).
 *  mock: kiro-data.rol (yoksa 'ogrenci'). live: GET /me/rol — auth katmanı bağlanınca
 *  bu uç authStore.user.rol'a köprülenir (rol tek kanon; ekran authStore'dan da okuyabilir). */
export async function getRol(): Promise<KiroRol> {
  if (cfg.mode === 'mock') return (await mock()).rol ?? 'ogrenci';
  return live<KiroRol>('/me/rol');
}
