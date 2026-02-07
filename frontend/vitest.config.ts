/// <reference types="vitest" />
import path from 'path';

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text-summary', 'json', 'html'],
      reportsDirectory: './coverage',

      // Include patterns
      include: [
        'src/**/*.{ts,tsx}',
        '!src/**/*.d.ts',
        '!src/main.tsx',
        '!src/vite-env.d.ts',
      ],

      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/test-utils.tsx',
        '**/__tests__/**',
        '**/__mocks__/**',
        'src/styles/',
        'coverage/',
        'dist/',
        '*.config.{js,ts}',
        'src/types.ts',
        'src/types/',
        'src/sw.ts',
        'src/utils/performance.tsx',
        'src/utils/performanceOptimizer.tsx',
      ],

      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
        // Critical components require higher coverage
        'src/components/ui/': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/components/Exam/': {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        'src/components/Auth/': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        'src/services/': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
        'src/hooks/': {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
        'src/utils/': {
          branches: 75,
          functions: 75,
          lines: 75,
          statements: 75,
        },
        // WCAG/Accessibility specific thresholds
        'src/components/Accessibility/': {
          branches: 75,
          functions: 75,
          lines: 75,
          statements: 75,
        },
        'src/utils/wcagValidator.ts': {
          branches: 85,
          functions: 85,
          lines: 85,
          statements: 85,
        },
      },

      // Watermarks for coverage colors
      watermarks: {
        statements: [80, 95],
        functions: [80, 95],
        branches: [80, 95],
        lines: [80, 95],
      },
    },
    // ========== MEMORY OPTIMIZATION (3 Şubat 2026) ==========
    // Sorun: 95 test dosyası × forks × isolate = ~48GB teorik memory
    // Çözüm v2: forks + memory limit + maxWorkers sınırlaması
    // Not: threads + isolate:false mock sorunlarına neden oldu
    pool: 'forks',
    isolate: true,             // Test izolasyonu korunuyor
    maxWorkers: 2,             // Sadece 2 paralel worker (memory için)
    minWorkers: 1,

    poolOptions: {
      forks: {
        singleFork: false,     // Paralel çalışabilir
        isolate: true,
        memoryLimit: '512MB',  // Her fork max 512MB
      }
    },

    // Dosya paralelliğini sınırla
    fileParallelism: true,
    // ==========================================================

    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,

    // Reporter configuration (lightweight for speed)
    reporter: ['default'],

    // Mock configuration
    deps: {
      optimizer: {
        web: {
          include: ['@testing-library/jest-dom'],
        },
      },
    },

    // Environment variables for tests
    env: {
      NODE_ENV: 'test',
      VITE_API_BASE_URL: 'http://localhost:8000',
      VITE_WS_URL: 'ws://localhost:8000',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});