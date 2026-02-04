"""
Backend'e hizli import fix uygula
Konum: C:/Users/husey/kiro2/
"""

import os
from pathlib import Path
import shutil
from datetime import datetime

def apply_quick_fix():
    """main.py'ye sys.path fix ekle"""

    print("="*60)
    print("QUICK FIX UYGULANIYOR")
    print("="*60)

    # main.py konumu
    main_py_path = Path(r"C:\Users\husey\kiro2\backend\main.py")

    if not main_py_path.exists():
        print(f"[ERROR] main.py bulunamadi: {main_py_path}")
        return False

    print(f"[OK] main.py bulundu: {main_py_path}")

    # Backup olustur
    backup_path = main_py_path.parent / f"main.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(main_py_path, backup_path)
    print(f"[OK] Backup olusturuldu: {backup_path.name}")

    # Mevcut icerigi oku
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Zaten fix uygulanmis mi kontrol et
    if "sys.path fix - QUICK FIX" in content:
        print("[WARN] Quick fix zaten uygulanmis!")
        return True

    # Fix kodunu hazirla
    fix_code = '''import sys
from pathlib import Path

# sys.path fix - QUICK FIX for import issues
# Add backend directory to Python path so routers can import from core, models, etc.
backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
    print(f"[QUICK FIX] Backend path added to sys.path: {backend_path}")

'''

    # "import os" satirindan once ekle
    if "import os" in content:
        content = content.replace("import os", fix_code + "import os", 1)
    else:
        # Dosya basina ekle
        content = fix_code + content

    # Guncelenmis icerigi yaz
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("[OK] Quick fix uygulandi!")
    print()
    print("Eklenen kod:")
    print("-"*60)
    print(fix_code)
    print("-"*60)

    return True

def verify_fix():
    """Fix'in dogru uygulandigini kontrol et"""
    print()
    print("FIX KONTROLU")
    print("="*60)

    main_py_path = Path(r"C:\Users\husey\kiro2\backend\main.py")

    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Ilk 25 satiri goster
    print("Ilk 25 satir:")
    for i, line in enumerate(lines[:25], 1):
        print(f"{i:2d}: {line}")

    # sys.path fix var mi?
    has_fix = "sys.path fix - QUICK FIX" in content

    print()
    if has_fix:
        print("[OK] Quick fix basariyla eklendi!")
    else:
        print("[ERROR] Quick fix eklenemedi!")

    return has_fix

if __name__ == "__main__":
    success = apply_quick_fix()

    if success:
        verify_fix()

        print()
        print("="*60)
        print("SONRAKI ADIMLAR")
        print("="*60)
        print("1. Backend'i baslat:")
        print("   cd C:\\Users\\husey\\kiro2")
        print("   python -m backend.main")
        print()
        print("2. Yeni terminalde test et:")
        print("   python test_current_performance.py")
        print()
        print("[OK] Hazir! Backend'i baslat ve sonuclari yapistir.")
    else:
        print()
        print("[ERROR] Fix uygulanamadi! Hata detaylarini paylas.")
