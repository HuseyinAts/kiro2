#!/usr/bin/env python3
"""
Cevap Anahtarı OCR - Orijinal Sayfalardan Crop v4
=================================================
Strateji:
1. Detection JSON'lardan cevaplar bbox'larını al
2. Orijinal PDF sayfalarından (PNG) crop yap - PADDING ile
3. Upscale + Preprocessing
4. OCR uygula
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# EasyOCR
import easyocr

# Paths
DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
PAGES_DIR = Path(r"C:\Users\husey\d-dataset\output\pages")  # Orijinal sayfalar
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v4")

PADDING = 20  # Crop'a eklenecek padding (piksel)
MIN_HEIGHT = 80  # Minimum crop yüksekliği

def find_page_image(book_name, page_name):
    """Sayfa görselini bul"""
    # Sayfa numarasını çıkar
    page_match = re.search(r'(\d+)', page_name)
    if not page_match:
        return None
    page_num = page_match.group(1)
    
    # Olası sayfa dosya isimleri
    possible_names = [
        f"sayfa_{page_num.zfill(4)}.png",
        f"page_{page_num.zfill(4)}.png",
        f"sayfa_{page_num}.png",
        f"page_{page_num}.png",
        f"{page_num.zfill(4)}.png",
        f"{page_num}.png"
    ]
    
    book_pages_dir = PAGES_DIR / book_name
    if not book_pages_dir.exists():
        # Benzer isim ara
        for d in PAGES_DIR.iterdir():
            if d.is_dir() and book_name[:20].lower() in d.name.lower():
                book_pages_dir = d
                break
    
    if not book_pages_dir.exists():
        return None
    
    for name in possible_names:
        path = book_pages_dir / name
        if path.exists():
            return path
    
    # Tüm PNG'leri dene
    try:
        for f in os.listdir(book_pages_dir):
            if f.endswith('.png') and page_num in f:
                return book_pages_dir / f
    except:
        pass
    
    return None

def crop_with_padding(img, x1, y1, x2, y2, padding=PADDING):
    """Padding ile crop yap"""
    w, h = img.size
    
    # Padding ekle
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    
    return img.crop((x1, y1, x2, y2))

def preprocess_for_ocr(img):
    """OCR için preprocessing"""
    w, h = img.size
    
    # Minimum yükseklik
    if h < MIN_HEIGHT:
        scale = MIN_HEIGHT / h
        new_w = int(w * scale)
        img = img.resize((new_w, MIN_HEIGHT), Image.Resampling.LANCZOS)
    
    # Grayscale
    if img.mode != 'L':
        img = img.convert('L')
    
    # Kontrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.8)
    
    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    return img

def extract_answers(text):
    """Cevapları çıkar - tüm pattern'ler"""
    answers = {}
    text = text.upper().replace('\n', ' ').strip()
    
    # Pattern'ler
    patterns = [
        r'(\d{1,3})\s*\.\s*([A-E])',      # 1.A
        r'(\d{1,3})\s*-\s*([A-E])',       # 1-A
        r'(\d{1,3})\s*\)\s*([A-E])',      # 1)A
        r'(\d{1,3})\s*:\s*([A-E])',       # 1:A
        r'(\d{1,3})\s+([A-E])\b',         # 1 A
        r'(\d{1,3})([A-E])\b',            # 1A
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for q_num, answer in matches:
            q_num = int(q_num)
            if 1 <= q_num <= 200:
                answers[q_num] = answer
    
    # Sadece harfler (ABCDE ACDBA...)
    if not answers:
        letters = re.findall(r'[A-E]', text)
        if 3 <= len(letters) <= 50:
            for i, letter in enumerate(letters, 1):
                answers[i] = letter
    
    return answers

def main():
    print("=" * 70)
    print("CEVAP ANAHTARI OCR - ORİJİNAL SAYFALARDAN v4")
    print("=" * 70)
    print(f"Tarih: {datetime.now()}")
    print(f"Detection: {DETECTIONS_DIR}")
    print(f"Sayfalar: {PAGES_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # EasyOCR
    print("\n🔄 EasyOCR yükleniyor...")
    reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
    print("✅ Model hazır")
    
    # İstatistikler
    stats = {
        "books": 0,
        "pages_found": 0,
        "pages_not_found": 0,
        "cevap_dets": 0,
        "crops_success": 0,
        "answers_found": 0
    }
    
    book_answers = defaultdict(dict)
    debug_samples = []
    
    # Detection klasörlerini tara
    try:
        books = sorted(os.listdir(DETECTIONS_DIR))
    except Exception as e:
        print(f"❌ Hata: {e}")
        return
    
    total_books = len(books)
    print(f"\n📚 Kitap sayısı: {total_books}")
    
    for book_idx, book_name in enumerate(books):
        book_det_dir = DETECTIONS_DIR / book_name
        if not book_det_dir.is_dir():
            continue
        
        stats["books"] += 1
        book_answer_count = 0
        
        # JSON detection dosyalarını oku
        try:
            json_files = [f for f in os.listdir(book_det_dir) if f.endswith('.json')]
        except:
            continue
        
        for json_file in json_files:
            try:
                with open(book_det_dir / json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
            except:
                continue
            
            # cevaplar class'ını bul
            cevap_dets = [d for d in detections if d.get('class_name') in ['cevaplar', 'cevap']]
            
            if not cevap_dets:
                continue
            
            stats["cevap_dets"] += len(cevap_dets)
            
            # Sayfa görselini bul
            page_name = json_file.replace('.json', '')
            page_path = find_page_image(book_name, page_name)
            
            if not page_path:
                stats["pages_not_found"] += 1
                continue
            
            stats["pages_found"] += 1
            
            try:
                page_img = Image.open(page_path)
            except:
                continue
            
            # Her cevap detection için
            for det in cevap_dets:
                try:
                    x1 = det.get('x1', det.get('bbox', [0])[0] if 'bbox' in det else 0)
                    y1 = det.get('y1', det.get('bbox', [0,0])[1] if 'bbox' in det else 0)
                    x2 = det.get('x2', det.get('bbox', [0,0,0])[2] if 'bbox' in det else 0)
                    y2 = det.get('y2', det.get('bbox', [0,0,0,0])[3] if 'bbox' in det else 0)
                    
                    # Crop
                    crop = crop_with_padding(page_img, x1, y1, x2, y2)
                    original_size = crop.size
                    
                    # Preprocess
                    crop_processed = preprocess_for_ocr(crop)
                    
                    # OCR
                    result = reader.readtext(np.array(crop_processed), detail=0)
                    raw_text = ' '.join(result)
                    
                    # Cevapları çıkar
                    answers = extract_answers(raw_text)
                    
                    stats["crops_success"] += 1
                    
                    # Debug
                    if len(debug_samples) < 30:
                        debug_samples.append({
                            "book": book_name[:40],
                            "page": page_name,
                            "bbox": [x1, y1, x2, y2],
                            "original_size": original_size,
                            "processed_size": crop_processed.size,
                            "raw_text": raw_text,
                            "answers": {str(k): v for k, v in answers.items()}
                        })
                    
                    if answers:
                        stats["answers_found"] += len(answers)
                        book_answer_count += len(answers)
                        
                        for q_num, answer in answers.items():
                            book_answers[book_name][q_num] = answer
                
                except Exception as e:
                    pass
            
            page_img.close()
        
        # Progress
        if (book_idx + 1) % 25 == 0 or book_idx == total_books - 1:
            print(f"  [{book_idx+1}/{total_books}] {book_name[:35]}... +{book_answer_count} cevap")
    
    # Kaydet
    debug_file = OUTPUT_DIR / "debug_samples.json"
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump(debug_samples, f, ensure_ascii=False, indent=2)
    
    answers_file = OUTPUT_DIR / "book_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        serializable = {k: {str(kk): vv for kk, vv in v.items()} for k, v in book_answers.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    # Özet
    print("\n" + "=" * 70)
    print("SONUÇ")
    print("=" * 70)
    print(f"  İşlenen kitap: {stats['books']}")
    print(f"  Cevap detection: {stats['cevap_dets']}")
    print(f"  Sayfa bulundu: {stats['pages_found']}")
    print(f"  Sayfa bulunamadı: {stats['pages_not_found']}")
    print(f"  Başarılı crop: {stats['crops_success']}")
    print(f"  Toplam cevap: {stats['answers_found']}")
    
    # Cevap oranı
    if stats['cevap_dets'] > 0:
        rate = stats['answers_found'] / stats['cevap_dets'] * 100
        print(f"  Cevap bulma oranı: {rate:.1f}%")
    
    print(f"\n  Debug: {debug_file}")
    
    # Debug örnekleri
    print("\n" + "-" * 70)
    print("DEBUG - İLK 10 ÖRNEK:")
    for s in debug_samples[:10]:
        print(f"\n📄 {s['book']}/{s['page']}")
        print(f"   Bbox: {s['bbox']}, Boyut: {s['original_size']} → {s['processed_size']}")
        print(f"   OCR: '{s['raw_text'][:80]}'" if s['raw_text'] else "   OCR: (boş)")
        print(f"   Cevap: {len(s['answers'])} bulundu - {dict(list(s['answers'].items())[:5])}")

if __name__ == "__main__":
    main()
