#!/usr/bin/env python3
"""
CEVAP ANAHTARI ÇIKARMA - ÖN İŞLEME OPTİMİZE v3
===============================================
Türkçe karakter sorunu düzeltildi (PIL kullanımı)
"""

import torch
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import easyocr
import gc
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# AYARLAR
# ============================================================
SCALE_FACTOR = 3.0          # 3x büyütme
CLAHE_CLIP_LIMIT = 2.0      # CLAHE kontrast
CLAHE_GRID_SIZE = (8, 8)    # CLAHE grid
BILATERAL_D = 9             # Bilateral filtre
BILATERAL_SIGMA = 75        # Bilateral sigma
ADAPTIVE_BLOCK = 15         # Adaptif eşikleme blok
ADAPTIVE_C = 8              # Adaptif eşikleme C

MAX_IMAGE_SIZE = 4000       # Büyütme sonrası max boyut
END_PAGES_TO_CHECK = 20     # Son 20 sayfa kontrol

# CUDA
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# PATHS
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\final_matched_v3")

print("=" * 70)
print("CEVAP ANAHTARI ÇIKARMA - ÖN İŞLEME v3 (Türkçe Fix)")
print(f"Tarih: {datetime.now()}")
print("=" * 70)
print(f"\n⚙️ AYARLAR:")
print(f"   • Büyütme: {SCALE_FACTOR}x")
print(f"   • CLAHE: clip={CLAHE_CLIP_LIMIT}, grid={CLAHE_GRID_SIZE}")
print(f"   • Adaptif eşikleme: block={ADAPTIVE_BLOCK}, C={ADAPTIVE_C}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ EasyOCR hazır")

# ============================================================
# TÜRKÇE KARAKTER UYUMLU GÖRÜNTÜ OKUMA
# ============================================================

def read_image_turkish_safe(img_path):
    """
    Türkçe karakterli dosya yollarını güvenli okuma
    PIL kullanarak Unicode desteği
    """
    try:
        # PIL ile oku (Unicode destekli)
        pil_img = Image.open(img_path)
        
        # RGB'ye çevir
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        # NumPy array'e çevir
        img_array = np.array(pil_img)
        
        # BGR'ye çevir (OpenCV formatı)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_bgr
    except Exception as e:
        print(f"      ⚠️ Okuma hatası: {e}")
        return None

# ============================================================
# ÖN İŞLEME FONKSİYONLARI
# ============================================================

