#!/usr/bin/env python3
"""
SORU-CEVAP EŞLEŞTİRME - ULTRA HIZLI VERSİYON
=============================================
RTX 3080 için maksimum optimizasyon
Hedef: 426 kitap < 30 dakika
"""

import torch
import numpy as np
from PIL import Image
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import easyocr
import gc

# ============================================================
# HIZLI AYARLAR
# ============================================================
MAX_IMAGE_SIZE = 1200       # Daha küçük = daha hızlı
END_PAGES_TO_CHECK = 15     # Sadece son 15 sayfa (30 yerine)
BOTTOM_PAGES_SAMPLE = 3     # Tip tespiti için sadece 3 sayfa
SKIP_TYPE_DETECTION = True  # Tip tespitini atla, direkt END varsay

# CUDA
if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# PATHS
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\final_matched")

print("=" * 70)
print("SORU-CEVAP EŞLEŞTİRME - ULTRA HIZLI")
print(f"Tarih: {datetime.now()}")
print("=" * 70)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# EasyOCR - minimal config
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır")

def fast_preprocess(img_path, max_size=MAX_IMAGE_SIZE):
    """Ultra hızlı görüntü hazırlama"""
    img = Image.open(img_path)
    w, h = img.size
    
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    return np.array(img)

def extract_answers(text):
    """Hızlı cevap çıkarma"""
    if not text or len(text) < 3:
        return {}
    
    answers = {}
    text = text.upper()
    
    # Tek regex
    for match in re.finditer(r'(\d{1,3})\s*[.\-:)\s]?\s*([A-E])\b', text):
        try:
            q = int(match.group(1))
            a = match.group(2)
            if 1 <= q <= 200:
                answers[q] = a
        except:
            pass
    
    return answers

def process_book_fast(book_path):
    """Kitabı hızlıca işle - sadece son sayfalar"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    if len(pages) < 5:
        return {}, 'SKIP'
    
    all_answers = {}
    
    # STRATEJI 1: Son 15 sayfayı tara (kitap sonu cevap anahtarı)
    end_pages = pages[-END_PAGES_TO_CHECK:]
    
    for page_path in end_pages:
        try:
            img_array = fast_preprocess(page_path)
            result = reader.readtext(img_array, detail=0)
            text = ' '.join(result)
            answers = extract_answers(text)
            
            if answers:
                all_answers.update(answers)
        except:
            pass
    
    # Yeterli cevap bulunduysa bitir
    if len(all_answers) >= 10:
        return all_answers, 'END'
    
    # STRATEJI 2: Sayfa altlarını kontrol et (bottom tipi)
    # Sadece belirli aralıklardaki sayfaları kontrol et
    check_indices = [len(pages)//4, len(pages)//2, 3*len(pages)//4]
    
    for idx in check_indices:
        if idx >= len(pages):
            continue
        
        page_path = pages[idx]
        try:
            img = Image.open(page_path)
            w, h = img.size
            
            # Alt %20'yi kırp
            bottom = img.crop((0, int(h * 0.80), w, h))
            
            if max(bottom.size) > 800:
                scale = 800 / max(bottom.size)
                bottom = bottom.resize((int(bottom.size[0] * scale), int(bottom.size[1] * scale)))
            
            if bottom.mode != 'RGB':
                bottom = bottom.convert('RGB')
            
            result = reader.readtext(np.array(bottom), detail=0)
            text = ' '.join(result)
            answers = extract_answers(text)
            
            if answers:
                all_answers.update(answers)
        except:
            pass
    
    answer_type = 'END' if len(all_answers) >= 5 else 'MIXED'
    return all_answers, answer_type

# ============================================================
# ANA İŞLEM
# ============================================================

print("\n" + "=" * 70)
print("HIZLI İŞLEME BAŞLIYOR")
print("=" * 70)

books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
total_books = len(books)
print(f"\n📚 Toplam kitap: {total_books}")

all_results = []
type_stats = defaultdict(int)
total_answers = 0

start_time = datetime.now()

for idx, book in enumerate(books):
    # İlerleme
    if idx % 20 == 0 and idx > 0:
        elapsed = (datetime.now() - start_time).total_seconds()
        speed = idx / elapsed
        eta = (total_books - idx) / speed
        print(f"\n⏱️ [{idx}/{total_books}] {idx/total_books*100:.1f}% - Hız: {speed:.1f} kitap/sn - ETA: {eta/60:.1f} dk")
    
    book_name = book.name
    print(f"[{idx+1}/{total_books}] {book_name[:40]}...", end=" ", flush=True)
    
    try:
        answers, answer_type = process_book_fast(book)
        
        type_stats[answer_type] += 1
        total_answers += len(answers)
        
        print(f"✅ {len(answers)} cevap")
        
        all_results.append({
            'book': book_name,
            'type': answer_type,
            'total_answers': len(answers),
            'answers': {str(k): v for k, v in answers.items()}
        })
        
    except Exception as e:
        print(f"❌ {e}")
        all_results.append({
            'book': book_name,
            'type': 'ERROR',
            'total_answers': 0,
            'answers': {}
        })
    
    # Her 50 kitapta GPU temizle
    if idx % 50 == 0:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

# ============================================================
# SONUÇ
# ============================================================

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "=" * 70)
print("ÖZET")
print("=" * 70)

print(f"\n⏱️ Toplam süre: {duration/60:.1f} dakika")
print(f"📚 İşlenen: {total_books} kitap")
print(f"📝 Toplam cevap: {total_answers}")
print(f"⚡ Hız: {total_books/duration:.2f} kitap/saniye")

print(f"\n📊 TİP DAĞILIMI:")
for t, c in sorted(type_stats.items(), key=lambda x: -x[1]):
    print(f"   {t}: {c} kitap ({c/total_books*100:.1f}%)")

# Kaydet
output_file = OUTPUT_DIR / "all_answers_fast.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'total_books': total_books,
            'total_answers': total_answers,
            'duration_minutes': duration/60,
            'speed_books_per_sec': total_books/duration
        },
        'books': all_results
    }, f, ensure_ascii=False, indent=2)

print(f"\n📁 Kaydedildi: {output_file}")

# Cevap bulunan kitaplar
books_with_answers = sum(1 for r in all_results if r['total_answers'] > 0)
print(f"\n✅ Cevap bulunan: {books_with_answers}/{total_books} kitap")
print(f"❌ Cevap bulunamayan: {total_books - books_with_answers} kitap")

print("\n" + "=" * 70)
print("TAMAMLANDI!")
print("=" * 70)
