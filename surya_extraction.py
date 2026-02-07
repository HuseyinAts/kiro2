#!/usr/bin/env python3
"""
CEVAP ANAHTARI ÇIKARMA - SURYA OCR
===================================
Surya OCR ile:
• 90+ dil desteği (Türkçe dahil)
• Yerleşik tablo tanıma
• Yerleşim analizi
• Yüksek doğruluk

Hedef: %50 → %70-80 doğruluk
"""

import torch
import numpy as np
from PIL import Image, ImageEnhance
import cv2
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import gc
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# SURYA OCR IMPORT
# ============================================================
print("🔄 Surya OCR yükleniyor...")
try:
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    from surya.table_rec import TableRecPredictor
    from surya.layout import LayoutPredictor
    print("✅ Surya OCR modülleri yüklendi")
except ImportError as e:
    print(f"❌ Surya OCR kurulu değil: {e}")
    print("   Kurulum: pip install surya-ocr")
    exit(1)

# ============================================================
# AYARLAR
# ============================================================
SCALE_FACTOR = 2.0          # 2x büyütme (Surya için yeterli)
CLAHE_CLIP_LIMIT = 2.0
END_PAGES_TO_CHECK = 20
BOTTOM_RATIO = 0.20

# GPU Kontrol
device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.cuda.is_available():
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("⚠️ CPU modu")

# PATHS
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\surya_results")

print("\n" + "=" * 70)
print("CEVAP ANAHTARI ÇIKARMA - SURYA OCR")
print(f"Tarih: {datetime.now()}")
print("=" * 70)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SURYA MODELLERİ BAŞLAT
# ============================================================
print("\n🔄 Surya modelleri yükleniyor (ilk seferde indirme gerekebilir)...")

try:
    # Detection (metin bölgesi tespiti)
    det_predictor = DetectionPredictor()
    print("   ✅ Detection predictor")
    
    # Recognition (OCR)
    rec_predictor = RecognitionPredictor()
    print("   ✅ Recognition predictor")
    
    # Table Recognition (tablo tanıma)
    table_predictor = TableRecPredictor()
    print("   ✅ Table predictor")
    
    # Layout (yerleşim analizi)
    layout_predictor = LayoutPredictor()
    print("   ✅ Layout predictor")
    
    print("✅ Tüm Surya modelleri hazır!")
    
except Exception as e:
    print(f"❌ Model yükleme hatası: {e}")
    print("   Modeller ilk kullanımda indirilecek...")

# ============================================================
# GÖRÜNTÜ İŞLEME
# ============================================================

def read_image_safe(img_path):
    """Türkçe karakter güvenli okuma"""
    try:
        img = Image.open(img_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        return None

def preprocess_pil(pil_img, scale=SCALE_FACTOR):
    """PIL görüntü ön işleme"""
    if pil_img is None:
        return None
    
    # Büyütme
    w, h = pil_img.size
    new_w, new_h = int(w * scale), int(h * scale)
    
    # Max boyut kontrolü
    if max(new_w, new_h) > 3000:
        ratio = 3000 / max(new_w, new_h)
        new_w, new_h = int(new_w * ratio), int(new_h * ratio)
    
    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Kontrast artır
    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.5)
    
    # Keskinlik artır
    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(1.5)
    
    return pil_img

def crop_bottom_pil(pil_img, ratio=BOTTOM_RATIO):
    """Sayfa altını kırp"""
    if pil_img is None:
        return None
    
    w, h = pil_img.size
    top = int(h * (1 - ratio))
    return pil_img.crop((0, top, w, h))

# ============================================================
# SURYA OCR FONKSİYONLARI
# ============================================================

def surya_ocr_full_page(pil_img):
    """Surya ile tam sayfa OCR"""
    if pil_img is None:
        return ""
    
    try:
        # Detection + Recognition
        det_results = det_predictor([pil_img])
        rec_results = rec_predictor([pil_img], det_results)
        
        # Metni birleştir
        text_lines = []
        for result in rec_results:
            for line in result.text_lines:
                text_lines.append(line.text)
        
        return ' '.join(text_lines)
    except Exception as e:
        return ""

