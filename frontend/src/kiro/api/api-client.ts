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
  ReviewItem, LastExam, CatItem, SeviyeBilgi, SubjectKey, KiroData,
  KatalogKey,
  Question,
  Odev,
  SinifOgrenci,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
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
  /** Auth token sağlayıcı (live) */
  getToken?: () => string | Promise<string>;
}

/** kiro-data.json'ın şekli (KiroData'nın salt-veri alt kümesi — fonksiyonlar hariç) */
export type MockData = Pick<KiroData,
  'engine' | 'persona' | 'subjects' | 'topics' | 'dersKatalog' | 'alanlar' | 'katalogKonular' |
  'katalogUniteler' | 'sinifRoster' | 'odevler' |
  'reviewQueue' | 'lastExam' | 'questionBank' | 'flashcards' | 'catBankMat' |
  'curriculum' | 'atomKirilim' | 'seviyeEsik'>;

let cfg: KiroApiConfig = { mode: 'mock' };
let mockCache: MockData | null = null;

export function configureKiroApi(next: KiroApiConfig): void {
  cfg = next;
  mockCache = typeof next.mockData === 'object' && next.mockData ? next.mockData : null;
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

async function live<T>(path: string, init?: RequestInit): Promise<T> {
  if (!cfg.baseUrl) throw new Error('KiroApi: live modda baseUrl zorunlu.');
  const f = cfg.fetchImpl ?? fetch;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (cfg.getToken) headers.Authorization = 'Bearer ' + (await cfg.getToken());
  const res = await f(cfg.baseUrl + path, { ...init, headers: { ...headers, ...(init?.headers as object) } });
  if (!res.ok) throw new KiroApiError(res.status, path);
  return (await res.json()) as T;
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
    return (await mock()).atomKirilim.find((x) => x.konu === konu) ?? null;
  }
  return live<AtomKirilim | null>('/topics/' + encodeURIComponent(konu) + '/atoms');
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
    return seviyeBilgiFrom(d.seviyeEsik, d.persona.xp);
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

/** 3 adımlı kurtarma: recover → verify (kod) → reset (Hesap Kurtarma ekranı birebir) */
export async function recover(eposta: string): Promise<{ ok: boolean }> {
  if (cfg.mode === 'mock') return { ok: true };
  return live<{ ok: boolean }>('/auth/recover', { method: 'POST', body: JSON.stringify({ eposta }) });
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

// ---------------------------------------------------------------------------
// Diğer sözleşme uçları (şekil: KIRO2 API Sozlesmesi §bildirim/§senkron/§fatura)
// GET /notifications · POST /sync/events · POST /billing/trial — ekran portu
// sırasında bu kalıpla eklenir (mock kısa devre + live fetch).
// ---------------------------------------------------------------------------
