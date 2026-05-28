/**
 * API Error type for type-safe error handling
 * Replaces 'any' type in catch blocks
 */
export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: Record<string, unknown>
}

/**
 * Type guard for ApiError
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as ApiError).message === 'string'
  );
}

/**
 * Extract error message from unknown error
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return 'Bilinmeyen bir hata oluştu';
}

export interface Message {
  role: 'user' | 'agent'
  content: string
  timestamp: string
  agent?: string
}

export interface Agent {
  id: string
  name: string
  description: string
  icon: string
}

export interface ChatRequest {
  agent: string
  message: string
  session_id?: string
}

export interface ChatResponse {
  response: string
  agent: string
  timestamp: string
  session_id?: string
}

// Öğrenci Dashboard türleri
export interface DashboardStats {
  tamamlanan_dersler: number
  toplam_dersler: number
  tamamlanan_sinavlar: number
  ortalama_puan: number
  toplam_calisma_suresi: number
  haftalik_hedef: number
  haftalik_ilerleme: number
  gunluk_seri: number
  toplam_puan: number
  seviye: number
  deneyim: number
  sonraki_seviye_deneyim: number
}

export interface ExamResult {
  sinav_id: string
  sinav_adi: string
  sinav_tipi: string
  tarih: string
  puan: number
  dogru_sayisi: number
  yanlis_sayisi: number
  bos_sayisi: number
  sure: number
  konu_performanslari: Record<string, number>
}

export interface Goal {
  hedef_id: string
  baslik: string
  aciklama?: string
  hedef_tipi: string
  hedef_degeri: number
  mevcut_deger: number
  baslangic_tarihi: string
  bitis_tarihi: string
  durum: string
  olusturma_tarihi: string
}

export interface Notification {
  bildirim_id: string
  baslik: string
  mesaj: string
  tip: 'basari' | 'uyari' | 'bilgi' | 'hata'
  okundu: boolean
  tarih: string
  eylem_url?: string
}

export interface PerformanceData {
  tarih: string
  dersler: number
  sinavlar: number
  puan: number
  calisma_suresi: number
}

export interface StudentProfile {
  ogrenci_id: string
  kullanici_id: string
  sinif_seviyesi: number
  okul_adi?: string
  hedef_sinav: string
  hedef_universiteler: string[]
  ogrenme_stili?: string
  guclu_alanlar: string[]
  zayif_alanlar: string[]
  gunluk_calisma_hedefi?: number
  veli_onay: boolean
  olusturma_tarihi: string
  son_guncelleme: string
}

// RBAC (Role-Based Access Control) türleri
export type UserRole = 'ogrenci' | 'ogretmen' | 'veli' | 'admin'

export interface User {
  id: string
  email: string
  ad: string
  soyad: string
  rol: UserRole
  aktif: boolean
  olusturma_tarihi: string
  son_giris?: string
  profil_resmi?: string
  telefon?: string
  okul_id?: string
  sinif_id?: string
}

export interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  refreshToken: string | null
  loading: boolean
  error: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  success: boolean
  // S179 fix (B-P0-24): backend returns user only on full success.
  // When 2FA is required, response is {success: false, requires_2fa: true, email}
  // and the frontend must transition to the 2FA TOTP screen instead of
  // showing the generic "Giriş başarısız" toast.
  user?: User
  message?: string
  requires_2fa?: boolean
  email?: string
}

export interface RegisterRequest {
  email: string
  password: string
  ad: string
  soyad: string
  birth_date: string
  rol: UserRole
  telefon?: string
  okul_id?: string
  veli_email?: string
}

// Rol bazlı izinler
export interface Permission {
  resource: string
  action: 'create' | 'read' | 'update' | 'delete'
  condition?: string
}

export interface RolePermissions {
  [key: string]: Permission[]
}

// Dashboard türleri - rol bazlı
export interface StudentDashboardData {
  stats: DashboardStats
  recentExams: ExamResult[]
  goals: Goal[]
  notifications: Notification[]
  performanceData: PerformanceData[]
}

export interface TeacherDashboardData {
  siniflar: ClassInfo[]
  ogrenciler: StudentSummary[]
  son_sinavlar: ExamSummary[]
  performans_ozeti: PerformanceOverview
}

export interface ParentDashboardData {
  cocuklar: ChildInfo[]
  haftalik_rapor: WeeklyReport[]
  bildirimler: Notification[]
}

export interface AdminDashboardData {
  sistem_istatistikleri: SystemStats
  kullanici_istatistikleri: UserStats
  performans_metrikleri: PerformanceMetrics
  son_aktiviteler: RecentActivity[]
}

// Yardımcı türler
export interface ClassInfo {
  sinif_id: string
  sinif_adi: string
  ogrenci_sayisi: number
  ortalama_basari: number
  seviye?: number
  ders?: string
}

export interface StudentSummary {
  ogrenci_id: string
  ad_soyad: string
  sinif: string
  son_sinav_puani: number
  genel_ortalama: number
}

export interface ExamSummary {
  sinav_id: string
  sinav_adi: string
  tarih: string
  katilimci_sayisi: number
  ortalama_puan: number
}

export interface PerformanceOverview {
  toplam_ogrenci: number
  aktif_ogrenci: number
  ortalama_basari: number
  gelisme_trendi: number
}

export interface ChildInfo {
  ogrenci_id: string
  ad_soyad: string
  sinif: string
  okul: string
  son_aktivite: string
  haftalik_ilerleme: number
}

export interface WeeklyReport {
  hafta: string
  calisma_suresi: number
  tamamlanan_dersler: number
  sinav_puanlari: number[]
  ortalama_puan: number
}

export interface SystemStats {
  toplam_kullanici: number
  aktif_kullanici: number
  toplam_sinav: number
  sistem_yuklemesi: number
}

export interface UserStats {
  ogrenci_sayisi: number
  ogretmen_sayisi: number
  veli_sayisi: number
  yeni_kayitlar: number
}

export interface PerformanceMetrics {
  ortalama_yanit_suresi: number
  sistem_kullanilabilirlik: number
  hata_orani: number
  kullanici_memnuniyeti: number
}

export interface RecentActivity {
  aktivite_id: string
  kullanici: string
  eylem: string
  tarih: string
  detay?: string
}

// Sınav sistemi türleri
export enum SinavTipi {
  TYT = 'TYT',
  AYT = 'AYT',
  YDT = 'YDT',
  LGS = 'LGS'
}

export enum SinavDurumu {
  HAZIR = 'HAZIR',
  DEVAM_EDIYOR = 'DEVAM_EDIYOR',
  TAMAMLANDI = 'TAMAMLANDI',
  IPTAL_EDILDI = 'IPTAL_EDILDI'
}

export enum ZorlukSeviyesi {
  KOLAY = 'KOLAY',
  ORTA = 'ORTA',
  ZOR = 'ZOR'
}

export interface SinavSorusu {
  soru_id: string
  soru_metni: string
  secenekler: string[]
  dogru_cevap: string
  konu: string
  alt_konu?: string
  zorluk_seviyesi: ZorlukSeviyesi
  cozum_aciklamasi?: string
  sinav_tipi: SinavTipi
  mufredat_kodu?: string
  olusturma_tarihi: string
  guncelleme_tarihi: string
  aktif: boolean
}

export interface SinavOturumu {
  sinav_id: string
  ogrenci_id: string
  sinav_tipi: SinavTipi
  toplam_soru_sayisi: number
  sure_dakika: number
  soru_listesi: string[]
  durum: SinavDurumu
  baslangic_zamani?: string
  bitis_zamani?: string
  kalan_sure?: number
  mevcut_soru_index: number
  cevaplanan_sorular: Record<string, string>
  isaretlenen_sorular: string[]
  olusturma_tarihi: string
  son_guncelleme: string
}

export interface KonuPerformansi {
  konu: string
  toplam_soru: number
  dogru_sayisi: number
  yanlis_sayisi: number
  bos_sayisi: number
  basari_yuzdesi: number
  ortalama_sure?: number
}

export interface SinavSonucu {
  sonuc_id: string
  sinav_id: string
  ogrenci_id: string
  sinav_tipi: SinavTipi
  toplam_soru: number
  dogru_sayisi: number
  yanlis_sayisi: number
  bos_sayisi: number
  net_sayisi: number
  ham_puan: number
  konu_performanslari: KonuPerformansi[]
  zorluk_dagilimi: Record<string, number>
  zaman_analizi: Record<string, number>
  sinif_ortalamasi?: number
  okul_ortalamasi?: number
  ulusal_ortalama?: number
  basari_sirasi?: number
  zayif_konular: string[]
  guclu_konular: string[]
  calisma_onerileri: string[]
  analiz_tarihi: string
  gecerli: boolean
}

/**
 * PerformanceResponse -> SinavSonucu adapter
 * Converts examService.PerformanceResponse to SinavSonucu type
 */
