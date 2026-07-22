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
}

export async function postAnswer(questionId: string, secilen: number): Promise<AnswerResult> {
  if (cfg.mode === 'mock') {
    const q = (await mock()).questionBank.find((x) => x.id === questionId);
    if (!q) throw new KiroApiError(404, '/questions/' + questionId + '/answer');
    return { correct: secilen === q.dogru, dogru: q.dogru, cozum: q.cozum, neden: q.neden, xpKazanilan: secilen === q.dogru ? 10 : 2 };
  }
  return live<AnswerResult>('/questions/' + questionId + '/answer', { method: 'POST', body: JSON.stringify({ secilen }) });
}

export interface CatNextResult { item: Omit<CatItem, 'dogru'>; theta: number; se: number; done: boolean }

export async function postCatNext(prev?: { konu: string; correct: boolean }): Promise<CatNextResult> {
  if (cfg.mode === 'mock') {
    // Basit simülasyon: sıradaki maddeyi güçlük sırasıyla ver (gerçek MLE/EAP sunucuda)
    const bank = (await mock()).catBankMat;
    const i = Math.min(bank.length - 1, Math.floor(Math.random() * bank.length));
    const { dogru: _gizli, ...item } = bank[i];
    return { item, theta: 0, se: 0.6, done: false };
  }
  return live<CatNextResult>('/cat/next', { method: 'POST', body: JSON.stringify(prev ?? {}) });
}

export type ReviewGrade = 'kolay' | 'iyi' | 'zor';

export async function postReviewGrade(konu: string, grade: ReviewGrade): Promise<{ nextDueIn: number }> {
  if (cfg.mode === 'mock') {
    // FSRS aralığı sunucuda hesaplanır; mock kaba bir genişleyen aralık döner
    const next = grade === 'kolay' ? 7 : grade === 'iyi' ? 3 : 1;
    return { nextDueIn: next };
  }
  return live<{ nextDueIn: number }>('/review/' + encodeURIComponent(konu) + '/grade', { method: 'POST', body: JSON.stringify({ grade }) });
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
