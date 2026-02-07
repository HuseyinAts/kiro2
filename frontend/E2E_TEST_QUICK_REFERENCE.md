# E2E Test Quick Reference

## Running Tests

```bash
# Start server and run tests
npm run test:e2e

# Run tests (server already running)
npm run test:e2e:noserver

# Interactive UI mode
npm run test:e2e:ui

# See browser
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# View report
npm run test:e2e:report

# Specific file
npx playwright test exam-flow.spec.ts

# Specific test
npx playwright test -g "should select answers"
```

## Selector Best Practices

### Priority Order
1. **data-testid** (most reliable)
2. **Role + Name** (semantic)
3. **Text content** (flexible)
4. **CSS/element** (last resort)

### Examples

```typescript
// ✅ GOOD - Multiple fallbacks
const button = page.locator('[data-testid="submit-button"]')
  .or(page.getByRole('button', { name: /gönder|submit/i }))
  .or(page.locator('text=Gönder'));

// ✅ GOOD - Semantic selector
const heading = page.getByRole('heading', { name: /dashboard/i });

// ⚠️ OK - Text content with regex
const message = page.locator('text=/başarılı|success/i');

// ❌ BAD - Fragile CSS selector
const element = page.locator('.MuiButton-root.css-abc123');
```

## Common Patterns

### Click with Visibility Check
```typescript
if (await button.isVisible({ timeout: 5000 })) {
  await button.click();
  await page.waitForTimeout(300); // Visual feedback
}
```

### Navigate and Wait
```typescript
await page.goto('/dashboard');
await expect(page).toHaveURL(/dashboard/i, { timeout: 10000 });
```

### Select from Dropdown
```typescript
await page.getByRole('combobox').click();
await page.getByRole('option', { name: /seçenek/i }).click();
```

### Fill Form
```typescript
await page.getByLabel(/e-posta/i).fill('test@example.com');
await page.getByLabel(/şifre/i).fill('password123');
await page.getByRole('button', { name: /giriş/i }).click();
```

### Check Text Visibility
```typescript
await expect(page.getByText(/hoş geldin/i)).toBeVisible();
```

### Wait for Multiple Elements
```typescript
await Promise.all([
  expect(page.locator('[data-testid="element-1"]')).toBeVisible(),
  expect(page.locator('[data-testid="element-2"]')).toBeVisible(),
]);
```

## Timeouts

| Action | Timeout |
|--------|---------|
| Element visible | 5000ms |
| Navigation | 10000ms |
| API response | 15000ms |
| Animation | 300ms |
| Network idle | 30000ms |

## Mock API Responses

```typescript
await page.route('**/api/endpoint', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ data: 'mock' })
  });
});
```

## Mock Browser APIs

```typescript
// Mock window.open
await page.evaluate(() => {
  window.open = () => null;
});

// Mock localStorage
await page.evaluate(() => {
  localStorage.setItem('key', 'value');
});

// Mock Date
await page.addInitScript(() => {
  Date.now = () => 1609459200000; // Fixed timestamp
});
```

## Debug Tips

### Take Screenshot
```typescript
await page.screenshot({ path: 'debug.png' });
```

### Get Page Content
```typescript
const html = await page.content();
console.log(html);
```

### Check Element Exists
```typescript
const exists = await page.locator('[data-testid="element"]').count() > 0;
```

### Wait and Inspect
```typescript
await page.pause(); // Opens inspector
```

### Console Logs
```typescript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

## Common Errors

### "Element not found"
✅ Add timeout: `.isVisible({ timeout: 5000 })`
✅ Check selector is correct
✅ Add fallback selectors

### "Test timeout"
✅ Increase timeout in test
✅ Check if server is running
✅ Use `SKIP_WEBSERVER=1` if server already up

### "Element not clickable"
✅ Wait for element: `await element.waitFor({ state: 'visible' })`
✅ Scroll into view: `await element.scrollIntoViewIfNeeded()`
✅ Check if element is behind overlay

### "Navigation timeout"
✅ Increase navigation timeout
✅ Wait for networkidle: `await page.waitForLoadState('networkidle')`
✅ Check if redirect is working

## Turkish Text Patterns

```typescript
// Login/Auth
/giriş|login/i
/çıkış|logout/i
/kayıt|register/i
/şifre|password/i
/e-posta|email/i

// Buttons
/gönder|submit/i
/iptal|cancel/i
/kaydet|save/i
/sil|delete/i

// Status
/başarılı|success/i
/hata|error/i
/uyarı|warning/i
/yükleniyor|loading/i

// Actions
/düzenle|edit/i
/görüntüle|view/i
/indir|download/i
/paylaş|share/i
```

## Test Structure

```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: Login, navigate, etc.
    await page.goto('/page');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    const button = page.getByRole('button', { name: /click/i });

    // Act
    await button.click();

    // Assert
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup if needed
  });
});
```

## Component Test IDs Needed

Add these to components for better testability:

```typescript
// Buttons
data-testid="submit-button"
data-testid="cancel-button"
data-testid="flag-button"

// Inputs
data-testid="email-input"
data-testid="password-input"

// Containers
data-testid="question-panel"
data-testid="answer-panel"
data-testid="navigation-panel"

// Status indicators
data-testid="loading-indicator"
data-testid="success-message"
data-testid="error-message"

// Lists/Cards
data-testid="video-card"
data-testid="question-card"
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run E2E Tests
  run: npm run test:e2e

- name: Upload Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Resources

- [Playwright Docs](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Selectors Guide](https://playwright.dev/docs/selectors)
- [API Reference](https://playwright.dev/docs/api/class-page)

---
*Last Updated: February 2, 2026*
