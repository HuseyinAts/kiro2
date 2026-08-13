import os
import json
from pathlib import Path
from PIL import Image
import numpy as np
import easyocr
import re

DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
IMAGES_DIR = Path(r"C:\Users\husey\d-dataset\output\images")
OUT_FILE = Path(r"C:\Users\husey\kiro2\large_boxes_test.txt")

results = []
results.append("=" * 70)
results.append("  BÜYÜK CEVAP KUTULARI ANALİZİ (>20K px²)")
results.append("=" * 70)

# EasyOCR
results.append("\nEasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True)
results.append("Hazır!\n")

large_boxes = []

# Tüm detection'ları tara
book_dirs = [d for d in os.listdir(str(DETECTIONS_DIR)) if os.path.isdir(DETECTIONS_DIR / d)][:100]

for book_name in book_dirs:
    book_path = DETECTIONS_DIR / book_name
    json_files = [f for f in os.listdir(str(book_path)) if f.endswith('.json')]

    for json_file in json_files:
        try:
            with open(book_path / json_file, 'r', encoding='utf-8') as f:
                detections = json.load(f)

            for det in detections:
                if det.get('class_name') == 'cevaplar':
                    w = det['x2'] - det['x1']
                    h = det['y2'] - det['y1']
                    area = w * h

                    if area > 20000:  # Büyük kutular
                        large_boxes.append({
                            'book': book_name,
                            'page': json_file.replace('.json', ''),
                            'bbox': (int(det['x1']), int(det['y1']), int(det['x2']), int(det['y2'])),
                            'size': f"{int(w)}x{int(h)}",
                            'area': int(area),
                            'confidence': det.get('confidence', 0)
                        })
        except:
            pass

results.append(f"Bulunan büyük kutu: {len(large_boxes)}")

# En büyük 10 kutuyu test et
large_boxes.sort(key=lambda x: x['area'], reverse=True)

results.append("\n" + "-" * 70)
results.append("EN BÜYÜK 10 KUTUNUN OCR ANALİZİ")
results.append("-" * 70)

for i, box in enumerate(large_boxes[:10]):
    results.append(f"\n[{i+1}] {box['book'][:40]}")
    results.append(f"    Sayfa: {box['page']}")
    results.append(f"    Boyut: {box['size']} ({box['area']:,} px²)")
    results.append(f"    Güven: {box['confidence']:.2f}")

    # Görüntüyü bul ve crop et
    book_img_dir = IMAGES_DIR / box['book']
    if book_img_dir.exists():
        page_files = [f for f in os.listdir(str(book_img_dir)) if box['page'].replace('sayfa_', '') in f]
        if page_files:
            img_path = book_img_dir / page_files[0]
            try:
                img = Image.open(str(img_path))
                # Crop
                x1, y1, x2, y2 = box['bbox']
                # Add padding
                pad = 10
                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(img.width, x2 + pad)
                y2 = min(img.height, y2 + pad)

                crop = img.crop((x1, y1, x2, y2))
                crop_array = np.array(crop)

                # OCR
                ocr_result = reader.readtext(crop_array, detail=0)
                raw_text = ' '.join(ocr_result)

                results.append(f"    OCR: '{raw_text[:150]}{'...' if len(raw_text) > 150 else ''}'")

                # Cevap pattern'i ara
                text_upper = raw_text.upper()
                p1 = re.findall(r'(\d{1,3})\s*[.\-:\s)]\s*([A-E])\b', text_upper)
                p2 = re.findall(r'(\d+)\s+([A-E])\b', text_upper)

                if p1:
                    results.append(f"    ✅ CEVAP BULUNDU (Pattern1): {p1[:15]}")
                elif p2:
                    results.append(f"    ✅ CEVAP BULUNDU (Pattern2): {p2[:15]}")
                else:
                    results.append(f"    ❌ Cevap pattern'i bulunamadı")

            except Exception as e:
                results.append(f"    HATA: {e}")

# Dosyaya yaz
with open(str(OUT_FILE), 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Done - check large_boxes_test.txt')
