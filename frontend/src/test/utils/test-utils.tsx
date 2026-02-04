/**
 * Enhanced Test Utilities
 * Comprehensive testing utilities with providers and helpers
 */

import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline } from '@mui/material'
import userEvent from '@testing-library/user-event'
import { vi, MockedFunction } from 'vitest'

import { lightTheme } from '../../theme/modernTheme'
import { AuthProvider } from '../../context/AuthProvider'

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
  })
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={lightTheme}>
          <CssBaseline />
          <MockAuthProvider user={user}>
            {children}
          </MockAuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  user?: MockUser
  queryClient?: QueryClient
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { user, queryClient, ...renderOptions } = options

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <AllProviders user={user} queryClient={queryClient}>
      {children}
    </AllProviders>
  )

  return render(ui, { wrapper: Wrapper, ...renderOptions })
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

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }
export { vi } from 'vitest'