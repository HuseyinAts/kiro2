"""
Türkiye Üniversite Sınavları Hazırlık Platformu - Python Ortam Kurulumu
Projeye uyumlu Python versiyonu ve bağımlılıkları otomatik kurulum
"""
import subprocess
import sys
import os
import platform
import json
from pathlib import Path
import logging

# Logging konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PythonEnvironmentSetup:
    """Python ortam kurulum ve yönetim sistemi"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_path = self.project_root / "backend"
        self.required_python_version = "3.11"  # Projeye uyumlu versiyon
        self.system_info = {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version()
        }
        
    def check_python_installation(self):
        """Python kurulumunu kontrol et"""
        logger.info("🐍 Python kurulumu kontrol ediliyor...")
        
        python_commands = ["python", "python3", "py"]
        working_python = None
        
        for cmd in python_commands:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    logger.info(f"[CHECK] {cmd}: {version_info}")
                    
                    # Version kontrolü
                    if self.required_python_version in version_info:
                        working_python = cmd
                        logger.info(f"[TARGET] Uyumlu Python bulundu: {cmd}")
                        break
                    else:
                        logger.warning(f"⚠️ {cmd} versiyonu uyumlu değil (Gerekli: {self.required_python_version})")
                        
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(f"[X] {cmd} bulunamadı")
        
        if not working_python:
            logger.error("[X] Uyumlu Python kurulumu bulunamadı!")
            return None
            
        return working_python
    
    def install_python_windows(self):
        """Windows için Python kurulumu"""
        logger.info("🪟 Windows için Python kurulumu başlatılıyor...")
        
        try:
            # Chocolatey ile kurulum dene
            logger.info("[PACKAGE] Chocolatey ile Python kurulumu deneniyor...")
            subprocess.run(["choco", "install", "python", "--version", "3.11.9", "-y"], 
                         check=True, timeout=300)
            logger.info("[CHECK] Python başarıyla kuruldu (Chocolatey)")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ Chocolatey bulunamadı veya kurulum başarısız")
            
        try:
            # Winget ile kurulum dene
            logger.info("[PACKAGE] Winget ile Python kurulumu deneniyor...")
            subprocess.run(["winget", "install", "Python.Python.3.11"], 
                         check=True, timeout=300)
            logger.info("[CHECK] Python başarıyla kuruldu (Winget)")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ Winget bulunamadı veya kurulum başarısız")
        
        # Manuel kurulum talimatları
        logger.error("[X] Otomatik kurulum başarısız!")
        logger.info("[CLIPBOARD] Manuel kurulum talimatları:")
        logger.info("1. https://www.python.org/downloads/ adresine gidin")
        logger.info("2. Python 3.11.9 sürümünü indirin")
        logger.info("3. 'Add Python to PATH' seçeneğini işaretleyin")
        logger.info("4. Kurulumu tamamlayın ve terminali yeniden başlatın")
        
        return False
    
    def install_python_linux(self):
        """Linux için Python kurulumu"""
        logger.info("🐧 Linux için Python kurulumu başlatılıyor...")
        
        try:
            # Ubuntu/Debian
            subprocess.run(["sudo", "apt", "update"], check=True, timeout=60)
            subprocess.run(["sudo", "apt", "install", "-y", "python3.11", "python3.11-pip", "python3.11-venv"], 
                         check=True, timeout=300)
            logger.info("[CHECK] Python başarıyla kuruldu (apt)")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ apt kurulumu başarısız")
            
        try:
            # CentOS/RHEL/Fedora
            subprocess.run(["sudo", "yum", "install", "-y", "python3.11", "python3.11-pip"], 
                         check=True, timeout=300)
            logger.info("[CHECK] Python başarıyla kuruldu (yum)")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ yum kurulumu başarısız")
        
        return False
    
    def install_python_macos(self):
        """macOS için Python kurulumu"""
        logger.info("🍎 macOS için Python kurulumu başlatılıyor...")
        
        try:
            # Homebrew ile kurulum
            subprocess.run(["brew", "install", "python@3.11"], check=True, timeout=300)
            logger.info("[CHECK] Python başarıyla kuruldu (Homebrew)")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠️ Homebrew kurulumu başarısız")
            logger.info("[CLIPBOARD] Homebrew kurulumu için: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        
        return False
    
    def create_virtual_environment(self, python_cmd):
        """Virtual environment oluştur"""
        logger.info("🏗️ Virtual environment oluşturuluyor...")
        
        venv_path = self.backend_path / "venv"
        
        try:
            # Mevcut venv'i sil
            if venv_path.exists():
                logger.info("🗑️ Mevcut virtual environment siliniyor...")
                import shutil
                shutil.rmtree(venv_path)
            
            # Yeni venv oluştur
            subprocess.run([python_cmd, "-m", "venv", str(venv_path)], 
                         check=True, timeout=120)
            logger.info(f"[CHECK] Virtual environment oluşturuldu: {venv_path}")
            
            # Activation scripti
            if self.system_info["platform"] == "Windows":
                activate_script = venv_path / "Scripts" / "activate.bat"
                pip_cmd = str(venv_path / "Scripts" / "pip.exe")
            else:
                activate_script = venv_path / "bin" / "activate"
                pip_cmd = str(venv_path / "bin" / "pip")
            
            logger.info(f"[MEMO] Aktivasyon scripti: {activate_script}")
            
            return pip_cmd
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] Virtual environment oluşturma hatası: {e}")
            return None
    
    def install_project_dependencies(self, pip_cmd):
        """Proje bağımlılıklarını yükle"""
        logger.info("[PACKAGE] Proje bağımlılıkları yükleniyor...")
        
        requirements_files = [
            self.backend_path / "requirements.txt",
            self.backend_path / "requirements_langchain.txt"
        ]
        
        # Pip'i güncelle
        try:
            subprocess.run([pip_cmd, "install", "--upgrade", "pip"], 
                         check=True, timeout=120)
            logger.info("[CHECK] pip güncellendi")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ pip güncelleme hatası: {e}")
        
        # Requirements dosyalarını yükle
        for req_file in requirements_files:
            if req_file.exists():
                try:
                    logger.info(f"[CLIPBOARD] {req_file.name} yükleniyor...")
                    subprocess.run([pip_cmd, "install", "-r", str(req_file)], 
                                 check=True, timeout=600)
                    logger.info(f"[CHECK] {req_file.name} başarıyla yüklendi")
                except subprocess.CalledProcessError as e:
                    logger.error(f"[X] {req_file.name} yükleme hatası: {e}")
                    return False
            else:
                logger.warning(f"⚠️ {req_file} bulunamadı")
        
        # Test bağımlılıkları
        test_packages = [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0", 
            "pytest-asyncio>=0.21.1",
            "coverage>=7.3.0",
            "pytest-html>=4.1.1"
        ]
        
        try:
            logger.info("🧪 Test bağımlılıkları yükleniyor...")
            subprocess.run([pip_cmd, "install"] + test_packages, 
                         check=True, timeout=300)
            logger.info("[CHECK] Test bağımlılıkları yüklendi")
        except subprocess.CalledProcessError as e:
            logger.error(f"[X] Test bağımlılıkları yükleme hatası: {e}")
            return False
        
        return True
    
    def create_activation_scripts(self):
        """Aktivasyon scriptleri oluştur"""
        logger.info("[MEMO] Aktivasyon scriptleri oluşturuluyor...")
        
        venv_path = self.backend_path / "venv"
        
        # Windows batch script
        windows_script = self.project_root / "activate_env.bat"
        with open(windows_script, "w") as f:
            f.write(f"""@echo off
