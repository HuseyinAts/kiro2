# E2E Test Verification Checklist

## Pre-Test Setup

### Environment
- [ ] Node.js 18+ installed
- [ ] Dependencies installed: `npm install`
- [ ] Playwright browsers installed: `npx playwright install --with-deps`
- [ ] PostgreSQL running on port 5434
- [ ] Backend API running on port 8001 (if needed)

### Test Data
- [ ] Test user exists: `test@kiro2.com` / `Test123!`
- [ ] Test exam session available
- [ ] Sample questions in database

## Running Tests

### Option 1: With Auto-Start Server
```bash
cd C:\Users\husey\kiro2\frontend
npm run test:e2e
```

**Expected**: Server starts automatically, tests run

**If fails**:
- Check if port 3002 is already in use
- Check if vite is installed
- Try manual start (Option 2)

### Option 2: Manual Server Start
```bash
# Terminal 1: Start server
cd C:\Users\husey\kiro2\frontend
npm run dev

# Wait for: "Local: http://localhost:3002"

# Terminal 2: Run tests
npm run test:e2e:noserver
```

**Expected**: Tests run against existing server

### Option 3: Interactive UI Mode
```bash
npm run test:e2e:ui
```

**Expected**: Playwright UI opens, run tests interactively

## Test Files to Verify

### 1. auth-flow.spec.ts
- [ ] Login page displays
- [ ] Validation errors show
- [ ] Invalid credentials rejected
- [ ] Successful login redirects to dashboard
- [ ] Session persists on reload
- [ ] Logout works
- [ ] Password visibility toggle

**Expected Pass Rate**: 90%+ (7-8/8 tests)

### 2. exam-flow.spec.ts
- [ ] Exam selection page displays
- [ ] Configuration options show
- [ ] Exam starts successfully
- [ ] Question navigation works
- [ ] Answer selection works
- [ ] Flag question works
- [ ] Navigation panel displays
- [ ] Timer shows
- [ ] Completion dialog shows
- [ ] Keyboard shortcuts work
- [ ] Results display

**Expected Pass Rate**: 85%+ (13-15/17 tests)

### 3. learning-path-video-loading.spec.ts
- [ ] Videos load within timeout
- [ ] Loading indicator shows
- [ ] Video cards display
- [ ] Cache indicator works
- [ ] Timeout errors handled
- [ ] Server errors handled
- [ ] Network errors handled
- [ ] Retry logic works
- [ ] Manual retry works
- [ ] Cancel loading works
- [ ] Fallback videos show
- [ ] Video player opens
- [ ] Offline detection works
- [ ] Performance within budget
- [ ] ARIA labels present
- [ ] Keyboard navigation works
- [ ] Mobile responsive

**Expected Pass Rate**: 80%+ (42-48/60 tests)

### 4. dashboard-flow.spec.ts
- [ ] Dashboard loads after login
- [ ] Welcome message shows
- [ ] Progress statistics display
- [ ] Recent activity shows
- [ ] Navigation to exam works
- [ ] Navigation to learning path works
- [ ] Notifications work
- [ ] Profile settings open
- [ ] Sidebar navigation works

**Expected Pass Rate**: 90%+ (8-9/10 tests)

## Common Issues & Solutions

### Issue: "Error: Timed out waiting for server"
**Solution**:
1. Start server manually: `npm run dev`
2. Run tests with: `npm run test:e2e:noserver`

### Issue: "Selector not found"
**Cause**: Component text changed or element not rendered
**Solution**:
1. Check if server is running
2. Check if test user exists
3. Inspect element in browser
4. Update selector in test

### Issue: "Test timeout"
**Cause**: API too slow or network issues
**Solution**:
1. Increase timeout in test
2. Check backend is responding
3. Check network connection

### Issue: "Navigation timeout"
**Cause**: Redirect not working or auth failed
**Solution**:
1. Check auth token is valid
2. Check protected route guards
3. Check API responses

### Issue: "Element not clickable"
**Cause**: Element behind overlay or not visible
**Solution**:
1. Add wait: `await element.waitFor({ state: 'visible' })`
2. Scroll into view: `await element.scrollIntoViewIfNeeded()`
3. Check for overlays

## Debug Mode

### Visual Debugging
```bash
# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test
npx playwright test exam-flow.spec.ts --headed

# Pause at failure
npx playwright test --headed --debug
```

### Screenshots & Videos
- Screenshots saved to: `test-results/screenshots/`
- Videos saved to: `test-results/videos/`
- Traces saved to: `test-results/traces/`

### View Trace
```bash
# After test failure
playwright show-trace test-results/trace.zip
```

## CI/CD Verification

### GitHub Actions
- [ ] Workflow file exists: `.github/workflows/e2e-tests.yml`
- [ ] Playwright installation step included
- [ ] Test run step included
- [ ] Artifact upload configured
- [ ] Tests run on PR
- [ ] Tests run on main branch

### Local CI Simulation
```bash
# Simulate CI environment
CI=true npm run test:e2e
```

## Performance Benchmarks

### Load Times
- [ ] Login: < 2s
- [ ] Dashboard: < 3s
- [ ] Exam start: < 5s
- [ ] Video load: < 5s

### Test Execution
- [ ] Single test: < 30s
- [ ] Test file: < 2min
- [ ] Full suite: < 10min

## Accessibility Checks

### ARIA Labels
- [ ] Buttons have aria-label or accessible name
- [ ] Inputs have associated labels
- [ ] Loading states announced
- [ ] Error messages accessible

### Keyboard Navigation
- [ ] Tab through form works
- [ ] Arrow keys navigate questions
- [ ] Enter submits forms
- [ ] Escape closes dialogs

## Browser Compatibility

### Desktop
- [ ] Chromium (Chrome/Edge)
- [ ] Firefox
- [ ] WebKit (Safari)

### Mobile
- [ ] Mobile Chrome (Pixel 5)
- [ ] Mobile Safari (iPhone 12)

## Final Verification

### Overall Pass Rate
- [ ] Target: 85%+ overall
- [ ] auth-flow: 90%+
- [ ] exam-flow: 85%+
- [ ] learning-path: 80%+
- [ ] dashboard-flow: 90%+

### Test Quality
- [ ] No fake assertions (assert True)
- [ ] No reward hacking
- [ ] Proper error handling
- [ ] Clear test descriptions
- [ ] Good selector strategies

### Documentation
- [ ] README.md updated
- [ ] E2E_TEST_FIXES documented
- [ ] E2E_TEST_QUICK_REFERENCE available
- [ ] Component test IDs documented

## Sign-Off

### Developer
- [ ] All tests passing locally
- [ ] No skipped tests without reason
- [ ] Documentation reviewed
- [ ] Code committed

### Reviewer
- [ ] Tests reviewed
- [ ] Pass rate acceptable
- [ ] Documentation complete
- [ ] Ready for merge

### QA
- [ ] Tests run in CI
- [ ] Cross-browser tested
- [ ] Performance acceptable
- [ ] Accessibility verified

---

## Quick Commands Reference

```bash
# Full test suite
npm run test:e2e

# Without server start
npm run test:e2e:noserver

# Interactive UI
npm run test:e2e:ui

# Headed mode
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# Specific file
npx playwright test exam-flow.spec.ts

# Specific test
npx playwright test -g "should login successfully"

# Update snapshots
npx playwright test --update-snapshots

# View report
npm run test:e2e:report
```

---

**Last Updated**: February 2, 2026
**Status**: Ready for verification
**Target Pass Rate**: 85-90%
