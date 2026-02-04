@echo off
chcp 65001 > nul
color 0A
cls

echo ╔════════════════════════════════════════════════════════════════════╗
echo ║     🦜🔗 LANGCHAIN KURULUM VE TEST                                 ║
echo ║     Anthropic + HuggingFace + Custom Endpoint                     ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo [1] Python kontrolü yapılıyor...
python --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python bulunamadı!
    echo 📥 Lütfen Python 3.8+ yükleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python bulundu
echo.

echo [2] Gerekli paketler yükleniyor...
echo ════════════════════════════════════════════════════════════════════
echo.

echo 📦 pip güncelleniyor...
python -m pip install --upgrade pip

echo.
echo 📦 LangChain yükleniyor...
python -m pip install langchain==0.1.0 langchain-community==0.0.10

echo.
echo 📦 Vector store ve embedding paketleri yükleniyor...
python -m pip install faiss-cpu sentence-transformers

echo.
echo 📦 Ek bağımlılıklar yükleniyor...
python -m pip install redis aioredis requests tiktoken pypdf chromadb

echo.
echo ════════════════════════════════════════════════════════════════════
echo [3] Kurulum kontrol ediliyor...
echo ════════════════════════════════════════════════════════════════════
echo.

python -c "import langchain; print('✅ LangChain kuruldu! Version:', langchain.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ❌ LangChain kurulumu başarısız!
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════════════════
echo [4] Custom Endpoint ile test yapılıyor...
echo ════════════════════════════════════════════════════════════════════
echo.

echo 🔗 Custom Endpoint: https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud
echo.

echo Test başlatılıyor...
echo.
python test_langchain_with_custom_endpoint.py

echo.
echo ════════════════════════════════════════════════════════════════════
echo.
echo 🎉 Test tamamlandı!
echo.
echo 📝 Sonraki adımlar:
echo    1. backend\.env dosyasına API anahtarlarınızı ekleyin
echo    2. ANTHROPIC_API_KEY=your-key
echo    3. HUGGINGFACEHUB_API_TOKEN=your-token
echo    4. Tekrar test için: python test_langchain_with_custom_endpoint.py
echo.
echo ════════════════════════════════════════════════════════════════════
echo.
pause