def surya_table_extract(pil_img):
    """Surya ile tablo çıkarma"""
    if pil_img is None:
        return []
    
    try:
        table_results = table_predictor([pil_img])
        
        cells = []
        for result in table_results:
            if hasattr(result, 'cells'):
                for cell in result.cells:
                    if hasattr(cell, 'text'):
                        cells.append(cell.text)
        
        return cells
    except Exception as e:
        return []

def surya_layout_analyze(pil_img):
    """Surya ile yerleşim analizi"""
    if pil_img is None:
        return []
    
    try:
        layout_results = layout_predictor([pil_img])
        
        regions = []
        for result in layout_results:
            if hasattr(result, 'bboxes'):
                for bbox in result.bboxes:
                    regions.append({
                        'label': bbox.label if hasattr(bbox, 'label') else 'unknown',
                        'bbox': bbox.bbox if hasattr(bbox, 'bbox') else []
                    })
        
        return regions
    except Exception as e:
        return []

# ============================================================
# CEVAP ÇIKARMA
# ============================================================

def extract_answers_from_text(text):
    """Metinden cevapları çıkar"""
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

def extract_answers_from_cells(cells):
    """Tablo hücrelerinden cevapları çıkar"""
    answers = {}
    
    for cell in cells:
        cell_answers = extract_answers_from_text(cell)
        answers.update(cell_answers)
    
    return answers

