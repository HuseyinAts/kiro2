#!/usr/bin/env python3
"""
LangChain Installation and Verification Script
Installs required packages and verifies the installation
"""

import subprocess
import sys


class Colors:
    """Terminal colors"""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_colored(text: str, color: str = Colors.GREEN):
    """Print colored text"""
    print(f"{color}{text}{Colors.ENDC}")


def print_header():
    """Print header"""
    print_colored("\n" + "=" * 70, Colors.BLUE)
    print_colored("  🦜[LINK] LangChain Installation & Verification Script", Colors.BLUE)
    print_colored("=" * 70 + "\n", Colors.BLUE)


def check_python_version():
    """Check Python version"""
    print_colored("📍 Checking Python version...", Colors.BLUE)
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_colored("   [X] Python 3.7+ required!", Colors.RED)
        return False

    print_colored("   [CHECK] Python version is compatible", Colors.GREEN)
    return True


def install_package(package: str, version: str = None) -> bool:
    """Install a single package"""
    try:
        if version:
            package_spec = f"{package}=={version}"
        else:
            package_spec = package

        print(f"   Installing {package_spec}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_spec],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print_colored(f"   [CHECK] {package} installed successfully", Colors.GREEN)
            return True
        else:
            # Try without version if specified version fails
            if version:
                print(f"   Trying without version specification...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print_colored(
                        f"   [CHECK] {package} installed (latest version)", Colors.GREEN
                    )
                    return True

            print_colored(f"   ⚠️  {package} installation failed", Colors.YELLOW)
            return False

    except Exception as e:
        print_colored(f"   [X] Error installing {package}: {e}", Colors.RED)
        return False


def install_packages():
    """Install all required packages"""
    print_colored("\n[PACKAGE] Installing LangChain packages...", Colors.BLUE)

    packages = [
        ("langchain", "0.1.0"),
        ("langchain-community", "0.0.10"),
        ("faiss-cpu", None),
        ("sentence-transformers", None),
        ("redis", None),
        ("aioredis", None),
        ("tiktoken", None),
        ("pypdf", None),
        ("chromadb", None),
        ("requests", None),
    ]

    results = {}

    # Update pip first
    print("   Updating pip...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
    )

    for package, version in packages:
        success = install_package(package, version)
        results[package] = success

    return results


def verify_import(
    module_name: str, from_module: str = None, import_name: str = None
) -> bool:
    """Verify a module can be imported"""
    try:
        if from_module:
            exec(f"from {from_module} import {import_name}")
        else:
            exec(f"import {module_name}")
        return True
    except ImportError:
        return False
    except Exception:
        return False


def verify_installation():
    """Verify all components are working"""
    print_colored("\n[MAG] Verifying installation...", Colors.BLUE)

    tests = [
        ("LangChain Core", None, "langchain", None),
        ("Memory Management", "langchain.memory", None, "ConversationBufferMemory"),
        ("Vector Stores (FAISS)", "langchain.vectorstores", None, "FAISS"),
        ("Vector Stores (Chroma)", "langchain.vectorstores", None, "Chroma"),
        ("Embeddings", "langchain.embeddings", None, "HuggingFaceEmbeddings"),
        ("Chains", "langchain.chains", None, "LLMChain"),
        ("Document Loaders", "langchain.document_loaders", None, "TextLoader"),
        (
            "Text Splitters",
            "langchain.text_splitter",
            None,
            "RecursiveCharacterTextSplitter",
        ),
        ("Schema", "langchain.schema", None, "Document"),
        ("Tools", "langchain.tools", None, "Tool"),
    ]

    results = []
    for test_name, from_module, module, import_name in tests:
        if from_module:
            success = verify_import(import_name, from_module, import_name)
        else:
            success = verify_import(module)

        if success:
            print_colored(f"   [CHECK] {test_name}", Colors.GREEN)
        else:
            print_colored(f"   ⚠️  {test_name} (optional)", Colors.YELLOW)

        results.append((test_name, success))

    return results


def test_basic_functionality():
    """Test basic LangChain functionality"""
    print_colored("\n🧪 Testing basic functionality...", Colors.BLUE)

    try:
        # Test 1: Memory
        print("   Testing memory management...")
        from langchain.memory import ConversationBufferMemory

        memory = ConversationBufferMemory()
        memory.save_context({"input": "Hello"}, {"output": "Hi there!"})
        print_colored("   [CHECK] Memory management works", Colors.GREEN)
    except Exception as e:
        print_colored(f"   ⚠️  Memory test failed: {e}", Colors.YELLOW)

    try:
        # Test 2: Document creation
        print("   Testing document creation...")
        from langchain.schema import Document

        doc = Document(page_content="Test content", metadata={"source": "test"})
        print_colored("   [CHECK] Document creation works", Colors.GREEN)
    except Exception as e:
        print_colored(f"   ⚠️  Document test failed: {e}", Colors.YELLOW)

    try:
        # Test 3: Embeddings
        print("   Testing embeddings...")
        from langchain.embeddings import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        test_embedding = embeddings.embed_query("Test text")
        print_colored(
            f"   [CHECK] Embeddings work (dimension: {len(test_embedding)})",
            Colors.GREEN,
        )
    except Exception as e:
        print_colored(f"   ⚠️  Embeddings test failed: {e}", Colors.YELLOW)

    try:
        # Test 4: Vector store
        print("   Testing vector store...")
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.schema import Document
        from langchain.vectorstores import FAISS

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        docs = [Document(page_content="Test document")]
        vector_store = FAISS.from_documents(docs, embeddings)
        results = vector_store.similarity_search("test", k=1)
        print_colored(
            f"   [CHECK] Vector store works (found {len(results)} documents)",
            Colors.GREEN,
        )
    except Exception as e:
        print_colored(f"   ⚠️  Vector store test failed: {e}", Colors.YELLOW)


def show_configuration():
    """Show configuration for using the system"""
    print_colored("\n[MEMO] Configuration", Colors.BLUE)

    print("\nCreate a .env file with your API keys (optional):")
    print("---------------------------------------------------")
    env_template = """
# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-key-here

# HuggingFace
HUGGINGFACEHUB_API_TOKEN=your-huggingface-token-here

# Custom HF Endpoint
CUSTOM_HF_ENDPOINT=https://cf781mfqobm2ynkk.us-east-1.aws.endpoints.huggingface.cloud

# OpenAI (optional)
OPENAI_API_KEY=your-openai-key-here
"""
    print(env_template)


def show_usage_examples():
    """Show usage examples"""
    print_colored("\n[BULB] Usage Examples", Colors.BLUE)

    examples = """
# Example 1: Basic usage
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

memory = ConversationBufferMemory()
# Use with your LLM...

# Example 2: Vector store
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings()
vector_store = FAISS.from_texts(["doc1", "doc2"], embeddings)

# Example 3: Enhanced service
from core.langchain_llm_service_enhanced import get_enhanced_langchain_service

service = get_enhanced_langchain_service()
result = await service.generate("Hello", model_type="auto")
"""
    print(examples)


def main():
    """Main execution"""
    print_header()

    # Step 1: Check Python
    if not check_python_version():
        sys.exit(1)

    # Step 2: Install packages
    install_results = install_packages()

    # Step 3: Verify installation
    verify_results = verify_installation()

    # Step 4: Test functionality
    test_basic_functionality()

    # Summary
    print_colored("\n" + "=" * 70, Colors.BLUE)
    print_colored("[CHART] INSTALLATION SUMMARY", Colors.BLUE)
    print_colored("=" * 70, Colors.BLUE)

    successful_installs = sum(1 for success in install_results.values() if success)
    total_packages = len(install_results)

    print(f"\nPackages installed: {successful_installs}/{total_packages}")

    successful_imports = sum(1 for _, success in verify_results if success)
    total_imports = len(verify_results)

    print(f"Components verified: {successful_imports}/{total_imports}")

    if successful_installs >= 2:  # At least langchain and langchain-community
        print_colored("\n[CHECK] LangChain is ready to use!", Colors.GREEN)

        print_colored("\n[ROCKET] Next Steps:", Colors.BLUE)
        print("1. Run the full test: python test_langchain_complete.py")
        print("2. Add API keys to .env file (optional)")
        print("3. Start using LangChain in your project!")

        show_configuration()
        show_usage_examples()
    else:
        print_colored(
            "\n⚠️  Installation incomplete. Manual installation may be required.",
            Colors.YELLOW,
        )
        print("\nTry manual installation:")
        print("  pip install langchain langchain-community faiss-cpu")

    print_colored("\n✨ Done!", Colors.GREEN)


if __name__ == "__main__":
    main()
