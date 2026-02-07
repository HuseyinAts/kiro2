/**
 * QuestionStatsDashboard Component
 * 141 sorunun istatistiklerini görsel olarak gösteren dashboard
 *
 * Features:
 * - Sınav tipi dağılımı (Pie chart)
 * - Konu dağılımı (Bar chart)
 * - Zorluk seviyesi dağılımı
 * - IRT parametreleri özeti
 * - Gerçek zamanlı istatistikler
 */

import * as React from 'react';
import {  useState, useEffect, useMemo  } from 'react';

import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import config from '@/config';

interface Question {
  id: number;
  exam_type: string;
  subject: string;
  topic: string;
  difficulty: number;
  discrimination: number;
  guessing: number;
}

interface QuestionStatsDashboardProps {
  apiUrl?: string;
}

export const QuestionStatsDashboard: React.FC<QuestionStatsDashboardProps> = ({
  apiUrl = `${config.api.baseURL}/api/questions`,
}) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch questions
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        setQuestions(data.questions || data || []);
      } catch (err) {
        console.error('Error fetching questions:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuestions();
  }, [apiUrl]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (questions.length === 0) {return null;}

    // Exam type distribution
    const examTypeCount: Record<string, number> = {};
    questions.forEach(q => {
      examTypeCount[q.exam_type] = (examTypeCount[q.exam_type] || 0) + 1;
    });

    // Subject distribution
    const subjectCount: Record<string, number> = {};
    questions.forEach(q => {
      subjectCount[q.subject] = (subjectCount[q.subject] || 0) + 1;
    });

    // Difficulty distribution
    const difficultyLevels = {
      'Kolay': 0,
      'Orta': 0,
      'Zor': 0,
      'Çok Zor': 0,
    };

    questions.forEach(q => {
      if (q.difficulty < 0.3) {difficultyLevels['Kolay']++;}
      else if (q.difficulty < 0.5) {difficultyLevels['Orta']++;}
      else if (q.difficulty < 0.7) {difficultyLevels['Zor']++;}
      else {difficultyLevels['Çok Zor']++;}
    });

    // IRT averages
    const avgDifficulty = questions.reduce((sum, q) => sum + q.difficulty, 0) / questions.length;
    const avgDiscrimination = questions.reduce((sum, q) => sum + q.discrimination, 0) / questions.length;
    const avgGuessing = questions.reduce((sum, q) => sum + q.guessing, 0) / questions.length;

    return {
      total: questions.length,
      examTypeCount,
      subjectCount,
      difficultyLevels,
      irt: {
        avgDifficulty,
        avgDiscrimination,
        avgGuessing,
      },
    };
  }, [questions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">İstatistik hesaplanamadı</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg p-8">
        <h1 className="text-3xl font-bold mb-2">Soru Bankası İstatistikleri</h1>
        <p className="text-blue-100">
          {stats.total} soru üzerinden detaylı analiz
        </p>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Toplam Soru</p>
              <p className="text-4xl font-bold text-blue-600">{stats.total}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Ortalama Zorluk</p>
              <p className="text-4xl font-bold text-green-600">
                {stats.irt.avgDifficulty.toFixed(2)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Konu Sayısı</p>
              <p className="text-4xl font-bold text-purple-600">
                {Object.keys(stats.subjectCount).length}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Ayırt Edicilik</p>
              <p className="text-4xl font-bold text-orange-600">
                {stats.irt.avgDiscrimination.toFixed(2)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Exam Type Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Sınav Tipi Dağılımı</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(stats.examTypeCount)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => {
                const percentage = (count / stats.total) * 100;
                const color = type === 'TYT' ? 'bg-blue-500' :
                             type === 'AYT' ? 'bg-green-500' : 'bg-purple-500';

                return (
                  <div key={type}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700">{type}</span>
                      <span className="text-sm text-gray-600">
                        {count} soru ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                      <div
                        className={`h-full ${color} transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>

      {/* Subject Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Konu Dağılımı</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(stats.subjectCount)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 10)
              .map(([subject, count]) => {
                const percentage = (count / stats.total) * 100;

                return (
                  <div key={subject} className="flex items-center gap-4">
                    <div className="w-32 flex-shrink-0 text-sm font-medium text-gray-700">
                      {subject}
                    </div>
                    <div className="flex-1 bg-gray-200 rounded-full h-8 overflow-hidden relative">
                      <div
                        className="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                      <span className="absolute inset-0 flex items-center justify-end pr-3 text-sm font-semibold text-gray-700">
                        {count}
                      </span>
                    </div>
                    <div className="w-16 text-right text-sm text-gray-600">
                      {percentage.toFixed(1)}%
                    </div>
                  </div>
                );
              })}
          </div>
        </CardContent>
      </Card>

      {/* Difficulty Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Zorluk Seviyesi Dağılımı</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.difficultyLevels).map(([level, count]) => {
                const percentage = (count / stats.total) * 100;
                const color = level === 'Kolay' ? 'bg-green-500' :
                             level === 'Orta' ? 'bg-yellow-500' :
                             level === 'Zor' ? 'bg-orange-500' : 'bg-red-500';

                return (
                  <div key={level}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-700">{level}</span>
                      <span className="text-sm text-gray-600">
                        {count} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-full ${color} rounded-full transition-all duration-500`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* IRT Parameters */}
        <Card>
          <CardHeader>
            <CardTitle>IRT Parametreleri Özeti</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Zorluk (Difficulty)
                  </span>
                  <span className="text-lg font-bold text-blue-600">
                    {stats.irt.avgDifficulty.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(stats.irt.avgDifficulty + 1) * 50}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  -1 (Çok Kolay) → +1 (Çok Zor)
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Ayırt Edicilik (Discrimination)
                  </span>
                  <span className="text-lg font-bold text-green-600">
                    {stats.irt.avgDiscrimination.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-full bg-green-500 rounded-full"
                    style={{ width: `${Math.min(stats.irt.avgDiscrimination * 50, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  0 (Düşük) → 2+ (Yüksek)
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Tahmin (Guessing)
                  </span>
                  <span className="text-lg font-bold text-purple-600">
                    {stats.irt.avgGuessing.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${stats.irt.avgGuessing * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  0 (Tahmin yok) → 1 (Sadece tahmin)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quality Indicators */}
      <Card>
        <CardHeader>
          <CardTitle>Soru Kalite Göstergeleri</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Yüksek Kalite</p>
              <p className="text-3xl font-bold text-green-600">
                {questions.filter(q =>
                  q.discrimination > 1.0 && q.difficulty > -0.5 && q.difficulty < 0.5,
                ).length}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Ayırt edicilik &gt; 1.0
              </p>
            </div>

            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Orta Kalite</p>
              <p className="text-3xl font-bold text-yellow-600">
                {questions.filter(q =>
                  q.discrimination >= 0.5 && q.discrimination <= 1.0,
                ).length}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Ayırt edicilik 0.5-1.0
              </p>
            </div>

            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">İncelenmeli</p>
              <p className="text-3xl font-bold text-red-600">
                {questions.filter(q => q.discrimination < 0.5).length}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Ayırt edicilik &lt; 0.5
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QuestionStatsDashboard;
