/**
 * EBA TV Service
 * 
 * EBA TV API'si ile iletişim için servis katmanı.
 */

import { apiClient } from './apiClient';

export interface EBAVideo {
  id: number;
  title: string;
  description: string;
  duration_minutes: number;
  category: string;
  grade_level: string;
  difficulty_level: string;
  quality_score: number;
  video_url: string;
  thumbnail_url?: string;
  subject_topics: string[];
  accessibility_features: string[];
  curriculum_alignment: {
    alignment_score: number;
  };
  created_date: string;
  last_updated: string;
}

export interface EBAContentCollection {
  total_videos: number;
  videos: EBAVideo[];
  categories: Record<string, number>;
  grade_levels: Record<string, number>;
  quality_distribution: Record<string, number>;
  last_updated: string;
}

export interface EBASearchFilters {
  query: string;
  grade_level?: string;
  category?: string;
  min_quality?: number;
  max_duration?: number;
  accessibility_required?: boolean;
}

export interface EBASearchResponse {
  videos: EBAVideo[];
  total_results: number;
  search_query: string;
  filters_applied: Record<string, any>;
  search_time_ms: number;
}

export interface EBARecommendationRequest {
  student_id: string;
  grade_level: string;
  weak_subjects: string[];
  learning_style: string;
  max_recommendations?: number;
}

export interface EBARecommendationResponse {
  recommendations: EBAVideo[];
  student_id: string;
  recommendation_reasons: Record<string, string>;
  personalization_score: number;
  generated_at: string;
}

export interface EBAStatistics {
  total_videos: number;
  categories: Record<string, {
    video_count: number;
    avg_quality: number;
    avg_duration: number;
    grade_distribution: Record<string, number>;
  }>;
  quality_distribution: Record<string, number>;
  last_updated: string;
  cache_status: string;
}

export interface EBAHealthStatus {
  success: boolean;
  status: string;
  data: {
    service_name: string;
    version: string;
    response_time_ms: number;
    cache_status: string;
    total_videos: number;
    last_updated: string;
    timestamp: string;
  };
  message: string;
}

class EbaTVService {
  private baseUrl = '/api/v1/eba-tv';

