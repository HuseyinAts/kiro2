/**
 * Enhanced Test Utilities
 * Comprehensive testing utilities with providers and helpers
 */

import * as React from 'react';
import {  ReactElement, ReactNode, createContext, useContext  } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter, MemoryRouter, MemoryRouterProps } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import userEvent from '@testing-library/user-event'
import { vi, MockedFunction } from 'vitest'

import { lightTheme } from '../../theme/modernTheme'
import { AuthProvider } from '../../context/AuthProvider'

// ============================================
// Mock Accessibility Context (Task #71)
// ============================================
interface MockAccessibilitySettings {
  fontSize: 'small' | 'medium' | 'large' | 'extra-large'
  highContrast: boolean
  reducedMotion: boolean
  dyslexiaSupport: boolean
  motorImpairmentSupport: boolean
  screenReaderOptimized: boolean
}

interface MockAccessibilityContextType {
  settings: MockAccessibilitySettings
  updateSetting: (key: keyof MockAccessibilitySettings, value: any) => void
  toggleHighContrast: () => void
  toggleReducedMotion: () => void
  increaseFontSize: () => void
  decreaseFontSize: () => void
  announce: (message: string, priority?: 'polite' | 'assertive') => void
}

const defaultAccessibilitySettings: MockAccessibilitySettings = {
  fontSize: 'medium',
  highContrast: false,
  reducedMotion: false,
  dyslexiaSupport: false,
  motorImpairmentSupport: false,
  screenReaderOptimized: false,
}

const MockAccessibilityContext = createContext<MockAccessibilityContextType | null>(null)

export const MockAccessibilityProvider: React.FC<{
  children: React.ReactNode
  settings?: Partial<MockAccessibilitySettings>
}> = ({ children, settings = {} }) => {
  const value: MockAccessibilityContextType = {
    settings: { ...defaultAccessibilitySettings, ...settings },
    updateSetting: vi.fn(),
    toggleHighContrast: vi.fn(),
    toggleReducedMotion: vi.fn(),
    increaseFontSize: vi.fn(),
    decreaseFontSize: vi.fn(),
    announce: vi.fn(),
  }

  return (
    <MockAccessibilityContext.Provider value={value}>
      {children}
    </MockAccessibilityContext.Provider>
  )
}

// Hook for tests that need accessibility context
export const useMockAccessibility = () => {
  const context = useContext(MockAccessibilityContext)
  if (!context) {
    throw new Error('useMockAccessibility must be used within MockAccessibilityProvider')
  }
  return context
}

// Mock user context
interface MockUser {
  id: string
  username: string
  email: string
  role: 'student' | 'teacher' | 'parent' | 'admin'
  firstName: string
  lastName: string
}

const mockUser: MockUser = {
  id: '1',
  username: 'test-user',
  email: 'test@example.com',
  role: 'student',
  firstName: 'Test',
  lastName: 'User'
}

// Auth Context Mock
const AuthContext = React.createContext({
  user: mockUser,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
  error: null
})

export const MockAuthProvider: React.FC<{ children: React.ReactNode; user?: MockUser }> = ({ 
  children, 
  user = mockUser 
}) => {
  const value = {
    user,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false,
    error: null
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// All providers wrapper
interface AllProvidersProps {
  children: React.ReactNode
  user?: MockUser
  queryClient?: QueryClient
  routerType?: 'browser' | 'memory' | 'none'
  initialEntries?: string[]
  withAccessibility?: boolean
  accessibilitySettings?: Partial<MockAccessibilitySettings>
}

const AllProviders: React.FC<AllProvidersProps> = ({
  children,
  user = mockUser,
  queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  }),
  routerType = 'browser',
  initialEntries = ['/'],
  withAccessibility = false,
  accessibilitySettings = {},
}) => {
  // Content without Router (for components that have their own Router)
  const innerContent = (
    <ThemeProvider theme={lightTheme}>
      <CssBaseline />
      <MockAuthProvider user={user}>
        {children}
      </MockAuthProvider>
    </ThemeProvider>
  )

  // Wrap with Router if needed
  let content: React.ReactNode
  if (routerType === 'none') {
    // No router wrapper - for App or components with built-in Router
    content = (
      <QueryClientProvider client={queryClient}>
        {innerContent}
      </QueryClientProvider>
    )
  } else if (routerType === 'memory') {
    content = (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          {innerContent}
        </MemoryRouter>
      </QueryClientProvider>
    )
  } else {
    content = (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          {innerContent}
        </BrowserRouter>
      </QueryClientProvider>
    )
  }

  if (withAccessibility) {
    return (
      <MockAccessibilityProvider settings={accessibilitySettings}>
        {content}
      </MockAccessibilityProvider>
    )
  }

  return content
}

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  user?: MockUser
  queryClient?: QueryClient
  routerType?: 'browser' | 'memory'
  initialEntries?: string[]
  withAccessibility?: boolean
  accessibilitySettings?: Partial<MockAccessibilitySettings>
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const {
    user,
    queryClient,
    routerType,
    initialEntries,
    withAccessibility,
    accessibilitySettings,
    ...renderOptions
  } = options

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AllProviders
      user={user}
      queryClient={queryClient}
      routerType={routerType}
      initialEntries={initialEntries}
      withAccessibility={withAccessibility}
      accessibilitySettings={accessibilitySettings}
    >
      {children}
    </AllProviders>
  )

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Convenience render functions for specific scenarios
export const renderWithRouter = (
  ui: ReactElement,
  options: CustomRenderOptions & { initialEntries?: string[] } = {}
) => {
  return customRender(ui, { ...options, routerType: 'memory' })
}

