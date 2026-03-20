/**
 * Test Suite: AIChatAssistant Component
 * Task 106: AI Chat - Session, Messaging, Image Upload Tests
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AIChatAssistant } from '../AIChatAssistant';
import { vi, Mock } from 'vitest';

// Mock fetch with vitest Mock type
const fetchMock = vi.fn() as Mock;
global.fetch = fetchMock;
global.alert = vi.fn();

const mockSessions = [
  {
    id: 'session-1',
    user_id: 'user-123',
    title: 'Matematik Çalışması',
    subject_type: 'mathematics',
    status: 'active',
    context: {},
    message_count: 5,
    total_tokens: 1000,
    total_cost: 0.05,
    created_at: '2025-10-28T10:00:00Z',
    updated_at: '2025-10-28T11:00:00Z'
  }
];

const mockMessages = [
  {
    id: 'msg-1',
    session_id: 'session-1',
    role: 'user' as const,
    content: 'Türev nedir?',
    created_at: '2025-10-28T10:00:00Z'
  },
  {
    id: 'msg-2',
    session_id: 'session-1',
    role: 'assistant' as const,
    content: 'Türev, bir fonksiyonun değişim hızını ölçer.',
    confidence_score: 0.95,
    created_at: '2025-10-28T10:01:00Z'
  }
];

describe('AIChatAssistant - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('renders chat interface', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Matematik Çalışması')).toBeInTheDocument();
    });
  });

  it('displays message input', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Mesajınızı yazın/i)).toBeInTheDocument();
    });
  });

  it('shows send button', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Gönder/i)).toBeInTheDocument();
    });
  });

  it('displays image upload button', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Resim yükle/i)).toBeInTheDocument();
    });
  });
});

describe('AIChatAssistant - Session Loading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('fetches sessions on mount', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/chat/sessions?user_id=user-123')
      );
    });
  });

  it('displays session list', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Matematik Çalışması')).toBeInTheDocument();
    });
  });

  it('auto-selects first active session', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions/session-1/messages')
      );
    });
  });

  it('hides session list when showSessionList is false', async () => {
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => [] });
    render(<AIChatAssistant userId="user-123" showSessionList={false} />);
    await waitFor(() => {
      expect(screen.queryByText('Matematik Çalışması')).not.toBeInTheDocument();
    });
  });
});

describe('AIChatAssistant - Message Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('displays user messages', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Türev nedir?')).toBeInTheDocument();
    });
  });

  it('displays assistant messages', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText(/Türev, bir fonksiyonun değişim hızını ölçer/)).toBeInTheDocument();
    });
  });

  it('shows loading state', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockImplementation(() => new Promise(() => {}));

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText(/Yükleniyor/i)).toBeInTheDocument();
    });
  });
});

describe('AIChatAssistant - New Session', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] });
  });

  it('shows new session button', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText(/Yeni Sohbet/i)).toBeInTheDocument();
    });
  });

  it('opens new session form', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      fireEvent.click(screen.getByText(/Yeni Sohbet/i));
      expect(screen.getByLabelText(/Oturum Başlığı/i)).toBeInTheDocument();
    });
  });

  it('creates new session', async () => {
    const newSession = { ...mockSessions[0], id: 'new-session', title: 'Yeni Sohbet' };
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => newSession })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => fireEvent.click(screen.getByText(/Yeni Sohbet/i)));

    const titleInput = screen.getByLabelText(/Oturum Başlığı/i);
    fireEvent.change(titleInput, { target: { value: 'Yeni Sohbet' } });

    fireEvent.click(screen.getByText(/Oluştur/i));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/chat/sessions'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  it('validates session title', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => fireEvent.click(screen.getByText(/Yeni Sohbet/i)));

    fireEvent.click(screen.getByText(/Oluştur/i));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Lütfen oturum başlığı girin');
    });
  });

  it('selects subject for new session', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => fireEvent.click(screen.getByText(/Yeni Sohbet/i)));

    const subjectSelect = screen.getByLabelText(/Konu/i);
    fireEvent.change(subjectSelect, { target: { value: 'physics' } });

    expect((subjectSelect as HTMLSelectElement).value).toBe('physics');
  });
});

describe('AIChatAssistant - Send Message', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('sends message', async () => {
    const newMessage = { ...mockMessages[0], id: 'new-msg', content: 'Yeni mesaj' };
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => newMessage });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Türev nedir?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Mesajınızı yazın/i);
    fireEvent.change(input, { target: { value: 'Yeni mesaj' } });

    const sendButton = screen.getByLabelText(/Gönder/i);
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/messages'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  it('clears input after send', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({}) });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Türev nedir?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Mesajınızı yazın/i) as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(screen.getByLabelText(/Gönder/i));

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('disables send during processing', async () => {
    fetchMock.mockImplementation(() => new Promise(() => {}));

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByText('Türev nedir?')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Mesajınızı yazın/i);
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(screen.getByLabelText(/Gönder/i));

    expect(screen.getByLabelText(/Gönder/i)).toBeDisabled();
  });
});

describe('AIChatAssistant - Image Upload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('handles image selection', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Resim yükle/i)).toBeInTheDocument();
    });

    const file = new File(['image'], 'test.png', { type: 'image/png' });
    const input = screen.getByLabelText(/Resim yükle/i);

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByAltText(/Önizleme/i)).toBeInTheDocument();
    });
  });

  it('validates image file type', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Resim yükle/i)).toBeInTheDocument();
    });

    const file = new File(['text'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/Resim yükle/i);

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith('Lütfen geçerli bir resim dosyası seçin');
    });
  });

  it('uploads image', async () => {
    const mockImageData = {
      id: 'img-1',
      session_id: 'session-1',
      file_path: '/uploads/test.png',
      file_size: 1024,
      processing_status: 'completed',
      ocr_text: 'Test OCR'
    };

    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => mockImageData });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Resim yükle/i)).toBeInTheDocument();
    });

    const file = new File(['image'], 'test.png', { type: 'image/png' });
    const input = screen.getByLabelText(/Resim yükle/i);

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false
    });

    fireEvent.change(input);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/upload-image'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  it('shows OCR results', async () => {
    const mockImageData = {
      id: 'img-1',
      ocr_text: 'Görsel metni: x² + 2x + 1 = 0',
      processing_status: 'completed'
    };

    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => mockImageData });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      const file = new File(['image'], 'test.png', { type: 'image/png' });
      const input = screen.getByLabelText(/Resim yükle/i);
      Object.defineProperty(input, 'files', { value: [file] });
      fireEvent.change(input);
    });

    await waitFor(() => {
      expect(screen.getByText(/Görsel metni:/)).toBeInTheDocument();
    });
  });
});

describe('AIChatAssistant - Error Handling', () => {
  it('handles session loading error', async () => {
    fetchMock.mockRejectedValue(new Error('Network error'));

    render(<AIChatAssistant userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load sessions/i)).toBeInTheDocument();
    });
  });

  it('handles message loading error', async () => {
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockRejectedValueOnce(new Error('Failed to load messages'));

    render(<AIChatAssistant userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load messages/i)).toBeInTheDocument();
    });
  });
});

describe('AIChatAssistant - Subject Selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock.mockResolvedValue({ ok: true, json: async () => [] });
  });

  it('uses initial subject', () => {
    render(<AIChatAssistant userId="user-123" initialSubject="physics" />);
    expect(screen.queryByText(/Matematik/i)).not.toBeInTheDocument();
  });

  it('displays all subject options', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => fireEvent.click(screen.getByText(/Yeni Sohbet/i)));

    const subjectSelect = screen.getByLabelText(/Konu/i);
    fireEvent.click(subjectSelect);

    expect(screen.getByText('Matematik')).toBeInTheDocument();
    expect(screen.getByText('Fizik')).toBeInTheDocument();
    expect(screen.getByText('Kimya')).toBeInTheDocument();
  });
});

describe('AIChatAssistant - Message Rating', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('shows helpful buttons for assistant messages', async () => {
    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Yararlı/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Yararlı değil/i)).toBeInTheDocument();
    });
  });

  it('rates message as helpful', async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({}) });

    render(<AIChatAssistant userId="user-123" />);
    await waitFor(() => {
      const helpfulButton = screen.getByLabelText(/Yararlı/i);
      fireEvent.click(helpfulButton);
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/rate'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('is_helpful')
        })
      );
    });
  });
});

describe('AIChatAssistant - Auto Scroll', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchMock
      .mockResolvedValueOnce({ ok: true, json: async () => mockSessions })
      .mockResolvedValueOnce({ ok: true, json: async () => mockMessages });
  });

  it('scrolls to bottom on new message', async () => {
    const scrollIntoViewMock = vi.fn();
    HTMLDivElement.prototype.scrollIntoView = scrollIntoViewMock;

    render(<AIChatAssistant userId="user-123" />);

    await waitFor(() => {
      expect(screen.getByText('Türev nedir?')).toBeInTheDocument();
    });

    expect(scrollIntoViewMock).toHaveBeenCalled();
  });
});
