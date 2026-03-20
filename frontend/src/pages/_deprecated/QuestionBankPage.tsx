/**
 * QuestionBankPage
 * Soru bankası ana sayfası - Tab'lı görünüm
 *
 * Tabs:
 * 1. Soru Listesi - Filtreleme ve görüntüleme
 * 2. İstatistikler - Dashboard ve analizler
 */

import * as React from 'react';
import {  useState  } from 'react';

import QuestionBank from '@/components/Questions/QuestionBank';
import QuestionStatsDashboard from '@/components/Questions/QuestionStatsDashboard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export const QuestionBankPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                KIRO2 Soru Bankası
              </h1>
              <p className="text-gray-600 mt-1">
                ÖSYM tarzı sorular - TYT, AYT, YDT
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium">
                77,336 Soru
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
            <TabsTrigger value="list" className="flex items-center gap-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              Soru Listesi
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              İstatistikler
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list" className="mt-0">
            <QuestionBank />
          </TabsContent>

          <TabsContent value="stats" className="mt-0">
            <QuestionStatsDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default QuestionBankPage;
