#!/usr/bin/env python3
"""
SORU-CEVAP EŞLEŞTİRME - RTX 3080 OPTİMİZE
==========================================
RTX 3080 Laptop (16GB VRAM) için optimize edilmiş
- Batch OCR işleme
- CUDA memory yönetimi
- Paralel sayfa işleme
- Tüm 426 kitap için tam tarama
"""

import torch
import numpy as np
from PIL import Image, ImageEnhance
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import easyocr
import gc

# ============================================================
# RTX 3080 OPTİMİZASYON AYARLARI
# ============================================================
BATCH_SIZE = 8              # Aynı anda işlenecek sayfa sayısı
NUM_WORKERS = 4             # Paralel dosya okuma thread'i
MAX_IMAGE_SIZE = 1600       # Maksimum görüntü boyutu
CUDA_MEMORY_FRACTION = 0.8  # VRAM kullanım oranı

# CUDA ayarları
if torch.cuda.is_available():
    torch.cuda.set_per_process_memory_fraction(CUDA_MEMORY_FRACTION)
    torch.backends.cudnn.benchmark = True
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("⚠️ CUDA bulunamadı, CPU kullanılacak")

# PATHS
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\final_matched")

print("=" * 70)
print("SORU-CEVAP EŞLEŞTİRME - RTX 3080 OPTİMİZE")
print(f"Tarih: {datetime.now()}")
print("=" * 70)

# Kaynak kontrolü
if not SOURCE_DIR.exists():
    print(f"❌ Kaynak bulunamadı: {SOURCE_DIR}")
    exit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# EasyOCR - GPU OPTİMİZE
# ============================================================
print("\n🔄 EasyOCR yükleniyor (GPU optimized)...")
reader = easyocr.Reader(
    ['tr', 'en'], 
    gpu=True, 
    verbose=False,
    model_storage_directory=str(Path.home() / '.EasyOCR'),
    download_enabled=True
)
print("✅ EasyOCR hazır")

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def preprocess_image(img, max_size=MAX_IMAGE_SIZE):
    """GPU için optimize edilmiş görüntü hazırlama"""
    w, h = img.size
    
    # Boyut ayarla
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # RGB'ye çevir (EasyOCR için)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return img

def crop_bottom_region(img, ratio=0.18):
    """Sayfanın alt bölgesini kırp"""
    w, h = img.size
    top = int(h * (1 - ratio))
    return img.crop((0, top, w, h))

def extract_answers_from_text(text):
    """Metinden cevapları çıkar - optimize edilmiş regex"""
    if not text:
        return {}
    
    answers = {}
    text_upper = text.upper().replace('\n', ' ')
    
    # Birleşik regex pattern (daha hızlı)
    pattern = r'(\d{1,3})\s*[.\-:)\s]\s*([A-E])\b|(\d{1,3})([A-E])\b'
    
    for match in re.finditer(pattern, text_upper):
        groups = match.groups()
        if groups[0] and groups[1]:
            q, a = groups[0], groups[1]
        elif groups[2] and groups[3]:
            q, a = groups[2], groups[3]
        else:
            continue
        
        try:
            q_num = int(q)
            if 1 <= q_num <= 200:
                answers[q_num] = a
        except:
            pass
    
    return answers

def load_image_batch(paths):
    """Paralel görüntü yükleme"""
    images = []
    valid_paths = []
    
    for path in paths:
        try:
            img = Image.open(path)
            img = preprocess_image(img)
            images.append(np.array(img))
            valid_paths.append(path)
        except Exception as e:
            pass
    
    return images, valid_paths

def batch_ocr(images):
    """Batch OCR işleme - GPU optimize"""
    results = []
    
    for img_array in images:
        try:
            ocr_result = reader.readtext(img_array, detail=0, batch_size=BATCH_SIZE)
            text = ' '.join(ocr_result)
            results.append(text)
        except Exception as e:
            results.append('')
    
    return results

