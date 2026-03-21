/**
 * Main Entry Point
 *
 * This is the application entry point loaded by index.html
 * Renders the App component into the DOM
 */

import axios from 'axios';
import * as React from 'react';
import * as ReactDOM from 'react-dom/client';

import { App } from './App';
import { registerOnlineSync } from './db/kiro2DB';
import './styles.css';

// Global axios defaults — ensures all direct axios calls send cookies
axios.defaults.withCredentials = true;

// Global fetch override — auto-add credentials for same-origin API calls
// Covers 100+ fetch() calls across the codebase without individual edits
const _originalFetch = window.fetch;
window.fetch = function (input: RequestInfo | URL, init?: RequestInit) {
  const url =
    typeof input === 'string'
      ? input
      : input instanceof Request
        ? input.url
        : input.toString();
  // Only add credentials for same-origin requests (starts with /)
  // Avoids CORS issues with external APIs (Khan, EBA, etc.)
  if (url.startsWith('/') || url.startsWith(window.location.origin)) {
    init = { ...init };
    if (!init.credentials) {
      init.credentials = 'include';
    }
  }
  return _originalFetch.call(window, input, init);
};

// FAZ-8: Register offline sync handler
registerOnlineSync();

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
