import clsx from 'clsx';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
// S179 fix (B-P0-62): use light build + register specific languages.
// Pre-fix `react-syntax-highlighter` Prism import bundled ALL 300+
// languages → 611 KB chatService chunk. Light build + 4 registered
// languages drops to ~80 KB.
import SyntaxHighlighter from 'react-syntax-highlighter/dist/esm/light';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import { vs2015 as vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('json', json);

import { dateUtils } from '@/utils/dateUtils';

interface ChatMessageProps {
  role: 'user' | 'agent'
  content: string
  timestamp: string
  agentName?: string
  agentIcon?: string
  isTyping?: boolean
}

export function ChatMessage({
  role,
  content,
  timestamp,
  agentName,
  agentIcon,
  isTyping,
}: ChatMessageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={clsx(
        'flex w-full mb-4',
        role === 'user' ? 'justify-end' : 'justify-start',
      )}
    >
      <div className={clsx(
        'flex max-w-[70%] gap-3',
        role === 'user' ? 'flex-row-reverse' : 'flex-row',
      )}>
        {/* Avatar */}
        <div className={clsx(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
          role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gradient-to-br from-purple-500 to-pink-500 text-white',
        )}>
          {role === 'user' ? '👤' : agentIcon || '🤖'}
        </div>

        {/* Message Content */}
        <div className="flex flex-col gap-1">
          {role === 'agent' && agentName && (
            <span className="text-xs text-gray-500 ml-2">{agentName}</span>
          )}

          <div className={clsx(
            'rounded-2xl px-4 py-3 shadow-sm',
            role === 'user'
              ? 'bg-blue-500 text-white rounded-tr-none'
              : 'bg-white text-gray-800 rounded-tl-none border border-gray-200',
          )}>
            {isTyping ? (
              <div className="flex gap-1 py-2">
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-2 h-2 bg-gray-400 rounded-full"
                />
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                  className="w-2 h-2 bg-gray-400 rounded-full"
                />
                <motion.span
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                  className="w-2 h-2 bg-gray-400 rounded-full"
                />
              </div>
            ) : (
              <ReactMarkdown
                className={clsx(
                  'prose prose-sm max-w-none',
                  role === 'user' && 'prose-invert',
                )}
                components={{
                  code({ className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match;
                    return !isInline ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus as any}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {content}
              </ReactMarkdown>
            )}
          </div>

          <span className={clsx(
            'text-xs text-gray-400 mt-1',
            role === 'user' ? 'text-right mr-2' : 'ml-2',
          )}>
            {dateUtils.format(timestamp, 'HH:mm')}
          </span>
        </div>
      </div>
    </motion.div>
  );
}