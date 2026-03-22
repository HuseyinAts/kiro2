/**
 * Learning Style Service - Frontend API İstemcisi
 *
 * Backend'deki öğrenme stili API'lerine bağlanır
 * Endpoint: /api/v1/learning-style/*
 */

import axios, { AxiosInstance } from 'axios';

import config from '../config';

// Base URL
const BASE_URL = config.api.baseURL;

// Axios instance — httpOnly cookie auth (no localStorage token)
const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor - hata yönetimi
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // setTimeout(0) allows pending promise chains to complete before redirect
      setTimeout(() => { window.location.href = '/login'; }, 0);
    }
    return Promise.reject(error);
  },
);

// Types
export interface VarkProfile {
  visual: number;
  auditory: number;
  reading: number;
  kinesthetic: number;
}

export interface FelderSilvermanProfile {
  active_reflective: number;
  sensing_intuitive: number;
  visual_verbal: number;
  sequential_global: number;
}

export interface LearningStyleProfile {
  student_id: string;
  name?: string;
  grade?: number;
  hibrit_kod: string;
  vark_profili: VarkProfile;
  felder_silverman_profili: FelderSilvermanProfile;
  dominant_vark_stili: string;
  dominant_felder_boyutu: string;
  guven_seviyesi: number;
  tespit_tarihi: string;
  profil_aciklamasi: string;
}

export interface BehavioralData {
  video_watch_time?: number;
  quiz_completion_rate?: number;
  reading_time?: number;
  interaction_count?: number;
  study_session_duration?: number;
}

export interface Recommendation {
  id: string;
  tip: string;
  title: string;
  aciklama: string;
  source: string;
  url?: string;
  duration?: number;
  oncelik: 'yüksek' | 'orta' | 'düşük';
  match_score: number;
}

// Service class
class LearningStyleService {
  /**
   * Öğrencinin öğrenme stilini tespit et
   */
  async detectLearningStyle(
    studentId: string,
    behavioralData?: BehavioralData,
  ): Promise<LearningStyleProfile> {
    try {
      const response = await api.get(`/api/v1/learning-style/detect/${studentId}`, {
        params: behavioralData,
      });
      return response.data.data || response.data;
    } catch (error) {
      console.error('Öğrenme stili tespit hatası:', error);
      throw error;
    }
  }

  /**
   * Kişiselleştirilmiş içerik önerileri al
   */
  async getRecommendations(
    studentId: string,
    subject?: string,
  ): Promise<Recommendation[]> {
    try {
      const response = await api.get(
        `/api/v1/learning-style/recommendations/${studentId}`,
        {
          params: { subject },
        },
      );
      return response.data.data || response.data;
    } catch (error) {
      console.error('Öneri alma hatası:', error);
      return [];
    }
  }

  /**
   * Davranışsal veri güncelle
   */
  async updateBehavioralData(
    studentId: string,
    behavioralData: BehavioralData,
  ): Promise<void> {
    try {
      await api.post(
        `/api/v1/learning-style/behavioral-data/${studentId}`,
        behavioralData,
      );
    } catch (error) {
      console.error('Davranışsal veri güncelleme hatası:', error);
      throw error;
    }
  }

  /**
   * Anket cevaplarını gönder
   */
  async submitQuestionnaire(
    studentId: string,
    responses: string[],
  ): Promise<LearningStyleProfile> {
    try {
      const response = await api.post(
        `/api/v1/learning-style/questionnaire/${studentId}`,
        { responses },
      );
      return response.data.data || response.data;
    } catch (error) {
      console.error('Anket gönderme hatası:', error);
      throw error;
    }
  }

  /**
   * Tüm hibrit kodları listele
   */
  async getAllHybridCodes(): Promise<string[]> {
    try {
      const response = await api.get('/api/v1/learning-style/hybrid-codes');
      return response.data.data || response.data;
    } catch (error) {
      console.error('Hibrit kod listesi alma hatası:', error);
      return [];
    }
  }

  /**
   * Servis istatistikleri
   */
  async getStatistics(): Promise<any> {
    try {
      const response = await api.get('/api/v1/learning-style/statistics');
      return response.data.data || response.data;
    } catch (error) {
      console.error('İstatistik alma hatası:', error);
      return null;
    }
  }

  /**
   * Profili export et (PDF/JSON)
   */
  async exportProfile(
    studentId: string,
    format: 'pdf' | 'json' = 'json',
  ): Promise<Blob | any> {
    try {
      const response = await api.get(
        `/api/v1/learning-style/export/${studentId}`,
        {
          params: { format },
          responseType: format === 'pdf' ? 'blob' : 'json',
        },
      );
      return response.data;
    } catch (error) {
      console.error('Profil export hatası:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const learningStyleService = new LearningStyleService();
export default learningStyleService;
