/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_DEBUG: string
  readonly VITE_ENABLE_WEBSOCKET: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_WS_TIMEOUT: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}