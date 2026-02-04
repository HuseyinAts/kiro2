/**
 * Cultural Adaptation API Servisi
 * Teknofest 2025 - Eğitim Eylemci Projesi
 */

import { CulturalContext, ApiResponse } from '../types/revolutionary';
import config from '../config';

const API_BASE_URL = config.api.baseURL;

export interface CulturalAdaptationResult {
  student_id: string;
  cultural_adaptation: {
    current_period: string;
    adaptation_multiplier: number;
    group_study_emphasis: number;
    family_involvement_level: number;
    teacher_guidance_preference: number;
    individual_focus_emphasis: number;
    motivational_message_type: string;
    cultural_context_explanation: string;
  };
  context_analysis: {
    detected_patterns: string[];
    confidence_scores: Record<string, number>;
    behavioral_indicators: Record<string, any>;
  };
  cultural_factors: {
    family_pressure_level: number;
    group_study_preference: number;
    teacher_respect_level: number;
    peer_competition_level: number;
    authority_acceptance_level: number;
    collective_success_orientation: number;
    elder_wisdom_value: number;
    social_harmony_importance: number;
  };
  recommendations: {
    study_approach: string;
    content_delivery: string;
    motivation_strategy: string;
    social_learning_balance: number;
  };
  last_updated: string;
}

export interface BehavioralUpdate {
  behavioral_data: Record<string, any>;
  context_changes: Record<string, any>;
  performance_indicators: Record<string, number>;
  timestamp: string;
}

class CulturalAdaptationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/cultural-adaptation`;
  }

  /**
   * Öğrenci kültürel adaptasyonunu getir
   */
  async getStudentCulturalAdaptation(
    studentId: string,
    forceRefresh: boolean = false
  ): Promise<ApiResponse<CulturalAdaptationResult>> {
    try {
      const params = new URLSearchParams();
      if (forceRefresh) {
        params.append('force_refresh', 'true');
      }

      const response = await fetch(
        `${this.baseUrl}/student/${studentId}?${params}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get cultural adaptation error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel adaptasyon getirme hatası',
      };
    }
  }

  /**
   * Davranışsal güncelleme gönder
   */
  async updateBehavioralData(
    studentId: string,
    behavioralUpdate: BehavioralUpdate
  ): Promise<ApiResponse<CulturalAdaptationResult>> {
    try {
      const response = await fetch(`${this.baseUrl}/student/${studentId}/behavioral-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(behavioralUpdate),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Update behavioral data error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Davranışsal veri güncelleme hatası',
      };
    }
  }

  /**
   * Kültürel bağlam tespit et
   */
  async detectCulturalContext(
    studentId: string,
    behavioralData: Record<string, any>
  ): Promise<ApiResponse<CulturalContext>> {
    try {
      const response = await fetch(`${this.baseUrl}/detect-context`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          behavioral_data: behavioralData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Detect cultural context error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel bağlam tespit hatası',
      };
    }
  }

  /**
   * Kültürel faktörleri güncelle
   */
  async updateCulturalFactors(
    studentId: string,
    culturalFactors: Record<string, number>
  ): Promise<ApiResponse<CulturalAdaptationResult>> {
    try {
      const response = await fetch(`${this.baseUrl}/student/${studentId}/cultural-factors`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          cultural_factors: culturalFactors,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Update cultural factors error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel faktör güncelleme hatası',
      };
    }
  }

  /**
   * Kültürel dönem bilgisi al
   */
  async getCurrentCulturalPeriod(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/current-period`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get current cultural period error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel dönem bilgisi alma hatası',
      };
    }
  }

  /**
   * Bölgesel kültür bilgisi al
   */
  async getRegionalCulture(region: string): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/regional-culture/${region}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get regional culture error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Bölgesel kültür bilgisi alma hatası',
      };
    }
  }

  /**
   * Kültürel adaptasyon önerilerini al
   */
  async getCulturalRecommendations(
    studentId: string,
    subject?: string,
    learningObjective?: string
  ): Promise<ApiResponse<any>> {
    try {
      const params = new URLSearchParams();
      if (subject) params.append('subject', subject);
      if (learningObjective) params.append('learning_objective', learningObjective);

      const response = await fetch(
        `${this.baseUrl}/student/${studentId}/recommendations?${params}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get cultural recommendations error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel öneriler alma hatası',
      };
    }
  }

  /**
   * Kültürel adaptasyon geçmişini al
   */
  async getCulturalHistory(
    studentId: string,
    limit: number = 10
  ): Promise<ApiResponse<any[]>> {
    try {
      const response = await fetch(
        `${this.baseUrl}/student/${studentId}/history?limit=${limit}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get cultural history error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Kültürel geçmiş alma hatası',
      };
    }
  }

  /**
   * Sistem sağlık kontrolü
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.status === 'healthy',
        data: data,
        message: data.status === 'healthy' ? 'Kültürel adaptasyon sistemi sağlıklı' : 'Sistem sağlıksız',
      };
    } catch (error) {
      console.error('Cultural adaptation health check error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Sağlık kontrolü hatası',
      };
    }
  }
}

// Singleton instance
const culturalAdaptationService = new CulturalAdaptationService();

export default culturalAdaptationService;