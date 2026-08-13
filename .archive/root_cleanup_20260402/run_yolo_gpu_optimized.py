"""
KIRO2 - RTX 3080 Optimized YOLO Detection
==========================================
GPU batch processing ile maksimum performans.
Tahmini: 82,980 sayfa / ~50 sayfa/sn = ~28 dakika
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
import torch
import gc

# Ultralytics import
from ultralytics import YOLO

# ==================== RTX 3080 OPTİMİZASYONLARI ====================

# CUDA optimizasyonları
torch.backends.cudnn.benchmark = True  # Otomatik en iyi algoritma seçimi
torch.backends.cudnn.deterministic = False  # Performans için
torch.backends.cuda.matmul.allow_tf32 = True  # TensorFloat-32 kullan
torch.backends.cudnn.allow_tf32 = True

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

# RTX 3080 için optimize edilmiş ayarlar
CONFIDENCE_THRESHOLD = 0.25
IMAGE_SIZE = 640
BATCH_SIZE = 32  # RTX 3080 8GB VRAM için optimal
MAX_BATCH_SIZE = 64  # Küçük görseller için artırılabilir

# Sınıf etiketleri
CLASS_NAMES = {
    0: "soru",
    1: "cevaplar",
    2: "konu",
    3: "sayfa",
    4: "test_no"
}

# ==================== FONKSİYONLAR ====================

def setup_gpu():
    """GPU optimizasyonlarını ayarla"""
    if not torch.cuda.is_available():
        print("❌ CUDA bulunamadı!")
        return "cpu"

    device = torch.device("cuda:0")
    gpu_name = torch.cuda.get_device_name(0)
    vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3

    # VRAM temizle
    torch.cuda.empty_cache()
    gc.collect()

    print(f"✅ GPU: {gpu_name}")
    print(f"   VRAM: {vram_total:.1f} GB")
    print(f"   CUDA: {torch.version.cuda}")
    print(f"   cuDNN: {torch.backends.cudnn.version()}")
    print(f"   TF32: Enabled")
    print(f"   cuDNN Benchmark: Enabled")

    return device


def load_model(model_path, device):
    """Model yükle ve GPU'ya taşı"""
    print(f"\n📦 Model yükleniyor: {model_path}")

    model = YOLO(model_path)
    model.to(device)

    # Warmup - GPU'yu ısıt
    print("🔥 GPU warmup...")
    dummy = torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE).to(device)
    for _ in range(3):
        model.predict(dummy, verbose=False)
    del dummy
    torch.cuda.empty_cache()

    print("✅ Model hazır")
    return model


def get_all_books(screenshots_dir):
    """Tüm kitapları listele"""
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
            png_files = sorted([f for f in os.listdir(item_path) if f.lower().endswith('.png')])
            if png_files:
                books.append({
                    'name': item,
                    'path': item_path,
                    'pages': png_files,
                    'page_count': len(png_files)
                })
    return sorted(books, key=lambda x: x['name'])


def process_batch(model, image_paths, conf_threshold=0.25):
    """Batch olarak görselleri işle - GPU'da paralel"""
    try:
        # Batch prediction - çok daha hızlı!
        results = model.predict(
            source=image_paths,
            conf=conf_threshold,
            imgsz=IMAGE_SIZE,
            verbose=False,
            stream=False,  # Tüm sonuçları bir kerede al
            device=0,
            half=True,  # FP16 - 2x hız artışı
            batch=len(image_paths)
        )

        all_detections = []

        for result in results:
            detections = []
            if result.boxes is not None and len(result.boxes) > 0:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = CLASS_NAMES.get(cls_id, f"class_{cls_id}")

                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": round(conf, 4),
                        "x1": int(x1),
                        "y1": int(y1),
                        "x2": int(x2),
                        "y2": int(y2)
                    })
            all_detections.append(detections)

        return all_detections

    except Exception as e:
        print(f"⚠️ Batch hata: {e}")
        return [[] for _ in image_paths]