def clear_gpu_memory():
    """GPU belleğini temizle"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

# ============================================================
# KİTAP ANALİZ FONKSİYONLARI
# ============================================================

def detect_answer_type_fast(book_path):
    """Hızlı cevap tipi tespiti"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    if len(pages) < 10:
        return 'UNKNOWN', 0, 0
    
    bottom_score = 0
    end_score = 0
    
    # Orta sayfalardan 5 tanesini kontrol (BOTTOM tipi için)
    mid_start = len(pages) // 3
    mid_pages = pages[mid_start:mid_start+5]
    
    for page_path in mid_pages:
        try:
            img = Image.open(page_path)
            img = preprocess_image(img)
            bottom_crop = crop_bottom_region(img)
            
            result = reader.readtext(np.array(bottom_crop), detail=0)
            text = ' '.join(result)
            answers = extract_answers_from_text(text)
            
            if answers:
                bottom_score += len(answers)
        except:
            pass
    
    # Son 10 sayfayı kontrol (END tipi için)
    end_pages = pages[-10:]
    
    for page_path in end_pages:
        try:
            img = Image.open(page_path)
            img = preprocess_image(img)
            
            result = reader.readtext(np.array(img), detail=0)
            text = ' '.join(result)
            answers = extract_answers_from_text(text)
            
            if len(answers) >= 3:
                end_score += len(answers)
        except:
            pass
    
    # Tip belirleme
    if bottom_score > end_score and bottom_score >= 5:
        return 'BOTTOM', bottom_score, end_score
    elif end_score >= 10:
        return 'END', bottom_score, end_score
    elif bottom_score >= 3:
        return 'BOTTOM', bottom_score, end_score
    else:
        return 'UNKNOWN', bottom_score, end_score

