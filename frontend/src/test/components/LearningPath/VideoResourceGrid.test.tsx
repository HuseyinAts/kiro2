/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * VideoResourceGrid Component Tests
 * 
 * Enhanced video resource grid bileşeni için testler
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { VideoResourceGrid } from '../../../components/LearningPath/VideoResourceGrid';
import { VideoResponse } from '../../../api';

// Mock video data
const mockVideos: VideoResponse[] = [
  {
    video_id: 'test-video-1',
    title: 'Matematik Türev Konu Anlatımı',
    channel: 'TonguçAkademi',
    channel_id: 'channel-1',
    duration: 'PT15M30S',
    view_count: 50000,
    upload_date: '2024-01-15',
    thumbnail: 'https://example.com/thumb1.jpg',
    quality_score: 0.85,
    subject: 'matematik',
    difficulty: 'orta',
    exam_type: 'YKS',
    url: 'https://youtube.com/watch?v=test1',
    scores: {
      turkish_score: 0.95,
      relevance_score: 0.88,
      quality_score: 0.82,
      final_score: 0.87
    },
    is_accessible: true,
    is_embeddable: true,
    is_turkish: true,
    description: 'Türev konusunu detaylı anlatım',
    duration_minutes: 15,
    like_count: 2500,
    tags: ['matematik', 'türev', 'yks'],
    caption_available: true,
    definition: 'hd'
  },
  {
    video_id: 'test-video-2',
    title: 'Fizik Hareket Konusu',
    channel: 'Khan Academy Türkçe',
    channel_id: 'channel-2',
    duration: 'PT20M',
    view_count: 30000,
    upload_date: '2024-01-10',
    thumbnail: 'https://example.com/thumb2.jpg',
    quality_score: 0.75,
    subject: 'fizik',
    difficulty: 'başlangıç',
    exam_type: 'LGS',
    url: 'https://youtube.com/watch?v=test2',
    scores: {
      turkish_score: 0.90,
      relevance_score: 0.75,
      quality_score: 0.70,
      final_score: 0.78
    },
    is_accessible: true,
    is_embeddable: true,
    is_turkish: true,
    description: 'Hareket konusu temel anlatım',
    duration_minutes: 20,
    like_count: 1500,
    tags: ['fizik', 'hareket', 'lgs'],
    caption_available: false,
    definition: 'sd'
  },
  {
    video_id: 'test-video-3',
    title: 'Kimya Atom Yapısı',
    channel: 'KAMP Online',
    channel_id: 'channel-3',
    duration: 'PT10M',
    view_count: 20000,
    upload_date: '2024-01-05',
    thumbnail: 'https://example.com/thumb3.jpg',
    quality_score: 0.65,
    subject: 'kimya',
    difficulty: 'ileri',
    exam_type: 'YKS',
    url: 'https://youtube.com/watch?v=test3',
    scores: {
      turkish_score: 0.85,
      relevance_score: 0.80,
      quality_score: 0.65,
      final_score: 0.75
    },
    is_accessible: false,
    is_embeddable: false,
    is_turkish: true,
    description: 'Atom yapısı ileri seviye',
    duration_minutes: 10,
    like_count: 800,
    tags: ['kimya', 'atom', 'yks'],
    caption_available: true,
    definition: 'hd'
  }
];

