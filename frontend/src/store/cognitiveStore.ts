import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type CognitiveStateMode = 'FLOW' | 'FOCUS' | 'OVERLOAD';

interface CognitiveState {
  mode: CognitiveStateMode;
  consecutiveErrors: number;
  averageResponseTime: number; // in seconds
  
  // Actions
  recordAnswer: (isCorrect: boolean, timeSpent: number) => void;
  resetCognitiveState: () => void;
  forceMode: (mode: CognitiveStateMode) => void;
}

/**
 * 2026 Adaptive UX Store (Cognitive Load Management)
 * Otonom olarak öğrencinin zorlanma seviyesine göre arayüzü ayarlar.
 */
export const useCognitiveStore = create<CognitiveState>()(
  persist(
    (set, get) => ({
      mode: 'FLOW',
      consecutiveErrors: 0,
      averageResponseTime: 0,

      recordAnswer: (isCorrect: boolean, timeSpent: number) => {
        const state = get();
        
        // Calculate moving average of response time
        const newAvgTime = state.averageResponseTime === 0 
          ? timeSpent 
          : (state.averageResponseTime * 0.7) + (timeSpent * 0.3);

        let newErrors = isCorrect ? 0 : state.consecutiveErrors + 1;
        let nextMode: CognitiveStateMode = 'FLOW';

        // Cognitive Load Analysis Algorithm
        if (newErrors >= 3 || (newErrors >= 2 && newAvgTime > 60)) {
          // Öğrenci çok zorlanıyor veya uzun süre bekleyip hata yapıyor.
          nextMode = 'OVERLOAD';
        } else if (newErrors === 1 || newAvgTime > 45) {
          // Odaklanmakta güçlük çekiyor, arayüzü sadeleştir.
          nextMode = 'FOCUS';
        } else {
          // İşler yolunda, rekabetçi oyunlaştırma aktif.
          nextMode = 'FLOW';
        }

        set({
          consecutiveErrors: newErrors,
          averageResponseTime: newAvgTime,
          mode: nextMode,
        });
      },

      resetCognitiveState: () => {
        set({
          mode: 'FLOW',
          consecutiveErrors: 0,
          averageResponseTime: 0,
        });
      },

      forceMode: (mode: CognitiveStateMode) => {
        set({ mode });
      },
    }),
    {
      name: 'kiro-cognitive-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
