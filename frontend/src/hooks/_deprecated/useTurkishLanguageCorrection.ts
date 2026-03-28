import { useState, useCallback, useRef } from 'react';

interface LanguageCorrection {
  original: string;
  corrected: string;
  suggestions: string[];
  confidence: number;
  type: 'spelling' | 'grammar' | 'style';
  explanation?: string;
}

interface UseTurkishLanguageCorrectionReturn {
  checkText: (text: string) => Promise<void>;
  suggestions: LanguageCorrection[];
  isChecking: boolean;
  error: string | null;
  clearSuggestions: () => void;
}

// Turkish language rules and common corrections
const TURKISH_CORRECTIONS = {
  // Common spelling mistakes
  spelling: {
    'birşey': 'bir şey',
    'herşey': 'her şey',
    'hiçbirşey': 'hiçbir şey',
    'neden': 'neden',
    'nedne': 'neden',
    'nasıl': 'nasıl',
    'tabi': 'tabii',
    'tabiki': 'tabii ki',
    'hemde': 'hem de',
    'yinede': 'yine de',
    'birde': 'bir de',
    'bide': 'bir de',
    'herzaman': 'her zaman',
    'herkes': 'herkes',
    'herkez': 'herkes',
    'birkaç': 'birkaç',
    'bikaç': 'birkaç',
    'çünki': 'çünkü',
    'çünku': 'çünkü',
    'olabilir': 'olabilir',
    'olabiliyor': 'olabiliyor',
    'yapabilir': 'yapabilir',
    'yapabiliyor': 'yapabiliyor',
  },

  // Grammar corrections
  grammar: {
    'gidiyorum': 'gidiyorum',
    'geliyorum': 'geliyorum',
    'yapıyorum': 'yapıyorum',
    'ediyorum': 'ediyorum',
    'biliyorum': 'biliyorum',
    'görüyorum': 'görüyorum',
    'diyorum': 'diyorum',
    'söylüyorum': 'söylüyorum',
  },

  // Style improvements
  style: {
    'çok güzel': 'harika',
    'çok iyi': 'mükemmel',
    'çok kötü': 'berbat',
    'çok büyük': 'devasa',
    'çok küçük': 'minik',
  },
};

// Turkish punctuation rules
const PUNCTUATION_RULES = [
  {
    pattern: /\s+([,.!?;:])/g,
    replacement: '$1',
    message: 'Noktalama işaretlerinden önce boşluk olmamalı',
  },
  {
    pattern: /([,.!?;:])\s*([a-zA-ZçğıöşüÇĞIİÖŞÜ])/g,
    replacement: '$1 $2',
    message: 'Noktalama işaretlerinden sonra boşluk olmalı',
  },
  {
    pattern: /\s{2,}/g,
    replacement: ' ',
    message: 'Çoklu boşluklar tek boşluk olmalı',
  },
];

