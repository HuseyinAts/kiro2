#!/usr/bin/env python3
"""
Cevap Anahtarı Eşleştirme Pipeline'ı
=====================================
YOLO detection'lardan cevap anahtarlarını çıkar ve sorularla eşleştir.

Adımlar:
1. Detection'lardan "cevaplar" sınıfını bul
2. Cevap anahtarı görsellerini crop et
3. OCR ile cevap anahtarlarını oku
4. Soru-cevap eşleştirmesi yap
5. Final verisetini oluştur
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from PIL import Image
import sys

# Ayarlar
DETECTIONS_DIR = r"C:\Users\husey\d-dataset\output\detections"
SCREENSHOTS_DIR = r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots"
OUTPUT_DIR = r"C:\Users\husey\d-dataset\output\answer_keys"
CROPS_DIR = r"C:\Users\husey\d-dataset\output\crops\cevaplar"

# Cevap pattern'leri
ANSWER_PATTERNS = [
    # Pattern 1: "1.A 2.B 3.C" veya "1-A 2-B 3-C"
    r'(\d{1,3})[.\-\s]*([A-Ea-e])',
    # Pattern 2: "1)A 2)B 3)C"
    r'(\d{1,3})\s*\)\s*([A-Ea-e])',
    # Pattern 3: Sadece harfler sıralı "A B C D E A B C"
    r'\b([A-Ea-e])\b',
    # Pattern 4: "Cevap: A" veya "Doğru Cevap: B"
    r'[Cc]evap[ı]?\s*[:=]\s*([A-Ea-e])',
]

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step_num, text):
    print(f"\n{'─' * 50}")
    print(f"  ADIM {step_num}: {text}")
    print(f"{'─' * 50}")

# ============================================================================
# ADIM 1: Detection'lardan cevap anahtarlarını bul
# ============================================================================
def step1_find_answer_detections():
    print_step(1, "CEVAP ANAHTARI DETECTION'LARINI BUL")
    
    stats = {
        "books_with_answers": 0,
        "total_answer_detections": 0,
        "books_processed": 0,
        "answer_pages": defaultdict(list)
    }
    
    detections_path = Path(DETECTIONS_DIR)
    
    for book_dir in sorted(detections_path.iterdir()):
        if not book_dir.is_dir():
            continue
        
        stats["books_processed"] += 1
        book_name = book_dir.name
        book_answers = []
        
        for json_file in sorted(book_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                
                for det in detections:
                    if det.get("class_name") == "cevaplar":
                        page_num = json_file.stem.replace("sayfa_", "").replace("page_", "")
                        book_answers.append({
                            "page": page_num,
                            "file": json_file.name,
                            "bbox": det.get("bbox", []),
                            "confidence": det.get("confidence", 0)
                        })
                        stats["total_answer_detections"] += 1
                        
            except Exception as e:
                pass
        
        if book_answers:
            stats["books_with_answers"] += 1
            stats["answer_pages"][book_name] = book_answers
    
    print(f"\n📊 ADIM 1 SONUCU:")
    print(f"   İşlenen kitap: {stats['books_processed']}")
    print(f"   Cevap içeren kitap: {stats['books_with_answers']}")
    print(f"   Toplam cevap detection: {stats['total_answer_detections']}")
    
    # İlk 5 kitabı göster
    print(f"\n   Örnek kitaplar:")
    for i, (book, answers) in enumerate(list(stats["answer_pages"].items())[:5]):
        print(f"      {book[:40]}: {len(answers)} cevap sayfası")
    
    return stats

# ============================================================================
# ADIM 2: Cevap anahtarı görsellerini crop et
# ============================================================================
def step2_crop_answer_images(answer_stats):
    print_step(2, "CEVAP ANAHTARI GÖRSELLERİNİ CROP ET")
    
    # Output dizinini oluştur
    crops_path = Path(CROPS_DIR)
    crops_path.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "cropped": 0,
        "failed": 0,
        "skipped": 0
    }
    
    screenshots_path = Path(SCREENSHOTS_DIR)
    
    for book_name, answers in answer_stats["answer_pages"].items():
        book_screenshots = screenshots_path / book_name
        book_crops = crops_path / book_name
        
        if not book_screenshots.exists():
            stats["skipped"] += len(answers)
            continue
        
        book_crops.mkdir(parents=True, exist_ok=True)
        
        for answer in answers:
            page_num = answer["page"]
            bbox = answer["bbox"]
            
            # Screenshot dosyasını bul
            screenshot_file = book_screenshots / f"sayfa_{page_num}.png"
            if not screenshot_file.exists():
                screenshot_file = book_screenshots / f"page_{page_num}.png"
            
            if not screenshot_file.exists():
                stats["failed"] += 1
                continue
            
            try:
                # Görseli aç ve crop et
                img = Image.open(screenshot_file)
                
                # bbox: [x1, y1, x2, y2] normalized (0-1) veya pixel
                if bbox and len(bbox) == 4:
                    x1, y1, x2, y2 = bbox
                    
                    # Normalized ise pixel'e çevir
                    if all(0 <= v <= 1 for v in bbox):
                        w, h = img.size
                        x1, y1, x2, y2 = int(x1*w), int(y1*h), int(x2*w), int(y2*h)
                    else:
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Crop
                    cropped = img.crop((x1, y1, x2, y2))
                    
                    # Kaydet
                    crop_file = book_crops / f"cevap_{page_num}.png"
                    cropped.save(crop_file)
                    stats["cropped"] += 1
                else:
                    stats["failed"] += 1
                    
            except Exception as e:
                stats["failed"] += 1
    
    print(f"\n📊 ADIM 2 SONUCU:")
    print(f"   Crop edilen: {stats['cropped']}")
    print(f"   Başarısız: {stats['failed']}")
    print(f"   Atlanan: {stats['skipped']}")
    
    return stats

# ============================================================================
# ADIM 3: Mevcut OCR sonuçlarından cevap anahtarlarını çıkar
# ============================================================================
def step3_extract_answers_from_ocr():
    print_step(3, "OCR SONUÇLARINDAN CEVAP ANAHTARLARINI ÇIKAR")
    
    # Mevcut OCR sonuçlarını oku
    ocr_file = Path(r"C:\Users\husey\d-dataset\output\ocr_v3\results.jsonl")
    
    if not ocr_file.exists():
        print("   ⚠️ OCR sonuçları bulunamadı!")
        return {}
    
    answer_keys = defaultdict(dict)
    stats = {
        "pages_with_answers": 0,
        "total_answers_found": 0,
        "books_processed": set()
    }
    
    with open(ocr_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                book = data.get("book", "")
                path = data.get("path", "")
                response = data.get("response", "")
                
                # Sayfa numarasını çıkar
                page_match = re.search(r'sayfa_(\d+)', path)
                if not page_match:
                    continue
                page_num = int(page_match.group(1))
                
                # Cevap anahtarı sayfası mı kontrol et
                if is_answer_key_page(response):
                    answers = extract_answers_from_text(response)
                    
                    if answers:
                        if book not in answer_keys:
                            answer_keys[book] = {}
                        
                        answer_keys[book][page_num] = answers
                        stats["pages_with_answers"] += 1
                        stats["total_answers_found"] += len(answers)
                        stats["books_processed"].add(book)
                        
            except Exception as e:
                pass
    
    print(f"\n📊 ADIM 3 SONUCU:")
    print(f"   Cevap içeren sayfa: {stats['pages_with_answers']}")
    print(f"   Toplam cevap: {stats['total_answers_found']}")
    print(f"   Kitap sayısı: {len(stats['books_processed'])}")
    
    # Örnek göster
    if answer_keys:
        print(f"\n   Örnek cevap anahtarları:")
        for book, pages in list(answer_keys.items())[:3]:
            for page, answers in list(pages.items())[:1]:
                sample = dict(list(answers.items())[:5])
                print(f"      {book[:30]}... sayfa {page}: {sample}")
    
    return answer_keys

def is_answer_key_page(text):
    """Metnin cevap anahtarı sayfası olup olmadığını kontrol et"""
    keywords = [
        "cevap anahtarı", "cevaplar", "doğru cevap", 
        "yanıt anahtarı", "answer key", "answers",
        "1.A", "1-A", "1)A", "1. A"
    ]
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def extract_answers_from_text(text):
    """Metinden cevapları çıkar"""
    answers = {}
    
    # Pattern 1: "1.A 2.B 3.C" formatı
    pattern1 = r'(\d{1,3})[.\-\s:)]*([A-Ea-e])\b'
    matches = re.findall(pattern1, text)
    
    for q_num, answer in matches:
        q_num = int(q_num)
        if 1 <= q_num <= 200:  # Makul soru numarası aralığı
            answers[q_num] = answer.upper()
    
    return answers

# ============================================================================
# ADIM 4: Soru-cevap eşleştirmesi
# ============================================================================
def step4_match_questions_answers(answer_keys):
    print_step(4, "SORU-CEVAP EŞLEŞTİRMESİ")
    
    detections_path = Path(DETECTIONS_DIR)
    
    stats = {
        "total_questions": 0,
        "matched_questions": 0,
        "unmatched_questions": 0,
        "books_with_matches": 0
    }
    
    matched_data = {}
    
    for book_dir in sorted(detections_path.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        book_answers = answer_keys.get(book_name, {})
        
        # Tüm cevapları birleştir
        all_answers = {}
        for page_answers in book_answers.values():
            all_answers.update(page_answers)
        
        book_questions = []
        
        # Soru detection'larını oku
        for json_file in sorted(book_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                
                page_num = json_file.stem.replace("sayfa_", "").replace("page_", "")
                
                for det in detections:
                    if det.get("class_name") == "soru":
                        stats["total_questions"] += 1
                        
                        # Soru numarasını tahmin et (basit yaklaşım)
                        # Gerçek uygulamada OCR ile soru numarası okunmalı
                        q_info = {
                            "book": book_name,
                            "page": page_num,
                            "bbox": det.get("bbox", []),
                            "confidence": det.get("confidence", 0),
                            "answer": None
                        }
                        book_questions.append(q_info)
                        
            except Exception as e:
                pass
        
        # Eşleştirme yap (sayfa bazlı)
        if all_answers and book_questions:
            stats["books_with_matches"] += 1
            
            # Basit eşleştirme: her sayfadaki soru sayısına göre
            for i, q in enumerate(book_questions):
                q_num = i + 1  # Basit sıralı numara
                if q_num in all_answers:
                    q["answer"] = all_answers[q_num]
                    stats["matched_questions"] += 1
                else:
                    stats["unmatched_questions"] += 1
        
        if book_questions:
            matched_data[book_name] = {
                "questions": book_questions,
                "answer_key": all_answers
            }
    
    print(f"\n📊 ADIM 4 SONUCU:")
    print(f"   Toplam soru: {stats['total_questions']}")
    print(f"   Eşleşen soru: {stats['matched_questions']}")
    print(f"   Eşleşmeyen soru: {stats['unmatched_questions']}")
    print(f"   Eşleşme oranı: {stats['matched_questions']/stats['total_questions']*100:.1f}%" if stats['total_questions'] > 0 else "N/A")
    
    return matched_data, stats

# ============================================================================
# ADIM 5: Final verisetini oluştur
# ============================================================================
def step5_create_final_dataset(matched_data, stats):
    print_step(5, "FİNAL VERİSETİNİ OLUŞTUR")
    
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Ana veri dosyası
    final_data = {
        "generated_at": datetime.now().isoformat(),
        "statistics": {
            "total_books": len(matched_data),
            "total_questions": stats["total_questions"],
            "matched_questions": stats["matched_questions"],
            "match_rate": stats["matched_questions"]/stats["total_questions"]*100 if stats["total_questions"] > 0 else 0
        },
        "books": {}
    }
    
    # Her kitap için özet
    for book_name, data in matched_data.items():
        questions = data["questions"]
        answer_key = data["answer_key"]
        
        matched = sum(1 for q in questions if q["answer"])
        
        final_data["books"][book_name] = {
            "total_questions": len(questions),
            "matched_questions": matched,
            "answer_key_size": len(answer_key),
            "match_rate": matched/len(questions)*100 if questions else 0
        }
    
    # Kaydet
    output_file = output_path / "answer_key_matching_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # Detaylı veri
    detailed_file = output_path / "detailed_question_answers.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(matched_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 ADIM 5 SONUCU:")
    print(f"   Kaydedilen dosyalar:")
    print(f"      {output_file}")
    print(f"      {detailed_file}")
    
    # En iyi eşleşme oranına sahip kitaplar
    print(f"\n   En yüksek eşleşme oranı:")
    sorted_books = sorted(
        final_data["books"].items(),
        key=lambda x: x[1]["match_rate"],
        reverse=True
    )
    for book, info in sorted_books[:5]:
        print(f"      {book[:40]}: {info['match_rate']:.1f}% ({info['matched_questions']}/{info['total_questions']})")
    
    return final_data

# ============================================================================
# ANA FONKSİYON
# ============================================================================
def main():
    print_header("CEVAP ANAHTARI EŞLEŞTİRME PIPELINE")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Adım 1: Detection'lardan cevap bul
    answer_stats = step1_find_answer_detections()
    
    # Adım 2: Crop işlemi (opsiyonel - OCR için)
    # crop_stats = step2_crop_answer_images(answer_stats)
    
    # Adım 3: OCR'dan cevap çıkar
    answer_keys = step3_extract_answers_from_ocr()
    
    # Adım 4: Soru-cevap eşleştir
    matched_data, match_stats = step4_match_questions_answers(answer_keys)
    
    # Adım 5: Final veriseti
    final_data = step5_create_final_dataset(matched_data, match_stats)
    
    # Özet
    print_header("İŞLEM TAMAMLANDI")
    print(f"""
📊 GENEL ÖZET:
   ✅ Cevap detection: {answer_stats['total_answer_detections']}
   ✅ Cevap anahtarı olan kitap: {len(answer_keys)}
   ✅ Toplam soru: {match_stats['total_questions']:,}
   ✅ Eşleşen soru: {match_stats['matched_questions']:,}
   📈 Eşleşme oranı: {final_data['statistics']['match_rate']:.1f}%
   
   Sonuçlar: {OUTPUT_DIR}
    """)

if __name__ == "__main__":
    main()