export function performanceToSinavSonucu(
  perf: {
    total_questions: number
    answered_questions: number
    correct_answers: number
    wrong_answers: number
    empty_answers: number
    net_score: number
    net_sayisi?: number
    raw_score: number
    percentile?: number
    estimated_ability?: number
    confidence_level?: number
    konu_performanslari?: Array<{
      konu: string
      dogru_sayisi: number
      toplam_soru: number
      basari_yuzdesi: number
    }>
    calisma_onerileri?: string[]
  },
  sessionId: string,
  studentId: string = 'unknown',
  examType: SinavTipi = SinavTipi.TYT,
): SinavSonucu {
  // Extract strong/weak subjects from konu_performanslari
  const konuPerformans = perf.konu_performanslari || [];
  const sortedKonular = [...konuPerformans].sort((a, b) => b.basari_yuzdesi - a.basari_yuzdesi);
  const gucluKonular = sortedKonular.filter(k => k.basari_yuzdesi >= 60).map(k => k.konu).slice(0, 3);
  const zayifKonular = sortedKonular.filter(k => k.basari_yuzdesi < 60).map(k => k.konu).slice(0, 3);

  return {
    sonuc_id: `result_${sessionId}`,
    sinav_id: sessionId,
    ogrenci_id: studentId,
    sinav_tipi: examType,
    toplam_soru: perf.total_questions,
    dogru_sayisi: perf.correct_answers,
    yanlis_sayisi: perf.wrong_answers,
    bos_sayisi: perf.empty_answers,
    net_sayisi: perf.net_sayisi ?? perf.net_score,
    ham_puan: perf.raw_score,
    konu_performanslari: konuPerformans.map(kp => ({
      konu: kp.konu,
      toplam_soru: kp.toplam_soru,
      dogru_sayisi: kp.dogru_sayisi,
      yanlis_sayisi: kp.toplam_soru - kp.dogru_sayisi,
      bos_sayisi: 0,
      basari_yuzdesi: kp.basari_yuzdesi,
      ortalama_sure: undefined,
    })),
    zorluk_dagilimi: {},
    zaman_analizi: {},
    sinif_ortalamasi: undefined,
    okul_ortalamasi: undefined,
    ulusal_ortalama: perf.percentile ? perf.percentile : undefined,
    basari_sirasi: undefined,
    zayif_konular: zayifKonular,
    guclu_konular: gucluKonular,
    calisma_onerileri: perf.calisma_onerileri || [],
    analiz_tarihi: new Date().toISOString(),
    gecerli: true,
  };
}

