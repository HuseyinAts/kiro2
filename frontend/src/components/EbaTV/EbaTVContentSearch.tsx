/**
 * EBA TV İçerik Arama Bileşeni
 * 
 * EBA TV videolarını arama ve filtreleme için gelişmiş arayüz.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Grid, List, Star, Clock, BookOpen, Users } from 'lucide-react';
import { debounce } from 'lodash';

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

interface SearchFilters {
  query: string;
  grade_level?: string;
  category?: string;
  min_quality: number;
  max_duration?: number;
  accessibility_required: boolean;
}

interface EbaTVContentSearchProps {
  onVideoSelect: (video: EBAVideo) => void;
  onSearchResults?: (results: EBAVideo[]) => void;
}

const CATEGORIES = [
  { value: 'matematik', label: 'Matematik' },
  { value: 'turkce', label: 'Türkçe' },
  { value: 'fen_bilimleri', label: 'Fen Bilimleri' },
  { value: 'sosyal_bilgiler', label: 'Sosyal Bilgiler' },
  { value: 'ingilizce', label: 'İngilizce' },
  { value: 'fizik', label: 'Fizik' },
  { value: 'kimya', label: 'Kimya' },
  { value: 'biyoloji', label: 'Biyoloji' },
  { value: 'tarih', label: 'Tarih' },
  { value: 'cografya', label: 'Coğrafya' }
];

const GRADE_LEVELS = [
  { value: '5', label: '5. Sınıf' },
  { value: '6', label: '6. Sınıf' },
  { value: '7', label: '7. Sınıf' },
  { value: '8', label: '8. Sınıf (LGS)' },
  { value: '9', label: '9. Sınıf' },
  { value: '10', label: '10. Sınıf' },
  { value: '11', label: '11. Sınıf' },
  { value: '12', label: '12. Sınıf (YKS)' }
];

export const EbaTVContentSearch: React.FC<EbaTVContentSearchProps> = ({
  onVideoSelect,
  onSearchResults
}) => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    min_quality: 6.0,
    accessibility_required: false
  });
  
  const [searchResults, setSearchResults] = useState<EBAVideo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'quality' | 'duration' | 'title'>('quality');
  const [searchTime, setSearchTime] = useState<number>(0);

  // Mock search function (gerçek uygulamada API çağrısı yapılacak)
  const searchVideos = async (searchFilters: SearchFilters): Promise<EBAVideo[]> => {
    // Simulated API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock data
    const mockVideos: EBAVideo[] = [
      {
        id: 1,
        title: "8. Sınıf Matematik - Çarpanlar ve Katlar",
        description: "Bu videoda 8. sınıf matematik dersi çarpanlar ve katlar konusunu detaylı olarak işleyeceğiz. EBOB ve EKOK kavramlarını örneklerle açıklayacağız.",
        duration_minutes: 25,
        category: "matematik",
        grade_level: "8",
        difficulty_level: "medium",
        quality_score: 9.25,
        video_url: "https://www.eba.gov.tr/video/matematik-8-sinif-carpanlar-katlar",
        thumbnail_url: "https://via.placeholder.com/320x180?text=Matematik+Video",
        subject_topics: ["Çarpanlar ve Katlar", "EBOB", "EKOK"],
        accessibility_features: ["altyazi", "transkript"],
        curriculum_alignment: { alignment_score: 0.85 }
      },
      {
        id: 2,
        title: "8. Sınıf Türkçe - Okuma Becerileri",
        description: "Okuduğunu anlama ve çıkarım yapma becerileri konusunu işleyeceğiz.",
        duration_minutes: 20,
        category: "turkce",
        grade_level: "8",
        difficulty_level: "medium",
        quality_score: 8.75,
        video_url: "https://www.eba.gov.tr/video/turkce-8-sinif-okuma-becerileri",
        thumbnail_url: "https://via.placeholder.com/320x180?text=Türkçe+Video",
        subject_topics: ["Okuma", "Anlama", "Çıkarım"],
        accessibility_features: ["altyazi"],
        curriculum_alignment: { alignment_score: 0.78 }
      },
      {
        id: 3,
        title: "12. Sınıf Fizik - Elektrik ve Manyetizma",
        description: "Elektrik ve manyetizma konusu YKS fizik hazırlık dersi. Detaylı konu anlatımı ve soru çözümleri.",
        duration_minutes: 40,
        category: "fizik",
        grade_level: "12",
        difficulty_level: "hard",
        quality_score: 9.50,
        video_url: "https://www.eba.gov.tr/video/fizik-12-sinif-elektrik-manyetizma",
        thumbnail_url: "https://via.placeholder.com/320x180?text=Fizik+Video",
        subject_topics: ["Elektrik", "Manyetizma", "YKS Fizik"],
        accessibility_features: ["altyazi", "transkript"],
        curriculum_alignment: { alignment_score: 0.92 }
      }
    ];

    // Filter videos based on search criteria
    return mockVideos.filter(video => {
      const matchesQuery = !searchFilters.query || 
        video.title.toLowerCase().includes(searchFilters.query.toLowerCase()) ||
        video.description.toLowerCase().includes(searchFilters.query.toLowerCase()) ||
        video.subject_topics.some(topic => 
          topic.toLowerCase().includes(searchFilters.query.toLowerCase())
        );

      const matchesGrade = !searchFilters.grade_level || 
        video.grade_level === searchFilters.grade_level;

      const matchesCategory = !searchFilters.category || 
        video.category === searchFilters.category;

      const matchesQuality = video.quality_score >= searchFilters.min_quality;

      const matchesDuration = !searchFilters.max_duration || 
        video.duration_minutes <= searchFilters.max_duration;

      const matchesAccessibility = !searchFilters.accessibility_required || 
        video.accessibility_features.length > 0;

      return matchesQuery && matchesGrade && matchesCategory && 
             matchesQuality && matchesDuration && matchesAccessibility;
    });
  };

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (searchFilters: SearchFilters) => {
      setIsLoading(true);
      const startTime = Date.now();
      
      try {
        const results = await searchVideos(searchFilters);
        const endTime = Date.now();
        
        setSearchResults(results);
        setSearchTime(endTime - startTime);
        onSearchResults?.(results);
      } catch (error) {
        console.error('Arama hatası:', error);
        setSearchResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    [onSearchResults]
  );

  // Effect for search
  useEffect(() => {
    if (filters.query.length >= 2 || filters.category || filters.grade_level) {
      debouncedSearch(filters);
    } else {
      setSearchResults([]);
    }
  }, [filters, debouncedSearch]);

  // Sort results
  const sortedResults = [...searchResults].sort((a, b) => {
    switch (sortBy) {
      case 'quality':
        return b.quality_score - a.quality_score;
      case 'duration':
        return a.duration_minutes - b.duration_minutes;
      case 'title':
        return a.title.localeCompare(b.title, 'tr');
      default:
        return 0;
    }
  });

  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      min_quality: 6.0,
      accessibility_required: false
    });
  };

  const getQualityColor = (score: number) => {
    if (score >= 9) return 'text-green-600';
    if (score >= 7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDifficultyBadge = (level: string) => {
    const colors = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800'
    };
    
    const labels = {
      easy: 'Kolay',
      medium: 'Orta',
      hard: 'Zor'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[level as keyof typeof colors]}`}>
        {labels[level as keyof typeof labels]}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Search Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          EBA TV İçerik Arama
        </h2>
        
        {/* Search Input */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Video ara... (matematik, türkçe, fizik vb.)"
            value={filters.query}
            onChange={(e) => handleFilterChange('query', e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filter Toggle and View Options */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Filter size={16} />
              <span>Filtreler</span>
            </button>
            
            {(filters.category || filters.grade_level || filters.min_quality > 6.0 || filters.accessibility_required) && (
              <button
                onClick={clearFilters}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Filtreleri Temizle
              </button>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {/* Sort Options */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="quality">Kaliteye Göre</option>
              <option value="duration">Süreye Göre</option>
              <option value="title">Alfabetik</option>
            </select>

            {/* View Mode */}
            <div className="flex border border-gray-300 rounded-lg">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
              >
                <Grid size={16} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'text-gray-600'}`}
              >
                <List size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Grade Level Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sınıf Seviyesi
              </label>
              <select
                value={filters.grade_level || ''}
                onChange={(e) => handleFilterChange('grade_level', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Tüm Sınıflar</option>
                {GRADE_LEVELS.map(grade => (
                  <option key={grade.value} value={grade.value}>
                    {grade.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Kategori
              </label>
              <select
                value={filters.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">Tüm Kategoriler</option>
                {CATEGORIES.map(category => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Quality Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Kalite: {filters.min_quality.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="10"
                step="0.5"
                value={filters.min_quality}
                onChange={(e) => handleFilterChange('min_quality', Number(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Accessibility Filter */}
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.accessibility_required}
                  onChange={(e) => handleFilterChange('accessibility_required', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="text-sm font-medium text-gray-700">
                  Erişilebilirlik Gerekli
                </span>
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      <div className="mb-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-gray-600">Aranıyor...</span>
          </div>
        ) : (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              {searchResults.length} video bulundu
              {searchTime > 0 && ` (${searchTime}ms)`}
            </span>
          </div>
        )}
      </div>

      {/* Results Grid/List */}
      {!isLoading && searchResults.length > 0 && (
        <div className={viewMode === 'grid' 
          ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
          : 'space-y-4'
        }>
          {sortedResults.map((video) => (
            <div
              key={video.id}
              onClick={() => onVideoSelect(video)}
              className={`bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer ${
                viewMode === 'list' ? 'flex' : ''
              }`}
            >
              {/* Thumbnail */}
              <div className={viewMode === 'list' ? 'w-48 flex-shrink-0' : ''}>
                <img
                  src={video.thumbnail_url || 'https://via.placeholder.com/320x180?text=EBA+TV'}
                  alt={video.title}
                  className="w-full h-48 object-cover"
                />
              </div>

              {/* Content */}
              <div className="p-4 flex-1">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900 line-clamp-2">
                    {video.title}
                  </h3>
                  <div className="flex items-center space-x-1 ml-2">
                    <Star className={`w-4 h-4 ${getQualityColor(video.quality_score)}`} />
                    <span className={`text-sm font-medium ${getQualityColor(video.quality_score)}`}>
                      {video.quality_score.toFixed(1)}
                    </span>
                  </div>
                </div>

                <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                  {video.description}
                </p>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <Clock size={14} className="text-gray-400" />
                      <span className="text-gray-600">{video.duration_minutes} dk</span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <BookOpen size={14} className="text-gray-400" />
                      <span className="text-gray-600">{video.grade_level}. Sınıf</span>
                    </div>

                    {video.accessibility_features.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <Users size={14} className="text-green-500" />
                        <span className="text-green-600">Erişilebilir</span>
                      </div>
                    )}
                  </div>

                  {getDifficultyBadge(video.difficulty_level)}
                </div>

                {/* Subject Topics */}
                {video.subject_topics.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {video.subject_topics.slice(0, 3).map((topic, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                    {video.subject_topics.length > 3 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        +{video.subject_topics.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {!isLoading && searchResults.length === 0 && filters.query && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-2">
            <Search size={48} className="mx-auto" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Sonuç bulunamadı
          </h3>
          <p className="text-gray-600">
            Arama kriterlerinizi değiştirmeyi deneyin.
          </p>
        </div>
      )}
    </div>
  );
};