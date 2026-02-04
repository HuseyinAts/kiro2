@echo off
chcp 65001 > nul
color 0A
cls

echo ╔══════════════════════════════════════════════════════════╗
echo ║         🦜 LANGCHAIN KURULUM VE TEST ARACI 🔗           ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

echo [1] Python versiyonu kontrol ediliyor...
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python bulunamadı! Python 3.8+ yüklemeniz gerekiyor.
    echo 📥 İndirmek için: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python bulundu
echo.

echo [2] Kurulum seçeneğini belirleyin:
echo.
echo   1) TAM KURULUM (Tüm özellikler)
echo   2) MİNİMAL KURULUM (Sadece temel LangChain)
echo   3) TEST ET (Mock test - kurulum gerektirmez)
echo   4) ÇIKIŞ
echo.
set /p choice="Seçiminiz (1-4): "

if "%choice%"=="1" goto full_install
if "%choice%"=="2" goto minimal_install
if "%choice%"=="3" goto test_only
if "%choice%"=="4" exit /b 0

:full_install
echo.
echo [TAM KURULUM] Başlatılıyor...
echo.

echo Sanal ortam oluşturuluyor...
python -m venv venv 2>nul
call venv\Scripts\activate.bat 2>nul

echo.
echo LangChain ve tüm bağımlılıklar yükleniyor...
echo Bu biraz zaman alabilir...
echo.

pip install --upgrade pip
pip install langchain==0.1.0
pip install langchain-community==0.0.10
pip install langchain-openai==0.0.5
pip install chromadb==0.4.22
pip install faiss-cpu==1.7.4
pip install sentence-transformers==2.2.2
pip install tiktoken==0.5.2
pip install pypdf==3.17.4
pip install redis==5.0.1
pip install openai==1.6.1

echo.
echo ✅ Tam kurulum tamamlandı!
goto test_system

:minimal_install
echo.
echo [MİNİMAL KURULUM] Başlatılıyor...
echo.

pip install langchain
pip install langchain-community
pip install sentence-transformers
pip install faiss-cpu

echo.
echo ✅ Minimal kurulum tamamlandı!
goto test_system

:test_only
echo.
echo [TEST MODU] Mock test çalıştırılıyor...
echo.
python test_langchain_mock.py
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Mock test çalıştırılamadı. Python dosyası kontrol ediliyor...
    if not exist test_langchain_mock.py (
        echo ❌ test_langchain_mock.py dosyası bulunamadı!
    )
)
goto end

:test_system
echo.
echo ══════════════════════════════════════════════════════════
echo Test ediliyor...
echo ══════════════════════════════════════════════════════════
echo.

REM Basit import testi
python -c "import langchain; print('✅ LangChain import edildi')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ LangChain import edilemedi!
    goto end
)

python -c "from langchain.memory import ConversationBufferMemory; print('✅ Memory modülü hazır')" 2>nul
python -c "from langchain.chains import LLMChain; print('✅ Chains modülü hazır')" 2>nul
python -c "from langchain.vectorstores import FAISS; print('✅ Vector store hazır')" 2>nul

echo.
echo Tam test çalıştırılıyor...
python test_langchain_integration.py 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ⚠️ Tam test bazı hatalar verdi (API key eksik olabilir)
    echo Mock test çalıştırılıyor...
    python test_langchain_mock.py
)

:end
echo.
echo ══════════════════════════════════════════════════════════
echo.
echo 📌 ÖNEMLİ NOTLAR:
echo.
echo 1. API Anahtarları (.env dosyası):
echo    - OPENAI_API_KEY=sk-...
echo    - ANTHROPIC_API_KEY=sk-ant-...
echo.
echo 2. Kullanım:
echo    python test_langchain_integration.py
echo.
echo 3. Mock Test (kurulum gerektirmez):
echo    python test_langchain_mock.py
echo.
echo ══════════════════════════════════════════════════════════
echo.
echo 🎉 İşlem tamamlandı!
echo.
pause