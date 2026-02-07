import os
from pathlib import Path
from PIL import Image
import numpy as np
import easyocr
import re

CROPS_DIR = Path(r'C:\Users\husey\d-dataset\output\crops\cevaplar_v2')
OUT_FILE = Path(r'C:\Users\husey\kiro2\ocr_debug_result.txt')

results = []
results.append("=" * 70)
results.append("  CEVAP ANAHTARI OCR - DETAYLI DEBUG")
results.append("=" * 70)

# EasyOCR yükle
results.append("\nEasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True)
results.append("EasyOCR hazır!\n")

# Test et
book_dirs = [d for d in os.listdir(str(CROPS_DIR)) if os.path.isdir(CROPS_DIR / d)][:8]

total_crops = 0
total_text_found = 0
total_answers = 0

for book in book_dirs:
    book_path = CROPS_DIR / book
    pngs = [f for f in os.listdir(str(book_path)) if f.endswith('.png')][:3]
    
    if not pngs:
        continue
    
    results.append(f"\n{'─' * 60}")
    results.append(f"📚 {book[:50]}")
    results.append(f"{'─' * 60}")
    
    for png in pngs:
        img_path = book_path / png
        total_crops += 1
        
        try:
            img = Image.open(str(img_path))
            img_array = np.array(img)
            w, h = img.size
            
            # OCR
            ocr_result = reader.readtext(img_array, detail=0)
            raw_text = ' '.join(ocr_result)
            
            results.append(f"\n  📄 {png}")
            results.append(f"     Boyut: {w}x{h} px")
            results.append(f"     OCR: '{raw_text}'")
            
            if raw_text.strip():
                total_text_found += 1
            
            # Regex test
            text_upper = raw_text.upper()
            
            # Pattern 1: 1.A, 1-A, 1:A formatı
            p1 = re.findall(r'(\d{1,3})\s*[.\-:\s)]\s*([A-E])\b', text_upper)
            
            # Pattern 2: Sadece harfler
            p2 = re.findall(r'\b([A-E])\b', text_upper)
            
            # Pattern 3: Tablo formatı (1 A 2 B)
            p3 = re.findall(r'(\d+)\s+([A-E])\b', text_upper)
            
            results.append(f"     Pattern1 (1.A): {p1}")
            results.append(f"     Pattern2 (harfler): {p2}")
            results.append(f"     Pattern3 (tablo): {p3}")
            
            if p1:
                total_answers += len(p1)
            elif p3:
                total_answers += len(p3)
            
        except Exception as e:
            results.append(f"  {png}: HATA - {e}")

results.append(f"\n{'=' * 70}")
results.append("  ÖZET")
results.append(f"{'=' * 70}")
results.append(f"\n  Test edilen crop: {total_crops}")
results.append(f"  Metin bulunan: {total_text_found}")
results.append(f"  Cevap bulunan: {total_answers}")
results.append(f"  Başarı oranı: {total_answers / max(total_crops, 1) * 100:.1f}%")

# Dosyaya yaz
with open(str(OUT_FILE), 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - check ocr_debug_result.txt')
