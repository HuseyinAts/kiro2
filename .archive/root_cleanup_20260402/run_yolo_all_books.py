"""
KIRO2 - Tum Kitaplar Icin YOLO Detection
==========================================
317 kitabin tum sayfalarinda soru/cevap tespiti yapar.

Kullanim:
    python run_yolo_all_books.py

Cikti:
    d-dataset/output/detections/{kitap_adi}/page_{sayfa}.json
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import torch

# Ultralytics import
try:
    from ultralytics import YOLO
except ImportError:
    print("❌ ultralytics kütüphanesi bulunamadı!")
    print("   Yüklemek için: pip install ultralytics")
    exit(1)

# ==================== YAPILANDIRMA ====================

# Model/dataset yolları (env override)
ROOT_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("KIRO2_YOLO_MODEL_PATH", str(ROOT_DIR / "models" / "yolo11_best.pt")))
SCREENSHOTS_DIR = Path(
    os.getenv("KIRO2_SCREENSHOTS_DIR", str(ROOT_DIR / "veriseti" / "zkitap" / "screenshots"))
)
ALLOWLIST_FILE = Path(
    os.getenv(
        "KIRO2_SCREENSHOTS_ALLOWLIST",
        str(ROOT_DIR / "veriseti" / "zkitap" / "screenshots_allowlist.txt"),
    )
)
OUTPUT_DIR = Path(
    os.getenv(
        "KIRO2_YOLO_DETECTIONS_OUTPUT_DIR",
        str(Path.home() / "d-dataset" / "output" / "detections"),
    )
)

# Minimum güven eşiği
CONFIDENCE_THRESHOLD = 0.25

# Görsel boyutu
IMAGE_SIZE = 640

# Batch size (GPU belleğine göre ayarla)
BATCH_SIZE = 8

# Paralel işlem sayısı
MAX_WORKERS = 4

# Sınıf etiketleri (YOLO eğitimindeki sıraya göre - dataset.yaml'dan)
CLASS_NAMES = {
    0: "soru",
    1: "cevaplar", 
    2: "konu",
    3: "sayfa",
    4: "test_no"
}

# ==================== FONKSİYONLAR ====================

def get_device():
    """GPU varsa kullan, yoksa CPU"""
    if torch.cuda.is_available():
        device = "cuda:0"
        gpu_name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"✅ GPU: {gpu_name} ({vram:.1f} GB)")
    else:
        device = "cpu"
        print("⚠️ GPU bulunamadı, CPU kullanılacak (yavaş olabilir)")
    return device


def load_model(model_path: str, device: str):
    """YOLO modelini yükle"""
    print(f"\n📦 Model yükleniyor: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"❌ Model dosyası bulunamadı: {model_path}")
        print("\n💡 Çözüm:")
        print("   1. Modeli eğitin: python train_yolo_kiro2.py")
        print("   2. Veya hazır modeli indirin")
        exit(1)
    
    model = YOLO(model_path)
    model.to(device)
    print(f"✅ Model yüklendi")
    
    return model


def get_all_books(screenshots_dir: str):
    """Tüm kitap klasörlerini listele"""
    books = []
    allowlist_path = ALLOWLIST_FILE
    if not allowlist_path.exists():
        raise FileNotFoundError(
            f"Allowlist bulunamadı (fail-closed): {allowlist_path}"
        )

    allowlist = {
        line.strip()
        for line in allowlist_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if not allowlist:
        raise RuntimeError(
            f"Allowlist boş (fail-closed): {allowlist_path}"
        )
    print(f"🔒 Allowlist aktif: {len(allowlist)} klasör")
    
    for item in os.listdir(screenshots_dir):
        item_path = os.path.join(screenshots_dir, item)
        if os.path.isdir(item_path):
            if item not in allowlist:
                continue
            # PNG dosyası sayısını kontrol et
            png_files = [f for f in os.listdir(item_path) if f.lower().endswith('.png')]
            if png_files:
                books.append({
                    'name': item,
                    'path': item_path,
                    'page_count': len(png_files)
                })
    
    return sorted(books, key=lambda x: x['name'])


def process_single_image(model, image_path: str, conf_threshold: float = 0.25):
    """Tek bir görseli işle"""
    try:
        results = model.predict(
            source=image_path,
            conf=conf_threshold,
            imgsz=IMAGE_SIZE,
            verbose=False
        )
        
        detections = []
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")
                    
                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": conf,
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    })
        
        return detections
    
    except Exception as e:
        print(f"⚠️ Hata ({image_path}): {e}")
        return []


def process_book(model, book: dict, output_dir: str, conf_threshold: float = 0.25):
    """Bir kitabın tüm sayfalarını işle"""
    book_name = book['name']
    book_path = book['path']
    
    # Çıktı klasörü
    book_output_dir = os.path.join(output_dir, book_name)
    os.makedirs(book_output_dir, exist_ok=True)
    
    # PNG dosyalarını al
    png_files = sorted([f for f in os.listdir(book_path) if f.lower().endswith('.png')])
    
    stats = {
        'total_pages': len(png_files),
        'processed': 0,
        'with_detections': 0,
        'total_detections': 0,
        'by_class': {}
    }
    
    for png_file in png_files:
        image_path = os.path.join(book_path, png_file)
        
        # Detection yap
        detections = process_single_image(model, image_path, conf_threshold)
        
        # JSON olarak kaydet
        page_name = Path(png_file).stem
        output_file = os.path.join(book_output_dir, f"{page_name}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detections, f, ensure_ascii=False, indent=2)
        
        # İstatistik güncelle
        stats['processed'] += 1
        if detections:
            stats['with_detections'] += 1
            stats['total_detections'] += len(detections)
            
            for det in detections:
                cls_name = det['class_name']
                stats['by_class'][cls_name] = stats['by_class'].get(cls_name, 0) + 1
    
    return stats


def main():
    """Ana işlem"""
    start_time = time.time()
    
    print("=" * 80)
    print("🚀 KIRO2 - TÜM KİTAPLAR İÇİN YOLO DETECTION")
    print("=" * 80)
    print(f"⏰ Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # GPU/CPU seç
    device = get_device()
    
    # Model yükle
    model = load_model(MODEL_PATH, device)
    
    # Kitapları listele
    print(f"\n📚 Kitaplar taranıyor: {SCREENSHOTS_DIR}")
    books = get_all_books(SCREENSHOTS_DIR)
    
    if not books:
        print("❌ Hiç kitap bulunamadı!")
        return
    
    total_pages = sum(b['page_count'] for b in books)
    print(f"✅ {len(books)} kitap, toplam {total_pages:,} sayfa bulundu")
    
    # Çıktı klasörü
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n📁 Çıktı klasörü: {OUTPUT_DIR}")
    
    # İşlem başlat
    print(f"\n{'='*80}")
    print("🔄 Detection başlatılıyor...")
    print(f"{'='*80}")
    
    all_stats = {
        'total_books': len(books),
        'total_pages': total_pages,
        'processed_pages': 0,
        'total_detections': 0,
        'by_class': {},
        'books': {}
    }
    
    for i, book in enumerate(books, 1):
        book_start = time.time()
        
        print(f"\n[{i}/{len(books)}] 📖 {book['name']} ({book['page_count']} sayfa)")
        
        # Kitabı işle
        stats = process_book(model, book, OUTPUT_DIR, CONFIDENCE_THRESHOLD)
        
        book_time = time.time() - book_start
        pages_per_sec = stats['processed'] / book_time if book_time > 0 else 0
        
        print(f"   ✅ {stats['processed']} sayfa işlendi ({book_time:.1f}s, {pages_per_sec:.1f} sayfa/s)")
        print(f"   📊 {stats['total_detections']} tespit: {stats['by_class']}")
        
        # Genel istatistik güncelle
        all_stats['processed_pages'] += stats['processed']
        all_stats['total_detections'] += stats['total_detections']
        all_stats['books'][book['name']] = stats
        
        for cls_name, count in stats['by_class'].items():
            all_stats['by_class'][cls_name] = all_stats['by_class'].get(cls_name, 0) + count
        
        # İlerleme tahmini
        elapsed = time.time() - start_time
        progress = all_stats['processed_pages'] / total_pages
        if progress > 0:
            eta = (elapsed / progress) - elapsed
            print(f"   ⏱️ Tahmini kalan süre: {eta/60:.0f} dakika")
    
    # Özet istatistikleri kaydet
    summary_file = os.path.join(OUTPUT_DIR, "detection_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)
    
    # Final rapor
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("✅ TÜM İŞLEMLER TAMAMLANDI!")
    print("=" * 80)
    
    print(f"""
📊 ÖZET:
   • Toplam kitap:     {all_stats['total_books']}
   • Toplam sayfa:     {all_stats['total_pages']:,}
   • İşlenen sayfa:    {all_stats['processed_pages']:,}
   • Toplam tespit:    {all_stats['total_detections']:,}
   
📈 TESPİT DAĞILIMI:
""")
    
    for cls_name, count in sorted(all_stats['by_class'].items(), key=lambda x: x[1], reverse=True):
        print(f"   • {cls_name}: {count:,}")
    
    print(f"""
⏱️ SÜRE:
   • Toplam:           {total_time/60:.1f} dakika
   • Sayfa/saniye:     {all_stats['processed_pages']/total_time:.1f}

📁 ÇIKTI:
   • Klasör:           {OUTPUT_DIR}
   • Özet dosyası:     {summary_file}
""")
    
    print("=" * 80)
    print("🎉 İşlem tamamlandı!")
    print("=" * 80)


if __name__ == "__main__":
    main()
