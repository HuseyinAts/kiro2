"""
YENİ STRATEJİ: Sayfa Bazlı Cevap Anahtarı Çıkarma
=================================================
Cevap kutusu yerine, cevaplar tespit edilen sayfanın TAMAMINI OCR'la
"""

import os
import json
from pathlib import Path
from PIL import Image
import numpy as np
import easyocr
import re
from collections import defaultdict

DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
IMAGES_DIR = Path(r"C:\Users\husey\d-dataset\output\images")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v3")
OUT_FILE = Path(r"C:\Users\husey\kiro2\page_ocr_test.txt")

results = []
results.append("=" * 70)
results.append("  SAYFA BAZLI CEVAP ANAHTARI TESTİ")
results.append("=" * 70)

# EasyOCR
results.append("\nEasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True)
results.append("Hazır!\n")

# Cevap içeren sayfaları bul
pages_with_cevap = []

book_dirs = [d for d in os.listdir(str(DETECTIONS_DIR)) if os.path.isdir(DETECTIONS_DIR / d)][:30]

for book_name in book_dirs:
    book_det_path = DETECTIONS_DIR / book_name
    json_files = [f for f in os.listdir(str(book_det_path)) if f.endswith('.json')]

    for json_file in sorted(json_files):
        try:
            with open(book_det_path / json_file, 'r', encoding='utf-8') as f:
                detections = json.load(f)

            cevap_count = sum(1 for d in detections if d.get('class_name') == 'cevaplar')

            if cevap_count > 0:
                pages_with_cevap.append({
                    'book': book_name,
                    'page': json_file.replace('.json', ''),
                    'cevap_count': cevap_count
                })
        except:
            pass

results.append(f"Cevap içeren sayfa: {len(pages_with_cevap)}")

# İlk 10 sayfanın TAMAMINI OCR'la
results.append("\n" + "-" * 70)
results.append("TÜM SAYFA OCR TESTİ")
results.append("-" * 70)

total_answers_found = 0

for i, page_info in enumerate(pages_with_cevap[:10]):
    book_name = page_info['book']
    page_name = page_info['page']

    results.append(f"\n[{i+1}] {book_name[:45]}")
    results.append(f"    Sayfa: {page_name}")

    # Görüntüyü bul
    book_img_dir = IMAGES_DIR / book_name
    if not book_img_dir.exists():
        results.append(f"    ❌ Görüntü dizini yok")
        continue

    # Sayfa numarasını çıkar
    page_num = page_name.replace('sayfa_', '')
    img_files = [f for f in os.listdir(str(book_img_dir)) if page_num in f and f.endswith(('.png', '.jpg', '.jpeg'))]

    if not img_files:
        results.append(f"    ❌ Görüntü dosyası yok")
        continue

    img_path = book_img_dir / img_files[0]

    try:
        img = Image.open(str(img_path))
        results.append(f"    Sayfa boyutu: {img.size[0]}x{img.size[1]}")

        # Sayfanın alt yarısını OCR'la (cevap anahtarı genelde altta)
        w, h = img.size
        # Alt %60'ı al
        crop = img.crop((0, int(h * 0.4), w, h))
        crop_array = np.array(crop)

        # OCR
        ocr_result = reader.readtext(crop_array, detail=0)
        raw_text = ' '.join(ocr_result)

        results.append(f"    OCR uzunluğu: {len(raw_text)} karakter")
        results.append(f"    İlk 200 karakter: '{raw_text[:200]}'")

        # Cevap pattern'leri ara
        text_upper = raw_text.upper()

        # Pattern 1: 1.A, 1-A, 1)A formatı
        p1 = re.findall(r'(\d{1,3})\s*[.\-:\s)]\s*([A-E])\b', text_upper)

        # Pattern 2: Tablo formatı (1 A 2 B)
        p2 = re.findall(r'\b(\d{1,2})\s+([A-E])\b', text_upper)

        # Pattern 3: CEVAP ANAHTARI yazısı var mı?
        has_cevap_text = 'CEVAP' in text_upper or 'YANITLAR' in text_upper

        if p1:
            results.append(f"    ✅ Pattern1 eşleşmeleri: {len(p1)} cevap")
            results.append(f"       Örnek: {p1[:20]}")
            total_answers_found += len(p1)
        elif p2:
            results.append(f"    ✅ Pattern2 eşleşmeleri: {len(p2)} cevap")
            results.append(f"       Örnek: {p2[:20]}")
            total_answers_found += len(p2)
        else:
            results.append(f"    ❌ Cevap pattern'i bulunamadı")
            if has_cevap_text:
                results.append(f"    💡 'CEVAP' kelimesi var ama format tanınmadı")
                # Ham metni göster
                results.append(f"    Ham metin örneği: '{text_upper[100:400]}'")

    except Exception as e:
        results.append(f"    HATA: {e}")

results.append(f"\n{'=' * 70}")
results.append(f"ÖZET: {total_answers_found} cevap bulundu")
results.append(f"{'=' * 70}")

# Dosyaya yaz
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
with open(str(OUT_FILE), 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print(f'Done - {total_answers_found} answers found')
