/**
 * Öneri Servisi - Kişiselleştirilmiş içerik önerileri
 *
 * Not: Bu servis şu an stub implementation olarak çalışmaktadır.
 * Backend API entegrasyonu ileride yapılacaktır.
 */

import { apiClient } from './apiClient';

export interface Recommendation {
  id: string
  tip: string
  title: string
  source: string
  duration?: number
  match_score: number
  url?: string
  difficulty?: string
  tags?: string[]
}

export interface RecommendationFilter {
  subject?: string
  difficulty?: string
  maxDuration?: number
  limit?: number
}

class RecommendationService {
  /**
   * Öğrenci için kişiselleştirilmiş önerileri getir
   */
  async getRecommendations(studentId: string, filter?: RecommendationFilter): Promise<Recommendation[]> {
    try {
      const response = await apiClient.get(`/api/v1/recommendations/${studentId}`, {
        params: filter,
      });
      return response.data;
    } catch (error) {
      console.warn('Öneri servisi API hatası, mock data kullanılıyor:', error);
      // Backend hazır değilse mock data döndür
      return this.getMockRecommendations(studentId, filter);
    }
  }

  /**
   * Konu bazlı önerileri getir
   */
  async getSubjectRecommendations(studentId: string, subject: string): Promise<Recommendation[]> {
    return this.getRecommendations(studentId, { subject });
  }

  /**
   * Günlük önerilen çalışma planını getir
   */
  async getDailyPlan(studentId: string): Promise<Recommendation[]> {
    try {
      const response = await apiClient.get(`/api/v1/recommendations/${studentId}/daily`);
      return response.data;
    } catch {
      console.warn('Günlük plan API hatası, mock data kullanılıyor');
      return this.getMockRecommendations(studentId, { limit: 3 });
    }
  }

  /**
   * Öneriyi tamamlandı olarak işaretle
   */
  async markCompleted(studentId: string, recommendationId: string): Promise<void> {
    try {
      await apiClient.post(`/api/v1/recommendations/${studentId}/complete`, {
        recommendation_id: recommendationId,
      });
    } catch (error) {
      console.error('Öneri tamamlama hatası:', error);
    }
  }

  /**
   * Mock data - Backend entegrasyonu öncesi test için
   */
  private getMockRecommendations(_studentId: string, filter?: RecommendationFilter): Recommendation[] {
    const mockData: Recommendation[] = [
      {
        id: 'rec_1',
        tip: 'video',
        title: 'Türev ve İntegral - Temel Kavramlar',
        source: 'EBA TV',
        duration: 25,
        match_score: 95,
        difficulty: 'orta',
        tags: ['matematik', 'türev', 'integral'],
      },
      {
        id: 'rec_2',
        tip: 'quiz',
        title: 'Geometri - Üçgenler Test',
        source: 'KIRO2',
        duration: 15,
        match_score: 88,
        difficulty: 'kolay',
        tags: ['matematik', 'geometri'],
      },
      {
        id: 'rec_3',
        tip: 'reading',
        title: 'Osmanlı Devleti - Kuruluş Dönemi',
        source: 'Khan Academy',
        duration: 20,
        match_score: 82,
        difficulty: 'orta',
        tags: ['tarih', 'osmanlı'],
      },
      {
        id: 'rec_4',
        tip: 'video',
        title: 'Fizik - Kuvvet ve Hareket',
        source: 'EBA TV',
        duration: 30,
        match_score: 79,
        difficulty: 'zor',
        tags: ['fizik', 'mekanik'],
      },
      {
        id: 'rec_5',
        tip: 'practice',
        title: 'Paragraf Yorumlama Teknikleri',
        source: 'KIRO2',
        duration: 25,
        match_score: 75,
        difficulty: 'orta',
        tags: ['türkçe', 'paragraf'],
      },
    ];

    let filtered = mockData;

    if (filter?.subject) {
      filtered = filtered.filter(rec =>
        rec.tags?.some(tag => tag.toLowerCase().includes(filter.subject!.toLowerCase())),
      );
    }

    if (filter?.difficulty) {
      filtered = filtered.filter(rec => rec.difficulty === filter.difficulty);
    }

    if (filter?.maxDuration) {
      filtered = filtered.filter(rec => (rec.duration || 0) <= filter.maxDuration!);
    }

    if (filter?.limit) {
      filtered = filtered.slice(0, filter.limit);
    }

    return filtered;
  }
}

// Singleton instance
export const recommendationService = new RecommendationService();
export default recommendationService;
