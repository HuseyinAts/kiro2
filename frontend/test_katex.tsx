import React from 'react';
import { renderToString } from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const text = '$A(1, 2)$ noktası';
const element = React.createElement(ReactMarkdown, {
  remarkPlugins: [[remarkMath, { singleDollarTextMath: true }]],
  rehypePlugins: [[rehypeKatex, { strict: false, trust: true, throwOnError: false }]],
}, text);

console.log(renderToString(element));
