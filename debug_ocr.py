#!/usr/bin/env python3
"""
Cevap Anahtarı OCR Debug - Kök Sebep Analizi
=============================================
"""

import os
import re
from pathlib import Path
from PIL import Image
import numpy as np

# EasyOCR
import easyocr

CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")

print("=" * 70)
print("  CEVAP ANAHTARI OCR - DEBUG ANALİZİ")
print("=" * 70)

# EasyOCR başlat
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True)
print("✅ Yüklendi\n")

# İlk 5 kitaptan birer örnek al
book_dirs = [d for d in os.listdir(str(CROPS_DIR)) if os.path.isdir(CROPS_DIR / d)][:10]

print(f"📊 Test edilecek kitap sayısı: {len(book_dirs)}\n")
print("-" * 70)

total_crops_tested = 0
total_answers_found = 0
ocr_outputs = []

for book_name in book_dirs:
    book_path = CROPS_DIR / book_name
    
    try:
        png_files = [f for f in os.listdir(str(book_path)) if f.endswith('.png')][:3]  # Her kitaptan 3 crop
    except:
        continue
    
    if not png_files:
        continue
    
    print(f"\n📚 KİTAP: {book_name[:50]}...")
    
    for png_file in png_files:
        crop_path = book_path / png_file
        total_crops_tested += 1
        
        try:
            # PIL ile yükle
            img = Image.open(str(crop_path))
            img_array = np.array(img)
            
            # Görüntü boyutu
            h, w = img_array.shape[:2]
            
            # OCR yap - detaylı sonuç
            result_detailed = reader.readtext(img_array, detail=1)
            result_simple = reader.readtext(img_array, detail=0)
            
            raw_text = ' '.join(result_simple)
            
            print(f"\n   📄 {png_file}")
            print(f"      Boyut: {w}x{h} px")
            print(f"      OCR Çıktısı: '{raw_text[:100]}{'...' if len(raw_text) > 100 else ''}'")
            
            # Detaylı sonuçları göster
            if result_detailed:
                print(f"      Tespit edilen metin kutuları: {len(result_detailed)}")
                for i, (bbox, text, conf) in enumerate(result_detailed[:5]):
                    print(f"         [{i+1}] '{text}' (güven: {conf:.2f})")
            
            # Mevcut regex pattern'i test et
            text_upper = raw_text.upper()
            pattern1 = r'(\d{1,3})\s*[.\-:\s)]\s*([A-E])\b'
            matches = re.findall(pattern1, text_upper)
            
            if matches:
                print(f"      ✅ Eşleşen cevaplar: {matches[:10]}")
                total_answers_found += len(matches)
            else:
                print(f"      ❌ Regex eşleşmesi YOK")
                
                # Alternatif pattern'leri dene
                # Pattern: Sadece harfler (A B C D E formatı)
                pattern_letters = r'\b([A-E])\b'
                letters = re.findall(pattern_letters, text_upper)
                if letters:
                    print(f"      💡 Sadece harfler: {letters[:20]}")
                
                # Pattern: Tablo formatı (1 A 2 B 3 C)
                pattern_table = r'(\d+)\s+([A-E])'
                table_matches = re.findall(pattern_table, text_upper)
                if table_matches:
                    print(f"      💡 Tablo formatı: {table_matches[:10]}")
            
            ocr_outputs.append({
                "file": png_file,
                "book": book_name,
                "size": f"{w}x{h}",
                "raw_text": raw_text,
                "matches": matches
            })
            
        except Exception as e:
            print(f"      ❌ Hata: {e}")

print("\n" + "=" * 70)
print("  ÖZET")
print("=" * 70)
print(f"\n📊 Test edilen crop: {total_crops_tested}")
print(f"📊 Bulunan cevap: {total_answers_found}")
print(f"📊 Başarı oranı: {total_answers_found / max(total_crops_tested, 1) * 100:.1f}%")

# En yaygın OCR çıktı formatlarını analiz et
print("\n" + "-" * 70)
print("  OCR ÇIKTI ANALİZİ")
print("-" * 70)

# Boş olmayan çıktıları göster
non_empty = [o for o in ocr_outputs if o["raw_text"].strip()]
empty = [o for o in ocr_outputs if not o["raw_text"].strip()]

print(f"\n📝 Metin bulunan crop: {len(non_empty)}")
print(f"📝 Boş çıktı: {len(empty)}")

if non_empty:
    print("\n🔍 Örnek OCR çıktıları:")
    for o in non_empty[:5]:
        print(f"\n   Dosya: {o['file']}")
        print(f"   Ham metin: '{o['raw_text']}'")

print("\n" + "=" * 70)
print("  ÖNERİLER")
print("=" * 70)

if len(empty) > len(non_empty) * 0.5:
    print("\n⚠️ Çoğu crop'tan metin okunamıyor!")
    print("   Olası sebepler:")
    print("   1. Görüntü çözünürlüğü çok düşük")
    print("   2. Cevap kutuları görsel/grafik içeriyor (metin değil)")
    print("   3. Görüntü ön işleme gerekiyor (contrast, threshold)")

if total_answers_found == 0:
    print("\n⚠️ Regex pattern'i metin formatına uymuyor!")
    print("   Cevap anahtarı formatını kontrol edin:")
    print("   - Türk soru bankalarında genellikle tablo formatı kullanılır")
    print("   - '1-A 2-B' yerine '1 A 2 B' veya grid formatı olabilir")
