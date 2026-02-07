# Visual Regression Testing - KIRO2

## Overview

Visual regression testing using BackstopJS to catch unintended UI changes across desktop, tablet, and mobile viewports.

## Setup

### Installation

```bash
cd frontend
npm install
```

BackstopJS (v6.3.23) is already in devDependencies.

## Usage

### 1. Create Reference Images (Baseline)

First time setup - capture the "golden" screenshots:

```bash
# Start the dev server first
npm run dev

# In another terminal, create baseline images
npm run test:visual:reference
```

This creates reference screenshots in `backstop_data/bitmaps_reference/`.

### 2. Run Visual Tests

Compare current UI against reference images:

```bash
npm run test:visual
```

Results:
- **PASS**: UI matches reference (within 0.1% threshold)
- **FAIL**: Visual differences detected - opens HTML report automatically

### 3. Review Differences

If tests fail, BackstopJS opens an HTML report showing:
- Reference image (expected)
- Test image (actual)
- Diff image (highlighted changes)

### 4. Approve Changes

If visual changes are intentional (new feature, design update):

```bash
npm run test:visual:approve
```

This updates the reference images to match current state.

## Tested Pages

| Page | URL | Delay |
|------|-----|-------|
| Login | `/login` | 1s |
| Dashboard | `/dashboard` | 2s |
| Exam Start | `/sinav` | 1s |
| Learning Path | `/learning-path` | 1.5s |
| Question Bank | `/soru-bankasi` | 1s |
| Student Profile | `/profil` | 1s |

## Viewports

| Device | Width x Height |
|--------|----------------|
| Desktop | 1920x1080 |
| Tablet | 768x1024 |
| Mobile | 375x812 |

## Configuration

Edit `backstop.config.cjs` to:
- Add/remove test scenarios
- Change viewports
- Adjust mismatch threshold (currently 0.1%)
- Modify delays

### Example: Add New Scenario

```javascript
// In backstop.config.cjs
scenarios: [
  // ... existing scenarios
  {
    label: "Teacher Dashboard",
    url: "http://localhost:3002/teacher/dashboard",
    delay: 2000,
    misMatchThreshold: 0.1,
  },
]
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Visual Regression Tests
  run: |
    cd frontend
    npm run dev &
    sleep 10  # Wait for dev server
    npm run test:visual
```

**Note:** Commit reference images to Git for CI comparison.

## Troubleshooting

### Test Fails with Timeout

**Issue:** Dev server not ready

**Solution:**
```bash
# Increase delay in backstop.config.cjs
delay: 3000,  // was 1000
```

### Too Many False Positives

**Issue:** Mismatch threshold too strict

**Solution:**
```javascript
// In backstop.config.cjs
misMatchThreshold: 0.5,  // was 0.1
```

### Reference Images Not Found

**Issue:** Baseline not created

**Solution:**
```bash
npm run test:visual:reference
```

## Best Practices

### When to Approve Changes

✅ **DO approve:**
- Intentional design updates
- New features with UI changes
- Bug fixes that change appearance

❌ **DON'T approve:**
- Random layout shifts
- Unexpected color changes
- Unintended spacing issues

### Update References After

- CSS/styling changes
- Component redesigns
- Layout refactoring
- New responsive breakpoints

### KIRO2 Specific Considerations

#### Turkish Character Support
- Tests verify UTF-8 rendering (ğ, ü, ş, ı, ö, ç)
- Ensures Türkçe text displays correctly

#### Responsive Design
- All 3 viewports test responsive behavior
- Critical for mobile YKS students

#### Dynamic Content
- Tests use delays to wait for API responses
- Dashboard waits 2s for data loading

#### Accessibility
- Visual tests complement a11y tests
- Verify high-contrast mode rendering

## File Structure

```
frontend/
├── backstop.config.cjs             # Configuration
├── backstop_data/
│   ├── bitmaps_reference/          # Baseline images (COMMIT)
│   ├── bitmaps_test/               # Test images (IGNORE)
│   ├── html_report/                # Test reports (IGNORE)
│   └── engine_scripts/             # Custom scripts
└── VISUAL_TESTING.md               # This file
```

## Resources

- [BackstopJS Documentation](https://github.com/garris/BackstopJS)
- [Playwright Engine](https://playwright.dev/)
- KIRO2 Testing Standards: `../.claude/rules/testing.md`

## Verification Checklist

Before committing UI changes:

- [ ] Run `npm run test:visual`
- [ ] Review diff report if failed
- [ ] Approve intentional changes: `npm run test:visual:approve`
- [ ] Commit updated reference images
- [ ] Verify tests pass in CI

---

**Cost:** $0 (self-hosted, no external services)
**Execution Time:** ~30-60 seconds for 6 scenarios x 3 viewports = 18 screenshots
**Maintenance:** Update references when UI changes intentionally

*Last updated: February 2, 2026*
