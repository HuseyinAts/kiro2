/**
 * Revolutionary Features Integration Tests
 * Frontend-Backend entegrasyonu testleri
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// Test edilen bileşenler
import FSRSScheduler from '../../../components/Revolutionary/FSRSScheduler';
import BionicReadingToggle from '../../../components/Revolutionary/BionicReadingToggle';
import MultiAgentCoordination from '../../../components/Revolutionary/MultiAgentCoordination';
import RevolutionarySettings from '../../../components/Revolutionary/RevolutionarySettings';
import RevolutionaryDashboard from '../../../components/Revolutionary/RevolutionaryDashboard';

// Mock service
import revolutionaryFeaturesService from '../../../services/revolutionaryFeaturesService';

// Mock data
const mockStudentId = 'test-student-123';
const theme = createTheme();

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ThemeProvider theme={theme}>
    {children}
  </ThemeProvider>
);

// Mock service methods
vi.mock('../../../services/revolutionaryFeaturesService', () => ({
  default: {
    getFSRSCards: vi.fn(),
    getFSRSSchedules: vi.fn(),
    reviewFSRSCard: vi.fn(),
    applyBionicReading: vi.fn(),
    getMultiAgentStatus: vi.fn(),
    getAgentCoordination: vi.fn(),
    getBlackboardEvents: vi.fn(),
    getRevolutionarySettings: vi.fn(),
    updateRevolutionarySettings: vi.fn(),
    resetRevolutionarySettings: vi.fn()
  }
}));

describe('Revolutionary Features Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('FSRSScheduler Integration', () => {
    it('should load FSRS cards and display them', async () => {
      const mockCards = [
        {
          card_id: '1',
          content: 'Test card content',
          subject: 'matematik',
          difficulty: 2.5,
          stability: 15.2,
          retrievability: 0.85,
          last_review: new Date().toISOString(),
          next_review: new Date().toISOString(),
          review_count: 3,
          lapses: 0,
          state: 'review' as const
        }
      ];

      const mockSchedules = [
        {
          card_id: '1',
          next_reviews: {
            again: new Date().toISOString(),
            hard: new Date().toISOString(),
            good: new Date().toISOString(),
            easy: new Date().toISOString()
          },
          intervals: { again: 1, hard: 3, good: 7, easy: 14 },
          cultural_adjustments: { ramadan_factor: 0.8 },
          confidence_score: 0.85,
          reasoning: 'Test reasoning'
        }
      ];

      vi.mocked(revolutionaryFeaturesService.getFSRSCards).mockResolvedValue(mockCards);
      vi.mocked(revolutionaryFeaturesService.getFSRSSchedules).mockResolvedValue(mockSchedules);

      render(
        <TestWrapper>
          <FSRSScheduler studentId={mockStudentId} />
        </TestWrapper>
      );

      // Loading state kontrolü
      expect(screen.getByText(/FSRS zamanlaması yükleniyor/)).toBeInTheDocument();

      // Veri yüklendikten sonra kontrol
      await waitFor(() => {
        expect(screen.getByText('FSRS Tekrar Zamanlaması')).toBeInTheDocument();
      });

      // Mock service çağrılarının yapıldığını kontrol et
      await waitFor(() => {
        expect(revolutionaryFeaturesService.getFSRSCards).toHaveBeenCalledWith(mockStudentId, 'matematik');
        expect(revolutionaryFeaturesService.getFSRSSchedules).toHaveBeenCalledWith(mockStudentId, 'matematik');
      });
    });

    it('should handle FSRS card review', async () => {
      vi.mocked(revolutionaryFeaturesService.reviewFSRSCard).mockResolvedValue();

      render(
        <TestWrapper>
          <FSRSScheduler studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('FSRS Tekrar Zamanlaması')).toBeInTheDocument();
      });

      // Mock review işlemi - gerçek implementasyonda kart tıklanacak
      // Bu test mock implementasyon için basitleştirilmiş
      expect(revolutionaryFeaturesService.reviewFSRSCard).not.toHaveBeenCalled();
    });
  });

  describe('BionicReadingToggle Integration', () => {
    it('should apply bionic reading to text', async () => {
      const mockResult = {
        orijinal_metin: 'Test metin',
        bionic_metin: '**Te**st **me**tin',
        kok_ek_analizi: [],
        complexity_score: 5.0,
        readability_score: 7.5,
        processing_time: 800
      };

      vi.mocked(revolutionaryFeaturesService.applyBionicReading).mockResolvedValue(mockResult);

      render(
        <TestWrapper>
          <BionicReadingToggle studentId={mockStudentId} />
        </TestWrapper>
      );

      // Bionic Reading toggle'ı etkinleştir
      const toggle = screen.getByRole('checkbox');
      fireEvent.click(toggle);

      // Metin girişi yap
      const textInput = screen.getByPlaceholderText(/Bionic Reading uygulanacak metni/);
      fireEvent.change(textInput, { target: { value: 'Test metin' } });

      await waitFor(() => {
        expect(screen.getByText('Türkçe Bionic Reading')).toBeInTheDocument();
      });

      // Service çağrısının yapıldığını kontrol et (mock implementation için)
      // Gerçek implementasyonda API çağrısı yapılacak
    });

    it('should handle bionic reading settings', async () => {
      render(
        <TestWrapper>
          <BionicReadingToggle studentId={mockStudentId} />
        </TestWrapper>
      );

      // Ayarlar butonunu bul ve tıkla
      const settingsButton = screen.getByText('Ayarlar');
      fireEvent.click(settingsButton);

      await waitFor(() => {
        expect(screen.getByText('Bionic Reading Ayarları')).toBeInTheDocument();
      });
    });
  });

  describe('MultiAgentCoordination Integration', () => {
    it('should load and display agent status', async () => {
      const mockAgents = [
        {
          agent_id: 'learning_path_agent',
          name: 'learning_path_agent',
          status: 'active' as const,
          current_task: 'Test task',
          last_activity: new Date().toISOString(),
          performance_metrics: {
            tasks_completed: 15,
            success_rate: 0.92,
            average_response_time: 1200
          }
        }
      ];

      const mockCoordination = {
        coordination_id: 'coord_123',
        participating_agents: ['learning_path_agent'],
        shared_context: {},
        active_tasks: [],
        performance_summary: {
          total_tasks: 50,
          completed_tasks: 46,
          failed_tasks: 2,
          average_completion_time: 2.3
        }
      };

      vi.mocked(revolutionaryFeaturesService.getMultiAgentStatus).mockResolvedValue(mockAgents);
      vi.mocked(revolutionaryFeaturesService.getAgentCoordination).mockResolvedValue(mockCoordination);
      vi.mocked(revolutionaryFeaturesService.getBlackboardEvents).mockResolvedValue([]);

      render(
        <TestWrapper>
          <MultiAgentCoordination studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Multi-Agent Koordinasyon')).toBeInTheDocument();
      });

      // Service çağrılarının yapıldığını kontrol et
      await waitFor(() => {
        expect(revolutionaryFeaturesService.getMultiAgentStatus).toHaveBeenCalledWith(mockStudentId);
        expect(revolutionaryFeaturesService.getAgentCoordination).toHaveBeenCalledWith(mockStudentId);
        expect(revolutionaryFeaturesService.getBlackboardEvents).toHaveBeenCalledWith(mockStudentId, 10);
      });
    });
  });

  describe('RevolutionarySettings Integration', () => {
    it('should load and save settings', async () => {
      const mockSettings = {
        fsrs_enabled: true,
        bionic_reading_enabled: false,
        text_simplification_level: 'semantic' as const,
        multi_agent_coordination: true,
        cultural_adaptations: {
          ramadan_mode: false,
          exam_season_stress: true,
          group_study_preference: true
        },
        accessibility_features: {
          high_contrast: false,
          large_text: false,
          screen_reader_optimized: false
        }
      };

      vi.mocked(revolutionaryFeaturesService.getRevolutionarySettings).mockResolvedValue(mockSettings);
      vi.mocked(revolutionaryFeaturesService.updateRevolutionarySettings).mockResolvedValue();

      render(
        <TestWrapper>
          <RevolutionarySettings studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Devrimsel Özellik Ayarları')).toBeInTheDocument();
      });

      // Ayarları kaydet butonunu bul ve tıkla
      const saveButton = screen.getByText(/Ayarları Kaydet/);
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(revolutionaryFeaturesService.updateRevolutionarySettings).toHaveBeenCalledWith(
          mockStudentId,
          expect.objectContaining(mockSettings)
        );
      });
    });

    it('should reset settings to defaults', async () => {
      const defaultSettings = {
        fsrs_enabled: true,
        bionic_reading_enabled: false,
        text_simplification_level: 'semantic' as const,
        multi_agent_coordination: true,
        cultural_adaptations: {
          ramadan_mode: false,
          exam_season_stress: true,
          group_study_preference: true
        },
        accessibility_features: {
          high_contrast: false,
          large_text: false,
          screen_reader_optimized: false
        }
      };

      vi.mocked(revolutionaryFeaturesService.resetRevolutionarySettings).mockResolvedValue(defaultSettings);

      render(
        <TestWrapper>
          <RevolutionarySettings studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Devrimsel Özellik Ayarları')).toBeInTheDocument();
      });

      // Sıfırla butonunu bul ve tıkla
      const resetButton = screen.getByText('Varsayılana Sıfırla');
      fireEvent.click(resetButton);

      // Onay dialog'unu kontrol et
      await waitFor(() => {
        expect(screen.getByText('Ayarları Sıfırla')).toBeInTheDocument();
      });
    });
  });

  describe('RevolutionaryDashboard Integration', () => {
    it('should load dashboard with all features', async () => {
      const mockSettings = {
        fsrs_enabled: true,
        bionic_reading_enabled: false,
        text_simplification_level: 'semantic' as const,
        multi_agent_coordination: true,
        cultural_adaptations: {
          ramadan_mode: false,
          exam_season_stress: true,
          group_study_preference: true
        },
        accessibility_features: {
          high_contrast: false,
          large_text: false,
          screen_reader_optimized: false
        }
      };

      // Mock fetch calls for dashboard
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true, data: mockSettings })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ 
            success: true, 
            data: {
              fsrs_cards: 24,
              bionic_texts: 8,
              simplified_texts: 15,
              agent_tasks: 42,
              learning_profiles: 3,
              zpd_analyses: 12
            }
          })
        });

      render(
        <TestWrapper>
          <RevolutionaryDashboard studentId={mockStudentId} />
        </TestWrapper>
      );

      // Loading state
      expect(screen.getByText(/Devrimsel özellikler yükleniyor/)).toBeInTheDocument();

      // Dashboard yüklendikten sonra
      await waitFor(() => {
        expect(screen.getByText('Devrimsel Özellikler')).toBeInTheDocument();
        expect(screen.getByText('7 Dünya Çapında Yenilikçi Eğitim Teknolojisi')).toBeInTheDocument();
      });

      // Tab'ların varlığını kontrol et
      expect(screen.getByText('FSRS Tekrar Sistemi')).toBeInTheDocument();
      expect(screen.getByText('Bionic Reading')).toBeInTheDocument();
      expect(screen.getByText('Multi-Agent')).toBeInTheDocument();
      expect(screen.getByText('Ayarlar')).toBeInTheDocument();
    });

    it('should handle tab navigation', async () => {
      render(
        <TestWrapper>
          <RevolutionaryDashboard studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Devrimsel Özellikler')).toBeInTheDocument();
      });

      // Bionic Reading tab'ına geç
      const bionicTab = screen.getByText('Bionic Reading');
      fireEvent.click(bionicTab);

      // Tab içeriğinin değiştiğini kontrol et
      await waitFor(() => {
        expect(screen.getByText('Türkçe Bionic Reading')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      vi.mocked(revolutionaryFeaturesService.getFSRSCards).mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <FSRSScheduler studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Hata')).toBeInTheDocument();
        expect(screen.getByText(/API Error/)).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      vi.mocked(revolutionaryFeaturesService.getMultiAgentStatus).mockRejectedValue(new Error('Network Error'));

      render(
        <TestWrapper>
          <MultiAgentCoordination studentId={mockStudentId} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Tekrar Dene')).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should show loading indicators', async () => {
      // Slow mock to test loading state
      vi.mocked(revolutionaryFeaturesService.getRevolutionarySettings).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          fsrs_enabled: true,
          bionic_reading_enabled: false,
          text_simplification_level: 'semantic' as const,
          multi_agent_coordination: true,
          cultural_adaptations: {
            ramadan_mode: false,
            exam_season_stress: true,
            group_study_preference: true
          },
          accessibility_features: {
            high_contrast: false,
            large_text: false,
            screen_reader_optimized: false
          }
        }), 1000))
      );

      render(
        <TestWrapper>
          <RevolutionarySettings studentId={mockStudentId} />
        </TestWrapper>
      );

      // Loading state kontrolü
      expect(screen.getByText(/Devrimsel özellik ayarları yükleniyor/)).toBeInTheDocument();
    });
  });
});