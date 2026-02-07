# Assets Directory

This directory contains static assets for the KIRO2 frontend application.

## Structure

```
assets/
├── images/          # Images and graphics
│   ├── logos/       # Brand logos and icons
│   ├── backgrounds/ # Background images
│   └── illustrations/ # Illustrations and graphics
├── icons/           # SVG icons and icon sets
│   ├── exam/        # Exam-related icons
│   ├── learning/    # Learning-related icons
│   └── ui/          # UI icons
└── fonts/           # Custom fonts (if needed)
    └── dyslexia/    # Dyslexia-friendly fonts
```

## Usage

### Importing Images

```typescript
import logo from '@/assets/images/logos/kiro2-logo.png';

function Header() {
  return <img src={logo} alt="KIRO2 Logo" />;
}
```

### Importing Icons

```typescript
import { ReactComponent as ExamIcon } from '@/assets/icons/exam/test.svg';

function ExamButton() {
  return (
    <button>
      <ExamIcon />
      Sınava Başla
    </button>
  );
}
```

### Importing Fonts

```typescript
// In your CSS/SCSS
@font-face {
  font-family: 'OpenDyslexic';
  src: url('@/assets/fonts/dyslexia/OpenDyslexic-Regular.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
}
```

## Guidelines

### Images

- **Format**: Use WebP for photos, PNG for transparency, SVG for logos
- **Size**: Optimize images before adding (use tinypng.com or imageoptim)
- **Naming**: Use kebab-case (e.g., `kiro2-logo.png`)
- **Responsive**: Provide multiple sizes for responsive images

### Icons

- **Format**: Prefer SVG for scalability
- **Size**: Keep SVG file size small (< 10KB)
- **Naming**: Use kebab-case and descriptive names
- **Accessibility**: Include title and description in SVG

### Fonts

- **Format**: Use WOFF2 for modern browsers, WOFF for fallback
- **Licensing**: Ensure fonts are properly licensed
- **Performance**: Limit custom fonts to 2-3 maximum
- **Dyslexia Support**: Include OpenDyslexic or similar fonts

## Optimization

### Image Optimization Tools

- [TinyPNG](https://tinypng.com/) - PNG/JPG compression
- [Squoosh](https://squoosh.app/) - Advanced image optimization
- [SVGOMG](https://jakearchibald.github.io/svgomg/) - SVG optimization

### Lazy Loading

```typescript
import { lazy, Suspense } from 'react';

const HeavyImage = lazy(() => import('./HeavyImage'));

function MyComponent() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyImage />
    </Suspense>
  );
}
```

### Responsive Images

```typescript
function ResponsiveImage() {
  return (
    <picture>
      <source srcSet="image-small.webp" media="(max-width: 640px)" />
      <source srcSet="image-medium.webp" media="(max-width: 1024px)" />
      <img src="image-large.webp" alt="Description" />
    </picture>
  );
}
```

## Accessibility

### Alt Text

```typescript
// Good
<img src={exam} alt="TYT Matematik sınav sayfası" />

// Bad
<img src={exam} alt="image" />
<img src={exam} /> // Missing alt
```

### Decorative Images

```typescript
// For decorative images, use empty alt
<img src={decoration} alt="" role="presentation" />
```

### Icons with Meaning

```typescript
// Add aria-label for icons that convey information
<button aria-label="Sınavı başlat">
  <StartIcon aria-hidden="true" />
</button>
```

## Performance Tips

1. **Use CDN**: Consider using a CDN for static assets in production
2. **Compression**: Enable gzip/brotli compression on server
3. **Caching**: Set proper cache headers for assets
4. **Code Splitting**: Split large assets into chunks
5. **Preloading**: Preload critical assets

```html
<!-- In index.html -->
<link rel="preload" href="/assets/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
```

## Brand Assets

### Logo Usage

- **Main Logo**: `images/logos/kiro2-logo.svg`
- **Icon Only**: `images/logos/kiro2-icon.svg`
- **White Version**: `images/logos/kiro2-logo-white.svg`

### Color Palette

Primary colors are defined in `src/theme.ts`:

- Primary: #1976d2
- Secondary: #dc004e
- Success: #4caf50
- Error: #f44336

### Typography

- **Heading Font**: Roboto
- **Body Font**: Open Sans
- **Dyslexia Font**: OpenDyslexic (optional)

## Turkish Educational Assets

### ÖSYM Format Icons

Place ÖSYM-related icons in `icons/exam/`:

- `tyt-icon.svg` - TYT exam icon
- `ayt-icon.svg` - AYT exam icon
- `ydt-icon.svg` - YDT exam icon

### Subject Icons

Place subject-specific icons in `icons/learning/`:

- `matematik-icon.svg` - Mathematics
- `fizik-icon.svg` - Physics
- `kimya-icon.svg` - Chemistry
- `biyoloji-icon.svg` - Biology
- etc.

## License

All custom assets created for KIRO2 are proprietary. Third-party assets must be properly licensed and attributed.

## Contributing

When adding new assets:

1. Optimize before adding
2. Use consistent naming
3. Update this README if adding new categories
4. Ensure proper licensing
5. Test on multiple devices

## Questions?

For questions about assets, contact the KIRO2 design team.
