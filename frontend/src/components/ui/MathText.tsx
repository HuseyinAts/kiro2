/**
 * MathText — LaTeX formül destekli metin render bileşeni.
 * KaTeX ile $...$ ve $$...$$ formatını render eder.
 * Chat'te zaten çalışıyor (TurkishChatInterface), bu sınav sorularına da taşıyor.
 */

import React, { Suspense } from 'react';
import './mathText.css';

const MarkdownRenderer = React.lazy(() => import('./MarkdownRenderer'));

interface MathTextProps {
  children: string;
  /** Inline modda <span>, block modda <div> */
  inline?: boolean;
}

function hasLatex(text: string): boolean {
  return text.includes('$') || text.includes('\\[') || text.includes('\\frac') || text.includes('\\sqrt') || text.includes('\\triangle');
}

function preprocessLatex(text: string): string {
  // Just normalize unescaped dollar signs and spacing, don't try to guess math bounds
  let t = text.replace(/\\\$/g, '$');
  t = t.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();

  // Auto-wrap if it looks like a purely bare math string (like \frac{26}{33} without text)
  if (!t.includes('$') && !t.includes('\\[') && t.startsWith('\\') && !t.includes(' ')) {
    t = `$${t}$`;
  } else if (!t.includes('$') && (t.includes('\\frac') || t.includes('\\sqrt') || t.includes('\\sin') || t.includes('\\cos') || t.includes('\\tan') || t.includes('\\cot') || t.includes('\\lim'))) {
    // If it's mixed text and math without $, this is a complex problem.
    // For now, we will wrap specific known commands using a simple regex,
    // or just let it pass as text if it's too complex.
    // Actually, react-markdown won't parse it without $. We'll wrap the whole thing if it's very short.
    if (t.length < 20) {
      t = `$${t}$`;
    }
  }
  return t;
}

export const MathText: React.FC<MathTextProps> = ({ children, inline = false }) => {
  if (!children) { return inline ? <span /> : <div />; }

  if (!hasLatex(children)) {
    const normalized = children.replace(/\n{3,}/g, '\n\n').replace(/[ \t]+/g, ' ').trim();
    return inline ? <span>{normalized}</span> : <div style={{ whiteSpace: 'pre-wrap' }}>{normalized}</div>;
  }

  const preprocessed = preprocessLatex(children);

  return (
    <Suspense fallback={inline ? <span>{children}</span> : <div style={{ whiteSpace: 'pre-wrap' }}>{children}</div>}>
      <MarkdownRenderer text={preprocessed} inline={inline} />
    </Suspense>
  );
};

export default MathText;
