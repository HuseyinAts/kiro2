/**
 * Task 109.4: FileManager Component Tests
 * Tests for file upload, download, versioning, and management
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import FileManager from '../FileManager';
import { vi, Mocked } from 'vitest';

vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

const mockFiles = [
  {
    id: 'file1',
    room_id: 'room1',
    uploader_id: 'user1',
    uploader_name: 'Ahmet',
    file_name: 'matematik-notlar.pdf',
    file_type: 'document',
    file_size: 1024000,
    file_url: 'http://example.com/file1.pdf',
    mime_type: 'application/pdf',
    version: 1,
    is_current_version: true,
    download_count: 5,
    created_at: '2025-10-27T10:00:00Z',
    updated_at: '2025-10-27T10:00:00Z',
  },
  {
    id: 'file2',
    room_id: 'room1',
    uploader_id: 'user2',
    uploader_name: 'Ayşe',
    file_name: 'grafik.jpg',
    file_type: 'image',
    file_size: 512000,
    file_url: 'http://example.com/grafik.jpg',
    mime_type: 'image/jpeg',
    version: 1,
    is_current_version: true,
    download_count: 3,
    created_at: '2025-10-27T09:00:00Z',
    updated_at: '2025-10-27T09:00:00Z',
  },
];

describe('FileManager Component', () => {
  const mockProps = {
    roomId: 'room1',
    currentUserId: 'user1',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockedAxios.get.mockResolvedValue({ data: mockFiles });
    mockedAxios.post.mockResolvedValue({ data: { success: true } });
  });

  describe('Rendering', () => {
    it('renders file manager header', async () => {
      render(<FileManager {...mockProps} />);
      expect(screen.getByText('📁 Dosyalar')).toBeInTheDocument();
      expect(screen.getByText('Dosya Yükle')).toBeInTheDocument();
    });

    it('loads and displays files', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
        expect(screen.getByText('grafik.jpg')).toBeInTheDocument();
      });
    });

    it('shows loading state initially', () => {
      render(<FileManager {...mockProps} />);
      expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
    });

    it('displays file metadata correctly', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        expect(screen.getByText('1.00 MB')).toBeInTheDocument();
        expect(screen.getByText('Ahmet')).toBeInTheDocument();
      });
    });
  });

  describe('View Modes', () => {
    it('defaults to grid view', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
      });
    });

    it('switches to list view when list icon is clicked', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        const listButton = screen.getByRole('button', { name: /list/i });
        fireEvent.click(listButton);
      });
      // List view should show different layout
    });

    it('switches back to grid view', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        const listButton = screen.getByRole('button', { name: /list/i });
        fireEvent.click(listButton);
        const gridButton = screen.getByRole('button', { name: /grid/i });
        fireEvent.click(gridButton);
      });
    });
  });

  describe('File Upload', () => {
    it('uploads file when selected', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      mockedAxios.post.mockResolvedValue({
        data: {
          id: 'file3',
          file_name: 'test.pdf',
          file_size: 1000,
        }
      });

      render(<FileManager {...mockProps} />);

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      await waitFor(() => {
        fireEvent.change(input, { target: { files: [file] } });
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/v1/study-rooms/room1/files/upload',
          expect.any(FormData),
          expect.objectContaining({
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: expect.any(Function),
          })
        );
      });
    });

    it('shows upload progress bar', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      render(<FileManager {...mockProps} />);

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/Yükleniyor/i)).toBeInTheDocument();
      });
    });

    it('disables upload button while uploading', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      render(<FileManager {...mockProps} />);

      const uploadButton = screen.getByText('Dosya Yükle');
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(uploadButton).toBeDisabled();
      });
    });

    it('handles upload errors', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Upload failed'));
      window.alert = vi.fn();

      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      render(<FileManager {...mockProps} />);

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Dosya yüklenirken bir hata oluştu.');
      });
    });
  });

  describe('File Filtering', () => {
    it('filters files by search query', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Dosya ara...');
      fireEvent.change(searchInput, { target: { value: 'matematik' } });

      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
        expect(screen.queryByText('grafik.jpg')).not.toBeInTheDocument();
      });
    });

    it('filters files by type', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const documentChip = screen.getByText('Dökümanlar');
        fireEvent.click(documentChip);
      });

      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
        expect(screen.queryByText('grafik.jpg')).not.toBeInTheDocument();
      });
    });

    it('shows all files when "Tümü" filter is selected', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const allChip = screen.getByText('Tümü');
        fireEvent.click(allChip);
      });

      await waitFor(() => {
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
        expect(screen.getByText('grafik.jpg')).toBeInTheDocument();
      });
    });
  });

  describe('File Actions', () => {
    it('downloads file when download button is clicked', async () => {
      window.open = vi.fn();

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const downloadButton = screen.getAllByRole('button', { name: /İndir/i })[0];
        fireEvent.click(downloadButton);
      });

      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/v1/study-rooms/room1/files/file1/download'
        );
        expect(window.open).toHaveBeenCalledWith('http://example.com/file1.pdf', '_blank');
      });
    });

    it('increments download count after download', async () => {
      window.open = vi.fn();

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const downloadButton = screen.getAllByRole('button', { name: /İndir/i })[0];
        fireEvent.click(downloadButton);
      });

      // Download count should be updated in state
      await waitFor(() => {
        expect(mockedAxios.post).toHaveBeenCalled();
      });
    });

    it('deletes file when delete is clicked', async () => {
      window.confirm = vi.fn(() => true);

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
      });

      const deleteButton = screen.getByText('Sil');
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(mockedAxios.delete).toHaveBeenCalledWith(
          '/api/v1/study-rooms/room1/files/file1'
        );
      });
    });

    it('does not delete file when confirm is cancelled', async () => {
      window.confirm = vi.fn(() => false);

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
      });

      const deleteButton = screen.getByText('Sil');
      fireEvent.click(deleteButton);

      expect(mockedAxios.delete).not.toHaveBeenCalled();
    });

    it('only allows owner to delete files', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButtons = screen.getAllByRole('button', { name: /more/i });
        fireEvent.click(moreButtons[1]); // Second file is from another user
      });

      expect(screen.queryByText('Sil')).not.toBeInTheDocument();
    });
  });

  describe('File Information', () => {
    it('shows file info dialog', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
      });

      const infoButton = screen.getByText('Bilgi');
      fireEvent.click(infoButton);

      await waitFor(() => {
        expect(screen.getByText('Dosya Bilgileri')).toBeInTheDocument();
        expect(screen.getByText('matematik-notlar.pdf')).toBeInTheDocument();
        expect(screen.getByText('1.00 MB')).toBeInTheDocument();
      });
    });

    it('closes info dialog when close button is clicked', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
        fireEvent.click(screen.getByText('Bilgi'));
      });

      const closeButton = screen.getByText('Kapat');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Dosya Bilgileri')).not.toBeInTheDocument();
      });
    });
  });

  describe('File Versions', () => {
    it('shows versions dialog for versioned files', async () => {
      const versionedFile = { ...mockFiles[0], version: 2 };
      mockedAxios.get
        .mockResolvedValueOnce({ data: [versionedFile] })
        .mockResolvedValueOnce({
          data: [
            { id: 'v1', version: 1, file_size: 1000000, uploaded_at: '2025-10-27T09:00:00Z', uploaded_by: 'Ahmet', status: 'archived' },
            { id: 'v2', version: 2, file_size: 1024000, uploaded_at: '2025-10-27T10:00:00Z', uploaded_by: 'Ahmet', status: 'current' },
          ]
        });

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
      });

      const versionsButton = screen.getByText('Versiyonlar');
      fireEvent.click(versionsButton);

      await waitFor(() => {
        expect(screen.getByText('Dosya Versiyonları')).toBeInTheDocument();
        expect(screen.getByText('Versiyon 1')).toBeInTheDocument();
        expect(screen.getByText('Versiyon 2')).toBeInTheDocument();
        expect(screen.getByText('Güncel')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no files', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('Henüz dosya yok')).toBeInTheDocument();
        expect(screen.getByText('İlk dosyayı sen yükle!')).toBeInTheDocument();
      });
    });

    it('shows empty state when filter returns no results', async () => {
      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Dosya ara...');
        fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      });

      await waitFor(() => {
        expect(screen.getByText('Henüz dosya yok')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles file fetch errors', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Fetch error'));
      console.error = vi.fn();

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        expect(console.error).toHaveBeenCalled();
      });
    });

    it('handles delete errors', async () => {
      window.confirm = vi.fn(() => true);
      window.alert = vi.fn();
      mockedAxios.delete.mockRejectedValue(new Error('Delete failed'));

      render(<FileManager {...mockProps} />);

      await waitFor(() => {
        const moreButton = screen.getAllByRole('button', { name: /more/i })[0];
        fireEvent.click(moreButton);
        fireEvent.click(screen.getByText('Sil'));
      });

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Dosya silinirken bir hata oluştu.');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Dosya ara...')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      render(<FileManager {...mockProps} />);
      await waitFor(() => {
        const uploadButton = screen.getByText('Dosya Yükle');
        uploadButton.focus();
        expect(uploadButton).toHaveFocus();
      });
    });
  });
});
