/**
 * Öneri Servisi - Kişiselleştirilmiş içerik önerileri
 *
 * Öncelik: `POST /api/v1/recommendations` (Chroma / içerik motoru).
 * Yedek: `GET .../learning-style/recommendations/{id}`, ardından mock.
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
  private _titleForContentType(tip: string): string {
    const map: Record<string, string> = {
      video_lecture: 'Video ders ve özet',
      infographic: 'Görsel infografik çalışması',
      visual_aid: 'Görsel destekli konu tekrarı',
      audio_content: 'Sesli içerik / dinleme',
      group_discussion: 'Grup tartışması / sesli tekrar',
      podcast: 'Podcast / sesli not',
      reading: 'Metin ve okuma odaklı çalışma',
      text_summary: 'Metin özeti ve notlar',
      flashcards: 'Kart tekrarları',
      interactive_simulation: 'Etkileşimli alıştırma',
      practice_test: 'Test ve deneme',
      hands_on_lab: 'Uygulamalı alıştırma',
    };
    if (map[tip]) {return map[tip];}
    return tip.replace(/_/g, ' ');
  }

  /**
   * Learning-style API yanıtını dashboard kartlarına dönüştürür
   */
  private mapFromContentRecommendationApi(
    raw: {
      recommendations?: Array<{
        content_id: string
        content_preview: string
        score: number
        metadata?: Record<string, unknown>
        recommendation_type?: string
      }>
    },
    filter?: RecommendationFilter,
  ): Recommendation[] {
    const list = raw.recommendations || [];
    let rows: Recommendation[] = list.map((r, i) => ({
      id: r.content_id || `rec-chroma-${i}`,
      tip: r.recommendation_type || 'content',
      title: r.content_preview?.slice(0, 200) || 'Önerilen içerik',
      source: 'İçerik önerisi (KIRO2)',
      match_score: Math.min(1, Math.max(0, r.score)),
      difficulty: filter?.difficulty || 'orta',
      tags: r.metadata?.subject ? [String(r.metadata.subject)] : ['genel'],
    }));
    if (filter?.limit) {
      rows = rows.slice(0, filter.limit);
    }
    return rows;
  }

  private mapFromLearningStylePayload(
    data: {
      recommended_content_types?: string[];
      hybrid_code?: string;
      confidence_score?: number;
      content_weights?: Record<string, number>;
      subject_area?: string;
      difficulty_level?: string;
    },
    filter?: RecommendationFilter,
  ): Recommendation[] {
    const types = data.recommended_content_types || [];
    const conf = Math.min(1, Math.max(0, data.confidence_score ?? 0.7));
    let rows: Recommendation[] = types.map((t, i) => {
      const w = data.content_weights?.[t];
      const match = w != null ? Math.min(1, 0.5 * conf + 0.5 * w) : conf;
      return {
        id: `rec-ls-${i}-${t}`,
        tip: t,
        title: this._titleForContentType(t),
        source: `Öğrenme stili${data.hybrid_code ? ` (${data.hybrid_code})` : ''}`,
        duration: 20,
        match_score: match,
        difficulty: (filter?.difficulty as string | undefined) || data.difficulty_level || 'orta',
        tags: [data.subject_area || 'genel'],
      };
    });
    if (filter?.maxDuration) {
      rows = rows.filter(rec => (rec.duration || 0) <= filter.maxDuration!);
    }
    if (filter?.limit) {
      rows = rows.slice(0, filter.limit);
    }
    return rows;
  }

  /**
   * Öğrenci için kişiselleştirilmiş önerileri getir
   */
  async getRecommendations(studentId: string, filter?: RecommendationFilter): Promise<Recommendation[]> {
    try {
      const chromaResp = await apiClient.post(
        '/api/v1/recommendations/',
        {
          user_id: studentId,
          limit: filter?.limit ?? 10,
          subject_filter: filter?.subject?.toUpperCase() || 'MATEMATIK',
          ensure_diversity: true,
        },
      );
      if (chromaResp.status === 200 && chromaResp.data && typeof chromaResp.data === 'object') {
        const mapped = this.mapFromContentRecommendationApi(
          chromaResp.data as {
            recommendations?: Array<{
              content_id: string
              content_preview: string
              score: number
              metadata?: Record<string, unknown>
              recommendation_type?: string
            }>
          },
          filter,
        );
        if (mapped.length > 0) {
          return mapped;
        }
      }
    } catch {
      /* 503 / ağ — learning-style veya mock’a düş */
    }

    try {
      const response = await apiClient.get(
        `/api/v1/learning-style/recommendations/${studentId}`,
        {
          params: {
            subject_area: filter?.subject || 'matematik',
            difficulty_level: filter?.difficulty || 'orta',
            force_refresh: false,
          },
        },
      );
      const root = response.data;
      const payload = root?.data != null ? root.data : root;
      if (payload && Array.isArray((payload as { recommended_content_types?: string[] }).recommended_content_types)) {
        return this.mapFromLearningStylePayload(
          payload as { recommended_content_types: string[]; hybrid_code?: string; confidence_score?: number; content_weights?: Record<string, number>; subject_area?: string; difficulty_level?: string },
          filter,
        );
      }
      if (Array.isArray(response.data)) {
        return response.data as Recommendation[];
      }
    } catch (error) {
      console.warn('Öneri servisi API hatası, mock data kullanılıyor:', error);
    }
    return this.getMockRecommendations(studentId, filter);
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
    return this.getRecommendations(studentId, { limit: 3 });
  }

  /**
   * Öneriyi tamamlandı olarak işaretle
   */
  async markCompleted(studentId: string, recommendationId: string): Promise<void> {
    try {
      await apiClient.post('/api/v1/recommendations/interaction', {
        user_id: studentId,
        content_id: recommendationId,
        interaction_type: 'complete',
        duration_seconds: 0,
        metadata: {},
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
        match_score: 0.95,
        difficulty: 'orta',
        tags: ['matematik', 'türev', 'integral'],
      },
      {
        id: 'rec_2',
        tip: 'quiz',
        title: 'Geometri - Üçgenler Test',
        source: 'KIRO2',
        duration: 15,
        match_score: 0.88,
        difficulty: 'kolay',
        tags: ['matematik', 'geometri'],
      },
      {
        id: 'rec_3',
        tip: 'reading',
        title: 'Osmanlı Devleti - Kuruluş Dönemi',
        source: 'Khan Academy',
        duration: 20,
        match_score: 0.82,
        difficulty: 'orta',
        tags: ['tarih', 'osmanlı'],
      },
      {
        id: 'rec_4',
        tip: 'video',
        title: 'Fizik - Kuvvet ve Hareket',
        source: 'EBA TV',
        duration: 30,
        match_score: 0.79,
        difficulty: 'zor',
        tags: ['fizik', 'mekanik'],
      },
      {
        id: 'rec_5',
        tip: 'practice',
        title: 'Paragraf Yorumlama Teknikleri',
        source: 'KIRO2',
        duration: 25,
        match_score: 0.75,
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