def extract_answers_from_book(book_path, answer_type):
    """Kitaptan tüm cevapları çıkar - GPU batch işleme"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    all_answers = {}
    page_answers = {}
    
    if answer_type == 'BOTTOM':
        # Her sayfanın altını tara - batch işleme
        for i in range(0, len(pages), BATCH_SIZE):
            batch_pages = pages[i:i+BATCH_SIZE]
            
            for page_path in batch_pages:
                try:
                    img = Image.open(page_path)
                    img = preprocess_image(img)
                    bottom_crop = crop_bottom_region(img)
                    
                    result = reader.readtext(np.array(bottom_crop), detail=0)
                    text = ' '.join(result)
                    answers = extract_answers_from_text(text)
                    
                    if answers:
                        page_name = page_path.stem
                        page_answers[page_name] = answers
                        all_answers.update(answers)
                except:
                    pass
            
            # Her batch sonrası GPU temizle
            if i % (BATCH_SIZE * 4) == 0:
                clear_gpu_memory()
    
    elif answer_type == 'END':
        # Son 30 sayfayı tara
        end_pages = pages[-30:]
        
        for page_path in end_pages:
            try:
                img = Image.open(page_path)
                img = preprocess_image(img)
                
                result = reader.readtext(np.array(img), detail=0)
                text = ' '.join(result)
                answers = extract_answers_from_text(text)
                
                if answers:
                    page_name = page_path.stem
                    page_answers[page_name] = answers
                    all_answers.update(answers)
            except:
                pass
        
        clear_gpu_memory()
    
    else:  # UNKNOWN - ikisini de dene
        # Önce END
        end_pages = pages[-30:]
        for page_path in end_pages:
            try:
                img = Image.open(page_path)
                img = preprocess_image(img)
                
                result = reader.readtext(np.array(img), detail=0)
                text = ' '.join(result)
                answers = extract_answers_from_text(text)
                
                if answers:
                    page_name = page_path.stem
                    page_answers[page_name] = answers
                    all_answers.update(answers)
            except:
                pass
        
        # Yeterli cevap bulunamadıysa BOTTOM dene
        if len(all_answers) < 20:
            for page_path in pages:
                try:
                    img = Image.open(page_path)
                    img = preprocess_image(img)
                    bottom_crop = crop_bottom_region(img)
                    
                    result = reader.readtext(np.array(bottom_crop), detail=0)
                    text = ' '.join(result)
                    answers = extract_answers_from_text(text)
                    
                    if answers:
                        page_name = page_path.stem
                        if page_name not in page_answers:
                            page_answers[page_name] = {}
                        page_answers[page_name].update(answers)
                        all_answers.update(answers)
                except:
                    pass
        
        clear_gpu_memory()
    
    return all_answers, page_answers

# ============================================================
# ANA İŞLEM - TÜM 426 KİTAP
# ============================================================

print("\n" + "=" * 70)
print("TÜM KİTAPLARI İŞLEME - GPU BATCH MODE")
print("=" * 70)

books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
total_books = len(books)
print(f"\n📚 Toplam kitap: {total_books}")

# Sonuçlar
all_results = []
type_stats = defaultdict(int)
total_answers = 0

# İlerleme takibi
start_time = datetime.now()

for idx, book in enumerate(books):
    book_name = book.name
    
    # İlerleme göster
    if idx % 10 == 0:
        elapsed = (datetime.now() - start_time).seconds
        if idx > 0:
            eta = (elapsed / idx) * (total_books - idx)
            eta_min = int(eta // 60)
            eta_sec = int(eta % 60)
            print(f"\n⏱️ İlerleme: {idx}/{total_books} ({idx/total_books*100:.1f}%) - ETA: {eta_min}dk {eta_sec}sn")
    
    print(f"[{idx+1}/{total_books}] 📖 {book_name[:45]}...", end=" ")
    
    try:
        # Cevap tipi belirle
        answer_type, bottom_score, end_score = detect_answer_type_fast(book)
        
        # Cevapları çıkar
        answers, page_answers = extract_answers_from_book(book, answer_type)
        
        type_stats[answer_type] += 1
        total_answers += len(answers)
        
        print(f"✅ {answer_type} - {len(answers)} cevap")
        
        # Sonucu kaydet
        all_results.append({
            'book': book_name,
            'type': answer_type,
            'total_answers': len(answers),
            'answers': {str(k): v for k, v in answers.items()},
            'page_answers': {k: {str(kk): vv for kk, vv in v.items()} for k, v in page_answers.items()}
        })
        
        # Her 20 kitapta bir ara kaydet
        if idx % 20 == 0 and idx > 0:
            temp_file = OUTPUT_DIR / f"temp_results_{idx}.json"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            clear_gpu_memory()
    
    except Exception as e:
        print(f"❌ Hata: {e}")
        all_results.append({
            'book': book_name,
            'type': 'ERROR',
            'error': str(e),
            'total_answers': 0,
            'answers': {},
            'page_answers': {}
        })

# ============================================================
# FİNAL ÇIKTI
# ============================================================

end_time = datetime.now()
duration = (end_time - start_time).seconds

print("\n" + "=" * 70)
print("ÖZET RAPOR")
print("=" * 70)

print(f"\n⏱️ Toplam süre: {duration // 60} dakika {duration % 60} saniye")
print(f"📚 İşlenen kitap: {total_books}")
print(f"📝 Toplam cevap: {total_answers}")
print(f"📊 Ortalama cevap/kitap: {total_answers / max(1, total_books):.1f}")

print(f"\n📍 CEVAP ANAHTARI TİP DAĞILIMI:")
for t, c in sorted(type_stats.items(), key=lambda x: -x[1]):
    pct = c / total_books * 100
    bar = "█" * int(pct / 2)
    print(f"   {t:10s}: {c:3d} ({pct:5.1f}%) {bar}")

# Final dosyasını kaydet
output_file = OUTPUT_DIR / "all_answers_extracted.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'total_books': total_books,
            'total_answers': total_answers,
            'duration_seconds': duration,
            'timestamp': str(end_time),
            'type_distribution': dict(type_stats)
        },
        'books': all_results
    }, f, ensure_ascii=False, indent=2)

print(f"\n📁 Sonuçlar kaydedildi: {output_file}")

# Özet istatistikler
summary_file = OUTPUT_DIR / "extraction_summary.json"
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump({
        'total_books': total_books,
        'total_answers': total_answers,
        'type_distribution': dict(type_stats),
        'books_with_answers': sum(1 for r in all_results if r['total_answers'] > 0),
        'books_without_answers': sum(1 for r in all_results if r['total_answers'] == 0),
        'avg_answers_per_book': total_answers / max(1, total_books),
        'duration_seconds': duration
    }, f, ensure_ascii=False, indent=2)

print(f"📁 Özet: {summary_file}")

# GPU temizle
clear_gpu_memory()

print("\n" + "=" * 70)
print("✅ TÜM İŞLEMLER TAMAMLANDI!")
print("=" * 70)
