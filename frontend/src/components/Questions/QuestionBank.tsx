/**
 * QuestionBank Component
 * 77,336 soruyu görüntülemek için ana component (question_bank tablosu)
 *
 * Features:
 * - Server-side pagination (POST /api/v1/questions/search)
 * - Filtreleme (Sınav tipi, Konu, Kaynak kitap, Zorluk)
 * - Arama (soru metni)
 * - Bloom taxonomy badge
 * - MathJax desteği
 * - Responsive design
 *
 * Updated: 2026-03-04 - question_bank API entegrasyonu (77K soru)
 */

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';

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
import { QuestionImage } from '@/components/ui/ImageZoomModal';

// API Response tipi (question_bank şeması)
interface SearchQuestion {
  id: string;
  question_text: string;
  question_image_url: string | null;
  image_alt_text?: string | null;
  image_width?: number | null;
  image_height?: number | null;
  options?: Record<string, string | null>;
  correct_answer?: string;
  exam_type: string;
  subject_area: string;
  source_book: string | null;
  topic: string | null;
  difficulty: string;
  bloom_level: number;
  bloom_category: string;
  irt_difficulty: number;
  quality_score: number | null;
  word_count: number;
  times_asked: number;
  success_rate: number;
  created_at: string;
}

interface SearchResponse {
  success: boolean;
  data: {
    questions: SearchQuestion[];
    total_count: number;
    limit: number;
    offset: number;
    facets: Record<string, Record<string, number>> | null;
    has_more: boolean;
  };
  message: string;
}

// Bloom level renkleri
const BLOOM_COLORS: Record<number, string> = {
  1: 'bg-gray-100 text-gray-700',
  2: 'bg-blue-100 text-blue-700',
  3: 'bg-green-100 text-green-700',
  4: 'bg-yellow-100 text-yellow-700',
  5: 'bg-orange-100 text-orange-700',
  6: 'bg-red-100 text-red-700',
};

const BLOOM_LABELS: Record<number, string> = {
  1: 'Hat\u0131rla',
  2: 'Anla',
  3: 'Uygula',
  4: 'Analiz',
  5: 'De\u011ferlendir',
  6: 'Olu\u015ftur',
};

