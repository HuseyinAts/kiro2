# KIRO2 Frontend Tests

This directory contains the test suite for the KIRO2 frontend application.

## Test Structure

```
frontend/tests/
├── setup.ts              # Test environment configuration
├── example.test.tsx      # Example tests and patterns
└── README.md             # This file
```

## Running Tests

### Run All Tests
```bash
cd frontend
npm test
```

### Run Tests with Coverage
```bash
npm run test:coverage
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run Specific Test File
```bash
npm test example.test.tsx
```

## Test Patterns

### Component Testing

```typescript
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MyComponent from '../src/components/MyComponent';

it('should render component', () => {
  render(
    <BrowserRouter>
      <MyComponent />
    </BrowserRouter>
  );

  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

### User Interaction Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should handle button click', async () => {
  const user = userEvent.setup();
  render(<Button onClick={handleClick}>Click me</Button>);

  await user.click(screen.getByText('Click me'));

  expect(handleClick).toHaveBeenCalled();
});
```

### API Mocking

```typescript
import { vi } from 'vitest';

it('should fetch data from API', async () => {
  const mockFetch = vi.fn().mockResolvedValue({
    json: async () => ({ data: 'mocked data' }),
  });

  global.fetch = mockFetch;

  // Test your component that uses fetch
  // ...

  expect(mockFetch).toHaveBeenCalledWith('/api/endpoint');
});
```

### Async Testing

```typescript
import { waitFor } from '@testing-library/react';

it('should load data asynchronously', async () => {
  render(<AsyncComponent />);

  await waitFor(() => {
    expect(screen.getByText('Loaded data')).toBeInTheDocument();
  });
});
```

## KIRO2-Specific Test Patterns

### Testing Question Components

```typescript
it('should render ÖSYM-style question', () => {
  const question = {
    id: '1',
    text: 'Aşağıdakilerden hangisi doğrudur?',
    options: [
      { id: 'A', text: 'Seçenek A' },
      { id: 'B', text: 'Seçenek B' },
      { id: 'C', text: 'Seçenek C' },
      { id: 'D', text: 'Seçenek D' },
    ],
    correctAnswer: 'A',
  };

  render(<QuestionCard question={question} />);

  expect(screen.getByText('Aşağıdakilerden hangisi doğrudur?')).toBeInTheDocument();
  expect(screen.getAllByRole('radio')).toHaveLength(4);
});
```

### Testing Exam Timer

```typescript
import { act } from '@testing-library/react';

it('should countdown exam timer', () => {
  vi.useFakeTimers();

  render(<ExamTimer duration={90} />);

  expect(screen.getByText('90:00')).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(60000); // 1 minute
  });

  expect(screen.getByText('89:00')).toBeInTheDocument();

  vi.useRealTimers();
});
```

### Testing Learning Path Progress

```typescript
it('should update progress on topic completion', () => {
  const { rerender } = render(
    <LearningPath completedTopics={5} totalTopics={10} />
  );

  expect(screen.getByText('50%')).toBeInTheDocument();

  rerender(
    <LearningPath completedTopics={7} totalTopics={10} />
  );

  expect(screen.getByText('70%')).toBeInTheDocument();
});
```

### Testing Accessibility Features

```typescript
it('should apply bionic reading', () => {
  render(<BionicText text="This is a test" />);

  const strongElements = screen.getAllByRole('generic');
  expect(strongElements.length).toBeGreaterThan(0);
});

