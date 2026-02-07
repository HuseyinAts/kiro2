#!/usr/bin/env python3
"""
YOLO Detection Temizlik ve Standardizasyon Script'i
===================================================
1. Duplikeleri temizle (page_ veya sayfa_ birini sil)
2. Bos kitaplari kontrol et
3. Sinif isimlerini standardize et
4. Summary'i yeniden hesapla
"""

import os
import json
import shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Ayarlar
DETECTIONS_DIR = r"C:\Users\husey\d-dataset\output\detections"
BACKUP_DIR = r"C:\Users\husey\d-dataset\output\detections_backup"
SCREENSHOTS_DIR = r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots"

# Sinif standardizasyonu
CLASS_MAPPING = {
    "zorluk_seviyesi": "test_no",  # zorluk_seviyesi -> test_no olarak standardize
    "class_5": "test_no"  # class_5 de test_no olsun
}

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step_num, text):
    print(f"\n{'─' * 50}")
    print(f"  ADIM {step_num}: {text}")
    print(f"{'─' * 50}")

# ============================================================================
# ADIM 1: DUPLIKELERI TEMIZLE
# ============================================================================
def step1_cleanup_duplicates():
    print_step(1, "DUPLIKELERI TEMIZLE")
    
    stats = {
        "books_with_duplicates": 0,
        "page_files_deleted": 0,
        "sayfa_files_kept": 0,
        "books_processed": 0
    }
    
    detections_path = Path(DETECTIONS_DIR)
    
    for book_dir in detections_path.iterdir():
        if not book_dir.is_dir():
            continue
        
        stats["books_processed"] += 1
        
        # page_ ve sayfa_ dosyalarini say
        page_files = list(book_dir.glob("page_*.json"))
        sayfa_files = list(book_dir.glob("sayfa_*.json"))
        
        if page_files and sayfa_files:
            # Duplike var!
            stats["books_with_duplicates"] += 1
            print(f"  📁 {book_dir.name}")
            print(f"     page_: {len(page_files)} | sayfa_: {len(sayfa_files)}")
            
            # page_ dosyalarini sil, sayfa_ tut
            for pf in page_files:
                pf.unlink()
                stats["page_files_deleted"] += 1
            
            stats["sayfa_files_kept"] += len(sayfa_files)
            print(f"     ✅ {len(page_files)} page_*.json silindi")
    
    print(f"\n📊 ADIM 1 SONUCU:")
    print(f"   Islenen kitap: {stats['books_processed']}")
    print(f"   Duplike kitap: {stats['books_with_duplicates']}")
    print(f"   Silinen page_ dosyasi: {stats['page_files_deleted']}")
    
    return stats

# ============================================================================
# ADIM 2: BOS KITAPLARI KONTROL ET
# ============================================================================
def step2_check_empty_books():
    print_step(2, "BOS KITAPLARI KONTROL ET")
    
    empty_books = []
    low_detection_books = []
    
    detections_path = Path(DETECTIONS_DIR)
    screenshots_path = Path(SCREENSHOTS_DIR)
    
    for book_dir in detections_path.iterdir():
        if not book_dir.is_dir():
            continue
        
        # Tum JSON dosyalarini oku
        total_detections = 0
        json_files = list(book_dir.glob("*.json"))
        
        for jf in json_files:
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_detections += len(data)
            except:
                pass
        
        page_count = len(json_files)
        
        if total_detections == 0 and page_count > 0:
            # Screenshot dizinini kontrol et
            screenshot_dir = screenshots_path / book_dir.name
            screenshot_exists = screenshot_dir.exists()
            screenshot_count = len(list(screenshot_dir.glob("*.png"))) if screenshot_exists else 0
            
            empty_books.append({
                "name": book_dir.name,
                "json_count": page_count,
                "screenshot_exists": screenshot_exists,
                "screenshot_count": screenshot_count
            })
        elif page_count > 50 and total_detections / page_count < 1:
            low_detection_books.append({
                "name": book_dir.name,
                "pages": page_count,
                "detections": total_detections,
                "ratio": total_detections / page_count
            })
    
    print(f"\n⚠️ BOS KITAPLAR ({len(empty_books)} adet):")
    for book in empty_books:
        status = "✅" if book["screenshot_exists"] else "❌"
        print(f"   {status} {book['name']}")
        print(f"      JSON: {book['json_count']} | Screenshot: {book['screenshot_count']}")
    
    print(f"\n📉 DUSUK TESPIT ORANLI KITAPLAR ({len(low_detection_books)} adet):")
    for book in sorted(low_detection_books, key=lambda x: x['ratio'])[:5]:
        print(f"   📉 {book['name'][:50]}")
        print(f"      {book['pages']} sayfa | {book['detections']} tespit | {book['ratio']:.2f}/sayfa")
    
    return {"empty": empty_books, "low": low_detection_books}

