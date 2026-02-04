/**
 * Hata Vurgulama Bileşeni
 * Requirements: REQ-51.36-51.40 (Hata vurgulama)
 * 
 * Bu bileşen:
 * - Yanlış adımları kırmızı ile vurgular
 * - Hata türünü belirler (işlem, kavram, dikkat hatası)
 * - Düzeltici öneriler sunar
 * - Doğru düzeltmelerde pozitif geri bildirim verir
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, XCircle, Lightbulb } from 'lucide-react';

export enum ErrorType {
  OPERATION = 'operation',      // İşlem hatası (2+2=5 gibi)
  CONCEPT = 'concept',          // Kavram hatası (yanlış formül kullanımı)
  ATTENTION = 'attention'       // Dikkat hatası (işaret unutma, kopyalama hatası)
}

interface MathError {
  type: ErrorType;
  description: string;
  incorrectPart: string;
  correctPart: string;
  suggestion: string;
}

interface ErrorHighlightProps {
  studentAnswer?: string;
  correctAnswer: string;
  onCorrection?: (isCorrect: boolean) => void;
  showFeedback?: boolean;
}

const ErrorHighlight: React.FC<ErrorHighlightProps> = ({
  studentAnswer,
  correctAnswer,
  onCorrection,
  showFeedback = true
}) => {
  const [error, setError] = useState<MathError | null>(null);
  const [isCorrected, setIsCorrected] = useState(false);
  const [showSuggestion, setShowSuggestion] = useState(false);

  // Hata tespiti
  React.useEffect(() => {
    if (studentAnswer && studentAnswer !== correctAnswer) {
      const detectedError = detectError(studentAnswer, correctAnswer);
      setError(detectedError);
      setIsCorrected(false);
      if (onCorrection) {
        onCorrection(false);
      }
    } else if (studentAnswer === correctAnswer) {
      setError(null);
      setIsCorrected(true);
      if (onCorrection) {
        onCorrection(true);
      }
    }
  }, [studentAnswer, correctAnswer, onCorrection]);

  // Basit hata tespit algoritması
  const detectError = (student: string, correct: string): MathError => {
    // İşlem hatası kontrolü (sayısal fark)
    const studentNum = parseFloat(student.replace(/[^0-9.-]/g, ''));
    const correctNum = parseFloat(correct.replace(/[^0-9.-]/g, ''));
    
    if (!isNaN(studentNum) && !isNaN(correctNum) && studentNum !== correctNum) {
      return {
        type: ErrorType.OPERATION,
        description: 'İşlem Hatası',
        incorrectPart: student,
        correctPart: correct,
        suggestion: 'İşlemi tekrar kontrol et. Hesap makinesini kullanabilirsin.'
      };
    }

    // İşaret hatası kontrolü
    if (student.replace('-', '') === correct.replace('-', '')) {
      return {
        type: ErrorType.ATTENTION,
        description: 'Dikkat Hatası (İşaret)',
        incorrectPart: student,
        correctPart: correct,
        suggestion: 'Pozitif/negatif işaretini kontrol et.'
      };
    }

    // Genel kavram hatası
    return {
      type: ErrorType.CONCEPT,
      description: 'Kavram Hatası',
      incorrectPart: student,
      correctPart: correct,
      suggestion: 'Bu adımda kullanılan yöntemi tekrar gözden geçir.'
    };
  };

  // Hata türüne göre renk
  const getErrorColor = (type: ErrorType) => {
    const colors = {
      [ErrorType.OPERATION]: 'bg-red-100 border-red-400 text-red-800',
      [ErrorType.CONCEPT]: 'bg-orange-100 border-orange-400 text-orange-800',
      [ErrorType.ATTENTION]: 'bg-yellow-100 border-yellow-400 text-yellow-800'
    };
    return colors[type];
  };

  // Hata türüne göre ikon
  const getErrorIcon = (type: ErrorType) => {
    const icons = {
      [ErrorType.OPERATION]: '🔢',
      [ErrorType.CONCEPT]: '💡',
      [ErrorType.ATTENTION]: '⚠️'
    };
    return icons[type];
  };

  if (!studentAnswer) {
    return null;
  }

  return (
    <div className="space-y-4">
      <AnimatePresence mode="wait">
        {/* Hata Gösterimi */}
        {error && !isCorrected && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`border-2 rounded-lg p-4 ${getErrorColor(error.type)}`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 text-3xl">
                {getErrorIcon(error.type)}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <XCircle size={20} />
                  <h4 className="font-semibold">{error.description}</h4>
                </div>

                {/* Yanlış Cevap */}
                <div className="mb-3">
                  <p className="text-sm font-medium mb-1">Senin Cevabın:</p>
                  <div className="bg-white bg-opacity-50 rounded px-3 py-2 font-mono">
                    <span className="line-through">{error.incorrectPart}</span>
                  </div>
                </div>

                {/* Doğru Cevap */}
                <div className="mb-3">
                  <p className="text-sm font-medium mb-1">Doğru Cevap:</p>
                  <div className="bg-white bg-opacity-50 rounded px-3 py-2 font-mono text-green-700 font-semibold">
                    {error.correctPart}
                  </div>
                </div>

                {/* Öneri Butonu */}
                <button
                  onClick={() => setShowSuggestion(!showSuggestion)}
                  className="flex items-center gap-2 px-3 py-2 bg-white hover:bg-gray-50 rounded-lg text-sm font-medium transition-colors shadow-sm"
                >
                  <Lightbulb size={16} />
                  <span>{showSuggestion ? 'Öneriyi Gizle' : 'Düzeltme Önerisi'}</span>
                </button>

                {/* Öneri */}
                <AnimatePresence>
                  {showSuggestion && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="mt-3 bg-white bg-opacity-70 rounded-lg p-3 border border-gray-200"
                    >
                      <p className="text-sm">{error.suggestion}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}

        {/* Başarı Gösterimi */}
        {isCorrected && showFeedback && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-green-100 border-2 border-green-400 rounded-lg p-4"
          >
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0 w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                <CheckCircle size={28} className="text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-green-800 text-lg">Doğru! 🎉</h4>
                <p className="text-green-700 text-sm mt-1">
                  Harika iş çıkardın! Cevabın tamamen doğru.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hata Türü Açıklamaları */}
      {error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h5 className="font-semibold text-blue-900 mb-2">💡 Hata Türleri Hakkında</h5>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="font-semibold">🔢 İşlem Hatası:</span>
              <span>Toplama, çıkarma, çarpma veya bölme işleminde yapılan hata</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">💡 Kavram Hatası:</span>
              <span>Yanlış formül veya yöntem kullanımı</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-semibold">⚠️ Dikkat Hatası:</span>
              <span>İşaret unutma, kopyalama hatası gibi dikkatsizlik</span>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ErrorHighlight;
