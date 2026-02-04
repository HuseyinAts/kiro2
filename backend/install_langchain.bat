@echo off
chcp 65001 > nul
color 0A
cls

echo ╔══════════════════════════════════════════════════════════════╗
echo ║         🦜 LANGCHAIN KURULUM SCRIPTI 🔗                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1] Python versiyonu kontrol ediliyor...
python --version 2>nul
if %errorlevel% neq 0 (
    python3 --version 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Python bulunamadı! Lütfen Python 3.8+ yükleyin.
        echo 📥 İndirmek için: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set PYTHON_CMD=python3
) else (
    set PYTHON_CMD=python
)

echo ✅ Python bulundu: %PYTHON_CMD%
echo.

echo [2] pip güncelleniyor...
%PYTHON_CMD% -m pip install --upgrade pip
echo.

echo [3] LangChain ve bağımlılıkları yükleniyor...
echo ════════════════════════════════════════════════════════════════
echo.

echo 📦 LangChain çekirdek paketleri yükleniyor...
%PYTHON_CMD% -m pip install langchain==0.1.0
if %errorlevel% neq 0 (
    echo ⚠️ LangChain kurulumu başarısız, alternatif versiyon deneniyor...
    %PYTHON_CMD% -m pip install langchain
)

echo.
echo 📦 LangChain Community yükleniyor...
%PYTHON_CMD% -m pip install langchain-community==0.0.10
if %errorlevel% neq 0 (
    echo ⚠️ Community kurulumu başarısız, alternatif versiyon deneniyor...
    %PYTHON_CMD% -m pip install langchain-community
)

echo.
echo 📦 FAISS vektör veritabanı yükleniyor...
%PYTHON_CMD% -m pip install faiss-cpu
if %errorlevel% neq 0 (
    echo ⚠️ FAISS kurulumu başarısız (opsiyonel)
)

echo.
echo 📦 Sentence Transformers (embeddings için) yükleniyor...
%PYTHON_CMD% -m pip install sentence-transformers
if %errorlevel% neq 0 (
    echo ⚠️ Sentence Transformers kurulumu başarısız (opsiyonel)
)

echo.
echo 📦 Ek bağımlılıklar yükleniyor...
%PYTHON_CMD% -m pip install redis aioredis requests tiktoken pypdf

echo.
echo ════════════════════════════════════════════════════════════════
echo [4] Kurulum tamamlandı! Sistemi test ediliyor...
echo ════════════════════════════════════════════════════════════════
echo.

echo Test 1: LangChain import kontrolü...
%PYTHON_CMD% -c "import langchain; print('✅ LangChain başarıyla yüklendi! Version:', langchain.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ❌ LangChain import edilemedi!
) 

echo.
echo Test 2: Memory modülü kontrolü...
%PYTHON_CMD% -c "from langchain.memory import ConversationBufferMemory; print('✅ Memory modülü hazır!')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Memory modülü yüklenemedi!
)

echo.
echo Test 3: Vector store kontrolü...
%PYTHON_CMD% -c "from langchain.vectorstores import FAISS; print('✅ FAISS vector store hazır!')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ FAISS yüklenemedi (opsiyonel)
)

echo.
echo Test 4: Embeddings kontrolü...
%PYTHON_CMD% -c "from langchain.embeddings import HuggingFaceEmbeddings; print('✅ HuggingFace embeddings hazır!')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ HuggingFace embeddings yüklenemedi (opsiyonel)
)

echo.
echo ════════════════════════════════════════════════════════════════
echo 📊 KURULUM ÖZETI
echo ════════════════════════════════════════════════════════════════
echo.
echo ✅ Yüklenen paketler:
%PYTHON_CMD% -m pip list | findstr "langchain faiss sentence-transformers"

echo.
echo ════════════════════════════════════════════════════════════════
echo [5] Sistemi tam test etmek için:
echo ════════════════════════════════════════════════════════════════
echo.
echo   %PYTHON_CMD% test_langchain_complete.py
echo.
echo veya
echo.
echo   %PYTHON_CMD% quick_install_test.py
echo.
echo ════════════════════════════════════════════════════════════════
echo.
echo 🎉 Kurulum tamamlandı!
echo.
pause