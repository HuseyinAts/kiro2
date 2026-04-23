"""
Zemberek-NLP Kurulum ve Konfigürasyon Scripti
"""

import logging
import os
import subprocess
import sys
import urllib.request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ZEMBEREK_VERSION = "0.18.0"
ZEMBEREK_JAR_URL = f"https://github.com/ahmetaa/zemberek-nlp/releases/download/v{ZEMBEREK_VERSION}/zemberek-full.jar"
ZEMBEREK_JAR_PATH = "zemberek-full.jar"


def check_java_installation():
    """Java kurulumunu kontrol et"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)

        if result.returncode == 0:
            version_info = result.stderr.split("\n")[0]
            logger.info(f"[CHECK] Java kurulu: {version_info}")

            # Java 11+ kontrolü
            if "11" in version_info or "17" in version_info or "21" in version_info:
                return True
            logger.warning("⚠️ Java 11+ önerilir")
            return True
        logger.error("[X] Java kurulu değil")
        return False

    except FileNotFoundError:
        logger.error("[X] Java bulunamadı")
        return False


def download_zemberek_jar():
    """Zemberek JAR dosyasını indir"""
    if os.path.exists(ZEMBEREK_JAR_PATH):
        logger.info(f"[CHECK] Zemberek JAR zaten mevcut: {ZEMBEREK_JAR_PATH}")
        return True

    try:
        logger.info(f"📥 Zemberek JAR indiriliyor: {ZEMBEREK_JAR_URL}")

        # Progress callback
        def progress_callback(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded * 100) // total_size)
                print(
                    f"\r   İndirme: {percent}% ({downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB)",
                    end="",
                )

        urllib.request.urlretrieve(
            ZEMBEREK_JAR_URL, ZEMBEREK_JAR_PATH, progress_callback
        )

        print()  # Yeni satır
        logger.info(f"[CHECK] Zemberek JAR başarıyla indirildi: {ZEMBEREK_JAR_PATH}")
        return True

    except Exception as e:
        logger.error(f"[X] Zemberek JAR indirme hatası: {e}")
        return False


def test_zemberek_server():
    """Zemberek server'ı test et"""
    try:
        logger.info("🧪 Zemberek server test ediliyor...")

        # Server'ı başlat (test için kısa süre)
        process = subprocess.Popen(
            ["java", "-Xmx2G", "-jar", ZEMBEREK_JAR_PATH, "--server", "--port", "6789"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 10 saniye bekle
        import time

        time.sleep(10)

        # Process'i durdur
        process.terminate()
        process.wait(timeout=5)

        logger.info("[CHECK] Zemberek server test başarılı")
        return True

    except Exception as e:
        logger.error(f"[X] Zemberek server test hatası: {e}")
        return False


def create_zemberek_service_script():
    """Zemberek servis scripti oluştur"""

    # Windows için batch script
    windows_script = f"""@echo off
echo Zemberek-NLP Server baslatiliyor...
java -Xmx4G -jar {ZEMBEREK_JAR_PATH} --server --port 6789
pause
"""

    with open("start_zemberek.bat", "w", encoding="utf-8") as f:
        f.write(windows_script)

    # Linux/Mac için shell script
    unix_script = f"""#!/bin/bash
echo "Zemberek-NLP Server başlatılıyor..."
java -Xmx4G -jar {ZEMBEREK_JAR_PATH} --server --port 6789
"""

    with open("start_zemberek.sh", "w", encoding="utf-8") as f:
        f.write(unix_script)

    # Shell script'i executable yap
    try:
        os.chmod("start_zemberek.sh", 0o755)
    except:
        pass

    logger.info("[CHECK] Zemberek servis scriptleri oluşturuldu:")
    logger.info("   Windows: start_zemberek.bat")
    logger.info("   Linux/Mac: start_zemberek.sh")


def create_systemd_service():
    """Linux için systemd service dosyası oluştur"""

    current_dir = os.path.abspath(".")
    jar_path = os.path.join(current_dir, ZEMBEREK_JAR_PATH)

    systemd_service = f"""[Unit]
Description=Zemberek-NLP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory={current_dir}
ExecStart=/usr/bin/java -Xmx4G -jar {jar_path} --server --port 6789
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    service_file = "zemberek-nlp.service"

    with open(service_file, "w", encoding="utf-8") as f:
        f.write(systemd_service)

    logger.info(f"[CHECK] Systemd service dosyası oluşturuldu: {service_file}")
    logger.info("   Kurulum için:")
    logger.info(f"   sudo cp {service_file} /etc/systemd/system/")
    logger.info("   sudo systemctl daemon-reload")
    logger.info("   sudo systemctl enable zemberek-nlp")
    logger.info("   sudo systemctl start zemberek-nlp")


def install_python_dependencies():
    """Python bağımlılıklarını kur"""
    try:
        logger.info("[PACKAGE] Python bağımlılıkları kuruluyor...")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements_turkish_nlp.txt",
            ],
            check=True,
        )

        logger.info("[CHECK] Python bağımlılıkları kuruldu")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"[X] Python bağımlılık kurulum hatası: {e}")
        return False
    except FileNotFoundError:
        logger.warning("⚠️ requirements_turkish_nlp.txt bulunamadı")
        return False


def main():
    """Ana kurulum fonksiyonu"""
    print("🇹🇷 ZEMBEREK-NLP KURULUM SCRIPTI")
    print("=" * 50)

    success_count = 0
    total_steps = 5

    # 1. Java kontrolü
    print("\n1️⃣ Java kurulum kontrolü...")
    if check_java_installation():
        success_count += 1
    else:
        print("[X] Java kurulumu gerekli!")
        print("   Ubuntu/Debian: sudo apt install openjdk-11-jdk")
        print("   CentOS/RHEL: sudo yum install java-11-openjdk-devel")
        print("   Windows: https://adoptium.net/ adresinden indirin")
        return False

    # 2. Zemberek JAR indirme
    print("\n2️⃣ Zemberek JAR dosyası indirme...")
    if download_zemberek_jar():
        success_count += 1

    # 3. Python bağımlılıkları
    print("\n3️⃣ Python bağımlılıkları kurulumu...")
    if install_python_dependencies():
        success_count += 1

    # 4. Servis scriptleri
    print("\n4️⃣ Servis scriptleri oluşturma...")
    try:
        create_zemberek_service_script()
        create_systemd_service()
        success_count += 1
    except Exception as e:
        logger.error(f"[X] Servis scripti oluşturma hatası: {e}")

    # 5. Test
    print("\n5️⃣ Zemberek server testi...")
    if os.path.exists(ZEMBEREK_JAR_PATH):
        if test_zemberek_server():
            success_count += 1

    # Sonuç
    print(f"\n[CHART] KURULUM SONUCU: {success_count}/{total_steps}")

    if success_count == total_steps:
        print("[CHECK] Zemberek-NLP kurulumu başarıyla tamamlandı!")
        print("\n[ROCKET] Başlatma talimatları:")
        print("   1. Zemberek server'ı başlatın:")
        print("      Windows: start_zemberek.bat")
        print("      Linux/Mac: ./start_zemberek.sh")
        print("   2. Backend server'ı başlatın:")
        print("      python main.py")
        print("   3. Test edin:")
        print("      python turkish_nlp_demo.py")
    else:
        print("[X] Kurulum tamamlanamadı!")
        print("   Hataları düzeltin ve tekrar çalıştırın")

    return success_count == total_steps


if __name__ == "__main__":
    main()
