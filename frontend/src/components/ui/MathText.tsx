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

/**
 * Bare LaTeX wrap — $ delimiter olmadan ham \frac, \sqrt, \alpha vb. varsa
 * remarkMath bunları render etmez (ham kalır: "\frac{26}{33}"). Bug #1 v2
 * (19 May 2026 beta01 flag `7c49c4d7`): opsiyonlarda DB'de `\frac{26}{33}`
 * format'ında — auto-wrap çözer.
 */
const BARE_LATEX_REGEX = /\\(?:frac|sqrt|sum|int|prod|lim|infty|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|pi|sigma|phi|psi|omega|cdot|times|le|ge|ne|approx|in|notin|cup|cap|subset|supset|forall|exists|partial|nabla|leftarrow|rightarrow|Leftrightarrow|Rightarrow|leq|geq|neq)\b/;

function autoWrapBareLatex(text: string): string {
  // Eğer $ delimiter zaten varsa veya bare LaTeX yoksa dokunma
  if (text.includes('$') || !BARE_LATEX_REGEX.test(text)) {
    return text;
  }
  // Tek bir bare LaTeX expression: tüm string'i $...$ ile sar
  return `$${text}$`;
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
  // + bare LaTeX auto-wrap ($ delimiter olmadan \frac vb. olanlar için)
  const preprocessed = autoWrapBareLatex(
    children.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim(),
  );

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
