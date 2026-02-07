#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIRO2 YOLO Model Eğitim Pipeline
================================
Bu script YOLO modelini KIRO2 veri seti ile eğitir.

Kullanım:
    python train_yolo.py --epochs 100 --batch 8 --imgsz 1280

Gereksinimler:
    pip install ultralytics torch torchvision
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

def check_requirements():
    """Gerekli paketleri kontrol et"""
    try:
        import torch
        import ultralytics
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        print(f"✅ Ultralytics: {ultralytics.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Eksik paket: {e}")
        print("Kurulum: pip install ultralytics torch torchvision")
        return False

def validate_dataset(data_yaml_path):
    """Veri setini doğrula"""
    import yaml
    
    with open(data_yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print(f"\n📁 Veri Seti Doğrulama")
    print(f"{'─'*40}")
    
    # Yolları kontrol et
    base_path = Path(data_yaml_path).parent
    train_path = base_path / config.get('train', 'train/images')
    val_path = base_path / config.get('val', 'val/images')
    
    if not train_path.exists():
        train_path = Path(config.get('train', ''))
    if not val_path.exists():
        val_path = Path(config.get('val', ''))
    
    train_images = list(train_path.glob('*.png')) + list(train_path.glob('*.jpg'))
    val_images = list(val_path.glob('*.png')) + list(val_path.glob('*.jpg'))
    
    print(f"  Train görüntüler: {len(train_images)}")
    print(f"  Val görüntüler: {len(val_images)}")
    print(f"  Sınıf sayısı: {config.get('nc', 'Bilinmiyor')}")
    print(f"  Sınıflar: {config.get('names', [])}")
    
    if len(train_images) == 0:
        print("❌ Train görüntüleri bulunamadı!")
        return False
    
    print("✅ Veri seti doğrulandı")
    return True

def train_model(args):
    """YOLO modelini eğit"""
    from ultralytics import YOLO
    
    print(f"\n🚀 YOLO Eğitim Başlıyor")
    print(f"{'─'*40}")
    print(f"  Model: {args.model}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch Size: {args.batch}")
    print(f"  Image Size: {args.imgsz}")
    print(f"  Device: {args.device}")
    
    # Model yükle
    model = YOLO(args.model)
    
    # Eğitim parametreleri
    train_params = {
        'data': args.data,
        'epochs': args.epochs,
        'imgsz': args.imgsz,
        'batch': args.batch,
        'device': args.device,
        'patience': args.patience,
        'save': True,
        'save_period': 10,
        'cache': args.cache,
        'workers': args.workers,
        'project': args.project,
        'name': args.name,
        'exist_ok': True,
        'pretrained': True,
        'optimizer': 'AdamW',
        'lr0': 0.001,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
        'augment': args.augment,
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        'degrees': 0.0,
        'translate': 0.1,
        'scale': 0.5,
        'shear': 0.0,
        'perspective': 0.0,
        'flipud': 0.0,
        'fliplr': 0.5,
        'mosaic': 1.0,
        'mixup': 0.0,
        'copy_paste': 0.0,
    }
    
    # Eğitimi başlat
    results = model.train(**train_params)
    
    print(f"\n✅ Eğitim Tamamlandı!")
    print(f"  Best model: {args.project}/{args.name}/weights/best.pt")
    
    return results

def evaluate_model(model_path, data_yaml):
    """Eğitilmiş modeli değerlendir"""
    from ultralytics import YOLO
    
    print(f"\n📊 Model Değerlendirme")
    print(f"{'─'*40}")
    
    model = YOLO(model_path)
    metrics = model.val(data=data_yaml)
    
    print(f"  mAP@0.5: {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:0.95: {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall: {metrics.box.mr:.4f}")
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description='KIRO2 YOLO Model Eğitimi')
    
    # Veri seti ayarları
    parser.add_argument('--data', type=str, 
                       default=r'C:\Users\husey\kiro2\veriseti\kiro2_yolo_dataset\data.yaml',
                       help='data.yaml dosya yolu')
    
    # Model ayarları
    parser.add_argument('--model', type=str, default='yolov8l.pt',
                       choices=['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt'],
                       help='Başlangıç modeli')
    
    # Eğitim ayarları
    parser.add_argument('--epochs', type=int, default=100, help='Epoch sayısı')
    parser.add_argument('--batch', type=int, default=8, help='Batch size')
    parser.add_argument('--imgsz', type=int, default=1280, help='Görüntü boyutu')
    parser.add_argument('--device', type=str, default='0', help='GPU device (0, 1, cpu)')
    parser.add_argument('--patience', type=int, default=20, help='Early stopping patience')
    parser.add_argument('--workers', type=int, default=8, help='Dataloader workers')
    parser.add_argument('--cache', action='store_true', help='Görüntüleri cache\'le')
    parser.add_argument('--augment', action='store_true', default=True, help='Data augmentation')
    
    # Çıktı ayarları
    parser.add_argument('--project', type=str, default='runs/kiro2', help='Proje dizini')
    parser.add_argument('--name', type=str, default=f'train_{datetime.now().strftime("%Y%m%d_%H%M")}',
                       help='Çalıştırma adı')
    
    # Sadece değerlendirme
    parser.add_argument('--eval-only', type=str, default=None,
                       help='Sadece değerlendirme yap (model yolu)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("KIRO2 YOLO MODEL EĞİTİM PIPELINE")
    print("="*60)
    
    # Gereksinimleri kontrol et
    if not check_requirements():
        sys.exit(1)
    
    # Veri setini doğrula
    if not validate_dataset(args.data):
        sys.exit(1)
    
    # Sadece değerlendirme mi?
    if args.eval_only:
        evaluate_model(args.eval_only, args.data)
    else:
        # Eğitimi başlat
        results = train_model(args)
        
        # Final değerlendirme
        best_model = Path(args.project) / args.name / 'weights' / 'best.pt'
        if best_model.exists():
            evaluate_model(str(best_model), args.data)

if __name__ == '__main__':
    main()
