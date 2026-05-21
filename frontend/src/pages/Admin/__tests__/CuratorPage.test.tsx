/**
 * CuratorPage smoke tests
 *
 * Verifies:
 *   - Queue renders with mock data
 *   - 'V' shortcut triggers verify verdict POST
 *   - 'R' shortcut triggers reject verdict POST
 *   - Filter change re-fetches the queue
 *   - Help overlay opens with '?'
 *
 * Notes:
 *  - We mock `apiRequest` (the only network surface used by useCuratorQueue
 *    hooks) so we don't need to spin up MSW handlers for this smoke test.
 *  - react-query v3: `useMutation`/`useQuery` are wrapped in a QueryClient
 *    that disables retries/cache for deterministic tests.
 */

import * as React from 'react';
import { describe, expect, it, vi, beforeEach, type Mock } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';

// Mock apiRequest BEFORE importing the page that uses it.
vi.mock('../../../utils/apiHelpers', () => ({
  apiRequest: vi.fn(),
}));

import { apiRequest } from '../../../utils/apiHelpers';
import { CuratorPage } from '../CuratorPage';

const mockApiRequest = apiRequest as unknown as Mock;

// ----------------------------------------------------------------------------
// Fixtures
// ----------------------------------------------------------------------------

const mockItem = {
  id: 'q-001',
  question_text: 'İki sayının toplamı 12, farkı 4 ise küçüğü kaçtır?',
  options: { A: '2', B: '4', C: '6', D: '8', E: '10' },
  correct_answer: 'B',
  subject_area: 'MATEMATIK',
  difficulty_level: 'EASY',
  quality_review_status: 'bronze_clean',
  image_url: null,
  misconception_tags: ['operation_error'],
  solution_steps: ['Topla ve böl'],
  similar_question_ids: [],
};

const mockItem2 = {
  ...mockItem,
  id: 'q-002',
  question_text: 'İkinci soru: x + 5 = 10 ise x kaçtır?',
};

const queueResponse = {
  items: [mockItem, mockItem2],
  total: 2,
  page: 1,
  per_page: 25,
};

const statsResponse = {
  pending_count: 14523,
  verified_today: 47,
  rejected_today: 12,
  avg_velocity_sec: 142,
};

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

function setupApiMock() {
  mockApiRequest.mockImplementation((url: string, options?: RequestInit) => {
    if (url.startsWith('/api/v1/curator/queue')) {
      return Promise.resolve(queueResponse);
    }
    if (url === '/api/v1/curator/stats') {
      return Promise.resolve(statsResponse);
    }
    if (url === '/api/v1/curator/verdict' && options?.method === 'POST') {
      return Promise.resolve({ ok: true });
    }
    return Promise.reject(new Error(`Unmocked URL: ${url}`));
  });
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <CuratorPage />
    </QueryClientProvider>,
  );
}

// ----------------------------------------------------------------------------
// Tests
// ----------------------------------------------------------------------------

describe('CuratorPage', () => {
  beforeEach(() => {
    mockApiRequest.mockReset();
    setupApiMock();
    cleanup();
  });

  it('renders the queue list with mock data', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-queue-list')).toBeInTheDocument();
    });

    expect(screen.getByTestId('queue-item-q-001')).toBeInTheDocument();
    expect(screen.getByTestId('queue-item-q-002')).toBeInTheDocument();

    // First item auto-selected -> question text visible in right pane
    await waitFor(() => {
      expect(screen.getByTestId('curator-question-text')).toHaveTextContent(
        'İki sayının toplamı 12',
      );
    });
  });

  it('renders stats bar with mock stats', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId('curator-stats-bar')).toBeInTheDocument();
    });
    expect(screen.getByText('14523')).toBeInTheDocument();
    expect(screen.getByText('47')).toBeInTheDocument();
  });

  it("sends 'verify' verdict when V key is pressed", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-question-text')).toBeInTheDocument();
    });

    fireEvent.keyDown(window, { key: 'v' });

    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/curator/verdict',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"verdict":"verify"'),
        }),
      );
    });
  });

  it("sends 'reject' verdict when R key is pressed", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-question-text')).toBeInTheDocument();
    });

    fireEvent.keyDown(window, { key: 'r' });

    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/curator/verdict',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"verdict":"reject"'),
        }),
      );
    });
  });

  it("sends 'archive' verdict when Archive button is clicked", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('action-archive')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('action-archive'));

    await waitFor(() => {
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/curator/verdict',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"verdict":"archive"'),
        }),
      );
    });
  });

  it('re-fetches queue when status filter changes', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-filter-chips')).toBeInTheDocument();
    });

    const initialCalls = mockApiRequest.mock.calls.filter((c) =>
      String(c[0]).startsWith('/api/v1/curator/queue'),
    ).length;

    fireEvent.click(screen.getByRole('button', { name: 'Pending' }));

    await waitFor(() => {
      const newCalls = mockApiRequest.mock.calls.filter((c) =>
        String(c[0]).startsWith('/api/v1/curator/queue'),
      ).length;
      expect(newCalls).toBeGreaterThan(initialCalls);
    });

    // The new request URL should include status=pending
    const lastQueueCall = [...mockApiRequest.mock.calls]
      .reverse()
      .find((c) => String(c[0]).startsWith('/api/v1/curator/queue'));
    expect(String(lastQueueCall?.[0])).toContain('status=pending');
  });

  it('opens help overlay with ? key', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-page')).toBeInTheDocument();
    });

    fireEvent.keyDown(window, { key: '?' });

    await waitFor(() => {
      expect(screen.getByTestId('help-overlay')).toBeInTheDocument();
    });
    expect(screen.getByText('Klavye Kısayolları')).toBeInTheDocument();
  });

  it('navigates between items with arrow keys', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('curator-question-text')).toHaveTextContent(
        'İki sayının toplamı 12',
      );
    });

    fireEvent.keyDown(window, { key: 'ArrowRight' });

    await waitFor(() => {
      expect(screen.getByTestId('curator-question-text')).toHaveTextContent('İkinci soru');
    });
  });

  it('highlights option A when 1 key is pressed', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('option-A')).toBeInTheDocument();
    });

    fireEvent.keyDown(window, { key: '1' });

    await waitFor(() => {
      const optA = screen.getByTestId('option-A');
      expect(optA.className).toContain('ring-2');
    });
  });
});
