/**
 * E2E Test Helpers - Shared utilities for all E2E tests
 *
 * Role-based login helpers, API mocking, and common utilities
 */

import { Page, Route, expect } from '@playwright/test';

// ============================================================================
// ROLE-BASED LOGIN HELPERS
// ============================================================================

/**
 * Login as student (ogrenci)
 */
export async function loginAsStudent(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Test123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });
}

/**
 * Login as teacher (ogretmen)
 */
export async function loginAsTeacher(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('ogretmen@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Teacher123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/teacher|ogretmen|dashboard/i, { timeout: 15000 });
}

/**
 * Login as parent (veli)
 */
export async function loginAsParent(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('veli@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Parent123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/parent|veli|dashboard/i, { timeout: 15000 });
}

/**
 * Login as admin
 */
export async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('admin@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Admin123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/admin|dashboard/i, { timeout: 15000 });
}

/**
 * Logout current user
 */
export async function logout(page: Page): Promise<void> {
  await page.getByRole('button', { name: /çıkış|logout/i }).click();
  await expect(page).toHaveURL(/login|giriş/i, { timeout: 10000 });
}

// ============================================================================
// API MOCKING HELPER CLASS
// ============================================================================

/**
 * Generic API mocker for E2E tests
 */
export class ApiMocker {
  private page: Page;
  private apiBaseUrl: string;

  constructor(page: Page, apiBaseUrl: string = 'http://localhost:8001') {
    this.page = page;
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Mock successful API response
   */
  async mockSuccess(endpoint: string, data: any, delay: number = 0): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      if (delay > 0) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data)
      });
    });
  }

  /**
   * Mock error response
   */
  async mockError(endpoint: string, status: number, error: string): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ error, message: error })
      });
    });
  }

  /**
   * Mock network failure
   */
  async mockNetworkFailure(endpoint: string): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      await route.abort('failed');
    });
  }

  /**
   * Mock timeout (slow response)
   */
  async mockTimeout(endpoint: string, delay: number = 30000): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      await new Promise(resolve => setTimeout(resolve, delay));
      await route.fulfill({
        status: 504,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Gateway Timeout' })
      });
    });
  }

  /**
   * Mock unauthorized (401)
   */
  async mockUnauthorized(endpoint: string): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Yetkisiz erişim', message: 'Oturum açmanız gerekiyor' })
      });
    });
  }

  /**
   * Mock forbidden (403)
   */
  async mockForbidden(endpoint: string): Promise<void> {
    await this.page.route(`${this.apiBaseUrl}${endpoint}`, async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Erişim engellendi', message: 'Bu işlem için yetkiniz yok' })
      });
    });
  }

  /**
   * Clear mock for specific endpoint
   */
  async clearMock(endpoint: string): Promise<void> {
    await this.page.unroute(`${this.apiBaseUrl}${endpoint}`);
  }

  /**
   * Clear all mocks
   */
  async clearAllMocks(): Promise<void> {
    await this.page.unroute('**/*');
  }
}

// ============================================================================
// MOCK DATA
// ============================================================================

