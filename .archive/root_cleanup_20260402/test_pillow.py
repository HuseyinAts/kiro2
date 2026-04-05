#!/usr/bin/env python3
"""Test Pillow and QR code functionality"""

import sys
import io

# Test Pillow
try:
    from PIL import Image, ImageDraw, ImageFont
    print(f"[OK] Pillow {Image.__version__} imported successfully")
    
    # Create a test image
    img = Image.new('RGB', (100, 100), color='red')
    draw = ImageDraw.Draw(img)
    draw.rectangle([25, 25, 75, 75], fill='blue')
    print("[OK] Test image created successfully")
except ImportError as e:
    print(f"[ERROR] Pillow import failed: {e}")
    sys.exit(1)

# Test QR Code
try:
    import qrcode
    print(f"[OK] QRCode library imported successfully")
    
    # Generate a test QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data('KIRO2 Test QR Code')
    qr.make(fit=True)
    
    # Create QR image using Pillow
    qr_img = qr.make_image(fill_color="black", back_color="white")
    print("[OK] QR code generated successfully")
    
    # Save to bytes (simulating what happens in the app)
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    print(f"[OK] QR code saved to buffer ({len(buffer.getvalue())} bytes)")
    
except ImportError as e:
    print(f"[ERROR] QRCode import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] QR generation failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All tests passed! Pillow is working correctly with Python 3.13")
print("[INFO] Requirements.txt has been updated to use Pillow>=12.0.0")