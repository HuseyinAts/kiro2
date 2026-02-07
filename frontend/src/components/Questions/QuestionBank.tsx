/**
 * QuestionBank Component
 * 2,010 soruyu görüntülemek için ana component
 *
 * Features:
 * - Soru listesi görüntüleme (turkiye_sinav_db)
 * - Filtreleme (Sınav tipi, Konu, Zorluk)
 * - Arama
 * - Sayfalama
 * - Responsive design
 * - MathJax desteği
 *
 * Updated: 2026-01-13 - API endpoint ve response mapping düzeltildi
 */

import * as React from 'react';
import {  useState, useEffect, useMemo  } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import config from '@/config';
import { initMathJax, typesetMath } from '@/config/mathjax.config';

// Backend API Response tipi (turkiye_sinav_db şeması)
interface APIQuestion {
  question_id: string;
  stem: string;
  options: Record<string, string>;
  correct_answer: string;
  explanation?: string;
  exam_type: string;
  subject: string;
  topic: string;
  difficulty: string;
  irt_discrimination?: number;
  irt_difficulty?: number;
  irt_guessing?: number;
  created_at?: string;
}

// Frontend Question tipi
interface Question {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  option_e: string;
  correct_answer: string;
  explanation: string;
  exam_type: string;
  subject: string;
  topic: string;
  difficulty: number;
  discrimination: number;
  guessing: number;
  created_at: string;
}

interface QuestionBankProps {
  apiUrl?: string;
}

// Zorluk string'ini sayıya çevir (turkiye_sinav_db: "kolay", "orta", "zor")
function parseDifficulty(diff: string | undefined): number {
  if (!diff) {return 0.5;}
  const normalized = diff.toLowerCase();
  if (normalized === 'kolay') {return 0.2;}
  if (normalized === 'orta') {return 0.5;}
  if (normalized === 'zor') {return 0.75;}
  if (normalized === 'çok zor') {return 0.9;}
  return 0.5;
}

// API response'u frontend tipine dönüştür
function mapAPIQuestion(q: APIQuestion): Question {
  return {
    id: q.question_id,
    question_text: q.stem || '',
    option_a: q.options?.A || '',
    option_b: q.options?.B || '',
    option_c: q.options?.C || '',
    option_d: q.options?.D || '',
    option_e: q.options?.E || '',
    correct_answer: q.correct_answer || '',
    explanation: q.explanation || '',
    exam_type: q.exam_type || '',
    subject: q.subject || '',
    topic: q.topic || '',
    difficulty: parseDifficulty(q.difficulty),
    discrimination: q.irt_discrimination || 1.0,
    guessing: q.irt_guessing || 0.25,
    created_at: q.created_at || '',
  };
}