echo 🐍 Python Virtual Environment Aktivasyonu
echo ==========================================
cd /d "{self.backend_path}"
call venv\\Scripts\\activate.bat
echo [CHECK] Virtual environment aktif!
echo [FOLDER] Çalışma dizini: {self.backend_path}
echo 🧪 Testleri çalıştırmak için: python run_coverage_analysis.py
echo [ROCKET] Sunucuyu başlatmak için: python main.py
cmd /k
""")
        
        # Linux/macOS shell script
        unix_script = self.project_root / "activate_env.sh"
        with open(unix_script, "w") as f:
            f.write(f"""#!/bin/bash
echo "🐍 Python Virtual Environment Aktivasyonu"
echo "=========================================="
cd "{self.backend_path}"
source venv/bin/activate
echo "[CHECK] Virtual environment aktif!"
echo "[FOLDER] Çalışma dizini: {self.backend_path}"
echo "🧪 Testleri çalıştırmak için: python run_coverage_analysis.py"
echo "[ROCKET] Sunucuyu başlatmak için: python main.py"
exec bash
""")
        
        # Unix script'i executable yap
        if self.system_info["platform"] != "Windows":
            os.chmod(unix_script, 0o755)
        
        logger.info(f"[CHECK] Windows script: {windows_script}")
        logger.info(f"[CHECK] Unix script: {unix_script}")
    
    def verify_installation(self, python_cmd):
        """Kurulumu doğrula"""
        logger.info("[MAG] Kurulum doğrulanıyor...")
        
        venv_path = self.backend_path / "venv"
        
        if self.system_info["platform"] == "Windows":
            python_venv = str(venv_path / "Scripts" / "python.exe")
        else:
            python_venv = str(venv_path / "bin" / "python")
        
        try:
            # Python versiyonu kontrol
            result = subprocess.run([python_venv, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"[CHECK] Virtual env Python: {result.stdout.strip()}")
            else:
                logger.error("[X] Virtual environment Python çalışmıyor")
                return False
            
            # Temel paketleri kontrol
            test_imports = [
                "import fastapi",
                "import pytest", 
                "import coverage",
                "import asyncio",
                "import pydantic"
            ]
            
            for test_import in test_imports:
                result = subprocess.run([python_venv, "-c", test_import], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    package_name = test_import.split()[1]
                    logger.info(f"[CHECK] {package_name} paketi çalışıyor")
                else:
                    logger.error(f"[X] {test_import} başarısız")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"[X] Doğrulama hatası: {e}")
            return False
    
    def setup_complete_environment(self):
        """Tam ortam kurulumu"""
        logger.info("[ROCKET] Python Ortam Kurulumu Başlatılıyor...")
        logger.info("=" * 60)
        logger.info(f"[DESKTOP] Platform: {self.system_info['platform']}")
        logger.info(f"🏗️ Mimari: {self.system_info['architecture']}")
        logger.info(f"[TARGET] Hedef Python: {self.required_python_version}")
        logger.info("=" * 60)
        
        # 1. Python kontrolü
        python_cmd = self.check_python_installation()
        
        if not python_cmd:
            logger.info("📥 Python kurulumu gerekli...")
            
            if self.system_info["platform"] == "Windows":
                success = self.install_python_windows()
            elif self.system_info["platform"] == "Linux":
                success = self.install_python_linux()
            elif self.system_info["platform"] == "Darwin":  # macOS
                success = self.install_python_macos()
            else:
                logger.error(f"[X] Desteklenmeyen platform: {self.system_info['platform']}")
                return False
            
            if not success:
                logger.error("[X] Python kurulumu başarısız!")
                return False
            
            # Kurulum sonrası tekrar kontrol
            python_cmd = self.check_python_installation()
            if not python_cmd:
                logger.error("[X] Python kurulumu doğrulanamadı!")
                return False
        
        # 2. Virtual environment oluştur
        pip_cmd = self.create_virtual_environment(python_cmd)
        if not pip_cmd:
            logger.error("[X] Virtual environment oluşturulamadı!")
            return False
        
        # 3. Bağımlılıkları yükle
        if not self.install_project_dependencies(pip_cmd):
            logger.error("[X] Bağımlılık yükleme başarısız!")
            return False
        
        # 4. Aktivasyon scriptleri oluştur
        self.create_activation_scripts()
        
        # 5. Kurulumu doğrula
        if not self.verify_installation(python_cmd):
            logger.error("[X] Kurulum doğrulaması başarısız!")
            return False
        
        # 6. Başarı mesajı
        logger.info("\n" + "=" * 60)
        logger.info("[PARTY] PYTHON ORTAM KURULUMU TAMAMLANDI!")
        logger.info("=" * 60)
        logger.info("[CLIPBOARD] Sonraki Adımlar:")
        
        if self.system_info["platform"] == "Windows":
            logger.info("  1. activate_env.bat dosyasını çalıştırın")
        else:
            logger.info("  1. ./activate_env.sh dosyasını çalıştırın")
        
        logger.info("  2. Test coverage analizi: python run_coverage_analysis.py")
        logger.info("  3. Sunucuyu başlatın: python main.py")
        logger.info("  4. Frontend'i başlatın: cd frontend && npm start")
        logger.info("=" * 60)
        
        return True


def main():
    """Ana fonksiyon"""
    setup = PythonEnvironmentSetup()
    success = setup.setup_complete_environment()
    
    if success:
        print("\n[CHECK] Python ortam kurulumu başarıyla tamamlandı!")
        return 0
    else:
        print("\n[X] Python ortam kurulumu başarısız!")
        return 1


if __name__ == "__main__":
    exit(main())