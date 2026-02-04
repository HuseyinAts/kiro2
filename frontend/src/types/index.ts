/**
 * TypeScript Type Definitions
 * Uygulama genelinde kullanılan tip tanımları
 */

// Enum'lar
export enum SinavTipi {
  TYT = 'TYT',
  AYT = 'AYT',
  YDT = 'YDT'
}

export enum SinavDurumu {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  ABANDONED = 'abandoned',
  EXPIRED = 'expired'
}

export enum ZorlukSeviyesi {
  KOLAY = 'KOLAY',
  ORTA = 'ORTA',
  ZOR = 'ZOR'
}

export enum KullaniciRolu {
  OGRENCI = 'OGRENCI',
  OGRETMEN = 'OGRETMEN',
  VELI = 'VELI',
  ADMIN = 'ADMIN'
}

// Kullanıcı tipleri
export interface Kullanici {
  kullanici_id: string
  email: string
  ad: string
  soyad: string
  rol: KullaniciRolu
  aktif: boolean
  kayit_tarihi: string
  son_giris: string | null
  profil_resmi?: string
  telefon?: string
  dogum_tarihi?: string
  cinsiyet?: 'ERKEK' | 'KADIN'
  okul?: string
  sinif?: string
}

// Sınav tipleri
export interface SinavOturumu {
  sinav_id: string
  ogrenci_id: string
  sinav_tipi: SinavTipi
  durum: SinavDurumu
  baslangic_zamani: string | null
  bitis_zamani: string | null
  toplam_sure_dakika: number
  kalan_sure_saniye: number
  toplam_soru_sayisi: number
  mevcut_soru_index: number
  soru_listesi: string[]
  cevaplanan_sorular: Record<string, string>
  isaretlenen_sorular: string[]
  ozel_konfigurasyonlar?: Record<string, any>
  olusturma_zamani: string
}

export interface SinavSorusu {
  soru_id: string
  sinav_tipi: SinavTipi
  konu: string
  alt_konu?: string
  zorluk_seviyesi: ZorlukSeviyesi
  soru_metni: string
  secenekler: string[]
  dogru_cevap: string
  aciklama?: string
  cozum_videosu?: string
  kaynak?: string
  irt_parametreleri?: {
    zorluk: number
    ayirt_edicilik: number
    tahmin: number
  }
  morfoloji_karmasikligi?: number
  olusturma_zamani: string
}

export interface SinavSonucu {
  sonuc_id: string
  sinav_id: string
  ogrenci_id: string
  sinav_tipi: SinavTipi
  ham_puan: number
  net_sayisi: number
  dogru_sayisi: number
  yanlis_sayisi: number
  bos_sayisi: number
  basari_yuzdesi: number
  sure_kullanimi_dakika: number
  konu_performanslari: KonuPerformansi[]
  calisma_onerileri: string[]
  zayif_konular: string[]
  guclu_konular: string[]
  ortalama_cevap_suresi: number
  hesaplama_zamani: string
}

export interface KonuPerformansi {
  konu: string
  toplam_soru: number
  dogru_sayisi: number
  yanlis_sayisi: number
  bos_sayisi: number
  basari_yuzdesi: number
  ortalama_zorluk: number
}

// Öğrenme stili tipleri
export interface OgrenmeStilineTespit {
  ogrenci_id: string
  vark_profili: VARKProfili
  felder_profili: FelderSilvermanProfili
  hibrit_kod: string
  guven_seviyesi: number
  tespit_zamani: string
}

export interface VARKProfili {
  gorsel: number
  isitsel: number
  okuma: number
  kinestetik: number
}

export interface FelderSilvermanProfili {
  aktif_yansitici: number
  algisal_sezgisel: number
  gorsel_sozel: number
  sirali_butunsel: number
}

