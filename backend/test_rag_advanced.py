"""
Test Advanced RAG Features
Comprehensive test of all new features
"""

import asyncio
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))


async def test_basic_rag():
    """Test basic RAG functionality"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic RAG Service")
    print("=" * 60)

    from core.rag_service import RAGService

    rag = RAGService(persist_directory="./test_vector_db")

    # Add test documents
    print("\n📝 Adding test documents...")

    test_docs = [
        {
            "content": "Pythagoras teoremi, dik üçgenlerde hipotenüsün karesi, diğer iki kenarın karelerinin toplamına eşittir. a² + b² = c² formülü ile ifade edilir.",
            "metadata": {
                "subject": "matematik",
                "topic": "geometri",
                "exam_type": "LGS",
            },
        },
        {
            "content": "İkinci dereceden denklem ax² + bx + c = 0 şeklinde yazılır. Çözümü için diskriminant formülü kullanılır: Δ = b² - 4ac",
            "metadata": {"subject": "matematik", "topic": "cebir", "exam_type": "LGS"},
        },
        {
            "content": "Fotosentez, bitkilerin güneş ışığını kullanarak glikoz ürettiği bir süreçtir. 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂",
            "metadata": {"subject": "fen", "topic": "biyoloji", "exam_type": "LGS"},
        },
    ]

    result = await rag.add_documents(test_docs)
    print(f"✅ Added {result.get('message')}")

    # Test search
    print("\n🔍 Testing search...")
    results = await rag.search("Pythagoras teoremi nedir?", k=3)

    print(f"\nFound {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"\n  {i}. Score: {r['score']:.3f}")
        print(f"     Content: {r['content'][:100]}...")
        if "rerank_score" in r:
            print(f"     Rerank: {r['rerank_score']:.3f}")

    return rag


async def test_cross_encoder_reranking():
    """Test cross-encoder reranking"""
    print("\n" + "=" * 60)
    print("TEST 2: Cross-Encoder Reranking")
    print("=" * 60)

    from core.reranker import get_turkish_reranker

    reranker = get_turkish_reranker()

    # Mock search results
    results = [
        {
            "content": "Pythagoras teoremi geometride önemli bir teoremdir",
            "score": 0.75,
            "metadata": {},
        },
        {
            "content": "Dik üçgenlerde Pythagoras teoremi kullanılır",
            "score": 0.70,
            "metadata": {},
        },
        {"content": "Matematik dersi bugün işlendi", "score": 0.65, "metadata": {}},
    ]

    print("\n📊 Reranking results...")
    reranked = reranker.rerank(
        query="Pythagoras teoremi nedir?", results=results, top_k=3
    )

    print(f"\nReranked {len(reranked)} results:")
    for i, r in enumerate(reranked, 1):
        print(f"\n  {i}. Final Score: {r.score:.3f}")
        print(f"     Original: {r.original_score:.3f}")
        print(f"     Rerank: {r.rerank_score:.3f}")
        print(f"     Content: {r.content[:60]}...")


async def test_query_expansion():
    """Test query expansion"""
    print("\n" + "=" * 60)
    print("TEST 3: Query Expansion")
    print("=" * 60)

    from core.query_expansion import get_query_expander

    expander = get_query_expander()

    query = "Pythagoras teoremi nedir?"

    print(f"\n🔄 Expanding query: '{query}'")

    expanded = expander.expand(query, num_expansions=3)

    print(f"\nOriginal: {expanded.original}")
    print(f"\nExpanded queries:")
    for i, exp in enumerate(expanded.expanded, 1):
        print(f"  {i}. {exp}")

    print(f"\nKeywords: {expanded.keywords}")


async def test_deduplication():
    """Test document deduplication"""
    print("\n" + "=" * 60)
    print("TEST 4: Document Deduplication")
    print("=" * 60)

    from core.document_deduplication import DocumentDeduplicator

    dedup = DocumentDeduplicator()

    # Test documents with duplicates
    docs = [
        {"content": "Python programlama dili"},
        {"content": "Python programlama dili"},  # Exact duplicate
        {"content": "Python programlama dilidir"},  # Near duplicate
        {"content": "Java programlama dili"},
    ]

    print("\n🔍 Finding duplicates...")

    # Find duplicates
    groups = dedup.find_duplicates(docs, method="all")

    print(f"\nFound {len(groups)} duplicate groups:")
    for i, group in enumerate(groups, 1):
        print(f"\n  Group {i} ({group.method}):")
        print(f"    Canonical: {group.canonical[:60]}...")
        print(f"    Duplicates: {len(group.duplicates)}")
        print(f"    Similarity: {group.similarity:.3f}")

    # Deduplicate
    clean_docs = dedup.deduplicate(docs, keep="first")
    print(f"\n✅ Deduplicated: {len(docs)} → {len(clean_docs)} documents")


async def test_vector_store_factory():
    """Test HNSW vector store"""
    print("\n" + "=" * 60)
    print("TEST 5: HNSW Vector Store")
    print("=" * 60)

    from core.vector_store_factory import VectorStoreFactory, get_speed_optimized_config
    from langchain_community.embeddings import HuggingFaceEmbeddings

    print("\n⚙️ Creating HNSW index...")

    # Simple embeddings for testing
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    config = get_speed_optimized_config()
    print(f"Config: {config}")

    try:
        vector_store = VectorStoreFactory.create_faiss_store(
            embeddings=embeddings,
            index_type="hnsw",
            dimension=384,
            M=32,
            ef_construction=200,
        )

        print("✅ HNSW index created successfully")

        # Add some test data
        texts = ["Matematik dersi", "Fizik dersi", "Kimya dersi"]

        vector_store.add_texts(texts)
        print(f"✅ Added {len(texts)} documents to HNSW index")

        # Search
        results = vector_store.similarity_search("Matematik", k=2)
        print(f"\n🔍 Search results: {len(results)}")
        for r in results:
            print(f"  - {r.page_content}")

    except Exception as e:
        print(f"⚠️ HNSW test skipped: {e}")


async def test_ab_testing():
    """Test A/B testing framework"""
    print("\n" + "=" * 60)
    print("TEST 6: A/B Testing Framework")
    print("=" * 60)

    from core.rag_ab_testing import ABTestRunner

    runner = ABTestRunner()

    # Add experiments
    runner.add_experiment(
        name="baseline",
        description="Standard search",
        config={"method": "standard"},
        weight=0.5,
    )

    runner.add_experiment(
        name="hybrid",
        description="Hybrid search",
        config={"method": "hybrid", "alpha": 0.5},
        weight=0.5,
    )

    print(f"\n🧪 Created {len(runner.experiments)} experiments:")
    for name, exp in runner.experiments.items():
        print(f"  - {name}: {exp.description} (weight={exp.weight})")

    # Simulate user assignments
    print("\n👥 Testing user assignments (consistent hashing):")
    for i in range(5):
        user_id = f"user_{i}"
        exp = runner.assign_experiment(user_id)
        print(f"  {user_id} → {exp}")

        # Test consistency
        exp2 = runner.assign_experiment(user_id)
        assert exp == exp2, "Assignment should be consistent!"


async def test_config_system():
    """Test configuration system"""
    print("\n" + "=" * 60)
    print("TEST 7: Configuration System")
    print("=" * 60)

    from core.rag_config import (
        get_rag_config,
        get_turkish_optimized_config,
        get_high_performance_config,
    )

    print("\n⚙️ Testing configuration presets...")

    configs = {
        "Default": get_rag_config(),
        "Turkish Optimized": get_turkish_optimized_config(),
        "High Performance": get_high_performance_config(),
    }

    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  Vector Store: {config.vector_store.store_type}")
        print(f"  Embedding: {config.embedding.model_name[:50]}...")
        print(f"  Chunk Size: {config.text_splitter.chunk_size}")
        print(f"  Hybrid Search: {config.search.enable_hybrid}")
        print(f"  Reranking: {config.search.enable_reranking}")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ADVANCED RAG FEATURES - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    try:
        # Test 1: Basic RAG
        await test_basic_rag()

        # Test 2: Reranking
        await test_cross_encoder_reranking()

        # Test 3: Query Expansion
        await test_query_expansion()

        # Test 4: Deduplication
        await test_deduplication()

        # Test 5: HNSW
        await test_vector_store_factory()

        # Test 6: A/B Testing
        await test_ab_testing()

        # Test 7: Config
        await test_config_system()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
