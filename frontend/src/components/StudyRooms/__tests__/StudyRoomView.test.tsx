/**
 * Test Suite: StudyRoomView Component
 * Task 109: Study Room View Integration Testing
 *
 * Tests the main study room container including tab navigation,
 * member display, room actions, and component integration.
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import StudyRoomView from '../StudyRoomView';
import { vi, Mocked } from 'vitest';

// ============================================================
// Mocks
// ============================================================

// Mock Axios
vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

// Mock child components - ESM requires { default: ... } export
vi.mock('../ChatInterface', () => ({
  default: function MockChatInterface({ roomId }: any) {
    return <div data-testid="chat-interface">Chat Interface - Room {roomId}</div>;
  },
}));

vi.mock('../FileManager', () => ({
  default: function MockFileManager({ roomId }: any) {
    return <div data-testid="file-manager">File Manager - Room {roomId}</div>;
  },
}));

vi.mock('../VideoConference', () => ({
  default: function MockVideoConference({ roomId, onLeave }: any) {
    return (
      <div data-testid="video-conference">
        Video Conference - Room {roomId}
        <button onClick={onLeave}>Leave Video</button>
      </div>
    );
  },
}));

vi.mock('../CollaborativeWhiteboard', () => ({
  default: function MockCollaborativeWhiteboard({ roomId }: any) {
    return <div data-testid="whiteboard">Whiteboard - Room {roomId}</div>;
  },
}));

// Mock window.confirm
global.confirm = vi.fn(() => true);

// ============================================================
// Test Data
// ============================================================

const mockRoom = {
  id: 'room1',
  name: 'TYT Matematik Çalışma Grubu',
  description: 'TYT matematik sorularını birlikte çözelim',
  topic: 'Denklemler',
  subject: 'Matematik',
  visibility: 'public' as const,
  status: 'active' as const,
  max_members: 10,
  member_count: 5,
  owner_id: 'user1',
  owner_name: 'Test User',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockMembers = [
  {
    id: 'member1',
    user_id: 'user1',
    name: 'Test User',
    avatar: 'avatar1.jpg',
    role: 'owner' as const,
    is_online: true,
    joined_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'member2',
    user_id: 'user2',
    name: 'User 2',
    avatar: 'avatar2.jpg',
    role: 'member' as const,
    is_online: true,
    joined_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'member3',
    user_id: 'user3',
    name: 'User 3',
    role: 'member' as const,
    is_online: false,
    joined_at: '2024-01-01T00:00:00Z',
  },
];

const mockProps = {
  roomId: 'room1',
  currentUserId: 'user1',
  currentUserName: 'Test User',
  onBack: vi.fn(),
};

// ============================================================
// Tests: Rendering
// ============================================================

describe('StudyRoomView Component - Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('renders loading state initially', () => {
    mockedAxios.get.mockReturnValue(new Promise(() => {})); // Never resolves

    render(<StudyRoomView {...mockProps} />);

    expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
  });

  it('renders room details after loading', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    expect(screen.getByText('Matematik')).toBeInTheDocument();
    expect(screen.getByText('Denklemler')).toBeInTheDocument();
    expect(screen.getByText('3 üye')).toBeInTheDocument();
  });

  it('displays all tabs', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    expect(screen.getByText('Sohbet')).toBeInTheDocument();
    expect(screen.getByText('Dosyalar')).toBeInTheDocument();
    expect(screen.getByText('Video')).toBeInTheDocument();
    expect(screen.getByText('Beyaz Tahta')).toBeInTheDocument();
  });

  it('displays back button', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('ArrowBackIcon')).toBeInTheDocument();
    });
  });

  it('displays online members', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      const avatars = document.querySelectorAll('.MuiAvatar-root');
      // Should show 2 online members
      expect(avatars.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('displays room menu button', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Data Fetching
// ============================================================

describe('StudyRoomView Component - Data Fetching', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('fetches room details on mount', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/study-rooms/room1');
    });
  });

  it('fetches members on mount', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/study-rooms/room1/members');
    });
  });

  it('handles room fetch error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockRejectedValueOnce(new Error('Fetch failed'));

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error fetching room details:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });

  it('handles members fetch error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.reject(new Error('Fetch failed'));
      }
      return Promise.resolve({ data: mockRoom });
    });

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Error fetching members:',
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Tab Navigation
// ============================================================

describe('StudyRoomView Component - Tab Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('shows chat interface by default', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });
  });

  it('switches to file manager tab', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    const filesTab = screen.getByText('Dosyalar');
    fireEvent.click(filesTab);

    await waitFor(() => {
      expect(screen.getByTestId('file-manager')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();
    });
  });

  it('switches to video conference tab', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    const videoTab = screen.getByText('Video');
    fireEvent.click(videoTab);

    await waitFor(() => {
      expect(screen.getByTestId('video-conference')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();
    });
  });

  it('switches to whiteboard tab', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    const whiteboardTab = screen.getByText('Beyaz Tahta');
    fireEvent.click(whiteboardTab);

    await waitFor(() => {
      expect(screen.getByTestId('whiteboard')).toBeInTheDocument();
      expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();
    });
  });

  it('maintains active tab state', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    // Switch to files
    fireEvent.click(screen.getByText('Dosyalar'));
    await waitFor(() => {
      expect(screen.getByTestId('file-manager')).toBeInTheDocument();
    });

    // Switch to video
    fireEvent.click(screen.getByText('Video'));
    await waitFor(() => {
      expect(screen.getByTestId('video-conference')).toBeInTheDocument();
    });

    // Switch back to chat
    fireEvent.click(screen.getByText('Sohbet'));
    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });
  });
});

// ============================================================
// Tests: Back Navigation
// ============================================================

describe('StudyRoomView Component - Back Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('calls onBack when back button clicked', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('ArrowBackIcon')).toBeInTheDocument();
    });

    const backButton = screen.getByTestId('ArrowBackIcon').closest('button')!;
    fireEvent.click(backButton);

    expect(mockProps.onBack).toHaveBeenCalled();
  });
});

// ============================================================
// Tests: Room Menu Actions
// ============================================================

describe('StudyRoomView Component - Room Menu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
    mockedAxios.post.mockResolvedValue({ data: {} });
    mockedAxios.delete.mockResolvedValue({ data: {} });
  });

  it('opens room menu', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Oda Ayarları')).toBeInTheDocument();
      expect(screen.getByText('Odadan Ayrıl')).toBeInTheDocument();
    });
  });

  it('leaves room when confirmed', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odadan Ayrıl')).toBeInTheDocument();
    });

    const leaveButton = screen.getByText('Odadan Ayrıl');
    fireEvent.click(leaveButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/study-rooms/room1/leave');
      expect(mockProps.onBack).toHaveBeenCalled();
    });
  });

  it('does not leave room when cancelled', async () => {
    (global.confirm as jest.Mock).mockReturnValueOnce(false);

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odadan Ayrıl')).toBeInTheDocument();
    });

    const leaveButton = screen.getByText('Odadan Ayrıl');
    fireEvent.click(leaveButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
    });

    expect(mockedAxios.post).not.toHaveBeenCalled();
    expect(mockProps.onBack).not.toHaveBeenCalled();
  });

  it('shows archive option for admins', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Arşivle')).toBeInTheDocument();
    });
  });

  it('archives room when confirmed', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Arşivle')).toBeInTheDocument();
    });

    const archiveButton = screen.getByText('Arşivle');
    fireEvent.click(archiveButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/study-rooms/room1/archive');
      expect(mockProps.onBack).toHaveBeenCalled();
    });
  });

  it('shows delete option for owner', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odayı Sil')).toBeInTheDocument();
    });
  });

  it('deletes room when confirmed', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odayı Sil')).toBeInTheDocument();
    });

    const deleteButton = screen.getByText('Odayı Sil');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(global.confirm).toHaveBeenCalled();
      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/v1/study-rooms/room1');
      expect(mockProps.onBack).toHaveBeenCalled();
    });
  });

  it('hides delete option for non-owners', async () => {
    const nonOwnerProps = { ...mockProps, currentUserId: 'user2' };

    render(<StudyRoomView {...nonOwnerProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Oda Ayarları')).toBeInTheDocument();
    });

    expect(screen.queryByText('Odayı Sil')).not.toBeInTheDocument();
  });

  it('hides archive option for non-admins', async () => {
    const nonAdminProps = { ...mockProps, currentUserId: 'user3' };

    render(<StudyRoomView {...nonAdminProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Oda Ayarları')).toBeInTheDocument();
    });

    expect(screen.queryByText('Arşivle')).not.toBeInTheDocument();
  });
});

// ============================================================
// Tests: Error Handling
// ============================================================

describe('StudyRoomView Component - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('handles leave room error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Leave failed'));

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odadan Ayrıl')).toBeInTheDocument();
    });

    const leaveButton = screen.getByText('Odadan Ayrıl');
    fireEvent.click(leaveButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error leaving room:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('handles archive room error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.post.mockRejectedValue(new Error('Archive failed'));

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Arşivle')).toBeInTheDocument();
    });

    const archiveButton = screen.getByText('Arşivle');
    fireEvent.click(archiveButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error archiving room:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it('handles delete room error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation();
    mockedAxios.delete.mockRejectedValue(new Error('Delete failed'));

    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('MoreVertIcon')).toBeInTheDocument();
    });

    const menuButton = screen.getByTestId('MoreVertIcon').closest('button')!;
    fireEvent.click(menuButton);

    await waitFor(() => {
      expect(screen.getByText('Odayı Sil')).toBeInTheDocument();
    });

    const deleteButton = screen.getByText('Odayı Sil');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Error deleting room:', expect.any(Error));
    });

    consoleSpy.mockRestore();
  });
});

// ============================================================
// Tests: Component Integration
// ============================================================

describe('StudyRoomView Component - Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/members')) {
        return Promise.resolve({ data: mockMembers });
      }
      return Promise.resolve({ data: mockRoom });
    });
  });

  it('passes correct props to ChatInterface', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });

    expect(screen.getByText('Chat Interface - Room room1')).toBeInTheDocument();
  });

  it('passes correct props to FileManager', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Dosyalar'));

    await waitFor(() => {
      expect(screen.getByTestId('file-manager')).toBeInTheDocument();
    });

    expect(screen.getByText('File Manager - Room room1')).toBeInTheDocument();
  });

  it('passes correct props to VideoConference', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Video'));

    await waitFor(() => {
      expect(screen.getByTestId('video-conference')).toBeInTheDocument();
    });

    expect(screen.getByText('Video Conference - Room room1')).toBeInTheDocument();
  });

  it('passes correct props to CollaborativeWhiteboard', async () => {
    render(<StudyRoomView {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Beyaz Tahta'));

    await waitFor(() => {
      expect(screen.getByTestId('whiteboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Whiteboard - Room room1')).toBeInTheDocument();
  });
});
