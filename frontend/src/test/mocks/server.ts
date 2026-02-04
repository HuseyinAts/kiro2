/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * MSW Server Setup
 * 
 * Test ortamı için mock server konfigürasyonu
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Mock server'ı kur
export const server = setupServer(...handlers)

// Test utilities
export const resetHandlers = () => server.resetHandlers()
export const restoreHandlers = () => server.restoreHandlers()

// Server lifecycle
export const startServer = () => server.listen({ onUnhandledRequest: 'error' })
export const stopServer = () => server.close()

// Custom handlers for specific tests
export const addHandler = (handler: any) => server.use(handler)
export const addHandlers = (handlers: any[]) => server.use(...handlers)