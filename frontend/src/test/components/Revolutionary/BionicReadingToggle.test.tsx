/**
 * BionicReadingToggle Test Suite
 * Bionic Reading bileşeni için kapsamlı testler
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import BionicReadingToggle from '../../../components/Revolutionary/BionicReadingToggle';

// Mock fetch
global.fetch = vi.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('BionicReadingToggle', () => {
  const mockOnTextChange = vi.fn();
  const mockStudentId = 'test-student-123';

  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('mock-token');
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should render with initial state', () => {
    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    expect(screen.getByText('Türkçe Bionic Reading')).toBeInTheDocument();
    expect(screen.getByText('Disleksi için Türkçe\'ye özel okuma desteği')).toBeInTheDocument();
    expect(screen.getByText('🚀 DEVRİMSEL ÖZELLİK')).toBeInTheDocument();
  });

  it('should toggle Bionic Reading on/off', async () => {
    // Mock API response for preferences
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: false,
          bold_ratio: 0.4,
          min_word_length: 3,
          auto_apply: false
        }
      })
    });

    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    const toggle = screen.getByRole('checkbox', { name: /Bionic Reading/i });
    
    // Initially should be off
    expect(toggle).not.toBeChecked();

    // Mock API response for updating preferences
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {}
      })
    });

    // Toggle on
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(toggle).toBeChecked();
    });
  });

  it('should apply Bionic Reading to text', async () => {
    // Mock preferences API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: true,
          bold_ratio: 0.4,
          min_word_length: 3,
          auto_apply: false
        }
      })
    });

    // Mock Bionic Reading API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          original_text: 'Test metin',
          bionic_text: '**Te**st **me**tin',
          processing_time_ms: 150
        }
      })
    });

    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Wait for preferences to load
    await waitFor(() => {
      const toggle = screen.getByRole('checkbox', { name: /Bionic Reading/i });
      expect(toggle).toBeChecked();
    });

    // Enter text
    const textInput = screen.getByPlaceholderText(/Bionic Reading uygulanacak metni/);
    fireEvent.change(textInput, { target: { value: 'Test metin' } });

    // Wait for Bionic Reading to be applied
    await waitFor(() => {
      expect(screen.getByText(/Te/)).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    // Mock preferences API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: true,
          bold_ratio: 0.4,
          min_word_length: 3,
          auto_apply: false
        }
      })
    });

    // Mock failed Bionic Reading API
    (fetch as any).mockRejectedValueOnce(new Error('API Error'));

    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Wait for preferences to load
    await waitFor(() => {
      const toggle = screen.getByRole('checkbox', { name: /Bionic Reading/i });
      expect(toggle).toBeChecked();
    });

    // Enter text
    const textInput = screen.getByPlaceholderText(/Bionic Reading uygulanacak metni/);
    fireEvent.change(textInput, { target: { value: 'Test metin' } });

    // Should show fallback message
    await waitFor(() => {
      expect(screen.getByText(/Backend API kullanılamıyor/)).toBeInTheDocument();
    });
  });

  it('should open and close settings dialog', async () => {
    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Open settings
    const settingsButton = screen.getByText('Ayarlar');
    fireEvent.click(settingsButton);

    await waitFor(() => {
      expect(screen.getByText('Bionic Reading Ayarları')).toBeInTheDocument();
    });

    // Close settings
    const cancelButton = screen.getByText('İptal');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText('Bionic Reading Ayarları')).not.toBeInTheDocument();
    });
  });

  it('should use sample texts', async () => {
    // Mock preferences API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: true,
          bold_ratio: 0.4,
          min_word_length: 3,
          auto_apply: false
        }
      })
    });

    // Mock Bionic Reading API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          original_text: 'Çocuklar bahçede oynuyorlar ve çok eğleniyorlar.',
          bionic_text: '**Çoc**uklar **bah**çede **oyn**uyorlar ve **ço**k **eğl**eniyorlar.',
          processing_time_ms: 200
        }
      })
    });

    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Wait for preferences to load
    await waitFor(() => {
      const toggle = screen.getByRole('checkbox', { name: /Bionic Reading/i });
      expect(toggle).toBeChecked();
    });

    // Click on first sample text
    const sampleButton = screen.getByText('Örnek 1');
    fireEvent.click(sampleButton);

    // Check if text input is filled
    const textInput = screen.getByPlaceholderText(/Bionic Reading uygulanacak metni/);
    expect(textInput).toHaveValue('Çocuklar bahçede oynuyorlar ve çok eğleniyorlar.');
  });

  it('should show dyslexia support component', () => {
    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    expect(screen.getByText('Disleksi Desteği')).toBeInTheDocument();
    expect(screen.getByText('ERİŞİLEBİLİRLİK')).toBeInTheDocument();
  });

  it('should handle auto-apply toggle', async () => {
    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    const autoApplyToggle = screen.getByRole('checkbox', { name: /Otomatik Uygula/i });
    
    // Toggle auto-apply
    fireEvent.click(autoApplyToggle);

    // Should update state
    expect(autoApplyToggle).toBeChecked();
  });

  it('should show info dialog', async () => {
    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Click info button
    const infoButton = screen.getByLabelText(/info/i);
    fireEvent.click(infoButton);

    await waitFor(() => {
      expect(screen.getByText('🚀 Türkçe Bionic Reading Hakkında')).toBeInTheDocument();
    });

    // Close dialog
    const closeButton = screen.getByText('Kapat');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('🚀 Türkçe Bionic Reading Hakkında')).not.toBeInTheDocument();
    });
  });

  it('should call onTextChange when Bionic Reading is applied', async () => {
    // Mock preferences API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          enabled: true,
          bold_ratio: 0.4,
          min_word_length: 3,
          auto_apply: false
        }
      })
    });

    // Mock Bionic Reading API
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          original_text: 'Test metin',
          bionic_text: '**Te**st **me**tin',
          processing_time_ms: 150
        }
      })
    });

    render(
      <BionicReadingToggle
        studentId={mockStudentId}
        onTextChange={mockOnTextChange}
      />
    );

    // Wait for preferences to load and toggle to be enabled
    await waitFor(() => {
      const toggle = screen.getByRole('checkbox', { name: /Bionic Reading/i });
      expect(toggle).toBeChecked();
    });

    // Enter text
    const textInput = screen.getByPlaceholderText(/Bionic Reading uygulanacak metni/);
    fireEvent.change(textInput, { target: { value: 'Test metin' } });

    // Wait for API call and callback
    await waitFor(() => {
      expect(mockOnTextChange).toHaveBeenCalledWith('**Te**st **me**tin', true);
    });
  });
});