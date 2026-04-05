/**
 * EBA TV Dashboard Bileşeni
 *
 * EBA TV içeriklerini yönetmek için ana dashboard.
 */

import { Play, TrendingUp, BookOpen, Clock, Star } from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { EbaTVContentSearch } from './EbaTVContentSearch';
import { EbaTVRecommendations } from './EbaTVRecommendations';
import { EbaTVVideoPlayer } from './EbaTVVideoPlayer';

interface EBAVideo {
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
}

interface StudentProfile {
  id: string;
  name: string;
  grade_level: string;
  weak_subjects: string[];
  learning_style: string;
  performance_data?: {
    average_score: number;
    strong_topics: string[];
    weak_topics: string[];
  };
}

interface EBAStatistics {
  total_videos: number;
  categories: Record<string, {
    video_count: number;
    avg_quality: number;
    avg_duration: number;
  }>;
  quality_distribution: {
    high: number;
    medium: number;
    low: number;
  };
}

export const EbaTVDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'search' | 'recommendations' | 'player'>('overview');
  const [selectedVideo, setSelectedVideo] = useState<EBAVideo | null>(null);
  const [statistics, setStatistics] = useState<EBAStatistics | null>(null);
  const [recentVideos, setRecentVideos] = useState<EBAVideo[]>([]);
  const [popularVideos, setPopularVideos] = useState<EBAVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Mock student profile
  const studentProfile: StudentProfile = {
    id: 'student_123',
    name: 'Ahmet Yılmaz',
    grade_level: '8',
    weak_subjects: ['matematik', 'fen_bilimleri'],
    learning_style: 'visual',
    performance_data: {
      average_score: 75,
      strong_topics: ['Türkçe', 'Sosyal Bilgiler'],
      weak_topics: ['Matematik', 'Fen Bilimleri'],
    },
  };

  // Mock data loading
  useEffect(() => {
    const loadDashboardData = async () => {
      setIsLoading(true);

      // Simulate API calls
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock statistics
      setStatistics({
        total_videos: 1250,
        categories: {
          matematik: { video_count: 320, avg_quality: 8.5, avg_duration: 22 },
          turkce: { video_count: 280, avg_quality: 8.2, avg_duration: 18 },
          fen_bilimleri: { video_count: 250, avg_quality: 8.7, avg_duration: 25 },
          sosyal_bilgiler: { video_count: 200, avg_quality: 8.1, avg_duration: 20 },
          fizik: { video_count: 100, avg_quality: 8.9, avg_duration: 30 },
          kimya: { video_count: 100, avg_quality: 8.6, avg_duration: 28 },
        },
        quality_distribution: {
          high: 850,
          medium: 320,
          low: 80,
        },
      });

      // Mock recent and popular videos
      const mockVideos: EBAVideo[] = [
        {
          id: 1,
          title: '8. Sınıf Matematik - Çarpanlar ve Katlar',
          description: 'Bu videoda 8. sınıf matematik dersi çarpanlar ve katlar konusunu detaylı olarak işleyeceğiz.',
          duration_minutes: 25,
          category: 'matematik',
          grade_level: '8',
          difficulty_level: 'medium',
          quality_score: 9.25,
          video_url: 'https://www.eba.gov.tr/video/matematik-8-sinif-carpanlar-katlar',
          thumbnail_url: 'https://via.placeholder.com/320x180?text=Matematik+Video',
          subject_topics: ['Çarpanlar ve Katlar', 'EBOB', 'EKOK'],
          accessibility_features: ['altyazi', 'transkript'],
          curriculum_alignment: { alignment_score: 0.85 },
        },
        {
          id: 2,
          title: '8. Sınıf Türkçe - Okuma Becerileri',
          description: 'Okuduğunu anlama ve çıkarım yapma becerileri konusunu işleyeceğiz.',
          duration_minutes: 20,
          category: 'turkce',
          grade_level: '8',
          difficulty_level: 'medium',
          quality_score: 8.75,
          video_url: 'https://www.eba.gov.tr/video/turkce-8-sinif-okuma-becerileri',
          thumbnail_url: 'https://via.placeholder.com/320x180?text=Türkçe+Video',
          subject_topics: ['Okuma', 'Anlama', 'Çıkarım'],
          accessibility_features: ['altyazi'],
          curriculum_alignment: { alignment_score: 0.78 },
        },
      ];

      setRecentVideos(mockVideos);
      setPopularVideos(mockVideos);
      setIsLoading(false);
    };

    loadDashboardData();
  }, []);

  const handleVideoSelect = (video: EBAVideo) => {
    setSelectedVideo(video);
    setActiveTab('player');
  };

  const handleVideoProgress = (progress: number) => {
  };

  const handleVideoComplete = () => {
    // Video tamamlandığında yapılacak işlemler
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      matematik: 'Matematik',
      turkce: 'Türkçe',
      fen_bilimleri: 'Fen Bilimleri',
      sosyal_bilgiler: 'Sosyal Bilgiler',
      fizik: 'Fizik',
      kimya: 'Kimya',
      biyoloji: 'Biyoloji',
    };
    return labels[category] || category;
  };

  const getQualityColor = (score: number) => {
    if (score >= 9) {return 'text-green-600';}
    if (score >= 7) {return 'text-yellow-600';}
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">EBA TV Dashboard Yükleniyor...</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Play className="text-red-600" size={32} />
                <h1 className="text-2xl font-bold text-gray-900">EBA TV</h1>
              </div>

              <div className="hidden md:flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'overview'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Genel Bakış
                </button>
                <button
                  onClick={() => setActiveTab('search')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'search'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Arama
                </button>
                <button
                  onClick={() => setActiveTab('recommendations')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'recommendations'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Öneriler
                </button>
                {selectedVideo && (
                  <button
                    onClick={() => setActiveTab('player')}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === 'player'
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Video Oynatıcı
                  </button>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Hoş geldin, <span className="font-medium">{studentProfile.name}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Play className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Toplam Video</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statistics?.total_videos.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BookOpen className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Kategori</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statistics ? Object.keys(statistics.categories).length : 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Star className="h-8 w-8 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Yüksek Kalite</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {statistics?.quality_distribution.high}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Sınıf Seviyesi</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {studentProfile.grade_level}. Sınıf
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Overview */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Kategori Dağılımı</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {statistics && Object.entries(statistics.categories).map(([category, data]) => (
                    <div key={category} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">
                        {getCategoryLabel(category)}
                      </h4>
                      <div className="space-y-1 text-sm text-gray-600">
                        <div className="flex justify-between">
                          <span>Video Sayısı:</span>
                          <span className="font-medium">{data.video_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Ortalama Kalite:</span>
                          <span className={`font-medium ${getQualityColor(data.avg_quality)}`}>
                            {data.avg_quality.toFixed(1)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Ortalama Süre:</span>
                          <span className="font-medium">{data.avg_duration} dk</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent and Popular Videos */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Videos */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Son Eklenen Videolar</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {recentVideos.map((video) => (
                      <div
                        key={video.id}
                        onClick={() => handleVideoSelect(video)}
                        className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                      >
                        <img
                          src={video.thumbnail_url || 'https://via.placeholder.com/80x60?text=EBA'}
                          alt={video.title}
                          className="w-20 h-15 object-cover rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {video.title}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                            <Clock size={12} />
                            <span>{video.duration_minutes} dk</span>
                            <Star size={12} className={getQualityColor(video.quality_score)} />
                            <span className={getQualityColor(video.quality_score)}>
                              {video.quality_score.toFixed(1)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Popular Videos */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Popüler Videolar</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {popularVideos.map((video) => (
                      <div
                        key={video.id}
                        onClick={() => handleVideoSelect(video)}
                        className="flex items-center space-x-4 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                      >
                        <img
                          src={video.thumbnail_url || 'https://via.placeholder.com/80x60?text=EBA'}
                          alt={video.title}
                          className="w-20 h-15 object-cover rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {video.title}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                            <Clock size={12} />
                            <span>{video.duration_minutes} dk</span>
                            <Star size={12} className={getQualityColor(video.quality_score)} />
                            <span className={getQualityColor(video.quality_score)}>
                              {video.quality_score.toFixed(1)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <EbaTVContentSearch
            onVideoSelect={handleVideoSelect}
            onSearchResults={(results) => console.log('Search results:', results)}
          />
        )}

        {activeTab === 'recommendations' && (
          <EbaTVRecommendations
            studentProfile={studentProfile}
            onVideoSelect={handleVideoSelect}
            maxRecommendations={12}
          />
        )}

        {activeTab === 'player' && selectedVideo && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedVideo.title}
              </h2>
              <p className="text-gray-600">
                {selectedVideo.description}
              </p>
            </div>

            <EbaTVVideoPlayer
              videoUrl={selectedVideo.video_url}
              title={selectedVideo.title}
              duration={selectedVideo.duration_minutes}
              thumbnail={selectedVideo.thumbnail_url}
              subtitles={selectedVideo.accessibility_features.includes('altyazi')}
              onProgress={handleVideoProgress}
              onComplete={handleVideoComplete}
            />

            {/* Video Info */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Video Bilgileri</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Kategori:</span>
                    <span className="font-medium">{getCategoryLabel(selectedVideo.category)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sınıf Seviyesi:</span>
                    <span className="font-medium">{selectedVideo.grade_level}. Sınıf</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Zorluk:</span>
                    <span className="font-medium capitalize">{selectedVideo.difficulty_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Kalite Skoru:</span>
                    <span className={`font-medium ${getQualityColor(selectedVideo.quality_score)}`}>
                      {selectedVideo.quality_score.toFixed(1)}/10
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Konu Başlıkları</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedVideo.subject_topics.map((topic, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                    >
                      {topic}
                    </span>
                  ))}
                </div>

                {selectedVideo.accessibility_features.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Erişilebilirlik:</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedVideo.accessibility_features.map((feature, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};