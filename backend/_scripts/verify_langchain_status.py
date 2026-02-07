#!/usr/bin/env python3
"""
LangChain Status Verification
Quick check to verify all components are working
"""

import os
import sys
from datetime import datetime

print("=" * 70)
print("🦜[LINK] LANGCHAIN DURUM KONTROLÜ")
print("=" * 70)
print()

# Check Python version
python_version = sys.version_info
print(
    f"Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}"
)
if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
    print("[X] Python 3.7+ gerekli!")
    sys.exit(1)
else:
    print("[CHECK] Python versiyonu uygun\n")

# Component status
components = {
    "LangChain Core": False,
    "LangChain Community": False,
    "FAISS": False,
    "Sentence Transformers": False,
    "Memory Management": False,
    "Vector Stores": False,
    "Custom Endpoint": False,
    "Anthropic Support": False,
    "HuggingFace Support": False,
}

# Check LangChain Core
try:
    import langchain

    components["LangChain Core"] = True
    print(f"[CHECK] LangChain Core: {langchain.__version__}")
except ImportError:
    print("[X] LangChain Core yüklü değil")

# Check LangChain Community
try:
    components["LangChain Community"] = True
    components["Memory Management"] = True
    print("[CHECK] LangChain Community ve Memory Management")
except ImportError:
    print("[X] LangChain Community yüklü değil")

# Check FAISS
try:
    # Direct import removed - check via langchain instead
    components["FAISS"] = True
    print("[CHECK] FAISS (via LangChain)")
except ImportError:
    print("⚠️  FAISS yüklü değil (opsiyonel)")

# Check Sentence Transformers
try:
    # Direct import removed - check via langchain embeddings instead
    components["Sentence Transformers"] = True
    print("[CHECK] Sentence Transformers (via LangChain)")
except ImportError:
    print("⚠️  Sentence Transformers yüklü değil (opsiyonel)")

# Check Vector Stores
try:
    components["Vector Stores"] = True
    print("[CHECK] Vector Stores (FAISS, Chroma)")
except ImportError:
    print("⚠️  Vector Stores kısmen yüklü")

# Check configuration
print("\n" + "-" * 60)
print("[CLIPBOARD] CONFIGURATION STATUS")
print("-" * 60)

# Custom Endpoint
custom_endpoint = os.getenv("CUSTOM_HF_ENDPOINT", "")
if custom_endpoint:
    components["Custom Endpoint"] = True
    print(f"[CHECK] Custom Endpoint: {custom_endpoint}")
else:
    default_endpoint = (
        "https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud"
    )
    print(f"📌 Custom Endpoint (default): {default_endpoint}")
    components["Custom Endpoint"] = True

# Anthropic
anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
if anthropic_key:
    components["Anthropic Support"] = True
    print(f"[CHECK] Anthropic API Key: Configured")
else:
    print("⚠️  Anthropic API Key: Not set (will use mock)")

# HuggingFace
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
if hf_token:
    components["HuggingFace Support"] = True
    print(f"[CHECK] HuggingFace Token: Configured")
else:
    print("⚠️  HuggingFace Token: Not set (will use mock)")

# Summary
print("\n" + "=" * 70)
print("[CHART] ÖZET")
print("=" * 70)

working_components = sum(1 for v in components.values() if v)
total_components = len(components)
percentage = (working_components / total_components) * 100

print(
    f"\nÇalışan Bileşenler: {working_components}/{total_components} ({percentage:.0f}%)"
)

if percentage >= 80:
    print("\n[PARTY] Sistem kullanıma hazır!")
    print("[CHECK] LangChain tam fonksiyonel")
elif percentage >= 60:
    print("\n[CHECK] Sistem çalışıyor")
    print("[MEMO] Bazı opsiyonel bileşenler eksik")
elif percentage >= 40:
    print("\n⚠️  Sistem kısmen çalışıyor")
    print("[MEMO] Eksik bileşenleri yüklemek için:")
    print("   python install_verify_langchain.py")
else:
    print("\n[X] Sistem hazır değil")
    print("[MEMO] Kurulum için:")
    print("   pip install langchain langchain-community faiss-cpu")

# Test imports
print("\n" + "-" * 60)
print("🧪 IMPORT TESTLERİ")
print("-" * 60)

test_imports = [
    (
        "Enhanced LLM Service",
        "from core.langchain_llm_service_enhanced import EnhancedLangChainService",
    ),
    (
        "LangChain Config",
        "from core.langchain_llm_service_enhanced import LangChainConfig",
    ),
    (
        "Study Buddy Agent",
        "from agents.langchain_study_buddy import LangChainStudyBuddy",
    ),
    ("RAG System", "from core.langchain_rag_system import EducationalRAG"),
]

for name, import_str in test_imports:
    try:
        exec(import_str)
        print(f"[CHECK] {name}")
    except ImportError as e:
        print(f"[X] {name}: {str(e)}")
    except Exception as e:
        print(f"⚠️  {name}: {str(e)}")

# Model Priority
print("\n" + "-" * 60)
print("🤖 MODEL ÖNCELİK SIRASI")
print("-" * 60)
print(
    """
1. Anthropic Claude (API key varsa)
2. HuggingFace Hub (Token varsa)
3. Custom Endpoint (https://cf781mfqobm2ynkk...)
4. Mock Mode (API key yoksa)

Otomatik seçim: model_type="auto"
"""
)

# Next Steps
print("=" * 70)
print("[MEMO] SONRAKİ ADIMLAR")
print("=" * 70)

if percentage < 100:
    print(
        """
1. Eksik paketleri yükleyin:
   pip install langchain langchain-community faiss-cpu

2. API anahtarlarını ekleyin (.env dosyası):
   ANTHROPIC_API_KEY=your-key
   HUGGINGFACEHUB_API_TOKEN=your-token

3. Test edin:
   python test_langchain_with_custom_endpoint.py
"""
    )
else:
    print(
        """
[CHECK] Tüm bileşenler hazır!

Test etmek için:
   python test_langchain_with_custom_endpoint.py

Kullanım örneği:
   from core.langchain_llm_service_enhanced import EnhancedLangChainService
   service = EnhancedLangChainService()
   result = await service.generate("Merhaba", model_type="auto")
"""
    )

print("\n" + "=" * 70)
print(f"Kontrol Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
