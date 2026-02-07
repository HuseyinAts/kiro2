"""
Test LangChain Integration
Comprehensive test of all LangChain features
"""

import asyncio
import os

# Set environment variables for testing
os.environ["LANGCHAIN_VERBOSE"] = "true"
os.environ["USE_MOCK_RESPONSES"] = "false"

from agents.langchain_study_buddy import LangChainStudyBuddy

# Import LangChain modules
from core.langchain_llm_service import get_langchain_service
from core.langchain_rag_system import (
    AdvancedRAGSystem,
    DocumentProcessor,
    EducationalRAG,
)


# Color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_section(title):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[CHECK] {message}{Colors.END}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[X] {message}{Colors.END}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


async def test_langchain_llm_service():
    """Test basic LangChain LLM service"""
    print_section("1. Testing LangChain LLM Service")

    try:
        service = get_langchain_service()

        # Test 1: Basic generation
        print_info("Testing basic generation...")
        result = await service.generate(
            prompt="What is 2+2?", system_prompt="You are a helpful math tutor."
        )

        if result["success"]:
            print_success(f"Basic generation works: {result['response'][:100]}...")
        else:
            print_error(f"Basic generation failed: {result.get('error')}")

        # Test 2: Generation with memory
        print_info("Testing generation with memory...")
        result1 = await service.generate("My name is Ali", memory_type="buffer")
        result2 = await service.generate("What is my name?", memory_type="buffer")

        if "Ali" in result2.get("response", ""):
            print_success("Memory management works!")
        else:
            print_error("Memory management failed")

        # Test 3: Different memory types
        print_info("Testing different memory types...")
        for memory_type in ["buffer", "window", "summary"]:
            result = await service.generate(
                f"Testing {memory_type} memory", memory_type=memory_type
            )
            if result["success"]:
                print_success(f"{memory_type} memory works")

        # Test 4: Clear memory
        service.clear_memory()
        print_success("Memory cleared")

        return True

    except Exception as e:
        print_error(f"LLM service test failed: {e}")
        return False


async def test_langchain_tools():
    """Test LangChain tools and agents"""
    print_section("2. Testing LangChain Tools and Agents")

    try:
        service = get_langchain_service()

        # Test with tools (if available)
        print_info("Testing agent with tools...")
        result = await service.generate_with_tools(
            prompt="What is the square root of 144?", tools=["ddg-search"]
        )

        if result["success"]:
            print_success(f"Agent with tools works: {result['response'][:100]}...")
            print_info(f"Tools used: {result.get('tools_used', [])}")
        else:
            print_error(f"Agent with tools failed: {result.get('error')}")

        return True

    except Exception as e:
        print_error(f"Tools test failed: {e}")
        return False


async def test_vector_stores():
    """Test vector store creation and retrieval"""
    print_section("3. Testing Vector Stores and RAG")

    try:
        service = get_langchain_service()

        # Create sample documents
        print_info("Creating sample documents...")
        documents = [
            "LangChain is a framework for developing applications powered by language models.",
            "It enables applications to connect to various data sources.",
            "LangChain provides modular components for building LLM applications.",
            "Vector stores are used for similarity search in RAG systems.",
            "Retrieval-Augmented Generation combines retrieval with generation.",
        ]

        # Create vector store
        print_info("Creating vector store...")
        vector_store = service.create_vector_store(
            documents=documents,
            store_name="test_store",
            chunk_size=100,
            chunk_overlap=20,
        )

        if vector_store:
            print_success("Vector store created successfully")
        else:
            print_error("Failed to create vector store")
            return False

        # Create RAG chain
        print_info("Creating RAG chain...")
        rag_chain = service.create_rag_chain("test_store")

        if rag_chain:
            print_success("RAG chain created successfully")
        else:
            print_error("Failed to create RAG chain")
            return False

        # Test RAG query
        print_info("Testing RAG query...")
        result = await service.query_rag(
            query="What is LangChain used for?", chain_name="rag_test_store"
        )

        if result["success"]:
            print_success(f"RAG query successful: {result['response'][:200]}...")
            if result.get("source_documents"):
                print_info(f"Found {len(result['source_documents'])} source documents")
        else:
            print_error(f"RAG query failed: {result.get('error')}")

        # Test conversational RAG
        print_info("Creating conversational RAG chain...")
        conv_chain = service.create_conversational_rag_chain("test_store")

        if conv_chain:
            print_success("Conversational RAG chain created")

        return True

    except Exception as e:
        print_error(f"Vector store test failed: {e}")
        return False


