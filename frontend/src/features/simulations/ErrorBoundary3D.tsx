/**
 * ErrorBoundary3D — Catches Three.js / WebGL errors gracefully
 * FAZ-6: 3D Simulasyon Modüller
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary3D extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[3D Sim] Render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center rounded-2xl bg-gray-100 p-8 gap-3 text-center">
          <span className="text-4xl">🔧</span>
          <p className="text-sm font-semibold text-gray-600">3D simülasyon yüklenemedi</p>
          <p className="text-xs text-gray-400">
            Tarayıcınız WebGL desteklemiyor olabilir.
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="text-xs px-3 py-1.5 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700 transition-colors"
          >
            Tekrar Dene
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary3D;
