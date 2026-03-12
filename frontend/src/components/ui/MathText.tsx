/**
 * MathText — LaTeX formül destekli metin render bileşeni.
 * KaTeX ile $...$ ve $$...$$ formatını render eder.
 * Chat'te zaten çalışıyor (TurkishChatInterface), bu sınav sorularına da taşıyor.
 */

import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface MathTextProps {
  children: string;
  /** Inline modda <span>, block modda <div> */
  inline?: boolean;
}

/** Metinde LaTeX var mı hızlı kontrol */
function hasLatex(text: string): boolean {
  return text.includes('$') || text.includes('\\frac') || text.includes('\\sqrt');
}

export const MathText: React.FC<MathTextProps> = ({ children, inline = false }) => {
  // Null/undefined guard — content + question_text ikisi de boşsa crash önle
  if (!children) return inline ? <span /> : <div />;

  // LaTeX yoksa doğrudan metin döndür (performans)
  if (!hasLatex(children)) {
    const normalized = children.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();
    return inline ? <span>{normalized}</span> : <div style={{ whiteSpace: 'pre-wrap' }}>{normalized}</div>;
  }

  // LaTeX yolunda da whitespace normalize et (OCR line-break temizliği)
  const preprocessed = children.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();

  return (
    <ReactMarkdown
      remarkPlugins={[remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        // Paragrafları inline modda span olarak render et
        p: ({ children: c }) => inline ? <span>{c}</span> : <p style={{ margin: 0 }}>{c}</p>,
      }}
    >
      {preprocessed}
    </ReactMarkdown>
  );
};

export default MathText;