export const renderWithAccessibility = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  return customRender(ui, { ...options, withAccessibility: true })
}

export const renderWithAll = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  return customRender(ui, {
    ...options,
    routerType: 'memory',
    withAccessibility: true,
  })
}

// For App or components that have their own Router
export const renderWithoutRouter = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  return customRender(ui, { ...options, routerType: 'none' })
}

// Test data factories
export const createMockUser = (overrides: Partial<MockUser> = {}): MockUser => ({
  ...mockUser,
  ...overrides
})

export const createMockExam = (overrides: any = {}) => ({
  id: '1',
  title: 'Test Sınavı',
  type: 'TYT',
  subject: 'Matematik',
  duration: 165,
  questionCount: 40,
  status: 'active',
  createdAt: '2024-01-01T00:00:00Z',
  ...overrides
})

export const createMockQuestion = (overrides: any = {}) => ({
  id: '1',
  text: 'Test sorusu?',
  options: ['A', 'B', 'C', 'D'],
  correctAnswer: 0,
  subject: 'Matematik',
  difficulty: 'easy',
  explanation: 'Test açıklaması',
  ...overrides
})

export const createMockExamResult = (overrides: any = {}) => ({
  id: '1',
  examId: '1',
  userId: '1',
  score: 85,
  correctAnswers: 34,
  totalQuestions: 40,
  timeSpent: 120,
  completedAt: '2024-01-01T12:00:00Z',
  subjectScores: {
    'Matematik': { correct: 15, total: 20, percentage: 75 }
  },
  ...overrides
})

// Wait utilities
export const waitForLoadingToFinish = () => 
  new Promise(resolve => setTimeout(resolve, 0))

// Mock localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    })
  }
}

// Mock fetch responses
export const mockFetchResponse = (data: any, ok = true, status = 200) => {
  return Promise.resolve({
    ok,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response)
}

// Error boundary for testing
export class TestErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Test Error Boundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return <div data-testid="error-boundary">Test Error: {this.state.error?.message}</div>
    }

    return this.props.children
  }
}

// Mock users for testing
export const mockUsers = {
  student: {
    id: '1',
    username: 'test-student',
    email: 'student@example.com',
    role: 'student' as const,
    firstName: 'Test',
    lastName: 'Student'
  },
  teacher: {
    id: '2',
    username: 'test-teacher',
    email: 'teacher@example.com',
    role: 'teacher' as const,
    firstName: 'Test',
    lastName: 'Teacher'
  },
  parent: {
    id: '3',
    username: 'test-parent',
    email: 'parent@example.com',
    role: 'parent' as const,
    firstName: 'Test',
    lastName: 'Parent'
  },
  admin: {
    id: '4',
    username: 'test-admin',
    email: 'admin@example.com',
    role: 'admin' as const,
    firstName: 'Test',
    lastName: 'Admin'
  }
}

// Custom render with user event
export const renderWithUser = (ui: ReactElement, options: CustomRenderOptions = {}) => {
  return {
    user: userEvent.setup(),
    ...customRender(ui, options)
  }
}

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }
export { userEvent }
export { vi } from 'vitest'

// Export wrapper components for direct use
export { AllProviders }
export { MockAccessibilityContext }
export { defaultAccessibilitySettings }
export type { MockAccessibilitySettings, MockAccessibilityContextType }