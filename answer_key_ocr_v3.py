#!/usr/bin/env python3
"""
Cevap Anahtarı OCR - Geliştirilmiş Versiyon
==========================================
Sorunlar:
1. Crop'lar çok küçük (38px yükseklik) - ÇÖZÜM: Upscale
2. Pattern eşleşmiyor - ÇÖZÜM: Daha fazla pattern
3. Düşük kontrast - ÇÖZÜM: Preprocessing
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

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v3")

def preprocess_image(img):
    """Küçük crop'ları OCR için optimize et"""
    w, h = img.size
    
    # 1. UPSCALE - Minimum 100px yükseklik
    if h < 100:
        scale = 100 / h
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 2. Grayscale
    if img.mode != 'L':
        img = img.convert('L')
    
    # 3. Kontrast artır
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # 4. Sharpen
    img = img.filter(ImageFilter.SHARPEN)
    
    return img

def extract_answers_advanced(text):
    """Gelişmiş cevap çıkarma - daha fazla pattern"""
    answers = {}
    
    # Normalize
    text = text.upper().replace('\n', ' ').replace('  ', ' ').strip()
    
    # Pattern 1: "1.A" "2.B" "3.C" (noktalı)
    p1 = re.findall(r'(\d{1,3})\s*\.\s*([A-E])\b', text)
    
    # Pattern 2: "1-A" "2-B" (tireli)
    p2 = re.findall(r'(\d{1,3})\s*-\s*([A-E])\b', text)
    
    # Pattern 3: "1)A" "2)B" (parantezli)
    p3 = re.findall(r'(\d{1,3})\s*\)\s*([A-E])\b', text)
    
    # Pattern 4: "1:A" "2:B" (iki nokta)
    p4 = re.findall(r'(\d{1,3})\s*:\s*([A-E])\b', text)
    
    # Pattern 5: "1 A" "2 B" (boşluklu)
    p5 = re.findall(r'(\d{1,3})\s+([A-E])\b', text)
    
    # Pattern 6: "1A" "2B" (bitişik)
    p6 = re.findall(r'(\d{1,3})([A-E])\b', text)
    
    # Tüm pattern'leri birleştir
    all_matches = p1 + p2 + p3 + p4 + p5 + p6
    
    for q_num, answer in all_matches:
        q_num = int(q_num)
        if 1 <= q_num <= 200:
            answers[q_num] = answer
    
    # Pattern 7: Sadece ardışık harfler (cevap şeridi)
    if not answers and len(text) > 3:
        # "ABCDE ACDBA BCDEA" gibi
        letters = re.findall(r'[A-E]', text)
        if len(letters) >= 3:
            # Ardışık harfleri say
            for i, letter in enumerate(letters[:50], 1):
                answers[i] = letter
    
    return answers

def main():
    print("=" * 70)
    print("CEVAP ANAHTARI OCR - GELİŞTİRİLMİŞ v3")
    print("=" * 70)
    print(f"Tarih: {datetime.now()}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # EasyOCR
    print("\n🔄 EasyOCR yükleniyor (GPU)...")
    reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
    print("✅ Model hazır")
    
    # İstatistikler
    stats = {
        "books": 0,
        "crops_processed": 0,
        "crops_with_answers": 0,
        "total_answers": 0,
        "failed": 0
    }
    
    book_answers = defaultdict(dict)
    debug_samples = []
    
    # Kitapları işle
    books = sorted(os.listdir(CROPS_DIR))
    total_books = len(books)
    
    for book_idx, book_name in enumerate(books):
        book_path = CROPS_DIR / book_name
        if not book_path.is_dir():
            continue
        
        try:
            png_files = sorted([f for f in os.listdir(book_path) if f.endswith('.png')])
        except:
            continue
        
        if not png_files:
            continue
        
        stats["books"] += 1
        book_answer_count = 0
        
        for png_file in png_files:
            crop_path = book_path / png_file
            
            try:
                # Resmi yükle
                img = Image.open(crop_path)
                original_size = img.size
                
                # Preprocessing
                img_processed = preprocess_image(img)
                processed_size = img_processed.size
                
                # OCR
                img_array = np.array(img_processed)
                result = reader.readtext(img_array, detail=0)
                raw_text = ' '.join(result)
                
                # Cevapları çıkar
                answers = extract_answers_advanced(raw_text)
                
                # Debug için ilk 50 örneği kaydet
                if len(debug_samples) < 50:
                    debug_samples.append({
                        "file": f"{book_name}/{png_file}",
                        "original_size": original_size,
                        "processed_size": processed_size,
                        "raw_text": raw_text,
                        "answers_found": len(answers),
                        "answers": answers
                    })
                
                if answers:
                    stats["crops_with_answers"] += 1
                    stats["total_answers"] += len(answers)
                    book_answer_count += len(answers)
                    
                    # Sayfa numarası
                    page_match = re.search(r'sayfa_(\d+)', png_file)
                    page_num = int(page_match.group(1)) if page_match else 0
                    
                    # Kitap cevaplarına ekle
                    for q_num, answer in answers.items():
                        book_answers[book_name][q_num] = answer
                
                stats["crops_processed"] += 1
                
            except Exception as e:
                stats["failed"] += 1
        
        # Progress
        if (book_idx + 1) % 25 == 0 or book_idx == total_books - 1:
            print(f"  [{book_idx+1}/{total_books}] {book_name[:35]}... +{book_answer_count} cevap")
    
    # Debug dosyası kaydet
    debug_file = OUTPUT_DIR / "debug_samples.json"
    with open(debug_file, 'w', encoding='utf-8') as f:
        # Convert answers keys to strings for JSON
        for sample in debug_samples:
            sample["answers"] = {str(k): v for k, v in sample["answers"].items()}
        json.dump(debug_samples, f, ensure_ascii=False, indent=2)
    
    # Sonuçları kaydet
    answers_file = OUTPUT_DIR / "book_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        serializable = {k: {str(kk): vv for kk, vv in v.items()} for k, v in book_answers.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    # Özet
    print("\n" + "=" * 70)
    print("SONUÇ")
    print("=" * 70)
    print(f"  İşlenen kitap: {stats['books']}")
    print(f"  İşlenen crop: {stats['crops_processed']}")
    print(f"  Cevap bulunan crop: {stats['crops_with_answers']} ({stats['crops_with_answers']/max(1,stats['crops_processed'])*100:.1f}%)")
    print(f"  Toplam cevap: {stats['total_answers']}")
    print(f"  Başarısız: {stats['failed']}")
    print(f"\n  Debug: {debug_file}")
    print(f"  Sonuçlar: {answers_file}")
    
    # Debug örnekleri göster
    print("\n" + "-" * 70)
    print("DEBUG - İLK 10 ÖRNEK:")
    print("-" * 70)
    for sample in debug_samples[:10]:
        print(f"\n📄 {sample['file']}")
        print(f"   Boyut: {sample['original_size']} → {sample['processed_size']}")
        print(f"   OCR: '{sample['raw_text'][:100]}...' " if len(sample['raw_text']) > 100 else f"   OCR: '{sample['raw_text']}'")
        print(f"   Cevap: {sample['answers_found']} bulundu - {dict(list(sample['answers'].items())[:5])}")

if __name__ == "__main__":
    main()
