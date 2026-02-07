#!/usr/bin/env python3
"""
YOLO Model Class İsimlerini Çıkar
"""

from pathlib import Path
from ultralytics import YOLO

# YOLO model yolu
MODEL_PATH = Path(r"C:\Users\husey\kiro2\models\yolo11_best.pt")

print("=" * 70)
print("YOLO MODEL CLASS ANALİZİ")
print("=" * 70)

print(f"\n📦 Model: {MODEL_PATH}")

if not MODEL_PATH.exists():
    print("❌ Model dosyası bulunamadı!")
    # Alternatif konumları ara
    alt_paths = [
        Path(r"C:\Users\husey\kiro2\models"),
        Path(r"C:\Users\husey\d-dataset"),
        Path(r"C:\Users\husey\kiro2"),
    ]
    for p in alt_paths:
        if p.exists():
            print(f"\n📁 {p} içindeki model dosyaları:")
            for f in p.rglob("*.pt"):
                print(f"   - {f}")
else:
    # Model yükle
    print("\n🔄 Model yükleniyor...")
    model = YOLO(str(MODEL_PATH))
    
    # Class isimlerini al
    print("\n🏷️ CLASS İSİMLERİ:")
    print("-" * 50)
    
    if hasattr(model, 'names'):
        names = model.names
        for class_id, class_name in names.items():
            print(f"   {class_id}: {class_name}")
    else:
        print("   Model'de 'names' attribute'u bulunamadı")
        print(f"   Model attributes: {dir(model)}")

print("\n" + "=" * 70)
