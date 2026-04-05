#!/usr/bin/env python3
"""Crop analizi - kök sebep araştırması"""

from PIL import Image
from pathlib import Path
import os
import easyocr

crops_dir = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")

print("=" * 60)
print("CEVAP ANAHTARI OCR - KÖK SEBEP ANALİZİ")
print("=" * 60)

# 1. CROP BOYUTLARI
print("\n1. CROP BOYUTLARI")
print("-" * 40)

count = 0
sizes = []
sample_crops = []

for book in os.listdir(crops_dir):
    book_path = crops_dir / book
    if not book_path.is_dir():
        continue
    for f in os.listdir(book_path):
        if f.endswith('.png'):
            try:
                full_path = book_path / f
                img = Image.open(full_path)
                w, h = img.size
                sizes.append((w, h))
                if count < 10:
                    print(f"  {book[:35]}/{f}: {w}x{h}")
                    sample_crops.append((full_path, img))
                count += 1
            except Exception as e:
                print(f"  HATA: {f} - {e}")

print(f"\n  Toplam crop: {len(sizes)}")
if sizes:
    avg_w = sum(s[0] for s in sizes) / len(sizes)
    avg_h = sum(s[1] for s in sizes) / len(sizes)
    min_w = min(s[0] for s in sizes)
    min_h = min(s[1] for s in sizes)
    max_w = max(s[0] for s in sizes)
    max_h = max(s[1] for s in sizes)
    print(f"  Ortalama: {avg_w:.0f}x{avg_h:.0f}")
    print(f"  Min: {min_w}x{min_h}")
    print(f"  Max: {max_w}x{max_h}")
    
    # Çok küçük crop'lar
    tiny = [s for s in sizes if s[0] < 50 or s[1] < 20]
    print(f"  Çok küçük (<50x20): {len(tiny)} ({len(tiny)/len(sizes)*100:.1f}%)")

# 2. EASYOCR TEST
print("\n2. EASYOCR HAM ÇIKTI TESTİ")
print("-" * 40)

reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)

for path, img in sample_crops[:5]:
    print(f"\n  📄 {path.parent.name[:30]}/{path.name}")
    print(f"     Boyut: {img.size}")
    
    import numpy as np
    img_array = np.array(img)
    
    # OCR yap
    result = reader.readtext(img_array, detail=1)
    
    print(f"     Tespit sayısı: {len(result)}")
    for detection in result:
        bbox, text, conf = detection
        print(f"     -> '{text}' (güven: {conf:.2f})")

# 3. ÖRNEK GÖRSEL KAYDET (inceleme için)
print("\n3. ÖRNEK GÖRSELLER")
print("-" * 40)

sample_dir = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v2\samples")
sample_dir.mkdir(parents=True, exist_ok=True)

for i, (path, img) in enumerate(sample_crops[:10]):
    save_path = sample_dir / f"sample_{i:02d}_{path.name}"
    img.save(save_path)
    print(f"  Kaydedildi: {save_path.name}")

print(f"\n  Örnekleri incele: {sample_dir}")

print("\n" + "=" * 60)
print("ANALİZ TAMAMLANDI")
print("=" * 60)
