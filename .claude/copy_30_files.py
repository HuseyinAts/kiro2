"""
30 kritik dosyayı organize eden script
"""
import os
import shutil
from pathlib import Path

# Ana dizinler
root_path = Path(r"C:\Users\husey\kiro2")
claude_files = root_path / ".claude" / "files"

# Kopyalanacak dosyalar (kategori, dosya_yolu, hedef_klasör)
files_to_copy = [
    # 01_documentation (8 dosya)
    ("01_documentation", "README.md", None),
    ("01_documentation", ".env.example", None),
    ("01_documentation", "docker-compose.yml", None),
    ("01_documentation", "docker-compose.production.yml", None),
    ("01_documentation", "API_INTEGRATION_SUMMARY.md", None),
    ("01_documentation", "PROJECT_ANALYSIS_REPORT.md", None),
    ("01_documentation", "DEPLOYMENT_STATUS.md", None),
    ("01_documentation", "AI_AGENTS_IMPROVEMENT_GUIDE.md", None),
    
    # 02_backend_services (8 dosya)
    ("02_backend_services", "backend/main.py", "main.py"),
    ("02_backend_services", "backend/services/sinav_motoru_service.py", "sinav_motoru_service.py"),
    ("02_backend_services", "backend/services/learning_style_service.py", "learning_style_service.py"),
    ("02_backend_services", "backend/services/soru_bankasi_service.py", "soru_bankasi_service.py"),
    ("02_backend_services", "backend/services/zpd_maarif_service.py", "zpd_maarif_service.py"),
    ("02_backend_services", "backend/services/irt_morfoloji_service.py", "irt_morfoloji_service.py"),
    ("02_backend_services", "backend/services/fsrs_service.py", "fsrs_service.py"),
    ("02_backend_services", "backend/services/parent_service.py", "parent_service.py"),
    
    # 03_learning_system (6 dosya)
    ("03_learning_system", "backend/HIBRIT_OGRENME_STILI_DEMO.md", None),
    ("03_learning_system", "backend/ZPD_MAARIF_DEMO.md", None),
    ("03_learning_system", "backend/IRT_MORFOLOJI_DEMO.md", None),
    ("03_learning_system", "backend/ZPD_MAARIF_RAPORU.md", None),
    ("03_learning_system", "backend/IRT_MORFOLOJI_RAPORU.md", None),
    ("03_learning_system", "backend/SINAV_MOTORU_RAPORU.md", None),
    
    # 04_api_endpoints (2 dosya)
    ("04_api_endpoints", "backend/websocket.py", None),
    ("04_api_endpoints", "backend/api_integration_test_strategy.py", None),
    
    # 05_ai_ml_modules (2 dosya)
    ("05_ai_ml_modules", "backend/LANGCHAIN_IMPLEMENTATION_COMPLETE.md", None),
    ("05_ai_ml_modules", "backend/BERTURK_IMPLEMENTATION_COMPLETE.md", None),
    
    # 06_frontend (2 dosya)
    ("06_frontend", "frontend/package.json", None),
    ("06_frontend", "frontend/vite.config.ts", None),
    
    # 07_tests (1 dosya)
    ("07_tests", "backend/TEST_COVERAGE_REPORT.md", None),
    
    # 08_deployment (1 dosya)
    ("08_deployment", "complete_setup_and_test.py", None),
]

def copy_file(source_path, dest_folder, dest_name=None):
    """Dosyayı kopyala"""
    try:
        source = root_path / source_path
        if not source.exists():
            return f"[X] Bulunamadı: {source_path}"
        
        # Hedef dosya adı
        if dest_name:
            dest = claude_files / dest_folder / dest_name
        else:
            dest = claude_files / dest_folder / source.name
        
        # Dosya boyutu kontrolü (2MB limit)
        file_size = source.stat().st_size
        if file_size > 2 * 1024 * 1024:
            return f"⚠️ Çok büyük ({file_size/1024/1024:.1f}MB): {source_path}"
        
        # Kopyala
        shutil.copy2(source, dest)
        return f"[CHECK] Kopyalandı: {source.name}"
    except Exception as e:
        return f"[X] Hata: {source_path} - {e}"

# Ana işlem
print("[FOLDER] 30 Kritik Dosya Kopyalanıyor...\n")
print("="*50)

total = 0
success = 0

for folder, file_path, dest_name in files_to_copy:
    total += 1
    result = copy_file(file_path, folder, dest_name)
    if result.startswith("[CHECK]"):
        success += 1
    print(f"[{total:02d}] {result}")

print("="*50)
print(f"\n[CHART] Sonuç: {success}/{total} dosya başarıyla kopyalandı")
print(f"[FOLDER] Dosyalar: {claude_files}")
