# Visual Regression Testing - Quick Start 🚀

## One-Time Setup

```bash
cd frontend
npm install
```

## Create Baseline (First Time)

```bash
# Terminal 1: Start dev server
npm run dev

# Terminal 2: Create baseline
npm run test:visual:reference
```

## Run Tests

```bash
npm run test:visual
```

This will:
1. Capture 18 screenshots (6 pages × 3 viewports)
2. Compare against baseline
3. Open HTML report if differences found

## Approve Changes

If visual changes are **intentional**:

```bash
npm run test:visual:approve
git add frontend/backstop_data/bitmaps_reference/
git commit -m "chore: Update visual baseline"
```

## Test Coverage

| Page | URL | Viewports |
|------|-----|-----------|
| Login | `/login` | Desktop, Tablet, Mobile |
| Dashboard | `/dashboard` | Desktop, Tablet, Mobile |
| Exam Start | `/sinav` | Desktop, Tablet, Mobile |
| Learning Path | `/learning-path` | Desktop, Tablet, Mobile |
| Question Bank | `/soru-bankasi` | Desktop, Tablet, Mobile |
| Student Profile | `/profil` | Desktop, Tablet, Mobile |

**Total: 18 screenshots**

## Commands Cheat Sheet

| Command | Description |
|---------|-------------|
| `npm run test:visual` | Run visual regression tests |
| `npm run test:visual:reference` | Create new baseline |
| `npm run test:visual:approve` | Approve current changes |
| `node scripts/verify-visual-testing-setup.cjs` | Verify setup |

## Configuration

Edit `backstop.config.cjs` to:
- Add/remove pages
- Change viewports
- Adjust delays
- Modify thresholds

## Troubleshooting

### Test timeout?
Increase delay in `backstop.config.cjs`:
```javascript
delay: 3000,  // was 1000
```

### Too many false positives?
Increase threshold in `backstop.config.cjs`:
```javascript
misMatchThreshold: 0.5,  // was 0.1
```

### Baseline not found?
Run:
```bash
npm run test:visual:reference
```

## Best Practices

✅ **DO:**
- Run tests before committing UI changes
- Review diff report carefully
- Approve only intentional changes
- Commit baseline images to Git

❌ **DON'T:**
- Approve changes without reviewing
- Ignore test failures
- Delete baseline images
- Skip tests in CI

## Documentation

- **Full Guide:** `VISUAL_TESTING.md`
- **Implementation Details:** `VISUAL_TESTING_SETUP.md`
- **Summary:** `VISUAL_TESTING_SUMMARY.md`

---

**Cost:** $0 (self-hosted)
**Execution Time:** ~30-60 seconds
**Setup Time:** ~5 minutes
**Status:** ✅ Ready to Use