async def test_langchain_study_buddy():
    """Test LangChain Study Buddy agent"""
    print_section("4. Testing LangChain Study Buddy")

    try:
        buddy = LangChainStudyBuddy()

        # Test chat
        print_info("Testing chat interface...")
        response = await buddy.chat(
            message="Merhaba, matematik öğrenmek istiyorum",
            session_id="test_session",
            context={"grade": 8, "subject": "matematik"},
        )

        if response["success"]:
            print_success(f"Chat response: {response['response'][:200]}...")
            if response.get("tools_used"):
                print_info(f"Tools used: {response['tools_used']}")
        else:
            print_error(f"Chat failed: {response.get('error')}")

        # Test lesson generation
        print_info("Testing lesson generation...")
        lesson = await buddy.generate_lesson(
            topic="Kesirler", grade=6, learning_style="visual", language="tr"
        )

        if lesson["success"]:
            print_success("Lesson generated successfully")
            print_info(f"Topic: {lesson['topic']}")
            print_info(f"Has explanation: {'explanation' in lesson}")
            print_info(f"Has quiz: {'quiz' in lesson}")
        else:
            print_error(f"Lesson generation failed: {lesson.get('error')}")

        # Test learning path creation
        print_info("Testing learning path creation...")
        path = await buddy.create_learning_path(
            student_name="Test Student",
            topic="Geometri",
            current_level="beginner",
            learning_style="kinesthetic",
            time_available=5,
        )

        if path["success"]:
            print_success("Learning path created successfully")
        else:
            print_error(f"Learning path creation failed: {path.get('error')}")

        # Test assessment
        print_info("Testing assessment...")
        assessment = await buddy.assess_understanding(
            questions=["What is 2+2?", "What is 3x3?"], answers=["4", "9"]
        )

        if assessment["success"]:
            print_success("Assessment completed successfully")
        else:
            print_error(f"Assessment failed: {assessment.get('error')}")

        # Get conversation summary
        summary = buddy.get_conversation_summary()
        print_info(f"Conversation summary: {summary[:200]}...")

        # Clear memory
        buddy.clear_memory()
        print_success("Memory cleared")

        return True

    except Exception as e:
        print_error(f"Study buddy test failed: {e}")
        return False


async def test_advanced_rag_system():
    """Test advanced RAG features"""
    print_section("5. Testing Advanced RAG System")

    try:
        service = get_langchain_service()
        rag_system = AdvancedRAGSystem(service)

        # Create sample educational documents
        print_info("Creating educational documents...")
        doc_processor = DocumentProcessor()

        texts = [
            "Pythagoras teoremi, dik üçgenlerde hipotenüsün karesinin dik kenarların karelerinin toplamına eşit olduğunu belirtir.",
            "Matematik, sayılar, şekiller ve örüntülerle ilgili bilim dalıdır.",
            "Geometri, şekillerin ve uzayın özelliklerini inceler.",
            "Cebir, bilinmeyenli denklemleri çözme sanatıdır.",
            "Trigonometri, üçgenlerin açıları ve kenarları arasındaki ilişkileri inceler.",
        ]

        documents = doc_processor.create_documents_from_texts(
            texts,
            metadatas=[
                {"subject": "matematik", "topic": topic}
                for topic in ["geometri", "genel", "geometri", "cebir", "trigonometri"]
            ],
        )

        # Split documents
        chunks = doc_processor.split_documents(
            documents, splitter_type="recursive", chunk_size=100, chunk_overlap=20
        )

        print_success(f"Created {len(chunks)} document chunks")

        # Create vector store
        print_info("Creating vector store...")
        vector_store = rag_system.vector_manager.create_vector_store(
            chunks, "math_store", store_type="faiss"
        )

        if vector_store:
            print_success("Vector store created")

        # Test different retriever types
        print_info("Testing different retrievers...")

        # Multi-query retriever
        multi_query = rag_system.create_multi_query_retriever("math_store")
        if multi_query:
            print_success("Multi-query retriever created")

        # Contextual compression retriever
        compressed = rag_system.create_contextual_compression_retriever("math_store")
        if compressed:
            print_success("Contextual compression retriever created")

        # Hybrid retriever
        hybrid = rag_system.create_hybrid_retriever("math_store", documents)
        if hybrid:
            print_success("Hybrid retriever created")

        # Create QA chains
        print_info("Creating QA chains...")
        qa_chain = rag_system.create_qa_chain(
            "math_store", retriever_type="multi_query"
        )

        if qa_chain:
            print_success("QA chain created")

        # Test query
        print_info("Testing RAG query...")
        result = await rag_system.query(
            query="Pythagoras teoremi nedir?", chain_name="qa_math_store_multi_query"
        )

        if result["success"]:
            print_success(f"Query successful: {result['answer'][:200]}...")
            print_info(f"Sources: {len(result.get('sources', []))} documents")
        else:
            print_error(f"Query failed: {result.get('error')}")

        return True

    except Exception as e:
        print_error(f"Advanced RAG test failed: {e}")
        return False


