@echo off
echo ========================================
echo LangChain Installation and Test Script
echo ========================================
echo.

echo [1] Installing LangChain dependencies...
echo.

REM Core LangChain packages
pip install langchain==0.1.0
pip install langchain-community==0.0.10
pip install langchain-openai==0.0.5

REM Vector stores
pip install chromadb==0.4.22
pip install faiss-cpu==1.7.4

REM Embeddings
pip install sentence-transformers==2.2.2
pip install tiktoken==0.5.2

REM Document processing
pip install pypdf==3.17.4
pip install unstructured==0.11.8

REM Additional dependencies
pip install redis==5.0.1
pip install aioredis==2.0.1
pip install openai==1.6.1
pip install anthropic==0.8.1

echo.
echo [2] Dependencies installed successfully!
echo.

echo [3] Running LangChain integration tests...
echo.
cd /d "%~dp0"
python test_langchain_integration.py

echo.
echo ========================================
echo Test complete!
echo ========================================
pause