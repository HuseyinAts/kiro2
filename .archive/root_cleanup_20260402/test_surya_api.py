#!/usr/bin/env python3
"""
Surya 0.17.0 API Test Script
============================
Surya'nın gerçek API yapısını keşfet.
"""

import sys
from pathlib import Path

# Test görüntüsü bul
test_dir = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
kitaplar = sorted([d for d in test_dir.iterdir() if d.is_dir()])

if not kitaplar:
    print("❌ Kitap bulunamadı!")
    sys.exit(1)

# İlk kitabın son sayfasını al
ilk_kitap = kitaplar[0]
sayfalar = sorted(ilk_kitap.glob("*.png")) + sorted(ilk_kitap.glob("*.jpg"))

if not sayfalar:
    print(f"❌ {ilk_kitap.name} içinde sayfa bulunamadı!")
    sys.exit(1)

test_sayfa = sayfalar[-1]  # Son sayfa
print(f"📄 Test sayfası: {test_sayfa}")

# PIL ile yükle
from PIL import Image
img = Image.open(test_sayfa).convert('RGB')
print(f"📐 Boyut: {img.size}")

# Surya modüllerini yükle
print("\n🔄 Surya modülleri yükleniyor...")

from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from surya.table_rec import TableRecPredictor

try:
    from surya.foundation import FoundationPredictor
    has_foundation = True
except ImportError:
    has_foundation = False

print(f"   Foundation: {'✅' if has_foundation else '❌'}")

# Modelleri yükle
det = DetectionPredictor()
print("   ✅ Detection")

if has_foundation:
    foundation = FoundationPredictor()
    rec = RecognitionPredictor(foundation)
else:
    rec = RecognitionPredictor()
print("   ✅ Recognition")

table = TableRecPredictor()
print("   ✅ Table")

# ========== TEST 1: OCR ==========
print("\n" + "="*60)
print("TEST 1: OCR (Recognition)")
print("="*60)

try:
    ocr_results = rec([img], det_predictor=det)
    print(f"Sonuç tipi: {type(ocr_results)}")
    print(f"Sonuç uzunluğu: {len(ocr_results)}")
    
    if ocr_results:
        result = ocr_results[0]
        print(f"\nResult tipi: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        # text_lines var mı?
        if hasattr(result, 'text_lines'):
            print(f"\ntext_lines tipi: {type(result.text_lines)}")
            print(f"text_lines uzunluğu: {len(result.text_lines)}")
            
            if result.text_lines:
                line = result.text_lines[0]
                print(f"\nİlk satır tipi: {type(line)}")
                print(f"İlk satır attributes: {dir(line)}")
                
                if hasattr(line, 'text'):
                    print(f"İlk satır text: {line.text[:100]}..." if len(line.text) > 100 else f"İlk satır text: {line.text}")
                
                if hasattr(line, 'confidence'):
                    print(f"İlk satır confidence: {line.confidence}")
        
        # Tüm metni birleştir
        if hasattr(result, 'text_lines'):
            full_text = ' '.join([
                line.text for line in result.text_lines 
                if hasattr(line, 'text') and line.text
            ])
            print(f"\n📝 Tam metin ({len(full_text)} karakter):")
            print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
            
except Exception as e:
    print(f"❌ OCR hatası: {e}")
    import traceback
    traceback.print_exc()

# ========== TEST 2: TABLO ==========
print("\n" + "="*60)
print("TEST 2: Tablo Tanıma")
print("="*60)

try:
    table_results = table([img])
    print(f"Sonuç tipi: {type(table_results)}")
    print(f"Sonuç uzunluğu: {len(table_results)}")
    
    if table_results:
        result = table_results[0]
        print(f"\nResult tipi: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        # Farklı attribute'ları kontrol et
        for attr in ['cells', 'table_cells', 'rows', 'columns', 'text', 'tables']:
            if hasattr(result, attr):
                val = getattr(result, attr)
                print(f"\n✅ {attr} bulundu!")
                print(f"   Tip: {type(val)}")
                if hasattr(val, '__len__'):
                    print(f"   Uzunluk: {len(val)}")
                    if len(val) > 0:
                        print(f"   İlk eleman tipi: {type(val[0])}")
                        if hasattr(val[0], '__dict__'):
                            print(f"   İlk eleman attributes: {dir(val[0])}")
                        
except Exception as e:
    print(f"❌ Tablo hatası: {e}")
    import traceback
    traceback.print_exc()

# ========== TEST 3: DETECTION ==========
print("\n" + "="*60)
print("TEST 3: Detection (Metin Bölgeleri)")
print("="*60)

try:
    det_results = det([img])
    print(f"Sonuç tipi: {type(det_results)}")
    print(f"Sonuç uzunluğu: {len(det_results)}")
    
    if det_results:
        result = det_results[0]
        print(f"\nResult tipi: {type(result)}")
        print(f"Result attributes: {dir(result)}")
        
        if hasattr(result, 'bboxes'):
            print(f"\nbboxes sayısı: {len(result.bboxes)}")
            
except Exception as e:
    print(f"❌ Detection hatası: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ TEST TAMAMLANDI")
print("="*60)
