#!/usr/bin/env python3
"""
SORU-CEVAP EŞLEŞTİRME - HİBRİT ÇÖZÜM
=====================================
3 farklı cevap anahtarı konumunu destekler:
1. Kitap sonu (son 30 sayfa)
2. Sayfa altı (her sayfanın alt %15'i)
3. Bölüm sonu (test sonları)
"""

from PIL import Image, ImageEnhance
import numpy as np
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import easyocr

# PATHS
SOURCE_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\final_matched")

print("=" * 70)
print("SORU-CEVAP EŞLEŞTİRME - HİBRİT ÇÖZÜM")
print(f"Tarih: {datetime.now()}")
print("=" * 70)

# Kaynak kontrolü
if not SOURCE_DIR.exists():
    print(f"❌ Kaynak bulunamadı: {SOURCE_DIR}")
    # Alternatif ara
    alts = list(Path(r"C:\Users\husey").rglob("screenshots"))
    for a in alts[:5]:
        print(f"   Bulundu: {a}")
    exit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# EasyOCR
print("\n🔄 EasyOCR yükleniyor...")
reader = easyocr.Reader(['tr', 'en'], gpu=True, verbose=False)
print("✅ Hazır")

def preprocess_image(img, target_height=None):
    """OCR için görüntü hazırla"""
    w, h = img.size
    
    # Boyut ayarla
    if target_height and h < target_height:
        scale = target_height / h
        img = img.resize((int(w * scale), target_height), Image.Resampling.LANCZOS)
    elif max(w, h) > 2000:
        scale = 2000 / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    
    return img

