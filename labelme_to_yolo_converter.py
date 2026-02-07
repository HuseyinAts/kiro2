"""
LabelMe JSON formatını YOLO formatına çeviren script
KIRO2 Projesi - Soru Annotation Converter
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import shutil
from tqdm import tqdm

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class LabelMeToYOLO:
    def __init__(self, class_names: List[str]):
        """
        Args:
            class_names: YOLO class isimleri (örn: ['soru', 'cevaplar', 'konu'])
        """
        self.class_names = class_names
        self.class_to_id = {name: idx for idx, name in enumerate(class_names)}

    def convert_bbox(self, points: List[List[float]], img_width: int, img_height: int) -> Tuple[float, float, float, float]:
        """
        LabelMe rectangle points → YOLO format (x_center, y_center, width, height) normalized

        Args:
            points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] from LabelMe
            img_width: Image width
            img_height: Image height

        Returns:
            (x_center, y_center, width, height) normalized [0-1]
        """
        # Extract all x and y coordinates
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]

        # Get bounding box
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)

        # Calculate YOLO format
        x_center = (x_min + x_max) / 2.0 / img_width
        y_center = (y_min + y_max) / 2.0 / img_height
        width = (x_max - x_min) / img_width
        height = (y_max - y_min) / img_height

        return x_center, y_center, width, height

    def convert_annotation(self, json_path: Path, output_dir: Path, images_output_dir: Path) -> bool:
        """
        Tek bir LabelMe JSON dosyasını YOLO formatına çevir

        Args:
            json_path: LabelMe JSON dosya yolu
            output_dir: YOLO label dosyaları için output klasörü
            images_output_dir: Görsel dosyaları için output klasörü

        Returns:
            bool: Başarılı mı?
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Image bilgilerini al
            img_height = data.get('imageHeight')
            img_width = data.get('imageWidth')

            if not img_height or not img_width:
                print(f"⚠️ Görsel boyutu yok: {json_path}")
                return False

            # YOLO label dosyası oluştur
            label_filename = json_path.stem + '.txt'
            label_path = output_dir / label_filename

            yolo_lines = []

            # Her shape için
            for shape in data.get('shapes', []):
                label = shape.get('label')
                points = shape.get('points')
                shape_type = shape.get('shape_type')

                # Sadece rectangle ve bilinen class'ları al
                if shape_type != 'rectangle':
                    continue

                if label not in self.class_to_id:
                    continue

                class_id = self.class_to_id[label]

                # Bbox'ı çevir
                x_center, y_center, width, height = self.convert_bbox(
                    points, img_width, img_height
                )

                # YOLO formatı: class_id x_center y_center width height
                yolo_line = f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
                yolo_lines.append(yolo_line)

            # YOLO label dosyasını yaz
            if yolo_lines:
                with open(label_path, 'w') as f:
                    f.write('\n'.join(yolo_lines))

                # Görsel dosyasını kopyala
                img_filename = data.get('imagePath')
                if img_filename:
                    # JSON ile aynı klasörde görsel ara
                    img_path = json_path.parent / img_filename

                    if not img_path.exists():
                        # Alternatif: aynı isimde .png ara
                        img_path = json_path.parent / (json_path.stem + '.png')

                    if img_path.exists():
                        img_output_path = images_output_dir / img_path.name
                        shutil.copy2(img_path, img_output_path)
                        return True
                    else:
                        print(f"⚠️ Görsel bulunamadı: {img_path}")
                        return False
            else:
                print(f"⚠️ Annotation yok: {json_path}")
                return False

        except Exception as e:
            print(f"❌ Hata: {json_path} - {str(e)}")
            return False

    def convert_dataset(
        self,
        annotation_sources: List[Path],
        output_base_dir: Path,
        train_ratio: float = 0.8
    ):
        """
        Tüm dataset'i çevir ve train/val split yap

        Args:
            annotation_sources: JSON dosyalarının bulunduğu klasörler listesi
            output_base_dir: YOLO dataset output klasörü
            train_ratio: Train için ayrılacak oran (0-1)
        """
        # Output klasörlerini oluştur
        train_images_dir = output_base_dir / 'images' / 'train'
        val_images_dir = output_base_dir / 'images' / 'val'
        train_labels_dir = output_base_dir / 'labels' / 'train'
        val_labels_dir = output_base_dir / 'labels' / 'val'

        for dir_path in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Tüm JSON dosyalarını topla
        all_json_files = []
        for source_dir in annotation_sources:
            json_files = list(source_dir.rglob('*.json'))
            all_json_files.extend(json_files)

        print(f"📊 Toplam {len(all_json_files)} JSON dosyası bulundu")

        # Shuffle ve split
        import random
        random.shuffle(all_json_files)

        split_idx = int(len(all_json_files) * train_ratio)
        train_files = all_json_files[:split_idx]
        val_files = all_json_files[split_idx:]

        print(f"✂️ Split: {len(train_files)} train, {len(val_files)} val")

        # Convert train set
        print("\n🔄 Train set dönüştürülüyor...")
        train_success = 0
        for json_path in tqdm(train_files, desc="Train"):
            if self.convert_annotation(json_path, train_labels_dir, train_images_dir):
                train_success += 1

        # Convert val set
        print("\n🔄 Val set dönüştürülüyor...")
        val_success = 0
        for json_path in tqdm(val_files, desc="Val"):
            if self.convert_annotation(json_path, val_labels_dir, val_images_dir):
                val_success += 1

        print(f"\n✅ Train: {train_success}/{len(train_files)} başarılı")
        print(f"✅ Val: {val_success}/{len(val_files)} başarılı")

        # YAML config dosyası oluştur
        self.create_yaml_config(output_base_dir)

        print(f"\n🎉 Dataset hazır: {output_base_dir}")

    def create_yaml_config(self, output_base_dir: Path):
        """YOLO config YAML dosyası oluştur"""
        yaml_content = f"""# KIRO2 Dataset Configuration
# Auto-generated

path: {output_base_dir.absolute()}
train: images/train
val: images/val

# Classes
names:
"""
        for idx, name in enumerate(self.class_names):
            yaml_content += f"  {idx}: {name}\n"

        yaml_path = output_base_dir / 'dataset.yaml'
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        print(f"📝 Config dosyası: {yaml_path}")


