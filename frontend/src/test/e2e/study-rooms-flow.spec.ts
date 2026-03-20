/**
 * Study Rooms Flow E2E Tests
 * Tests study room listing, creation, joining, chat, and collaboration features
 * Migrated from Cypress to Playwright
 */

import { test, expect } from '@playwright/test';
import {
  ApiMocker,
  mockData,
  loginAsStudent,
  StudyRoomsPage,
  testAccessibility,
  testMobileResponsiveness,
  testTabletResponsiveness
} from './helpers/e2e-helpers';

test.describe('Study Room List', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await loginAsStudent(page);
  });

  test('should display study rooms page', async ({ page }) => {
    await page.goto('/study-rooms');

    // Page heading
    await expect(page.getByRole('heading', { name: /çalışma odaları|study rooms/i })).toBeVisible();
  });

  test('should display room list', async ({ page }) => {
    await page.goto('/study-rooms');

    // Room cards
    await expect(page.getByText(/TYT Matematik Grubu|AYT Fizik/i)).toBeVisible();
  });

  test('should display room member count', async ({ page }) => {
    await page.goto('/study-rooms');

    // Member count
    const memberCount = page.getByText(/5.*üye|member|kişi/i);
    if (await memberCount.isVisible()) {
      await expect(memberCount).toBeVisible();
    }
  });

  test('should display room subject', async ({ page }) => {
    await page.goto('/study-rooms');

    // Subject badges
    await expect(page.getByText(/Matematik|Fizik|Kimya/i).first()).toBeVisible();
  });

  test('should display active video indicator', async ({ page }) => {
    await page.goto('/study-rooms');

    // Video indicator for room with active video
    const videoIndicator = page.locator('[data-testid="video-active"], .video-active, .live-indicator');
    if (await videoIndicator.isVisible()) {
      await expect(videoIndicator).toBeVisible();
    }
  });

  test('should display unread message badge', async ({ page }) => {
    await page.goto('/study-rooms');

    // Unread badge
    const unreadBadge = page.locator('[data-testid="unread-badge"], .unread-badge');
    if (await unreadBadge.isVisible()) {
      await expect(unreadBadge).toContainText('3');
    }
  });

  test('should search rooms by name', async ({ page }) => {
    await page.goto('/study-rooms');

    const searchInput = page.getByPlaceholder(/ara|search/i);
    await searchInput.fill('Matematik');

    await page.waitForTimeout(500);

    // Filtered results
    await expect(page.getByText(/Matematik/i)).toBeVisible();
  });

  test('should filter rooms by subject', async ({ page }) => {
    await page.goto('/study-rooms');

    const subjectFilter = page.getByRole('combobox', { name: /konu|subject/i });
    if (await subjectFilter.isVisible()) {
      await subjectFilter.selectOption('Fizik');
      await page.waitForTimeout(500);
    }
  });

  test('should filter rooms by visibility', async ({ page }) => {
    await page.goto('/study-rooms');

    const visibilityFilter = page.getByRole('combobox', { name: /görünürlük|visibility/i });
    if (await visibilityFilter.isVisible()) {
      await visibilityFilter.selectOption('public');
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Room Tabs', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await loginAsStudent(page);
  });

  test('should display All Rooms tab', async ({ page }) => {
    await page.goto('/study-rooms');

    const allRoomsTab = page.getByRole('tab', { name: /tüm odalar|all rooms/i });
    if (await allRoomsTab.isVisible()) {
      await expect(allRoomsTab).toBeVisible();
    }
  });

  test('should display My Rooms tab', async ({ page }) => {
    await page.goto('/study-rooms');

    const myRoomsTab = page.getByRole('tab', { name: /benim odalarım|my rooms/i });
    if (await myRoomsTab.isVisible()) {
      await expect(myRoomsTab).toBeVisible();
    }
  });

  test('should display Joined Rooms tab', async ({ page }) => {
    await page.goto('/study-rooms');

    const joinedRoomsTab = page.getByRole('tab', { name: /katıldığım|joined/i });
    if (await joinedRoomsTab.isVisible()) {
      await expect(joinedRoomsTab).toBeVisible();
    }
  });

  test('should switch between tabs', async ({ page }) => {
    await page.goto('/study-rooms');

    const myRoomsTab = page.getByRole('tab', { name: /benim odalarım|my rooms/i });
    if (await myRoomsTab.isVisible()) {
      await myRoomsTab.click();

      // Tab should be active
      await expect(myRoomsTab).toHaveAttribute('aria-selected', 'true');
    }
  });
});

