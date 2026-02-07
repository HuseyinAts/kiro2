#!/usr/bin/env python3
"""
Cevap Anahtarı OCR Pipeline - EasyOCR (Ücretsiz, Yerel)
========================================================
41,529 cevap kutusunu EasyOCR ile işle
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import time

# EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️ EasyOCR yüklü değil: pip install easyocr")

# Ayarlar
CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v2")
DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step_num, text):
    print(f"\n{'─' * 50}")
    print(f"  ADIM {step_num}: {text}")
    print(f"{'─' * 50}")

def extract_answers_from_text(text):
    """OCR metninden soru-cevap çiftlerini çıkar"""
    answers = {}
    
    # Metni temizle
    text = text.upper().replace('\n', ' ').replace('  ', ' ')
    
    # Pattern 1: "1.A" veya "1-A" veya "1 A" veya "1:A"
    pattern1 = r'(\d{1,3})\s*[.\-:\s)]\s*([A-E])\b'
    matches = re.findall(pattern1, text)
    
    for q_num, answer in matches:
        q_num = int(q_num)
        if 1 <= q_num <= 200:
            answers[q_num] = answer
    
    # Pattern 2: Sadece ardışık harfler (1'den başlayarak)
    if not answers:
        pattern2 = r'\b([A-E])\b'
        letters = re.findall(pattern2, text)
        for i, letter in enumerate(letters[:50], 1):  # Max 50
            answers[i] = letter
    
    return answers

# ============================================================================
# ADIM 1: EasyOCR ile tüm crop'ları işle
# ============================================================================
def step1_ocr_with_easyocr():
    print_step(1, "EASYOCR ILE OCR")
    
    if not EASYOCR_AVAILABLE:
        print("   ❌ EasyOCR yüklü değil!")
        print("   Yüklemek için: pip install easyocr")
        return {}
    
    # EasyOCR başlat (GPU varsa kullan)
    print("   🔄 EasyOCR modeli yükleniyor...")
    reader = easyocr.Reader(['tr', 'en'], gpu=True)
    print("   ✅ Model yüklendi")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sonuçlar
    all_results = []
    book_answers = defaultdict(dict)
    
    stats = {
        "books_processed": 0,
        "crops_processed": 0,
        "answers_found": 0,
        "failed": 0
    }
    
    # Her kitap için
    book_dirs = sorted([d for d in CROPS_DIR.iterdir() if d.is_dir()])
    total_books = len(book_dirs)
    
    for book_idx, book_dir in enumerate(book_dirs):
        book_name = book_dir.name
        crop_files = sorted(book_dir.glob("*.png"))
        
        if not crop_files:
            continue
        
        stats["books_processed"] += 1
        book_answer_count = 0
        
        for crop_file in crop_files:
            try:
                # OCR yap
                result = reader.readtext(str(crop_file), detail=0)
                text = ' '.join(result)
                
                # Cevapları çıkar
                answers = extract_answers_from_text(text)
                
                if answers:
                    # Sayfa numarasını çıkar
                    page_match = re.search(r'sayfa_(\d+)', crop_file.stem)
                    page_num = page_match.group(1) if page_match else "unknown"
                    
                    all_results.append({
                        "book": book_name,
                        "page": page_num,
                        "file": crop_file.name,
                        "raw_text": text,
                        "answers": answers
                    })
                    
                    # Kitap cevaplarına ekle
                    for q_num, answer in answers.items():
                        book_answers[book_name][q_num] = answer
                    
                    stats["answers_found"] += len(answers)
                    book_answer_count += len(answers)
                
                stats["crops_processed"] += 1
                
            except Exception as e:
                stats["failed"] += 1
        
        # Progress
        if (book_idx + 1) % 20 == 0 or book_idx == total_books - 1:
            print(f"   [{book_idx+1}/{total_books}] {book_name[:30]}... +{book_answer_count} cevap")
    
    print(f"\n📊 ADIM 1 SONUCU:")
    print(f"   İşlenen kitap: {stats['books_processed']}")
    print(f"   İşlenen crop: {stats['crops_processed']}")
    print(f"   Bulunan cevap: {stats['answers_found']}")
    print(f"   Başarısız: {stats['failed']}")
    
    # Sonuçları kaydet
    results_file = OUTPUT_DIR / "easyocr_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    answers_file = OUTPUT_DIR / "book_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        serializable = {k: {str(kk): vv for kk, vv in v.items()} for k, v in book_answers.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    return book_answers, stats

# ============================================================================
# ADIM 2: Soru-cevap eşleştirmesi
# ============================================================================
def step2_match_questions(book_answers):
    print_step(2, "SORU-CEVAP EŞLEŞTİRMESİ")
    
    final_stats = {
        "total_questions": 0,
        "matched_questions": 0,
        "books_with_matches": 0
    }
    
    final_data = {}
    
    for book_dir in sorted(DETECTIONS_DIR.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        answers = book_answers.get(book_name, {})
        
        # Soru sayısını hesapla
        question_count = 0
        matched_count = 0
        
        for json_file in book_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                
                soru_dets = [d for d in detections if d.get("class_name") == "soru"]
                question_count += len(soru_dets)
                
            except:
                pass
        
        final_stats["total_questions"] += question_count
        
        if answers:
            # Basit eşleştirme: cevap anahtarındaki soru sayısı kadar eşleşme
            matched_count = min(len(answers), question_count)
            final_stats["matched_questions"] += matched_count
            final_stats["books_with_matches"] += 1
        
        final_data[book_name] = {
            "total_questions": question_count,
            "answer_key_size": len(answers),
            "matched": matched_count,
            "match_rate": matched_count / question_count * 100 if question_count > 0 else 0
        }
    
    # Kaydet
    final_file = OUTPUT_DIR / "matching_results.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    match_rate = final_stats["matched_questions"] / final_stats["total_questions"] * 100 if final_stats["total_questions"] > 0 else 0
    
    print(f"\n📊 ADIM 2 SONUCU:")
    print(f"   Toplam soru: {final_stats['total_questions']:,}")
    print(f"   Eşleşen soru: {final_stats['matched_questions']:,}")
    print(f"   Cevap bulunan kitap: {final_stats['books_with_matches']}")
    print(f"   Eşleşme oranı: {match_rate:.1f}%")
    
    # En iyi kitaplar
    print(f"\n   En yüksek eşleşme oranı:")
    sorted_books = sorted(final_data.items(), key=lambda x: x[1]["match_rate"], reverse=True)
    for book, info in sorted_books[:10]:
        if info["matched"] > 0:
            print(f"      {book[:40]}: {info['match_rate']:.1f}% ({info['matched']}/{info['total_questions']})")
    
    return final_stats

# ============================================================================
# ANA FONKSİYON
# ============================================================================
def main():
    print_header("CEVAP ANAHTARI OCR - EASYOCR (ÜCRETSİZ)")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Crop dizini: {CROPS_DIR}")
    print(f"Toplam kitap: {len(list(CROPS_DIR.iterdir()))}")
    
    # Adım 1: OCR
    book_answers, ocr_stats = step1_ocr_with_easyocr()
    
    if not book_answers:
        print("\n❌ Cevap bulunamadı!")
        return
    
    # Adım 2: Eşleştirme
    match_stats = step2_match_questions(book_answers)
    
    # Özet
    print_header("İŞLEM TAMAMLANDI")
    match_rate = match_stats["matched_questions"] / match_stats["total_questions"] * 100 if match_stats["total_questions"] > 0 else 0
    print(f"""
📊 GENEL ÖZET:
   ✅ İşlenen crop: {ocr_stats['crops_processed']:,}
   ✅ Bulunan cevap: {ocr_stats['answers_found']:,}
   ✅ Toplam soru: {match_stats['total_questions']:,}
   ✅ Eşleşen soru: {match_stats['matched_questions']:,}
   📈 Eşleşme oranı: {match_rate:.1f}%
   
   Sonuçlar: {OUTPUT_DIR}
    """)

if __name__ == "__main__":
    main()
