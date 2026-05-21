import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { visualizer } from 'rollup-plugin-visualizer'
import path from 'path'

export default defineConfig({
  plugins: [
    react({
      // Fast Refresh için optimize edilmiş ayarlar
      fastRefresh: true,
      jsxImportSource: 'react'
    }),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        globIgnores: ['**/stats.html', '**/node_modules/**'],
        maximumFileSizeToCacheInBytes: 10 * 1024 * 1024, // 10MB limit
        // Cache API responses for offline use
        runtimeCaching: [
          {
            urlPattern: /^\/api\/realms\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'kiro2-realms-cache',
              expiration: { maxAgeSeconds: 60 * 60 * 24 }, // 24h
            },
          },
          {
            urlPattern: /^\/api\/gamification\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'kiro2-gamification-cache',
              expiration: { maxAgeSeconds: 60 * 30 }, // 30m
            },
          },
          {
            urlPattern: /^\/static\/crops\//,
            handler: 'CacheFirst',
            options: {
              cacheName: 'kiro2-question-images',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 7 }, // 7d
            },
          },
        ],
      },
      manifest: {
        name: 'KIRO2 YKS Hazırlık',
        short_name: 'KIRO2',
        description: 'Yapay zeka destekli YKS/TYT/AYT hazırlık platformu',
        theme_color: '#667EEA',
        background_color: '#0F172A',
        display: 'standalone',
        orientation: 'portrait-primary',
        start_url: '/dashboard',
        scope: '/',
        lang: 'tr',
        categories: ['education'],
        icons: [
          { src: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512x512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512x512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
        shortcuts: [
          {
            name: 'Sınav Başlat',
            url: '/exam/start',
            description: 'Hızlıca sınav başlat',
          },
          {
            name: 'Alemler',
            url: '/realms',
            description: 'Konu alemlerini keşfet',
          },
        ],
      },
      devOptions: {
        enabled: false,
      },
    }),
    // Bundle analyzer (only in build mode)
    visualizer({
      filename: './dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap', // Options: treemap, sunburst, network
    })
  ],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/',
        'coverage/',
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.NODE_ENV === 'development',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: process.env.NODE_ENV === 'production',
        drop_debugger: true,
        pure_funcs: process.env.NODE_ENV === 'production' ? ['console.log', 'console.info'] : [],
      },
      mangle: {
        safari10: false,
      },
    },
    rollupOptions: {
      output: {
        // S179 fix (B-P0-63 + B-P0-61): grouped manualChunks.
        //
        // Pre-fix `manualChunks: undefined` produced 188 separate MUI icon
        // chunks (each ~0.2 KB) → HTTP overhead even on HTTP/2; auto
        // code-split also let `refractor` blow chatService chunk to 611 KB.
        //
        // We group: mui-icons together (was 188 chunks → 1), mui-core,
        // recharts+d3 into 'charts', react-router into 'router'. App
        // chunks stay auto-split by route.
        //
        // KIRO2 lesson (Session 74): keep `react` itself in the entry
        // bundle, NOT in a vendor chunk — splitting React across chunks
        // breaks createContext order. Hence no react/react-dom group.
        manualChunks: (id: string) => {
          if (id.includes('node_modules/@mui/icons-material')) {
            return 'mui-icons';
          }
          if (id.includes('node_modules/@mui')) {
            return 'mui-core';
          }
          if (
            id.includes('node_modules/recharts') ||
            id.includes('node_modules/d3-')
          ) {
            return 'charts';
          }
          if (
            id.includes('node_modules/react-router') ||
            id.includes('node_modules/@remix-run')
          ) {
            return 'router';
          }
          return undefined;
        },
        // Chunk dosya isimlendirme
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name!.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `images/[name]-[hash][extname]`;
          }
          if (/css/i.test(ext)) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
      // External dependencies (CDN'den yüklenecekler)
      external: process.env.NODE_ENV === 'production' ? [] : [],
    },
    // Chunk size optimizasyonu
    chunkSizeWarningLimit: 500, // 500KB uyarı limiti
    // CSS code splitting
    cssCodeSplit: true,
    // Asset inlining threshold
    assetsInlineLimit: 4096, // 4KB altındaki assetler inline edilir
  },
  // Development optimizasyonları
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
      'axios',
      'dayjs',
      'react-query'
    ],
    exclude: [
      // Büyük kütüphaneleri exclude et
      'recharts',
      'framer-motion'
    ]
  },
  server: {
    port: 3001,
    host: true,
    // HMR optimizasyonu - React Router için
    hmr: {
      overlay: false,
      clientPort: 3001,
    },
    // Proxy konfigürasyonu - Backend port 8000
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        timeout: 120000,
        proxyTimeout: 120000,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    },
    // File watching optimizasyonu
    watch: {
      usePolling: false,
      interval: 100,
    },
  },
  preview: {
    port: 3001,
    // Preview server optimizasyonları
    headers: {
      'Cache-Control': 'public, max-age=31536000',
    },
  },
  // CSS optimizasyonları
  css: {
    devSourcemap: process.env.NODE_ENV === 'development',
    preprocessorOptions: {}
  },
  // JSON optimizasyonu
  json: {
    namedExports: true,
    stringify: false,
  },
  // Worker optimizasyonu
  worker: {
    format: 'es',
    plugins: () => [react()]
  }
})