def preprocess_image(img_path, scale=SCALE_FACTOR):
    """
    KRİTİK ÖN İŞLEME PİPELINE
    """
    # Türkçe güvenli okuma
    img = read_image_turkish_safe(img_path)
    if img is None:
        return None
    
    h, w = img.shape[:2]
    
    # ADIM 1: 3x BÜYÜTME
    new_w, new_h = int(w * scale), int(h * scale)
    
    # Maksimum boyut kontrolü
    if max(new_w, new_h) > MAX_IMAGE_SIZE:
        ratio = MAX_IMAGE_SIZE / max(new_w, new_h)
        new_w, new_h = int(new_w * ratio), int(new_h * ratio)
    
    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # ADIM 2: GRİ TONLAMA
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # ADIM 3: CLAHE KONTRAST
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_GRID_SIZE)
    enhanced = clahe.apply(gray)
    
    # ADIM 4: BİLATERAL FİLTRE
    denoised = cv2.bilateralFilter(enhanced, BILATERAL_D, BILATERAL_SIGMA, BILATERAL_SIGMA)
    
    # ADIM 5: ADAPTİF EŞİKLEME
    binary = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 
        blockSize=ADAPTIVE_BLOCK, 
        C=ADAPTIVE_C
    )
    
    # ADIM 6: BEYAZ KENARLIK
    bordered = cv2.copyMakeBorder(binary, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
    
    return bordered

def preprocess_bottom_region(img_path, bottom_ratio=0.20, scale=SCALE_FACTOR):
    """Sayfa altı bölgesi için özel ön işleme"""
    # Türkçe güvenli okuma
    img = read_image_turkish_safe(img_path)
    if img is None:
        return None
    
    h, w = img.shape[:2]
    
    # Alt bölgeyi kırp
    top = int(h * (1 - bottom_ratio))
    bottom_region = img[top:h, 0:w]
    
    # Büyütme
    bh, bw = bottom_region.shape[:2]
    new_w, new_h = int(bw * scale), int(bh * scale)
    
    # Max boyut kontrolü
    if max(new_w, new_h) > 2000:
        ratio = 2000 / max(new_w, new_h)
        new_w, new_h = int(new_w * ratio), int(new_h * ratio)
    
    bottom_region = cv2.resize(bottom_region, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # Gri + CLAHE + Adaptif
    gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_GRID_SIZE)
    enhanced = clahe.apply(gray)
    denoised = cv2.bilateralFilter(enhanced, BILATERAL_D, BILATERAL_SIGMA, BILATERAL_SIGMA)
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, ADAPTIVE_BLOCK, ADAPTIVE_C)
    bordered = cv2.copyMakeBorder(binary, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
    
    return bordered

# ============================================================
# GELİŞMİŞ REGEX DESENLERİ
# ============================================================

def extract_answers_advanced(text):
    """Gelişmiş cevap çıkarma"""
    if not text or len(text) < 3:
        return {}
    
    text = fix_ocr_errors(text)
    text_upper = text.upper()
    
    answers = {}
    
    patterns = [
        r'(\d{1,3})\s*[.]\s*([A-E])\b',
        r'(\d{1,3})\s*\)\s*([A-E])\b',
        r'(\d{1,3})\s*[-]\s*([A-E])\b',
        r'(\d{1,3})\s*[:]\s*([A-E])\b',
        r'(\d{1,3})\s+([A-E])(?=\s|\d|$)',
        r'(\d{1,3})([A-E])(?=\s|\d|$)',
        r'([A-E])\s*[-.:)]\s*(\d{1,3})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            if match[0] in 'ABCDE' and match[1].isdigit():
                answer, q_num = match[0], match[1]
            else:
                q_num, answer = match[0], match[1]
            
            try:
                q = int(q_num)
                if 1 <= q <= 300 and answer in 'ABCDE':
                    answers[q] = answer
            except:
                pass
    
    return answers

def fix_ocr_errors(text):
    """OCR hatalarını düzelt"""
    replacements = [
        (r'[lI|](?=\s*[.\):-]?\s*[A-Ea-e])', '1'),
        (r'O(?=\s*[.\):-]?\s*[A-Ea-e])', '0'),
        (r'S(?=\d)', '5'),
        (r'Z(?=\d)', '2'),
        (r'G(?=\s*[.\):-]?\s*[A-Ea-e])', '6'),
        (r'B(?=\s*[.\):-]?\s*\d)', '8'),
        (r'\bI\b', '1'),
        (r'\bl\b', '1'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text

# ============================================================
# EasyOCR
# ============================================================

def ocr_with_easyocr(img_array):
    """EasyOCR ile OCR"""
    if img_array is None:
        return ""
    
    try:
        results = reader.readtext(
            img_array,
            allowlist='ABCDEabcde0123456789.()-: ',
            min_size=5,
            text_threshold=0.5,
            low_text=0.3,
            link_threshold=0.3,
            decoder='greedy',  # greedy daha hızlı, overflow yok
            contrast_ths=0.1,
            adjust_contrast=0.5,
        )
        
        text = ' '.join([r[1] for r in results])
        return text
    except Exception as e:
        return ""

# ============================================================
# KİTAP İŞLEME
# ============================================================

def process_book(book_path):
    """Kitabı işle"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    if len(pages) < 5:
        return {}, 'SKIP', 0
    
    all_answers = {}
    
    # STRATEJİ 1: SON SAYFALARI KONTROL
    end_pages = pages[-END_PAGES_TO_CHECK:]
    end_answers = {}
    
    for page_path in end_pages:
        try:
            processed = preprocess_image(page_path)
            if processed is None:
                continue
            
            text = ocr_with_easyocr(processed)
            answers = extract_answers_advanced(text)
            
            if answers:
                end_answers.update(answers)
        except:
            pass
    
    # STRATEJİ 2: SAYFA ALTLARI
    bottom_answers = {}
    mid_start = len(pages) // 4
    sample_pages = pages[mid_start:mid_start+15]
    
    for page_path in sample_pages:
        try:
            processed = preprocess_bottom_region(page_path)
            if processed is None:
                continue
            
            text = ocr_with_easyocr(processed)
            answers = extract_answers_advanced(text)
            
            if answers:
                bottom_answers.update(answers)
        except:
            pass
    
    # HANGİSİ DAHA İYİ?
    if len(end_answers) > len(bottom_answers):
        all_answers = end_answers
        answer_type = 'END'
    elif len(bottom_answers) > 5:
        all_answers = bottom_answers
        answer_type = 'BOTTOM'
    else:
        all_answers = {**bottom_answers, **end_answers}
        answer_type = 'MIXED'
    
    return all_answers, answer_type, 0

# ============================================================
# ANA İŞLEM
# ============================================================

print("\n" + "=" * 70)
print("TÜM KİTAPLARI İŞLEME")
print("=" * 70)

books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
total_books = len(books)
print(f"\n📚 Toplam kitap: {total_books}")

all_results = []
type_stats = defaultdict(int)
total_answers = 0
books_with_many_answers = 0

start_time = datetime.now()

for idx, book in enumerate(books):
    if idx % 20 == 0 and idx > 0:
        elapsed = (datetime.now() - start_time).total_seconds()
        speed = idx / elapsed
        eta = (total_books - idx) / speed if speed > 0 else 0
        
        current_avg = total_answers / idx if idx > 0 else 0
        print(f"\n⏱️ [{idx}/{total_books}] {idx/total_books*100:.1f}%")
        print(f"   Hız: {speed:.2f} kitap/sn | ETA: {eta/60:.1f} dk")
        print(f"   Toplam cevap: {total_answers} | Ort: {current_avg:.1f}/kitap")
    
    book_name = book.name
    print(f"[{idx+1}/{total_books}] {book_name[:40]}...", end=" ", flush=True)
    
    try:
        answers, answer_type, _ = process_book(book)
        
        type_stats[answer_type] += 1
        total_answers += len(answers)
        
        if len(answers) >= 20:
            books_with_many_answers += 1
        
        status = "✅" if len(answers) >= 10 else "⚠️" if len(answers) > 0 else "❌"
        print(f"{status} {answer_type} - {len(answers)} cevap")
        
        all_results.append({
            'book': book_name,
            'type': answer_type,
            'total_answers': len(answers),
            'answers': {str(k): v for k, v in sorted(answers.items())}
        })
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        all_results.append({
            'book': book_name,
            'type': 'ERROR',
            'total_answers': 0,
            'answers': {}
        })
    
    if idx % 30 == 0:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

# ============================================================
# SONUÇ
# ============================================================

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "=" * 70)
print("ÖZET RAPOR")
print("=" * 70)

print(f"\n⏱️ Toplam süre: {duration/60:.1f} dakika")
print(f"📚 İşlenen: {len(books)} kitap")
print(f"📝 Toplam cevap: {total_answers}")
print(f"📊 Ortalama cevap/kitap: {total_answers/max(1,len(books)):.1f}")
print(f"✅ 20+ cevaplı kitap: {books_with_many_answers} ({books_with_many_answers/max(1,len(books))*100:.1f}%)")

print(f"\n📍 TİP DAĞILIMI:")
for t, c in sorted(type_stats.items(), key=lambda x: -x[1]):
    pct = c / len(books) * 100
    bar = "█" * int(pct / 3)
    print(f"   {t:10s}: {c:3d} ({pct:5.1f}%) {bar}")

# Kaydet
output_file = OUTPUT_DIR / "answers_preprocessed_v3.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'total_books': len(books),
            'total_answers': total_answers,
            'avg_answers_per_book': total_answers / max(1, len(books)),
            'books_with_20plus_answers': books_with_many_answers,
            'duration_minutes': duration / 60,
        },
        'type_distribution': dict(type_stats),
        'books': all_results
    }, f, ensure_ascii=False, indent=2)

print(f"\n📁 Sonuçlar: {output_file}")

print("\n" + "=" * 70)
print("KARŞILAŞTIRMA")
print("=" * 70)
print(f"   ÖNCEKİ: 2,436 cevap | Ort: 5.7/kitap")
print(f"   ŞİMDİ:  {total_answers} cevap | Ort: {total_answers/max(1,len(books)):.1f}/kitap")

improvement = (total_answers / 2436 - 1) * 100 if total_answers > 0 else 0
print(f"\n   📈 İYİLEŞME: {'+' if improvement > 0 else ''}{improvement:.1f}%")

print("\n" + "=" * 70)
print("TAMAMLANDI!")
print("=" * 70)
