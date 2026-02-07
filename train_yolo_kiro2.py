"""
KIRO2 - YOLO Model Eğitim Script'i
YOLOv11 kullanarak soru detection modeli eğitir
"""

from ultralytics import YOLO
from pathlib import Path
import torch

def train_yolo_model(
    dataset_yaml: str,
    model_size: str = 'n',  # n, s, m, l, x
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = '0'
):
    """
    YOLO modelini eğit

    Args:
        dataset_yaml: Dataset config dosyası yolu
        model_size: Model boyutu (n=nano, s=small, m=medium, l=large, x=xlarge)
        epochs: Epoch sayısı
        imgsz: Görsel boyutu
        batch: Batch size
        device: GPU device ('0', '1', veya 'cpu')
    """

    print("=" * 80)
    print("🚀 KIRO2 - YOLO Model Eğitimi")
    print("=" * 80)

    # GPU kontrolü
    if torch.cuda.is_available():
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️ GPU bulunamadı, CPU kullanılacak")
        device = 'cpu'

    # Model yükle
    model_name = f'yolo11{model_size}.pt'
    print(f"\n📦 Model: {model_name}")

    model = YOLO(model_name)

    # Eğitim parametreleri
    print(f"\n⚙️ Eğitim Parametreleri:")
    print(f"   Dataset: {dataset_yaml}")
    print(f"   Epochs: {epochs}")
    print(f"   Image Size: {imgsz}")
    print(f"   Batch Size: {batch}")
    print(f"   Device: {device}")

    # Eğitimi başlat
    print("\n🎯 Eğitim başlatılıyor...")
    print("=" * 80)

    results = model.train(
        data=dataset_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,

        # Optimization
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,

        # Augmentation
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,

        # Validation
        val=True,
        save=True,
        save_period=10,

        # Logging
        project='runs/detect',
        name='kiro2_soru_detection',
        exist_ok=True,

        # Advanced
        patience=50,
        plots=True,
        verbose=True
    )

    print("\n" + "=" * 80)
    print("✅ Eğitim tamamlandı!")
    print("=" * 80)

    # Sonuçları göster
    print(f"\n📊 En İyi Model:")
    print(f"   Path: {model.trainer.best}")
    print(f"   mAP@50: {results.results_dict.get('metrics/mAP50(B)', 0):.4f}")
    print(f"   mAP@50-95: {results.results_dict.get('metrics/mAP50-95(B)', 0):.4f}")

    return results


def validate_model(model_path: str, dataset_yaml: str):
    """
    Modeli validation seti üzerinde test et

    Args:
        model_path: Eğitilmiş model dosyası
        dataset_yaml: Dataset config
    """
    print("\n" + "=" * 80)
    print("🧪 Model Validation")
    print("=" * 80)

    model = YOLO(model_path)

    results = model.val(
        data=dataset_yaml,
        split='val',
        save_json=True,
        save_hybrid=True
    )

    print(f"\n📊 Validation Sonuçları:")
    print(f"   mAP@50: {results.box.map50:.4f}")
    print(f"   mAP@50-95: {results.box.map:.4f}")
    print(f"   Precision: {results.box.mp:.4f}")
    print(f"   Recall: {results.box.mr:.4f}")

    return results


def export_model(model_path: str, export_format: str = 'onnx'):
    """
    Modeli farklı formatlara export et

    Args:
        model_path: Model dosyası
        export_format: Export formatı (onnx, torchscript, coreml, etc.)
    """
    print(f"\n📦 Model Export: {export_format}")

    model = YOLO(model_path)

    exported = model.export(format=export_format)

    print(f"✅ Export edildi: {exported}")

    return exported


def main():
    """Ana çalıştırma"""

    # Dataset config
    dataset_yaml = r'C:\Users\husey\kiro2\yolo_dataset\dataset.yaml'

    # Model eğit
    results = train_yolo_model(
        dataset_yaml=dataset_yaml,
        model_size='n',      # Hızlı test için nano
        epochs=50,           # CPU için epoch azaltıldı
        imgsz=416,           # CPU için görsel boyutu küçültüldü
        batch=4,             # CPU için batch size azaltıldı
        device='cpu'         # CPU kullan
    )

    # En iyi modeli validate et
    best_model = 'runs/detect/kiro2_soru_detection/weights/best.pt'

    validate_model(best_model, dataset_yaml)

    # ONNX export (production için)
    export_model(best_model, 'onnx')

    print("\n" + "=" * 80)
    print("🎉 TÜM İŞLEMLER TAMAMLANDI!")
    print("=" * 80)
    print(f"\n📁 Model Konumu: {best_model}")
    print(f"📊 Logs: runs/detect/kiro2_soru_detection/")


if __name__ == '__main__':
    main()
