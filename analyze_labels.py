#!/usr/bin/env python3
"""
Orijinal etiket dosyalarını ve YOLO class'larını analiz et
"""

import os
from pathlib import Path
from collections import Counter
import yaml

BASE_DIR = Path(r"C:\Users\husey\d-dataset")

print("=" * 70)
print("ORİJİNAL ETİKET VE YOLO CLASS ANALİZİ")
print("=" * 70)

# 1. d-dataset altındaki klasör yapısı
print("\n📁 d-dataset KLASÖR YAPISI:")
for item in sorted(BASE_DIR.iterdir()):
    if item.is_dir():
        # Alt dosya sayıları
        txt_count = len(list(item.rglob("*.txt")))
        yaml_count = len(list(item.rglob("*.yaml"))) + len(list(item.rglob("*.yml")))
        png_count = len(list(item.rglob("*.png")))
        jpg_count = len(list(item.rglob("*.jpg")))
        json_count = len(list(item.rglob("*.json")))
        
        if txt_count + yaml_count + png_count + jpg_count + json_count > 0:
            print(f"\n   {item.name}/")
            print(f"      TXT: {txt_count}, YAML: {yaml_count}, PNG: {png_count}, JPG: {jpg_count}, JSON: {json_count}")

# 2. YOLO config dosyalarını bul
print("\n" + "=" * 70)
print("YOLO CONFIG DOSYALARI (data.yaml):")
print("=" * 70)

yaml_files = list(BASE_DIR.rglob("*.yaml")) + list(BASE_DIR.rglob("*.yml"))
for yaml_file in yaml_files[:10]:
    print(f"\n📄 {yaml_file}")
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500])
            
            # YAML parse et
            try:
                data = yaml.safe_load(content)
                if 'names' in data:
                    print(f"\n   🏷️ CLASS İSİMLERİ: {data['names']}")
            except:
                pass
    except Exception as e:
        print(f"   Hata: {e}")

# 3. Etiket dosyalarından class ID'leri analiz et
print("\n" + "=" * 70)
print("ETİKET DOSYALARINDA CLASS ID DAĞILIMI:")
print("=" * 70)

# labels klasörünü ara
labels_dirs = [
    BASE_DIR / "labels",
    BASE_DIR / "train" / "labels",
    BASE_DIR / "valid" / "labels",
]

class_counts = Counter()

for labels_dir in labels_dirs:
    if labels_dir.exists():
        print(f"\n📁 {labels_dir}")
        txt_files = list(labels_dir.rglob("*.txt"))[:1000]
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            class_id = parts[0]
                            class_counts[class_id] += 1
            except:
                pass

if class_counts:
    print(f"\n   Class ID Dağılımı:")
    for class_id, count in class_counts.most_common():
        print(f"      Class {class_id}: {count} etiket")
else:
    # Tüm txt dosyalarını ara
    print("\n   Labels klasörü bulunamadı, tüm TXT dosyalarını tarıyorum...")
    all_txt = list(BASE_DIR.rglob("*.txt"))[:500]
    for txt_file in all_txt:
        if 'label' in str(txt_file).lower() or 'train' in str(txt_file).lower():
            try:
                with open(txt_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:  # YOLO format: class x y w h
                            class_id = parts[0]
                            class_counts[class_id] += 1
            except:
                pass
    
    if class_counts:
        print(f"\n   Class ID Dağılımı:")
        for class_id, count in class_counts.most_common():
            print(f"      Class {class_id}: {count} etiket")

print("\n" + "=" * 70)
