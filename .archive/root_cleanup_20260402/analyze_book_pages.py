#!/usr/bin/env python3
"""
Kitap başı ve sonu analizi - Cevap anahtarı nerede?
"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import os
import re
from pathlib import Path
from collections import defaultdict
import easyocr

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v4")

print("=" * 70)
print("KİTAP BAŞI/SONU ANALİZİ - CEVAP ANAHTARI NEREDE?")
print("=" * 70)

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır\n")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Farklı kitapları seç
books = sorted(os.listdir(CROPS_DIR))

# Farklı yayınlardan seç
selected_books = []
keywords = ['ACİL', 'Apotemi', '345', 'Esen', 'Palme', 'Karekök', 'Limit', 'Okyanus', 'Bilgi']
for keyword in keywords:
    for book in books:
        if keyword.lower() in book.lower() and book not in selected_books:
            selected_books.append(book)
            break
    if len(selected_books) >= 5:
        break

# Yeterli kitap yoksa ekle
while len(selected_books) < 5 and len(books) > len(selected_books):
    for book in books:
        if book not in selected_books:
            selected_books.append(book)
            break

print(f"📚 Seçilen {len(selected_books)} kitap:")
for b in selected_books:
    print(f"   - {b[:50]}")

def extract_page_num(filename):
    """Dosya adından sayfa numarasını çıkar"""
    match = re.search(r'sayfa_(\d+)', filename)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def preprocess_image(img):
    """OCR için görüntüyü hazırla"""
    w, h = img.size
    # Upscale
    if h < 80:
        scale = 80 / h
        img = img.resize((int(w * scale), 80), Image.Resampling.LANCZOS)
    # Grayscale + kontrast
    if img.mode != 'L':
        img = img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img

def looks_like_answer_key(text):
    """Bu metin cevap anahtarına benziyor mu?"""
    text_upper = text.upper()
    
    # Cevap pattern'leri
    patterns = [
        r'\d+\s*[.\-:)]\s*[A-E]',  # 1.A, 1-A, 1:A, 1)A
        r'[A-E]\s*[A-E]\s*[A-E]',   # AAA, ABC vb ardışık harfler
        r'CEVAP',
        r'ANSWER',
        r'YANITLAR',
    ]
    
    for pattern in patterns:
        if re.search(pattern, text_upper):
            return True
    
    # Sadece A-E harflerinin yoğunluğu
    letters = re.findall(r'[A-E]', text_upper)
    if len(letters) >= 5 and len(letters) / max(1, len(text)) > 0.3:
        return True
    
    return False

def analyze_book(book_name):
    """Bir kitabın ilk ve son 25 sayfasını analiz et"""
    book_path = CROPS_DIR / book_name
    
    try:
        all_files = sorted([f for f in os.listdir(book_path) if f.endswith('.png')], 
                          key=extract_page_num)
    except:
        return None
    
    if len(all_files) < 10:
        return None
    
    # İlk 25 ve son 25
    first_25 = all_files[:25]
    last_25 = all_files[-25:] if len(all_files) > 25 else []
    
    results = {
        'book': book_name,
        'total_crops': len(all_files),
        'first_25': [],
        'last_25': []
    }
    
    # İlk 25 sayfayı analiz et
    for f in first_25:
        try:
            img = Image.open(book_path / f)
            img_proc = preprocess_image(img)
            ocr_result = reader.readtext(np.array(img_proc), detail=0)
            text = ' '.join(ocr_result)
            
            is_answer = looks_like_answer_key(text)
            page_num = extract_page_num(f)
            
            results['first_25'].append({
                'file': f,
                'page': page_num,
                'text': text[:100],
                'is_answer_key': is_answer
            })
        except:
            pass
    
    # Son 25 sayfayı analiz et
    for f in last_25:
        try:
            img = Image.open(book_path / f)
            img_proc = preprocess_image(img)
            ocr_result = reader.readtext(np.array(img_proc), detail=0)
            text = ' '.join(ocr_result)
            
            is_answer = looks_like_answer_key(text)
            page_num = extract_page_num(f)
            
            results['last_25'].append({
                'file': f,
                'page': page_num,
                'text': text[:100],
                'is_answer_key': is_answer
            })
        except:
            pass
    
    return results

# Her kitabı analiz et
all_results = []

for i, book in enumerate(selected_books):
    print(f"\n{'='*70}")
    print(f"📖 [{i+1}/5] {book[:55]}")
    print('='*70)
    
    result = analyze_book(book)
    if not result:
        print("   ❌ Analiz edilemedi")
        continue
    
    all_results.append(result)
    
    print(f"   Toplam crop: {result['total_crops']}")
    
    # İlk 25
    first_answers = [r for r in result['first_25'] if r['is_answer_key']]
    print(f"\n   📄 İLK 25 SAYFA ({len(result['first_25'])} crop):")
    print(f"      Cevap benzeri: {len(first_answers)}")
    
    for r in result['first_25'][:8]:
        marker = "✅" if r['is_answer_key'] else "  "
        text_preview = r['text'][:50].replace('\n', ' ')
        print(f"      {marker} Sayfa {r['page']:03d}: '{text_preview}...'")
    
    # Son 25
    last_answers = [r for r in result['last_25'] if r['is_answer_key']]
    print(f"\n   📄 SON 25 SAYFA ({len(result['last_25'])} crop):")
    print(f"      Cevap benzeri: {len(last_answers)}")
    
    for r in result['last_25'][-8:]:
        marker = "✅" if r['is_answer_key'] else "  "
        text_preview = r['text'][:50].replace('\n', ' ')
        print(f"      {marker} Sayfa {r['page']:03d}: '{text_preview}...'")

# Özet
print("\n" + "=" * 70)
print("ÖZET ANALİZ")
print("=" * 70)

total_first = sum(len([r for r in res['first_25'] if r['is_answer_key']]) for res in all_results)
total_last = sum(len([r for r in res['last_25'] if r['is_answer_key']]) for res in all_results)

print(f"\n📊 CEVAP ANAHTARI KONUMU:")
print(f"   İlk 25 sayfada bulunan: {total_first}")
print(f"   Son 25 sayfada bulunan: {total_last}")

if total_last > total_first:
    print(f"\n   💡 SONUÇ: Cevap anahtarları KİTAP SONUNDA!")
elif total_first > total_last:
    print(f"\n   💡 SONUÇ: Cevap anahtarları KİTAP BAŞINDA!")
else:
    print(f"\n   ⚠️ SONUÇ: Belirsiz veya dağınık")

# Tüm OCR çıktılarını kaydet
import json
output_file = OUTPUT_DIR / "book_analysis.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f"\n   Detaylar: {output_file}")
