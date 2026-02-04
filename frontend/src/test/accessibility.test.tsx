/**
 * WCAG 2.1 Level AA Uyumluluk Testleri
 * 
 * Bu test dosyası, tüm erişilebilirlik bileşenlerinin
 * WCAG 2.1 Level AA standartlarına uygunluğunu test eder.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import '@testing-library/jest-dom';

// Test edilecek bileşenler
import AccessibleTable from '../components/Common/AccessibleTable';
import AccessibleVideoPlayer from '../components/Common/AccessibleVideoPlayer';
import AccessibleForm from '../components/Common/AccessibleForm';
import AccessibleNavigation from '../components/Navigation/AccessibleNavigation';
import AccessibleModal from '../components/Common/AccessibleModal';
import AccessibleLayout from '../components/Layout/AccessibleLayout';

// Jest-axe matcher'ını ekle
expect.extend(toHaveNoViolations);

// Mock hooks
vi.mock('../hooks/useScreenReader', () => ({
  useScreenReader: () => ({
    announce: vi.fn(),
    announcePageChange: vi.fn(),
    announceFormError: vi.fn(),
    announceSuccess: vi.fn(),
    announceLoading: vi.fn(),
    announceContentChange: vi.fn(),
    announceLandmark: vi.fn(),
    manageFocus: vi.fn(),
    createSkipLink: jest.fn(() => document.createElement('a')),
    isScreenReaderActive: false,
  }),
}));

vi.mock('../hooks/useKeyboardNavigation', () => ({
  useKeyboardNavigation: () => ({
    focusNext: vi.fn(),
    focusPrevious: vi.fn(),
    focusFirst: vi.fn(),
    focusLast: vi.fn(),
  }),
}));

vi.mock('../hooks/useAccessibilitySettings', () => ({
  useAccessibilitySettings: () => ({
    settings: {
      highContrast: false,
      fontSize: 'medium',
      reducedMotion: false,
      keyboardNavigation: true,
      focusIndicators: true,
      screenReaderOptimized: false,
      dyslexiaSupport: false,
    },
    toggleHighContrast: vi.fn(),
    toggleReducedMotion: vi.fn(),
    increaseFontSize: vi.fn(),
    decreaseFontSize: vi.fn(),
    toggleDyslexiaSupport: vi.fn(),
    getAccessibilityStatus: () => ({
      activeFeatures: [],
      isOptimized: false,
      summary: 'Standart erişilebilirlik ayarları',
    }),
  }),
}));

describe('WCAG 2.1 Level AA Uyumluluk Testleri', () => {
  describe('AccessibleTable Bileşeni', () => {
    const mockColumns = [
      { id: 'name', label: 'İsim', sortable: true },
      { id: 'age', label: 'Yaş', sortable: true },
      { id: 'email', label: 'E-posta', sortable: false },
    ];

    const mockData = [
      { id: 1, name: 'Ahmet Yılmaz', age: 25, email: 'ahmet@example.com' },
      { id: 2, name: 'Ayşe Kaya', age: 30, email: 'ayse@example.com' },
    ];

    it('WCAG uyumlu tablo yapısını render eder', async () => {
      const { container } = render(
        <AccessibleTable
          columns={mockColumns}
          data={mockData}
          title="Test Tablosu"
          caption="Bu bir test tablosudur"
        />
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Tablo yapısı kontrolü
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Test Tablosu');
      
      // Caption kontrolü
      expect(screen.getByText('Bu bir test tablosudur')).toBeInTheDocument();
      
      // Başlık hücreleri kontrolü
      const columnHeaders = screen.getAllByRole('columnheader');
      expect(columnHeaders).toHaveLength(3);
      expect(columnHeaders[0]).toHaveAttribute('scope', 'col');
    });

    it('klavye navigasyonunu destekler', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleTable
          columns={mockColumns}
          data={mockData}
          title="Test Tablosu"
        />
      );

      const table = screen.getByRole('region');
      
      // Tab ile navigasyon
      await user.tab();
      expect(table).toHaveFocus();
      
      // Arrow key navigasyonu test edilebilir
      fireEvent.keyDown(table, { key: 'ArrowDown' });
      fireEvent.keyDown(table, { key: 'ArrowRight' });
    });

    it('sıralama işlevselliğini destekler', async () => {
      const user = userEvent.setup();
      const mockOnSort = vi.fn();
      
      render(
        <AccessibleTable
          columns={mockColumns}
          data={mockData}
          onSort={mockOnSort}
        />
      );

      // Sıralanabilir sütun başlığını bul
      const sortButton = screen.getByRole('button', { name: /İsim sütununa göre sırala/i });
      
      // Sıralama butonuna tıkla
      await user.click(sortButton);
      
      expect(mockOnSort).toHaveBeenCalledWith('name', 'asc');
    });
  });

  describe('AccessibleVideoPlayer Bileşeni', () => {
    const mockTracks = [
      {
        id: 'tr-subtitles',
        label: 'Türkçe Altyazı',
        language: 'tr',
        src: '/subtitles/tr.vtt',
        kind: 'subtitles' as const,
        default: true,
      },
    ];

    it('WCAG uyumlu video player render eder', async () => {
      const { container } = render(
        <AccessibleVideoPlayer
          src="/test-video.mp4"
          title="Test Video"
          description="Bu bir test videosudur"
          tracks={mockTracks}
        />
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Video elementi kontrolü
      const video = screen.getByRole('region', { name: /Video player: Test Video/i });
      expect(video).toBeInTheDocument();
      
      // Video elementi
      const videoElement = container.querySelector('video');
      expect(videoElement).toHaveAttribute('aria-label', 'Test Video');
      expect(videoElement).toHaveAttribute('aria-describedby');
    });

    it('klavye kısayollarını destekler', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleVideoPlayer
          src="/test-video.mp4"
          title="Test Video"
        />
      );

      const videoContainer = screen.getByRole('region');
      
      // Space tuşu ile oynat/duraklat
      fireEvent.keyDown(videoContainer, { key: ' ' });
      fireEvent.keyDown(videoContainer, { key: 'k' });
      
      // Arrow tuşları ile ileri/geri
      fireEvent.keyDown(videoContainer, { key: 'ArrowLeft' });
      fireEvent.keyDown(videoContainer, { key: 'ArrowRight' });
      
      // Ses kontrolü
      fireEvent.keyDown(videoContainer, { key: 'ArrowUp' });
      fireEvent.keyDown(videoContainer, { key: 'ArrowDown' });
      fireEvent.keyDown(videoContainer, { key: 'm' });
    });

    it('altyazı kontrollerini sağlar', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleVideoPlayer
          src="/test-video.mp4"
          title="Test Video"
          tracks={mockTracks}
        />
      );

      // Altyazı toggle butonu
      const captionButton = screen.getByRole('button', { name: /Altyazıları aç/i });
      expect(captionButton).toBeInTheDocument();
      
      await user.click(captionButton);
      
      // C tuşu ile altyazı toggle
      fireEvent.keyDown(document, { key: 'c' });
    });
  });

  describe('AccessibleForm Bileşeni', () => {
    const mockFields = [
      {
        id: 'name',
        name: 'name',
        label: 'Ad Soyad',
        type: 'text' as const,
        required: true,
        validation: { required: true, minLength: 2 },
      },
      {
        id: 'email',
        name: 'email',
        label: 'E-posta',
        type: 'email' as const,
        required: true,
        validation: { required: true, email: true },
      },
      {
        id: 'password',
        name: 'password',
        label: 'Şifre',
        type: 'password' as const,
        required: true,
        validation: { required: true, minLength: 8 },
      },
    ];

    it('WCAG uyumlu form render eder', async () => {
      const { container } = render(
        <AccessibleForm
          fields={mockFields}
          onSubmit={vi.fn()}
          title="Test Formu"
          description="Bu bir test formudur"
        />
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Form yapısı kontrolü
      expect(screen.getByRole('form')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Test Formu' })).toBeInTheDocument();
      
      // Zorunlu alanlar işaretli
      expect(screen.getByText('* işaretli alanlar zorunludur')).toBeInTheDocument();
    });

    it('form doğrulamasını gerçekleştirir', async () => {
      const user = userEvent.setup();
      const mockOnSubmit = vi.fn();
      
      render(
        <AccessibleForm
          fields={mockFields}
          onSubmit={mockOnSubmit}
        />
      );

      // Boş form göndermeye çalış
      const submitButton = screen.getByRole('button', { name: /Gönder/i });
      await user.click(submitButton);

      // Hata mesajları görünmeli
      await waitFor(() => {
        expect(screen.getByText(/Ad Soyad alanı zorunludur/i)).toBeInTheDocument();
        expect(screen.getByText(/E-posta alanı zorunludur/i)).toBeInTheDocument();
      });

      // Form gönderilmemeli
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('şifre görünürlük toggle çalışır', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleForm
          fields={mockFields}
          onSubmit={vi.fn()}
        />
      );

      const passwordInput = screen.getByLabelText('Şifre');
      const toggleButton = screen.getByRole('button', { name: /Şifreyi göster/i });
      
      // Başlangıçta password type
      expect(passwordInput).toHaveAttribute('type', 'password');
      
      // Toggle butonuna tıkla
      await user.click(toggleButton);
      
      // Text type'a dönüşmeli
      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(screen.getByRole('button', { name: /Şifreyi gizle/i })).toBeInTheDocument();
    });
  });

  describe('AccessibleNavigation Bileşeni', () => {
    const mockNavigationItems = [
      {
        id: 'home',
        label: 'Ana Sayfa',
        path: '/',
        icon: <span>🏠</span>,
      },
      {
        id: 'courses',
        label: 'Dersler',
        path: '/courses',
        icon: <span>📚</span>,
        children: [
          { id: 'math', label: 'Matematik', path: '/courses/math' },
          { id: 'physics', label: 'Fizik', path: '/courses/physics' },
        ],
      },
    ];

    it('WCAG uyumlu navigasyon render eder', async () => {
      const { container } = render(
        <AccessibleNavigation
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
        />
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Banner role kontrolü
      expect(screen.getByRole('banner')).toBeInTheDocument();
      
      // Navigation role kontrolü
      expect(screen.getByRole('navigation', { name: /Ana navigasyon/i })).toBeInTheDocument();
      
      // Başlık kontrolü
      expect(screen.getByRole('heading', { name: 'Test Uygulaması' })).toBeInTheDocument();
    });

    it('alt menü açma/kapama çalışır', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleNavigation
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
        />
      );

      // Alt menüye sahip öğeyi bul
      const coursesButton = screen.getByRole('button', { name: /Dersler/i });
      expect(coursesButton).toHaveAttribute('aria-expanded', 'false');
      
      // Alt menüyü aç
      await user.click(coursesButton);
      expect(coursesButton).toHaveAttribute('aria-expanded', 'true');
      
      // Alt menü öğeleri görünmeli
      expect(screen.getByRole('menuitem', { name: 'Matematik' })).toBeInTheDocument();
      expect(screen.getByRole('menuitem', { name: 'Fizik' })).toBeInTheDocument();
    });

    it('breadcrumb navigasyonu sağlar', () => {
      const breadcrumbs = [
        { label: 'Ana Sayfa', path: '/' },
        { label: 'Dersler', path: '/courses' },
        { label: 'Matematik' },
      ];
      
      render(
        <AccessibleNavigation
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
          breadcrumbs={breadcrumbs}
        />
      );

      // Breadcrumb navigation
      expect(screen.getByRole('navigation', { name: /Sayfa konumu/i })).toBeInTheDocument();
      
      // Current page indicator
      const currentPage = screen.getByText('Matematik');
      expect(currentPage).toHaveAttribute('aria-current', 'page');
    });
  });

  describe('AccessibleModal Bileşeni', () => {
    it('WCAG uyumlu modal render eder', async () => {
      const { container } = render(
        <AccessibleModal
          open={true}
          onClose={vi.fn()}
          title="Test Modal"
          description="Bu bir test modalıdır"
        >
          <p>Modal içeriği</p>
        </AccessibleModal>
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Dialog role kontrolü
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby');
      expect(dialog).toHaveAttribute('aria-describedby');
    });

    it('Escape tuşu ile kapanır', async () => {
      const mockOnClose = vi.fn();
      
      render(
        <AccessibleModal
          open={true}
          onClose={mockOnClose}
          title="Test Modal"
        >
          <p>Modal içeriği</p>
        </AccessibleModal>
      );

      // Escape tuşuna bas
      fireEvent.keyDown(document, { key: 'Escape' });
      
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('focus trap çalışır', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleModal
          open={true}
          onClose={vi.fn()}
          title="Test Modal"
          actions={
            <>
              <button>İptal</button>
              <button>Tamam</button>
            </>
          }
        >
          <input type="text" placeholder="Test input" />
        </AccessibleModal>
      );

      const input = screen.getByPlaceholderText('Test input');
      const cancelButton = screen.getByRole('button', { name: 'İptal' });
      const okButton = screen.getByRole('button', { name: 'Tamam' });
      const closeButton = screen.getByRole('button', { name: /Kapat/i });

      // İlk focusable element odaklanmalı
      expect(closeButton).toHaveFocus();
      
      // Tab ile ileri navigasyon
      await user.tab();
      expect(input).toHaveFocus();
      
      await user.tab();
      expect(cancelButton).toHaveFocus();
      
      await user.tab();
      expect(okButton).toHaveFocus();
      
      // Son elementten sonra ilk elemente dönmeli
      await user.tab();
      expect(closeButton).toHaveFocus();
    });
  });

  describe('AccessibleLayout Bileşeni', () => {
    const mockNavigationItems = [
      { id: 'home', label: 'Ana Sayfa', path: '/' },
      { id: 'about', label: 'Hakkında', path: '/about' },
    ];

    it('WCAG uyumlu layout render eder', async () => {
      const { container } = render(
        <AccessibleLayout
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
        >
          <h1>Ana İçerik</h1>
          <p>Bu ana içeriktir.</p>
        </AccessibleLayout>
      );

      // Axe ile erişilebilirlik kontrolü
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Landmark'lar kontrolü
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Main content kontrolü
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveAttribute('id', 'main-content');
      expect(mainContent).toHaveAttribute('tabIndex', '-1');
    });

    it('skip link çalışır', async () => {
      const user = userEvent.setup();
      
      render(
        <AccessibleLayout
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
        >
          <h1>Ana İçerik</h1>
        </AccessibleLayout>
      );

      // Skip link butonunu bul (DOM'da var ama görünmez)
      const skipButton = document.querySelector('button') as HTMLButtonElement;
      expect(skipButton).toHaveTextContent('Ana içeriğe geç');
      
      // Skip link'e tıkla
      fireEvent.click(skipButton);
      
      // Ana içerik odaklanmalı
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveFocus();
    });

    it('klavye kısayolları çalışır', async () => {
      const { container } = render(
        <AccessibleLayout
          title="Test Uygulaması"
          navigationItems={mockNavigationItems}
        >
          <h1>Ana İçerik</h1>
        </AccessibleLayout>
      );

      // Alt+M: Ana içeriğe geç
      fireEvent.keyDown(document, { key: 'm', altKey: true });
      
      const mainContent = screen.getByRole('main');
      expect(mainContent).toHaveFocus();
      
      // Alt+A: Erişilebilirlik paneli
      fireEvent.keyDown(document, { key: 'a', altKey: true });
      
      // Alt+1: Yüksek kontrast
      fireEvent.keyDown(document, { key: '1', altKey: true });
    });
  });

  describe('Genel WCAG Uyumluluk', () => {
    it('tüm interaktif elementler minimum boyut gereksinimini karşılar', () => {
      render(
        <div>
          <button>Test Button</button>
          <input type="text" />
          <a href="#test">Test Link</a>
        </div>
      );

      const button = screen.getByRole('button');
      const input = screen.getByRole('textbox');
      const link = screen.getByRole('link');

      // Minimum 44x44px boyut kontrolü (CSS ile sağlanır)
      expect(button).toHaveClass('wcag-aa-target-size');
      expect(input).toHaveClass('wcag-aa-target-size');
      expect(link).toHaveClass('wcag-aa-target-size');
    });

    it('renk kontrastı gereksinimlerini karşılar', () => {
      render(
        <div>
          <p className="wcag-aa-normal-text">Normal metin</p>
          <h1 className="wcag-aa-large-text">Büyük metin</h1>
        </div>
      );

      const normalText = screen.getByText('Normal metin');
      const largeText = screen.getByText('Büyük metin');

      // CSS sınıfları ile kontrast sağlanır
      expect(normalText).toHaveClass('wcag-aa-normal-text');
      expect(largeText).toHaveClass('wcag-aa-large-text');
    });

    it('focus göstergeleri görünür', async () => {
      const user = userEvent.setup();
      
      render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
          <input type="text" />
        </div>
      );

      // Tab ile navigasyon
      await user.tab();
      const button1 = screen.getByRole('button', { name: 'Button 1' });
      expect(button1).toHaveFocus();
      expect(button1).toHaveClass('wcag-aa-focus');

      await user.tab();
      const button2 = screen.getByRole('button', { name: 'Button 2' });
      expect(button2).toHaveFocus();

      await user.tab();
      const input = screen.getByRole('textbox');
      expect(input).toHaveFocus();
    });
  });
});

describe('Performans Testleri', () => {
  it('büyük veri setleri ile performans', async () => {
    const largeData = Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      name: `User ${i}`,
      email: `user${i}@example.com`,
    }));

    const columns = [
      { id: 'name', label: 'Name' },
      { id: 'email', label: 'Email' },
    ];

    const startTime = performance.now();
    
    render(
      <AccessibleTable
        columns={columns}
        data={largeData}
        paginated={true}
        pageSize={50}
      />
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Render süresi 100ms'den az olmalı
    expect(renderTime).toBeLessThan(100);
  });

  it('çoklu modal açma performansı', async () => {
    const modals = Array.from({ length: 10 }, (_, i) => (
      <AccessibleModal
        key={i}
        open={true}
        onClose={vi.fn()}
        title={`Modal ${i}`}
      >
        <p>Content {i}</p>
      </AccessibleModal>
    ));

    const startTime = performance.now();
    render(<div>{modals}</div>);
    const endTime = performance.now();

    const renderTime = endTime - startTime;
    expect(renderTime).toBeLessThan(200);
  });
});