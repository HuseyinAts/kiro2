#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🦜 LANGCHAIN INSTALLATION SCRIPT 🔗                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python installation
echo -e "${BLUE}[1] Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    echo -e "${GREEN}✅ Python found: $(python --version)${NC}"
else
    echo -e "${RED}❌ Python not found! Please install Python 3.8+${NC}"
    echo -e "${YELLOW}📥 Download from: https://www.python.org/downloads/${NC}"
    exit 1
fi

# Update pip
echo -e "\n${BLUE}[2] Updating pip...${NC}"
$PYTHON_CMD -m pip install --upgrade pip

# Install LangChain and dependencies
echo -e "\n${BLUE}[3] Installing LangChain and dependencies...${NC}"
echo "════════════════════════════════════════════════════════════════"

echo -e "\n${YELLOW}📦 Installing LangChain core...${NC}"
$PYTHON_CMD -m pip install langchain==0.1.0 || $PYTHON_CMD -m pip install langchain

echo -e "\n${YELLOW}📦 Installing LangChain Community...${NC}"
$PYTHON_CMD -m pip install langchain-community==0.0.10 || $PYTHON_CMD -m pip install langchain-community

echo -e "\n${YELLOW}📦 Installing FAISS vector store...${NC}"
$PYTHON_CMD -m pip install faiss-cpu || echo -e "${YELLOW}⚠️  FAISS installation failed (optional)${NC}"

echo -e "\n${YELLOW}📦 Installing Sentence Transformers...${NC}"
$PYTHON_CMD -m pip install sentence-transformers || echo -e "${YELLOW}⚠️  Sentence Transformers installation failed (optional)${NC}"

echo -e "\n${YELLOW}📦 Installing additional dependencies...${NC}"
$PYTHON_CMD -m pip install redis aioredis requests tiktoken pypdf

# Test installation
echo -e "\n${BLUE}[4] Testing installation...${NC}"
echo "════════════════════════════════════════════════════════════════"

echo -e "\nTest 1: LangChain import..."
if $PYTHON_CMD -c "import langchain; print('✅ LangChain successfully loaded! Version:', langchain.__version__)" 2>/dev/null; then
    :
else
    echo -e "${RED}❌ LangChain import failed!${NC}"
fi

echo -e "\nTest 2: Memory module..."
if $PYTHON_CMD -c "from langchain.memory import ConversationBufferMemory; print('✅ Memory module ready!')" 2>/dev/null; then
    :
else
    echo -e "${RED}❌ Memory module failed!${NC}"
fi

echo -e "\nTest 3: Vector store..."
if $PYTHON_CMD -c "from langchain.vectorstores import FAISS; print('✅ FAISS vector store ready!')" 2>/dev/null; then
    :
else
    echo -e "${YELLOW}⚠️  FAISS not loaded (optional)${NC}"
fi

echo -e "\nTest 4: Embeddings..."
if $PYTHON_CMD -c "from langchain.embeddings import HuggingFaceEmbeddings; print('✅ HuggingFace embeddings ready!')" 2>/dev/null; then
    :
else
    echo -e "${YELLOW}⚠️  HuggingFace embeddings not loaded (optional)${NC}"
fi

# Summary
echo -e "\n${BLUE}${BOLD}════════════════════════════════════════════════════════════════"
echo "📊 INSTALLATION SUMMARY"
echo -e "════════════════════════════════════════════════════════════════${NC}"

echo -e "\n${GREEN}✅ Installed packages:${NC}"
$PYTHON_CMD -m pip list | grep -E "langchain|faiss|sentence-transformers"

echo -e "\n${BLUE}${BOLD}════════════════════════════════════════════════════════════════"
echo "[5] To run full tests:"
echo -e "════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  $PYTHON_CMD test_langchain_complete.py"
echo ""
echo "or"
echo ""
echo "  $PYTHON_CMD quick_install_test.py"
echo ""
echo -e "${GREEN}${BOLD}🎉 Installation complete!${NC}"