// ZPD Maarif tipleri
export interface ZPDMaarifAnalizi {
  ogrenci_id: string
  mevcut_seviye: number
  zpd_alt_sinir: number
  zpd_ust_sinir: number
  optimal_zorluk: number
  kulturel_faktorler: Record<string, number>
  maarif_uyumu: number
  oneriler: string[]
  analiz_zamani: string
}

// IRT Morfoloji tipleri
export interface IRTMorfolojiAnalizi {
  soru_id: string
  morfolojik_karmasiklik: number
  zorluk_ayarlamasi: number
  ogrenci_morfoloji_farkindaliği: number
  tahmin_olasiligi: number
  analiz_detaylari: {
    ek_sayisi: number
    turetim_derinligi: number
    bilesik_karmasikligi: number
    ses_degisimleri: number
    anlam_belirsizligi: number
  }
}

// Devrimsel özellik tipleri
export interface FSRSParametreleri {
  ogrenci_id: string
  parametreler: number[]
  kulturel_ayarlamalar: Record<string, number>
  son_guncelleme: string
}

export interface FSRSCard {
  card_id: string
  content: string
  subject: string
  difficulty: number
  stability: number
  retrievability: number
  last_review: string
  next_review: string
  review_count: number
  lapses: number
  state: 'new' | 'learning' | 'review' | 'relearning'
  cultural_adjustments?: FSRSCulturalAdjustments
  turkish_parameters?: number[]
}

export interface FSRSSchedule {
  card_id: string
  next_reviews: {
    again: string
    hard: string
    good: string
    easy: string
  }
  intervals: {
    again: number
    hard: number
    good: number
    easy: number
  }
  cultural_adjustments: FSRSCulturalAdjustments
  confidence_score: number
  reasoning: string
}

export interface MetinBasitlestirmeResult {
  orijinal_metin: string
  seviye1_leksikal: string
  seviye2_sentaktik: string
  seviye3_semantik: string
  karmasiklik_azalma: number
  okunabilirlik_skoru: number
}

export interface BionicReadingResult {
  orijinal_metin: string
  bionic_metin: string
  kok_ek_analizi: Array<{
    kelime: string
    kok: string
    ekler: string[]
    bionic_format: string
  }>
  complexity_score: number
  readability_score: number
  processing_time: number
}

export interface MultiAgentStatus {
  agent_id: string
  name: string
  status: AgentStatus
  current_task?: string
  last_activity: string
  performance_metrics: AgentPerformanceMetrics
}

export interface BlackboardEvent {
  event_id: string
  type: string
  source_agent: string
  target_agents: string[]
  data: BlackboardEventData
  timestamp: string
  processed: boolean
}

export interface AgentCoordination {
  coordination_id: string
  participating_agents: string[]
  shared_context: Record<string, any>
  active_tasks: MultiAgentTask[]
  performance_summary: PerformanceSummary
}

export interface RevolutionaryFeatureSettings {
  fsrs_enabled: boolean
  bionic_reading_enabled: boolean
  text_simplification_level: SimplificationLevel
  multi_agent_coordination: boolean
  cultural_adaptations: {
    ramadan_mode: boolean
    exam_season_stress: boolean
    group_study_preference: boolean
  }
  accessibility_features: {
    high_contrast: boolean
    large_text: boolean
    screen_reader_optimized: boolean
  }
}

// FSRS Grade tipleri
export type FSRSGrade = 1 | 2 | 3 | 4 // Again, Hard, Good, Easy

// Agent Status tipleri
export type AgentStatus = 'active' | 'idle' | 'processing' | 'error'

// Task Status tipleri  
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

// Text Simplification Level tipleri
export type SimplificationLevel = 'lexical' | 'syntactic' | 'semantic'

// Bionic Reading Settings tipleri
export interface BionicReadingSettings {
  rootBoldRatio: number
  suffixBoldRatio: number
  minBoldChars: number
  maxBoldChars: number
}

// FSRS Cultural Adjustments tipleri
export interface FSRSCulturalAdjustments {
  ramadan_factor: number
  exam_season_stress: number
  summer_break_decay: number
  group_study_bonus: number
  family_pressure: number
}

