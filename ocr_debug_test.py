#!/usr/bin/env python3
"""
OCR Debug Test - Crop'ların içeriğini göster
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
from pathlib import Path
import easyocr

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v4")

print("=" * 70)
print("OCR DEBUG TESTİ - CROP İÇERİKLERİ")
print("=" * 70)

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır\n")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# İlk 5 kitaptan örnekler al
sample_count = 0
max_samples = 30

for book_name in sorted(os.listdir(CROPS_DIR))[:10]:
    book_path = CROPS_DIR / book_name
    if not book_path.is_dir():
        continue
    
    try:
        pngs = sorted([f for f in os.listdir(book_path) if f.endswith('.png')])[:5]
    except:
        continue
    
    for png_file in pngs:
        if sample_count >= max_samples:
            break
        
        crop_path = book_path / png_file
        
        try:
            # Orijinal görsel
            img = Image.open(crop_path)
            w, h = img.size
            
            print(f"\n{'─'*60}")
            print(f"📄 {book_name[:40]}")
            print(f"   Dosya: {png_file}")
            print(f"   Boyut: {w}x{h}px")
            
            # RAW OCR (preprocessing yok)
            img_array = np.array(img)
            raw_result = reader.readtext(img_array, detail=1)
            
            print(f"\n   🔍 RAW OCR:")
            if raw_result:
                for bbox, text, conf in raw_result:
                    print(f"      '{text}' (güven: {conf:.2f})")
            else:
                print(f"      (boş sonuç)")
            
            # PROCESSED OCR (upscale + kontrast)
            # Upscale 3x
            scale = 3
            img_up = img.resize((w*scale, h*scale), Image.Resampling.LANCZOS)
            
            # Grayscale + kontrast
            if img_up.mode != 'L':
                img_up = img_up.convert('L')
            enhancer = ImageEnhance.Contrast(img_up)
            img_up = enhancer.enhance(2.0)
            img_up = img_up.filter(ImageFilter.SHARPEN)
            
            proc_result = reader.readtext(np.array(img_up), detail=1)
            
            print(f"\n   🔬 PROCESSED OCR (3x upscale + kontrast):")
            if proc_result:
                for bbox, text, conf in proc_result:
                    print(f"      '{text}' (güven: {conf:.2f})")
            else:
                print(f"      (boş sonuç)")
            
            # Örnek görseli kaydet
            img_up.save(OUTPUT_DIR / f"sample_{sample_count:02d}_processed.png")
            img.save(OUTPUT_DIR / f"sample_{sample_count:02d}_original.png")
            
            sample_count += 1
            
        except Exception as e:
            print(f"   ❌ Hata: {e}")
    
    if sample_count >= max_samples:
        break

print(f"\n{'='*70}")
print(f"Örnekler kaydedildi: {OUTPUT_DIR}")
print(f"{'='*70}")
