/**
 * Çözüm Karşılaştırma Bileşeni - Task 73.3
 * REQ-13.1: Alternatif çözüm yolları karşılaştırma
 *
 * Features:
 * - Side-by-side solution comparison
 * - Time, difficulty, steps comparison
 * - Pros/cons comparison
 * - Visual diff highlighting
 */

import { Clock, Zap, Award, CheckCircle, X } from 'lucide-react';
import * as React from 'react';

interface Solution {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  estimated_time_seconds: number;
  steps: any[];
  advantages?: string[];
  disadvantages?: string[];
  is_fastest?: boolean;
}

interface SolutionComparisonProps {
  solutions: Solution[];
  onClose?: () => void;
}

const SolutionComparison: React.FC<SolutionComparisonProps> = ({ solutions, onClose }) => {
  if (solutions.length < 2) {
    return (
      <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p>Karşılaştırma için en az 2 çözüm seçin.</p>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) {return `${seconds}s`;}
    return `${Math.floor(seconds / 60)}d ${seconds % 60}s`;
  };

  return (
    <div className="solution-comparison bg-white rounded-lg shadow-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Çözüm Karşılaştırması</h2>
        {onClose && (
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded">
            <X size={24} />
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {solutions.slice(0, 2).map((solution) => (
          <div key={solution.id} className="border-2 border-gray-200 rounded-lg p-4">
            {/* Header */}
            <div className="mb-4">
              <h3 className="font-bold text-lg mb-2">{solution.title}</h3>
              <div className="flex flex-wrap gap-2 text-sm">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{solution.category}</span>
                <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{solution.difficulty}</span>
                {solution.is_fastest && (
                  <span className="px-2 py-1 bg-green-500 text-white rounded flex items-center gap-1">
                    <Zap size={14} /> En Hızlı
                  </span>
                )}
              </div>
            </div>

            {/* Stats */}
            <div className="space-y-3 mb-4">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-gray-500" />
                <span className="text-sm">Süre: <strong>{formatTime(solution.estimated_time_seconds)}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Award size={16} className="text-gray-500" />
                <span className="text-sm">Adım: <strong>{solution.steps.length}</strong></span>
              </div>
            </div>

            {/* Pros */}
            {solution.advantages && solution.advantages.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold text-sm text-green-700 mb-2 flex items-center gap-1">
                  <CheckCircle size={14} /> Avantajlar
                </h4>
                <ul className="text-xs space-y-1">
                  {solution.advantages.slice(0, 3).map((adv, i) => (
                    <li key={i} className="text-green-600">✓ {adv}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cons */}
            {solution.disadvantages && solution.disadvantages.length > 0 && (
              <div>
                <h4 className="font-semibold text-sm text-red-700 mb-2">Dezavantajlar</h4>
                <ul className="text-xs space-y-1">
                  {solution.disadvantages.slice(0, 3).map((dis, i) => (
                    <li key={i} className="text-red-600">✗ {dis}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Comparison Summary */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-800 mb-2">Karşılaştırma Özeti</h4>
        <div className="text-sm text-blue-700 space-y-1">
          <p>• En hızlı: <strong>{solutions.find(s => s.is_fastest)?.title || solutions[0].title}</strong></p>
          <p>• En az adım: <strong>{solutions.reduce((min, s) => s.steps.length < min.steps.length ? s : min).title}</strong></p>
          <p>• En kolay: <strong>{solutions.find(s => s.difficulty === 'kolay')?.title || 'Yok'}</strong></p>
        </div>
      </div>
    </div>
  );
};

export default SolutionComparison;