// Agent Performance Metrics tipleri
export interface AgentPerformanceMetrics {
  tasks_completed: number
  success_rate: number
  average_response_time: number
}

// Blackboard Event Data tipleri
export interface BlackboardEventData {
  [key: string]: any
}

// Multi-Agent Task tipleri
export interface MultiAgentTask {
  task_id: string
  assigned_agent: string
  status: TaskStatus
  dependencies: string[]
}

// Performance Summary tipleri
export interface PerformanceSummary {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  average_completion_time: number
}

// Revolutionary Features API Response tipleri
export interface RevolutionaryFeaturesResponse<T = any> extends ApiResponse<T> {
  processing_time?: number
  feature_type?: 'fsrs' | 'bionic_reading' | 'text_simplification' | 'multi_agent'
}

// FSRS Review Request tipleri
export interface FSRSReviewRequest {
  student_id: string
  card_id: string
  grade: FSRSGrade
  review_time?: string
  cultural_context?: FSRSCulturalAdjustments
}

// Text Simplification Request tipleri
export interface TextSimplificationRequest {
  text: string
  level: SimplificationLevel
  preserve_meaning?: boolean
  target_audience?: 'elementary' | 'middle' | 'high' | 'university'
  student_id?: string
}

// Bionic Reading Request tipleri
export interface BionicReadingRequest {
  text: string
  settings?: BionicReadingSettings
  student_id?: string
  language?: 'tr' | 'en'
}

// Multi-Agent Coordination Request tipleri
export interface MultiAgentCoordinationRequest {
  student_id: string
  task_type?: string
  priority?: 'low' | 'medium' | 'high'
  context?: Record<string, any>
}

// Revolutionary Features Statistics tipleri
export interface RevolutionaryFeaturesStats {
  fsrs_stats: {
    total_cards: number
    cards_due_today: number
    average_retention: number
    total_reviews: number
  }
  bionic_reading_stats: {
    texts_processed: number
    average_complexity_reduction: number
    reading_speed_improvement: number
  }
  text_simplification_stats: {
    texts_simplified: number
    average_readability_improvement: number
    most_used_level: SimplificationLevel
  }
  multi_agent_stats: {
    active_agents: number
    total_coordinations: number
    average_task_completion_time: number
    success_rate: number
  }
}

// Error types for Revolutionary Features
export interface RevolutionaryFeatureError extends AppError {
  feature_type: 'fsrs' | 'bionic_reading' | 'text_simplification' | 'multi_agent'
  error_category: 'api_error' | 'processing_error' | 'validation_error' | 'timeout_error'
}

// Event types for Revolutionary Features
export interface RevolutionaryFeatureEvent extends WebSocketEvent {
  feature_type: 'fsrs' | 'bionic_reading' | 'text_simplification' | 'multi_agent'
  student_id: string
  event_data: {
    action: string
    result?: any
    error?: RevolutionaryFeatureError
  }
}

// Text Simplification tipleri
export interface SimplificationResult {
  original_text: string
  simplified_text: string
  level: string
  complexity_score: number
  readability_score: number
  changes_made: string[]
  stats: {
    original_length: number
    simplified_length: number
    length_reduction: number
    complexity_reduction: number
    readability_improvement: number
    changes_count: number
    processing_time: number
  }
}

// Hibrit Öğrenme Profili tipleri
export interface HybridLearningProfile {
  student_id: string
  vark_profile: {
    visual: number
    auditory: number
    reading: number
    kinesthetic: number
    dominant: string
  }
  felder_profile: {
    active_reflective: number
    sensing_intuitive: number
    visual_verbal: number
    sequential_global: number
    preferences: string[]
  }
  hybrid_code: string
  confidence: {
    score: number
    level: string
  }
  detection_date: string
  last_updated: string
  data_points_used: number
}

