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

// FAZ-8: Register offline sync handler
registerOnlineSync();

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
