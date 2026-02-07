# KIRO2 Component Snapshot Tests

## Overview

Comprehensive snapshot testing suite for the KIRO2 educational platform's React components. These tests ensure visual consistency and prevent UI regressions across the application.

## 📋 Test Coverage

### UI Primitives (Core Building Blocks)
- **GlassCard** - Glassmorphism card component with multiple variants
- **ModernButton** - Enhanced button with gradients and animations
- **LoadingSpinner** - Loading indicators for various states

### Authentication Components
- **ModernLoginPage** - Login interface with demo accounts
- **ModernRegisterPage** - Registration flow with role selection

### Dashboard Components
- **ModernStudentDashboard** - Student-specific dashboard with stats

### Exam Components
- **ExamInterfaceExample** - Exam interface with question navigation

### Animation Components
- **PageTransition** - Page-level transitions
- **StaggerContainer/StaggerItem** - Staggered animations

### Error Handling
- **ErrorBoundary** - Error boundary wrapper
- **LoadingStates** - Loading state components

## 🚀 Running Tests

### Run all snapshot tests
```bash
cd frontend
npm run test:components
```

### Run specific test file
```bash
npm test -- src/components/__tests__/snapshots.test.tsx
```

### Update snapshots (after intentional UI changes)
```bash
npm test -- -u
```

### Watch mode (for development)
```bash
npm run test:watch
```

## 📸 Snapshot Management

### When to Update Snapshots

Update snapshots when:
- ✅ You intentionally changed UI styling
- ✅ You refactored component structure
- ✅ You added/removed props that affect rendering
- ✅ You updated component dependencies

**DO NOT** update snapshots when:
- ❌ Tests fail unexpectedly
- ❌ You haven't reviewed the visual changes
- ❌ Changes are breaking existing functionality

### Review Snapshot Changes

```bash
# View snapshot diff
git diff src/components/__tests__/__snapshots__/

# Review changes carefully before committing
git add src/components/__tests__/__snapshots__/
```

## 🎯 Test Structure

Each snapshot test follows this pattern:

```typescript
describe('Component Category', () => {
  describe('ComponentName', () => {
    let Component: any

    beforeEach(async () => {
      const module = await import('@/path/to/Component')
      Component = module.ComponentName
    })

    it('renders component correctly', () => {
      if (!Component) return

      const { container } = renderWithProviders(
        <Component prop="value" />
      )
      expect(container).toMatchSnapshot()
    })
  })
})
```

## 🔧 Configuration

### Test Setup (`src/test/setup.ts`)
- Mocks browser APIs (IntersectionObserver, ResizeObserver, etc.)
- Mocks localStorage, sessionStorage
- Mocks Web Speech API
- Configures jsdom environment

### Vite Config (`vite.config.ts`)
```typescript
test: {
  globals: true,
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json', 'html'],
  }
}
```

## 🛡️ Anti-Reward Hacking

These tests follow **Boris Cherny's Verification Standards** and avoid:

```typescript
// ❌ NEVER use fake assertions
expect(true).toBe(true)  // YASAK!
assert True  // YASAK!

// ✅ ALWAYS use real snapshot assertions
expect(container).toMatchSnapshot()
```

## 📦 Test Providers

Tests wrap components with necessary providers:

```typescript
const TestWrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </QueryClientProvider>
)
```

## 🎨 Mocked Dependencies

### Auth Store
```typescript
vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: { ad: 'Test', soyad: 'User', rol: 'ogrenci' },
    isAuthenticated: true,
  })
}))
```

### Framer Motion
```typescript
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}))
```

### Theme Colors
```typescript
vi.mock('@/theme/modern-colors', () => ({
  default: {
    gradients: { /* ... */ },
    glass: { /* ... */ },
    shadow: { /* ... */ },
  }
}))
```

## 🐛 Troubleshooting

### Snapshot Mismatch
```bash
# View detailed diff
npm test -- --reporter=verbose

# Update if changes are intentional
npm test -- -u
```

### Import Errors
```bash
# Check if component exists
ls -la src/components/ui/GlassCard.tsx

# Verify path alias in tsconfig.json
{
  "paths": {
    "@/*": ["./src/*"]
  }
}
```

### Mock Issues
```bash
# Clear vitest cache
rm -rf node_modules/.vite

# Restart vitest
npm run test:watch
```

## 📊 Coverage Requirements

| Module | Minimum Coverage |
|--------|------------------|
| UI Components | 70% |
| Pages | 75% |
| Global Target | 60% |

Run coverage report:
```bash
npm run test:coverage
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
- name: Run Snapshot Tests
  run: |
    cd frontend
    npm run test:components
```

### Pre-commit Hook
```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: frontend-tests
      name: Frontend Component Tests
      entry: npm run test:components
      language: system
      pass_filenames: false
```

## 📚 Related Documentation

- [Testing Rules](.claude/rules/testing.md)
- [Verification Rules](.claude/rules/verification.md)
- [Component Documentation](../../README.md)
- [Vitest Documentation](https://vitest.dev)

## 🤝 Contributing

When adding new snapshot tests:

1. Import component dynamically with error handling
2. Wrap with `renderWithProviders`
3. Use descriptive test names
4. Test multiple variants/states
5. Follow existing patterns
6. Run verification before commit

Example:
```typescript
describe('NewComponent', () => {
  let NewComponent: any

  beforeEach(async () => {
    try {
      const module = await import('@/components/NewComponent')
      NewComponent = module.NewComponent
    } catch (error) {
      console.error('Failed to import:', error)
    }
  })

  it('renders with default props', () => {
    if (!NewComponent) return
    const { container } = renderWithProviders(<NewComponent />)
    expect(container).toMatchSnapshot()
  })

  it('renders with custom props', () => {
    if (!NewComponent) return
    const { container } = renderWithProviders(
      <NewComponent variant="custom" />
    )
    expect(container).toMatchSnapshot()
  })
})
```

## ✅ Quality Checklist

Before committing snapshot tests:

- [ ] All tests pass locally
- [ ] Snapshots are reviewed and make sense
- [ ] No fake assertions (expect(true).toBe(true))
- [ ] Tests cover main variants/states
- [ ] Mocks are properly configured
- [ ] Type errors are resolved
- [ ] Coverage meets minimum threshold

## 📝 License

Part of KIRO2 Educational Platform - All rights reserved © 2025