// İçerik Önerisi tipleri
export interface ContentRecommendation {
  recommended_content_types: string[]
  content_weights: Record<string, number>
  learning_strategies: string[]
  study_techniques: string[]
  adjustments: {
    difficulty: number
    pace: number
  }
}

// ZPD Maarif tipleri (güncellenmiş)
export interface TurkishZPDRange {
  student_id: string
  subject: string
  current_level: number
  lower_bound: number
  upper_bound: number
  optimal_challenge: number
  group_individual_balance: number
  cultural_context: {
    group_learning_preference: number
    teacher_respect_level: number
    family_involvement: number
    peer_competition: number
    authority_acceptance: number
    collective_success: number
    elder_wisdom_value: number
    social_harmony: number
  }
  maarif_alignment: {
    overall_alignment: number
    national_values_alignment: number
    universal_values_alignment: number
    root_values_alignment: number
    aligned_values: string[]
  }
  calculated_at: string
}

export interface ZPDRecommendation {
  student_id: string
  subject: string
  recommended_difficulty: number
  learning_mode: string
  content_type: string
  teacher_guidance_level: number
  peer_support_level: number
  maarif_integration: string[]
  reasoning: string
  confidence_score: number
}

export interface CulturalContext {
  student_id: string
  group_learning_preference: number
  teacher_respect_level: number
  family_involvement: number
  peer_competition: number
  authority_acceptance: number
  collective_success: number
  elder_wisdom_value: number
  social_harmony: number
  detected_at: string
}

// API Response tipleri
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Form tipleri
export interface LoginForm {
  email: string
  password: string
  remember_me?: boolean
}

export interface RegisterForm {
  email: string
  password: string
  password_confirm: string
  ad: string
  soyad: string
  rol: KullaniciRolu
  telefon?: string
  okul?: string
  sinif?: string
}

export interface ProfileUpdateForm {
  ad: string
  soyad: string
  telefon?: string
  dogum_tarihi?: string
  cinsiyet?: 'ERKEK' | 'KADIN'
  okul?: string
  sinif?: string
}

// Dashboard tipleri
export interface DashboardStats {
  toplam_sinav: number
  tamamlanan_sinav: number
  ortalama_basari: number
  calisma_suresi_dakika: number
  son_sinav_tarihi?: string
  hedef_net?: number
  mevcut_net?: number
  ilerleme_yuzdesi: number
}

export interface RecentActivity {
  id: string
  tip: 'SINAV' | 'CALISMA' | 'BASARI'
  baslik: string
  aciklama: string
  tarih: string
  icon?: string
  color?: string
}

// Bildirim tipleri
export interface Bildirim {
  id: string
  kullanici_id: string
  baslik: string
  mesaj: string
  tip: 'BILGI' | 'UYARI' | 'HATA' | 'BASARI'
  okundu: boolean
  olusturma_zamani: string
  son_okuma_zamani?: string
}

// İçerik tipleri
export interface EgitimIcerigi {
  id: string
  baslik: string
  aciklama: string
  tip: 'VIDEO' | 'MAKALE' | 'INTERAKTIF' | 'PDF'
  url: string
  thumbnail?: string
  sure_dakika?: number
  zorluk_seviyesi: ZorlukSeviyesi
  konular: string[]
  etiketler: string[]
  begeni_sayisi: number
  goruntulenme_sayisi: number
  olusturma_zamani: string
}

// Hata tipleri
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
}

// Revolutionary Features - re-export from dedicated file
export * from './revolutionary'

// Utility tipleri
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

// Event tipleri
export interface WebSocketEvent {
  type: string
  data: any
  timestamp: string
}

// Theme tipleri
export interface ThemeConfig {
  mode: 'light' | 'dark'
  primaryColor: string
  secondaryColor: string
  fontSize: 'small' | 'medium' | 'large'
  accessibility: {
    highContrast: boolean
    reducedMotion: boolean
    screenReader: boolean
  }
}