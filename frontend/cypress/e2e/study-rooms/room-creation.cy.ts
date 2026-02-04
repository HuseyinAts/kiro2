/**
 * Cypress E2E Test: Study Room Creation Journey
 * Tests the complete flow of creating and joining a study room
 */

describe('Study Room Creation Journey', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/login');
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });

  describe('Room Creation Flow', () => {
    it('navigates to study rooms page', () => {
      cy.visit('/study-rooms');
      cy.contains('Grup Çalışma Odaları').should('be.visible');
      cy.contains('Yeni Oda Oluştur').should('be.visible');
    });

    it('opens room creation dialog', () => {
      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();
      cy.contains('Yeni Çalışma Odası Oluştur').should('be.visible');
    });

    it('validates required fields', () => {
      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();

      // Try to create without name
      cy.contains('button', 'Oluştur').should('be.disabled');

      // Fill name
      cy.get('input[label="Oda Adı"]').type('TYT Matematik Grubu');
      cy.contains('button', 'Oluştur').should('not.be.disabled');
    });

    it('creates public room successfully', () => {
      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();

      // Fill form
      cy.get('input[label="Oda Adı"]').type('TYT Matematik Çalışma Grubu');
      cy.get('textarea[label="Açıklama"]').type('TYT matematik sorularını birlikte çözelim');
      cy.get('input[label="Konu"]').type('Denklemler');
      cy.get('select[label="Ders"]').select('Matematik');
      cy.get('select[label="Gizlilik"]').select('Herkese Açık');

      // Create room
      cy.contains('button', 'Oluştur').click();

      // Should navigate to room
      cy.url().should('include', '/study-rooms/');
      cy.contains('TYT Matematik Çalışma Grubu').should('be.visible');
    });

    it('creates password-protected room', () => {
      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();

      cy.get('input[label="Oda Adı"]').type('Özel Matematik Grubu');
      cy.get('select[label="Gizlilik"]').select('Şifre Korumalı');

      // Password field should appear
      cy.get('input[label="Oda Şifresi"]').should('be.visible');
      cy.get('input[label="Oda Şifresi"]').type('test123');

      cy.contains('button', 'Oluştur').click();
      cy.url().should('include', '/study-rooms/');
    });

    it('creates private room', () => {
      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();

      cy.get('input[label="Oda Adı"]').type('Özel Grup');
      cy.get('select[label="Gizlilik"]').select('Özel (Sadece Davetli)');

      cy.contains('button', 'Oluştur').click();
      cy.url().should('include', '/study-rooms/');
    });
  });

  describe('Room Discovery', () => {
    beforeEach(() => {
      // Create test rooms via API
      cy.request('POST', '/api/study-rooms', {
        name: 'Test Room 1',
        subject: 'Matematik',
        visibility: 'public'
      });
      cy.request('POST', '/api/study-rooms', {
        name: 'Test Room 2',
        subject: 'Fizik',
        visibility: 'public'
      });
    });

    it('displays room list', () => {
      cy.visit('/study-rooms');
      cy.contains('Test Room 1').should('be.visible');
      cy.contains('Test Room 2').should('be.visible');
    });

    it('filters rooms by search', () => {
      cy.visit('/study-rooms');
      cy.get('input[placeholder="Oda ara..."]').type('Test Room 1');

      cy.contains('Test Room 1').should('be.visible');
      cy.contains('Test Room 2').should('not.exist');
    });

    it('filters rooms by subject', () => {
      cy.visit('/study-rooms');
      cy.get('select[label="Ders"]').select('Matematik');

      cy.contains('Matematik').should('be.visible');
      cy.contains('Fizik').should('not.exist');
    });

    it('filters rooms by visibility', () => {
      cy.visit('/study-rooms');
      cy.get('select[label="Gizlilik"]').select('Herkese Açık');

      cy.get('.room-card').should('have.length.greaterThan', 0);
    });
  });

  describe('Joining Rooms', () => {
    it('joins public room', () => {
      cy.visit('/study-rooms');
      cy.contains('.room-card', 'Test Room 1').within(() => {
        cy.contains('button', 'Katıl').click();
      });

      cy.url().should('include', '/study-rooms/');
      cy.contains('Test Room 1').should('be.visible');
    });

    it('joins password-protected room', () => {
      // Create password room
      cy.request('POST', '/api/study-rooms', {
        name: 'Protected Room',
        visibility: 'password',
        password: 'test123'
      });

      cy.visit('/study-rooms');
      cy.contains('.room-card', 'Protected Room').within(() => {
        cy.contains('button', 'Katıl').click();
      });

      // Should prompt for password
      cy.window().then((win) => {
        cy.stub(win, 'prompt').returns('test123');
      });

      cy.url().should('include', '/study-rooms/');
    });

    it('cannot join full room', () => {
      // Create full room
      cy.request('POST', '/api/study-rooms', {
        name: 'Full Room',
        max_members: 1,
        member_count: 1
      });

      cy.visit('/study-rooms');
      cy.contains('.room-card', 'Full Room').within(() => {
        cy.contains('button', 'Dolu').should('be.disabled');
      });
    });
  });

  describe('Room Tabs', () => {
    it('shows all rooms by default', () => {
      cy.visit('/study-rooms');
      cy.contains('Tüm Odalar').should('have.class', 'active');
    });

    it('switches to my rooms tab', () => {
      cy.visit('/study-rooms');
      cy.contains('Benim Odalarım').click();

      // Should show only rooms created by user
      cy.url().should('include', 'tab=my-rooms');
    });

    it('switches to joined rooms tab', () => {
      cy.visit('/study-rooms');
      cy.contains('Katıldığım Odalar').click();

      cy.url().should('include', 'tab=joined');
    });
  });

  describe('Room Information Display', () => {
    it('displays room metadata correctly', () => {
      cy.visit('/study-rooms');
      cy.get('.room-card').first().within(() => {
        cy.get('.room-name').should('be.visible');
        cy.get('.room-subject').should('be.visible');
        cy.get('.member-count').should('be.visible');
      });
    });

    it('shows active video indicator', () => {
      // Create room with active video
      cy.request('POST', '/api/study-rooms', {
        name: 'Video Room',
        has_active_video: true
      });

      cy.visit('/study-rooms');
      cy.contains('.room-card', 'Video Room').within(() => {
        cy.get('[data-testid="VideoCallIcon"]').should('be.visible');
      });
    });

    it('shows unread message badge', () => {
      // Create room with unread messages
      cy.request('POST', '/api/study-rooms', {
        name: 'Chat Room',
        unread_messages: 5
      });

      cy.visit('/study-rooms');
      cy.contains('.room-card', 'Chat Room').within(() => {
        cy.contains('5').should('be.visible');
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', () => {
      // Mock API failure
      cy.intercept('GET', '/api/study-rooms', { statusCode: 500 });

      cy.visit('/study-rooms');
      cy.contains('Yükleniyor...').should('be.visible');
    });

    it('handles room creation errors', () => {
      cy.intercept('POST', '/api/study-rooms', { statusCode: 400 });

      cy.visit('/study-rooms');
      cy.contains('Yeni Oda Oluştur').click();
      cy.get('input[label="Oda Adı"]').type('Test Room');
      cy.contains('button', 'Oluştur').click();

      // Should show error message
      cy.contains('hata').should('be.visible');
    });

    it('handles join errors', () => {
      cy.intercept('POST', '/api/study-rooms/*/join', { statusCode: 403 });

      cy.visit('/study-rooms');
      cy.contains('button', 'Katıl').first().click();

      cy.contains('hata').should('be.visible');
    });
  });

  describe('Responsive Design', () => {
    it('works on mobile viewport', () => {
      cy.viewport('iphone-x');
      cy.visit('/study-rooms');

      cy.contains('Grup Çalışma Odaları').should('be.visible');
      cy.contains('Yeni Oda Oluştur').should('be.visible');
    });

    it('works on tablet viewport', () => {
      cy.viewport('ipad-2');
      cy.visit('/study-rooms');

      cy.get('.room-card').should('be.visible');
    });

    it('works on desktop viewport', () => {
      cy.viewport(1920, 1080);
      cy.visit('/study-rooms');

      cy.get('.room-card').should('have.length.greaterThan', 0);
    });
  });

  describe('Performance', () => {
    it('loads room list within 2 seconds', () => {
      const start = Date.now();
      cy.visit('/study-rooms');
      cy.get('.room-card').should('be.visible');

      cy.then(() => {
        const duration = Date.now() - start;
        expect(duration).to.be.lessThan(2000);
      });
    });

    it('filters rooms efficiently', () => {
      cy.visit('/study-rooms');
      cy.get('input[placeholder="Oda ara..."]').type('Test');

      // Should filter instantly
      cy.get('.room-card').should('be.visible');
    });
  });
});
