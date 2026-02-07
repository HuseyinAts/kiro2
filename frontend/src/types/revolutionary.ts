/**
 * Revolutionary Features Type Definitions
 * Devrimsel özellikler için tip tanımları
 */

// FSRS tipleri
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

export interface FSRSCulturalAdjustments {
  ramadan_factor: number
  exam_season_stress: number
  summer_break_decay: number
  group_study_bonus: number
  family_pressure: number
}

export type FSRSGrade = 1 | 2 | 3 | 4 // Again, Hard, Good, Easy

// Bionic Reading tipleri
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

export interface BionicReadingSettings {
  rootBoldRatio: number
  suffixBoldRatio: number
  minBoldChars: number
  maxBoldChars: number
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

export interface MetinBasitlestirmeResult {
  orijinal_metin: string
  seviye1_leksikal: string
  seviye2_sentaktik: string
  seviye3_semantik: string
  karmasiklik_azalma: number
  okunabilirlik_skoru: number
}

export type SimplificationLevel = 'lexical' | 'syntactic' | 'semantic'

// Multi-Agent tipleri
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

export type AgentStatus = 'active' | 'idle' | 'processing' | 'error'
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'failed'

export interface AgentPerformanceMetrics {
  tasks_completed: number
  success_rate: number
  average_response_time: number
}

export interface BlackboardEventData {
  [key: string]: any
}

export interface MultiAgentTask {
  task_id: string
  assigned_agent: string
  status: TaskStatus
  dependencies: string[]
}

export interface PerformanceSummary {
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  average_completion_time: number
}

// Revolutionary Feature Settings
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

// Learning Style tipleri
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

// ZPD Maarif tipleri
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
  data: T | null
  message?: string
  error?: string
}

// Request tipleri
export interface FSRSReviewRequest {
  student_id: string
  card_id: string
  grade: FSRSGrade
  review_time?: string
  cultural_context?: FSRSCulturalAdjustments
}

export interface TextSimplificationRequest {
  text: string
  level: SimplificationLevel
  preserve_meaning?: boolean
  target_audience?: 'elementary' | 'middle' | 'high' | 'university'
  student_id?: string
}

export interface BionicReadingRequest {
  text: string
  settings?: BionicReadingSettings
  student_id?: string
  language?: 'tr' | 'en'
}

export interface MultiAgentCoordinationRequest {
  student_id: string
  task_type?: string
  priority?: 'low' | 'medium' | 'high'
  context?: Record<string, any>
}

// Statistics tipleri
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