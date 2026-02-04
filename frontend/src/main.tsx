/**
 * Main Entry Point
 *
 * This is the application entry point loaded by index.html
 * Renders the App component into the DOM
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './app'
import './styles.css'

const root = ReactDOM.createRoot(document.getElementById('root')!)

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