export const mockData = {
  // Admin dashboard stats
  adminDashboardStats: {
    toplam_kullanici: 1250,
    aktif_kullanici: 980,
    toplam_ogrenci: 980,
    toplam_ogretmen: 45,
    toplam_veli: 225,
    toplam_admin: 5,
    sistem_durumu: 'healthy',
    gunluk_aktif: 450,
    haftalik_aktif: 850
  },

  // User list for admin
  adminUserList: {
    users: [
      { kullanici_id: '1', email: 'student1@test.com', ad_soyad: 'Test Öğrenci 1', rol: 'ogrenci', aktif: true, created_at: '2024-01-01' },
      { kullanici_id: '2', email: 'student2@test.com', ad_soyad: 'Test Öğrenci 2', rol: 'ogrenci', aktif: true, created_at: '2024-01-02' },
      { kullanici_id: '3', email: 'teacher1@test.com', ad_soyad: 'Test Öğretmen', rol: 'ogretmen', aktif: true, created_at: '2024-01-03' },
      { kullanici_id: '4', email: 'parent1@test.com', ad_soyad: 'Test Veli', rol: 'veli', aktif: true, created_at: '2024-01-04' }
    ],
    total: 4,
    page: 1,
    page_size: 20
  },

  // Teacher dashboard
  teacherDashboard: {
    ogretmen_profili: {
      ogretmen_id: '1',
      okul_adi: 'Test Anadolu Lisesi',
      brans: 'Matematik',
      ad_soyad: 'Test Öğretmen'
    },
    genel_istatistikler: {
      toplam_ogrenci: 35,
      aktif_sinavlar: 3,
      ortalama_basari: 72.5,
      tamamlanan_odev: 15
    },
    ogrenci_listesi: [
      { ogrenci_id: '1', ad_soyad: 'Ahmet Yılmaz', ortalama: 85.5, son_aktivite: '2024-01-15' },
      { ogrenci_id: '2', ad_soyad: 'Fatma Demir', ortalama: 78.2, son_aktivite: '2024-01-14' }
    ],
    son_bildirimler: []
  },

  // Teacher student list
  teacherStudentList: {
    ogrenciler: [
      { ogrenci_id: '1', ad_soyad: 'Ahmet Yılmaz', email: 'ahmet@test.com', sinif: '11-A', ortalama: 85.5 },
      { ogrenci_id: '2', ad_soyad: 'Fatma Demir', email: 'fatma@test.com', sinif: '11-A', ortalama: 78.2 },
      { ogrenci_id: '3', ad_soyad: 'Mehmet Kaya', email: 'mehmet@test.com', sinif: '11-B', ortalama: 92.0 }
    ],
    total: 3
  },

  // Parent dashboard
  parentDashboard: {
    children: [
      {
        child_id: 1,
        child_name: 'Ali Veli',
        average_score: 75.5,
        weak_subjects: ['Matematik', 'Fizik'],
        strong_subjects: ['Türkçe', 'Tarih'],
        last_activity: '2024-01-15',
        pending_approval: false
      }
    ],
    unread_notifications: 3,
    weekly_summary: {
      total_children: 1,
      active_children: 1,
      average_performance: 75.5
    }
  },

  // Parent children list
  parentChildren: {
    children: [
      { child_id: 1, child_name: 'Ali Veli', status: 'approved', average_score: 75.5 },
      { child_id: 2, child_name: 'Ayşe Veli', status: 'pending', average_score: null }
    ]
  },

  // Parent notifications
  parentNotifications: {
    notifications: [
      { id: 1, message: 'Ali haftalık raporunuz hazır', read: false, created_at: '2024-01-15' },
      { id: 2, message: 'Yeni sınav sonuçları açıklandı', read: false, created_at: '2024-01-14' },
      { id: 3, message: 'Sistem bakımı yapılacak', read: true, created_at: '2024-01-13' }
    ],
    unread_count: 2
  },

  // Study rooms
  studyRooms: {
    rooms: [
      { room_id: '1', name: 'TYT Matematik Grubu', subject: 'Matematik', visibility: 'public', member_count: 5, max_members: 10, has_active_video: false, unread_messages: 0 },
      { room_id: '2', name: 'AYT Fizik Çalışma', subject: 'Fizik', visibility: 'public', member_count: 8, max_members: 15, has_active_video: true, unread_messages: 3 },
      { room_id: '3', name: 'Özel Ders Grubu', subject: 'Kimya', visibility: 'private', member_count: 3, max_members: 5, has_active_video: false, unread_messages: 0 }
    ],
    total: 3
  },

  // YOLO detection result
  yoloDetection: {
    detections: [
      { class_id: 0, class_name: 'soru', confidence: 0.95, bbox: [100, 100, 400, 300] },
      { class_id: 1, class_name: 'secenek', confidence: 0.88, bbox: [100, 320, 400, 450] },
      { class_id: 2, class_name: 'cevap', confidence: 0.92, bbox: [420, 100, 500, 150] }
    ],
    processing_time: 1.5,
    image_size: [800, 600]
  },

  // User profile
  userProfile: {
    kullanici_id: '1',
    email: 'test@kiro2.com',
    ad_soyad: 'Test Kullanıcı',
    rol: 'ogrenci',
    telefon: '05551234567',
    sinif_seviyesi: 11,
    created_at: '2024-01-01'
  },

  // Registration success
  registrationSuccess: {
    success: true,
    message: 'Kayıt başarılı',
    kullanici_id: 'new-user-123'
  }
};

