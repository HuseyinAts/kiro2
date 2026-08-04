import React from 'react';
import { renderToString } from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const tests = [
  '$A(1, 2)$ noktası',
  '$A(1,2)$noktası',
  '$\\triangle ABC$',
  '\\frac{26}{33}',
  '\\$A(1, 2)\\$ noktası'
];

tests.forEach(t => {
  const element = React.createElement(ReactMarkdown, {
    remarkPlugins: [[remarkMath, { singleDollarTextMath: true }]],
    rehypePlugins: [[rehypeKatex, { strict: false, trust: true, throwOnError: false }]],
  }, t);
  console.log(`\n--- Test: ${t} ---`);
  console.log(renderToString(element));
});
