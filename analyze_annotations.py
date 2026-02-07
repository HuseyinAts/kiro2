"""
Analyze LabelMe JSON files to understand the conversion issue
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def analyze_annotations():
    """Analyze annotation structure"""

    base_path = Path(r'C:\Users\husey\kiro2\veriseti')
    annotation_sources = [
        base_path / 'annotation' / 'images',
        base_path / 'zkitap' / 'screenshots'
    ]

    all_json_files = []
    for source_dir in annotation_sources:
        json_files = list(source_dir.rglob('*.json'))
        all_json_files.extend(json_files)

    print(f"📊 Total JSON files: {len(all_json_files)}")
    print()

    # Track image references
    image_references = defaultdict(list)
    json_with_no_shapes = 0
    json_with_shapes = 0

    # Sample first 10 JSONs
    print("🔍 Sampling first 10 JSON files:")
    print("=" * 80)

    for i, json_path in enumerate(all_json_files[:10]):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            img_path = data.get('imagePath', 'N/A')
            shapes = data.get('shapes', [])

            print(f"{i+1}. JSON: {json_path.name}")
            print(f"   Image: {img_path}")
            print(f"   Shapes: {len(shapes)}")

            if shapes:
                labels = [s.get('label') for s in shapes]
                print(f"   Labels: {labels}")
            print()

        except Exception as e:
            print(f"   ERROR: {e}")
            print()

    print("=" * 80)
    print("📈 Full analysis...")
    print()

    # Full analysis
    for json_path in all_json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            img_path = data.get('imagePath', '')
            shapes = data.get('shapes', [])

            if shapes:
                json_with_shapes += 1
                # Track which JSON files reference the same image
                if img_path:
                    image_references[img_path].append(json_path.name)
            else:
                json_with_no_shapes += 1

        except Exception as e:
            pass

    print(f"✅ JSON files with shapes: {json_with_shapes}")
    print(f"⚠️ JSON files with NO shapes: {json_with_no_shapes}")
    print()

    # Find images referenced by multiple JSONs
    multi_ref_images = {img: jsons for img, jsons in image_references.items() if len(jsons) > 1}

    print(f"🔄 Images referenced by MULTIPLE JSON files: {len(multi_ref_images)}")
    print(f"📸 Unique images referenced: {len(image_references)}")
    print()

    if multi_ref_images:
        print("📋 Sample of images with multiple JSON files:")
        print("=" * 80)
        for i, (img, jsons) in enumerate(list(multi_ref_images.items())[:5]):
            print(f"{i+1}. Image: {img}")
            print(f"   Referenced by {len(jsons)} JSON files:")
            for j in jsons[:3]:  # Show first 3
                print(f"   - {j}")
            if len(jsons) > 3:
                print(f"   ... and {len(jsons) - 3} more")
            print()

    print("=" * 80)
    print("🎯 CONCLUSION:")
    print(f"   - Total JSON files: {len(all_json_files)}")
    print(f"   - JSON with annotations: {json_with_shapes}")
    print(f"   - Unique images: {len(image_references)}")
    print(f"   - Expected converted files: ~{len(image_references)}")
    print()
    print("💡 DIAGNOSIS:")
    if len(multi_ref_images) > 0:
        print(f"   ⚠️ {len(multi_ref_images)} images have multiple annotations")
        print(f"   ⚠️ Conversion script overwrites images with same filename")
        print(f"   ✅ This explains why we have {len(image_references)} files, not {json_with_shapes}")
    else:
        print(f"   ✅ No duplicate image references found")

if __name__ == '__main__':
    analyze_annotations()
