import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TurkishChatInterface } from '../TurkishChatInterface';
import chatService from '../../../services/chatService';

// Mock the services and hooks
vi.mock('../../../services/chatService');
vi.mock('../../../hooks/useWebSocket');
vi.mock('../../../hooks/useTurkishLanguageCorrection');

const mockChatService = chatService as jest.Mocked<typeof chatService>;

// Mock WebSocket hook
const mockUseWebSocket = {
  isConnected: true,
  connectionStatus: 'connected' as const,
  sendMessage: vi.fn(),
  lastMessage: null,
  error: null,
  reconnect: vi.fn()
};

// Mock Turkish language correction hook
const mockUseTurkishLanguageCorrection = {
  checkText: vi.fn(),
  suggestions: [],
  isChecking: false,
  error: null,
  clearSuggestions: vi.fn()
};

vi.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => mockUseWebSocket
}));

vi.mock('../../../hooks/useTurkishLanguageCorrection', () => ({
  useTurkishLanguageCorrection: () => mockUseTurkishLanguageCorrection
}));

describe('TurkishChatInterface', () => {
  const defaultProps = {
    studentId: 'test-student-123',
    sessionId: 'test-session-456',
    subject: 'matematik'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockChatService.loadMessagesFromLocalStorage.mockReturnValue([]);
    mockChatService.loadSession.mockResolvedValue([]);
  });

  it('renders chat interface correctly', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Türkçe AI Asistan')).toBeInTheDocument();
    expect(screen.getByText('matematik • Bağlı')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Mesajınızı Türkçe yazın...')).toBeInTheDocument();
  });

  it('shows empty state when no messages', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Merhaba! Size nasıl yardımcı olabilirim?')).toBeInTheDocument();
    expect(screen.getByText('Türkçe sorularınızı sorabilir, konuları açıklamamı isteyebilirsiniz.')).toBeInTheDocument();
  });

  it('displays quick action buttons in empty state', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Konu açıkla')).toBeInTheDocument();
    expect(screen.getByText('Soru sor')).toBeInTheDocument();
    expect(screen.getByText('Örnek ver')).toBeInTheDocument();
    expect(screen.getByText('Özet çıkar')).toBeInTheDocument();
  });

  it('handles text input correctly', async () => {
    const user = userEvent.setup();
    render(<TurkishChatInterface {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    await user.type(input, 'Merhaba, matematik konusunda yardım istiyorum');
    
    expect(input).toHaveValue('Merhaba, matematik konusunda yardım istiyorum');
  });

  it('sends message when form is submitted', async () => {
    const user = userEvent.setup();
    const onMessageSent = vi.fn();
    
    render(
      <TurkishChatInterface 
        {...defaultProps} 
        onMessageSent={onMessageSent}
      />
    );
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    const sendButton = screen.getByRole('button', { name: /gönder/i });
    
    await user.type(input, 'Test mesajı');
    await user.click(sendButton);
    
    expect(onMessageSent).toHaveBeenCalledWith('Test mesajı');
    expect(mockUseWebSocket.sendMessage).toHaveBeenCalledWith('turkish_nlp', 'Test mesajı');
  });

  it('sends message with Enter key', async () => {
    const user = userEvent.setup();
    const onMessageSent = vi.fn();
    
    render(
      <TurkishChatInterface 
        {...defaultProps} 
        onMessageSent={onMessageSent}
      />
    );
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    
    await user.type(input, 'Test mesajı{enter}');
    
    expect(onMessageSent).toHaveBeenCalledWith('Test mesajı');
  });

  it('creates new line with Shift+Enter', async () => {
    const user = userEvent.setup();
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    
    await user.type(input, 'İlk satır{shift}{enter}İkinci satır');
    
    expect(input).toHaveValue('İlk satır\nİkinci satır');
  });

  it('shows connection status correctly', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('matematik • Bağlı')).toBeInTheDocument();
  });

  it('shows disconnected status when WebSocket is not connected', () => {
    mockUseWebSocket.isConnected = false;
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('matematik • Bağlantı kesildi')).toBeInTheDocument();
  });

  it('handles quick action button clicks', async () => {
    const user = userEvent.setup();
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    const konutAciklaButton = screen.getByText('Konu açıkla');
    await user.click(konutAciklaButton);
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    expect(input).toHaveValue('Bu konuyu detaylı olarak açıklar mısın?');
  });

  it('shows typing indicator when loading', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    // Simulate loading state by triggering a message send
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    const sendButton = screen.getByRole('button', { name: /gönder/i });
    
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(sendButton);
    
    expect(screen.getByText('Yazıyor...')).toBeInTheDocument();
  });

  it('disables input and send button when loading', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    const sendButton = screen.getByRole('button', { name: /gönder/i });
    
    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(sendButton);
    
    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('loads messages from localStorage on mount', () => {
    const mockMessages = [
      {
        id: '1',
        role: 'user' as const,
        content: 'Test mesajı',
        timestamp: new Date().toISOString()
      }
    ];
    
    mockChatService.loadMessagesFromLocalStorage.mockReturnValue(mockMessages);
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(mockChatService.loadMessagesFromLocalStorage).toHaveBeenCalled();
  });

  it('loads session messages when sessionId is provided', async () => {
    const mockSessionMessages = [
      {
        id: '1',
        role: 'agent' as const,
        content: 'Merhaba! Size nasıl yardımcı olabilirim?',
        agent: 'turkish_nlp',
        timestamp: new Date().toISOString()
      }
    ];
    
    mockChatService.loadSession.mockResolvedValue(mockSessionMessages);
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    await waitFor(() => {
      expect(mockChatService.loadSession).toHaveBeenCalledWith('test-session-456');
    });
  });

  it('handles language correction suggestions', () => {
    mockUseTurkishLanguageCorrection.suggestions = [
      {
        original: 'birşey',
        corrected: 'bir şey',
        suggestions: ['bir şey'],
        confidence: 0.9,
        type: 'spelling' as const
      }
    ];
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Dil düzeltme önerileri:')).toBeInTheDocument();
    expect(screen.getByText('bir şey')).toBeInTheDocument();
  });

  it('applies language correction when suggestion is clicked', async () => {
    const user = userEvent.setup();
    
    mockUseTurkishLanguageCorrection.suggestions = [
      {
        original: 'birşey',
        corrected: 'bir şey',
        suggestions: ['bir şey'],
        confidence: 0.9,
        type: 'spelling' as const
      }
    ];
    
    render(<TurkishChatInterface {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Mesajınızı Türkçe yazın...');
    await user.type(input, 'birşey');
    
    const correctionButton = screen.getByText('bir şey');
    await user.click(correctionButton);
    
    expect(input).toHaveValue('bir şey');
  });

  it('shows input hints', () => {
    render(<TurkishChatInterface {...defaultProps} />);
    
    expect(screen.getByText('Enter ile gönder • Shift+Enter ile yeni satır')).toBeInTheDocument();
  });

  it('calls onAgentResponse when agent responds', () => {
    const onAgentResponse = vi.fn();
    const mockResponse = {
      id: 'agent-1',
      role: 'agent' as const,
      content: 'Merhaba! Size yardımcı olabilirim.',
      agent: 'turkish_nlp',
      timestamp: new Date().toISOString()
    };
    
    mockUseWebSocket.lastMessage = mockResponse;
    
    render(
      <TurkishChatInterface 
        {...defaultProps} 
        onAgentResponse={onAgentResponse}
      />
    );
    
    expect(onAgentResponse).toHaveBeenCalledWith(mockResponse);
  });
});