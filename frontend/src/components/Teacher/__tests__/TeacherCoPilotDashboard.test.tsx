import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TeacherCoPilotDashboard } from '../TeacherCoPilotDashboard';

describe('TeacherCoPilotDashboard Component', () => {
  it('renders Teacher Co-Pilot Dashboard correctly with fallback data', async () => {
    // Mock global fetch
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        json: async () => ({
          success: true,
          data: {
            class_id: '12-A',
            class_name: 'Sınıf 12-A (YKS Sayısal Maratonu)',
            total_students: 32,
            zpd_distribution: {
              scaffolding_needed: 8,
              independent_mastery: 19,
              advanced_mastery: 5,
              scaffolding_percentage: 25.0,
              independent_percentage: 59.4,
              advanced_percentage: 15.6,
            },
            fsrs_retention: {
              average_retention_rate: 84.2,
              decay_risk_cards_count: 48,
              decay_risk_topics: ['Türevde Ekstremum Noktaları'],
              recommended_review_date: '2026-08-10',
            },
            misconception_alerts: [
              {
                alert_id: 'alert-01',
                class_id: '12-A',
                subject: 'Matematik',
                topic: 'Türev',
                risk_level: 'HIGH',
                affected_students_count: 12,
                misconception_title: 'Teğet Eğimi ile Yerel Ekstremum Karıştırılması',
                ai_socratic_recommendation: 'Türevin sıfır olduğu noktayı inceleyin.',
                created_at: '2026-08-06',
              },
            ],
            timestamp: '2026-08-06',
          },
        }),
      })
    );

    render(<TeacherCoPilotDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Pedagojik AI Co-Pilot Paneli/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Yakınsal Gelişim Alanı \(ZPD\) Dağılımı/i)).toBeInTheDocument();
    expect(screen.getByText(/FSRS-6 Unutma Eğrisi/i)).toBeInTheDocument();
    expect(screen.getByText(/Teğet Eğimi ile Yerel Ekstremum Karıştırılması/i)).toBeInTheDocument();
  });

  // --- Veri kaynağı beyanı (7 Ağu 2026) ---
  // Backend yanıtı `data_source: "mock"` taşıyor ama ekranda görünmezse
  // öğretmen sabit veriyi gerçek ölçüm sanır. Eski rozet düpedüz "Canlı"
  // diyordu. Bu iki test, etiketin ekrana ulaştığını çiviler.

  const yanit = (dataSource?: string) => ({
    json: async () => ({
      success: true,
      data_source: dataSource,
      data: {
        class_id: '12-A',
        class_name: 'Sınıf 12-A',
        total_students: 32,
        zpd_distribution: {
          scaffolding_needed: 8,
          independent_mastery: 19,
          advanced_mastery: 5,
          scaffolding_percentage: 25.0,
          independent_percentage: 59.4,
          advanced_percentage: 15.6,
        },
        fsrs_retention: {
          average_retention_rate: 84.2,
          decay_risk_cards_count: 48,
          decay_risk_topics: ['Türev'],
          recommended_review_date: '2026-08-10',
        },
        misconception_alerts: [],
        timestamp: '2026-08-06',
      },
    }),
  });

  it('mock veride "ÖRNEK VERİ" rozetini gösterir, "Canlı" demez', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(yanit('mock')));
    render(<TeacherCoPilotDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/ÖRNEK VERİ — gerçek ölçüm değil/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/Canlı ZPD & FSRS-6 Akışı/i)).not.toBeInTheDocument();
  });

  it('data_source eksikse güvenli tarafa düşer (mock kabul eder)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(yanit(undefined)));
    render(<TeacherCoPilotDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/ÖRNEK VERİ — gerçek ölçüm değil/i)).toBeInTheDocument();
    });
  });
});
