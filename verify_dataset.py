"""Verify YOLO dataset"""
import sys
from pathlib import Path

# Windows encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

dataset_path = Path(r'C:\Users\husey\kiro2\yolo_dataset')

train_img = len(list((dataset_path / 'images' / 'train').glob('*')))
train_lbl = len(list((dataset_path / 'labels' / 'train').glob('*.txt')))
val_img = len(list((dataset_path / 'images' / 'val').glob('*')))
val_lbl = len(list((dataset_path / 'labels' / 'val').glob('*.txt')))

print("=" * 60)
print("🎯 YOLO DATASET VERIFICATION")
print("=" * 60)
print()
print(f"📂 TRAIN SET:")
print(f"   Images: {train_img}")
print(f"   Labels: {train_lbl}")
print()
print(f"📂 VAL SET:")
print(f"   Images: {val_img}")
print(f"   Labels: {val_lbl}")
print()
print(f"📊 TOTAL:")
print(f"   Unique Images: {train_img + val_img}")
print(f"   Total Labels: {train_lbl + val_lbl}")
print()
print("=" * 60)
print("✅ Dataset is ready for training!" if train_img > 0 and val_img > 0 else "⚠️ Dataset might be incomplete")
print("=" * 60)