describe('VideoResourceGrid - Enhanced Video Scores', () => {
  it('videoları başarıyla render eder', () => {
    const { container } = render(<VideoResourceGrid videos={mockVideos} />);
    
    // Video başlıklarının görünür olduğunu kontrol et
    expect(screen.getByText('Matematik Türev Konu Anlatımı')).toBeInTheDocument();
    expect(screen.getByText('Fizik Hareket Konusu')).toBeInTheDocument();
    expect(screen.getByText('Kimya Atom Yapısı')).toBeInTheDocument();
    
    // Grid container'ın render edildiğini kontrol et
    expect(container.querySelector('.MuiGrid-container')).toBeInTheDocument();
  });

  it('loading durumunda gelişmiş skeleton ve bilgilendirme gösterir', () => {
    render(<VideoResourceGrid videos={[]} loading={true} />);
    
    // Loading mesajını kontrol et
    expect(screen.getByText(/en uygun Türkçe eğitim videoları aranıyor/i)).toBeInTheDocument();
    expect(screen.getByText(/Türkçe içerik, konu uygunluğu ve kalite kontrolünden geçiriliyor/i)).toBeInTheDocument();
  });

  it('hata durumunda gelişmiş hata mesajı ve yardım gösterir', () => {
    const errorMessage = 'Video yükleme hatası';
    render(<VideoResourceGrid videos={[]} error={errorMessage} />);
    
    // Hata mesajını kontrol et
    expect(screen.getByText(/video yüklenirken bir hata oluştu/i)).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    
    // Yardımcı bilgilerin göründüğünü kontrol et
    expect(screen.getByText(/ne yapabilirsiniz/i)).toBeInTheDocument();
    expect(screen.getByText(/İnternet bağlantınızı kontrol edin/i)).toBeInTheDocument();
  });

  it('erişilebilirlik istatistiklerini gösterir', () => {
    render(<VideoResourceGrid videos={mockVideos} />);
    
    // Erişilebilir video sayısını kontrol et
    expect(screen.getByText(/2 Erişilebilir/i)).toBeInTheDocument();
    
    // Erişim sorunu olan video sayısını kontrol et
    expect(screen.getByText(/1 Erişim Sorunu/i)).toBeInTheDocument();
    
    // Türkçe video sayısını kontrol et
    expect(screen.getByText(/3 Türkçe/i)).toBeInTheDocument();
  });

  it('video sayısını doğru gösterir', () => {
    render(<VideoResourceGrid videos={mockVideos} />);
    
    expect(screen.getByText('3 video bulundu')).toBeInTheDocument();
  });

  it('filtreleme seçeneklerini gösterir', () => {
    render(<VideoResourceGrid videos={mockVideos} />);
    
    // Zorluk filtresi
    expect(screen.getAllByText('Zorluk')[0]).toBeInTheDocument();
    
    // Süre filtresi
    expect(screen.getAllByText('Süre')[0]).toBeInTheDocument();
  });

  it('enhanced skorları olan videoları destekler', () => {
    const videoWithScores = mockVideos[0];
    render(<VideoResourceGrid videos={[videoWithScores]} />);
    
    // Video kartının render edildiğini kontrol et
    expect(screen.getByText(videoWithScores.title)).toBeInTheDocument();
  });

  it('geriye dönük uyumluluk için eski format videoları destekler', () => {
    const legacyVideo: VideoResponse = {
      video_id: 'legacy-1',
      title: 'Eski Format Video',
      channel: 'Test Channel',
      channel_id: 'channel-legacy',
      duration: 'PT10M',
      view_count: 1000,
      upload_date: '2024-01-01',
      thumbnail: 'https://example.com/thumb.jpg',
      quality_score: 0.7,
      subject: 'matematik',
      difficulty: 'orta',
      exam_type: 'YKS',
      url: 'https://youtube.com/watch?v=legacy'
    };
    
    render(<VideoResourceGrid videos={[legacyVideo]} />);
    
    expect(screen.getByText('Eski Format Video')).toBeInTheDocument();
  });

  it('onVideoPlay callback fonksiyonunu çağırır', async () => {
    const onVideoPlay = vi.fn();
    render(<VideoResourceGrid videos={mockVideos} onVideoPlay={onVideoPlay} />);
    
    // İzle butonunu bul ve tıkla
    const playButtons = screen.getAllByText('İzle');
    playButtons[0].click();
    
    await waitFor(() => {
      expect(onVideoPlay).toHaveBeenCalledWith(mockVideos[0]);
    });
  });
});