def extract_answers_from_text(text):
    """Metinden cevapları çıkar"""
    answers = {}
    text_upper = text.upper().replace('\n', ' ')
    
    # Tüm pattern'ler
    patterns = [
        r'(\d{1,3})\s*[.\-:)]\s*([A-E])\b',      # 1.A, 1-A, 1:A, 1)A
        r'(\d{1,3})\s+([A-E])\b',                 # 1 A
        r'(\d{1,3})([A-E])\b',                    # 1A (bitişik)
        r'([A-E])\s*[.\-:)]\s*(\d{1,3})',         # A.1, A-1 (ters)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            # Ters pattern kontrolü
            if re.match(r'[A-E]', match[0]):
                a, q = match
            else:
                q, a = match
            try:
                q_num = int(q)
                if 1 <= q_num <= 200 and a in 'ABCDE':
                    answers[q_num] = a
            except:
                pass
    
    return answers

def crop_bottom_region(img, ratio=0.15):
    """Sayfanın alt bölgesini kırp (cevap şeridi için)"""
    w, h = img.size
    top = int(h * (1 - ratio))
    return img.crop((0, top, w, h))

def crop_top_region(img, ratio=0.10):
    """Sayfanın üst bölgesini kırp (başlık için)"""
    w, h = img.size
    bottom = int(h * ratio)
    return img.crop((0, 0, w, bottom))

def analyze_page_for_answers(img_path, check_regions=['bottom', 'full']):
    """Bir sayfada cevap anahtarı ara"""
    results = {
        'bottom': {'text': '', 'answers': {}},
        'full': {'text': '', 'answers': {}},
        'top': {'text': '', 'answers': {}}
    }
    
    try:
        img = Image.open(img_path)
        img = preprocess_image(img)
        
        # BOTTOM - Sayfa altı (en yaygın konum)
        if 'bottom' in check_regions:
            bottom_crop = crop_bottom_region(img, ratio=0.18)  # Alt %18
            bottom_crop = preprocess_image(bottom_crop, target_height=100)
            
            ocr_result = reader.readtext(np.array(bottom_crop), detail=0)
            text = ' '.join(ocr_result)
            answers = extract_answers_from_text(text)
            
            results['bottom'] = {'text': text[:200], 'answers': answers}
        
        # FULL - Tüm sayfa (kitap sonu cevap sayfaları için)
        if 'full' in check_regions:
            ocr_result = reader.readtext(np.array(img), detail=0)
            text = ' '.join(ocr_result)
            answers = extract_answers_from_text(text)
            
            results['full'] = {'text': text[:500], 'answers': answers}
        
        # TOP - Sayfa üstü (test başlığı için)
        if 'top' in check_regions:
            top_crop = crop_top_region(img, ratio=0.12)
            ocr_result = reader.readtext(np.array(top_crop), detail=0)
            text = ' '.join(ocr_result)
            
            results['top'] = {'text': text[:100], 'answers': {}}
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def detect_answer_location_type(book_path):
    """Kitabın cevap anahtarı tipini belirle"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    if len(pages) < 10:
        return None, {}
    
    stats = {
        'bottom_answers': 0,
        'bottom_pages': 0,
        'end_answers': 0,
        'end_pages': 0,
        'samples': []
    }
    
    # ORTA SAYFALARDAN ÖRNEK (sayfa altı kontrolü)
    mid_start = len(pages) // 3
    mid_pages = pages[mid_start:mid_start+10]
    
    for page in mid_pages:
        result = analyze_page_for_answers(page, check_regions=['bottom'])
        if result['bottom']['answers']:
            stats['bottom_answers'] += len(result['bottom']['answers'])
            stats['bottom_pages'] += 1
            if len(stats['samples']) < 3:
                stats['samples'].append({
                    'type': 'bottom',
                    'page': page.name,
                    'answers': result['bottom']['answers']
                })
    
    # SON 15 SAYFA (kitap sonu kontrolü)
    end_pages = pages[-15:]
    
    for page in end_pages:
        result = analyze_page_for_answers(page, check_regions=['full'])
        if len(result['full']['answers']) >= 5:  # En az 5 cevap
            stats['end_answers'] += len(result['full']['answers'])
            stats['end_pages'] += 1
            if len(stats['samples']) < 6:
                stats['samples'].append({
                    'type': 'end',
                    'page': page.name,
                    'answers': result['full']['answers']
                })
    
    # Tip belirleme
    if stats['bottom_pages'] >= 3 and stats['bottom_answers'] > stats['end_answers']:
        return 'BOTTOM', stats
    elif stats['end_pages'] >= 2:
        return 'END', stats
    elif stats['bottom_pages'] >= 1:
        return 'BOTTOM', stats
    else:
        return 'UNKNOWN', stats

def extract_all_answers(book_path, answer_type):
    """Kitaptaki tüm cevapları çıkar"""
    pages = sorted(book_path.glob("*.png")) + sorted(book_path.glob("*.jpg"))
    pages = sorted(pages, key=lambda x: x.name)
    
    all_answers = {}
    page_answers = {}
    
    if answer_type == 'BOTTOM':
        # Her sayfanın altını tara
        for page in pages:
            result = analyze_page_for_answers(page, check_regions=['bottom'])
            if result['bottom']['answers']:
                page_name = page.stem
                page_answers[page_name] = result['bottom']['answers']
                all_answers.update(result['bottom']['answers'])
    
    elif answer_type == 'END':
        # Son 30 sayfayı tara
        end_pages = pages[-30:]
        for page in end_pages:
            result = analyze_page_for_answers(page, check_regions=['full'])
            if result['full']['answers']:
                page_name = page.stem
                page_answers[page_name] = result['full']['answers']
                all_answers.update(result['full']['answers'])
    
    else:  # UNKNOWN - ikisini de dene
        # Önce bottom
        for page in pages:
            result = analyze_page_for_answers(page, check_regions=['bottom'])
            if result['bottom']['answers']:
                page_name = page.stem
                page_answers[page_name] = result['bottom']['answers']
                all_answers.update(result['bottom']['answers'])
        
        # Sonra end
        end_pages = pages[-30:]
        for page in end_pages:
            result = analyze_page_for_answers(page, check_regions=['full'])
            if result['full']['answers']:
                page_name = page.stem
                if page_name not in page_answers:
                    page_answers[page_name] = {}
                page_answers[page_name].update(result['full']['answers'])
                all_answers.update(result['full']['answers'])
    
    return all_answers, page_answers

# ANA İŞLEM
print("\n" + "=" * 70)
print("ADIM 1: KİTAP ANALİZİ - CEVAP ANAHTARI TİPİ BELİRLEME")
print("=" * 70)

books = sorted([d for d in SOURCE_DIR.iterdir() if d.is_dir()])
print(f"\n📚 Toplam kitap: {len(books)}")

# İlk 10 kitabı analiz et (test için)
test_books = books[:10]

book_results = []

for idx, book in enumerate(test_books):
    print(f"\n[{idx+1}/{len(test_books)}] 📖 {book.name[:50]}...")
    
    # Cevap tipi belirle
    answer_type, stats = detect_answer_location_type(book)
    
    print(f"   📍 Tip: {answer_type}")
    print(f"   📊 Alt: {stats['bottom_pages']} sayfa, {stats['bottom_answers']} cevap")
    print(f"   📊 Son: {stats['end_pages']} sayfa, {stats['end_answers']} cevap")
    
    if stats['samples']:
        print(f"   📝 Örnek: {stats['samples'][0]}")
    
    # Tüm cevapları çıkar
    all_answers, page_answers = extract_all_answers(book, answer_type)
    
    print(f"   ✅ Toplam {len(all_answers)} benzersiz cevap bulundu")
    
    book_results.append({
        'book': book.name,
        'type': answer_type,
        'stats': {
            'bottom_pages': stats['bottom_pages'],
            'bottom_answers': stats['bottom_answers'],
            'end_pages': stats['end_pages'],
            'end_answers': stats['end_answers']
        },
        'total_answers': len(all_answers),
        'answers': {str(k): v for k, v in all_answers.items()},
        'page_answers': {k: {str(kk): vv for kk, vv in v.items()} for k, v in page_answers.items()}
    })

# ÖZET
print("\n" + "=" * 70)
print("ÖZET")
print("=" * 70)

type_counts = defaultdict(int)
total_answers = 0

for r in book_results:
    type_counts[r['type']] += 1
    total_answers += r['total_answers']

print(f"\n📊 CEVAP ANAHTARI TİP DAĞILIMI:")
for t, c in type_counts.items():
    print(f"   {t}: {c} kitap")

print(f"\n📊 TOPLAM CEVAP: {total_answers}")

# Sonuçları kaydet
output_file = OUTPUT_DIR / "answer_extraction_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(book_results, f, ensure_ascii=False, indent=2)

print(f"\n📁 Sonuçlar: {output_file}")

print("\n" + "=" * 70)
print("TAMAMLANDI")
print("=" * 70)
