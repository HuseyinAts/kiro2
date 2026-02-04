/**
 * Alternatif Çözümler Görüntüleyici - Task 73.1-73.2
 * REQ-13.1: Alternatif çözüm yolları
 *
 * Features:
 * - Multiple solution methods display
 * - Solution category badges (klasik, hızlı, görsel, mantıksal, formül)
 * - Difficulty and time estimates
 * - Step-by-step breakdown for each solution
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Clock,
  Zap,
  TrendingUp,
  Award,
  Eye,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
  Lightbulb,
  CheckCircle
} from 'lucide-react';

interface SolutionStep {
  step_number: number;
  description: string;
  formula?: string;
  explanation?: string;
}

interface AlternativeSolution {
  id: string;
  title: string;
  category: 'klasik' | 'hızlı' | 'görsel' | 'mantıksal' | 'formül';
  difficulty: 'kolay' | 'orta' | 'zor';
  estimated_time_seconds: number;
  steps: SolutionStep[];
  tips?: string[];
  prerequisites?: string[];
  advantages?: string[];
  disadvantages?: string[];
  video_url?: string;
  created_by_type: 'teacher' | 'student' | 'ai';
  votes: {
    upvotes: number;
    downvotes: number;
  };
  views: number;
  is_fastest?: boolean;
  is_recommended?: boolean;
}

interface AlternativeSolutionsViewerProps {
  questionId: string;
  onSolutionSelect?: (solutionId: string) => void;
}

const AlternativeSolutionsViewer: React.FC<AlternativeSolutionsViewerProps> = ({
  questionId,
  onSolutionSelect
}) => {
  const [solutions, setSolutions] = useState<AlternativeSolution[]>([]);
  const [selectedSolution, setSelectedSolution] = useState<AlternativeSolution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'fastest' | 'popular' | 'difficulty'>('popular');

  // Load alternative solutions
  useEffect(() => {
    loadSolutions();
  }, [questionId]);

  const loadSolutions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/questions/${questionId}/solutions`);

      if (response.data.success) {
        setSolutions(response.data.data.solutions);
        // Auto-select first solution
        if (response.data.data.solutions.length > 0) {
          setSelectedSolution(response.data.data.solutions[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load solutions:', err);
      setError('Çözümler yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort solutions
  const getFilteredAndSortedSolutions = () => {
    let filtered = solutions;

    // Filter by category
    if (filterCategory !== 'all') {
      filtered = filtered.filter(s => s.category === filterCategory);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'fastest':
          return a.estimated_time_seconds - b.estimated_time_seconds;
        case 'popular':
          return (b.votes.upvotes - b.votes.downvotes) - (a.votes.upvotes - a.votes.downvotes);
        case 'difficulty':
          const difficultyOrder = { 'kolay': 1, 'orta': 2, 'zor': 3 };
          return difficultyOrder[a.difficulty] - difficultyOrder[b.difficulty];
        default:
          return 0;
      }
    });

    return filtered;
  };

  const handleSolutionClick = (solution: AlternativeSolution) => {
    setSelectedSolution(solution);
    if (onSolutionSelect) {
      onSolutionSelect(solution.id);
    }
  };

  const handleVote = async (solutionId: string, voteType: 'upvote' | 'downvote') => {
    try {
      await axios.post(`/api/v1/questions/${questionId}/solutions/${solutionId}/vote`, {
        vote_type: voteType
      });

      // Refresh solutions
      await loadSolutions();
    } catch (err) {
      console.error('Vote failed:', err);
    }
  };

  // Category colors and icons
  const getCategoryStyle = (category: string) => {
    const styles = {
      klasik: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300', icon: '📘' },
      hızlı: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', icon: '⚡' },
      görsel: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300', icon: '🎨' },
      mantıksal: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', icon: '🧠' },
      formül: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: '∑' }
    };
    return styles[category as keyof typeof styles] || styles.klasik;
  };

  const getDifficultyBadge = (difficulty: string) => {
    const badges = {
      kolay: { bg: 'bg-green-500', text: 'Kolay' },
      orta: { bg: 'bg-yellow-500', text: 'Orta' },
      zor: { bg: 'bg-red-500', text: 'Zor' }
    };
    return badges[difficulty as keyof typeof badges] || badges.orta;
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}d ${secs}s`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-xl">Çözümler yükleniyor...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  const filteredSolutions = getFilteredAndSortedSolutions();

  return (
    <div className="alternative-solutions-viewer">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Alternatif Çözüm Yolları</h2>
        <p className="text-gray-600">
          Bu soru için {solutions.length} farklı çözüm yöntemi mevcut. Her biri farklı yaklaşım ve hız avantajları sunar.
        </p>
      </div>

      {/* Filters and Sort */}
      <div className="mb-6 flex flex-wrap gap-4 items-center">
        {/* Category Filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Kategori:</span>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">Tümü</option>
            <option value="klasik">📘 Klasik</option>
            <option value="hızlı">⚡ Hızlı</option>
            <option value="görsel">🎨 Görsel</option>
            <option value="mantıksal">🧠 Mantıksal</option>
            <option value="formül">∑ Formül</option>
          </select>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Sırala:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="popular">Popülerlik</option>
            <option value="fastest">En Hızlı</option>
            <option value="difficulty">Zorluk</option>
          </select>
        </div>

        <div className="ml-auto text-sm text-gray-500">
          {filteredSolutions.length} çözüm gösteriliyor
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Solution List (Left Sidebar) */}
        <div className="lg:col-span-1 space-y-3">
          {filteredSolutions.map((solution) => {
            const categoryStyle = getCategoryStyle(solution.category);
            const difficultyBadge = getDifficultyBadge(solution.difficulty);
            const isSelected = selectedSolution?.id === solution.id;

            return (
              <button
                key={solution.id}
                onClick={() => handleSolutionClick(solution)}
                className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50 shadow-lg'
                    : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md'
                }`}
              >
                {/* Category Badge */}
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs px-2 py-1 rounded ${categoryStyle.bg} ${categoryStyle.text} border ${categoryStyle.border}`}>
                    {categoryStyle.icon} {solution.category.charAt(0).toUpperCase() + solution.category.slice(1)}
                  </span>
                  {solution.is_fastest && (
                    <span className="text-xs px-2 py-1 rounded bg-green-500 text-white flex items-center gap-1">
                      <Zap size={12} /> En Hızlı
                    </span>
                  )}
                </div>

                {/* Title */}
                <h3 className="font-bold text-sm mb-2">{solution.title}</h3>

                {/* Stats */}
                <div className="flex items-center gap-3 text-xs text-gray-600 mb-2">
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {formatTime(solution.estimated_time_seconds)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye size={12} />
                    {solution.views}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded ${difficultyBadge.bg} text-white`}>
                    {difficultyBadge.text}
                  </span>
                </div>

                {/* Votes */}
                <div className="flex items-center gap-2 text-xs">
                  <span className="flex items-center gap-1 text-green-600">
                    <ThumbsUp size={12} />
                    {solution.votes.upvotes}
                  </span>
                  <span className="flex items-center gap-1 text-red-600">
                    <ThumbsDown size={12} />
                    {solution.votes.downvotes}
                  </span>
                </div>

                {solution.is_recommended && (
                  <div className="mt-2 text-xs text-blue-600 flex items-center gap-1">
                    <Award size={12} />
                    Önerilen
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Selected Solution Detail (Main Content) */}
        <div className="lg:col-span-2">
          {selectedSolution ? (
            <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
              {/* Header */}
              <div className="mb-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h2 className="text-2xl font-bold mb-2">{selectedSolution.title}</h2>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-sm px-3 py-1 rounded ${getCategoryStyle(selectedSolution.category).bg} ${getCategoryStyle(selectedSolution.category).text}`}>
                        {getCategoryStyle(selectedSolution.category).icon} {selectedSolution.category}
                      </span>
                      <span className={`text-sm px-3 py-1 rounded ${getDifficultyBadge(selectedSolution.difficulty).bg} text-white`}>
                        {getDifficultyBadge(selectedSolution.difficulty).text}
                      </span>
                      <span className="text-sm px-3 py-1 rounded bg-gray-200 flex items-center gap-1">
                        <Clock size={14} />
                        {formatTime(selectedSolution.estimated_time_seconds)}
                      </span>
                    </div>
                  </div>

                  {/* Vote Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleVote(selectedSolution.id, 'upvote')}
                      className="p-2 rounded border hover:bg-green-50 hover:border-green-500 transition-colors"
                    >
                      <ThumbsUp size={18} className="text-green-600" />
                    </button>
                    <button
                      onClick={() => handleVote(selectedSolution.id, 'downvote')}
                      className="p-2 rounded border hover:bg-red-50 hover:border-red-500 transition-colors"
                    >
                      <ThumbsDown size={18} className="text-red-600" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Advantages & Disadvantages */}
              {(selectedSolution.advantages || selectedSolution.disadvantages) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {selectedSolution.advantages && selectedSolution.advantages.length > 0 && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <h4 className="font-semibold text-green-800 mb-2 flex items-center gap-1">
                        <CheckCircle size={16} />
                        Avantajları
                      </h4>
                      <ul className="text-sm space-y-1">
                        {selectedSolution.advantages.map((adv, idx) => (
                          <li key={idx} className="text-green-700">• {adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedSolution.disadvantages && selectedSolution.disadvantages.length > 0 && (
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <h4 className="font-semibold text-red-800 mb-2">Dezavantajları</h4>
                      <ul className="text-sm space-y-1">
                        {selectedSolution.disadvantages.map((dis, idx) => (
                          <li key={idx} className="text-red-700">• {dis}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Prerequisites */}
              {selectedSolution.prerequisites && selectedSolution.prerequisites.length > 0 && (
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 mb-6">
                  <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-1">
                    <BookOpen size={16} />
                    Ön Gereksinimler
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedSolution.prerequisites.map((req, idx) => (
                      <span key={idx} className="text-xs px-3 py-1 bg-blue-200 text-blue-800 rounded-full">
                        {req}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Solution Steps */}
              <div className="mb-6">
                <h3 className="text-lg font-bold mb-4">Çözüm Adımları</h3>
                <div className="space-y-4">
                  {selectedSolution.steps.map((step) => (
                    <div key={step.step_number} className="flex gap-4">
                      {/* Step Number */}
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
                        {step.step_number}
                      </div>

                      {/* Step Content */}
                      <div className="flex-1">
                        <p className="text-gray-800 mb-2">{step.description}</p>
                        {step.formula && (
                          <div className="p-3 bg-gray-50 rounded border border-gray-200 font-mono text-sm">
                            {step.formula}
                          </div>
                        )}
                        {step.explanation && (
                          <p className="text-sm text-gray-600 mt-2 italic">
                            💡 {step.explanation}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tips */}
              {selectedSolution.tips && selectedSolution.tips.length > 0 && (
                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <h4 className="font-semibold text-yellow-800 mb-2 flex items-center gap-1">
                    <Lightbulb size={16} />
                    İpuçları
                  </h4>
                  <ul className="text-sm space-y-1">
                    {selectedSolution.tips.map((tip, idx) => (
                      <li key={idx} className="text-yellow-700">💡 {tip}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Video */}
              {selectedSolution.video_url && (
                <div className="mt-6">
                  <h4 className="font-semibold mb-2">Video Çözüm</h4>
                  <iframe
                    src={selectedSolution.video_url}
                    className="w-full h-64 rounded-lg border"
                    title="Video çözüm"
                    allowFullScreen
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
              <p className="text-gray-500">Bir çözüm seçin</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlternativeSolutionsViewer;
