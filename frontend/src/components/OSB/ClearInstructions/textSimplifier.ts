/**
 * Task 95: Text Simplification Utilities
 * Metin basitleştirme yardımcıları
 */

/**
 * Deyimleri basit dile çevir (Task 95.1)
 */
export const idiomReplacements: Record<string, string> = {
  // Türkçe deyimler → Basit açıklamalar
  'aklını başına topla': 'dikkatli ol',
  'gözü arkada kalma': 'endişelenme',
  'kafayı taktı': 'çok düşünüyor',
  'elinden geleni yap': 'yapabildiğin kadar yap',
  'işin içinden çık': 'halletmeye çalış',
  'işi şansa bırakma': 'planla ve çalış',

  // Mecazi ifadeler → Kelimesi kelimesine
  'zaman akıyor': 'zaman geçiyor',
  'ağzından bal damlıyor': 'çok güzel konuşuyor',
  'içinden geçti': 'aklına geldi',
  'yüreği yanıyor': 'çok üzgün',
  'göz kulak olmak': 'dikkatli olmak',
};

/**
 * Metni basitleştir (Task 95.1)
 */
export function simplifyText(text: string): string {
  let simplified = text;

  // Deyimleri değiştir
  Object.entries(idiomReplacements).forEach(([idiom, replacement]) => {
    const regex = new RegExp(idiom, 'gi');
    simplified = simplified.replace(regex, replacement);
  });

  return simplified;
}

/**
 * Cümleleri kısalt (Task 95.2)
 * Uzun cümleleri daha kısa cümlelere böl
 */
export function shortenSentences(text: string): string {
  // Uzun cümleleri tespit et (50+ karakter)
  const sentences = text.split(/[.!?]+/).filter(s => s.trim());

  return sentences
    .map(sentence => {
      const trimmed = sentence.trim();
      if (trimmed.length <= 50) {return trimmed;}

      // Bağlaçlardan böl
      const conjunctions = [' ve ', ' ama ', ' fakat ', ' ancak ', ' çünkü ', ' eğer '];
      for (const conj of conjunctions) {
        if (trimmed.includes(conj)) {
          const parts = trimmed.split(conj);
          return parts.join(`. ${parts[1] ? parts[1][0].toUpperCase() + parts[1].slice(1) : ''}`);
        }
      }

      return trimmed;
    })
    .join('. ')
    + '.';
}

/**
 * Adımları numaralandır (Task 95.3)
 */
export function numberSteps(text: string): Array<{ number: number; text: string }> {
  const sentences = text
    .split(/[.!?]+/)
    .map(s => s.trim())
    .filter(s => s.length > 0);

  return sentences.map((sentence, index) => ({
    number: index + 1,
    text: sentence.endsWith('.') ? sentence : sentence + '.',
  }));
}

/**
 * Örnek oluştur (Task 95.4)
 * Soyut kavrama somut örnek ekle
 */
export const commonExamples: Record<string, string> = {
  // Matematik
  'fonksiyon': 'Örnek: f(x) = 2x + 3 bir fonksiyondur.',
  'denklem': 'Örnek: 2x + 5 = 13 bir denklemdir.',
  'geometri': 'Örnek: Üçgenin iç açıları toplamı 180 derecedir.',

  // Türkçe
  'özne': 'Örnek: "Ali okula gitti" cümlesinde "Ali" öznedir.',
  'yüklem': 'Örnek: "Ali okula gitti" cümlesinde "gitti" yüklemdir.',
  'sıfat': 'Örnek: "Kırmızı araba" tamlamasında "kırmızı" sıfattır.',

  // Fizik
  'hız': 'Örnek: Bir araba saatte 60 km gidiyorsa, hızı 60 km/h dir.',
  'ivme': 'Örnek: Hızlanan bir arabanın ivmesi vardır.',

  // Kimya
  'element': 'Örnek: Oksijen (O) bir elementtir.',
  'bileşik': 'Örnek: Su (H₂O) bir bileşiktir.',

  // Biyoloji
  'hücre': 'Örnek: İnsan vücudu milyonlarca hücreden oluşur.',
  'doku': 'Örnek: Kas dokusu kasılıp gevşeyebilir.',
};

/**
 * Kelimeye örnek ekle
 */
export function addExample(keyword: string): string | undefined {
  const lowerKeyword = keyword.toLowerCase();
  return commonExamples[lowerKeyword];
}

/**
 * Tam metin işleme (tüm Task 95 kuralları)
 */
export function processForOSB(text: string): {
  simplified: string;
  shortened: string;
  steps: Array<{ number: number; text: string }>;
  hasIdioms: boolean;
} {
  const simplified = simplifyText(text);
  const shortened = shortenSentences(simplified);
  const steps = numberSteps(shortened);
  const hasIdioms = simplified !== text;

  return {
    simplified,
    shortened,
    steps,
    hasIdioms,
  };
}