def fix_ocr_errors(text):
    """OCR hatalarını düzelt"""
    replacements = [
        (r'[lI|](?=\s*[.\):-]?\s*[A-Ea-e])', '1'),
        (r'O(?=\s*[.\):-]?\s*[A-Ea-e])', '0'),
        (r'S(?=\d)', '5'),
        (r'Z(?=\d)', '2'),
        (r'\bI\b', '1'),
        (r'\bl\b', '1'),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    
    return text

# ============================================================
# KİTAP İŞLEME
# ============================================================

def process_book_surya(book_path):
    """Kitabı Surya OCR ile işle"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    if len(pages) < 5:
        return {}, 'SKIP'
    
    all_answers = {}
    method_used = 'NONE'
    
    # ========== STRATEJİ 1: SON SAYFALAR (Kitap sonu cevap anahtarı) ==========
    end_pages = pages[-END_PAGES_TO_CHECK:]
    end_answers = {}
    
    for page_path in end_pages:
        try:
            # Görüntüyü oku ve ön işle
            pil_img = read_image_safe(page_path)
            pil_img = preprocess_pil(pil_img)
            
            if pil_img is None:
                continue
            
            # ÖNCE TABLO DENEİ
            cells = surya_table_extract(pil_img)
            if cells:
                cell_answers = extract_answers_from_cells(cells)
                if cell_answers:
                    end_answers.update(cell_answers)
                    continue
            
            # TABLO YOKSA TAM SAYFA OCR
            text = surya_ocr_full_page(pil_img)
            text_answers = extract_answers_from_text(text)
            
            if text_answers:
                end_answers.update(text_answers)
                
        except Exception as e:
            pass
    
    # ========== STRATEJİ 2: SAYFA ALTLARI ==========
    bottom_answers = {}
    mid_start = len(pages) // 4
    sample_pages = pages[mid_start:mid_start+15]
    
    for page_path in sample_pages:
        try:
            pil_img = read_image_safe(page_path)
            if pil_img is None:
                continue
            
            # Alt bölgeyi kırp
            bottom_img = crop_bottom_pil(pil_img)
            bottom_img = preprocess_pil(bottom_img, scale=2.5)
            
            if bottom_img is None:
                continue
            
            # OCR
            text = surya_ocr_full_page(bottom_img)
            text_answers = extract_answers_from_text(text)
            
            if text_answers:
                bottom_answers.update(text_answers)
                
        except:
            pass
    
    # ========== EN İYİ STRATEJİYİ SEÇ ==========
    if len(end_answers) > len(bottom_answers):
        all_answers = end_answers
        method_used = 'END'
    elif len(bottom_answers) > 5:
        all_answers = bottom_answers
        method_used = 'BOTTOM'
    else:
        all_answers = {**bottom_answers, **end_answers}
        method_used = 'MIXED'
    
    return all_answers, method_used

# ============================================================
# ANA İŞLEM
# ============================================================

print("\n" + "=" * 70)
print("TÜM KİTAPLARI İŞLEME - SURYA OCR")
print("=" * 70)

books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
total_books = len(books)
print(f"\n📚 Toplam kitap: {total_books}")

# Test modu
TEST_MODE = False
if TEST_MODE:
    books = books[:10]
    print(f"⚠️ TEST MODU: İlk {len(books)} kitap")

all_results = []
type_stats = defaultdict(int)
total_answers = 0
books_with_many_answers = 0

start_time = datetime.now()

for idx, book in enumerate(books):
    # İlerleme
    if idx % 10 == 0 and idx > 0:
        elapsed = (datetime.now() - start_time).total_seconds()
        speed = idx / elapsed if elapsed > 0 else 0
        eta = (total_books - idx) / speed if speed > 0 else 0
        
        current_avg = total_answers / idx if idx > 0 else 0
        print(f"\n⏱️ [{idx}/{total_books}] {idx/total_books*100:.1f}%")
        print(f"   Hız: {speed:.3f} kitap/sn | ETA: {eta/60:.1f} dk")
        print(f"   Toplam cevap: {total_answers} | Ort: {current_avg:.1f}/kitap")
    
    book_name = book.name
    print(f"[{idx+1}/{total_books}] {book_name[:40]}...", end=" ", flush=True)
    
    try:
        answers, method = process_book_surya(book)
        
        type_stats[method] += 1
        total_answers += len(answers)
        
        if len(answers) >= 20:
            books_with_many_answers += 1
        
        status = "✅" if len(answers) >= 10 else "⚠️" if len(answers) > 0 else "❌"
        print(f"{status} {method} - {len(answers)} cevap")
        
        all_results.append({
            'book': book_name,
            'method': method,
            'total_answers': len(answers),
            'answers': {str(k): v for k, v in sorted(answers.items())}
        })
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        all_results.append({
            'book': book_name,
            'method': 'ERROR',
            'total_answers': 0,
            'answers': {}
        })
    
    # GPU temizle
    if idx % 20 == 0:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

# ============================================================
# SONUÇ
# ============================================================

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "=" * 70)
print("ÖZET RAPOR - SURYA OCR")
print("=" * 70)

print(f"\n⏱️ Toplam süre: {duration/60:.1f} dakika")
print(f"📚 İşlenen: {len(books)} kitap")
print(f"📝 Toplam cevap: {total_answers}")
print(f"📊 Ortalama cevap/kitap: {total_answers/max(1,len(books)):.1f}")
print(f"✅ 20+ cevaplı kitap: {books_with_many_answers} ({books_with_many_answers/max(1,len(books))*100:.1f}%)")

print(f"\n📍 YÖNTEM DAĞILIMI:")
for t, c in sorted(type_stats.items(), key=lambda x: -x[1]):
    pct = c / len(books) * 100
    bar = "█" * int(pct / 3)
    print(f"   {t:10s}: {c:3d} ({pct:5.1f}%) {bar}")

# Kaydet
output_file = OUTPUT_DIR / "surya_answers.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'ocr_engine': 'Surya OCR',
            'total_books': len(books),
            'total_answers': total_answers,
            'avg_answers_per_book': total_answers / max(1, len(books)),
            'books_with_20plus_answers': books_with_many_answers,
            'duration_minutes': duration / 60,
        },
        'method_distribution': dict(type_stats),
        'books': all_results
    }, f, ensure_ascii=False, indent=2)

print(f"\n📁 Sonuçlar: {output_file}")

# Karşılaştırma
print("\n" + "=" * 70)
print("KARŞILAŞTIRMA")
print("=" * 70)
print(f"   EasyOCR (önceki):  2,436 cevap | Ort: 5.7/kitap")
print(f"   SURYA OCR (şimdi): {total_answers} cevap | Ort: {total_answers/max(1,len(books)):.1f}/kitap")

if total_answers > 2436:
    improvement = (total_answers / 2436 - 1) * 100
    print(f"\n   📈 İYİLEŞME: +{improvement:.1f}%")
else:
    print(f"\n   ⚠️ Beklenen iyileşme sağlanamadı")

print("\n" + "=" * 70)
print("TAMAMLANDI!")
print("=" * 70)
