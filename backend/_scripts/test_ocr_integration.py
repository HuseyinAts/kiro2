"""
KIRO2 OCR Integration Test Script
=================================

TYT Matematik sayfalarından soru çıkarmak için test.

Kullanım:
    cd backend
    python test_ocr_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Backend path'i ekle
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_ocr_service():
    """OCR service test"""
    print("\n" + "="*60)
    print("KIRO2 OCR Integration Test")
    print("="*60)
    
    # 1. OCR Service'i import et
    print("\n[1] OCR Service import ediliyor...")
    try:
        from services.unified_ocr_service import (
            UnifiedOCRService,
            OCREngine,
            get_ocr_service,
            TextProcessor
        )
        print("    ✓ UnifiedOCRService imported")
    except ImportError as e:
        print(f"    ✗ Import hatası: {e}")
        print("\n    EasyOCR kurulumu gerekiyor:")
        print("    pip install easyocr")
        return False
    
    # 2. Test görseli kontrol et
    print("\n[2] Test görselleri kontrol ediliyor...")
    
    test_images_dir = Path(__file__).parent.parent / "test_results" / "yolo11_test"
    isler_files_dir = Path(__file__).parent.parent / "veriseti" / "isler-files" / "kitaplar" / "bs-2025-tyt-matematik-sb"
    
    test_image = None
    
    if test_images_dir.exists():
        test_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.png"))
        if test_files:
            test_image = test_files[0]
            print(f"    ✓ Test görseli bulundu: {test_image.name}")
    
    if test_image is None and isler_files_dir.exists():
        webp_files = list(isler_files_dir.glob("p-*.webp"))
        if webp_files:
            test_image = webp_files[0]
            print(f"    ✓ İşler-files görseli bulundu: {test_image.name}")
    
    if test_image is None:
        print("    ✗ Test görseli bulunamadı")
        print(f"    Kontrol edilen yerler:")
        print(f"      - {test_images_dir}")
        print(f"      - {isler_files_dir}")
        return False
    
    # 3. OCR Service başlat
    print("\n[3] OCR Service başlatılıyor...")
    try:
        # GPU olmadan başlat (test için)
        ocr_service = UnifiedOCRService(
            primary_engine=OCREngine.TESSERACT,  # Tesseract ile başla (daha hızlı kurulum)
            fallback_engine=OCREngine.TESSERACT,
            use_gpu=False,
            languages=['tr', 'en']
        )
        print(f"    ✓ OCR Service başlatıldı")
        print(f"      Primary engine: {ocr_service.primary_engine.value}")
        print(f"      Languages: {ocr_service.languages}")
    except Exception as e:
        print(f"    ✗ OCR Service başlatma hatası: {e}")
        return False
    
    # 4. OCR çalıştır
    print("\n[4] OCR çalıştırılıyor...")
    try:
        import cv2
        img = cv2.imread(str(test_image))
        
        if img is None:
            # WebP için PIL dene
            from PIL import Image
            import numpy as np
            pil_img = Image.open(test_image)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        print(f"    Görsel boyutu: {img.shape}")
        
        result = ocr_service.extract_text(img)
        
        print(f"    ✓ OCR tamamlandı")
        print(f"      Engine: {result.engine}")
        print(f"      Confidence: {result.confidence:.2%}")
        print(f"      İşlem süresi: {result.processing_time_ms:.0f}ms")
        print(f"      Matematik tespit: {'Evet' if result.has_math else 'Hayır'}")
        print(f"      Kutu sayısı: {len(result.boxes)}")
        print(f"\n    --- Çıkarılan Metin (ilk 500 karakter) ---")
        print(f"    {result.text[:500]}...")
        
    except Exception as e:
        print(f"    ✗ OCR hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. TextProcessor test
    print("\n[5] TextProcessor test ediliyor...")
    try:
        # Matematik tespiti
        test_text = "x² + 2x + 1 = 0 denkleminin kökleri nedir?"
        has_math = TextProcessor.detect_math(test_text)
        print(f"    ✓ Matematik tespiti: {has_math}")
        
        # LaTeX dönüştürme
        latex = TextProcessor.convert_to_latex(test_text)
        print(f"    ✓ LaTeX: {latex}")
        
        # Soru numarası çıkarma
        test_q = "15. Bir üçgenin kenarları..."
        q_num = TextProcessor.extract_question_number(test_q)
        print(f"    ✓ Soru numarası: {q_num}")
        
        # Şık çıkarma
        test_options = """
        A) 5 cm
        B) 6 cm
        C) 7 cm
        D) 8 cm
        E) 9 cm
        """
        options = TextProcessor.extract_options(test_options)
        print(f"    ✓ Şıklar: {options}")
        
    except Exception as e:
        print(f"    ✗ TextProcessor hatası: {e}")
        return False
    
    print("\n" + "="*60)
    print("✓ TÜM TESTLER BAŞARILI")
    print("="*60)
    
    print("\n📋 Sonraki Adımlar:")
    print("  1. EasyOCR kurulumu: pip install easyocr")
    print("  2. PaddleOCR kurulumu: pip install paddlepaddle paddleocr")
    print("  3. Backend başlat: uvicorn main:app --reload")
    print("  4. API test: POST /api/ocr/extract")
    print("  5. YOLO+OCR: POST /api/ocr/yolo-detect-ocr")
    
    return True


def test_yolo_ocr_pipeline():
    """YOLO + OCR pipeline testi"""
    print("\n" + "="*60)
    print("YOLO + OCR Pipeline Test")
    print("="*60)
    
    try:
        from services.yolo_question_detector import get_question_detector, DetectionClass
        print("    ✓ YOLO detector imported")
        
        detector = get_question_detector()
        info = detector.get_model_info()
        print(f"    Model: {info.get('model_path', 'N/A')}")
        print(f"    Classes: {info.get('classes', [])}")
        
    except Exception as e:
        print(f"    ✗ YOLO hatası: {e}")
        print("    YOLO modeli yüklü olmayabilir")


if __name__ == "__main__":
    print("\n🚀 KIRO2 OCR Test Script")
    
    # YOLO test
    test_yolo_ocr_pipeline()
    
    # OCR test
    asyncio.run(test_ocr_service())
