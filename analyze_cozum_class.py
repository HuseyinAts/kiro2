#!/usr/bin/env python3
"""
COZUM Class Analizi - Cevap anahtarları burada mı?
"""

from PIL import Image, ImageEnhance
import numpy as np
import os
import re
from pathlib import Path
import easyocr

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v4")

print("=" * 70)
print("COZUM CLASS ANALİZİ - CEVAP ANAHTARLARI BURADA MI?")
print("=" * 70)

# Mevcut crop klasörlerini listele
print("\n📁 MEVCUT CROP KLASÖRLERİ:")
for item in sorted(CROPS_DIR.iterdir()):
    if item.is_dir():
        png_count = len(list(item.rglob("*.png")))
        print(f"   {item.name}: {png_count} PNG")

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır")

def preprocess(img):
    w, h = img.size
    if h < 80:
        scale = 80 / h
        img = img.resize((int(w * scale), 80), Image.Resampling.LANCZOS)
    if img.mode != 'L':
        img = img.convert('L')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img

def has_answer_pattern(text):
    """Cevap anahtarı pattern'i var mı?"""
    text = text.upper()
    # 1.A 2.B pattern
    if re.search(r'\d+\s*[.\-:)]\s*[A-E]', text):
        return True
    # Ardışık A-E harfleri (en az 5 tane)
    letters = re.findall(r'[A-E]', text)
    if len(letters) >= 5:
        return True
    return False

# Her class için analiz
classes_to_check = ['cozum', 'cevaplar_v2', 'soru']

for class_name in classes_to_check:
    class_dir = CROPS_DIR / class_name
    if not class_dir.exists():
        continue
    
    print(f"\n{'='*70}")
    print(f"📂 {class_name.upper()} CLASS ANALİZİ")
    print('='*70)
    
    # Kitapları say
    books = [d for d in class_dir.iterdir() if d.is_dir()]
    total_pngs = sum(len(list(b.glob("*.png"))) for b in books)
    
    print(f"   Kitap: {len(books)}, Toplam crop: {total_pngs}")
    
    # Rastgele 20 örnek analiz et
    samples = []
    answer_like = 0
    
    for book in books[:10]:
        try:
            pngs = sorted([f for f in os.listdir(book) if f.endswith('.png')])[:5]
        except:
            continue
        
        for png in pngs:
            if len(samples) >= 20:
                break
            
            try:
                img = Image.open(book / png)
                img_proc = preprocess(img)
                result = reader.readtext(np.array(img_proc), detail=0)
                text = ' '.join(result)
                
                is_answer = has_answer_pattern(text)
                if is_answer:
                    answer_like += 1
                
                samples.append({
                    'book': book.name[:30],
                    'file': png,
                    'size': img.size,
                    'text': text[:60],
                    'is_answer': is_answer
                })
            except:
                pass
    
    print(f"\n   📊 ÖRNEK ANALİZ ({len(samples)} crop):")
    print(f"   Cevap benzeri: {answer_like} ({answer_like/max(1,len(samples))*100:.0f}%)")
    
    print(f"\n   Örnekler:")
    for s in samples[:15]:
        marker = "✅" if s['is_answer'] else "  "
        print(f"   {marker} {s['book'][:25]}... | {s['size'][0]}x{s['size'][1]} | '{s['text'][:40]}...'")

print("\n" + "=" * 70)
print("ANALİZ TAMAMLANDI")
print("=" * 70)
