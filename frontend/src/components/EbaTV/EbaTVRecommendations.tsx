/**
 * EBA TV Öneriler Bileşeni
 *
 * Öğrenci profiline göre kişiselleştirilmiş EBA TV video önerileri.
 */

import { Star, BookOpen, TrendingUp, Target, Brain, Users } from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

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

interface RecommendationReason {
  type: 'weak_subject' | 'learning_style' | 'quality' | 'curriculum' | 'difficulty';
  description: string;
  icon: React.ReactNode;
  color: string;
}

interface StudentProfile {
  id: string;
  grade_level: string;
  weak_subjects: string[];
  learning_style: string;
  performance_data?: {
    average_score: number;
    strong_topics: string[];
    weak_topics: string[];
  };
}

interface EbaTVRecommendationsProps {
  studentProfile: StudentProfile;
  onVideoSelect: (video: EBAVideo) => void;
  maxRecommendations?: number;
}

export const EbaTVRecommendations: React.FC<EbaTVRecommendationsProps> = ({
  studentProfile,
  onVideoSelect,
  maxRecommendations = 10,
}) => {
  const [recommendations, setRecommendations] = useState<EBAVideo[]>([]);
  const [recommendationReasons, setRecommendationReasons] = useState<Record<string, RecommendationReason[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [personalizationScore, setPersonalizationScore] = useState<number>(0);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock recommendation service
  const getRecommendations = async (profile: StudentProfile): Promise<{
    recommendations: EBAVideo[];
    reasons: Record<string, RecommendationReason[]>;
    personalizationScore: number;
  }> => {
    // Simulated API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Mock recommendations based on profile
    const mockRecommendations: EBAVideo[] = [
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
      {
        id: 3,
        title: '8. Sınıf Fen Bilimleri - Madde ve Değişim',
        description: 'Maddenin halleri ve fiziksel-kimyasal değişimler konusunu örneklerle açıklıyoruz.',
        duration_minutes: 30,
        category: 'fen_bilimleri',
        grade_level: '8',
        difficulty_level: 'medium',
        quality_score: 8.90,
        video_url: 'https://www.eba.gov.tr/video/fen-8-sinif-madde-degisim',
        thumbnail_url: 'https://via.placeholder.com/320x180?text=Fen+Video',
        subject_topics: ['Madde', 'Fiziksel Değişim', 'Kimyasal Değişim'],
        accessibility_features: ['altyazi', 'transkript'],
        curriculum_alignment: { alignment_score: 0.82 },
      },
    ];

    // Generate reasons for each recommendation
    const reasons: Record<string, RecommendationReason[]> = {};

    mockRecommendations.forEach(video => {
      const videoReasons: RecommendationReason[] = [];

      // Weak subject reason
      if (profile.weak_subjects.includes(video.category)) {
        videoReasons.push({
          type: 'weak_subject',
          description: `Zayıf konu: ${video.category}`,
          icon: <Target size={16} />,
          color: 'text-red-600',
        });
      }

      // Learning style reason
      if (profile.learning_style === 'visual' && video.duration_minutes <= 25) {
        videoReasons.push({
          type: 'learning_style',
          description: 'Görsel öğrenme stiline uygun',
          icon: <Brain size={16} />,
          color: 'text-purple-600',
        });
      }

      // Quality reason
      if (video.quality_score >= 9.0) {
        videoReasons.push({
          type: 'quality',
          description: 'Yüksek kalite skoru',
          icon: <Star size={16} />,
          color: 'text-yellow-600',
        });
      }

      // Curriculum alignment reason
      if (video.curriculum_alignment.alignment_score >= 0.8) {
        videoReasons.push({
          type: 'curriculum',
          description: 'Yüksek müfredat uyumu',
          icon: <BookOpen size={16} />,
          color: 'text-green-600',
        });
      }

      reasons[video.id.toString()] = videoReasons;
    });

    // Calculate personalization score
    const totalScore = mockRecommendations.reduce((sum, video) => {
      return sum + video.quality_score + (video.curriculum_alignment.alignment_score * 10);
    }, 0);

    const personalizationScore = totalScore / (mockRecommendations.length * 2);

    return {
      recommendations: mockRecommendations,
      reasons,
      personalizationScore,
    };
  };

  // Load recommendations
  useEffect(() => {
    const loadRecommendations = async () => {
      setIsLoading(true);
      try {
        const result = await getRecommendations(studentProfile);
        setRecommendations(result.recommendations);
        setRecommendationReasons(result.reasons);
        setPersonalizationScore(result.personalizationScore);
      } catch (error) {
        console.error('Öneriler yüklenirken hata:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecommendations();
  }, [studentProfile]);

  // Filter recommendations by category
  const filteredRecommendations = selectedCategory === 'all'
    ? recommendations
    : recommendations.filter(video => video.category === selectedCategory);

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(recommendations.map(video => video.category)))];

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      all: 'Tümü',
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

  const getDifficultyBadge = (level: string) => {
    const colors = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800',
    };

    const labels = {
      easy: 'Kolay',
      medium: 'Orta',
      hard: 'Zor',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[level as keyof typeof colors]}`}>
        {labels[level as keyof typeof labels]}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Kişiselleştirilmiş öneriler hazırlanıyor...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Sizin İçin Önerilen Videolar
          </h2>

          {/* Personalization Score */}
          <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-lg">
            <TrendingUp className="text-blue-600" size={20} />
            <span className="text-sm font-medium text-blue-900">
              Kişiselleştirme: {personalizationScore.toFixed(1)}/10
            </span>
          </div>
        </div>

        {/* Student Profile Summary */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Sınıf:</span>
              <span className="ml-2 text-gray-900">{studentProfile.grade_level}. Sınıf</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Öğrenme Stili:</span>
              <span className="ml-2 text-gray-900 capitalize">{studentProfile.learning_style}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Zayıf Konular:</span>
              <span className="ml-2 text-gray-900">
                {studentProfile.weak_subjects.map(subject => getCategoryLabel(subject)).join(', ')}
              </span>
            </div>
          </div>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {getCategoryLabel(category)}
              {category !== 'all' && (
                <span className="ml-1 text-xs">
                  ({recommendations.filter(v => v.category === category).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Recommendations Grid */}
      {filteredRecommendations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRecommendations.slice(0, maxRecommendations).map((video) => (
            <div
              key={video.id}
              onClick={() => onVideoSelect(video)}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
            >
              {/* Thumbnail */}
              <div className="relative">
                <img
                  src={video.thumbnail_url || 'https://via.placeholder.com/320x180?text=EBA+TV'}
                  alt={video.title}
                  className="w-full h-48 object-cover"
                />

                {/* Quality Badge */}
                <div className="absolute top-2 right-2 bg-black bg-opacity-75 text-white px-2 py-1 rounded-lg text-sm flex items-center space-x-1">
                  <Star className={getQualityColor(video.quality_score)} size={14} />
                  <span>{video.quality_score.toFixed(1)}</span>
                </div>

                {/* Duration */}
                <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white px-2 py-1 rounded text-sm">
                  {video.duration_minutes} dk
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                  {video.title}
                </h3>

                <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                  {video.description}
                </p>

                {/* Video Info */}
                <div className="flex items-center justify-between text-sm mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-1">
                      <BookOpen size={14} className="text-gray-400" />
                      <span className="text-gray-600">{video.grade_level}. Sınıf</span>
                    </div>

                    {video.accessibility_features.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <Users size={14} className="text-green-500" />
                        <span className="text-green-600 text-xs">Erişilebilir</span>
                      </div>
                    )}
                  </div>

                  {getDifficultyBadge(video.difficulty_level)}
                </div>

                {/* Recommendation Reasons */}
                <div className="space-y-2">
                  <div className="text-xs font-medium text-gray-700 mb-1">
                    Neden öneriliyor:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {recommendationReasons[video.id.toString()]?.map((reason, index) => (
                      <div
                        key={index}
                        className={`flex items-center space-x-1 px-2 py-1 bg-gray-100 rounded-full text-xs ${reason.color}`}
                      >
                        {reason.icon}
                        <span>{reason.description}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Subject Topics */}
                {video.subject_topics.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {video.subject_topics.slice(0, 2).map((topic, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                    {video.subject_topics.length > 2 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        +{video.subject_topics.length - 2}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <BookOpen size={48} className="mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Bu kategoride öneri bulunamadı
          </h3>
          <p className="text-gray-600">
            Diğer kategorileri kontrol edin veya profilinizi güncelleyin.
          </p>
        </div>
      )}

      {/* Load More Button */}
      {filteredRecommendations.length > maxRecommendations && (
        <div className="text-center mt-6">
          <button className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
            Daha Fazla Öneri Göster
          </button>
        </div>
      )}
    </div>
  );
};