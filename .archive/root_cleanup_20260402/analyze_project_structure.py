"""
Proje yapisini analiz et ve import sorunlarini tespit et
Konum: C:/Users/husey/kiro2/
"""

import os
from pathlib import Path
import sys

def analyze_project_structure(root_path: str):
    """Proje yapisini analiz et"""
    root = Path(root_path)

    print("="*60)
    print("PROJE YAPISI ANALIZI")
    print("="*60)
    print(f"Root Path: {root}")
    print()

    # Ana dizinleri kontrol et
    important_dirs = [
        'core',
        'models',
        'algorithms',
        'api',
        'services',
        'backend',
        'frontend'
    ]

    print("Onemli Klasorler:")
    found_dirs = {}
    for dir_name in important_dirs:
        dir_path = root / dir_name
        exists = dir_path.exists()
        found_dirs[dir_name] = exists
        status = "[OK]" if exists else "[NO]"
        print(f"   {status} {dir_name}: {dir_path}")

    print()

    # __init__.py kontrolu
    print("__init__.py Dosyalari:")
    for dir_name, exists in found_dirs.items():
        if exists:
            init_file = root / dir_name / "__init__.py"
            has_init = init_file.exists()
            status = "[OK]" if has_init else "[NO]"
            print(f"   {status} {dir_name}/__init__.py")

    print()

    # main.py konumu
    print("main.py Konumu:")
    main_locations = [
        root / "main.py",
        root / "backend" / "main.py",
    ]

    main_py_found = None
    for location in main_locations:
        if location.exists():
            main_py_found = location
            print(f"   [OK] {location}")
            break

    if not main_py_found:
        print(f"   [NO] main.py bulunamadi!")

    print()

    # Python path kontrolu
    print("Python Path:")
    for i, path in enumerate(sys.path[:5], 1):
        print(f"   {i}. {path}")

    print()

    # Backend icindeki klasorleri kontrol et
    backend_path = root / "backend"
    if backend_path.exists():
        print("Backend Klasoru Yapisi:")
        backend_subdirs = [d.name for d in backend_path.iterdir() if d.is_dir()][:10]
        for subdir in backend_subdirs:
            init_exists = (backend_path / subdir / "__init__.py").exists()
            status = "[OK]" if init_exists else "[NO]"
            print(f"   {status} backend/{subdir}/")

    print()
    print("="*60)
    print("ANALIZ TAMAMLANDI")
    print("="*60)

    # Oneri
    print("\nONERILER:")

    if not found_dirs.get('backend'):
        print("1. 'backend' klasoru yok - dosyalar root'ta mi?")

    missing_inits = [d for d, exists in found_dirs.items()
                     if exists and not (root / d / "__init__.py").exists()]
    if missing_inits:
        print(f"2. __init__.py dosyasi eksik: {', '.join(missing_inits)}")

    if str(root) not in sys.path:
        print(f"3. Root klasoru Python path'e eklenecek: {root}")

    return {
        "root": root,
        "found_dirs": found_dirs,
        "main_py": main_py_found
    }

if __name__ == "__main__":
    # Proje root'u
    project_root = r"C:\Users\husey\kiro2"

    if not os.path.exists(project_root):
        print(f"[ERROR] Klasor bulunamadi: {project_root}")
        sys.exit(1)

    result = analyze_project_structure(project_root)

    print("\nAnaliz sonuclarini buraya yapistirin...")
