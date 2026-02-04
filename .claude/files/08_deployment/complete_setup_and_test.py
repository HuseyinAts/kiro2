"""
Teknofest 2025 - YKS Hazırlık Platformu
Otomatik Kurulum ve Test Scripti
"""

import os
import sys
import subprocess
import platform
import json
import time
from pathlib import Path

class SetupAndTest:
    """Otomatik kurulum ve test sınıfı"""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.python_version = sys.version_info
        self.os_type = platform.system()
        
    def check_python_version(self):
        """Python versiyonunu kontrol et"""
        print("[MAG] Python versiyonu kontrol ediliyor...")
        
        if self.python_version.major < 3 or \
           (self.python_version.major == 3 and self.python_version.minor < 11):
            print(f"[X] Python 3.11+ gerekli. Mevcut: {sys.version}")
            return False
        
        print(f"[CHECK] Python {sys.version} bulundu")
        return True
    
    def setup_virtual_environment(self):
        """Virtual environment oluştur"""
        print("\n[PACKAGE] Virtual environment oluşturuluyor...")
        
        venv_path = self.backend_dir / "venv"
        
        if not venv_path.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
            print("[CHECK] Virtual environment oluşturuldu")
        else:
            print("[CHECK] Virtual environment zaten mevcut")
        
        return venv_path
    
    def install_backend_dependencies(self, venv_path):
        """Backend bağımlılıklarını yükle"""
        print("\n[BOOKS] Backend bağımlılıkları yükleniyor...")
        
        if self.os_type == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
        
        requirements_file = self.backend_dir / "requirements.txt"
        
        if requirements_file.exists():
            subprocess.run([str(pip_path), "install", "-r", str(requirements_file)])
            print("[CHECK] Backend bağımlılıkları yüklendi")
        else:
            print("⚠️ requirements.txt bulunamadı")
    
    def install_frontend_dependencies(self):
        """Frontend bağımlılıklarını yükle"""
        print("\n[BOOKS] Frontend bağımlılıkları yükleniyor...")
        
        if not (self.frontend_dir / "package.json").exists():
            print("⚠️ package.json bulunamadı")
            return
        
        os.chdir(self.frontend_dir)
        
        # npm install
        result = subprocess.run(["npm", "install"], capture_output=True)
        if result.returncode == 0:
            print("[CHECK] Frontend bağımlılıkları yüklendi")
        else:
            print("⚠️ npm install hatası")
        
        os.chdir(self.root_dir)
    
    def create_env_file(self):
        """Environment dosyası oluştur"""
        print("\n[LOCKED_KEY] Environment dosyası oluşturuluyor...")
        
        env_file = self.root_dir / ".env"
        env_example = self.root_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("[CHECK] .env dosyası oluşturuldu")
        elif env_file.exists():
            print("[CHECK] .env dosyası zaten mevcut")
        else:
            # Minimum .env oluştur
            with open(env_file, 'w') as f:
                f.write("""# YKS Hazırlık Platformu Environment
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/turkiye_sinav_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars
""")
            print("[CHECK] Minimum .env dosyası oluşturuldu")
    
    def test_backend(self):
        """Backend testlerini çalıştır"""
        print("\n🧪 Backend testleri çalıştırılıyor...")
        
        os.chdir(self.backend_dir)
        
        # pytest ile testleri çalıştır
        result = subprocess.run(
            ["python", "-m", "pytest", "-v", "--tb=short"],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("[CHECK] Backend testleri başarılı")
        else:
            print("⚠️ Bazı testler başarısız")
        
        os.chdir(self.root_dir)
    
    def check_services(self):
        """Servislerin durumunu kontrol et"""
        print("\n[MAG] Servis durumları kontrol ediliyor...")
        
        services = {
            "PostgreSQL": 5432,
            "Redis": 6379,
            "Elasticsearch": 9200
        }
        
        import socket
        
        for service, port in services.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"[CHECK] {service} (port {port}) aktif")
            else:
                print(f"⚠️ {service} (port {port}) aktif değil")
    
    def run_docker_compose(self):
        """Docker compose ile servisleri başlat"""
        print("\n🐳 Docker servisleri başlatılıyor...")
        
        compose_file = self.root_dir / "docker-compose.yml"
        
        if not compose_file.exists():
            print("⚠️ docker-compose.yml bulunamadı")
            return
        
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("[CHECK] Docker servisleri başlatıldı")
        else:
            print("⚠️ Docker compose hatası")
    
    def generate_report(self):
        """Kurulum raporu oluştur"""
        print("\n[CHART] Kurulum raporu oluşturuluyor...")
        
        report = {
            "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            "os": self.os_type,
            "backend_dir": str(self.backend_dir),
            "frontend_dir": str(self.frontend_dir),
            "env_file": (self.root_dir / ".env").exists(),
            "docker_compose": (self.root_dir / "docker-compose.yml").exists()
        }
        
        report_file = self.root_dir / "setup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[CHECK] Rapor oluşturuldu: {report_file}")
        
        return report
    
    def run_complete_setup(self):
        """Tam kurulum işlemini çalıştır"""
        print("=" * 50)
        print("[ROCKET] YKS HAZIRLIK PLATFORMU - OTOMATIK KURULUM")
        print("=" * 50)
        
        # Python versiyonu kontrolü
        if not self.check_python_version():
            print("\n[X] Kurulum iptal edildi")
            return False
        
        # Virtual environment
        venv_path = self.setup_virtual_environment()
        
        # Backend bağımlılıkları
        self.install_backend_dependencies(venv_path)
        
        # Frontend bağımlılıkları
        self.install_frontend_dependencies()
        
        # Environment dosyası
        self.create_env_file()
        
        # Servisleri kontrol et
        self.check_services()
        
        # Backend testleri
        self.test_backend()
        
        # Rapor oluştur
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("[CHECK] KURULUM TAMAMLANDI!")
        print("=" * 50)
        
        print("\n[CLIPBOARD] Sonraki adımlar:")
        print("1. docker-compose up -d")
        print("2. cd backend && uvicorn main:app --reload")
        print("3. cd frontend && npm run dev")
        print("\n[GLOBE] Erişim:")
        print("- Backend API: http://localhost:8000")
        print("- Frontend: http://localhost:3000")
        print("- API Docs: http://localhost:8000/docs")
        
        return True


if __name__ == "__main__":
    setup = SetupAndTest()
    success = setup.run_complete_setup()
    sys.exit(0 if success else 1)