  /**
   * EBA TV ana sayfa bilgilerini getir
   */
  async getHomeInfo(): Promise<any> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/`);
      return response.data;
    } catch (error) {
      console.error('EBA TV ana sayfa bilgileri alınamadı:', error);
      throw error;
    }
  }

  /**
   * Tüm EBA TV içeriklerini getir
   */
  async getAllContent(forceRefresh: boolean = false): Promise<EBAContentCollection> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/content`, {
        params: { force_refresh: forceRefresh }
      });
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'İçerikler alınamadı');
      }
    } catch (error) {
      console.error('EBA TV içerikleri alınamadı:', error);
      throw error;
    }
  }

  /**
   * EBA TV içeriklerinde arama yap
   */
  async searchContent(filters: EBASearchFilters): Promise<EBASearchResponse> {
    try {
      const params: Record<string, any> = {
        query: filters.query
      };

      if (filters.grade_level) params.grade_level = filters.grade_level;
      if (filters.category) params.category = filters.category;
      if (filters.min_quality !== undefined) params.min_quality = filters.min_quality;
      if (filters.max_duration) params.max_duration = filters.max_duration;
      if (filters.accessibility_required !== undefined) {
        params.accessibility_required = filters.accessibility_required;
      }

      const response = await apiClient.get(`${this.baseUrl}/search`, { params });
      return response.data;
    } catch (error) {
      console.error('EBA TV arama hatası:', error);
      throw error;
    }
  }

  /**
   * Kişiselleştirilmiş EBA TV önerileri al
   */
  async getRecommendations(request: EBARecommendationRequest): Promise<EBARecommendationResponse> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/recommendations`, request);
      return response.data;
    } catch (error) {
      console.error('EBA TV önerileri alınamadı:', error);
      throw error;
    }
  }

  /**
   * Müfredat konusuna göre içerik getir
   */
  async getContentByCurriculumTopic(
    gradeLevel: string,
    category: string,
    topic: string
  ): Promise<{
    grade_level: string;
    category: string;
    topic: string;
    total_results: number;
    videos: EBAVideo[];
  }> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/curriculum/${gradeLevel}/${category}/${encodeURIComponent(topic)}`
      );
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Müfredat içerikleri alınamadı');
      }
    } catch (error) {
      console.error('EBA TV müfredat içerikleri alınamadı:', error);
      throw error;
    }
  }

  /**
   * EBA TV istatistiklerini getir
   */
  async getStatistics(): Promise<EBAStatistics> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/statistics`);
      return response.data;
    } catch (error) {
      console.error('EBA TV istatistikleri alınamadı:', error);
      throw error;
    }
  }

  /**
   * Video kalite analizini getir
   */
  async analyzeVideoQuality(videoId: number): Promise<any> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/quality/analyze/${videoId}`);
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Kalite analizi alınamadı');
      }
    } catch (error) {
      console.error('EBA TV kalite analizi alınamadı:', error);
      throw error;
    }
  }

  /**
   * EBA TV servis sağlık durumunu kontrol et
   */
  async getHealthStatus(): Promise<EBAHealthStatus> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/health`);
      return response.data;
    } catch (error) {
      console.error('EBA TV sağlık durumu alınamadı:', error);
      throw error;
    }
  }

  /**
   * Video izleme geçmişini kaydet (mock)
   */
  async recordVideoView(videoId: number, watchDuration: number): Promise<void> {
    try {
      // Mock implementation - gerçek uygulamada API endpoint'i olacak
      console.log(`Video ${videoId} izlendi: ${watchDuration} saniye`);
      
      // Local storage'a kaydet
      const viewHistory = this.getViewHistory();
      const viewRecord = {
        videoId,
        watchDuration,
        timestamp: new Date().toISOString()
      };
      
      viewHistory.push(viewRecord);
      localStorage.setItem('eba_tv_view_history', JSON.stringify(viewHistory));
    } catch (error) {
      console.error('Video izleme kaydı yapılamadı:', error);
    }
  }

  /**
   * Video izleme geçmişini getir
   */
  getViewHistory(): Array<{
    videoId: number;
    watchDuration: number;
    timestamp: string;
  }> {
    try {
      const history = localStorage.getItem('eba_tv_view_history');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('İzleme geçmişi alınamadı:', error);
      return [];
    }
  }

  /**
   * Video favorilere ekle/çıkar
   */
  toggleFavorite(videoId: number): boolean {
    try {
      const favorites = this.getFavorites();
      const index = favorites.indexOf(videoId);
      
      if (index > -1) {
        favorites.splice(index, 1);
      } else {
        favorites.push(videoId);
      }
      
      localStorage.setItem('eba_tv_favorites', JSON.stringify(favorites));
      return index === -1; // true if added, false if removed
    } catch (error) {
      console.error('Favori işlemi yapılamadı:', error);
      return false;
    }
  }

  /**
   * Favori videoları getir
   */
  getFavorites(): number[] {
    try {
      const favorites = localStorage.getItem('eba_tv_favorites');
      return favorites ? JSON.parse(favorites) : [];
    } catch (error) {
      console.error('Favoriler alınamadı:', error);
      return [];
    }
  }

  /**
   * Video favori mi kontrol et
   */
  isFavorite(videoId: number): boolean {
    const favorites = this.getFavorites();
    return favorites.includes(videoId);
  }

  /**
   * Arama geçmişini kaydet
   */
  saveSearchHistory(query: string): void {
    try {
      const history = this.getSearchHistory();
      
      // Duplicate'ları kaldır
      const filteredHistory = history.filter(item => item !== query);
      
      // En başa ekle
      filteredHistory.unshift(query);
      
      // Maksimum 10 arama kaydı tut
      const limitedHistory = filteredHistory.slice(0, 10);
      
      localStorage.setItem('eba_tv_search_history', JSON.stringify(limitedHistory));
    } catch (error) {
      console.error('Arama geçmişi kaydedilemedi:', error);
    }
  }

  /**
   * Arama geçmişini getir
   */
  getSearchHistory(): string[] {
    try {
      const history = localStorage.getItem('eba_tv_search_history');
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('Arama geçmişi alınamadı:', error);
      return [];
    }
  }

  /**
   * Arama geçmişini temizle
   */
  clearSearchHistory(): void {
    try {
      localStorage.removeItem('eba_tv_search_history');
    } catch (error) {
      console.error('Arama geçmişi temizlenemedi:', error);
    }
  }

  /**
   * Video oynatma ayarlarını kaydet
   */
  savePlayerSettings(settings: {
    volume: number;
    playbackRate: number;
    subtitlesEnabled: boolean;
    autoplay: boolean;
  }): void {
    try {
      localStorage.setItem('eba_tv_player_settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Oynatıcı ayarları kaydedilemedi:', error);
    }
  }

  /**
   * Video oynatma ayarlarını getir
   */
  getPlayerSettings(): {
    volume: number;
    playbackRate: number;
    subtitlesEnabled: boolean;
    autoplay: boolean;
  } {
    try {
      const settings = localStorage.getItem('eba_tv_player_settings');
      return settings ? JSON.parse(settings) : {
        volume: 1,
        playbackRate: 1,
        subtitlesEnabled: true,
        autoplay: false
      };
    } catch (error) {
      console.error('Oynatıcı ayarları alınamadı:', error);
      return {
        volume: 1,
        playbackRate: 1,
        subtitlesEnabled: true,
        autoplay: false
      };
    }
  }
}

// Singleton instance
export const ebaTVService = new EbaTVService();
export default ebaTVService;