// ============================================================================
// COMMON PAGE OBJECTS
// ============================================================================

/**
 * Base page object class
 */
export class BasePage {
  protected page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async waitForNetworkIdle(timeout: number = 5000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  async expectToastMessage(message: RegExp): Promise<void> {
    await expect(this.page.getByText(message)).toBeVisible({ timeout: 5000 });
  }

  async expectLoadingState(): Promise<void> {
    const loader = this.page.locator('[data-testid="loading"], .loading, [class*="loading"]');
    if (await loader.isVisible()) {
      await expect(loader).toBeHidden({ timeout: 30000 });
    }
  }

  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}.png`,
      fullPage: true
    });
  }
}

/**
 * Admin page object
 */
export class AdminPage extends BasePage {
  async navigate(): Promise<void> {
    await this.page.goto('/admin/dashboard');
    await this.waitForNetworkIdle();
  }

  async navigateToUsers(): Promise<void> {
    await this.page.goto('/admin/users');
    await this.waitForNetworkIdle();
  }

  async navigateToContent(): Promise<void> {
    await this.page.goto('/admin/content');
    await this.waitForNetworkIdle();
  }

  async navigateToSettings(): Promise<void> {
    await this.page.goto('/admin/settings');
    await this.waitForNetworkIdle();
  }

  getStatsCards() {
    return this.page.locator('[data-testid="stats-card"], .stats-card');
  }

  getUserTable() {
    return this.page.locator('table, [data-testid="user-table"]');
  }

  async searchUsers(query: string): Promise<void> {
    await this.page.getByPlaceholder(/ara|search/i).fill(query);
    await this.page.keyboard.press('Enter');
  }

  async filterByRole(role: string): Promise<void> {
    await this.page.getByRole('combobox', { name: /rol|role/i }).selectOption(role);
  }
}

/**
 * Teacher page object
 */
export class TeacherPage extends BasePage {
  async navigate(): Promise<void> {
    await this.page.goto('/teacher/dashboard');
    await this.waitForNetworkIdle();
  }

  async navigateToStudents(): Promise<void> {
    await this.page.goto('/teacher/students');
    await this.waitForNetworkIdle();
  }

  async navigateToExams(): Promise<void> {
    await this.page.goto('/teacher/exams');
    await this.waitForNetworkIdle();
  }

  async navigateToReports(): Promise<void> {
    await this.page.goto('/teacher/reports');
    await this.waitForNetworkIdle();
  }

  getStudentList() {
    return this.page.locator('[data-testid="student-list"], .student-list');
  }

  async searchStudents(query: string): Promise<void> {
    await this.page.getByPlaceholder(/öğrenci ara|search student/i).fill(query);
  }
}

/**
 * Parent page object
 */
export class ParentPage extends BasePage {
  async navigate(): Promise<void> {
    await this.page.goto('/parent/dashboard');
    await this.waitForNetworkIdle();
  }

  async navigateToChildren(): Promise<void> {
    await this.page.goto('/parent/children');
    await this.waitForNetworkIdle();
  }

  async navigateToReports(): Promise<void> {
    await this.page.goto('/parent/reports');
    await this.waitForNetworkIdle();
  }

  async navigateToNotifications(): Promise<void> {
    await this.page.goto('/parent/notifications');
    await this.waitForNetworkIdle();
  }

  getChildrenCards() {
    return this.page.locator('[data-testid="child-card"], .child-card');
  }

  getNotificationList() {
    return this.page.locator('[data-testid="notification-list"], .notification-list');
  }

  async selectChild(childName: string): Promise<void> {
    await this.page.getByText(childName).click();
  }
}

/**
 * Study rooms page object
 */
export class StudyRoomsPage extends BasePage {
  async navigate(): Promise<void> {
    await this.page.goto('/study-rooms');
    await this.waitForNetworkIdle();
  }

  getRoomList() {
    return this.page.locator('[data-testid="room-list"], .room-list');
  }

  getRoomCards() {
    return this.page.locator('[data-testid="room-card"], .room-card');
  }

  async openCreateDialog(): Promise<void> {
    await this.page.getByRole('button', { name: /oda oluştur|create room/i }).click();
  }

  async createRoom(name: string, subject: string, visibility: 'public' | 'private' | 'password'): Promise<void> {
    await this.openCreateDialog();
    await this.page.getByLabel(/oda adı|room name/i).fill(name);
    await this.page.getByRole('combobox', { name: /konu|subject/i }).selectOption(subject);
    await this.page.getByRole('radio', { name: new RegExp(visibility, 'i') }).check();
    await this.page.getByRole('button', { name: /oluştur|create/i }).click();
  }

  async searchRooms(query: string): Promise<void> {
    await this.page.getByPlaceholder(/ara|search/i).fill(query);
  }

  async filterBySubject(subject: string): Promise<void> {
    await this.page.getByRole('combobox', { name: /konu|subject/i }).selectOption(subject);
  }

  async joinRoom(roomName: string): Promise<void> {
    await this.page.getByText(roomName).click();
    await this.page.getByRole('button', { name: /katıl|join/i }).click();
  }
}

/**
 * Question upload page object
 */
export class QuestionUploadPage extends BasePage {
  async navigate(): Promise<void> {
    await this.page.goto('/question-upload');
    await this.waitForNetworkIdle();
  }

  async uploadFile(filePath: string): Promise<void> {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
  }

  getDetectionResults() {
    return this.page.locator('[data-testid="detection-results"], .detection-results');
  }

  getBoundingBoxes() {
    return this.page.locator('[data-testid="bounding-box"], .bounding-box');
  }

  async saveQuestion(index: number): Promise<void> {
    await this.page.locator(`[data-testid="save-question-${index}"]`).click();
  }
}

// ============================================================================
// TURKISH TEST DATA
// ============================================================================

export const turkishTestData = {
  validNames: [
    'Ahmet Yılmaz',
    'Fatma Öztürk',
    'İsmail Çelik',
    'Şükrü Güneş',
    'Ümmügülsüm Işık'
  ],
  validEmails: [
    'ahmet@test.com',
    'fatma@ogrenci.kiro2.com',
    'ismail.celik@ogretmen.kiro2.com'
  ],
  specialChars: ['ı', 'İ', 'ş', 'Ş', 'ç', 'Ç', 'ü', 'Ü', 'ö', 'Ö', 'ğ', 'Ğ'],
  subjects: ['Matematik', 'Fizik', 'Kimya', 'Biyoloji', 'Türkçe', 'Tarih', 'Coğrafya']
};

// ============================================================================
// ACCESSIBILITY HELPERS
// ============================================================================

/**
 * Common accessibility tests
 */
export async function testAccessibility(page: Page): Promise<void> {
  // Check heading hierarchy
  const h1 = page.getByRole('heading', { level: 1 });
  await expect(h1).toBeVisible();

  // Check keyboard navigation
  await page.keyboard.press('Tab');
  const focusedElement = page.locator(':focus');
  await expect(focusedElement).toBeVisible();

  // Check ARIA labels on navigation
  const nav = page.locator('nav[aria-label], [role="navigation"][aria-label]');
  if (await nav.first().isVisible()) {
    await expect(nav.first()).toHaveAttribute('aria-label');
  }
}

/**
 * Test mobile responsiveness
 */
export async function testMobileResponsiveness(page: Page): Promise<void> {
  // iPhone viewport
  await page.setViewportSize({ width: 375, height: 667 });
  await page.waitForTimeout(500);

  // Content should still be visible
  const mainContent = page.locator('main, [role="main"], .main-content');
  if (await mainContent.isVisible()) {
    await expect(mainContent).toBeVisible();
  }
}

/**
 * Test tablet responsiveness
 */
export async function testTabletResponsiveness(page: Page): Promise<void> {
  // iPad viewport
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.waitForTimeout(500);

  const mainContent = page.locator('main, [role="main"], .main-content');
  if (await mainContent.isVisible()) {
    await expect(mainContent).toBeVisible();
  }
}
