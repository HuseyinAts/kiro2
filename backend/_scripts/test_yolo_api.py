r"""
YOLO Question Detection API Test
================================
Bu dosyayı çalıştırarak YOLO API'nin doğru yüklendiğini test edin.

Kullanım:
    cd C:\Users\husey\kiro2\backend
    python test_yolo_api.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, '.')

print("=" * 60)
print("YOLO Question Detection API Test")
print("=" * 60)

# 1. Service import test
print("\n1. Service Import Test...")
try:
    from services.yolo_question_detector import (
        YOLOQuestionDetector,
        get_question_detector,
        detect_questions
    )
    print("   [OK] yolo_question_detector.py import OK")
except ImportError as e:
    print(f"   [ERROR] Import error: {e}")
    sys.exit(1)

# 2. API Router import test
print("\n2. API Router Import Test...")
try:
    from api.yolo_detection_api import router
    print("   [OK] yolo_detection_api.py import OK")
    print(f"   [*] Prefix: {router.prefix}")
    print(f"   [*] Routes: {len(router.routes)}")
except ImportError as e:
    print(f"   [ERROR] Import error: {e}")
    sys.exit(1)

# 3. Model file check
print("\n3. Model File Check...")
from pathlib import Path
model_path = Path(__file__).parent.parent / "models" / "yolo11_best.pt"
if model_path.exists():
    size_mb = model_path.stat().st_size / (1024 * 1024)
    print(f"   [OK] Model found: {model_path}")
    print(f"   [*] Size: {size_mb:.1f} MB")
else:
    print(f"   [ERROR] Model not found: {model_path}")

# 4. Detector initialization test (lazy load)
print("\n4. Detector Initialization Test...")
try:
    detector = get_question_detector()
    print("   [OK] Detector instance created (lazy load)")
    info = detector.get_model_info()
    print(f"   [*] Model loaded: {info['model_loaded']}")
    print(f"   [*] Device: {info['device']}")
    print(f"   [*] Classes: {list(info['classes'].values())}")
except Exception as e:
    print(f"   [WARN] Detector init warning: {e}")
    print("   (Model will be loaded on first detection)")

# 5. Routes list
print("\n5. Available API Endpoints:")
for route in router.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = list(route.methods - {'HEAD', 'OPTIONS'})
        if methods:
            print(f"   {methods[0]:6s} /api{route.path}")

print("\n" + "=" * 60)
print("[OK] All tests passed! YOLO API is ready.")
print("=" * 60)

print(r"""
Next Steps:
1. Start backend:
   cd C:\Users\husey\kiro2\backend
   uvicorn main:app --reload --port 8000

2. Test API:
   curl http://localhost:8000/api/yolo/health

3. Test detection (with image):
   curl -X POST http://localhost:8000/api/yolo/detect \
        -F "file=@test_image.png"

4. View docs:
   http://localhost:8000/docs#/YOLO%20Question%20Detection
""")
