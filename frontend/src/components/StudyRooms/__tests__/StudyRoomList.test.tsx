/**
 * Task 109.1: StudyRoomList Component Tests
 *
 * Tests for study room listing, filtering, and creation
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import StudyRoomList from '../StudyRoomList';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock data
const mockRooms = [
  {
    id: '1',
    name: 'TYT Matematik Çalışma Grubu',
    description: 'TYT matematik sorularını birlikte çözelim',
    topic: 'Denklemler',
    subject: 'Matematik',
    visibility: 'public',
    status: 'active',
    max_members: 50,
    member_count: 12,
    owner_id: 'user1',
    owner_name: 'Ahmet Yılmaz',
    created_at: '2025-10-27T10:00:00Z',
    updated_at: '2025-10-27T10:00:00Z',
    has_active_video: true,
    unread_messages: 3,
  },
  {
    id: '2',
    name: 'AYT Fizik Grubu',
    description: 'Fizik konularını tartışalım',
    topic: 'Elektrik',
    subject: 'Fizik',
    visibility: 'private',
    status: 'active',
    max_members: 30,
    member_count: 8,
    owner_id: 'user2',
    owner_name: 'Ayşe Demir',
    created_at: '2025-10-27T09:00:00Z',
    updated_at: '2025-10-27T09:00:00Z',
    has_active_video: false,
    unread_messages: 0,
  },
];

describe('StudyRoomList Component', () => {
  const mockOnRoomSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockRooms });
  });

  describe('Rendering', () => {
    it('renders the component with title', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      expect(screen.getByText('📚 Grup Çalışma Odaları')).toBeInTheDocument();
      expect(screen.getByText('Yeni Oda Oluştur')).toBeInTheDocument();
    });

    it('displays loading state initially', () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
    });

    it('renders room list after data is loaded', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
        expect(screen.getByText('AYT Fizik Grubu')).toBeInTheDocument();
      });
    });

    it('displays room cards with correct information', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        // Check room details
        expect(screen.getByText('Matematik')).toBeInTheDocument();
        expect(screen.getByText('Denklemler')).toBeInTheDocument();
        expect(screen.getByText('12/50')).toBeInTheDocument();
      });
    });

    it('shows video indicator for rooms with active video', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const videoIcons = screen.getAllByTestId('VideoCallIcon');
        expect(videoIcons.length).toBeGreaterThan(0);
      });
    });

    it('shows unread message badge', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // Unread count
      });
    });
  });

  describe('Tabs', () => {
    it('renders all three tabs', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      expect(screen.getByText('Tüm Odalar')).toBeInTheDocument();
      expect(screen.getByText('Benim Odalarım')).toBeInTheDocument();
      expect(screen.getByText('Katıldığım Odalar')).toBeInTheDocument();
    });

    it('fetches different data when switching tabs', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith('/api/study-rooms');
      });

      // Click "My Rooms" tab
      fireEvent.click(screen.getByText('Benim Odalarım'));

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith('/api/study-rooms/my-rooms');
      });

      // Click "Joined Rooms" tab
      fireEvent.click(screen.getByText('Katıldığım Odalar'));

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith('/api/study-rooms/joined');
      });
    });
  });

  describe('Filtering', () => {
    it('filters rooms by search query', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Oda ara...');
      fireEvent.change(searchInput, { target: { value: 'Matematik' } });

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
        expect(screen.queryByText('AYT Fizik Grubu')).not.toBeInTheDocument();
      });
    });

    it('filters rooms by subject', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getAllByText('Matematik').length).toBeGreaterThan(0);
      });

      // Select Matematik filter
      const subjectFilter = screen.getByLabelText('Ders');
      fireEvent.mouseDown(subjectFilter);
      fireEvent.click(screen.getByText('Matematik'));

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
        expect(screen.queryByText('AYT Fizik Grubu')).not.toBeInTheDocument();
      });
    });

    it('filters rooms by visibility', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
      });

      const visibilityFilter = screen.getByLabelText('Gizlilik');
      fireEvent.mouseDown(visibilityFilter);
      fireEvent.click(screen.getByText('Herkese Açık'));

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
        expect(screen.queryByText('AYT Fizik Grubu')).not.toBeInTheDocument();
      });
    });

    it('combines multiple filters', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
      });

      // Search + Subject filter
      const searchInput = screen.getByPlaceholderText('Oda ara...');
      fireEvent.change(searchInput, { target: { value: 'TYT' } });

      const subjectFilter = screen.getByLabelText('Ders');
      fireEvent.mouseDown(subjectFilter);
      fireEvent.click(screen.getByText('Matematik'));

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
        expect(screen.queryByText('AYT Fizik Grubu')).not.toBeInTheDocument();
      });
    });
  });

  describe('Room Creation', () => {
    it('opens create dialog when button is clicked', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      const createButton = screen.getByText('Yeni Oda Oluştur');
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText('Yeni Çalışma Odası Oluştur')).toBeInTheDocument();
      });
    });

    it('validates required fields in create dialog', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: 'Oluştur' });
        expect(createButton).toBeDisabled();
      });
    });

    it('enables create button when name is filled', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        const nameInput = screen.getByLabelText('Oda Adı');
        fireEvent.change(nameInput, { target: { value: 'Test Odası' } });
      });

      const createButton = screen.getByRole('button', { name: 'Oluştur' });
      expect(createButton).not.toBeDisabled();
    });

    it('creates room with correct data', async () => {
      mockedAxios.post.mockResolvedValue({ data: { id: '3', name: 'Test Odası' } });

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        fireEvent.change(screen.getByLabelText('Oda Adı'), { target: { value: 'Test Odası' } });
        fireEvent.change(screen.getByLabelText('Açıklama'), { target: { value: 'Test açıklaması' } });
      });

      fireEvent.click(screen.getByRole('button', { name: 'Oluştur' }));

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/study-rooms', expect.objectContaining({
          name: 'Test Odası',
          description: 'Test açıklaması',
        }));
      });
    });

    it('shows password field when password visibility is selected', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        const visibilitySelect = screen.getByLabelText('Gizlilik');
        fireEvent.mouseDown(visibilitySelect);
        fireEvent.click(screen.getByText('Şifre Korumalı'));
      });

      expect(screen.getByLabelText('Oda Şifresi')).toBeInTheDocument();
    });

    it('closes dialog on cancel', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        expect(screen.getByText('Yeni Çalışma Odası Oluştur')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('İptal'));

      await waitFor(() => {
        expect(screen.queryByText('Yeni Çalışma Odası Oluştur')).not.toBeInTheDocument();
      });
    });
  });

  describe('Room Joining', () => {
    it('calls onRoomSelect when join button is clicked for public room', async () => {
      mockedAxios.post.mockResolvedValue({ data: { success: true } });

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const joinButtons = screen.getAllByText('Katıl');
        fireEvent.click(joinButtons[0]);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/study-rooms/1/join');
        expect(mockOnRoomSelect).toHaveBeenCalledWith('1');
      });
    });

    it('prompts for password when joining password-protected room', async () => {
      window.prompt = vi.fn().mockReturnValue('test-password');
      mockedAxios.post.mockResolvedValue({ data: { success: true } });

      // Add password-protected room
      const passwordRoom = { ...mockRooms[0], id: '3', visibility: 'password' };
      mockedAxios.get.mockResolvedValue({ data: [...mockRooms, passwordRoom] });

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const joinButtons = screen.getAllByText('Katıl');
        fireEvent.click(joinButtons[2]); // Third room is password-protected
      });

      await waitFor(() => {
        expect(window.prompt).toHaveBeenCalled();
        expect(mockedAxios.post).toHaveBeenCalledWith('/api/study-rooms/3/join', {
          password: 'test-password',
        });
      });
    });

    it('disables join button for full rooms', async () => {
      const fullRoom = { ...mockRooms[0], member_count: 50, max_members: 50 };
      mockedAxios.get.mockResolvedValue({ data: [fullRoom] });

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const joinButton = screen.getByText('Dolu');
        expect(joinButton).toBeDisabled();
      });
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no rooms exist', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('Henüz çalışma odası yok')).toBeInTheDocument();
        expect(screen.getByText('İlk odayı siz oluşturun!')).toBeInTheDocument();
      });
    });

    it('displays empty state when filters return no results', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByText('TYT Matematik Çalışma Grubu')).toBeInTheDocument();
      });

      // Search for non-existent room
      const searchInput = screen.getByPlaceholderText('Oda ara...');
      fireEvent.change(searchInput, { target: { value: 'NonExistentRoom' } });

      await waitFor(() => {
        expect(screen.getByText('Henüz çalışma odası yok')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      console.error = vi.fn(); // Suppress error logs in test

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(console.error).toHaveBeenCalled();
      });
    });

    it('handles room creation errors', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Creation failed'));
      console.error = vi.fn();

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      fireEvent.click(screen.getByText('Yeni Oda Oluştur'));

      await waitFor(() => {
        fireEvent.change(screen.getByLabelText('Oda Adı'), { target: { value: 'Test' } });
      });

      fireEvent.click(screen.getByRole('button', { name: 'Oluştur' }));

      await waitFor(() => {
        expect(console.error).toHaveBeenCalled();
      });
    });

    it('handles join room errors with alert', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Join failed'));
      window.alert = vi.fn();
      console.error = vi.fn();

      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const joinButtons = screen.getAllByText('Katıl');
        fireEvent.click(joinButtons[0]);
      });

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Odaya katılırken bir hata oluştu.');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        expect(screen.getByLabelText('Ders')).toBeInTheDocument();
        expect(screen.getByLabelText('Gizlilik')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      render(<StudyRoomList onRoomSelect={mockOnRoomSelect} />);

      await waitFor(() => {
        const createButton = screen.getByText('Yeni Oda Oluştur');
        createButton.focus();
        expect(createButton).toHaveFocus();
      });
    });
  });
});