def main():
    """Ana çalıştırma fonksiyonu"""

    # KIRO2 için class isimleri
    class_names = ['soru', 'cevaplar', 'konu', 'sayfa', 'test no']

    # Converter oluştur
    converter = LabelMeToYOLO(class_names)

    # Annotation kaynaklarını tanımla
    base_path = Path(r'C:\Users\husey\kiro2\veriseti')

    annotation_sources = [
        base_path / 'annotation' / 'images',
        base_path / 'zkitap' / 'screenshots'
    ]

    # Output klasörü
    output_dir = Path(r'C:\Users\husey\kiro2\yolo_dataset')

    print("🚀 KIRO2 - LabelMe → YOLO Converter")
    print("=" * 60)
    print(f"📂 Annotation kaynakları:")
    for source in annotation_sources:
        print(f"   - {source}")
    print(f"📂 Output: {output_dir}")
    print(f"🏷️ Classes: {class_names}")
    print("=" * 60)

    # Convert!
    converter.convert_dataset(
        annotation_sources=annotation_sources,
        output_base_dir=output_dir,
        train_ratio=0.8
    )

    print("\n✅ Conversion tamamlandı!")
    print(f"\n📁 Dataset yapısı:")
    print(f"   {output_dir}/")
    print(f"   ├── images/")
    print(f"   │   ├── train/")
    print(f"   │   └── val/")
    print(f"   ├── labels/")
    print(f"   │   ├── train/")
    print(f"   │   └── val/")
    print(f"   └── dataset.yaml")


if __name__ == '__main__':
    main()
