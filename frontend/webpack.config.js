/**
 * KIRO2 Frontend Webpack Configuration
 * Advanced optimization for Turkish educational platform
 */

const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const WorkboxPlugin = require('workbox-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';
const isAnalyze = process.env.ANALYZE === 'true';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  
  entry: {
    main: './src/index.tsx',
    // Separate entry for service worker
    sw: './src/sw.ts'
  },
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isProduction ? 'js/[name].[contenthash:8].js' : 'js/[name].js',
    chunkFilename: isProduction ? 'js/[name].[contenthash:8].chunk.js' : 'js/[name].chunk.js',
    publicPath: '/',
    clean: true,
    // Enable cross-origin loading for chunks
    crossOriginLoading: 'anonymous',
  },
  
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx', '.json'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@pages': path.resolve(__dirname, 'src/pages'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@hooks': path.resolve(__dirname, 'src/hooks'),
      '@services': path.resolve(__dirname, 'src/services'),
      '@styles': path.resolve(__dirname, 'src/styles'),
      '@assets': path.resolve(__dirname, 'src/assets'),
    },
    // Fallbacks for Node.js polyfills (if needed)
    fallback: {
      "crypto": require.resolve("crypto-browserify"),
      "buffer": require.resolve("buffer"),
      "stream": require.resolve("stream-browserify"),
      "util": require.resolve("util"),
    }
  },
  
  module: {
    rules: [
      // TypeScript/JavaScript
      {
        test: /\.(ts|tsx|js|jsx)$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', {
                  targets: {
                    browsers: ['> 1%', 'last 2 versions', 'not dead']
                  },
                  modules: false,
                  useBuiltIns: 'usage',
                  corejs: 3
                }],
                ['@babel/preset-react', {
                  runtime: 'automatic',
                  development: !isProduction
                }],
                '@babel/preset-typescript'
              ],
              plugins: [
                // Production optimizations
                isProduction && ['babel-plugin-transform-remove-prop-types', { removeImport: true }],
                isProduction && 'babel-plugin-transform-react-remove-prop-types',
                // Dynamic imports
                '@babel/plugin-syntax-dynamic-import',
                // Class properties
                '@babel/plugin-proposal-class-properties',
                // Async/await
                '@babel/plugin-transform-runtime',
                // React optimization
                !isProduction && 'react-hot-loader/babel',
              ].filter(Boolean),
              cacheDirectory: true,
            }
          }
        ]
      },
      
      // CSS Modules and regular CSS
      {
        test: /\.css$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          {
            loader: 'css-loader',
            options: {
              modules: {
                auto: true,
                localIdentName: isProduction ? '[hash:base64:5]' : '[local]--[hash:base64:5]'
              },
              importLoaders: 1,
            }
          },
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  'tailwindcss',
                  'autoprefixer',
                  ...(isProduction ? ['cssnano'] : [])
                ]
              }
            }
          }
        ]
      },
      
      // SCSS/Sass
      {
        test: /\.(scss|sass)$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          'css-loader',
          'postcss-loader',
          'sass-loader'
        ]
      },
      
      // Images
      {
        test: /\.(png|jpe?g|gif|svg|webp|avif)$/i,
        type: 'asset',
        generator: {
          filename: 'images/[name].[contenthash:8][ext]'
        },
        parser: {
          dataUrlCondition: {
            maxSize: 8192 // 8KB
          }
        }
      },
      
      // Fonts
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[contenthash:8][ext]'
        }
      },
      
      // Videos
      {
        test: /\.(mp4|webm|ogg|mp3|wav|flac|aac)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'media/[name].[contenthash:8][ext]'
        }
      }
    ]
  },
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      // JavaScript minification
      new TerserPlugin({
        terserOptions: {
          parse: {
            ecma: 8,
          },
          compress: {
            ecma: 5,
            warnings: false,
            comparisons: false,
            inline: 2,
            drop_console: isProduction,
            drop_debugger: isProduction,
            pure_funcs: isProduction ? ['console.log', 'console.info'] : [],
            passes: 2
          },
          mangle: {
            safari10: true,
          },
          output: {
            ecma: 5,
            comments: false,
            ascii_only: true,
          },
        },
        parallel: true,
        extractComments: false,
      }),
      
      // CSS minification
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: ['default', {
            discardComments: { removeAll: true },
            normalizeUnicode: false // Keep Turkish characters
          }]
        }
      })
    ],
    
    // Code splitting strategy
    splitChunks: {
      chunks: 'all',
      minSize: 20000,
      maxSize: 250000,
      cacheGroups: {
        // Vendor libraries
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          chunks: 'all',
        },
        
        // React ecosystem
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom|react-router)[\\/]/,
          name: 'react',
          priority: 20,
          chunks: 'all',
        },
        
        // UI libraries
        ui: {
          test: /[\\/]node_modules[\\/](@mui|@emotion|framer-motion)[\\/]/,
          name: 'ui',
          priority: 15,
          chunks: 'all',
        },
        
        // Utilities
        utils: {
          test: /[\\/]node_modules[\\/](axios|dayjs|lodash|formik|yup)[\\/]/,
          name: 'utils',
          priority: 12,
          chunks: 'all',
        },
        
        // Charts and visualization
        charts: {
          test: /[\\/]node_modules[\\/](recharts|d3|chart\.js)[\\/]/,
          name: 'charts',
          priority: 13,
          chunks: 'all',
        },
        
        // Common components
        common: {
          name: 'common',
          minChunks: 2,
          priority: 5,
          chunks: 'all',
          reuseExistingChunk: true,
        }
      }
    },
    
    // Runtime chunk
    runtimeChunk: 'single',
    
    // Module IDs
    moduleIds: isProduction ? 'deterministic' : 'named',
    chunkIds: isProduction ? 'deterministic' : 'named',
  },
  
  plugins: [
    // HTML template
    new HtmlWebpackPlugin({
      template: './public/index.html',
      favicon: './public/favicon.ico',
      inject: true,
      minify: isProduction ? {
        removeComments: true,
        collapseWhitespace: true,
        removeRedundantAttributes: true,
        useShortDoctype: true,
        removeEmptyAttributes: true,
        removeStyleLinkTypeAttributes: true,
        keepClosingSlash: true,
        minifyJS: true,
        minifyCSS: true,
        minifyURLs: true,
      } : false,
      // Turkish meta tags
      templateParameters: {
        lang: 'tr',
        title: 'KIRO2 - Türkiye Üniversite Sınavları Hazırlık Platformu',
        description: 'AI destekli kişiselleştirilmiş eğitim platformu',
        keywords: 'YKS, TYT, AYT, üniversite sınavı, eğitim, AI',
      }
    }),
    
    // CSS extraction
    isProduction && new MiniCssExtractPlugin({
      filename: 'css/[name].[contenthash:8].css',
      chunkFilename: 'css/[name].[contenthash:8].chunk.css',
    }),
    
    // Environment variables
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
      'process.env.REACT_APP_API_URL': JSON.stringify(process.env.REACT_APP_API_URL || 'http://localhost:8000/api'),
      'process.env.REACT_APP_WS_URL': JSON.stringify(process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws'),
      'process.env.REACT_APP_VERSION': JSON.stringify(process.env.npm_package_version),
    }),
    
    // Provide Node.js globals for browser
    new webpack.ProvidePlugin({
      Buffer: ['buffer', 'Buffer'],
      process: 'process/browser',
    }),
    
    // Compression for production
    isProduction && new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 8192,
      minRatio: 0.8,
    }),
    
    // Progressive Web App
    isProduction && new WorkboxPlugin.GenerateSW({
      clientsClaim: true,
      skipWaiting: true,
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/fonts\.googleapis\.com/,
          handler: 'StaleWhileRevalidate',
          options: {
            cacheName: 'google-fonts-stylesheets',
          }
        },
        {
          urlPattern: /^https:\/\/fonts\.gstatic\.com/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'google-fonts-webfonts',
            expiration: {
              maxEntries: 30,
              maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
            }
          }
        },
        {
          urlPattern: /^https:\/\/api\./,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 60 * 5, // 5 minutes
            }
          }
        },
        {
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|avif)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'images',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
            }
          }
        }
      ]
    }),
    
    // Bundle analyzer (only when ANALYZE=true)
    isAnalyze && new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: true,
      reportFilename: 'bundle-analysis.html'
    }),
    
    // Progress plugin for development
    !isProduction && new webpack.ProgressPlugin(),
    
  ].filter(Boolean),
  
  devtool: isProduction ? 'source-map' : 'eval-source-map',
  
  devServer: {
    port: 3000,
    host: 'localhost',
    hot: true,
    open: true,
    historyApiFallback: true,
    compress: true,
    static: {
      directory: path.resolve(__dirname, 'public'),
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      }
    },
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    // Turkish locale support
    headers: {
      'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'
    }
  },
  
  performance: {
    maxEntrypointSize: 512000, // 500KB
    maxAssetSize: 512000, // 500KB
    hints: isProduction ? 'warning' : false,
  },
  
  stats: {
    colors: true,
    modules: false,
    children: false,
    chunks: false,
    chunkModules: false,
    entrypoints: false,
    // Show Turkish characters properly
    outputPath: true,
  },
  
  // Experiments
  experiments: {
    // Enable top-level await
    topLevelAwait: true,
  },
  
  // Cache configuration
  cache: {
    type: 'filesystem',
    buildDependencies: {
      config: [__filename],
    },
    cacheDirectory: path.resolve(__dirname, 'node_modules/.cache/webpack'),
  },
};