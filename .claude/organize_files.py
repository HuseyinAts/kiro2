"""
Claude AI Projects için dosyaları otomatik organize eden script
"""

import os
import shutil
import json
from pathlib import Path
import time

class ClaudeProjectOrganizer:
    def __init__(self):
        self.root_path = Path(r"C:\Users\husey\kiro2")
        self.claude_path = self.root_path / ".claude"
        self.files_path = self.claude_path / "files"
        
        # Kritik dosyaların listesi (öncelik sırasına göre)
        self.critical_files = {
            "01_documentation": [
                "README.md",
                "PROJECT_ANALYSIS_REPORT.md",
                "DEPLOYMENT_STATUS.md",
                "AI_AGENTS_IMPROVEMENT_GUIDE.md",
                ".env.example",
                "docker-compose.yml",
                "docker-compose.production.yml",
                "CODE_QUALITY.md"
            ],
            "02_backend_services": [
                "backend/main.py",
                "backend/fast_main.py",
                "backend/services/sinav_motoru_service.py",
                "backend/services/soru_bankasi_service.py",
                "backend/services/zpd_maarif_service.py",
                "backend/services/learning_style_service.py",
                "backend/services/irt_morfoloji_service.py",
                "backend/services/fsrs_service.py"
            ],
            "03_learning_system": [
                "backend/HIBRIT_OGRENME_STILI_DEMO.md",
                "backend/ZPD_MAARIF_DEMO.md",
                "backend/IRT_MORFOLOJI_DEMO.md",
                "backend/ZPD_MAARIF_RAPORU.md",
                "backend/IRT_MORFOLOJI_RAPORU.md",
                "backend/SINAV_MOTORU_RAPORU.md",
                "backend/TEMEL_VERI_MODELLERI_RAPORU.md"
            ],
            "04_api_endpoints": [
                "API_INTEGRATION_SUMMARY.md",
                "FRONTEND_BACKEND_INTEGRATION_REPORT.md",
                "backend/api_integration_test_strategy.py",
                "backend/websocket.py",
                "backend/websocket_exam.py"
            ],
            "05_ai_ml_modules": [
                "backend/agents/minimal_agents.py",
                "backend/agents/simple_agents.py",
                "backend/LANGCHAIN_IMPLEMENTATION_COMPLETE.md",
                "backend/BERTURK_IMPLEMENTATION_COMPLETE.md",
                "backend/TURKISH_NLP_IMPLEMENTATION.md"
            ],
            "06_frontend": [
                "frontend/package.json",
                "frontend/vite.config.ts",
                "frontend/tailwind.config.js",
                "frontend/tsconfig.json",
                "frontend/index.html"
            ],
            "07_tests": [
                "backend/test_sinav_motoru_basic.py",
                "backend/test_learning_style_simple.py",
                "backend/test_rag.py",
                "backend/TEST_COVERAGE_REPORT.md",
                "TEST_COVERAGE_SUMMARY.md"
            ],
            "08_monitoring": [
                "MONITORING_IMPLEMENTATION_SUMMARY.md",
                "PERFORMANCE_OPTIMIZATION_README.md",
                "backend/optimize_performance.py",
                "backend/coverage_monitoring_system.py",
                "backend/MONITORING_SYSTEM_README.md"
            ],
            "09_deployment": [
                "PRODUCTION_DEPLOYMENT.md",
                "GITHUB_SECRETS_SETUP.md",
                "complete_setup_and_test.py",
                "start-dev.bat",
                "deploy-production.sh"
            ],
            "10_configuration": [
                "backend/requirements.txt",
                "backend/requirements_langchain.txt",
                "backend/requirements_turkish_nlp.txt",
                "backend/pyproject.toml",
                "backend/pytest.ini",
                "sonar-project.properties"
            ]
        }
        
        self.stats = {
            "total_files": 0,
            "copied_files": 0,
            "skipped_files": 0,
            "errors": []
        }
    
    def create_folder_structure(self):
        """Klasör yapısını oluştur"""
        print("[FOLDER] Klasör yapısı oluşturuluyor...")
        
        for folder in self.critical_files.keys():
            folder_path = self.files_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CHECK] {folder} klasörü oluşturuldu")
    
    def copy_file(self, source_path, dest_folder):
        """Dosyayı kopyala ve boyutunu kontrol et"""
        source_file = self.root_path / source_path
        
        if not source_file.exists():
            self.stats["skipped_files"] += 1
            self.stats["errors"].append(f"Dosya bulunamadı: {source_path}")
            return False
        
        # Dosya boyutunu kontrol et (2MB limit)
        file_size = source_file.stat().st_size
        if file_size > 2 * 1024 * 1024:  # 2MB
            print(f"  ⚠️ {source_path} dosyası çok büyük ({file_size / 1024 / 1024:.2f}MB)")
            # Büyük dosyaları özetle
            return self.create_summary(source_file, dest_folder)
        
        # Dosyayı kopyala
        dest_file = self.files_path / dest_folder / source_file.name
        try:
            shutil.copy2(source_file, dest_file)
            self.stats["copied_files"] += 1
            print(f"  [CHECK] {source_file.name} kopyalandı")
            return True
        except Exception as e:
            self.stats["errors"].append(f"Kopyalama hatası {source_path}: {e}")
            return False
    
    def create_summary(self, source_file, dest_folder):
        """Büyük dosyalar için özet oluştur"""
        summary_name = source_file.stem + "_SUMMARY.md"
        dest_file = self.files_path / dest_folder / summary_name
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # İlk 50 ve son 50 satırı al
            summary_content = f"# {source_file.name} - Özet\n\n"
            summary_content += f"Dosya boyutu: {source_file.stat().st_size / 1024 / 1024:.2f}MB\n"
            summary_content += f"Toplam satır sayısı: {len(lines)}\n\n"
            summary_content += "## İlk 50 satır:\n```\n"
            summary_content += "".join(lines[:50])
            summary_content += "```\n\n## Son 50 satır:\n```\n"
            summary_content += "".join(lines[-50:])
            summary_content += "```"
            
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            print(f"  [MEMO] {summary_name} özet dosyası oluşturuldu")
            return True
        except:
            return False
    
    def organize_files(self):
        """Tüm dosyaları organize et"""
        print("\n[ROCKET] Dosyalar organize ediliyor...\n")
        
        for folder, files in self.critical_files.items():
            print(f"📂 {folder} klasörü işleniyor...")
            
            for file_path in files:
                self.stats["total_files"] += 1
                self.copy_file(file_path, folder)
            
            print()
    
    def create_index_file(self):
        """Index dosyası oluştur"""
        index_content = "# [BOOKS] Claude AI Projects - Dosya İndeksi\n\n"
        index_content += f"Oluşturulma Tarihi: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for folder in sorted(self.files_path.iterdir()):
            if folder.is_dir():
                index_content += f"## [FOLDER] {folder.name}\n\n"
                
                for file in sorted(folder.iterdir()):
                    if file.is_file():
                        size_kb = file.stat().st_size / 1024
                        index_content += f"- {file.name} ({size_kb:.1f}KB)\n"
                
                index_content += "\n"
        
        index_file = self.claude_path / "FILE_INDEX.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print("[CLIPBOARD] FILE_INDEX.md oluşturuldu")
    
    def print_statistics(self):
        """İstatistikleri yazdır"""
        print("\n" + "="*50)
        print("[CHART] ORGANİZASYON İSTATİSTİKLERİ")
        print("="*50)
        print(f"Toplam dosya sayısı: {self.stats['total_files']}")
        print(f"Kopyalanan dosyalar: {self.stats['copied_files']}")
        print(f"Atlanan dosyalar: {self.stats['skipped_files']}")
        
        if self.stats['errors']:
            print(f"\n⚠️ Hatalar ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:5]:  # İlk 5 hatayı göster
                print(f"  - {error}")
    
    def create_upload_instructions(self):
        """Claude'a yükleme talimatları oluştur"""
        instructions = """# 📤 Claude AI Projects'e Dosya Yükleme Talimatları

## Adım 1: Instructions Bölümü
1. `.claude/CLAUDE_AI_INSTRUCTIONS.md` dosyasını açın
2. İçeriği kopyalayın
3. Claude Projects > Instructions bölümüne yapıştırın

## Adım 2: Files Bölümü (Öncelik Sırasına Göre)

### İlk Yükleme (En Kritik 15 Dosya)
"""
        
        # İlk 15 kritik dosyayı listele
        file_count = 0
        for folder in ["01_documentation", "02_backend_services", "03_learning_system"]:
            folder_path = self.files_path / folder
            if folder_path.exists():
                instructions += f"\n#### {folder}:\n"
                for file in sorted(folder_path.iterdir())[:5]:
                    if file.is_file() and file_count < 15:
                        instructions += f"{file_count + 1}. `{folder}/{file.name}`\n"
                        file_count += 1
        
        instructions += """
## Notlar:
- Her dosya max 2MB olmalı
- Binary dosyalar (resim, video) eklemeyin
- Encoding: UTF-8
- Toplam 50 dosyaya kadar ekleyebilirsiniz

## Hızlı Kontrol:
[CHECK] Instructions eklendi mi?
[CHECK] README.md eklendi mi?
[CHECK] main.py eklendi mi?
[CHECK] .env.example eklendi mi?
[CHECK] Servis dosyaları eklendi mi?

Başarılar! [ROCKET]
"""
        
        upload_file = self.claude_path / "UPLOAD_INSTRUCTIONS.md"
        with open(upload_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("[MEMO] UPLOAD_INSTRUCTIONS.md oluşturuldu")
    
    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("[TARGET] Claude AI Projects Dosya Organizasyonu Başladı")
        print("="*50)
        
        # Klasör yapısını oluştur
        self.create_folder_structure()
        
        # Dosyaları organize et
        self.organize_files()
        
        # Index dosyası oluştur
        self.create_index_file()
        
        # Yükleme talimatları oluştur
        self.create_upload_instructions()
        
        # İstatistikleri yazdır
        self.print_statistics()
        
        print("\n[CHECK] Organizasyon tamamlandı!")
        print(f"[FOLDER] Dosyalar şurada: {self.files_path}")

if __name__ == "__main__":
    organizer = ClaudeProjectOrganizer()
    organizer.run()
