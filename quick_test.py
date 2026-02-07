import os
from pathlib import Path
from PIL import Image

CROPS_DIR = Path(r'C:\Users\husey\d-dataset\output\crops\cevaplar_v2')
OUT_FILE = Path(r'C:\Users\husey\kiro2\debug_result.txt')

results = []

# İlk kitapları bul
book_dirs = [d for d in os.listdir(str(CROPS_DIR)) if os.path.isdir(CROPS_DIR / d)][:5]
results.append(f'Bulunan kitap: {len(book_dirs)}')

for book in book_dirs:
    book_path = CROPS_DIR / book
    pngs = [f for f in os.listdir(str(book_path)) if f.endswith('.png')][:2]
    results.append(f'\n{book}: {len(pngs)} crop')
    
    for png in pngs:
        img_path = book_path / png
        try:
            img = Image.open(str(img_path))
            results.append(f'  {png}: {img.size[0]}x{img.size[1]} px, mode={img.mode}')
        except Exception as e:
            results.append(f'  {png}: HATA - {e}')

# Dosyaya yaz
with open(str(OUT_FILE), 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done')