# ============================================================================
# ADIM 3: SINIF ISIMLERINI STANDARDIZE ET
# ============================================================================
def step3_standardize_classes():
    print_step(3, "SINIF ISIMLERINI STANDARDIZE ET")
    
    stats = {
        "files_updated": 0,
        "detections_updated": 0,
        "class_changes": defaultdict(int)
    }
    
    detections_path = Path(DETECTIONS_DIR)
    
    for book_dir in detections_path.iterdir():
        if not book_dir.is_dir():
            continue
        
        for json_file in book_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not data:
                    continue
                
                modified = False
                for detection in data:
                    old_class = detection.get("class_name", "")
                    if old_class in CLASS_MAPPING:
                        new_class = CLASS_MAPPING[old_class]
                        detection["class_name"] = new_class
                        stats["class_changes"][f"{old_class} -> {new_class}"] += 1
                        stats["detections_updated"] += 1
                        modified = True
                
                if modified:
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False)
                    stats["files_updated"] += 1
                    
            except Exception as e:
                pass
    
    print(f"\n📊 ADIM 3 SONUCU:")
    print(f"   Guncellenen dosya: {stats['files_updated']}")
    print(f"   Guncellenen tespit: {stats['detections_updated']}")
    print(f"\n   Sinif degisiklikleri:")
    for change, count in stats["class_changes"].items():
        print(f"      {change}: {count}")
    
    return stats

# ============================================================================
# ADIM 4: SUMMARY'I YENIDEN HESAPLA
# ============================================================================
def step4_recalculate_summary():
    print_step(4, "SUMMARY'I YENIDEN HESAPLA")
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_books": 0,
        "total_pages": 0,
        "processed_pages": 0,
        "total_detections": 0,
        "by_class": defaultdict(int),
        "books": {}
    }
    
    detections_path = Path(DETECTIONS_DIR)
    
    for book_dir in sorted(detections_path.iterdir()):
        if not book_dir.is_dir():
            continue
        
        book_name = book_dir.name
        book_stats = {
            "total_pages": 0,
            "processed": 0,
            "total_detections": 0,
            "by_class": defaultdict(int)
        }
        
        for json_file in book_dir.glob("*.json"):
            book_stats["total_pages"] += 1
            book_stats["processed"] += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for detection in data:
                    class_name = detection.get("class_name", "unknown")
                    book_stats["total_detections"] += 1
                    book_stats["by_class"][class_name] += 1
                    summary["by_class"][class_name] += 1
                    
            except:
                pass
        
        # Book stats to regular dict
        book_stats["by_class"] = dict(book_stats["by_class"])
        
        summary["books"][book_name] = book_stats
        summary["total_books"] += 1
        summary["total_pages"] += book_stats["total_pages"]
        summary["processed_pages"] += book_stats["processed"]
        summary["total_detections"] += book_stats["total_detections"]
    
    # Convert defaultdict to dict
    summary["by_class"] = dict(summary["by_class"])
    
    # Save summary
    summary_path = detections_path / "detection_summary.json"
    
    # Backup old summary
    if summary_path.exists():
        backup_path = detections_path / "detection_summary_backup.json"
        shutil.copy(summary_path, backup_path)
        print(f"   ✅ Eski summary yedeklendi: detection_summary_backup.json")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 ADIM 4 SONUCU - YENI SUMMARY:")
    print(f"   Toplam Kitap: {summary['total_books']}")
    print(f"   Toplam Sayfa: {summary['total_pages']:,}")
    print(f"   Toplam Tespit: {summary['total_detections']:,}")
    print(f"\n   Sinif Dagilimi:")
    for cls, count in sorted(summary["by_class"].items(), key=lambda x: -x[1]):
        pct = count / summary["total_detections"] * 100 if summary["total_detections"] > 0 else 0
        print(f"      {cls:15} : {count:>8,} ({pct:5.1f}%)")
    
    return summary

# ============================================================================
# ANA FONKSIYON
# ============================================================================
def main():
    print_header("YOLO DETECTION TEMIZLIK VE STANDARDIZASYON")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dizin: {DETECTIONS_DIR}")
    
    # Adim 1
    step1_stats = step1_cleanup_duplicates()
    
    # Adim 2
    step2_stats = step2_check_empty_books()
    
    # Adim 3
    step3_stats = step3_standardize_classes()
    
    # Adim 4
    step4_summary = step4_recalculate_summary()
    
    # Final ozet
    print_header("ISLEM TAMAMLANDI")
    print(f"""
📊 OZET:
   ✅ Duplike temizligi: {step1_stats['page_files_deleted']} dosya silindi
   ⚠️ Bos kitaplar: {len(step2_stats['empty'])} adet
   ✅ Sinif standardizasyonu: {step3_stats['detections_updated']} tespit guncellendi
   ✅ Summary yeniden hesaplandi: {step4_summary['total_detections']:,} tespit
    """)

if __name__ == "__main__":
    main()
