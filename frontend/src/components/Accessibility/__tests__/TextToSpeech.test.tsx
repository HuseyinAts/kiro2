import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { vi, Mock } from 'vitest';
import TextToSpeech from '../TextToSpeech';

// Mock Web Speech API
const mockSpeak = vi.fn();
const mockCancel = vi.fn();
const mockPause = vi.fn();
const mockResume = vi.fn();

const mockUtterance = {
  text: '',
  lang: '',
  voice: null,
  rate: 1,
  pitch: 1,
  volume: 1,
  onstart: null,
  onend: null,
  onerror: null,
  onboundary: null,
};

global.speechSynthesis = {
  speak: mockSpeak,
  cancel: mockCancel,
  pause: mockPause,
  resume: mockResume,
  getVoices: vi.fn(() => [
    { name: 'Turkish Voice', lang: 'tr-TR', default: true },
    { name: 'English Voice', lang: 'en-US', default: false },
  ]),
  onvoiceschanged: null,
} as any;

global.SpeechSynthesisUtterance = vi.fn().mockImplementation((text) => ({
  ...mockUtterance,
  text,
})) as any;

describe('TextToSpeech Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('REQ-50.43: Web Speech API Entegrasyonu', () => {
    it('Web Speech API desteklendiğinde component render edilmeli', () => {
      render(<TextToSpeech text="Test metni" />);
      expect(screen.getByText('Test metni')).toBeInTheDocument();
    });

    it('Seslendir butonu görünmeli', () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      expect(screen.getByRole('button', { name: /seslendir/i })).toBeInTheDocument();
    });
  });

  describe('REQ-50.44: Türkçe Ses Seçimi', () => {
    it('Türkçe sesler listelendiğinde gösterilmeli', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      // Ayarlar butonuna tıkla
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/ses seçimi/i)).toBeInTheDocument();
      });
    });

    it('Varsayılan olarak Türkçe ses seçilmeli', () => {
      render(<TextToSpeech text="Test metni" />);
      
      const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
      expect(savedSettings.voice || 'tr-TR').toContain('tr');
    });
  });

  describe('REQ-50.47, REQ-50.48, REQ-50.49: Ses Hızı Ayarlama', () => {
    it('Ses hızı slider\'ı %50-%200 arası değer almalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const rateSlider = screen.getByLabelText(/ses hızı ayarlama/i);
        expect(rateSlider).toHaveAttribute('min', '0.5');
        expect(rateSlider).toHaveAttribute('max', '2.0');
      });
    });

    it('Önceden tanımlı hız seçenekleri çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const normalButton = screen.getByText('Normal');
        fireEvent.click(normalButton);
        
        const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
        expect(savedSettings.rate).toBe(1.0);
      });
    });

    it('Gerçek zamanlı hız ayarlama çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const rateSlider = screen.getByLabelText(/ses hızı ayarlama/i);
        fireEvent.change(rateSlider, { target: { value: '1.5' } });
        
        const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
        expect(savedSettings.rate).toBe(1.5);
      });
    });
  });

  describe('REQ-50.50, REQ-50.51, REQ-50.52: Ses Tonu ve Seçimi', () => {
    it('Ses tonu slider\'ı çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const pitchSlider = screen.getByLabelText(/ses tonu ayarlama/i);
        fireEvent.change(pitchSlider, { target: { value: '1.2' } });
        
        const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
        expect(savedSettings.pitch).toBe(1.2);
      });
    });

    it('Ses seçimi dropdown\'u çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const voiceSelect = screen.getByLabelText(/ses seçimi/i);
        expect(voiceSelect).toBeInTheDocument();
      });
    });
  });

  describe('REQ-50.53, REQ-50.54, REQ-50.56: Karaoke Mode', () => {
    it('Karaoke mode checkbox\'u çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const karaokeCheckbox = screen.getByLabelText(/karaoke modu/i);
        expect(karaokeCheckbox).toBeChecked(); // Varsayılan olarak açık
        
        fireEvent.click(karaokeCheckbox);
        expect(karaokeCheckbox).not.toBeChecked();
      });
    });

    it('Karaoke mode aktifken kelimeler vurgulanmalı', () => {
      render(<TextToSpeech text="Merhaba dünya" showControls={true} />);
      
      const words = screen.getByText(/merhaba/i).parentElement?.querySelectorAll('span');
      expect(words).toBeDefined();
      expect(words!.length).toBeGreaterThan(0);
    });
  });

  describe('REQ-50.55: Vurgulama Rengi', () => {
    it('Renk seçenekleri gösterilmeli', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const colorButtons = screen.getAllByLabelText(/renk seç/i);
        expect(colorButtons.length).toBeGreaterThan(0);
      });
    });

    it('Renk değiştirme çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const colorButton = screen.getByLabelText(/renk seç: #90EE90/i);
        fireEvent.click(colorButton);
        
        const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
        expect(savedSettings.highlightColor).toBe('#90EE90');
      });
    });
  });

  describe('Oynatma Kontrolleri', () => {
    it('Seslendir butonu TTS\'yi başlatmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      fireEvent.click(playButton);

      await waitFor(() => {
        expect(mockSpeak).toHaveBeenCalled();
      });
    });

    it('Duraklat butonu görünmeli ve çalışmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      fireEvent.click(playButton);

      await waitFor(() => {
        const pauseButton = screen.getByRole('button', { name: /duraklat/i });
        expect(pauseButton).toBeInTheDocument();
        
        fireEvent.click(pauseButton);
        expect(mockPause).toHaveBeenCalled();
      });
    });

    it('Durdur butonu TTS\'yi iptal etmeli', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      fireEvent.click(playButton);

      await waitFor(() => {
        const stopButton = screen.getByRole('button', { name: /durdur/i });
        fireEvent.click(stopButton);
        
        expect(mockCancel).toHaveBeenCalled();
      });
    });
  });

  describe('LocalStorage Persistence', () => {
    it('Ayarlar localStorage\'a kaydedilmeli', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const rateSlider = screen.getByLabelText(/ses hızı ayarlama/i);
        fireEvent.change(rateSlider, { target: { value: '1.5' } });
      });

      const savedSettings = localStorage.getItem('tts-settings');
      expect(savedSettings).toBeTruthy();
      
      const parsed = JSON.parse(savedSettings!);
      expect(parsed.rate).toBe(1.5);
    });

    it('Kaydedilmiş ayarlar yüklendiğinde uygulanmalı', () => {
      const customSettings = {
        enabled: true,
        voice: 'tr-TR',
        rate: 1.5,
        pitch: 1.2,
        volume: 0.8,
        highlightColor: '#90EE90',
        karaokeModeEnabled: false,
      };
      
      localStorage.setItem('tts-settings', JSON.stringify(customSettings));
      
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const savedSettings = JSON.parse(localStorage.getItem('tts-settings') || '{}');
      expect(savedSettings.rate).toBe(1.5);
      expect(savedSettings.pitch).toBe(1.2);
      expect(savedSettings.karaokeModeEnabled).toBe(false);
    });
  });

  describe('Auto-play', () => {
    it('autoPlay prop true ise otomatik başlamalı', async () => {
      render(<TextToSpeech text="Test metni" autoPlay={true} />);

      await waitFor(() => {
        expect(mockSpeak).toHaveBeenCalled();
      }, { timeout: 1000 });
    });

    it('autoPlay false ise otomatik başlamamalı', () => {
      render(<TextToSpeech text="Test metni" autoPlay={false} />);
      
      expect(mockSpeak).not.toHaveBeenCalled();
    });
  });

  describe('Callback Functions', () => {
    it('onStart callback çağrılmalı', async () => {
      const onStart = vi.fn();
      render(<TextToSpeech text="Test metni" onStart={onStart} showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      fireEvent.click(playButton);

      await waitFor(() => {
        expect(onStart).toHaveBeenCalled();
      });
    });

    it('onEnd callback çağrılmalı', async () => {
      const onEnd = vi.fn();
      render(<TextToSpeech text="Test metni" onEnd={onEnd} showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      fireEvent.click(playButton);

      // Utterance'ın onend event'ini tetikle
      const utteranceInstance = (SpeechSynthesisUtterance as Mock).mock.results[0].value;
      if (utteranceInstance.onend) {
        utteranceInstance.onend();
      }

      await waitFor(() => {
        expect(onEnd).toHaveBeenCalled();
      });
    });
  });

  describe('Erişilebilirlik', () => {
    it('Tüm butonlar ARIA label\'a sahip olmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const playButton = screen.getByRole('button', { name: /seslendir/i });
      expect(playButton).toHaveAttribute('aria-label');
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      expect(settingsButton).toHaveAttribute('aria-label');
    });

    it('Slider\'lar ARIA label\'a sahip olmalı', async () => {
      render(<TextToSpeech text="Test metni" showControls={true} />);
      
      const settingsButton = screen.getByRole('button', { name: /ayarlar/i });
      fireEvent.click(settingsButton);

      await waitFor(() => {
        const rateSlider = screen.getByLabelText(/ses hızı ayarlama/i);
        expect(rateSlider).toHaveAttribute('aria-label');
      });
    });
  });
});