// Difficulty badge renkleri
function getDifficultyColor(difficulty: string): string {
  switch (difficulty) {
    case 'VERY_EASY': return 'bg-green-100 text-green-800';
    case 'EASY': return 'bg-green-50 text-green-700';
    case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
    case 'HARD': return 'bg-orange-100 text-orange-800';
    case 'VERY_HARD': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

function getDifficultyLabel(difficulty: string): string {
  switch (difficulty) {
    case 'VERY_EASY': return 'Cok Kolay';
    case 'EASY': return 'Kolay';
    case 'MEDIUM': return 'Orta';
    case 'HARD': return 'Zor';
    case 'VERY_HARD': return 'Cok Zor';
    default: return difficulty;
  }
}

// Subject alan renkleri
function getSubjectColor(subject: string): string {
  const colors: Record<string, string> = {
    MATEMATIK: 'bg-blue-100 text-blue-800',
    GEOMETRI: 'bg-indigo-100 text-indigo-800',
    FIZIK: 'bg-purple-100 text-purple-800',
    KIMYA: 'bg-pink-100 text-pink-800',
    BIYOLOJI: 'bg-emerald-100 text-emerald-800',
    TURKCE: 'bg-amber-100 text-amber-800',
    EDEBIYAT: 'bg-rose-100 text-rose-800',
    TARIH: 'bg-orange-100 text-orange-800',
    COGRAFYA: 'bg-teal-100 text-teal-800',
  };
  return colors[subject] || 'bg-gray-100 text-gray-800';
}

const SUBJECTS = [
  'MATEMATIK', 'GEOMETRI', 'FIZIK', 'KIMYA', 'BIYOLOJI',
  'TURKCE', 'EDEBIYAT', 'TARIH', 'COGRAFYA', 'FELSEFE',
  'DIN_KULTURU', 'GENEL',
];

export const QuestionBank: React.FC = () => {
  // Data state
  const [questions, setQuestions] = useState<SearchQuestion[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [examTypeFilter, setExamTypeFilter] = useState<string>('all');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');
  const [sourceBookFilter, setSourceBookFilter] = useState<string>('all');

  // Pagination (server-side)
  const [currentPage, setCurrentPage] = useState(1);
  const questionsPerPage = 20;

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Book list for filter
  const [books, setBooks] = useState<{ source_book: string; question_count: number }[]>([]);

  // Initialize MathJax on mount
  useEffect(() => {
    initMathJax();
  }, []);

  // Fetch books for filter dropdown
  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const url = `${config.api.baseURL}/api/v1/questions/books`;
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setBooks(data.data.books || []);
          }
        }
      } catch {
        // Non-critical, silently ignore
      }
    };
    fetchBooks();
  }, []);

  // Fetch questions (server-side search)
  const fetchQuestions = useCallback(async () => {
    try {
      setLoading(true);
      const url = `${config.api.baseURL}/api/v1/questions/search`;

      const body: Record<string, unknown> = {
        limit: questionsPerPage,
        offset: (currentPage - 1) * questionsPerPage,
        show_answers: true,
      };

      if (debouncedSearch) {body.search_query = debouncedSearch;}
      if (examTypeFilter !== 'all') {body.exam_type = examTypeFilter;}
      if (subjectFilter !== 'all') {body.subject_area = subjectFilter;}
      if (sourceBookFilter !== 'all') {body.source_book = sourceBookFilter;}
      if (difficultyFilter !== 'all') {body.difficulty = difficultyFilter;}

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Sorular yuklenemedi (HTTP ${response.status})`);
      }

      const data: SearchResponse = await response.json();

      if (data.success) {
        setQuestions(data.data.questions);
        setTotalCount(data.data.total_count);
        setError(null);
      } else {
        throw new Error('API basarisiz yanit dondu');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata olustu';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [currentPage, debouncedSearch, examTypeFilter, subjectFilter, difficultyFilter, sourceBookFilter, questionsPerPage]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  // MathJax typeset after questions load
  useEffect(() => {
    if (questions.length > 0) {
      const timer = setTimeout(() => {
        typesetMath();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [questions]);

  // Pagination
  const totalPages = Math.ceil(totalCount / questionsPerPage);

  // Reset filters
  const resetFilters = () => {
    setSearchQuery('');
    setDebouncedSearch('');
    setExamTypeFilter('all');
    setSubjectFilter('all');
    setDifficultyFilter('all');
    setSourceBookFilter('all');
    setCurrentPage(1);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-800 font-semibold mb-2">Hata Olustu</p>
        <p className="text-red-600">{error}</p>
        <Button
          onClick={() => fetchQuestions()}
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
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Soru Bankasi</h2>
              <p className="text-gray-600 mt-1">
                Toplam {totalCount.toLocaleString('tr-TR')} soru
              </p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {totalCount.toLocaleString('tr-TR')} Soru
              </span>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <Input
                placeholder="Soru metni ara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>

            {/* Exam Type Filter */}
            <Select value={examTypeFilter} onValueChange={(value) => {
              setExamTypeFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Sinav Tipi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tum Sinavlar</SelectItem>
                <SelectItem value="TYT">TYT</SelectItem>
                <SelectItem value="AYT">AYT</SelectItem>
                <SelectItem value="YDT">YDT</SelectItem>
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
                <SelectItem value="all">Tum Konular</SelectItem>
                {SUBJECTS.map(subject => (
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
                <SelectItem value="all">Tum Seviyeler</SelectItem>
                <SelectItem value="VERY_EASY">Cok Kolay</SelectItem>
                <SelectItem value="EASY">Kolay</SelectItem>
                <SelectItem value="MEDIUM">Orta</SelectItem>
                <SelectItem value="HARD">Zor</SelectItem>
                <SelectItem value="VERY_HARD">Cok Zor</SelectItem>
              </SelectContent>
            </Select>

            {/* Source Book Filter */}
            <Select value={sourceBookFilter} onValueChange={(value) => {
              setSourceBookFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger>
                <SelectValue placeholder="Kaynak Kitap" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tum Kitaplar ({books.length})</SelectItem>
                {books.slice(0, 50).map(book => (
                  <SelectItem key={book.source_book} value={book.source_book}>
                    {book.source_book} ({book.question_count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Active Filters Info */}
          {(searchQuery || examTypeFilter !== 'all' || subjectFilter !== 'all' || difficultyFilter !== 'all' || sourceBookFilter !== 'all') && (
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

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center min-h-[200px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
            <p className="text-gray-600">Sorular yukleniyor...</p>
          </div>
        </div>
      )}

      {/* Questions List */}
      {!loading && (
        <div className="space-y-4">
          {questions.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">Filtrelerinize uygun soru bulunamadi.</p>
              </CardContent>
            </Card>
          ) : (
            questions.map((question) => (
              <Card key={question.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      {/* Badges */}
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className="text-sm font-mono text-gray-400">
                          {question.id.slice(0, 8)}
                        </span>
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                          {question.exam_type}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSubjectColor(question.subject_area)}`}>
                          {question.subject_area}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getDifficultyColor(question.difficulty)}`}>
                          {getDifficultyLabel(question.difficulty)}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${BLOOM_COLORS[question.bloom_level] || 'bg-gray-100'}`}>
                          B{question.bloom_level}: {BLOOM_LABELS[question.bloom_level] || question.bloom_category}
                        </span>
                        {question.quality_score != null && (
                          <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded text-xs">
                            Q:{question.quality_score.toFixed(0)}
                          </span>
                        )}
                      </div>

                      {/* Question text */}
                      <p className="text-gray-900 font-medium mb-4 whitespace-pre-line">
                        {question.question_text}
                      </p>
                      {question.question_image_url && (
                        <QuestionImage
                          src={question.question_image_url}
                          alt={question.image_alt_text || undefined}
                          width={question.image_width || undefined}
                          height={question.image_height || undefined}
                        />
                      )}
                    </div>
                  </div>

                  {/* Options */}
                  <div className="grid grid-cols-1 gap-2 mb-4">
                    {['A', 'B', 'C', 'D', 'E'].map(option => {
                      const optionValue = question.options?.[option];
                      if (!optionValue) {return null;}
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
                                Dogru Cevap
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Footer: Source book + metadata */}
                  <div className="flex items-center justify-between gap-4 text-xs text-gray-500 border-t pt-3 flex-wrap">
                    <div className="flex items-center gap-4">
                      {question.source_book && (
                        <span title="Kaynak kitap">
                          {question.source_book}
                        </span>
                      )}
                      <span>{question.word_count} kelime</span>
                      <span>IRT: {question.irt_difficulty.toFixed(2)}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      {question.times_asked > 0 && (
                        <span>
                          {question.times_asked}x soruldu ({(question.success_rate * 100).toFixed(0)}% basari)
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="text-sm text-gray-600">
                Sayfa {currentPage} / {totalPages.toLocaleString('tr-TR')}
                <span className="ml-2">
                  (Toplam {totalCount.toLocaleString('tr-TR')} soru)
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(1)}
                  disabled={currentPage === 1}
                >
                  {'<<'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                >
                  Onceki
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
                  Sonraki
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  {'>>'}
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
