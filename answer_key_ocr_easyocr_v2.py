#!/usr/bin/env python3
"""
Cevap Anahtarı OCR Pipeline - EasyOCR v2 (Encoding Fix)
========================================================
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️ EasyOCR yüklü değil: pip install easyocr")

# PIL for image loading (more robust)
from PIL import Image
import numpy as np

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
        for i, letter in enumerate(letters[:50], 1):
            answers[i] = letter
    
    return answers

def load_image_safe(path):
    """Güvenli image loading - PIL kullan"""
    try:
        img = Image.open(path)
        return np.array(img)
    except Exception as e:
        return None

# ============================================================================
# ADIM 1: EasyOCR ile tüm crop'ları işle
# ============================================================================
def step1_ocr_with_easyocr():
    print_step(1, "EASYOCR ILE OCR")
    
    if not EASYOCR_AVAILABLE:
        print("   ❌ EasyOCR yüklü değil!")
        return {}, {}
    
    # EasyOCR başlat
    print("   🔄 EasyOCR modeli yükleniyor (GPU)...")
    reader = easyocr.Reader(['tr', 'en'], gpu=True)
    print("   ✅ Model yüklendi")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sonuçlar
    all_results = []
    book_answers = defaultdict(dict)
    
    stats = {
        "books_processed": 0,
        "crops_processed": 0,
        "crops_failed": 0,
        "answers_found": 0
    }
    
    # Her kitap için - os.listdir kullan (encoding sorununu aşmak için)
    try:
        book_names = os.listdir(str(CROPS_DIR))
    except Exception as e:
        print(f"   ❌ Dizin okunamadı: {e}")
        return {}, stats
    
    total_books = len(book_names)
    print(f"   📚 Toplam kitap: {total_books}")
    
    for book_idx, book_name in enumerate(sorted(book_names)):
        book_path = CROPS_DIR / book_name
        
        if not book_path.is_dir():
            continue
        
        # PNG dosyalarını bul
        try:
            png_files = [f for f in os.listdir(str(book_path)) if f.endswith('.png')]
        except Exception as e:
            print(f"   ⚠️ {book_name}: dizin okunamadı")
            continue
        
        if not png_files:
            continue
        
        stats["books_processed"] += 1
        book_answer_count = 0
        
        for png_file in sorted(png_files):
            crop_path = book_path / png_file
            
            try:
                # PIL ile yükle
                img = load_image_safe(str(crop_path))
                if img is None:
                    stats["crops_failed"] += 1
                    continue
                
                # OCR yap (numpy array olarak)
                result = reader.readtext(img, detail=0)
                text = ' '.join(result)
                
                # Cevapları çıkar
                answers = extract_answers_from_text(text)
                
                if answers:
                    page_match = re.search(r'sayfa_(\d+)', png_file)
                    page_num = page_match.group(1) if page_match else "unknown"
                    
                    all_results.append({
                        "book": book_name,
                        "page": page_num,
                        "file": png_file,
                        "raw_text": text,
                        "answers": answers
                    })
                    
                    for q_num, answer in answers.items():
                        book_answers[book_name][q_num] = answer
                    
                    stats["answers_found"] += len(answers)
                    book_answer_count += len(answers)
                
                stats["crops_processed"] += 1
                
            except Exception as e:
                stats["crops_failed"] += 1
        
        # Progress
        if (book_idx + 1) % 20 == 0 or book_idx == total_books - 1:
            print(f"   [{book_idx+1}/{total_books}] {book_name[:35]}... +{book_answer_count} cevap")
    
    print(f"\n📊 ADIM 1 SONUCU:")
    print(f"   İşlenen kitap: {stats['books_processed']}")
    print(f"   İşlenen crop: {stats['crops_processed']}")
    print(f"   Başarısız: {stats['crops_failed']}")
    print(f"   Bulunan cevap: {stats['answers_found']}")
    
    # Sonuçları kaydet
    results_file = OUTPUT_DIR / "easyocr_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    answers_file = OUTPUT_DIR / "book_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        serializable = {k: {str(kk): vv for kk, vv in v.items()} for k, v in book_answers.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 Kaydedildi: {results_file}")
    
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
    
    # Detection kitaplarını listele
    try:
        det_books = os.listdir(str(DETECTIONS_DIR))
    except:
        print("   ❌ Detection dizini okunamadı")
        return final_stats
    
    for book_name in det_books:
        book_path = DETECTIONS_DIR / book_name
        if not book_path.is_dir():
            continue
        
        # Soru sayısını hesapla
        question_count = 0
        
        try:
            json_files = [f for f in os.listdir(str(book_path)) if f.endswith('.json')]
        except:
            continue
        
        for json_file in json_files:
            try:
                with open(book_path / json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                soru_dets = [d for d in detections if d.get("class_name") == "soru"]
                question_count += len(soru_dets)
            except:
                pass
        
        final_stats["total_questions"] += question_count
        
        # Cevap anahtarını bul (isim benzerliği ile)
        answers = book_answers.get(book_name, {})
        
        # Eğer direkt eşleşme yoksa, benzer isim ara
        if not answers:
            for ans_book in book_answers.keys():
                # Basit benzerlik: ilk 20 karakter aynı mı?
                if book_name[:20].lower() == ans_book[:20].lower():
                    answers = book_answers[ans_book]
                    break
        
        if answers:
            matched_count = min(len(answers), question_count)
            final_stats["matched_questions"] += matched_count
            final_stats["books_with_matches"] += 1
        else:
            matched_count = 0
        
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
    print(f"\n   🏆 En yüksek eşleşme:")
    sorted_books = sorted(final_data.items(), key=lambda x: x[1]["matched"], reverse=True)
    for book, info in sorted_books[:10]:
        if info["matched"] > 0:
            print(f"      {book[:40]}: {info['matched']} soru")
    
    return final_stats

# ============================================================================
# ANA FONKSİYON
# ============================================================================
def main():
    print_header("CEVAP ANAHTARI OCR - EASYOCR v2")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Crop dizini: {CROPS_DIR}")
    
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
   ✅ Başarısız: {ocr_stats['crops_failed']:,}
   ✅ Bulunan cevap: {ocr_stats['answers_found']:,}
   ✅ Toplam soru: {match_stats['total_questions']:,}
   ✅ Eşleşen soru: {match_stats['matched_questions']:,}
   📈 Eşleşme oranı: {match_rate:.1f}%
   
   Sonuçlar: {OUTPUT_DIR}
    """)

if __name__ == "__main__":
    main()
