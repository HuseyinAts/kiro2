#!/usr/bin/env python3
"""
Cevap Anahtarı OCR Pipeline - Gemini API
=========================================
YOLO'nun tespit ettiği "cevaplar" bölgelerini:
1. Crop et
2. Gemini ile OCR yap
3. Cevap pattern'lerini çıkar
4. Sonuçları kaydet
"""

import os
import json
import re
import base64
from pathlib import Path
from PIL import Image
import io
from datetime import datetime
from collections import defaultdict
import time

# Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai yüklü değil: pip install google-generativeai")

# Ayarlar
DETECTIONS_DIR = Path(r"C:\Users\husey\d-dataset\output\detections")
SCREENSHOTS_DIR = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
OUTPUT_DIR = Path(r"C:\Users\husey\d-dataset\output\answer_keys_v2")
CROPS_DIR = Path(r"C:\Users\husey\d-dataset\output\crops\cevaplar_v2")

# Gemini API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step_num, text):
    print(f"\n{'─' * 50}")
    print(f"  ADIM {step_num}: {text}")
    print(f"{'─' * 50}")

# ============================================================================
# ADIM 1: Cevap kutularını crop et
# ============================================================================
def step1_crop_answer_boxes():
    print_step(1, "CEVAP KUTULARINI CROP ET")
    
    CROPS_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "books_processed": 0,
        "total_crops": 0,
        "failed": 0,
        "crop_info": []
    }
    
    for book_dir in sorted(DETECTIONS_DIR.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        screenshot_dir = SCREENSHOTS_DIR / book_name
        
        if not screenshot_dir.exists():
            continue
        
        stats["books_processed"] += 1
        book_crops_dir = CROPS_DIR / book_name
        book_crops_dir.mkdir(parents=True, exist_ok=True)
        
        for json_file in sorted(book_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                
                # Cevap detection'larını bul
                cevap_dets = [d for d in detections if d.get("class_name") == "cevaplar"]
                
                if not cevap_dets:
                    continue
                
                # Screenshot dosyasını bul
                page_num = json_file.stem
                screenshot_file = screenshot_dir / f"{page_num}.png"
                
                if not screenshot_file.exists():
                    continue
                
                # Görseli aç
                img = Image.open(screenshot_file)
                w, h = img.size
                
                for i, det in enumerate(cevap_dets):
                    try:
                        # bbox koordinatları
                        x1 = int(det.get("x1", 0))
                        y1 = int(det.get("y1", 0))
                        x2 = int(det.get("x2", 0))
                        y2 = int(det.get("y2", 0))
                        
                        # Biraz padding ekle
                        padding = 5
                        x1 = max(0, x1 - padding)
                        y1 = max(0, y1 - padding)
                        x2 = min(w, x2 + padding)
                        y2 = min(h, y2 + padding)
                        
                        # Crop
                        cropped = img.crop((x1, y1, x2, y2))
                        
                        # Kaydet
                        crop_filename = f"{page_num}_cevap_{i}.png"
                        crop_path = book_crops_dir / crop_filename
                        cropped.save(crop_path)
                        
                        stats["total_crops"] += 1
                        stats["crop_info"].append({
                            "book": book_name,
                            "page": page_num,
                            "crop_file": str(crop_path),
                            "bbox": [x1, y1, x2, y2],
                            "confidence": det.get("confidence", 0)
                        })
                        
                    except Exception as e:
                        stats["failed"] += 1
                        
            except Exception as e:
                pass
        
        if stats["books_processed"] % 50 == 0:
            print(f"   İşlenen: {stats['books_processed']} kitap, {stats['total_crops']} crop")
    
    print(f"\n📊 ADIM 1 SONUCU:")
    print(f"   İşlenen kitap: {stats['books_processed']}")
    print(f"   Toplam crop: {stats['total_crops']}")
    print(f"   Başarısız: {stats['failed']}")
    
    # Crop info'yu kaydet
    info_file = OUTPUT_DIR / "crop_info.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(stats["crop_info"], f, ensure_ascii=False, indent=2)
    
    return stats

# ============================================================================
# ADIM 2: Gemini ile OCR
# ============================================================================
def step2_ocr_with_gemini(crop_info, max_items=1000):
    print_step(2, "GEMINI ILE OCR")
    
    if not GEMINI_AVAILABLE:
        print("   ❌ Gemini API kullanılamıyor")
        return {}
    
    if not GEMINI_API_KEY:
        print("   ❌ GEMINI_API_KEY environment variable'ı ayarlanmamış")
        print("   Ayarlamak için: set GEMINI_API_KEY=your_api_key")
        return {}
    
    # Gemini'yi yapılandır
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    ocr_results = []
    stats = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "answers_found": 0
    }
    
    # Prompt
    prompt = """Bu görsel bir soru bankasından alınmış cevap anahtarı kutusudur.
Görseldeki tüm soru numarası ve cevap harflerini çıkar.

SADECE JSON formatında yanıt ver, başka hiçbir şey yazma:
{
  "cevaplar": {
    "1": "A",
    "2": "B",
    "3": "C"
  }
}

Eğer cevap anahtarı görünmüyorsa veya okunamıyorsa:
{"cevaplar": {}}
"""
    
    # İşlenecek crop'ları sınırla
    items_to_process = crop_info[:max_items]
    
    for i, info in enumerate(items_to_process):
        try:
            crop_path = Path(info["crop_file"])
            
            if not crop_path.exists():
                stats["failed"] += 1
                continue
            
            # Görseli base64'e çevir
            with open(crop_path, 'rb') as f:
                img_data = f.read()
            
            # Gemini'ye gönder
            img = Image.open(io.BytesIO(img_data))
            
            response = model.generate_content([prompt, img])
            result_text = response.text
            
            # JSON'u parse et
            try:
                # JSON bloğunu çıkar
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    result_json = json.loads(json_match.group())
                    cevaplar = result_json.get("cevaplar", {})
                    
                    if cevaplar:
                        ocr_results.append({
                            "book": info["book"],
                            "page": info["page"],
                            "answers": cevaplar
                        })
                        stats["answers_found"] += len(cevaplar)
                        stats["success"] += 1
                    else:
                        stats["success"] += 1  # Başarılı ama boş
                else:
                    stats["failed"] += 1
                    
            except json.JSONDecodeError:
                stats["failed"] += 1
            
            stats["processed"] += 1
            
            # Progress
            if stats["processed"] % 100 == 0:
                print(f"   İşlenen: {stats['processed']}/{len(items_to_process)}, Bulunan cevap: {stats['answers_found']}")
            
            # Rate limit için bekle
            time.sleep(0.1)
            
        except Exception as e:
            stats["failed"] += 1
            if stats["failed"] % 10 == 0:
                print(f"   ⚠️ Hata: {str(e)[:50]}")
    
    print(f"\n📊 ADIM 2 SONUCU:")
    print(f"   İşlenen: {stats['processed']}")
    print(f"   Başarılı: {stats['success']}")
    print(f"   Başarısız: {stats['failed']}")
    print(f"   Bulunan cevap: {stats['answers_found']}")
    
    # Sonuçları kaydet
    ocr_file = OUTPUT_DIR / "ocr_results.json"
    with open(ocr_file, 'w', encoding='utf-8') as f:
        json.dump(ocr_results, f, ensure_ascii=False, indent=2)
    
    return ocr_results

# ============================================================================
# ADIM 3: Cevapları birleştir ve eşleştir
# ============================================================================
def step3_merge_and_match(ocr_results):
    print_step(3, "CEVAPLARI BİRLEŞTİR VE EŞLEŞTİR")
    
    # Kitap bazında cevapları birleştir
    book_answers = defaultdict(dict)
    
    for result in ocr_results:
        book = result["book"]
        answers = result["answers"]
        
        for q_num, answer in answers.items():
            try:
                q_int = int(q_num)
                book_answers[book][q_int] = answer.upper()
            except:
                pass
    
    # İstatistikler
    stats = {
        "books_with_answers": len(book_answers),
        "total_answers": sum(len(a) for a in book_answers.values())
    }
    
    print(f"\n📊 ADIM 3 SONUCU:")
    print(f"   Cevap bulunan kitap: {stats['books_with_answers']}")
    print(f"   Toplam cevap: {stats['total_answers']}")
    
    # Örnek göster
    print(f"\n   Örnek cevap anahtarları:")
    for book, answers in list(book_answers.items())[:3]:
        sample = dict(list(sorted(answers.items()))[:10])
        print(f"      {book[:40]}: {sample}")
    
    # Kaydet
    answers_file = OUTPUT_DIR / "merged_answers.json"
    with open(answers_file, 'w', encoding='utf-8') as f:
        # dict'i JSON serializable yap
        serializable = {k: dict(v) for k, v in book_answers.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    
    return book_answers, stats

# ============================================================================
# ADIM 4: Final eşleştirme ve veriseti oluştur
# ============================================================================
def step4_create_final_dataset(book_answers):
    print_step(4, "FİNAL VERİSETİNİ OLUŞTUR")
    
    final_stats = {
        "total_questions": 0,
        "matched_questions": 0,
        "books_processed": 0
    }
    
    final_data = {}
    
    for book_dir in sorted(DETECTIONS_DIR.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        answers = book_answers.get(book_name, {})
        
        final_stats["books_processed"] += 1
        
        book_questions = []
        
        for json_file in sorted(book_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    detections = json.load(f)
                
                page_num = json_file.stem
                
                # Soru detection'larını say
                soru_dets = [d for d in detections if d.get("class_name") == "soru"]
                
                for det in soru_dets:
                    final_stats["total_questions"] += 1
                    
                    q_info = {
                        "page": page_num,
                        "bbox": [det.get("x1"), det.get("y1"), det.get("x2"), det.get("y2")],
                        "confidence": det.get("confidence", 0),
                        "answer": None
                    }
                    book_questions.append(q_info)
                    
            except:
                pass
        
        # Eşleştirme - sayfa bazlı soru numarası tahmini
        if answers:
            for i, q in enumerate(book_questions):
                q_num = i + 1
                if q_num in answers:
                    q["answer"] = answers[q_num]
                    final_stats["matched_questions"] += 1
        
        if book_questions:
            final_data[book_name] = {
                "questions": book_questions,
                "answer_key": answers,
                "matched_count": sum(1 for q in book_questions if q["answer"])
            }
    
    # Kaydet
    final_file = OUTPUT_DIR / "final_dataset.json"
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False)
    
    match_rate = final_stats["matched_questions"] / final_stats["total_questions"] * 100 if final_stats["total_questions"] > 0 else 0
    
    print(f"\n📊 ADIM 4 SONUCU:")
    print(f"   İşlenen kitap: {final_stats['books_processed']}")
    print(f"   Toplam soru: {final_stats['total_questions']:,}")
    print(f"   Eşleşen soru: {final_stats['matched_questions']:,}")
    print(f"   Eşleşme oranı: {match_rate:.1f}%")
    
    return final_data, final_stats

# ============================================================================
# ANA FONKSİYON
# ============================================================================
def main():
    print_header("CEVAP ANAHTARI OCR PIPELINE - GEMINI")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Gemini API: {'✅ Hazır' if GEMINI_API_KEY else '❌ API Key yok'}")
    
    # Adım 1: Crop
    crop_stats = step1_crop_answer_boxes()
    
    if not GEMINI_API_KEY:
        print("\n⚠️ GEMINI_API_KEY ayarlanmadığı için OCR atlanıyor.")
        print("   Ayarlamak için: set GEMINI_API_KEY=your_api_key")
        print(f"   Crop'lar kaydedildi: {CROPS_DIR}")
        return
    
    # Adım 2: OCR (ilk 1000 crop ile test)
    ocr_results = step2_ocr_with_gemini(crop_stats["crop_info"], max_items=1000)
    
    # Adım 3: Birleştir
    book_answers, merge_stats = step3_merge_and_match(ocr_results)
    
    # Adım 4: Final
    final_data, final_stats = step4_create_final_dataset(book_answers)
    
    # Özet
    print_header("İŞLEM TAMAMLANDI")
    match_rate = final_stats["matched_questions"] / final_stats["total_questions"] * 100 if final_stats["total_questions"] > 0 else 0
    print(f"""
📊 GENEL ÖZET:
   ✅ Crop edilen: {crop_stats['total_crops']:,}
   ✅ OCR işlenen: {len(ocr_results)}
   ✅ Toplam cevap: {merge_stats['total_answers']:,}
   ✅ Eşleşen soru: {final_stats['matched_questions']:,}
   📈 Eşleşme oranı: {match_rate:.1f}%
   
   Sonuçlar: {OUTPUT_DIR}
    """)

if __name__ == "__main__":
    main()
