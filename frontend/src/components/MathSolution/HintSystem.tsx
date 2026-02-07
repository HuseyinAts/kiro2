/**
 * İpucu Sistemi Bileşeni
 * Requirements: REQ-51.31-51.35 (İpucu sistemi)
 */

import { Lightbulb, Lock, Unlock } from 'lucide-react';
import * as React from 'react';
import {  useState  } from 'react';

interface HintSystemProps {
  problemId: string;
  stepNumber: number;
  hints: string[];
}

const HintSystem: React.FC<HintSystemProps> = ({ problemId: _problemId, stepNumber: _stepNumber, hints }) => {
  const [unlockedHints, setUnlockedHints] = useState<number[]>([]);

  const hintLevelNames = [
    'Hafif İpucu',
    'Orta İpucu',
    'Detaylı İpucu',
  ];

  const hintLevelColors = [
    'bg-yellow-100 border-yellow-300',
    'bg-orange-100 border-orange-300',
    'bg-red-100 border-red-300',
  ];

  const unlockHint = (level: number) => {
    if (!unlockedHints.includes(level)) {
      setUnlockedHints([...unlockedHints, level]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lightbulb className="text-yellow-600" size={24} />
          <h4 className="font-semibold text-gray-800">İpuçları</h4>
        </div>
        <span className="text-sm text-gray-600">
          {unlockedHints.length} / {hints.length}
        </span>
      </div>

      <div className="space-y-3">
        {hints.map((hint, index) => {
          const level = index + 1;
          const isUnlocked = unlockedHints.includes(level);

          return (
            <div key={level} className={`border-2 rounded-lg p-3 ${
              isUnlocked ? hintLevelColors[index] : 'bg-gray-50 border-gray-300'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-sm">{hintLevelNames[index]}</span>
                {!isUnlocked ? (
                  <button
                    onClick={() => unlockHint(level)}
                    className="flex items-center gap-2 px-3 py-1 bg-white rounded text-sm"
                  >
                    <Lock size={14} />
                    Aç
                  </button>
                ) : (
                  <Unlock size={16} className="text-green-600" />
                )}
              </div>
              {isUnlocked && <p className="text-gray-800">{hint}</p>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HintSystem;