// ============================================
// REVOLUTIONARY FEATURES TYPES
// Re-exported from types/revolutionary.ts for single source of truth
// ============================================

export type {
  RevolutionaryFeatureSettings,
  SimplificationResult,
  TurkishZPDRange,
  ZPDRecommendation,
  CulturalContext,
  FSRSCard,
  FSRSSchedule,
  FSRSCulturalAdjustments,
  FSRSGrade,
  BionicReadingResult,
  BionicReadingSettings,
  MultiAgentStatus,
  AgentCoordination,
  BlackboardEvent,
  BlackboardEventData,
  AgentStatus,
  TaskStatus,
  AgentPerformanceMetrics,
  MultiAgentTask,
  PerformanceSummary,
  HybridLearningProfile,
  ContentRecommendation,
  MetinBasitlestirmeResult,
  SimplificationLevel,
  ApiResponse,
  FSRSReviewRequest,
  TextSimplificationRequest,
  BionicReadingRequest,
  MultiAgentCoordinationRequest,
  RevolutionaryFeaturesStats,
} from './types/revolutionary';

// Additional Revolutionary Types - kept in types.ts for backward compatibility
export interface QuestionAnalysis {
  question_id: string
  difficulty_estimate: number
  discrimination_index: number
  topic_tags: string[]
  cognitive_level: 'remember' | 'understand' | 'apply' | 'analyze' | 'evaluate' | 'create'
  time_estimate: number
  common_mistakes: string[]
}

export interface StudentMorphologyProfile {
  student_id: string
  learning_speed: number
  retention_rate: number
  preferred_difficulty: number
  peak_performance_hours: number[]
  weak_topics: string[]
  strong_topics: string[]
  learning_style: string
}

// AgentInfo kept for backward compatibility (simplified version)
export interface AgentInfo {
  id: string
  name: string
  type: 'tutor' | 'evaluator' | 'recommender' | 'coordinator'
  status: 'idle' | 'working' | 'waiting' | 'error'
  current_task?: string
  last_action?: string
}