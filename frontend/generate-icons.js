/**
 * PWA Icon Generator
 * SVG'den farklı boyutlarda PNG iconlar oluşturur
 */

const fs = require('fs');
const path = require('path');

// Gerekli boyutlar
const sizes = [
  16, 32, 48, 72, 96, 120, 128, 144, 152, 180, 192, 256, 384, 512
];

// Basit SVG to Canvas converter (Node.js için)
function createIconPlaceholder(size) {
  // Basit bir SVG string oluştur
  const svg = `
    <svg width="${size}" height="${size}" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1976d2;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#42a5f5;stop-opacity:1" />
        </linearGradient>
      </defs>
      
      <circle cx="256" cy="256" r="240" fill="url(#grad1)" stroke="#1565c0" stroke-width="8"/>
      
      <g transform="translate(256,256)">
        <rect x="-80" y="-60" width="160" height="120" rx="8" fill="white" opacity="0.9"/>
        <rect x="-70" y="-50" width="140" height="100" rx="4" fill="#f5f5f5"/>
        <rect x="-60" y="-40" width="120" height="80" rx="4" fill="white"/>
        
        <rect x="-50" y="-25" width="80" height="4" rx="2" fill="#1976d2" opacity="0.7"/>
        <rect x="-50" y="-15" width="100" height="4" rx="2" fill="#1976d2" opacity="0.5"/>
        <rect x="-50" y="-5" width="90" height="4" rx="2" fill="#1976d2" opacity="0.5"/>
        <rect x="-50" y="5" width="70" height="4" rx="2" fill="#1976d2" opacity="0.5"/>
        <rect x="-50" y="15" width="85" height="4" rx="2" fill="#1976d2" opacity="0.5"/>
        
        <circle cx="40" cy="-35" r="12" fill="#ff9800"/>
        <text x="40" y="-30" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="white">AI</text>
      </g>
      
      <g transform="translate(400,112)">
        <rect x="0" y="0" width="60" height="40" fill="#e30a17"/>
        <circle cx="20" cy="20" r="8" fill="white"/>
        <circle cx="22" cy="20" r="6" fill="#e30a17"/>
        <polygon points="35,12 40,20 35,28 45,24 45,16" fill="white"/>
      </g>
    </svg>
  `;
  
  return svg;
}

// Icon dosyalarını oluştur
function generateIcons() {
  const imagesDir = path.join(__dirname, 'public', 'images');
  
  // Images dizinini oluştur
  if (!fs.existsSync(imagesDir)) {
    fs.mkdirSync(imagesDir, { recursive: true });
  }
  
  sizes.forEach(size => {
    const svg = createIconPlaceholder(size);
    const filename = `icon-${size}x${size}.png`;
    const filepath = path.join(imagesDir, filename);
    
    // SVG dosyası olarak kaydet (gerçek projede SVG to PNG converter kullanılmalı)
    const svgFilename = `icon-${size}x${size}.svg`;
    const svgFilepath = path.join(imagesDir, svgFilename);
    
    fs.writeFileSync(svgFilepath, svg);
    
    console.log(`Generated: ${svgFilename}`);
  });
  
  // Özel dosyalar
  const specialFiles = [
    'favicon.ico',
    'apple-touch-icon.png',
    'masked-icon.svg',
    'shortcut-exam.png',
    'shortcut-plan.png',
    'shortcut-chat.png',
    'screenshot-wide.png',
    'screenshot-narrow.png'
  ];
  
  specialFiles.forEach(filename => {
    const filepath = path.join(imagesDir, filename);
    
    if (filename.endsWith('.svg')) {
      const svg = createIconPlaceholder(512);
      fs.writeFileSync(filepath, svg);
    } else if (filename.endsWith('.png') || filename.endsWith('.ico')) {
      // Placeholder olarak SVG kaydet
      const svg = createIconPlaceholder(512);
      const svgPath = filepath.replace(/\.(png|ico)$/, '.svg');
      fs.writeFileSync(svgPath, svg);
    }
    
    console.log(`Generated placeholder: ${filename}`);
  });
  
  console.log('\n✅ Icon generation completed!');
  console.log('📝 Note: SVG placeholders created. For production, convert to PNG using a proper tool.');
}

// Script çalıştır
if (require.main === module) {
  generateIcons();
}

module.exports = { generateIcons };