def process_book_gpu_batch(model, book, output_dir, batch_size=BATCH_SIZE):
    """Kitabı GPU batch processing ile işle"""
    book_name = book['name']
    book_path = book['path']
    pages = book['pages']

    # Çıktı klasörü
    book_output_dir = os.path.join(output_dir, book_name)
    os.makedirs(book_output_dir, exist_ok=True)

    stats = {
        'total_pages': len(pages),
        'processed': 0,
        'total_detections': 0,
        'by_class': {}
    }

    # Batch'ler halinde işle
    for i in range(0, len(pages), batch_size):
        batch_pages = pages[i:i + batch_size]
        batch_paths = [os.path.join(book_path, p) for p in batch_pages]

        # GPU batch processing
        batch_detections = process_batch(model, batch_paths)

        # Sonuçları kaydet
        for page_name, detections in zip(batch_pages, batch_detections):
            output_file = os.path.join(book_output_dir, f"{Path(page_name).stem}.json")

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(detections, f, ensure_ascii=False)

            stats['processed'] += 1
            stats['total_detections'] += len(detections)

            for det in detections:
                cls_name = det['class_name']
                stats['by_class'][cls_name] = stats['by_class'].get(cls_name, 0) + 1

    return stats


def main():
    """Ana işlem - RTX 3080 optimized"""
    start_time = time.time()

    print("=" * 80)
    print("🚀 KIRO2 - RTX 3080 OPTİMİZE YOLO DETECTION")
    print("=" * 80)
    print(f"⏰ Başlangıç: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # GPU setup
    device = setup_gpu()

    # Model yükle
    model = load_model(MODEL_PATH, device)

    # Kitapları listele
    print(f"\n📚 Kitaplar taranıyor...")
    books = get_all_books(SCREENSHOTS_DIR)

    if not books:
        print("❌ Kitap bulunamadı!")
        return

    total_pages = sum(b['page_count'] for b in books)
    print(f"✅ {len(books)} kitap, {total_pages:,} sayfa")
    print(f"📁 Çıktı: {OUTPUT_DIR}")
    print(f"⚡ Batch size: {BATCH_SIZE}")
    print(f"🎯 FP16 (Half precision): Enabled")

    # Çıktı klasörü
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n{'='*80}")
    print("🔄 Detection başlatılıyor...")
    print(f"{'='*80}\n")

    # İstatistikler
    all_stats = {
        'total_books': len(books),
        'total_pages': total_pages,
        'processed_pages': 0,
        'total_detections': 0,
        'by_class': {},
        'books': {}
    }

    processed_pages = 0

    for i, book in enumerate(books, 1):
        book_start = time.time()

        # Kitabı işle
        stats = process_book_gpu_batch(model, book, OUTPUT_DIR, BATCH_SIZE)

        book_time = time.time() - book_start
        pages_per_sec = stats['processed'] / book_time if book_time > 0 else 0
        processed_pages += stats['processed']

        # İlerleme
        progress = processed_pages / total_pages * 100
        elapsed = time.time() - start_time
        eta = (elapsed / processed_pages * total_pages - elapsed) if processed_pages > 0 else 0

        print(f"[{i}/{len(books)}] 📖 {book['name'][:50]}")
        print(f"   ✅ {stats['processed']} sayfa | {book_time:.1f}s | {pages_per_sec:.1f} sayfa/s")
        print(f"   📊 {stats['total_detections']} tespit | İlerleme: %{progress:.1f} | ETA: {eta/60:.0f}dk")

        # Genel istatistik
        all_stats['processed_pages'] += stats['processed']
        all_stats['total_detections'] += stats['total_detections']
        all_stats['books'][book['name']] = stats

        for cls_name, count in stats['by_class'].items():
            all_stats['by_class'][cls_name] = all_stats['by_class'].get(cls_name, 0) + count

        # Her 10 kitapta VRAM temizle
        if i % 10 == 0:
            torch.cuda.empty_cache()

    # Özet kaydet
    summary_file = os.path.join(OUTPUT_DIR, "detection_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, ensure_ascii=False, indent=2)

    # Final rapor
    total_time = time.time() - start_time
    avg_speed = all_stats['processed_pages'] / total_time

    print(f"\n{'='*80}")
    print("✅ TAMAMLANDI!")
    print(f"{'='*80}")
    print(f"""
📊 ÖZET:
   • Kitap:        {all_stats['total_books']}
   • Sayfa:        {all_stats['processed_pages']:,}
   • Tespit:       {all_stats['total_detections']:,}
   • Süre:         {total_time/60:.1f} dakika
   • Hız:          {avg_speed:.1f} sayfa/saniye

📈 TESPİT DAĞILIMI:""")

    for cls_name, count in sorted(all_stats['by_class'].items(), key=lambda x: x[1], reverse=True):
        print(f"   • {cls_name}: {count:,}")

    print(f"\n📁 Çıktı: {OUTPUT_DIR}")
    print(f"📄 Özet: {summary_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
