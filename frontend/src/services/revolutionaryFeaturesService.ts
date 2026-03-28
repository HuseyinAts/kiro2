/**
 * Revolutionary Features Service
 * Devrimsel özellikler için API servisleri
 */

import {
  FSRSCard,
  FSRSSchedule,
  BionicReadingResult,
  MultiAgentStatus,
  BlackboardEvent,
  AgentCoordination,
  RevolutionaryFeatureSettings,
  ApiResponse,
  SimplificationResult,
  TurkishZPDRange,
  ZPDRecommendation,
  CulturalContext,
  HybridLearningProfile,
  ContentRecommendation,
} from '../types/revolutionary';

// Import edilen tipler kullanılacak - duplicate tanımlar kaldırıldı

class RevolutionaryFeaturesService {
  private baseUrl = '/api/v1';

  // FSRS Servisleri
  async getFSRSCards(studentId: string, subject?: string): Promise<FSRSCard[]> {
    try {
      // Backend API çağrısı
      const params = new URLSearchParams();
      if (subject) {params.append('subject', subject);}

      const response = await fetch(`${this.baseUrl}/fsrs/cards/${studentId}?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<FSRSCard[]> = await response.json();

      if (!apiResult.success || !apiResult.data) {
        throw new Error(apiResult.message || 'FSRS kartlari alinamadi');
      }

      return apiResult.data;

    } catch (error) {
      console.error('FSRS Cards API hatası:', error);

      // Fallback: Mock implementation
      // Fallback: Mock FSRS cards

      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock kartlar
      const mockCards: FSRSCard[] = [
        {
          card_id: '1',
          content: 'Türkiye\'nin başkenti neresidir?',
          subject: subject || 'genel',
          difficulty: 2.5,
          stability: 15.2,
          retrievability: 0.85,
          last_review: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          next_review: new Date().toISOString(),
          review_count: 3,
          lapses: 0,
          state: 'review',
        },
        {
          card_id: '2',
          content: 'Osmanlı İmparatorluğu hangi yılda kurulmuştur?',
          subject: subject || 'genel',
          difficulty: 4.1,
          stability: 8.7,
          retrievability: 0.65,
          last_review: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          next_review: new Date().toISOString(),
          review_count: 5,
          lapses: 1,
          state: 'learning',
        },
      ];

      return mockCards;
    }
  }

  async getFSRSSchedules(studentId: string, subject?: string): Promise<FSRSSchedule[]> {
    try {
      // Backend API çağrısı
      const params = new URLSearchParams();
      if (subject) {params.append('subject', subject);}

      const response = await fetch(`${this.baseUrl}/fsrs/schedules/${studentId}?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<FSRSSchedule[]> = await response.json();

      if (!apiResult.success || !apiResult.data) {
        throw new Error(apiResult.message || 'FSRS cizelgeleri alinamadi');
      }

      return apiResult.data;

    } catch (error) {
      console.error('FSRS Schedules API hatası:', error);

      // Fallback: Mock implementation
      // Fallback: Mock FSRS schedules

      await new Promise(resolve => setTimeout(resolve, 400));

      const mockSchedules: FSRSSchedule[] = [
        {
          card_id: '1',
          next_reviews: {
            again: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
            hard: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
            good: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            easy: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
          },
          intervals: { again: 1, hard: 3, good: 7, easy: 14 },
          cultural_adjustments: {
            ramadan_factor: 0.8,
            exam_season_stress: 1.3,
            summer_break_decay: 0.6,
            group_study_bonus: 1.2,
            family_pressure: 1.1,
          },
          confidence_score: 0.85,
          reasoning: 'Türk öğrenci davranış kalıplarına göre optimize edildi',
        },
      ];

      return mockSchedules;
    }
  }

  async reviewFSRSCard(_studentId: string, _cardId: string, _grade: 1 | 2 | 3 | 4): Promise<void> {
    // Mock implementation - backend API henüz hazır değil
    // Mock: FSRS review

    await new Promise(resolve => setTimeout(resolve, 300));

    // Mock başarılı yanıt - gerçek implementasyonda backend'e kaydedilecek
    return Promise.resolve();
  }

  // Bionic Reading Servisleri
  async applyBionicReading(
    text: string,
    _studentId?: string,
    settings?: any,
  ): Promise<BionicReadingResult> {
    try {
      // Backend API çağrısı - Doğru endpoint kullan
      const response = await fetch(`${this.baseUrl}/bionic-reading/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          text: text,
          use_cache: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Bionic Reading işlemi başarısız');
      }

      // API sonucunu BionicReadingResult formatına çevir
      const result: BionicReadingResult = {
        orijinal_metin: apiResult.data.original_text,
        bionic_metin: apiResult.data.bionic_text,
        kok_ek_analizi: [], // Backend'den gelecek
        complexity_score: 0, // Backend'den gelecek
        readability_score: 0, // Backend'den gelecek
        processing_time: apiResult.data.processing_time_ms || 0,
      };

      return result;

    } catch (error) {
      console.error('Bionic Reading API hatası:', error);

      // Fallback: Mock implementation
      // Fallback: Mock Bionic Reading

      await new Promise(resolve => setTimeout(resolve, 800));

      const mockResult: BionicReadingResult = {
        orijinal_metin: text,
        bionic_metin: this.applyMockBionicReading(text, settings),
        kok_ek_analizi: this.analyzeMockTurkishWords(text),
        complexity_score: this.calculateMockComplexity(text),
        readability_score: this.calculateMockReadability(text),
        processing_time: 800,
      };

      return mockResult;
    }
  }

  async getBionicReadingPreferences(_studentId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/bionic-reading/preferences`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Tercihler alınamadı');
      }

      return apiResult.data;

    } catch (error) {
      console.error('Bionic Reading tercihleri API hatası:', error);

      // Fallback: Default preferences
      return {
        enabled: false,
        bold_ratio: 0.4,
        min_word_length: 3,
        auto_apply: false,
        font_weight: 'bold',
        highlight_color: '#000000',
      };
    }
  }

  async updateBionicReadingPreferences(_studentId: string, preferences: any): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/bionic-reading/preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Tercihler güncellenemedi');
      }

    } catch (error) {
      console.error('Bionic Reading tercihleri güncelleme hatası:', error);
      throw error;
    }
  }

  async processMultipleBionicTexts(texts: string[], studentId?: string): Promise<BionicReadingResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/bionic-reading/process-multiple`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          texts: texts,
          use_cache: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Çoklu metin işlemi başarısız');
      }

      // API sonuçlarını BionicReadingResult formatına çevir
      return apiResult.data.results.map((result: any) => ({
        orijinal_metin: result.data?.original_text || '',
        bionic_metin: result.data?.bionic_text || '',
        kok_ek_analizi: [],
        complexity_score: 0,
        readability_score: 0,
        processing_time: result.data?.processing_time_ms || 0,
      }));

    } catch (error) {
      console.error('Çoklu Bionic Reading API hatası:', error);

      // Fallback: Process each text individually with mock
      const results: BionicReadingResult[] = [];
      for (const text of texts) {
        const result = await this.applyBionicReading(text, studentId);
        results.push(result);
      }
      return results;
    }
  }

  private applyMockBionicReading(text: string, settings?: any): string {
    const rootBoldRatio = settings?.rootBoldRatio || 40;
    const words = text.split(/(\s+)/);

    return words.map(word => {
      if (word.trim().length < 3 || /^\s+$/.test(word)) {return word;}

      const cleanWord = word.replace(/[.,!?;:]/g, '');
      const punctuation = word.replace(cleanWord, '');

      const boldLength = Math.max(2, Math.floor(cleanWord.length * (rootBoldRatio / 100)));
      const boldPart = cleanWord.substring(0, boldLength);
      const normalPart = cleanWord.substring(boldLength);

      return `**${boldPart}**${normalPart}${punctuation}`;
    }).join('');
  }

  private analyzeMockTurkishWords(text: string) {
    const words = text.split(/\s+/).filter(w => w.length > 2);
    return words.slice(0, 5).map(word => ({
      kelime: word.replace(/[.,!?;:]/g, ''),
      kok: word.substring(0, Math.max(2, word.length - 2)),
      ekler: word.length > 4 ? [word.substring(word.length - 2)] : [],
      bionic_format: this.applyMockBionicReading(word),
    }));
  }

  private calculateMockComplexity(text: string): number {
    const avgWordLength = text.split(/\s+/).reduce((sum, word) => sum + word.length, 0) / text.split(/\s+/).length;
    return Math.min(10, avgWordLength / 2);
  }

  private calculateMockReadability(text: string): number {
    const sentences = text.split(/[.!?]+/).length;
    const words = text.split(/\s+/).length;
    const avgWordsPerSentence = words / sentences;
    return Math.max(1, 10 - (avgWordsPerSentence / 5));
  }

  // Metin Basitleştirme Servisleri
  async simplifyText(
    text: string,
    level: 'lexical' | 'syntactic' | 'semantic',
    preserveMeaning: boolean = true,
  ): Promise<SimplificationResult> {
    const response = await fetch(`${this.baseUrl}/text-simplification/simplify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        text: text,
        level: level,
        preserve_meaning: preserveMeaning,
      }),
    });

    if (!response.ok) {
      throw new Error('Metin basitleştirilemedi');
    }

    const data: ApiResponse<SimplificationResult> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Metin basitlestirme sirasinda hata olustu');
    }

    return data.data;
  }

  // Multi-Agent Servisleri
  async getMultiAgentStatus(_studentId: string): Promise<MultiAgentStatus[]> {
    // Mock implementation - backend API henüz hazır değil
    // Mock: Getting multi-agent status

    await new Promise(resolve => setTimeout(resolve, 600));

    const mockAgents: MultiAgentStatus[] = [
      {
        agent_id: 'learning_path_agent',
        name: 'learning_path_agent',
        status: 'active',
        current_task: 'Matematik öğrenme yolu oluşturuyor',
        last_activity: new Date().toISOString(),
        performance_metrics: {
          tasks_completed: 15,
          success_rate: 0.92,
          average_response_time: 1200,
        },
      },
      {
        agent_id: 'study_buddy_agent',
        name: 'study_buddy_agent',
        status: 'processing',
        current_task: 'Kişiselleştirilmiş sorular hazırlıyor',
        last_activity: new Date(Date.now() - 30000).toISOString(),
        performance_metrics: {
          tasks_completed: 23,
          success_rate: 0.87,
          average_response_time: 800,
        },
      },
      {
        agent_id: 'accessibility_agent',
        name: 'accessibility_agent',
        status: 'idle',
        current_task: undefined,
        last_activity: new Date(Date.now() - 120000).toISOString(),
        performance_metrics: {
          tasks_completed: 8,
          success_rate: 0.95,
          average_response_time: 1500,
        },
      },
    ];

    return mockAgents;
  }

  async getAgentCoordination(_studentId: string): Promise<AgentCoordination> {
    // Mock implementation - backend API henüz hazır değil
    // Mock: Getting agent coordination

    await new Promise(resolve => setTimeout(resolve, 500));

    const mockCoordination: AgentCoordination = {
      coordination_id: 'coord_' + Date.now(),
      participating_agents: ['learning_path_agent', 'study_buddy_agent', 'accessibility_agent'],
      shared_context: {
        student_learning_style: 'visual',
        current_subject: 'matematik',
        difficulty_level: 6.5,
      },
      active_tasks: [
        {
          task_id: 'task_1',
          assigned_agent: 'learning_path_agent',
          status: 'in_progress',
          dependencies: [],
        },
        {
          task_id: 'task_2',
          assigned_agent: 'study_buddy_agent',
          status: 'pending',
          dependencies: ['task_1'],
        },
      ],
      performance_summary: {
        total_tasks: 50,
        completed_tasks: 46,
        failed_tasks: 2,
        average_completion_time: 2.3,
      },
    };

    return mockCoordination;
  }

  async getBlackboardEvents(_studentId: string, limit: number = 10): Promise<BlackboardEvent[]> {
    // Mock implementation - backend API henüz hazır değil
    // Mock: Getting blackboard events

    await new Promise(resolve => setTimeout(resolve, 400));

    const mockEvents: BlackboardEvent[] = [
      {
        event_id: 'event_1',
        type: 'learning_style_detected',
        source_agent: 'learning_path_agent',
        target_agents: ['study_buddy_agent', 'accessibility_agent'],
        data: { style: 'visual', confidence: 0.85 },
        timestamp: new Date(Date.now() - 300000).toISOString(),
        processed: true,
      },
      {
        event_id: 'event_2',
        type: 'difficulty_adjusted',
        source_agent: 'study_buddy_agent',
        target_agents: ['learning_path_agent'],
        data: { new_difficulty: 6.5, reason: 'performance_improvement' },
        timestamp: new Date(Date.now() - 180000).toISOString(),
        processed: true,
      },
      {
        event_id: 'event_3',
        type: 'content_simplified',
        source_agent: 'accessibility_agent',
        target_agents: ['study_buddy_agent'],
        data: { original_complexity: 8.2, simplified_complexity: 5.1 },
        timestamp: new Date(Date.now() - 120000).toISOString(),
        processed: false,
      },
    ].slice(0, limit);

    return mockEvents;
  }

  // Öğrenme Stili Servisleri
  async detectLearningStyle(studentId: string): Promise<HybridLearningProfile> {
    const response = await fetch(`${this.baseUrl}/learning-style/detect/${studentId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Öğrenme stili tespit edilemedi');
    }

    const data: ApiResponse<HybridLearningProfile> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Ogrenme stili tespiti sirasinda hata olustu');
    }

    return data.data;
  }

  async getContentRecommendations(studentId: string): Promise<ContentRecommendation> {
    const response = await fetch(`${this.baseUrl}/learning-style/recommendations/${studentId}`);

    if (!response.ok) {
      throw new Error('Icerik onerileri yuklenemedi');
    }

    const data: ApiResponse<ContentRecommendation> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Icerik onerileri alinirken hata olustu');
    }

    return data.data;
  }

  async getLearningStyleExplanation(studentId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/learning-style/explanation/${studentId}`);

    if (!response.ok) {
      throw new Error('Öğrenme stili açıklaması yüklenemedi');
    }

    const data: ApiResponse<any> = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Öğrenme stili açıklaması alınırken hata oluştu');
    }

    return data.data;
  }

  // ZPD Maarif Servisleri
  async calculateRevolutionaryZPD(
    studentId: string,
    subject: string,
    currentLevel: number,
    behavioralData: any,
    contentDescription: string = '',
  ): Promise<TurkishZPDRange> {
    const response = await fetch(`${this.baseUrl}/zpd-maarif/revolutionary/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        subject: subject,
        current_level: currentLevel,
        behavioral_data: behavioralData,
        content_description: contentDescription,
      }),
    });

    if (!response.ok) {
      throw new Error('ZPD hesaplanamadı');
    }

    const data: ApiResponse<TurkishZPDRange> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'ZPD hesaplama sirasinda hata olustu');
    }

    return data.data;
  }

  async generateRevolutionaryRecommendation(
    studentId: string,
    subject: string,
    currentLevel: number,
    behavioralData: any,
    learningObjective: string,
    contentDescription: string = '',
  ): Promise<ZPDRecommendation> {
    const response = await fetch(`${this.baseUrl}/zpd-maarif/revolutionary/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        subject: subject,
        current_level: currentLevel,
        behavioral_data: behavioralData,
        learning_objective: learningObjective,
        content_description: contentDescription,
      }),
    });

    if (!response.ok) {
      throw new Error('ZPD onerisi olusturulamadi');
    }

    const data: ApiResponse<ZPDRecommendation> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'ZPD onerisi olusturma sirasinda hata olustu');
    }

    return data.data;
  }

  async detectCulturalContext(studentId: string, behavioralData: any): Promise<CulturalContext> {
    const response = await fetch(`${this.baseUrl}/zpd-maarif/revolutionary/cultural-context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        behavioral_data: behavioralData,
      }),
    });

    if (!response.ok) {
      throw new Error('Kulturel baglam tespit edilemedi');
    }

    const data: ApiResponse<CulturalContext> = await response.json();
    if (!data.success || !data.data) {
      throw new Error(data.message || 'Kulturel baglam tespiti sirasinda hata olustu');
    }

    return data.data;
  }

  // Ayarlar Servisleri
  async getRevolutionarySettings(studentId: string): Promise<RevolutionaryFeatureSettings> {
    try {
      const response = await fetch(`${this.baseUrl}/revolutionary-features/settings/${studentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<RevolutionaryFeatureSettings> = await response.json();

      if (!apiResult.success || !apiResult.data) {
        throw new Error(apiResult.message || 'Ayarlar alinamadi');
      }

      return apiResult.data;

    } catch (error) {
      console.error('Revolutionary Settings API hatası:', error);

      // Fallback: Mock implementation
      // Fallback: Mock revolutionary settings

      await new Promise(resolve => setTimeout(resolve, 500));

      const mockSettings: RevolutionaryFeatureSettings = {
        fsrs_enabled: true,
        bionic_reading_enabled: false,
        text_simplification_level: 'semantic',
        multi_agent_coordination: true,
        cultural_adaptations: {
          ramadan_mode: false,
          exam_season_stress: true,
          group_study_preference: true,
        },
        accessibility_features: {
          high_contrast: false,
          large_text: false,
          screen_reader_optimized: false,
        },
      };

      return mockSettings;
    }
  }

  async updateRevolutionarySettings(
    studentId: string,
    settings: RevolutionaryFeatureSettings,
  ): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/revolutionary-features/settings/${studentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const apiResult: ApiResponse<any> = await response.json();

      if (!apiResult.success) {
        throw new Error(apiResult.message || 'Ayarlar güncellenemedi');
      }

    } catch (error) {
      console.error('Revolutionary Settings güncelleme hatası:', error);

      // Fallback: Mock implementation
      // Fallback: Mock updating revolutionary settings

      await new Promise(resolve => setTimeout(resolve, 800));
    }
  }

  async resetRevolutionarySettings(_studentId: string): Promise<RevolutionaryFeatureSettings> {
    // Mock implementation - backend API henüz hazır değil
    // Mock: Resetting revolutionary settings

    await new Promise(resolve => setTimeout(resolve, 600));

    const defaultSettings: RevolutionaryFeatureSettings = {
      fsrs_enabled: true,
      bionic_reading_enabled: false,
      text_simplification_level: 'semantic',
      multi_agent_coordination: true,
      cultural_adaptations: {
        ramadan_mode: false,
        exam_season_stress: true,
        group_study_preference: true,
      },
      accessibility_features: {
        high_contrast: false,
        large_text: false,
        screen_reader_optimized: false,
      },
    };

    return defaultSettings;
  }

  // İstatistikler
  async getRevolutionaryStats(studentId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/revolutionary-features/stats/${studentId}`);

    if (!response.ok) {
      throw new Error('Devrimsel özellik istatistikleri yüklenemedi');
    }

    const data: ApiResponse<any> = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'İstatistikler alınırken hata oluştu');
    }

    return data.data;
  }

  // IRT İstatistikleri
  async getIRTStatistics(params?: { subject?: string; examType?: string }): Promise<IRTStatistics> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.subject) {queryParams.append('subject', params.subject);}
      if (params?.examType) {queryParams.append('exam_type', params.examType);}

      const response = await fetch(`${this.baseUrl}/irt/statistics?${queryParams}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const data: ApiResponse<IRTStatistics> = await response.json();
      if (!data.success || !data.data) {
        throw new Error(data.message || 'IRT istatistikleri alinamadi');
      }

      return data.data;

    } catch (error) {
      console.error('IRT Statistics API hatası:', error);

      // Fallback: Mock implementation
      return {
        total_questions: 37350,
        calibrated_questions: 35000,
        average_difficulty: 0.52,
        average_discrimination: 0.68,
        reliability_coefficient: 0.89,
        subjects: ['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce', 'tarih', 'cografya'],
        difficulty_distribution: { easy: 0.25, medium: 0.50, hard: 0.25 },
      };
    }
  }

  // Kalite Raporu
  async getQualityReport(questionId?: string): Promise<QualityReport> {
    try {
      const url = questionId
        ? `${this.baseUrl}/quality/report/${questionId}`
        : `${this.baseUrl}/quality/report`;

      const response = await fetch(url, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const data: ApiResponse<QualityReport> = await response.json();
      if (!data.success || !data.data) {
        throw new Error(data.message || 'Kalite raporu alinamadi');
      }

      return data.data;

    } catch (error) {
      console.error('Quality Report API hatası:', error);

      // Fallback: Mock implementation
      return {
        overall_score: 0.85,
        content_quality: 0.88,
        pedagogical_quality: 0.82,
        technical_quality: 0.86,
        accessibility_score: 0.79,
        recommendations: [
          'Daha fazla görsel içerik ekleyin',
          'Soru çeldirici kalitesini artırın',
        ],
        generated_at: new Date().toISOString(),
      };
    }
  }

  // Hızlı Soru Değerlendirmesi
  async quickQuestionEvaluation(questionId: string): Promise<QuickQuestionEvaluation> {
    try {
      const response = await fetch(`${this.baseUrl}/questions/${questionId}/quick-evaluation`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`API hatası: ${response.status}`);
      }

      const data: ApiResponse<QuickQuestionEvaluation> = await response.json();
      if (!data.success || !data.data) {
        throw new Error(data.message || 'Soru degerlendirmesi alinamadi');
      }

      return data.data;

    } catch (error) {
      console.error('Quick Question Evaluation API hatası:', error);

      // Fallback: Mock implementation
      return {
        question_id: questionId,
        difficulty_estimate: 0.55,
        discrimination_estimate: 0.72,
        quality_score: 0.84,
        irt_parameters: { a: 1.2, b: 0.3, c: 0.2 },
        recommended_level: 'orta',
        evaluation_confidence: 0.88,
        suggestions: [],
      };
    }
  }
}