export const useTurkishLanguageCorrection = (): UseTurkishLanguageCorrectionReturn => {
  const [suggestions, setSuggestions] = useState<LanguageCorrection[]>([]);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Check spelling using built-in corrections
  const checkSpelling = useCallback((text: string): LanguageCorrection[] => {
    const corrections: LanguageCorrection[] = [];
    const words = text.split(/\s+/);

    words.forEach(word => {
      const cleanWord = word.replace(/[^\w\sçğıöşüÇĞIİÖŞÜ]/g, '').toLowerCase();

      if (cleanWord.length < 2) {return;}

      // Check against known corrections
      Object.entries(TURKISH_CORRECTIONS.spelling).forEach(([wrong, correct]) => {
        if (cleanWord === wrong) {
          corrections.push({
            original: word,
            corrected: correct,
            suggestions: [correct],
            confidence: 0.9,
            type: 'spelling',
            explanation: `"${wrong}" yerine "${correct}" yazılmalı`,
          });
        }
      });

      // Check for common patterns
      if (cleanWord.includes('birşey')) {
        corrections.push({
          original: word,
          corrected: word.replace('birşey', 'bir şey'),
          suggestions: [word.replace('birşey', 'bir şey')],
          confidence: 0.95,
          type: 'spelling',
          explanation: '"bir şey" ayrı yazılır',
        });
      }

      if (cleanWord.includes('herşey')) {
        corrections.push({
          original: word,
          corrected: word.replace('herşey', 'her şey'),
          suggestions: [word.replace('herşey', 'her şey')],
          confidence: 0.95,
          type: 'spelling',
          explanation: '"her şey" ayrı yazılır',
        });
      }
    });

    return corrections;
  }, []);

  // Check grammar patterns
  const checkGrammar = useCallback((text: string): LanguageCorrection[] => {
    const corrections: LanguageCorrection[] = [];

    // Check for common grammar mistakes
    const grammarPatterns = [
      {
        pattern: /\b(gidiyom|geliyom|yapıyom|ediyom)\b/gi,
        replacement: (match: string) => {
          const base = match.slice(0, -2);
          return base + 'orum';
        },
        message: 'Fiil çekimi düzeltildi',
      },
      {
        pattern: /\b(birşeyi|herşeyi)\b/gi,
        replacement: (match: string) => match.replace('şey', ' şey'),
        message: '"şey" kelimesi ayrı yazılır',
      },
      {
        pattern: /\b(hemde|yinede|birde)\b/gi,
        replacement: (match: string) => {
          if (match.toLowerCase().includes('hemde')) {return 'hem de';}
          if (match.toLowerCase().includes('yinede')) {return 'yine de';}
          if (match.toLowerCase().includes('birde')) {return 'bir de';}
          return match;
        },
        message: 'Bağlaç ayrı yazılır',
      },
    ];

    grammarPatterns.forEach(({ pattern, replacement, message }) => {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        if (match[0] && match.index !== undefined) {
          const corrected = typeof replacement === 'function'
            ? replacement(match[0])
            : replacement;

          corrections.push({
            original: match[0],
            corrected: corrected,
            suggestions: [corrected],
            confidence: 0.8,
            type: 'grammar',
            explanation: message,
          });
        }
      }
    });

    return corrections;
  }, []);

  // Check punctuation
  const checkPunctuation = useCallback((text: string): LanguageCorrection[] => {
    const corrections: LanguageCorrection[] = [];

    PUNCTUATION_RULES.forEach(({ pattern, replacement, message }) => {
      if (pattern.test(text)) {
        const corrected = text.replace(pattern, replacement);
        if (corrected !== text) {
          corrections.push({
            original: text,
            corrected: corrected,
            suggestions: [corrected],
            confidence: 0.7,
            type: 'style',
            explanation: message,
          });
        }
      }
    });

    return corrections;
  }, []);

  // Main text checking function
  const checkText = useCallback(async (text: string): Promise<void> => {
    if (!text.trim() || text.length < 3) {
      setSuggestions([]);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsChecking(true);
    setError(null);

    try {
      // Simulate API delay for realistic UX
      await new Promise(resolve => setTimeout(resolve, 500));

      if (abortControllerRef.current.signal.aborted) {
        return;
      }

      const allCorrections: LanguageCorrection[] = [];

      // Check spelling
      const spellingCorrections = checkSpelling(text);
      allCorrections.push(...spellingCorrections);

      // Check grammar
      const grammarCorrections = checkGrammar(text);
      allCorrections.push(...grammarCorrections);

      // Check punctuation
      const punctuationCorrections = checkPunctuation(text);
      allCorrections.push(...punctuationCorrections);

      // Remove duplicates and sort by confidence
      const uniqueCorrections = allCorrections
        .filter((correction, index, array) =>
          array.findIndex(c => c.original === correction.original) === index,
        )
        .sort((a, b) => b.confidence - a.confidence)
        .slice(0, 5); // Limit to top 5 suggestions

      setSuggestions(uniqueCorrections);

    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Dil kontrolü hatası:', error);
        setError('Dil kontrolü yapılırken hata oluştu');
      }
    } finally {
      setIsChecking(false);
    }
  }, [checkSpelling, checkGrammar, checkPunctuation]);

  // Clear suggestions
  const clearSuggestions = useCallback(() => {
    setSuggestions([]);
    setError(null);
  }, []);

  return {
    checkText,
    suggestions,
    isChecking,
    error,
    clearSuggestions,
  };
};