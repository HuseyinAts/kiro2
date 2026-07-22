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
} from '../types';

// SPRINT8 · Grup 6 tiplerini ekranlara `../api` üzerinden de açık tut (re-export).
export type {
  LeagueStanding, LeagueData,
  DuelQuestion, DuelMatch, DuelAnswerResult, DuelTurSonucu, DuelResult, DuelRating, DuelOpponent,
  Friend, CoopQuest, FriendsData,
  StreakDay, StreakData,
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
  'curriculum' | 'atomKirilim' | 'seviyeEsik' |
  'league' | 'duelOpponent' | 'friends' | 'streak'>;

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
  return { gunler, aralik: '29 Haz – 5 Tem', gunlukHedefDk: d.persona.gunlukHedefDk };
}

export async function getPlanWeek(): Promise<PlanWeek> {
  if (cfg.mode === 'mock') return buildMockPlanWeek(await mock());
  return live<PlanWeek>('/plan/week');
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
    seri: p.seri,
    rekor: p.seriRekor,
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
