/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * Test Setup Configuration
 * 
 * Bu dosya tüm testler için gerekli setup'ları içerir
 */

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

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

// Mock fetch
global.fetch = vi.fn()

// Mock WebSocket
const WebSocketMock = vi.fn().mockImplementation(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1,
}))

// Add static properties to the mock constructor
Object.assign(WebSocketMock, {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
})

global.WebSocket = WebSocketMock as any

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

// Setup test environment variables
process.env.NODE_ENV = 'test'
process.env.VITE_API_BASE_URL = 'http://localhost:8000'
process.env.VITE_WS_URL = 'ws://localhost:8000'