it('should support keyboard navigation', async () => {
  const user = userEvent.setup();
  render(<ExamInterface />);

  await user.keyboard('{Tab}');
  expect(screen.getByRole('button', { name: 'Sonraki' })).toHaveFocus();

  await user.keyboard('{Enter}');
  // Assert next question is shown
});
```

## Test Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Components | 80%+ | TBD |
| Hooks | 90%+ | TBD |
| Utils | 95%+ | TBD |
| Services | 85%+ | TBD |
| Overall | 85%+ | TBD |

## Best Practices

### 1. Test User Behavior, Not Implementation

❌ **Bad:**
```typescript
it('should set loading state to true', () => {
  const { result } = renderHook(() => useData());
  expect(result.current.loading).toBe(true);
});
```

✅ **Good:**
```typescript
it('should show loading spinner while fetching data', () => {
  render(<DataComponent />);
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});
```

### 2. Use Descriptive Test Names

❌ **Bad:**
```typescript
it('works', () => { /* ... */ });
```

✅ **Good:**
```typescript
it('should display error message when login fails with invalid credentials', () => { /* ... */ });
```

### 3. Follow AAA Pattern

```typescript
it('should calculate exam score correctly', () => {
  // Arrange
  const correct = 18;
  const total = 20;

  // Act
  const score = calculateScore(correct, total);

  // Assert
  expect(score).toBe(90);
});
```

### 4. Mock External Dependencies

```typescript
// Mock API calls
vi.mock('../services/api', () => ({
  fetchQuestions: vi.fn().mockResolvedValue([]),
}));

// Mock localStorage
beforeEach(() => {
  localStorage.clear();
  localStorage.setItem('authToken', 'mock-token');
});
```

### 5. Test Error Scenarios

```typescript
it('should handle network errors gracefully', async () => {
  vi.spyOn(console, 'error').mockImplementation(() => {});

  const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));
  global.fetch = mockFetch;

  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText(/hata oluştu/i)).toBeInTheDocument();
  });
});
```

## Accessibility Testing

### Using jest-axe

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Testing Keyboard Navigation

```typescript
it('should navigate with keyboard', async () => {
  const user = userEvent.setup();
  render(<QuestionNavigation />);

  await user.keyboard('{Tab}');
  expect(screen.getByRole('button', { name: /sonraki/i })).toHaveFocus();

  await user.keyboard('{Tab}');
  expect(screen.getByRole('button', { name: /önceki/i })).toHaveFocus();
});
```

## Integration Testing

### Testing Complete User Flows

```typescript
describe('Complete exam flow', () => {
  it('should allow user to complete an exam', async () => {
    const user = userEvent.setup();

    // 1. Start exam
    render(<ExamPage />);
    await user.click(screen.getByRole('button', { name: /sınavı başlat/i }));

    // 2. Answer questions
    await user.click(screen.getByLabelText('A'));
    await user.click(screen.getByRole('button', { name: /sonraki/i }));

    // 3. Submit exam
    await user.click(screen.getByRole('button', { name: /sınavı bitir/i }));
    await user.click(screen.getByRole('button', { name: /onayla/i }));

    // 4. Verify results
    await waitFor(() => {
      expect(screen.getByText(/sonuçlar/i)).toBeInTheDocument();
    });
  });
});
```

## Performance Testing

```typescript
import { renderPerformance } from './utils/performanceUtils';

it('should render quickly', () => {
  const renderTime = renderPerformance(() => {
    render(<HeavyComponent data={largeDataset} />);
  });

  expect(renderTime).toBeLessThan(100); // milliseconds
});
```

## Turkish-Specific Testing

### Testing Turkish Text

```typescript
it('should handle Turkish characters correctly', () => {
  const turkishText = 'Ğğ İı Öö Şş Üü Çç';
  render(<TextComponent text={turkishText} />);
  expect(screen.getByText(turkishText)).toBeInTheDocument();
});
```

### Testing ÖSYM Format

```typescript
it('should format question in ÖSYM style', () => {
  const question = {
    text: 'Aşağıdakilerden hangisi yanlıştır?',
    // ...
  };

  render(<OSYMQuestion question={question} />);
  expect(screen.getByText(/aşağıdakilerden hangisi/i)).toBeInTheDocument();
});
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)
- [User Event](https://testing-library.com/docs/user-event/intro)
- [KIRO2 Component Documentation](../docs/components.md)

## Contributing

When adding new tests:

1. Follow the existing patterns
2. Write descriptive test names
3. Test both success and error scenarios
4. Include accessibility tests
5. Maintain >85% code coverage
6. Update this README if adding new patterns

## Questions?

For questions about testing, contact the KIRO2 development team or refer to the main project documentation.