// Ek tipler
export interface IRTStatistics {
  total_questions: number;
  calibrated_questions: number;
  average_difficulty: number;
  average_discrimination: number;
  reliability_coefficient: number;
  subjects: string[];
  difficulty_distribution: { easy: number; medium: number; hard: number };
}

export interface QualityReport {
  overall_score: number;
  content_quality: number;
  pedagogical_quality: number;
  technical_quality: number;
  accessibility_score: number;
  recommendations: string[];
  generated_at: string;
}

export interface QuickQuestionEvaluation {
  question_id: string;
  difficulty_estimate: number;
  discrimination_estimate: number;
  quality_score: number;
  irt_parameters: { a: number; b: number; c: number };
  recommended_level: string;
  evaluation_confidence: number;
  suggestions: string[];
  // Additional fields used by IRTMorphologyAnalysis
  tahmini_zorluk?: number;
  morfolojik_karmasiklik?: number;
  uygunluk_skoru?: number;
  zorluk_seviyesi?: string;
  oneriler?: string[];
}

// Re-export types from types/revolutionary for components that import from this service
export type {
  QuestionAnalysis,
  StudentMorphologyProfile,
} from '../types';

export type {
  HybridLearningProfile,
  ContentRecommendation,
} from '../types/revolutionary';

export const revolutionaryFeaturesService = new RevolutionaryFeaturesService();
export default revolutionaryFeaturesService;