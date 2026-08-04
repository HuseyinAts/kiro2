
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './mathText.css';

interface MarkdownRendererProps {
  text: string;
  inline: boolean;
}

export default function MarkdownRenderer({ text, inline }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[[remarkMath, { singleDollarTextMath: true }]]}
      rehypePlugins={[[rehypeKatex, { strict: false, trust: true, throwOnError: false }]]}
      components={{
        p: ({ children: c }) => (inline ? <span>{c}</span> : <p style={{ margin: 0 }}>{c}</p>),
      }}
    >
      {text}
    </ReactMarkdown>
  );
}