export const QuestionBank: React.FC<QuestionBankProps> = ({
  apiUrl = `${config.api.baseURL}/soru-bankasi/sorular`,
}) => {
  // State
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [examTypeFilter, setExamTypeFilter] = useState<string>('all');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const questionsPerPage = 10;

  // Initialize MathJax on mount
  useEffect(() => {
    initMathJax();
  }, []);

  // Fetch questions with response mapping
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true);
        // Server-side pagination için limit/offset ekle
        const url = new URL(apiUrl, window.location.origin);
        url.searchParams.set('limit', '500'); // İlk yüklemede 500 soru

        const response = await fetch(url.toString());

        if (!response.ok) {
          throw new Error(`Sorular yüklenemedi (HTTP ${response.status})`);
        }

        const data = await response.json();

        // API response formatını kontrol et ve map et
        const rawQuestions: APIQuestion[] = Array.isArray(data)
          ? data
          : data.questions || data.data || [];

        // turkiye_sinav_db şemasından frontend şemasına map et
        const mappedQuestions = rawQuestions.map(mapAPIQuestion);

        setQuestions(mappedQuestions);
        setError(null);

        console.log(`✅ ${mappedQuestions.length} soru yüklendi`);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Bir hata oluştu';
        setError(errorMessage);
        console.error('❌ Error fetching questions:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuestions();
  }, [apiUrl]);

  // MathJax typeset after questions load
  useEffect(() => {
    if (questions.length > 0) {
      // Slight delay to ensure DOM is updated
      const timer = setTimeout(() => {
        typesetMath();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [questions, currentPage]);

  // Filter questions
  const filteredQuestions = useMemo(() => {
    return questions.filter(q => {
      // Search filter
      const matchesSearch = searchQuery === '' ||
        q.question_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.topic.toLowerCase().includes(searchQuery.toLowerCase());

      // Exam type filter
      const matchesExamType = examTypeFilter === 'all' || q.exam_type === examTypeFilter;

      // Subject filter
      const matchesSubject = subjectFilter === 'all' || q.subject === subjectFilter;

      // Difficulty filter
      const matchesDifficulty = difficultyFilter === 'all' ||
        getDifficultyLevel(q.difficulty) === difficultyFilter;

      return matchesSearch && matchesExamType && matchesSubject && matchesDifficulty;
    });
  }, [questions, searchQuery, examTypeFilter, subjectFilter, difficultyFilter]);

  // Pagination
  const indexOfLastQuestion = currentPage * questionsPerPage;
  const indexOfFirstQuestion = indexOfLastQuestion - questionsPerPage;
  const currentQuestions = filteredQuestions.slice(indexOfFirstQuestion, indexOfLastQuestion);
  const totalPages = Math.ceil(filteredQuestions.length / questionsPerPage);

  // Get unique values for filters
  const examTypes = useMemo(() =>
    Array.from(new Set(questions.map(q => q.exam_type))),
    [questions],
  );

  const subjects = useMemo(() =>
    Array.from(new Set(questions.map(q => q.subject))),
    [questions],
  );

  // Helper functions
  function getDifficultyLevel(difficulty: number): string {
    if (difficulty < 0.3) {return 'Kolay';}
    if (difficulty < 0.5) {return 'Orta';}
    if (difficulty < 0.7) {return 'Zor';}
    return 'Çok Zor';
  }

  function getDifficultyColor(difficulty: number): string {
    if (difficulty < 0.3) {return 'bg-green-100 text-green-800';}
    if (difficulty < 0.5) {return 'bg-yellow-100 text-yellow-800';}
    if (difficulty < 0.7) {return 'bg-orange-100 text-orange-800';}
    return 'bg-red-100 text-red-800';
  }

  // Reset filters
  const resetFilters = () => {
    setSearchQuery('');
    setExamTypeFilter('all');
    setSubjectFilter('all');
    setDifficultyFilter('all');
    setCurrentPage(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Sorular yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 font-semibold mb-2">Hata Oluştu</p>
        <p className="text-red-600">{error}</p>
        <Button
          onClick={() => window.location.reload()}
          className="mt-4"
          variant="outline"
        >
          Yeniden Dene
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Soru Bankası</h2>
              <p className="text-gray-600 mt-1">
                Toplam {questions.length} soru, {filteredQuestions.length} sonuç gösteriliyor
              </p>
            </div>
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                TYT: {questions.filter(q => q.exam_type === 'TYT').length}
              </span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                AYT: {questions.filter(q => q.exam_type === 'AYT').length}
              </span>
              <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                YDT: {questions.filter(q => q.exam_type === 'YDT').length}
              </span>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <Input
                placeholder="Soru veya konu ara..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full"
              />
            </div>

            {/* Exam Type Filter */}
            <Select value={examTypeFilter} onValueChange={(value) => {
              setExamTypeFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Sınav Tipi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Sınavlar</SelectItem>
                {examTypes.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Subject Filter */}
            <Select value={subjectFilter} onValueChange={(value) => {
              setSubjectFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Konu" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Konular</SelectItem>
                {subjects.map(subject => (
                  <SelectItem key={subject} value={subject}>{subject}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Difficulty Filter */}
            <Select value={difficultyFilter} onValueChange={(value) => {
              setDifficultyFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Zorluk" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tüm Seviyeler</SelectItem>
                <SelectItem value="Kolay">Kolay</SelectItem>
                <SelectItem value="Orta">Orta</SelectItem>
                <SelectItem value="Zor">Zor</SelectItem>
                <SelectItem value="Çok Zor">Çok Zor</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Active Filters Info */}
          {(searchQuery || examTypeFilter !== 'all' || subjectFilter !== 'all' || difficultyFilter !== 'all') && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-gray-600">Filtreler aktif:</span>
              <Button
                variant="outline"
                size="sm"
                onClick={resetFilters}
              >
                Filtreleri Temizle
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Questions List */}
      <div className="space-y-4">
        {currentQuestions.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">Filtrelerinize uygun soru bulunamadı.</p>
            </CardContent>
          </Card>
        ) : (
          currentQuestions.map((question, _index) => (
            <Card key={question.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-semibold text-gray-500">
                        #{question.id}
                      </span>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                        {question.exam_type}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                        {question.subject}
                      </span>
                      <span className="text-xs text-gray-500">
                        {question.topic}
                      </span>
                    </div>
                    <p className="text-gray-900 font-medium mb-4">
                      {question.question_text}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor(question.difficulty)}`}>
                    {getDifficultyLevel(question.difficulty)}
                  </span>
                </div>

                {/* Options */}
                <div className="grid grid-cols-1 gap-2 mb-4">
                  {['A', 'B', 'C', 'D', 'E'].map(option => {
                    const optionValue = question[`option_${option.toLowerCase()}` as keyof Question] as string;
                    const isCorrect = question.correct_answer === option;

                    return (
                      <div
                        key={option}
                        className={`p-3 rounded-lg border-2 ${
                          isCorrect
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 bg-white'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`font-semibold ${isCorrect ? 'text-green-700' : 'text-gray-700'}`}>
                            {option})
                          </span>
                          <span className={isCorrect ? 'text-green-900' : 'text-gray-900'}>
                            {optionValue}
                          </span>
                          {isCorrect && (
                            <span className="ml-auto text-green-600 text-sm font-medium">
                              ✓ Doğru Cevap
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* IRT Parameters */}
                <div className="flex items-center gap-4 text-xs text-gray-600 border-t pt-3">
                  <span>Zorluk: {question.difficulty.toFixed(2)}</span>
                  <span>Ayırt Edicilik: {question.discrimination.toFixed(2)}</span>
                  <span>Tahmin: {question.guessing.toFixed(2)}</span>
                </div>

                {/* Explanation */}
                {question.explanation && (
                  <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-700">
                      <span className="font-semibold text-blue-900">Açıklama:</span> {question.explanation}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Sayfa {currentPage} / {totalPages}
                <span className="ml-2">
                  ({indexOfFirstQuestion + 1}-{Math.min(indexOfLastQuestion, filteredQuestions.length)} arası gösteriliyor)
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                >
                  ← Önceki
                </Button>

                {/* Page numbers */}
                <div className="flex gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setCurrentPage(pageNum)}
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                >
                  Sonraki →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuestionBank;
