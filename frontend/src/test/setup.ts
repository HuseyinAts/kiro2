/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * Test Setup Configuration
 * 
 * Bu dosya tüm testler için gerekli setup'ları içerir
 */

import '@testing-library/jest-dom'
import { vi, expect, describe, it, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'

// Jest compatibility - expose jest globals for tests that use jest.fn(), etc.
// @ts-expect-error - Adding jest global for backwards compatibility
globalThis.jest = {
  fn: vi.fn,
  spyOn: vi.spyOn,
  mock: vi.mock,
  clearAllMocks: vi.clearAllMocks,
  resetAllMocks: vi.resetAllMocks,
  restoreAllMocks: vi.restoreAllMocks,
  useFakeTimers: vi.useFakeTimers,
  useRealTimers: vi.useRealTimers,
  advanceTimersByTime: vi.advanceTimersByTime,
  runAllTimers: vi.runAllTimers,
  runOnlyPendingTimers: vi.runOnlyPendingTimers,
  clearAllTimers: vi.clearAllTimers,
  setSystemTime: vi.setSystemTime,
  getMockedSystemTime: vi.getMockedSystemTime,
  getRealSystemTime: vi.getRealSystemTime,
  isMockFunction: vi.isMockFunction,
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
} as any

// Mock ResizeObserver - proper class-based mock
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
} as any

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
} as Storage
global.localStorage = localStorageMock

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
} as Storage
global.sessionStorage = sessionStorageMock

// Mock fetch with default success response
// Supports both vitest (vi.fn) and jest-style (mockResolvedValue) patterns
const fetchMock = vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: async () => ({}),
  text: async () => '',
  blob: async () => new Blob(),
  headers: new Headers(),
});
global.fetch = fetchMock;

// Mock WebSocket - use function constructor to avoid vitest/tinyspy wrapping issues
// @ts-expect-error - Intentionally using function constructor for compatibility
function MockWebSocket(this: any, url: string, _protocols?: string | string[]) {
  this.url = url
  this.readyState = 1 // OPEN
  this.onopen = null
  this.onclose = null
  this.onmessage = null
  this.onerror = null

  // Simulate connection opening
  setTimeout(() => {
    if (this.onopen) {
      this.onopen(new Event('open'))
    }
  }, 0)

  this.send = function(_data: string) {}
  this.close = function() {
    if (this.onclose) this.onclose()
  }
  this.addEventListener = function() {}
  this.removeEventListener = function() {}
}
MockWebSocket.CONNECTING = 0
MockWebSocket.OPEN = 1
MockWebSocket.CLOSING = 2
MockWebSocket.CLOSED = 3

global.WebSocket = MockWebSocket as any

// Mock canvas context
HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({ data: new Array(4) })),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => ({ data: new Array(4) })),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn(),
})

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url')
global.URL.revokeObjectURL = vi.fn()

// Mock console methods for cleaner test output
global.console = {
  ...console,
  // Suppress console.log in tests unless needed
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
}

// Mock Web Speech API (SpeechSynthesisUtterance)
class SpeechSynthesisUtteranceMock {
  text: string
  lang: string
  rate: number
  pitch: number
  volume: number
  voice: any

  constructor(text = '') {
    this.text = text
    this.lang = 'tr-TR'
    this.rate = 1
    this.pitch = 1
    this.volume = 1
    this.voice = null
  }
}

global.SpeechSynthesisUtterance = SpeechSynthesisUtteranceMock as any

// Mock speechSynthesis
global.speechSynthesis = {
  speak: vi.fn(),
  cancel: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  getVoices: vi.fn(() => []),
  speaking: false,
  pending: false,
  paused: false,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(() => true),
} as any

// Mock Fullscreen API
Element.prototype.requestFullscreen = vi.fn().mockResolvedValue(undefined)
document.exitFullscreen = vi.fn().mockResolvedValue(undefined)

Object.defineProperty(document, 'fullscreenElement', {
  writable: true,
  configurable: true,
  value: null
})

Object.defineProperty(document, 'fullscreenEnabled', {
  writable: true,
  configurable: true,
  value: true
})

// Mock Notification API
global.Notification = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
})) as any

Object.assign(global.Notification, {
  permission: 'granted',
  requestPermission: vi.fn().mockResolvedValue('granted'),
})

// Mock MediaDevices (for camera/microphone access)
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  configurable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [],
      getVideoTracks: () => [],
      getAudioTracks: () => [],
      addTrack: vi.fn(),
      removeTrack: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }),
    enumerateDevices: vi.fn().mockResolvedValue([]),
  },
})

// Mock Clipboard API
Object.defineProperty(navigator, 'clipboard', {
  writable: true,
  configurable: true,
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
    readText: vi.fn().mockResolvedValue(''),
    write: vi.fn().mockResolvedValue(undefined),
    read: vi.fn().mockResolvedValue([]),
  },
})

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn()

// Mock window.alert, confirm, prompt (jsdom not implemented)
window.alert = vi.fn()
window.confirm = vi.fn(() => true)
window.prompt = vi.fn(() => '')

// Mock HTMLMediaElement for video/audio tests (jsdom limitation)
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  configurable: true,
  writable: true,
  value: vi.fn().mockImplementation(() => Promise.resolve()),
})

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  configurable: true,
  writable: true,
  value: vi.fn(),
})

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  configurable: true,
  writable: true,
  value: vi.fn(),
})

Object.defineProperty(HTMLMediaElement.prototype, 'addTextTrack', {
  configurable: true,
  writable: true,
  value: vi.fn(),
})

// Mock video element properties
Object.defineProperty(HTMLVideoElement.prototype, 'canPlayType', {
  configurable: true,
  writable: true,
  value: vi.fn(() => 'maybe'),
})

// Setup test environment variables
process.env.NODE_ENV = 'test'
process.env.VITE_API_BASE_URL = 'http://localhost:8000'
process.env.VITE_WS_URL = 'ws://localhost:8000'

// Global error handler to suppress React concurrent mode errors
window.onerror = function(message) {
  if (typeof message === 'string' && message.includes('Should not already be working')) {
    return true
  }
  return false
}

// MSW Server Setup
import { server } from './mocks/server'

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