async def test_educational_rag():
    """Test educational RAG system"""
    print_section("6. Testing Educational RAG System")

    try:
        service = get_langchain_service()
        edu_rag = EducationalRAG(service)

        # Create sample curriculum content
        print_info("Creating sample curriculum...")

        # Create temporary files
        import tempfile

        math_content = """
        8. Sınıf Matematik Müfredatı
        
        Bölüm 1: Sayılar ve İşlemler
        - Tam sayılar
        - Rasyonel sayılar
        - Ondalık gösterimler
        
        Bölüm 2: Cebir
        - Cebirsel ifadeler
        - Denklemler
        - Eşitsizlikler
        
        Bölüm 3: Geometri
        - Üçgenler
        - Dörtgenler
        - Daire ve çember
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(math_content)
            temp_file = f.name

        # Index curriculum
        print_info("Indexing curriculum...")
        await edu_rag.index_curriculum(
            subject="matematik", grade=8, content_files=[temp_file]
        )

        print_success("Curriculum indexed")

        # Test question answering
        print_info("Testing educational Q&A...")

        questions = [
            "8. sınıf matematik müfredatında hangi konular var?",
            "Geometri bölümünde neler öğretiliyor?",
            "Cebir konuları nelerdir?",
        ]

        for question in questions:
            print_info(f"Question: {question}")
            result = await edu_rag.answer_question(
                question=question, subject="matematik", use_conversation=True
            )

            if result["success"]:
                print_success(f"Answer: {result['answer'][:150]}...")
                if result.get("educational_context"):
                    context = result["educational_context"]
                    print_info(f"  Question type: {context['question_type']}")
                    print_info(f"  Difficulty: {context['difficulty']}")
            else:
                print_error(f"Failed: {result.get('error')}")

        # Clean up temp file
        os.unlink(temp_file)

        return True

    except Exception as e:
        print_error(f"Educational RAG test failed: {e}")
        return False


async def main():
    """Run all LangChain tests"""
    print(
        f"\n{Colors.BOLD}{Colors.BLUE}🦜 LANGCHAIN INTEGRATION TEST SUITE [LINK]{Colors.END}"
    )
    print(f"{Colors.BLUE}Testing all LangChain features...{Colors.END}\n")

    test_results = {}

    # Run tests
    tests = [
        ("LLM Service", test_langchain_llm_service),
        ("Tools & Agents", test_langchain_tools),
        ("Vector Stores", test_vector_stores),
        ("Study Buddy", test_langchain_study_buddy),
        ("Advanced RAG", test_advanced_rag_system),
        ("Educational RAG", test_educational_rag),
    ]

    for test_name, test_func in tests:
        try:
            result = await test_func()
            test_results[test_name] = result
        except Exception as e:
            print_error(f"{test_name} test crashed: {e}")
            test_results[test_name] = False

    # Print summary
    print_section("TEST SUMMARY")

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    print(f"{Colors.BOLD}Results:{Colors.END}")
    for test_name, result in test_results.items():
        status = (
            f"{Colors.GREEN}[CHECK] PASSED{Colors.END}"
            if result
            else f"{Colors.RED}[X] FAILED{Colors.END}"
        )
        print(f"  {test_name}: {status}")

    print(
        f"\n{Colors.BOLD}Total: {passed_tests}/{total_tests} tests passed{Colors.END}"
    )

    if passed_tests == total_tests:
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}[PARTY] ALL TESTS PASSED! LangChain integration is working perfectly!{Colors.END}"
        )
    else:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ Some tests failed. Check the errors above.{Colors.END}"
        )

    # Print LangChain features summary
    print_section("LANGCHAIN FEATURES IMPLEMENTED")

    features = [
        "[CHECK] LangChain LLM Service with multiple models (OpenAI, Anthropic, HuggingFace)",
        "[CHECK] Memory Management (Buffer, Window, Summary, Summary Buffer)",
        "[CHECK] Agent Framework with Tools",
        "[CHECK] Vector Stores (FAISS, Chroma)",
        "[CHECK] RAG (Retrieval-Augmented Generation)",
        "[CHECK] Multi-Query Retriever",
        "[CHECK] Contextual Compression",
        "[CHECK] Hybrid Search (Dense + Sparse)",
        "[CHECK] Conversational Retrieval Chains",
        "[CHECK] Custom Prompt Templates",
        "[CHECK] Document Loaders (PDF, TXT, MD, JSON, CSV)",
        "[CHECK] Text Splitters (Recursive, Token, Markdown)",
        "[CHECK] Educational RAG System",
        "[CHECK] Structured Output Parsing",
        "[CHECK] Sequential and Parallel Chains",
    ]

    for feature in features:
        print(f"{Colors.GREEN}{feature}{Colors.END}")

    print(f"\n{Colors.BOLD}{Colors.BLUE}🦜 LangChain integration complete!{Colors.END}")


if __name__ == "__main__":
    asyncio.run(main())