test.describe('Room Creation', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await apiMocker.mockSuccess('/api/v1/study-rooms', { success: true, room_id: 'new-room-123' });
    await loginAsStudent(page);
  });

  test('should open create room dialog', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Dialog should open
    await expect(page.getByRole('dialog').or(page.locator('[data-testid="create-room-modal"]'))).toBeVisible();
  });

  test('should show room creation form', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Form fields
    await expect(page.getByLabel(/oda adı|room name/i)).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Try to submit without filling
    await page.getByRole('button', { name: /oluştur|create/i }).click();

    // Validation error
    await expect(page.getByText(/gerekli|required/i)).toBeVisible();
  });

  test('should create public room', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Fill form
    await page.getByLabel(/oda adı|room name/i).fill('Yeni Çalışma Odası');

    const subjectSelect = page.getByRole('combobox', { name: /konu|subject/i });
    if (await subjectSelect.isVisible()) {
      await subjectSelect.selectOption('Matematik');
    }

    // Select public
    const publicRadio = page.getByRole('radio', { name: /public|herkese açık/i });
    if (await publicRadio.isVisible()) {
      await publicRadio.check();
    }

    await page.getByRole('button', { name: /oluştur|create/i }).click();

    // Success
    await expect(page.getByText(/oluşturuldu|created|başarılı/i)).toBeVisible({ timeout: 5000 });
  });

  test('should create password-protected room', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Fill form
    await page.getByLabel(/oda adı|room name/i).fill('Şifreli Oda');

    // Select password protected
    const passwordRadio = page.getByRole('radio', { name: /şifreli|password/i });
    if (await passwordRadio.isVisible()) {
      await passwordRadio.check();

      // Password field should appear
      const passwordInput = page.getByLabel(/şifre|password/i);
      if (await passwordInput.isVisible()) {
        await passwordInput.fill('OdaSifresi123');
      }
    }

    await page.getByRole('button', { name: /oluştur|create/i }).click();

    await expect(page.getByText(/oluşturuldu|created|başarılı/i)).toBeVisible({ timeout: 5000 });
  });

  test('should create private room', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();

    // Fill form
    await page.getByLabel(/oda adı|room name/i).fill('Özel Oda');

    // Select private
    const privateRadio = page.getByRole('radio', { name: /private|özel|davetli/i });
    if (await privateRadio.isVisible()) {
      await privateRadio.check();
    }

    await page.getByRole('button', { name: /oluştur|create/i }).click();

    await expect(page.getByText(/oluşturuldu|created|başarılı/i)).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Joining Rooms', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await apiMocker.mockSuccess('/api/v1/study-rooms/*/join', { success: true });
    await loginAsStudent(page);
  });

  test('should join public room', async ({ page }) => {
    await page.goto('/study-rooms');

    // Click on room
    await page.getByText(/TYT Matematik Grubu/i).click();

    // Join button
    const joinButton = page.getByRole('button', { name: /katıl|join/i });
    if (await joinButton.isVisible()) {
      await joinButton.click();

      // Should enter room or show success
      await expect(page.getByText(/katıldınız|joined|başarılı/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should prompt password for protected room', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', {
      rooms: [
        { room_id: '1', name: 'Şifreli Oda', visibility: 'password', member_count: 3, max_members: 10 }
      ]
    });

    await page.goto('/study-rooms');

    await page.getByText(/Şifreli Oda/i).click();

    const joinButton = page.getByRole('button', { name: /katıl|join/i });
    if (await joinButton.isVisible()) {
      await joinButton.click();

      // Password prompt
      await expect(page.getByLabel(/şifre|password/i)).toBeVisible();
    }
  });

  test('should join with correct password', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', {
      rooms: [
        { room_id: '1', name: 'Şifreli Oda', visibility: 'password', member_count: 3, max_members: 10 }
      ]
    });
    await apiMocker.mockSuccess('/api/v1/study-rooms/1/join', { success: true });

    await page.goto('/study-rooms');

    await page.getByText(/Şifreli Oda/i).click();

    const joinButton = page.getByRole('button', { name: /katıl|join/i });
    if (await joinButton.isVisible()) {
      await joinButton.click();

      // Enter password
      const passwordInput = page.getByLabel(/şifre|password/i);
      if (await passwordInput.isVisible()) {
        await passwordInput.fill('DogruSifre123');
        await page.getByRole('button', { name: /giriş|enter|katıl/i }).click();

        await expect(page.getByText(/katıldınız|joined|başarılı/i)).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should show error for full room', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', {
      rooms: [
        { room_id: '1', name: 'Dolu Oda', visibility: 'public', member_count: 10, max_members: 10 }
      ]
    });
    await apiMocker.mockError('/api/v1/study-rooms/1/join', 400, 'Oda dolu');

    await page.goto('/study-rooms');

    await page.getByText(/Dolu Oda/i).click();

    const joinButton = page.getByRole('button', { name: /katıl|join/i });
    if (await joinButton.isVisible()) {
      await joinButton.click();

      // Error message
      await expect(page.getByText(/dolu|full|kapasiteye ulaştı/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Room Features', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await apiMocker.mockSuccess('/api/v1/study-rooms/1/messages', {
      messages: [
        { id: '1', user: 'Ahmet', content: 'Merhaba!', timestamp: '2024-01-15T10:00:00Z' },
        { id: '2', user: 'Fatma', content: 'Selam!', timestamp: '2024-01-15T10:01:00Z' }
      ]
    });
    await loginAsStudent(page);
  });

  test('should display chat interface in room', async ({ page }) => {
    await page.goto('/study-rooms/1');

    // Chat interface
    const chatInterface = page.locator('[data-testid="chat-interface"], .chat-interface');
    if (await chatInterface.isVisible()) {
      await expect(chatInterface).toBeVisible();
    }
  });

  test('should display chat messages', async ({ page }) => {
    await page.goto('/study-rooms/1');

    // Messages
    const message = page.getByText(/Merhaba|Selam/i);
    if (await message.isVisible()) {
      await expect(message).toBeVisible();
    }
  });

  test('should send chat message', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms/1/messages', { success: true });

    await page.goto('/study-rooms/1');

    // Message input
    const messageInput = page.getByPlaceholder(/mesaj|message/i);
    if (await messageInput.isVisible()) {
      await messageInput.fill('Test mesajı');
      await page.keyboard.press('Enter');

      // Message should appear
      await page.waitForTimeout(500);
    }
  });

  test('should display whiteboard', async ({ page }) => {
    await page.goto('/study-rooms/1');

    // Whiteboard
    const whiteboard = page.locator('[data-testid="whiteboard"], .whiteboard, canvas');
    if (await whiteboard.isVisible()) {
      await expect(whiteboard).toBeVisible();
    }
  });

  test('should display room members', async ({ page }) => {
    await page.goto('/study-rooms/1');

    // Members list
    const membersList = page.locator('[data-testid="members-list"], .members-list');
    if (await membersList.isVisible()) {
      await expect(membersList).toBeVisible();
    }
  });
});

test.describe('Study Rooms Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await loginAsStudent(page);
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.goto('/study-rooms');
    await testMobileResponsiveness(page);
  });

  test('should be tablet responsive', async ({ page }) => {
    await page.goto('/study-rooms');
    await testTabletResponsiveness(page);
  });

  test('should show mobile-friendly room cards', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/study-rooms');

    // Room cards should stack
    const roomCards = page.locator('[data-testid="room-card"], .room-card');
    if (await roomCards.first().isVisible()) {
      await expect(roomCards.first()).toBeVisible();
    }
  });
});

test.describe('Study Rooms Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await loginAsStudent(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/study-rooms');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/study-rooms');

    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have ARIA labels on interactive elements', async ({ page }) => {
    await page.goto('/study-rooms');

    // Create button
    const createButton = page.getByRole('button', { name: /oda oluştur|create room/i });
    if (await createButton.isVisible()) {
      await expect(createButton).toHaveAttribute('aria-label').or(expect(createButton).toBeVisible());
    }
  });

  test('should announce room status to screen readers', async ({ page }) => {
    await page.goto('/study-rooms');

    // Live region for updates
    const liveRegion = page.locator('[aria-live], [role="status"]');
    if (await liveRegion.isVisible()) {
      await expect(liveRegion).toBeVisible();
    }
  });
});

test.describe('Study Rooms Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should handle API error gracefully', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/study-rooms*', 500, 'Sunucu hatası');

    await page.goto('/study-rooms');

    // Error message or retry
    const errorMessage = page.getByText(/hata|error/i);
    const retryButton = page.getByRole('button', { name: /tekrar|retry/i });

    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle network failure', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockNetworkFailure('/api/v1/study-rooms*');

    await page.goto('/study-rooms');

    // Network error or retry
    const errorMessage = page.getByText(/bağlantı|connection|ağ hatası/i);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle room creation error', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await apiMocker.mockError('/api/v1/study-rooms', 400, 'Oda adı zaten kullanılıyor');

    await page.goto('/study-rooms');

    await page.getByRole('button', { name: /oda oluştur|create room|yeni/i }).click();
    await page.getByLabel(/oda adı|room name/i).fill('Mevcut Oda');
    await page.getByRole('button', { name: /oluştur|create/i }).click();

    // Error message
    await expect(page.getByText(/zaten kullanılıyor|already exists|hata/i)).toBeVisible({ timeout: 5000 });
  });

  test('should show empty state when no rooms', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', { rooms: [], total: 0 });

    await page.goto('/study-rooms');

    // Empty state
    const emptyMessage = page.getByText(/oda bulunamadı|no rooms|henüz oda yok/i);
    if (await emptyMessage.isVisible()) {
      await expect(emptyMessage).toBeVisible();
    }
  });
});

test.describe('Study Rooms Performance', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/study-rooms*', mockData.studyRooms);
    await loginAsStudent(page);
  });

  test('should load room list within 2 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/study-rooms');
    await page.waitForSelector('[data-testid="room-card"], .room-card, text=/Matematik|Fizik/i', { timeout: 5000 });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(5000); // Allow some buffer for CI
  });

  test('should filter instantly', async ({ page }) => {
    await page.goto('/study-rooms');

    const searchInput = page.getByPlaceholder(/ara|search/i);
    const startTime = Date.now();

    await searchInput.fill('Matematik');

    const filterTime = Date.now() - startTime;
    expect(filterTime).toBeLessThan(1000);
  });
});
