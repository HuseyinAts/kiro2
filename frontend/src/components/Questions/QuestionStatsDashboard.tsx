/**
 * QuestionStatsDashboard Component
 * 77,336 sorunun istatistiklerini server-side faceted search ile gosteren dashboard
 *
 * Features:
 * - Sinav tipi dagilimi
 * - Konu dagilimi
 * - Bloom taxonomy dagilimi
 * - Kitap istatistikleri
 *
 * Updated: 2026-03-04 - Server-side faceted search (77K soru)
 */

import * as React from 'react';
import { useState, useEffect } from 'react';

import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import config from '@/config';

interface FacetData {
  [key: string]: number;
}

interface StatsData {
  total: number;
  examTypes: FacetData;
  subjects: FacetData;
  totalBooks: number;
  topBooks: { source_book: string; question_count: number }[];
}

export const QuestionStatsDashboard: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch faceted search for exam_type and subject_area
        const searchUrl = `${config.api.baseURL}/api/v1/questions/search`;
        const booksUrl = `${config.api.baseURL}/api/v1/questions/books`;

        const [searchRes, booksRes] = await Promise.all([
          fetch(searchUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              limit: 1,
              offset: 0,
              facets: ['exam_type', 'subject_area'],
            }),
          }),
          fetch(booksUrl),
        ]);

        const searchData = await searchRes.json();
        const booksData = await booksRes.json();

        const facets = searchData?.data?.facets || {};
        const books = booksData?.data?.books || [];

        setStats({
          total: searchData?.data?.total_count || 0,
          examTypes: facets.exam_type || {},
          subjects: facets.subject_area || {},
          totalBooks: booksData?.data?.total_books || 0,
          topBooks: books.slice(0, 15),
        });
      } catch (err) {
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

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
        <p className="text-gray-500">Istatistik hesaplanamadi</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white rounded-lg p-8">
        <h1 className="text-3xl font-bold mb-2">Soru Bankasi Istatistikleri</h1>
        <p className="text-blue-100">
          {stats.total.toLocaleString('tr-TR')} soru uzerinden detayli analiz
        </p>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Toplam Soru</p>
              <p className="text-4xl font-bold text-blue-600">
                {stats.total.toLocaleString('tr-TR')}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Konu Sayisi</p>
              <p className="text-4xl font-bold text-purple-600">
                {Object.keys(stats.subjects).length}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Kaynak Kitap</p>
              <p className="text-4xl font-bold text-green-600">
                {stats.totalBooks}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">Sinav Tipi</p>
              <p className="text-4xl font-bold text-orange-600">
                {Object.keys(stats.examTypes).length}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Exam Type Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Sinav Tipi Dagilimi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(stats.examTypes)
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
                        {count.toLocaleString('tr-TR')} soru ({percentage.toFixed(1)}%)
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
          <CardTitle>Konu Dagilimi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(stats.subjects)
              .sort(([, a], [, b]) => b - a)
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
                        {count.toLocaleString('tr-TR')}
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

      {/* Top Books */}
      <Card>
        <CardHeader>
          <CardTitle>En Cok Sorulu Kitaplar (Top 15)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stats.topBooks.map((book, idx) => {
              const maxCount = stats.topBooks[0]?.question_count || 1;
              const percentage = (book.question_count / maxCount) * 100;

              return (
                <div key={book.source_book} className="flex items-center gap-4">
                  <div className="w-8 text-right text-sm font-bold text-gray-400">
                    {idx + 1}.
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-700 truncate">
                        {book.source_book}
                      </span>
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        ({book.question_count} soru)
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QuestionStatsDashboard;
