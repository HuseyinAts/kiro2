#!/usr/bin/env python3
"""Hızlı crop analizi - sadece boyutlar"""

from PIL import Image
from pathlib import Path
import os

crops_dir = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")

print("CROP BOYUT ANALİZİ")
print("=" * 50)

sizes = []
samples = []

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
                sizes.append((w, h, book, f))
                if len(samples) < 10:
                    samples.append((full_path, w, h, book, f))
            except:
                pass

print(f"Toplam crop: {len(sizes)}")

if sizes:
    widths = [s[0] for s in sizes]
    heights = [s[1] for s in sizes]

    print(f"\nGENİŞLİK:")
    print(f"  Min: {min(widths)}, Max: {max(widths)}, Ort: {sum(widths)/len(widths):.0f}")

    print(f"\nYÜKSEKLİK:")
    print(f"  Min: {min(heights)}, Max: {max(heights)}, Ort: {sum(heights)/len(heights):.0f}")

    # Küçük crop'lar
    tiny_w = len([w for w in widths if w < 100])
    tiny_h = len([h for h in heights if h < 30])
    print(f"\nKÜÇÜK CROP'LAR:")
    print(f"  Genişlik < 100px: {tiny_w} ({tiny_w/len(sizes)*100:.1f}%)")
    print(f"  Yükseklik < 30px: {tiny_h} ({tiny_h/len(sizes)*100:.1f}%)")

    # En küçükler
    print(f"\nEN KÜÇÜK 5 CROP:")
    sorted_by_area = sorted(sizes, key=lambda x: x[0]*x[1])[:5]
    for w, h, book, f in sorted_by_area:
        print(f"  {w}x{h} - {book[:30]}/{f}")

    # Örnekler
    print(f"\nÖRNEK CROP'LAR:")
    for path, w, h, book, f in samples[:10]:
        print(f"  {w}x{h} - {book[:35]}/{f}")

# Örnek kaydet
sample_dir = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v2\samples")
sample_dir.mkdir(parents=True, exist_ok=True)
for i, (path, w, h, book, f) in enumerate(samples[:10]):
    img = Image.open(path)
    img.save(sample_dir / f"sample_{i:02d}.png")
print(f"\nÖrnekler: {sample_dir}")
