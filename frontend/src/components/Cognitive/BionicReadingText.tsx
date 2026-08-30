import React, { useMemo } from 'react';
import './neuro-inclusive.css';

interface BionicReadingTextProps {
  text: string;
  enabled?: boolean;
  className?: string;
}

/**
 * Transforms a single word into Bionic Reading format.
 * Bolds the first half of the word (excluding punctuation).
 */
// Export'un tek sebebi: algoritmayi izole test eden BionicReadingText.test.tsx
// (bkz. ayni desenin emsali: pages/ModernExamStartPage.tsx:61-62). react-refresh
// uyarisi bu bilincli tercihin sonucu.
// eslint-disable-next-line react-refresh/only-export-components
export const bionicWord = (word: string): React.ReactNode => {
  // If word is too short, just bold the whole thing or the first letter.
  // Actually, standard is:
  // length 1 -> bold 1
  // length 2 -> bold 1
  // length 3 -> bold 2
  // length 4 -> bold 2
  // length > 4 -> bold roughly half (ceil(length / 2))

  // Use regex to separate punctuation from the actual word
  // \w is only ASCII, so we explicitly define character classes
  const match = word.match(/^([^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]*)([a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]+)([^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]*)$/);

  if (!match) {
    // If it's just punctuation or numbers, return as is
    return word;
  }

  const [, prefix, coreWord, suffix] = match;

  let boldLength = 1;
  const len = coreWord.length;

  if (len === 1) {boldLength = 1;}
  else if (len <= 3) {boldLength = 1;}
  else if (len === 4) {boldLength = 2;}
  else {boldLength = Math.ceil(len / 2);}

  const boldPart = coreWord.slice(0, boldLength);
  const normalPart = coreWord.slice(boldLength);

  return (
    <>
      {prefix}
      <span className="bionic-bold">{boldPart}</span>
      {normalPart}
      {suffix}
    </>
  );
};

export const BionicReadingText: React.FC<BionicReadingTextProps> = ({
  text,
  enabled = true,
  className = '',
}) => {

  const content = useMemo(() => {
    if (!enabled) {return text;}

    // Tokenize to protect HTML tags and MathJax ($...$ or $$...$$)
    // This regex captures block math, inline math, HTML tags, and markdown images/links.
    const tokenRegex = /(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$|<[^>]+>|\[.*?\]\(.*?\))/g;

    // Split the text into tokens (some are protected, some are raw text)
    const tokens = text.split(tokenRegex);

    return tokens.map((token, tIndex) => {
      // If token matches the protected patterns, return it as-is
      if (
        token.startsWith('$') ||
        token.startsWith('<') ||
        (token.startsWith('[') && token.includes(']('))
      ) {
        return <React.Fragment key={`token-${tIndex}`}>{token}</React.Fragment>;
      }

      // Otherwise, process as bionic reading text
      // Split text by lines first to preserve paragraphs
      const paragraphs = token.split('\n');

      return paragraphs.map((paragraph, pIndex) => {
        if (!paragraph.trim() && paragraph.length > 0) {
           return <React.Fragment key={`space-${tIndex}-${pIndex}`}>{paragraph}</React.Fragment>;
        }
        if (!paragraph) {return null;}

        // Split by spaces to process words
        const words = paragraph.split(' ');

        const processedParagraph = words.map((word, wIndex) => (
          <React.Fragment key={`w-${tIndex}-${pIndex}-${wIndex}`}>
            {bionicWord(word)}
            {/* Add space back unless it's the last word */}
            {wIndex < words.length - 1 && ' '}
          </React.Fragment>
        ));

        return (
          <React.Fragment key={`p-${tIndex}-${pIndex}`}>
            {processedParagraph}
            {pIndex < paragraphs.length - 1 && <br />}
          </React.Fragment>
        );
      });
    });
  }, [text, enabled]);

  return (
    <div className={`${enabled ? 'neuro-inclusive-mode' : ''} ${className}`}>
      {content}
    </div>
  );
};

export default BionicReadingText;
