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
import { configureKiroApi } from './kiro/api/api-client';
import { registerOnlineSync } from './db/kiro2DB';
import './styles/fonts.css';
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

// KIRO2 Faz 4 — kiro api-client merkezi bootstrap (ekran modül-üstü mock çağrıları kaldırıldı).
// Auth = httpOnly cookie: baseUrl = origin (same-origin) → yukarıdaki fetch override
// credentials:'include' ekler. Mode env ile: VITE_KIRO_API_MODE=mock → dev'de mock (default live).
const _kiroEnv = import.meta.env as unknown as Record<string, string | undefined>;
const _kiroMode: 'mock' | 'live' = _kiroEnv.VITE_KIRO_API_MODE === 'mock' ? 'mock' : 'live';
configureKiroApi({ mode: _kiroMode, baseUrl: window.location.origin });

// FAZ-8: Register offline sync handler
registerOnlineSync();

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
